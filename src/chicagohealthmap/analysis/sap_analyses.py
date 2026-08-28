"""Fail-closed statistical analysis helpers for the signed Chicago SAP."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from scipy import stats  # type: ignore[import-untyped]

from chicagohealthmap.analysis.case_studies import (
    COMMUNITY,
    DIABETES_COMPONENTS,
    CaseStudyAnalysisError,
    combined_diabetes_is_approved,
)

OUTCOME = "life_expectancy_mean_2022_2024"
HYPERTENSION = "hypertension_ehr_percent_2022_2024"
DIABETES = "diabetes_ehr_percent_2022_2024"
COPD = "copd_ehr_percent_2022_2024"
ADJUSTMENT_COVARIATES = (
    "pct_age_65_plus",
    "pct_female",
    "pct_below_fpl",
    "capture_rate_mean_2022_2024",
)
MODEL_EXPOSURES = {"C1": (HYPERTENSION, DIABETES), "C2": (COPD,)}
MODEL_ELIGIBILITY_FLAGS = {
    "C1": ("hypertension_exposure_complete", "diabetes_exposure_complete"),
    "C2": ("copd_exposure_complete",),
}
TEMPORAL_YEARS = tuple(str(year) for year in range(2019, 2025))
PRIMARY_YEARS = ("2022", "2023", "2024")
CONTINUITY_STATES = {"pending", "resolved_no_discontinuity", "resolved_discontinuity"}
OUTCOME_SOURCE_ID = "chicago_health_atlas_life_expectancy"
OUTCOME_SNAPSHOT_ID = "chicago_health_atlas_life_expectancy_2026-07-13"
OUTCOME_LINEAGE_ID = "config/source_registry.yml#chicago_health_atlas_life_expectancy"
IQR_SOURCE_POPULATION_ID = "pooled_2022_2024_model_specific_eligible_population"


@dataclass(frozen=True)
class GovernedModelResult:
    """Candidate adjusted model outputs with frozen scaling and provenance metadata."""

    model_id: str
    coefficients: pd.DataFrame
    contrasts: pd.DataFrame
    residuals: pd.Series
    outcome: pd.Series
    design: np.ndarray
    design_columns: tuple[str, ...]
    scaling: dict[str, dict[str, Any]]
    metadata: dict[str, Any]


def fit_primary_models(frame: pd.DataFrame) -> dict[str, GovernedModelResult]:
    """Fit only adjusted models that pass every frozen readiness gate."""

    readiness = assess_primary_model_readiness(frame)
    ready_models = readiness.loc[
        readiness["status"].eq("ready_for_adjusted_primary_model"), "model_id"
    ].tolist()
    return _fit_adjusted_models(
        frame,
        ready_models,
        analysis_status="freeze_candidate_primary_model_unsecured",
        primary_estimand_executed=True,
    )


def fit_audit_only_exploratory_models(
    frame: pd.DataFrame,
) -> dict[str, GovernedModelResult]:
    """Fit estimable collinearity failures in a non-primary diagnostic bundle."""

    readiness = assess_primary_model_readiness(frame)
    audit_statuses = {
        "withheld_pairwise_correlation_above_0_80",
        "withheld_vif_above_5",
    }
    audit_models = readiness.loc[readiness["status"].isin(audit_statuses), "model_id"].tolist()
    return _fit_adjusted_models(
        frame,
        audit_models,
        analysis_status="audit_only_exploratory",
        primary_estimand_executed=False,
    )


def _fit_adjusted_models(
    frame: pd.DataFrame,
    model_ids: Sequence[str],
    *,
    analysis_status: str,
    primary_estimand_executed: bool,
) -> dict[str, GovernedModelResult]:
    """Fit a governed subset of the prespecified adjusted models."""

    working = _validate_model_frame(frame)
    results: dict[str, GovernedModelResult] = {}
    for model_id, exposure_tuple in MODEL_EXPOSURES.items():
        if model_id not in model_ids:
            continue
        exposures = list(exposure_tuple)
        complete = _eligible_model_data(working, model_id, include_covariates=True)
        if len(complete) < 70:
            raise CaseStudyAnalysisError(
                f"{model_id} primary model has fewer than 70 complete areas"
            )
        if any(int(complete[column].nunique()) < 10 for column in exposures):
            raise CaseStudyAnalysisError(
                f"{model_id} primary model exposure has fewer than 10 distinct values"
            )

        transformed = complete.copy()
        scaling: dict[str, dict[str, Any]] = {}
        for column in exposures:
            center = float(transformed[column].mean())
            scale = _iqr(transformed[column])
            if scale <= 0 or not np.isfinite(scale):
                raise CaseStudyAnalysisError(f"{model_id} exposure {column} has nonpositive IQR")
            transformed[column] = (transformed[column] - center) / scale
            scaling[column] = {"center": center, "scale": scale, "scale_type": "IQR"}
        for column in ADJUSTMENT_COVARIATES:
            center = float(transformed[column].mean())
            scale = float(transformed[column].std(ddof=1))
            if scale <= 0 or not np.isfinite(scale):
                raise CaseStudyAnalysisError(
                    f"{model_id} adjustment covariate {column} has nonpositive SD"
                )
            transformed[column] = (transformed[column] - center) / scale
            scaling[column] = {"center": center, "scale": scale, "scale_type": "SD"}

        predictors = [*exposures, *ADJUSTMENT_COVARIATES]
        design = _design_matrix(transformed, predictors)
        if np.linalg.matrix_rank(design) < design.shape[1]:
            raise CaseStudyAnalysisError(
                f"{model_id} primary model design matrix is rank deficient"
            )
        outcome = transformed[OUTCOME].to_numpy(dtype=float)
        try:
            beta = np.linalg.solve(design.T @ design, design.T @ outcome)
            covariance = _hc3_covariance(design, outcome)
        except (ArithmeticError, np.linalg.LinAlgError, ValueError) as error:
            raise CaseStudyAnalysisError(
                f"{model_id} primary model covariance is not estimable"
            ) from error
        if not np.isfinite(beta).all() or not np.isfinite(covariance).all():
            raise CaseStudyAnalysisError(f"{model_id} primary model covariance is not finite")

        term_names = ["alpha"]
        term_names.extend(
            {HYPERTENSION: "beta_h", DIABETES: "beta_d", COPD: "beta_c"}[column]
            for column in exposures
        )
        term_names.extend(
            {
                "pct_age_65_plus": "gamma_age65",
                "pct_female": "gamma_female",
                "pct_below_fpl": "gamma_poverty",
                "capture_rate_mean_2022_2024": "gamma_capture",
            }[column]
            for column in ADJUSTMENT_COVARIATES
        )
        roles = [
            "intercept",
            *("exposure" for _ in exposures),
            *("adjustment" for _ in ADJUSTMENT_COVARIATES),
        ]
        scales = [
            "mean-centered anchor",
            *("1 frozen IQR" for _ in exposures),
            *("1 SD" for _ in ADJUSTMENT_COVARIATES),
        ]
        critical_primary = float(stats.norm.ppf(0.9875))
        rows: list[dict[str, Any]] = []
        for index, (term, role, scale_label) in enumerate(
            zip(term_names, roles, scales, strict=True)
        ):
            coefficient_confidence = 0.975 if role == "exposure" and model_id == "C2" else 0.95
            critical = (
                critical_primary
                if coefficient_confidence == 0.975
                else float(stats.norm.ppf(0.975))
            )
            standard_error = float(np.sqrt(covariance[index, index]))
            estimate = float(beta[index])
            rows.append(
                {
                    "model_id": model_id,
                    "term": term,
                    "role": role,
                    "estimate": estimate,
                    "standard_error": standard_error,
                    "ci_low": estimate - critical * standard_error,
                    "ci_high": estimate + critical * standard_error,
                    "confidence_level": coefficient_confidence,
                    "scale": scale_label,
                    "unit": "life_expectancy_years",
                    "n": len(transformed),
                    "covariance_type": "HC3",
                    "analysis_status": analysis_status,
                    "primary_estimand_executed": primary_estimand_executed,
                    "results_authorized": False,
                }
            )

        coefficient_table = pd.DataFrame.from_records(rows)
        contrast_rows: list[dict[str, Any]] = []
        if model_id == "C1":
            joint_vector = np.zeros(len(beta), dtype=float)
            joint_vector[1 : 1 + len(exposures)] = 1.0
            contrast_rows.extend(
                [
                    _primary_contrast_record(
                        "C1",
                        model_id,
                        joint_vector,
                        beta,
                        covariance,
                        len(complete),
                        0.975,
                        analysis_status,
                        primary_estimand_executed,
                    ),
                    _primary_contrast_record(
                        "C1-H",
                        model_id,
                        np.array([0.0, 1.0, 0.0, *([0.0] * 4)]),
                        beta,
                        covariance,
                        len(complete),
                        0.95,
                        analysis_status,
                        primary_estimand_executed,
                    ),
                    _primary_contrast_record(
                        "C1-D",
                        model_id,
                        np.array([0.0, 0.0, 1.0, *([0.0] * 4)]),
                        beta,
                        covariance,
                        len(complete),
                        0.95,
                        analysis_status,
                        primary_estimand_executed,
                    ),
                ]
            )
        else:
            vector = np.zeros(len(beta), dtype=float)
            vector[1] = 1.0
            contrast_rows.append(
                _primary_contrast_record(
                    "C2",
                    model_id,
                    vector,
                    beta,
                    covariance,
                    len(complete),
                    0.975,
                    analysis_status,
                    primary_estimand_executed,
                )
            )

        residuals = pd.Series(
            outcome - design @ beta,
            index=transformed["geography_id"].astype(str),
            name="residual",
            dtype=float,
        )
        results[model_id] = GovernedModelResult(
            model_id=model_id,
            coefficients=coefficient_table,
            contrasts=pd.DataFrame.from_records(contrast_rows),
            residuals=residuals,
            outcome=pd.Series(
                outcome,
                index=transformed["geography_id"].astype(str),
                name=OUTCOME,
                dtype=float,
            ),
            design=design.copy(),
            design_columns=tuple(["intercept", *predictors]),
            scaling=scaling,
            metadata={
                "analysis_status": analysis_status,
                "primary_estimand_executed": primary_estimand_executed,
                "results_authorized": False,
                "estimator": "unweighted_ols",
                "covariance_type": "HC3",
                "n": len(complete),
                "adjustment_set": list(ADJUSTMENT_COVARIATES),
                "exposures": exposures,
            },
        )
    return results


def build_coefficient_table(results: dict[str, GovernedModelResult]) -> pd.DataFrame:
    """Combine full alpha/beta/gamma coefficient rows in deterministic order."""

    if not results:
        raise CaseStudyAnalysisError("primary model results are empty")
    order = {"C1": 0, "C2": 1}
    output = pd.concat([result.coefficients for result in results.values()], ignore_index=True)
    return output.sort_values(
        ["model_id", "role", "term"],
        key=lambda values: values.map(order) if values.name == "model_id" else values,
        kind="mergesort",
    ).reset_index(drop=True)


def build_adjusted_residuals(
    results: dict[str, GovernedModelResult],
) -> dict[str, pd.Series]:
    """Return adjusted residuals with explicit primary-diagnostic metadata."""

    if not results:
        raise CaseStudyAnalysisError("adjusted model results are empty")
    output: dict[str, pd.Series] = {}
    for model_id, result in results.items():
        residuals = result.residuals.copy()
        primary_estimand_executed = bool(
            result.metadata.get("primary_estimand_executed", True)
        )
        residuals.attrs = {
            "model_id": model_id,
            "analysis_status": (
                "adjusted_primary_residual"
                if primary_estimand_executed
                else "audit_only_exploratory"
            ),
            "primary_estimand_executed": primary_estimand_executed,
            "adjustment_set": "|".join(ADJUSTMENT_COVARIATES),
            "n": len(residuals),
            "results_authorized": False,
        }
        output[model_id] = residuals
    return output


def _primary_contrast_record(
    estimand_id: str,
    model_id: str,
    contrast: np.ndarray,
    beta: np.ndarray,
    covariance: np.ndarray,
    n: int,
    confidence_level: float,
    analysis_status: str,
    primary_estimand_executed: bool,
) -> dict[str, Any]:
    estimate = float(contrast @ beta)
    variance = float(contrast @ covariance @ contrast)
    if variance < 0 or not np.isfinite(variance):
        raise CaseStudyAnalysisError(f"{estimand_id} contrast covariance is not estimable")
    standard_error = float(np.sqrt(variance))
    critical = float(stats.norm.ppf(1 - (1 - confidence_level) / 2))
    return {
        "estimand_id": estimand_id,
        "model_id": model_id,
        "estimate": estimate,
        "standard_error": standard_error,
        "ci_low": estimate - critical * standard_error,
        "ci_high": estimate + critical * standard_error,
        "confidence_level": confidence_level,
        "n": n,
        "covariance_type": "HC3",
        "estimator": "unweighted_ols",
        "adjustment_set": "pct_age_65_plus|pct_female|pct_below_fpl|capture_rate_mean_2022_2024",
        "analysis_status": analysis_status,
        "primary_estimand_executed": primary_estimand_executed,
        "results_authorized": False,
        "interpretation": "noncausal_ecological_association",
    }


def assess_primary_model_readiness(frame: pd.DataFrame) -> pd.DataFrame:
    """Evaluate every frozen execution gate for the adjusted C1 and C2 models."""

    _validate_nonempty(frame, "primary model frame")
    _require_columns(
        frame,
        {
            "geography_id",
            OUTCOME,
            HYPERTENSION,
            DIABETES,
            COPD,
            "life_expectancy_years_complete",
            *MODEL_ELIGIBILITY_FLAGS["C1"],
            *MODEL_ELIGIBILITY_FLAGS["C2"],
        },
        "model frame",
    )
    _validate_unique(frame, ["geography_id"], "model frame")
    missing_covariates = sorted(set(ADJUSTMENT_COVARIATES) - set(frame.columns))
    numeric_columns = [OUTCOME, HYPERTENSION, DIABETES, COPD, "life_expectancy_years_complete"]
    numeric_columns.extend(column for column in ADJUSTMENT_COVARIATES if column in frame)
    working = _validated_numeric_frame(frame, numeric_columns, "model frame")
    _validate_model_flags(working)

    records: list[dict[str, Any]] = []
    for model_id, exposures in MODEL_EXPOSURES.items():
        exposure_outcome = _eligible_model_data(working, model_id, include_covariates=False)
        distinct_values = {
            exposure: int(exposure_outcome[exposure].nunique()) for exposure in exposures
        }
        failed_gates: list[str] = []
        if len(exposure_outcome) < 70:
            failed_gates.append("insufficient_complete_areas")
        if any(value < 10 for value in distinct_values.values()):
            failed_gates.append("insufficient_exposure_variation")
        if missing_covariates:
            failed_gates.append("missing_covariates")
        record: dict[str, Any] = {
            "model_id": model_id,
            "status": "ready_for_adjusted_primary_model",
            "reason": "all_frozen_readiness_gates_passed",
            "missing_covariates": "",
            "n_complete": len(exposure_outcome),
            "n_exposure_outcome_complete": len(exposure_outcome),
            "n_adjusted_complete": pd.NA,
            "design_rank": pd.NA,
            "design_columns": 1 + len(exposures) + len(ADJUSTMENT_COVARIATES),
            "maximum_vif": pd.NA,
            "vif_offending_predictor": "",
            "maximum_absolute_pairwise_correlation": pd.NA,
            "maximum_correlation_predictor_1": "",
            "maximum_correlation_predictor_2": "",
            "standardized_design_condition_number": pd.NA,
            "hc3_covariance_status": "not_assessed",
            "minimum_distinct_exposure_values": min(distinct_values.values()),
            "distinct_exposure_values": "|".join(
                f"{key}={value}" for key, value in sorted(distinct_values.items())
            ),
            "failed_gates": "|".join(failed_gates),
        }
        if missing_covariates:
            record.update(
                status="withheld_missing_covariates",
                reason="required_adjustment_covariates_absent",
                missing_covariates="|".join(missing_covariates),
            )
            records.append(record)
            continue
        complete = _eligible_model_data(working, model_id, include_covariates=True)
        record["n_adjusted_complete"] = len(complete)
        record["n_complete"] = len(complete)
        adjusted_distinct = {exposure: int(complete[exposure].nunique()) for exposure in exposures}
        if len(complete) < 70:
            record["failed_gates"] = _append_gate(
                record["failed_gates"], "adjusted_insufficient_complete_areas"
            )
        if any(value < 10 for value in adjusted_distinct.values()):
            record["failed_gates"] = _append_gate(
                record["failed_gates"], "adjusted_insufficient_exposure_variation"
            )
        if len(complete) < 70:
            record.update(
                status="withheld_insufficient_complete_areas",
                reason="fewer_than_70_complete_community_areas",
            )
            records.append(record)
            continue
        distinct = min(int(complete[column].nunique()) for column in exposures)
        record["minimum_distinct_exposure_values"] = distinct
        if distinct < 10:
            record.update(
                status="withheld_insufficient_exposure_variation",
                reason="required_exposure_has_fewer_than_10_distinct_values",
            )
            records.append(record)
            continue
        exposure_iqrs = {column: _iqr(complete[column]) for column in exposures}
        if any(value <= 0 or not np.isfinite(value) for value in exposure_iqrs.values()):
            record.update(
                status="withheld_nonpositive_exposure_iqr",
                reason="required_exposure_has_nonpositive_iqr",
                failed_gates=_append_gate(record["failed_gates"], "nonpositive_exposure_iqr"),
            )
            records.append(record)
            continue
        predictors = [*exposures, *ADJUSTMENT_COVARIATES]
        diagnostics = _design_gate_diagnostics(complete, predictors)
        record.update(
            design_rank=diagnostics["design_rank"],
            maximum_vif=diagnostics["maximum_vif"],
            vif_offending_predictor=diagnostics["vif_offending_predictor"],
            maximum_absolute_pairwise_correlation=diagnostics[
                "maximum_absolute_pairwise_correlation"
            ],
            maximum_correlation_predictor_1=diagnostics[
                "maximum_correlation_predictor_1"
            ],
            maximum_correlation_predictor_2=diagnostics[
                "maximum_correlation_predictor_2"
            ],
            standardized_design_condition_number=diagnostics[
                "standardized_design_condition_number"
            ],
            hc3_covariance_status=diagnostics["hc3_covariance_status"],
        )
        if diagnostics["design_rank"] < record["design_columns"]:
            record.update(
                status="withheld_rank_deficient",
                reason="design_matrix_not_full_rank",
                failed_gates=_append_gate(record["failed_gates"], "rank_deficient"),
            )
            records.append(record)
            continue
        if diagnostics["hc3_covariance_status"] != "estimable_and_finite":
            record.update(
                status="withheld_covariance_failure",
                reason="hc3_covariance_not_estimable_and_finite",
                failed_gates=_append_gate(record["failed_gates"], "covariance_failure"),
            )
            records.append(record)
            continue
        if diagnostics["maximum_absolute_pairwise_correlation"] > 0.80:
            record.update(
                status="withheld_pairwise_correlation_above_0_80",
                reason="predictor_pairwise_correlation_exceeds_0_80",
                failed_gates=_append_gate(
                    record["failed_gates"], "pairwise_correlation_above_0_80"
                ),
            )
            records.append(record)
            continue
        maximum_vif = float(diagnostics["maximum_vif"])
        if maximum_vif > 5.0:
            record.update(
                status="withheld_vif_above_5",
                reason="predictor_vif_exceeds_5",
                failed_gates=_append_gate(record["failed_gates"], "vif_above_5"),
            )
        records.append(record)
    return pd.DataFrame.from_records(records)


def build_model_gate_diagnostics(frame: pd.DataFrame) -> pd.DataFrame:
    """Return deterministic predictor-level diagnostics with model gate fields."""

    readiness = assess_primary_model_readiness(frame)
    readiness_by_model = readiness.set_index("model_id").to_dict(orient="index")
    missing_covariates = set(ADJUSTMENT_COVARIATES) - set(frame.columns)
    working = _validate_model_frame(frame) if not missing_covariates else None
    records: list[dict[str, Any]] = []
    for model_id, exposure_tuple in MODEL_EXPOSURES.items():
        predictors = [*exposure_tuple, *ADJUSTMENT_COVARIATES]
        predictor_vifs: dict[str, float] = {}
        if working is not None:
            complete = _eligible_model_data(working, model_id, include_covariates=True)
            if len(complete) >= 70:
                predictor_vifs = _design_gate_diagnostics(complete, predictors)[
                    "predictor_vifs"
                ]
        model_fields = readiness_by_model[model_id]
        for predictor in predictors:
            records.append(
                {
                    "model_id": model_id,
                    "predictor": predictor,
                    "predictor_role": (
                        "exposure" if predictor in exposure_tuple else "adjustment"
                    ),
                    "predictor_vif": predictor_vifs.get(predictor, pd.NA),
                    **model_fields,
                    "results_authorized": False,
                }
            )
    return pd.DataFrame.from_records(records)


def fit_minimally_adjusted_sensitivities(frame: pd.DataFrame) -> pd.DataFrame:
    """Fit unadjusted HC3 sensitivity contrasts without claiming primary execution."""

    working = _validate_model_frame(frame)
    c1_data = _eligible_model_data(working, "C1", False)
    c2_data = _eligible_model_data(working, "C2", False)
    c2 = _fit_model(c2_data, [COPD])
    c_iqr = _iqr(c2["data"][COPD])
    if c_iqr <= 0:
        raise CaseStudyAnalysisError("sensitivity model has a nonpositive frozen exposure IQR")

    records: list[dict[str, Any]] = []
    if len(c1_data) >= 70:
        c1 = _fit_model(c1_data, [HYPERTENSION, DIABETES])
        h_iqr = _iqr(c1["data"][HYPERTENSION])
        d_iqr = _iqr(c1["data"][DIABETES])
        if min(h_iqr, d_iqr) <= 0:
            raise CaseStudyAnalysisError("sensitivity model has a nonpositive frozen exposure IQR")
        c1_contrasts = {
            "C1": np.array([0.0, h_iqr, d_iqr]),
            "C1-H": np.array([0.0, h_iqr, 0.0]),
            "C1-D": np.array([0.0, 0.0, d_iqr]),
        }
        records.extend(
            _contrast_record(
                estimand_id,
                c1,
                contrast,
                0.975 if estimand_id == "C1" else 0.95,
                h_iqr,
                d_iqr,
                np.nan,
            )
            for estimand_id, contrast in c1_contrasts.items()
        )
    records.append(_contrast_record("C2", c2, np.array([0.0, c_iqr]), 0.975, np.nan, np.nan, c_iqr))
    order = {"C1": 0, "C1-H": 1, "C1-D": 2, "C2": 3}
    return pd.DataFrame.from_records(records).sort_values(
        "estimand_id", key=lambda values: values.map(order), kind="mergesort"
    )


def build_unadjusted_sensitivity_residuals(frame: pd.DataFrame, model_id: str) -> pd.Series:
    """Return residuals from the governed model-specific unadjusted sensitivity fit."""

    if model_id not in MODEL_EXPOSURES:
        raise CaseStudyAnalysisError(f"unsupported sensitivity residual model_id: {model_id}")
    working = _validate_model_frame(frame)
    eligible = _eligible_model_data(working, model_id, include_covariates=False)
    fit = _fit_model(eligible, list(MODEL_EXPOSURES[model_id]))
    residuals = fit["outcome"] - fit["design"] @ fit["beta"]
    output = pd.Series(
        residuals,
        index=eligible["geography_id"].astype(str),
        name="residual",
        dtype=float,
    )
    output.attrs = {
        "model_id": f"{model_id}_unadjusted",
        "analysis_status": "supported_sensitivity_not_primary",
        "primary_estimand_executed": False,
        "adjustment_set": "unadjusted",
        "n": len(output),
    }
    return output


def summarize_influence(frame: pd.DataFrame, model_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return exact SAP influence flags and model-level deletion summaries."""

    if model_id not in MODEL_EXPOSURES:
        raise CaseStudyAnalysisError(f"unsupported influence model_id: {model_id}")
    working = _validate_model_frame(frame)
    exposures = list(MODEL_EXPOSURES[model_id])
    complete = _eligible_model_data(working, model_id, False).reset_index(drop=True)
    if len(complete) < 70:
        raise CaseStudyAnalysisError("influence model has fewer than 70 complete areas")
    fit = _fit_model(complete, exposures)
    design = fit["design"]
    n, p = design.shape
    diagnostics = _influence_diagnostics(design, fit["outcome"])
    areas = pd.concat([complete[["geography_id"]], diagnostics.reset_index(drop=True)], axis=1)
    areas["cooks_threshold"] = 4 / n
    areas["leverage_threshold"] = 2 * p / n
    areas["studentized_residual_threshold"] = 3.0
    areas["cooks_flag"] = areas["cooks_distance"] > areas["cooks_threshold"]
    areas["leverage_flag"] = areas["leverage"] > areas["leverage_threshold"]
    areas["studentized_residual_flag"] = (
        areas["externally_studentized_residual"].abs() > areas["studentized_residual_threshold"]
    )
    areas["any_influence_flag"] = areas[
        ["cooks_flag", "leverage_flag", "studentized_residual_flag"]
    ].any(axis=1)

    frozen_iqrs = {exposure: _iqr(complete[exposure]) for exposure in exposures}
    original = _contrast_estimate(fit, model_id, frozen_iqrs)
    principal_low, principal_high = _contrast_interval(fit, model_id, frozen_iqrs, 0.975)
    leave_one_out = np.array(
        [_leave_one_out_estimate(complete, model_id, index, frozen_iqrs) for index in range(n)],
        dtype=float,
    )
    finite_leave_one_out = leave_one_out[np.isfinite(leave_one_out)]
    if len(finite_leave_one_out) != n:
        raise CaseStudyAnalysisError("leave-one-area-out covariance or contrast failed")
    sign_changes = np.sign(leave_one_out) != np.sign(original)
    if original == 0:
        magnitude_change = np.where(np.abs(leave_one_out) > 0, np.inf, 0.0)
    else:
        magnitude_change = np.abs(np.abs(leave_one_out) - abs(original)) / abs(original)
    magnitude_fragile = (magnitude_change > 0.30) & ~np.isclose(
        magnitude_change, 0.30, rtol=1e-12, atol=1e-12
    )
    areas["leave_one_out_estimate"] = leave_one_out
    areas["leave_one_out_sign_change"] = sign_changes
    areas["leave_one_out_magnitude_change_ratio"] = magnitude_change
    areas["leave_one_out_magnitude_change_gt_30pct"] = magnitude_fragile

    unflagged = complete.loc[~areas["any_influence_flag"].to_numpy()].copy()
    exclude_flagged_estimate = np.nan
    exclude_flagged_low = np.nan
    exclude_flagged_high = np.nan
    exclude_flagged_status = "withheld_not_estimable"
    if len(unflagged) > len(exposures) + 1:
        try:
            exclude_fit = _fit_model(unflagged, exposures, minimum_n=len(exposures) + 2)
            exclude_flagged_estimate = _contrast_estimate(exclude_fit, model_id, frozen_iqrs)
            exclude_flagged_low, exclude_flagged_high = _contrast_interval(
                exclude_fit, model_id, frozen_iqrs, 0.975
            )
            exclude_flagged_status = "supported_sensitivity_not_primary"
        except (CaseStudyAnalysisError, np.linalg.LinAlgError, ValueError):
            pass
    exclusion_direction_stable: object = pd.NA
    exclusion_percentage_change = np.nan
    exclusion_interval_overlap: object = pd.NA
    exclusion_threshold_crossed: object = pd.NA
    if np.isfinite(exclude_flagged_estimate):
        exclusion_direction_stable = bool(np.sign(exclude_flagged_estimate) == np.sign(original))
        exclusion_percentage_change = (
            np.inf
            if original == 0 and exclude_flagged_estimate != 0
            else 100 * abs(abs(exclude_flagged_estimate) - abs(original)) / abs(original)
            if original != 0
            else 0.0
        )
        exclusion_interval_overlap = bool(
            exclude_flagged_low <= principal_high and principal_low <= exclude_flagged_high
        )
        exclusion_threshold_crossed = bool(
            not exclusion_direction_stable or exclusion_percentage_change > 30
        )
    summary = pd.DataFrame.from_records(
        [
            {
                "model_id": model_id,
                "principal_sensitivity_estimate": original,
                "areas_retained_in_principal_fit": n,
                "design_parameters": p,
                "flagged_areas": int(areas["any_influence_flag"].sum()),
                "leave_one_out_min": float(leave_one_out.min()),
                "leave_one_out_max": float(leave_one_out.max()),
                "any_sign_change": bool(sign_changes.any()),
                "any_magnitude_change_gt_30pct": bool(magnitude_fragile.any()),
                "magnitude_change_at_exact_30pct_is_fragile": False,
                "fragile": bool(sign_changes.any() or magnitude_fragile.any()),
                "exclude_all_flagged_estimate": exclude_flagged_estimate,
                "exclude_all_flagged_n": len(unflagged),
                "exclude_all_flagged_status": exclude_flagged_status,
                "exclude_all_flagged_ci_low": exclude_flagged_low,
                "exclude_all_flagged_ci_high": exclude_flagged_high,
                "exclude_all_flagged_direction_stable": exclusion_direction_stable,
                "exclude_all_flagged_absolute_percentage_change": exclusion_percentage_change,
                "exclude_all_flagged_interval_overlap": exclusion_interval_overlap,
                "exclude_all_flagged_threshold_crossed": exclusion_threshold_crossed,
                "analysis_status": "supported_sensitivity_not_primary",
            }
        ]
    )
    return areas.sort_values("geography_id", kind="mergesort"), summary


