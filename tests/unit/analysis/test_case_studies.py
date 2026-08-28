from __future__ import annotations

import pandas as pd
import pytest

from chicagohealthmap.analysis.case_studies import (
    CaseStudyAnalysisError,
    build_primary_community_frame,
    build_tract_cohort_flow,
    build_tract_concordance_frame,
    classify_discordance,
    summarize_concordance,
    summarize_dataset_shape,
    summarize_resource_quality,
    validate_analytic_dataset,
)


def _row(
    geography_type: str,
    geography_id: str,
    year: str,
    condition_id: str,
    numerator: int,
    denominator: int,
    measure: float,
) -> dict[str, object]:
    condition_family = "diabetes" if condition_id.startswith("diabetes_") else condition_id
    comparator_measure = {
        "hypertension": "bphigh_crudeprev",
        "copd": "copd_crudeprev",
    }.get(condition_id, "diabetes_crudeprev")
    return {
        "geography_type": geography_type,
        "geography_id": geography_id,
        "time_period": year,
        "condition_id": condition_id,
        "source_condition_label": condition_id,
        "geography_name": f"Area {geography_id}",
        "condition_family": condition_family,
        "case_id": "cardiometabolic_bundle",
        "numerator": numerator,
        "denominator": denominator,
        "published_measure_value": measure,
        "published_measure_unit": "source_percent_or_rate",
        "life_expectancy_estimate": 75.0 + int(year) - 2022
        if geography_type == "chicago_community_area"
        else None,
        "public_comparator_estimate": 20.0 if geography_type == "census_tract" else None,
        "public_comparator_role": "tract_concordance_discordance_comparator"
        if geography_type == "census_tract"
        else None,
        "public_comparator_measure_id": comparator_measure,
        "suppression_flag": numerator < 10,
        "capture_rate": 0.5,
        "pct_age_65_plus": 12.0 + int(geography_id[-1]),
        "pct_female": 51.0 + int(geography_id[-1]),
        "pct_below_fpl": 15.0 + int(geography_id[-1]),
        "acs_adult_population": 1000.0 + 100 * int(geography_id[-1]),
        "reliability_flag": "reliability_available",
        "source_id": "test_first_party_source",
        "snapshot_id": "test_first_party_snapshot",
        "source_position_contract": "S4",
        "disease_value_derivation": "direct_first_party_export_not_interpolated",
    }


def _dataset() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for year in ["2022", "2023", "2024"]:
        rows.extend(
            [
                _row("chicago_community_area", "01", year, "hypertension", 100, 1000, 10.0),
                _row(
                    "chicago_community_area",
                    "01",
                    year,
                    "diabetes_with_complication",
                    30,
                    1000,
                    3.0,
                ),
                _row(
                    "chicago_community_area",
                    "01",
                    year,
                    "diabetes_without_complication",
                    70,
                    1000,
                    7.0,
                ),
                _row("chicago_community_area", "01", year, "copd", 50, 1000, 5.0),
                _row("census_tract", "17031010100", year, "hypertension", 20, 100, 0.20),
                _row(
                    "census_tract",
                    "17031010100",
                    year,
                    "diabetes_with_complication",
                    40,
                    100,
                    0.04,
                ),
                _row(
                    "census_tract",
                    "17031010100",
                    year,
                    "diabetes_without_complication",
                    60,
                    100,
                    0.06,
                ),
                _row("census_tract", "17031010100", year, "copd", 12, 100, 0.12),
            ]
        )
    return pd.DataFrame(rows)


def _approved_dataset() -> pd.DataFrame:
    dataset = _dataset()
    dataset["combined_diabetes_semantics_approved"] = True
    return dataset


