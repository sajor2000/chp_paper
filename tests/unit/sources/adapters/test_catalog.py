from __future__ import annotations

import json
import csv
import io
from pathlib import Path

import httpx
import pytest
from pydantic import HttpUrl

from chicagohealthmap.sources.adapters.catalog import (
    ArcGisAdapter,
    CatalogResponseError,
    OfficialBulkAdapter,
    validate_atlas_payload,
    validate_hrsa_csv,
    validate_svi_csv,
)
from chicagohealthmap.sources.registry import load_registry
from chicagohealthmap.sources.snapshot import SnapshotWriter


ROOT = Path(__file__).parents[4]


def source(source_id: str):
    return load_registry(ROOT / "config/source_registry.yml").by_id[source_id]


def authentic_svi() -> bytes:
    return (
        ROOT / "sources/public/cdc_atsdr_svi/snapshots/2026-07-13/original/2022/data/Illinois.csv"
    ).read_bytes()


def arcgis_metadata(*, name: str = "Health Care Service Delivery Sites") -> dict[str, object]:
    return {
        "name": name,
        "id": 0,
        "fields": [{"name": "OBJECTID", "type": "esriFieldTypeOID"}],
        "maxRecordCount": 2000,
    }


def test_arcgis_metadata_precedes_id_and_feature_queries(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if not request.url.path.endswith("/query"):
            return httpx.Response(200, json=arcgis_metadata())
        if request.url.params.get("returnIdsOnly") == "true":
            return httpx.Response(200, json={"objectIdFieldName": "OBJECTID", "objectIds": [1, 2]})
        payload = json.loads((ROOT / "tests/fixtures/catalog/arcgis_page.json").read_text())
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)
    adapter = ArcGisAdapter(
        source=source("hrsa_health_centers_current"),
        return_geometry=True,
        client=client,
    )
    writer = SnapshotWriter(tmp_path, "hrsa_health_centers_current", "2026-07-14")
    manifest = adapter.fetch(writer)

    assert len(manifest.files) == 4
    assert [r.url.params.get("returnIdsOnly") for r in requests] == [None, "true", None]
    page = requests[-1].url.params
    assert page["where"] == "1=1"
    assert page["outFields"] == "*"
    assert page["returnGeometry"] == "true"
    assert page["orderByFields"] == "OBJECTID ASC"
    assert page["objectIds"] == "1,2"


@pytest.mark.parametrize(
    "ids,features,message",
    [
        ([1, 2], [1, 1], "duplicate"),
        ([1, 2], [1], "missing"),
        ([1, 2], [2, 1], "order"),
    ],
)
def test_arcgis_rejects_id_reconciliation_failures(
    tmp_path: Path, ids: list[int], features: list[int], message: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if not request.url.path.endswith("/query"):
            return httpx.Response(200, json=arcgis_metadata())
        if request.url.params.get("returnIdsOnly") == "true":
            return httpx.Response(200, json={"objectIdFieldName": "OBJECTID", "objectIds": ids})
        return httpx.Response(
            200,
            json={
                "features": [
                    {"attributes": {"OBJECTID": item}, "geometry": {"x": -87.6, "y": 41.8}}
                    for item in features
                ],
                "exceededTransferLimit": False,
            },
        )

    adapter = ArcGisAdapter(
        source=source("hrsa_health_centers_current"),
        return_geometry=True,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    writer = SnapshotWriter(tmp_path, "hrsa_health_centers_current", "2026-07-14")
    with pytest.raises(CatalogResponseError, match=message):
        adapter.fetch(writer)
    assert not writer.staging_path.exists()


def test_arcgis_rejects_metadata_drift_and_page_loop(tmp_path: Path) -> None:
    adapter = ArcGisAdapter(
        source=source("hrsa_health_centers_current"),
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json=arcgis_metadata(name="Changed"))
            )
        ),
    )
    writer = SnapshotWriter(tmp_path, "hrsa_health_centers_current", "2026-07-14")
    with pytest.raises(CatalogResponseError, match="metadata"):
        adapter.fetch(writer)
    assert not writer.staging_path.exists()


