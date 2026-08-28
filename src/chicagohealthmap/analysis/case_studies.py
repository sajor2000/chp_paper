"""Deterministic analytic views for the Chicago case-study notebook."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from scipy import stats  # type: ignore[import-untyped]

PRIMARY_KEY = ["geography_type", "geography_id", "time_period", "condition_id"]
COMMUNITY = "chicago_community_area"
TRACT = "census_tract"
CONTEMPORARY_YEARS = ("2022", "2023", "2024")
DIABETES_COMPONENTS = {
    "diabetes_with_complication",
    "diabetes_without_complication",
}
CONDITION_PRIORITY = {"hypertension": 1, "diabetes": 2, "copd": 3}
MINIMUM_TRACT_ANNUAL_DENOMINATOR = 30


class CaseStudyAnalysisError(ValueError):
    """Raised when a frozen analytic dataset cannot support the notebook."""


def load_analytic_dataset(path: Path) -> pd.DataFrame:
    """Load and validate the frozen analytic dataset."""

    dataset = pd.read_parquet(path)
    validate_analytic_dataset(dataset)
    return dataset


def validate_analytic_dataset(dataset: pd.DataFrame) -> None:
    """Validate the minimal contract needed by the notebook."""

    required = {
        *PRIMARY_KEY,
        "geography_name",
        "condition_family",
        "case_id",
        "numerator",
        "denominator",
        "published_measure_value",
        "published_measure_unit",
        "life_expectancy_estimate",
        "public_comparator_estimate",
        "public_comparator_role",
        "suppression_flag",
        "capture_rate",
        "reliability_flag",
        "source_position_contract",
    }
    missing = sorted(required - set(dataset.columns))
    if missing:
        raise CaseStudyAnalysisError(f"analytic dataset is missing columns: {missing}")
    duplicate_count = int(dataset.duplicated(PRIMARY_KEY).sum())
    if duplicate_count:
        raise CaseStudyAnalysisError(f"analytic dataset has {duplicate_count} duplicate keys")
    diabetes_rows = dataset.loc[dataset["condition_family"] == "diabetes"]
    if diabetes_rows["condition_id"].isna().any():
        raise CaseStudyAnalysisError("analytic dataset has null diabetes condition IDs")
    diabetes_conditions = set(diabetes_rows["condition_id"].astype(str).unique())
    unexpected_diabetes = diabetes_conditions - DIABETES_COMPONENTS
    if unexpected_diabetes:
        raise CaseStudyAnalysisError(
            f"analytic dataset has unexpected diabetes components: {sorted(unexpected_diabetes)}"
        )


def summarize_dataset_shape(dataset: pd.DataFrame) -> pd.DataFrame:
    """Summarize row counts for notebook audit display."""

    return (
        dataset.groupby(["geography_type", "condition_id"], dropna=False)
        .agg(
            rows=("condition_id", "size"),
            geographies=("geography_id", "nunique"),
            years=("time_period", "nunique"),
            suppressed_rows=("suppression_flag", "sum"),
        )
        .reset_index()
        .sort_values(["geography_type", "condition_id"], kind="mergesort")
    )


def build_tract_cohort_flow(dataset: pd.DataFrame) -> pd.DataFrame:
    """Count the prespecified tract-year-condition eligibility cascade.

    The output keeps suppression and small-denominator exclusions distinct so a
    reviewer can reconstruct the analytic cohort without inspecting row-level
    records. Counts are aggregate quality-control results.
    """

    required = {
        "geography_type",
        "geography_id",
        "time_period",
        "condition_id",
        "numerator",
        "denominator",
        "suppression_flag",
        "primary_tract_annual_eligible",
    }
    missing = sorted(required - set(dataset.columns))
    if missing:
        raise CaseStudyAnalysisError(f"tract cohort flow is missing columns: {missing}")
    tract = dataset.loc[dataset["geography_type"].eq(TRACT)].copy()
    tract["denominator_numeric"] = pd.to_numeric(tract["denominator"], errors="coerce")
    tract["denominator_eligible"] = tract["denominator_numeric"].ge(
        MINIMUM_TRACT_ANNUAL_DENOMINATOR
    )
    tract["observable_after_suppression"] = (
        tract["denominator_eligible"]
        & ~tract["suppression_flag"].astype(bool)
        & tract["numerator"].notna()
    )
    calculated = tract["observable_after_suppression"] & tract["denominator_numeric"].notna()
    recorded = tract["primary_tract_annual_eligible"].astype(bool)
    if not calculated.equals(recorded):
        mismatch = int((calculated != recorded).sum())
        raise CaseStudyAnalysisError(
            f"stored tract eligibility disagrees with the cohort rule for {mismatch} rows"
        )

    records: list[dict[str, object]] = []
    for (condition_id, time_period), group in tract.groupby(
        ["condition_id", "time_period"], sort=True, dropna=False
    ):
        denominator_eligible = group["denominator_eligible"].astype(bool)
        observable = group["observable_after_suppression"].astype(bool)
        eligible = group["primary_tract_annual_eligible"].astype(bool)
        records.append(
            {
                "condition_id": condition_id,
                "time_period": str(time_period),
                "boundary_eligible_rows": int(len(group)),
                "boundary_eligible_tracts": int(group["geography_id"].nunique()),
                "denominator_ge_30_rows": int(denominator_eligible.sum()),
                "denominator_ge_30_tracts": int(
                    group.loc[denominator_eligible, "geography_id"].nunique()
                ),
                "observable_after_suppression_rows": int(observable.sum()),
                "observable_after_suppression_tracts": int(
                    group.loc[observable, "geography_id"].nunique()
                ),
                "primary_eligible_rows": int(eligible.sum()),
                "primary_eligible_tracts": int(
                    group.loc[eligible, "geography_id"].nunique()
                ),
                "excluded_denominator_lt_30_or_missing_rows": int(
                    (~denominator_eligible).sum()
                ),
                "excluded_suppressed_or_missing_numerator_rows": int(
                    (denominator_eligible & ~observable).sum()
                ),
            }
        )
    return pd.DataFrame.from_records(records).sort_values(
        ["condition_id", "time_period"], kind="mergesort", ignore_index=True
    )


def _condition_summary(rows: pd.DataFrame, output_prefix: str) -> pd.DataFrame:
    rows = rows.copy()
    rows["annual_eligible"] = (
        rows["suppression_flag"].eq(False) & rows["numerator"].notna() & rows["denominator"].notna()
    )
    rows["eligible_numerator"] = rows["numerator"].where(rows["annual_eligible"])
    rows["eligible_denominator"] = rows["denominator"].where(rows["annual_eligible"])
    grouped = rows.groupby(["geography_id", "geography_name"], dropna=False)
    summary = grouped.agg(
        **{
            f"{output_prefix}_numerator_sum": ("eligible_numerator", "sum"),
            f"{output_prefix}_denominator_sum": ("eligible_denominator", "sum"),
            f"{output_prefix}_annual_rows": ("time_period", "nunique"),
            f"{output_prefix}_eligible_annual_rows": ("annual_eligible", "sum"),
            f"{output_prefix}_suppressed_rows": ("suppression_flag", "sum"),
        }
    )
    summary[f"{output_prefix}_ineligible_annual_rows"] = (
        summary[f"{output_prefix}_annual_rows"] - summary[f"{output_prefix}_eligible_annual_rows"]
    )
    summary[f"{output_prefix}_ehr_percent_2022_2024"] = (
        100
        * summary[f"{output_prefix}_numerator_sum"]
        / summary[f"{output_prefix}_denominator_sum"]
    )
    summary[f"{output_prefix}_exposure_complete"] = summary[
        f"{output_prefix}_eligible_annual_rows"
    ].eq(len(CONTEMPORARY_YEARS))
    return summary


def combined_diabetes_is_approved(group: pd.DataFrame) -> bool:
    """Return true only for an explicitly approved, denominator-equivalent annual pair."""

    required = {
        "condition_id",
        "numerator",
        "denominator",
        "published_measure_value",
        "suppression_flag",
        "combined_diabetes_semantics_approved",
    }
    if not required.issubset(group.columns):
        return False
    if set(group["condition_id"].astype(str)) != DIABETES_COMPONENTS:
        return False
    if group["condition_id"].duplicated().any():
        return False
    numerator = pd.to_numeric(group["numerator"], errors="coerce")
    denominator = pd.to_numeric(group["denominator"], errors="coerce")
    if (
        group["suppression_flag"].astype(bool).any()
        or numerator.isna().any()
        or denominator.isna().any()
        or group["published_measure_value"].isna().any()
        or denominator.nunique() != 1
        or denominator.iloc[0] <= 0
        or numerator.sum() > denominator.iloc[0]
    ):
        return False
    return bool(group["combined_diabetes_semantics_approved"].astype(bool).all())


def _diabetes_summary(rows: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["geography_id", "geography_name", "time_period"]
    annual_records: list[dict[str, object]] = []
    for keys, group in rows.groupby(group_cols, dropna=False, sort=True):
        approved = combined_diabetes_is_approved(group)
        annual_records.append(
            {
                **dict(zip(group_cols, keys, strict=True)),
                "numerator": (
                    float(pd.to_numeric(group["numerator"], errors="coerce").sum())
                    if approved
                    else np.nan
                ),
                "denominator": (
                    float(pd.to_numeric(group["denominator"], errors="coerce").iloc[0])
                    if approved
                    else np.nan
                ),
                "component_rows": int(len(group)),
                "suppressed_rows": int(group["suppression_flag"].astype(bool).sum()),
                "annual_eligible": approved,
            }
        )
    annual = pd.DataFrame.from_records(annual_records)
    areas = rows[["geography_id", "geography_name"]].drop_duplicates()
    expected = areas.merge(pd.DataFrame({"time_period": CONTEMPORARY_YEARS}), how="cross")
    annual = expected.merge(annual, on=group_cols, how="left")
    annual["annual_eligible"] = annual["annual_eligible"].fillna(False).astype(bool)
    annual["eligible_numerator"] = annual["numerator"].where(annual["annual_eligible"])
    annual["eligible_denominator"] = annual["denominator"].where(annual["annual_eligible"])
    output = annual.groupby(["geography_id", "geography_name"], dropna=False).agg(
        diabetes_numerator_sum=("eligible_numerator", lambda values: values.sum(min_count=1)),
        diabetes_denominator_sum=("eligible_denominator", lambda values: values.sum(min_count=1)),
        diabetes_component_rows=("component_rows", "sum"),
        diabetes_suppressed_rows=("suppressed_rows", "sum"),
        diabetes_eligible_annual_rows=("annual_eligible", "sum"),
    )
    output["diabetes_ineligible_annual_rows"] = (
        len(CONTEMPORARY_YEARS) - output["diabetes_eligible_annual_rows"]
    )
    output["diabetes_ehr_percent_2022_2024"] = (
        100 * output["diabetes_numerator_sum"] / output["diabetes_denominator_sum"]
    )
    output["diabetes_exposure_complete"] = output["diabetes_eligible_annual_rows"].eq(
        len(CONTEMPORARY_YEARS)
    )
    return output


def _published_proportions_as_percentage_points(rows: pd.DataFrame) -> pd.Series:
    if rows.empty:
        return pd.Series(index=rows.index, dtype=float)
    units = set(rows["published_measure_unit"].dropna().astype(str).unique())
    if rows["published_measure_unit"].isna().any() or units != {"source_percent_or_rate"}:
        raise CaseStudyAnalysisError(
            f"tract concordance has unsupported published measure units: {sorted(units)}"
        )
    return 100 * rows["published_measure_value"]


def build_primary_community_frame(dataset: pd.DataFrame) -> pd.DataFrame:
    """Build one-row-per-community-area contemporary model frame."""

    validate_analytic_dataset(dataset)
    community = dataset[
        (dataset["geography_type"] == COMMUNITY)
        & (dataset["time_period"].astype(str).isin(CONTEMPORARY_YEARS))
    ].copy()
    annual_contract = community.groupby(["geography_id", "time_period"], dropna=False).agg(
        capture_values=("capture_rate", "nunique"),
        acs_values=("acs_adult_population", "nunique"),
    )
    if bool((annual_contract[["capture_values", "acs_values"]] > 1).any().any()):
        raise CaseStudyAnalysisError("community capture or ACS denominator disagrees within year")
    outcome_years = community.drop_duplicates(["geography_id", "time_period"]).copy()
    outcome_years["capture_numerator"] = (
        pd.to_numeric(outcome_years["capture_rate"], errors="coerce")
        * pd.to_numeric(outcome_years["acs_adult_population"], errors="coerce")
    )
    outcome = outcome_years.groupby(["geography_id", "geography_name"], dropna=False).agg(
        life_expectancy_mean_2022_2024=("life_expectancy_estimate", "mean"),
        life_expectancy_years_complete=("life_expectancy_estimate", "count"),
        capture_numerator_sum_2022_2024=("capture_numerator", "sum"),
        capture_acs_denominator_sum_2022_2024=("acs_adult_population", "sum"),
    )
    outcome["capture_rate_mean_2022_2024"] = (
        outcome["capture_numerator_sum_2022_2024"]
        / outcome["capture_acs_denominator_sum_2022_2024"]
    )
    covariate_columns = [
        "pct_age_65_plus",
        "pct_female",
        "pct_below_fpl",
        "acs_adult_population",
    ]
    missing_covariates = sorted(set(covariate_columns) - set(community.columns))
    if missing_covariates:
        raise CaseStudyAnalysisError(
            f"community frame is missing frozen covariates: {missing_covariates}"
        )
    covariates = community[["geography_id", "geography_name", *covariate_columns]].copy()
    for column in covariate_columns:
        distinct = covariates.groupby(["geography_id", "geography_name"])[column].nunique(
            dropna=True
        )
        if bool((distinct > 1).any()):
            raise CaseStudyAnalysisError(
                f"community covariate {column} disagrees within a geography"
            )
        if covariates[column].isna().any():
            raise CaseStudyAnalysisError(f"community covariate {column} contains missing values")
    covariates = covariates.groupby(
        ["geography_id", "geography_name"], as_index=True, sort=True
    ).first()
    hypertension = _condition_summary(
        community[community["condition_id"] == "hypertension"], "hypertension"
    )
    diabetes = _diabetes_summary(community[community["condition_family"] == "diabetes"])
    copd = _condition_summary(community[community["condition_id"] == "copd"], "copd")
    frame = outcome.join([covariates, hypertension, diabetes, copd], how="left").reset_index()
    frame["primary_model_complete"] = (
        frame["life_expectancy_years_complete"].eq(len(CONTEMPORARY_YEARS))
        & frame["hypertension_exposure_complete"]
        & frame["diabetes_exposure_complete"]
        & frame["copd_exposure_complete"]
    )
    return frame.sort_values("geography_id", kind="mergesort")


def build_tract_concordance_frame(dataset: pd.DataFrame) -> pd.DataFrame:
    """Build a complete-period, denominator-pooled tract comparison frame."""

    validate_analytic_dataset(dataset)
    tract = dataset[
        (dataset["geography_type"] == TRACT)
        & (dataset["time_period"].astype(str).isin(CONTEMPORARY_YEARS))
        & dataset["public_comparator_estimate"].notna()
    ].copy()
    _published_proportions_as_percentage_points(tract)
    non_diabetes = tract[tract["condition_family"] != "diabetes"].copy()
    non_diabetes["annual_eligible"] = (
        non_diabetes["suppression_flag"].eq(False)
        & non_diabetes["numerator"].notna()
        & non_diabetes["denominator"].notna()
        & pd.to_numeric(non_diabetes["denominator"], errors="coerce").ge(
            MINIMUM_TRACT_ANNUAL_DENOMINATOR
        )
        & non_diabetes["published_measure_value"].notna()
    )
    non_diabetes["eligible_numerator"] = non_diabetes["numerator"].where(
        non_diabetes["annual_eligible"]
    )
    non_diabetes["eligible_denominator"] = non_diabetes["denominator"].where(
        non_diabetes["annual_eligible"]
    )
    non_diabetes["concordance_condition_id"] = non_diabetes["condition_id"]
    non_diabetes["concordance_source_label"] = non_diabetes["source_condition_label"]
    diabetes = tract[tract["condition_family"] == "diabetes"].copy()
    diabetes_annual = _combined_diabetes_tract_years(diabetes)
    annual = pd.concat([non_diabetes, diabetes_annual], ignore_index=True, sort=False)
    group_cols = ["geography_id", "concordance_condition_id", "concordance_source_label"]
    frame = (
        annual.groupby(group_cols, dropna=False)
        .agg(
            numerator_sum=("eligible_numerator", "sum"),
            denominator_sum=("eligible_denominator", "sum"),
            public_comparator_estimate=("public_comparator_estimate", "first"),
            public_comparator_measure_id=("public_comparator_measure_id", "first"),
            capture_rate_mean_2022_2024=("capture_rate", "mean"),
            suppressed_rows=("suppression_flag", "sum"),
            annual_rows=("time_period", "nunique"),
            eligible_annual_rows=("annual_eligible", "sum"),
        )
        .reset_index()
        .rename(
            columns={
                "concordance_condition_id": "condition_id",
                "concordance_source_label": "source_condition_label",
            }
        )
    )
    frame["ineligible_annual_rows"] = frame["annual_rows"] - frame["eligible_annual_rows"]
    frame = frame.loc[frame["eligible_annual_rows"].eq(len(CONTEMPORARY_YEARS))].copy()
    frame["ehr_percent_mean_2022_2024"] = (
        100 * frame["numerator_sum"] / frame["denominator_sum"]
    )
    frame["pooling_method"] = "sum_annual_numerators_divided_by_sum_annual_denominators"
    frame["signed_difference"] = (
        frame["ehr_percent_mean_2022_2024"] - frame["public_comparator_estimate"]
    )
    frame["absolute_difference"] = frame["signed_difference"].abs()
    return frame.sort_values(["condition_id", "geography_id"], kind="mergesort")


def _combined_diabetes_tract_years(diabetes: pd.DataFrame) -> pd.DataFrame:
    if diabetes.empty:
        return diabetes.assign(
            eligible_numerator=[], eligible_denominator=[], annual_eligible=[],
            concordance_condition_id=[], concordance_source_label=[]
        )
    diabetes = diabetes.copy()
    diabetes = diabetes.groupby(["geography_id", "time_period"], group_keys=False).filter(
        combined_diabetes_is_approved
    )
    if diabetes.empty:
        return diabetes.assign(
            eligible_numerator=pd.Series(dtype=float),
            eligible_denominator=pd.Series(dtype=float),
            annual_eligible=pd.Series(dtype=bool),
            concordance_condition_id=pd.Series(dtype=str),
            concordance_source_label=pd.Series(dtype=str),
        )
    group_cols = ["geography_id", "time_period"]
    combined = (
        diabetes.groupby(group_cols, dropna=False)
        .agg(
            numerator=("numerator", "sum"),
            denominator=("denominator", "first"),
            public_comparator_estimate=("public_comparator_estimate", "first"),
            public_comparator_measure_id=("public_comparator_measure_id", "first"),
            capture_rate=("capture_rate", "mean"),
            suppression_flag=("suppression_flag", "sum"),
        )
        .reset_index()
    )
    combined["annual_eligible"] = pd.to_numeric(combined["denominator"], errors="coerce").ge(
        MINIMUM_TRACT_ANNUAL_DENOMINATOR
    )
    combined["eligible_numerator"] = combined["numerator"].where(combined["annual_eligible"])
    combined["eligible_denominator"] = combined["denominator"].where(combined["annual_eligible"])
    combined["concordance_condition_id"] = "diabetes"
    combined["concordance_source_label"] = "diabetes_combined_components"
    return combined


def summarize_resource_quality(dataset: pd.DataFrame) -> pd.DataFrame:
    """Summarize resource quality by geography type and condition."""

    required = {
        "geography_type",
        "condition_id",
        "geography_id",
        "time_period",
        "numerator",
        "denominator",
        "published_measure_value",
        "published_measure_unit",
        "capture_rate",
        "suppression_flag",
        "reliability_flag",
        "source_id",
        "snapshot_id",
        "source_position_contract",
        "disease_value_derivation",
    }
    _require_columns(dataset, required, "resource quality dataset")
    units = set(dataset["published_measure_unit"].dropna().astype(str).unique())
    if dataset["published_measure_unit"].isna().any() or units != {"source_percent_or_rate"}:
        raise CaseStudyAnalysisError(
            f"resource quality has unsupported measure units: {sorted(units)}"
        )

    working = dataset.copy()
    for column in ["numerator", "denominator", "published_measure_value", "capture_rate"]:
        working[column] = _validated_numeric(working[column], column, "resource quality")
    valid_suppression = working["suppression_flag"].map(
        lambda value: isinstance(value, (bool, np.bool_))
    )
    if not bool(valid_suppression.all()):
        raise CaseStudyAnalysisError("suppression_flag must contain booleans")
    for column in [
        "source_id",
        "snapshot_id",
        "source_position_contract",
        "disease_value_derivation",
    ]:
        if working[column].isna().any():
            raise CaseStudyAnalysisError(
                f"resource quality has missing provenance column: {column}"
            )

    working["disease_measure_percentage_points"] = 100 * working["published_measure_value"]
    working["missing_state"] = working[["numerator", "denominator"]].isna().any(axis=1)
    working["disease_value_missing"] = working["published_measure_value"].isna()
    working["disease_measure_eligible"] = (
        ~working["suppression_flag"] & ~working["disease_value_missing"]
    )
    if "primary_tract_annual_eligible" in working.columns:
        tract_rows = working["geography_type"].eq(TRACT)
        working.loc[tract_rows, "disease_measure_eligible"] = working.loc[
            tract_rows, "primary_tract_annual_eligible"
        ].astype(bool)
    working["reliability_available"] = working["reliability_flag"].eq("reliability_available")

    records: list[dict[str, object]] = []
    group_columns = ["geography_type", "condition_id"]
    for keys, group in working.groupby(group_columns, dropna=False, sort=True, observed=False):
        rows = int(len(group))
        denominator = group["denominator"]
        measure = group["disease_measure_percentage_points"].where(
            group["disease_measure_eligible"]
        )
        capture = group["capture_rate"]
        capture_missing_rows = int(capture.isna().sum())
        missing_rows = int(group["missing_state"].sum())
        suppressed_rows = int(group["suppression_flag"].sum())
        disease_missing_rows = int(group["disease_value_missing"].sum())
        disease_eligible_rows = int(group["disease_measure_eligible"].sum())
        reliability_available_rows = int(group["reliability_available"].sum())
        direct_first_party_rows = int(
            group["disease_value_derivation"].eq("direct_first_party_export_not_interpolated").sum()
        )
        records.append(
            {
                "geography_type": keys[0],
                "condition_id": keys[1],
                "rows": rows,
                "geographies": int(group["geography_id"].nunique(dropna=True)),
                "years": int(group["time_period"].nunique(dropna=True)),
                "denominator_median": float(denominator.median()),
                "denominator_iqr": _iqr(denominator),
                "disease_measure_median_percentage_points": float(measure.median()),
                "disease_measure_iqr_percentage_points": _iqr(measure),
                "disease_measure_eligible_rows": disease_eligible_rows,
                "capture_median": float(capture.median()),
                "capture_iqr": _iqr(capture),
                "capture_missing_rows": capture_missing_rows,
                "capture_missing_percentage": _percentage(capture_missing_rows, rows),
                "missing_rows": missing_rows,
                "missing_percentage": _percentage(missing_rows, rows),
                "suppressed_rows": suppressed_rows,
                "suppression_percentage": _percentage(suppressed_rows, rows),
                "disease_value_missing_rows": disease_missing_rows,
                "disease_value_missing_percentage": _percentage(disease_missing_rows, rows),
                "reliability_available_rows": reliability_available_rows,
                "reliability_available_percentage": _percentage(reliability_available_rows, rows),
                "reliability_qualification_status": "withheld_pending_reliability_rule",
                "reliability_qualified_rows": pd.NA,
                "reliability_qualified_percentage": pd.NA,
                "percentage_denominator_rows": rows,
                "missing_percentage_denominator_rows": rows,
                "suppression_percentage_denominator_rows": rows,
                "disease_value_missing_percentage_denominator_rows": rows,
                "reliability_available_percentage_denominator_rows": rows,
                "reliability_qualified_percentage_denominator_rows": pd.NA,
                "source_ids": _sorted_ids(group["source_id"]),
                "snapshot_ids": _sorted_ids(group["snapshot_id"]),
                "source_position_contracts": _sorted_ids(group["source_position_contract"]),
                "disease_value_derivations": _sorted_ids(group["disease_value_derivation"]),
                "direct_first_party_rows": direct_first_party_rows,
                "direct_first_party_percentage": _percentage(direct_first_party_rows, rows),
            }
        )
    return pd.DataFrame.from_records(records).sort_values(group_columns, kind="mergesort")


def classify_discordance(
    frame: pd.DataFrame, bins: Literal["quartile", "tertile"] = "quartile"
) -> pd.DataFrame:
    """Classify pairwise-complete geography pairs using common-set cut points."""

    if bins not in {"quartile", "tertile"}:
        raise CaseStudyAnalysisError(f"unsupported discordance bins: {bins}")
    required = {"condition_id", "ehr_percent_mean_2022_2024", "public_comparator_estimate"}
    _require_columns(frame, required, "concordance frame")
    if frame.empty:
        raise CaseStudyAnalysisError("concordance frame has no rows")
    frame = frame.copy()
    for column in ["ehr_percent_mean_2022_2024", "public_comparator_estimate"]:
        frame[column] = _validated_numeric(frame[column], column, "concordance frame")

    quantiles = (0.25, 0.5, 0.75) if bins == "quartile" else (1 / 3, 0.5, 2 / 3)
    classified_groups: list[pd.DataFrame] = []
    for condition_id, original in frame.groupby("condition_id", sort=True, dropna=False):
        group = original.dropna(
            subset=["ehr_percent_mean_2022_2024", "public_comparator_estimate"]
        ).copy()
        if group.empty:
            raise CaseStudyAnalysisError(
                f"condition {condition_id!s} has no pairwise-complete common set"
            )
        ehr_cuts = _cut_points(group["ehr_percent_mean_2022_2024"], quantiles, condition_id)
        public_cuts = _cut_points(group["public_comparator_estimate"], quantiles, condition_id)
        ehr_low, ehr_mid, ehr_high = ehr_cuts
        public_low, public_mid, public_high = public_cuts

        ehr = group["ehr_percent_mean_2022_2024"].astype(float)
        public = group["public_comparator_estimate"].astype(float)
        conditions = [
            ehr.ge(ehr_high) & public.ge(public_high),
            ehr.le(ehr_low) & public.le(public_low),
            ehr.ge(ehr_high) & public.lt(public_mid),
            public.ge(public_high) & ehr.lt(ehr_mid),
        ]
        labels = [
            "concordant_high",
            "concordant_low",
            "ehr_high_public_not_high",
            "public_high_ehr_not_high",
        ]
        group["discordance_category"] = np.select(conditions, labels, default="intermediate")
        group["discordance_bins"] = bins
        for prefix, cuts in [("ehr", ehr_cuts), ("public", public_cuts)]:
            group[f"{prefix}_low_cutpoint"] = cuts[0]
            group[f"{prefix}_mid_cutpoint"] = cuts[1]
            group[f"{prefix}_high_cutpoint"] = cuts[2]
        classified_groups.append(group)
    return pd.concat(classified_groups).sort_index(kind="mergesort")


def summarize_concordance(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize EHR/public concordance without designating either measure as truth."""

    required = {"condition_id", "ehr_percent_mean_2022_2024", "public_comparator_estimate"}
    _require_columns(frame, required, "concordance frame")
    if frame.empty:
        raise CaseStudyAnalysisError("concordance frame has no rows")
    frame = frame.copy()
    for column in ["ehr_percent_mean_2022_2024", "public_comparator_estimate"]:
        frame[column] = _validated_numeric(frame[column], column, "concordance frame")
    records: list[dict[str, object]] = []
    category_names = [
        "concordant_high",
        "concordant_low",
        "ehr_high_public_not_high",
        "public_high_ehr_not_high",
        "intermediate",
    ]
    for condition_id, original in frame.groupby("condition_id", sort=True, dropna=False):
        group = original.dropna(
            subset=["ehr_percent_mean_2022_2024", "public_comparator_estimate"]
        ).copy()
        x = group["ehr_percent_mean_2022_2024"].astype(float)
        y = group["public_comparator_estimate"].astype(float)
        spearman_r = spearman_p = pearson_r = pearson_p = None
        if len(group) >= 3 and x.nunique() > 1 and y.nunique() > 1:
            spearman = stats.spearmanr(x, y)
            pearson = stats.pearsonr(x, y)
            spearman_r, spearman_p = float(spearman.statistic), float(spearman.pvalue)
            pearson_r, pearson_p = float(pearson.statistic), float(pearson.pvalue)

        record: dict[str, object] = {
            "condition_id": str(condition_id),
            "condition_priority": CONDITION_PRIORITY.get(str(condition_id), 999),
            "rows": int(len(group)),
            "spearman_r": spearman_r,
            "spearman_p": spearman_p,
            "pearson_r": pearson_r,
            "pearson_p": pearson_p,
            "median_signed_difference": float((x - y).median()) if len(group) else None,
            "median_absolute_difference": float((x - y).abs().median()) if len(group) else None,
            "spearman_priority": "primary",
            "pearson_priority": "supportive",
            "weighted_kappa_priority": "supportive",
            "comparator_family": "tract_ehr_public_comparators",
            "comparator_interpretation": "neither_measure_is_a_gold_standard",
        }
        try:
            classified = classify_discordance(group, bins="quartile")
        except CaseStudyAnalysisError as error:
            if "degenerate" not in str(error):
                raise
            record.update(
                {
                    "ehr_q25": None,
                    "ehr_q50": None,
                    "ehr_q75": None,
                    "public_q25": None,
                    "public_q50": None,
                    "public_q75": None,
                    "weighted_kappa_quadratic": None,
                    "categorization_status": "withheld_degenerate_cutpoints",
                }
            )
            record.update({f"{category}_count": 0 for category in category_names})
        else:
            first = classified.iloc[0]
            ehr_cuts = (
                float(first["ehr_low_cutpoint"]),
                float(first["ehr_mid_cutpoint"]),
                float(first["ehr_high_cutpoint"]),
            )
            public_cuts = (
                float(first["public_low_cutpoint"]),
                float(first["public_mid_cutpoint"]),
                float(first["public_high_cutpoint"]),
            )
            ehr_quartile = _rank_bins(x, ehr_cuts)
            public_quartile = _rank_bins(y, public_cuts)
            counts = classified["discordance_category"].value_counts()
            record.update(
                {
                    "ehr_q25": ehr_cuts[0],
                    "ehr_q50": ehr_cuts[1],
                    "ehr_q75": ehr_cuts[2],
                    "public_q25": public_cuts[0],
                    "public_q50": public_cuts[1],
                    "public_q75": public_cuts[2],
                    "weighted_kappa_quadratic": _quadratic_weighted_kappa(
                        ehr_quartile, public_quartile
                    ),
                    "categorization_status": "available",
                }
            )
            record.update(
                {f"{category}_count": int(counts.get(category, 0)) for category in category_names}
            )
        records.append(record)

    summary = pd.DataFrame.from_records(records)
    combined_p = pd.concat([summary["spearman_p"], summary["pearson_p"]], ignore_index=True)
    combined_adjusted = _benjamini_hochberg(combined_p)
    condition_count = len(summary)
    summary["spearman_p_bh"] = combined_adjusted.iloc[:condition_count].to_numpy()
    summary["pearson_p_bh"] = combined_adjusted.iloc[condition_count:].to_numpy()
    summary["comparator_family_id"] = "tract_ehr_public_correlation_tests"
    summary["multiplicity_denominator"] = int(combined_p.notna().sum())
    return summary.sort_values(["condition_priority", "condition_id"], kind="mergesort")


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"{label} is missing columns: {missing}")


