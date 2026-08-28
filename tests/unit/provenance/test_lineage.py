from pathlib import Path

import pandas as pd
import pytest

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.external.normalize import EXPECTED_PUBLIC_DATASETS
from chicagohealthmap.provenance import lineage as lineage_module
from chicagohealthmap.provenance.lineage import (
    build_project_provenance,
    LineageError,
    LineageRecord,
    TableFigureSource,
    verify_artifact_references,
    verify_materialized_datasets,
    verify_lineage_matches_field_maps,
    verify_inventory_sources,
    verify_project_provenance,
    verify_processed_fields,
    write_provenance_reports,
)


def _lineage(field: str = "model_based_estimate") -> LineageRecord:
    return LineageRecord(
        output_dataset="cdc_places_current_tract",
        output_field=field,
        transformation_function="normalize_places",
        transformation_version="1",
        input_dataset="illinois_census_tracts.csv",
        input_field="bphigh_crudeprev",
        source_id="cdc_places_current_tract",
        snapshot_id="cdc_places_current_tract_2026-07-13",
        evidence_decision_reference="config/source_registry.yml#cdc_places_current_tract",
    )


def test_processed_fields_must_all_have_field_level_lineage() -> None:
    verify_processed_fields({"cdc_places_current_tract": {"model_based_estimate"}}, [_lineage()])
    with pytest.raises(LineageError, match="confidence_interval"):
        verify_processed_fields(
            {"cdc_places_current_tract": {"model_based_estimate", "confidence_interval"}},
            [_lineage()],
        )


def test_table_figure_sources_must_reference_registered_artifacts() -> None:
    reference = TableFigureSource(
        artifact_id="table_1", artifact_type="table", dataset_id="cdc_places_current_tract"
    )
    verify_artifact_references([reference], {"cdc_places_current_tract"})
    with pytest.raises(LineageError, match="unregistered"):
        verify_artifact_references([reference], {"other"})


def test_provenance_reports_are_deterministic(tmp_path: Path) -> None:
    paths = write_provenance_reports(
        tmp_path,
        inventory=[
            {
                "source_id": "cdc_places_current_tract",
                "snapshot_id": "cdc_places_current_tract_2026-07-13",
            }
        ],
        lineage=[_lineage()],
        artifact_sources=[],
    )
    first = {path.name: path.read_bytes() for path in paths}
    paths = write_provenance_reports(
        tmp_path,
        inventory=[
            {
                "source_id": "cdc_places_current_tract",
                "snapshot_id": "cdc_places_current_tract_2026-07-13",
            }
        ],
        lineage=[_lineage()],
        artifact_sources=[],
    )
    assert {path.name: path.read_bytes() for path in paths} == first
    assert {path.name for path in paths} == {
        "data_source_inventory.csv",
        "variable_lineage.csv",
        "table_figure_sources.csv",
    }


def test_materialized_dataset_verification_fails_on_empty_or_missing_schema(tmp_path: Path) -> None:
    with pytest.raises(LineageError, match="missing processed dataset.*places"):
        verify_materialized_datasets(tmp_path, {"places"})

    (tmp_path / "places.parquet").write_bytes(b"not read for inventory check")
    with pytest.raises(LineageError, match="missing schema metadata.*places"):
        verify_materialized_datasets(tmp_path, {"places"})


def test_lineage_verification_rejects_normalized_name_as_invented_raw_field() -> None:
    frame = pd.DataFrame(
        {
            "source_id": ["cdc_places_current_tract"],
            "snapshot_id": ["cdc_places_current_tract_2026-07-13"],
            "source_field_map": ['{"estimate":"bphigh_crudeprev"}'],
            "estimate": [31.2],
        }
    )
    false_lineage = [_lineage("estimate")]
    false_lineage[0] = LineageRecord(**{**false_lineage[0].__dict__, "input_field": "estimate"})
    with pytest.raises(LineageError, match="false input field.*bphigh_crudeprev"):
        verify_lineage_matches_field_maps("cdc_places_current_tract", frame, false_lineage)


def test_project_verification_fails_when_destructive_copy_has_all_parquet_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    monkeypatch.setattr(lineage_module, "verify_public_provenance", lambda _paths: None)
    with pytest.raises(LineageError, match="missing processed dataset"):
        verify_project_provenance(paths)


def test_project_build_fails_before_reading_when_one_declared_dataset_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    paths.processed.joinpath("public").mkdir(parents=True)
    missing = "tract_community_overlay_2024"
    for dataset in EXPECTED_PUBLIC_DATASETS - {missing}:
        (paths.processed / "public" / f"{dataset}.parquet").write_bytes(b"placeholder")
        (paths.processed / "public" / f"{dataset}.schema.json").write_text("{}")
    monkeypatch.setattr(lineage_module, "verify_public_provenance", lambda _paths: None)
    with pytest.raises(LineageError, match=f"missing processed dataset: {missing}"):
        build_project_provenance(paths)


@pytest.mark.parametrize(
    "missing",
    [
        "capricorn_chicagohealthmap_export_2026_05_27",
        "chicagohealthmap_website_methods",
    ],
)
def test_inventory_verification_requires_each_first_party_snapshot(missing: str) -> None:
    required = {
        "public_source",
        "capricorn_chicagohealthmap_export_2026_05_27",
        "chicagohealthmap_website_methods",
    }
    inventory = pd.DataFrame({"source_id": sorted(required - {missing})})
    with pytest.raises(LineageError, match=missing):
        verify_inventory_sources(inventory, required)
