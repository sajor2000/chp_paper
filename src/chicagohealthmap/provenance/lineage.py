"""Variable- and artifact-level provenance contracts."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping, Set
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.external.normalize import (
    EXPECTED_PUBLIC_DATASETS,
    REQUIRED_PROVENANCE_COLUMNS,
    verify_public_provenance,
)
from chicagohealthmap.provenance.citations import citations_for_project, write_citations
from chicagohealthmap.sources.registry import load_registry


class LineageError(ValueError):
    """Processed fields or published artifacts have incomplete lineage."""


FIRST_PARTY_INVENTORY_SOURCE_IDS = frozenset(
    {
        "capricorn_chicagohealthmap_export_2026_05_27",
        "chicagohealthmap_website_methods",
    }
)


@dataclass(frozen=True)
class LineageRecord:
    output_dataset: str
    output_field: str
    transformation_function: str
    transformation_version: str
    input_dataset: str
    input_field: str
    source_id: str
    snapshot_id: str
    evidence_decision_reference: str

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not value.strip():
                raise LineageError(f"{name} must not be blank")


@dataclass(frozen=True)
class TableFigureSource:
    artifact_id: str
    artifact_type: str
    dataset_id: str


def _mapped_input_pairs(value: str, default_source_id: str) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for item in value.split("|"):
        source_prefix, separator, input_field = item.partition(":")
        if separator and source_prefix.replace("_", "").isalnum():
            pairs.add((source_prefix, input_field))
        else:
            pairs.add((default_source_id, item))
    return pairs


def verify_processed_fields(
    processed_fields: Mapping[str, Set[str]], lineage: Iterable[LineageRecord]
) -> None:
    observed = {(record.output_dataset, record.output_field) for record in lineage}
    missing = sorted(
        (dataset, field)
        for dataset, fields in processed_fields.items()
        for field in fields
        if (dataset, field) not in observed
    )
    if missing:
        rendered = ", ".join(f"{dataset}.{field}" for dataset, field in missing)
        raise LineageError(f"processed fields lack lineage: {rendered}")


def verify_artifact_references(
    references: Iterable[TableFigureSource], registered_datasets: Set[str]
) -> None:
    unregistered = sorted(
        {record.dataset_id for record in references if record.dataset_id not in registered_datasets}
    )
    if unregistered:
        raise LineageError(
            f"artifact references unregistered dataset(s): {', '.join(unregistered)}"
        )


def verify_materialized_datasets(processed_dir: Path, expected: Set[str]) -> None:
    """Require every declared Parquet and schema companion before content verification."""

    for dataset in sorted(expected):
        parquet = processed_dir / f"{dataset}.parquet"
        schema = processed_dir / f"{dataset}.schema.json"
        if not parquet.is_file() or parquet.is_symlink():
            raise LineageError(f"missing processed dataset: {dataset}")
        if not schema.is_file() or schema.is_symlink():
            raise LineageError(f"missing schema metadata: {dataset}")


def verify_inventory_sources(inventory: pd.DataFrame, required_source_ids: Set[str]) -> None:
    if "source_id" not in inventory:
        raise LineageError("data source inventory has no source_id column")
    missing = sorted(required_source_ids - set(inventory["source_id"].astype(str)))
    if missing:
        raise LineageError(f"data source inventory is missing: {', '.join(missing)}")


def verify_lineage_matches_field_maps(
    dataset: str, frame: pd.DataFrame, lineage: Iterable[LineageRecord]
) -> None:
    """Require lineage input fields to equal the persisted row-level source maps."""

    records = list(lineage)
    for (source_id, snapshot_id), rows in frame.groupby(["source_id", "snapshot_id"]):
        expected: dict[str, set[tuple[str, str]]] = {}
        for raw_map in rows["source_field_map"].drop_duplicates():
            try:
                field_map = json.loads(str(raw_map))
            except json.JSONDecodeError as error:
                raise LineageError(f"{dataset} has malformed source_field_map JSON") from error
            if not isinstance(field_map, dict):
                raise LineageError(f"{dataset} source_field_map must be an object")
            for output_field, input_field in field_map.items():
                expected.setdefault(str(output_field), set()).update(
                    _mapped_input_pairs(str(input_field), str(source_id))
                )
        for output_field, expected_inputs in expected.items():
            expected_source_ids = {input_source for input_source, _ in expected_inputs}
            observed_inputs = {
                (record.source_id, record.input_field)
                for record in records
                if record.output_dataset == dataset
                and record.output_field == output_field
                and record.source_id in expected_source_ids
            }
            if observed_inputs != expected_inputs:
                rendered = ", ".join(
                    f"{input_source}:{input_field}"
                    for input_source, input_field in sorted(expected_inputs)
                )
                raise LineageError(
                    f"{dataset}.{output_field} has false input field lineage; expected {rendered}"
                )


def _write_csv(path: Path, rows: list[dict[str, object]], fields: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_provenance_reports(
    output_dir: Path,
    *,
    inventory: Iterable[Mapping[str, object]],
    lineage: Iterable[LineageRecord],
    artifact_sources: Iterable[TableFigureSource],
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory_rows = sorted(
        (dict(row) for row in inventory), key=lambda row: tuple(map(str, row.values()))
    )
    lineage_rows = sorted((asdict(row) for row in lineage), key=lambda row: tuple(row.values()))
    artifact_rows = sorted(
        (asdict(row) for row in artifact_sources), key=lambda row: tuple(row.values())
    )
    inventory_fields = tuple(inventory_rows[0]) if inventory_rows else ("source_id", "snapshot_id")
    lineage_fields = tuple(LineageRecord.__dataclass_fields__)
    artifact_fields = tuple(TableFigureSource.__dataclass_fields__)
    paths = (
        output_dir / "data_source_inventory.csv",
        output_dir / "variable_lineage.csv",
        output_dir / "table_figure_sources.csv",
    )
    _write_csv(paths[0], inventory_rows, inventory_fields)
    _write_csv(paths[1], lineage_rows, lineage_fields)
    _write_csv(paths[2], artifact_rows, artifact_fields)
    return paths


def build_project_provenance(paths: ProjectPaths) -> tuple[Path, ...]:
    """Build citations, inventory, and complete field lineage for materialized public tables."""

    registry = verify_public_provenance(paths)
    verify_materialized_datasets(paths.processed / "public", EXPECTED_PUBLIC_DATASETS)
    parquet_paths = sorted((paths.processed / "public").glob("*.parquet"))
    inventory = [
        {
            "source_id": source.source_id,
            "snapshot_id": f"{source.source_id}_2026-07-13",
            "organization": source.organization,
            "dataset_title": source.dataset_title,
            "release_vintage": source.release,
            "access_date": source.access_date.isoformat(),
            "license": source.license,
            "catalog_id": source.catalog_id or "",
            "citation_id": next(
                item.citation_id
                for item in citations_for_project(paths)
                if item.source_id == source.source_id
            ),
        }
        for source in sorted(registry.sources, key=lambda item: item.source_id)
    ]
    inventory.extend(
        {
            "source_id": citation.source_id,
            "snapshot_id": (
                citation.source_id
                if citation.source_id.startswith("capricorn_")
                else f"{citation.source_id}_2026-07-13"
            ),
            "organization": citation.organization,
            "dataset_title": citation.title,
            "release_vintage": citation.version,
            "access_date": citation.accessed.isoformat(),
            "license": (
                "restricted"
                if citation.source_id.startswith("capricorn_")
                else "public website methods"
            ),
            "catalog_id": citation.catalog_id or "",
            "citation_id": citation.citation_id,
        }
        for citation in citations_for_project(paths)
        if citation.source_id.startswith(("capricorn_", "chicagohealthmap_"))
    )
    records: list[LineageRecord] = []
    processed_fields: dict[str, set[str]] = {}
    for parquet_path in parquet_paths:
        frame = pd.read_parquet(parquet_path)
        dataset = parquet_path.stem
        processed_fields[dataset] = set(frame.columns)
        source_ids = sorted(set(frame["source_id"].astype(str)))
        snapshot_ids = sorted(set(frame["snapshot_id"].astype(str)))
        if not source_ids or not snapshot_ids:
            raise LineageError(f"{dataset} has incomplete source identity")
        for field in frame.columns:
            for source_id in source_ids:
                source_rows = frame.loc[frame["source_id"].astype(str) == source_id]
                source_snapshots = sorted(set(source_rows["snapshot_id"].astype(str)))
                if len(source_snapshots) != 1:
                    raise LineageError(f"{dataset}.{field} has ambiguous snapshot identity")
                input_pairs: set[tuple[str, str]]
                if field in REQUIRED_PROVENANCE_COLUMNS:
                    input_pairs = {(source_id, "provenance contract")}
                else:
                    input_pairs = set()
                    for raw_map in source_rows["source_field_map"].drop_duplicates():
                        field_map = json.loads(str(raw_map))
                        if field not in field_map:
                            raise LineageError(
                                f"{dataset}.{field} is absent from persisted source_field_map"
                            )
                        input_pairs.update(_mapped_input_pairs(str(field_map[field]), source_id))
                transformation = {
                    "cdc_places_current_tract": "normalize_places",
                    "chicago_health_atlas_life_expectancy": "normalize_atlas",
                    "chicago_health_atlas_mortality": "normalize_atlas",
                    "census_acs_2022_5y": "normalize_acs",
                    "census_acs_2024_5y": "normalize_acs",
                }.get(dataset, "normalize_all_public")
                for input_source_id, input_field in sorted(input_pairs):
                    records.append(
                        LineageRecord(
                            output_dataset=dataset,
                            output_field=field,
                            transformation_function=transformation,
                            transformation_version="1",
                            input_dataset="immutable frozen snapshot",
                            input_field=input_field,
                            source_id=input_source_id,
                            snapshot_id=(
                                source_snapshots[0]
                                if input_source_id == source_id
                                else f"{input_source_id}_2026-07-13"
                            ),
                            evidence_decision_reference=(
                                f"config/source_registry.yml#{input_source_id}"
                            ),
                        )
                    )
    verify_processed_fields(processed_fields, records)
    reports = write_provenance_reports(
        paths.provenance, inventory=inventory, lineage=records, artifact_sources=[]
    )
    return (*reports, *write_citations(paths))


def verify_project_provenance(paths: ProjectPaths) -> None:
    """Verify materialized reports remain complete and registered."""

    verify_public_provenance(paths)
    verify_materialized_datasets(paths.processed / "public", EXPECTED_PUBLIC_DATASETS)
    required = {
        "data_source_inventory.csv",
        "variable_lineage.csv",
        "table_figure_sources.csv",
        "data_sources.csl.json",
        "data_sources.bib",
    }
    missing = sorted(name for name in required if not (paths.provenance / name).is_file())
    if missing:
        raise LineageError(f"provenance artifacts are missing: {', '.join(missing)}")
    inventory = pd.read_csv(paths.provenance / "data_source_inventory.csv", dtype=str)
    lineage = pd.read_csv(paths.provenance / "variable_lineage.csv", dtype=str)
    artifacts = pd.read_csv(paths.provenance / "table_figure_sources.csv", dtype=str)
    registered = {
        source.source_id
        for source in load_registry(paths.root / "config/source_registry.yml").sources
    }
    verify_inventory_sources(inventory, registered | set(FIRST_PARTY_INVENTORY_SOURCE_IDS))
    if lineage.empty or lineage.isna().any(axis=None):
        raise LineageError("variable lineage is incomplete")
    lineage_records = [
        LineageRecord(
            **{field: str(getattr(row, field)) for field in LineageRecord.__dataclass_fields__}
        )
        for row in lineage.itertuples(index=False)
    ]
    parquet_paths = sorted((paths.processed / "public").glob("*.parquet"))
    registered_datasets = {path.stem for path in parquet_paths}
    verify_artifact_references(
        [
            TableFigureSource(
                artifact_id=str(row.artifact_id),
                artifact_type=str(row.artifact_type),
                dataset_id=str(row.dataset_id),
            )
            for row in artifacts.itertuples(index=False)
        ],
        registered_datasets,
    )
    try:
        csl = json.loads((paths.provenance / "data_sources.csl.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise LineageError("CSL citation file is invalid") from error
    expected_citations = citations_for_project(paths)
    if (
        not isinstance(csl, list)
        or {item.get("id") for item in csl if isinstance(item, dict)}
        != {item.citation_id for item in expected_citations}
        or any(
            not isinstance(item, dict)
            or item.get("type") != "dataset"
            or not item.get("title")
            or not item.get("URL")
            for item in csl
        )
    ):
        raise LineageError("dataset citations are incomplete")
    bibtex = (paths.provenance / "data_sources.bib").read_text(encoding="utf-8")
    if bibtex.count("@dataset{") != len(expected_citations):
        raise LineageError("BibTeX dataset citations are incomplete")
    for parquet_path in parquet_paths:
        frame = pd.read_parquet(parquet_path)
        fields = set(frame.columns)
        observed = set(lineage.loc[lineage["output_dataset"] == parquet_path.stem, "output_field"])
        if not fields <= observed:
            raise LineageError(f"processed fields lack lineage: {parquet_path.stem}")
        verify_lineage_matches_field_maps(parquet_path.stem, frame, lineage_records)
