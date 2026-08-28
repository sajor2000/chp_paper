from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from chicagohealthmap.analysis.case_studies import CaseStudyAnalysisError
from chicagohealthmap.analysis.sap_analyses import (
    ADJUSTMENT_COVARIATES,
    assess_primary_model_readiness,
    build_adjusted_residuals,
    build_model_gate_diagnostics,
    fit_primary_models,
    build_unadjusted_sensitivity_residuals,
    fit_audit_only_exploratory_models,
    fit_minimally_adjusted_sensitivities,
    summarize_influence,
    summarize_temporal_robustness,
)


EXPOSURES = {
    "C1": ["hypertension_ehr_percent_2022_2024", "diabetes_ehr_percent_2022_2024"],
    "C2": ["copd_ehr_percent_2022_2024"],
}
COVARIATES = ["pct_age_65_plus", "pct_female", "pct_below_fpl", "capture_rate_mean_2022_2024"]


def _model_frame(n: int = 77) -> pd.DataFrame:
    i = np.arange(n, dtype=float)
    hypertension = 5 + i / 5 + (i % 7) / 10
    diabetes = 3 + (i % 13) + i / 20
    copd = 2 + (i % 11) / 2 + i / 30
    return pd.DataFrame(
        {
            "geography_id": [f"{value + 1:02d}" for value in range(n)],
            "life_expectancy_mean_2022_2024": (
                82 - 0.12 * hypertension - 0.08 * diabetes - 0.2 * copd + 0.03 * (i % 5)
            ),
            "hypertension_ehr_percent_2022_2024": hypertension,
            "diabetes_ehr_percent_2022_2024": diabetes,
            "copd_ehr_percent_2022_2024": copd,
            "pct_age_65_plus": 8 + (i % 17),
            "pct_female": 45 + (i % 9),
            "pct_below_fpl": 5 + (i % 19),
            "acs_adult_population": 1000 + 37 * i,
            "capture_rate_mean_2022_2024": 0.2 + (i % 23) / 1000,
            "life_expectancy_years_complete": [3] * n,
            "hypertension_exposure_complete": [True] * n,
            "diabetes_exposure_complete": [True] * n,
            "copd_exposure_complete": [True] * n,
        }
    )


def _orthogonal_predictor_frame(explained_fraction: float) -> pd.DataFrame:
    frame = _model_frame()
    rng = np.random.default_rng(20260715)
    raw = rng.normal(size=(len(frame), 7))
    centered = raw - raw.mean(axis=0)
    basis, _ = np.linalg.qr(centered)
    frame["diabetes_ehr_percent_2022_2024"] = basis[:, 0]
    frame["pct_age_65_plus"] = basis[:, 1]
    frame["pct_female"] = basis[:, 3]
    frame["pct_below_fpl"] = basis[:, 4]
    frame["capture_rate_mean_2022_2024"] = basis[:, 5]
    signal_weight = np.sqrt(explained_fraction / 2)
    frame["hypertension_ehr_percent_2022_2024"] = (
        signal_weight * basis[:, 0]
        + signal_weight * basis[:, 1]
        + np.sqrt(1 - explained_fraction) * basis[:, 2]
    )
    return frame


def test_readiness_uses_frozen_primary_adjustment_set() -> None:
    readiness = assess_primary_model_readiness(_model_frame()).set_index("model_id")

    assert ADJUSTMENT_COVARIATES == (
        "pct_age_65_plus",
        "pct_female",
        "pct_below_fpl",
        "capture_rate_mean_2022_2024",
    )
    assert readiness.loc["C1", "design_columns"] == 7
    assert readiness.loc["C2", "design_columns"] == 6
    assert set(readiness["status"]) == {"ready_for_adjusted_primary_model"}


def test_readiness_withholds_vif_above_five_and_names_predictor() -> None:
    above = assess_primary_model_readiness(_orthogonal_predictor_frame(0.81)).set_index(
        "model_id"
    )

    assert above.loc["C1", "maximum_vif"] > 5.0
    assert above.loc["C1", "status"] == "withheld_vif_above_5"
    assert above.loc["C1", "vif_offending_predictor"] == (
        "hypertension_ehr_percent_2022_2024"
    )


@pytest.mark.parametrize(
    ("maximum_vif", "expected_status"),
    [
        (5.0, "ready_for_adjusted_primary_model"),
        (np.nextafter(5.0, np.inf), "withheld_vif_above_5"),
    ],
)
def test_readiness_uses_exact_representable_vif_boundary(
    monkeypatch: pytest.MonkeyPatch,
    maximum_vif: float,
    expected_status: str,
) -> None:
    import chicagohealthmap.analysis.sap_analyses as module

    original = module._design_gate_diagnostics

    def boundary_diagnostics(
        complete: pd.DataFrame, predictors: list[str]
    ) -> dict[str, object]:
        diagnostics = original(complete, predictors)
        diagnostics["maximum_vif"] = maximum_vif
        diagnostics["vif_offending_predictor"] = predictors[0]
        return diagnostics

    monkeypatch.setattr(module, "_design_gate_diagnostics", boundary_diagnostics)

    status = assess_primary_model_readiness(_model_frame()).set_index("model_id").loc[
        "C1", "status"
    ]

    assert status == expected_status


