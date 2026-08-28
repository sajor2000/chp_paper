from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

import chicagohealthmap.analysis.dataset as dataset_module
from chicagohealthmap.cli import app
from chicagohealthmap.analysis.dataset import (
    AnalyticDatasetError,
    AnalyticDatasetArtifacts,
    build_chicago_case_study_dataset,
    build_zcta_sidecar_dataset,
    ensure_chicago_case_study_dataset,
    ensure_zcta_sidecar_dataset,
)


def test_analytic_dataset_artifacts_preserves_legacy_constructor() -> None:
    artifacts = AnalyticDatasetArtifacts(
        Path("dataset.parquet"),
        Path("dataset.csv"),
        Path("dataset.schema.json"),
        Path("dataset_lineage.csv"),
        Path("study_manifest.json"),
    )

    assert len(artifacts.required_paths) == 5
    assert artifacts.source_join_manifest_path is None


def _write_pipe(path: Path, rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join("|".join("" if value is None else str(value) for value in row) for row in rows)
        + "\n",
        encoding="utf-8",
    )


def _condition_row(
    record_id: int,
    geography_id: int,
    year: int,
    condition: str,
    numerator: int,
    denominator: int,
    measure: float,
) -> list[object]:
    row: list[object] = [""] * 67
    row[0] = record_id
    row[1] = geography_id
    row[2] = year
    row[3] = condition
    row[4] = numerator
    row[24] = denominator
    row[44] = measure
    return row


