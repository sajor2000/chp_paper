"""Investigator screening workbench for frozen PubMed literature snapshots."""

from __future__ import annotations

import csv
import hashlib
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


BATCH_COLUMNS = [
    "batch_id",
    "batch_sequence",
    "pmid",
    "title",
    "abstract",
    "journal",
    "publication_year",
    "publication_date",
    "query_ids",
    "pubmed_url",
    "title_abstract_decision",
    "exclusion_reason",
    "full_text_required",
    "evidence_use_categories",
    "condition_tags",
    "geography_tags",
    "reviewer",
    "decision_date",
    "adjudication_notes",
]
INDEX_COLUMNS = ["batch_file", "batch_id", "row_count", "first_pmid", "last_pmid", "sha256"]
ALLOWED_DECISIONS = {"include", "exclude", "background", "awaiting_full_text"}
ALLOWED_FULL_TEXT_REQUIRED = {"yes", "no", "unknown", ""}


class ScreeningWorkbenchError(ValueError):
    """Screening workbench inputs or reviewer batches are unsafe or invalid."""


@dataclass(frozen=True, slots=True)
class ScreeningBuildReport:
    """Summary of generated investigator-screening batches."""

    snapshot_date: str
    status: str
    gate: str
    gate_status: str
    records: int
    batches: int
    batch_size: int
    index_path: str
    batch_files: tuple[str, ...]
    blocked_actions: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScreeningValidationReport:
    """Summary of returned investigator-screening batch validation."""

    snapshot_date: str
    gate: str
    gate_status: str
    rows: int
    unique_pmids: int
    pending_decisions: int
    included: int
    excluded: int
    background: int
    awaiting_full_text: int
    require_complete: bool
    blocked_actions: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""

        return asdict(self)


def _blocked_actions() -> tuple[str, ...]:
    return (
        "no novelty assertion",
        "no case promotion",
        "no confirmatory modeling",
        "no analytic dataset or marimo case-study notebook",
    )


