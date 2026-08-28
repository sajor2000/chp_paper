"""Artifact naming, provenance, and checksum helpers for analytic datasets."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LEGACY_DATASET_ID = "chicago_case_studies_analytic"
ASSEMBLY_MANIFEST_SCHEMA_VERSION = 1


class AnalyticDatasetError(ValueError):
    """Raised when the analytic dataset cannot be built reproducibly."""


@dataclass(frozen=True, slots=True)
class AnalyticDatasetArtifacts:
    """Paths written by the analytic dataset builder."""

    parquet_path: Path
    csv_path: Path
    schema_path: Path
    lineage_path: Path
    manifest_path: Path
    source_join_manifest_path: Path | None = None
    data_book_csv_path: Path | None = None
    data_book_html_path: Path | None = None

    @property
    def required_paths(self) -> tuple[Path, ...]:
        """Return every configured artifact required for checksum-safe reuse."""

        paths = (
            self.parquet_path,
            self.csv_path,
            self.schema_path,
            self.lineage_path,
            self.manifest_path,
            self.source_join_manifest_path,
            self.data_book_csv_path,
            self.data_book_html_path,
        )
        return tuple(path for path in paths if path is not None)


@dataclass(frozen=True, slots=True)
class DatasetBuildDecision:
    """A deterministic record of whether a dataset was built or reused."""

    artifacts: AnalyticDatasetArtifacts
    action: str
    reason: str


def sha256_file(path: Path) -> str:
    """Hash a file without buffering the complete artifact in memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validated_output_stem(value: str) -> str:
    """Reject output stems that could escape the requested output directory."""

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value):
        raise ValueError("output_stem must contain only letters, numbers, underscores, or hyphens")
    return value


def artifact_paths(output_dir: Path, output_stem: str) -> AnalyticDatasetArtifacts:
    """Resolve the complete governed artifact set for an output stem."""

    manifest_name = (
        "study_manifest.json"
        if output_stem == LEGACY_DATASET_ID
        else f"{output_stem}_manifest.json"
    )
    return AnalyticDatasetArtifacts(
        parquet_path=output_dir / f"{output_stem}.parquet",
        csv_path=output_dir / f"{output_stem}.csv",
        schema_path=output_dir / f"{output_stem}.schema.json",
        lineage_path=output_dir / f"{output_stem}_lineage.csv",
        manifest_path=output_dir / manifest_name,
        source_join_manifest_path=output_dir / f"{output_stem}_source_join_manifest.json",
        data_book_csv_path=output_dir / f"{output_stem}_data_book.csv",
        data_book_html_path=output_dir / f"{output_stem}_data_book.html",
    )


def source_join_contract(
    root: Path,
    source_id: str,
    dataset_id: str,
    first_party_inputs: tuple[Path, ...],
) -> dict[str, Any]:
    """Describe every source byte stream and governed join used by the builder."""

    source_specs = (
        (
            source_id,
            "direct_ehr_diagnosed_measure",
            tuple((relative, True) for relative in first_party_inputs),
        ),
        (
            "chicago_health_atlas",
            "community_area_outcome",
            (
                (Path("data/processed/public/chicago_health_atlas_life_expectancy.parquet"), False),
                (Path("data/processed/public/chicago_health_atlas_mortality.parquet"), False),
            ),
        ),
        (
            "us_census_acs",
            "community_area_adjustment",
            (
                (Path("data/processed/public/census_acs_2024_community_area_covariates.parquet"), True),
                (Path("data/processed/public/chicago_community_areas_current.parquet"), False),
                (Path("data/processed/public/census_tiger_2024_tract.parquet"), False),
                (Path("data/processed/public/tract_community_overlay_2024.parquet"), False),
            ),
        ),
        (
            "cdc_places",
            "tract_public_comparator",
            ((Path("data/processed/public/cdc_places_current_tract.parquet"), False),),
        ),
    )
    sources = []
    for source_name, role, inputs in source_specs:
        records = []
        for relative, required in inputs:
            path = root / relative
            exists = path.is_file()
            records.append(
                {
                    "path": relative.as_posix(),
                    "required": required,
                    "exists": exists,
                    "sha256": sha256_file(path) if exists else None,
                }
            )
        sources.append(
            {
                "source_id": source_name,
                "role": role,
                "path": records[0]["path"],
                "sha256": records[0]["sha256"],
                "inputs": records,
            }
        )
    return {
        "dataset_id": dataset_id,
        "sources": sources,
        "joins": [
            {"name": "community_context", "keys": ["geography_id"], "validation": "many_to_one"},
            {"name": "community_area_adjustment", "keys": ["community_area_id"], "validation": "many_to_one"},
            {
                "name": "health_atlas_outcome",
                "keys": ["geography_id", "time_period"],
                "validation": "many_to_one",
            },
            {
                "name": "places_tract_comparator",
                "keys": ["geography_id", "public_comparator_measure_id"],
                "validation": "many_to_one",
            },
        ],
    }


def source_inputs_match(root: Path, sources: object) -> bool:
    """Confirm that source presence and hashes match a recorded contract."""

    if not isinstance(sources, list):
        return False
    try:
        records = [item for source in sources for item in source["inputs"]]
        for record in records:
            path = root / str(record["path"])
            exists = path.is_file()
            if exists != bool(record["exists"]):
                return False
            if bool(record["required"]) and not exists:
                return False
            if exists and sha256_file(path) != record.get("sha256"):
                return False
    except (KeyError, TypeError):
        return False
    return True
