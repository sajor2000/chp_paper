from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from chicagohealthmap.analysis.case_studies import (
    CaseStudyAnalysisError,
    build_primary_community_frame,
)
from chicagohealthmap.analysis.sap_analyses import build_unadjusted_sensitivity_residuals
from chicagohealthmap.analysis.spatial import (
    CANONICALIZATION,
    CONSTRUCTION_METHOD,
    ISLAND_POLICY,
    TRANSFORMATION,
    SpatialWeights,
    _conditional_neighbor_lags,
    _requires_spatial_escalation,
    _weights_checksum,
    build_queen_weights,
    build_rook_weights,
    build_smallest_connected_distance_weights,
    build_topology_summary,
    build_spatial_error_sensitivity_table,
    classify_spatial_stability,
    compute_local_spatial_diagnostics,
    summarize_fdr_spatial_survival,
    evaluate_spatial_scan_feasibility,
    fit_spatial_error_sensitivity,
    permutation_moran,
)


def _polygon_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "geography_id": ["C", "A", "D", "B"],
            "geometry_wkt": [
                "POLYGON ((2 0, 3 0, 3 1, 2 1, 2 0))",
                "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))",
                "POLYGON ((1 1, 2 1, 2 2, 1 2, 1 1))",
                "POLYGON ((1 0, 2 0, 2 1, 1 1, 1 0))",
            ],
        }
    )


def _independent_moran(values: np.ndarray, matrix: np.ndarray) -> float:
    centered = values - values.mean()
    return float(
        len(values) / matrix.sum() * (centered @ matrix @ centered) / (centered @ centered)
    )


def test_spatial_error_sensitivity_returns_converged_finite_result() -> None:
    weights = build_queen_weights(_polygon_frame())
    outcome = pd.Series([1.0, 2.0, 3.0, 4.0], index=weights.geography_ids)
    design = np.column_stack([np.ones(4), np.arange(4, dtype=float)])

    result = fit_spatial_error_sensitivity(outcome, design, weights)

    assert result.converged is True
    assert np.isfinite(result.coefficients).all()
    assert np.isfinite(result.covariance).all()
    assert -0.99 < result.lambda_hat < 0.99
    assert result.weights_checksum == weights.checksum


def test_spatial_error_table_runs_only_crossed_moran_gates() -> None:
    weights = build_queen_weights(_polygon_frame())
    model_result = SimpleNamespace(
        outcome=pd.Series([1.0, 2.0, 3.0, 4.0], index=weights.geography_ids),
        design=np.column_stack([np.ones(4), np.arange(4, dtype=float), [0.0, 1.0, 0.0, 1.0]]),
        coefficients=pd.DataFrame({"term": ["alpha", "beta_h", "beta_d"]}),
        contrasts=pd.DataFrame(
            {
                "estimand_id": ["C1", "C1-H", "C1-D"],
                "estimate": [1.0, 0.5, 0.5],
            }
        ),
    )
    diagnostics = pd.DataFrame(
        {
            "model_id": ["C1", "C2"],
            "escalation_required": [True, False],
        }
    )

    table = build_spatial_error_sensitivity_table(
        {"C1": model_result, "C2": model_result},
        diagnostics,
        {"C1": weights, "C2": weights},
    )

    c1 = table.loc[table["model_id"].eq("C1")]
    c2 = table.loc[table["model_id"].eq("C2")]
    assert set(c1["spatial_error_status"]) == {"mandatory_spatial_sensitivity_run"}
    assert {"alpha", "beta_h", "beta_d", "C1", "C1-H", "C1-D"} <= set(c1["term"])
    contrasts = c1.loc[c1["row_type"].eq("spatial_error_contrast")]
    assert set(contrasts["analysis_status"]) == {"mandatory_spatial_sensitivity"}
    assert set(contrasts["results_authorized"]) == {False}
    assert set(contrasts["model_sensitivity_status"]) <= {
        "model-sensitive",
        "not_model_sensitive",
    }
    assert c2.iloc[0]["spatial_error_status"] == "not_run_no_escalation"


