from __future__ import annotations

import json
from pathlib import Path

import pytest

from chicagohealthmap.quality.views import (
    QualityCheckpointError,
    findings_view,
    gate_3_decision,
    guard_review_paths,
    load_quality_checkpoint,
    review_sections_view,
    schema_evidence_view,
    write_gate_3_decision,
)


@pytest.fixture
def closed_checkpoint() -> dict[str, object]:
    return {
        "source_id": "capricorn_chicagohealthmap_export_2026_05_27",
        "snapshot_id": "capricorn_chicagohealthmap_export_2026_05_27_2026-05-27",
        "gate_3_status": "closed",
        "source_rows_read": 0,
        "schema_evidence": {
            "tables": 21,
            "field_positions": 549,
            "verified_positions": 0,
            "unverified_positions": 549,
            "analysis_usable_tables": 0,
        },
        "findings": [
            {
                "code": "unverified_schema",
                "severity": "fatal",
                "message": "semantic field contracts are not fully evidence-verified",
                "affected_row_count": 0,
            }
        ],
    }


def test_schema_evidence_view_preserves_disclosure_safe_counts(
    closed_checkpoint: dict[str, object],
) -> None:
    frame = schema_evidence_view(closed_checkpoint)

    assert frame.to_dict("records") == [
        {"metric": "tables", "value": 21},
        {"metric": "field_positions", "value": 549},
        {"metric": "verified_positions", "value": 0},
        {"metric": "unverified_positions", "value": 549},
        {"metric": "analysis_usable_tables", "value": 0},
        {"metric": "source_rows_read", "value": 0},
    ]


def test_findings_view_exposes_only_machine_readable_findings(
    closed_checkpoint: dict[str, object],
) -> None:
    frame = findings_view(closed_checkpoint)

    assert frame.to_dict("records") == [
        {
            "code": "unverified_schema",
            "severity": "fatal",
            "message": "semantic field contracts are not fully evidence-verified",
            "affected_row_count": 0,
        }
    ]


def test_review_sections_remain_not_evaluated_when_no_rows_were_read(
    closed_checkpoint: dict[str, object],
) -> None:
    frame = review_sections_view(closed_checkpoint)

    assert frame["section"].tolist() == [
        "source inventory",
        "schema and field evidence",
        "denominator checks",
        "suppression and zero audit",
        "coverage and reliability",
        "demographic representation",
        "age-adjustment feasibility",
        "candidate-condition coverage",
    ]
    assert frame["status"].tolist() == [
        "checkpoint only",
        "blocked",
        "not evaluated",
        "not evaluated",
        "not evaluated",
        "not evaluated",
        "not evaluated",
        "not evaluated",
    ]


def test_gate_3_decision_stays_closed_and_names_blocked_analyses(
    closed_checkpoint: dict[str, object],
) -> None:
    decision = gate_3_decision(closed_checkpoint)

    assert decision == {
        "decision_version": 1,
        "source_id": "capricorn_chicagohealthmap_export_2026_05_27",
        "snapshot_id": "capricorn_chicagohealthmap_export_2026_05_27_2026-05-27",
        "gate": "Gate 3",
        "status": "closed",
        "source_rows_read": 0,
        "schema_evidence": {
            "tables": 21,
            "field_positions": 549,
            "verified_positions": 0,
            "unverified_positions": 549,
            "analysis_usable_tables": 0,
        },
        "blocker_codes": ["unverified_schema"],
        "blocked_analyses": [
            "disease candidate scoring",
            "analysis-ready EHR publication",
            "confirmatory modeling",
        ],
        "decision_basis": "schema evidence checkpoint; no source rows or values read",
    }


def test_checkpoint_loader_rejects_inconsistent_or_analysis_claiming_payloads(
    tmp_path: Path, closed_checkpoint: dict[str, object]
) -> None:
    closed_checkpoint["source_rows_read"] = 1
    path = tmp_path / "quality.json"
    path.write_text(json.dumps(closed_checkpoint), encoding="utf-8")

    with pytest.raises(QualityCheckpointError, match="zero source rows"):
        load_quality_checkpoint(path)


def test_decision_writer_is_deterministic(
    tmp_path: Path, closed_checkpoint: dict[str, object]
) -> None:
    destination = tmp_path / "gate_3_decision.json"

    write_gate_3_decision(destination, gate_3_decision(closed_checkpoint))
    first = destination.read_bytes()
    write_gate_3_decision(destination, gate_3_decision(closed_checkpoint))

    assert destination.read_bytes() == first
    assert first.endswith(b"\n")


def test_review_paths_reject_repository_source_storage(tmp_path: Path) -> None:
    root = tmp_path / "project"
    report = root / "outputs" / "quality" / "ehr_quality.json"

    with pytest.raises(QualityCheckpointError, match="source or raw-data storage"):
        guard_review_paths(report, root / "sources" / "decision.json", root)

    with pytest.raises(QualityCheckpointError, match="source or raw-data storage"):
        guard_review_paths(root / "data" / "raw" / "quality.json", root / "out.json", root)


def test_review_paths_require_strict_quality_directory_containment(tmp_path: Path) -> None:
    root = tmp_path / "project"
    quality = root / "outputs" / "quality"
    report = quality / "ehr_quality.json"

    with pytest.raises(QualityCheckpointError, match="strictly inside"):
        guard_review_paths(report, quality, root)

    with pytest.raises(QualityCheckpointError, match="strictly inside"):
        guard_review_paths(tmp_path / "external.json", quality / "decision.json", root)

    with pytest.raises(QualityCheckpointError, match="must differ"):
        guard_review_paths(report, report, root)


@pytest.mark.parametrize("target_name", ["root", "sources", "sibling", "external"])
def test_review_paths_reject_any_symlinked_quality_storage_root(
    tmp_path: Path, target_name: str
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "outputs").mkdir()
    targets = {
        "root": root,
        "sources": root / "sources",
        "sibling": root / "sibling",
        "external": tmp_path / "external",
    }
    target = targets[target_name]
    target.mkdir(exist_ok=True)
    (root / "outputs" / "quality").symlink_to(target, target_is_directory=True)
    quality = root / "outputs" / "quality"

    with pytest.raises(QualityCheckpointError, match="canonical lexical location"):
        guard_review_paths(quality / "report.json", quality / "decision.json", root)