def test_build_tract_cohort_flow_reconstructs_sequential_exclusions() -> None:
    dataset = _approved_dataset()
    tract = dataset["geography_type"].eq("census_tract")
    small = (
        tract
        & dataset["condition_id"].eq("hypertension")
        & dataset["time_period"].eq("2022")
    )
    suppressed = (
        tract
        & dataset["condition_id"].eq("copd")
        & dataset["time_period"].eq("2023")
    )
    dataset.loc[small, "denominator"] = 29
    dataset.loc[suppressed, "suppression_flag"] = True
    denominator_eligible = pd.to_numeric(dataset["denominator"], errors="coerce").ge(30)
    dataset["primary_tract_annual_eligible"] = (
        tract
        & denominator_eligible
        & ~dataset["suppression_flag"].astype(bool)
        & dataset["numerator"].notna()
    )

    flow = build_tract_cohort_flow(dataset)

    hypertension_2022 = flow.loc[
        flow["condition_id"].eq("hypertension") & flow["time_period"].eq("2022")
    ].iloc[0]
    copd_2023 = flow.loc[
        flow["condition_id"].eq("copd") & flow["time_period"].eq("2023")
    ].iloc[0]
    assert hypertension_2022["excluded_denominator_lt_30_or_missing_rows"] == 1
    assert hypertension_2022["primary_eligible_rows"] == 0
    assert copd_2023["excluded_suppressed_or_missing_numerator_rows"] == 1
    assert copd_2023["primary_eligible_rows"] == 0


def test_build_tract_cohort_flow_rejects_stale_recorded_eligibility() -> None:
    dataset = _approved_dataset()
    dataset["primary_tract_annual_eligible"] = True
    first_tract = dataset.index[dataset["geography_type"].eq("census_tract")][0]
    dataset.loc[first_tract, "primary_tract_annual_eligible"] = False

    with pytest.raises(CaseStudyAnalysisError, match="stored tract eligibility disagrees"):
        build_tract_cohort_flow(dataset)


def test_validate_analytic_dataset_rejects_duplicate_primary_key() -> None:
    dataset = pd.concat([_dataset(), _dataset().iloc[[0]]], ignore_index=True)

    with pytest.raises(CaseStudyAnalysisError, match="duplicate keys"):
        validate_analytic_dataset(dataset)


def test_build_primary_community_frame_sums_contemporary_exposures() -> None:
    frame = build_primary_community_frame(_approved_dataset())

    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["life_expectancy_years_complete"] == 3
    assert bool(row["primary_model_complete"]) is True
    assert row["hypertension_ehr_percent_2022_2024"] == pytest.approx(10.0)
    assert row["diabetes_ehr_percent_2022_2024"] == pytest.approx(10.0)
    assert row["copd_ehr_percent_2022_2024"] == pytest.approx(5.0)


def test_combined_diabetes_fails_closed_without_explicit_semantic_approval() -> None:
    row = build_primary_community_frame(_dataset()).iloc[0]

    assert pd.isna(row["diabetes_ehr_percent_2022_2024"])
    assert row["diabetes_eligible_annual_rows"] == 0
    assert bool(row["diabetes_exposure_complete"]) is False
    assert bool(row["primary_model_complete"]) is False


def test_build_primary_community_frame_carries_one_frozen_covariate_value_per_area() -> None:
    frame = build_primary_community_frame(_dataset())

    assert frame["geography_id"].nunique() == 1
    columns = ["pct_age_65_plus", "pct_female", "pct_below_fpl", "acs_adult_population"]
    assert frame[columns].notna().all().all()
    assert frame["capture_rate_mean_2022_2024"].notna().all()
    assert frame.groupby("geography_id")["pct_age_65_plus"].nunique().max() == 1


def test_build_primary_community_frame_excludes_suppressed_annual_exposure() -> None:
    dataset = _approved_dataset()
    suppressed = (
        (dataset["geography_type"] == "chicago_community_area")
        & (dataset["condition_id"] == "hypertension")
        & (dataset["time_period"] == "2023")
    )
    dataset.loc[suppressed, ["numerator", "published_measure_value"]] = [5, 0.005]
    dataset.loc[suppressed, "suppression_flag"] = True

    frame = build_primary_community_frame(dataset)

    row = frame.iloc[0]
    assert row["hypertension_numerator_sum"] == 200
    assert row["hypertension_denominator_sum"] == 2000
    assert row["hypertension_eligible_annual_rows"] == 2
    assert row["hypertension_ineligible_annual_rows"] == 1
    assert bool(row["hypertension_exposure_complete"]) is False


