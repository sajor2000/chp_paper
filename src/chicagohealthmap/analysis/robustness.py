"""Governed, deterministic robustness-analysis records and comparisons."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, TypedDict, overload

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from scipy import stats  # type: ignore[import-untyped]

from chicagohealthmap.analysis.case_studies import CaseStudyAnalysisError
from chicagohealthmap.analysis.sap_analyses import (
    ADJUSTMENT_COVARIATES,
    MODEL_ELIGIBILITY_FLAGS,
    MODEL_EXPOSURES,
    OUTCOME,
    PRIMARY_YEARS,
    _add_disruption_flags,
    _influence_diagnostics,
    _pooled_association_frame,
    _temporal_area_years,
    assess_primary_model_readiness,
)

COMMON_ROBUSTNESS_COLUMNS = (
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
)


class _FitResult(TypedDict):
    estimate: float
    ci_low: float
    ci_high: float
    eligible_n: int
    design: np.ndarray
    outcome: np.ndarray
    beta: np.ndarray
    covariance: np.ndarray


def direction_stability(reference: float, variant: float) -> bool | pd._libs.missing.NAType:
    """Return deterministic sign agreement, treating two zeros as stable."""

    if not np.isfinite([reference, variant]).all():
        return pd.NA
    return bool(np.sign(reference) == np.sign(variant))


@overload
def absolute_percentage_change(
    reference: float, variant: float, *, return_reason: Literal[False] = False
) -> float: ...


@overload
def absolute_percentage_change(
    reference: float, variant: float, *, return_reason: Literal[True]
) -> tuple[float, str]: ...


def absolute_percentage_change(
    reference: float, variant: float, *, return_reason: bool = False
) -> float | tuple[float, str]:
    """Calculate the governed absolute percentage change with denominator reasons."""

    reason = "available"
    if not np.isfinite(reference):
        value = float("nan")
        reason = "reference_unavailable"
    elif not np.isfinite(variant):
        value = float("nan")
        reason = "variant_unavailable"
    elif reference == 0:
        value = float("nan")
        reason = "reference_zero"
    else:
        value = abs((variant - reference) / reference) * 100.0
    return (value, reason) if return_reason else value


def ci_overlap(
    reference_low: float,
    reference_high: float,
    variant_low: float,
    variant_high: float,
) -> bool | pd._libs.missing.NAType:
    """Test overlap of two closed intervals; touching endpoints overlap."""

    values = np.asarray([reference_low, reference_high, variant_low, variant_high], dtype=float)
    if not np.isfinite(values).all():
        return pd.NA
    if reference_low > reference_high or variant_low > variant_high:
        raise CaseStudyAnalysisError("confidence interval bounds are reversed")
    return bool(variant_low <= reference_high and reference_low <= variant_high)


def capture_quartile_cut_points(
    frame: pd.DataFrame,
    eligible: pd.Series | Callable[[pd.DataFrame], pd.Series],
) -> tuple[float, float, float]:
    """Freeze capture quartiles from the governed eligible analytic population."""

    mask = (
        eligible(frame) if callable(eligible) else eligible.reindex(frame.index, fill_value=False)
    )
    if mask.dtype != bool:
        raise CaseStudyAnalysisError("capture quartile eligibility mask must be boolean")
    values = pd.to_numeric(
        frame.loc[mask, "capture_rate_mean_2022_2024"], errors="coerce"
    ).to_numpy(dtype=float)
    if len(values) < 4 or not np.isfinite(values).all():
        raise CaseStudyAnalysisError(
            "capture quartiles require at least four finite eligible values"
        )
    cuts = np.quantile(values, [0.25, 0.50, 0.75], method="linear")
    if not np.all(np.diff(cuts) > 0):
        raise CaseStudyAnalysisError("capture quartile cut points are not strictly increasing")
    return float(cuts[0]), float(cuts[1]), float(cuts[2])


def build_not_applicable_rows() -> pd.DataFrame:
    """Emit explicit governed records for prespecified inapplicable analyses."""

    reasons = {
        "implausible_ratio_exclusion": "no_current_community_area_flagged",
        "multiple_imputation": "adjustment_covariates_complete",
        "precision_weighting": "life_expectancy_uncertainty_unavailable",
        "exclude_crosswalk_derived_disease_estimates": "chm_disease_values_are_direct_exports",
    }
    records = []
    for variant, reason in reasons.items():
        records.append(
            {
                "model": "C1|C2",
                "estimand": "not_applicable",
                "variant": variant,
                "target_population": "governed_community_area_population",
                "estimate": np.nan,
                "ci_low": np.nan,
                "ci_high": np.nan,
                "eligible_n": pd.NA,
                "direction_stability": pd.NA,
                "absolute_percentage_change": np.nan,
                "ci_overlap": pd.NA,
                "threshold_crossed": f"not_applicable:{reason}",
                "analysis_status": "not_applicable",
                "authorization_status": "results_not_authorized",
                "percentage_change_reason": "not_applicable",
                "primary_estimand_executed": False,
                "results_authorized": False,
            }
        )
    return pd.DataFrame.from_records(records)


def build_governed_robustness_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Run adjusted reference, weighting, capture, and influence variants."""

    records: list[dict[str, object]] = []
    primary_execution = _governed_primary_execution(frame)
    for model_id in ("C1", "C2"):
        complete = _eligible_adjusted_frame(frame, model_id, minimum_n=0)
        if len(complete) < 70:
            records.append(
                {
                    "model": model_id,
                    "estimand": model_id,
                    "variant": "continuous_capture_reference",
                    "target_population": "not_run",
                    "estimate": np.nan,
                    "ci_low": np.nan,
                    "ci_high": np.nan,
                    "eligible_n": len(complete),
                    "direction_stability": pd.NA,
                    "absolute_percentage_change": np.nan,
                    "ci_overlap": pd.NA,
                    "threshold_crossed": "not_run_insufficient_complete_areas",
                    "analysis_status": "not_run_combined_diabetes_semantics_unapproved",
                    "authorization_status": "results_not_authorized",
                    "primary_estimand_executed": False,
                    "results_authorized": False,
                }
            )
            continue
        scaling = _frozen_scaling(complete, model_id)
        reference = _fit_adjusted(complete, model_id, scaling=scaling)
        reference_record = _variant_record(
            model_id,
            "continuous_capture_reference",
            reference,
            reference,
            target_population="distribution_of_eligible_community_areas",
            estimator="unweighted_ols_hc3",
            primary_estimand_executed=primary_execution[model_id],
        )
        records.append(reference_record)

        weighted = _fit_adjusted(
            complete,
            model_id,
            scaling=scaling,
            weights=complete["acs_adult_population"].to_numpy(dtype=float),
        )
        records.append(
            _variant_record(
                model_id,
                "population_weighted_ols",
                weighted,
                reference,
                target_population="population_weighted_community_area_adult_population",
                estimator="population_weighted_ols_hc3",
                primary_estimand_executed=primary_execution[model_id],
            )
        )

        quartiles = capture_quartile_cut_points(complete, pd.Series(True, index=complete.index))
        categorical = _fit_adjusted(
            complete,
            model_id,
            scaling=scaling,
            capture_quartiles=quartiles,
        )
        quartile_record = _variant_record(
            model_id,
            "frozen_capture_quartiles",
            categorical,
            reference,
            target_population="distribution_of_eligible_community_areas",
            estimator="unweighted_ols_hc3_capture_quartiles",
            primary_estimand_executed=primary_execution[model_id],
        )
        quartile_record["capture_cut_points"] = "|".join(f"{value:.12g}" for value in quartiles)
        records.append(quartile_record)

        diagnostics = _influence_diagnostics(reference["design"], reference["outcome"])
        diagnostics = diagnostics.reset_index(drop=True)
        n, p = reference["design"].shape
        flagged = (
            (diagnostics["cooks_distance"] > 4 / n)
            | (diagnostics["leverage"] > 2 * p / n)
            | (diagnostics["externally_studentized_residual"].abs() > 3)
        ).to_numpy()
        for position, geography_id in enumerate(complete["geography_id"].astype(str)):
            subset = complete.drop(complete.index[position])
            leave_one = _fit_adjusted(subset, model_id, scaling=scaling)
            row = _variant_record(
                model_id,
                f"leave_one_area_out:{geography_id}",
                leave_one,
                reference,
                target_population="eligible_community_areas_excluding_one",
                estimator="unweighted_ols_hc3",
                primary_estimand_executed=primary_execution[model_id],
            )
            row["excluded_geography_id"] = geography_id
            records.append(row)

        unflagged = complete.loc[~flagged].copy()
        if len(unflagged) <= reference["design"].shape[1]:
            raise CaseStudyAnalysisError("all-flagged exclusion is not estimable")
        excluded = _fit_adjusted(unflagged, model_id, scaling=scaling)
        exclusion_row = _variant_record(
            model_id,
            "exclude_all_prespecified_flagged_areas",
            excluded,
            reference,
            target_population="eligible_community_areas_excluding_all_prespecified_flags",
            estimator="unweighted_ols_hc3",
            primary_estimand_executed=primary_execution[model_id],
        )
        exclusion_row["flagged_area_count"] = int(flagged.sum())
        records.append(exclusion_row)

    output = pd.concat(
        [pd.DataFrame.from_records(records), build_not_applicable_rows()],
        ignore_index=True,
        sort=False,
    )
    for column in COMMON_ROBUSTNESS_COLUMNS:
        if column not in output:
            output[column] = pd.NA
    return output.sort_values(["model", "estimand", "variant"], kind="mergesort").reset_index(
        drop=True
    )


