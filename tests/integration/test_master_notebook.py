from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import uuid

import pandas as pd
from matplotlib import image as mpimg
import pytest


def _run(root: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "uv",
            "run",
            str(root / "notebooks/00_master_chicago_healthmap_pipeline.py"),
            "--output-dir",
            output.as_posix(),
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=240,
    )


def _hashes(path: Path) -> dict[str, str]:
    def digest(file: Path) -> str:
        value = sha256()
        with file.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                value.update(chunk)
        return value.hexdigest()

    return {file.name: digest(file) for file in sorted(path.iterdir()) if file.is_file()}


def test_master_notebook_is_deterministic_and_submission_ready(
    request: pytest.FixtureRequest,
) -> None:
    root = Path(__file__).parents[2]
    token = uuid.uuid4().hex
    first = root / "outputs/notebooks" / f"master-test-{token}-first"
    second = root / "outputs/notebooks" / f"master-test-{token}-second"
    request.addfinalizer(lambda: shutil.rmtree(first, ignore_errors=True))
    request.addfinalizer(lambda: shutil.rmtree(second, ignore_errors=True))
    first_run = _run(root, first)
    second_run = _run(root, second)
    assert first_run.returncode == 0, first_run.stderr
    assert second_run.returncode == 0, second_run.stderr
    assert _hashes(first) == _hashes(second)
    manifest = json.loads((first / "notebook_run_manifest.json").read_text())
    governed_hashes = manifest["output_sha256"]
    assert manifest["results_authorized"] is False
    git_status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    expected_dirty = True if git_status.returncode else bool(git_status.stdout.strip())
    expected_binding = (
        "explicit_source_sha256_git_metadata_unavailable"
        if git_status.returncode
        else "git_head_plus_explicit_source_sha256"
    )
    assert manifest["git_dirty"] is expected_dirty
    assert manifest["dirty_source_binding"] == expected_binding
    assert manifest["notebook_path"] == "notebooks/00_master_chicago_healthmap_pipeline.py"
    assert manifest["input_path"] == "00_master_analytic_dataset.parquet"
    assert len(manifest["output_sha256"]) >= 90
    assert "supplement_aggregation_loss.csv" in manifest["output_sha256"]
    assert "supplement_claim_evidence_audit.csv" in manifest["output_sha256"]
    assert "supplement_geographic_resolution_matrix.csv" in manifest["output_sha256"]
    assert "biostatistical_display_review.csv" in manifest["output_sha256"]
    assert manifest["main_display_ids"] == [
        "table_1",
        "figure_1",
        "figure_2",
        "figure_3",
        "table_2",
    ]
    assert set(manifest["main_display_artifacts"]) == set(manifest["main_display_ids"])
    main_artifacts = [
        artifact
        for artifacts in manifest["main_display_artifacts"].values()
        for artifact in artifacts
    ]
    assert len(main_artifacts) == len(set(main_artifacts)) == 10
    assert all((first / artifact).is_file() for artifact in main_artifacts)
    assert all((first / name).is_file() for name in manifest["output_sha256"])
    assert manifest["dataset_build_action"] == "rebuilt"
    assert manifest["dataset_build_reason"] == "required_artifact_missing"
    reload_run = _run(root, first)
    assert reload_run.returncode == 0, reload_run.stderr
    reload_manifest = json.loads((first / "notebook_run_manifest.json").read_text())
    assert reload_manifest["dataset_build_action"] == "reused"
    assert reload_manifest["dataset_build_reason"] == "artifact_and_source_checksums_match"
    assert reload_manifest["output_sha256"] == governed_hashes
    dataset = pd.read_parquet(first / "00_master_analytic_dataset.parquet")
    assert dataset.shape == (20_536, 97)
    assert dataset["geography_type"].value_counts().to_dict() == {
        "census_tract": 18_688,
        "chicago_community_area": 1_848,
    }
    assert dataset["condition_id"].nunique() == 4
    assert sorted(dataset["time_period"].unique()) == [
        "2019",
        "2020",
        "2021",
        "2022",
        "2023",
        "2024",
    ]
    assert not dataset.duplicated(
        ["geography_type", "geography_id", "time_period", "condition_id"]
    ).any()
    assert set(dataset["disease_value_derivation"]) == {
        "direct_first_party_export_not_interpolated"
    }
    assert (first / "00_master_analytic_dataset_data_book.csv").is_file()
    assert (first / "00_master_analytic_dataset_source_join_manifest.json").is_file()
    assert (first / "figure_1_submission.pdf").is_file()
    assert (first / "figure_2_submission.pdf").is_file()
    assert (first / "figure_3_submission.pdf").is_file()
    assert (first / "supplement_coefficient_forest.pdf").is_file()
    assert (first / "supplement_model_diagnostics.pdf").is_file()
    aggregation_loss = pd.read_csv(first / "supplement_aggregation_loss.csv")
    assert len(aggregation_loss) == 4
    assert set(aggregation_loss["condition_id"]) == {"hypertension", "copd"}
    assert set(aggregation_loss["zip_zcta_sensitivity_status"]) == {"direct_zcta_comparison"}
    consequence = pd.read_csv(first / "supplement_geographic_consequence_transitions.csv")
    assert set(consequence["comparison_geography_type"]) == {
        "chicago_community_area",
        "zcta",
    }
    assert not consequence["results_authorized"].any()
    assert not aggregation_loss["results_authorized"].any()
    assert set(aggregation_loss["analysis_status"]) == {"geographic_resolution_sensitivity"}
    table_1 = pd.read_csv(first / "table_1_resource_quality.csv")
    assert table_1.shape == (4, 9)
    assert table_1["Condition-year records, No."].sum() == 1_848
    assert table_1["Community areas represented, No."].eq(77).all()
    assert "CHM condition-record denominator, median (IQR)" in table_1
    table_2 = pd.read_csv(first / "table_2_model_readiness_sensitivities.csv")
    assert table_2["Condition"].tolist() == [
        "Hypertension",
        "Combined diabetes components",
        "COPD",
    ]
    assert table_2["Tract/community eligible tracts, No."].iloc[[0, 2]].tolist() == [722, 411]
    assert pd.isna(table_2["Tract/community eligible tracts, No."].iloc[1])
    assert table_2["Quartile disagreement, No. (%)"].iloc[[0, 2]].tolist() == [
        "255 (35.3)", "206 (50.1)"
    ]
    assert table_2["Quartile disagreement, No. (%)"].iloc[1] == "—"
    assert table_2["Q4 movers, No. (%)"].iloc[[0, 2]].tolist() == ["76 (10.5)", "101 (24.6)"]
    assert table_2["Q4 movers, No. (%)"].iloc[1] == "—"
    assert not any("Estimate" in column or "Authorization" in column for column in table_2)
    display_review = pd.read_csv(first / "biostatistical_display_review.csv")
    assert len(display_review) == 26
    assert set(display_review.columns) == {
        "Display", "Review result", "Main limitation", "Needed supplement or decision"
    }
    manuscript_narratives = json.loads((first / "manuscript_result_narratives.json").read_text())
    assert manuscript_narratives["manuscript_import_allowed"] is False
    assert all(
        set(manuscript_narratives[model]) == {"status", "manuscript_import_allowed", "narrative"}
        for model in ("C1", "C2")
    )
    claims = pd.read_csv(first / "supplement_claim_evidence_audit.csv")
    assert set(claims["claim_id"]) == {"C1", "C2", "GR"}
    assert not claims["authorization"].any()
    c1 = claims.loc[claims["claim_id"].eq("C1")].iloc[0]
    assert pd.isna(c1["estimate"]) and pd.isna(c1["ci_low"]) and pd.isna(c1["ci_high"])
    contents = json.loads((first / "supplement_table_of_contents.json").read_text())
    assert "numbered_manuscript_displays" in contents
    assert "machine_readable_reproducibility_files" in contents
    figure_qa = json.loads((first / "figure_qa.json").read_text())
    assert figure_qa["status"] == "passed_automated_render_and_accessibility_smoke_check"
    assert figure_qa["accessibility"]["simulations_generated"] == [
        "grayscale",
        "protanopia",
        "deuteranopia",
    ]
    assert figure_qa["accessibility"]["manual_inspection_status"] == (
        "manual_inspection_required_for_current_output_hashes"
    )
    palette_simulations = figure_qa["accessibility"]["palette_simulations"]
    assert set(palette_simulations) == {"cividis", "RdBu_r", "categorical"}
    assert all(
        metric["minimum_pairwise_rgb_distance"] > 0.05
        for palette in palette_simulations.values()
        for metric in palette.values()
    )
    secondary = figure_qa["accessibility"]["secondary_encodings_verified"]
    assert all(details["passed"] for details in secondary.values())
    assert secondary["categorical_hatching"]["status"] == (
        "not_applicable_no_categorical_main_map_fill"
    )
    assert "//" in secondary["transition_hatching"]["observed"]
    assert secondary["quartile_matrix_annotations"]["observed"] == 32
    assert secondary["stability_marker_shapes"]["observed_vertex_counts"]
    for name, qa in figure_qa["figures"].items():
        image = mpimg.imread(first / name)
        assert image.shape[:2] == (qa["pixel_height"], qa["pixel_width"])
        assert image.shape[1] >= 1400
        assert image.shape[0] >= 550
        assert float(image.std()) > 0.05
        assert set(qa["simulations"]) == {"grayscale", "protanopia", "deuteranopia"}
        assert all(metric["nonblank"] for metric in qa["simulations"].values())
        assert all(metric["luminance_range"] > 0.5 for metric in qa["simulations"].values())
    narratives = json.loads((first / "manuscript_result_narratives.json").read_text())
    assert narratives["manuscript_import_allowed"] is False
    assert narratives["C1"]["manuscript_import_allowed"] is False
    assert narratives["C2"]["manuscript_import_allowed"] is False
