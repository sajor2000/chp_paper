import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from chicagohealthmap.config import ProjectPaths

from chicagohealthmap.external.geography import (
    GeographyError,
    build_authoritative_tract_overlays,
    build_tract_community_overlay,
    normalize_zcta_tract_relationship,
    validate_tract_geography,
)

ROOT = ProjectPaths.discover()


def _tracts() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "STATEFP": ["17", "17"],
            "COUNTYFP": ["031", "031"],
            "GEOID": ["17031000001", "17031000002"],
            "tract_vintage": ["2020", "2024"],
        },
        geometry=[
            Polygon([(0, 0), (2, 0), (2, 1), (0, 1)]),
            Polygon([(0, 1), (1, 1), (1, 2), (0, 2)]),
        ],
        crs="EPSG:3435",
    )


def test_tract_validation_requires_geoid_state_county_valid_geometry_and_crs() -> None:
    validated = validate_tract_geography(_tracts())
    assert set(validated["tract_vintage"]) == {"2020", "2024"}

    bad = _tracts()
    bad.loc[0, "GEOID"] = "17031"
    with pytest.raises(GeographyError, match="11-digit"):
        validate_tract_geography(bad)


def test_overlay_uses_intersection_area_and_records_crossing_tracts_and_slivers() -> None:
    tracts = _tracts().iloc[[0]].copy()
    communities = gpd.GeoDataFrame(
        {"community_area_id": ["01", "02"]},
        geometry=[
            Polygon([(0, 0), (1.5, 0), (1.5, 1), (0, 1)]),
            Polygon([(1.5, 0), (2, 0), (2, 1), (1.5, 1)]),
        ],
        crs=tracts.crs,
    )

    result = build_tract_community_overlay(tracts, communities, sliver_tolerance=0.01)

    assert result.weights["weight"].tolist() == pytest.approx([0.75, 0.25])
    assert result.weights.groupby("geography_id")["weight"].sum().tolist() == pytest.approx([1.0])
    assert result.crossing_tract_ids == ("17031000001",)
    assert result.slivers.empty


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [("STATEFP", "18", "Illinois"), ("COUNTYFP", "043", "Cook County")],
)
def test_tract_validation_rejects_wrong_state_or_county(
    column: str, value: str, message: str
) -> None:
    frame = _tracts()
    frame[column] = value
    with pytest.raises(GeographyError, match=message):
        validate_tract_geography(frame)


def test_tract_validation_rejects_missing_crs_and_empty_or_invalid_geometry() -> None:
    without_crs = _tracts().set_crs(None, allow_override=True)
    with pytest.raises(GeographyError, match="declare a CRS"):
        validate_tract_geography(without_crs)

    empty = _tracts()
    empty.loc[0, "geometry"] = Polygon()
    with pytest.raises(GeographyError, match="nonempty"):
        validate_tract_geography(empty)

    invalid = _tracts()
    invalid.loc[0, "geometry"] = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
    with pytest.raises(GeographyError, match="valid"):
        validate_tract_geography(invalid)


def test_overlay_rejects_nonprojected_crs() -> None:
    tracts = _tracts().to_crs("EPSG:4326")
    communities = gpd.GeoDataFrame(
        {"community_area_id": ["01"]},
        geometry=[tracts.geometry.iloc[0]],
        crs=tracts.crs,
    )
    with pytest.raises(GeographyError, match="projected CRS"):
        build_tract_community_overlay(tracts.iloc[[0]], communities)


def test_authoritative_frozen_overlays_have_unit_weights_and_provenance() -> None:
    overlays = build_authoritative_tract_overlays(ROOT)
    assert set(overlays) == {"2020", "2024"}
    for year, frame in overlays.items():
        assert not frame.empty
        assert frame.groupby("geography_id")["weight"].sum().tolist() == pytest.approx(
            [1.0] * frame["geography_id"].nunique(), abs=1e-6
        )
        assert set(frame["tract_vintage"]) == {year}
        assert {"is_crossing_tract", "is_sliver", "source_id", "snapshot_id"} <= set(frame.columns)
        assert frame["is_crossing_tract"].any()


def test_zcta_relationship_retains_splits_and_selects_dominant_land_overlap() -> None:
    relationship = pd.DataFrame(
        [
            {
                "GEOID_ZCTA5_20": "60601",
                "GEOID_TRACT_20": "17031010100",
                "AREALAND_TRACT_20": "100",
                "AREAWATER_TRACT_20": "0",
                "AREALAND_PART": "100",
                "AREAWATER_PART": "0",
            },
            {
                "GEOID_ZCTA5_20": "60602",
                "GEOID_TRACT_20": "17031010200",
                "AREALAND_TRACT_20": "100",
                "AREAWATER_TRACT_20": "0",
                "AREALAND_PART": "70",
                "AREAWATER_PART": "0",
            },
            {
                "GEOID_ZCTA5_20": "60603",
                "GEOID_TRACT_20": "17031010200",
                "AREALAND_TRACT_20": "100",
                "AREAWATER_TRACT_20": "0",
                "AREALAND_PART": "30",
                "AREAWATER_PART": "0",
            },
        ]
    )

    result = normalize_zcta_tract_relationship(
        relationship, eligible_tract_ids={"17031010100", "17031010200"}
    )

    contained = result.loc[result["geography_id"] == "17031010100"].iloc[0]
    split = result.loc[result["geography_id"] == "17031010200"]
    assert contained["dominant_zcta_id"] == "60601"
    assert bool(contained["is_noncrossing"])
    assert split["is_crossing_tract"].all()
    assert split.loc[split["is_dominant"], "zcta_id"].tolist() == ["60602"]
    assert split["overlap_fraction"].sum() == pytest.approx(1.0)
    assert result.columns[:6].tolist() == [
        "zcta_id",
        "geography_id",
        "tract_land_area",
        "tract_water_area",
        "overlap_land_area",
        "overlap_water_area",
    ]


def test_zcta_relationship_fails_closed_for_missing_or_duplicate_tracts() -> None:
    duplicate = pd.DataFrame(
        [
            {
                "GEOID_ZCTA5_20": "60601",
                "GEOID_TRACT_20": "17031010100",
                "AREALAND_TRACT_20": "100",
                "AREAWATER_TRACT_20": "0",
                "AREALAND_PART": "100",
                "AREAWATER_PART": "0",
            }
        ]
        * 2
    )
    with pytest.raises(GeographyError, match="duplicate"):
        normalize_zcta_tract_relationship(duplicate, eligible_tract_ids={"17031010100"})
    with pytest.raises(GeographyError, match="missing eligible"):
        normalize_zcta_tract_relationship(
            duplicate.iloc[:1], eligible_tract_ids={"17031010100", "17031099999"}
        )