@pytest.mark.parametrize(
    ("ols", "spatial", "expected"),
    [
        (-1.0, -1.21, "model-sensitive"),
        (-1.0, 0.1, "model-sensitive"),
        (-1.0, -1.2, "not_model_sensitive"),
        (0.0, 0.0, "not_model_sensitive"),
    ],
)
def test_classify_spatial_stability_uses_signed_sap_threshold(
    ols: float, spatial: float, expected: str
) -> None:
    assert classify_spatial_stability(ols, spatial) == expected


def test_queen_weights_include_edge_and_point_neighbors_and_are_canonical() -> None:
    frame = _polygon_frame()

    weights = build_queen_weights(frame)
    reordered = build_queen_weights(frame.sample(frac=1, random_state=12))

    assert weights.geography_ids == ("A", "B", "C", "D")
    assert weights.neighbor_ids == (
        ("B", "D"),
        ("A", "C", "D"),
        ("B", "D"),
        ("A", "B", "C"),
    )
    assert weights.neighbor_indices == ((1, 3), (0, 2, 3), (1, 3), (0, 1, 2))
    assert np.array_equal(weights.binary_matrix, weights.binary_matrix.T)
    assert np.diag(weights.binary_matrix).tolist() == [0, 0, 0, 0]
    assert weights.matrix.sum(axis=1) == pytest.approx(np.ones(4))
    assert weights.matrix[0, 1] == pytest.approx(0.5)  # shared edge
    assert weights.matrix[0, 3] == pytest.approx(0.5)  # shared point
    assert weights.checksum == reordered.checksum
    assert np.array_equal(weights.matrix, reordered.matrix)
    assert weights.construction_method == "first_order_queen_contiguity"
    assert weights.transformation == "row_standardized"


def test_rook_excludes_point_contacts_and_is_deterministic() -> None:
    frame = _polygon_frame()

    weights = build_rook_weights(frame)
    reordered = build_rook_weights(frame.sample(frac=1, random_state=2))

    assert weights.neighbor_ids == (("B",), ("A", "C", "D"), ("B",), ("B",))
    assert weights.construction_method == "first_order_rook_contiguity"
    assert weights.checksum == reordered.checksum
    assert np.array_equal(weights.binary_matrix, weights.binary_matrix.T)


def test_distance_weights_use_smallest_observed_connected_threshold() -> None:
    frame = _polygon_frame()

    weights = build_smallest_connected_distance_weights(frame)
    summary = build_topology_summary({"distance": weights, "rook": build_rook_weights(frame)})

    assert weights.construction_method == "smallest_connected_centroid_distance_band"
    assert weights.distance_threshold == pytest.approx(1.0)
    assert weights.neighbor_ids == (("B",), ("A", "C", "D"), ("B",), ("B",))
    assert set(summary["topology_method"]) == {
        "first_order_rook_contiguity",
        "smallest_connected_centroid_distance_band",
    }
    assert summary["connected"].all()
    assert set(summary["island_count"]) == {0}
    assert summary["checksum"].str.fullmatch(r"[0-9a-f]{64}").all()


@pytest.mark.parametrize(
    ("frame", "message"),
    [
        (
            pd.DataFrame({"geography_id": ["A", "A"], "geometry_wkt": ["POINT (0 0)"] * 2}),
            "duplicate",
        ),
        (
            pd.DataFrame({"geography_id": ["A", None], "geometry_wkt": ["POINT (0 0)"] * 2}),
            "null geography",
        ),
        (pd.DataFrame({"geography_id": ["A"], "geometry_wkt": [None]}), "null WKT"),
        (pd.DataFrame({"geography_id": ["A"], "geometry_wkt": ["not wkt"]}), "malformed WKT"),
        (pd.DataFrame({"geography_id": ["A"], "geometry_wkt": ["POINT (0 0)"]}), "polygon"),
        (pd.DataFrame({"geography_id": ["A"], "geometry_wkt": ["POLYGON EMPTY"]}), "empty"),
        (
            pd.DataFrame(
                {
                    "geography_id": ["A"],
                    "geometry_wkt": ["POLYGON ((0 0, 2 2, 0 2, 2 0, 0 0))"],
                }
            ),
            "invalid",
        ),
        (
            pd.DataFrame(
                {
                    "geography_id": ["A"],
                    "geometry_wkt": ["POLYGON ((0 0, nan 0, 1 1, 0 1, 0 0))"],
                }
            ),
            "finite",
        ),
    ],
)
def test_queen_weights_reject_invalid_geometry_contracts(frame: pd.DataFrame, message: str) -> None:
    with pytest.raises(CaseStudyAnalysisError, match=message):
        build_queen_weights(frame)


