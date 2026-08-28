from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.config import PROJECT_ROOT_ENV


def _blocked_root(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    (tmp_path / "config" / "first_party_sources.yml").write_text(
        "source_id: capricorn_chicagohealthmap_export_2026_05_27\n"
        "snapshot_date: '2026-05-27'\n"
        "files: [table.text]\n",
        encoding="utf-8",
    )
    (tmp_path / "config" / "first_party_schemas.yml").write_text(
        "schema_version: 1\n"
        "tables:\n"
        "  table.text:\n"
        "    observed_rows: 1\n"
        "    observed_field_counts: [1]\n"
        "    positional_contract:\n"
        "      count: 1\n"
        "      evidence_status: unverified\n"
        "      evidence_source: owner documentation unavailable\n",
        encoding="utf-8",
    )
    return tmp_path


def test_real_ingest_checkpoint_fails_closed_without_writing_parquet(
    tmp_path: Path, monkeypatch
) -> None:
    root = _blocked_root(tmp_path)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))

    result = CliRunner().invoke(app, ["ehr", "ingest", "--snapshot-date", "2026-05-27"])

    assert result.exit_code == 1
    assert "Gate 3 closed" in result.output
    report = json.loads((root / "outputs" / "quality" / "ehr_quality.json").read_text())
    assert report["gate_3_status"] == "closed"
    assert report["schema_evidence"] == {
        "tables": 1,
        "field_positions": 1,
        "verified_positions": 0,
        "unverified_positions": 1,
        "analysis_usable_tables": 0,
    }
    assert report["findings"][0]["code"] == "unverified_schema"
    assert not list((root / "data" / "interim").rglob("*.parquet"))


def test_quality_checkpoint_writes_disclosure_safe_markdown_and_fails_closed(
    tmp_path: Path, monkeypatch
) -> None:
    root = _blocked_root(tmp_path)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))

    result = CliRunner().invoke(app, ["ehr", "quality", "--snapshot-date", "2026-05-27"])

    assert result.exit_code == 1
    summary = (root / "outputs" / "quality" / "ehr_quality_summary.md").read_text()
    assert "Gate 3: CLOSED" in summary
    assert "No source rows or values were read" in summary
    assert "unverified positions: 1" in summary