def test_readiness_withholds_pairwise_correlation_strictly_above_point_eight() -> None:
    frame = _orthogonal_predictor_frame(0.2)
    diabetes = frame["diabetes_ehr_percent_2022_2024"].to_numpy()
    candidate = np.random.default_rng(77).normal(size=len(frame))
    candidate -= candidate.mean()
    candidate -= diabetes * (candidate @ diabetes)
    noise = candidate / np.linalg.norm(candidate)
    boundary = frame.copy()
    boundary["hypertension_ehr_percent_2022_2024"] = 0.80 * diabetes + 0.60 * noise
    frame["hypertension_ehr_percent_2022_2024"] = (
        0.81 * diabetes + np.sqrt(1 - 0.81**2) * noise
    )

    boundary_result = assess_primary_model_readiness(boundary).set_index("model_id").loc["C1"]
    result = assess_primary_model_readiness(frame).set_index("model_id").loc["C1"]

    assert boundary_result["maximum_absolute_pairwise_correlation"] == pytest.approx(0.80)
    assert boundary_result["status"] == "ready_for_adjusted_primary_model"
    assert result["maximum_absolute_pairwise_correlation"] == pytest.approx(0.81)
    assert result["status"] == "withheld_pairwise_correlation_above_0_80"
    assert "pairwise_correlation_above_0_80" in result["failed_gates"]


def test_model_gate_diagnostics_are_deterministic_and_predictor_granular() -> None:
    frame = _orthogonal_predictor_frame(0.81)

    first = build_model_gate_diagnostics(frame)
    second = build_model_gate_diagnostics(frame)

    pd.testing.assert_frame_equal(first, second)
    assert list(first.groupby("model_id", sort=False).size()) == [6, 5]
    assert list(first.loc[first["model_id"].eq("C1"), "predictor"]) == [
        "hypertension_ehr_percent_2022_2024",
        "diabetes_ehr_percent_2022_2024",
        *ADJUSTMENT_COVARIATES,
    ]
    assert {
        "predictor_vif",
        "maximum_vif",
        "maximum_absolute_pairwise_correlation",
        "standardized_design_condition_number",
        "design_rank",
        "design_columns",
        "hc3_covariance_status",
        "status",
        "failed_gates",
        "results_authorized",
    } <= set(first.columns)
    assert set(first["results_authorized"]) == {False}


def test_withheld_model_is_separate_from_primary_and_labeled_audit_only() -> None:
    frame = _orthogonal_predictor_frame(0.81)

    primary = fit_primary_models(frame)
    audit = fit_audit_only_exploratory_models(frame)

    assert set(primary) == {"C2"}
    assert set(audit) == {"C1"}
    c1 = audit["C1"]
    assert c1.metadata["analysis_status"] == "audit_only_exploratory"
    assert c1.metadata["primary_estimand_executed"] is False
    assert c1.metadata["results_authorized"] is False
    assert set(c1.coefficients["analysis_status"]) == {"audit_only_exploratory"}
    assert set(c1.coefficients["primary_estimand_executed"]) == {False}
    assert set(c1.coefficients["results_authorized"]) == {False}
    assert set(c1.contrasts["analysis_status"]) == {"audit_only_exploratory"}
    assert set(c1.contrasts["primary_estimand_executed"]) == {False}
    assert set(c1.contrasts["results_authorized"]) == {False}
    residuals = build_adjusted_residuals(audit)["C1"]
    assert residuals.attrs["analysis_status"] == "audit_only_exploratory"
    assert residuals.attrs["primary_estimand_executed"] is False
    assert residuals.attrs["results_authorized"] is False


def test_primary_models_return_scaled_coefficients_and_joint_contrast() -> None:
    results = fit_primary_models(_model_frame())
    c1 = results["C1"]
    c2 = results["C2"]
    assert {
        "alpha",
        "beta_h",
        "beta_d",
        "gamma_age65",
        "gamma_female",
        "gamma_poverty",
        "gamma_capture",
    } == set(c1.coefficients["term"])
    assert set(c1.coefficients["role"]) == {"intercept", "exposure", "adjustment"}
    coefficients = c1.coefficients.set_index("term")
    joint = c1.contrasts.set_index("estimand_id").loc["C1", "estimate"]
    assert joint == pytest.approx(
        coefficients.loc["beta_h", "estimate"] + coefficients.loc["beta_d", "estimate"]
    )
    assert c1.contrasts.set_index("estimand_id").loc["C1", "confidence_level"] == pytest.approx(
        0.975
    )
    assert coefficients.loc["beta_h", "confidence_level"] == pytest.approx(0.95)
    assert coefficients.loc["beta_d", "confidence_level"] == pytest.approx(0.95)
    assert c2.coefficients.set_index("term").loc["beta_c", "confidence_level"] == pytest.approx(
        0.975
    )


def test_adjusted_residuals_are_keyed_to_primary_model_population() -> None:
    frame = _model_frame()
    frame.loc[0, "copd_exposure_complete"] = False
    results = fit_primary_models(frame)

    residuals = build_adjusted_residuals(results)

    assert set(residuals) == {"C1", "C2"}
    assert len(residuals["C1"]) == 77
    assert len(residuals["C2"]) == 76
    assert residuals["C1"].attrs["analysis_status"] == "adjusted_primary_residual"


@pytest.mark.parametrize("missing", [COVARIATES, *[[column] for column in COVARIATES]])
def test_readiness_withholds_both_models_when_adjustment_covariates_missing(
    missing: list[str],
) -> None:
    frame = _model_frame().drop(columns=missing)

    result = assess_primary_model_readiness(frame)

    assert list(result["model_id"]) == ["C1", "C2"]
    assert set(result["status"]) == {"withheld_missing_covariates"}
    assert set(result["missing_covariates"]) == {"|".join(sorted(missing))}
    assert set(result["n_exposure_outcome_complete"]) == {77}
    assert result["n_adjusted_complete"].isna().all()
    assert result["failed_gates"].str.contains("missing_covariates").all()