def test_primary_model_complete_requires_all_exposures_and_outcome_complete() -> None:
    dataset = _dataset()
    suppressed = (
        (dataset["geography_type"] == "chicago_community_area")
        & (dataset["condition_id"] == "copd")
        & (dataset["time_period"] == "2023")
    )
    dataset.loc[suppressed, "suppression_flag"] = True

    row = build_primary_community_frame(dataset).iloc[0]

    assert row["life_expectancy_years_complete"] == 3
    assert bool(row["copd_exposure_complete"]) is False
    assert bool(row["primary_model_complete"]) is False


@pytest.mark.parametrize("unavailable_reason", ["suppressed", "missing"])
def test_build_primary_community_frame_requires_both_diabetes_components_per_year(
    unavailable_reason: str,
) -> None:
    dataset = _approved_dataset()
    component = (
        (dataset["geography_type"] == "chicago_community_area")
        & (dataset["condition_id"] == "diabetes_with_complication")
        & (dataset["time_period"] == "2023")
    )
    if unavailable_reason == "suppressed":
        dataset.loc[component, "suppression_flag"] = True
    else:
        dataset = dataset.loc[~component].copy()

    frame = build_primary_community_frame(dataset)

    row = frame.iloc[0]
    assert row["diabetes_numerator_sum"] == 200
    assert row["diabetes_denominator_sum"] == 2000
    assert row["diabetes_eligible_annual_rows"] == 2
    assert row["diabetes_ineligible_annual_rows"] == 1
    assert bool(row["diabetes_exposure_complete"]) is False


def test_diabetes_aggregation_rejects_unexpected_family_component() -> None:
    dataset = _dataset()
    unexpected = dataset.loc[
        (dataset["geography_type"] == "chicago_community_area")
        & (dataset["condition_id"] == "hypertension")
        & (dataset["time_period"] == "2022")
    ].copy()
    unexpected["condition_id"] = "diabetes_other"
    unexpected["condition_family"] = "diabetes"
    dataset = pd.concat([dataset, unexpected], ignore_index=True)

    with pytest.raises(CaseStudyAnalysisError, match="unexpected diabetes components"):
        build_primary_community_frame(dataset)


def test_diabetes_aggregation_rejects_null_family_condition_id() -> None:
    dataset = _dataset()
    unidentified = dataset.loc[
        (dataset["geography_type"] == "chicago_community_area")
        & (dataset["condition_id"] == "hypertension")
        & (dataset["time_period"] == "2022")
    ].copy()
    unidentified["condition_id"] = None
    unidentified["condition_family"] = "diabetes"
    dataset = pd.concat([dataset, unidentified], ignore_index=True)

    with pytest.raises(CaseStudyAnalysisError, match="null diabetes condition IDs"):
        build_primary_community_frame(dataset)


def test_build_tract_concordance_frame_and_summary() -> None:
    frame = build_tract_concordance_frame(_approved_dataset())
    summary = summarize_concordance(frame)

    assert set(frame["condition_id"]) == {"copd", "diabetes", "hypertension"}
    assert set(frame["annual_rows"]) == {3}
    diabetes = frame.loc[frame["condition_id"] == "diabetes"].iloc[0]
    assert diabetes["source_condition_label"] == "diabetes_combined_components"
    assert diabetes["ehr_percent_mean_2022_2024"] == pytest.approx(100.0)
    assert "spearman_r" in set(summary.columns)
    assert summary["rows"].sum() == 3


@pytest.mark.parametrize("unavailable_reason", ["suppressed", "missing"])
def test_build_tract_concordance_requires_both_diabetes_components_per_year(
    unavailable_reason: str,
) -> None:
    dataset = _approved_dataset()
    component = (
        (dataset["geography_type"] == "census_tract")
        & (dataset["condition_id"] == "diabetes_with_complication")
        & (dataset["time_period"] == "2023")
    )
    if unavailable_reason == "suppressed":
        dataset.loc[component, "suppression_flag"] = True
    else:
        dataset = dataset.loc[~component].copy()

    frame = build_tract_concordance_frame(dataset)

    assert "diabetes" not in set(frame["condition_id"])


