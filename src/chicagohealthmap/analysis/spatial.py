"""Deterministic spatial diagnostics governed by the signed Chicago SAP."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from scipy import optimize  # type: ignore[import-untyped]
from shapely import get_coordinates, wkt  # type: ignore[import-untyped]
from shapely.errors import GEOSException  # type: ignore[import-untyped]
from shapely.geometry.base import BaseGeometry  # type: ignore[import-untyped]

from chicagohealthmap.analysis.case_studies import CaseStudyAnalysisError
from chicagohealthmap.analysis.contracts import A1_A7_ANALYSIS_NAMES

PERMUTATION_RULE = "two_sided_abs_deviation_from_expected_add_one"
SUPPORTIVE_ROLE = "supportive_sensitivity_not_primary"
CONSTRUCTION_METHOD = "first_order_queen_contiguity"
ROOK_CONSTRUCTION_METHOD = "first_order_rook_contiguity"
DISTANCE_CONSTRUCTION_METHOD = "smallest_connected_centroid_distance_band"
TRANSFORMATION = "row_standardized"
ISLAND_POLICY = "fail_closed_no_neighbor_repair"
CANONICALIZATION = "lexicographically_ordered_geography_ids"


@dataclass(frozen=True, eq=False)
class SpatialWeights:
    """Canonical first-order queen weights and their frozen run metadata."""

    geography_ids: tuple[str, ...]
    matrix: np.ndarray
    binary_matrix: np.ndarray
    neighbor_indices: tuple[tuple[int, ...], ...]
    neighbor_ids: tuple[tuple[str, ...], ...]
    checksum: str
    construction_method: str = CONSTRUCTION_METHOD
    transformation: str = TRANSFORMATION
    island_policy: str = ISLAND_POLICY
    canonicalization: str = CANONICALIZATION
    distance_threshold: float | None = None


@dataclass(frozen=True)
class MoranResult:
    """Observed Global Moran diagnostic and deterministic permutation metadata."""

    observed_i: float
    expected_i: float
    permutation_p_value: float
    permutations: int
    seed: int
    n: int
    weights_checksum: str
    escalation_required: bool
    analysis_role: str = SUPPORTIVE_ROLE
    permutation_rule: str = PERMUTATION_RULE
    weights_transformation: str = "row_standardized"


@dataclass(frozen=True)
class SpatialErrorResult:
    """Concentrated-likelihood spatial-error sensitivity result."""

    lambda_hat: float
    coefficients: np.ndarray
    covariance: np.ndarray
    log_likelihood: float
    converged: bool
    weights_checksum: str
    metadata: dict[str, object]


def fit_spatial_error_sensitivity(
    outcome: pd.Series,
    design: np.ndarray,
    weights: SpatialWeights,
) -> SpatialErrorResult:
    """Fit a bounded spatial-error sensitivity with the supplied OLS design."""

    _validate_weights(weights)
    if design.ndim != 2 or design.shape[0] != len(weights.geography_ids):
        raise CaseStudyAnalysisError("spatial-error design has invalid dimensions")
    if not np.isfinite(design).all():
        raise CaseStudyAnalysisError("spatial-error design has nonfinite values")
    residual_ids = tuple(str(value) for value in outcome.index)
    if residual_ids != weights.geography_ids:
        raise CaseStudyAnalysisError("spatial-error outcome IDs do not match weights")
    values = pd.to_numeric(outcome, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise CaseStudyAnalysisError("spatial-error outcome has nonfinite values")

    identity = np.eye(len(values))
    degrees_of_freedom = len(values) - design.shape[1]
    if degrees_of_freedom <= 0:
        raise CaseStudyAnalysisError("spatial-error design has no residual degrees of freedom")

    def solve(lambda_value: float) -> tuple[float, np.ndarray, np.ndarray, float] | None:
        transform = identity - lambda_value * weights.matrix
        sign, logdet = np.linalg.slogdet(transform)
        if sign <= 0 or not np.isfinite(logdet):
            return None
        transformed_design = transform @ design
        transformed_outcome = transform @ values
        crossproduct = transformed_design.T @ transformed_design
        if np.linalg.matrix_rank(crossproduct) < crossproduct.shape[0]:
            return None
        try:
            inverse = np.linalg.inv(crossproduct)
        except np.linalg.LinAlgError:
            return None
        beta = inverse @ transformed_design.T @ transformed_outcome
        residual = transformed_outcome - transformed_design @ beta
        residual_sum_squares = float(residual @ residual)
        sigma_squared_ml = residual_sum_squares / len(values)
        if sigma_squared_ml <= 0 or not np.isfinite(sigma_squared_ml):
            return None
        log_likelihood = float(
            -0.5 * len(values) * (np.log(2 * np.pi * sigma_squared_ml) + 1) + logdet
        )
        covariance = (residual_sum_squares / degrees_of_freedom) * inverse
        return log_likelihood, beta, covariance, float(lambda_value)

    def objective(lambda_value: float) -> float:
        candidate = solve(float(lambda_value))
        return np.inf if candidate is None else -candidate[0]

    optimized = optimize.minimize_scalar(
        objective,
        bounds=(-0.98, 0.98),
        method="bounded",
        options={"xatol": 1e-8, "maxiter": 500},
    )
    best = solve(float(optimized.x)) if optimized.success else None
    if best is None or abs(float(optimized.x)) >= 0.979999:
        raise CaseStudyAnalysisError("spatial-error sensitivity did not converge")
    best_log_likelihood, beta, covariance, best_lambda = best
    if not np.isfinite(beta).all() or not np.isfinite(covariance).all():
        raise CaseStudyAnalysisError("spatial-error sensitivity has nonfinite estimates")
    return SpatialErrorResult(
        lambda_hat=float(best_lambda),
        coefficients=beta,
        covariance=covariance,
        log_likelihood=float(best_log_likelihood),
        converged=True,
        weights_checksum=weights.checksum,
        metadata={
            "estimator": "concentrated_likelihood_spatial_error",
            "lambda_search": "bounded_scalar_optimization_-0.98_to_0.98",
            "optimizer_success": bool(optimized.success),
            "analysis_status": "mandatory_spatial_sensitivity",
            "results_authorized": False,
        },
    )


def build_spatial_error_sensitivity_table(
    primary_results: Mapping[str, Any],
    spatial_diagnostics: pd.DataFrame,
    weights_by_model: Mapping[str, SpatialWeights],
) -> pd.DataFrame:
    """Run mandatory spatial-error sensitivities and emit a tidy governed table."""

    records: list[dict[str, object]] = []
    for diagnostic in spatial_diagnostics.sort_values("model_id", kind="mergesort").to_dict(
        "records"
    ):
        model_id = str(diagnostic["model_id"])
        weights = weights_by_model[model_id]
        model_result = primary_results[model_id]
        if bool(diagnostic["escalation_required"]):
            records.extend(_spatial_error_coefficient_records(model_id, model_result, weights))
            records.extend(_spatial_error_contrast_records(model_id, model_result, weights))
        else:
            records.append(_spatial_error_no_escalation_record(model_id, weights))
    return pd.DataFrame.from_records(records)


def classify_spatial_stability(ols_estimate: float, spatial_estimate: float) -> str:
    """Classify the SAP spatial-error comparison without changing the primary estimator."""

    if not np.isfinite([ols_estimate, spatial_estimate]).all():
        raise CaseStudyAnalysisError("spatial stability estimates must be finite")
    if np.sign(ols_estimate) != np.sign(spatial_estimate):
        return "model-sensitive"
    if abs(ols_estimate) == 0:
        return "model-sensitive" if abs(spatial_estimate) > 0 else "not_model_sensitive"
    magnitude_change = abs(abs(spatial_estimate) - abs(ols_estimate)) / abs(ols_estimate)
    if magnitude_change > 0.20 and not np.isclose(magnitude_change, 0.20):
        return "model-sensitive"
    return "not_model_sensitive"


def _spatial_error_coefficient_records(
    model_id: str, model_result: Any, weights: SpatialWeights
) -> list[dict[str, object]]:
    outcome, design = _aligned_spatial_error_inputs(model_result, weights)
    sensitivity = fit_spatial_error_sensitivity(outcome, design, weights)
    terms = list(model_result.coefficients["term"])
    if len(terms) != len(sensitivity.coefficients):
        raise CaseStudyAnalysisError("spatial-error coefficient terms do not match adjusted design")
    standard_errors = np.sqrt(np.diag(sensitivity.covariance))
    return [
        {
            "model_id": model_id,
            "term": term,
            "row_type": "spatial_error_coefficient",
            "spatial_error_status": "mandatory_spatial_sensitivity_run",
            "moran_escalation_required": True,
            "lambda_hat": sensitivity.lambda_hat,
            "estimate": float(estimate),
            "standard_error": float(standard_error),
            "log_likelihood": sensitivity.log_likelihood,
            "converged": sensitivity.converged,
            "weights_checksum": sensitivity.weights_checksum,
            **sensitivity.metadata,
        }
        for term, estimate, standard_error in zip(
            terms, sensitivity.coefficients, standard_errors, strict=True
        )
    ]


def _spatial_error_contrast_records(
    model_id: str, model_result: Any, weights: SpatialWeights
) -> list[dict[str, object]]:
    outcome, design = _aligned_spatial_error_inputs(model_result, weights)
    sensitivity = fit_spatial_error_sensitivity(outcome, design, weights)
    term_positions = {term: index for index, term in enumerate(model_result.coefficients["term"])}
    ols_contrasts = model_result.contrasts.set_index("estimand_id")
    records: list[dict[str, object]] = []
    for estimand_id, contrast in _spatial_contrast_vectors(model_id, term_positions).items():
        spatial_estimate = float(contrast @ sensitivity.coefficients)
        spatial_variance = float(contrast @ sensitivity.covariance @ contrast)
        if spatial_variance < 0 or not np.isfinite(spatial_variance):
            raise CaseStudyAnalysisError("spatial-error contrast covariance is not estimable")
        ols_estimate = float(ols_contrasts.loc[estimand_id, "estimate"])
        records.append(
            {
                "model_id": model_id,
                "term": estimand_id,
                "row_type": "spatial_error_contrast",
                "spatial_error_status": "mandatory_spatial_sensitivity_run",
                "moran_escalation_required": True,
                "lambda_hat": sensitivity.lambda_hat,
                "estimate": spatial_estimate,
                "standard_error": float(np.sqrt(spatial_variance)),
                "log_likelihood": sensitivity.log_likelihood,
                "converged": sensitivity.converged,
                "weights_checksum": sensitivity.weights_checksum,
                "ols_estimate": ols_estimate,
                "absolute_magnitude_change_ratio": _magnitude_change_ratio(
                    ols_estimate, spatial_estimate
                ),
                "direction_changed": bool(np.sign(ols_estimate) != np.sign(spatial_estimate)),
                "model_sensitivity_status": classify_spatial_stability(
                    ols_estimate, spatial_estimate
                ),
                **sensitivity.metadata,
            }
        )
    return records


def _spatial_contrast_vectors(
    model_id: str, term_positions: Mapping[str, int]
) -> dict[str, np.ndarray]:
    output: dict[str, np.ndarray] = {}
    if model_id == "C1":
        for estimand_id, terms in {
            "C1": ("beta_h", "beta_d"),
            "C1-H": ("beta_h",),
            "C1-D": ("beta_d",),
        }.items():
            vector = np.zeros(len(term_positions), dtype=float)
            for term in terms:
                vector[term_positions[term]] = 1.0
            output[estimand_id] = vector
        return output
    if model_id == "C2":
        vector = np.zeros(len(term_positions), dtype=float)
        vector[term_positions["beta_c"]] = 1.0
        return {"C2": vector}
    raise CaseStudyAnalysisError(f"unsupported spatial-error model_id: {model_id}")


def _magnitude_change_ratio(ols_estimate: float, spatial_estimate: float) -> float:
    if not np.isfinite([ols_estimate, spatial_estimate]).all():
        raise CaseStudyAnalysisError("spatial stability estimates must be finite")
    if abs(ols_estimate) == 0:
        return np.inf if abs(spatial_estimate) > 0 else 0.0
    return float(abs(abs(spatial_estimate) - abs(ols_estimate)) / abs(ols_estimate))


def _spatial_error_no_escalation_record(
    model_id: str, weights: SpatialWeights
) -> dict[str, object]:
    return {
        "model_id": model_id,
        "term": "not_applicable",
        "row_type": "spatial_error_not_run",
        "spatial_error_status": "not_run_no_escalation",
        "moran_escalation_required": False,
        "lambda_hat": pd.NA,
        "estimate": pd.NA,
        "standard_error": pd.NA,
        "log_likelihood": pd.NA,
        "converged": pd.NA,
        "weights_checksum": weights.checksum,
        "estimator": "not_applicable",
        "lambda_search": "not_applicable",
        "analysis_status": "not_run_no_escalation",
        "model_sensitivity_status": "not_applicable",
        "results_authorized": False,
    }


def _aligned_spatial_error_inputs(
    model_result: Any, weights: SpatialWeights
) -> tuple[pd.Series, np.ndarray]:
    outcome = model_result.outcome
    design = model_result.design
    if tuple(outcome.index.astype(str)) == weights.geography_ids:
        return outcome, design
    source_index = pd.Index(outcome.index.astype(str))
    order = source_index.get_indexer(weights.geography_ids)
    if (order < 0).any():
        raise CaseStudyAnalysisError(
            "spatial-error model population does not match adjusted model output"
        )
    aligned_outcome = outcome.iloc[order].copy()
    aligned_outcome.index = weights.geography_ids
    return aligned_outcome, design[order, :]


def build_queen_weights(frame: pd.DataFrame) -> SpatialWeights:
    """Build canonical row-standardized queen weights without repairing islands."""

    geography_ids, geometries = _canonical_spatial_geometries(frame)
    n = len(geography_ids)
    binary = np.zeros((n, n), dtype=np.uint8)
    for left in range(n):
        for right in range(left + 1, n):
            try:
                if geometries[left].relate_pattern(geometries[right], "T********"):
                    raise CaseStudyAnalysisError(
                        "distinct geometry interiors intersect for geography IDs "
                        f"{geography_ids[left]} and {geography_ids[right]}"
                    )
                if geometries[left].touches(geometries[right]):
                    binary[left, right] = 1
                    binary[right, left] = 1
            except GEOSException as exc:
                raise CaseStudyAnalysisError(
                    "queen topology comparison failed for geography IDs "
                    f"{geography_ids[left]} and {geography_ids[right]}"
                ) from exc

    return _spatial_weights_from_binary(
        geography_ids, binary, construction_method=CONSTRUCTION_METHOD
    )


def build_rook_weights(frame: pd.DataFrame) -> SpatialWeights:
    """Build deterministic rook contiguity and fail closed on islands."""

    geography_ids, geometries = _canonical_spatial_geometries(frame)
    n = len(geography_ids)
    binary = np.zeros((n, n), dtype=np.uint8)
    for left in range(n):
        for right in range(left + 1, n):
            try:
                if geometries[left].relate_pattern(geometries[right], "T********"):
                    raise CaseStudyAnalysisError(
                        "distinct geometry interiors intersect for geography IDs "
                        f"{geography_ids[left]} and {geography_ids[right]}"
                    )
                shared_boundary = geometries[left].boundary.intersection(geometries[right].boundary)
                if geometries[left].touches(geometries[right]) and shared_boundary.length > 0:
                    binary[left, right] = 1
                    binary[right, left] = 1
            except GEOSException as exc:
                raise CaseStudyAnalysisError(
                    "rook topology comparison failed for geography IDs "
                    f"{geography_ids[left]} and {geography_ids[right]}"
                ) from exc
    return _spatial_weights_from_binary(
        geography_ids, binary, construction_method=ROOK_CONSTRUCTION_METHOD
    )


def build_smallest_connected_distance_weights(frame: pd.DataFrame) -> SpatialWeights:
    """Build the smallest observed centroid-distance band yielding one connected graph."""

    geography_ids, geometries = _canonical_spatial_geometries(frame)
    centroids = np.asarray([[geometry.centroid.x, geometry.centroid.y] for geometry in geometries])
    deltas = centroids[:, None, :] - centroids[None, :, :]
    distances = np.sqrt(np.sum(deltas * deltas, axis=2))
    if not np.isfinite(distances).all():
        raise CaseStudyAnalysisError("centroid distances contain nonfinite values")
    observed = np.unique(distances[np.triu_indices(len(geography_ids), 1)])
    threshold: float | None = None
    binary: np.ndarray | None = None
    for candidate in observed:
        candidate_binary = ((distances <= candidate) & (distances > 0)).astype(np.uint8)
        if _binary_graph_connected(candidate_binary):
            threshold = float(candidate)
            binary = candidate_binary
            break
    if threshold is None or binary is None:
        raise CaseStudyAnalysisError("distance-band topology is disconnected")
    return _spatial_weights_from_binary(
        geography_ids,
        binary,
        construction_method=DISTANCE_CONSTRUCTION_METHOD,
        distance_threshold=threshold,
    )


def build_topology_summary(weights_by_name: Mapping[str, SpatialWeights]) -> pd.DataFrame:
    """Summarize deterministic topology, connectivity, neighbors, and checksums."""

    records: list[dict[str, object]] = []
    for name, weights in sorted(weights_by_name.items()):
        _validate_weights(weights)
        counts = weights.binary_matrix.sum(axis=1).astype(int)
        records.append(
            {
                "weights_definition": name,
                "topology_method": weights.construction_method,
                "distance_threshold": weights.distance_threshold,
                "connected": _binary_graph_connected(weights.binary_matrix),
                "island_count": int(np.sum(counts == 0)),
                "area_count": len(weights.geography_ids),
                "edge_count": int(weights.binary_matrix.sum() // 2),
                "neighbor_min": int(counts.min()),
                "neighbor_median": float(np.median(counts)),
                "neighbor_max": int(counts.max()),
                "checksum": weights.checksum,
                "transformation": weights.transformation,
                "analysis_status": "governed_alternative_spatial_weights",
                "authorization_status": "results_not_authorized",
                "results_authorized": False,
            }
        )
    return pd.DataFrame.from_records(records)


def _canonical_spatial_geometries(
    frame: pd.DataFrame,
) -> tuple[tuple[str, ...], tuple[BaseGeometry, ...]]:
    required = {"geography_id", "geometry_wkt"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"spatial geometry frame is missing columns: {missing}")
    if frame.empty:
        raise CaseStudyAnalysisError("spatial geometry frame is empty")
    if frame["geography_id"].isna().any():
        raise CaseStudyAnalysisError("spatial geometry frame has null geography IDs")
    if frame["geometry_wkt"].isna().any():
        raise CaseStudyAnalysisError("spatial geometry frame has null WKT")
    working = frame[["geography_id", "geometry_wkt"]].copy()
    working["geography_id"] = working["geography_id"].astype(str)
    if working["geography_id"].str.strip().eq("").any():
        raise CaseStudyAnalysisError("spatial geometry frame has blank geography IDs")
    duplicates = sorted(
        working.loc[working["geography_id"].duplicated(False), "geography_id"].unique()
    )
    if duplicates:
        raise CaseStudyAnalysisError(
            f"spatial geometry frame has duplicate geography IDs: {duplicates}"
        )
    working = working.sort_values("geography_id", kind="mergesort").reset_index(drop=True)
    geography_ids = tuple(working["geography_id"])
    geometries = tuple(
        _validated_geometry(geography_id, geometry_text)
        for geography_id, geometry_text in working.itertuples(index=False, name=None)
    )
    return geography_ids, geometries


def _binary_graph_connected(binary: np.ndarray) -> bool:
    if binary.ndim != 2 or binary.shape[0] != binary.shape[1] or len(binary) == 0:
        return False
    visited = {0}
    frontier = [0]
    while frontier:
        node = frontier.pop()
        for neighbor in np.flatnonzero(binary[node]):
            neighbor_int = int(neighbor)
            if neighbor_int not in visited:
                visited.add(neighbor_int)
                frontier.append(neighbor_int)
    return len(visited) == len(binary)


def _spatial_weights_from_binary(
    geography_ids: tuple[str, ...],
    binary: np.ndarray,
    *,
    construction_method: str,
    distance_threshold: float | None = None,
) -> SpatialWeights:
    if not np.array_equal(binary, binary.T):
        raise CaseStudyAnalysisError("spatial binary weights are not symmetric")
    neighbor_indices = tuple(tuple(np.flatnonzero(row).tolist()) for row in binary)
    islands = [
        geography_ids[index] for index, neighbors in enumerate(neighbor_indices) if not neighbors
    ]
    if islands:
        raise CaseStudyAnalysisError(f"{construction_method} weights have islands: {islands}")
    if not _binary_graph_connected(binary):
        raise CaseStudyAnalysisError(f"{construction_method} weights graph is disconnected")
    row_counts = binary.sum(axis=1, dtype=float)
    matrix = binary.astype(float) / row_counts[:, None]
    neighbor_ids = tuple(
        tuple(geography_ids[index] for index in indices) for indices in neighbor_indices
    )
    checksum = _weights_checksum(
        geography_ids,
        binary,
        matrix,
        construction_method=construction_method,
        transformation=TRANSFORMATION,
        island_policy=ISLAND_POLICY,
        canonicalization=CANONICALIZATION,
        distance_threshold=distance_threshold,
    )
    return SpatialWeights(
        geography_ids=geography_ids,
        matrix=_immutable_array(matrix),
        binary_matrix=_immutable_array(binary),
        neighbor_indices=neighbor_indices,
        neighbor_ids=neighbor_ids,
        checksum=checksum,
        construction_method=construction_method,
        distance_threshold=distance_threshold,
    )


def permutation_moran(
    residuals: pd.Series,
    weights: SpatialWeights,
    permutations: int = 9999,
    seed: int = 20260715,
) -> MoranResult:
    """Calculate Global Moran's I and its exact governed permutation diagnostic."""

    _validate_run_configuration(permutations, seed)
    _validate_weights(weights)
    if residuals.index.has_duplicates:
        raise CaseStudyAnalysisError("Moran residual IDs contain duplicates")
    residual_ids = tuple(str(value) for value in residuals.index)
    if len(set(residual_ids)) != len(residual_ids):
        raise CaseStudyAnalysisError("Moran residual IDs contain duplicates after normalization")
    expected_ids = set(weights.geography_ids)
    actual_ids = set(residual_ids)
    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        raise CaseStudyAnalysisError(
            f"Moran residual ID mismatch: missing={missing}, extra={extra}"
        )

    values_by_id = pd.Series(residuals.to_numpy(), index=residual_ids)
    raw_values = values_by_id.to_numpy()
    if np.iscomplexobj(raw_values):
        raise CaseStudyAnalysisError("Moran residuals contain complex values")
    if values_by_id.map(lambda value: isinstance(value, (bool, np.bool_))).any():
        raise CaseStudyAnalysisError("Moran residuals contain boolean values")
    numeric = pd.to_numeric(values_by_id.loc[list(weights.geography_ids)], errors="coerce")
    values = numeric.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise CaseStudyAnalysisError("Moran residuals contain missing or nonfinite values")
    centered = values - values.mean()
    denominator = float(centered @ centered)
    if denominator <= 0 or not np.isfinite(denominator):
        raise CaseStudyAnalysisError("Moran residuals are constant")

    observed = _moran_i(centered, weights.matrix)
    expected = -1.0 / (len(values) - 1)
    rng = np.random.default_rng(seed)
    permutation_statistics = np.array(
        [_moran_i(rng.permutation(centered), weights.matrix) for _ in range(permutations)]
    )
    threshold = abs(observed - expected)
    extreme = int(np.sum(np.abs(permutation_statistics - expected) >= threshold))
    p_value = (extreme + 1) / (permutations + 1)
    return MoranResult(
        observed_i=observed,
        expected_i=expected,
        permutation_p_value=p_value,
        permutations=permutations,
        seed=seed,
        n=len(values),
        weights_checksum=weights.checksum,
        escalation_required=_requires_spatial_escalation(observed, p_value),
    )


