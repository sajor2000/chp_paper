from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.config import PROJECT_ROOT_ENV
from chicagohealthmap.literature.audit import EvidenceAuditError, audit_gate_2_evidence


ROOT = Path(__file__).parents[2]
SNAPSHOT_DATE = "2026-07-14"


def _copy_evidence_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "fixture"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
    for relative in [
        "config/literature_queries.yml",
        "sources/literature/pubmed/snapshots/2026-07-14/search_manifest.json",
        "sources/literature/pubmed/snapshots/2026-07-14/records.csv",
        "sources/literature/pubmed/snapshots/2026-07-14/screening.csv",
        "sources/literature/paperclip/snapshots/2026-07-14/full_text_manifest.csv",
        "sources/literature/paperclip/snapshots/2026-07-14/paperclip_workflow_manifest.csv",
        "sources/literature/web/snapshots/2026-07-14/chicagohealthmap_data_glossary.json",
        "sources/literature/tool_failures.csv",
    ]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def _rewrite_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_gate_2_audit_reports_open_frozen_evidence_state() -> None:
    report = audit_gate_2_evidence(ROOT, SNAPSHOT_DATE)

    assert report.gate == "Gate 2"
    assert report.status == "open"
    assert report.pubmed["searches"] == 6
    assert report.pubmed["unique_pmids"] == 1178
    assert report.pubmed["metadata_retrieved"] == 1165
    assert report.pubmed["metadata_unavailable"] == 13
    assert report.pubmed["pending_investigator_reviews"] == 1178
    assert report.paperclip["workflow_candidates"] == 45
    assert report.paperclip["successful_maps"] == 41
    assert report.paperclip["timed_out_maps"] == 4
    assert report.paperclip["full_text_rows"] == 9
    assert report.paperclip["verified_ok_claims"] == 6
    assert report.current_web["source_ids"] == ("chicagohealthmap_data_glossary",)
    assert "small_cell_suppression" in report.current_web["concepts"]
    assert "monthly_cap_reached_bonus_eligible" in report.tool_failures["tavily_failure_codes"]
    assert "no confirmatory modeling" in report.blocked_actions


def test_gate_2_audit_cli_outputs_json_and_check_fails() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app, ["evidence", "audit", "--gate", "2", "--snapshot-date", SNAPSHOT_DATE]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["gate"] == "Gate 2"
    assert payload["status"] == "open"

    check = runner.invoke(
        app,
        ["evidence", "audit", "--gate", "2", "--snapshot-date", SNAPSHOT_DATE, "--check"],
    )
    assert check.exit_code == 1
    assert "Gate 2 remains open" in check.stderr


def test_gate_2_audit_rejects_symlinked_artifact(tmp_path: Path) -> None:
    root = _copy_evidence_fixture(tmp_path)
    records = root / "sources/literature/pubmed/snapshots/2026-07-14/records.csv"
    records.unlink()
    records.symlink_to(ROOT / "sources/literature/pubmed/snapshots/2026-07-14/records.csv")

    with pytest.raises(EvidenceAuditError, match="symlink"):
        audit_gate_2_evidence(root, SNAPSHOT_DATE)


def test_gate_2_audit_rejects_mismatched_screening_pmids(tmp_path: Path) -> None:
    root = _copy_evidence_fixture(tmp_path)
    screening = root / "sources/literature/pubmed/snapshots/2026-07-14/screening.csv"
    with screening.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["pmid"] = "999999999"
    _rewrite_csv(screening, rows)

    with pytest.raises(EvidenceAuditError, match="screening rows do not match"):
        audit_gate_2_evidence(root, SNAPSHOT_DATE)


def test_gate_2_audit_rejects_duplicate_record_pmids(tmp_path: Path) -> None:
    root = _copy_evidence_fixture(tmp_path)
    records = root / "sources/literature/pubmed/snapshots/2026-07-14/records.csv"
    with records.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows.append(dict(rows[0]))
    _rewrite_csv(records, rows)

    with pytest.raises(EvidenceAuditError, match="records contain duplicate PMIDs"):
        audit_gate_2_evidence(root, SNAPSHOT_DATE)


def test_gate_2_audit_rejects_duplicate_screening_pmids(tmp_path: Path) -> None:
    root = _copy_evidence_fixture(tmp_path)
    screening = root / "sources/literature/pubmed/snapshots/2026-07-14/screening.csv"
    with screening.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows.append(dict(rows[0]))
    _rewrite_csv(screening, rows)

    with pytest.raises(EvidenceAuditError, match="screening contains duplicate PMIDs"):
        audit_gate_2_evidence(root, SNAPSHOT_DATE)


def test_gate_2_audit_rejects_query_drift(tmp_path: Path) -> None:
    root = _copy_evidence_fixture(tmp_path)
    manifest_path = root / "sources/literature/pubmed/snapshots/2026-07-14/search_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["searches"][0]["original_query"] = "drifted query"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(EvidenceAuditError, match="frozen query mismatch"):
        audit_gate_2_evidence(root, SNAPSHOT_DATE)


def test_gate_2_audit_cli_uses_configured_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_evidence_fixture(tmp_path)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))

    result = CliRunner().invoke(
        app, ["evidence", "audit", "--gate", "2", "--snapshot-date", SNAPSHOT_DATE]
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["pubmed"]["unique_pmids"] == 1178