def test_build_tract_concordance_excludes_absent_diabetes_year() -> None:
    dataset = _approved_dataset()
    absent_year = (
        (dataset["geography_type"] == "census_tract")
        & (dataset["condition_family"] == "diabetes")
        & (dataset["time_period"] == "2023")
    )
    dataset = dataset.loc[~absent_year].copy()

    frame = build_tract_concordance_frame(dataset)

    assert "diabetes" not in set(frame["condition_id"])


def test_build_tract_concordance_converts_source_proportion_to_percentage_points() -> None:
    dataset = _dataset()
    mask = (dataset["geography_type"] == "census_tract") & (
        dataset["condition_id"] == "hypertension"
    )
    dataset.loc[mask, "published_measure_value"] = 0.20

    frame = build_tract_concordance_frame(dataset)

    hypertension = frame.loc[frame["condition_id"] == "hypertension"].iloc[0]
    assert hypertension["ehr_percent_mean_2022_2024"] == pytest.approx(20.0)


def test_build_tract_concordance_uses_pooled_counts_not_unweighted_annual_mean() -> None:
    dataset = _approved_dataset()
    mask = (dataset["geography_type"] == "census_tract") & (
        dataset["condition_id"] == "hypertension"
    )
    dataset.loc[mask, "numerator"] = [10, 40, 90]
    dataset.loc[mask, "denominator"] = [100, 200, 300]
    dataset.loc[mask, "published_measure_value"] = [0.10, 0.20, 0.30]

    frame = build_tract_concordance_frame(dataset)
    hypertension = frame.loc[frame["condition_id"] == "hypertension"].iloc[0]

    assert hypertension["ehr_percent_mean_2022_2024"] == pytest.approx(100 * 140 / 600)
    assert hypertension["ehr_percent_mean_2022_2024"] != pytest.approx(20.0)


def test_build_tract_concordance_rejects_unknown_source_measure_units() -> None:
    dataset = _dataset()
    dataset.loc[dataset["geography_type"] == "census_tract", "published_measure_unit"] = "unknown"

    with pytest.raises(CaseStudyAnalysisError, match="published measure units"):
        build_tract_concordance_frame(dataset)


def test_build_tract_concordance_rejects_mixed_valid_and_missing_units() -> None:
    dataset = _dataset()
    tract_index = dataset.index[dataset["geography_type"] == "census_tract"]
    dataset.loc[tract_index[0], "published_measure_unit"] = None

    with pytest.raises(CaseStudyAnalysisError, match="published measure units"):
        build_tract_concordance_frame(dataset)


def test_summarize_concordance_drops_incomplete_ehr_public_pairs() -> None:
    frame = pd.DataFrame(
        {
            "condition_id": ["copd"] * 5,
            "ehr_percent_mean_2022_2024": [10.0, 20.0, 30.0, float("nan"), 50.0],
            "public_comparator_estimate": [12.0, 22.0, 32.0, 42.0, float("nan")],
            "signed_difference": [-2.0, -2.0, -2.0, float("nan"), float("nan")],
            "absolute_difference": [2.0, 2.0, 2.0, float("nan"), float("nan")],
        }
    )

    summary = summarize_concordance(frame)

    row = summary.iloc[0]
    assert row["rows"] == 3
    assert row["spearman_r"] == pytest.approx(1.0)
    assert row["pearson_r"] == pytest.approx(1.0)
    assert row["median_signed_difference"] == pytest.approx(-2.0)
    assert row["median_absolute_difference"] == pytest.approx(2.0)


def test_summarize_dataset_shape_is_human_readable() -> None:
    summary = summarize_dataset_shape(_dataset())

    assert {"geography_type", "condition_id", "rows", "geographies", "years"}.issubset(
        summary.columns
    )


