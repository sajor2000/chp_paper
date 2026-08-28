"""Governed tract-level complementarity and within-area heterogeneity summaries.

All functions in this module are descriptive.  They compare direct EHR-diagnosed
tract observations with a public comparator and use ``measurement_discordance`` as
the neutral interpretation.  No area prevalence is reconstructed.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from scipy import stats  # type: ignore[import-untyped]
from chicagohealthmap.analysis.contracts import A1_A7_ANALYSIS_NAMES, validate_analysis_result

from chicagohealthmap.analysis.case_studies import (
    CaseStudyAnalysisError,
    combined_diabetes_is_approved,
)
from chicagohealthmap.analysis.uncertainty_analysis import (
    parse_places_confidence_interval as parse_places_confidence_interval,
    propagate_uncertainty_discordance as propagate_uncertainty_discordance,
)

BOOTSTRAP_SEED = 20260715
BOOTSTRAP_REPLICATES = 1000
DOMINANT_ASSIGNMENT_THRESHOLD = 0.99
CONTEMPORARY_YEARS = ("2022", "2023", "2024")
DIRECT_DERIVATION = "direct_first_party_export_not_interpolated"
DIABETES_COMPONENTS = {"diabetes_with_complication", "diabetes_without_complication"}


def _measure_column(frame: pd.DataFrame) -> str:
    for column in ("ehr_percent", "published_measure_value"):
        if column in frame:
            return column
    raise CaseStudyAnalysisError("descriptive analysis requires a direct CHM measure column")


def _validate_descriptive_input(frame: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    required = {"geography_id", "community_area_id", "condition_id"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"descriptive analysis is missing columns: {missing}")
    condition_ids = frame["condition_id"].dropna().astype(str).unique()
    if len(condition_ids) != 1:
        raise CaseStudyAnalysisError("descriptive analysis requires one condition")
    if "geography_type" in frame and frame["geography_type"].astype(str).ne("census_tract").any():
        raise CaseStudyAnalysisError("descriptive tract analyses require census-tract rows")
    if "disease_value_derivation" in frame:
        if frame["disease_value_derivation"].astype(str).ne(DIRECT_DERIVATION).any():
            raise CaseStudyAnalysisError(
                "descriptive analyses require direct, uninterpolated CHM values"
            )
    if "suppression_flag" in frame:
        suppressed = (
            frame["suppression_flag"]
            .astype("string")
            .str.lower()
            .isin({"1", "true", "t", "yes", "y"})
        )
        if suppressed.any():
            raise CaseStudyAnalysisError("descriptive analyses require suppression-excluded rows")
    measure = _measure_column(frame)
    work = frame.copy()
    work[measure] = pd.to_numeric(work[measure], errors="coerce")
    work = work.dropna(subset=["community_area_id", measure])
    if not np.isfinite(work[measure].to_numpy(dtype=float)).all():
        raise CaseStudyAnalysisError("descriptive measure contains nonfinite values")
    if work["geography_id"].duplicated().any():
        raise CaseStudyAnalysisError("descriptive analysis requires one row per tract")
    if "time_period" in work:
        periods = set(work["time_period"].astype(str))
        if not periods.issubset(set(CONTEMPORARY_YEARS)):
            raise CaseStudyAnalysisError("descriptive analyses are limited to 2022-2024")
    return work, measure


def _moment_vpc(work: pd.DataFrame, measure: str, group_column: str = "community_area_id") -> float:
    groups = work.groupby(group_column, sort=True)[measure]
    group_count = groups.ngroups
    counts = groups.size()
    means = groups.mean()
    grand = float(work[measure].mean())
    ss_between = float(((means - grand).pow(2) * counts).sum())
    ss_within = float(groups.apply(lambda values: ((values - values.mean()) ** 2).sum()).sum())
    if ss_between + ss_within <= 0 or group_count < 2 or len(work) <= group_count:
        raise CaseStudyAnalysisError("variance partition is not estimable")
    ms_between = ss_between / (group_count - 1)
    ms_within = ss_within / (len(work) - group_count)
    n_bar = (len(work) - float((counts**2).sum() / len(work))) / (group_count - 1)
    between_variance = max((ms_between - ms_within) / max(n_bar, 1.0), 0.0)
    return float(between_variance / (between_variance + ms_within))


def compute_variance_partition(frame: pd.DataFrame) -> dict[str, object]:
    """Estimate the share of direct tract-measure variance between areas.

    The point estimate and every cluster-bootstrap replicate use the same
    one-way random-effects method-of-moments estimator. This is an observed-scale
    tract-measure partition, not a patient-level intraclass correlation.
    """

    work, measure = _validate_descriptive_input(frame)
    if work["community_area_id"].nunique() < 2 or len(work) < 3:
        raise CaseStudyAnalysisError(
            "variance partition requires at least two areas and three tracts"
        )
    vpc = _moment_vpc(work, measure)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    area_ids = np.array(sorted(work["community_area_id"].astype(str).unique()))
    area_frames = {
        str(area): group.copy()
        for area, group in work.groupby(work["community_area_id"].astype(str), sort=False)
    }
    bootstrap_values: list[float] = []
    failed_replicates = 0
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled = rng.choice(area_ids, size=len(area_ids), replace=True)
        parts = []
        for index, area in enumerate(sampled):
            part = area_frames[str(area)].copy()
            part["community_area_id"] = f"{area}__bootstrap_{index}"
            parts.append(part)
        try:
            bootstrap_values.append(_moment_vpc(pd.concat(parts, ignore_index=True), measure))
        except CaseStudyAnalysisError:
            failed_replicates += 1
    if len(bootstrap_values) < 0.95 * BOOTSTRAP_REPLICATES:
        raise CaseStudyAnalysisError("fewer than 95% of VPC bootstrap replicates were estimable")
    ci_low, ci_high = np.quantile(bootstrap_values, [0.025, 0.975])
    condition_id = str(work["condition_id"].iloc[0])
    result = {
        "analysis_id": "A1",
        "analysis_name": A1_A7_ANALYSIS_NAMES["A1"],
        "estimand": "between-community-area share of direct tract-measure variance",
        "unit": "proportion of variance",
        "denominator": int(len(work)),
        "period": "2022-2024 pooled direct tract measures",
        "uncertainty": "95% nonparametric community-area cluster bootstrap interval",
        "diagnostic_status": "eligible_with_precision_caution",
        "sensitivity_status": "primary_direct_tract_assignment",
        "source_artifact": "direct_chm_tract_frame",
        "results_authorized": False,
        "condition_id": condition_id,
        "scale": "census_tract",
        "assignment_rule": "direct_or_dominant_linkage",
        "estimate": float(vpc),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "bootstrap_requested_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_replicates": len(bootstrap_values),
        "bootstrap_failed_replicates": failed_replicates,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_cluster_unit": "community_area_id",
        "bootstrap_estimator": "method_of_moments_cluster_resample",
        "bootstrap_interval_method": "percentile_2.5_97.5",
        "estimator": "method_of_moments_one_way_random_effects",
        "eligible_n": int(len(work)),
        "community_area_n": int(work["community_area_id"].nunique()),
        "vpc_icc": float(vpc),
        "within_variance_share": float(1.0 - vpc),
    }
    return validate_analysis_result(result)


def compute_discriminatory_accuracy(
    frame: pd.DataFrame, *, threshold: str = "75th_percentile"
) -> dict[str, object]:
    """Quantify how well area labels separate high direct tract measures.

    The rank-based AUC is a descriptive separation statistic.  It is not a
    prediction, validation, or claim of superiority for the area label.
    """

    work, measure = _validate_descriptive_input(frame)
    quantiles = {"median": 0.5, "tertile": 2 / 3, "75th_percentile": 0.75}
    if threshold not in quantiles:
        raise CaseStudyAnalysisError(f"unsupported discriminatory threshold: {threshold}")
    area_counts = work.groupby("community_area_id")[measure].transform("size")
    work = work.loc[area_counts.ge(2)].copy()
    area_counts = work.groupby("community_area_id")[measure].transform("size")
    cutoff = float(work[measure].quantile(quantiles[threshold]))
    labels = work[measure].ge(cutoff).astype(int)
    if labels.nunique() < 2:
        raise CaseStudyAnalysisError("discriminatory accuracy threshold has one eligible class")
    area_sum = work.groupby("community_area_id")[measure].transform("sum")
    area_score = (area_sum - work[measure]) / (area_counts.loc[work.index] - 1)
    high = area_score.loc[labels.eq(1)]
    low = area_score.loc[labels.eq(0)]
    auc = float(
        stats.mannwhitneyu(high, low, alternative="two-sided").statistic / (len(high) * len(low))
    )
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    area_ids = np.array(sorted(work["community_area_id"].astype(str).unique()))
    area_frames = {
        str(area): group.copy()
        for area, group in work.groupby(work["community_area_id"].astype(str), sort=False)
    }
    auc_bootstrap: list[float] = []
    failed_replicates = 0
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled = rng.choice(area_ids, size=len(area_ids), replace=True)
        parts = []
        for index, area in enumerate(sampled):
            part = area_frames[str(area)].copy()
            part["community_area_id"] = f"{area}__bootstrap_{index}"
            parts.append(part)
        replicate = pd.concat(parts, ignore_index=True)
        replicate_scores = replicate.groupby("community_area_id")[measure].transform("sum")
        replicate_counts = replicate.groupby("community_area_id")[measure].transform("size")
        replicate_cutoff = float(replicate[measure].quantile(quantiles[threshold]))
        replicate_labels = replicate[measure].ge(replicate_cutoff).astype(int)
        if replicate_labels.nunique() < 2 or (replicate_counts < 2).any():
            failed_replicates += 1
            continue
        replicate_scores = (replicate_scores - replicate[measure]) / (replicate_counts - 1)
        high_rep = replicate_scores.loc[replicate_labels.eq(1)]
        low_rep = replicate_scores.loc[replicate_labels.eq(0)]
        auc_bootstrap.append(
            float(stats.mannwhitneyu(high_rep, low_rep, alternative="two-sided").statistic)
            / (len(high_rep) * len(low_rep))
        )
    ci_low, ci_high = (
        np.quantile(auc_bootstrap, [0.025, 0.975]) if auc_bootstrap else (np.nan, np.nan)
    )
    result = {
        "analysis_id": "A2",
        "analysis_name": A1_A7_ANALYSIS_NAMES["A2"],
        "estimand": "descriptive separation of high direct tract measures by community-area label",
        "unit": "area-label AUC",
        "denominator": int(len(work)),
        "period": "2022-2024 pooled direct tract measures",
        "uncertainty": "95% nonparametric community-area cluster bootstrap interval",
        "diagnostic_status": "eligible_with_descriptive_boundary",
        "sensitivity_status": threshold,
        "source_artifact": "direct_chm_tract_frame",
        "results_authorized": False,
        "condition_id": str(work["condition_id"].iloc[0]),
        "scale": "census_tract",
        "assignment_rule": "direct_or_dominant_linkage",
        "estimate": auc,
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "bootstrap_replicates": int(len(auc_bootstrap)),
        "bootstrap_requested_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_failed_replicates": failed_replicates,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_cluster_unit": "community_area_id",
        "bootstrap_interval_method": "percentile_2.5_97.5",
        "estimator": "mann_whitney_leave_one_tract_out_area_mean",
        "eligible_n": int(len(work)),
        "threshold": threshold,
        "threshold_value": cutoff,
        "bootstrap_threshold_rule": "recomputed_within_each_cluster_resample",
        "auc": auc,
    }
    return validate_analysis_result(result)


def percentile_rank(values: pd.Series) -> pd.Series:
    """Return deterministic within-source percentile ranks (average ties, 0-1 scale)."""

    if not isinstance(values, pd.Series):
        values = pd.Series(values)
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.isna().any():
        raise CaseStudyAnalysisError("percentile ranks require finite values")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise CaseStudyAnalysisError("percentile ranks require finite values")
    return numeric.rank(method="average", pct=True, ascending=True)


def _rerank_concordance(frame: pd.DataFrame) -> pd.DataFrame:
    """Recompute all rank-derived fields for one analytic sample."""

    ranked = frame.copy()
    ranked["ehr_rank"] = percentile_rank(ranked["ehr_percent"])
    ranked["public_rank"] = percentile_rank(ranked["public_comparator_estimate"])
    ranked["paired_percentile_rank_gap"] = ranked["ehr_rank"] - ranked["public_rank"]
    ranked["absolute_percentile_rank_gap"] = ranked["paired_percentile_rank_gap"].abs()
    ranked["discordance_category"] = _discordance_categories(ranked)
    return ranked


def assign_capture_quartile(
    values: pd.Series, frozen_cut_points: tuple[float, float, float] | None = None
) -> dict[str, object]:
    """Assign deterministic capture quartiles using linear quantiles."""

    if not isinstance(values, pd.Series):
        values = pd.Series(values)
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.isna().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise CaseStudyAnalysisError("capture quartiles require finite values")
    cuts = frozen_cut_points or tuple(
        float(value) for value in np.quantile(numeric, [0.25, 0.50, 0.75], method="linear")
    )
    if not len(cuts) == 3 or not np.all(np.isfinite(cuts)):
        raise CaseStudyAnalysisError("capture quartiles require three finite cut points")
    if not (cuts[0] < cuts[1] < cuts[2]):
        raise CaseStudyAnalysisError("capture quartile cut points are not strictly increasing")
    labels = pd.Series(
        np.select(
            [numeric.le(cuts[0]), numeric.le(cuts[1]), numeric.le(cuts[2])],
            ["Q1", "Q2", "Q3"],
            default="Q4",
        ),
        index=values.index,
        dtype="object",
    )
    return {"cut_points": tuple(float(cut) for cut in cuts), "labels": labels}


def _required_columns(dataset: pd.DataFrame) -> None:
    required = {
        "geography_type",
        "geography_id",
        "time_period",
        "condition_id",
        "numerator",
        "denominator",
        "published_measure_value",
        "public_comparator_estimate",
        "suppression_flag",
        "capture_rate",
        "reliability_tier",
        "community_area_id",
        "max_community_area_weight",
        "is_crossing_tract",
        "disease_value_derivation",
    }
    missing = sorted(required - set(dataset.columns))
    if missing:
        raise CaseStudyAnalysisError(f"tract complementarity dataset is missing columns: {missing}")


def _metadata(frame: pd.DataFrame) -> pd.DataFrame:
    metadata_columns = [
        "geography_id",
        "community_area_id",
        "max_community_area_weight",
        "is_crossing_tract",
        "capture_rate",
        "reliability_tier",
        "reliability_flag",
        "source_id",
        "snapshot_id",
    ]
    available = [column for column in metadata_columns if column in frame]
    records: list[dict[str, object]] = []
    for tract, group in frame.groupby("geography_id", sort=True, dropna=False):
        record: dict[str, object] = {"geography_id": tract}
        for column in available:
            values = group[column].dropna().astype(str).unique().tolist()
            if column in {"capture_rate", "max_community_area_weight"}:
                numeric = pd.to_numeric(group[column], errors="coerce").dropna()
                if numeric.empty and column == "max_community_area_weight":
                    raise CaseStudyAnalysisError(f"tract {tract} has missing {column}")
                record[column] = float(numeric.mean()) if not numeric.empty else np.nan
                if column == "max_community_area_weight":
                    record[column] = float(numeric.min())
            elif column == "is_crossing_tract":
                record[column] = bool(group[column].fillna(True).astype(bool).any())
            else:
                if len(values) > 1:
                    raise CaseStudyAnalysisError(f"tract {tract} has conflicting {column}")
                record[column] = values[0] if values else pd.NA
        records.append(record)
    return pd.DataFrame.from_records(records)


def _pooled_direct_measure(dataset: pd.DataFrame, geography_type: str) -> pd.DataFrame:
    """Pool direct numerator/denominator records across years, failing closed for diabetes."""

    required = {
        "geography_type", "geography_id", "time_period", "condition_id", "condition_family",
        "numerator", "denominator", "published_measure_value", "suppression_flag",
        "disease_value_derivation",
    }
    missing = sorted(required - set(dataset.columns))
    if missing:
        raise CaseStudyAnalysisError(f"pooled direct measure is missing columns: {missing}")
    direct = dataset.loc[
        dataset["geography_type"].eq(geography_type)
        & dataset["time_period"].astype(str).isin(CONTEMPORARY_YEARS)
        & dataset["disease_value_derivation"].eq(DIRECT_DERIVATION)
        & ~dataset["suppression_flag"].astype(bool)
    ].copy()
    direct["numerator"] = pd.to_numeric(direct["numerator"], errors="coerce")
    direct["denominator"] = pd.to_numeric(direct["denominator"], errors="coerce")
    minimum_denominator = 30 if geography_type == "census_tract" else 1
    direct = direct.loc[
        direct["numerator"].ge(0) & direct["denominator"].ge(minimum_denominator)
    ].copy()
    key = ["geography_id", "time_period", "condition_id"]
    if direct.duplicated(key).any():
        raise CaseStudyAnalysisError("duplicate direct geography-condition-year rows")
    non_diabetes = direct.loc[~direct["condition_family"].eq("diabetes")].copy()
    diabetes = direct.loc[direct["condition_family"].eq("diabetes")].copy()
    diabetes = diabetes.groupby(["geography_id", "time_period"], group_keys=False).filter(
        combined_diabetes_is_approved
    )
    if not diabetes.empty:
        diabetes = diabetes.groupby(["geography_id", "time_period"], as_index=False).agg(
            numerator=("numerator", "sum"), denominator=("denominator", "first")
        )
        diabetes["condition_id"] = "diabetes"
    annual = pd.concat(
        [non_diabetes[["geography_id", "time_period", "condition_id", "numerator", "denominator"]], diabetes],
        ignore_index=True,
        sort=False,
    )
    pooled = annual.groupby(["geography_id", "condition_id"], as_index=False).agg(
        numerator=("numerator", "sum"), denominator=("denominator", "sum"),
        eligible_years=("time_period", "nunique"),
    )
    pooled = pooled.loc[pooled["eligible_years"].eq(len(CONTEMPORARY_YEARS))].copy()
    pooled["ehr_percent"] = 100 * pooled["numerator"] / pooled["denominator"]
    return pooled


def build_direct_tract_analysis_frame(
    dataset: pd.DataFrame,
    *,
    noncrossing_only: bool = False,
    area_assignment_threshold: float = DOMINANT_ASSIGNMENT_THRESHOLD,
) -> pd.DataFrame:
    """Build the CHM-only pooled tract frame used by A1 and exploratory A2."""

    _required_columns(dataset)
    if not 0 < area_assignment_threshold <= 1:
        raise CaseStudyAnalysisError("area assignment threshold must be in (0, 1]")
    tract = dataset.loc[
        dataset["geography_type"].eq("census_tract")
        & dataset["time_period"].astype(str).isin(CONTEMPORARY_YEARS)
    ].copy()
    tract = tract.loc[
        pd.to_numeric(tract["max_community_area_weight"], errors="coerce")
        >= area_assignment_threshold
    ].copy()
    if noncrossing_only:
        tract = tract.loc[~tract["is_crossing_tract"].astype(bool)].copy()
    pooled = _pooled_direct_measure(tract, "census_tract")
    if pooled.empty:
        raise CaseStudyAnalysisError("no eligible direct tract observations")
    pooled = pooled.merge(_metadata(tract), on="geography_id", how="left", validate="many_to_one")
    pooled["ehr_rank"] = pooled.groupby("condition_id", sort=False)["ehr_percent"].rank(
        method="average", pct=True
    )
    pooled["assignment_rule"] = (
        f"dominant_community_area_max_overlay_weight_gte_{area_assignment_threshold:.2f}"
    )
    pooled["crossing_sensitivity"] = "noncrossing_only" if noncrossing_only else "all_eligible"
    pooled["analysis_population"] = "chm_only_complete_2022_2024"
    pooled["results_authorized"] = False
    return pooled.sort_values(
        ["condition_id", "geography_id"], kind="mergesort", ignore_index=True
    )


def _aggregate_annual(tract: pd.DataFrame) -> pd.DataFrame:
    """Build eligible annual direct values for denominator-pooled rank summaries."""

    tract = tract.copy()
    direct = tract[tract["disease_value_derivation"].eq(DIRECT_DERIVATION)].copy()
    direct["eligible"] = (
        ~direct["suppression_flag"].astype(bool)
        & direct["numerator"].notna()
        & direct["denominator"].notna()
        & direct["published_measure_value"].notna()
        & direct["public_comparator_estimate"].notna()
    )
    direct["published_measure_value"] = pd.to_numeric(
        direct["published_measure_value"], errors="coerce"
    )
    direct["numerator"] = pd.to_numeric(direct["numerator"], errors="coerce")
    direct["denominator"] = pd.to_numeric(direct["denominator"], errors="coerce")
    key = ["geography_id", "time_period", "condition_id"]
    if direct.duplicated(key).any():
        raise CaseStudyAnalysisError("duplicate tract-condition-year rows")
    direct["eligible"] &= direct["numerator"].ge(0) & direct["denominator"].ge(30)
    non_diabetes = direct.loc[~direct["condition_id"].isin(DIABETES_COMPONENTS)].copy()
    diabetes = direct.loc[direct["condition_id"].isin(DIABETES_COMPONENTS)].copy()
    diabetes = diabetes.groupby(["geography_id", "time_period"], group_keys=False).filter(
        combined_diabetes_is_approved
    )
    if not diabetes.empty:
        diabetes = diabetes.groupby(["geography_id", "time_period"], as_index=False).agg(
            numerator=("numerator", "sum"),
            denominator=("denominator", "first"),
            eligible=("eligible", "all"),
        )
        diabetes["condition_id"] = "diabetes"
        diabetes["public_comparator_estimate"] = np.nan
    annual = pd.concat(
        [
            non_diabetes[
                [
                    "geography_id", "time_period", "condition_id", "numerator", "denominator",
                    "public_comparator_estimate", "eligible",
                ]
            ],
            diabetes,
        ],
        ignore_index=True,
        sort=False,
    )
    annual["ehr_percent"] = 100 * annual["numerator"] / annual["denominator"]
    return annual


def build_tract_percentile_concordance(
    dataset: pd.DataFrame,
    *,
    noncrossing_only: bool = False,
    area_assignment_threshold: float = DOMINANT_ASSIGNMENT_THRESHOLD,
    capture_cut_points: tuple[float, float, float],
) -> pd.DataFrame:
    """Build one eligible, dominantly assigned row per tract-condition."""

    _required_columns(dataset)
    if not 0 < area_assignment_threshold <= 1:
        raise CaseStudyAnalysisError("area assignment threshold must be in (0, 1]")
    tract = dataset.loc[
        dataset["geography_type"].eq("census_tract")
        & dataset["time_period"].astype(str).isin(CONTEMPORARY_YEARS)
    ].copy()
    key = ["geography_id", "time_period", "condition_id"]
    if tract.duplicated(key).any():
        raise CaseStudyAnalysisError("duplicate tract-condition-year rows")
    tract = tract.loc[
        pd.to_numeric(tract["max_community_area_weight"], errors="coerce")
        >= area_assignment_threshold
    ].copy()
    if noncrossing_only:
        tract = tract.loc[~tract["is_crossing_tract"].astype(bool)].copy()
    if tract.empty:
        raise CaseStudyAnalysisError("no tracts remain after assignment eligibility")
    annual = _aggregate_annual(tract)
    if annual.empty:
        raise CaseStudyAnalysisError("no eligible direct tract observations")
    eligible = annual.loc[annual["eligible"]].copy()
    frame = eligible.groupby(["geography_id", "condition_id"], sort=True, as_index=False).agg(
        numerator=("numerator", "sum"),
        denominator=("denominator", "sum"),
        public_comparator_estimate=("public_comparator_estimate", "first"),
        eligible_annual_rows=("time_period", "nunique"),
    )
    frame["ehr_percent"] = 100 * frame["numerator"] / frame["denominator"]
    annual_rows = annual.groupby(["geography_id", "condition_id"], sort=True, as_index=False).agg(
        annual_rows=("time_period", "nunique")
    )
    frame = frame.merge(annual_rows, on=["geography_id", "condition_id"], how="left")
    meta = _metadata(tract)
    frame = frame.merge(meta, on="geography_id", how="left", validate="many_to_one")
    frame["ineligible_annual_rows"] = frame["annual_rows"] - frame["eligible_annual_rows"]
    frame = frame.loc[
        frame["annual_rows"].eq(len(CONTEMPORARY_YEARS))
        & frame["eligible_annual_rows"].eq(len(CONTEMPORARY_YEARS))
    ].copy()
    frame["exposure_eligibility_status"] = "complete_2022_2024"
    frame["assignment_rule"] = (
        f"dominant_community_area_max_overlay_weight_gte_{area_assignment_threshold:.2f}"
    )
    frame["crossing_sensitivity"] = "noncrossing_only" if noncrossing_only else "all_eligible"
    ranks = []
    for _, group in frame.groupby("condition_id", sort=False):
        ranks.append(_rerank_concordance(group))
    frame = pd.concat(ranks, ignore_index=True).sort_values(
        ["condition_id", "geography_id"], kind="mergesort"
    )
    capture_values = pd.to_numeric(frame["capture_rate"], errors="coerce")
    valid_capture = capture_values.notna() & np.isfinite(capture_values)
    frame["capture_quartile"] = pd.Series("unavailable", index=frame.index, dtype="object")
    capture_points: tuple[float, float, float]
    if int(valid_capture.sum()) > 0:
        capture = assign_capture_quartile(capture_values.loc[valid_capture], capture_cut_points)
        labels = cast(pd.Series, capture["labels"])
        frame.loc[valid_capture, "capture_quartile"] = labels.astype(str)
        capture_points = cast(tuple[float, float, float], capture["cut_points"])
    else:
        capture_points = (np.nan, np.nan, np.nan)
    frame["capture_quartile_cut_points"] = "|".join(
        f"{float(value):.12g}" for value in capture_points
    )
    frame["source_reliability_provenance"] = frame.apply(
        lambda row: (
            f"source_id={row.get('source_id', pd.NA)};snapshot_id={row.get('snapshot_id', pd.NA)};reliability_tier={row.get('reliability_tier', pd.NA)};reliability_flag={row.get('reliability_flag', pd.NA)}"
        ),
        axis=1,
    )
    frame["analysis_status"] = "descriptive_measurement_discordance"
    frame["interpretation_label"] = "measurement_discordance_only_neutral"
    frame["results_authorized"] = pd.Series(False, index=frame.index, dtype=object)
    return frame.reset_index(drop=True)


def _discordance_categories(frame: pd.DataFrame) -> pd.Series:
    ehr = frame["ehr_rank"].astype(float)
    public = frame["public_rank"].astype(float)
    return pd.Series(
        np.select(
            [
                ehr.gt(0.75) & public.gt(0.75),
                ehr.le(0.25) & public.le(0.25),
                ehr.gt(0.75) & public.lt(0.50),
                public.gt(0.75) & ehr.lt(0.50),
            ],
            [
                "concordant_high",
                "concordant_low",
                "ehr_high_public_not_high",
                "public_high_ehr_not_high",
            ],
            default="intermediate",
        ),
        index=frame.index,
        dtype="object",
    )


def _quadratic_weighted_kappa(first: Iterable[int], second: Iterable[int]) -> float | None:
    values_first, values_second = list(first), list(second)
    if not values_first:
        return None
    observed = np.zeros((4, 4), dtype=float)
    for left, right in zip(values_first, values_second, strict=True):
        observed[int(left), int(right)] += 1
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0)) / observed.sum()
    weights = np.fromfunction(lambda row, column: ((row - column) / 3) ** 2, (4, 4))
    denominator = float((weights * expected).sum())
    return None if denominator == 0 else float(1 - (weights * observed).sum() / denominator)


def gwet_ac1(first: Iterable[int], second: Iterable[int], categories: int = 4) -> float | None:
    """Return Gwet's AC1 for two categorical ratings.

    The pooled marginal distribution supplies the chance-agreement term.  A
    degenerate or empty comparison is reported as not estimable rather than as
    a zero agreement statistic.
    """

    left, right = np.asarray(list(first), dtype=int), np.asarray(list(second), dtype=int)
    if left.size == 0 or left.size != right.size:
        return None
    if categories < 2 or np.any(left < 0) or np.any(right < 0):
        raise CaseStudyAnalysisError("Gwet AC1 categories are invalid")
    if np.any(left >= categories) or np.any(right >= categories):
        raise CaseStudyAnalysisError("Gwet AC1 category exceeds declared range")
    observed = float(np.mean(left == right))
    pooled = np.bincount(np.concatenate([left, right]), minlength=categories) / (2 * left.size)
    expected = float(np.sum(pooled * (1.0 - pooled)) / (categories - 1))
    if np.isclose(1.0 - expected, 0.0):
        return None
    return float((observed - expected) / (1.0 - expected))


def _quartile_bins(values: pd.Series) -> np.ndarray:
    return (_rank_quartile(values) - 1).to_numpy(dtype=int)


def _metric_record(group: pd.DataFrame) -> dict[str, object]:
    x = group["ehr_rank"].astype(float)
    y = group["public_rank"].astype(float)
    spearman = (
        stats.spearmanr(x, y) if len(group) >= 3 and x.nunique() > 1 and y.nunique() > 1 else None
    )
    return {
        "sample_n": int(len(group)),
        "spearman_r": float(spearman.statistic) if spearman is not None else np.nan,
        "quadratic_weighted_kappa": _quadratic_weighted_kappa(_quartile_bins(x), _quartile_bins(y)),
        "gwet_ac1": gwet_ac1(_quartile_bins(x), _quartile_bins(y)),
        "median_absolute_percentile_rank_gap": float(
            group["absolute_percentile_rank_gap"].median()
        ),
        "discordance_category_total": int(group["discordance_category"].notna().sum()),
    }


def summarize_concordance_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize agreement overall and by frozen capture/reliability strata."""

    required = {
        "condition_id",
        "ehr_rank",
        "public_rank",
        "absolute_percentile_rank_gap",
        "discordance_category",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"concordance frame is missing columns: {missing}")
    groups: list[tuple[str, object, pd.DataFrame]] = []
    for condition, group in frame.groupby("condition_id", sort=True):
        groups.append(("overall", condition, group))
        for (capture, reliability), strata in group.groupby(
            ["capture_quartile", "reliability_tier"], dropna=False, sort=True
        ):
            groups.append((f"capture={capture};reliability={reliability}", condition, strata))
    records = []
    for stratum, condition, group in groups:
        record = _metric_record(group)
        record.update(
            {
                "condition_id": str(condition),
                "stratum": stratum,
                "capture_quartile": stratum.split(";")[0].removeprefix("capture=")
                if stratum != "overall"
                else "all",
                "reliability_tier": stratum.split(";")[1].removeprefix("reliability=")
                if stratum != "overall"
                else "all",
                "source_reliability_provenance": "|".join(
                    sorted(
                        group.get("source_reliability_provenance", pd.Series(dtype=object))
                        .dropna()
                        .astype(str)
                        .unique()
                    )
                ),
                "assignment_rule": "dominant_community_area_max_overlay_weight_gte_0.99",
                "crossing_sensitivity": "|".join(
                    sorted(group["crossing_sensitivity"].astype(str).unique())
                )
                if "crossing_sensitivity" in group
                else "unspecified",
                "analysis_status": "descriptive_measurement_discordance",
                "interpretation_label": "measurement_discordance_only_neutral",
                "results_authorized": False,
            }
        )
        records.append(record)
    output = pd.DataFrame.from_records(records)
    output["results_authorized"] = pd.Series(False, index=output.index, dtype=object)
    output["_stratum_order"] = output["stratum"].ne("overall").astype(int)
    return (
        output.sort_values(["condition_id", "_stratum_order", "stratum"], kind="mergesort")
        .drop(columns="_stratum_order")
        .reset_index(drop=True)
    )


