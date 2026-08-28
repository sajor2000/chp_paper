from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chicagohealthmap.analysis.tract_complementarity import (
    _quartile_bins,
    _rank_quartile,
    _rerank_concordance,
    assign_capture_quartile,
    build_direct_ehr_rank_frame,
    build_direct_tract_analysis_frame,
    build_direct_consequence_rank_frame,
    build_annual_direct_consequence_rank_frame,
    build_geographic_consequence_tables,
    build_tract_percentile_concordance,
    cluster_bootstrap_concordance,
    compute_discriminatory_accuracy,
    compute_variance_partition,
    gwet_ac1,
    propagate_uncertainty_discordance,
    percentile_rank,
    parse_places_confidence_interval,
    summarize_community_area_aggregation_loss,
    summarize_concordance_metrics,
    summarize_annual_consequence_stability,
    summarize_within_community_heterogeneity,
)

CUTS = (0.075, 0.125, 0.175)


def _rows() -> pd.DataFrame:
    rows = []
    for tract, area, weight, crossing, capture, reliability, ehr, public in [
        ("t1", "01", 1.0, False, 0.05, "Low (2-5%)", 0.10, 5.0),
        ("t2", "01", 1.0, False, 0.10, "Moderate (5-10%)", 0.20, 10.0),
        ("t3", "02", 0.98, True, 0.15, "High (10-20%)", 0.30, 20.0),
        ("t4", "02", 1.0, True, 0.20, "Very High (>=20%)", 0.40, 40.0),
    ]:
        for year in ("2022", "2023", "2024"):
            rows.append(
                {
                    "geography_type": "census_tract",
                    "geography_id": tract,
                    "geography_name": tract,
                    "time_period": year,
                    "condition_id": "hypertension",
                    "condition_family": "hypertension",
                    "numerator": int(ehr * 100),
                    "denominator": 100,
                    "published_measure_value": ehr,
                    "published_measure_unit": "source_percent_or_rate",
                    "public_comparator_estimate": public,
                    "public_comparator_measure_id": "bphigh_crudeprev",
                    "suppression_flag": False,
                    "capture_rate": capture,
                    "reliability_tier": reliability,
                    "reliability_flag": "reliability_available",
                    "community_area_id": area,
                    "max_community_area_weight": weight,
                    "is_crossing_tract": crossing,
                    "disease_value_derivation": "direct_first_party_export_not_interpolated",
                    "source_id": "chm",
                    "snapshot_id": "snap",
                }
            )
    return pd.DataFrame(rows)


def _community_rows() -> pd.DataFrame:
    rows = []
    for area, value in [("01", 0.15), ("02", 0.35)]:
        for year in ("2022", "2023", "2024"):
            rows.append(
                {
                    "geography_type": "chicago_community_area",
                    "geography_id": area,
                    "time_period": year,
                    "condition_id": "hypertension",
                    "condition_family": "hypertension",
                "numerator": int(value * 100),
                    "denominator": 100,
                    "published_measure_value": value,
                    "suppression_flag": False,
                    "disease_value_derivation": "direct_first_party_export_not_interpolated",
                }
            )
    return pd.DataFrame(rows)


def test_percentile_rank_uses_average_ties_and_is_deterministic() -> None:
    result = percentile_rank(pd.Series([10.0, 20.0, 20.0, 40.0]))
    assert result.tolist() == pytest.approx([0.25, 0.625, 0.625, 1.0])


def test_quartile_boundaries_are_identical_across_rank_uses() -> None:
    ranks = pd.Series([0.25, 0.50, 0.75, 0.75001])
    assert _rank_quartile(ranks).tolist() == [1, 2, 3, 4]
    assert _quartile_bins(ranks).tolist() == [0, 1, 2, 3]


def test_bootstrap_reranking_recomputes_rank_derived_fields() -> None:
    frame = pd.DataFrame(
        {
            "ehr_percent": [30.0, 10.0, 20.0],
            "public_comparator_estimate": [10.0, 30.0, 20.0],
            "ehr_rank": [0.1, 0.2, 0.3],
            "public_rank": [0.1, 0.2, 0.3],
        }
    )
    ranked = _rerank_concordance(frame)
    assert ranked["ehr_rank"].tolist() == pytest.approx([1.0, 1 / 3, 2 / 3])
    assert ranked["public_rank"].tolist() == pytest.approx([1 / 3, 1.0, 2 / 3])
    assert ranked["absolute_percentile_rank_gap"].tolist() == pytest.approx([2 / 3, 2 / 3, 0])


