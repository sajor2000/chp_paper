"""Disclosure-safe readiness assessment for scientific gate progression."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from chicagohealthmap.governance.s5_scorecard import (
    S5ScorecardError,
    validate_s5_reconciliation_draft_payload,
)


class ReadinessError(ValueError):
    """Governance readiness evidence is missing or invalid."""


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    """Machine-readable non-authorizing readiness report."""

    through: str
    analysis_authorized: bool
    results_authorized: bool
    gates: dict[str, dict[str, Any]]
    blocked_actions: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""

        return asdict(self)


def _safe_file(root: Path, relative_path: str) -> Path:
    path = root / relative_path
    if path.is_symlink():
        raise ReadinessError(f"readiness evidence is a symlink: {relative_path}")
    if not path.is_file():
        raise ReadinessError(f"readiness evidence is missing: {relative_path}")
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError) as error:
        raise ReadinessError(f"readiness evidence escapes repository: {relative_path}") from error
    return path


def _read_json(root: Path, relative_path: str) -> dict[str, Any]:
    path = _safe_file(root, relative_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as error:
        raise ReadinessError(f"readiness evidence is invalid JSON: {relative_path}") from error
    if not isinstance(payload, dict):
        raise ReadinessError(f"readiness evidence must be an object: {relative_path}")
    return payload


def _read_optional_json(root: Path, relative_path: str) -> dict[str, Any] | None:
    try:
        return _read_json(root, relative_path)
    except ReadinessError:
        return None


def _read_csv(root: Path, relative_path: str) -> list[dict[str, str]]:
    path = _safe_file(root, relative_path)
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except csv.Error as error:
        raise ReadinessError(f"readiness evidence is malformed CSV: {relative_path}") from error
    if not rows or not rows[0]:
        raise ReadinessError(f"readiness evidence CSV is empty: {relative_path}")
    return rows


def _validate_approval(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"human", "date", "decision"}:
        raise ReadinessError(f"{label} approval is invalid")
    human = value.get("human")
    raw_date = value.get("date")
    if (
        not isinstance(human, str)
        or not human.strip()
        or human != human.strip()
        or not isinstance(raw_date, str)
        or raw_date != raw_date.strip()
        or value.get("decision") != "approved"
    ):
        raise ReadinessError(f"{label} approval is invalid")
    try:
        date.fromisoformat(raw_date)
    except ValueError as error:
        raise ReadinessError(f"{label} approval date is invalid") from error
    return {"human": human, "date": raw_date, "decision": "approved"}


def _safe_relative_file(root: Path, relative_path: str, label: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() in {"", "."}:
        raise ReadinessError(f"{label} path is invalid")
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ReadinessError(f"{label} path must not use symlinks")
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        raise ReadinessError(f"{label} path is missing") from None
    if not resolved.is_file():
        raise ReadinessError(f"{label} path is missing")
    return resolved


def _validate_s5_approval(
    root: Path, expected_candidates: tuple[tuple[str, str], ...]
) -> dict[str, Any] | None:
    record = _read_optional_json(root, "outputs/governance/case_selection.json")
    if record is None:
        return None
    if (
        set(record) != {"record_type", "gate", "status", "outcome_blinded", "cases", "approval"}
        or record.get("record_type") != "outcome_blinded_case_selection"
        or record.get("gate") != "S5"
        or record.get("status") != "approved"
        or record.get("outcome_blinded") is not True
    ):
        raise ReadinessError("S5 approval record is invalid")
    cases = record.get("cases")
    if not isinstance(cases, list) or len(cases) != len(expected_candidates):
        raise ReadinessError("S5 approval cases are invalid")
    parsed_cases: list[dict[str, Any]] = []
    for expected_order, (expected_case_id, expected_display_name) in enumerate(
        expected_candidates, start=1
    ):
        raw = cases[expected_order - 1]
        if not isinstance(raw, dict) or set(raw) != {"order", "case_id", "display_name"}:
            raise ReadinessError("S5 approval case fields are invalid")
        if (
            raw.get("order") != expected_order
            or raw.get("case_id") != expected_case_id
            or raw.get("display_name") != expected_display_name
        ):
            raise ReadinessError("S5 approval case order is invalid")
        parsed_cases.append(
            {
                "order": expected_order,
                "case_id": expected_case_id,
                "display_name": expected_display_name,
            }
        )
    return {
        "status": "approved",
        "approval_record_path": "outputs/governance/case_selection.json",
        "cases": tuple(parsed_cases),
        "case_ids": tuple(case_id for case_id, _ in expected_candidates),
        "approval": _validate_approval(record.get("approval"), "S5"),
    }


def _validate_signed_sap(root: Path, expected_case_ids: tuple[str, ...]) -> dict[str, Any]:
    record = _read_json(root, "outputs/governance/signed_sap.json")
    if (
        set(record)
        != {"record_type", "status", "version", "path", "sha256", "case_ids", "approval"}
        or record.get("record_type") != "signed_statistical_analysis_plan"
        or record.get("status") != "signed"
        or not isinstance(record.get("version"), str)
        or not record["version"].strip()
        or record.get("case_ids") != list(expected_case_ids)
    ):
        raise ReadinessError("S6 signed SAP record is invalid")
    digest = record.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ReadinessError("S6 signed SAP checksum is invalid")
    sap_path = _safe_relative_file(root, str(record.get("path", "")), "S6 signed SAP")
    if sha256(sap_path.read_bytes()).hexdigest() != digest:
        raise ReadinessError("S6 signed SAP checksum is invalid")
    approval = _validate_approval(record.get("approval"), "S6 signed SAP")
    return {
        "path": record["path"],
        "version": record["version"],
        "sha256": digest,
        "case_ids": tuple(expected_case_ids),
        "approval": approval,
    }


def _validate_s6_authority(root: Path, s5: dict[str, Any]) -> dict[str, Any]:
    if s5.get("status") != "approved":
        return {
            "status": "blocked",
            "blocked_by": ("S4", "S5"),
            "required_evidence": (
                "signed frozen SAP, study manifest, model shells, sensitivity families, "
                "multiplicity rule, and negative-control decision"
            ),
        }
    record = _read_optional_json(root, "outputs/governance/s6_analysis_authority.json")
    if record is None:
        return {
            "status": "blocked",
            "blocked_by": ("S6 signed analysis authority",),
            "required_evidence": (
                "signed frozen SAP, final variable dictionary, model shells, sensitivity "
                "families, multiplicity rule, and software/version manifest"
            ),
        }
    expected_case_ids = tuple(str(case_id) for case_id in s5.get("case_ids", ()))
    if (
        set(record)
        != {
            "record_type",
            "gate",
            "status",
            "analysis_authorized",
            "results_authorized",
            "case_ids",
            "signed_sap_record",
            "artifacts",
            "approval",
        }
        or record.get("record_type") != "s6_analysis_authority"
        or record.get("gate") != "S6"
        or record.get("status") != "approved"
        or record.get("analysis_authorized") is not True
        or record.get("results_authorized") is not False
        or record.get("case_ids") != list(expected_case_ids)
        or record.get("signed_sap_record") != "outputs/governance/signed_sap.json"
    ):
        raise ReadinessError("S6 analysis authority is invalid")
    signed_sap = _validate_signed_sap(root, expected_case_ids)
    artifacts = record.get("artifacts")
    required_artifacts = {
        "final_variable_dictionary",
        "model_shells",
        "sensitivity_families",
        "multiplicity_rule",
        "software_manifest",
    }
    if not isinstance(artifacts, dict) or set(artifacts) != required_artifacts:
        raise ReadinessError("S6 analysis authority artifacts are invalid")
    for label, raw_path in artifacts.items():
        if not isinstance(raw_path, str):
            raise ReadinessError("S6 analysis authority artifact path is invalid")
        _safe_relative_file(root, raw_path, f"S6 {label}")
    return {
        "status": "approved",
        "analysis_authorized": True,
        "results_authorized": False,
        "case_ids": expected_case_ids,
        "signed_sap": signed_sap,
        "artifacts": {str(key): str(value) for key, value in artifacts.items()},
        "approval": _validate_approval(record.get("approval"), "S6"),
    }


def _gate_2(root: Path) -> dict[str, Any]:
    attestation = _read_json(root, "docs/analysis/gate_2_evidence_packet_attestation.json")
    if (
        attestation.get("gate") != "Gate 2"
        or attestation.get("decision") != "accepted"
        or attestation.get("snapshot_date") != "2026-07-14"
    ):
        raise ReadinessError("Gate 2 evidence packet attestation is invalid")
    screening = _read_csv(root, "sources/literature/pubmed/snapshots/2026-07-14/screening.csv")
    pending = sum(row.get("investigator_review") == "pending" for row in screening)
    return {
        "status": "packet_accepted_screening_pending" if pending else "ready_for_review",
        "evidence_packet_attestation": "accepted",
        "attested_on": attestation["attested_on"],
        "snapshot_date": "2026-07-14",
        "screening_rows": len(screening),
        "pending_screening_decisions": pending,
        "remaining": (
            "complete title/abstract screening, full-text expansion, "
            "comparator/novelty adjudication, and evidence-matrix acceptance"
        ),
    }


def _gate_3(root: Path) -> dict[str, Any]:
    decision = _read_json(root, "outputs/quality/gate_3_decision.json")
    schema = decision.get("schema_evidence", {})
    unverified = schema.get("unverified_positions", 549)
    usable = schema.get("analysis_usable_tables", 0)
    return {
        "status": "closed" if decision.get("status") == "closed" else "open",
        "unverified_positions": unverified,
        "analysis_usable_tables": usable,
        "remaining": (
            "data-owner verification of phenotype, numerator, denominator, "
            "suppression, reliability, capture, geography, and time semantics"
        ),
    }


def _s4(root: Path) -> dict[str, Any]:
    try:
        packet = _read_json(root, "docs/analysis/s4_methods_mapping.json")
    except ReadinessError:
        return {
            "status": "blocked",
            "blocked_by": ("S4 methods dictionary mapping packet",),
            "required_evidence": (
                "accepted ChicagoHealthMap website methods dictionary and candidate field mapping"
            ),
        }
    position_mappings = packet.get("position_mappings", {})
    guarded = {
        name
        for name, mapping in position_mappings.items()
        if isinstance(mapping, dict) and str(mapping.get("status", "")).endswith("_guarded")
    }
    has_case_frame = packet.get("case_study_spatial_frame", {}).get("frame") == "City of Chicago"
    has_core_positions = all(
        concept in position_mappings
        for concept in ("geography", "time_period", "phenotype", "numerator", "capture_rate")
    )
    blocked_by: tuple[str, ...]
    if has_case_frame and has_core_positions:
        status = "methods_dictionary_accepted_position_mapping_guarded"
        blocked_by = (
            "adult-denominator reconstruction guard",
            "subgroup block audit",
            "S6 authorization",
        )
        required_evidence = (
            "complete denominator/subgroup audit, S5 outcome-blinded case scoring, and S6 "
            "signed SAP before final analytic dataset or confirmatory modeling"
        )
        position_mapping_status = "partial_guarded" if guarded else "accepted"
    else:
        status = "methods_dictionary_accepted_mapping_pending"
        blocked_by = ("candidate position mapping acceptance",)
        required_evidence = (
            "accept exact source positions for phenotype, numerator, denominator, suppression, "
            "reliability, capture, geography, and time semantics"
        )
        position_mapping_status = "pending"
    return {
        "status": status,
        "methods_dictionary_status": packet.get("status", "unknown"),
        "analysis_authorized": bool(packet.get("analysis_authorized")) is True,
        "case_study_spatial_frame": packet.get("case_study_spatial_frame", {}).get("frame"),
        "position_mapping_status": position_mapping_status,
        "guarded_concepts": tuple(sorted(guarded)),
        "blocked_by": blocked_by,
        "required_evidence": required_evidence,
    }


def _s5(root: Path, s4_status: str) -> dict[str, Any]:
    try:
        scorecard = _read_json(root, "docs/analysis/s5_case_selection_scorecard.json")
    except ReadinessError:
        return {
            "status": "blocked",
            "blocked_by": ("S4", "outcome-blinded candidate scoring"),
            "required_evidence": (
                "investigator approval of outcome-blinded case-study candidate scores"
            ),
        }
    if (
        scorecard.get("record_type") != "outcome_blinded_case_selection_scorecard_template"
        or scorecard.get("gate") != "S5"
        or scorecard.get("status") != "scorecard_template_ready"
        or scorecard.get("outcome_blinded") is not True
        or scorecard.get("results_authorized") is not False
        or scorecard.get("analysis_authorized") is not False
    ):
        raise ReadinessError("S5 scorecard template is invalid")
    scoring = scorecard.get("scoring_domains")
    candidates = scorecard.get("candidate_shells")
    if not isinstance(scoring, list) or len(scoring) != 8:
        raise ReadinessError("S5 scorecard scoring domains are invalid")
    if not isinstance(candidates, list) or len(candidates) != 2:
        raise ReadinessError("S5 scorecard candidate shells are invalid")
    expected_candidates = tuple(
        (str(candidate.get("case_id", "")), str(candidate.get("display_name", "")))
        for candidate in candidates
    )
    approved = _validate_s5_approval(root, expected_candidates)
    if approved is not None:
        return {
            "status": "approved",
            "scorecard_status": scorecard["status"],
            "approval_record_path": approved["approval_record_path"],
            "case_ids": approved["case_ids"],
            "cases": approved["cases"],
            "approval": approved["approval"],
            "s4_dependency_status": s4_status,
            "blocked_by": ("S6 authorization",),
            "required_evidence": (
                "signed S6 analysis authority before confirmatory modeling, final analytic "
                "dataset construction, or the combined marimo case-study notebook"
            ),
        }
    worksheet_status = "not_built"
    try:
        worksheets = _read_json(root, "docs/analysis/s5_blinded_scoring_artifacts.json")
    except ReadinessError:
        worksheets = {}
    if worksheets:
        if (
            worksheets.get("record_type") != "outcome_blinded_s5_scoring_artifacts_template"
            or worksheets.get("gate") != "S5"
            or worksheets.get("status") != "worksheets_ready_reconciliation_pending"
            or worksheets.get("outcome_blinded") is not True
            or worksheets.get("results_authorized") is not False
        ):
            raise ReadinessError("S5 blinded scoring artifacts are invalid")
        raw_worksheets = worksheets.get("scorer_worksheets")
        reconciliation = worksheets.get("reconciliation_template")
        approval = worksheets.get("approval_record_format")
        if (
            not isinstance(raw_worksheets, list)
            or len(raw_worksheets) != 2
            or not isinstance(reconciliation, dict)
            or reconciliation.get("status") != "pending_reconciliation"
            or not isinstance(approval, dict)
            or approval.get("destination") != "outputs/governance/case_selection.json"
        ):
            raise ReadinessError("S5 worksheet structure is invalid")
        worksheet_status = str(worksheets["status"])
    try:
        draft_payload = _read_json(
            root, "outputs/governance/case_selection_reconciliation_draft.json"
        )
    except ReadinessError:
        draft_payload = {}
    if draft_payload:
        try:
            draft = validate_s5_reconciliation_draft_payload(draft_payload)
        except S5ScorecardError as error:
            raise ReadinessError("S5 reconciliation draft is invalid") from error
        return {
            "status": "reconciled_pending_human_approval",
            "scorecard_status": scorecard["status"],
            "worksheet_status": worksheet_status,
            "reconciliation_status": draft.status,
            "results_authorized": draft.results_authorized,
            "approval_record_path": draft.approval_record_path,
            "s4_dependency_status": s4_status,
            "candidate_shells": tuple(candidate.get("case_id", "") for candidate in candidates),
            "blocked_by": (
                "signed S5 portfolio decision",
                "S6 authorization",
            ),
            "required_evidence": (
                "human approval record at outputs/governance/case_selection.json before "
                "outcome linkage or downstream analysis"
            ),
        }
    return {
        "status": "scorecard_template_ready_scoring_pending",
        "scorecard_status": scorecard["status"],
        "worksheet_status": worksheet_status,
        "s4_dependency_status": s4_status,
        "candidate_shells": tuple(candidate.get("case_id", "") for candidate in candidates),
        "blocked_by": (
            "two independent blinded scores",
            "reconciled scorecard",
            "signed S5 portfolio decision",
            "S6 authorization",
        ),
        "required_evidence": (
            "two independent blinded scores, original/reconciled records, fixed anchors, "
            "and signed portfolio decision before outcome linkage"
        ),
    }


def assess_readiness(root: Path, *, through: str = "S6") -> ReadinessReport:
    """Assess Gate 2/S4-S6 readiness without authorizing analysis."""

    if through != "S6":
        raise ReadinessError("only --through S6 is currently supported")
    resolved_root = root.resolve()
    if not (resolved_root / "pyproject.toml").is_file():
        raise ReadinessError("root is not a ChicagoHealthMap repository")
    gate_2 = _gate_2(resolved_root)
    gate_3 = _gate_3(resolved_root)
    s4 = _s4(resolved_root)
    s5 = _s5(resolved_root, str(s4.get("status", "unknown")))
    s6 = _validate_s6_authority(resolved_root, s5)
    analysis_authorized = s6.get("status") == "approved"
    gates = {
        "Gate 2": gate_2,
        "Gate 3": gate_3,
        "S4": s4,
        "S5": s5,
        "S6": s6,
    }
    return ReadinessReport(
        through=through,
        analysis_authorized=analysis_authorized,
        results_authorized=False,
        gates=gates,
        blocked_actions=(
            ("no Results prose before S7", "no manuscript drafting before result freeze")
            if analysis_authorized
            else (
                "no confirmatory modeling",
                "no Results prose",
                "no case promotion",
                "no final analytic dataset",
                "no combined marimo case-study notebook",
            )
        ),
    )