def summarize_within_community_heterogeneity(frame: pd.DataFrame) -> pd.DataFrame:
    """Describe direct tract rank distributions within each dominantly assigned area."""

    required = {"condition_id", "community_area_id", "ehr_rank", "is_crossing_tract"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"heterogeneity frame is missing columns: {missing}")
    records: list[dict[str, object]] = []
    for (condition, area), group in frame.groupby(
        ["condition_id", "community_area_id"], sort=True, dropna=False
    ):
        ranks = group["ehr_rank"].astype(float)
        top = ranks.gt(0.75)
        bottom = ranks.le(0.25)
        records.append(
            {
                "condition_id": str(condition),
                "community_area_id": str(area),
                "eligible_tract_count": int(len(group)),
                "median_rank": float(ranks.median()),
                "rank_iqr": float(ranks.quantile(0.75) - ranks.quantile(0.25)),
                "rank_range": float(ranks.max() - ranks.min()),
                "top_quartile_share": float(top.mean()),
                "bottom_quartile_share": float(bottom.mean()),
                "high_low_rank_coexistence": bool(top.any() and bottom.any()),
                "assignment_rule": str(group["assignment_rule"].iloc[0]),
                "max_overlay_weight": float(group["max_community_area_weight"].max()),
                "crossing_sensitivity": str(group["crossing_sensitivity"].iloc[0]),
                "analysis_status": "descriptive_within_community_distribution",
                "interpretation_label": "direct_tract_distribution_not_area_prevalence",
                "results_authorized": False,
            }
        )
    output = pd.DataFrame.from_records(records)
    output["results_authorized"] = pd.Series(False, index=output.index, dtype=object)
    return output


