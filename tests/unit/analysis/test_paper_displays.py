from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chicagohealthmap.analysis.case_studies import CaseStudyAnalysisError
from chicagohealthmap.analysis.paper_displays import (
    MAIN_DISPLAY_IDS,
    build_adjusted_prediction_data,
    build_compact_table_1,
    build_compact_table_2,
    build_geographic_consequence_display_data,
    build_geographic_main_evidence,
    build_flow_summary,
    build_resolution_heatmap_data,
    build_true_tract_gap_frame,
    confidence_interval_label,
)
from chicagohealthmap.analysis.sap_analyses import fit_primary_models


def _model_frame(n: int = 77) -> pd.DataFrame:
    i = np.arange(n, dtype=float)
    hypertension = 5 + i / 5 + (i % 7) / 10
    diabetes = 3 + (i % 13) + i / 20
    copd = 2 + (i % 11) / 2 + i / 30
    return pd.DataFrame(
        {
            "geography_id": [f"{value + 1:02d}" for value in range(n)],
            "life_expectancy_mean_2022_2024": 82 - 0.12 * hypertension - 0.2 * copd,
            "hypertension_ehr_percent_2022_2024": hypertension,
            "diabetes_ehr_percent_2022_2024": diabetes,
            "copd_ehr_percent_2022_2024": copd,
            "pct_age_65_plus": 8 + (i % 17),
            "pct_female": 45 + (i % 9),
            "pct_below_fpl": 5 + (i % 19),
            "capture_rate_mean_2022_2024": 0.2 + (i % 23) / 1000,
            "life_expectancy_years_complete": 3,
            "hypertension_exposure_complete": True,
            "diabetes_exposure_complete": True,
            "copd_exposure_complete": True,
        }
    )


def test_compact_table_1_is_chm_only_and_community_area_only() -> None:
    source = pd.DataFrame(
        {
            "geography_type": ["census_tract"] + ["chicago_community_area"] * 4,
            "condition_id": [
                "copd",
                "copd",
                "diabetes_with_complication",
                "diabetes_without_complication",
                "hypertension",
            ],
            "rows": [100, 462, 462, 462, 462],
            "geographies": [20, 77, 77, 77, 77],
            "years": [6, 6, 6, 6, 6],
            "denominator_median": [320.0, 3163.0, 3193.0, 3193.0, 3193.0],
            "denominator_iqr": [100.0, 3102.0, 3102.0, 3102.0, 3102.0],
            "disease_measure_eligible_rows": [75, 457, 462, 462, 462],
            "percentage_denominator_rows": [100, 462, 462, 462, 462],
            "suppressed_rows": [25, 5, 0, 0, 0],
            "suppression_percentage_denominator_rows": [100, 462, 462, 462, 462],
            "capture_median": [0.08, 0.0735, 0.0735, 0.0735, 0.0735],
            "capture_iqr": [0.04, 0.0609, 0.0609, 0.0609, 0.0609],
            "reliability_qualification_status": ["withheld_pending_reliability_rule"] * 5,
        }
    )

    table = build_compact_table_1(source)

    assert list(table.columns) == [
        "Condition",
        "Years, No.",
        "Condition-year records, No.",
        "Community areas represented, No.",
        "CHM condition-record denominator, median (IQR)",
        "Eligible, No. (%)",
        "Suppressed, No. (%)",
        "Source-published capture, median (IQR), %",
        "Reliability status",
    ]
    assert table.shape == (4, 9)
    assert table["Condition-year records, No."].eq(462).all()
    assert table["Community areas represented, No."].eq(77).all()
    assert "Geography" not in table
    assert table.loc[table["Condition"].eq("COPD"), "Eligible, No. (%)"].item() == "457 (98.9)"


def test_ci_label_is_generated_from_result_level() -> None:
    assert confidence_interval_label(0.975) == "97.5% CI"
    assert confidence_interval_label(0.95) == "95% CI"
    with pytest.raises(ValueError, match="confidence level"):
        confidence_interval_label(2.0)