def test_queen_weights_reject_missing_columns_and_islands() -> None:
    with pytest.raises(CaseStudyAnalysisError, match="missing columns"):
        build_queen_weights(pd.DataFrame({"geography_id": ["A"]}))
    islands = pd.DataFrame(
        {
            "geography_id": ["A", "B"],
            "geometry_wkt": [
                "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))",
                "POLYGON ((3 0, 4 0, 4 1, 3 1, 3 0))",
            ],
        }
    )
    with pytest.raises(CaseStudyAnalysisError, match="islands.*A.*B"):
        build_queen_weights(islands)


@pytest.mark.parametrize(
    "second_wkt",
    [
        "POLYGON ((0 0, 2 0, 2 2, 0 2, 0 0))",
        "POLYGON ((1 0, 3 0, 3 2, 1 2, 1 0))",
    ],
)
def test_queen_weights_reject_equal_or_overlapping_polygon_interiors(
    second_wkt: str,
) -> None:
    frame = pd.DataFrame(
        {
            "geography_id": ["A", "B", "C"],
            "geometry_wkt": [
                "POLYGON ((0 0, 2 0, 2 2, 0 2, 0 0))",
                second_wkt,
                "POLYGON ((0 2, 1 2, 1 3, 0 3, 0 2))",
            ],
        }
    )

    with pytest.raises(CaseStudyAnalysisError, match="interiors intersect.*A.*B"):
        build_queen_weights(frame)


def test_queen_weights_reject_nonfinite_z_but_accept_ordinary_2d() -> None:
    invalid = _polygon_frame()
    invalid.loc[invalid["geography_id"].eq("A"), "geometry_wkt"] = (
        "POLYGON Z ((0 0 1, 1 0 nan, 1 1 1, 0 1 1, 0 0 1))"
    )

    with pytest.raises(CaseStudyAnalysisError, match="nonfinite coordinates"):
        build_queen_weights(invalid)
    assert len(build_queen_weights(_polygon_frame()).geography_ids) == 4


def test_queen_weight_arrays_have_genuinely_immutable_backing() -> None:
    weights = build_queen_weights(_polygon_frame())
    matrix_before = weights.matrix.copy()
    binary_before = weights.binary_matrix.copy()

    for values in (weights.matrix, weights.binary_matrix):
        with pytest.raises(ValueError):
            values.setflags(write=True)
        with pytest.raises(ValueError):
            values[0, 0] = 1

    assert np.array_equal(weights.matrix, matrix_before)
    assert np.array_equal(weights.binary_matrix, binary_before)


def test_moran_matches_hand_calculation_and_exact_seeded_permutations() -> None:
    weights = build_queen_weights(_polygon_frame())
    values = np.array([1.0, 2.0, 4.0, 8.0])
    residuals = pd.Series(values, index=weights.geography_ids)
    permutations = 37
    seed = 654

    result = permutation_moran(residuals, weights, permutations=permutations, seed=seed)
    expected_i = -1 / 3
    observed = _independent_moran(values, weights.matrix)
    rng = np.random.default_rng(seed)
    permuted = np.array(
        [_independent_moran(rng.permutation(values), weights.matrix) for _ in range(permutations)]
    )
    extreme = int(np.sum(np.abs(permuted - expected_i) >= abs(observed - expected_i)))

    assert result.observed_i == pytest.approx(observed)
    assert result.observed_i == pytest.approx(-122 / 345)
    assert result.expected_i == pytest.approx(expected_i)
    assert result.permutation_p_value == pytest.approx((extreme + 1) / (permutations + 1))
    assert result.permutations == permutations
    assert result.seed == seed
    assert result.n == 4
    assert result.weights_checksum == weights.checksum
    assert result.permutation_rule == "two_sided_abs_deviation_from_expected_add_one"
    assert result.analysis_role == "supportive_sensitivity_not_primary"