def _make_fixture_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    source = root / "sources/first_party/capricorn/snapshots/2026-05-27/original"
    public = root / "data/processed/public"
    source.mkdir(parents=True)
    public.mkdir(parents=True)

    _write_pipe(
        source / "fact_community_area_condition_stats.text",
        [
            _condition_row(1, 1, 2024, "hypertension", 120, 1000, 12.0),
            _condition_row(2, 1, 2024, "diabetes_with_complication", 8, 1000, 0.8),
            _condition_row(3, 1, 2024, "diabetes_without_complication", 55, 1000, 5.5),
            _condition_row(4, 1, 2024, "COPD", 42, 1000, 4.2),
            _condition_row(5, 1, 2024, "asthma", 99, 1000, 9.9),
        ],
    )
    _write_pipe(
        source / "fact_tract_condition_stats.text",
        [
            _condition_row(11, "17031010100", 2024, "hypertension", 7, 100, 7.0),
            _condition_row(12, "17031010100", 2024, "diabetes_with_complication", 4, 100, 4.0),
            _condition_row(13, "17031010100", 2024, "diabetes_without_complication", 11, 100, 11.0),
            _condition_row(14, "17031010100", 2024, "COPD", 3, 100, 3.0),
            _condition_row(15, "17031999900", 2024, "hypertension", 99, 100, 99.0),
        ],
    )
    _write_pipe(source / "dim_community_areas.text", [[1, "Rogers Park"] + [""] * 15])
    _write_pipe(
        source / "dim_community_area_reliability_crosswalk.text",
        [[1, 0.21, "usable", "aligned", "usable_aligned", "Public reliability note", ""]],
    )
    _write_pipe(
        source / "dim_tract_reliability_crosswalk.text",
        [["17031010100", 0.08, "guarded", "imbalanced", "guarded_imbalanced", "Tract note", ""]],
    )
    _write_pipe(
        source / "fact_zcta_condition_stats.text",
        [
            _condition_row(21, 60601, 2024, "hypertension", 70, 1000, 7.0),
            _condition_row(22, 60601, 2024, "diabetes_with_complication", 20, 1000, 2.0),
            _condition_row(23, 60601, 2024, "diabetes_without_complication", 50, 1000, 5.0),
            _condition_row(24, 60601, 2024, "COPD", 30, 1000, 3.0),
            _condition_row(25, 60601, 2024, "asthma", 90, 1000, 9.0),
        ],
    )
    zcta_geometry = (
        "0103000000010000000500000000000000000000000000000000000000000000000000"
        "F03F0000000000000000000000000000F03F000000000000F03F000000000000000000"
        "0000000000F03F00000000000000000000000000000000"
    )
    _write_pipe(source / "dim_zcta.text", [[60601, "Chicago"] + [""] * 12 + [zcta_geometry, ""]])
    _write_pipe(
        source / "dim_zcta_reliability_crosswalk.text",
        [[60601, 0.12, "usable", "aligned", "usable_aligned", "ZCTA note", ""]],
    )
    (root / "sources/first_party/capricorn/snapshots/2026-05-27/manifest.json").parent.mkdir(
        parents=True, exist_ok=True
    )
    (root / "sources/first_party/capricorn/snapshots/2026-05-27/manifest.json").write_text(
        json.dumps(
            {
                "source_id": "capricorn_chicagohealthmap_export_2026_05_27",
                "snapshot_id": "capricorn_chicagohealthmap_export_2026_05_27_2026-05-27",
                "snapshot_date": "2026-05-27",
                "validation_status": "passed",
                "files": [],
            }
        ),
        encoding="utf-8",
    )

    pd.DataFrame(
        [
            {
                "geography_id": "01",
                "community_area_name": "Rogers Park",
                "geometry_wkt": "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))",
                "source_id": "city_boundaries",
                "snapshot_id": "city_boundaries_snapshot",
            }
        ]
    ).to_parquet(public / "chicago_community_areas_current.parquet")
    pd.DataFrame(
        [
            {
                "community_area_id": "01",
                "total_population": 54173.0,
                "pct_female": 51.45,
                "pct_age_65_plus": 12.63,
                "pct_below_fpl": 17.94,
                "acs_adult_population": 47486.0,
                "pct_female_standard_error": 0.8,
                "pct_female_moe90": 1.316,
                "pct_age_65_plus_standard_error": 0.6,
                "pct_age_65_plus_moe90": 0.987,
                "pct_below_fpl_standard_error": 1.1,
                "pct_below_fpl_moe90": 1.8095,
                "acs_adult_population_standard_error": 500.0,
                "acs_adult_population_moe90": 822.5,
                "uncertainty_status": "available_variance_replicates",
                "source_id": "census_acs_2024_5y_population_weighted_community_area",
                "time_period": "2020-2024",
                "release_vintage": "2024 ACS 5-year",
                "allocation_method": "whole_block_internal_point_then_population_weight",
                "allocation_weight_source": "2020 Census PL 94-171 P1 total population",
                "poverty_universe": "population for whom poverty status is determined (ACS B17001)",
                "boundary_snapshot_id": "city_boundaries_snapshot",
                "boundary_release_vintage": "current",
            }
        ]
    ).to_parquet(public / "census_acs_2024_community_area_covariates.parquet")
    pd.DataFrame(
        [
            {
                "geography_id": "17031010100",
                "community_area_id": "01",
                "weight": 0.62,
                "covered_fraction": 1.0,
                "is_crossing_tract": True,
                "is_sliver": False,
                "source_id": "tract_community_overlay_2024",
                "snapshot_id": "tract_community_overlay_2024_snapshot",
                "boundary_source_id": "chicago_community_areas_current",
                "boundary_snapshot_id": "chicago_community_areas_current_snapshot",
                "tract_vintage": "2024",
            },
            {
                "geography_id": "17031010100",
                "community_area_id": "02",
                "weight": 0.38,
                "covered_fraction": 1.0,
                "is_crossing_tract": True,
                "is_sliver": False,
                "source_id": "tract_community_overlay_2024",
                "snapshot_id": "tract_community_overlay_2024_snapshot",
                "boundary_source_id": "chicago_community_areas_current",
                "boundary_snapshot_id": "chicago_community_areas_current_snapshot",
                "tract_vintage": "2024",
            },
        ]
    ).to_parquet(public / "tract_community_overlay_2024.parquet")
    pd.DataFrame(
        [
            {
                "geography_id": "17031010100",
                "geometry_wkt": "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))",
                "tract_vintage": "2024",
            }
        ]
    ).to_parquet(public / "census_tiger_2024_tract.parquet")
    pd.DataFrame(
        [
            {
                "geography_id": "1714000-1",
                "time_period": "2024",
                "estimate": 77.2,
                "standard_error": 1.1,
            }
        ]
    ).to_parquet(public / "chicago_health_atlas_life_expectancy.parquet")
    pd.DataFrame(
        [
            {
                "geography_id": "1714000-1",
                "time_period": "2020-2024",
                "estimate": 812.0,
                "standard_error": 22.0,
            }
        ]
    ).to_parquet(public / "chicago_health_atlas_mortality.parquet")
    pd.DataFrame(
        [
            {
                "geography_id": "17031010100",
                "time_period": "2023 BRFSS / 2025 release",
                "measure_id": "bphigh_crudeprev",
                "measure_type": "model_based_estimate",
                "model_based_estimate": 25.0,
                "confidence_interval": "(20.0, 30.0)",
            },
            {
                "geography_id": "17031010100",
                "time_period": "2023 BRFSS / 2025 release",
                "measure_id": "diabetes_crudeprev",
                "measure_type": "model_based_estimate",
                "model_based_estimate": 12.0,
                "confidence_interval": "(9.0, 15.0)",
            },
            {
                "geography_id": "17031010100",
                "time_period": "2023 BRFSS / 2025 release",
                "measure_id": "copd_crudeprev",
                "measure_type": "model_based_estimate",
                "model_based_estimate": 6.0,
                "confidence_interval": "(4.0, 8.0)",
            },
        ]
    ).to_parquet(public / "cdc_places_current_tract.parquet")
    return root


