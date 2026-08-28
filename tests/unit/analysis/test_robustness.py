from __future__ import annotations

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from chicagohealthmap.analysis.robustness import (
    COMMON_ROBUSTNESS_COLUMNS,
    absolute_percentage_change,
    build_not_applicable_rows,
    build_adjusted_diagnostic_data,
    build_adjusted_temporal_robustness,
    build_governed_robustness_summary,
    capture_quartile_cut_points,
    ci_overlap,
    direction_stability,
)


def _model_frame(n: int = 77) -> pd.DataFrame:
    x = np.linspace(-2.0, 2.0, n)
    order = np.arange(n)
    return pd.DataFrame(
        {
            "geography_id": [f"CA{index + 1:02d}" for index in range(n)],
            "life_expectancy_mean_2022_2024": 76 - 0.7 * x + 0.2 * np.sin(order),
            "hypertension_ehr_percent_2022_2024": 25 + 3 * x + np.sin(order * 0.7),
            "diabetes_ehr_percent_2022_2024": 10 + x + np.cos(order * 0.4),
            "copd_ehr_percent_2022_2024": 7 + 1.8 * x + np.sin(order * 0.9),
            "pct_age_65_plus": 14 + np.cos(order * 0.3),
            "pct_female": 51 + np.sin(order * 0.2),
            "pct_below_fpl": 18 + np.cos(order * 0.5),
            "capture_rate_mean_2022_2024": 0.25 + 0.05 * np.sin(order * 0.6),
            "acs_adult_population": 1000 + 17 * order,
            "life_expectancy_years_complete": True,
            "hypertension_exposure_complete": True,
            "diabetes_exposure_complete": True,
            "copd_exposure_complete": True,
        }
    )


def _primary_temporal_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for area_index, geography_id in enumerate(frame["geography_id"]):
        for year in (2022, 2023, 2024):
            year_offset = year - 2022
            hypertension = 20 + area_index % 17 + year_offset
            diabetes_one = 3 + area_index % 5
            diabetes_two = 4 + area_index % 9 + year_offset
            copd = 5 + area_index % 13 + year_offset
            outcome = 88 - 0.08 * hypertension - 0.12 * (diabetes_one + diabetes_two) - 0.2 * copd
            for condition, numerator in (
                ("hypertension", hypertension),
                ("diabetes_with_complication", diabetes_one),
                ("diabetes_without_complication", diabetes_two),
                ("copd", copd),
            ):
                rows.append(
                    {
                        "geography_type": "chicago_community_area",
                        "geography_id": geography_id,
                        "time_period": str(year),
                        "condition_id": condition,
                        "condition_family": (
                            "diabetes" if condition.startswith("diabetes") else condition
                        ),
                        "numerator": numerator,
                        "denominator": 1000 + area_index,
                        "published_measure_value": 100 * numerator / (1000 + area_index),
                        "suppression_flag": False,
                        "combined_diabetes_semantics_approved": True,
                        "capture_rate": 0.2 + area_index / 1000 + year_offset / 100,
                        "life_expectancy_estimate": outcome,
                        "life_expectancy_time_period": str(year),
                    }
                )
    return pd.DataFrame.from_records(rows)


def test_common_schema_and_prespecified_not_applicable_rows_are_governed() -> None:
    rows = build_not_applicable_rows()

    assert set(COMMON_ROBUSTNESS_COLUMNS) <= set(rows.columns)
    assert set(rows["variant"]) == {
        "implausible_ratio_exclusion",
        "multiple_imputation",
        "precision_weighting",
        "exclude_crosswalk_derived_disease_estimates",
    }
    assert set(rows["analysis_status"]) == {"not_applicable"}
    assert set(rows["authorization_status"]) == {"results_not_authorized"}
    assert rows["estimate"].isna().all()
    assert rows["threshold_crossed"].str.startswith("not_applicable:").all()


def test_comparison_definitions_handle_zero_missing_and_closed_intervals() -> None:
    assert direction_stability(-1.0, -0.2) is True
    assert direction_stability(0.0, 0.0) is True
    assert direction_stability(0.0, 0.1) is False
    assert direction_stability(np.nan, 1.0) is pd.NA
    assert absolute_percentage_change(2.0, 3.0) == pytest.approx(50.0)
    change, reason = absolute_percentage_change(0.0, 3.0, return_reason=True)
    assert np.isnan(change)
    assert reason == "reference_zero"
    assert ci_overlap(0.0, 1.0, 1.0, 2.0) is True
    assert ci_overlap(0.0, 0.9, 1.0, 2.0) is False
    assert ci_overlap(np.nan, 1.0, 1.0, 2.0) is pd.NA


def test_capture_quartile_cut_points_are_frozen_from_governed_eligible_population() -> None:
    frame = pd.DataFrame(
        {
            "capture_rate_mean_2022_2024": [9.0, 1.0, 7.0, 3.0, 100.0],
            "eligible": [True, True, True, True, False],
        }
    )

    cut_points = capture_quartile_cut_points(frame, frame["eligible"])
    reordered = capture_quartile_cut_points(
        frame.sample(frac=1, random_state=4), lambda x: x["eligible"]
    )

    assert cut_points == pytest.approx((2.5, 5.0, 7.5))
    assert reordered == pytest.approx(cut_points)


