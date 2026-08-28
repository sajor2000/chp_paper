"""Build the frozen Chicago case-study analytic dataset."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from shapely import from_wkb, from_wkt  # type: ignore[import-untyped]
from shapely.ops import unary_union  # type: ignore[import-untyped]

from chicagohealthmap.analysis.dataset_artifacts import (
    ASSEMBLY_MANIFEST_SCHEMA_VERSION,
    AnalyticDatasetArtifacts,
    AnalyticDatasetError,
    DatasetBuildDecision,
    artifact_paths as _artifact_paths,
    sha256_file as _sha256_file,
    source_inputs_match as _source_inputs_match,
    source_join_contract as _source_join_contract,
    validated_output_stem as _validated_output_stem,
)
from chicagohealthmap.analysis.raw_data_contract import (
    CONTRACT_PATH as RAW_DATA_CONTRACT_PATH,
    assert_primary_tract_contract,
)

DATASET_ID = "chicago_case_studies_analytic"
FIRST_PARTY_SNAPSHOT = Path("sources/first_party/capricorn/snapshots/2026-05-27")
FIRST_PARTY_ORIGINAL = FIRST_PARTY_SNAPSHOT / "original"
COMMUNITY_FACT_TABLE = "fact_community_area_condition_stats.text"
TRACT_FACT_TABLE = "fact_tract_condition_stats.text"
COMMUNITY_DIM_TABLE = "dim_community_areas.text"
COMMUNITY_RELIABILITY_TABLE = "dim_community_area_reliability_crosswalk.text"
TRACT_RELIABILITY_TABLE = "dim_tract_reliability_crosswalk.text"
ZCTA_DATASET_ID = "chicago_healthmap_zcta_sidecar"
ZCTA_FACT_TABLE = "fact_zcta_condition_stats.text"
ZCTA_DIM_TABLE = "dim_zcta.text"
ZCTA_RELIABILITY_TABLE = "dim_zcta_reliability_crosswalk.text"
ZCTA_INPUTS = (
    FIRST_PARTY_ORIGINAL / ZCTA_FACT_TABLE,
    FIRST_PARTY_ORIGINAL / ZCTA_DIM_TABLE,
    FIRST_PARTY_ORIGINAL / ZCTA_RELIABILITY_TABLE,
    FIRST_PARTY_SNAPSHOT / "manifest.json",
)
FIRST_PARTY_INPUTS = (
    FIRST_PARTY_ORIGINAL / COMMUNITY_FACT_TABLE,
    FIRST_PARTY_ORIGINAL / TRACT_FACT_TABLE,
    FIRST_PARTY_ORIGINAL / COMMUNITY_DIM_TABLE,
    FIRST_PARTY_ORIGINAL / COMMUNITY_RELIABILITY_TABLE,
    FIRST_PARTY_ORIGINAL / TRACT_RELIABILITY_TABLE,
    FIRST_PARTY_SNAPSHOT / "manifest.json",
)


def _read_pipe(path: Path, expected_fields: int) -> list[list[str]]:
    if not path.is_file():
        raise AnalyticDatasetError(f"required first-party table is missing: {path}")
    rows: list[list[str]] = []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.reader(handle, delimiter="|"):
            if not row or not any(value.strip() for value in row):
                continue
            if len(row) != expected_fields:
                raise AnalyticDatasetError(
                    f"{path.name} expected {expected_fields} fields, observed {len(row)}"
                )
            rows.append([value.strip() for value in row])
    return rows


def _text(row: list[str], position: int) -> str | None:
    value = row[position - 1].strip()
    return value or None


def _number(value: str | None) -> float | None:
    if value is None:
        return None
    normalized = value.replace(",", "").strip()
    if normalized in {"", "N/A", "NA", "<10"}:
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def _integer(value: str | None) -> int | None:
    number = _number(value)
    if number is None:
        return None
    return int(number)


def _condition_id(label: str) -> str:
    return label.strip().lower().replace(" ", "_")


def _condition_family(condition_id: str) -> str:
    if condition_id.startswith("diabetes_"):
        return "diabetes"
    return condition_id


def _community_area_id(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.startswith("1714000-"):
        text = text.rsplit("-", maxsplit=1)[-1]
    try:
        number = int(float(text))
    except ValueError:
        return text.zfill(2) if text.isdigit() else text
    return f"{number:02d}"


def _case_id(condition_id: str) -> str | None:
    if condition_id in {
        "hypertension",
        "diabetes_with_complication",
        "diabetes_without_complication",
    }:
        return "cardiometabolic_bundle"
    if condition_id == "copd":
        return "respiratory_copd"
    return None


def _community_dimension(root: Path) -> pd.DataFrame:
    rows = _read_pipe(root / FIRST_PARTY_ORIGINAL / COMMUNITY_DIM_TABLE, 17)
    records = [
        {
            "geography_id": _community_area_id(_text(row, 1)),
            "geography_name_source": _text(row, 2),
        }
        for row in rows
    ]
    return pd.DataFrame.from_records(records).drop_duplicates("geography_id")


def _community_reliability(root: Path) -> pd.DataFrame:
    return _reliability_crosswalk(root, COMMUNITY_RELIABILITY_TABLE)


def _tract_reliability(root: Path) -> pd.DataFrame:
    return _reliability_crosswalk(root, TRACT_RELIABILITY_TABLE)


def _zcta_id(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.zfill(5) if text.isdigit() else text


def _zcta_dimension(root: Path) -> pd.DataFrame:
    rows = _read_pipe(root / FIRST_PARTY_ORIGINAL / ZCTA_DIM_TABLE, 16)
    records: list[dict[str, Any]] = []
    for row in rows:
        geography_id = _zcta_id(_text(row, 1))
        geometry_hex = _text(row, 15)
        if geography_id is None or geometry_hex is None:
            raise AnalyticDatasetError("ZCTA dimension has a missing key or geometry")
        try:
            geometry = from_wkb(bytes.fromhex(geometry_hex))
        except (ValueError, TypeError) as error:
            raise AnalyticDatasetError(f"ZCTA {geography_id} geometry is invalid EWKB") from error
        if (
            geometry.is_empty
            or not geometry.is_valid
            or geometry.geom_type
            not in {
                "Polygon",
                "MultiPolygon",
            }
        ):
            raise AnalyticDatasetError(f"ZCTA {geography_id} geometry is not a valid polygon")
        records.append(
            {
                "geography_id": geography_id,
                "geography_name_source": _text(row, 2),
                "geometry_wkt": geometry.wkt,
            }
        )
    output = pd.DataFrame.from_records(records)
    if output["geography_id"].duplicated().any():
        raise AnalyticDatasetError("ZCTA dimension geography keys must be unique")
    return output


def _zcta_reliability(root: Path) -> pd.DataFrame:
    output = _reliability_crosswalk(root, ZCTA_RELIABILITY_TABLE)
    output["geography_id"] = output["geography_id"].map(_zcta_id)
    if output["geography_id"].duplicated().any():
        raise AnalyticDatasetError("ZCTA reliability geography keys must be unique")
    return output


def _reliability_crosswalk(root: Path, table: str) -> pd.DataFrame:
    rows = _read_pipe(root / FIRST_PARTY_ORIGINAL / table, 7)
    is_community = table == COMMUNITY_RELIABILITY_TABLE
    records = [
        {
            "geography_id": _community_area_id(_text(row, 1)) if is_community else _text(row, 1),
            "capture_rate": _number(_text(row, 2)),
            "reliability_tier": _text(row, 3),
            "equity_alignment_label": _text(row, 4),
            "combined_reliability_label": _text(row, 5),
            "public_reliability_description": _text(row, 6),
        }
        for row in rows
    ]
    return pd.DataFrame.from_records(records).drop_duplicates("geography_id")


def _optional_parquet(root: Path, relative: str) -> pd.DataFrame:
    path = root / relative
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_parquet(path)


def _community_geometry(root: Path) -> pd.DataFrame:
    data = _optional_parquet(root, "data/processed/public/chicago_community_areas_current.parquet")
    required = {"geography_id", "community_area_name", "geometry_wkt"}
    if data.empty or not required.issubset(data.columns):
        return pd.DataFrame(columns=["geography_id", "community_area_name", "geometry_wkt"])
    output = data[list(required)].copy()
    output["geography_id"] = output["geography_id"].map(_community_area_id)
    return output.drop_duplicates("geography_id")


def _community_covariates(root: Path, expected_ids: set[str]) -> pd.DataFrame:
    path = root / "data/processed/public/census_acs_2024_community_area_covariates.parquet"
    if not path.is_file():
        raise AnalyticDatasetError(f"required Census community covariates are missing: {path}")
    data = pd.read_parquet(path)
    measures = {
        "total_population",
        "pct_female",
        "pct_age_65_plus",
        "pct_below_fpl",
        "acs_adult_population",
    }
    uncertainty = {
        f"{measure}_{suffix}"
        for measure in ("pct_female", "pct_age_65_plus", "pct_below_fpl", "acs_adult_population")
        for suffix in ("standard_error", "moe90")
    }
    provenance = {
        "uncertainty_status",
        "source_id",
        "time_period",
        "release_vintage",
        "allocation_method",
        "allocation_weight_source",
        "poverty_universe",
        "boundary_snapshot_id",
        "boundary_release_vintage",
    }
    required = {"community_area_id"} | measures | uncertainty | provenance
    missing = sorted(required - set(data.columns))
    if missing:
        raise AnalyticDatasetError(
            f"Census community covariates lack required fields: {', '.join(missing)}"
        )
    output = data[list(required)].copy()
    output["community_area_id"] = output["community_area_id"].map(_community_area_id)
    identifiers = set(output["community_area_id"].astype(str))
    if output["community_area_id"].duplicated().any() or identifiers != expected_ids:
        raise AnalyticDatasetError(
            "Census community covariate IDs must exactly match the primary community frame"
        )
    numeric = output[list(measures | uncertainty)].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise AnalyticDatasetError("Census community covariates contain missing numeric values")
    output[list(measures | uncertainty)] = numeric
    return output.rename(
        columns={
            "total_population": "acs_total_population",
            "uncertainty_status": "census_covariate_uncertainty_status",
            "source_id": "census_covariate_source_id",
            "time_period": "census_covariate_time_period",
            "release_vintage": "census_covariate_release_vintage",
            "allocation_method": "census_covariate_allocation_method",
            "allocation_weight_source": "census_covariate_allocation_weight_source",
            "poverty_universe": "census_covariate_poverty_universe",
            "boundary_snapshot_id": "census_covariate_boundary_snapshot_id",
            "boundary_release_vintage": "census_covariate_boundary_release_vintage",
        }
    )


def _tract_geometry(root: Path) -> pd.DataFrame:
    data = _optional_parquet(root, "data/processed/public/census_tiger_2024_tract.parquet")
    required = {"geography_id", "geometry_wkt"}
    if data.empty or not required.issubset(data.columns):
        return pd.DataFrame(columns=["geography_id", "geometry_wkt"])
    columns = ["geography_id", "geometry_wkt"]
    output = data[columns].astype({"geography_id": "string"}).drop_duplicates("geography_id")
    return output


def _tract_city_membership(root: Path) -> pd.DataFrame:
    """Classify Cook County tracts using the frozen Chicago polygon union."""

    tracts = _optional_parquet(root, "data/processed/public/census_tiger_2024_tract.parquet")
    communities = _optional_parquet(
        root, "data/processed/public/chicago_community_areas_current.parquet"
    )
    required_tract = {"geography_id", "geometry_wkt"}
    required_community = {"geography_id", "geometry_wkt"}
    if tracts.empty or not required_tract.issubset(tracts.columns):
        raise AnalyticDatasetError("tract city membership requires the frozen 2024 tract geometry")
    if communities.empty or not required_community.issubset(communities.columns):
        raise AnalyticDatasetError(
            "tract city membership requires the frozen Chicago community-area geometry"
        )
    try:
        city = unary_union([from_wkt(value) for value in communities["geometry_wkt"]])
    except (TypeError, ValueError) as error:
        raise AnalyticDatasetError("Chicago community-area geometry cannot form a city union") from error
    if city.is_empty or not city.is_valid:
        raise AnalyticDatasetError("Chicago city geometry union is empty or invalid")

    records: list[dict[str, Any]] = []
    for row in tracts[["geography_id", "geometry_wkt"]].itertuples(index=False):
        geography_id = str(row.geography_id)
        try:
            geometry = from_wkt(row.geometry_wkt)
        except (TypeError, ValueError) as error:
            raise AnalyticDatasetError(
                f"tract {geography_id} has invalid frozen geometry"
            ) from error
        if geometry.is_empty or not geometry.is_valid:
            raise AnalyticDatasetError(f"tract {geography_id} geometry is empty or invalid")
        point_in_city = bool(city.covers(geometry.representative_point()))
        records.append(
            {
                "geography_id": geography_id,
                "city_inclusion_primary_eligible": point_in_city,
                "city_inclusion_primary_rule": (
                    "2024_tract_representative_point_covered_by_frozen_chicago_union"
                ),
                "city_inclusion_geometry_vintage": "2024 TIGER tract; frozen Chicago boundary",
            }
        )
    output = pd.DataFrame.from_records(records)
    if output["geography_id"].duplicated().any():
        raise AnalyticDatasetError("tract city-membership geography keys must be unique")
    return output


def _tract_community_overlay(root: Path) -> pd.DataFrame:
    data = _optional_parquet(root, "data/processed/public/tract_community_overlay_2024.parquet")
    required = {
        "geography_id",
        "community_area_id",
        "weight",
        "covered_fraction",
        "is_crossing_tract",
        "is_sliver",
    }
    optional = {
        "source_id",
        "snapshot_id",
        "boundary_source_id",
        "boundary_snapshot_id",
        "tract_vintage",
    }
    if data.empty or not required.issubset(data.columns):
        return pd.DataFrame(
            columns=[
                "geography_id",
                "community_area_id",
                "community_area_ids",
                "community_area_weights_json",
                "max_community_area_weight",
                "covered_fraction",
                "is_crossing_tract",
                "is_sliver",
                "overlay_row_count",
                "tract_community_linkage_source_id",
                "tract_community_linkage_snapshot_id",
                "community_area_boundary_source_id",
                "community_area_boundary_snapshot_id",
                "tract_community_linkage_method",
                "tract_community_linkage_role",
                "disease_value_derivation",
                "tract_vintage",
            ]
        )
    data = data[list(required | (optional & set(data.columns)))].copy()
    data["geography_id"] = data["geography_id"].astype("string")
    data["community_area_id"] = data["community_area_id"].map(_community_area_id)
    data["weight"] = pd.to_numeric(data["weight"], errors="coerce")
    data["covered_fraction"] = pd.to_numeric(data["covered_fraction"], errors="coerce")
    data = data.sort_values(
        ["geography_id", "weight", "community_area_id"], ascending=[True, False, True]
    )
    records: list[dict[str, Any]] = []
    for geography_id, group in data.groupby("geography_id", sort=True):
        weights = {
            str(row.community_area_id): float(row.weight)
            for row in group.itertuples()
            if pd.notna(row.weight)
        }
        records.append(
            {
                "geography_id": str(geography_id),
                "community_area_id": str(group.iloc[0]["community_area_id"]),
                "community_area_ids": ";".join(group["community_area_id"].astype(str).tolist()),
                "community_area_weights_json": json.dumps(weights, sort_keys=True),
                "max_community_area_weight": (
                    float(group["weight"].max()) if group["weight"].notna().any() else None
                ),
                "covered_fraction": (
                    float(group["covered_fraction"].max())
                    if group["covered_fraction"].notna().any()
                    else None
                ),
                "is_crossing_tract": bool(group["is_crossing_tract"].fillna(False).any()),
                "is_sliver": bool(group["is_sliver"].fillna(False).any()),
                "overlay_row_count": int(len(group)),
                "tract_community_linkage_source_id": _first_group_value(
                    group, "source_id", "tract_community_overlay_2024"
                ),
                "tract_community_linkage_snapshot_id": _first_group_value(
                    group, "snapshot_id", "tract_community_overlay_2024"
                ),
                "community_area_boundary_source_id": _first_group_value(
                    group, "boundary_source_id", "chicago_community_areas_current"
                ),
                "community_area_boundary_snapshot_id": _first_group_value(
                    group, "boundary_snapshot_id", "chicago_community_areas_current"
                ),
                "tract_community_linkage_method": "projected_polygon_intersection_area_weight",
                "tract_community_linkage_role": (
                    "geographic_linkage_metadata_only_not_disease_interpolation"
                ),
                "disease_value_derivation": "direct_first_party_export_not_interpolated",
                "tract_vintage": _first_group_value(group, "tract_vintage", "2024"),
            }
        )
    return pd.DataFrame.from_records(records)


def _first_group_value(group: pd.DataFrame, column: str, default: str) -> str:
    if column not in group.columns:
        return default
    values = group[column].dropna().astype(str)
    if values.empty:
        return default
    return values.iloc[0]


def _health_atlas_measure(root: Path, relative: str, prefix: str) -> pd.DataFrame:
    data = _optional_parquet(root, relative)
    required = {"geography_id", "time_period", "estimate", "standard_error"}
    if data.empty or not required.issubset(data.columns):
        return pd.DataFrame(columns=["geography_id", f"{prefix}_time_period"])
    renamed = data.rename(
        columns={
            "time_period": f"{prefix}_time_period",
            "estimate": f"{prefix}_estimate",
            "standard_error": f"{prefix}_standard_error",
        }
    )
    renamed["geography_id"] = renamed["geography_id"].map(_community_area_id)
    return renamed[
        [
            "geography_id",
            f"{prefix}_time_period",
            f"{prefix}_estimate",
            f"{prefix}_standard_error",
        ]
    ].drop_duplicates(["geography_id", f"{prefix}_time_period"])


def _latest_period_by_geography(data: pd.DataFrame, period_column: str) -> pd.DataFrame:
    if data.empty:
        return data
    ordered = data.assign(_period_sort=data[period_column].astype("string"))
    ordered = ordered.sort_values(["geography_id", "_period_sort"])
    return ordered.drop_duplicates("geography_id", keep="last").drop(columns="_period_sort")


def _places_measure_id(condition_id: str) -> str | None:
    if condition_id == "hypertension":
        return "bphigh_crudeprev"
    if condition_id.startswith("diabetes_"):
        return "diabetes_crudeprev"
    if condition_id == "copd":
        return "copd_crudeprev"
    return None


def _places_comparators(root: Path) -> pd.DataFrame:
    data = _optional_parquet(root, "data/processed/public/cdc_places_current_tract.parquet")
    required = {
        "geography_id",
        "time_period",
        "measure_id",
        "measure_type",
        "model_based_estimate",
        "confidence_interval",
    }
    columns = [
        "geography_id",
        "public_comparator_measure_id",
        "public_comparator_time_period",
        "public_comparator_measure_type",
        "public_comparator_estimate",
        "public_comparator_confidence_interval",
    ]
    if data.empty or not required.issubset(data.columns):
        return pd.DataFrame(columns=columns)
    renamed = data.rename(
        columns={
            "measure_id": "public_comparator_measure_id",
            "time_period": "public_comparator_time_period",
            "measure_type": "public_comparator_measure_type",
            "model_based_estimate": "public_comparator_estimate",
            "confidence_interval": "public_comparator_confidence_interval",
        }
    )
    renamed["geography_id"] = renamed["geography_id"].astype("string")
    return renamed[columns].drop_duplicates(["geography_id", "public_comparator_measure_id"])


def _suppression_reason(numerator: int | None, measure: float | None) -> str | None:
    if numerator is None or measure is None:
        return "source_measure_unavailable"
    if numerator == 0:
        return "zero_or_suppressed_unresolved"
    if 0 < numerator < 10:
        return "positive_below_public_suppression_threshold"
    return None


def _case_fact_records(
    root: Path,
    source_id: str,
    snapshot_id: str,
    table: str,
    geography_type: str,
    geography_level_role: str,
) -> pd.DataFrame:
    rows = _read_pipe(root / FIRST_PARTY_ORIGINAL / table, 67)
    records: list[dict[str, Any]] = []
    for row in rows:
        condition_label = _text(row, 4)
        if condition_label is None:
            continue
        condition_id = _condition_id(condition_label)
        case_id = _case_id(condition_id)
        if case_id is None:
            continue
        numerator = _integer(_text(row, 5))
        measure = _number(_text(row, 45))
        reason = _suppression_reason(numerator, measure)
        source_geography_id = _text(row, 2)
        geography_id = (
            _community_area_id(source_geography_id)
            if geography_type == "chicago_community_area"
            else source_geography_id
        )
        records.append(
            {
                "source_id": source_id,
                "snapshot_id": snapshot_id,
                "source_table": table,
                "source_record_id": _text(row, 1),
                "geography_type": geography_type,
                "source_geography_id": source_geography_id,
                "geography_id": geography_id,
                "geography_level_role": geography_level_role,
                "time_period": _text(row, 3),
                "condition_id": condition_id,
                "source_condition_label": condition_label,
                "condition_label": condition_label,
                "condition_family": _condition_family(condition_id),
                "case_id": case_id,
                "numerator": numerator,
                "denominator": _integer(_text(row, 25)),
                "denominator_status": "guarded_source_position_25",
                "published_measure_name": "source_published_condition_measure",
                "published_measure_value": measure,
                "published_measure_unit": "source_percent_or_rate",
                "suppression_flag": reason is not None,
                "suppression_reason": reason,
                "source_position_contract": (
                    "S4 accepted positions: geography=2, year=3, condition=4, "
                    "numerator=5, guarded denominator=25, published measure=45"
                ),
                "sap_variable_role": "case_study_exposure_or_descriptive_measure",
            }
        )
    return pd.DataFrame.from_records(records)


def _fact_table_audit(root: Path, table: str) -> dict[str, int]:
    """Count source rows before condition filtering and suppression labeling."""

    rows = _read_pipe(root / FIRST_PARTY_ORIGINAL / table, 67)
    selected = []
    for row in rows:
        label = _text(row, 4)
        if label is not None and _case_id(_condition_id(label)) is not None:
            selected.append(row)
    missing = sum(
        _text(row, 4) is None or _integer(_text(row, 25)) is None or _number(_text(row, 45)) is None
        for row in selected
    )
    suppressed = sum(
        _suppression_reason(_integer(_text(row, 5)), _number(_text(row, 45))) is not None
        for row in selected
    )
    return {
        "input_rows": len(rows),
        "selected_rows": len(selected),
        "excluded_rows": len(rows) - len(selected),
        "missing_rows": missing,
        "suppressed_rows": suppressed,
    }


def _source_manifest(root: Path) -> dict[str, Any]:
    path = root / FIRST_PARTY_SNAPSHOT / "manifest.json"
    if not path.is_file():
        raise AnalyticDatasetError(f"required snapshot manifest is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AnalyticDatasetError("first-party snapshot manifest must be a JSON object")
    return payload


def _schema(dataset: pd.DataFrame, dataset_id: str) -> dict[str, Any]:
    return {
        "dataset_id": dataset_id,
        "schema_version": 1,
        "grain": "geography_type-geography_id-period-condition",
        "primary_key": ["geography_type", "geography_id", "time_period", "condition_id"],
        "columns": [
            {
                "name": column,
                "dtype": str(dataset[column].dtype),
                "nullable": bool(dataset[column].isna().any()),
            }
            for column in dataset.columns
        ],
    }


def _lineage_rows(columns: list[str]) -> list[dict[str, str]]:
    first_party = {
        "source_id",
        "snapshot_id",
        "source_table",
        "source_record_id",
        "source_geography_id",
        "geography_id",
        "time_period",
        "condition_id",
        "source_condition_label",
        "condition_label",
        "condition_family",
        "case_id",
        "numerator",
        "denominator",
        "published_measure_value",
        "suppression_flag",
    }
    rows: list[dict[str, str]] = []
    for column in columns:
        if column == "disease_value_derivation":
            source_table = "analysis_dataset_builder"
            note = (
                "Audit label: disease values remain direct first-party exports, not interpolated."
            )
        elif column in first_party:
            source_table = "condition fact tables"
            note = "Mapped from S4 accepted first-party condition-stat positions."
        elif column in {"capture_rate", "reliability_tier", "public_reliability_description"}:
            source_table = "reliability crosswalk tables"
            note = "Mapped from S4 accepted reliability crosswalk positions."
        elif column in {"community_area_name", "geometry_wkt"}:
            source_table = "chicago_community_areas_current.parquet"
            note = "Public City of Chicago community-area boundary snapshot."
        elif (
            column.startswith("community_area_")
            or column.startswith("tract_community_")
            or column
            in {
                "is_crossing_tract",
                "is_sliver",
                "overlay_row_count",
                "linkage_method",
                "linkage_role",
            }
        ):
            source_table = "tract_community_overlay_2024.parquet"
            note = (
                "Geographic linkage metadata only; disease values are not interpolated "
                "or derived from this overlay."
            )
        elif column.startswith("public_comparator_"):
            source_table = "cdc_places_current_tract.parquet"
            note = "CDC PLACES tract comparator for concordance/discordance summaries."
        elif column.startswith("census_covariate_") or column in {
            "acs_total_population",
            "pct_female",
            "pct_age_65_plus",
            "pct_below_fpl",
            "acs_adult_population",
            "pct_female_standard_error",
            "pct_female_moe90",
            "pct_age_65_plus_standard_error",
            "pct_age_65_plus_moe90",
            "pct_below_fpl_standard_error",
            "pct_below_fpl_moe90",
            "acs_adult_population_standard_error",
            "acs_adult_population_moe90",
        }:
            source_table = "census_acs_2024_community_area_covariates.parquet"
            note = (
                "Official ACS tract components allocated by 2020 Census block internal point "
                "and PL P1 population weight; uncertainty uses 80 ACS variance replicates."
            )
        else:
            source_table = "derived_or_optional_public_context"
            note = "Derived audit field or optional public comparator context."
        rows.append(
            {
                "column": column,
                "source_table": source_table,
                "source_position": "see source_position_contract",
                "audit_note": note,
            }
        )
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _data_book(dataset: pd.DataFrame, lineage: pd.DataFrame) -> pd.DataFrame:
    records = pd.DataFrame(
        {
            "column": dataset.columns,
            "dtype": [str(dataset[column].dtype) for column in dataset.columns],
            "nullable": [bool(dataset[column].isna().any()) for column in dataset.columns],
            "non_missing_count": [int(dataset[column].notna().sum()) for column in dataset.columns],
            "missing_count": [int(dataset[column].isna().sum()) for column in dataset.columns],
        }
    )
    return records.merge(lineage, on="column", how="left", validate="one_to_one")


def build_chicago_case_study_dataset(
    root: Path,
    output_dir: Path,
    output_stem: str = DATASET_ID,
) -> AnalyticDatasetArtifacts:
    """Build one frozen, notebook-ready analytic dataset for the approved case studies."""

    root = root.resolve()
    raw_data_audit = (
        assert_primary_tract_contract(root)
        if (root / RAW_DATA_CONTRACT_PATH).is_file()
        else None
    )
    output_stem = _validated_output_stem(output_stem)
    output_dir.mkdir(parents=True, exist_ok=True)
    stability_source_id = "__source_stability_check__"
    source_contract_at_start = _source_join_contract(
        root, stability_source_id, output_stem, FIRST_PARTY_INPUTS
    )
    source_manifest = _source_manifest(root)
    source_id = str(source_manifest.get("source_id", "capricorn_chicagohealthmap_export"))
    snapshot_id = str(source_manifest.get("snapshot_id", "capricorn_chicagohealthmap_snapshot"))

    community = _case_fact_records(
        root,
        source_id=source_id,
        snapshot_id=snapshot_id,
        table=COMMUNITY_FACT_TABLE,
        geography_type="chicago_community_area",
        geography_level_role="primary_case_study_frame",
    )
    tract = _case_fact_records(
        root,
        source_id=source_id,
        snapshot_id=snapshot_id,
        table=TRACT_FACT_TABLE,
        geography_type="census_tract",
        geography_level_role="sensitivity_spatial_heterogeneity",
    )
    community_fact_audit = _fact_table_audit(root, COMMUNITY_FACT_TABLE)
    tract_fact_audit = _fact_table_audit(root, TRACT_FACT_TABLE)
    assembly_steps: list[dict[str, Any]] = [
        {
            "step_id": "direct_chm_facts",
            "step_order": 1,
            "source_ids": [source_id],
            "role": "direct_first_party_measure",
            "operation": "parse_and_filter_governed_condition_fact_tables",
            "input_rows": community_fact_audit["input_rows"] + tract_fact_audit["input_rows"],
            "output_rows": len(community) + len(tract),
            "matched_rows": len(community) + len(tract),
            "unmatched_rows": 0,
            "excluded_rows": community_fact_audit["excluded_rows"]
            + tract_fact_audit["excluded_rows"],
            "missing_rows": community_fact_audit["missing_rows"] + tract_fact_audit["missing_rows"],
            "suppressed_rows": community_fact_audit["suppressed_rows"]
            + tract_fact_audit["suppressed_rows"],
            "join_key": ["source_geography_id", "time_period", "condition_id"],
            "join_validation": "not_applicable_direct_parse",
            "field_role": "direct_disease_values",
            "clinical_values_created": False,
            "notes": "Asthma and other non-governed conditions are excluded; suppression is retained.",
        }
    ]
    overlay_all = _tract_community_overlay(root).merge(
        _tract_city_membership(root),
        on="geography_id",
        how="left",
        validate="one_to_one",
    )
    if overlay_all["city_inclusion_primary_eligible"].isna().any():
        raise AnalyticDatasetError("Chicago-intersecting tracts lack city-membership geometry")
    overlay_all["city_inclusion_area50_sensitivity_eligible"] = pd.to_numeric(
        overlay_all["covered_fraction"], errors="coerce"
    ).ge(0.5)
    overlay_all["city_inclusion_primary_eligible"] = overlay_all[
        "city_inclusion_primary_eligible"
    ].astype(bool)
    overlay_all["city_inclusion_reason"] = overlay_all[
        "city_inclusion_primary_eligible"
    ].map(
        {
            True: "included_representative_point_in_chicago",
            False: "excluded_boundary_intersection_with_representative_point_outside_chicago",
        }
    )
    overlay = overlay_all.loc[overlay_all["city_inclusion_primary_eligible"]].copy()
    tract_before_overlay = len(tract)
    if not tract.empty:
        tract = tract.merge(overlay, on="geography_id", how="inner")
    assembly_steps.append(
        {
            "step_id": "tract_overlay_linkage",
            "step_order": 2,
            "source_ids": ["tract_community_overlay_2024"],
            "role": "linkage_metadata_only",
            "operation": "restrict_tract_rows_to_authoritative_chicago_overlay",
            "input_rows": tract_before_overlay,
            "output_rows": len(tract),
            "matched_rows": len(tract),
            "unmatched_rows": tract_before_overlay - len(tract),
            "excluded_rows": tract_before_overlay - len(tract),
            "missing_rows": 0,
            "suppressed_rows": 0,
            "join_key": ["geography_id"],
            "join_validation": "many_to_one",
            "field_role": "geographic_linkage_metadata",
            "clinical_values_created": False,
            "notes": (
                "The primary cohort requires a tract representative point covered by the "
                "frozen Chicago union. The overlay does not interpolate or aggregate CHM "
                "disease values."
            ),
        }
    )
    community["community_area_id"] = community["geography_id"]
    community["community_area_ids"] = community["geography_id"]
    community["community_area_weights_json"] = None
    community["max_community_area_weight"] = None
    community["covered_fraction"] = None
    community["is_crossing_tract"] = False
    community["is_sliver"] = False
    community["overlay_row_count"] = 1
    community["tract_community_linkage_source_id"] = None
    community["tract_community_linkage_snapshot_id"] = None
    community["community_area_boundary_source_id"] = "chicago_community_areas_current"
    community["community_area_boundary_snapshot_id"] = None
    community["tract_community_linkage_method"] = "not_applicable_direct_community_area_export"
    community["tract_community_linkage_role"] = "not_applicable_primary_direct_export"
    community["disease_value_derivation"] = "direct_first_party_export_not_interpolated"
    community["tract_vintage"] = None
    community["city_inclusion_primary_eligible"] = pd.NA
    community["city_inclusion_primary_rule"] = "not_applicable_direct_community_area_export"
    community["city_inclusion_area50_sensitivity_eligible"] = pd.NA
    community["city_inclusion_geometry_vintage"] = None
    community["city_inclusion_reason"] = "not_applicable_direct_community_area_export"
    community_covariates = _community_covariates(
        root, set(community["community_area_id"].astype(str))
    )
    community = community.merge(
        community_covariates,
        on="community_area_id",
        how="left",
        validate="many_to_one",
    )
    community_covariate_matches = int(community["acs_adult_population"].notna().sum())
    assembly_steps.append(
        {
            "step_id": "community_acs_covariates",
            "step_order": 3,
            "source_ids": ["us_census_acs"],
            "role": "community_area_adjustment",
            "operation": "left_join_acs_covariates_to_community_rows",
            "input_rows": len(community),
            "output_rows": len(community),
            "matched_rows": community_covariate_matches,
            "unmatched_rows": len(community) - community_covariate_matches,
            "excluded_rows": 0,
            "missing_rows": len(community) - community_covariate_matches,
            "suppressed_rows": 0,
            "join_key": ["community_area_id"],
            "join_validation": "many_to_one",
            "field_role": "public_adjustment_covariates",
            "clinical_values_created": False,
            "notes": "ACS values describe community areas and do not replace CHM measures.",
        }
    )
    dataset = pd.concat([community, tract], ignore_index=True, sort=False)
    if dataset.empty:
        raise AnalyticDatasetError("no approved Chicago case-study condition rows were found")
    assembly_steps.append(
        {
            "step_id": "concat_geography_frames",
            "step_order": 4,
            "source_ids": [source_id],
            "role": "analytic_frame_assembly",
            "operation": "concatenate_direct_community_and_tract_frames",
            "input_rows": len(community) + len(tract),
            "output_rows": len(dataset),
            "matched_rows": len(dataset),
            "unmatched_rows": 0,
            "excluded_rows": 0,
            "missing_rows": 0,
            "suppressed_rows": int(dataset["suppression_flag"].fillna(False).sum()),
            "join_key": ["geography_type", "geography_id", "time_period", "condition_id"],
            "join_validation": "concatenation_no_join",
            "field_role": "direct_values_preserved",
            "clinical_values_created": False,
            "notes": "Community and tract disease values remain direct; no tract aggregation is performed.",
        }
    )
    community_context = (
        _community_dimension(root)
        .merge(_community_reliability(root), on="geography_id", how="left")
        .merge(_community_geometry(root), on="geography_id", how="left")
    )
    tract_context = (
        _tract_reliability(root)
        .merge(_tract_geometry(root), on="geography_id", how="left")
        .assign(community_area_name=None, geography_name_source=None)
    )
    context = pd.concat([community_context, tract_context], ignore_index=True, sort=False)
    dataset = dataset.merge(context, on="geography_id", how="left")
    context_matches = int(dataset["geometry_wkt"].notna().sum())
    assembly_steps.append(
        {
            "step_id": "geography_context",
            "step_order": 5,
            "source_ids": ["chicago_community_areas_current", "census_tiger_2024_tract"],
            "role": "geography_context",
            "operation": "left_join_names_reliability_and_geometry",
            "input_rows": len(community) + len(tract),
            "output_rows": len(dataset),
            "matched_rows": context_matches,
            "unmatched_rows": len(dataset) - context_matches,
            "excluded_rows": 0,
            "missing_rows": len(dataset) - context_matches,
            "suppressed_rows": 0,
            "join_key": ["geography_id"],
            "join_validation": "many_to_one",
            "field_role": "linked_geography_and_reliability_metadata",
            "clinical_values_created": False,
            "notes": "Geometry and reliability are metadata; they do not create disease values.",
        }
    )

    life_expectancy = _health_atlas_measure(
        root,
        "data/processed/public/chicago_health_atlas_life_expectancy.parquet",
        "life_expectancy",
    )
    mortality = _latest_period_by_geography(
        _health_atlas_measure(
            root,
            "data/processed/public/chicago_health_atlas_mortality.parquet",
            "mortality",
        ),
        "mortality_time_period",
    )
    dataset = dataset.merge(
        life_expectancy,
        left_on=["geography_id", "time_period"],
        right_on=["geography_id", "life_expectancy_time_period"],
        how="left",
    )
    atlas_matches = int(dataset["life_expectancy_estimate"].notna().sum())
    assembly_steps.append(
        {
            "step_id": "health_atlas_outcomes",
            "step_order": 6,
            "source_ids": ["chicago_health_atlas"],
            "role": "community_area_outcome",
            "operation": "left_join_life_expectancy_by_geography_and_period",
            "input_rows": len(dataset),
            "output_rows": len(dataset),
            "matched_rows": atlas_matches,
            "unmatched_rows": len(dataset) - atlas_matches,
            "excluded_rows": 0,
            "missing_rows": len(dataset) - atlas_matches,
            "suppressed_rows": 0,
            "join_key": ["geography_id", "time_period"],
            "join_validation": "many_to_one",
            "field_role": "public_outcome",
            "clinical_values_created": False,
            "notes": "Atlas outcomes remain public comparator context, not CHM exposure values.",
        }
    )
    dataset = dataset.merge(mortality, on="geography_id", how="left")
    mortality_matches = int(dataset["mortality_estimate"].notna().sum())
    assembly_steps.append(
        {
            "step_id": "health_atlas_mortality",
            "step_order": 7,
            "source_ids": ["chicago_health_atlas"],
            "role": "community_area_outcome_context",
            "operation": "left_join_latest_mortality_by_geography",
            "input_rows": len(dataset),
            "output_rows": len(dataset),
            "matched_rows": mortality_matches,
            "unmatched_rows": len(dataset) - mortality_matches,
            "excluded_rows": 0,
            "missing_rows": len(dataset) - mortality_matches,
            "suppressed_rows": 0,
            "join_key": ["geography_id"],
            "join_validation": "many_to_one",
            "field_role": "public_outcome_context",
            "clinical_values_created": False,
            "notes": "Latest Atlas mortality is context only and does not alter CHM disease values.",
        }
    )
    dataset["public_comparator_measure_id"] = dataset["condition_id"].map(_places_measure_id)
    dataset = dataset.merge(
        _places_comparators(root),
        on=["geography_id", "public_comparator_measure_id"],
        how="left",
    )
    places_matches = int(dataset["public_comparator_estimate"].notna().sum())
    assembly_steps.append(
        {
            "step_id": "places_tract_comparators",
            "step_order": 8,
            "source_ids": ["cdc_places"],
            "role": "tract_public_comparator",
            "operation": "left_join_places_by_tract_and_measure_id",
            "input_rows": len(dataset),
            "output_rows": len(dataset),
            "matched_rows": places_matches,
            "unmatched_rows": len(dataset) - places_matches,
            "excluded_rows": 0,
            "missing_rows": len(dataset) - places_matches,
            "suppressed_rows": 0,
            "join_key": ["geography_id", "public_comparator_measure_id"],
            "join_validation": "many_to_one",
            "field_role": "public_tract_comparator",
            "clinical_values_created": False,
            "notes": "PLACES is a comparator for tract concordance, not validation of CHM.",
        }
    )
    dataset["public_comparator_source"] = (
        dataset["public_comparator_estimate"]
        .notna()
        .map({True: "CDC PLACES tract model-based estimate", False: None})
    )
    dataset["public_comparator_role"] = (
        dataset["public_comparator_estimate"]
        .notna()
        .map({True: "tract_concordance_discordance_comparator", False: None})
    )
    dataset["public_comparator_note"] = (
        dataset["public_comparator_measure_id"]
        .notna()
        .map(
            {
                True: (
                    "Comparator construct differs from the EHR-diagnosed CHM condition-record measure; "
                    "use for concordance/discordance, not validation accuracy."
                ),
                False: None,
            }
        )
    )
    dataset["geography_name"] = dataset["community_area_name"].fillna(
        dataset["geography_name_source"]
    )
    dataset.loc[dataset["geography_name"].isna(), "geography_name"] = dataset.loc[
        dataset["geography_name"].isna(), "geography_id"
    ]
    dataset["capture_flag"] = (
        dataset["capture_rate"]
        .isna()
        .map({True: "capture_rate_missing", False: "capture_rate_available"})
    )
    dataset["reliability_flag"] = (
        dataset["reliability_tier"]
        .isna()
        .map({True: "reliability_missing", False: "reliability_available"})
    )
    dataset["linkage_method"] = dataset["tract_community_linkage_method"]
    dataset["linkage_role"] = dataset["tract_community_linkage_role"]
    tract_rows = dataset["geography_type"].eq("census_tract")
    denominator = pd.to_numeric(dataset["denominator"], errors="coerce")
    dataset["primary_tract_annual_eligible"] = (
        tract_rows
        & dataset["city_inclusion_primary_eligible"].fillna(False).astype(bool)
        & ~dataset["suppression_flag"].fillna(True).astype(bool)
        & pd.to_numeric(dataset["numerator"], errors="coerce").notna()
        & denominator.ge(30)
    )
    dataset["primary_tract_annual_exclusion_reason"] = "not_applicable_higher_geography"
    dataset.loc[tract_rows, "primary_tract_annual_exclusion_reason"] = "eligible"
    dataset.loc[
        tract_rows & denominator.lt(30), "primary_tract_annual_exclusion_reason"
    ] = "annual_denominator_below_30"
    dataset.loc[
        tract_rows & denominator.isna(), "primary_tract_annual_exclusion_reason"
    ] = "annual_denominator_missing"
    dataset.loc[
        tract_rows & dataset["suppression_flag"].fillna(True).astype(bool),
        "primary_tract_annual_exclusion_reason",
    ] = dataset.loc[
        tract_rows & dataset["suppression_flag"].fillna(True).astype(bool),
        "suppression_reason",
    ].fillna("source_measure_unavailable")
    dataset["analysis_frame"] = (
        "City of Chicago community areas plus tract representative points within Chicago"
    )
    dataset["source_scope"] = "six-county CAPriCORN/ChicagoHealthMap provenance retained"
    dataset["dataset_role"] = "frozen_input_for_combined_marimo_case_studies"
    assembly_steps.append(
        {
            "step_id": "derive_flags_lineage",
            "step_order": 9,
            "source_ids": ["analysis_dataset_builder"],
            "role": "derived_analysis_metadata",
            "operation": "derive_roles_flags_and_lineage_fields",
            "input_rows": len(dataset),
            "output_rows": len(dataset),
            "matched_rows": len(dataset),
            "unmatched_rows": 0,
            "excluded_rows": 0,
            "missing_rows": int(dataset.isna().any(axis=1).sum()),
            "suppressed_rows": int(dataset["suppression_flag"].fillna(False).sum()),
            "join_key": ["geography_id", "condition_id", "time_period"],
            "join_validation": "derived_fields_no_join",
            "field_role": "derived_flags_and_lineage",
            "clinical_values_created": False,
            "notes": "Roles and lineage labels are derived metadata; missing is not zero.",
        }
    )

    ordered_columns = [
        "source_id",
        "snapshot_id",
        "source_table",
        "source_record_id",
        "geography_type",
        "geography_level_role",
        "source_geography_id",
        "geography_id",
        "geography_name",
        "community_area_id",
        "community_area_ids",
        "community_area_weights_json",
        "max_community_area_weight",
        "covered_fraction",
        "is_crossing_tract",
        "is_sliver",
        "overlay_row_count",
        "tract_community_linkage_source_id",
        "tract_community_linkage_snapshot_id",
        "community_area_boundary_source_id",
        "community_area_boundary_snapshot_id",
        "tract_community_linkage_method",
        "tract_community_linkage_role",
        "linkage_method",
        "linkage_role",
        "disease_value_derivation",
        "tract_vintage",
        "city_inclusion_primary_eligible",
        "city_inclusion_primary_rule",
        "city_inclusion_area50_sensitivity_eligible",
        "city_inclusion_geometry_vintage",
        "city_inclusion_reason",
        "time_period",
        "condition_id",
        "source_condition_label",
        "condition_label",
        "condition_family",
        "case_id",
        "numerator",
        "denominator",
        "denominator_status",
        "published_measure_name",
        "published_measure_value",
        "published_measure_unit",
        "suppression_flag",
        "suppression_reason",
        "primary_tract_annual_eligible",
        "primary_tract_annual_exclusion_reason",
        "capture_rate",
        "capture_flag",
        "reliability_tier",
        "reliability_flag",
        "equity_alignment_label",
        "combined_reliability_label",
        "public_reliability_description",
        "acs_total_population",
        "pct_female",
        "pct_female_standard_error",
        "pct_female_moe90",
        "pct_age_65_plus",
        "pct_age_65_plus_standard_error",
        "pct_age_65_plus_moe90",
        "pct_below_fpl",
        "pct_below_fpl_standard_error",
        "pct_below_fpl_moe90",
        "acs_adult_population",
        "acs_adult_population_standard_error",
        "acs_adult_population_moe90",
        "census_covariate_uncertainty_status",
        "census_covariate_source_id",
        "census_covariate_time_period",
        "census_covariate_release_vintage",
        "census_covariate_allocation_method",
        "census_covariate_allocation_weight_source",
        "census_covariate_poverty_universe",
        "census_covariate_boundary_snapshot_id",
        "census_covariate_boundary_release_vintage",
        "life_expectancy_time_period",
        "life_expectancy_estimate",
        "life_expectancy_standard_error",
        "mortality_time_period",
        "mortality_estimate",
        "mortality_standard_error",
        "public_comparator_source",
        "public_comparator_role",
        "public_comparator_measure_id",
        "public_comparator_time_period",
        "public_comparator_measure_type",
        "public_comparator_estimate",
        "public_comparator_confidence_interval",
        "public_comparator_note",
        "geometry_wkt",
        "analysis_frame",
        "source_scope",
        "sap_variable_role",
        "source_position_contract",
        "dataset_role",
    ]
    dataset = dataset[ordered_columns].sort_values(
        ["geography_type", "geography_id", "time_period", "condition_id"], kind="mergesort"
    )
    if dataset.duplicated(["geography_type", "geography_id", "time_period", "condition_id"]).any():
        raise AnalyticDatasetError("analytic dataset primary key is not unique")
    primary_key = ["geography_type", "geography_id", "time_period", "condition_id"]
    assembly_steps.append(
        {
            "step_id": "final_key_validation",
            "step_order": 10,
            "source_ids": ["analysis_dataset_builder"],
            "role": "analytic_dataset_validation",
            "operation": "validate_final_grain_and_unique_key",
            "input_rows": len(dataset),
            "output_rows": len(dataset),
            "matched_rows": len(dataset),
            "unmatched_rows": 0,
            "excluded_rows": 0,
            "missing_rows": int(dataset[primary_key].isna().any(axis=1).sum()),
            "suppressed_rows": int(dataset["suppression_flag"].fillna(False).sum()),
            "join_key": primary_key,
            "join_validation": "unique_key",
            "primary_key": primary_key,
            "unique_key": not dataset.duplicated(primary_key).any(),
            "field_role": "derived_validation_metadata",
            "clinical_values_created": False,
            "notes": "Missing, suppressed, and zero-count states remain explicit in the final artifact.",
        }
    )
    source_records = {
        str(record["source_id"]): record for record in source_contract_at_start["sources"]
    }
    step_artifact_paths = {
        "direct_chm_facts": {path.as_posix() for path in FIRST_PARTY_INPUTS},
        "tract_overlay_linkage": {"data/processed/public/tract_community_overlay_2024.parquet"},
        "community_acs_covariates": {
            "data/processed/public/census_acs_2024_community_area_covariates.parquet"
        },
        "concat_geography_frames": {path.as_posix() for path in FIRST_PARTY_INPUTS},
        "geography_context": {
            "data/processed/public/chicago_community_areas_current.parquet",
            "data/processed/public/census_tiger_2024_tract.parquet",
            "data/processed/public/tract_community_overlay_2024.parquet",
        },
        "health_atlas_outcomes": {
            "data/processed/public/chicago_health_atlas_life_expectancy.parquet"
        },
        "health_atlas_mortality": {"data/processed/public/chicago_health_atlas_mortality.parquet"},
        "places_tract_comparators": {"data/processed/public/cdc_places_current_tract.parquet"},
        "derive_flags_lineage": set(),
        "final_key_validation": set(),
    }
    step_coverage = {
        "direct_chm_facts": ("community areas and Chicago-intersecting tracts", "2019-2024"),
        "tract_overlay_linkage": (
            "tract representative points covered by the frozen Chicago union",
            "2024 overlay snapshot",
        ),
        "community_acs_covariates": ("77 community areas", "2020-2024 ACS"),
        "concat_geography_frames": ("community areas and census tracts", "2019-2024"),
        "geography_context": ("community areas and census tracts", "2024 boundary snapshots"),
        "health_atlas_outcomes": ("community areas", "source-specific Atlas periods"),
        "health_atlas_mortality": ("community areas", "latest available Atlas period"),
        "places_tract_comparators": ("census tracts", "2023 BRFSS / 2025 PLACES release"),
        "derive_flags_lineage": ("community areas and census tracts", "2019-2024"),
        "final_key_validation": ("community areas and census tracts", "2019-2024"),
    }
    for step in assembly_steps:
        geography_coverage, period_coverage = step_coverage[str(step["step_id"])]
        step["geography_coverage"] = geography_coverage
        step["period_coverage"] = period_coverage
        step["cardinality"] = step["join_validation"]
        permitted_paths = step_artifact_paths[str(step["step_id"])]
        step["input_artifacts"] = [
            {
                "source_id": source_id
                if source_name == "__source_stability_check__"
                else source_name,
                "path": item["path"],
                "sha256": item["sha256"],
            }
            for source_name, record in source_records.items()
            for item in record.get("inputs", [])
            if item["path"] in permitted_paths
        ]

    source_contract_at_end = _source_join_contract(
        root, stability_source_id, output_stem, FIRST_PARTY_INPUTS
    )
    if source_contract_at_end != source_contract_at_start:
        raise AnalyticDatasetError("source inputs changed while the analytic dataset was building")
    source_join = source_contract_at_start
    source_join["assembly_manifest_schema_version"] = ASSEMBLY_MANIFEST_SCHEMA_VERSION
    source_join["assembly_steps"] = assembly_steps
    source_join["sources"][0]["source_id"] = source_id
    artifacts = _artifact_paths(output_dir, output_stem)
    parquet_path = artifacts.parquet_path
    csv_path = artifacts.csv_path
    schema_path = artifacts.schema_path
    lineage_path = artifacts.lineage_path
    manifest_path = artifacts.manifest_path
    source_join_manifest_path = artifacts.source_join_manifest_path
    data_book_csv_path = artifacts.data_book_csv_path
    data_book_html_path = artifacts.data_book_html_path
    assert source_join_manifest_path is not None
    assert data_book_csv_path is not None
    assert data_book_html_path is not None

    dataset.to_parquet(parquet_path, index=False)
    dataset.to_csv(csv_path, index=False)
    _write_json(schema_path, _schema(dataset, output_stem))
    lineage = pd.DataFrame(_lineage_rows(list(dataset.columns)))
    lineage.to_csv(lineage_path, index=False)
    data_book = _data_book(dataset, lineage)
    data_book.to_csv(data_book_csv_path, index=False)
    data_book_html_path.write_text(data_book.to_html(index=False, border=0), encoding="utf-8")
    source_join["artifact_checksums"] = {
        path.name: _sha256_file(path)
        for path in (
            parquet_path,
            csv_path,
            schema_path,
            lineage_path,
            data_book_csv_path,
            data_book_html_path,
        )
    }
    _write_json(source_join_manifest_path, source_join)

    manifest = {
        "manifest_schema_version": 2,
        "dataset_id": output_stem,
        "created_at_utc": source_manifest.get(
            "created_at_utc", f"{source_manifest.get('snapshot_date', '2026-05-27')}T00:00:00+00:00"
        ),
        "created_at_utc_semantics": "deterministic_source_snapshot_time_not_wall_clock_build_time",
        "source_snapshot_at_utc": source_manifest.get(
            "created_at_utc", f"{source_manifest.get('snapshot_date', '2026-05-27')}T00:00:00+00:00"
        ),
        "grain": "geography_type-geography_id-period-condition",
        "primary_key": ["geography_type", "geography_id", "time_period", "condition_id"],
        "geography_levels": sorted(dataset["geography_type"].dropna().unique().tolist()),
        "analysis_authority": "human_approved_s5_s6_unless_catastrophic_blocker",
        "results_authorized": False,
        "raw_data_contract": {
            "status": (
                "primary_tract_contract_passed"
                if raw_data_audit is not None
                else "not_run_contract_absent_in_test_fixture"
            ),
            "contract_version": (
                raw_data_audit.contract_version if raw_data_audit is not None else None
            ),
            "primary_tract_contract_passed": (
                raw_data_audit.primary_tract_contract_passed
                if raw_data_audit is not None
                else None
            ),
            "higher_geography_estimand_authorized": False,
            "unresolved_signoff_items": (
                list(raw_data_audit.unresolved_signoff_items)
                if raw_data_audit is not None
                else []
            ),
        },
        "row_count": int(len(dataset)),
        "condition_ids": sorted(dataset["condition_id"].dropna().unique().tolist()),
        "case_ids": sorted(dataset["case_id"].dropna().unique().tolist()),
        "source_snapshot_id": snapshot_id,
        "source_manifest_validation_status": source_manifest.get("validation_status"),
        "suppression_rule": "ChicagoHealthMap glossary: counts fewer than 10 are suppressed.",
        "city_inclusion_rule": (
            "Community-area rows use the direct 77-area ChicagoHealthMap export; tract rows are "
            "limited to direct first-party tract disease rows whose 2024 TIGER tract "
            "representative point is covered by the frozen union of 77 Chicago community "
            "areas. The 50% tract-area rule is retained as a sensitivity definition."
        ),
        "tract_boundary_audit": {
            "any_intersection_tracts": int(overlay_all["geography_id"].nunique()),
            "primary_representative_point_tracts": int(
                overlay_all.loc[
                    overlay_all["city_inclusion_primary_eligible"], "geography_id"
                ].nunique()
            ),
            "area50_sensitivity_tracts": int(
                overlay_all.loc[
                    overlay_all["city_inclusion_area50_sensitivity_eligible"], "geography_id"
                ].nunique()
            ),
            "primary_and_area50_tracts": int(
                overlay_all.loc[
                    overlay_all["city_inclusion_primary_eligible"]
                    & overlay_all["city_inclusion_area50_sensitivity_eligible"],
                    "geography_id",
                ].nunique()
            ),
        },
        "annual_tract_minimum_denominator": 30,
        "clinical_value_rule": (
            "Disease numerators, denominators, and published measures are direct "
            "ChicagoHealthMap/CAPriCORN first-party export values. The tract-community overlay "
            "is linkage metadata only and is not used to create disease values."
        ),
        "checksums": {
            "census_acs_2024_community_area_covariates.parquet": _sha256_file(
                root / "data/processed/public/census_acs_2024_community_area_covariates.parquet"
            ),
            parquet_path.name: _sha256_file(parquet_path),
            csv_path.name: _sha256_file(csv_path),
            schema_path.name: _sha256_file(schema_path),
            lineage_path.name: _sha256_file(lineage_path),
            data_book_csv_path.name: _sha256_file(data_book_csv_path),
            data_book_html_path.name: _sha256_file(data_book_html_path),
            source_join_manifest_path.name: _sha256_file(source_join_manifest_path),
        },
    }
    _write_json(manifest_path, manifest)
    return artifacts


def _zcta_source_contract(root: Path, source_id: str) -> dict[str, Any]:
    inputs = []
    for relative in ZCTA_INPUTS:
        path = root / relative
        inputs.append(
            {
                "path": relative.as_posix(),
                "required": True,
                "exists": path.is_file(),
                "sha256": _sha256_file(path) if path.is_file() else None,
            }
        )
    return {
        "dataset_id": ZCTA_DATASET_ID,
        "sources": [
            {
                "source_id": source_id,
                "role": "direct_zcta_ehr_diagnosed_measure_and_metadata",
                "inputs": inputs,
            }
        ],
        "joins": [
            {
                "name": "zcta_context",
                "keys": ["geography_id"],
                "validation": "many_to_one",
                "role": "linked_metadata_only",
            }
        ],
    }


def build_zcta_sidecar_dataset(
    root: Path,
    output_dir: Path,
    output_stem: str = ZCTA_DATASET_ID,
) -> AnalyticDatasetArtifacts:
    """Build direct ZCTA facts as a governed sidecar without changing the primary dataset."""

    root = root.resolve()
    output_stem = _validated_output_stem(output_stem)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_manifest = _source_manifest(root)
    source_id = str(source_manifest.get("source_id", "capricorn_chicagohealthmap_export"))
    snapshot_id = str(source_manifest.get("snapshot_id", "capricorn_chicagohealthmap_snapshot"))
    source_contract_start = _zcta_source_contract(root, source_id)
    if not _source_inputs_match(root, source_contract_start["sources"]):
        raise AnalyticDatasetError("required ZCTA sidecar source inputs are missing")

    facts = _case_fact_records(
        root,
        source_id=source_id,
        snapshot_id=snapshot_id,
        table=ZCTA_FACT_TABLE,
        geography_type="zcta",
        geography_level_role="direct_coarser_geography_sensitivity",
    )
    facts["geography_id"] = facts["geography_id"].map(_zcta_id)
    facts["source_geography_id"] = facts["source_geography_id"].map(_zcta_id)
    context = _zcta_dimension(root).merge(
        _zcta_reliability(root), on="geography_id", how="inner", validate="one_to_one"
    )
    dimension_ids = set(context["geography_id"].astype(str))
    fact_ids = set(facts["geography_id"].dropna().astype(str))
    if not fact_ids.issubset(dimension_ids):
        raise AnalyticDatasetError(
            "ZCTA fact keys must be present in dimension and reliability tables"
        )
    dataset = facts.merge(context, on="geography_id", how="left", validate="many_to_one")
    dataset["disease_value_derivation"] = "direct_first_party_export_not_interpolated"
    dataset["geographic_linkage_role"] = "direct_zcta_metadata_not_tract_aggregation"
    key = ["geography_type", "geography_id", "time_period", "condition_id"]
    if dataset.duplicated(key).any():
        raise AnalyticDatasetError("ZCTA sidecar primary key is not unique")
    dataset = dataset.sort_values(key, kind="mergesort").reset_index(drop=True)

    if _zcta_source_contract(root, source_id) != source_contract_start:
        raise AnalyticDatasetError("ZCTA source inputs changed while the sidecar was building")
    artifacts = _artifact_paths(output_dir, output_stem)
    assert artifacts.source_join_manifest_path is not None
    assert artifacts.data_book_csv_path is not None
    assert artifacts.data_book_html_path is not None
    dataset.to_parquet(artifacts.parquet_path, index=False)
    dataset.to_csv(artifacts.csv_path, index=False)
    _write_json(artifacts.schema_path, _schema(dataset, output_stem))
    lineage = pd.DataFrame(_lineage_rows(list(dataset.columns)))
    lineage.loc[lineage["column"] == "geometry_wkt", "source_table"] = ZCTA_DIM_TABLE
    lineage.to_csv(artifacts.lineage_path, index=False)
    data_book = _data_book(dataset, lineage)
    data_book.to_csv(artifacts.data_book_csv_path, index=False)
    artifacts.data_book_html_path.write_text(
        data_book.to_html(index=False, border=0), encoding="utf-8"
    )
    source_contract_start["assembly_manifest_schema_version"] = ASSEMBLY_MANIFEST_SCHEMA_VERSION
    source_contract_start["assembly_steps"] = [
        {
            "step_id": "direct_zcta_facts",
            "step_order": 1,
            "input_rows": _fact_table_audit(root, ZCTA_FACT_TABLE)["input_rows"],
            "output_rows": len(dataset),
            "join_key": ["geography_id"],
            "join_validation": "many_to_one",
            "field_role": "direct_values_with_linked_metadata",
            "clinical_values_created": False,
        }
    ]
    artifact_set = (
        artifacts.parquet_path,
        artifacts.csv_path,
        artifacts.schema_path,
        artifacts.lineage_path,
        artifacts.data_book_csv_path,
        artifacts.data_book_html_path,
    )
    source_contract_start["artifact_checksums"] = {
        path.name: _sha256_file(path) for path in artifact_set
    }
    _write_json(artifacts.source_join_manifest_path, source_contract_start)
    audit = _fact_table_audit(root, ZCTA_FACT_TABLE)
    manifest = {
        "manifest_schema_version": 2,
        "dataset_id": output_stem,
        "grain": "zcta-period-condition",
        "primary_key": key,
        "source_input_rows": audit["input_rows"],
        "selected_rows": audit["selected_rows"],
        "excluded_rows": audit["excluded_rows"],
        "row_count": len(dataset),
        "geography_count": int(dataset["geography_id"].nunique()),
        "condition_ids": sorted(dataset["condition_id"].unique().tolist()),
        "time_periods": sorted(dataset["time_period"].unique().tolist()),
        "clinical_value_rule": "Direct first-party ZCTA values; never derived from tracts.",
        "results_authorized": False,
        "checksums": {
            **{path.name: _sha256_file(path) for path in artifact_set},
            artifacts.source_join_manifest_path.name: _sha256_file(
                artifacts.source_join_manifest_path
            ),
        },
    }
    _write_json(artifacts.manifest_path, manifest)
    return artifacts


def ensure_zcta_sidecar_dataset(
    root: Path,
    output_dir: Path,
    output_stem: str = ZCTA_DATASET_ID,
    *,
    rebuild: bool = False,
) -> DatasetBuildDecision:
    """Reuse a checksum-matching ZCTA sidecar or deterministically rebuild it."""

    root = root.resolve()
    artifacts = _artifact_paths(output_dir, _validated_output_stem(output_stem))

    def rebuild_sidecar(reason: str) -> DatasetBuildDecision:
        built = build_zcta_sidecar_dataset(root, output_dir, output_stem)
        return DatasetBuildDecision(artifacts=built, action="rebuilt", reason=reason)

    if rebuild:
        return rebuild_sidecar("explicit_rebuild_requested")
    if any(not path.is_file() for path in artifacts.required_paths):
        return rebuild_sidecar("required_artifact_missing")
    try:
        manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
        assert artifacts.source_join_manifest_path is not None
        source_join = json.loads(artifacts.source_join_manifest_path.read_text(encoding="utf-8"))
        checksums = manifest["checksums"]
    except (AssertionError, KeyError, TypeError, json.JSONDecodeError):
        return rebuild_sidecar("manifest_invalid")
    checksum_paths = tuple(
        path for path in artifacts.required_paths if path != artifacts.manifest_path
    )
    if any(checksums.get(path.name) != _sha256_file(path) for path in checksum_paths):
        return rebuild_sidecar("artifact_checksum_mismatch")
    if not _source_inputs_match(root, source_join.get("sources")):
        return rebuild_sidecar("source_checksum_mismatch")
    return DatasetBuildDecision(
        artifacts=artifacts,
        action="reused",
        reason="artifact_and_source_checksums_match",
    )


def _rebuild_decision(
    root: Path,
    output_dir: Path,
    output_stem: str,
    reason: str,
) -> DatasetBuildDecision:
    artifacts = build_chicago_case_study_dataset(root, output_dir, output_stem)
    return DatasetBuildDecision(artifacts=artifacts, action="rebuilt", reason=reason)


def ensure_chicago_case_study_dataset(
    root: Path,
    output_dir: Path,
    output_stem: str = DATASET_ID,
    *,
    rebuild: bool = False,
) -> DatasetBuildDecision:
    """Reuse a checksum-matching build or deterministically rebuild all artifacts."""

    root = root.resolve()
    output_stem = _validated_output_stem(output_stem)
    artifacts = _artifact_paths(output_dir, output_stem)
    if rebuild:
        return _rebuild_decision(root, output_dir, output_stem, "explicit_rebuild_requested")
    if any(not path.is_file() for path in artifacts.required_paths):
        return _rebuild_decision(root, output_dir, output_stem, "required_artifact_missing")
    try:
        manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
        source_join_path = artifacts.source_join_manifest_path
        if source_join_path is None:
            return _rebuild_decision(root, output_dir, output_stem, "manifest_invalid")
        source_join = json.loads(source_join_path.read_text(encoding="utf-8"))
        checksums = manifest["checksums"]
        sources = source_join["sources"]
    except (KeyError, TypeError, json.JSONDecodeError):
        return _rebuild_decision(root, output_dir, output_stem, "manifest_invalid")
    if manifest.get("dataset_id") != output_stem or source_join.get("dataset_id") != output_stem:
        return _rebuild_decision(root, output_dir, output_stem, "manifest_dataset_id_mismatch")
    checksum_paths = tuple(
        path for path in artifacts.required_paths if path != artifacts.manifest_path
    )
    if any(checksums.get(path.name) != _sha256_file(path) for path in checksum_paths):
        return _rebuild_decision(root, output_dir, output_stem, "artifact_checksum_mismatch")
    if not _source_inputs_match(root, sources):
        return _rebuild_decision(root, output_dir, output_stem, "source_checksum_mismatch")
    return DatasetBuildDecision(
        artifacts=artifacts,
        action="reused",
        reason="artifact_and_source_checksums_match",
    )