def test_model_specific_eligibility_gives_frozen_like_c1_77_and_c2_76() -> None:
    frame = _model_frame()
    frame.loc[0, "copd_exposure_complete"] = False

    readiness = assess_primary_model_readiness(frame).set_index("model_id")
    sensitivity = fit_minimally_adjusted_sensitivities(frame).set_index("estimand_id")

    assert readiness.loc["C1", "n_exposure_outcome_complete"] == 77
    assert readiness.loc["C2", "n_exposure_outcome_complete"] == 76
    assert sensitivity.loc["C1", "n"] == 77
    assert sensitivity.loc["C1-H", "n"] == 77
    assert sensitivity.loc["C1-D", "n"] == 77
    assert sensitivity.loc["C2", "n"] == 76
    assert set(sensitivity["adjustment_set"]) == {"unadjusted"}
    assert set(sensitivity["model_id"]) == {"C1_unadjusted", "C2_unadjusted"}


def test_unadjusted_residuals_reuse_model_specific_eligibility_and_fit() -> None:
    frame = _model_frame()
    frame.loc[frame["geography_id"].eq("76"), "copd_exposure_complete"] = False

    residuals = build_unadjusted_sensitivity_residuals(frame, "C2")
    eligible = frame.loc[~frame["geography_id"].eq("76")]
    design = np.column_stack([np.ones(len(eligible)), eligible["copd_ehr_percent_2022_2024"]])
    outcome = eligible["life_expectancy_mean_2022_2024"].to_numpy()
    expected = outcome - design @ np.linalg.solve(design.T @ design, design.T @ outcome)

    assert residuals.name == "residual"
    assert list(residuals.index) == list(eligible["geography_id"])
    assert residuals.to_numpy() == pytest.approx(expected)
    assert "76" not in residuals.index
    assert residuals.attrs == {
        "model_id": "C2_unadjusted",
        "analysis_status": "supported_sensitivity_not_primary",
        "primary_estimand_executed": False,
        "adjustment_set": "unadjusted",
        "n": 76,
    }


def test_unadjusted_residuals_reject_unsupported_model_id() -> None:
    with pytest.raises(CaseStudyAnalysisError, match="unsupported.*model_id"):
        build_unadjusted_sensitivity_residuals(_model_frame(), "C3")


def test_readiness_gates_sample_size_distinct_values_and_rank() -> None:
    too_small = assess_primary_model_readiness(_model_frame(69))
    assert set(too_small["status"]) == {"withheld_insufficient_complete_areas"}
    assert set(too_small["n_complete"]) == {69}

    few_distinct = _model_frame()
    few_distinct["copd_ehr_percent_2022_2024"] = np.arange(77) % 9
    distinct_result = assess_primary_model_readiness(few_distinct)
    assert distinct_result.set_index("model_id").loc["C2", "status"] == (
        "withheld_insufficient_exposure_variation"
    )
    assert (
        "insufficient_exposure_variation"
        in distinct_result.set_index("model_id").loc["C2", "failed_gates"]
    )

    deficient = _model_frame()
    deficient["pct_female"] = 2 * deficient["pct_age_65_plus"]
    rank_result = assess_primary_model_readiness(deficient)
    assert set(rank_result["status"]) == {"withheld_rank_deficient"}
    assert set(rank_result["failed_gates"]) == {"rank_deficient"}

    zero_iqr = _model_frame()
    zero_iqr["copd_ehr_percent_2022_2024"] = [0.0] * 68 + [float(value) for value in range(1, 10)]
    zero_iqr_result = assess_primary_model_readiness(zero_iqr).set_index("model_id")
    assert zero_iqr_result.loc["C2", "status"] == "withheld_nonpositive_exposure_iqr"
    assert "nonpositive_exposure_iqr" in zero_iqr_result.loc["C2", "failed_gates"]


def test_readiness_fails_closed_when_hc3_covariance_is_not_finite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import chicagohealthmap.analysis.sap_analyses as module

    monkeypatch.setattr(module, "_hc3_covariance", lambda *_: np.full((7, 7), np.nan))

    result = assess_primary_model_readiness(_model_frame())

    assert set(result["status"]) == {"withheld_covariance_failure"}
    assert set(result["failed_gates"]) == {"covariance_failure"}


def test_readiness_fails_closed_for_constant_predictor_without_nonfinite_metrics() -> None:
    frame = _model_frame()
    frame["pct_female"] = 50.0

    result = assess_primary_model_readiness(frame)

    assert set(result["status"]) == {"withheld_rank_deficient"}
    assert set(result["failed_gates"]) == {"rank_deficient"}
    assert result["maximum_vif"].isna().all()
    assert result["standardized_design_condition_number"].isna().all()
    assert result["maximum_absolute_pairwise_correlation"].map(
        lambda value: pd.isna(value) or np.isfinite(value)
    ).all()


def test_readiness_inventory_recomputes_adjusted_n_and_variation() -> None:
    missing = _model_frame()
    missing.loc[:7, "pct_female"] = np.nan
    result = assess_primary_model_readiness(missing).set_index("model_id")
    assert set(result["n_exposure_outcome_complete"]) == {77}
    assert set(result["n_adjusted_complete"]) == {69}
    assert result["failed_gates"].str.contains("adjusted_insufficient_complete_areas").all()

    variation = _model_frame()
    variation["hypertension_ehr_percent_2022_2024"] = np.arange(77) % 10
    variation.loc[variation["hypertension_ehr_percent_2022_2024"].eq(9), "pct_female"] = np.nan
    c1 = assess_primary_model_readiness(variation).set_index("model_id").loc["C1"]
    assert c1["n_exposure_outcome_complete"] == 77
    assert c1["n_adjusted_complete"] == 70
    assert "adjusted_insufficient_exposure_variation" in c1["failed_gates"]


