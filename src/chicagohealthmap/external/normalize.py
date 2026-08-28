"""Normalize verified public snapshots without changing their estimands."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import geopandas as gpd  # type: ignore[import-untyped]

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.external.geography import (
    build_authoritative_tract_overlays,
    validate_tract_geoid,
)
from chicagohealthmap.sources.registry import SourceRegistry, load_registry
from chicagohealthmap.sources.snapshot import sha256_file

REQUIRED_PROVENANCE_COLUMNS = (
    "source_id",
    "snapshot_id",
    "source_record_id",
    "source_field_map",
    "release_vintage",
    "geography_type",
    "geography_id",
    "time_period",
)

EXPECTED_PUBLIC_DATASETS = frozenset(
    {
        "source_inventory",
        "chicago_health_atlas_life_expectancy",
        "chicago_health_atlas_mortality",
        "cdc_places_current_tract",
        "cdc_svi_2022_tract",
        "hrsa_health_centers_current",
        "chicago_community_areas_current",
        "census_tiger_2019_tract",
        "census_tiger_2020_tract",
        "census_tiger_2023_tract",
        "census_tiger_2024_tract",
        "census_acs_2022_5y",
        "census_acs_2024_5y",
        "tract_community_overlay_2020",
        "tract_community_overlay_2024",
    }
)


class NormalizationError(ValueError):
    """A source cannot be normalized without inventing or losing meaning."""


_MISSING_NUMERIC_TOKENS = frozenset({"", "NA", "N/A", "NULL"})
_INTERVAL = re.compile(
    r"^\(\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*,\s*"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\)$"
)
_ACS_NUMERIC_SENTINELS = {
    -999999999.0: "missing",
    -888888888.0: "not_applicable",
    -666666666.0: "unavailable",
    -555555555.0: "controlled_estimate",
    -333333333.0: "median_below_lower_bound",
    -222222222.0: "median_above_upper_bound",
}


def _parse_numeric(value: Any, field: str) -> Any:
    if value is None or value is pd.NA or (isinstance(value, float) and math.isnan(value)):
        return pd.NA
    if isinstance(value, str) and value.strip().upper() in _MISSING_NUMERIC_TOKENS:
        return pd.NA
    try:
        parsed = pd.to_numeric(value, errors="raise")
    except (TypeError, ValueError) as error:
        raise NormalizationError(f"{field} has a malformed numeric source value") from error
    if not math.isfinite(float(parsed)):
        raise NormalizationError(f"{field} has a malformed numeric source value")
    return parsed


def _parse_interval(value: Any, field: str) -> Any:
    if value is None or value is pd.NA or (isinstance(value, float) and math.isnan(value)):
        return pd.NA
    rendered = str(value).strip()
    if rendered.upper() in _MISSING_NUMERIC_TOKENS:
        return pd.NA
    match = _INTERVAL.fullmatch(rendered)
    if match is None:
        raise NormalizationError(f"{field} has a malformed numeric interval")
    lower, upper = map(float, match.groups())
    if not (math.isfinite(lower) and math.isfinite(upper) and lower <= upper):
        raise NormalizationError(f"{field} has a malformed numeric interval")
    return rendered


def _decode_numeric_state(
    value: Any, field: str, sentinels: Mapping[float, str]
) -> tuple[Any, str]:
    parsed = _parse_numeric(value, field)
    if parsed is pd.NA:
        return pd.NA, "missing_source"
    state = sentinels.get(float(parsed))
    if state is not None:
        return pd.NA, state
    return parsed, "reported"


@dataclass(frozen=True)
class NormalizationReport:
    artifacts: tuple[Path, ...]
    row_counts: Mapping[str, int]


def _verify_checksum_inventory(root: Path, inventory_path: Path) -> int:
    if not inventory_path.is_file() or inventory_path.is_symlink():
        raise NormalizationError(f"checksum inventory is absent or unsafe: {inventory_path.name}")
    count = 0
    for line in inventory_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as error:
            raise NormalizationError("checksum inventory is malformed") from error
        candidate = root / relative
        if candidate.is_symlink() or not candidate.is_file() or sha256_file(candidate) != digest:
            raise NormalizationError(f"snapshot checksum verification failed: {relative}")
        count += 1
    if count == 0:
        raise NormalizationError("checksum inventory has no records")
    return count


def verify_public_provenance(paths: ProjectPaths) -> SourceRegistry:
    """Fail closed unless registry decisions and frozen public bytes are verified."""

    registry = load_registry(paths.root / "config" / "source_registry.yml")
    unverified = sorted(
        source.source_id for source in registry.sources if source.verification.status != "verified"
    )
    if unverified:
        raise NormalizationError(f"unverified source snapshots: {', '.join(unverified)}")
    _verify_checksum_inventory(paths.root, paths.sources / "public" / "CHECKSUMS.sha256")
    _verify_checksum_inventory(
        paths.root, paths.sources / "curated" / "metopio" / "CHECKSUMS.sha256"
    )
    return registry


def _base_row(
    *,
    source_id: str,
    snapshot_id: str,
    source_record_id: str,
    source_field_map: Mapping[str, str],
    release_vintage: str,
    geography_type: str,
    geography_id: str,
    time_period: str,
) -> dict[str, Any]:
    values = (
        source_id,
        snapshot_id,
        source_record_id,
        release_vintage,
        geography_type,
        time_period,
    )
    if any(not value.strip() for value in values):
        raise NormalizationError("normalized provenance fields must not be blank")
    return {
        "source_id": source_id,
        "snapshot_id": snapshot_id,
        "source_record_id": source_record_id,
        "source_field_map": dict(source_field_map),
        "release_vintage": release_vintage,
        "geography_type": geography_type,
        "geography_id": geography_id,
        "time_period": time_period,
    }


def normalize_places(
    frame: pd.DataFrame, *, source_id: str, snapshot_id: str, release_vintage: str
) -> pd.DataFrame:
    """Convert selected PLACES estimates to a long, explicitly model-based table."""

    if "tractfips" not in frame:
        raise NormalizationError("PLACES input is missing tractfips")
    estimate_fields = sorted(
        field for field in frame.columns if re.fullmatch(r"[a-z0-9_]+_crudeprev", field)
    )
    if not estimate_fields:
        raise NormalizationError("PLACES input has no registered crude estimate fields")
    rows: list[dict[str, Any]] = []
    for source_index, source_row in frame.iterrows():
        geoid = validate_tract_geoid(str(source_row["tractfips"]))
        for estimate_field in estimate_fields:
            ci_field = estimate_field.removesuffix("_crudeprev") + "_crude95ci"
            if ci_field not in frame:
                raise NormalizationError(
                    f"PLACES estimate {estimate_field} has no confidence interval"
                )
            field_map = {
                "measure_id": estimate_field,
                "measure_type": estimate_field,
                "model_based_estimate": estimate_field,
                "confidence_interval": ci_field,
            }
            row = _base_row(
                source_id=source_id,
                snapshot_id=snapshot_id,
                source_record_id=f"{geoid}:{estimate_field}:{source_index}",
                source_field_map=field_map,
                release_vintage=release_vintage,
                geography_type="census_tract",
                geography_id=geoid,
                time_period="2023 BRFSS / 2025 release",
            )
            row.update(
                measure_id=estimate_field,
                measure_type="model_based_estimate",
                model_based_estimate=_parse_numeric(source_row[estimate_field], estimate_field),
                confidence_interval=_parse_interval(source_row[ci_field], ci_field),
            )
            rows.append(row)
    return pd.DataFrame(rows)


def normalize_acs(
    frame: pd.DataFrame,
    *,
    source_id: str,
    snapshot_id: str,
    release_vintage: str,
    time_period: str,
) -> pd.DataFrame:
    """Retain ACS detailed-table estimates and margins of error as paired values."""

    if "GEO_ID" not in frame:
        raise NormalizationError("ACS input is missing GEO_ID")
    estimate_fields = sorted(field for field in frame if re.fullmatch(r"[A-Z]\d{5}_E\d{3}", field))
    rows: list[dict[str, Any]] = []
    for source_index, source_row in frame.iterrows():
        raw_geoid = str(source_row["GEO_ID"])
        geoid = validate_tract_geoid(raw_geoid.removeprefix("1400000US"))
        for estimate_field in estimate_fields:
            moe_field = estimate_field.replace("_E", "_M", 1)
            if moe_field not in frame:
                raise NormalizationError(f"ACS estimate {estimate_field} has no margin of error")
            estimate, estimate_state = _decode_numeric_state(
                source_row[estimate_field], estimate_field, _ACS_NUMERIC_SENTINELS
            )
            margin_of_error, margin_of_error_state = _decode_numeric_state(
                source_row[moe_field], moe_field, _ACS_NUMERIC_SENTINELS
            )
            row = _base_row(
                source_id=source_id,
                snapshot_id=snapshot_id,
                source_record_id=f"{raw_geoid}:{estimate_field}:{source_index}",
                source_field_map={
                    "variable_id": estimate_field,
                    "estimate": estimate_field,
                    "estimate_state": estimate_field,
                    "margin_of_error": moe_field,
                    "margin_of_error_state": moe_field,
                },
                release_vintage=release_vintage,
                geography_type="census_tract",
                geography_id=geoid,
                time_period=time_period,
            )
            row.update(
                variable_id=estimate_field.removesuffix("_E001")
                if estimate_field.endswith("_E001")
                else estimate_field.rsplit("_E", 1)[0],
                estimate=estimate,
                estimate_state=estimate_state,
                margin_of_error=margin_of_error,
                margin_of_error_state=margin_of_error_state,
            )
            rows.append(row)
    return pd.DataFrame(rows)


def normalize_atlas(
    records: Iterable[Mapping[str, Any]],
    *,
    source_id: str,
    snapshot_id: str,
    release_vintage: str,
    indicator_label: str,
) -> pd.DataFrame:
    """Normalize Atlas observations while retaining its exact indicator identity."""

    rows: list[dict[str, Any]] = []
    for source_index, source_row in enumerate(records):
        required = {"g", "l", "a", "d", "v", "se"}
        if not required <= set(source_row):
            raise NormalizationError("Atlas observation is incomplete")
        geography_id = str(source_row["g"])
        row = _base_row(
            source_id=source_id,
            snapshot_id=snapshot_id,
            source_record_id=f"{source_row['a']}:{source_row['d']}:{geography_id}:{source_index}",
            source_field_map={
                "indicator_id": "a",
                "indicator_label": "a",
                "estimate": "v",
                "standard_error": "se",
            },
            release_vintage=release_vintage,
            geography_type="chicago_community_area",
            geography_id=geography_id,
            time_period=str(source_row["d"]),
        )
        row.update(
            indicator_id=str(source_row["a"]),
            indicator_label=indicator_label,
            estimate=_parse_numeric(source_row["v"], "v"),
            standard_error=_parse_numeric(source_row["se"], "se"),
        )
        rows.append(row)
    return pd.DataFrame(rows)


def normalize_first_party(source_path: Path, *, glossary_path: Path) -> pd.DataFrame:
    """Fail before reading an EHR export: its 549 positional meanings remain unverified."""

    del source_path, glossary_path
    raise NormalizationError(
        "Gate 3 closed: the glossary cannot promote 549 unverified first-party positions"
    )


def write_normalized_table(frame: pd.DataFrame, path: Path) -> Path:
    """Write deterministic Parquet plus a compact schema/metadata sidecar."""

    missing = sorted(set(REQUIRED_PROVENANCE_COLUMNS) - set(frame.columns))
    if missing:
        raise NormalizationError(f"normalized table is missing provenance columns: {missing}")
    if "prevalence" in frame.columns:
        raise NormalizationError("generic prevalence fields are prohibited")
    output_fields = set(frame.columns) - set(REQUIRED_PROVENANCE_COLUMNS)
    for row_number, field_map in enumerate(frame["source_field_map"]):
        if not isinstance(field_map, Mapping):
            raise NormalizationError(f"source_field_map row {row_number} must be a mapping")
        unmapped = sorted(output_fields - set(field_map))
        if unmapped:
            raise NormalizationError(
                f"source_field_map row {row_number} lacks output field(s): {', '.join(unmapped)}"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    writable = frame.copy()
    writable["source_field_map"] = writable["source_field_map"].map(
        lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    )
    writable.to_parquet(path, index=False)
    columns = {
        name: ("json" if name == "source_field_map" else str(dtype))
        for name, dtype in writable.dtypes.items()
    }
    sidecar = {"columns": columns, "row_count": len(writable), "schema_version": 1}
    path.with_suffix(".schema.json").write_text(
        json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def _registry_table(registry: SourceRegistry) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for source in sorted(registry.sources, key=lambda item: item.source_id):
        row = _base_row(
            source_id=source.source_id,
            snapshot_id=f"{source.source_id}_2026-07-13",
            source_record_id=f"registry:{source.source_id}",
            source_field_map={
                "organization": "organization",
                "dataset_title": "dataset_title",
                "catalog_id": "catalog_id",
                "license": "license",
            },
            release_vintage=source.release,
            geography_type="source_declared",
            geography_id=source.geography,
            time_period="|".join(source.years),
        )
        row.update(
            organization=source.organization,
            dataset_title=source.dataset_title,
            catalog_id=source.catalog_id,
            license=source.license,
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _atlas_table(paths: ProjectPaths, *, topic: str, source_id: str, label: str) -> pd.DataFrame:
    directory = (
        paths.sources / "public/chicago_health_atlas/snapshots/2026-07-13/original/data" / topic
    )
    records: list[Mapping[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise NormalizationError(f"Atlas response is malformed: {path.name}")
        records.extend(payload["results"])
    return normalize_atlas(
        records,
        source_id=source_id,
        snapshot_id=f"{source_id}_2026-07-13",
        release_vintage="frozen API snapshot 2026-07-13",
        indicator_label=label,
    )


def _svi_table(paths: ProjectPaths) -> pd.DataFrame:
    source_id = "cdc_svi_2022_tract"
    path = (
        paths.sources / "public/cdc_atsdr_svi/snapshots/2026-07-13/original/2022/data/Illinois.csv"
    )
    source = pd.read_csv(path, dtype={"FIPS": "string", "ST": "string", "STCNTY": "string"})
    source = source.loc[source["FIPS"].str.startswith("17031", na=False)].copy()
    value_fields = ("RPL_THEMES", "RPL_THEME1", "RPL_THEME2", "RPL_THEME3", "RPL_THEME4")
    rows: list[dict[str, Any]] = []
    for index, raw in source.iterrows():
        geoid = validate_tract_geoid(str(raw["FIPS"]))
        for field in value_fields:
            rank, rank_state = _decode_numeric_state(raw[field], field, {-999.0: "not_available"})
            row = _base_row(
                source_id=source_id,
                snapshot_id=f"{source_id}_2026-07-13",
                source_record_id=f"{geoid}:{field}:{index}",
                source_field_map={
                    "variable_id": field,
                    "svi_percentile_rank": field,
                    "svi_percentile_rank_state": field,
                },
                release_vintage="CDC/ATSDR SVI 2022 corrected 2024-12-11",
                geography_type="census_tract",
                geography_id=geoid,
                time_period="2022",
            )
            row.update(
                variable_id=field,
                svi_percentile_rank=rank,
                svi_percentile_rank_state=rank_state,
            )
            rows.append(row)
    return pd.DataFrame(rows)


def _hrsa_table(paths: ProjectPaths) -> pd.DataFrame:
    source_id = "hrsa_health_centers_current"
    path = (
        paths.sources
        / "public/hrsa_health_centers/snapshots/2026-07-13/original/data/Health_Center_Service_Delivery_and_LookAlike_Sites.csv"
    )
    source = pd.read_csv(path, dtype="string")
    source = source.loc[source["Site State Abbreviation"] == "IL"].copy()
    x = "Geocoding Artifact Address Primary X Coordinate"
    y = "Geocoding Artifact Address Primary Y Coordinate"
    rows: list[dict[str, Any]] = []
    for index, raw in source.iterrows():
        site_id = str(raw["Health Center Location Identification Number"])
        row = _base_row(
            source_id=source_id,
            snapshot_id=f"{source_id}_2026-07-13",
            source_record_id=f"{raw['Health Center Number']}:{site_id}:{index}",
            source_field_map={
                "site_name": "Site Name",
                "site_type": "Health Center Type",
                "longitude": x,
                "latitude": y,
            },
            release_vintage="daily file frozen 2026-07-13",
            geography_type="health_center_site",
            geography_id=site_id,
            time_period="2026-07-13",
        )
        row.update(
            site_name=raw["Site Name"],
            site_type=raw["Health Center Type"],
            longitude=_parse_numeric(raw[x], x),
            latitude=_parse_numeric(raw[y], y),
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _community_area_table(paths: ProjectPaths) -> pd.DataFrame:
    source_id = "chicago_community_areas_current"
    source = gpd.read_file(
        paths.sources
        / "public/chicago_data_portal/snapshots/2026-07-13/original/community_areas_igwz-8jzy/data/community_areas.geojson"
    )
    if len(source) != 77 or not source.geometry.is_valid.all():
        raise NormalizationError("community-area snapshot is incomplete or invalid")
    rows: list[dict[str, Any]] = []
    for index, raw in source.iterrows():
        area_id = str(raw["area_numbe"]).zfill(2)
        row = _base_row(
            source_id=source_id,
            snapshot_id=f"{source_id}_2026-07-13",
            source_record_id=f"community_area:{area_id}:{index}",
            source_field_map={
                "community_area_name": "community",
                "geometry_wkt": "geometry",
            },
            release_vintage="current boundary snapshot 2026-07-13",
            geography_type="chicago_community_area",
            geography_id=area_id,
            time_period="current at 2026-07-13",
        )
        row.update(community_area_name=raw["community"], geometry_wkt=raw.geometry.wkt)
        rows.append(row)
    return pd.DataFrame(rows)


def _tiger_table(paths: ProjectPaths, year: str) -> pd.DataFrame:
    source_id = f"census_tiger_{year}_tract"
    source = gpd.read_file(
        paths.sources
        / f"public/us_census_tiger_line/snapshots/2026-07-13/original/{year}/tract/tl_{year}_17_tract.zip"
    )
    source = source.loc[
        (source["STATEFP"].astype(str) == "17")
        & (source["COUNTYFP"].astype(str).str.zfill(3) == "031")
    ].copy()
    if source.empty or source.crs is None or not source.geometry.is_valid.all():
        raise NormalizationError(f"TIGER {year} Cook tract snapshot is incomplete or invalid")
    rows: list[dict[str, Any]] = []
    for index, raw in source.iterrows():
        geoid = validate_tract_geoid(str(raw["GEOID"]))
        row = _base_row(
            source_id=source_id,
            snapshot_id=f"{source_id}_2026-07-13",
            source_record_id=f"{year}:{geoid}:{index}",
            source_field_map={
                "state_fips": "STATEFP",
                "county_fips": "COUNTYFP",
                "geometry_wkt": "geometry",
                "crs": "TIGER CRS metadata",
                "tract_vintage": "TIGER release metadata",
            },
            release_vintage=f"TIGER/Line {year}",
            geography_type="census_tract",
            geography_id=geoid,
            time_period=year,
        )
        row.update(
            state_fips="17",
            county_fips="031",
            geometry_wkt=raw.geometry.wkt,
            crs=str(source.crs),
            tract_vintage=year,
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _acs_table_based(paths: ProjectPaths, year: str) -> pd.DataFrame:
    source_id = f"census_acs_{year}_5y"
    directory = (
        paths.sources
        / f"public/us_census_acs/snapshots/2026-07-13/original/{year}/acs5/bulk/data/5YRData"
    )
    normalized: list[pd.DataFrame] = []
    for path in sorted(directory.glob("*.dat")):
        for chunk in pd.read_csv(path, sep="|", dtype="string", chunksize=10_000):
            cook_tracts = chunk.loc[
                chunk["GEO_ID"].str.startswith("1400000US17031", na=False)
            ].copy()
            if cook_tracts.empty:
                continue
            normalized.append(
                normalize_acs(
                    cook_tracts,
                    source_id=source_id,
                    snapshot_id=f"{source_id}_2026-07-13",
                    release_vintage=f"{year} ACS 5-year table-based Summary File",
                    time_period={"2022": "2018-2022", "2024": "2020-2024"}[year],
                )
            )
    if not normalized:
        raise NormalizationError(f"ACS {year} snapshot has no Cook County tract rows")
    return pd.concat(normalized, ignore_index=True)


def _overlay_tables(paths: ProjectPaths) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for year, frame in build_authoritative_tract_overlays(paths).items():
        normalized = frame.copy()
        normalized["source_record_id"] = (
            normalized["geography_id"] + ":" + normalized["community_area_id"]
        )
        tiger_source = f"census_tiger_{year}_tract"
        boundary_source = "chicago_community_areas_current"
        field_map = {
            "community_area_id": f"{boundary_source}:area_numbe",
            "intersection_area": f"{tiger_source}:geometry|{boundary_source}:geometry",
            "weight": f"{tiger_source}:geometry|{boundary_source}:geometry",
            "covered_fraction": f"{tiger_source}:geometry|{boundary_source}:geometry",
            "is_crossing_tract": f"{tiger_source}:geometry|{boundary_source}:geometry",
            "is_sliver": f"{tiger_source}:geometry|{boundary_source}:geometry",
            "boundary_source_id": f"{boundary_source}:source_id",
            "boundary_snapshot_id": f"{boundary_source}:snapshot_id",
            "tract_vintage": f"{tiger_source}:release",
        }
        normalized["source_field_map"] = [field_map.copy() for _ in range(len(normalized))]
        normalized["release_vintage"] = f"TIGER/Line {year} × current community areas"
        normalized["geography_type"] = "tract_to_chicago_community_area_overlay"
        normalized["time_period"] = year
        tables[f"tract_community_overlay_{year}"] = normalized
    return tables


def normalize_all_public(paths: ProjectPaths) -> NormalizationReport:
    """Materialize verified public tables offline; never inspect first-party source rows."""

    registry = verify_public_provenance(paths)
    places_path = (
        paths.sources
        / "public/cdc_places/snapshots/2026-07-13/original/2025_release/data/illinois_census_tracts.csv"
    )
    places_raw = pd.read_csv(places_path, dtype={"tractfips": "string", "countyfips": "string"})
    places_raw = places_raw.loc[places_raw["countyfips"] == "17031"].copy()
    places = normalize_places(
        places_raw[
            [
                "tractfips",
                "bphigh_crudeprev",
                "bphigh_crude95ci",
                "diabetes_crudeprev",
                "diabetes_crude95ci",
                "copd_crudeprev",
                "copd_crude95ci",
            ]
        ],
        source_id="cdc_places_current_tract",
        snapshot_id="cdc_places_current_tract_2026-07-13",
        release_vintage="PLACES 2025 release",
    )
    tables = {
        "source_inventory": _registry_table(registry),
        "chicago_health_atlas_life_expectancy": _atlas_table(
            paths,
            topic="VRLE",
            source_id="chicago_health_atlas_life_expectancy",
            label="Life expectancy",
        ),
        "chicago_health_atlas_mortality": _atlas_table(
            paths,
            topic="VRDTHR",
            source_id="chicago_health_atlas_mortality",
            label="All-cause mortality rate",
        ),
        "cdc_places_current_tract": places,
        "cdc_svi_2022_tract": _svi_table(paths),
        "hrsa_health_centers_current": _hrsa_table(paths),
        "chicago_community_areas_current": _community_area_table(paths),
        **{
            f"census_tiger_{year}_tract": _tiger_table(paths, year)
            for year in ("2019", "2020", "2023", "2024")
        },
        **{f"census_acs_{year}_5y": _acs_table_based(paths, year) for year in ("2022", "2024")},
        **_overlay_tables(paths),
    }
    artifacts: list[Path] = []
    for name, frame in tables.items():
        artifacts.append(
            write_normalized_table(frame, paths.interim / "public" / f"{name}.parquet")
        )
        artifacts.append(
            write_normalized_table(frame, paths.processed / "public" / f"{name}.parquet")
        )
    return NormalizationReport(
        artifacts=tuple(artifacts), row_counts={name: len(frame) for name, frame in tables.items()}
    )