def test_geographic_main_evidence_drives_three_row_table_2() -> None:
    agreement = pd.DataFrame(
        {
            "condition_id": ["hypertension", "diabetes", "copd"] * 2,
            "sample_n": [792, 770, 586, 100, 100, 100],
            "spearman_r": [0.865, 0.730, 0.719, 0.999, 0.999, 0.999],
            "quadratic_weighted_kappa": [0.826, 0.700, 0.671, 0.999, 0.999, 0.999],
            "gwet_ac1": [0.529, 0.333, 0.367, 0.999, 0.999, 0.999],
            "stratum": ["overall"] * 3 + ["capture_quartile"] * 3,
            "noncrossing_only": [False] * 6,
            "results_authorized": [False] * 6,
        }
    )
    partition = pd.DataFrame(
        {
            "analysis_id": ["A1", "A2"] * 3,
            "condition_id": ["hypertension"] * 2 + ["diabetes"] * 2 + ["copd"] * 2,
            "estimate": [0.731, 0.928, 0.717, 0.863, 0.553, 0.830],
            "sensitivity_status": ["primary"] * 6,
            "results_authorized": [False] * 6,
        }
    )
    resolution = pd.DataFrame(
        {
            "condition_id": ["hypertension", "diabetes", "copd"] * 2,
            "tract_sample_n": [792, 770, 584, 800, 780, 600],
            "exact_quartile_agreement_count": [515, 472, 298, 1, 1, 1],
            "exact_quartile_agreement_pct": [65.025, 61.299, 51.027, 1.0, 1.0, 1.0],
            "quartile_disagree_count": [277, 298, 286, 999, 999, 999],
            "quartile_disagree_pct": [34.975, 38.701, 48.973, 99.0, 99.0, 99.0],
            "comparison_geography_type": ["chicago_community_area"] * 3 + ["zcta"] * 3,
            "noncrossing_only": [False] * 6,
            "results_authorized": [False] * 6,
        }
    )
    transitions = pd.DataFrame(
        {
            "condition_id": ["hypertension", "hypertension", "diabetes", "diabetes", "copd", "copd"]
            * 2,
            "transition_state": ["moves_into_highest_quartile", "moves_out_of_highest_quartile"]
            * 6,
            "tract_count": [44, 55, 83, 58, 85, 40, 999, 999, 999, 999, 999, 999],
            "comparison_geography_type": ["chicago_community_area"] * 6 + ["zcta"] * 6,
            "sensitivity_status": ["all_eligible"] * 12,
            "results_authorized": [False] * 12,
        }
    )

    evidence = build_geographic_main_evidence(agreement, partition, resolution, transitions)
    table = build_compact_table_2(evidence)

    assert evidence["condition_id"].tolist() == ["hypertension", "diabetes", "copd"]
    assert table["Condition"].tolist() == [
        "Hypertension",
        "Combined diabetes components",
        "COPD",
    ]
    assert list(table.columns) == [
        "Condition",
        "Tract/community eligible tracts, No.",
        "Exact quartile agreement, No. (%)",
        "Quartile disagreement, No. (%)",
        "Within-community variance share",
        "Q4 transition eligible tracts, No.",
        "Q4 movers, No. (%)",
    ]
    assert table.loc[2, "Tract/community eligible tracts, No."] == 584
    assert evidence.loc[2, "agreement_eligible_n"] == 586
    assert pd.isna(evidence.loc[1, "agreement_eligible_n"])
    assert evidence.loc[1, "availability_reason"] == (
        "combined_components_not_primary_places_comparator_pending_phenotype_and_period_mapping|"
        "spearman_r:not_available|weighted_kappa:not_available|gwet_ac1:not_available"
    )
    assert table.loc[0, "Q4 movers, No. (%)"] == "99 (100.0)"
    assert table.loc[2, "Quartile disagreement, No. (%)"] == "286 (49.0)"
    assert not evidence["results_authorized"].any()
    assert not evidence["manuscript_import_allowed"].any()
    assert "metric-specific" in evidence.loc[0, "uncertainty_status"]