def test_local_spatial_diagnostics_are_seeded_and_fdr_scoped() -> None:
    weights = build_queen_weights(_polygon_frame())
    values = pd.Series([1.0, 2.0, 4.0, 8.0], index=weights.geography_ids)
    comparator = pd.Series([1.5, 2.5, 3.5, 7.5], index=weights.geography_ids)
    first = compute_local_spatial_diagnostics(
        values, weights, comparator=comparator, permutations=19
    )
    second = compute_local_spatial_diagnostics(
        values, weights, comparator=comparator, permutations=19
    )
    pd.testing.assert_frame_equal(first, second)
    assert {"local_moran", "getis_ord_gi_star", "bivariate_lisa"} <= set(first["statistic_family"])
    assert first["p_adjusted"].dropna().between(0, 1).all()
    assert set(first["permutation_method"]) == {
        "conditional_focal_value_fixed_two_sided_centered"
    }
    assert first["results_authorized"].eq(False).all()
    assert first["fdr_family"].nunique() == 3


def test_conditional_local_permutations_exclude_the_focal_value() -> None:
    weights = build_queen_weights(_polygon_frame())
    values = np.array([100.0, 1.0, 2.0, 3.0])

    lags = _conditional_neighbor_lags(
        values, weights, permutations=50, rng=np.random.default_rng(9)
    )

    assert lags[:, 0].max() <= 3.0


def test_local_fdr_family_is_scoped_by_condition_period_and_statistic() -> None:
    weights = build_queen_weights(_polygon_frame())
    values = pd.Series([1.0, 2.0, 4.0, 8.0], index=weights.geography_ids)
    result = compute_local_spatial_diagnostics(
        values,
        weights,
        permutations=19,
        condition_id="copd",
        period="2024",
    )

    assert set(result["condition_id"]) == {"copd"}
    assert set(result["period"]) == {"2024"}
    assert set(result["fdr_family"]) == {
        "copd|2024|local_moran",
        "copd|2024|getis_ord_gi_star",
    }


def test_fdr_survival_summary_never_counts_raw_only_clusters_as_survivors() -> None:
    diagnostics = pd.DataFrame(
        {
            "condition_id": ["copd", "copd"],
            "period": ["2024", "2024"],
            "statistic_family": ["local_moran", "local_moran"],
            "geography_id": ["a", "b"],
            "cluster_label": ["high-high", "low-low"],
            "p_raw": [0.01, 0.03],
            "p_adjusted": [0.08, 0.04],
            "significant_fdr_05": [False, True],
            "weights_checksum": ["x", "x"],
            "seed": [1, 1],
            "permutations": [9999, 9999],
            "denominator": [2, 2],
            "results_authorized": [False, False],
        }
    )

    summary = summarize_fdr_spatial_survival(diagnostics).iloc[0]

    assert int(summary["raw_p_lt_05_count"]) == 2
    assert int(summary["fdr_surviving_count"]) == 1
    assert summary["fdr_surviving_geography_ids"] == "b"
    assert summary["results_authorized"] is False


def test_spatial_scan_fails_closed_without_count_population_contract() -> None:
    result = evaluate_spatial_scan_feasibility(pd.DataFrame({"geography_id": ["A"]}))
    assert result["status"] == "not_run_no_governed_scan_population"
    assert result["results_authorized"] is False


def test_moran_aligns_residual_ids_and_is_deterministic() -> None:
    weights = build_queen_weights(_polygon_frame())
    residuals = pd.Series([3.0, -2.0, 7.0, 1.0], index=["D", "B", "A", "C"])

    first = permutation_moran(residuals, weights, permutations=51, seed=98)
    second = permutation_moran(residuals.sort_index(), weights, permutations=51, seed=98)

    assert first == second


