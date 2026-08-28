from __future__ import annotations

from hashlib import sha256
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from matplotlib import image as mpimg
import pandas as pd
import pytest
import numpy as np


EXPECTED = {
    "table_1_resource_quality.csv",
    "table_1_resource_quality.html",
    "etable_1_resource_quality.csv",
    "etable_1_resource_quality.html",
    "table_2_model_readiness_sensitivities.csv",
    "table_2_model_readiness_sensitivities.html",
    "manuscript_results_handoff.json",
    "figure_legends.json",
    "supplement_full_coefficient_table.csv",
    "supplement_full_coefficient_table.html",
    "supplement_model_gate_diagnostics.csv",
    "figure_1_data_flow_coverage.png",
    "figure_2_cardiometabolic_patterns.png",
    "figure_3_copd_patterns.png",
    "supplement_temporal_models.csv",
    "supplement_leave_one_year_out.csv",
    "supplement_disruption_audit.csv",
    "supplement_influence_c1.csv",
    "supplement_influence_c2.csv",
    "supplement_spatial_diagnostics.csv",
    "supplement_spatial_error_sensitivity.csv",
    "supplement_robustness_summary.csv",
    "supplement_alternative_spatial_weights.csv",
    "supplement_adjusted_diagnostic_data.csv",
    "supplement_concordance_summary.csv",
    "supplement_discordance_quartile.csv",
    "supplement_discordance_tertile.csv",
    "supplement_multiplicity_inventory.csv",
    "supplement_tract_complementarity.csv",
    "supplement_within_community_heterogeneity.csv",
    "supplement_concordance_bootstrap.csv",
    "notebook_run_manifest.json",
}


def _run_notebook(project_root: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "uv",
            "run",
            str(project_root / "notebooks" / "02_chicago_case_studies.py"),
            "--output-dir",
            output_dir.as_posix(),
        ],
        cwd=project_root,
        env={**os.environ, "PYTHONHASHSEED": "0"},
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )


def _hashes(directory: Path) -> dict[str, str]:
    return {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.iterdir())
        if path.is_file()
    }


