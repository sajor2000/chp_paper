from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from chicagohealthmap.sources.adapters.socrata import SocrataAdapter, SocrataResponseError
from chicagohealthmap.sources.registry import load_registry
from chicagohealthmap.sources.snapshot import SnapshotWriter


ROOT = Path(__file__).parents[3]


def _source(source_id: str):
    return load_registry(ROOT / "config/source_registry.yml").by_id[source_id]


def _community_page() -> dict[str, object]:
    template = json.loads((ROOT / "tests/fixtures/socrata/page_0001.json").read_text())["features"][
        0
    ]
    features = []
    for area_id in range(1, 78):
        feature = json.loads(json.dumps(template))
        feature["properties"].update(
            area_numbe=str(area_id),
            area_num_1=str(area_id),
            community=f"AREA {area_id}",
        )
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}


@respx.mock
def test_fetches_metadata_count_then_pages_and_never_persists_optional_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source("chicago_community_areas_current")
    metadata = json.loads((ROOT / "tests/fixtures/socrata/metadata.json").read_text())
    page = _community_page()
    token = "runtime-only-socrata-token"
    monkeypatch.setenv("SOCRATA_APP_TOKEN", token)
    metadata_route = respx.get("https://data.cityofchicago.org/api/views/igwz-8jzy").mock(
        return_value=httpx.Response(200, json=metadata)
    )
    count_route = respx.get(
        "https://data.cityofchicago.org/resource/igwz-8jzy.json",
        params={"$select": "count(*) AS count"},
    ).mock(return_value=httpx.Response(200, json=[{"count": "77"}]))
    page_route = respx.get(
        "https://data.cityofchicago.org/resource/igwz-8jzy.geojson",
        params={
            "$select": "the_geom,area_numbe,community,area_num_1,shape_area,shape_len",
            "$order": "area_numbe ASC",
            "$limit": "50000",
            "$offset": "0",
        },
    ).mock(return_value=httpx.Response(200, json=page))
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-14")

    manifest = SocrataAdapter().fetch(source, writer)

    assert metadata_route.call_count == count_route.call_count == page_route.call_count == 1
    assert all(
        call.request.headers["X-App-Token"] == token
        for call in (metadata_route.calls[0], count_route.calls[0], page_route.calls[0])
    )
    final = tmp_path / source.source_id / "snapshots/2026-07-14"
    assert json.loads((final / "original/metadata/socrata_view.json").read_text()) == metadata
    assert json.loads((final / "original/pages/page_0001.geojson").read_text()) == page
    request_manifest = json.loads((final / "requests/request_manifest.json").read_text())
    assert request_manifest["count_query"] == {"$select": "count(*) AS count"}
    assert request_manifest["page_query"]["$limit"] == "50000"
    assert request_manifest["row_count"] == 77
    assert request_manifest["page_count"] == 1
    assert request_manifest["release"] == source.release
    assert request_manifest["semantics"] == "official community-area boundary geometry"
    serialized = "\n".join(
        path.read_text(errors="ignore") for path in final.rglob("*") if path.is_file()
    )
    assert token not in serialized
    assert len(manifest.files) == 4


@respx.mock
def test_fetch_fails_closed_on_duplicate_keys_count_mismatch_order_and_bad_geometry(
    tmp_path: Path,
) -> None:
    source = _source("chicago_community_areas_current")
    metadata = json.loads((ROOT / "tests/fixtures/socrata/metadata.json").read_text())
    original = _community_page()
    mutations = {
        "duplicate primary key": lambda page: page["features"][1]["properties"].update(
            area_numbe="1"
        ),
        "stable primary-key order": lambda page: page["features"].reverse(),
        "geometry": lambda page: page["features"][0].update(
            geometry={"type": "MultiPolygon", "coordinates": [1]}
        ),
    }
    for index, (message, mutate) in enumerate(mutations.items()):
        page = json.loads(json.dumps(original))
        mutate(page)
        respx.get("https://data.cityofchicago.org/api/views/igwz-8jzy").mock(
            return_value=httpx.Response(200, json=metadata)
        )
        respx.get(
            "https://data.cityofchicago.org/resource/igwz-8jzy.json",
            params={"$select": "count(*) AS count"},
        ).mock(return_value=httpx.Response(200, json=[{"count": "77"}]))
        respx.get(
            "https://data.cityofchicago.org/resource/igwz-8jzy.geojson",
            params={
                "$select": "the_geom,area_numbe,community,area_num_1,shape_area,shape_len",
                "$order": "area_numbe ASC",
                "$limit": "50000",
                "$offset": "0",
            },
        ).mock(return_value=httpx.Response(200, json=page))
        writer = SnapshotWriter(tmp_path / str(index), source.source_id, "2026-07-14")
        with pytest.raises(SocrataResponseError, match=message):
            SocrataAdapter().fetch(source, writer)
        assert not writer.staging_path.exists()