def _manual_hc3(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    inverse = np.linalg.inv(x.T @ x)
    beta = inverse @ x.T @ y
    residual = y - x @ beta
    leverage = np.diag(x @ inverse @ x.T)
    meat = x.T @ np.diag((residual / (1 - leverage)) ** 2) @ x
    return beta, inverse @ meat @ inverse


def test_sensitivity_contrasts_use_joint_covariance_frozen_iqrs_and_ci_levels() -> None:
    frame = _model_frame()
    result = fit_minimally_adjusted_sensitivities(frame).set_index("estimand_id")

    h = frame["hypertension_ehr_percent_2022_2024"].to_numpy()
    d = frame["diabetes_ehr_percent_2022_2024"].to_numpy()
    c = frame["copd_ehr_percent_2022_2024"].to_numpy()
    y = frame["life_expectancy_mean_2022_2024"].to_numpy()
    h_iqr, d_iqr, c_iqr = (
        np.percentile(values, 75) - np.percentile(values, 25) for values in (h, d, c)
    )
    beta_c1, covariance_c1 = _manual_hc3(np.column_stack([np.ones(len(frame)), h, d]), y)
    joint = beta_c1[1] * h_iqr + beta_c1[2] * d_iqr
    joint_variance = (
        h_iqr**2 * covariance_c1[1, 1]
        + d_iqr**2 * covariance_c1[2, 2]
        + 2 * h_iqr * d_iqr * covariance_c1[1, 2]
    )
    beta_c2, covariance_c2 = _manual_hc3(np.column_stack([np.ones(len(frame)), c]), y)

    assert result.loc["C1", "estimate"] == pytest.approx(joint)
    assert result.loc["C1", "standard_error"] == pytest.approx(np.sqrt(joint_variance))
    assert result.loc["C1-H", "estimate"] == pytest.approx(beta_c1[1] * h_iqr)
    assert result.loc["C1-D", "estimate"] == pytest.approx(beta_c1[2] * d_iqr)
    assert result.loc["C2", "estimate"] == pytest.approx(beta_c2[1] * c_iqr)
    assert result.loc["C1", "confidence_level"] == pytest.approx(0.975)
    assert result.loc["C2", "confidence_level"] == pytest.approx(0.975)
    assert result.loc["C1-H", "confidence_level"] == pytest.approx(0.95)
    assert result.loc["C1-D", "confidence_level"] == pytest.approx(0.95)
    z = stats.norm.ppf(0.9875)
    assert result.loc["C1", "ci_low"] == pytest.approx(joint - z * np.sqrt(joint_variance))
    assert set(result["analysis_status"]) == {"supported_sensitivity_not_primary"}
    assert set(result["interpretation"]) == {"noncausal_ecological_association"}
    assert set(result["n"]) == {77}
    assert result.loc["C1", "hypertension_iqr"] == pytest.approx(h_iqr)
    assert result.loc["C1", "diabetes_iqr"] == pytest.approx(d_iqr)


def test_influence_uses_strict_thresholds_and_reports_leave_one_out_fragility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import chicagohealthmap.analysis.sap_analyses as module

    frame = _model_frame()
    n = len(frame)
    p = 3
    diagnostics = pd.DataFrame(
        {
            "cooks_distance": [4 / n, 4 / n + 1e-9, 0.0, 0.0] + [0.0] * (n - 4),
            "leverage": [0.0, 0.0, 2 * p / n, 2 * p / n + 1e-9] + [0.0] * (n - 4),
            "externally_studentized_residual": [0.0, 0.0, 3.0, -3.000000001] + [0.0] * (n - 4),
        }
    )
    monkeypatch.setattr(module, "_influence_diagnostics", lambda *_: diagnostics)
    monkeypatch.setattr(module, "_contrast_estimate", lambda *_: -1.0)
    estimates = iter([-1.0, -1.3, -1.3000001, 0.2] + [-0.9] * (n - 4))
    monkeypatch.setattr(module, "_leave_one_out_estimate", lambda *_: next(estimates))

    areas, summary = summarize_influence(frame, "C1")
    row = summary.iloc[0]

    assert not bool(areas.loc[0, "cooks_flag"])
    assert bool(areas.loc[1, "cooks_flag"])
    assert not bool(areas.loc[2, "leverage_flag"])
    assert bool(areas.loc[3, "leverage_flag"])
    assert not bool(areas.loc[2, "studentized_residual_flag"])
    assert bool(areas.loc[3, "studentized_residual_flag"])
    assert not bool(areas.loc[1, "leave_one_out_magnitude_change_gt_30pct"])
    assert bool(areas.loc[2, "leave_one_out_magnitude_change_gt_30pct"])
    assert row["leave_one_out_min"] == pytest.approx(-1.3000001)
    assert row["leave_one_out_max"] == pytest.approx(0.2)
    assert bool(row["any_sign_change"])
    assert bool(row["any_magnitude_change_gt_30pct"])
    assert not bool(row["magnitude_change_at_exact_30pct_is_fragile"])
    assert row["areas_retained_in_principal_fit"] == n


def test_influence_diagnostics_match_independent_matrix_reference() -> None:
    import chicagohealthmap.analysis.sap_analyses as module

    frame = _model_frame()
    x = np.column_stack([np.ones(len(frame)), frame["copd_ehr_percent_2022_2024"].to_numpy()])
    y = frame["life_expectancy_mean_2022_2024"].to_numpy()
    inverse = np.linalg.inv(x.T @ x)
    beta = inverse @ x.T @ y
    residual = y - x @ beta
    leverage = np.diag(x @ inverse @ x.T)
    n, p = x.shape
    mse = residual @ residual / (n - p)
    cooks = residual**2 / (p * mse) * leverage / (1 - leverage) ** 2
    deleted_mse = ((n - p) * mse - residual**2 / (1 - leverage)) / (n - p - 1)
    external = residual / np.sqrt(deleted_mse * (1 - leverage))

    actual = module._influence_diagnostics(x, y)

    assert actual["cooks_distance"].to_numpy() == pytest.approx(cooks)
    assert actual["leverage"].to_numpy() == pytest.approx(leverage)
    assert actual["externally_studentized_residual"].to_numpy() == pytest.approx(external)


def test_influence_leave_one_out_holds_full_population_iqrs_fixed() -> None:
    frame = _model_frame()
    _, summary = summarize_influence(frame, "C1")
    h_iqr = np.percentile(frame[EXPOSURES["C1"][0]], 75) - np.percentile(
        frame[EXPOSURES["C1"][0]], 25
    )
    d_iqr = np.percentile(frame[EXPOSURES["C1"][1]], 75) - np.percentile(
        frame[EXPOSURES["C1"][1]], 25
    )
    estimates = []
    for index in range(len(frame)):
        reduced = frame.drop(index=index)
        x = np.column_stack(
            [
                np.ones(len(reduced)),
                reduced[EXPOSURES["C1"][0]],
                reduced[EXPOSURES["C1"][1]],
            ]
        )
        beta = np.linalg.solve(x.T @ x, x.T @ reduced["life_expectancy_mean_2022_2024"])
        estimates.append(beta[1] * h_iqr + beta[2] * d_iqr)

    row = summary.iloc[0]
    assert row["leave_one_out_min"] == pytest.approx(min(estimates))
    assert row["leave_one_out_max"] == pytest.approx(max(estimates))


def test_influence_exclude_all_flagged_runs_when_below_primary_n_but_estimable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import chicagohealthmap.analysis.sap_analyses as module

    frame = _model_frame()
    diagnostics = pd.DataFrame(
        {
            "cooks_distance": [1.0] * 8 + [0.0] * 69,
            "leverage": [0.0] * 77,
            "externally_studentized_residual": [0.0] * 77,
        }
    )
    monkeypatch.setattr(module, "_influence_diagnostics", lambda *_: diagnostics)

    _, summary = summarize_influence(frame, "C1")

    row = summary.iloc[0]
    assert row["flagged_areas"] == 8
    assert row["exclude_all_flagged_n"] == 69
    assert row["exclude_all_flagged_status"] == "supported_sensitivity_not_primary"
    assert np.isfinite(row["exclude_all_flagged_estimate"])
    assert "exclude_all_flagged_direction_stable" in summary
    assert "exclude_all_flagged_absolute_percentage_change" in summary
    assert "exclude_all_flagged_interval_overlap" in summary
    assert "exclude_all_flagged_threshold_crossed" in summary


def test_influence_at_n70_runs_n69_leave_one_out_with_frozen_iqr() -> None:
    frame = _model_frame(70)

    areas, summary = summarize_influence(frame, "C2")

    assert len(areas) == 70
    assert areas["leave_one_out_estimate"].notna().all()
    assert summary.iloc[0]["areas_retained_in_principal_fit"] == 70


def _temporal_dataset(n: int = 77) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for area_number in range(1, n + 1):
        area = f"{area_number:02d}"
        for year in range(2019, 2025):
            hypertension = 8 + (area_number % 23) + year - 2019
            diabetes_one = 2 + (area_number % 7)
            diabetes_two = 3 + (area_number % 11) + year - 2019
            copd = 4 + (area_number % 17) + (year - 2019) // 2
            life_expectancy = (
                90 - 0.1 * hypertension - 0.2 * (diabetes_one + diabetes_two) - 0.3 * copd
            )
            for condition, numerator in [
                ("hypertension", hypertension),
                ("diabetes_with_complication", diabetes_one),
                ("diabetes_without_complication", diabetes_two),
                ("copd", copd),
            ]:
                rows.append(
                    {
                        "geography_type": "chicago_community_area",
                        "geography_id": area,
                        "time_period": str(year),
                        "condition_id": condition,
                        "condition_family": "diabetes"
                        if condition.startswith("diabetes")
                        else condition,
                        "numerator": numerator,
                        "denominator": 100,
                        "published_measure_value": numerator,
                        "suppression_flag": False,
                        "combined_diabetes_semantics_approved": True,
                        "capture_rate": 0.5,
                        "life_expectancy_estimate": life_expectancy,
                        "life_expectancy_time_period": str(year),
                        "source_id": "capricorn_chicagohealthmap_export_2026_05_27",
                        "snapshot_id": "capricorn_chicagohealthmap_export_2026_05_27_2026-05-27",
                    }
                )
    return pd.DataFrame(rows)


def test_temporal_outputs_separate_periods_and_preserve_exact_denominators() -> None:
    dataset = _temporal_dataset()
    annual, leave_one_out = summarize_temporal_robustness(dataset)

    model_rows = annual.query(
        "row_type == 'association_model' and analysis_id in ['annual_2019', 'annual_2020', 'annual_2021', 'annual_2022', 'annual_2023', 'annual_2024']"
    )
    assert set(model_rows["time_period"]) == {"2019", "2020", "2021", "2022", "2023", "2024"}
    assert set(model_rows["estimand_id"]) == {"C1", "C1-H", "C1-D", "C2"}
    roles = model_rows.drop_duplicates("time_period").set_index("time_period")["period_role"]
    assert roles.to_dict() == {
        "2019": "baseline",
        "2020": "disruption",
        "2021": "disruption",
        "2022": "primary_annual",
        "2023": "primary_annual",
        "2024": "primary_annual",
    }
    assert set(model_rows["n_paired"]) == {77}
    assert set(model_rows["analysis_status"]) == {"supported_temporal_sensitivity_not_primary"}
    assert model_rows["estimate"].notna().all()
    assert set(leave_one_out["omitted_year"]) == {"2022", "2023", "2024"}
    assert set(leave_one_out["included_years"]) == {"2022|2023", "2022|2024", "2023|2024"}
    assert not leave_one_out["included_years"].str.contains("2020|2021", regex=True).any()
    assert set(leave_one_out["estimand_id"]) == {"C1", "C1-H", "C1-D", "C2"}
    assert set(leave_one_out["n_paired"]) == {77}
    assert leave_one_out["estimate"].notna().all()
    assert set(model_rows["iqr_source_population_id"]) == {
        "pooled_2022_2024_model_specific_eligible_population"
    }
    c1_rows = model_rows.query("estimand_id in ['C1', 'C1-H', 'C1-D']")
    assert c1_rows["hypertension_iqr"].nunique() == 1
    assert c1_rows["diabetes_iqr"].nunique() == 1
    assert model_rows.query("estimand_id == 'C2'")["copd_iqr"].nunique() == 1
    all_comparable = pd.concat(
        [annual.query("row_type == 'association_model'"), leave_one_out], ignore_index=True
    )
    assert (
        all_comparable.query("estimand_id in ['C1', 'C1-H', 'C1-D']")["hypertension_iqr"].nunique()
        == 1
    )
    assert (
        all_comparable.query("estimand_id in ['C1', 'C1-H', 'C1-D']")["diabetes_iqr"].nunique() == 1
    )
    assert all_comparable.query("estimand_id == 'C2'")["copd_iqr"].nunique() == 1
    assert set(model_rows["total_geography_universe"]) == {77}
    assert set(model_rows["n_exposure_complete"]) == {77}
    assert set(model_rows["n_outcome_complete"]) == {77}
    assert set(model_rows["n_paired"]) == {77}
    assert set(model_rows["exposure_source_id"]) == {"capricorn_chicagohealthmap_export_2026_05_27"}
    assert set(model_rows["outcome_source_id"]) == {"chicago_health_atlas_life_expectancy"}
    assert set(model_rows["outcome_snapshot_id"]) == {
        "chicago_health_atlas_life_expectancy_2026-07-13"
    }
    assert set(model_rows["outcome_lineage_id"]) == {
        "config/source_registry.yml#chicago_health_atlas_life_expectancy"
    }
    assert not (model_rows["exposure_source_id"] == model_rows["outcome_source_id"]).any()


def test_temporal_outcomes_are_order_invariant_and_reject_repeated_row_disagreement() -> None:
    dataset = _temporal_dataset()
    expected, _ = summarize_temporal_robustness(dataset)
    shuffled, _ = summarize_temporal_robustness(dataset.sample(frac=1, random_state=42))
    columns = ["analysis_id", "estimand_id", "n_paired", "estimate"]
    pd.testing.assert_frame_equal(
        expected.query("row_type == 'association_model'")[columns].reset_index(drop=True),
        shuffled.query("row_type == 'association_model'")[columns].reset_index(drop=True),
    )

    mismatch = dataset.copy()
    mismatch.loc[0, "life_expectancy_estimate"] += 1
    with pytest.raises(CaseStudyAnalysisError, match="inconsistent repeated Atlas outcome"):
        summarize_temporal_robustness(mismatch)

    missingness = dataset.copy()
    missingness.loc[0, "life_expectancy_estimate"] = np.nan
    with pytest.raises(CaseStudyAnalysisError, match="inconsistent repeated Atlas outcome"):
        summarize_temporal_robustness(missingness)


def test_temporal_pooled_outcome_requires_every_requested_aligned_year() -> None:
    dataset = _temporal_dataset()
    missing = dataset["geography_id"].eq("01") & dataset["time_period"].eq("2022")
    dataset.loc[missing, "life_expectancy_estimate"] = np.nan
    annual, leave_one_out = summarize_temporal_robustness(dataset)

    n_by_omission = leave_one_out.query("estimand_id == 'C1'").set_index("omitted_year")["n_paired"]
    assert n_by_omission.to_dict() == {"2022": 77, "2023": 76, "2024": 76}
    aligned = annual.query(
        "row_type == 'association_model' and analysis_id == 'most_recent_common_outcome_alignment'"
    )
    assert set(aligned["n_paired"]) == {77}

    mismatched = _temporal_dataset()
    period = mismatched["geography_id"].eq("01") & mismatched["time_period"].eq("2023")
    mismatched.loc[period, "life_expectancy_time_period"] = "2022"
    _, mismatched_loyo = summarize_temporal_robustness(mismatched)
    assert set(mismatched_loyo.query("omitted_year != '2023'")["n_paired"]) == {76}


def test_temporal_annual_estimate_matches_independent_reference() -> None:
    dataset = _temporal_dataset()
    annual, _ = summarize_temporal_robustness(dataset)
    c1 = annual.query(
        "row_type == 'association_model' and time_period == '2019' and estimand_id == 'C1'"
    ).iloc[0]
    year = dataset.query("time_period == '2019'")
    hypertension = year.query("condition_id == 'hypertension'").sort_values("geography_id")
    diabetes = (
        year.query("condition_family == 'diabetes'")
        .groupby("geography_id")
        .agg(numerator=("numerator", "sum"), denominator=("denominator", "max"))
    )
    outcome = hypertension["life_expectancy_estimate"].to_numpy()
    h_value = 100 * hypertension["numerator"].to_numpy() / hypertension["denominator"].to_numpy()
    d_value = 100 * diabetes["numerator"].to_numpy() / diabetes["denominator"].to_numpy()
    design = np.column_stack([np.ones(len(hypertension)), h_value, d_value])
    beta = np.linalg.solve(design.T @ design, design.T @ outcome)
    expected = beta[1] * (np.percentile(h_value, 75) - np.percentile(h_value, 25)) + beta[2] * (
        np.percentile(d_value, 75) - np.percentile(d_value, 25)
    )
    assert c1["n_paired"] == 77
    assert c1["estimate"] == pytest.approx(expected)


def test_temporal_combined_diabetes_requires_both_unsuppressed_components() -> None:
    dataset = _temporal_dataset()
    missing = (
        (dataset["geography_id"] == "02")
        & (dataset["time_period"] == "2023")
        & (dataset["condition_id"] == "diabetes_with_complication")
    )
    dataset.loc[missing, "suppression_flag"] = True

    annual, leave_one_out = summarize_temporal_robustness(dataset)

    diabetes_2023 = annual.query(
        "row_type == 'association_model' and estimand_id == 'C1' and time_period == '2023'"
    ).iloc[0]
    assert diabetes_2023["n_paired"] == 76
    omitted_2022 = leave_one_out.query("estimand_id == 'C1' and omitted_year == '2022'").iloc[0]
    assert omitted_2022["n_paired"] == 76


def test_temporal_diabetes_denominator_mismatch_is_ineligible() -> None:
    dataset = _temporal_dataset()
    mismatch = (
        (dataset["geography_id"] == "02")
        & (dataset["time_period"] == "2023")
        & (dataset["condition_id"] == "diabetes_with_complication")
    )
    dataset.loc[mismatch, "denominator"] = 101

    annual, leave_one_out = summarize_temporal_robustness(dataset)

    c1 = annual.query(
        "row_type == 'association_model' and estimand_id == 'C1' and time_period == '2023'"
    ).iloc[0]
    assert c1["n_paired"] == 76
    assert c1["diabetes_denominator_mismatch_geographies"] == 1
    mismatch_by_omission = leave_one_out.groupby("omitted_year")[
        "diabetes_denominator_mismatch_geographies"
    ].first()
    assert mismatch_by_omission.to_dict() == {"2022": 1, "2023": 0, "2024": 1}


def test_temporal_disruption_candidate_is_pending_until_continuity_review() -> None:
    dataset = _temporal_dataset()
    severe = (
        (dataset["geography_id"] == "01")
        & (dataset["time_period"] == "2020")
        & (dataset["condition_id"] == "hypertension")
    )
    dataset.loc[severe, ["numerator", "denominator", "capture_rate"]] = [90, 100, 0.05]

    annual, _ = summarize_temporal_robustness(dataset)

    candidate = annual.query("row_type == 'disruption_candidate'").iloc[0]
    assert candidate["candidate_id"] == "01|hypertension|2020"
    assert candidate["disruption_status"] == "candidate_disruption_pending_continuity_review"
    exclusion = annual.query(
        "row_type == 'association_model' and analysis_id == 'exclude_confirmed_disruption_areas'"
    )
    assert set(exclusion["status"]) == {"withheld_pending_continuity_review"}


def test_temporal_confirmed_disruption_runs_exclusion_only_after_resolution() -> None:
    dataset = _temporal_dataset()
    dataset["continuity_review_status"] = "resolved_no_discontinuity"
    severe = (
        (dataset["geography_id"] == "01")
        & (dataset["time_period"] == "2020")
        & (dataset["condition_id"] == "hypertension")
    )
    dataset.loc[severe, "numerator"] = 90

    annual, _ = summarize_temporal_robustness(dataset)

    candidate = annual.query("row_type == 'disruption_candidate'").iloc[0]
    assert candidate["disruption_status"] == "confirmed_disruption_after_continuity_review"
    exclusion = annual.query(
        "row_type == 'association_model' and analysis_id == 'exclude_confirmed_disruption_areas'"
    )
    assert set(exclusion["status"]) == {"supported_sensitivity_not_primary"}
    assert set(exclusion["n_paired"]) == {76}


def test_temporal_continuity_state_is_closed_and_diabetes_components_must_agree() -> None:
    dataset = _temporal_dataset()
    dataset["continuity_review_status"] = "pending"
    severe = (
        dataset["geography_id"].eq("01")
        & dataset["time_period"].eq("2020")
        & dataset["condition_family"].eq("diabetes")
    )
    dataset.loc[severe, "numerator"] = [40, 50]
    dataset.loc[
        severe & dataset["condition_id"].eq("diabetes_with_complication"),
        "continuity_review_status",
    ] = "resolved_no_discontinuity"
    annual, _ = summarize_temporal_robustness(dataset)
    candidate = annual.query("row_type == 'disruption_candidate'").iloc[0]
    assert candidate["disruption_status"] == "candidate_disruption_pending_continuity_review"

    invalid = _temporal_dataset()
    invalid["continuity_review_status"] = "invented_state"
    with pytest.raises(CaseStudyAnalysisError, match="continuity_review_status"):
        summarize_temporal_robustness(invalid)


def test_temporal_diabetes_resolved_plus_null_continuity_normalizes_to_pending() -> None:
    dataset = _temporal_dataset()
    dataset["continuity_review_status"] = "pending"
    severe = (
        dataset["geography_id"].eq("01")
        & dataset["time_period"].eq("2020")
        & dataset["condition_family"].eq("diabetes")
    )
    dataset.loc[severe, "numerator"] = [40, 50]
    dataset.loc[
        severe & dataset["condition_id"].eq("diabetes_with_complication"),
        "continuity_review_status",
    ] = "resolved_no_discontinuity"
    dataset.loc[
        severe & dataset["condition_id"].eq("diabetes_without_complication"),
        "continuity_review_status",
    ] = None

    annual, _ = summarize_temporal_robustness(dataset)

    candidate = annual.query("row_type == 'disruption_candidate'").iloc[0]
    assert candidate["continuity_review_status"] == "pending"
    assert candidate["disruption_status"] == "candidate_disruption_pending_continuity_review"
    withheld = annual.query(
        "row_type == 'association_model' and analysis_id == 'exclude_confirmed_disruption_areas'"
    )
    assert set(withheld["status"]) == {"withheld_pending_continuity_review"}
    assert set(withheld["total_geography_universe"]) == {77}
    assert set(withheld["iqr_source_population_id"]) == {
        "pooled_2022_2024_model_specific_eligible_population"
    }
    assert withheld.query("estimand_id in ['C1', 'C1-H', 'C1-D']")["hypertension_iqr"].notna().all()
    assert withheld.query("estimand_id == 'C2'")["copd_iqr"].notna().all()
    assert set(withheld["exposure_source_id"]) == {"capricorn_chicagohealthmap_export_2026_05_27"}
    assert set(withheld["outcome_source_id"]) == {"chicago_health_atlas_life_expectancy"}
    assert withheld["n_paired"].isna().all()
    assert withheld["n_suppression_excluded"].isna().all()


def test_temporal_missing_entire_condition_year_emits_explicit_withheld_rows() -> None:
    dataset = _temporal_dataset()
    dataset = dataset.loc[~(dataset["time_period"].eq("2024") & dataset["condition_id"].eq("copd"))]

    annual, _ = summarize_temporal_robustness(dataset)

    c2 = annual.query(
        "row_type == 'association_model' and estimand_id == 'C2' and time_period == '2024'"
    ).iloc[0]
    assert c2["n_paired"] == 0
    assert c2["status"] == "withheld_no_eligible_pairs"


def test_temporal_outputs_most_recent_common_outcome_alignment_rows() -> None:
    annual, _ = summarize_temporal_robustness(_temporal_dataset())

    assert {"candidate_id", "disruption_status", "continuity_review_status"} <= set(annual.columns)
    aligned = annual.query(
        "row_type == 'association_model' and analysis_id == 'most_recent_common_outcome_alignment'"
    )
    assert set(aligned["estimand_id"]) == {"C1", "C1-H", "C1-D", "C2"}
    assert set(aligned["included_years"]) == {"2022|2023|2024"}
    assert set(aligned["outcome_years"]) == {"2024"}
    assert set(aligned["n_paired"]) == {77}


@pytest.mark.parametrize(
    ("function_name", "frame"),
    [
        ("readiness", pd.DataFrame()),
        ("sensitivity", pd.DataFrame()),
        ("influence", pd.DataFrame()),
        ("temporal", pd.DataFrame()),
    ],
)
def test_public_interfaces_reject_empty_frames(function_name: str, frame: pd.DataFrame) -> None:
    with pytest.raises(CaseStudyAnalysisError):
        if function_name == "readiness":
            assess_primary_model_readiness(frame)
        elif function_name == "sensitivity":
            fit_minimally_adjusted_sensitivities(frame)
        elif function_name == "influence":
            summarize_influence(frame, "C1")
        else:
            summarize_temporal_robustness(frame)


def test_model_interfaces_reject_duplicate_ids_and_malformed_numeric_values() -> None:
    duplicate = pd.concat([_model_frame(), _model_frame().iloc[[0]]], ignore_index=True)
    with pytest.raises(CaseStudyAnalysisError, match="duplicate geography_id"):
        fit_minimally_adjusted_sensitivities(duplicate)

    malformed = _model_frame()
    malformed["copd_ehr_percent_2022_2024"] = malformed["copd_ehr_percent_2022_2024"].astype(object)
    malformed.loc[0, "copd_ehr_percent_2022_2024"] = "not-a-number"
    with pytest.raises(CaseStudyAnalysisError, match="malformed numeric"):
        assess_primary_model_readiness(malformed)


def test_nonempty_missing_column_inputs_fail_closed() -> None:
    with pytest.raises(CaseStudyAnalysisError, match="missing columns"):
        assess_primary_model_readiness(_model_frame().drop(columns=["copd_exposure_complete"]))
    with pytest.raises(CaseStudyAnalysisError, match="missing columns"):
        summarize_temporal_robustness(
            _temporal_dataset().drop(columns=["life_expectancy_time_period"])
        )
    with pytest.raises(CaseStudyAnalysisError, match="missing columns"):
        summarize_temporal_robustness(_temporal_dataset().drop(columns=["source_id"]))


def test_temporal_rejects_duplicate_keys_malformed_flags_and_nonfinite_values() -> None:
    dataset = _temporal_dataset()
    duplicate = pd.concat([dataset, dataset.iloc[[0]]], ignore_index=True)
    with pytest.raises(CaseStudyAnalysisError, match="duplicate keys"):
        summarize_temporal_robustness(duplicate)

    malformed_flag = dataset.copy()
    malformed_flag["suppression_flag"] = malformed_flag["suppression_flag"].astype(object)
    malformed_flag.loc[0, "suppression_flag"] = "False"
    with pytest.raises(CaseStudyAnalysisError, match="suppression_flag"):
        summarize_temporal_robustness(malformed_flag)

    nonfinite = dataset.copy()
    nonfinite["numerator"] = nonfinite["numerator"].astype(float)
    nonfinite.loc[0, "numerator"] = np.inf
    with pytest.raises(CaseStudyAnalysisError, match="non-finite"):
        summarize_temporal_robustness(nonfinite)