def test_moran_rejects_weights_with_inconsistent_neighbor_metadata() -> None:
    weights = build_queen_weights(_polygon_frame())
    invalid = replace(
        weights,
        neighbor_indices=((1,), *weights.neighbor_indices[1:]),
        neighbor_ids=(("B",), *weights.neighbor_ids[1:]),
    )
    residuals = pd.Series([1.0, 2.0, 3.0, 5.0], index=weights.geography_ids)

    with pytest.raises(CaseStudyAnalysisError, match="neighbor metadata"):
        permutation_moran(residuals, invalid, permutations=9)


def test_moran_rejects_checksum_consistent_disconnected_non_island_weights() -> None:
    geography_ids = ("A", "B", "C", "D")
    binary = np.array(
        [
            [0, 1, 0, 0],
            [1, 0, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ],
        dtype=np.uint8,
    )
    matrix = binary.astype(float)
    checksum = _weights_checksum(
        geography_ids,
        binary,
        matrix,
        construction_method=CONSTRUCTION_METHOD,
        transformation=TRANSFORMATION,
        island_policy=ISLAND_POLICY,
        canonicalization=CANONICALIZATION,
    )
    weights = SpatialWeights(
        geography_ids=geography_ids,
        matrix=matrix,
        binary_matrix=binary,
        neighbor_indices=((1,), (0,), (3,), (2,)),
        neighbor_ids=(("B",), ("A",), ("D",), ("C",)),
        checksum=checksum,
    )
    residuals = pd.Series([1.0, 2.0, 3.0, 4.0], index=geography_ids)

    with pytest.raises(CaseStudyAnalysisError, match="disconnected"):
        permutation_moran(residuals, weights, permutations=9)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("construction_method", "rook"),
        ("transformation", "binary"),
        ("island_policy", "repair"),
        ("canonicalization", "input_order"),
    ],
)
def test_moran_rejects_tampered_weight_metadata(field: str, value: str) -> None:
    weights = build_queen_weights(_polygon_frame())
    invalid = replace(weights, **{field: value})
    residuals = pd.Series([1.0, 2.0, 3.0, 5.0], index=weights.geography_ids)

    with pytest.raises(CaseStudyAnalysisError, match="metadata"):
        permutation_moran(residuals, invalid, permutations=9)


def test_moran_rejects_unsorted_weight_ids_and_tampered_checksum() -> None:
    weights = build_queen_weights(_polygon_frame())
    residuals = pd.Series([1.0, 2.0, 3.0, 5.0], index=weights.geography_ids)

    with pytest.raises(CaseStudyAnalysisError, match="lexicographically sorted"):
        permutation_moran(
            residuals,
            replace(weights, geography_ids=("B", "A", "C", "D")),
            permutations=9,
        )
    with pytest.raises(CaseStudyAnalysisError, match="checksum"):
        permutation_moran(
            residuals,
            replace(weights, checksum="0" * 64),
            permutations=9,
        )


@pytest.mark.parametrize(
    ("residuals", "message"),
    [
        (pd.Series([1.0, 2.0, 3.0], index=["A", "B", "C"]), "ID mismatch"),
        (pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=["A", "B", "C", "D", "E"]), "ID mismatch"),
        (pd.Series([1.0, 2.0, 3.0, 4.0], index=["A", "A", "C", "D"]), "duplicate"),
        (pd.Series([1.0, 2.0, np.nan, 4.0], index=["A", "B", "C", "D"]), "nonfinite"),
        (pd.Series([1.0, 2.0, np.inf, 4.0], index=["A", "B", "C", "D"]), "nonfinite"),
        (pd.Series([4.0, 4.0, 4.0, 4.0], index=["A", "B", "C", "D"]), "constant"),
        (pd.Series([1.0, 2.0, 3.0 + 2.0j, 4.0], index=["A", "B", "C", "D"]), "complex"),
        (pd.Series([1.0, 2.0, True, 4.0], index=["A", "B", "C", "D"]), "boolean"),
    ],
)
def test_moran_rejects_unusable_residuals(residuals: pd.Series, message: str) -> None:
    with pytest.raises(CaseStudyAnalysisError, match=message):
        permutation_moran(residuals, build_queen_weights(_polygon_frame()), permutations=9)


