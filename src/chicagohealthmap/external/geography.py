"""Strict geography validation and area-weighted tract overlays."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd  # type: ignore[import-untyped]
import pandas as pd  # type: ignore[import-untyped]

from chicagohealthmap.config import ProjectPaths


class GeographyError(ValueError):
    """Geography identity, geometry, CRS, or overlay weights are invalid."""


def validate_tract_geoid(value: str) -> str:
    if not re.fullmatch(r"\d{11}", value):
        raise GeographyError("tract GEOID must be exactly 11-digit")
    if not value.startswith("17"):
        raise GeographyError("tract GEOID must use Illinois state FIPS 17")
    return value


def validate_tract_geography(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    required = {"STATEFP", "COUNTYFP", "GEOID", "tract_vintage", "geometry"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise GeographyError(f"tract geography is missing columns: {missing}")
    if frame.crs is None:
        raise GeographyError("tract geography must declare a CRS")
    if frame.empty or frame.geometry.isna().any() or frame.geometry.is_empty.any():
        raise GeographyError("tract geometry must be present and nonempty")
    if not frame.geometry.is_valid.all():
        raise GeographyError("tract geometry must be valid")
    for value in frame["GEOID"].astype(str):
        validate_tract_geoid(value)
    if set(frame["STATEFP"].astype(str)) != {"17"}:
        raise GeographyError("tracts must use Illinois state FIPS 17")
    if set(frame["COUNTYFP"].astype(str)) != {"031"}:
        raise GeographyError("included Chicago tracts must use Cook County FIPS 031")
    if not set(frame["tract_vintage"].astype(str)) <= {"2019", "2020", "2023", "2024"}:
        raise GeographyError("tract vintage is not an approved frozen TIGER release")
    return frame.copy()


@dataclass(frozen=True)
class OverlayResult:
    weights: pd.DataFrame
    slivers: pd.DataFrame
    crossing_tract_ids: tuple[str, ...]


def build_tract_community_overlay(
    tracts: gpd.GeoDataFrame,
    communities: gpd.GeoDataFrame,
    *,
    sliver_tolerance: float = 1e-6,
    weight_tolerance: float = 1e-6,
) -> OverlayResult:
    """Build polygon-intersection weights; centroid-only assignment is never used."""

    tracts = validate_tract_geography(tracts)
    if communities.crs is None or tracts.crs != communities.crs:
        raise GeographyError("tract and community geometries must share a declared CRS")
    if not tracts.crs.is_projected:
        raise GeographyError("overlay requires a projected CRS for area weights")
    if "community_area_id" not in communities or not communities.geometry.is_valid.all():
        raise GeographyError("community areas require valid geometry and community_area_id")
    intersections = gpd.overlay(
        tracts[["GEOID", "geometry"]],
        communities[["community_area_id", "geometry"]],
        how="intersection",
        keep_geom_type=False,
    )
    intersections["intersection_area"] = intersections.geometry.area
    covered_areas = intersections.groupby("GEOID")["intersection_area"].transform("sum")
    if (covered_areas <= 0).any():
        raise GeographyError("overlay intersections must have positive area")
    intersections["weight"] = intersections["intersection_area"] / covered_areas
    intersections = intersections.rename(columns={"GEOID": "geography_id"})
    weights = intersections[
        ["geography_id", "community_area_id", "intersection_area", "weight"]
    ].sort_values(["geography_id", "community_area_id"], ignore_index=True)
    sums = weights.groupby("geography_id")["weight"].sum()
    if (
        set(sums.index) != set(tracts["GEOID"].astype(str))
        or not ((sums - 1.0).abs() <= weight_tolerance).all()
    ):
        raise GeographyError("overlay weights must sum to 1 for every included Chicago tract")
    slivers = weights.loc[weights["weight"] < sliver_tolerance].reset_index(drop=True)
    crossing = tuple(sorted(sums.index[weights.groupby("geography_id").size() > 1]))
    return OverlayResult(weights=weights, slivers=slivers, crossing_tract_ids=crossing)


def build_authoritative_tract_overlays(
    paths: ProjectPaths,
    *,
    sliver_tolerance: float = 1e-6,
) -> dict[str, pd.DataFrame]:
    """Build 2020/2024 area overlays from the verified frozen authoritative boundaries."""

    community_path = (
        paths.sources / "public/chicago_data_portal/snapshots/2026-07-13/original/"
        "community_areas_igwz-8jzy/data/community_areas.geojson"
    )
    communities = gpd.read_file(community_path)
    if len(communities) != 77 or communities.crs is None:
        raise GeographyError("authoritative community-area snapshot is incomplete")
    communities = communities.rename(columns={"area_numbe": "community_area_id"})
    communities["community_area_id"] = communities["community_area_id"].astype(str).str.zfill(2)
    communities = communities.to_crs("EPSG:3435")
    city = communities.geometry.union_all()

    overlays: dict[str, pd.DataFrame] = {}
    for year in ("2020", "2024"):
        tract_path = (
            paths.sources
            / f"public/us_census_tiger_line/snapshots/2026-07-13/original/{year}/tract/"
            f"tl_{year}_17_tract.zip"
        )
        tracts = gpd.read_file(tract_path)
        tracts = tracts.loc[
            (tracts["STATEFP"].astype(str) == "17")
            & (tracts["COUNTYFP"].astype(str).str.zfill(3) == "031")
        ].copy()
        if tracts.crs is None:
            raise GeographyError(f"authoritative TIGER {year} snapshot has no CRS")
        tracts = tracts.to_crs("EPSG:3435")
        tracts["tract_vintage"] = year
        tracts = tracts.loc[tracts.geometry.intersection(city).area > 0].copy()
        tract_areas = tracts.set_index("GEOID").geometry.area
        result = build_tract_community_overlay(
            tracts,
            communities,
            sliver_tolerance=sliver_tolerance,
        )
        frame = result.weights.copy()
        covered = frame.groupby("geography_id")["intersection_area"].transform("sum")
        frame["covered_fraction"] = frame.apply(
            lambda row: covered.loc[row.name] / tract_areas.loc[row["geography_id"]], axis=1
        )
        crossing = set(result.crossing_tract_ids)
        sliver_keys = set(
            zip(result.slivers["geography_id"], result.slivers["community_area_id"], strict=True)
        )
        frame["is_crossing_tract"] = frame["geography_id"].isin(crossing)
        frame["is_sliver"] = [
            (geoid, area_id) in sliver_keys
            for geoid, area_id in zip(
                frame["geography_id"], frame["community_area_id"], strict=True
            )
        ]
        source_id = f"census_tiger_{year}_tract"
        frame["source_id"] = source_id
        frame["snapshot_id"] = f"{source_id}_2026-07-13"
        frame["boundary_source_id"] = "chicago_community_areas_current"
        frame["boundary_snapshot_id"] = "chicago_community_areas_current_2026-07-13"
        frame["tract_vintage"] = year
        overlays[year] = frame
    return overlays


def normalize_zcta_tract_relationship(
    frame: pd.DataFrame,
    *,
    eligible_tract_ids: set[str] | None = None,
    coverage_tolerance: float = 1e-6,
) -> pd.DataFrame:
    """Normalize the official 2020 ZCTA-to-tract relation for comparison-only linkage."""

    required = (
        "GEOID_ZCTA5_20",
        "GEOID_TRACT_20",
        "AREALAND_TRACT_20",
        "AREAWATER_TRACT_20",
        "AREALAND_PART",
        "AREAWATER_PART",
    )
    missing_columns = sorted(set(required) - set(frame.columns))
    if missing_columns:
        raise GeographyError(f"ZCTA relationship is missing columns: {missing_columns}")
    output = frame[list(required)].rename(
        columns={
            "GEOID_ZCTA5_20": "zcta_id",
            "GEOID_TRACT_20": "geography_id",
            "AREALAND_TRACT_20": "tract_land_area",
            "AREAWATER_TRACT_20": "tract_water_area",
            "AREALAND_PART": "overlap_land_area",
            "AREAWATER_PART": "overlap_water_area",
        }
    )
    output["zcta_id"] = output["zcta_id"].astype("string").str.strip().str.zfill(5)
    output["geography_id"] = output["geography_id"].astype("string").str.strip()
    output = output.loc[output["zcta_id"].str.fullmatch(r"\d{5}", na=False)].copy()
    if eligible_tract_ids is not None:
        output = output.loc[output["geography_id"].isin(eligible_tract_ids)].copy()
    if output.empty:
        raise GeographyError("ZCTA relationship contains no eligible tract links")
    if output.duplicated(["geography_id", "zcta_id"]).any():
        raise GeographyError("ZCTA relationship contains duplicate tract-ZCTA rows")
    for geoid in output["geography_id"].astype(str):
        validate_tract_geoid(geoid)
    if eligible_tract_ids is not None:
        observed = set(output["geography_id"].astype(str))
        missing_tracts = sorted(eligible_tract_ids - observed)
        if missing_tracts:
            raise GeographyError(
                f"ZCTA relationship is missing eligible tracts: {missing_tracts[:3]}"
            )

    numeric = [
        "tract_land_area",
        "tract_water_area",
        "overlap_land_area",
        "overlap_water_area",
    ]
    output[numeric] = output[numeric].apply(pd.to_numeric, errors="coerce")
    if output[numeric].isna().any().any() or (output[numeric] < 0).any().any():
        raise GeographyError("ZCTA relationship area fields must be finite nonnegative numbers")
    tract_area = output["tract_land_area"] + output["tract_water_area"]
    if (tract_area <= 0).any():
        raise GeographyError("ZCTA relationship tract area must be positive")
    output["overlap_fraction"] = (
        output["overlap_land_area"] + output["overlap_water_area"]
    ) / tract_area
    coverage = output.groupby("geography_id")["overlap_fraction"].transform("sum")
    if (coverage <= 0).any() or (coverage > 1 + coverage_tolerance).any():
        raise GeographyError("ZCTA relationship overlap fractions do not reconcile")
    output["zcta_count"] = output.groupby("geography_id")["zcta_id"].transform("size")
    output["is_crossing_tract"] = output["zcta_count"] > 1
    output = output.sort_values(
        ["geography_id", "overlap_land_area", "zcta_id"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    output["is_dominant"] = ~output.duplicated("geography_id")
    dominant = output.loc[output["is_dominant"], ["geography_id", "zcta_id"]].rename(
        columns={"zcta_id": "dominant_zcta_id"}
    )
    output = output.merge(dominant, on="geography_id", how="left", validate="many_to_one")
    output["covered_fraction"] = output.groupby("geography_id")["overlap_fraction"].transform("sum")
    output["is_noncrossing"] = (~output["is_crossing_tract"]) & (
        output["covered_fraction"] >= 1 - coverage_tolerance
    )
    output["relationship_vintage"] = "2020"
    output["linkage_role"] = "comparison_metadata_only_not_disease_aggregation"
    return output.sort_values(["geography_id", "zcta_id"], ignore_index=True)


def load_zcta_tract_relationship(
    path: Path,
    *,
    eligible_tract_ids: set[str],
) -> pd.DataFrame:
    """Read frozen official bytes and return a governed comparison-only link table."""

    if not path.is_file() or path.is_symlink():
        raise GeographyError(f"frozen ZCTA relationship is missing or unsafe: {path}")
    frame = pd.read_csv(path, sep="|", dtype="string", encoding="utf-8-sig")
    return normalize_zcta_tract_relationship(
        frame,
        eligible_tract_ids=eligible_tract_ids,
    )
