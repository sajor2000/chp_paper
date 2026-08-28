import csv
import json
from pathlib import Path
from urllib.parse import quote

import yaml


ROOT = Path(__file__).parents[2]
PUBMED = ROOT / "sources/literature/pubmed/snapshots/2026-07-14"
PAPERCLIP = ROOT / "sources/literature/paperclip/snapshots/2026-07-14"
ALLOWED_DECISIONS = {"include", "exclude", "background", "awaiting_full_text"}
ALLOWED_VERIFICATION = {"OK", "gap", "unverified", "unavailable_full_text"}
LIVE_OK = {
    "PMC10042425": (
        "L11;L15",
        "36973497",
        "In Chicago in 2018, average life expectancy for non-Hispanic Black residents was 9.1 years lower than for non-Hispanic White residents; cause-specific decomposition identified heart disease, cancer, and homicide contributions that differed by sex.",
    ),
    "PMC6902479": (
        "L13",
        "31818263",
        "With few amendments, clinical-trial statistical-analysis-plan guidance can be applied to observational studies to increase transparency and validity.",
    ),
    "PMC5013936": (
        "L6;L12",
        "27668265",
        "Standard missing-data approaches may fail to control selection bias in EHR research because observed data arise from complex patient, provider, and health-system decisions.",
    ),
    "PMC9364501": (
        "L49",
        "35945537",
        "Electronic health records contain information only about people receiving health care, and local estimate validity can vary with EHR population coverage and participating providers.",
    ),
    "PMC4963128": (
        "L36",
        "27463641",
        "The reported zip-code correlations are ecological and hypothesis-generating rather than proof of a causal relationship, and cells with fewer than 15 people were excluded.",
    ),
    "PMC9694563": (
        "L18",
        "36434553",
        "A scoping review included six studies using real-world and traditional data for noncommunicable-disease surveillance and found unclear evidence that the tools improved policy or practice decisions.",
    ),
}
WORKFLOW = {
    "multisystem EHR surveillance": (
        "multisystem electronic health record public health surveillance clinical data network",
        "s_6343ea9a",
        "m_8ac31e81",
    ),
    "small-area EHR measurement": (
        "small-area neighborhood electronic health record disease measurement mapping",
        "s_06eacba5",
        "m_4f4856b5",
    ),
    "denominator and healthcare-capture bias": (
        "electronic health record denominator healthcare capture selection bias representativeness",
        "s_35a3b8cb",
        "m_2e480cba",
    ),
    "hypertension and diabetes comparisons": (
        "neighborhood hypertension diabetes electronic health record survey comparison",
        "s_a2015688",
        "m_d85718ba",
    ),
    "COPD comparisons": (
        "COPD mortality spatial small-area geographic comparison",
        "s_1ac839f3",
        "m_98c88a8a",
    ),
    "ecological and spatial health analysis": (
        "ecological spatial health analysis limitations modifiable areal unit",
        "s_9c0b79fb",
        "m_94cff116",
    ),
    "life-expectancy inequities": (
        "Chicago neighborhood life expectancy inequities mortality",
        "s_fd7d8be5",
        "m_16755626",
    ),
    "prespecification missingness and observational estimands": (
        "observational study prespecification missing data estimand statistical analysis plan",
        "s_292eaf6a",
        "m_5dc1af31",
    ),
    "FQHC/CBO planning demonstrations": (
        "federally qualified health center community organization geospatial resource planning",
        "s_91ef3cc2",
        "m_d7afe153",
    ),
}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_pubmed_pages_reconcile_to_unique_records() -> None:
    manifest = json.loads((PUBMED / "search_manifest.json").read_text(encoding="utf-8"))
    records = _csv_rows(PUBMED / "records.csv")
    configured = yaml.safe_load((ROOT / "config/literature_queries.yml").read_text())
    frozen = {item["id"]: item["versions"][0]["query"] for item in configured["queries"]}

    assert manifest["execution_date"] == "2026-07-14"
    assert manifest["investigator_review"] == "pending"
    assert {search["query_id"] for search in manifest["searches"]} == set(frozen)
    observed: dict[str, set[str]] = {}
    all_pmids: set[str] = set()
    for search in manifest["searches"]:
        assert search["original_query"] == frozen[search["query_id"]]
        assert search["applied_filters"] == {"language": "english"}
        expected_effective = f"{search['original_query']} AND english[Language]"
        assert search["effective_query"] == expected_effective
        page_pmids = [pmid for page in search["pages"] for pmid in page["pmids"]]
        assert len(page_pmids) == search["total_count"]
        assert len(set(page_pmids)) == search["total_count"]
        assert len(search["pages"]) == 1
        page = search["pages"][0]
        assert page["offset"] == 0
        assert page["returned_count"] == len(page["pmids"]) == search["total_count"]
        expected_url = "https://pubmed.ncbi.nlm.nih.gov/?term=" + quote(
            expected_effective, safe="()*"
        )
        assert page["search_url"] == expected_url
        observed[search["query_id"]] = set(page_pmids)
        all_pmids.update(page_pmids)

    assert len(records) == len(all_pmids)
    assert len({row["pmid"] for row in records}) == len(records)
    for row in records:
        expected = sorted(query_id for query_id, pmids in observed.items() if row["pmid"] in pmids)
        assert row["query_ids"] == ";".join(expected)

    unavailable = [row for row in records if row["retrieval_status"] == "unavailable"]
    assert len(unavailable) == 13
    metadata_fields = set(records[0]) - {"pmid", "retrieval_status", "query_ids"}
    assert all(all(not row[field] for field in metadata_fields) for row in unavailable)