@pytest.mark.parametrize(("permutations", "seed"), [(0, 1), (-1, 1), (1.5, 1), (5, -1), (5, True)])
def test_moran_rejects_bad_run_configuration(permutations: object, seed: object) -> None:
    residuals = pd.Series([1.0, 2.0, 3.0, 5.0], index=["A", "B", "C", "D"])
    with pytest.raises(CaseStudyAnalysisError, match="permutations|seed"):
        permutation_moran(  # type: ignore[arg-type]
            residuals,
            build_queen_weights(_polygon_frame()),
            permutations=permutations,
            seed=seed,
        )


def test_spatial_escalation_uses_exact_sap_boundaries() -> None:
    assert _requires_spatial_escalation(0.10, 0.049999)
    assert _requires_spatial_escalation(-0.10, 0.049999)
    assert not _requires_spatial_escalation(np.nextafter(0.10, 0.0), 0.049999)
    assert not _requires_spatial_escalation(0.10, 0.05)


def test_frozen_full_topology_and_c2_eligible_sensitivity_smoke() -> None:
    root = Path(__file__).parents[3]
    analytic_path = root / "outputs/frozen/chicago_case_studies_analytic.parquet"
    geometry_path = root / "data/processed/public/chicago_community_areas_current.parquet"
    if not analytic_path.is_file() or not geometry_path.is_file():
        pytest.skip("local frozen data are intentionally untracked")

    dataset = pd.read_parquet(analytic_path)
    frame = build_primary_community_frame(dataset)
    geometry = pd.read_parquet(geometry_path)[["geography_id", "geometry_wkt"]]
    full_weights = build_queen_weights(geometry)
    residuals = build_unadjusted_sensitivity_residuals(frame, "C2")
    eligible_geometry = geometry.loc[geometry["geography_id"].astype(str).isin(residuals.index)]
    eligible_weights = build_queen_weights(eligible_geometry)
    result = permutation_moran(residuals, eligible_weights, permutations=99, seed=20260715)

    assert len(full_weights.geography_ids) == 77
    assert int(full_weights.binary_matrix.sum() / 2) == 197
    assert all(full_weights.neighbor_indices)
    assert full_weights.matrix.sum(axis=1) == pytest.approx(np.ones(77))
    assert (
        full_weights.checksum == "f1a9b8ade1bf4ed1258b54f97dd78a8c710dc51cc03350053c99df59b2de7922"
    )
    assert len(eligible_weights.geography_ids) == 76
    assert "76" not in eligible_weights.geography_ids
    assert int(eligible_weights.binary_matrix.sum() / 2) == 195
    assert all(eligible_weights.neighbor_indices)
    assert (
        eligible_weights.checksum
        == "927384844fbace67e43cd79a2aa757420e026cac1a063f7b4968b784c7e417b5"
    )
    assert result.n == 76
    assert result.analysis_role == "supportive_sensitivity_not_primary"
    assert residuals.attrs["model_id"] == "C2_unadjusted"
    assert residuals.attrs["primary_estimand_executed"] is False


def test_weight_metadata_constants_are_frozen() -> None:
    assert CONSTRUCTION_METHOD == "first_order_queen_contiguity"
    assert TRANSFORMATION == "row_standardized"
    assert ISLAND_POLICY == "fail_closed_no_neighbor_repair"
    assert CANONICALIZATION == "lexicographically_ordered_geography_ids"


@pytest.mark.parametrize(
    ("field", "changed_value"),
    [
        ("construction_method", "rook_contiguity"),
        ("transformation", "binary"),
        ("island_policy", "nearest_neighbor_repair"),
        ("canonicalization", "input_order"),
    ],
)
def test_checksum_binds_every_frozen_metadata_field(field: str, changed_value: str) -> None:
    weights = build_queen_weights(_polygon_frame())
    metadata = {
        "construction_method": CONSTRUCTION_METHOD,
        "transformation": TRANSFORMATION,
        "island_policy": ISLAND_POLICY,
        "canonicalization": CANONICALIZATION,
    }
    changed = {**metadata, field: changed_value}

    changed_checksum = _weights_checksum(
        weights.geography_ids,
        weights.binary_matrix,
        weights.matrix,
        **changed,
    )

    assert changed_checksum != weights.checksum