def test_dominant_threshold_and_duplicate_fail_closed() -> None:
    frame = build_tract_percentile_concordance(
        _rows(), area_assignment_threshold=0.99, capture_cut_points=CUTS
    )
    assert set(frame["geography_id"]) == {"t1", "t2", "t4"}
    duplicate = pd.concat([_rows(), _rows().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        build_tract_percentile_concordance(duplicate, capture_cut_points=CUTS)


def test_noncrossing_sensitivity_and_strata_are_explicit() -> None:
    frame = build_tract_percentile_concordance(
        _rows(), noncrossing_only=False, capture_cut_points=CUTS
    )
    assert frame["capture_quartile"].notna().all()
    assert frame["reliability_tier"].notna().all()
    assert frame["is_crossing_tract"].any()
    noncrossing = build_tract_percentile_concordance(
        _rows(), noncrossing_only=True, capture_cut_points=CUTS
    )
    assert not noncrossing["is_crossing_tract"].any()


def test_concordance_metrics_include_gap_kappa_and_categories() -> None:
    frame = build_tract_percentile_concordance(
        _rows(), noncrossing_only=True, capture_cut_points=CUTS
    )
    summary = summarize_concordance_metrics(frame)
    assert {"spearman_r", "quadratic_weighted_kappa", "median_absolute_percentile_rank_gap"} <= set(
        summary
    )
    assert int(summary.iloc[0]["sample_n"]) == 2
    assert int(summary.iloc[0]["discordance_category_total"]) == 2
    assert summary.iloc[0]["results_authorized"] is False


def test_within_community_denominators_and_coexistence() -> None:
    frame = build_tract_percentile_concordance(
        _rows(), noncrossing_only=True, capture_cut_points=CUTS
    )
    summary = summarize_within_community_heterogeneity(frame)
    area_one = summary.loc[summary["community_area_id"].eq("01")].iloc[0]
    assert int(area_one["eligible_tract_count"]) == 2
    assert area_one["top_quartile_share"] == pytest.approx(0.5)
    assert area_one["bottom_quartile_share"] == pytest.approx(0.0)
    assert bool(area_one["high_low_rank_coexistence"]) is False


def test_community_area_aggregation_loss_quantifies_rank_reclassification() -> None:
    analytic = pd.concat([_rows(), _community_rows()], ignore_index=True, sort=False)
    tract_frame = build_tract_percentile_concordance(
        analytic, noncrossing_only=False, capture_cut_points=CUTS
    )
    summary = summarize_community_area_aggregation_loss(analytic, tract_frame)

    row = summary.loc[summary["condition_id"].eq("hypertension")].iloc[0]
    assert int(row["tract_sample_n"]) == 3
    assert int(row["comparison_geography_n"]) == 2
    assert row["median_absolute_percentile_rank_gap"] == pytest.approx(1 / 6)
    assert row["quartile_disagree_pct"] == pytest.approx(100 / 3)
    assert row["q4_movement_pct"] == pytest.approx(0)
    assert row["quartile_disagree_pct_ci_low"] <= row["quartile_disagree_pct"]
    assert row["quartile_disagree_pct_ci_high"] >= row["quartile_disagree_pct"]
    assert row["bootstrap_rank_rule"] == "recomputed_within_each_cluster_resample"
    assert row["analysis_status"] == "geographic_resolution_sensitivity"
    assert row["interpretation_label"] == "tract_resolution_not_area_prevalence"
    assert row["results_authorized"] is False


def test_direct_community_rank_frame_preserves_direct_measure_grain() -> None:
    frame = build_direct_ehr_rank_frame(_community_rows(), "chicago_community_area")

    assert frame[["geography_id", "ehr_percent"]].to_dict("records") == [
        {"geography_id": "01", "ehr_percent": 15.0},
        {"geography_id": "02", "ehr_percent": 35.0},
    ]
    assert frame["ehr_rank"].tolist() == pytest.approx([0.5, 1.0])
    assert set(frame["eligible_years"]) == {3}
    assert frame["results_authorized"].eq(False).all()


def test_direct_rank_frame_pools_numerators_and_denominators_across_years() -> None:
    dataset = _community_rows()
    mask = dataset["geography_id"].eq("01")
    dataset.loc[mask, "denominator"] = [100, 200, 300]
    dataset.loc[mask, "numerator"] = [10, 40, 90]
    dataset.loc[mask, "published_measure_value"] = [0.10, 0.20, 0.30]

    frame = build_direct_ehr_rank_frame(dataset, "chicago_community_area")

    pooled = frame.loc[frame["geography_id"].eq("01"), "ehr_percent"].item()
    assert pooled == pytest.approx(100 * 140 / 600)
    assert pooled != pytest.approx(20.0)


def test_direct_rank_frame_excludes_combined_diabetes_with_unequal_denominators() -> None:
    rows = []
    for year in ("2022", "2023", "2024"):
        for condition_id, denominator in (
            ("diabetes_with_complication", 100),
            ("diabetes_without_complication", 120),
        ):
            rows.append(
                {
                    "geography_type": "census_tract",
                    "geography_id": "t1",
                    "time_period": year,
                    "condition_id": condition_id,
                    "condition_family": "diabetes",
                    "numerator": 10,
                    "denominator": denominator,
                    "published_measure_value": 0.1,
                    "suppression_flag": False,
                    "disease_value_derivation": "direct_first_party_export_not_interpolated",
                }
            )

    frame = build_direct_ehr_rank_frame(pd.DataFrame(rows), "census_tract")

    assert frame.empty


def test_direct_consequence_rank_frame_counts_each_annual_denominator_once() -> None:
    frame = build_direct_consequence_rank_frame(_rows(), "census_tract")

    assert set(frame["mean_annual_source_denominator"]) == {100.0}
    assert frame["denominator_unit"].eq("mean_annual_source_denominator_not_unique_people").all()


def test_annual_direct_consequence_rank_frame_preserves_year_specific_denominator() -> None:
    frame = build_annual_direct_consequence_rank_frame(_rows(), "census_tract")

    assert len(frame) == 12
    assert set(frame["time_period"]) == {"2022", "2023", "2024"}
    assert set(frame["mean_annual_source_denominator"]) == {100.0}
    assert frame.groupby("time_period")["ehr_rank"].max().eq(1.0).all()


def test_cluster_bootstrap_seed_and_denominator_are_deterministic() -> None:
    frame = build_tract_percentile_concordance(
        _rows(), noncrossing_only=True, capture_cut_points=CUTS
    )
    one = cluster_bootstrap_concordance(frame, n_replicates=50)
    two = cluster_bootstrap_concordance(frame, n_replicates=50)
    pd.testing.assert_frame_equal(one, two)
    assert set(one["seed"]) == {20260715}
    assert set(one["cluster_unit"]) == {"community_area_id"}
    assert np.all(one["replicate_count"].eq(50))
    assert "gwet_ac1" in set(one["metric"])
    assert one["uncertainty"].eq("95% community-area cluster bootstrap interval").all()
    assert one["bootstrap_interval_method"].eq("percentile_2.5_97.5").all()
    assert one["bootstrap_rank_rule"].eq("recomputed_within_each_cluster_resample").all()


def test_capture_quartile_cuts_are_frozen_and_reused() -> None:
    values = pd.Series([0.1, 0.2, 0.3, 0.4])
    cuts = assign_capture_quartile(values)
    assert cuts["cut_points"] == pytest.approx((0.175, 0.25, 0.325))
    assert cuts["labels"].tolist() == ["Q1", "Q2", "Q3", "Q4"]


def test_frozen_capture_cut_points_are_identical_across_crossing_sensitivity() -> None:
    all_tracts = build_tract_percentile_concordance(
        _rows(), noncrossing_only=False, capture_cut_points=CUTS
    )
    noncrossing = build_tract_percentile_concordance(
        _rows(), noncrossing_only=True, capture_cut_points=CUTS
    )
    assert set(all_tracts["capture_quartile_cut_points"]) == {"0.075|0.125|0.175"}
    assert set(noncrossing["capture_quartile_cut_points"]) == {"0.075|0.125|0.175"}


def test_primary_concordance_excludes_incomplete_three_year_tracts() -> None:
    dataset = _rows()
    missing_public = (dataset["geography_id"].eq("t1")) & dataset["time_period"].eq("2023")
    dataset.loc[missing_public, "public_comparator_estimate"] = np.nan
    frame = build_tract_percentile_concordance(
        dataset, noncrossing_only=True, capture_cut_points=CUTS
    )
    assert "t1" not in set(frame["geography_id"])
    assert frame["eligible_annual_rows"].eq(3).all()
    assert frame["exposure_eligibility_status"].eq("complete_2022_2024").all()


def test_chm_only_tract_frame_does_not_require_places_completeness() -> None:
    dataset = _rows()
    dataset.loc[
        dataset["geography_id"].eq("t1") & dataset["time_period"].eq("2023"),
        "public_comparator_estimate",
    ] = np.nan
    frame = build_direct_tract_analysis_frame(dataset)
    assert set(frame["geography_id"]) == {"t1", "t2", "t4"}
    assert frame["analysis_population"].eq("chm_only_complete_2022_2024").all()
    assert frame.groupby("condition_id")["ehr_rank"].max().eq(1.0).all()


def test_gwet_ac1_is_one_for_perfect_quartile_agreement() -> None:
    assert gwet_ac1([0, 1, 2, 3], [0, 1, 2, 3]) == pytest.approx(1.0)


def test_discordance_high_not_high_requires_the_other_source_below_the_median() -> None:
    dataset = _rows()
    dataset.loc[dataset["geography_id"].eq("t2"), "public_comparator_estimate"] = 30.0
    frame = build_tract_percentile_concordance(
        dataset, noncrossing_only=True, capture_cut_points=CUTS
    )

    t2 = frame.loc[frame["geography_id"].eq("t2")].iloc[0]
    assert t2["discordance_category"] != "ehr_high_public_not_high"


def test_uncertainty_discordance_fails_closed_without_governed_intervals() -> None:
    result = propagate_uncertainty_discordance(
        pd.DataFrame(
            {
                "geography_id": ["t1"],
                "condition_id": ["hypertension"],
                "ehr_percent": [10.0],
                "public_comparator_estimate": [12.0],
            }
        )
    )
    assert result["analysis_id"] == "A5"
    assert result["status"] == "not_run_uncertainty_unavailable"
    assert result["results_authorized"] is False


def test_uncertainty_discordance_fails_closed_for_incompatible_metadata() -> None:
    frame = pd.DataFrame(
        {
            "geography_id": ["t1"],
            "condition_id": ["hypertension"],
            "ehr_percent": [10.0],
            "public_comparator_estimate": [12.0],
            "public_comparator_lower": [11.0],
            "public_comparator_upper": [13.0],
            "acs_moe": [1.0],
            "public_comparator_source_id": ["unknown"],
        }
    )
    result = propagate_uncertainty_discordance(frame)
    assert result["status"] == "not_run_incompatible_uncertainty_contract"


def test_uncertainty_discordance_success_path_is_seeded_and_governed() -> None:
    frame = pd.DataFrame(
        {
            "geography_id": ["t1", "t2"],
            "condition_id": ["hypertension"] * 2,
            "ehr_percent": [10.0, 20.0],
            "public_comparator_estimate": [11.0, 19.0],
            "public_comparator_lower": [9.0, 17.0],
            "public_comparator_upper": [13.0, 21.0],
            "acs_moe": [0.5, 0.5],
            "public_comparator_source_id": ["cdc_places"] * 2,
            "public_comparator_unit": ["percent"] * 2,
            "public_comparator_confidence_level": [0.95] * 2,
            "public_comparator_geography_vintage": ["2020_census_tract"] * 2,
            "acs_moe_source_id": ["us_census_acs"] * 2,
            "acs_moe_unit": ["percentage_points"] * 2,
            "acs_moe_confidence_level": [0.90] * 2,
            "acs_geography_vintage": ["2020_census_tract"] * 2,
        }
    )
    first = propagate_uncertainty_discordance(frame, n_replicates=20, seed=42)
    second = propagate_uncertainty_discordance(frame, n_replicates=20, seed=42)
    assert first == second
    assert first["status"] == "available_places_only_interval_propagation"
    assert first["condition_id"] == "hypertension"
    assert first["joint_uncertainty_status"] == "not_run_incompatible_uncertainty_contract"
    assert first["uncertainty_role"] == "public_comparator_rank_uncertainty"
    assert first["eligible_n"] == 2
    assert first["results_authorized"] is False

    changed_acs = frame.assign(acs_moe=[50.0, 75.0])
    assert propagate_uncertainty_discordance(changed_acs, n_replicates=20, seed=42) == first


@pytest.mark.parametrize(
    ("value", "expected"),
    [("(20.0, 30.0)", (20.0, 30.0)), ("20.0 - 30.0", (20.0, 30.0))],
)
def test_places_confidence_interval_parser_accepts_ordered_finite_bounds(
    value: str, expected: tuple[float, float]
) -> None:
    assert parse_places_confidence_interval(value) == expected


@pytest.mark.parametrize("value", ["", "30, 20", "not available", "(-1, 20)"])
def test_places_confidence_interval_parser_fails_closed(value: str) -> None:
    with pytest.raises(ValueError):
        parse_places_confidence_interval(value)


def test_variance_partition_recovers_between_and_within_share() -> None:
    frame = pd.DataFrame(
        {
            "geography_id": ["t1", "t2", "t3", "t4"],
            "community_area_id": ["a", "a", "b", "b"],
            "condition_id": ["hypertension"] * 4,
            "ehr_percent": [0.1, 0.3, 0.7, 0.9],
            "is_crossing_tract": [False] * 4,
        }
    )
    result = compute_variance_partition(frame)
    assert result["analysis_id"] == "A1"
    assert 0 < result["vpc_icc"] < 1
    assert result["eligible_n"] == 4
    assert result["estimator"] == "method_of_moments_one_way_random_effects"
    assert result["bootstrap_requested_replicates"] == 1000
    assert result["bootstrap_failed_replicates"] == 0
    assert result["bootstrap_estimator"] == "method_of_moments_cluster_resample"
    assert result["bootstrap_interval_method"] == "percentile_2.5_97.5"
    assert result["results_authorized"] is False


def test_discriminatory_accuracy_is_descriptive_area_label_auc() -> None:
    frame = pd.DataFrame(
        {
            "geography_id": ["t1", "t2", "t3", "t4"],
            "community_area_id": ["a", "a", "b", "b"],
            "condition_id": ["hypertension"] * 4,
            "ehr_percent": [0.1, 0.2, 0.8, 0.9],
        }
    )
    result = compute_discriminatory_accuracy(frame, threshold="75th_percentile")
    assert result["analysis_id"] == "A2"
    assert result["auc"] > 0.5
    assert result["estimator"] == "mann_whitney_leave_one_tract_out_area_mean"
    assert result["bootstrap_requested_replicates"] == 1000
    assert result["bootstrap_interval_method"] == "percentile_2.5_97.5"
    assert result["bootstrap_threshold_rule"] == "recomputed_within_each_cluster_resample"
    assert "predict" not in result["analysis_name"].lower()
    assert result["results_authorized"] is False


def test_geographic_consequences_reconcile_q4_states_and_source_denominators() -> None:
    tract = pd.DataFrame(
        {
            "geography_id": ["t1", "t2", "t3", "t4"],
            "condition_id": ["copd"] * 4,
            "ehr_rank": [0.9, 0.8, 0.2, 0.1],
            "mean_annual_source_denominator": [100.0, 200.0, 300.0, 400.0],
        }
    )
    coarse = pd.DataFrame(
        {
            "geography_id": ["a", "b"],
            "condition_id": ["copd", "copd"],
            "ehr_rank": [0.6, 0.9],
        }
    )
    linkage = pd.DataFrame(
        {
            "geography_id": ["t1", "t2", "t3", "t4"],
            "comparison_geography_id": ["a", "a", "b", "b"],
            "is_dominant": [True] * 4,
            "is_crossing_tract": [False, True, False, False],
        }
    )

    result = build_geographic_consequence_tables(
        tract,
        coarse,
        linkage,
        comparison_geography_type="zcta",
    )
    transitions = result["transitions"].set_index("transition_state")

    assert int(transitions.loc["moves_out_of_highest_quartile", "tract_count"]) == 2
    assert transitions.loc[
        "moves_out_of_highest_quartile", "mean_annual_source_denominator"
    ] == pytest.approx(300.0)
    assert int(transitions.loc["moves_into_highest_quartile", "tract_count"]) == 2
    assert int(transitions["tract_count"].sum()) == 4
    assert transitions["mean_annual_source_denominator"].sum() == pytest.approx(1000.0)
    assert result["details"]["results_authorized"].eq(False).all()


def test_mixed_extremes_and_noncrossing_sensitivity_are_explicit() -> None:
    tract = pd.DataFrame(
        {
            "geography_id": ["t1", "t2", "t3"],
            "condition_id": ["hypertension"] * 3,
            "ehr_rank": [0.9, 0.1, 0.5],
            "mean_annual_source_denominator": [100.0, 200.0, 300.0],
        }
    )
    coarse = pd.DataFrame(
        {"geography_id": ["a"], "condition_id": ["hypertension"], "ehr_rank": [0.75]}
    )
    linkage = pd.DataFrame(
        {
            "geography_id": ["t1", "t2", "t3"],
            "comparison_geography_id": ["a", "a", "a"],
            "is_dominant": [True, True, True],
            "is_crossing_tract": [False, False, True],
        }
    )

    all_result = build_geographic_consequence_tables(
        tract, coarse, linkage, comparison_geography_type="chicago_community_area"
    )
    noncrossing = build_geographic_consequence_tables(
        tract,
        coarse,
        linkage,
        comparison_geography_type="chicago_community_area",
        noncrossing_only=True,
    )

    mixed = all_result["mixed_extremes"].iloc[0]
    assert mixed["comparison_geography_id"] == "a"
    assert int(mixed["eligible_tract_count"]) == 3
    assert mixed["mean_annual_source_denominator"] == pytest.approx(600.0)
    assert len(noncrossing["details"]) == 2
    assert noncrossing["details"]["sensitivity_status"].eq("noncrossing_only").all()


def test_geographic_consequence_ranks_use_the_linked_analytic_population() -> None:
    tract = pd.DataFrame(
        {
            "geography_id": ["excluded", "t1", "t2"],
            "condition_id": ["copd"] * 3,
            "ehr_percent": [1.0, 2.0, 3.0],
            "ehr_rank": [1 / 3, 2 / 3, 1.0],
            "mean_annual_source_denominator": [100.0] * 3,
        }
    )
    coarse = pd.DataFrame(
        {"geography_id": ["a"], "condition_id": ["copd"], "ehr_rank": [1.0]}
    )
    linkage = pd.DataFrame(
        {
            "geography_id": ["excluded", "t1", "t2"],
            "comparison_geography_id": ["a", "a", "a"],
            "is_dominant": [False, True, True],
            "is_crossing_tract": [False, False, False],
        }
    )

    detail = build_geographic_consequence_tables(
        tract, coarse, linkage, comparison_geography_type="chicago_community_area"
    )["details"]

    assert detail.set_index("geography_id")["ehr_rank"].to_dict() == {"t1": 0.5, "t2": 1.0}


def test_annual_consequence_stability_uses_signed_state_and_two_of_three_rule() -> None:
    detail = pd.DataFrame(
        {
            "geography_id": ["t1"] * 3 + ["t2"] * 3,
            "condition_id": ["copd"] * 6,
            "time_period": ["2022", "2023", "2024"] * 2,
            "transition_state": [
                "moves_out_of_highest_quartile",
                "moves_out_of_highest_quartile",
                "remains_high",
                "remains_below_highest_quartile",
                "moves_into_highest_quartile",
                "remains_high",
            ],
            "tract_is_high": [True, True, True, False, False, True],
            "comparison_is_high": [False, False, True, False, True, True],
        }
    )

    stability = summarize_annual_consequence_stability(detail)
    persistence = stability["tract_persistence"].set_index("geography_id")

    assert persistence.loc["t1", "persistent_transition_state"] == ("moves_out_of_highest_quartile")
    assert bool(persistence.loc["t1", "meets_two_of_three_rule"])
    assert persistence.loc["t2", "persistent_transition_state"] == "unstable"
    assert stability["annual_jaccard"]["results_authorized"].eq(False).all()