def _pooled_direct_ehr_percent(dataset: pd.DataFrame, geography_type: str) -> pd.DataFrame:
    required = {
        "geography_type",
        "geography_id",
        "time_period",
        "condition_id",
        "condition_family",
        "numerator",
        "denominator",
        "published_measure_value",
        "suppression_flag",
        "disease_value_derivation",
    }
    missing = sorted(required - set(dataset.columns))
    if missing:
        raise CaseStudyAnalysisError(f"aggregation-loss dataset is missing columns: {missing}")
    return _pooled_direct_measure(dataset, geography_type)


def build_direct_ehr_rank_frame(dataset: pd.DataFrame, geography_type: str) -> pd.DataFrame:
    """Rank SAP primary numerator/denominator-pooled CHM measures within condition."""

    pooled = _pooled_direct_ehr_percent(dataset, geography_type).copy()
    pooled["ehr_rank"] = pooled.groupby("condition_id", sort=True)["ehr_percent"].transform(
        percentile_rank
    )
    pooled["geography_type"] = geography_type
    pooled["results_authorized"] = False
    return pooled


def build_direct_consequence_rank_frame(dataset: pd.DataFrame, geography_type: str) -> pd.DataFrame:
    """Add mean annual source-denominator accounting to direct rank frames."""

    rank_frame = build_direct_ehr_rank_frame(dataset, geography_type)
    direct = dataset.loc[
        dataset["geography_type"].eq(geography_type)
        & dataset["time_period"].astype(str).isin(CONTEMPORARY_YEARS)
        & dataset["disease_value_derivation"].eq(DIRECT_DERIVATION)
    ].copy()
    direct["denominator"] = pd.to_numeric(direct["denominator"], errors="coerce")
    direct = direct.loc[
        ~direct["suppression_flag"].astype(bool) & direct["denominator"].notna()
    ].copy()
    non_diabetes = direct.loc[~direct["condition_family"].eq("diabetes")].copy()
    annual = non_diabetes.groupby(
        ["geography_id", "condition_family", "time_period"], sort=True, as_index=False
    ).agg(source_denominator=("denominator", "first"))
    diabetes = direct.loc[direct["condition_family"].eq("diabetes")].copy()
    diabetes = diabetes.groupby(["geography_id", "time_period"], sort=True).filter(
        combined_diabetes_is_approved
    )
    diabetes_annual = diabetes.groupby(
        ["geography_id", "time_period"], sort=True, as_index=False
    ).agg(source_denominator=("denominator", "first"))
    diabetes_annual["condition_family"] = "diabetes"
    annual = pd.concat([annual, diabetes_annual], ignore_index=True, sort=False)
    denominator = annual.groupby(
        ["geography_id", "condition_family"], sort=True, as_index=False
    ).agg(
        mean_annual_source_denominator=("source_denominator", "mean"),
        denominator_years=("time_period", "nunique"),
    )
    denominator = denominator.loc[denominator["denominator_years"].eq(len(CONTEMPORARY_YEARS))]
    denominator = denominator.rename(columns={"condition_family": "condition_id"})
    output = rank_frame.merge(
        denominator,
        on=["geography_id", "condition_id"],
        how="inner",
        validate="one_to_one",
    )
    output["denominator_unit"] = "mean_annual_source_denominator_not_unique_people"
    output["denominator_status"] = "guarded_source_position_25"
    output["results_authorized"] = False
    return output