def _validated_numeric(values: pd.Series, column: str, label: str) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    malformed = values.notna() & (numeric.isna() | ~np.isfinite(numeric))
    if malformed.any():
        raise CaseStudyAnalysisError(f"{label} has non-numeric {column}")
    return numeric


def _sorted_ids(values: pd.Series) -> str:
    return "|".join(sorted(set(values.astype(str))))


def _iqr(values: pd.Series) -> float:
    return float(values.quantile(0.75) - values.quantile(0.25))


def _percentage(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def _cut_points(
    values: pd.Series, quantiles: tuple[float, float, float], condition_id: object
) -> tuple[float, float, float]:
    numeric = values.astype(float)
    cuts = (
        float(numeric.quantile(quantiles[0])),
        float(numeric.quantile(quantiles[1])),
        float(numeric.quantile(quantiles[2])),
    )
    if not cuts[0] < cuts[1] < cuts[2]:
        raise CaseStudyAnalysisError(
            f"condition {condition_id!s} has degenerate discordance cut points: {cuts}"
        )
    return cuts


def _rank_bins(values: pd.Series, cuts: tuple[float, float, float]) -> np.ndarray:
    low, mid, high = cuts
    return np.select(
        [values.le(low), values.lt(mid), values.lt(high)], [0, 1, 2], default=3
    ).astype(int)


def _quadratic_weighted_kappa(first: np.ndarray, second: np.ndarray) -> float | None:
    observed = np.zeros((4, 4), dtype=float)
    for first_rank, second_rank in zip(first, second, strict=True):
        observed[first_rank, second_rank] += 1
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0)) / observed.sum()
    weights = np.fromfunction(lambda row, column: ((row - column) / 3) ** 2, (4, 4))
    expected_disagreement = float((weights * expected).sum())
    if expected_disagreement == 0:
        return None
    return float(1 - (weights * observed).sum() / expected_disagreement)


def _benjamini_hochberg(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.dropna().sort_values(kind="mergesort")
    adjusted = pd.Series(np.nan, index=values.index, dtype=float)
    if valid.empty:
        return adjusted
    count = len(valid)
    raw_adjusted = valid.to_numpy() * count / np.arange(1, count + 1)
    monotone = np.minimum.accumulate(raw_adjusted[::-1])[::-1]
    adjusted.loc[valid.index] = np.minimum(monotone, 1.0)
    return adjusted
