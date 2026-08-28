"""Offline orchestration for reproducible source and evidence checkpoints."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq  # type: ignore[import-untyped]

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.external.normalize import normalize_all_public
from chicagohealthmap.ingest.schemas import load_schema_catalog
from chicagohealthmap.provenance.lineage import build_project_provenance, verify_project_provenance
from chicagohealthmap.sources.registry import load_registry
from chicagohealthmap.sources.snapshot import sha256_file


class RebuildError(ValueError):
    """The offline rebuild cannot safely complete."""


@dataclass(frozen=True)
class RebuildReport:
    """Disclosure-safe summary of an offline rebuild through Phase 4."""

    through_phase: int
    offline: bool
    gates: dict[str, str]
    blocked_analyses: tuple[str, ...]
    row_counts: dict[str, int]
    schema_hashes: dict[str, str]
    provenance_hashes: dict[str, str]
    provenance_artifacts: tuple[str, ...]
    registry_source_count: int
    first_party_schema_evidence: dict[str, int]

    def to_jsonable(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable payload without local absolute paths."""

        return asdict(self)


def _relative_hashes(root: Path, paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file() or path.is_symlink():
            raise RebuildError(f"expected rebuild artifact is missing or unsafe: {path.name}")
        hashes[path.relative_to(root).as_posix()] = sha256_file(path)
    return hashes


def _first_party_schema_evidence(root: Path) -> dict[str, int]:
    catalog = load_schema_catalog(root / "config" / "first_party_schemas.yml")
    fields = [field for table in catalog.tables.values() for field in table.fields]
    verified = sum(field.evidence_status.value == "verified" for field in fields)
    usable = sum(table.analysis_usable for table in catalog.tables.values())
    return {
        "tables": len(catalog.tables),
        "field_positions": len(fields),
        "verified_positions": verified,
        "unverified_positions": len(fields) - verified,
        "analysis_usable_tables": usable,
    }


def _gate_3_status(paths: ProjectPaths, schema_evidence: dict[str, int]) -> str:
    decision_path = paths.outputs / "quality" / "gate_3_decision.json"
    if decision_path.is_file() and not decision_path.is_symlink():
        try:
            payload = json.loads(decision_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise RebuildError("Gate 3 decision artifact is invalid JSON") from error
        if payload.get("status") == "closed" and payload.get("source_rows_read") == 0:
            return "closed"
    if schema_evidence["unverified_positions"] or schema_evidence["analysis_usable_tables"] == 0:
        return "closed"
    return "eligible_for_review"


def _processed_row_counts(paths: ProjectPaths) -> dict[str, int]:
    counts: dict[str, int] = {}
    for parquet in sorted((paths.processed / "public").glob("*.parquet")):
        if parquet.is_symlink():
            raise RebuildError(f"processed artifact is unsafe: {parquet.name}")
        counts[parquet.stem] = pq.ParquetFile(parquet).metadata.num_rows
    if not counts:
        raise RebuildError("offline rebuild produced no processed public tables")
    return counts


def rebuild_through_phase_4(root: Path, offline: bool = True) -> RebuildReport:
    """Rebuild and verify Phase 4 public-data/provenance artifacts without network access."""

    if not offline:
        raise ValueError("offline=False is not authorized without a future explicit plan")

    paths = ProjectPaths.from_root(root)
    if not (paths.root / "pyproject.toml").is_file():
        raise RebuildError("root is not a ChicagoHealthMap repository")
    registry = load_registry(paths.root / "config" / "source_registry.yml")
    schema_evidence = _first_party_schema_evidence(paths.root)

    normalization = normalize_all_public(paths)
    build_project_provenance(paths)
    verify_project_provenance(paths)

    processed_schemas = sorted((paths.processed / "public").glob("*.schema.json"))
    provenance_paths = sorted(path for path in paths.provenance.glob("*") if path.is_file())
    provenance_artifacts = tuple(path.name for path in provenance_paths if path.is_file())
    row_counts = dict(sorted(normalization.row_counts.items()))
    processed_row_counts = _processed_row_counts(paths)
    rebuilt_row_counts = {
        dataset: processed_row_counts.get(dataset, -1) for dataset in row_counts
    }
    if row_counts != rebuilt_row_counts:
        raise RebuildError("processed row counts changed after provenance verification")

    gate_3_status = _gate_3_status(paths, schema_evidence)
    gate_4_status = "passed"
    blocked_analyses = (
        "novelty and interpretation claims pending Gate 2 investigator review",
        "disease candidate scoring pending Gate 3 field semantics",
        "analysis-ready EHR publication pending Gate 3 field semantics",
        "confirmatory modeling pending Gate 2 and Gate 3",
    )
    return RebuildReport(
        through_phase=4,
        offline=True,
        gates={"Gate 2": "open", "Gate 3": gate_3_status, "Gate 4": gate_4_status},
        blocked_analyses=blocked_analyses,
        row_counts=row_counts,
        schema_hashes=_relative_hashes(paths.root, processed_schemas),
        provenance_hashes=_relative_hashes(paths.root, provenance_paths),
        provenance_artifacts=tuple(sorted(provenance_artifacts)),
        registry_source_count=len(registry.sources),
        first_party_schema_evidence=schema_evidence,
    )