def summarize_temporal_robustness(
    dataset: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit annual and leave-one-primary-year-out association sensitivities."""

    required = {
        "geography_type",
        "geography_id",
        "time_period",
        "condition_id",
        "condition_family",
        "numerator",
        "denominator",
        "suppression_flag",
        "capture_rate",
        "life_expectancy_estimate",
        "life_expectancy_time_period",
        "source_id",
        "snapshot_id",
    }
    _validate_nonempty(dataset, "temporal dataset")
    _require_columns(dataset, required, "temporal dataset")
    _validate_unique(
        dataset,
        ["geography_type", "geography_id", "time_period", "condition_id"],
        "temporal dataset",
    )
    valid_flags = dataset["suppression_flag"].map(lambda value: isinstance(value, (bool, np.bool_)))
    if not bool(valid_flags.all()):
        raise CaseStudyAnalysisError("temporal suppression_flag must contain booleans")
    working = _validated_numeric_frame(
        dataset,
        ["numerator", "denominator", "capture_rate", "life_expectancy_estimate"],
        "temporal dataset",
    )
    working["time_period"] = working["time_period"].astype(str)
    working = working.loc[
        working["geography_type"].eq(COMMUNITY) & working["time_period"].isin(TEMPORAL_YEARS)
    ].copy()
    if working.empty:
        raise CaseStudyAnalysisError("temporal dataset has no community-area rows for 2019-2024")
    if "continuity_review_status" in working:
        states = set(working["continuity_review_status"].dropna().astype(str).unique())
        invalid_states = states - CONTINUITY_STATES
        if invalid_states:
            raise CaseStudyAnalysisError(
                f"temporal continuity_review_status has unsupported values: {sorted(invalid_states)}"
            )
    _validate_repeated_atlas_outcomes(working)
    unexpected_diabetes = (
        set(working.loc[working["condition_family"].eq("diabetes"), "condition_id"].dropna())
        - DIABETES_COMPONENTS
    )
    if unexpected_diabetes:
        raise CaseStudyAnalysisError(
            f"temporal dataset has unexpected diabetes components: {sorted(unexpected_diabetes)}"
        )
    annual_area = _add_disruption_flags(_temporal_area_years(working))
    primary_frame = _pooled_association_frame(annual_area, PRIMARY_YEARS, PRIMARY_YEARS)
    frozen_iqrs = _frozen_temporal_iqrs(primary_frame)
    provenance = _temporal_provenance(working)
    annual_records: list[dict[str, Any]] = []
    for year in TEMPORAL_YEARS:
        annual_frame = _annual_association_frame(annual_area, year)
        annual_records.extend(
            _temporal_model_records(
                annual_frame,
                analysis_id=f"annual_{year}",
                time_period=year,
                period_role=_period_role(year),
                included_years=year,
                outcome_years=year,
                diabetes_mismatches=int(
                    annual_area.loc[
                        annual_area["time_period"].eq(year)
                        & annual_area["condition_id"].eq("diabetes"),
                        "diabetes_denominator_mismatch",
                    ].sum()
                ),
                frozen_iqrs=frozen_iqrs,
                provenance=provenance,
            )
        )

    candidates = annual_area.loc[annual_area["disruption_candidate"]].copy()
    for row in candidates.itertuples(index=False):
        annual_records.append(_disruption_candidate_record(row))

    pending_candidates = candidates.loc[
        candidates["disruption_status"].eq("candidate_disruption_pending_continuity_review")
    ]
    confirmed_candidates = candidates.loc[
        candidates["disruption_status"].eq("confirmed_disruption_after_continuity_review")
    ]
    if not pending_candidates.empty:
        annual_records.extend(
            _withheld_temporal_records(
                analysis_id="exclude_confirmed_disruption_areas",
                status="withheld_pending_continuity_review",
                included_years="2022|2023|2024",
                outcome_years="2022|2023|2024",
                frame=primary_frame,
                frozen_iqrs=frozen_iqrs,
                provenance=provenance,
                diabetes_mismatches=_diabetes_mismatch_geographies(annual_area, PRIMARY_YEARS),
            )
        )
    else:
        confirmed_areas = set(confirmed_candidates["geography_id"])
        exclusion_frame = primary_frame.loc[~primary_frame["geography_id"].isin(confirmed_areas)]
        annual_records.extend(
            _temporal_model_records(
                exclusion_frame,
                analysis_id="exclude_confirmed_disruption_areas",
                time_period="2022-2024",
                period_role="disruption_exclusion_sensitivity",
                included_years="2022|2023|2024",
                outcome_years="2022|2023|2024",
                diabetes_mismatches=_diabetes_mismatch_geographies(annual_area, PRIMARY_YEARS),
                frozen_iqrs=frozen_iqrs,
                provenance=provenance,
            )
        )

    recent_frame = _pooled_association_frame(annual_area, PRIMARY_YEARS, ("2024",))
    annual_records.extend(
        _temporal_model_records(
            recent_frame,
            analysis_id="most_recent_common_outcome_alignment",
            time_period="2022-2024",
            period_role="outcome_alignment_sensitivity",
            included_years="2022|2023|2024",
            outcome_years="2024",
            diabetes_mismatches=_diabetes_mismatch_geographies(annual_area, PRIMARY_YEARS),
            frozen_iqrs=frozen_iqrs,
            provenance=provenance,
        )
    )

    leave_records: list[dict[str, Any]] = []
    for omitted in PRIMARY_YEARS:
        included = tuple(year for year in PRIMARY_YEARS if year != omitted)
        frame = _pooled_association_frame(annual_area, included, included)
        records = _temporal_model_records(
            frame,
            analysis_id=f"leave_out_{omitted}",
            time_period="2022-2024",
            period_role="leave_one_primary_year_out",
            included_years="|".join(included),
            outcome_years="|".join(included),
            diabetes_mismatches=_diabetes_mismatch_geographies(annual_area, included),
            frozen_iqrs=frozen_iqrs,
            provenance=provenance,
        )
        for record in records:
            record["omitted_year"] = omitted
        leave_records.extend(records)
    annual = pd.DataFrame.from_records(annual_records).sort_values(
        ["row_type", "analysis_id", "estimand_id", "candidate_id"],
        kind="mergesort",
        na_position="last",
    )
    leave_one_out = pd.DataFrame.from_records(leave_records).sort_values(
        ["omitted_year", "estimand_id"], kind="mergesort"
    )
    return annual, leave_one_out


def _validate_model_frame(frame: pd.DataFrame) -> pd.DataFrame:
    _validate_nonempty(frame, "sensitivity model frame")
    required = {
        "geography_id",
        OUTCOME,
        HYPERTENSION,
        DIABETES,
        COPD,
        "life_expectancy_years_complete",
        *MODEL_ELIGIBILITY_FLAGS["C1"],
        *MODEL_ELIGIBILITY_FLAGS["C2"],
    }
    _require_columns(frame, required, "sensitivity model frame")
    _validate_unique(frame, ["geography_id"], "sensitivity model frame")
    output = _validated_numeric_frame(
        frame,
        [OUTCOME, HYPERTENSION, DIABETES, COPD, "life_expectancy_years_complete"],
        "model frame",
    )
    _validate_model_flags(output)
    return output


def _validate_model_flags(frame: pd.DataFrame) -> None:
    for column in {*MODEL_ELIGIBILITY_FLAGS["C1"], *MODEL_ELIGIBILITY_FLAGS["C2"]}:
        valid = frame[column].map(lambda value: isinstance(value, (bool, np.bool_)))
        if not bool(valid.all()):
            raise CaseStudyAnalysisError(f"model frame {column} must contain booleans")


def _eligible_model_data(
    frame: pd.DataFrame, model_id: str, include_covariates: bool
) -> pd.DataFrame:
    exposures = list(MODEL_EXPOSURES[model_id])
    flags = list(MODEL_ELIGIBILITY_FLAGS[model_id])
    columns = ["geography_id", OUTCOME, *exposures]
    if include_covariates:
        columns.extend(ADJUSTMENT_COVARIATES)
    eligible = frame[flags].all(axis=1) & frame["life_expectancy_years_complete"].eq(3)
    return frame.loc[eligible, columns].dropna().copy()


def _fit_model(frame: pd.DataFrame, exposures: list[str], minimum_n: int = 70) -> dict[str, Any]:
    data = frame[[OUTCOME, *exposures]].dropna().copy()
    if len(data) < minimum_n:
        raise CaseStudyAnalysisError(f"sensitivity model has fewer than {minimum_n} complete areas")
    if min(int(data[column].nunique()) for column in exposures) < 10:
        raise CaseStudyAnalysisError("sensitivity model exposure has fewer than 10 distinct values")
    design = _design_matrix(data, exposures)
    if np.linalg.matrix_rank(design) < design.shape[1]:
        raise CaseStudyAnalysisError("sensitivity model design matrix is rank deficient")
    outcome = data[OUTCOME].to_numpy(dtype=float)
    try:
        beta = np.linalg.solve(design.T @ design, design.T @ outcome)
        covariance = _hc3_covariance(design, outcome)
    except (ArithmeticError, np.linalg.LinAlgError, ValueError) as error:
        raise CaseStudyAnalysisError("sensitivity model covariance is not estimable") from error
    if not np.isfinite(beta).all() or not np.isfinite(covariance).all():
        raise CaseStudyAnalysisError("sensitivity model covariance is not finite")
    return {
        "data": data,
        "design": design,
        "outcome": outcome,
        "beta": beta,
        "covariance": covariance,
    }


def _contrast_record(
    estimand_id: str,
    fit: dict[str, Any],
    contrast: np.ndarray,
    confidence_level: float,
    hypertension_iqr: float,
    diabetes_iqr: float,
    copd_iqr: float,
) -> dict[str, Any]:
    estimate = float(contrast @ fit["beta"])
    variance = float(contrast @ fit["covariance"] @ contrast)
    if variance < 0 or not np.isfinite(variance):
        raise CaseStudyAnalysisError(f"{estimand_id} contrast covariance is not estimable")
    standard_error = float(np.sqrt(variance))
    critical = float(stats.norm.ppf(1 - (1 - confidence_level) / 2))
    return {
        "estimand_id": estimand_id,
        "model_id": "C1_unadjusted" if estimand_id.startswith("C1") else "C2_unadjusted",
        "estimate": estimate,
        "standard_error": standard_error,
        "ci_low": estimate - critical * standard_error,
        "ci_high": estimate + critical * standard_error,
        "confidence_level": confidence_level,
        "n": len(fit["data"]),
        "hypertension_iqr": hypertension_iqr,
        "diabetes_iqr": diabetes_iqr,
        "copd_iqr": copd_iqr,
        "covariance_type": "HC3",
        "estimator": "unweighted_ols",
        "adjustment_set": "unadjusted",
        "analysis_status": "supported_sensitivity_not_primary",
        "primary_estimand_executed": False,
        "interpretation": "noncausal_ecological_association",
    }


def _contrast_estimate(
    fit: dict[str, Any], model_id: str, frozen_iqrs: dict[str, float] | None = None
) -> float:
    iqrs = frozen_iqrs or {
        exposure: _iqr(fit["data"][exposure]) for exposure in MODEL_EXPOSURES[model_id]
    }
    if model_id == "C1":
        return float(fit["beta"][1] * iqrs[HYPERTENSION] + fit["beta"][2] * iqrs[DIABETES])
    return float(fit["beta"][1] * iqrs[COPD])


def _contrast_interval(
    fit: dict[str, Any],
    model_id: str,
    frozen_iqrs: dict[str, float],
    confidence_level: float,
) -> tuple[float, float]:
    contrast = (
        np.array([0.0, frozen_iqrs[HYPERTENSION], frozen_iqrs[DIABETES]])
        if model_id == "C1"
        else np.array([0.0, frozen_iqrs[COPD]])
    )
    estimate = float(contrast @ fit["beta"])
    variance = float(contrast @ fit["covariance"] @ contrast)
    if variance < 0 or not np.isfinite(variance):
        raise CaseStudyAnalysisError("influence contrast covariance is not estimable")
    critical = float(stats.norm.ppf(1 - (1 - confidence_level) / 2))
    half_width = critical * np.sqrt(variance)
    return estimate - half_width, estimate + half_width


def _leave_one_out_estimate(
    frame: pd.DataFrame,
    model_id: str,
    index: int,
    frozen_iqrs: dict[str, float],
) -> float:
    reduced = frame.drop(index=frame.index[index])
    exposures = list(MODEL_EXPOSURES[model_id])
    return _contrast_estimate(
        _fit_model(reduced, exposures, minimum_n=len(exposures) + 2),
        model_id,
        frozen_iqrs,
    )


def _influence_diagnostics(design: np.ndarray, outcome: np.ndarray) -> pd.DataFrame:
    inverse = np.linalg.inv(design.T @ design)
    beta = inverse @ design.T @ outcome
    residual = outcome - design @ beta
    n, p = design.shape
    leverage = np.diag(design @ inverse @ design.T)
    residual_df = n - p
    if residual_df <= 1 or np.any(1 - leverage <= 0):
        raise CaseStudyAnalysisError("influence diagnostics are not estimable")
    mse = float(residual @ residual / residual_df)
    cooks = residual**2 / (p * mse) * leverage / (1 - leverage) ** 2
    deleted_sse = residual_df * mse - residual**2 / (1 - leverage)
    deleted_mse = deleted_sse / (residual_df - 1)
    external = residual / np.sqrt(deleted_mse * (1 - leverage))
    values = np.column_stack([cooks, leverage, external])
    if not np.isfinite(values).all():
        raise CaseStudyAnalysisError("influence diagnostics contain non-finite values")
    return pd.DataFrame(
        values,
        columns=["cooks_distance", "leverage", "externally_studentized_residual"],
    )


def _hc3_covariance(design: np.ndarray, outcome: np.ndarray) -> np.ndarray:
    inverse = np.linalg.inv(design.T @ design)
    beta = inverse @ design.T @ outcome
    residual = outcome - design @ beta
    leverage = np.diag(design @ inverse @ design.T)
    adjusted = residual / (1 - leverage)
    return inverse @ (design.T @ np.diag(adjusted**2) @ design) @ inverse


def _design_matrix(frame: pd.DataFrame, columns: Sequence[str]) -> np.ndarray:
    return np.column_stack(
        [np.ones(len(frame)), *(frame[column].to_numpy(dtype=float) for column in columns)]
    )


def _iqr(values: pd.Series) -> float:
    numeric = values.to_numpy(dtype=float)
    return float(np.percentile(numeric, 75) - np.percentile(numeric, 25))


def _validate_repeated_atlas_outcomes(dataset: pd.DataFrame) -> None:
    for keys, group in dataset.groupby(["geography_id", "time_period"], sort=True, observed=False):
        estimates = group["life_expectancy_estimate"]
        periods = group["life_expectancy_time_period"]
        estimate_missingness_consistent = estimates.isna().all() or estimates.notna().all()
        period_missingness_consistent = periods.isna().all() or periods.notna().all()
        estimate_values_consistent = estimates.dropna().nunique() <= 1
        period_values_consistent = periods.dropna().astype(str).nunique() <= 1
        if not all(
            [
                estimate_missingness_consistent,
                period_missingness_consistent,
                estimate_values_consistent,
                period_values_consistent,
            ]
        ):
            raise CaseStudyAnalysisError(
                f"inconsistent repeated Atlas outcome for geography-year {keys}"
            )


def _temporal_provenance(dataset: pd.DataFrame) -> dict[str, str]:
    for column in ["source_id", "snapshot_id"]:
        if dataset[column].isna().any():
            raise CaseStudyAnalysisError(f"temporal exposure provenance is missing {column}")
    source_ids = sorted(dataset["source_id"].astype(str).unique())
    snapshot_ids = sorted(dataset["snapshot_id"].astype(str).unique())
    return {
        "exposure_source_id": "|".join(source_ids),
        "exposure_snapshot_id": "|".join(snapshot_ids),
        "outcome_source_id": OUTCOME_SOURCE_ID,
        "outcome_snapshot_id": OUTCOME_SNAPSHOT_ID,
        "outcome_lineage_id": OUTCOME_LINEAGE_ID,
        "outcome_provenance_contract": "registered_frozen_public_source_lineage",
    }


def _frozen_temporal_iqrs(frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    output: dict[str, dict[str, float]] = {}
    for model_id, exposures in MODEL_EXPOSURES.items():
        complete = frame[[OUTCOME, *exposures]].dropna()
        if len(complete) < 70:
            output[model_id] = {exposure: np.nan for exposure in exposures}
        else:
            output[model_id] = {exposure: _iqr(complete[exposure]) for exposure in exposures}
    return output


def _temporal_area_years(dataset: pd.DataFrame) -> pd.DataFrame:
    areas = sorted(dataset["geography_id"].astype(str).unique())
    outcomes = (
        dataset.groupby(["geography_id", "time_period"], sort=True, observed=False)
        .agg(
            life_expectancy_estimate=("life_expectancy_estimate", "first"),
            life_expectancy_time_period=("life_expectancy_time_period", "first"),
        )
        .reset_index()
    )
    outcome_lookup = outcomes.set_index(["geography_id", "time_period"]).to_dict("index")
    records: list[dict[str, Any]] = []
    for area in areas:
        for year in TEMPORAL_YEARS:
            outcome = outcome_lookup.get(
                (area, year),
                {
                    "life_expectancy_estimate": np.nan,
                    "life_expectancy_time_period": pd.NA,
                },
            )
            area_year = dataset.loc[
                dataset["geography_id"].astype(str).eq(area) & dataset["time_period"].eq(year)
            ]
            for condition in ("hypertension", "diabetes", "copd"):
                if condition == "diabetes":
                    source = area_year.loc[area_year["condition_family"].eq("diabetes")]
                    source = source.copy()
                    source["component_eligible"] = (
                        source["condition_id"].isin(DIABETES_COMPONENTS)
                        & ~source["suppression_flag"]
                        & source["numerator"].notna()
                        & source["denominator"].notna()
                        & source["denominator"].gt(0)
                    )
                    eligible = source.loc[source["component_eligible"]]
                    exact_components = (
                        set(eligible["condition_id"]) == DIABETES_COMPONENTS and len(eligible) == 2
                    )
                    denominator_match = (
                        exact_components and eligible["denominator"].nunique(dropna=False) == 1
                    )
                    semantics_approved = combined_diabetes_is_approved(source)
                    annual_eligible = bool(
                        exact_components and denominator_match and semantics_approved
                    )
                    mismatch = bool(exact_components and not denominator_match)
                    suppression_excluded = bool(source["suppression_flag"].any())
                    missing_excluded = bool(
                        len(source) != 2
                        or source[["numerator", "denominator"]].isna().any(axis=None)
                    )
                    reason = (
                        "eligible"
                        if annual_eligible
                        else "combined_diabetes_semantics_unapproved"
                        if exact_components and denominator_match and not semantics_approved
                        else "diabetes_component_denominator_mismatch"
                        if mismatch
                        else "missing_or_suppressed_diabetes_component"
                    )
                    numerator = float(eligible["numerator"].sum()) if annual_eligible else np.nan
                    denominator = (
                        float(eligible["denominator"].iloc[0]) if annual_eligible else np.nan
                    )
                    eligible_components = int(source["component_eligible"].sum())
                else:
                    source = area_year.loc[area_year["condition_id"].eq(condition)]
                    annual_eligible = bool(
                        len(source) == 1
                        and not bool(source.iloc[0]["suppression_flag"])
                        and pd.notna(source.iloc[0]["numerator"])
                        and pd.notna(source.iloc[0]["denominator"])
                        and float(source.iloc[0]["denominator"]) > 0
                    )
                    mismatch = False
                    suppression_excluded = bool(
                        len(source) == 1 and bool(source.iloc[0]["suppression_flag"])
                    )
                    missing_excluded = bool(
                        source.empty or source[["numerator", "denominator"]].isna().any(axis=None)
                    )
                    reason = "eligible" if annual_eligible else "missing_or_suppressed_condition"
                    numerator = float(source.iloc[0]["numerator"]) if annual_eligible else np.nan
                    denominator = (
                        float(source.iloc[0]["denominator"]) if annual_eligible else np.nan
                    )
                    eligible_components = int(annual_eligible)
                capture = float(source["capture_rate"].mean()) if not source.empty else np.nan
                continuity_values = (
                    source["continuity_review_status"]
                    if "continuity_review_status" in source
                    else pd.Series(dtype=object)
                )
                continuity_states = set(continuity_values.dropna().astype(str).unique())
                continuity = (
                    next(iter(continuity_states))
                    if len(source) == (2 if condition == "diabetes" else 1)
                    and int(continuity_values.notna().sum()) == len(source)
                    and len(continuity_states) == 1
                    else "pending"
                )
                outcome_period = str(outcome["life_expectancy_time_period"])
                outcome_eligible = bool(
                    pd.notna(outcome["life_expectancy_estimate"]) and outcome_period == year
                )
                records.append(
                    {
                        "geography_id": area,
                        "time_period": year,
                        "condition_id": condition,
                        "numerator": numerator,
                        "denominator": denominator,
                        "capture_rate": capture,
                        "annual_eligible": annual_eligible,
                        "ineligibility_reason": reason,
                        "eligible_component_rows": eligible_components,
                        "diabetes_denominator_mismatch": mismatch,
                        "suppression_excluded": suppression_excluded,
                        "missing_excluded": missing_excluded,
                        "exposure_percentage_points": 100 * numerator / denominator
                        if annual_eligible
                        else np.nan,
                        "life_expectancy_estimate": outcome["life_expectancy_estimate"]
                        if outcome_eligible
                        else np.nan,
                        "life_expectancy_time_period": outcome_period,
                        "outcome_eligible": outcome_eligible,
                        "continuity_review_status": continuity,
                    }
                )
    return pd.DataFrame.from_records(records).sort_values(
        ["condition_id", "geography_id", "time_period"], kind="mergesort"
    )


def _add_disruption_flags(area_years: pd.DataFrame) -> pd.DataFrame:
    output = area_years.copy()
    output["annual_change_percentage_points"] = output.groupby(
        ["geography_id", "condition_id"], sort=False
    )["exposure_percentage_points"].diff()
    output["median_absolute_annual_change"] = output.groupby(
        ["geography_id", "condition_id"], sort=False
    )["annual_change_percentage_points"].transform(lambda values: values.abs().median())
    output["disruption_candidate"] = (
        output["time_period"].isin(["2020", "2021"])
        & output["annual_change_percentage_points"].abs().gt(10)
        & output["annual_change_percentage_points"]
        .abs()
        .gt(2 * output["median_absolute_annual_change"])
    )
    output["disruption_status"] = "not_a_disruption_candidate"
    pending = output["disruption_candidate"]
    output.loc[pending, "disruption_status"] = "candidate_disruption_pending_continuity_review"
    resolved = pending & output["continuity_review_status"].eq("resolved_no_discontinuity")
    output.loc[resolved, "disruption_status"] = "confirmed_disruption_after_continuity_review"
    reviewed_break = pending & output["continuity_review_status"].eq("resolved_discontinuity")
    output.loc[reviewed_break, "disruption_status"] = "candidate_not_confirmed_due_continuity_break"
    return output


def _annual_association_frame(area_years: pd.DataFrame, year: str) -> pd.DataFrame:
    rows = area_years.loc[area_years["time_period"].eq(year)].copy()
    exposures = rows.pivot(
        index="geography_id", columns="condition_id", values="exposure_percentage_points"
    )
    outcomes = rows.groupby("geography_id", sort=True)["life_expectancy_estimate"].first()
    frame = exposures.rename(
        columns={"hypertension": HYPERTENSION, "diabetes": DIABETES, "copd": COPD}
    ).join(outcomes.rename(OUTCOME))
    for field in ["suppression_excluded", "missing_excluded", "diabetes_denominator_mismatch"]:
        flags = rows.pivot(index="geography_id", columns="condition_id", values=field).rename(
            columns=lambda condition: f"{condition}_{field}"
        )
        frame = frame.join(flags)
    return frame.reset_index()


def _diabetes_mismatch_geographies(area_years: pd.DataFrame, years: tuple[str, ...]) -> int:
    mismatches = area_years.loc[
        area_years["condition_id"].eq("diabetes")
        & area_years["time_period"].isin(years)
        & area_years["diabetes_denominator_mismatch"]
    ]
    return int(mismatches["geography_id"].nunique())


def _pooled_association_frame(
    area_years: pd.DataFrame,
    exposure_years: tuple[str, ...],
    outcome_years: tuple[str, ...],
) -> pd.DataFrame:
    subset = area_years.loc[area_years["time_period"].isin(exposure_years)]
    pooled_records: list[dict[str, Any]] = []
    for (area, condition), group in subset.groupby(
        ["geography_id", "condition_id"], sort=True, observed=False
    ):
        eligible = bool(
            len(group) == len(exposure_years)
            and int(group["annual_eligible"].sum()) == len(exposure_years)
        )
        pooled_records.append(
            {
                "geography_id": area,
                "condition_id": condition,
                "exposure": 100 * group["numerator"].sum() / group["denominator"].sum()
                if eligible
                else np.nan,
                "suppression_excluded": bool(group["suppression_excluded"].any()),
                "missing_excluded": bool(group["missing_excluded"].any()),
                "diabetes_denominator_mismatch": bool(group["diabetes_denominator_mismatch"].any()),
            }
        )
    pooled_data = pd.DataFrame.from_records(pooled_records)
    exposures = pooled_data.pivot(index="geography_id", columns="condition_id", values="exposure")
    outcome_rows = (
        area_years.loc[area_years["time_period"].isin(outcome_years)]
        .drop_duplicates(["geography_id", "time_period"])
        .copy()
    )
    outcomes = outcome_rows.groupby("geography_id", sort=True).agg(
        outcome=("life_expectancy_estimate", "mean"),
        outcome_year_count=("time_period", "nunique"),
        outcome_nonmissing_count=("life_expectancy_estimate", "count"),
    )
    outcomes["outcome"] = outcomes["outcome"].where(
        outcomes["outcome_year_count"].eq(len(outcome_years))
        & outcomes["outcome_nonmissing_count"].eq(len(outcome_years))
    )
    frame = exposures.rename(
        columns={"hypertension": HYPERTENSION, "diabetes": DIABETES, "copd": COPD}
    ).join(outcomes["outcome"].rename(OUTCOME))
    for field in ["suppression_excluded", "missing_excluded", "diabetes_denominator_mismatch"]:
        flags = pooled_data.pivot(
            index="geography_id", columns="condition_id", values=field
        ).rename(columns=lambda condition: f"{condition}_{field}")
        frame = frame.join(flags)
    return frame.reset_index()


def _temporal_model_records(
    frame: pd.DataFrame,
    *,
    analysis_id: str,
    time_period: str,
    period_role: str,
    included_years: str,
    outcome_years: str,
    diabetes_mismatches: int,
    frozen_iqrs: dict[str, dict[str, float]],
    provenance: dict[str, str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for model_id, exposures in MODEL_EXPOSURES.items():
        conditions = ("hypertension", "diabetes") if model_id == "C1" else ("copd",)
        total_geographies = int(frame["geography_id"].nunique())
        exposure_complete = frame[list(exposures)].notna().all(axis=1)
        outcome_complete = frame[OUTCOME].notna()
        complete = frame[["geography_id", OUTCOME, *exposures]].dropna()
        suppression_excluded = frame[
            [f"{condition}_suppression_excluded" for condition in conditions]
        ].any(axis=1)
        missing_excluded = frame[[f"{condition}_missing_excluded" for condition in conditions]].any(
            axis=1
        )
        estimands = ("C1", "C1-H", "C1-D") if model_id == "C1" else ("C2",)
        status = (
            "withheld_no_eligible_pairs"
            if complete.empty
            else "withheld_insufficient_complete_areas"
            if len(complete) < 70
            else "supported_sensitivity_not_primary"
        )
        if status == "supported_sensitivity_not_primary" and not all(
            np.isfinite(value) for value in frozen_iqrs[model_id].values()
        ):
            status = "withheld_frozen_iqr_population_unavailable"
        model_records: list[dict[str, Any]] = []
        if status == "supported_sensitivity_not_primary":
            try:
                fit = _fit_model(complete, list(exposures))
                iqrs = frozen_iqrs[model_id]
                if model_id == "C1":
                    contrasts = {
                        "C1": np.array([0.0, iqrs[HYPERTENSION], iqrs[DIABETES]]),
                        "C1-H": np.array([0.0, iqrs[HYPERTENSION], 0.0]),
                        "C1-D": np.array([0.0, 0.0, iqrs[DIABETES]]),
                    }
                else:
                    contrasts = {"C2": np.array([0.0, iqrs[COPD]])}
                for estimand, contrast in contrasts.items():
                    model_records.append(
                        _contrast_record(
                            estimand,
                            fit,
                            contrast,
                            0.975 if estimand in {"C1", "C2"} else 0.95,
                            iqrs.get(HYPERTENSION, np.nan),
                            iqrs.get(DIABETES, np.nan),
                            iqrs.get(COPD, np.nan),
                        )
                    )
            except CaseStudyAnalysisError:
                status = "withheld_model_not_estimable"
        if not model_records:
            model_records = [
                {
                    "estimand_id": estimand,
                    "estimate": np.nan,
                    "standard_error": np.nan,
                    "ci_low": np.nan,
                    "ci_high": np.nan,
                    "confidence_level": 0.975 if estimand in {"C1", "C2"} else 0.95,
                }
                for estimand in estimands
            ]
        for record in model_records:
            record.update(
                row_type="association_model",
                analysis_id=analysis_id,
                time_period=time_period,
                period_role=period_role,
                included_years=included_years,
                outcome_years=outcome_years,
                n_paired=len(complete),
                status=status,
                analysis_status="supported_temporal_sensitivity_not_primary"
                if status == "supported_sensitivity_not_primary"
                else status,
                adjustment_set="unadjusted",
                primary_estimand_executed=False,
                formal_test_family="not_applicable_no_formal_p_values",
                diabetes_denominator_mismatch_geographies=diabetes_mismatches,
                total_geography_universe=total_geographies,
                n_exposure_complete=int(exposure_complete.sum()),
                n_outcome_complete=int(outcome_complete.sum()),
                n_suppression_excluded=int(suppression_excluded.sum()),
                n_missing_exposure_excluded=int(missing_excluded.sum()),
                n_denominator_mismatch_excluded=diabetes_mismatches if model_id == "C1" else 0,
                n_pair_excluded=total_geographies - len(complete),
                iqr_source_population_id=IQR_SOURCE_POPULATION_ID,
                candidate_id=pd.NA,
                disruption_status=pd.NA,
                continuity_review_status=pd.NA,
                **provenance,
            )
            records.append(record)
    return records


def _withheld_temporal_records(
    *,
    analysis_id: str,
    status: str,
    included_years: str,
    outcome_years: str,
    frame: pd.DataFrame,
    frozen_iqrs: dict[str, dict[str, float]],
    provenance: dict[str, str],
    diabetes_mismatches: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for model_id, estimands in {"C1": ("C1", "C1-H", "C1-D"), "C2": ("C2",)}.items():
        exposures = MODEL_EXPOSURES[model_id]
        iqrs = frozen_iqrs[model_id]
        exposure_complete = frame[list(exposures)].notna().all(axis=1)
        outcome_complete = frame[OUTCOME].notna()
        for estimand in estimands:
            record: dict[str, Any] = {
                "row_type": "association_model",
                "analysis_id": analysis_id,
                "estimand_id": estimand,
                "model_id": f"{model_id}_unadjusted",
                "time_period": "2022-2024",
                "period_role": "disruption_exclusion_sensitivity",
                "included_years": included_years,
                "outcome_years": outcome_years,
                "n_paired": pd.NA,
                "total_geography_universe": int(frame["geography_id"].nunique()),
                "n_exposure_complete": int(exposure_complete.sum()),
                "n_outcome_complete": int(outcome_complete.sum()),
                "n_suppression_excluded": pd.NA,
                "n_missing_exposure_excluded": pd.NA,
                "n_denominator_mismatch_excluded": diabetes_mismatches if model_id == "C1" else 0,
                "n_pair_excluded": pd.NA,
                "estimate": np.nan,
                "standard_error": np.nan,
                "ci_low": np.nan,
                "ci_high": np.nan,
                "status": status,
                "analysis_status": status,
                "adjustment_set": "unadjusted",
                "primary_estimand_executed": False,
                "formal_test_family": "not_applicable_no_formal_p_values",
                "hypertension_iqr": iqrs.get(HYPERTENSION, np.nan),
                "diabetes_iqr": iqrs.get(DIABETES, np.nan),
                "copd_iqr": iqrs.get(COPD, np.nan),
                "iqr_source_population_id": IQR_SOURCE_POPULATION_ID,
                "candidate_id": pd.NA,
                "disruption_status": pd.NA,
                "continuity_review_status": pd.NA,
            }
            record.update(provenance)
            records.append(record)
    return records


def _disruption_candidate_record(row: Any) -> dict[str, Any]:
    return {
        "row_type": "disruption_candidate",
        "analysis_id": "disruption_candidate_audit",
        "estimand_id": pd.NA,
        "candidate_id": f"{row.geography_id}|{row.condition_id}|{row.time_period}",
        "geography_id": row.geography_id,
        "condition_id": row.condition_id,
        "time_period": row.time_period,
        "period_role": "disruption",
        "included_years": row.time_period,
        "outcome_years": pd.NA,
        "n_paired": pd.NA,
        "estimate": np.nan,
        "annual_change_percentage_points": row.annual_change_percentage_points,
        "median_absolute_annual_change": row.median_absolute_annual_change,
        "denominator": row.denominator,
        "capture_rate": row.capture_rate,
        "continuity_review_status": row.continuity_review_status,
        "disruption_status": row.disruption_status,
        "status": row.disruption_status,
        "analysis_status": "descriptive_disruption_audit",
        "primary_estimand_executed": False,
    }


def _period_role(year: str) -> str:
    if year == "2019":
        return "baseline"
    if year in {"2020", "2021"}:
        return "disruption"
    return "primary_annual"


def _validated_numeric_frame(
    frame: pd.DataFrame, columns: Sequence[str], context: str
) -> pd.DataFrame:
    output = frame.copy()
    for column in columns:
        original = output[column]
        converted = pd.to_numeric(original, errors="coerce")
        malformed = original.notna() & converted.isna()
        if malformed.any():
            raise CaseStudyAnalysisError(f"{context} has malformed numeric values in {column}")
        finite = converted.dropna().map(np.isfinite)
        if not bool(finite.all()):
            raise CaseStudyAnalysisError(f"{context} has non-finite values in {column}")
        output[column] = converted
    return output


def _validate_nonempty(frame: pd.DataFrame, context: str) -> None:
    if frame.empty:
        raise CaseStudyAnalysisError(f"{context} has no rows")


def _design_gate_diagnostics(
    complete: pd.DataFrame, predictors: Sequence[str]
) -> dict[str, Any]:
    predictor_frame = complete.loc[:, predictors]
    values = predictor_frame.to_numpy(dtype=float)
    standard_deviations = values.std(axis=0, ddof=1)
    variable_mask = (standard_deviations > 0) & np.isfinite(standard_deviations)
    variable_indices = np.flatnonzero(variable_mask)
    maximum_correlation: object = pd.NA
    maximum_correlation_predictor_1 = ""
    maximum_correlation_predictor_2 = ""
    if len(variable_indices) >= 2:
        variable_correlation = np.corrcoef(values[:, variable_mask], rowvar=False)
        upper_rows, upper_columns = np.triu_indices(len(variable_indices), k=1)
        upper_correlations = np.abs(variable_correlation[upper_rows, upper_columns])
        maximum_index = int(np.argmax(upper_correlations))
        maximum_row = int(variable_indices[upper_rows[maximum_index]])
        maximum_column = int(variable_indices[upper_columns[maximum_index]])
        maximum_correlation = float(upper_correlations[maximum_index])
        maximum_correlation_predictor_1 = predictors[maximum_row]
        maximum_correlation_predictor_2 = predictors[maximum_column]

    if not bool(variable_mask.all()):
        standardized_condition_number: object = pd.NA
    else:
        standardized = (values - values.mean(axis=0)) / standard_deviations
        standardized_design = np.column_stack([np.ones(len(standardized)), standardized])
        standardized_condition_number = float(np.linalg.cond(standardized_design))

    design = _design_matrix(complete, predictors)
    design_rank = int(np.linalg.matrix_rank(design))
    predictor_vifs: dict[str, float] = {}
    maximum_vif: object = pd.NA
    vif_offending_predictor = ""
    if design_rank == design.shape[1]:
        correlation = np.corrcoef(values, rowvar=False)
        inverse_correlation = np.linalg.inv(correlation)
        predictor_vifs = {
            predictor: float(inverse_correlation[index, index])
            for index, predictor in enumerate(predictors)
        }
        vif_offending_predictor = max(predictors, key=predictor_vifs.__getitem__)
        maximum_vif = predictor_vifs[vif_offending_predictor]

    try:
        covariance = _hc3_covariance(design, complete[OUTCOME].to_numpy(dtype=float))
    except (ArithmeticError, np.linalg.LinAlgError, ValueError):
        covariance = np.full((design.shape[1], design.shape[1]), np.nan)
    covariance_ok = covariance.shape == (design.shape[1], design.shape[1]) and bool(
        np.isfinite(covariance).all()
    )
    return {
        "design_rank": design_rank,
        "predictor_vifs": predictor_vifs,
        "maximum_vif": maximum_vif,
        "vif_offending_predictor": vif_offending_predictor,
        "maximum_absolute_pairwise_correlation": maximum_correlation,
        "maximum_correlation_predictor_1": maximum_correlation_predictor_1,
        "maximum_correlation_predictor_2": maximum_correlation_predictor_2,
        "standardized_design_condition_number": standardized_condition_number,
        "hc3_covariance_status": (
            "estimable_and_finite" if covariance_ok else "not_estimable_or_nonfinite"
        ),
    }


def _append_gate(existing: object, gate: str) -> str:
    value = str(existing)
    return f"{value}|{gate}" if value else gate


def _require_columns(frame: pd.DataFrame, required: set[str], context: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"{context} is missing columns: {missing}")


def _validate_unique(frame: pd.DataFrame, key: list[str], context: str) -> None:
    duplicates = int(frame.duplicated(key).sum())
    if duplicates:
        key_label = "geography_id" if key == ["geography_id"] else "keys"
        raise CaseStudyAnalysisError(f"{context} has {duplicates} duplicate {key_label}")