def test_arcgis_accepts_transfer_flag_after_exact_registered_ids(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if not request.url.path.endswith("/query"):
            return httpx.Response(200, json=arcgis_metadata())
        if request.url.params.get("returnIdsOnly") == "true":
            return httpx.Response(200, json={"objectIdFieldName": "OBJECTID", "objectIds": [1, 2]})
        return httpx.Response(
            200,
            json={
                "features": [{"attributes": {"OBJECTID": item}} for item in (1, 2)],
                "exceededTransferLimit": True,
            },
        )

    adapter = ArcGisAdapter(
        source=source("hrsa_health_centers_current"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    writer = SnapshotWriter(tmp_path, "hrsa_health_centers_current", "2026-07-14")

    manifest = adapter.fetch(writer)

    assert sum(item.row_count or 0 for item in manifest.files) == 2


def test_arcgis_rejects_arbitrary_same_shaped_registry_source() -> None:
    registered = source("hrsa_health_centers_current")
    changed = registered.model_copy(
        update={
            "fallback": registered.fallback.model_copy(
                update={
                    "url": HttpUrl(
                        "https://gisportal.hrsa.gov/server/rest/services/Other/MapServer/0/"
                    )
                }
            )
        }
    )
    with pytest.raises(ValueError, match="registered HRSA ArcGIS"):
        ArcGisAdapter(source=changed)


def test_official_bulk_requires_headers_and_records_provenance(tmp_path: Path) -> None:
    content = authentic_svi()

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=content,
            headers={
                "Content-Type": "text/csv",
                "Content-Length": str(len(content)),
                "ETag": '"fixed"',
                "Last-Modified": "Mon, 13 Jul 2026 00:00:00 GMT",
            },
        )

    adapter = OfficialBulkAdapter(client=httpx.Client(transport=httpx.MockTransport(handler)))
    writer = SnapshotWriter(tmp_path, "cdc_svi_2022_tract", "2026-07-14")
    manifest = adapter.fetch(source("cdc_svi_2022_tract"), writer)
    provenance = json.loads(
        (writer.final_path / "requests/acquisition.json").read_text(encoding="utf-8")
    )
    assert len(manifest.files) == 2
    assert provenance["etag"] == '"fixed"'
    assert provenance["content_length"] == len(content)
    assert provenance["resolved_url"].startswith("https://svi.cdc.gov/")
    assert len(provenance["sha256"]) == 64


def test_official_bulk_uses_shared_retry_boundary(tmp_path: Path) -> None:
    content = authentic_svi()
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503)
        return httpx.Response(
            200,
            content=content,
            headers={
                "Content-Type": "text/csv",
                "Content-Length": str(len(content)),
                "ETag": '"fixed"',
                "Last-Modified": "Mon, 13 Jul 2026 00:00:00 GMT",
            },
        )

    writer = SnapshotWriter(tmp_path, "cdc_svi_2022_tract", "2026-07-14")
    OfficialBulkAdapter(
        client=httpx.Client(transport=httpx.MockTransport(handler)), sleep=lambda _: None
    ).fetch(source("cdc_svi_2022_tract"), writer)

    assert calls == 2


@pytest.mark.parametrize("missing", ["ETag", "Last-Modified", "Content-Length"])
def test_official_bulk_rejects_missing_integrity_header(tmp_path: Path, missing: str) -> None:
    content = b"a,b\n1,2\n"
    headers = {
        "Content-Type": "text/csv",
        "Content-Length": str(len(content)),
        "ETag": '"fixed"',
        "Last-Modified": "Mon, 13 Jul 2026 00:00:00 GMT",
    }
    del headers[missing]

    def handler(_: httpx.Request) -> httpx.Response:
        response = httpx.Response(200, content=content, headers=headers)
        if missing == "Content-Length":
            del response.headers["Content-Length"]
        return response

    client = httpx.Client(transport=httpx.MockTransport(handler))
    writer = SnapshotWriter(tmp_path, "cdc_svi_2022_tract", "2026-07-14")
    with pytest.raises(CatalogResponseError, match=missing.casefold().replace("-", "[- ]?")):
        OfficialBulkAdapter(client=client).fetch(source("cdc_svi_2022_tract"), writer)
    assert not writer.staging_path.exists()


def test_official_bulk_rejects_redirect() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(302, headers={"Location": "https://example.com/data.csv"})
        )
    )
    with pytest.raises(CatalogResponseError, match="redirect"):
        OfficialBulkAdapter(client=client).response(source("cdc_svi_2022_tract"))