def _benjamini_hochberg(values: np.ndarray) -> np.ndarray:
    """Adjust a named local-test family while retaining the raw p values."""

    if values.size == 0:
        return values.copy()
    order = np.argsort(values, kind="mergesort")
    adjusted = np.empty(values.size, dtype=float)
    running = 1.0
    for rank in range(values.size, 0, -1):
        position = order[rank - 1]
        running = min(running, float(values[position]) * values.size / rank)
        adjusted[position] = running
    return np.clip(adjusted, 0.0, 1.0)


def _aligned_spatial_values(values: pd.Series, weights: SpatialWeights) -> np.ndarray:
    if values.index.has_duplicates:
        raise CaseStudyAnalysisError("local spatial values contain duplicate geography IDs")
    normalized = pd.Series(values.to_numpy(), index=values.index.astype(str))
    if set(normalized.index) != set(weights.geography_ids):
        raise CaseStudyAnalysisError("local spatial values do not match weights geography IDs")
    numeric = pd.to_numeric(normalized.loc[list(weights.geography_ids)], errors="coerce")
    output = numeric.to_numpy(dtype=float)
    if not np.isfinite(output).all() or np.isclose(output.std(ddof=0), 0):
        raise CaseStudyAnalysisError("local spatial values are missing, nonfinite, or constant")
    return (output - output.mean()) / output.std(ddof=0)