@respx.mock
def test_fetch_rejects_bad_response_types_content_limits_and_redacts_transport_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source("chicago_community_areas_current")
    secret = "must-never-appear"
    monkeypatch.setenv("SOCRATA_APP_TOKEN", secret)
    respx.get("https://data.cityofchicago.org/api/views/igwz-8jzy").mock(
        side_effect=httpx.ConnectError(secret)
    )
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-14")

    with pytest.raises(SocrataResponseError) as captured:
        SocrataAdapter().fetch(source, writer)

    assert secret not in str(captured.value)
    assert captured.value.__cause__ is None
    assert not writer.staging_path.exists()


@respx.mock
def test_anonymous_places_fetch_preserves_only_registered_model_based_fields(
    tmp_path: Path,
) -> None:
    source = _source("cdc_places_current_tract")
    frozen_metadata = json.loads(
        (
            ROOT
            / "sources/public/cdc_places/snapshots/2026-07-13/original/2025_release/metadata/socrata_view.json"
        ).read_text()
    )
    row = {
        "stateabbr": "IL",
        "statedesc": "Illinois",
        "countyname": "Cook",
        "countyfips": "17031",
        "tractfips": "17031010100",
        "totalpopulation": "1000",
        "totalpop18plus": "800",
        "bphigh_crudeprev": "30.1",
        "bphigh_crude95ci": "(28,32)",
        "diabetes_crudeprev": "10.2",
        "diabetes_crude95ci": "(9,11)",
        "copd_crudeprev": "6.3",
        "copd_crude95ci": "(5,7)",
    }
    metadata_route = respx.get("https://data.cdc.gov/api/views/yjkw-uj5s").mock(
        return_value=httpx.Response(200, json=frozen_metadata)
    )
    count_route = respx.get(
        "https://data.cdc.gov/resource/yjkw-uj5s.json",
        params={"$select": "count(*) AS count", "$where": "stateabbr='IL' AND countyfips='17031'"},
    ).mock(return_value=httpx.Response(200, json=[{"count": "1"}]))
    page_route = respx.get(
        "https://data.cdc.gov/resource/yjkw-uj5s.csv",
        params={
            "$select": dict(source.request.parameters)["$select"],
            "$where": "stateabbr='IL' AND countyfips='17031'",
            "$order": "tractfips ASC",
            "$limit": "50000",
            "$offset": "0",
        },
    ).mock(
        return_value=httpx.Response(
            200,
            content=(
                ",".join(row)
                + "\n"
                + ",".join(f'"{value}"' if "," in value else value for value in row.values())
                + "\n"
            ).encode(),
            headers={"content-type": "text/csv"},
        )
    )

    manifest = SocrataAdapter(environ={}).fetch(
        source, SnapshotWriter(tmp_path, source.source_id, "2026-07-14")
    )

    assert "X-App-Token" not in metadata_route.calls[0].request.headers
    assert count_route.call_count == page_route.call_count == 1
    final = tmp_path / source.source_id / "snapshots/2026-07-14"
    request_manifest = json.loads((final / "requests/request_manifest.json").read_text())
    assert (
        request_manifest["semantics"] == "model-based small-area estimates; not observed prevalence"
    )
    assert request_manifest["row_count"] == 1
    assert any(item.row_count == 1 for item in manifest.files)


@respx.mock
@pytest.mark.parametrize(
    ("bad_page", "message"),
    [
        ({"unexpected": []}, "response type"),
        ({"type": "FeatureCollection", "features": "not-a-list"}, "response type"),
    ],
)
def test_fetch_rejects_invalid_page_response_types_and_cleans_staging(
    tmp_path: Path, bad_page: object, message: str
) -> None:
    source = _source("chicago_community_areas_current")
    metadata = json.loads((ROOT / "tests/fixtures/socrata/metadata.json").read_text())
    respx.get("https://data.cityofchicago.org/api/views/igwz-8jzy").mock(
        return_value=httpx.Response(200, json=metadata)
    )
    respx.get(
        "https://data.cityofchicago.org/resource/igwz-8jzy.json",
        params={"$select": "count(*) AS count"},
    ).mock(return_value=httpx.Response(200, json=[{"count": "77"}]))
    respx.get(
        "https://data.cityofchicago.org/resource/igwz-8jzy.geojson",
        params={
            "$select": "the_geom,area_numbe,community,area_num_1,shape_area,shape_len",
            "$order": "area_numbe ASC",
            "$limit": "50000",
            "$offset": "0",
        },
    ).mock(return_value=httpx.Response(200, json=bad_page))
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-14")

    with pytest.raises(SocrataResponseError, match=message):
        SocrataAdapter().fetch(source, writer)

    assert not writer.staging_path.exists()