def build_annual_direct_consequence_rank_frame(
    dataset: pd.DataFrame, geography_type: str
) -> pd.DataFrame:
    """Build year-specific direct ranks and source-denominator accounting."""

    direct = dataset.loc[
        dataset["geography_type"].eq(geography_type)
        & dataset["time_period"].astype(str).isin(CONTEMPORARY_YEARS)
        & dataset["disease_value_derivation"].eq(DIRECT_DERIVATION)
    ].copy()
    direct["denominator"] = pd.to_numeric(direct["denominator"], errors="coerce")
    direct["published_measure_value"] = pd.to_numeric(
        direct["published_measure_value"], errors="coerce"
    )
    direct = direct.loc[
        ~direct["suppression_flag"].astype(bool)
        & direct["numerator"].notna()
        & direct["denominator"].notna()
        & direct["published_measure_value"].notna()
    ].copy()
    key = ["geography_id", "time_period", "condition_id"]
    if direct.duplicated(key).any():
        raise CaseStudyAnalysisError("annual direct consequence frame contains duplicate rows")
    non_diabetes = direct.loc[~direct["condition_family"].eq("diabetes")].copy()
    non_diabetes["ehr_percent"] = non_diabetes["published_measure_value"] * 100
    non_diabetes["mean_annual_source_denominator"] = non_diabetes["denominator"]
    non_diabetes = non_diabetes.rename(columns={"condition_family": "analysis_condition_id"})
    annual = non_diabetes[
        [
            "geography_id",
            "time_period",
            "analysis_condition_id",
            "ehr_percent",
            "mean_annual_source_denominator",
        ]
    ].rename(columns={"analysis_condition_id": "condition_id"})
    diabetes = direct.loc[direct["condition_family"].eq("diabetes")].copy()
    diabetes = diabetes.groupby(["geography_id", "time_period"], sort=True).filter(
        combined_diabetes_is_approved
    )
    diabetes_annual = diabetes.groupby(
        ["geography_id", "time_period"], sort=True, as_index=False
    ).agg(
        ehr_percent=("published_measure_value", lambda values: float(values.sum() * 100)),
        mean_annual_source_denominator=("denominator", "first"),
    )
    diabetes_annual["condition_id"] = "diabetes"
    annual = pd.concat([annual, diabetes_annual], ignore_index=True, sort=False)
    annual["ehr_rank"] = annual.groupby(["condition_id", "time_period"], sort=True)[
        "ehr_percent"
    ].transform(percentile_rank)
    annual["geography_type"] = geography_type
    annual["denominator_unit"] = "annual_source_denominator_not_unique_people"
    annual["denominator_status"] = "guarded_source_position_25"
    annual["results_authorized"] = False
    return annual.sort_values(
        ["condition_id", "time_period", "geography_id"], kind="mergesort", ignore_index=True
    )


