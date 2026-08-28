"""Fail-closed audits for frozen literature and evidence-review artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


class EvidenceAuditError(ValueError):
    """Evidence artifacts are missing, unsafe, malformed, or internally inconsistent."""


@dataclass(frozen=True, slots=True)
class Gate2EvidenceAudit:
    """Disclosure-safe Gate 2 evidence status report."""

    gate: str
    status: str
    snapshot_date: str
    pubmed: dict[str, Any]
    paperclip: dict[str, Any]
    current_web: dict[str, Any]
    tool_failures: dict[str, Any]
    blocked_actions: tuple[str, ...]
    required_next_steps: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable payload."""

        return asdict(self)


def _safe_file(root: Path, relative_path: str) -> Path:
    path = root / relative_path
    if path.is_symlink():
        raise EvidenceAuditError(f"evidence artifact is a symlink: {relative_path}")
    try:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError) as error:
        raise EvidenceAuditError(f"unsafe evidence path: {relative_path}") from error
    if not path.is_file():
        raise EvidenceAuditError(f"missing evidence artifact: {relative_path}")
    return path


def _read_csv(root: Path, relative_path: str) -> list[dict[str, str]]:
    path = _safe_file(root, relative_path)
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except csv.Error as error:
        raise EvidenceAuditError(f"malformed CSV evidence artifact: {relative_path}") from error
    if not rows:
        raise EvidenceAuditError(f"empty CSV evidence artifact: {relative_path}")
    if not rows[0]:
        raise EvidenceAuditError(f"missing CSV header in evidence artifact: {relative_path}")
    return rows