@respx.mock
def test_fetch_rejects_page_content_over_limit_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source("chicago_community_areas_current")
    metadata = json.loads((ROOT / "tests/fixtures/socrata/metadata.json").read_text())
    monkeypatch.setattr("chicagohealthmap.sources.adapters.socrata._MAX_PAGE_BYTES", 10)
    respx.get("https://data.cityofchicago.org/api/views/igwz-8jzy").mock(
        return_value=httpx.Response(200, json=metadata)
    )
    respx.get(
        "https://data.cityofchicago.org/resource/igwz-8jzy.json",
        params={"$select": "count(*) AS count"},
    ).mock(return_value=httpx.Response(200, json=[{"count": "77"}]))
    respx.get(
        "https://data.cityofchicago.org/resource/igwz-8jzy.geojson",
        params={
            "$select": "the_geom,area_numbe,community,area_num_1,shape_area,shape_len",
            "$order": "area_numbe ASC",
            "$limit": "50000",
            "$offset": "0",
        },
    ).mock(return_value=httpx.Response(200, json={"type": "FeatureCollection", "features": []}))
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-14")

    with pytest.raises(SocrataResponseError, match="request failed"):
        SocrataAdapter().fetch(source, writer)

    assert not writer.staging_path.exists()


@respx.mock
@pytest.mark.parametrize("status", [408, 425, 429, 500, 502, 503, 504])
def test_socrata_retries_exact_transient_status_and_validates_json_content_type(
    tmp_path: Path, status: int
) -> None:
    source = _source("chicago_community_areas_current")
    metadata = json.loads((ROOT / "tests/fixtures/socrata/metadata.json").read_text())
    metadata_route = respx.get("https://data.cityofchicago.org/api/views/igwz-8jzy").mock(
        side_effect=[
            httpx.Response(
                status, headers={"Retry-After": "0", "content-type": "application/json"}
            ),
            httpx.Response(200, json=metadata),
        ]
    )
    respx.get(
        "https://data.cityofchicago.org/resource/igwz-8jzy.json",
        params={"$select": "count(*) AS count"},
    ).mock(return_value=httpx.Response(200, json=[{"count": "77"}]))
    respx.get("https://data.cityofchicago.org/resource/igwz-8jzy.geojson").mock(
        return_value=httpx.Response(200, json=_community_page())
    )

    SocrataAdapter(sleep=lambda _: None).fetch(
        source, SnapshotWriter(tmp_path, source.source_id, "2026-07-14")
    )

    assert metadata_route.call_count == 2

    bad_writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-15")
    respx.get("https://data.cityofchicago.org/api/views/igwz-8jzy").mock(
        return_value=httpx.Response(200, content=b"{}", headers={"content-type": "text/html"})
    )
    with pytest.raises(SocrataResponseError, match="request failed"):
        SocrataAdapter(sleep=lambda _: None).fetch(source, bad_writer)
    assert not bad_writer.staging_path.exists()


def test_socrata_forces_timeout_disables_redirects_and_redacts_token(tmp_path: Path) -> None:
    source = _source("chicago_community_areas_current")
    secret = "socrata-review-secret"
    observed: list[dict[str, float]] = []
    evil_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal evil_calls
        observed.append(request.extensions["timeout"])
        if request.url.host == "evil.example":
            evil_calls += 1
            return httpx.Response(200, json={})
        return httpx.Response(302, headers={"location": "https://evil.example/collect"})

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True, timeout=1)
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-14")
    try:
        with pytest.raises(SocrataResponseError) as captured:
            SocrataAdapter(
                client=client, environ={"SOCRATA_APP_TOKEN": secret}, sleep=lambda _: None
            ).fetch(source, writer)
    finally:
        client.close()
    assert observed == [{"connect": 20.0, "read": 120.0, "write": 120.0, "pool": 20.0}]
    assert evil_calls == 0
    assert secret not in repr(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    assert not writer.staging_path.exists()


def test_socrata_rejects_oversized_stream_while_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source("chicago_community_areas_current")
    metadata = json.loads((ROOT / "tests/fixtures/socrata/metadata.json").read_text())

    class LargeStream(httpx.SyncByteStream):
        def __iter__(self):
            yield b"12345678"
            yield b"abcdefgh"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/api/views/"):
            return httpx.Response(200, json=metadata)
        if request.url.path.endswith(".json"):
            return httpx.Response(200, json=[{"count": "77"}])
        return httpx.Response(
            200, stream=LargeStream(), headers={"content-type": "application/geo+json"}
        )

    monkeypatch.setattr("chicagohealthmap.sources.adapters.socrata._MAX_PAGE_BYTES", 10)
    client = httpx.Client(transport=httpx.MockTransport(handler))
    writer = SnapshotWriter(tmp_path, source.source_id, "2026-07-14")
    try:
        with pytest.raises(SocrataResponseError, match="request failed"):
            SocrataAdapter(client=client, sleep=lambda _: None).fetch(source, writer)
    finally:
        client.close()
    assert not writer.staging_path.exists()