def build_adjusted_diagnostic_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Expose tidy residual-vs-fitted, Q-Q, leverage, and influence data."""

    records: list[pd.DataFrame] = []
    primary_execution = _governed_primary_execution(frame)
    for model_id in ("C1", "C2"):
        complete = _eligible_adjusted_frame(frame, model_id, minimum_n=0)
        if len(complete) < 70:
            continue
        fit = _fit_adjusted(complete, model_id, scaling=_frozen_scaling(complete, model_id))
        influence = _influence_diagnostics(fit["design"], fit["outcome"]).reset_index(drop=True)
        residuals = fit["outcome"] - fit["design"] @ fit["beta"]
        order = np.argsort(residuals, kind="mergesort")
        ranks = np.empty(len(residuals), dtype=int)
        ranks[order] = np.arange(len(residuals))
        theoretical = stats.norm.ppf((np.arange(len(residuals)) + 0.5) / len(residuals))
        diagnostic = pd.DataFrame(
            {
                "model": model_id,
                "geography_id": complete["geography_id"].astype(str).to_numpy(),
                "fitted_value": fit["design"] @ fit["beta"],
                "residual": residuals,
                "qq_theoretical_quantile": theoretical[ranks],
                "qq_sample_quantile": residuals,
                "leverage": influence["leverage"],
                "cooks_distance": influence["cooks_distance"],
                "externally_studentized_residual": influence["externally_studentized_residual"],
                "analysis_status": _analysis_status(model_id, primary_execution[model_id]),
                "authorization_status": "results_not_authorized",
                "primary_estimand_executed": primary_execution[model_id],
                "results_authorized": False,
            }
        )
        records.append(diagnostic)
    return pd.concat(records, ignore_index=True).sort_values(
        ["model", "geography_id"], kind="mergesort"
    )


def build_adjusted_temporal_robustness(
    dataset: pd.DataFrame, adjustment_frame: pd.DataFrame
) -> pd.DataFrame:
    """Fit adjusted leave-one-primary-year-out variants with compatible pooled ACS covariates."""

    working = dataset.loc[
        dataset["geography_type"].eq("chicago_community_area")
        & dataset["time_period"].astype(str).isin(PRIMARY_YEARS)
    ].copy()
    working["time_period"] = working["time_period"].astype(str)
    annual = _add_disruption_flags(_temporal_area_years(working))
    reference_frame = _merge_temporal_adjustment(
        _pooled_association_frame(annual, PRIMARY_YEARS, PRIMARY_YEARS),
        annual,
        PRIMARY_YEARS,
        adjustment_frame,
    )
    records: list[dict[str, object]] = []
    primary_execution = _governed_primary_execution(adjustment_frame)
    for model_id in ("C1", "C2"):
        eligible_adjustment = adjustment_frame[
            list(MODEL_ELIGIBILITY_FLAGS[model_id])
        ].eq(True).all(axis=1)  # noqa: E712
        if int(eligible_adjustment.sum()) < 70:
            continue
        reference_complete = _eligible_adjusted_frame(reference_frame, model_id, minimum_n=0)
        if len(reference_complete) < 70:
            continue
        scaling = _frozen_scaling(reference_complete, model_id)
        reference = _fit_adjusted(reference_complete, model_id, scaling=scaling)
        for omitted in PRIMARY_YEARS:
            included = tuple(year for year in PRIMARY_YEARS if year != omitted)
            pooled = _pooled_association_frame(annual, included, included)
            variant_frame = _merge_temporal_adjustment(pooled, annual, included, adjustment_frame)
            complete = _eligible_adjusted_frame(variant_frame, model_id)
            fit = _fit_adjusted(complete, model_id, scaling=scaling)
            row = _variant_record(
                model_id,
                f"leave_one_primary_year_out:{omitted}",
                fit,
                reference,
                target_population="pooled_2022_2024_eligible_community_areas",
                estimator="unweighted_ols_hc3_adjusted_temporal",
                primary_estimand_executed=primary_execution[model_id],
            )
            row["omitted_year"] = omitted
            row["included_years"] = "|".join(included)
            row["temporal_adjustment_covariates"] = (
                "compatible_pooled_acs_covariates_plus_period_capture"
            )
            records.append(row)
    return pd.DataFrame.from_records(records).sort_values(
        ["model", "omitted_year"], kind="mergesort"
    )


def _merge_temporal_adjustment(
    pooled: pd.DataFrame,
    annual: pd.DataFrame,
    included_years: tuple[str, ...],
    adjustment_frame: pd.DataFrame,
) -> pd.DataFrame:
    static_covariates = adjustment_frame[
        [
            "geography_id",
            "pct_age_65_plus",
            "pct_female",
            "pct_below_fpl",
            "acs_adult_population",
        ]
    ].drop_duplicates("geography_id")
    capture = (
        annual.loc[annual["time_period"].isin(included_years)]
        .groupby(["geography_id", "time_period"], sort=True)["capture_rate"]
        .first()
        .groupby("geography_id", sort=True)
        .mean()
        .rename("capture_rate_mean_2022_2024")
        .reset_index()
    )
    output = pooled.merge(static_covariates, on="geography_id", how="left", validate="one_to_one")
    output = output.merge(capture, on="geography_id", how="left", validate="one_to_one")
    output["life_expectancy_years_complete"] = output[OUTCOME].notna()
    output["hypertension_exposure_complete"] = output["hypertension_ehr_percent_2022_2024"].notna()
    output["diabetes_exposure_complete"] = output["diabetes_ehr_percent_2022_2024"].notna()
    output["copd_exposure_complete"] = output["copd_ehr_percent_2022_2024"].notna()
    return output


def _eligible_adjusted_frame(
    frame: pd.DataFrame, model_id: str, *, minimum_n: int = 70
) -> pd.DataFrame:
    required = {
        "geography_id",
        OUTCOME,
        "acs_adult_population",
        *MODEL_EXPOSURES[model_id],
        *MODEL_ELIGIBILITY_FLAGS[model_id],
        *ADJUSTMENT_COVARIATES,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"robustness frame is missing columns: {missing}")
    mask = frame[list(MODEL_ELIGIBILITY_FLAGS[model_id])].eq(True).all(axis=1)  # noqa: E712
    columns = [OUTCOME, "acs_adult_population", *MODEL_EXPOSURES[model_id], *ADJUSTMENT_COVARIATES]
    numeric = frame.loc[mask, ["geography_id", *columns]].copy()
    for column in columns:
        numeric[column] = pd.to_numeric(numeric[column], errors="coerce")
    numeric = numeric.dropna(subset=columns).sort_values("geography_id", kind="mergesort")
    if len(numeric) < minimum_n or not np.isfinite(numeric[columns].to_numpy(dtype=float)).all():
        raise CaseStudyAnalysisError(
            f"robustness model has fewer than {minimum_n} finite complete areas"
        )
    if (numeric["acs_adult_population"] <= 0).any():
        raise CaseStudyAnalysisError("adult-population weights must be positive")
    return numeric.reset_index(drop=True)


def _frozen_scaling(complete: pd.DataFrame, model_id: str) -> dict[str, tuple[float, float]]:
    scaling: dict[str, tuple[float, float]] = {}
    for column in MODEL_EXPOSURES[model_id]:
        scale = float(complete[column].quantile(0.75) - complete[column].quantile(0.25))
        scaling[column] = (float(complete[column].mean()), scale)
    for column in ADJUSTMENT_COVARIATES:
        scaling[column] = (float(complete[column].mean()), float(complete[column].std(ddof=1)))
    if any(scale <= 0 or not np.isfinite(scale) for _, scale in scaling.values()):
        raise CaseStudyAnalysisError("robustness scaling contains a nonpositive value")
    return scaling


def _fit_adjusted(
    complete: pd.DataFrame,
    model_id: str,
    *,
    scaling: dict[str, tuple[float, float]],
    weights: np.ndarray | None = None,
    capture_quartiles: tuple[float, float, float] | None = None,
) -> _FitResult:
    transformed = complete.copy()
    predictors = list(MODEL_EXPOSURES[model_id])
    for column in (*MODEL_EXPOSURES[model_id], *ADJUSTMENT_COVARIATES):
        if column == "capture_rate_mean_2022_2024" and capture_quartiles is not None:
            continue
        center, scale = scaling[column]
        transformed[column] = (transformed[column] - center) / scale
        predictors.append(column) if column in ADJUSTMENT_COVARIATES else None
    if capture_quartiles is not None:
        categories = np.digitize(
            complete["capture_rate_mean_2022_2024"].to_numpy(dtype=float),
            capture_quartiles,
            right=True,
        )
        for category in (1, 2, 3):
            column = f"capture_quartile_{category + 1}"
            transformed[column] = (categories == category).astype(float)
            predictors.append(column)
    design = np.column_stack(
        [
            np.ones(len(transformed)),
            *(transformed[column].to_numpy(dtype=float) for column in predictors),
        ]
    )
    outcome = transformed[OUTCOME].to_numpy(dtype=float)
    if weights is None:
        root_weights = np.ones(len(outcome))
    else:
        root_weights = np.sqrt(np.asarray(weights, dtype=float))
    weighted_design = design * root_weights[:, None]
    weighted_outcome = outcome * root_weights
    crossproduct = weighted_design.T @ weighted_design
    if np.linalg.matrix_rank(crossproduct) < crossproduct.shape[0]:
        raise CaseStudyAnalysisError("robustness design matrix is rank deficient")
    inverse = np.linalg.inv(crossproduct)
    beta = inverse @ weighted_design.T @ weighted_outcome
    weighted_residual = weighted_outcome - weighted_design @ beta
    leverage = np.einsum("ij,jk,ik->i", weighted_design, inverse, weighted_design)
    adjusted = weighted_residual / (1 - leverage)
    covariance = (
        inverse @ (weighted_design.T @ ((adjusted * adjusted)[:, None] * weighted_design)) @ inverse
    )
    contrast = np.zeros(len(beta))
    contrast[1 : 1 + len(MODEL_EXPOSURES[model_id])] = 1.0
    estimate = float(contrast @ beta)
    variance = float(contrast @ covariance @ contrast)
    critical = float(stats.norm.ppf(0.9875))
    standard_error = float(np.sqrt(variance))
    return {
        "estimate": estimate,
        "ci_low": estimate - critical * standard_error,
        "ci_high": estimate + critical * standard_error,
        "eligible_n": len(complete),
        "design": design,
        "outcome": outcome,
        "beta": beta,
        "covariance": covariance,
    }


def _governed_primary_execution(frame: pd.DataFrame) -> dict[str, bool]:
    readiness = assess_primary_model_readiness(frame).set_index("model_id")["status"]
    return {
        "C1": False,
        "C2": bool(readiness.get("C2") == "ready_for_adjusted_primary_model"),
    }


def _analysis_status(model_id: str, primary_estimand_executed: bool) -> str:
    if model_id == "C2" and primary_estimand_executed:
        return "freeze_candidate_primary_model_unsecured"
    return "audit_only_exploratory"


def _variant_record(
    model_id: str,
    variant: str,
    fit: _FitResult,
    reference: _FitResult,
    *,
    target_population: str,
    estimator: str,
    primary_estimand_executed: bool,
) -> dict[str, object]:
    estimate = float(fit["estimate"])
    ci_low = float(fit["ci_low"])
    ci_high = float(fit["ci_high"])
    reference_estimate = float(reference["estimate"])
    change, reason = absolute_percentage_change(reference_estimate, estimate, return_reason=True)
    stable = direction_stability(reference_estimate, estimate)
    overlap = ci_overlap(float(reference["ci_low"]), float(reference["ci_high"]), ci_low, ci_high)
    crossed = bool(stable is False or (np.isfinite(change) and change > 30))
    return {
        "model": model_id,
        "estimand": model_id,
        "variant": variant,
        "target_population": target_population,
        "estimate": estimate,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "eligible_n": int(fit["eligible_n"]),
        "direction_stability": stable,
        "absolute_percentage_change": change,
        "ci_overlap": overlap,
        "threshold_crossed": (
            "crossed:sign_change_or_absolute_percentage_change_gt_30"
            if crossed
            else "not_crossed:sign_change_or_absolute_percentage_change_gt_30"
        ),
        "analysis_status": _analysis_status(model_id, primary_estimand_executed),
        "authorization_status": "results_not_authorized",
        "percentage_change_reason": reason,
        "estimator": estimator,
        "covariance_type": "HC3",
        "adjustment_set": "|".join(ADJUSTMENT_COVARIATES),
        "primary_estimand_executed": primary_estimand_executed,
        "results_authorized": False,
    }