def test_zcta_sidecar_preserves_direct_values_and_primary_contract(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"
    primary = build_chicago_case_study_dataset(root=root, output_dir=output_dir)
    primary_before = pd.read_parquet(primary.parquet_path)

    artifacts = build_zcta_sidecar_dataset(root=root, output_dir=output_dir)
    zcta = pd.read_parquet(artifacts.parquet_path)
    manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))

    assert artifacts.parquet_path.name == "chicago_healthmap_zcta_sidecar.parquet"
    assert len(zcta) == 4
    assert set(zcta["geography_type"]) == {"zcta"}
    assert set(zcta["geography_id"]) == {"60601"}
    assert zcta.set_index("condition_id").loc["hypertension", "published_measure_value"] == 7.0
    assert zcta["disease_value_derivation"].eq("direct_first_party_export_not_interpolated").all()
    assert zcta["geometry_wkt"].str.startswith("POLYGON").all()
    assert manifest["source_input_rows"] == 5
    assert manifest["results_authorized"] is False
    pd.testing.assert_frame_equal(primary_before, pd.read_parquet(primary.parquet_path))


def test_zcta_sidecar_reuses_and_rebuilds_on_source_change(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"

    built = ensure_zcta_sidecar_dataset(root=root, output_dir=output_dir)
    reused = ensure_zcta_sidecar_dataset(root=root, output_dir=output_dir)
    source = root / "sources/first_party/capricorn/snapshots/2026-05-27/original"
    fact_path = source / "fact_zcta_condition_stats.text"
    fact_path.write_text(fact_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    rebuilt = ensure_zcta_sidecar_dataset(root=root, output_dir=output_dir)

    assert built.action == "rebuilt"
    assert reused.action == "reused"
    assert rebuilt.action == "rebuilt"
    assert rebuilt.reason == "source_checksum_mismatch"


def test_builder_writes_biostatistician_auditable_dataset_shape(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"

    artifacts = build_chicago_case_study_dataset(root=root, output_dir=output_dir)

    dataset = pd.read_parquet(artifacts.parquet_path)
    assert artifacts.csv_path.is_file()
    assert artifacts.schema_path.is_file()
    assert artifacts.lineage_path.is_file()
    assert artifacts.manifest_path.is_file()
    assert len(dataset) == 8
    assert set(dataset["geography_type"]) == {"chicago_community_area", "census_tract"}
    assert set(dataset["condition_id"]) == {
        "hypertension",
        "diabetes_with_complication",
        "diabetes_without_complication",
        "copd",
    }
    assert set(dataset["case_id"]) == {"cardiometabolic_bundle", "respiratory_copd"}
    assert (
        dataset.duplicated(["geography_type", "geography_id", "time_period", "condition_id"]).sum()
        == 0
    )
    assert dataset["sap_variable_role"].notna().all()
    assert dataset["source_position_contract"].str.contains("S4").all()


def test_builder_preserves_source_diabetes_labels_and_suppression_guardrail(
    tmp_path: Path,
) -> None:
    root = _make_fixture_root(tmp_path)

    artifacts = build_chicago_case_study_dataset(root=root, output_dir=root / "outputs/frozen")

    dataset = pd.read_parquet(artifacts.parquet_path)
    diabetes = dataset[dataset["condition_family"] == "diabetes"].sort_values("condition_id")
    assert diabetes["condition_id"].drop_duplicates().tolist() == [
        "diabetes_with_complication",
        "diabetes_without_complication",
    ]
    assert diabetes["condition_label"].drop_duplicates().tolist() == [
        "diabetes_with_complication",
        "diabetes_without_complication",
    ]
    suppressed = dataset.loc[
        (dataset["geography_type"] == "chicago_community_area")
        & (dataset["condition_id"] == "diabetes_with_complication")
    ].iloc[0]
    assert bool(suppressed["suppression_flag"]) is True
    assert suppressed["suppression_reason"] == "positive_below_public_suppression_threshold"
    assert suppressed["numerator"] == 8


def test_builder_includes_census_tract_sensitivity_layer(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)

    artifacts = build_chicago_case_study_dataset(root=root, output_dir=root / "outputs/frozen")

    dataset = pd.read_parquet(artifacts.parquet_path)
    tracts = dataset[dataset["geography_type"] == "census_tract"]
    assert len(tracts) == 4
    assert set(tracts["geography_level_role"]) == {"sensitivity_spatial_heterogeneity"}
    assert set(tracts["community_area_id"]) == {"01"}
    assert set(tracts["community_area_ids"]) == {"01;02"}
    assert set(tracts["is_crossing_tract"]) == {True}
    assert set(tracts["overlay_row_count"]) == {2}
    assert set(tracts["tract_community_linkage_method"]) == {
        "projected_polygon_intersection_area_weight"
    }
    assert set(tracts["tract_community_linkage_source_id"]) == {"tract_community_overlay_2024"}
    assert set(tracts["tract_community_linkage_role"]) == {
        "geographic_linkage_metadata_only_not_disease_interpolation"
    }
    assert set(tracts["linkage_method"]) == {"projected_polygon_intersection_area_weight"}
    assert set(tracts["linkage_role"]) == {
        "geographic_linkage_metadata_only_not_disease_interpolation"
    }
    assert set(tracts["disease_value_derivation"]) == {"direct_first_party_export_not_interpolated"}
    assert tracts["suppression_flag"].sum() == 3
    assert set(tracts["capture_flag"]) == {"capture_rate_available"}
    assert "17031999900" not in set(dataset["source_geography_id"])


def test_builder_normalizes_public_ids_and_prejoins_comparators_for_notebook(
    tmp_path: Path,
) -> None:
    root = _make_fixture_root(tmp_path)

    artifacts = build_chicago_case_study_dataset(root=root, output_dir=root / "outputs/frozen")

    dataset = pd.read_parquet(artifacts.parquet_path)
    community = dataset[dataset["geography_type"] == "chicago_community_area"]
    tract = dataset[dataset["geography_type"] == "census_tract"]
    assert set(community["geography_id"]) == {"01"}
    assert set(community["source_geography_id"]) == {"1"}
    assert community["life_expectancy_estimate"].notna().all()
    assert community["mortality_estimate"].notna().all()
    assert tract["life_expectancy_estimate"].isna().all()
    assert tract["public_comparator_estimate"].notna().all()
    assert set(tract["public_comparator_role"]) == {"tract_concordance_discordance_comparator"}
    assert set(tract["public_comparator_measure_id"]) == {
        "bphigh_crudeprev",
        "copd_crudeprev",
        "diabetes_crudeprev",
    }


def test_builder_joins_census_covariates_only_to_community_rows(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)

    artifacts = build_chicago_case_study_dataset(root=root, output_dir=root / "outputs/frozen")

    dataset = pd.read_parquet(artifacts.parquet_path)
    community = dataset[dataset["geography_type"] == "chicago_community_area"]
    tract = dataset[dataset["geography_type"] == "census_tract"]
    assert set(community["pct_female"]) == {51.45}
    assert set(community["pct_age_65_plus"]) == {12.63}
    assert set(community["pct_below_fpl"]) == {17.94}
    assert set(community["acs_adult_population"]) == {47486.0}
    assert set(community["census_covariate_uncertainty_status"]) == {
        "available_variance_replicates"
    }
    assert tract["pct_female"].isna().all()


def test_builder_manifest_and_lineage_support_audit_trail(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)

    artifacts = build_chicago_case_study_dataset(root=root, output_dir=root / "outputs/frozen")

    manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(artifacts.schema_path.read_text(encoding="utf-8"))
    lineage = pd.read_csv(artifacts.lineage_path)
    assert manifest["dataset_id"] == "chicago_case_studies_analytic"
    assert manifest["grain"] == "geography_type-geography_id-period-condition"
    assert manifest["primary_key"] == [
        "geography_type",
        "geography_id",
        "time_period",
        "condition_id",
    ]
    assert manifest["geography_levels"] == ["census_tract", "chicago_community_area"]
    assert manifest["analysis_authority"] == "human_approved_s5_s6_unless_catastrophic_blocker"
    assert manifest["city_inclusion_rule"] == (
        "Community-area rows use the direct 77-area ChicagoHealthMap export; tract rows are "
        "limited to direct first-party tract disease rows whose 2024 TIGER tract representative "
        "point is covered by the frozen union of 77 Chicago community areas. The 50% tract-area "
        "rule is retained as a sensitivity definition."
    )
    assert manifest["annual_tract_minimum_denominator"] == 30
    assert manifest["tract_boundary_audit"] == {
        "any_intersection_tracts": 1,
        "area50_sensitivity_tracts": 1,
        "primary_and_area50_tracts": 1,
        "primary_representative_point_tracts": 1,
    }
    assert "chicago_case_studies_analytic.parquet" in manifest["checksums"]
    assert {"column", "source_table", "source_position", "audit_note"}.issubset(lineage.columns)
    assert set(schema["primary_key"]) == {
        "geography_type",
        "geography_id",
        "time_period",
        "condition_id",
    }
    assert "source_condition_label" in {column["name"] for column in schema["columns"]}
    assert "public_comparator_role" in {column["name"] for column in schema["columns"]}
    assert "published_measure_value" in {column["name"] for column in schema["columns"]}


def test_analysis_build_dataset_cli_writes_frozen_artifacts(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"

    result = CliRunner().invoke(
        app,
        [
            "analysis",
            "build-dataset",
            "--root",
            str(root),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["dataset_id"] == "chicago_case_studies_analytic"
    assert payload["row_count"] == 8
    assert (output_dir / "chicago_case_studies_analytic.parquet").is_file()
    assert (output_dir / "study_manifest.json").is_file()


def test_analysis_build_dataset_cli_accepts_optional_output_stem(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"

    result = CliRunner().invoke(
        app,
        [
            "analysis",
            "build-dataset",
            "--root",
            str(root),
            "--output-dir",
            str(output_dir),
            "--output-stem",
            "00_master_analytic_dataset",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["dataset_id"] == "00_master_analytic_dataset"
    assert (output_dir / "00_master_analytic_dataset.parquet").is_file()
    assert (output_dir / "00_master_analytic_dataset_manifest.json").is_file()


def test_builder_accepts_custom_output_stem_and_writes_complete_data_book(
    tmp_path: Path,
) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"

    artifacts = build_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )

    assert artifacts.parquet_path.name == "00_master_analytic_dataset.parquet"
    assert artifacts.csv_path.name == "00_master_analytic_dataset.csv"
    assert artifacts.schema_path.name == "00_master_analytic_dataset.schema.json"
    assert artifacts.lineage_path.name == "00_master_analytic_dataset_lineage.csv"
    assert artifacts.manifest_path.name == "00_master_analytic_dataset_manifest.json"
    assert artifacts.source_join_manifest_path.name == (
        "00_master_analytic_dataset_source_join_manifest.json"
    )
    assert artifacts.data_book_csv_path.name == "00_master_analytic_dataset_data_book.csv"
    assert artifacts.data_book_html_path.name == "00_master_analytic_dataset_data_book.html"

    dataset = pd.read_parquet(artifacts.parquet_path)
    data_book = pd.read_csv(artifacts.data_book_csv_path)
    assert len(data_book) == len(dataset.columns) == 97
    assert set(data_book.columns) == {
        "column",
        "dtype",
        "nullable",
        "non_missing_count",
        "missing_count",
        "source_table",
        "source_position",
        "audit_note",
    }
    assert "<table" in artifacts.data_book_html_path.read_text(encoding="utf-8")


def test_custom_stem_manifest_binds_sources_joins_and_artifact_checksums(
    tmp_path: Path,
) -> None:
    root = _make_fixture_root(tmp_path)
    artifacts = build_chicago_case_study_dataset(
        root=root,
        output_dir=root / "outputs/frozen",
        output_stem="00_master_analytic_dataset",
    )

    manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
    source_join = json.loads(artifacts.source_join_manifest_path.read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == "00_master_analytic_dataset"
    assert manifest["manifest_schema_version"] == 2
    assert manifest["created_at_utc"] == manifest["source_snapshot_at_utc"]
    assert "not_wall_clock" in manifest["created_at_utc_semantics"]
    assert source_join["dataset_id"] == "00_master_analytic_dataset"
    assert {row["source_id"] for row in source_join["sources"]} == {
        "capricorn_chicagohealthmap_export_2026_05_27",
        "chicago_health_atlas",
        "us_census_acs",
        "cdc_places",
    }
    assert {row["role"] for row in source_join["sources"]} == {
        "direct_ehr_diagnosed_measure",
        "community_area_outcome",
        "community_area_adjustment",
        "tract_public_comparator",
    }
    assert all(row["validation"] in {"many_to_one", "one_to_one"} for row in source_join["joins"])
    expected_artifacts = {
        artifacts.parquet_path.name,
        artifacts.csv_path.name,
        artifacts.schema_path.name,
        artifacts.lineage_path.name,
        artifacts.data_book_csv_path.name,
        artifacts.data_book_html_path.name,
    }
    assert set(source_join["artifact_checksums"]) == expected_artifacts
    assert set(manifest["checksums"]) >= expected_artifacts


def test_source_join_manifest_exposes_deterministic_assembly_steps(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    artifacts = build_chicago_case_study_dataset(
        root=root,
        output_dir=root / "outputs/frozen",
        output_stem="00_master_analytic_dataset",
    )

    source_join = json.loads(artifacts.source_join_manifest_path.read_text(encoding="utf-8"))
    steps = source_join["assembly_steps"]

    assert [step["step_id"] for step in steps] == [
        "direct_chm_facts",
        "tract_overlay_linkage",
        "community_acs_covariates",
        "concat_geography_frames",
        "geography_context",
        "health_atlas_outcomes",
        "health_atlas_mortality",
        "places_tract_comparators",
        "derive_flags_lineage",
        "final_key_validation",
    ]
    assert steps[0]["role"] == "direct_first_party_measure"
    assert steps[0]["input_artifacts"]
    assert any(
        "fact_community_area_condition_stats.text" in item["path"]
        for item in steps[0]["input_artifacts"]
    )
    assert {item["path"] for item in steps[1]["input_artifacts"]} == {
        "data/processed/public/tract_community_overlay_2024.parquet"
    }
    assert {item["path"] for item in steps[2]["input_artifacts"]} == {
        "data/processed/public/census_acs_2024_community_area_covariates.parquet"
    }
    assert steps[1]["join_key"] == ["geography_id"]
    assert steps[1]["clinical_values_created"] is False
    assert steps[2]["join_validation"] == "many_to_one"
    assert steps[2]["cardinality"] == "many_to_one"
    assert steps[5]["join_key"] == ["geography_id", "time_period"]
    assert steps[5]["join_validation"] == "many_to_one"
    assert steps[-1]["primary_key"] == [
        "geography_type",
        "geography_id",
        "time_period",
        "condition_id",
    ]
    assert steps[-1]["unique_key"] is True
    for step in steps:
        assert {"input_rows", "output_rows", "excluded_rows", "missing_rows"} <= set(step)


def test_builder_rejects_unsafe_output_stem(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)

    with pytest.raises(ValueError, match="output_stem"):
        build_chicago_case_study_dataset(
            root=root,
            output_dir=root / "outputs/frozen",
            output_stem="../escape",
        )


def test_cli_rejects_unsafe_output_stem(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "analysis",
            "build-dataset",
            "--root",
            str(root),
            "--output-dir",
            str(root / "outputs/frozen"),
            "--output-stem",
            "../escape",
        ],
    )

    assert result.exit_code != 0
    assert "output_stem" in result.output


def test_ensure_dataset_reuses_checksum_matching_build(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"
    built = build_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )
    before = {path: path.stat().st_mtime_ns for path in built.required_paths}

    decision = ensure_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
        rebuild=False,
    )

    assert decision.action == "reused"
    assert decision.reason == "artifact_and_source_checksums_match"
    assert {path: path.stat().st_mtime_ns for path in built.required_paths} == before


def test_ensure_dataset_rebuilds_corrupt_artifact(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"
    built = build_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )
    built.csv_path.write_text("corrupt\n", encoding="utf-8")

    decision = ensure_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )

    assert decision.action == "rebuilt"
    assert decision.reason == "artifact_checksum_mismatch"
    assert len(pd.read_csv(decision.artifacts.csv_path)) == 8


def test_ensure_dataset_rebuilds_when_source_checksum_changes(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"
    build_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )
    source_manifest = root / "sources/first_party/capricorn/snapshots/2026-05-27/manifest.json"
    source_manifest.write_text(
        source_manifest.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    decision = ensure_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )

    assert decision.action == "rebuilt"
    assert decision.reason == "source_checksum_mismatch"


def test_ensure_dataset_rebuilds_when_first_party_fact_changes(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"
    build_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )
    fact = (
        root
        / "sources/first_party/capricorn/snapshots/2026-05-27/original"
        / "fact_community_area_condition_stats.text"
    )
    fact.write_text(fact.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    decision = ensure_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )

    assert decision.action == "rebuilt"
    assert decision.reason == "source_checksum_mismatch"


def test_builder_requires_frozen_boundary_sources_for_primary_tract_membership(
    tmp_path: Path,
) -> None:
    root = _make_fixture_root(tmp_path)
    public = root / "data/processed/public"
    for name in (
        "chicago_community_areas_current.parquet",
        "census_tiger_2024_tract.parquet",
        "cdc_places_current_tract.parquet",
    ):
        (public / name).unlink(missing_ok=True)

    with pytest.raises(AnalyticDatasetError, match="tract city membership requires"):
        build_chicago_case_study_dataset(
            root=root,
            output_dir=root / "outputs/frozen",
            output_stem="00_master_analytic_dataset",
        )


def test_builder_rejects_source_change_during_assembly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"
    original = dataset_module._case_fact_records
    changed = False

    def mutate_after_read(*args: object, **kwargs: object) -> pd.DataFrame:
        nonlocal changed
        result = original(*args, **kwargs)
        if not changed:
            fact = root / dataset_module.FIRST_PARTY_ORIGINAL / dataset_module.TRACT_FACT_TABLE
            fact.write_text(fact.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            changed = True
        return result

    monkeypatch.setattr(dataset_module, "_case_fact_records", mutate_after_read)

    with pytest.raises(AnalyticDatasetError, match="changed while"):
        build_chicago_case_study_dataset(
            root=root,
            output_dir=output_dir,
            output_stem="00_master_analytic_dataset",
        )
    assert not (output_dir / "00_master_analytic_dataset.parquet").exists()


def test_builder_rejects_manifest_change_during_parse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"
    original = dataset_module._source_manifest

    def replace_after_parse(project_root: Path) -> dict[str, object]:
        payload = original(project_root)
        path = project_root / dataset_module.FIRST_PARTY_SNAPSHOT / "manifest.json"
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        return payload

    monkeypatch.setattr(dataset_module, "_source_manifest", replace_after_parse)

    with pytest.raises(AnalyticDatasetError, match="changed while"):
        build_chicago_case_study_dataset(
            root=root,
            output_dir=output_dir,
            output_stem="00_master_analytic_dataset",
        )
    assert not (output_dir / "00_master_analytic_dataset.parquet").exists()


def test_ensure_dataset_honors_explicit_rebuild(tmp_path: Path) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"
    build_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )

    decision = ensure_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
        rebuild=True,
    )

    assert decision.action == "rebuilt"
    assert decision.reason == "explicit_rebuild_requested"


@pytest.mark.parametrize(
    ("artifact_name", "replacement", "reason"),
    [
        ("manifest_path", "{", "manifest_invalid"),
        ("source_join_manifest_path", "{}", "manifest_invalid"),
        (
            "manifest_path",
            json.dumps({"dataset_id": "wrong", "checksums": {}}),
            "manifest_dataset_id_mismatch",
        ),
    ],
)
def test_ensure_dataset_recovers_from_invalid_manifests(
    tmp_path: Path,
    artifact_name: str,
    replacement: str,
    reason: str,
) -> None:
    root = _make_fixture_root(tmp_path)
    output_dir = root / "outputs/frozen"
    artifacts = build_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )
    getattr(artifacts, artifact_name).write_text(replacement, encoding="utf-8")

    decision = ensure_chicago_case_study_dataset(
        root=root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
    )

    assert decision.action == "rebuilt"
    assert decision.reason == reason
    assert all(path.is_file() for path in decision.artifacts.required_paths)
