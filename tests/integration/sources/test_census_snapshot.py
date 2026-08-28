from __future__ import annotations

import json
import zipfile
from pathlib import Path

import geopandas as gpd
import httpx
import pytest
import respx
import pyogrio
from shapely.geometry import Polygon

from chicagohealthmap.sources.adapters.census import (
    CensusAcsAdapter,
    CensusResponseError,
    CensusTigerAdapter,
    CensusZctaRelationshipAdapter,
)
from chicagohealthmap.sources.registry import load_registry
from chicagohealthmap.sources.snapshot import SnapshotWriter


ROOT = Path(__file__).parents[3]


@respx.mock
def test_acs_fetch_preserves_one_raw_response_and_redacted_metadata_per_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = json.loads((ROOT / "tests/fixtures/census/acs_group_response.json").read_text())
    source = load_registry(ROOT / "config/source_registry.yml").by_id["census_acs_2024_5y"]
    monkeypatch.setenv("CENSUS_API_KEY", "fixture-secret-key")
    route = respx.get("https://api.census.gov/data/2024/acs/acs5").mock(
        return_value=httpx.Response(200, json=payload)
    )
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-14")

    manifest = CensusAcsAdapter(year=2024, groups=("B01001",)).fetch(source, writer)

    assert route.call_count == 1
    request = route.calls[0].request
    assert request.url.params["get"] == "NAME,group(B01001)"
    assert request.url.params["for"] == "tract:*"
    assert request.url.params["in"] == "state:17 county:031"
    assert request.url.params["key"] == "fixture-secret-key"
    final = tmp_path / source.source_id / "snapshots/2026-07-14"
    raw = final / "original/2024/acs5/groups/B01001.json"
    metadata = json.loads((final / "requests/2024/acs5/groups/B01001.json").read_text())
    finalized_manifest = json.loads((final / "manifest.json").read_text())
    assert json.loads(raw.read_text()) == payload
    assert metadata["group"] == "B01001"
    assert metadata["row_count"] == 2
    assert len(metadata["header_sha256"]) == 64
    assert metadata["query"] == {
        "for": "tract:*",
        "get": "NAME,group(B01001)",
        "in": "state:17 county:031",
    }
    assert "fixture-secret-key" not in json.dumps(metadata)
    assert finalized_manifest["acquisitions"] == [
        {
            "group": "B01001",
            "url": "https://api.census.gov/data/2024/acs/acs5",
            "parameters": [
                ["get", "NAME,group(B01001)"],
                ["for", "tract:*"],
                ["in", "state:17 county:031"],
            ],
            "row_count": 2,
            "header_sha256": metadata["header_sha256"],
        }
    ]
    assert "fixture-secret-key" not in (final / "manifest.json").read_text()
    assert [item.row_count for item in manifest.files if item.path.startswith("original/")] == [2]


@respx.mock
def test_acs_fetch_disables_redirects_even_for_a_redirecting_injected_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = load_registry(ROOT / "config/source_registry.yml").by_id["census_acs_2024_5y"]
    monkeypatch.setenv("CENSUS_API_KEY", "fixture-secret-key")
    first = respx.get("https://api.census.gov/data/2024/acs/acs5").mock(
        return_value=httpx.Response(302, headers={"location": "https://example.org/capture"})
    )
    redirected = respx.get("https://example.org/capture").mock(return_value=httpx.Response(200))
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-14")

    with httpx.Client(follow_redirects=True) as client:
        with pytest.raises(CensusResponseError, match="HTTP 302"):
            CensusAcsAdapter(year=2024, groups=("B01001",), client=client).fetch(source, writer)

    assert first.call_count == 1
    assert redirected.call_count == 0
    assert not writer.staging_path.exists()


def test_tiger_fetch_preserves_zip_before_cook_filter_and_original_crs(tmp_path: Path) -> None:
    source = load_registry(ROOT / "config/source_registry.yml").by_id["census_tiger_2024_tract"]
    fixture = ROOT / "tests/fixtures/census/tiger_tract_fixture.zip"
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-14")

    manifest = CensusTigerAdapter(year=2024, archive_path=fixture).fetch(source, writer)

    final = tmp_path / source.source_id / "snapshots/2026-07-14"
    preserved = final / "original/2024/tract/tl_2024_17_tract.zip"
    parquet = final / "interim/2024/cook_county_tracts.parquet"
    assert preserved.read_bytes() == fixture.read_bytes()
    cook = gpd.read_parquet(parquet)
    assert cook.crs == "EPSG:4269"
    assert cook["GEOID"].tolist() == ["17031010100"]
    assert cook["COUNTYFP"].tolist() == ["031"]
    assert cook["source_id"].tolist() == [source.source_id]
    assert cook["source_release"].tolist() == [source.release]
    assert cook.geometry.notna().all()
    assert {item.path for item in manifest.files} == {
        "original/2024/tract/tl_2024_17_tract.zip",
        "requests/2024/tract/archive.json",
        "interim/2024/cook_county_tracts.parquet",
    }