def _read_json(root: Path, relative_path: str) -> dict[str, Any]:
    path = _safe_file(root, relative_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise EvidenceAuditError(f"malformed JSON evidence artifact: {relative_path}") from error
    if not isinstance(payload, dict):
        raise EvidenceAuditError(f"JSON evidence artifact must be an object: {relative_path}")
    return payload


def _read_yaml(root: Path, relative_path: str) -> dict[str, Any]:
    path = _safe_file(root, relative_path)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise EvidenceAuditError(f"malformed YAML evidence artifact: {relative_path}") from error
    if not isinstance(payload, dict):
        raise EvidenceAuditError(f"YAML evidence artifact must be a mapping: {relative_path}")
    return payload


def _require_columns(rows: list[dict[str, str]], columns: set[str], relative_path: str) -> None:
    observed = set(rows[0])
    missing = columns - observed
    if missing:
        raise EvidenceAuditError(
            f"{relative_path} missing required column(s): {', '.join(sorted(missing))}"
        )


def _frozen_queries(root: Path) -> dict[str, str]:
    config = _read_yaml(root, "config/literature_queries.yml")
    raw_queries = config.get("queries")
    if not isinstance(raw_queries, list) or not raw_queries:
        raise EvidenceAuditError("literature query config contains no queries")
    frozen: dict[str, str] = {}
    for item in raw_queries:
        if not isinstance(item, dict):
            raise EvidenceAuditError("literature query config contains a malformed query")
        query_id = item.get("id")
        versions = item.get("versions")
        if not isinstance(query_id, str) or not query_id:
            raise EvidenceAuditError("literature query config contains a query without an id")
        if not isinstance(versions, list) or not versions or not isinstance(versions[0], dict):
            raise EvidenceAuditError(f"literature query {query_id} has no frozen version")
        query = versions[0].get("query")
        if not isinstance(query, str) or not query:
            raise EvidenceAuditError(f"literature query {query_id} has an invalid frozen query")
        frozen[query_id] = query
    return frozen


def _audit_pubmed(root: Path, snapshot_date: str) -> dict[str, Any]:
    base = f"sources/literature/pubmed/snapshots/{snapshot_date}"
    manifest = _read_json(root, f"{base}/search_manifest.json")
    records = _read_csv(root, f"{base}/records.csv")
    screening = _read_csv(root, f"{base}/screening.csv")
    _require_columns(records, {"pmid", "retrieval_status", "query_ids"}, f"{base}/records.csv")
    _require_columns(
        screening,
        {"pmid", "investigator_review", "title_abstract_status", "decision"},
        f"{base}/screening.csv",
    )

    frozen = _frozen_queries(root)
    raw_searches = manifest.get("searches")
    if not isinstance(raw_searches, list) or not raw_searches:
        raise EvidenceAuditError("PubMed search manifest contains no searches")
    if {search.get("query_id") for search in raw_searches if isinstance(search, dict)} != set(
        frozen
    ):
        raise EvidenceAuditError("PubMed manifest query IDs do not match frozen config")

    query_yields: dict[str, int] = {}
    manifest_pmids: set[str] = set()
    for raw_search in raw_searches:
        if not isinstance(raw_search, dict):
            raise EvidenceAuditError("PubMed search manifest contains malformed search")
        query_id = raw_search.get("query_id")
        original_query = raw_search.get("original_query")
        total_count = raw_search.get("total_count")
        pages = raw_search.get("pages")
        if not isinstance(query_id, str) or query_id not in frozen:
            raise EvidenceAuditError("PubMed search manifest contains unknown query ID")
        if original_query != frozen[query_id]:
            raise EvidenceAuditError(f"PubMed frozen query mismatch for {query_id}")
        if not isinstance(total_count, int) or total_count < 0:
            raise EvidenceAuditError(f"PubMed search {query_id} has invalid total_count")
        if not isinstance(pages, list) or not pages:
            raise EvidenceAuditError(f"PubMed search {query_id} has no pages")
        page_pmids: list[str] = []
        for page in pages:
            if not isinstance(page, dict) or not isinstance(page.get("pmids"), list):
                raise EvidenceAuditError(f"PubMed search {query_id} has malformed page")
            page_pmids.extend(str(pmid) for pmid in page["pmids"])
        if len(page_pmids) != total_count or len(set(page_pmids)) != total_count:
            raise EvidenceAuditError(f"PubMed search {query_id} count does not reconcile")
        query_yields[query_id] = total_count
        manifest_pmids.update(page_pmids)

    record_pmids = {row["pmid"] for row in records}
    screening_pmids = {row["pmid"] for row in screening}
    if len(record_pmids) != len(records):
        raise EvidenceAuditError("PubMed records contain duplicate PMIDs")
    if len(screening_pmids) != len(screening):
        raise EvidenceAuditError("PubMed screening contains duplicate PMIDs")
    if record_pmids != manifest_pmids:
        raise EvidenceAuditError("PubMed records do not match search-manifest PMIDs")
    if screening_pmids != record_pmids:
        raise EvidenceAuditError("PubMed screening rows do not match record PMIDs")
    if any(row["investigator_review"] != "pending" for row in screening):
        raise EvidenceAuditError("PubMed screening contains nonpending investigator review")
    if any(row["title_abstract_status"] != "pending_initial_screen" for row in screening):
        raise EvidenceAuditError("PubMed title/abstract screening is not uniformly pending")

    unavailable = sum(row["retrieval_status"] == "unavailable" for row in records)
    return {
        "searches": len(raw_searches),
        "unique_pmids": len(manifest_pmids),
        "records": len(records),
        "metadata_retrieved": len(records) - unavailable,
        "metadata_unavailable": unavailable,
        "screening_rows": len(screening),
        "pending_investigator_reviews": sum(
            row["investigator_review"] == "pending" for row in screening
        ),
        "completed_title_abstract_screens": 0,
        "query_yields": dict(sorted(query_yields.items())),
    }


def _audit_paperclip(root: Path, snapshot_date: str) -> dict[str, Any]:
    base = f"sources/literature/paperclip/snapshots/{snapshot_date}"
    full_text = _read_csv(root, f"{base}/full_text_manifest.csv")
    workflow = _read_csv(root, f"{base}/paperclip_workflow_manifest.csv")
    _require_columns(full_text, {"pmcid", "verification_status"}, f"{base}/full_text_manifest.csv")
    _require_columns(
        workflow,
        {"candidate_pmcid", "map_status"},
        f"{base}/paperclip_workflow_manifest.csv",
    )

    ok_claims = [row for row in full_text if row["verification_status"] == "OK"]
    unverified_or_gap = [
        row for row in full_text if row["verification_status"] in {"unverified", "gap"}
    ]
    return {
        "workflow_candidates": len(workflow),
        "successful_maps": sum(row["map_status"] == "success" for row in workflow),
        "timed_out_maps": sum(row["map_status"] == "timeout" for row in workflow),
        "full_text_rows": len(full_text),
        "verified_ok_claims": len(ok_claims),
        "unverified_or_gap_rows": len(unverified_or_gap),
        "verified_pmcids": tuple(sorted(row["pmcid"] for row in ok_claims)),
    }


def _audit_tool_failures(root: Path) -> dict[str, Any]:
    rows = _read_csv(root, "sources/literature/tool_failures.csv")
    _require_columns(rows, {"tool", "operation", "failure_code", "status"}, "tool_failures.csv")
    open_rows = [row for row in rows if row["status"] == "open"]
    closed_rows = [row for row in rows if row["status"] == "closed"]
    tavily_codes = sorted(
        {row["failure_code"] for row in rows if row["tool"] == "Tavily MCP" and row["failure_code"]}
    )
    if "monthly_cap_reached_bonus_eligible" not in tavily_codes:
        raise EvidenceAuditError("Tavily monthly-cap failure is missing from tool failures")
    return {
        "rows": len(rows),
        "open": len(open_rows),
        "closed": len(closed_rows),
        "tavily_failure_codes": tavily_codes,
    }


def _audit_current_web(root: Path, snapshot_date: str) -> dict[str, Any]:
    payload = _read_json(
        root,
        f"sources/literature/web/snapshots/{snapshot_date}/chicagohealthmap_data_glossary.json",
    )
    required = {"access_date", "authority", "source_id", "title", "tool", "url", "verified_facts"}
    missing = required - set(payload)
    if missing:
        raise EvidenceAuditError(
            "current-web glossary artifact missing field(s): " + ", ".join(sorted(missing))
        )
    facts = payload["verified_facts"]
    if not isinstance(facts, list) or not facts:
        raise EvidenceAuditError("current-web glossary artifact contains no verified facts")
    if (
        payload["tool"] != "Tavily MCP"
        or payload["url"] != "https://chicagohealthmap.com/data-glossary"
    ):
        raise EvidenceAuditError("current-web glossary artifact does not preserve Tavily source")
    concepts = tuple(
        sorted(str(fact.get("concept", "")) for fact in facts if isinstance(fact, dict))
    )
    required_concepts = {
        "capture_rate",
        "geography",
        "small_cell_suppression",
        "standardized_mean_difference",
        "capture_rate_metric",
    }
    if set(concepts) != required_concepts:
        raise EvidenceAuditError("current-web glossary artifact does not contain required concepts")
    return {
        "sources": 1,
        "official_first_party_sources": 1,
        "tavily_sources": 1,
        "source_ids": (payload["source_id"],),
        "urls": (payload["url"],),
        "concepts": concepts,
    }


def audit_gate_2_evidence(root: Path, snapshot_date: str) -> Gate2EvidenceAudit:
    """Audit frozen Gate 2 evidence artifacts without advancing the scientific gate."""

    if snapshot_date != "2026-07-14":
        raise EvidenceAuditError("only frozen snapshot date 2026-07-14 is currently supported")
    resolved_root = root.resolve()
    if not (resolved_root / "pyproject.toml").is_file():
        raise EvidenceAuditError("root is not a ChicagoHealthMap repository")
    return Gate2EvidenceAudit(
        gate="Gate 2",
        status="open",
        snapshot_date=snapshot_date,
        pubmed=_audit_pubmed(resolved_root, snapshot_date),
        paperclip=_audit_paperclip(resolved_root, snapshot_date),
        current_web=_audit_current_web(resolved_root, snapshot_date),
        tool_failures=_audit_tool_failures(resolved_root),
        blocked_actions=(
            "no novelty assertion",
            "no manuscript claim from unverified evidence",
            "no case promotion",
            "no confirmatory modeling",
            "no analytic dataset or case-study notebook before S6/Gate prerequisites",
        ),
        required_next_steps=(
            "investigator screening of 1,178 PubMed records",
            "full-text expansion for included/background records",
            "comparator and novelty adjudication",
            "official and gray-literature update",
            "investigator acceptance of the evidence matrix",
        ),
    )
