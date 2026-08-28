"""Disclosure-safe view models for the Gate 3 review notebook."""

from __future__ import annotations

import json
from collections.abc import Mapping
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]


class QualityCheckpointError(ValueError):
    """The disclosure-safe checkpoint is missing or internally inconsistent."""


SCHEMA_METRICS = (
    "tables",
    "field_positions",
    "verified_positions",
    "unverified_positions",
    "analysis_usable_tables",
)


def _nonnegative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise QualityCheckpointError(f"{label} must be a nonnegative integer")
    return value


def _validate_checkpoint(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise QualityCheckpointError("quality checkpoint must be a JSON object")
    for key in ("source_id", "snapshot_id"):
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            raise QualityCheckpointError(f"{key} must be a nonempty string")
    if payload.get("gate_3_status") != "closed":
        raise QualityCheckpointError("review notebook requires a closed Gate 3 checkpoint")
    if _nonnegative_integer(payload.get("source_rows_read"), "source_rows_read") != 0:
        raise QualityCheckpointError("review checkpoint must record zero source rows read")

    evidence = payload.get("schema_evidence")
    if not isinstance(evidence, dict) or set(evidence) != set(SCHEMA_METRICS):
        raise QualityCheckpointError("schema_evidence has an unexpected shape")
    counts = {key: _nonnegative_integer(evidence[key], key) for key in SCHEMA_METRICS}
    if counts["verified_positions"] + counts["unverified_positions"] != counts["field_positions"]:
        raise QualityCheckpointError(
            "verified and unverified positions must sum to field positions"
        )
    if counts["analysis_usable_tables"] > counts["tables"]:
        raise QualityCheckpointError("analysis-usable tables cannot exceed tables")

    findings = payload.get("findings")
    if not isinstance(findings, list) or not findings:
        raise QualityCheckpointError("closed checkpoint must contain at least one finding")
    for finding in findings:
        if not isinstance(finding, dict):
            raise QualityCheckpointError("each finding must be an object")
        if set(finding) != {"code", "severity", "message", "affected_row_count"}:
            raise QualityCheckpointError("finding has an unexpected shape")
        if finding["severity"] not in {"fatal", "warning"}:
            raise QualityCheckpointError("finding severity must be fatal or warning")
        for key in ("code", "message"):
            if not isinstance(finding[key], str) or not finding[key]:
                raise QualityCheckpointError(f"finding {key} must be a nonempty string")
        _nonnegative_integer(finding["affected_row_count"], "affected_row_count")
    if not any(finding["severity"] == "fatal" for finding in findings):
        raise QualityCheckpointError("closed checkpoint must contain a fatal finding")
    return payload


def load_quality_checkpoint(path: Path) -> dict[str, Any]:
    """Load and validate a frozen disclosure-safe quality checkpoint."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, JSONDecodeError) as error:
        raise QualityCheckpointError("quality checkpoint is missing or invalid JSON") from error
    return _validate_checkpoint(payload)


def guard_review_paths(report_path: Path, decision_path: Path, project_root: Path) -> None:
    """Confine notebook input and output to disclosure-safe repository storage."""

    root = project_root.resolve()
    canonical_quality_root = root / "outputs" / "quality"
    quality_root = canonical_quality_root.resolve()
    if quality_root != canonical_quality_root:
        raise QualityCheckpointError(
            "repository outputs/quality must resolve to its canonical lexical location"
        )
    resolved_paths = tuple(candidate.resolve() for candidate in (report_path, decision_path))
    for resolved in resolved_paths:
        if resolved == quality_root or not resolved.is_relative_to(quality_root):
            raise QualityCheckpointError(
                "review paths must be strictly inside repository outputs/quality; "
                "source or raw-data storage and external paths are forbidden"
            )
    if resolved_paths[0] == resolved_paths[1]:
        raise QualityCheckpointError("quality report and Gate 3 decision paths must differ")


def schema_evidence_view(checkpoint: Mapping[str, Any]) -> pd.DataFrame:
    """Return ordered schema-evidence counts without reading source data."""

    payload = _validate_checkpoint(dict(checkpoint))
    evidence = payload["schema_evidence"]
    records = [{"metric": metric, "value": evidence[metric]} for metric in SCHEMA_METRICS]
    records.append({"metric": "source_rows_read", "value": payload["source_rows_read"]})
    return pd.DataFrame.from_records(records, columns=["metric", "value"])


def findings_view(checkpoint: Mapping[str, Any]) -> pd.DataFrame:
    """Return the checkpoint findings in stable source order."""

    payload = _validate_checkpoint(dict(checkpoint))
    columns = ["code", "severity", "message", "affected_row_count"]
    return pd.DataFrame.from_records(payload["findings"], columns=columns)


def review_sections_view(checkpoint: Mapping[str, Any]) -> pd.DataFrame:
    """State which planned reviews were possible without semantic source access."""

    _validate_checkpoint(dict(checkpoint))
    records = [
        {
            "section": "source inventory",
            "status": "checkpoint only",
            "basis": "table count from the frozen schema-evidence checkpoint",
        },
        {
            "section": "schema and field evidence",
            "status": "blocked",
            "basis": "semantic field positions remain unverified",
        },
    ]
    unavailable = (
        "denominator checks",
        "suppression and zero audit",
        "coverage and reliability",
        "demographic representation",
        "age-adjustment feasibility",
        "candidate-condition coverage",
    )
    records.extend(
        {
            "section": section,
            "status": "not evaluated",
            "basis": "requires owner-verified semantic fields; zero source rows were read",
        }
        for section in unavailable
    )
    return pd.DataFrame.from_records(records, columns=["section", "status", "basis"])


def gate_3_decision(checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    """Build the deterministic machine-readable Gate 3 decision."""

    payload = _validate_checkpoint(dict(checkpoint))
    return {
        "decision_version": 1,
        "source_id": payload["source_id"],
        "snapshot_id": payload["snapshot_id"],
        "gate": "Gate 3",
        "status": "closed",
        "source_rows_read": 0,
        "schema_evidence": {
            metric: payload["schema_evidence"][metric] for metric in SCHEMA_METRICS
        },
        "blocker_codes": sorted(
            finding["code"] for finding in payload["findings"] if finding["severity"] == "fatal"
        ),
        "blocked_analyses": [
            "disease candidate scoring",
            "analysis-ready EHR publication",
            "confirmatory modeling",
        ],
        "decision_basis": "schema evidence checkpoint; no source rows or values read",
    }


def write_gate_3_decision(path: Path, decision: Mapping[str, Any]) -> None:
    """Write a byte-stable decision artifact outside source storage."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(decision), indent=2, sort_keys=True) + "\n", encoding="utf-8")