def test_tiger_fetch_rejects_output_alias_before_publication(tmp_path: Path) -> None:
    source = load_registry(ROOT / "config/source_registry.yml").by_id["census_tiger_2024_tract"]
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-14")
    adapter = CensusTigerAdapter(year=2024, archive_path=writer.staging_path / "alias.zip")
    adapter.archive_path.write_bytes(b"PK")  # type: ignore[union-attr]

    with pytest.raises(Exception):
        adapter.fetch(source, writer)

    assert not writer.staging_path.exists()


@respx.mock
def test_zcta_relationship_fetch_preserves_official_bytes_and_record_layout(tmp_path: Path) -> None:
    source = load_registry(ROOT / "config/source_registry.yml").by_id[
        "census_zcta_2020_tract_relationship"
    ]
    payload = (
        "OID_ZCTA5_20|GEOID_ZCTA5_20|NAMELSAD_ZCTA5_20|AREALAND_ZCTA5_20|"
        "AREAWATER_ZCTA5_20|MTFCC_ZCTA5_20|CLASSFP_ZCTA5_20|FUNCSTAT_ZCTA5_20|"
        "OID_TRACT_20|GEOID_TRACT_20|NAMELSAD_TRACT_20|AREALAND_TRACT_20|"
        "AREAWATER_TRACT_20|MTFCC_TRACT_20|FUNCSTAT_TRACT_20|AREALAND_PART|"
        "AREAWATER_PART\n"
        "22160601|60601|ZCTA5 60601|100|0|G6350|B5|S|207901|17031010100|"
        "Census Tract 101|100|0|G5020|S|100|0\n"
    ).encode()
    route = respx.get(str(source.endpoint_url)).mock(
        return_value=httpx.Response(200, content=payload)
    )
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-16")

    manifest = CensusZctaRelationshipAdapter().fetch(source, writer)

    final = tmp_path / source.source_id / "snapshots/2026-07-16"
    raw = final / "original/2020/tab20_zcta520_tract20_natl.txt"
    assert route.call_count == 1
    assert raw.read_bytes() == payload
    assert [item.row_count for item in manifest.files if item.path.startswith("original/")] == [1]


def _write_modified_tiger_fixture(tmp_path: Path, mutation: str) -> Path:
    source = ROOT / "tests/fixtures/census/tiger_tract_fixture.zip"
    frame = pyogrio.read_dataframe(f"/vsizip/{source.resolve()}")
    if mutation == "duplicate":
        frame.loc[1, ["STATEFP", "COUNTYFP", "TRACTCE", "GEOID"]] = frame.loc[
            0, ["STATEFP", "COUNTYFP", "TRACTCE", "GEOID"]
        ]
    elif mutation == "malformed":
        frame.loc[0, "COUNTYFP"] = "31"
    elif mutation == "self_intersection":
        frame.loc[0, "geometry"] = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    directory = tmp_path / mutation
    directory.mkdir()
    pyogrio.write_dataframe(frame, directory / "tl_2024_17_tract.shp", driver="ESRI Shapefile")
    archive_path = tmp_path / f"{mutation}.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for component in directory.glob("tl_2024_17_tract.*"):
            archive.write(component, component.name)
    return archive_path


@pytest.mark.parametrize("mutation", ["duplicate", "malformed", "self_intersection"])
def test_tiger_fetch_rejects_adversarial_geography_and_geometry(
    tmp_path: Path, mutation: str
) -> None:
    source = load_registry(ROOT / "config/source_registry.yml").by_id["census_tiger_2024_tract"]
    archive = _write_modified_tiger_fixture(tmp_path, mutation)
    writer = SnapshotWriter(tmp_path / "output", source.source_id, "2026-07-14")

    with pytest.raises(CensusResponseError):
        CensusTigerAdapter(year=2024, archive_path=archive).fetch(source, writer)

    assert not writer.staging_path.exists()