def test_case_studies_notebook_writes_deterministic_governed_outputs() -> None:
    project_root = Path(__file__).parents[2]
    token = uuid.uuid4().hex
    first = Path("outputs") / "notebooks" / f"pytest-{token}-first"
    second = Path("outputs") / "notebooks" / f"pytest-{token}-second"

    first_run = _run_notebook(project_root, first)
    second_run = _run_notebook(project_root, second)
    try:
        assert first_run.returncode == 0, first_run.stderr
        assert second_run.returncode == 0, second_run.stderr
        first_dir, second_dir = project_root / first, project_root / second
        assert {path.name for path in first_dir.iterdir()} == EXPECTED
        assert _hashes(first_dir) == _hashes(second_dir)

        tract_complementarity = pd.read_csv(first_dir / "supplement_tract_complementarity.csv")
        analytic = pd.read_parquet(
            project_root / "outputs/frozen/chicago_case_studies_analytic.parquet"
        )
        area_capture = (
            analytic.loc[
                analytic["geography_type"].eq("chicago_community_area")
                & analytic["time_period"].astype(str).isin(["2022", "2023", "2024"])
            ]
            .groupby("geography_id", sort=True)["capture_rate"]
            .mean()
            .dropna()
        )
        governed_cuts = np.quantile(area_capture, [0.25, 0.5, 0.75], method="linear")
        governed_cut_text = "|".join(f"{value:.12g}" for value in governed_cuts)
        assert set(tract_complementarity["capture_quartile_cut_points"]) == {governed_cut_text}
        assert set(tract_complementarity["capture_quartile_cut_point_source"]) == {
            "governed_community_area_eligible_population"
        }

        manifest = json.loads((first_dir / "notebook_run_manifest.json").read_text())
        assert manifest["results_authorized"] is False
        assert manifest["primary_adjusted_models_executed"] is True
        assert manifest["primary_adjusted_model_ids"] == ["C2"]
        assert manifest["audit_only_exploratory_model_ids"] == []
        assert manifest["time_zone"] == "America/Chicago"
        assert manifest["full_77_weights_checksum"] == (
            "f1a9b8ade1bf4ed1258b54f97dd78a8c710dc51cc03350053c99df59b2de7922"
        )
        assert manifest["eligible_c2_weights_checksum"] == (
            "927384844fbace67e43cd79a2aa757420e026cac1a063f7b4968b784c7e417b5"
        )
        assert set(manifest["output_sha256"]) == EXPECTED - {"notebook_run_manifest.json"}
        assert manifest["manifest_self_hash_policy"] == "excluded_to_avoid_recursive_hash"
        git_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
        git_dirty = True if git_status.returncode else bool(git_status.stdout.strip())
        expected_binding = (
            "explicit_source_sha256_git_metadata_unavailable"
            if git_status.returncode
            else "git_head_plus_explicit_source_sha256"
        )
        assert manifest["dirty_source_binding"] == expected_binding
        assert manifest["git_dirty"] is git_dirty
        for name, digest in manifest["output_sha256"].items():
            assert digest == sha256((first_dir / name).read_bytes()).hexdigest()
        for key in ("input", "sap", "uv_lock", "notebook"):
            path = project_root / manifest[f"{key}_path"]
            assert manifest[f"{key}_sha256"] == sha256(path.read_bytes()).hexdigest()
        for relative, digest in manifest["analysis_source_sha256"].items():
            assert digest == sha256((project_root / relative).read_bytes()).hexdigest()
        expected_ledgers = {
            "docs/analysis/chm_complementarity_evidence_ledger.md",
            "docs/analysis/chm_complementarity_display_ledger.csv",
        }
        assert set(manifest["handoff_ledger_sha256"]) == expected_ledgers
        for relative, digest in manifest["handoff_ledger_sha256"].items():
            assert digest == sha256((project_root / relative).read_bytes()).hexdigest()

        table_1 = pd.read_csv(first_dir / "table_1_resource_quality.csv")
        required_audit = {
            "rows",
            "disease_measure_eligible_rows",
            "percentage_denominator_rows",
            "suppression_percentage_denominator_rows",
            "missing_percentage_denominator_rows",
            "reliability_available_rows",
            "reliability_available_percentage_denominator_rows",
            "disease_measure_unit",
            "reliability_qualification_status",
            "map_population_areas",
            "map_c2_complete_areas",
            "map_c2_incomplete_areas",
            "map_unavailable_areas",
            "qualification_withheld_areas",
        }
        assert required_audit <= set(table_1.columns)
        community = table_1.loc[table_1["geography_type"].eq("chicago_community_area")]
        copd = community.loc[community["condition_id"].eq("copd")].iloc[0]
        assert (copd["disease_measure_eligible_rows"], copd["rows"]) == (457, 462)
        assert set(
            community.loc[community["condition_id"].ne("copd"), "disease_measure_eligible_rows"]
        ) == {462}
        assert set(community["reliability_qualification_status"]) == {
            "withheld_pending_reliability_rule"
        }
        assert set(community["map_population_areas"]) == {77}
        assert set(community["map_c2_complete_areas"]) == {76}
        assert set(community["map_c2_incomplete_areas"]) == {1}
        assert set(community["map_unavailable_areas"]) == {0}
        assert set(community["qualification_withheld_areas"]) == {77}
        tract_rows = table_1.loc[table_1["geography_type"].eq("census_tract")]
        assert (
            tract_rows[["map_population_areas", "map_c2_complete_areas", "map_c2_incomplete_areas"]]
            .isna()
            .all()
            .all()
        )
        table_1_html = (first_dir / "table_1_resource_quality.html").read_text()
        assert "Table 1. Resource quality" in table_1_html
        assert "Eligible rows / exact source rows" in table_1_html

        table_2 = pd.read_csv(first_dir / "table_2_model_readiness_sensitivities.csv")
        required_model = {
            "estimand_id",
            "readiness_status",
            "withholding_reason",
            "contrast_definition",
            "estimate_unit",
            "scale_iqr",
            "ci_label",
            "n",
            "adjustment_status",
            "analysis_status",
            "interpretation_label",
            "model_choice",
            "moran_residual_model_id",
            "moran_escalation_required",
            "spatial_error_status",
            "model_sensitivity_status",
            "weights_checksum",
            "influence_fragile",
        }
        assert required_model <= set(table_2.columns)
        readiness_rows = table_2.loc[table_2["row_type"].eq("adjusted_primary_readiness")]
        assert dict(zip(readiness_rows["model_key"], readiness_rows["readiness_status"])) == {
            "C1": "withheld_insufficient_complete_areas",
            "C2": "ready_for_adjusted_primary_model",
        }
        assert bool(
            readiness_rows.loc[readiness_rows["model_key"].eq("C1"), "primary_estimand_executed"]
            .eq(False)
            .all()
        )
        primary_contrasts = table_2.loc[table_2["row_type"].eq("adjusted_primary_contrast")]
        assert set(primary_contrasts["model_id"]) == {"C2"}
        assert set(primary_contrasts["confidence_level"]) == {0.975}
        sensitivities = table_2.loc[table_2["row_type"].eq("supported_sensitivity")]
        assert set(sensitivities["estimate_unit"]) == {
            "life_expectancy_years_per_frozen_IQR_contrast"
        }
        assert set(sensitivities["ci_label"]) == {"97.5% CI"}
        assert set(sensitivities["analysis_status"]) == {"supported_sensitivity_not_primary"}
        assert set(table_2["moran_residual_model_id"].dropna()) == {"C2"}
        assert set(table_2.loc[table_2["estimate"].notna(), "model_key"]) == {"C2"}
        table_2_html = (first_dir / "table_2_model_readiness_sensitivities.html").read_text()
        assert "Table 2. Primary adjusted estimates and supported sensitivities" in table_2_html
        handoff = json.loads((first_dir / "manuscript_results_handoff.json").read_text())
        assert handoff["results_authorized"] is False
        assert handoff["manuscript_import_allowed"] is False
        assert "blocked_tavily_monthly_cap" in handoff["live_journal_verification"]
        assert "observed CAPriCORN adults" in handoff["interpretation_boundary"]
        assert handoff["primary_result_sentences"] == []
        assert handoff["spatial_diagnostic_sentences"] == []
        assert handoff["withheld_result_status"] == {
            "cardiometabolic": "not_run_combined_diabetes_semantics_unapproved",
            "copd": "withheld_pending_independent_review",
        }
        assert {"model_gate_findings", "complementarity_metrics", "robustness_results", "per_result_import_authorization"} <= set(handoff)
        assert handoff["per_result_import_authorization"]["C1"]["manuscript_import_allowed"] is False
        assert handoff["audit_only"]["manuscript_import_allowed"] is False
        legends = json.loads((first_dir / "figure_legends.json").read_text())
        assert set(legends) == {"figure_1", "figure_2", "figure_3"}
        assert set(legends.values()) == {"[WITHHELD pending independent S7 review.]"}

        coefficient_table = pd.read_csv(first_dir / "supplement_full_coefficient_table.csv")
        assert set(coefficient_table["model_id"]) == {"C2"}
        assert {"alpha", "beta_c", "gamma_capture"} <= set(coefficient_table["term"])
        assert "audit_only_exploratory" not in set(coefficient_table["analysis_status"])
        coefficient_html = (first_dir / "supplement_full_coefficient_table.html").read_text()
        assert "Full alpha, beta, and gamma coefficients" in coefficient_html

        model_gates = pd.read_csv(first_dir / "supplement_model_gate_diagnostics.csv")
        assert list(model_gates.groupby("model_id", sort=False).size()) == [6, 5]
        c1_gates = model_gates.loc[model_gates["model_id"].eq("C1")]
        c2_gates = model_gates.loc[model_gates["model_id"].eq("C2")]
        assert set(c1_gates["status"]) == {"withheld_insufficient_complete_areas"}
        assert set(c2_gates["status"]) == {"ready_for_adjusted_primary_model"}
        assert c1_gates["maximum_vif"].isna().all()
        assert set(c2_gates["hc3_covariance_status"]) == {"estimable_and_finite"}
        assert set(model_gates["results_authorized"]) == {False}

        spatial_error = pd.read_csv(first_dir / "supplement_spatial_error_sensitivity.csv")
        assert set(spatial_error["model_id"]) == {"C2"}
        spatial_diagnostics = pd.read_csv(first_dir / "supplement_spatial_diagnostics.csv")
        assert set(spatial_diagnostics["model_id"]) == {"C2"}

        robustness = pd.read_csv(first_dir / "supplement_robustness_summary.csv")
        assert {
            "model",
            "estimand",
            "variant",
            "target_population",
            "estimate",
            "ci_low",
            "ci_high",
            "eligible_n",
            "direction_stability",
            "absolute_percentage_change",
            "ci_overlap",
            "threshold_crossed",
            "analysis_status",
            "authorization_status",
        } <= set(robustness.columns)
        assert {"population_weighted_ols", "frozen_capture_quartiles"} <= set(robustness["variant"])
        adjusted_temporal = robustness.loc[
            robustness["variant"].str.startswith("leave_one_primary_year_out:")
        ]
        assert set(adjusted_temporal["variant"]) == {
            "leave_one_primary_year_out:2022",
            "leave_one_primary_year_out:2023",
            "leave_one_primary_year_out:2024",
        }
        assert set(adjusted_temporal["estimator"]) == {"unweighted_ols_hc3_adjusted_temporal"}
        assert set(adjusted_temporal["adjustment_set"]) == {
            "pct_age_65_plus|pct_female|pct_below_fpl|capture_rate_mean_2022_2024"
        }
        annual_unadjusted = pd.read_csv(first_dir / "supplement_temporal_models.csv")
        early_annual = annual_unadjusted.loc[
            annual_unadjusted["analysis_id"].isin(["annual_2019", "annual_2020", "annual_2021"])
            & annual_unadjusted["row_type"].eq("association_model")
        ]
        assert set(early_annual["adjustment_set"]) == {"unadjusted"}
        assert set(early_annual["primary_estimand_executed"]) == {False}
        assert set(robustness["authorization_status"]) == {"results_not_authorized"}
        assert set(robustness.loc[robustness["model"].eq("C1"), "primary_estimand_executed"]) == {
            False
        }
        frozen_variants = robustness.set_index(["model", "variant"])
        assert frozen_variants.loc[("C2", "continuous_capture_reference"), "estimate"] == (
            pytest.approx(-2.60461891442)
        )
        assert frozen_variants.loc[("C2", "population_weighted_ols"), "estimate"] == (
            pytest.approx(-3.97430624591)
        )
        assert frozen_variants.loc[("C2", "frozen_capture_quartiles"), "capture_cut_points"] == (
            "0.051875|0.07475|0.113425"
        )

        alternative = pd.read_csv(first_dir / "supplement_alternative_spatial_weights.csv")
        assert set(alternative["topology_method"]) == {
            "first_order_rook_contiguity",
            "smallest_connected_centroid_distance_band",
        }
        assert alternative["connected"].all()
        assert set(alternative["island_count"]) == {0}
        assert alternative["checksum"].str.fullmatch(r"[0-9a-f]{64}").all()
        assert set(alternative["model"]) == {"C2"}
        assert set(alternative["analysis_status"]) == {"freeze_candidate_primary_model_unsecured"}
        frozen_topology = alternative.set_index("weights_definition")
        assert frozen_topology.loc["rook", "checksum"] == (
            "86cf5f1a1f04f41add2a6aec9b688bc00f56a1363fc2263a968b4ad1789f00d6"
        )
        assert frozen_topology.loc["smallest_connected_distance_band", "checksum"] == (
            "3da4f09dfbf60868be84963eab77197809d6e6e1b0f99b2aa40ea3f7b1d7fd77"
        )
        assert frozen_topology.loc[
            "smallest_connected_distance_band", "distance_threshold"
        ] == pytest.approx(0.0422693076511)
        assert set(alternative["spatial_error_status"]) == {"mandatory_spatial_sensitivity_run"}
        assert (
            alternative[["spatial_error_estimate", "spatial_error_ci_low", "spatial_error_ci_high"]]
            .notna()
            .all()
            .all()
        )
        assert (alternative["spatial_error_weights_checksum"] == alternative["checksum"]).all()

        adjusted_diagnostics = pd.read_csv(first_dir / "supplement_adjusted_diagnostic_data.csv")
        assert {"C2"} == set(adjusted_diagnostics["model"])
        assert {
            "fitted_value",
            "residual",
            "qq_theoretical_quantile",
            "leverage",
            "cooks_distance",
            "externally_studentized_residual",
        } <= set(adjusted_diagnostics.columns)

        for figure_name in (
            "figure_1_data_flow_coverage.png",
            "figure_2_cardiometabolic_patterns.png",
            "figure_3_copd_patterns.png",
        ):
            pixels = mpimg.imread(first_dir / figure_name)
            assert float(pixels.std()) > 0.02
    finally:
        shutil.rmtree(project_root / first, ignore_errors=True)
        shutil.rmtree(project_root / second, ignore_errors=True)


def test_case_studies_notebook_rejects_unexpected_stale_outputs() -> None:
    project_root = Path(__file__).parents[2]
    output = Path("outputs") / "notebooks" / f"pytest-stale-{uuid.uuid4().hex}"
    output_dir = project_root / output
    output_dir.mkdir(parents=True)
    (output_dir / "stale_unregistered_artifact.csv").write_text("stale\n", encoding="utf-8")

    result = _run_notebook(project_root, output)
    try:
        assert result.returncode != 0
        assert "unexpected files" in result.stderr
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