def test_summarize_resource_quality_preserves_zero_and_uses_explicit_denominators() -> None:
    dataset = pd.DataFrame(
        {
            "geography_type": ["census_tract"] * 4,
            "condition_id": ["copd"] * 4,
            "geography_id": ["a", "a", "b", "b"],
            "time_period": ["2022", "2023", "2022", "2023"],
            "numerator": [0.0, 5.0, None, 20.0],
            "denominator": [0.0, 100.0, None, 300.0],
            "published_measure_value": [0.0, 0.05, None, 0.20],
            "published_measure_unit": ["source_percent_or_rate"] * 4,
            "capture_rate": [0.0, 0.5, None, 1.0],
            "suppression_flag": [False, True, False, False],
            "reliability_flag": [
                "reliability_available",
                "reliability_available",
                "reliability_missing",
                "reliability_available",
            ],
            "source_id": ["source-b", "source-a", "source-b", "source-a"],
            "snapshot_id": ["snapshot-2", "snapshot-1", "snapshot-2", "snapshot-1"],
            "source_position_contract": ["contract-b", "contract-a", "contract-b", "contract-a"],
            "disease_value_derivation": [
                "direct_first_party_export_not_interpolated",
                "direct_first_party_export_not_interpolated",
                "other_validated_derivation",
                "direct_first_party_export_not_interpolated",
            ],
        }
    )

    row = summarize_resource_quality(dataset).iloc[0]

    assert row["rows"] == 4
    assert row["geographies"] == 2
    assert row["years"] == 2
    assert row["denominator_median"] == pytest.approx(100.0)
    assert row["denominator_iqr"] == pytest.approx(150.0)
    assert row["disease_measure_median_percentage_points"] == pytest.approx(10.0)
    assert row["disease_measure_iqr_percentage_points"] == pytest.approx(10.0)
    assert row["disease_measure_eligible_rows"] == 2
    assert row["capture_median"] == pytest.approx(0.5)
    assert row["capture_iqr"] == pytest.approx(0.5)
    assert row["capture_missing_rows"] == 1
    assert row["capture_missing_percentage"] == pytest.approx(25.0)
    assert row["missing_rows"] == 1
    assert row["missing_percentage"] == pytest.approx(25.0)
    assert row["suppressed_rows"] == 1
    assert row["suppression_percentage"] == pytest.approx(25.0)
    assert row["disease_value_missing_rows"] == 1
    assert row["disease_value_missing_percentage"] == pytest.approx(25.0)
    assert row["reliability_available_rows"] == 3
    assert row["reliability_available_percentage"] == pytest.approx(75.0)
    assert row["reliability_qualification_status"] == "withheld_pending_reliability_rule"
    assert pd.isna(row["reliability_qualified_rows"])
    assert pd.isna(row["reliability_qualified_percentage"])
    assert row["percentage_denominator_rows"] == 4
    assert row["missing_percentage_denominator_rows"] == 4
    assert row["suppression_percentage_denominator_rows"] == 4
    assert row["disease_value_missing_percentage_denominator_rows"] == 4
    assert row["reliability_available_percentage_denominator_rows"] == 4
    assert pd.isna(row["reliability_qualified_percentage_denominator_rows"])
    assert row["source_ids"] == "source-a|source-b"
    assert row["snapshot_ids"] == "snapshot-1|snapshot-2"
    assert row["source_position_contracts"] == "contract-a|contract-b"
    assert row["disease_value_derivations"] == (
        "direct_first_party_export_not_interpolated|other_validated_derivation"
    )
    assert row["direct_first_party_rows"] == 3
    assert row["direct_first_party_percentage"] == pytest.approx(75.0)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("numerator", "not-a-number"),
        ("denominator", "bad"),
        ("capture_rate", "bad"),
        ("published_measure_value", "bad"),
    ],
)
def test_summarize_resource_quality_rejects_malformed_numeric_values(
    column: str, value: str
) -> None:
    dataset = _dataset().iloc[[0]].copy()
    dataset[column] = dataset[column].astype(object)
    dataset.loc[dataset.index[0], column] = value

    with pytest.raises(CaseStudyAnalysisError, match=f"non-numeric {column}"):
        summarize_resource_quality(dataset)


@pytest.mark.parametrize(
    "column", ["source_id", "snapshot_id", "source_position_contract", "disease_value_derivation"]
)
def test_summarize_resource_quality_requires_nonmissing_provenance(column: str) -> None:
    dataset = _dataset().iloc[[0]].copy()
    dataset.loc[dataset.index[0], column] = None

    with pytest.raises(CaseStudyAnalysisError, match=f"missing provenance column: {column}"):
        summarize_resource_quality(dataset)


