from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.config import PROJECT_ROOT_ENV
from chicagohealthmap.literature.screening import (
    BATCH_COLUMNS,
    ScreeningWorkbenchError,
    build_screening_batches,
    validate_screening_batches,
)


ROOT = Path(__file__).parents[2]
SNAPSHOT_DATE = "2026-07-14"


def _copy_pubmed_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "fixture"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
    for relative in [
        "sources/literature/pubmed/snapshots/2026-07-14/records.csv",
        "sources/literature/pubmed/snapshots/2026-07-14/screening.csv",
    ]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], columns: list[str] | None = None) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_build_screening_batches_creates_index_and_twelve_batches(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"

    report = build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=100)

    assert report.status == "ready_for_investigator_screening"
    assert report.gate_status == "open"
    assert report.records == 1178
    assert report.batches == 12
    assert (output_dir / "screening_index.csv").is_file()
    assert (
        (output_dir / "README.md")
        .read_text(encoding="utf-8")
        .startswith("# PubMed screening workbench")
    )
    first_batch = _read_csv(output_dir / "batch_001.csv")
    assert list(first_batch[0]) == BATCH_COLUMNS
    assert len(first_batch) == 100
    assert first_batch[0]["batch_id"] == "B001"
    assert first_batch[0]["title_abstract_decision"] == ""
    assert first_batch[0]["reviewer"] == ""
    index = _read_csv(output_dir / "screening_index.csv")
    assert len(index) == 12
    assert index[0]["batch_file"] == "batch_001.csv"
    assert len(index[0]["sha256"]) == 64


def test_build_screening_batches_refuses_nonempty_output_without_force(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    output_dir.mkdir(parents=True)
    (output_dir / "keep.txt").write_text("do not overwrite", encoding="utf-8")

    with pytest.raises(ScreeningWorkbenchError, match="refusing to overwrite"):
        build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=100)

    report = build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=100, force=True)
    assert report.batches == 12
    assert not (output_dir / "keep.txt").exists()


def test_validate_screening_batches_reports_pending_blank_decisions(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=500)

    report = validate_screening_batches(root, SNAPSHOT_DATE, output_dir)

    assert report.gate_status == "open"
    assert report.rows == 1178
    assert report.unique_pmids == 1178
    assert report.pending_decisions == 1178
    assert report.included == 0
    assert report.excluded == 0


def test_validate_screening_batches_requires_complete_when_requested(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=500)

    with pytest.raises(ScreeningWorkbenchError, match="blank decisions"):
        validate_screening_batches(root, SNAPSHOT_DATE, output_dir, require_complete=True)


def test_validate_screening_batches_rejects_missing_batch_files(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=500)
    (output_dir / "batch_003.csv").unlink()

    with pytest.raises(ScreeningWorkbenchError, match="missing"):
        validate_screening_batches(root, SNAPSHOT_DATE, output_dir)


def test_validate_screening_batches_rejects_incomplete_pmid_coverage(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=500)
    batch = output_dir / "batch_001.csv"
    rows = _read_csv(batch)
    _write_csv(batch, rows[:-1], BATCH_COLUMNS)

    with pytest.raises(ScreeningWorkbenchError, match="missing expected PMIDs"):
        validate_screening_batches(root, SNAPSHOT_DATE, output_dir)


def test_validate_screening_batches_rejects_later_row_extra_columns(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=500)
    batch = output_dir / "batch_001.csv"
    lines = batch.read_text(encoding="utf-8").splitlines()
    lines[2] = lines[2] + ",unexpected"
    batch.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ScreeningWorkbenchError, match="malformed CSV"):
        validate_screening_batches(root, SNAPSHOT_DATE, output_dir)


def test_validate_screening_batches_rejects_short_rows(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=500)
    batch = output_dir / "batch_001.csv"
    lines = batch.read_text(encoding="utf-8").splitlines()
    lines[2] = ",".join(lines[2].split(",")[:-1])
    batch.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ScreeningWorkbenchError, match="malformed CSV"):
        validate_screening_batches(root, SNAPSHOT_DATE, output_dir)


def test_validate_screening_batches_rejects_duplicate_pmids(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=500)
    batch = output_dir / "batch_001.csv"
    rows = _read_csv(batch)
    rows[1]["pmid"] = rows[0]["pmid"]
    _write_csv(batch, rows, BATCH_COLUMNS)

    with pytest.raises(ScreeningWorkbenchError, match="duplicate PMIDs"):
        validate_screening_batches(root, SNAPSHOT_DATE, output_dir)


def test_validate_screening_batches_rejects_unknown_pmids(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=500)
    batch = output_dir / "batch_001.csv"
    rows = _read_csv(batch)
    rows[0]["pmid"] = "999999999"
    _write_csv(batch, rows, BATCH_COLUMNS)

    with pytest.raises(ScreeningWorkbenchError, match="unknown PMIDs"):
        validate_screening_batches(root, SNAPSHOT_DATE, output_dir)


def test_validate_screening_batches_rejects_invalid_decision(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=500)
    batch = output_dir / "batch_001.csv"
    rows = _read_csv(batch)
    rows[0]["title_abstract_decision"] = "maybe"
    _write_csv(batch, rows, BATCH_COLUMNS)

    with pytest.raises(ScreeningWorkbenchError, match="invalid title/abstract decision"):
        validate_screening_batches(root, SNAPSHOT_DATE, output_dir)


def test_validate_screening_batches_rejects_exclusion_without_reason(tmp_path: Path) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    output_dir = root / "outputs/literature/screening/2026-07-14"
    build_screening_batches(root, SNAPSHOT_DATE, output_dir, batch_size=500)
    batch = output_dir / "batch_001.csv"
    rows = _read_csv(batch)
    rows[0]["title_abstract_decision"] = "exclude"
    rows[0]["exclusion_reason"] = ""
    _write_csv(batch, rows, BATCH_COLUMNS)

    with pytest.raises(ScreeningWorkbenchError, match="exclusion reason"):
        validate_screening_batches(root, SNAPSHOT_DATE, output_dir)


def test_screening_workbench_cli_builds_and_validates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_pubmed_fixture(tmp_path)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))
    output_dir = root / "outputs/literature/screening/2026-07-14"
    runner = CliRunner()

    build = runner.invoke(
        app,
        [
            "evidence",
            "screening",
            "build",
            "--snapshot-date",
            SNAPSHOT_DATE,
            "--batch-size",
            "400",
            "--output-dir",
            str(output_dir),
        ],
    )
    assert build.exit_code == 0
    assert json.loads(build.stdout)["batches"] == 3

    validate = runner.invoke(
        app,
        [
            "evidence",
            "screening",
            "validate",
            "--snapshot-date",
            SNAPSHOT_DATE,
            "--input-dir",
            str(output_dir),
        ],
    )
    assert validate.exit_code == 0
    assert json.loads(validate.stdout)["pending_decisions"] == 1178