def _rank_quartile(values: pd.Series) -> pd.Series:
    ranks = values.astype(float)
    return pd.Series(
        _rank_quartile_array(ranks.to_numpy()),
        index=values.index,
        dtype="int64",
    )


def _rank_quartile_array(values: np.ndarray) -> np.ndarray:
    ranks = np.asarray(values, dtype=float)
    return np.select(
        [ranks <= 0.25, ranks <= 0.50, ranks <= 0.75],
        [1, 2, 3],
        default=4,
    ).astype(int)


def summarize_community_area_aggregation_loss(
    dataset: pd.DataFrame, tract_frame: pd.DataFrame
) -> pd.DataFrame:
    """Compare direct tract ranks with linked direct community-area ranks.

    The public function name is retained for artifact compatibility. The estimand is
    a direct cross-frame classification difference, not literal aggregation loss.
    """

    def metrics(tract_rank: object, community_rank: object) -> dict[str, float]:
        tract_values = np.asarray(tract_rank, dtype=float)
        community_values = np.asarray(community_rank, dtype=float)
        tract_quartile = _rank_quartile_array(tract_values)
        community_quartile = _rank_quartile_array(community_values)
        gap = np.abs(tract_values - community_values)
        return {
            "median_absolute_percentile_rank_gap": float(np.median(gap)),
            "mean_absolute_percentile_rank_gap": float(np.mean(gap)),
            "quartile_disagree_pct": float(100 * np.mean(tract_quartile != community_quartile)),
            "q4_movement_pct": float(
                100 * np.mean((tract_quartile == 4) != (community_quartile == 4))
            ),
        }

    required = {
        "condition_id",
        "geography_id",
        "community_area_id",
        "ehr_percent",
        "ehr_rank",
        "assignment_rule",
        "crossing_sensitivity",
    }
    missing = sorted(required - set(tract_frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"cross-frame tract comparison is missing columns: {missing}")
    community = build_direct_ehr_rank_frame(dataset, "chicago_community_area")
    community = community.rename(
        columns={"geography_id": "community_area_id", "ehr_percent": "community_ehr_percent"}
    )
    community["community_area_id"] = community["community_area_id"].astype(str).str.zfill(2)
    records: list[dict[str, object]] = []
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    for condition, tract_group in tract_frame.groupby("condition_id", sort=True):
        comparison = community.loc[community["condition_id"].eq(condition)].copy()
        if comparison.empty:
            continue
        comparison = comparison.rename(columns={"ehr_rank": "community_rank"})
        merged = tract_group.merge(
            comparison[["community_area_id", "community_ehr_percent", "community_rank"]],
            on="community_area_id",
            how="inner",
            validate="many_to_one",
        )
        if merged.empty:
            continue
        tract_rank = merged["ehr_rank"].astype(float)
        community_rank = merged["community_rank"].astype(float)
        tract_quartile = _rank_quartile(tract_rank)
        community_quartile = _rank_quartile(community_rank)
        point = metrics(tract_rank, community_rank)
        bootstrap: dict[str, list[float]] = {name: [] for name in point}
        area_ids = np.array(sorted(merged["community_area_id"].astype(str).unique()))
        area_lookup = {area: index for index, area in enumerate(area_ids)}
        row_area = np.array(
            [area_lookup[area] for area in merged["community_area_id"].astype(str)], dtype=int
        )
        tract_values = merged["ehr_percent"].to_numpy(dtype=float)
        area_values = np.array(
            [
                merged.loc[
                    merged["community_area_id"].astype(str).eq(area), "community_ehr_percent"
                ].iloc[0]
                for area in area_ids
            ],
            dtype=float,
        )
        for _ in range(BOOTSTRAP_REPLICATES):
            sampled = rng.integers(0, len(area_ids), size=len(area_ids))
            multiplicity = np.bincount(sampled, minlength=len(area_ids))
            row_index = np.repeat(np.arange(len(merged)), multiplicity[row_area])
            sampled_area_index = np.repeat(np.arange(len(area_ids)), multiplicity)
            replicate_tract_rank = stats.rankdata(
                tract_values[row_index], method="average"
            ) / len(row_index)
            sampled_area_rank = stats.rankdata(
                area_values[sampled_area_index], method="average"
            ) / len(sampled_area_index)
            rank_by_area = np.empty(len(area_ids), dtype=float)
            rank_by_area[sampled_area_index] = sampled_area_rank
            replicate_metrics = metrics(
                replicate_tract_rank, rank_by_area[row_area[row_index]]
            )
            for name, value in replicate_metrics.items():
                bootstrap[name].append(value)
        spearman = (
            stats.spearmanr(merged["ehr_percent"], merged["community_ehr_percent"])
            if len(merged) >= 3
            and merged["ehr_percent"].nunique() > 1
            and merged["community_ehr_percent"].nunique() > 1
            else None
        )
        exact_agreement = tract_quartile.eq(community_quartile)
        records.append(
            {
                "condition_id": str(condition),
                "comparison_geography_type": "chicago_community_area",
                "comparison_geography_label": "dominant_direct_community_area",
                "tract_sample_n": int(len(merged)),
                "comparison_geography_n": int(merged["community_area_id"].nunique()),
                "spearman_tract_value_vs_comparison_value": (
                    float(spearman.statistic) if spearman is not None else np.nan
                ),
                "median_absolute_percentile_rank_gap": point[
                    "median_absolute_percentile_rank_gap"
                ],
                "median_absolute_percentile_rank_gap_ci_low": float(
                    np.quantile(bootstrap["median_absolute_percentile_rank_gap"], 0.025)
                ),
                "median_absolute_percentile_rank_gap_ci_high": float(
                    np.quantile(bootstrap["median_absolute_percentile_rank_gap"], 0.975)
                ),
                "mean_absolute_percentile_rank_gap": point["mean_absolute_percentile_rank_gap"],
                "exact_quartile_agreement_count": int(exact_agreement.sum()),
                "exact_quartile_agreement_pct": float(100 * exact_agreement.mean()),
                "quartile_disagree_count": int((tract_quartile != community_quartile).sum()),
                "quartile_disagree_pct": point["quartile_disagree_pct"],
                "quartile_disagree_pct_ci_low": float(
                    np.quantile(bootstrap["quartile_disagree_pct"], 0.025)
                ),
                "quartile_disagree_pct_ci_high": float(
                    np.quantile(bootstrap["quartile_disagree_pct"], 0.975)
                ),
                "q4_movement_pct": point["q4_movement_pct"],
                "q4_movement_pct_ci_low": float(
                    np.quantile(bootstrap["q4_movement_pct"], 0.025)
                ),
                "q4_movement_pct_ci_high": float(
                    np.quantile(bootstrap["q4_movement_pct"], 0.975)
                ),
                "opposite_extreme_count": int(
                    (
                        ((tract_quartile == 4) & (community_quartile == 1))
                        | ((tract_quartile == 1) & (community_quartile == 4))
                    ).sum()
                ),
                "opposite_extreme_pct": float(
                    100
                    * (
                        ((tract_quartile == 4) & (community_quartile == 1))
                        | ((tract_quartile == 1) & (community_quartile == 4))
                    ).mean()
                ),
                "tract_high_comparison_not_high_count": int(
                    ((tract_quartile == 4) & (community_quartile < 4)).sum()
                ),
                "tract_low_comparison_not_low_count": int(
                    ((tract_quartile == 1) & (community_quartile > 1)).sum()
                ),
                "assignment_rule": str(merged["assignment_rule"].iloc[0]),
                "crossing_sensitivity": str(merged["crossing_sensitivity"].iloc[0]),
                "analysis_status": "geographic_resolution_sensitivity",
                "interpretation_label": "tract_resolution_not_area_prevalence",
                "comparability_gate_status": "cross_frame_only_no_literal_aggregation",
                "comparability_gate_reason": (
                    "Direct tract and direct community-area CHM values are compared as linked "
                    "cross-frame classifications; tract disease values are not aggregated."
                ),
                "bootstrap_requested_replicates": BOOTSTRAP_REPLICATES,
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "bootstrap_cluster_unit": "community_area_id",
                "bootstrap_rank_rule": "recomputed_within_each_cluster_resample",
                "bootstrap_interval_method": "percentile_2.5_97.5",
                "zip_zcta_sensitivity_status": "not_run_no_tract_zcta_crosswalk",
                "results_authorized": False,
            }
        )
    output = pd.DataFrame.from_records(records)
    output["results_authorized"] = pd.Series(False, index=output.index, dtype=object)
    return output


_TRANSITION_STATES = (
    "remains_high",
    "moves_out_of_highest_quartile",
    "moves_into_highest_quartile",
    "remains_below_highest_quartile",
)


def build_geographic_consequence_tables(
    tract_frame: pd.DataFrame,
    coarser_frame: pd.DataFrame,
    linkage: pd.DataFrame,
    *,
    comparison_geography_type: str,
    noncrossing_only: bool = False,
) -> dict[str, pd.DataFrame]:
    """Reconcile direct tract and direct coarser ranks without aggregating disease values."""

    tract_required = {
        "geography_id",
        "condition_id",
        "ehr_rank",
        "mean_annual_source_denominator",
    }
    coarse_required = {"geography_id", "condition_id", "ehr_rank"}
    link_required = {"geography_id", "comparison_geography_id", "is_crossing_tract"}
    for name, frame, required in (
        ("tract", tract_frame, tract_required),
        ("coarser", coarser_frame, coarse_required),
        ("linkage", linkage, link_required),
    ):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise CaseStudyAnalysisError(f"{name} consequence frame is missing columns: {missing}")
    links = linkage.copy()
    if "is_dominant" in links:
        links = links.loc[links["is_dominant"].astype(bool)].copy()
    if links["geography_id"].duplicated().any():
        raise CaseStudyAnalysisError("consequence linkage requires one dominant row per tract")
    if noncrossing_only:
        links = links.loc[~links["is_crossing_tract"].astype(bool)].copy()
    tract = tract_frame.merge(links, on="geography_id", how="inner", validate="many_to_one")
    if "ehr_percent" in tract:
        rank_groups = ["condition_id"] + (["time_period"] if "time_period" in tract else [])
        tract["ehr_rank"] = tract.groupby(rank_groups, sort=False)["ehr_percent"].rank(
            method="average", pct=True
        )
    coarse = coarser_frame.rename(
        columns={"geography_id": "comparison_geography_id", "ehr_rank": "comparison_rank"}
    )
    merge_keys = ["comparison_geography_id", "condition_id"]
    if "time_period" in tract and "time_period" in coarse:
        merge_keys.append("time_period")
    elif ("time_period" in tract) != ("time_period" in coarse):
        raise CaseStudyAnalysisError("tract and coarser consequence periods must align")
    detail = tract.merge(
        coarse[merge_keys + ["comparison_rank"]],
        on=merge_keys,
        how="inner",
        validate="many_to_one",
    )
    if detail.empty:
        raise CaseStudyAnalysisError("no direct tract/coarser consequence pairs are eligible")
    if detail.duplicated(["geography_id", "condition_id"] + merge_keys[2:]).any():
        raise CaseStudyAnalysisError("consequence comparison contains duplicate tract rows")
    detail["tract_quartile"] = _rank_quartile(detail["ehr_rank"])
    detail["comparison_quartile"] = _rank_quartile(detail["comparison_rank"])
    detail["tract_is_high"] = detail["tract_quartile"].eq(4)
    detail["comparison_is_high"] = detail["comparison_quartile"].eq(4)
    detail["transition_state"] = np.select(
        [
            detail["tract_is_high"] & detail["comparison_is_high"],
            detail["tract_is_high"] & ~detail["comparison_is_high"],
            ~detail["tract_is_high"] & detail["comparison_is_high"],
        ],
        list(_TRANSITION_STATES[:3]),
        default=_TRANSITION_STATES[3],
    )
    detail["comparison_geography_type"] = comparison_geography_type
    detail["sensitivity_status"] = "noncrossing_only" if noncrossing_only else "all_eligible"
    detail["denominator_unit"] = "mean_annual_source_denominator_not_unique_people"
    detail["clinical_value_rule"] = "direct_tract_and_direct_coarser_values_only"
    detail["results_authorized"] = False

    grouping = ["condition_id"] + (["time_period"] if "time_period" in detail else [])
    grouped = detail.groupby(grouping + ["transition_state"], sort=True, as_index=False).agg(
        tract_count=("geography_id", "size"),
        mean_annual_source_denominator=("mean_annual_source_denominator", "sum"),
    )
    bases = detail[grouping].drop_duplicates().assign(_join=1)
    states = pd.DataFrame({"transition_state": _TRANSITION_STATES, "_join": 1})
    transitions = bases.merge(states, on="_join").drop(columns="_join")
    transitions = transitions.merge(
        grouped, on=grouping + ["transition_state"], how="left", validate="one_to_one"
    )
    transitions[["tract_count", "mean_annual_source_denominator"]] = transitions[
        ["tract_count", "mean_annual_source_denominator"]
    ].fillna(0)
    transitions["comparison_geography_type"] = comparison_geography_type
    transitions["sensitivity_status"] = detail["sensitivity_status"].iloc[0]
    transitions["results_authorized"] = False

    mixed_records: list[dict[str, object]] = []
    mixed_grouping = grouping + ["comparison_geography_id"]
    for keys, group in detail.groupby(mixed_grouping, sort=True):
        key_values = keys if isinstance(keys, tuple) else (keys,)
        if not (group["tract_quartile"].eq(1).any() and group["tract_quartile"].eq(4).any()):
            continue
        record = dict(zip(mixed_grouping, key_values, strict=True))
        record.update(
            {
                "eligible_tract_count": int(len(group)),
                "mean_annual_source_denominator": float(
                    group["mean_annual_source_denominator"].sum()
                ),
                "comparison_rank": float(group["comparison_rank"].iloc[0]),
                "crossing_tract_count": int(group["is_crossing_tract"].astype(bool).sum()),
                "comparison_geography_type": comparison_geography_type,
                "sensitivity_status": detail["sensitivity_status"].iloc[0],
                "results_authorized": False,
            }
        )
        mixed_records.append(record)
    mixed = pd.DataFrame.from_records(mixed_records)
    if not mixed.empty:
        mixed["results_authorized"] = False
    return {
        "details": detail.sort_values(grouping + ["geography_id"]).reset_index(drop=True),
        "transitions": transitions.sort_values(grouping + ["transition_state"]).reset_index(
            drop=True
        ),
        "mixed_extremes": mixed,
    }


def summarize_annual_consequence_stability(
    detail: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Summarize annual Q4 overlap and signed transition persistence."""

    required = {
        "geography_id",
        "condition_id",
        "time_period",
        "transition_state",
        "tract_is_high",
        "comparison_is_high",
    }
    missing = sorted(required - set(detail.columns))
    if missing:
        raise CaseStudyAnalysisError(f"annual consequence detail is missing columns: {missing}")
    annual_records: list[dict[str, object]] = []
    for (condition, period), group in detail.groupby(["condition_id", "time_period"], sort=True):
        tract_high = set(group.loc[group["tract_is_high"].astype(bool), "geography_id"])
        comparison_high = set(group.loc[group["comparison_is_high"].astype(bool), "geography_id"])
        union = tract_high | comparison_high
        annual_records.append(
            {
                "condition_id": str(condition),
                "time_period": str(period),
                "eligible_tract_count": int(len(group)),
                "top_quartile_jaccard": (
                    float(len(tract_high & comparison_high) / len(union)) if union else 1.0
                ),
                "results_authorized": False,
            }
        )
    persistence_records: list[dict[str, object]] = []
    for (condition, tract), group in detail.groupby(["condition_id", "geography_id"], sort=True):
        counts = group["transition_state"].astype(str).value_counts()
        state = str(counts.index[0]) if int(counts.iloc[0]) >= 2 else "unstable"
        persistence_records.append(
            {
                "condition_id": str(condition),
                "geography_id": str(tract),
                "eligible_year_count": int(group["time_period"].nunique()),
                "persistent_transition_state": state,
                "meets_two_of_three_rule": state != "unstable",
                "results_authorized": False,
            }
        )
    return {
        "annual_jaccard": pd.DataFrame.from_records(annual_records),
        "tract_persistence": pd.DataFrame.from_records(persistence_records),
    }


def cluster_bootstrap_concordance(
    frame: pd.DataFrame,
    *,
    n_replicates: int = 1000,
    seed: int = BOOTSTRAP_SEED,
) -> pd.DataFrame:
    """Bootstrap agreement metrics by resampling community areas, not tracts."""

    if n_replicates < 1:
        raise CaseStudyAnalysisError("bootstrap replicate count must be positive")
    if "community_area_id" not in frame:
        raise CaseStudyAnalysisError("bootstrap requires community_area_id")
    rng = np.random.default_rng(seed)
    records: list[dict[str, object]] = []
    for condition, original in frame.groupby("condition_id", sort=True):
        areas = np.array(sorted(original["community_area_id"].astype(str).unique()))
        if len(areas) == 0:
            continue
        estimates: dict[str, list[object]] = {
            "spearman_r": [],
            "median_absolute_percentile_rank_gap": [],
            "quadratic_weighted_kappa": [],
            "gwet_ac1": [],
        }
        sampled_denominators: list[int] = []
        for _ in range(n_replicates):
            sampled = rng.choice(areas, size=len(areas), replace=True)
            replicate = pd.concat(
                [
                    original.loc[original["community_area_id"].astype(str).eq(area)]
                    for area in sampled
                ],
                ignore_index=True,
            )
            sampled_denominators.append(int(len(replicate)))
            metric = _metric_record(_rerank_concordance(replicate))
            for key in estimates:
                estimates[key].append(metric[key])
        point = _metric_record(original)
        for metric_name, values in estimates.items():
            numeric = np.asarray(values, dtype=float)
            if np.isfinite(numeric).any():
                ci_low = float(np.nanpercentile(numeric, 2.5))
                ci_high = float(np.nanpercentile(numeric, 97.5))
            else:
                ci_low = ci_high = np.nan
            records.append(
                {
                    "condition_id": str(condition),
                    "metric": metric_name,
                    "estimate": point[metric_name],
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "sample_n": int(len(original)),
                    "bootstrap_mean_sample_n": float(np.mean(sampled_denominators)),
                    "replicate_count": int(n_replicates),
                    "seed": int(seed),
                    "cluster_unit": "community_area_id",
                    "bootstrap_interval_method": "percentile_2.5_97.5",
                    "bootstrap_rank_rule": "recomputed_within_each_cluster_resample",
                    "uncertainty": "95% community-area cluster bootstrap interval",
                    "dependence_note": "addresses within-area dependence; not a complete correction for spatial dependence",
                    "analysis_status": "descriptive_cluster_bootstrap",
                    "interpretation_label": "measurement_discordance_only_neutral",
                    "results_authorized": False,
                }
            )
    output = pd.DataFrame.from_records(records)
    output["results_authorized"] = pd.Series(False, index=output.index, dtype=object)
    return output.sort_values(["condition_id", "metric"], kind="mergesort").reset_index(drop=True)