@pytest.mark.parametrize(
    "header,value,message",
    [
        ("ETag", "unquoted", "ETag"),
        ("ETag", 'W/"weak"', "ETag"),
        ("Last-Modified", "yesterday", "Last-Modified"),
    ],
)
def test_official_bulk_rejects_malformed_integrity_headers(
    header: str, value: str, message: str
) -> None:
    content = (ROOT / "tests/fixtures/catalog/official_bulk.csv").read_bytes()
    headers = {
        "Content-Type": "text/csv",
        "Content-Length": str(len(content)),
        "ETag": '"fixed"',
        "Last-Modified": "Mon, 13 Jul 2026 00:00:00 GMT",
    }
    headers[header] = value
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, content=content, headers=headers)
        )
    )
    with pytest.raises(CatalogResponseError, match=message):
        OfficialBulkAdapter(client=client).response(source("cdc_svi_2022_tract"))


def test_official_bulk_rejects_unregistered_octet_stream() -> None:
    content = (ROOT / "tests/fixtures/catalog/official_bulk.csv").read_bytes()
    headers = {
        "Content-Type": "application/octet-stream",
        "Content-Length": str(len(content)),
        "ETag": '"fixed"',
        "Last-Modified": "Mon, 13 Jul 2026 00:00:00 GMT",
    }
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, content=content, headers=headers)
        )
    )
    with pytest.raises(CatalogResponseError):
        OfficialBulkAdapter(client=client).response(source("cdc_svi_2022_tract"))


def test_family_semantic_validators_reject_wrong_identity() -> None:
    atlas = {
        "params": {"topic": "VRDTHR", "period": "2024", "layer": "neighborhood"},
        "count": 0,
        "results": [],
    }
    with pytest.raises(CatalogResponseError, match="topic"):
        validate_atlas_payload(atlas, topic="VRLE", period="2024")
    with pytest.raises(CatalogResponseError, match="SVI"):
        validate_svi_csv(b"FIPS,RPL_THEMES\n17001000100,nan\n")
    with pytest.raises(CatalogResponseError, match="HRSA"):
        validate_hrsa_csv(b"Site Name,X\nA,nan\n")


def test_svi_requires_corrected_release_fields() -> None:
    with pytest.raises(CatalogResponseError, match="SVI"):
        validate_svi_csv(
            b"FIPS,RPL_THEMES,RPL_THEME1,RPL_THEME2,RPL_THEME3,RPL_THEME4,F_TOTAL\n17001000100,0,0,0,0,0,0\n"
        )


def test_hrsa_rejects_spreadsheet_formula_and_bad_update_date() -> None:
    path = (
        ROOT
        / "sources/public/hrsa_health_centers/snapshots/2026-07-13/original/data/Health_Center_Service_Delivery_and_LookAlike_Sites.csv"
    )
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        fields = next(reader)
        row = next(reader)
    row[fields.index("Site Name")] = "=FORMULA"
    row[fields.index("Data Warehouse Record Create Date")] = "not-a-date"
    body = io.StringIO()
    writer = csv.writer(body)
    writer.writerow(fields)
    writer.writerow(row)
    with pytest.raises(CatalogResponseError):
        validate_hrsa_csv(body.getvalue().encode())


@pytest.mark.parametrize(
    "validator,path",
    [
        (
            validate_svi_csv,
            ROOT
            / "sources/public/cdc_atsdr_svi/snapshots/2026-07-13/original/2022/data/Illinois.csv",
        ),
        (
            validate_hrsa_csv,
            ROOT
            / "sources/public/hrsa_health_centers/snapshots/2026-07-13/original/data/Health_Center_Service_Delivery_and_LookAlike_Sites.csv",
        ),
    ],
)
@pytest.mark.parametrize("mutation", ["extra", "missing"])
def test_live_catalog_csv_rejects_any_schema_drift(validator, path: Path, mutation: str) -> None:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header = next(csv.reader([lines[0]]))
    if mutation == "extra":
        header.append("UNREGISTERED_COLUMN")
    else:
        header.pop()
    output = io.StringIO()
    csv.writer(output).writerow(header)
    with pytest.raises(CatalogResponseError, match="schema"):
        validator((output.getvalue() + "\n".join(lines[1:]) + "\n").encode())