def test_geographic_main_evidence_marks_missing_metric_unavailable() -> None:
    agreement = pd.DataFrame(
        {
            "condition_id": ["hypertension", "diabetes", "copd"],
            "sample_n": [3, 3, 3],
            "spearman_r": [0.8, 0.7, 0.6],
            "quadratic_weighted_kappa": [0.7, 0.6, 0.5],
            "gwet_ac1": [0.5, 0.4, np.nan],
            "stratum": ["overall"] * 3,
            "noncrossing_only": [False] * 3,
            "results_authorized": [False] * 3,
        }
    )
    partition = pd.DataFrame(
        {
            "analysis_id": ["A1", "A2"] * 3,
            "condition_id": ["hypertension"] * 2 + ["diabetes"] * 2 + ["copd"] * 2,
            "vpc_icc": [0.7, np.nan, 0.6, np.nan, 0.5, np.nan],
            "auc": [np.nan, 0.9, np.nan, 0.8, np.nan, 0.7],
            "ci_low": [0.6, 0.8, 0.5, 0.7, 0.4, 0.6],
            "ci_high": [0.8, 1.0, 0.7, 0.9, 0.6, 0.8],
            "results_authorized": [False] * 6,
        }
    )
    resolution = pd.DataFrame(
        {
            "condition_id": ["hypertension", "diabetes", "copd"],
            "tract_sample_n": [3, 3, 3],
            "quartile_disagree_count": [1, 1, 1],
            "quartile_disagree_pct": [33.3, 33.3, 33.3],
            "comparison_geography_type": ["chicago_community_area"] * 3,
            "noncrossing_only": [False] * 3,
            "results_authorized": [False] * 3,
        }
    )
    transitions = pd.DataFrame(
        {
            "condition_id": [
                "hypertension",
                "hypertension",
                "diabetes",
                "diabetes",
                "copd",
                "copd",
            ],
            "transition_state": ["moves_into_highest_quartile", "moves_out_of_highest_quartile"]
            * 3,
            "tract_count": [1, 0, 1, 0, 1, 0],
            "comparison_geography_type": ["chicago_community_area"] * 6,
            "sensitivity_status": ["all_eligible"] * 6,
            "results_authorized": [False] * 6,
        }
    )

    evidence = build_geographic_main_evidence(agreement, partition, resolution, transitions)
    copd = evidence.loc[evidence["condition_id"].eq("copd")].iloc[0]

    assert copd["availability_status"] == "partial_metric_availability"
    assert "gwet_ac1:not_available" in copd["availability_reason"]
    assert copd["unit"] == "condition-specific eligible census tracts"
    assert copd["comparison_geography_type"] == "chicago_community_area"
    assert copd["uncertainty_aware_agreement_status"] == "not_run"
    assert copd["source_checksum"] == "not_provided_in_frame"
    assert bool(copd["results_authorized"]) is False


def test_geographic_main_evidence_rejects_model_fields() -> None:
    """The main geographic evidence contract cannot carry model outputs."""
    agreement = pd.DataFrame(
        {
            "condition_id": ["hypertension"],
            "sample_n": [3],
            "spearman_r": [0.8],
            "quadratic_weighted_kappa": [0.7],
            "gwet_ac1": [0.5],
            "stratum": ["overall"],
            "noncrossing_only": [False],
            "results_authorized": [False],
            "model_id": ["C1"],
        }
    )
    partition = pd.DataFrame(
        {
            "analysis_id": ["A1", "A2"],
            "condition_id": ["hypertension", "hypertension"],
            "estimate": [0.7, 0.8],
            "sensitivity_status": ["primary", "primary"],
            "results_authorized": [False, False],
        }
    )
    resolution = pd.DataFrame(
        {
            "condition_id": ["hypertension"],
            "tract_sample_n": [3],
            "quartile_disagree_count": [1],
            "quartile_disagree_pct": [33.3],
            "comparison_geography_type": ["chicago_community_area"],
            "noncrossing_only": [False],
            "results_authorized": [False],
        }
    )
    transitions = pd.DataFrame(
        {
            "condition_id": ["hypertension", "hypertension"],
            "transition_state": [
                "moves_into_highest_quartile",
                "moves_out_of_highest_quartile",
            ],
            "tract_count": [1, 0],
            "comparison_geography_type": ["chicago_community_area"] * 2,
            "sensitivity_status": ["all_eligible"] * 2,
            "results_authorized": [False, False],
        }
    )
    with pytest.raises(CaseStudyAnalysisError, match="model fields"):
        build_geographic_main_evidence(agreement, partition, resolution, transitions)