def _safe_file(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise ScreeningWorkbenchError(f"{label} is a symlink: {path}")
    if not path.is_file():
        raise ScreeningWorkbenchError(f"{label} is missing: {path}")
    return path


def _safe_directory(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise ScreeningWorkbenchError(f"{label} is a symlink: {path}")
    if not path.is_dir():
        raise ScreeningWorkbenchError(f"{label} is missing: {path}")
    return path


def _read_csv(path: Path, label: str) -> list[dict[str, str]]:
    _safe_file(path, label)
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except csv.Error as error:
        raise ScreeningWorkbenchError(f"{label} is malformed CSV") from error
    if not rows:
        raise ScreeningWorkbenchError(f"{label} is empty")
    if not rows[0]:
        raise ScreeningWorkbenchError(f"{label} has no header")
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ScreeningWorkbenchError(f"{label} is malformed CSV")
    return rows


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_or_posix(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _snapshot_paths(root: Path, snapshot_date: str) -> tuple[Path, Path]:
    if snapshot_date != "2026-07-14":
        raise ScreeningWorkbenchError("only frozen snapshot date 2026-07-14 is currently supported")
    base = root / "sources/literature/pubmed/snapshots" / snapshot_date
    return base / "records.csv", base / "screening.csv"


def _frozen_pubmed_rows(root: Path, snapshot_date: str) -> list[dict[str, str]]:
    records_path, screening_path = _snapshot_paths(root, snapshot_date)
    records = _read_csv(records_path, "PubMed records")
    screening = _read_csv(screening_path, "PubMed screening queue")
    for rows, label in ((records, "PubMed records"), (screening, "PubMed screening queue")):
        pmids = [row.get("pmid", "") for row in rows]
        if any(not pmid for pmid in pmids):
            raise ScreeningWorkbenchError(f"{label} contains blank PMIDs")
        if len(set(pmids)) != len(pmids):
            raise ScreeningWorkbenchError(f"{label} contains duplicate PMIDs")
    record_pmids = {row["pmid"] for row in records}
    screening_pmids = {row["pmid"] for row in screening}
    if record_pmids != screening_pmids:
        raise ScreeningWorkbenchError("PubMed record/screening PMID sets do not match")
    return sorted(records, key=lambda row: int(row["pmid"]))


def _prepare_output_dir(output_dir: Path, force: bool) -> None:
    if output_dir.exists():
        if output_dir.is_symlink() or not output_dir.is_dir():
            raise ScreeningWorkbenchError(f"output directory is unsafe: {output_dir}")
        if any(output_dir.iterdir()):
            if not force:
                raise ScreeningWorkbenchError(
                    f"refusing to overwrite nonempty output directory: {output_dir}"
                )
            shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def _readme_text(snapshot_date: str) -> str:
    return (
        "# PubMed screening workbench\n\n"
        f"Snapshot date: {snapshot_date}\n\n"
        "Gate 2 remains open. These files are reviewer work queues, not completed screening.\n\n"
        "Allowed `title_abstract_decision` values: `include`, `exclude`, `background`, "
        "`awaiting_full_text`, or blank while still pending.\n\n"
        "Use exactly one nonblank `exclusion_reason` when `title_abstract_decision` is "
        "`exclude`. Use `full_text_required` values `yes`, `no`, `unknown`, or blank.\n\n"
        "Do not add protected first-party clinical data to these files.\n"
    )


def build_screening_batches(
    root: Path,
    snapshot_date: str,
    output_dir: Path,
    *,
    batch_size: int,
    force: bool = False,
) -> ScreeningBuildReport:
    """Build deterministic investigator-screening batch CSVs from frozen PubMed records."""

    if batch_size <= 0:
        raise ScreeningWorkbenchError("batch_size must be positive")
    resolved_root = root.resolve()
    records = _frozen_pubmed_rows(resolved_root, snapshot_date)
    _prepare_output_dir(output_dir, force)

    batch_files: list[Path] = []
    index_rows: list[dict[str, str]] = []
    for index, start in enumerate(range(0, len(records), batch_size), start=1):
        batch_records = records[start : start + batch_size]
        batch_id = f"B{index:03d}"
        batch_path = output_dir / f"batch_{index:03d}.csv"
        rows = [
            {
                "batch_id": batch_id,
                "batch_sequence": str(sequence),
                "pmid": row["pmid"],
                "title": row.get("title", ""),
                "abstract": row.get("abstract", ""),
                "journal": row.get("journal", ""),
                "publication_year": row.get("publication_year", ""),
                "publication_date": row.get("publication_date", ""),
                "query_ids": row.get("query_ids", ""),
                "pubmed_url": row.get("pubmed_url", ""),
                "title_abstract_decision": "",
                "exclusion_reason": "",
                "full_text_required": "",
                "evidence_use_categories": "",
                "condition_tags": "",
                "geography_tags": "",
                "reviewer": "",
                "decision_date": "",
                "adjudication_notes": "",
            }
            for sequence, row in enumerate(batch_records, start=1)
        ]
        _write_csv(batch_path, BATCH_COLUMNS, rows)
        batch_files.append(batch_path)
        index_rows.append(
            {
                "batch_file": batch_path.name,
                "batch_id": batch_id,
                "row_count": str(len(rows)),
                "first_pmid": rows[0]["pmid"],
                "last_pmid": rows[-1]["pmid"],
                "sha256": _sha256_file(batch_path),
            }
        )

    index_path = output_dir / "screening_index.csv"
    _write_csv(index_path, INDEX_COLUMNS, index_rows)
    (output_dir / "README.md").write_text(_readme_text(snapshot_date), encoding="utf-8")
    return ScreeningBuildReport(
        snapshot_date=snapshot_date,
        status="ready_for_investigator_screening",
        gate="Gate 2",
        gate_status="open",
        records=len(records),
        batches=len(batch_files),
        batch_size=batch_size,
        index_path=_relative_or_posix(resolved_root, index_path),
        batch_files=tuple(_relative_or_posix(resolved_root, path) for path in batch_files),
        blocked_actions=_blocked_actions(),
    )


def _batch_paths(input_dir: Path) -> list[Path]:
    _safe_directory(input_dir, "screening input directory")
    index_path = input_dir / "screening_index.csv"
    index_rows = _read_csv(index_path, "screening index")
    if list(index_rows[0]) != INDEX_COLUMNS:
        raise ScreeningWorkbenchError("screening index has invalid columns")
    paths: list[Path] = []
    for row in index_rows:
        batch_file = row["batch_file"]
        if not batch_file.startswith("batch_") or Path(batch_file).name != batch_file:
            raise ScreeningWorkbenchError(
                f"screening index contains invalid batch file: {batch_file}"
            )
        path = input_dir / batch_file
        _safe_file(path, "screening batch")
        paths.append(path)
    if not paths:
        raise ScreeningWorkbenchError("screening index contains no batch CSV files")
    return paths


def _validate_batch_header(rows: list[dict[str, str]], path: Path) -> None:
    if list(rows[0]) != BATCH_COLUMNS:
        raise ScreeningWorkbenchError(f"screening batch has invalid columns: {path.name}")


def validate_screening_batches(
    root: Path,
    snapshot_date: str,
    input_dir: Path,
    *,
    require_complete: bool = False,
) -> ScreeningValidationReport:
    """Validate returned investigator-screening batches without closing Gate 2."""

    resolved_root = root.resolve()
    known_pmids = {row["pmid"] for row in _frozen_pubmed_rows(resolved_root, snapshot_date)}
    rows: list[dict[str, str]] = []
    for path in _batch_paths(input_dir):
        batch_rows = _read_csv(path, "screening batch")
        _validate_batch_header(batch_rows, path)
        rows.extend(batch_rows)

    pmids = [row["pmid"] for row in rows]
    if len(set(pmids)) != len(pmids):
        raise ScreeningWorkbenchError("screening batches contain duplicate PMIDs")
    if unknown := sorted(set(pmids) - known_pmids):
        raise ScreeningWorkbenchError(f"screening batches contain unknown PMIDs: {unknown[0]}")
    if missing := sorted(known_pmids - set(pmids)):
        raise ScreeningWorkbenchError(f"screening batches are missing expected PMIDs: {missing[0]}")

    counts = {"": 0, "include": 0, "exclude": 0, "background": 0, "awaiting_full_text": 0}
    for row in rows:
        decision = row["title_abstract_decision"].strip()
        full_text_required = row["full_text_required"].strip()
        exclusion_reason = row["exclusion_reason"].strip()
        if decision == "" and require_complete:
            raise ScreeningWorkbenchError("screening batches contain blank decisions")
        if decision and decision not in ALLOWED_DECISIONS:
            raise ScreeningWorkbenchError(f"invalid title/abstract decision: {decision}")
        if full_text_required not in ALLOWED_FULL_TEXT_REQUIRED:
            raise ScreeningWorkbenchError(f"invalid full_text_required value: {full_text_required}")
        if decision == "exclude" and not exclusion_reason:
            raise ScreeningWorkbenchError("excluded screening rows require an exclusion reason")
        if decision != "exclude" and exclusion_reason:
            raise ScreeningWorkbenchError(
                "exclusion reason is allowed only when decision is exclude"
            )
        counts[decision] += 1

    return ScreeningValidationReport(
        snapshot_date=snapshot_date,
        gate="Gate 2",
        gate_status="open",
        rows=len(rows),
        unique_pmids=len(set(pmids)),
        pending_decisions=counts[""],
        included=counts["include"],
        excluded=counts["exclude"],
        background=counts["background"],
        awaiting_full_text=counts["awaiting_full_text"],
        require_complete=require_complete,
        blocked_actions=_blocked_actions(),
    )