def _conditional_neighbor_lags(
    values: np.ndarray,
    weights: SpatialWeights,
    permutations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Permute neighbors while freezing each focal observation."""

    output = np.empty((permutations, len(values)), dtype=float)
    indices = np.arange(len(values))
    for focal in range(len(values)):
        neighbors = np.flatnonzero(weights.binary_matrix[focal])
        pool = values[indices != focal]
        neighbor_weights = weights.matrix[focal, neighbors]
        for row in range(permutations):
            sampled = rng.choice(pool, size=len(neighbors), replace=False)
            output[row, focal] = float(neighbor_weights @ sampled)
    return output


def _conditional_gi_star(
    z: np.ndarray,
    weights: SpatialWeights,
    permutations: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Return standard Gi* z scores and focal-value-frozen permutations."""

    binary_self = weights.binary_matrix.astype(float) + np.eye(len(z))
    weight_sum = binary_self.sum(axis=1)
    denominator = np.sqrt(
        (len(z) * np.square(binary_self).sum(axis=1) - np.square(weight_sum))
        / (len(z) - 1)
    )
    valid = denominator > 0
    observed = np.full(len(z), np.nan, dtype=float)
    observed[valid] = (binary_self @ z)[valid] / denominator[valid]
    permuted = np.full((permutations, len(z)), np.nan, dtype=float)
    indices = np.arange(len(z))
    for focal in range(len(z)):
        if not valid[focal]:
            continue
        neighbor_count = int(weights.binary_matrix[focal].sum())
        pool = z[indices != focal]
        for row in range(permutations):
            sampled = rng.choice(pool, size=neighbor_count, replace=False)
            permuted[row, focal] = float((z[focal] + sampled.sum()) / denominator[focal])
    return observed, permuted


def compute_local_spatial_diagnostics(
    values: pd.Series,
    weights: SpatialWeights,
    *,
    comparator: pd.Series | None = None,
    permutations: int = 999,
    seed: int = 20260715,
    condition_id: str = "unspecified",
    period: str = "unspecified",
) -> pd.DataFrame:
    """Compute deterministic local Moran, Gi*, and optional bivariate LISA rows."""

    _validate_run_configuration(permutations, seed)
    _validate_weights(weights)
    z = _aligned_spatial_values(values, weights)
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []

    def add_family(
        family: str, observed: np.ndarray, permuted: np.ndarray, labels: list[str]
    ) -> None:
        estimable = np.isfinite(observed) & np.isfinite(permuted).all(axis=0)
        permutation_center = np.full(len(observed), np.nan, dtype=float)
        permutation_center[estimable] = permuted[:, estimable].mean(axis=0)
        raw = np.full(len(observed), np.nan, dtype=float)
        raw[estimable] = (
            np.sum(
                np.abs(permuted[:, estimable] - permutation_center[estimable])
                >= np.abs(observed[estimable] - permutation_center[estimable]),
                axis=0,
            )
            + 1
        ) / (permutations + 1)
        adjusted = np.full(len(observed), np.nan, dtype=float)
        adjusted[estimable] = _benjamini_hochberg(raw[estimable])
        for index, geography_id in enumerate(weights.geography_ids):
            rows.append(
                {
                    "analysis_id": "A7",
                    "analysis_name": A1_A7_ANALYSIS_NAMES["A7"],
                    "condition_id": condition_id,
                    "period": period,
                    "statistic_family": family,
                    "geography_id": geography_id,
                    "statistic": float(observed[index]) if estimable[index] else np.nan,
                    "p_raw": float(raw[index]),
                    "p_adjusted": float(adjusted[index]),
                    "fdr_family": f"{condition_id}|{period}|{family}",
                    "cluster_label": labels[index] if estimable[index] else "not_estimable",
                    "raw_significant_05": bool(raw[index] < 0.05) if estimable[index] else False,
                    "significant_fdr_05": (
                        bool(adjusted[index] < 0.05) if estimable[index] else False
                    ),
                    "weights_checksum": weights.checksum,
                    "seed": int(seed),
                    "permutations": int(permutations),
                    "permutation_method": "conditional_focal_value_fixed_two_sided_centered",
                    "denominator": len(weights.geography_ids),
                    "diagnostic_status": (
                        "eligible_local_cluster_diagnostic"
                        if estimable[index]
                        else "not_estimable_full_neighborhood"
                    ),
                    "sensitivity_status": "queen_weights_primary",
                    "source_artifact": "direct_chm_spatial_frame",
                    "results_authorized": False,
                }
            )

    local = z * (weights.matrix @ z)
    local_permuted = z * _conditional_neighbor_lags(z, weights, permutations, rng)
    local_labels = []
    lag = weights.matrix @ z
    for own, neighbor in zip(z, lag, strict=True):
        local_labels.append(
            "high-high"
            if own > 0 and neighbor > 0
            else "low-low"
            if own < 0 and neighbor < 0
            else "high-low"
            if own > 0
            else "low-high"
            if neighbor > 0
            else "not_classified"
        )
    add_family("local_moran", local, local_permuted, local_labels)

    gi, gi_permuted = _conditional_gi_star(z, weights, permutations, rng)
    gi_labels = ["high" if value > 0 else "low" for value in np.nan_to_num(gi)]
    add_family("getis_ord_gi_star", gi, gi_permuted, gi_labels)

    if comparator is not None:
        comparator_z = _aligned_spatial_values(comparator, weights)
        bivariate = z * (weights.matrix @ comparator_z)
        bivariate_permuted = z * _conditional_neighbor_lags(
            comparator_z, weights, permutations, rng
        )
        bivariate_lag = weights.matrix @ comparator_z
        bivariate_labels = []
        for own, neighbor in zip(z, bivariate_lag, strict=True):
            bivariate_labels.append(
                "high-high"
                if own > 0 and neighbor > 0
                else "low-low"
                if own < 0 and neighbor < 0
                else "high-low"
                if own > 0
                else "low-high"
                if neighbor > 0
                else "not_classified"
            )
        add_family("bivariate_lisa", bivariate, bivariate_permuted, bivariate_labels)
    output = pd.DataFrame.from_records(rows)
    output["results_authorized"] = pd.Series(False, index=output.index, dtype=object)
    return output


def summarize_fdr_spatial_survival(diagnostics: pd.DataFrame) -> pd.DataFrame:
    """Count raw local signals separately from BH-FDR surviving classifications."""

    required = {
        "condition_id",
        "period",
        "statistic_family",
        "geography_id",
        "cluster_label",
        "p_raw",
        "p_adjusted",
        "significant_fdr_05",
        "weights_checksum",
        "seed",
        "permutations",
        "denominator",
        "results_authorized",
    }
    missing = sorted(required - set(diagnostics.columns))
    if missing:
        raise CaseStudyAnalysisError(f"spatial survival diagnostics are missing: {missing}")
    if diagnostics["results_authorized"].astype(bool).any():
        raise CaseStudyAnalysisError("spatial survival inputs must remain unauthorized")
    records: list[dict[str, object]] = []
    grouping = ["condition_id", "period", "statistic_family"]
    for keys, group in diagnostics.groupby(grouping, sort=True):
        condition, period, family = keys
        survivors = group.loc[group["significant_fdr_05"].astype(bool)].copy()
        records.append(
            {
                "condition_id": str(condition),
                "period": str(period),
                "statistic_family": str(family),
                "eligible_tract_count": int(len(group)),
                "raw_p_lt_05_count": int(pd.to_numeric(group["p_raw"]).lt(0.05).sum()),
                "fdr_surviving_count": int(len(survivors)),
                "fdr_surviving_geography_ids": "|".join(
                    sorted(survivors["geography_id"].astype(str))
                ),
                "fdr_surviving_labels": "|".join(
                    sorted(
                        f"{row.geography_id}:{row.cluster_label}" for row in survivors.itertuples()
                    )
                ),
                "weights_checksum": str(group["weights_checksum"].iloc[0]),
                "seed": int(group["seed"].iloc[0]),
                "permutations": int(group["permutations"].iloc[0]),
                "denominator": int(group["denominator"].iloc[0]),
                "multiplicity_rule": "benjamini_hochberg_within_condition_period_statistic",
                "interpretation_boundary": "zero_survivors_does_not_prove_no_spatial_clustering",
                "results_authorized": False,
            }
        )
    output = pd.DataFrame.from_records(records)
    output["results_authorized"] = pd.Series(False, index=output.index, dtype=object)
    return output


def evaluate_spatial_scan_feasibility(frame: pd.DataFrame) -> dict[str, object]:
    """Return a fail-closed scan status unless count/population inputs are governed."""

    has_inputs = {"geography_id", "case_count", "population"}.issubset(frame.columns)
    status = (
        "not_run_scan_backend_unavailable" if has_inputs else "not_run_no_governed_scan_population"
    )
    return {
        "analysis_id": "A7",
        "analysis_name": A1_A7_ANALYSIS_NAMES["A7"],
        "estimand": "spatial scan cluster evidence",
        "unit": "geography-level cluster",
        "denominator": int(len(frame)),
        "period": "governed scan inputs supplied by caller",
        "uncertainty": "scan-specific Monte-Carlo significance not run",
        "diagnostic_status": status,
        "sensitivity_status": "supplement_feasibility_gate",
        "source_artifact": "governed_count_population_frame",
        "results_authorized": False,
        "status": status,
        "software_provenance": "no external scan backend invoked",
    }


def _validated_geometry(geography_id: str, geometry_text: object) -> BaseGeometry:
    if not isinstance(geometry_text, str):
        raise CaseStudyAnalysisError(f"geometry {geography_id} has malformed WKT")
    try:
        geometry = wkt.loads(geometry_text)
    except (GEOSException, ValueError, TypeError) as exc:
        raise CaseStudyAnalysisError(f"geometry {geography_id} has malformed WKT") from exc
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise CaseStudyAnalysisError(f"geometry {geography_id} is not a polygon or multipolygon")
    if geometry.is_empty:
        raise CaseStudyAnalysisError(f"geometry {geography_id} is empty")
    coordinates = get_coordinates(geometry, include_z=True, include_m=True)
    if coordinates.size == 0 or not np.isfinite(coordinates[:, :2]).all():
        raise CaseStudyAnalysisError(f"geometry {geography_id} has nonfinite coordinates")
    if geometry.has_z and not np.isfinite(coordinates[:, 2]).all():
        raise CaseStudyAnalysisError(f"geometry {geography_id} has nonfinite coordinates")
    if geometry.has_m and not np.isfinite(coordinates[:, 3]).all():
        raise CaseStudyAnalysisError(f"geometry {geography_id} has nonfinite coordinates")
    if not geometry.is_valid:
        raise CaseStudyAnalysisError(f"geometry {geography_id} is invalid")
    return geometry


def _moran_i(centered: np.ndarray, matrix: np.ndarray) -> float:
    denominator = float(centered @ centered)
    statistic = (
        len(centered) / float(matrix.sum()) * float(centered @ matrix @ centered) / denominator
    )
    if not np.isfinite(statistic):
        raise CaseStudyAnalysisError("Moran statistic is not finite")
    return statistic


def _weights_checksum(
    geography_ids: tuple[str, ...],
    binary: np.ndarray,
    matrix: np.ndarray,
    *,
    construction_method: str,
    transformation: str,
    island_policy: str,
    canonicalization: str,
    distance_threshold: float | None = None,
) -> str:
    canonical = {
        "geography_ids": geography_ids,
        "binary_matrix": binary.astype(int).tolist(),
        "row_standardized_matrix": matrix.tolist(),
        "construction_method": construction_method,
        "transformation": transformation,
        "island_policy": island_policy,
        "canonicalization": canonicalization,
    }
    if distance_threshold is not None:
        canonical["distance_threshold"] = distance_threshold
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _validate_weights(weights: SpatialWeights) -> None:
    n = len(weights.geography_ids)
    if n < 2 or len(set(weights.geography_ids)) != n:
        raise CaseStudyAnalysisError("spatial weights have invalid geography IDs")
    if weights.geography_ids != tuple(sorted(weights.geography_ids)):
        raise CaseStudyAnalysisError(
            "spatial weight geography IDs are not lexicographically sorted"
        )
    allowed_methods = {
        CONSTRUCTION_METHOD,
        ROOK_CONSTRUCTION_METHOD,
        DISTANCE_CONSTRUCTION_METHOD,
    }
    if (
        weights.construction_method not in allowed_methods
        or weights.transformation != TRANSFORMATION
        or weights.island_policy != ISLAND_POLICY
        or weights.canonicalization != CANONICALIZATION
    ):
        raise CaseStudyAnalysisError("spatial weights metadata does not match the frozen contract")
    if weights.construction_method == DISTANCE_CONSTRUCTION_METHOD:
        if weights.distance_threshold is None or not np.isfinite(weights.distance_threshold):
            raise CaseStudyAnalysisError("distance weights have invalid threshold metadata")
    elif weights.distance_threshold is not None:
        raise CaseStudyAnalysisError("non-distance weights unexpectedly define a threshold")
    if weights.matrix.shape != (n, n) or weights.binary_matrix.shape != (n, n):
        raise CaseStudyAnalysisError("spatial weights matrices have invalid dimensions")
    if not np.isfinite(weights.matrix).all() or np.any(weights.matrix < 0):
        raise CaseStudyAnalysisError("spatial weights matrix has invalid values")
    if not np.array_equal(weights.binary_matrix, weights.binary_matrix.T):
        raise CaseStudyAnalysisError("spatial binary weights are not symmetric")
    if not np.isin(weights.binary_matrix, (0, 1)).all():
        raise CaseStudyAnalysisError("spatial binary weights contain nonbinary values")
    if np.any(np.diag(weights.matrix)) or np.any(np.diag(weights.binary_matrix)):
        raise CaseStudyAnalysisError("spatial weights diagonal is not zero")
    if not np.allclose(weights.matrix.sum(axis=1), 1.0, rtol=0, atol=1e-12):
        raise CaseStudyAnalysisError("spatial weights are not row standardized")
    if any(not neighbors for neighbors in weights.neighbor_indices):
        raise CaseStudyAnalysisError("spatial weights contain islands")
    if not _binary_graph_connected(weights.binary_matrix):
        raise CaseStudyAnalysisError("spatial weights graph is disconnected")
    expected_indices = tuple(tuple(np.flatnonzero(row).tolist()) for row in weights.binary_matrix)
    expected_ids = tuple(
        tuple(weights.geography_ids[index] for index in indices) for indices in expected_indices
    )
    if weights.neighbor_indices != expected_indices or weights.neighbor_ids != expected_ids:
        raise CaseStudyAnalysisError("spatial weights neighbor metadata is inconsistent")
    expected_matrix = (
        weights.binary_matrix.astype(float)
        / weights.binary_matrix.sum(axis=1, dtype=float)[:, None]
    )
    if not np.allclose(weights.matrix, expected_matrix, rtol=0, atol=1e-15):
        raise CaseStudyAnalysisError("spatial standardized weights do not match binary weights")
    checksum = _weights_checksum(
        weights.geography_ids,
        weights.binary_matrix,
        weights.matrix,
        construction_method=weights.construction_method,
        transformation=weights.transformation,
        island_policy=weights.island_policy,
        canonicalization=weights.canonicalization,
        distance_threshold=weights.distance_threshold,
    )
    if checksum != weights.checksum:
        raise CaseStudyAnalysisError("spatial weights checksum does not match their structure")


def _validate_run_configuration(permutations: int, seed: int) -> None:
    if isinstance(permutations, bool) or not isinstance(permutations, int) or permutations < 1:
        raise CaseStudyAnalysisError("Moran permutations must be an integer of at least 1")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise CaseStudyAnalysisError("Moran seed must be a nonnegative integer")


def _requires_spatial_escalation(observed_i: float, p_value: float) -> bool:
    return abs(observed_i) >= 0.10 and p_value < 0.05


def _immutable_array(values: np.ndarray) -> np.ndarray:
    data = values.tobytes(order="C")
    return np.frombuffer(data, dtype=values.dtype).reshape(values.shape)