def test_geographic_consequence_display_data_keeps_dynamic_denominators() -> None:
    transitions = pd.DataFrame(
        {
            "condition_id": [
                "hypertension",
                "hypertension",
                "diabetes",
                "diabetes",
                "copd",
                "copd",
            ],
            "transition_state": ["moves_into_highest_quartile", "moves_out_of_highest_quartile"]
            * 3,
            "tract_count": [44, 55, 83, 58, 85, 40],
            "mean_annual_source_denominator": [
                12943.7,
                19070.7,
                32569.7,
                17148.3,
                35270.7,
                15221.7,
            ],
            "comparison_geography_type": ["chicago_community_area"] * 6,
            "sensitivity_status": ["all_eligible"] * 6,
        }
    )
    mixed = pd.DataFrame(
        {
            "condition_id": ["hypertension", "diabetes", "copd", "copd"],
            "comparison_geography_id": [1, 1, 1, 2],
            "comparison_geography_type": ["chicago_community_area"] * 4,
            "sensitivity_status": ["all_eligible"] * 4,
        }
    )
    stability = pd.DataFrame(
        {
            "condition_id": ["hypertension", "diabetes", "copd"],
            "time_period": [2024, 2024, 2024],
            "top_quartile_jaccard": [0.62, 0.49, 0.45],
            "result_type": ["annual_jaccard"] * 3,
            "comparison_geography_type": ["chicago_community_area"] * 3,
            "sensitivity_status": ["all_eligible"] * 3,
        }
    )
    resolution = pd.DataFrame(
        {
            "condition_id": ["hypertension", "diabetes", "copd"],
            "quartile_disagree_pct": [36.0, 44.6, 50.0],
            "noncrossing_only": [True] * 3,
        }
    )

    result = build_geographic_consequence_display_data(transitions, mixed, stability, resolution)

    assert result["transitions"].shape[0] == 6
    assert result["mixed_counts"].set_index("condition_id").loc["copd", "community_area_n"] == 2
    assert result["noncrossing"].set_index("condition_id").loc[
        "diabetes", "quartile_disagree_pct"
    ] == pytest.approx(44.6)
    copd = result["transitions"].query("condition_id == 'copd'")
    assert copd["tract_count"].sum() == 125
    assert copd["mean_annual_source_denominator"].sum() == pytest.approx(50492.4)


def test_adjusted_prediction_uses_observed_exposure_range_and_primary_ci() -> None:
    primary_frame = _model_frame()
    result = fit_primary_models(primary_frame)["C2"]
    prediction = build_adjusted_prediction_data(result, primary_frame, points=25)

    exposure = "copd_ehr_percent_2022_2024"
    eligible = primary_frame.loc[primary_frame["copd_exposure_complete"]]
    assert len(prediction) == 25
    assert prediction["exposure"].iloc[[0, -1]].tolist() == pytest.approx(
        [eligible[exposure].min(), eligible[exposure].max()]
    )
    assert set(prediction["confidence_level"]) == {0.975}
    assert set(prediction["n"]) == {len(eligible)}
    assert np.all(prediction["ci_low"] <= prediction["prediction"])
    assert np.all(prediction["prediction"] <= prediction["ci_high"])
    assert not prediction["results_authorized"].any()


def test_flow_summary_keeps_overlapping_case_denominators_as_branches() -> None:
    source = pd.DataFrame(
        {"rows": [100, 80], "disease_measure_eligible_rows": [90, 70], "suppressed_rows": [2, 1]}
    )
    flow = build_flow_summary(source, case_denominators={"C1": 77, "C2": 76})
    assert tuple(MAIN_DISPLAY_IDS) == ("table_1", "figure_1", "figure_2", "figure_3", "table_2")
    assert flow.loc[flow["stage"].eq("pooled_community_areas"), "count"].item() == 77
    assert flow.loc[flow["stage"].eq("case_eligible"), "count"].tolist() == [77, 76]
    assert flow.loc[flow["stage"].eq("case_eligible"), "branch"].tolist() == ["C1", "C2"]


def test_flow_summary_records_combined_diabetes_not_run_as_zero() -> None:
    source = pd.DataFrame(
        {"rows": [100], "disease_measure_eligible_rows": [90], "suppressed_rows": [2]}
    )

    flow = build_flow_summary(source, case_denominators={"C1": 0, "C2": 76})

    assert flow.loc[flow["branch"].eq("C1"), "count"].item() == 0
    assert flow.loc[flow["stage"].eq("pooled_community_areas"), "count"].item() == 76


def test_resolution_heatmap_is_complete_and_filters_non_crossing_rule() -> None:
    rows = pd.DataFrame(
        {
            "condition_id": ["copd", "copd"],
            "community_quartile": [1, 4],
            "tract_quartile": [1, 4],
            "tract_percent": [55.0, 45.0],
            "noncrossing_only": [False, False],
        }
    )
    matrix = build_resolution_heatmap_data(rows, "copd")
    assert matrix.shape == (4, 4)
    assert matrix.loc[1, 1] == 55.0
    assert matrix.loc[4, 4] == 45.0
    assert matrix.fillna(0).to_numpy().sum() == pytest.approx(100)


def test_true_tract_gap_frame_rejects_community_geometry() -> None:
    gaps = pd.DataFrame({"geography_id": ["1"], "paired_percentile_rank_gap": [0.25]})
    geometry = pd.DataFrame(
        {
            "geography_id": ["1"],
            "geometry_wkt": ["POLYGON ((0 0, 1 0, 1 1, 0 0))"],
            "geography_type": ["chicago_community_area"],
        }
    )
    with pytest.raises(CaseStudyAnalysisError, match="non-tract"):
        build_true_tract_gap_frame(gaps, geometry)
