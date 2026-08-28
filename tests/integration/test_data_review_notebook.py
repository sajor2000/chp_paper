from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest


def _run_notebook(
    project_root: Path, report: Path, decision: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "uv",
            "run",
            str(project_root / "notebooks" / "01_data_review.py"),
            "--report-path",
            str(report),
            "--decision-path",
            str(decision),
        ],
        cwd=project_root,
        env={**os.environ, "PYTHONHASHSEED": "0"},
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _write_checkpoint(report: Path) -> None:
    report.write_text(
        json.dumps(
            {
                "source_id": "fixture",
                "snapshot_id": "fixture_2026-05-27",
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
                        "message": "schema evidence is unverified",
                        "affected_row_count": 0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_data_review_notebook_writes_closed_gate_decision() -> None:
    project_root = Path(__file__).parents[2]
    fixture_dir = project_root / "outputs" / "quality" / f"pytest-{uuid.uuid4().hex}"
    report = fixture_dir / "ehr_quality.json"
    decision = fixture_dir / "gate_3_decision.json"
    fixture_dir.mkdir(parents=True)
    _write_checkpoint(report)
    try:
        completed = _run_notebook(project_root, report, decision)
        assert completed.returncode == 0, completed.stderr
        assert json.loads(decision.read_text()) == {
            "blocked_analyses": [
                "disease candidate scoring",
                "analysis-ready EHR publication",
                "confirmatory modeling",
            ],
            "blocker_codes": ["unverified_schema"],
            "decision_basis": "schema evidence checkpoint; no source rows or values read",
            "decision_version": 1,
            "gate": "Gate 3",
            "schema_evidence": {
                "analysis_usable_tables": 0,
                "field_positions": 549,
                "tables": 21,
                "unverified_positions": 549,
                "verified_positions": 0,
            },
            "snapshot_id": "fixture_2026-05-27",
            "source_id": "fixture",
            "source_rows_read": 0,
            "status": "closed",
        }
    finally:
        shutil.rmtree(fixture_dir)


def test_notebook_source_does_not_touch_raw_exports_or_sources() -> None:
    project_root = Path(__file__).parents[2]
    source = (project_root / "notebooks" / "01_data_review.py").read_text()

    assert "sources/" not in source
    assert "data/raw" not in source
    assert "read_csv" not in source
    assert "read_parquet" not in source


def test_data_review_notebook_rejects_a_source_storage_destination() -> None:
    project_root = Path(__file__).parents[2]
    checkpoint = project_root / "outputs" / "quality" / "ehr_quality.json"
    forbidden = project_root / "sources" / "gate_3_decision.json"

    completed = _run_notebook(project_root, checkpoint, forbidden)

    assert completed.returncode != 0
    assert not forbidden.exists()


def test_data_review_notebook_rejects_direct_external_output(tmp_path: Path) -> None:
    project_root = Path(__file__).parents[2]
    checkpoint = project_root / "outputs" / "quality" / "ehr_quality.json"
    forbidden = tmp_path / "gate_3_decision.json"
    forbidden.write_bytes(b"external sentinel\n")

    completed = _run_notebook(project_root, checkpoint, forbidden)

    assert completed.returncode != 0
    assert forbidden.read_bytes() == b"external sentinel\n"


def test_data_review_notebook_rejects_symlink_output_escape(tmp_path: Path) -> None:
    project_root = Path(__file__).parents[2]
    checkpoint = project_root / "outputs" / "quality" / "ehr_quality.json"
    fixture_dir = project_root / "outputs" / "quality" / f"pytest-{uuid.uuid4().hex}"
    external = tmp_path / "external"
    external.mkdir()
    fixture_dir.mkdir(parents=True)
    escape = fixture_dir / "escape"
    escape.symlink_to(external, target_is_directory=True)
    forbidden = escape / "gate_3_decision.json"
    forbidden.write_bytes(b"symlink sentinel\n")
    try:
        completed = _run_notebook(project_root, checkpoint, forbidden)
        assert completed.returncode != 0
        assert (external / "gate_3_decision.json").read_bytes() == b"symlink sentinel\n"
    finally:
        shutil.rmtree(fixture_dir)


@pytest.mark.parametrize("quality_target", ["root", "sources"])
def test_data_review_notebook_rejects_symlinked_quality_root(
    tmp_path: Path, quality_target: str
) -> None:
    project_root = Path(__file__).parents[2]
    fake_root = tmp_path / "fake-project"
    fake_notebooks = fake_root / "notebooks"
    fake_outputs = fake_root / "outputs"
    fake_notebooks.mkdir(parents=True)
    fake_outputs.mkdir()
    shutil.copy2(project_root / "notebooks" / "01_data_review.py", fake_notebooks)
    target = fake_root if quality_target == "root" else fake_root / "sources"
    target.mkdir(exist_ok=True)
    (fake_outputs / "quality").symlink_to(target, target_is_directory=True)
    report = fake_outputs / "quality" / "ehr_quality.json"
    decision = fake_outputs / "quality" / "gate_3_decision.json"
    _write_checkpoint(report)
    decision.write_bytes(b"internal sentinel\n")

    completed = subprocess.run(
        [
            "uv",
            "run",
            str(fake_notebooks / "01_data_review.py"),
            "--report-path",
            str(report),
            "--decision-path",
            str(decision),
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert completed.returncode != 0
    assert decision.read_bytes() == b"internal sentinel\n"
