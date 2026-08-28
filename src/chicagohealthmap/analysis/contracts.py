"""Neutral contracts shared by descriptive analyses and presentation layers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]
import numpy as np

A1_A7_ANALYSIS_NAMES: dict[str, str] = {
    "A1": "Variance partitioning / VPC-ICC",
    "A2": "Area-label discriminatory accuracy",
    "A3": "CHM–PLACES rank concordance",
    "A4": "Quartile agreement",
    "A5": "Uncertainty-aware discordance",
    "A6": "Geographic scale sensitivity",
    "A7": "Local spatial structure",
}

FRAME_COLUMNS = {
    "geography_type",
    "geography_id",
    "community_area_id",
    "time_period",
    "condition_id",
    "published_measure_value",
    "suppression_flag",
    "is_crossing_tract",
    "reliability_tier",
    "disease_value_derivation",
}

RESULT_FIELDS = {
    "analysis_id",
    "analysis_name",
    "estimand",
    "unit",
    "denominator",
    "period",
    "uncertainty",
    "diagnostic_status",
    "sensitivity_status",
    "source_artifact",
    "results_authorized",
}


def build_complementarity_frame(
    dataset: pd.DataFrame,
    *,
    condition_id: str,
    geography_type: str = "census_tract",
    years: Sequence[str] = ("2022", "2023", "2024"),
    require_public_comparator: bool = False,
    reliability_tiers: Sequence[str] | None = None,
    noncrossing_only: bool = False,
) -> pd.DataFrame:
    """Return one frozen, complete-case frame shared by A1 through A6."""

    missing = sorted(FRAME_COLUMNS - set(dataset.columns))
    if require_public_comparator and "public_comparator_estimate" not in dataset:
        missing.append("public_comparator_estimate")
    if missing:
        raise ValueError(f"complementarity frame is missing columns: {sorted(set(missing))}")
    if (
        dataset["disease_value_derivation"]
        .astype(str)
        .ne("direct_first_party_export_not_interpolated")
        .any()
    ):
        raise ValueError("complementarity frame requires direct, uninterpolated CHM values")
    key = ["geography_type", "geography_id", "time_period", "condition_id"]
    if dataset.duplicated(key).any():
        raise ValueError("complementarity frame contains duplicate geography-period-condition keys")
    frame = dataset.loc[
        dataset["condition_id"].astype(str).eq(condition_id)
        & dataset["geography_type"].astype(str).eq(geography_type)
        & dataset["time_period"].astype(str).isin(tuple(str(year) for year in years))
    ].copy()
    frame = frame.loc[~_flag_series(frame["suppression_flag"])]
    exposure = pd.to_numeric(frame["published_measure_value"], errors="coerce")
    frame = frame.loc[exposure.notna() & np.isfinite(exposure)].copy()
    frame["published_measure_value"] = exposure.loc[frame.index]
    if require_public_comparator:
        comparator = pd.to_numeric(frame["public_comparator_estimate"], errors="coerce")
        frame = frame.loc[comparator.notna() & np.isfinite(comparator)].copy()
        frame["public_comparator_estimate"] = comparator.loc[frame.index]
    if reliability_tiers is not None:
        frame = frame.loc[frame["reliability_tier"].astype(str).isin(tuple(reliability_tiers))]
    if noncrossing_only:
        frame = frame.loc[~frame["is_crossing_tract"].astype(bool)]
    frame = frame.sort_values(["geography_id", "time_period"], kind="mergesort").reset_index(
        drop=True
    )
    frame["analysis_condition_id"] = condition_id
    frame["analysis_scale"] = geography_type
    frame["analysis_years"] = ",".join(str(year) for year in years)
    frame["analysis_assignment_rule"] = (
        "noncrossing_only" if noncrossing_only else "direct_or_dominant_linkage"
    )
    frame["analysis_reliability_rule"] = (
        "all_available" if reliability_tiers is None else ",".join(reliability_tiers)
    )
    frame["analysis_complete_case"] = True
    frame["analysis_denominator"] = len(frame)
    frame["analysis_excluded_rows"] = len(dataset) - len(frame)
    frame["results_authorized"] = False
    return frame


def _flag_series(values: pd.Series) -> pd.Series:
    """Interpret common serialized boolean values without treating ``'false'`` as true."""

    if pd.api.types.is_bool_dtype(values):
        return values.fillna(False)
    normalized = values.astype("string").str.strip().str.lower()
    return normalized.isin({"1", "true", "t", "yes", "y"})


def validate_analysis_result(result: Mapping[str, object]) -> dict[str, object]:
    """Validate a result row before it reaches reporting or audit layers."""

    missing = sorted(RESULT_FIELDS - set(result))
    if missing:
        raise ValueError(f"analysis result is missing fields: {missing}")
    analysis_id = str(result["analysis_id"])
    if analysis_id not in A1_A7_ANALYSIS_NAMES:
        raise ValueError(f"unknown descriptive analysis id: {analysis_id}")
    if str(result["analysis_name"]) != A1_A7_ANALYSIS_NAMES[analysis_id]:
        raise ValueError("analysis_name does not match analysis_id")
    if result["results_authorized"] is not False:
        raise ValueError("descriptive analysis authorization must remain false")
    denominator = result["denominator"]
    if (
        isinstance(denominator, bool)
        or not isinstance(denominator, (int, float))
        or denominator < 0
    ):
        raise ValueError("descriptive analysis denominator must be nonnegative")
    for field in ("estimate", "ci_low", "ci_high"):
        if field in result and result[field] is not None:
            try:
                value = float(cast(Any, result[field]))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"descriptive analysis {field} is not numeric") from exc
            if not math.isfinite(value):
                raise ValueError(f"descriptive analysis {field} is not finite")
    return dict(result)