def test_screening_contract_is_conservative_and_pending_review() -> None:
    records = _csv_rows(PUBMED / "records.csv")
    screening = _csv_rows(PUBMED / "screening.csv")

    assert {row["pmid"] for row in screening} == {row["pmid"] for row in records}
    assert len(screening) == 1178
    for row in screening:
        assert row["decision"] in ALLOWED_DECISIONS
        assert row["reviewer"] == "codex_initial_screen"
        assert row["investigator_review"] == "pending"
        assert row["title_abstract_status"] == "pending_initial_screen"
        assert row["decision"] == "awaiting_full_text"
        assert row["full_text_required"] == "unknown"
        assert bool(row["exclusion_reason"]) is (row["decision"] == "exclude")


def test_full_text_and_evidence_claims_use_explicit_verification_status() -> None:
    full_text = _csv_rows(PAPERCLIP / "full_text_manifest.csv")
    assert all(row["verification_status"] in ALLOWED_VERIFICATION for row in full_text)
    ok = {row["pmcid"]: row for row in full_text if row["verification_status"] == "OK"}
    assert set(ok) == set(LIVE_OK)
    for pmcid, (lines, pmid, claim) in LIVE_OK.items():
        assert ok[pmcid]["support_location"] == lines
        assert ok[pmcid]["pmid"] == pmid
        assert ok[pmcid]["claim"] == claim

    fqhc = next(row for row in full_text if row["pmcid"] == "PMC8942056")
    assert fqhc["verification_status"] == "unverified"
    assert fqhc["full_text_status"] == "verifier_error"

    matrix = (ROOT / "docs/methods/evidence_matrix.md").read_text(encoding="utf-8")
    assert "Investigator review: **pending**" in matrix
    assert "| gap |" in matrix
    assert "Gate 2 status: **pending investigator review**" in matrix
    assert "PMC5013936 | Paperclip L6 and L12" in matrix
    assert "PMC8942056" in matrix and "verifier error" in matrix

    exported = _csv_rows(PAPERCLIP / "verified_corpus.csv")
    assert {row["paper_id"] for row in exported} == set(LIVE_OK)
    exported_by_id = {row["paper_id"]: row for row in exported}
    for pmcid, (_, _, claim) in LIVE_OK.items():
        assert exported_by_id[pmcid]["annotations"] == claim
    for suffix in ("bib", "md"):
        text = (PAPERCLIP / f"verified_corpus.{suffix}").read_text(encoding="utf-8")
        assert all(pmcid in text for pmcid in LIVE_OK)
        assert "PMC8942056" not in text
    markdown = (PAPERCLIP / "verified_corpus.md").read_text(encoding="utf-8")
    assert "`L6,L12`" in markdown


def test_paperclip_workflow_manifest_reconciles_all_theme_maps() -> None:
    rows = _csv_rows(PAPERCLIP / "paperclip_workflow_manifest.csv")
    assert len(rows) == 45
    assert {row["theme"] for row in rows} == set(WORKFLOW)
    assert all(row["theme_query"] and row["search_id"] and row["map_id"] for row in rows)
    assert all(row["candidate_pmcid"].startswith("PMC") for row in rows)
    for search_id in {row["search_id"] for row in rows}:
        search_rows = [row for row in rows if row["search_id"] == search_id]
        assert len(search_rows) == 5
        assert len({row["candidate_pmcid"] for row in search_rows}) == 5
        assert len({row["theme_query"] for row in search_rows}) == 1
        assert len({row["map_id"] for row in search_rows}) == 1
    for theme, (query, search_id, map_id) in WORKFLOW.items():
        theme_rows = [row for row in rows if row["theme"] == theme]
        assert {row["theme_query"] for row in theme_rows} == {query}
        assert {row["search_id"] for row in theme_rows} == {search_id}
        assert {row["map_id"] for row in theme_rows} == {map_id}
    status_counts = {
        status: sum(row["map_status"] == status for row in rows)
        for status in {row["map_status"] for row in rows}
    }
    assert status_counts == {"success": 41, "timeout": 4}
    assert {row["candidate_pmcid"] for row in rows if row["map_status"] == "timeout"} == {
        "PMC10894218",
        "PMC6902479",
        "PMC12459141",
        "PMC11210632",
    }


def test_tavily_failure_is_preserved_exactly() -> None:
    rows = _csv_rows(ROOT / "sources/literature/tool_failures.csv")
    assert any(
        row["tool"] == "Tavily MCP"
        and row["failure_code"] == "monthly_cap_reached_bonus_eligible"
        and row["date"] == "2026-07-14"
        for row in rows
    )
