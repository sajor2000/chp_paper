"""Governed uncertainty propagation for tract-level descriptive agreement."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from chicagohealthmap.analysis.case_studies import CaseStudyAnalysisError
from chicagohealthmap.analysis.contracts import A1_A7_ANALYSIS_NAMES, validate_analysis_result

BOOTSTRAP_SEED = 20260715


def parse_places_confidence_interval(value: object) -> tuple[float, float]:
    """Parse a PLACES percentage interval and fail closed on malformed bounds."""

    numbers = re.findall(r"[+-]?\d+(?:\.\d+)?", str(value))
    if len(numbers) != 2:
        raise ValueError("PLACES confidence interval must contain exactly two numeric bounds")
    lower, upper = (float(number) for number in numbers)
    if not np.isfinite([lower, upper]).all() or not 0 <= lower < upper <= 100:
        raise ValueError("PLACES confidence interval bounds must be ordered within 0 to 100")
    return lower, upper


def _percentile_rank(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.isna().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise CaseStudyAnalysisError("percentile ranks require finite values")
    return numeric.rank(method="average", pct=True, ascending=True)


def _not_run_record(base: dict[str, object], status: str, seed: int) -> dict[str, object]:
    return validate_analysis_result(
        {
            **base,
            "status": status,
            "uncertainty_source": "PLACES interval required for comparator-rank uncertainty",
            "joint_uncertainty_status": "not_run_incompatible_uncertainty_contract",
            "replicate_count": 0,
            "seed": seed,
        }
    )


def propagate_uncertainty_discordance(
    frame: pd.DataFrame,
    *,
    n_replicates: int = 1000,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, object]:
    """Propagate PLACES intervals into comparator ranks without mixing ACS uncertainty."""

    required = {"geography_id", "condition_id", "ehr_percent", "public_comparator_estimate"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"uncertainty propagation is missing columns: {missing}")
    conditions = sorted(frame["condition_id"].dropna().astype(str).unique())
    if len(conditions) != 1:
        raise CaseStudyAnalysisError("uncertainty propagation requires exactly one condition")
    lower_name = next(
        (name for name in ("public_comparator_lower", "public_comparator_ci_low") if name in frame),
        None,
    )
    upper_name = next(
        (
            name
            for name in ("public_comparator_upper", "public_comparator_ci_high")
            if name in frame
        ),
        None,
    )
    base: dict[str, object] = {
        "analysis_id": "A5",
        "analysis_name": A1_A7_ANALYSIS_NAMES["A5"],
        "condition_id": conditions[0],
        "estimand": "share of tract rank gaps exceeding comparator uncertainty",
        "unit": "probability of discordance beyond supplied interval",
        "denominator": int(len(frame)),
        "period": "pooled source rows supplied by caller",
        "uncertainty": "seeded Monte-Carlo interval propagation",
        "diagnostic_status": "not_run",
        "sensitivity_status": "primary_interval_rule",
        "source_artifact": "direct_chm_and_governed_public_interval_frame",
        "results_authorized": False,
        "discordance_rule": "absolute percentile-rank gap >0.25",
    }
    work_frame = frame.copy()
    if lower_name is None or upper_name is None:
        if "public_comparator_confidence_interval" not in work_frame:
            return _not_run_record(base, "not_run_uncertainty_unavailable", seed)
        parsed: list[tuple[float, float]] = []
        try:
            parsed = [
                parse_places_confidence_interval(value)
                for value in work_frame["public_comparator_confidence_interval"]
            ]
        except ValueError:
            return _not_run_record(base, "not_run_uncertainty_unavailable", seed)
        work_frame["public_comparator_lower"] = [bounds[0] for bounds in parsed]
        work_frame["public_comparator_upper"] = [bounds[1] for bounds in parsed]
        lower_name, upper_name = "public_comparator_lower", "public_comparator_upper"
    contract = {
        "public_comparator_unit": "percent",
        "public_comparator_confidence_level": 0.95,
        "public_comparator_geography_vintage": "2020_census_tract",
    }
    compatible_source = (
        "public_comparator_source_id" in work_frame
        and work_frame["public_comparator_source_id"].notna().all()
        and work_frame["public_comparator_source_id"]
        .isin({"cdc_places", "cdc_places_current_tract"})
        .all()
    )
    if not compatible_source or not all(
        name in frame and frame[name].notna().all() and frame[name].eq(expected).all()
        for name, expected in contract.items()
    ):
        return _not_run_record(base, "not_run_incompatible_uncertainty_contract", seed)
    if n_replicates < 1:
        raise CaseStudyAnalysisError("uncertainty replicate count must be positive")
    work = work_frame[list(required) + [lower_name, upper_name]].copy()
    numeric = work.drop(columns=["geography_id", "condition_id"]).apply(
        pd.to_numeric, errors="coerce"
    )
    work[numeric.columns] = numeric
    valid = numeric.notna().all(axis=1) & np.isfinite(numeric).all(axis=1)
    work = work.loc[
        valid
        & numeric[lower_name].ge(0)
        & numeric[upper_name].le(100)
        & numeric[lower_name].lt(numeric[upper_name])
    ]
    if work.empty:
        return _not_run_record(base, "not_run_uncertainty_unavailable", seed)
    ehr_rank = _percentile_rank(work["ehr_percent"])
    rng = np.random.default_rng(seed)
    discordant = np.zeros(len(work), dtype=float)
    for _ in range(n_replicates):
        standard_error = (
            work[upper_name].to_numpy(dtype=float) - work[lower_name].to_numpy(dtype=float)
        ) / (2 * 1.96)
        sampled = rng.normal(
            work["public_comparator_estimate"].to_numpy(dtype=float), standard_error
        )
        sampled = np.clip(sampled, 0.0, 100.0)
        public_rank = _percentile_rank(pd.Series(sampled, index=work.index))
        discordant += (ehr_rank.subtract(public_rank).abs().to_numpy() > 0.25).astype(float)
    probability = discordant / n_replicates
    return validate_analysis_result(
        {
            **base,
            "status": "available_places_only_interval_propagation",
            "diagnostic_status": "eligible",
            "uncertainty_source": "CDC PLACES confidence interval only",
            "uncertainty_role": "public_comparator_rank_uncertainty",
            "joint_uncertainty_status": "not_run_incompatible_uncertainty_contract",
            "eligible_n": int(len(work)),
            "replicate_count": int(n_replicates),
            "seed": int(seed),
            "mean_discordance_probability": float(probability.mean()),
            "max_discordance_probability": float(probability.max()),
            "tract_discordance_probability": dict(
                zip(work["geography_id"].astype(str), probability.astype(float), strict=True)
            ),
        }
    )