@pytest.mark.parametrize("value", [1, 0, "False", None])
def test_summarize_resource_quality_rejects_non_boolean_suppression(value: object) -> None:
    dataset = _dataset().iloc[[0]].copy()
    dataset["suppression_flag"] = dataset["suppression_flag"].astype(object)
    dataset.loc[dataset.index[0], "suppression_flag"] = value

    with pytest.raises(CaseStudyAnalysisError, match="suppression_flag must contain booleans"):
        summarize_resource_quality(dataset)


def _discordance_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "condition_id": ["copd"] * 9,
            "geography_id": [f"g{index}" for index in range(9)],
            "ehr_percent_mean_2022_2024": list(range(9)),
            "public_comparator_estimate": [0, 1, 2, 8, 4, 5, 6, 3, 7],
        }
    )


def test_classify_discordance_assigns_all_frozen_categories_at_boundaries() -> None:
    classified = classify_discordance(_discordance_frame()).set_index("geography_id")

    assert classified.loc["g6", "discordance_category"] == "concordant_high"
    assert classified.loc["g2", "discordance_category"] == "concordant_low"
    assert classified.loc["g7", "discordance_category"] == "ehr_high_public_not_high"
    assert classified.loc["g3", "discordance_category"] == "public_high_ehr_not_high"
    assert classified.loc["g5", "discordance_category"] == "intermediate"
    assert classified.loc["g6", "ehr_high_cutpoint"] == pytest.approx(6.0)
    assert classified.loc["g2", "ehr_low_cutpoint"] == pytest.approx(2.0)
    assert classified.loc["g5", "public_mid_cutpoint"] == pytest.approx(4.0)


def test_classify_discordance_tertile_thresholds_are_deterministic() -> None:
    classified = classify_discordance(_discordance_frame(), bins="tertile").set_index(
        "geography_id"
    )

    assert classified.loc["g5", "ehr_high_cutpoint"] == pytest.approx(16 / 3)
    assert classified.loc["g5", "ehr_low_cutpoint"] == pytest.approx(8 / 3)
    assert classified.loc["g5", "ehr_mid_cutpoint"] == pytest.approx(4.0)
    assert classified.loc["g7", "discordance_category"] == "ehr_high_public_not_high"


@pytest.mark.parametrize("bins", ["decile", "quartiles"])
def test_classify_discordance_rejects_unsupported_bins(bins: str) -> None:
    with pytest.raises(CaseStudyAnalysisError, match="unsupported discordance bins"):
        classify_discordance(_discordance_frame(), bins=bins)  # type: ignore[arg-type]


def test_classify_discordance_fails_closed_for_degenerate_ties() -> None:
    frame = _discordance_frame()
    frame["ehr_percent_mean_2022_2024"] = 1.0

    with pytest.raises(CaseStudyAnalysisError, match="degenerate"):
        classify_discordance(frame)


def test_classify_discordance_rejects_malformed_numeric_values() -> None:
    frame = _discordance_frame()
    frame["ehr_percent_mean_2022_2024"] = frame["ehr_percent_mean_2022_2024"].astype(object)
    frame.loc[0, "ehr_percent_mean_2022_2024"] = "bad"

    with pytest.raises(CaseStudyAnalysisError, match="non-numeric ehr_percent_mean_2022_2024"):
        classify_discordance(frame)


def test_summarize_concordance_reports_known_quadratic_weighted_kappa() -> None:
    frame = pd.DataFrame(
        {
            "condition_id": ["copd"] * 8,
            "geography_id": [f"g{index}" for index in range(8)],
            "ehr_percent_mean_2022_2024": list(range(8)),
            "public_comparator_estimate": list(range(8)),
        }
    )
    frame["signed_difference"] = 0.0
    frame["absolute_difference"] = 0.0

    row = summarize_concordance(frame).iloc[0]

    assert row["weighted_kappa_quadratic"] == pytest.approx(1.0)
    assert row["ehr_q25"] == pytest.approx(1.75)
    assert row["ehr_q50"] == pytest.approx(3.5)
    assert row["ehr_q75"] == pytest.approx(5.25)
    assert row["concordant_high_count"] == 2
    assert row["concordant_low_count"] == 2
    assert row["spearman_priority"] == "primary"
    assert row["pearson_priority"] == "supportive"
    assert row["condition_priority"] == 3
    assert row["comparator_interpretation"] == "neither_measure_is_a_gold_standard"