def test_weighted_adjusted_hc3_matches_independent_statsmodels() -> None:
    import statsmodels.api as sm

    frame = _model_frame()
    summary = build_governed_robustness_summary(frame)
    row = summary.loc[
        summary["model"].eq("C2") & summary["variant"].eq("population_weighted_ols")
    ].iloc[0]
    exposure = frame["copd_ehr_percent_2022_2024"]
    transformed = pd.DataFrame(
        {
            "copd": (exposure - exposure.mean())
            / (exposure.quantile(0.75) - exposure.quantile(0.25)),
            "age": (frame["pct_age_65_plus"] - frame["pct_age_65_plus"].mean())
            / frame["pct_age_65_plus"].std(ddof=1),
            "female": (frame["pct_female"] - frame["pct_female"].mean())
            / frame["pct_female"].std(ddof=1),
            "poverty": (frame["pct_below_fpl"] - frame["pct_below_fpl"].mean())
            / frame["pct_below_fpl"].std(ddof=1),
            "capture": (
                frame["capture_rate_mean_2022_2024"] - frame["capture_rate_mean_2022_2024"].mean()
            )
            / frame["capture_rate_mean_2022_2024"].std(ddof=1),
        }
    )
    fit = sm.WLS(
        frame["life_expectancy_mean_2022_2024"],
        sm.add_constant(transformed, has_constant="add"),
        weights=frame["acs_adult_population"],
    ).fit(cov_type="HC3")
    critical = 2.241402727604947  # standard-normal 97.5% two-sided interval

    assert row["estimate"] == pytest.approx(fit.params["copd"], rel=1e-10)
    assert row["ci_low"] == pytest.approx(fit.params["copd"] - critical * fit.bse["copd"], rel=1e-9)
    assert row["target_population"] == "population_weighted_community_area_adult_population"
    assert row["estimator"] == "population_weighted_ols_hc3"


def test_adjusted_influence_quartiles_and_na_rows_share_schema() -> None:
    summary = build_governed_robustness_summary(_model_frame())

    assert set(COMMON_ROBUSTNESS_COLUMNS) <= set(summary.columns)
    assert {"continuous_capture_reference", "frozen_capture_quartiles"} <= set(summary["variant"])
    assert summary["capture_cut_points"].dropna().str.count(r"\|").eq(2).all()
    loo = summary.loc[summary["variant"].str.startswith("leave_one_area_out:")]
    assert len(loo.loc[loo["model"].eq("C2")]) == 77
    excluded = summary.loc[summary["variant"].eq("exclude_all_prespecified_flagged_areas")]
    assert set(excluded["adjustment_set"]) == {
        "pct_age_65_plus|pct_female|pct_below_fpl|capture_rate_mean_2022_2024"
    }
    assert set(summary["authorization_status"]) == {"results_not_authorized"}
    assert set(summary.loc[summary["model"].eq("C1"), "primary_estimand_executed"]) == {False}


def test_adjusted_diagnostic_data_exposes_all_prespecified_plot_inputs() -> None:
    diagnostic = build_adjusted_diagnostic_data(_model_frame())

    assert {
        "model",
        "geography_id",
        "fitted_value",
        "residual",
        "qq_theoretical_quantile",
        "qq_sample_quantile",
        "leverage",
        "cooks_distance",
        "externally_studentized_residual",
        "analysis_status",
        "authorization_status",
    } <= set(diagnostic.columns)
    assert diagnostic.groupby("model").size().to_dict() == {"C1": 77, "C2": 77}
    assert (
        np.isfinite(diagnostic[["fitted_value", "residual", "leverage", "cooks_distance"]])
        .all()
        .all()
    )


def test_c2_readiness_failure_cannot_emit_primary_robustness_or_diagnostics() -> None:
    frame = _model_frame()
    order = np.arange(len(frame))
    frame["copd_ehr_percent_2022_2024"] = 2 * frame["pct_age_65_plus"] + 0.01 * np.sin(order * 1.7)

    summary = build_governed_robustness_summary(frame)
    diagnostic = build_adjusted_diagnostic_data(frame)

    c2_summary = summary.loc[summary["model"].eq("C2")]
    c2_diagnostic = diagnostic.loc[diagnostic["model"].eq("C2")]
    assert set(c2_summary["analysis_status"]) == {"audit_only_exploratory"}
    assert set(c2_summary["primary_estimand_executed"]) == {False}
    assert set(c2_diagnostic["analysis_status"]) == {"audit_only_exploratory"}
    assert set(c2_diagnostic["primary_estimand_executed"]) == {False}

    temporal = build_adjusted_temporal_robustness(_primary_temporal_dataset(frame), frame)
    c2_temporal = temporal.loc[temporal["model"].eq("C2")]
    assert set(c2_temporal["analysis_status"]) == {"audit_only_exploratory"}
    assert set(c2_temporal["primary_estimand_executed"]) == {False}