def test_summarize_concordance_reports_known_nonperfect_quadratic_weighted_kappa() -> None:
    frame = pd.DataFrame(
        {
            "condition_id": ["copd"] * 8,
            "ehr_percent_mean_2022_2024": list(range(8)),
            "public_comparator_estimate": [0, 1, 2, 4, 3, 5, 6, 7],
        }
    )

    row = summarize_concordance(frame).iloc[0]

    assert row["weighted_kappa_quadratic"] == pytest.approx(0.9)


def test_summarize_concordance_bh_adjusts_each_metric_within_comparator_family() -> None:
    frame = pd.concat(
        [
            pd.DataFrame(
                {
                    "condition_id": condition,
                    "geography_id": [f"{condition}-{index}" for index in range(5)],
                    "ehr_percent_mean_2022_2024": [1, 2, 3, 4, 5],
                    "public_comparator_estimate": public,
                }
            )
            for condition, public in [
                ("copd", [1, 4, 9, 16, 25]),
                ("diabetes", [1, 2, 10, 4, 20]),
                ("hypertension", [20, 1, 10, 2, 4]),
            ]
        ],
        ignore_index=True,
    )
    frame["signed_difference"] = (
        frame["ehr_percent_mean_2022_2024"] - frame["public_comparator_estimate"]
    )
    frame["absolute_difference"] = frame["signed_difference"].abs()

    summary = summarize_concordance(frame).set_index("condition_id")

    assert summary.loc["copd", "spearman_p"] == pytest.approx(1.4042654220543672e-24)
    assert summary.loc["diabetes", "spearman_p"] == pytest.approx(0.03738607346849874)
    assert summary.loc["hypertension", "spearman_p"] == pytest.approx(0.6238376647810728)
    assert summary.loc["copd", "pearson_p"] == pytest.approx(0.0031090131086883516)
    assert summary.loc["diabetes", "pearson_p"] == pytest.approx(0.1006539687666509)
    assert summary.loc["hypertension", "pearson_p"] == pytest.approx(0.2610877937427129)
    assert set(summary["comparator_family_id"]) == {"tract_ehr_public_correlation_tests"}
    assert set(summary["multiplicity_denominator"]) == {6}
    assert summary.loc["copd", "spearman_p_bh"] == pytest.approx(8.425592532326162e-24)
    assert summary.loc["diabetes", "spearman_p_bh"] == pytest.approx(0.07477214693699748)
    assert summary.loc["hypertension", "spearman_p_bh"] == pytest.approx(0.623837664781073)
    assert summary.loc["copd", "pearson_p_bh"] == pytest.approx(0.009327039326065056)
    assert summary.loc["diabetes", "pearson_p_bh"] == pytest.approx(0.15098095314997637)
    assert summary.loc["hypertension", "pearson_p_bh"] == pytest.approx(0.31330535249125546)


def test_summarize_concordance_rejects_empty_schema_valid_input() -> None:
    frame = pd.DataFrame(
        columns=["condition_id", "ehr_percent_mean_2022_2024", "public_comparator_estimate"]
    )

    with pytest.raises(CaseStudyAnalysisError, match="concordance frame has no rows"):
        summarize_concordance(frame)


def test_summarize_concordance_rejects_malformed_numeric_values() -> None:
    frame = _discordance_frame()
    frame["public_comparator_estimate"] = frame["public_comparator_estimate"].astype(object)
    frame.loc[0, "public_comparator_estimate"] = "bad"

    with pytest.raises(CaseStudyAnalysisError, match="non-numeric public_comparator_estimate"):
        summarize_concordance(frame)
