"""Fail-closed Socrata acquisition for the two approved public datasets."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from urllib.parse import urlsplit

import httpx
from pydantic import HttpUrl
from shapely.errors import GEOSException  # type: ignore[import-untyped]
from shapely.geometry import shape  # type: ignore[import-untyped]

from chicagohealthmap.sources.adapters.base import AcquisitionPlan
from chicagohealthmap.sources.http import AcquisitionError, HttpAcquirer
from chicagohealthmap.sources.models import SnapshotManifest
from chicagohealthmap.sources.registry import RegistrySource
from chicagohealthmap.sources.snapshot import SnapshotWriter, sha256_file

PAGE_LIMIT = 50_000
_MAX_METADATA_BYTES = 16 * 1024 * 1024
_MAX_COUNT_BYTES = 1024 * 1024
_MAX_PAGE_BYTES = 256 * 1024 * 1024
_MAX_ROWS = 2_000_000
_APPROVED_IDS = frozenset({"cdc_places_current_tract", "chicago_community_areas_current"})
_GEOMETRY_TYPES = frozenset({"polygon", "multipolygon"})
_TRACT_GEOID = re.compile(r"^17\d{9}$")
_PLACES_FIELDS = (
    "stateabbr",
    "statedesc",
    "countyname",
    "countyfips",
    "tractfips",
    "totalpopulation",
    "totalpop18plus",
    "bphigh_crudeprev",
    "bphigh_crude95ci",
    "diabetes_crudeprev",
    "diabetes_crude95ci",
    "copd_crudeprev",
    "copd_crude95ci",
)
_CHICAGO_FIELDS = (
    "the_geom",
    "area_numbe",
    "community",
    "area_num_1",
    "shape_area",
    "shape_len",
)
_FIELD_TYPES: dict[str, dict[str, str]] = {
    "cdc_places_current_tract": {
        "stateabbr": "text",
        "statedesc": "text",
        "countyname": "text",
        "countyfips": "text",
        "tractfips": "text",
        "totalpopulation": "text",
        "totalpop18plus": "number",
        "bphigh_crudeprev": "number",
        "bphigh_crude95ci": "text",
        "diabetes_crudeprev": "number",
        "diabetes_crude95ci": "text",
        "copd_crudeprev": "number",
        "copd_crude95ci": "text",
    },
    "chicago_community_areas_current": {
        "the_geom": "multipolygon",
        "area_numbe": "number",
        "community": "text",
        "area_num_1": "text",
        "shape_area": "number",
        "shape_len": "number",
    },
}
_EXACT_REQUESTS: dict[str, dict[str, str]] = {
    "cdc_places_current_tract": {
        "$select": ",".join(_PLACES_FIELDS),
        "$where": "stateabbr='IL' AND countyfips='17031'",
        "$order": "tractfips ASC",
        "$limit": str(PAGE_LIMIT),
    },
    "chicago_community_areas_current": {
        "$select": ",".join(_CHICAGO_FIELDS),
        "$order": "area_numbe ASC",
        "$limit": str(PAGE_LIMIT),
    },
}
_SEMANTICS = {
    "cdc_places_current_tract": "model-based small-area estimates; not observed prevalence",
    "chicago_community_areas_current": "official community-area boundary geometry",
}


class SocrataResponseError(RuntimeError):
    """A Socrata response violates identity, schema, paging, or content contracts."""


@dataclass(frozen=True, slots=True)
class SocrataMetadata:
    """Identity and schema fields required to validate subsequent raw pages."""

    dataset_id: str
    dataset_title: str
    department: str
    updated_at: int
    license_name: str
    field_types: Mapping[str, str]


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _selected_fields(source: RegistrySource) -> tuple[str, ...]:
    select = source.request.parameters.get("$select")
    if select is None:
        raise ValueError("approved Socrata request must register $select")
    fields = tuple(field.strip() for field in select.split(","))
    if not fields or any(not field for field in fields) or len(set(fields)) != len(fields):
        raise ValueError("approved Socrata $select is invalid")
    return fields


def _validate_source(source: RegistrySource) -> None:
    if source.source_id not in _APPROVED_IDS or source.transport != "socrata":
        raise ValueError("source is not an approved Socrata dataset")
    if source.catalog_id is None:
        raise ValueError("approved Socrata source lacks a catalog ID")
    parsed = urlsplit(str(source.endpoint_url))
    expected_suffixes = (f"/{source.catalog_id}.csv", f"/{source.catalog_id}.geojson")
    if parsed.hostname != source.official_domain or not parsed.path.endswith(expected_suffixes):
        raise ValueError("Socrata endpoint does not match the registered domain and catalog ID")
    registered = dict(source.request.parameters)
    if registered != _EXACT_REQUESTS[source.source_id]:
        raise ValueError("Socrata query differs from the approved source contract")
    if source.primary_key != (
        ("tractfips",) if source.source_id.startswith("cdc_") else ("area_numbe",)
    ):
        raise ValueError("Socrata primary key differs from the approved source contract")
    if source.source_id == "cdc_places_current_tract":
        purpose = source.analytical_purpose.casefold()
        if "model-based" not in purpose or "not observed ehr prevalence" not in purpose:
            raise ValueError("PLACES semantics must remain explicitly model-based")


def _manifest_core(source: RegistrySource) -> dict[str, object]:
    _validate_source(source)
    return {
        "source_id": source.source_id,
        "dataset_id": source.catalog_id,
        "dataset_title": source.dataset_title,
        "endpoint_url": str(source.endpoint_url),
        "metadata_url": f"https://{source.official_domain}/api/views/{source.catalog_id}",
        "count_url": f"https://{source.official_domain}/resource/{source.catalog_id}.json",
        "count_query": dict(SocrataAdapter.count_parameters(source)),
        "page_query": dict(SocrataAdapter.page_parameters(source, offset=0)),
        "primary_key": list(source.primary_key),
        "release": source.release,
        "semantics": _SEMANTICS[source.source_id],
    }


def request_manifest_hash(source: RegistrySource) -> str:
    """Hash the complete credential-free request contract for drift detection."""
    if source.source_id not in _APPROVED_IDS or source.transport != "socrata":
        raise ValueError("source is not an approved Socrata dataset")
    contract = {
        "source_id": source.source_id,
        "dataset_id": source.catalog_id,
        "endpoint_url": str(source.endpoint_url),
        "parameters": dict(source.request.parameters),
        "primary_key": list(source.primary_key),
        "release": source.release,
    }
    return hashlib.sha256(_canonical_json(contract)).hexdigest()


def parse_socrata_metadata(payload: object, source: RegistrySource) -> SocrataMetadata:
    """Validate exact dataset identity, selected schema, update, license, and geometry type."""
    _validate_source(source)
    if not isinstance(payload, dict):
        raise SocrataResponseError("Socrata metadata response must be an object")
    if payload.get("id") != source.catalog_id or payload.get("name") != source.dataset_title:
        raise SocrataResponseError("Socrata metadata identity differs from the registry")
    columns = payload.get("columns")
    if not isinstance(columns, list) or not columns:
        raise SocrataResponseError("Socrata metadata schema is missing")
    field_types: dict[str, str] = {}
    for column in columns:
        if not isinstance(column, dict):
            raise SocrataResponseError("Socrata metadata schema contains an invalid column")
        field = column.get("fieldName")
        data_type = column.get("dataTypeName")
        if (
            not isinstance(field, str)
            or not field
            or not isinstance(data_type, str)
            or not data_type
        ):
            raise SocrataResponseError("Socrata metadata schema contains an invalid column")
        if field in field_types:
            raise SocrataResponseError("Socrata metadata schema contains duplicate fields")
        field_types[field] = data_type.casefold()
    if not set(_selected_fields(source)).issubset(field_types):
        raise SocrataResponseError("Socrata metadata schema lacks a registered selected field")
    if not set(source.primary_key).issubset(field_types):
        raise SocrataResponseError("Socrata metadata schema lacks the registered primary key")
    if (
        source.source_id == "chicago_community_areas_current"
        and field_types["the_geom"] not in _GEOMETRY_TYPES
    ):
        raise SocrataResponseError(
            "Socrata geometry metadata differs from the registered polygon type"
        )
    if any(
        field_types.get(field) != data_type
        for field, data_type in _FIELD_TYPES[source.source_id].items()
    ):
        raise SocrataResponseError("Socrata metadata schema field types differ from registry")
    updated_at = payload.get("rowsUpdatedAt")
    attribution = payload.get("attribution")
    license_payload = payload.get("license")
    if (
        isinstance(updated_at, bool)
        or not isinstance(updated_at, int)
        or updated_at < 0
        or not isinstance(attribution, str)
        or not attribution.strip()
        or not isinstance(license_payload, dict)
        or not isinstance(license_payload.get("name"), str)
        or not license_payload["name"].strip()
    ):
        raise SocrataResponseError(
            "Socrata metadata lacks department, update, or license provenance"
        )
    if source.source_id == "cdc_places_current_tract":
        description = payload.get("description")
        if not isinstance(description, str) or "model-based" not in description.casefold():
            raise SocrataResponseError("PLACES metadata no longer identifies model-based estimates")
    return SocrataMetadata(
        dataset_id=source.catalog_id or "",
        dataset_title=source.dataset_title,
        department=attribution,
        updated_at=updated_at,
        license_name=license_payload["name"],
        field_types=MappingProxyType(field_types),
    )


def _parse_json(content: bytes, label: str) -> object:
    try:
        return json.loads(content)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SocrataResponseError(f"Socrata {label} response is not valid JSON") from error


def _parse_csv_rows(content: bytes, label: str) -> list[dict[str, str]]:
    try:
        text = content.decode("utf-8-sig", errors="strict")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise SocrataResponseError(f"Socrata {label} CSV header is invalid")
        rows = list(reader)
    except UnicodeError as error:
        raise SocrataResponseError(f"Socrata {label} response is not valid UTF-8") from error
    if any(None in row for row in rows):
        raise SocrataResponseError(f"Socrata {label} CSV row width is invalid")
    return rows


def _parse_count(content: bytes) -> int:
    try:
        payload = _parse_json(content, "count")
    except SocrataResponseError:
        payload = _parse_csv_rows(content, "count")
    if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
        features = payload.get("features")
        if isinstance(features, list):
            payload = [
                feature.get("properties") for feature in features if isinstance(feature, dict)
            ]
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        raise SocrataResponseError("Socrata count response type is invalid")
    raw = payload[0].get("count")
    if not isinstance(raw, (str, int)) or isinstance(raw, bool):
        raise SocrataResponseError("Socrata count response value is invalid")
    try:
        count = int(raw)
    except ValueError as error:
        raise SocrataResponseError("Socrata count response value is invalid") from error
    if str(count) != str(raw) or count < 0 or count > _MAX_ROWS:
        raise SocrataResponseError("Socrata count response value is outside accepted limits")
    return count


def _parse_page(content: bytes, source: RegistrySource) -> tuple[list[dict[str, object]], object]:
    suffix = Path(urlsplit(str(source.endpoint_url)).path).suffix.casefold()
    if suffix == ".csv":
        try:
            payload = _parse_json(content, "page")
        except SocrataResponseError:
            payload = _parse_csv_rows(content, "page")
    else:
        payload = _parse_json(content, "page")
    if suffix == ".geojson":
        if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
            raise SocrataResponseError("Socrata GeoJSON page response type is invalid")
        features = payload.get("features")
        if not isinstance(features, list):
            raise SocrataResponseError("Socrata GeoJSON features response type is invalid")
        rows: list[dict[str, object]] = []
        for feature in features:
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                raise SocrataResponseError("Socrata GeoJSON feature is invalid")
            properties = feature.get("properties")
            geometry = feature.get("geometry")
            if not isinstance(properties, dict):
                raise SocrataResponseError("Socrata GeoJSON properties are invalid")
            if source.source_id == "chicago_community_areas_current" and (
                not isinstance(geometry, dict)
                or str(geometry.get("type", "")).casefold() not in _GEOMETRY_TYPES
                or not isinstance(geometry.get("coordinates"), list)
                or not geometry["coordinates"]
            ):
                raise SocrataResponseError("Socrata geometry is missing or invalid")
            if source.source_id == "chicago_community_areas_current":
                try:
                    parsed_geometry = shape(geometry)
                except (GEOSException, TypeError, ValueError, AttributeError):
                    raise SocrataResponseError("Socrata geometry is malformed") from None
                if (
                    parsed_geometry.geom_type.casefold() not in _GEOMETRY_TYPES
                    or parsed_geometry.is_empty
                    or not parsed_geometry.is_valid
                    or any(not Decimal(str(value)).is_finite() for value in parsed_geometry.bounds)
                ):
                    raise SocrataResponseError("Socrata geometry is malformed")
            rows.append(properties)
        return rows, payload
    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
        raise SocrataResponseError("Socrata page response type is invalid")
    return payload, payload


def _comparable(value: object, data_type: str) -> object:
    if isinstance(value, (dict, list, bool)) or value is None:
        raise SocrataResponseError("Socrata primary key value is invalid")
    if data_type == "number":
        try:
            return Decimal(str(value))
        except InvalidOperation as error:
            raise SocrataResponseError("Socrata numeric primary key is invalid") from error
    if not isinstance(value, (str, int)):
        raise SocrataResponseError("Socrata primary key value is invalid")
    return str(value)


def _validate_row_fields(
    row: Mapping[str, object], source: RegistrySource, *, geojson: bool
) -> None:
    expected = set(_selected_fields(source))
    if geojson:
        expected.remove("the_geom")
    if set(row) != expected:
        raise SocrataResponseError("Socrata page field set differs from registry")
    if source.source_id == "cdc_places_current_tract":
        _validate_places_domain(row, cook_only=True)


def _validate_places_domain(row: Mapping[str, object], *, cook_only: bool) -> None:
    tract = row.get("tractfips")
    county = row.get("countyfips")
    if (
        row.get("stateabbr") != "IL"
        or row.get("statedesc") != "Illinois"
        or not isinstance(row.get("countyname"), str)
        or not row["countyname"]
        or not isinstance(county, str)
        or re.fullmatch(r"^17\d{3}$", county) is None
        or cook_only
        and (county != "17031" or row.get("countyname") != "Cook")
        or not isinstance(tract, str)
        or _TRACT_GEOID.fullmatch(tract) is None
        or not tract.startswith(county)
    ):
        raise SocrataResponseError("PLACES row violates the registered geographic domain")
    for field in ("totalpopulation", "totalpop18plus"):
        raw = row.get(field)
        if not isinstance(raw, (str, int)) or not str(raw).isdigit():
            raise SocrataResponseError("PLACES row has an invalid population value")
    for field in ("bphigh_crudeprev", "diabetes_crudeprev", "copd_crudeprev"):
        try:
            value = Decimal(str(row.get(field)))
        except InvalidOperation:
            raise SocrataResponseError("PLACES row has an invalid model estimate") from None
        if not value.is_finite() or value < 0 or value > 100:
            raise SocrataResponseError("PLACES row has an invalid model estimate")
    for field in ("bphigh_crude95ci", "diabetes_crude95ci", "copd_crude95ci"):
        interval = row.get(field)
        if not isinstance(interval, str) or not interval.strip():
            raise SocrataResponseError("PLACES row lacks a registered confidence interval")


class SocrataAdapter:
    """Acquire exact registered SODA queries with deterministic, reconciled paging."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        environ: Mapping[str, str] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._environ = environ if environ is not None else os.environ
        self._sleep = sleep

    @staticmethod
    def count_parameters(source: RegistrySource) -> tuple[tuple[str, str], ...]:
        _validate_source(source)
        parameters = [("$select", "count(*) AS count")]
        where = source.request.parameters.get("$where")
        if where is not None:
            parameters.append(("$where", where))
        return tuple(parameters)

    @staticmethod
    def page_parameters(source: RegistrySource, *, offset: int) -> tuple[tuple[str, str], ...]:
        _validate_source(source)
        if (
            isinstance(offset, bool)
            or not isinstance(offset, int)
            or offset < 0
            or offset % PAGE_LIMIT
        ):
            raise ValueError("Socrata offset must be a nonnegative page boundary")
        registered = dict(source.request.parameters)
        return tuple(
            (name, value)
            for name, value in (
                ("$select", registered["$select"]),
                ("$where", registered.get("$where")),
                ("$order", registered["$order"]),
                ("$limit", str(PAGE_LIMIT)),
                ("$offset", str(offset)),
            )
            if value is not None
        )

    def plan(self, source: RegistrySource) -> AcquisitionPlan:
        _validate_source(source)
        return AcquisitionPlan(
            source_id=source.source_id,
            url=HttpUrl(f"https://{source.official_domain}/api/views/{source.catalog_id}"),
            parameters=tuple(_EXACT_REQUESTS[source.source_id].items()),
            transport="socrata",
            destination_paths=(
                "original/metadata/socrata_view.json",
                "original/count/count.json",
                "original/pages/",
                "requests/request_manifest.json",
            ),
            required_environment_variables=(),
            fallback_status=source.fallback.status,
        )

    @staticmethod
    def _response(
        client: httpx.Client,
        url: str,
        *,
        parameters: tuple[tuple[str, str], ...],
        headers: Mapping[str, str],
        maximum_bytes: int,
        label: str,
        expected_content_types: tuple[str, ...],
        sleep: Callable[[float], None],
    ) -> bytes:
        failed = False
        try:
            return HttpAcquirer(
                client=client,
                expected_content_types=expected_content_types,
                credential_headers=headers,
                max_response_bytes=maximum_bytes,
                sleep=sleep,
            ).request_bytes(
                method="GET",
                url=url,
                query=parameters,
            )
        except AcquisitionError:
            failed = True
        if failed:
            raise SocrataResponseError("Socrata request failed") from None
        raise AssertionError("unreachable")

    def fetch(self, source: RegistrySource, writer: SnapshotWriter) -> SnapshotManifest:
        """Fetch metadata, count, and all pages before atomic snapshot publication."""
        _validate_source(source)
        if writer.source_id != source.source_id:
            writer.cleanup()
            raise ValueError("snapshot writer source does not match Socrata source")
        token = self._environ.get("SOCRATA_APP_TOKEN")
        headers = {} if not token else {"X-App-Token": token}
        metadata_url = f"https://{source.official_domain}/api/views/{source.catalog_id}"
        count_url = f"https://{source.official_domain}/resource/{source.catalog_id}.json"
        endpoint = str(source.endpoint_url)
        owns_client = self._client is None
        client = self._client or httpx.Client(follow_redirects=False)
        try:
            metadata_content = self._response(
                client,
                metadata_url,
                parameters=(),
                headers=headers,
                maximum_bytes=_MAX_METADATA_BYTES,
                label="metadata",
                expected_content_types=("application/json",),
                sleep=self._sleep,
            )
            metadata_payload = _parse_json(metadata_content, "metadata")
            metadata = parse_socrata_metadata(metadata_payload, source)
            writer.write_bytes("original/metadata/socrata_view.json", metadata_content)

            count_parameters = self.count_parameters(source)
            count_content = self._response(
                client,
                count_url,
                parameters=count_parameters,
                headers=headers,
                maximum_bytes=_MAX_COUNT_BYTES,
                label="count",
                expected_content_types=("application/json",),
                sleep=self._sleep,
            )
            expected_count = _parse_count(count_content)
            if source.source_id == "chicago_community_areas_current" and expected_count != 77:
                raise SocrataResponseError("Chicago Socrata count must be exactly 77")
            writer.write_bytes("original/count/count.json", count_content)
            writer.annotate_file("original/count/count.json", row_count=1, page_count=1)

            observed_keys: set[tuple[object, ...]] = set()
            previous_key: tuple[object, ...] | None = None
            page_count = 0
            fetched_count = 0
            suffix = Path(urlsplit(endpoint).path).suffix.casefold().lstrip(".") or "json"
            while fetched_count < expected_count:
                offset = page_count * PAGE_LIMIT
                parameters = self.page_parameters(source, offset=offset)
                content = self._response(
                    client,
                    endpoint,
                    parameters=parameters,
                    headers=headers,
                    maximum_bytes=_MAX_PAGE_BYTES,
                    label="page",
                    expected_content_types=(
                        ("text/csv", "application/csv", "application/octet-stream")
                        if suffix == "csv"
                        else ("application/geo+json", "application/json")
                    ),
                    sleep=self._sleep,
                )
                rows, _ = _parse_page(content, source)
                expected_page_rows = min(PAGE_LIMIT, expected_count - fetched_count)
                if len(rows) != expected_page_rows:
                    raise SocrataResponseError("Socrata page termination differs from count(*)")
                for row in rows:
                    _validate_row_fields(row, source, geojson=suffix == "geojson")
                    key = tuple(
                        _comparable(row.get(field), metadata.field_types[field])
                        for field in source.primary_key
                    )
                    if key in observed_keys:
                        raise SocrataResponseError("Socrata duplicate primary key is fatal")
                    if previous_key is not None and key <= previous_key:
                        raise SocrataResponseError("Socrata page lacks stable primary-key order")
                    observed_keys.add(key)
                    previous_key = key
                page_count += 1
                fetched_count += len(rows)
                page_path = f"original/pages/page_{page_count:04d}.{suffix}"
                writer.write_bytes(page_path, content)
                writer.annotate_file(page_path, row_count=len(rows), page_count=1)

            if fetched_count != expected_count or len(observed_keys) != expected_count:
                raise SocrataResponseError("Socrata count does not equal unique fetched rows")
            if source.source_id == "chicago_community_areas_current" and observed_keys != {
                (Decimal(area_id),) for area_id in range(1, 78)
            }:
                raise SocrataResponseError(
                    "Chicago community-area IDs must be exactly 1 through 77"
                )
            request_manifest = _manifest_core(source)
            request_manifest.update(
                {
                    "request_manifest_sha256": request_manifest_hash(source),
                    "row_count": fetched_count,
                    "page_count": page_count,
                    "metadata": {
                        "department": metadata.department,
                        "license": metadata.license_name,
                        "rows_updated_at": metadata.updated_at,
                        "field_types": dict(metadata.field_types),
                    },
                }
            )
            writer.write_bytes("requests/request_manifest.json", _canonical_json(request_manifest))
            writer.annotate_file(
                "requests/request_manifest.json",
                row_count=fetched_count,
                page_count=page_count,
            )
            return writer.finalize()
        except BaseException:
            writer.cleanup()
            raise
        finally:
            if owns_client:
                client.close()


@dataclass(frozen=True, slots=True)
class FrozenSocrataSnapshot:
    source_id: str
    snapshot_date: str
    file_count: int
    row_count: int


_LEGACY_FILES = {
    "cdc_places_current_tract": (
        "sources/public/cdc_places/snapshots/2026-07-13/original/2025_release/data/illinois_census_tracts.csv",
        "sources/public/cdc_places/snapshots/2026-07-13/original/2025_release/metadata/measure_definitions.html",
        "sources/public/cdc_places/snapshots/2026-07-13/original/2025_release/metadata/socrata_view.json",
    ),
    "chicago_community_areas_current": (
        "sources/public/chicago_data_portal/snapshots/2026-07-13/original/community_areas_igwz-8jzy/data/community_areas.geojson",
        "sources/public/chicago_data_portal/snapshots/2026-07-13/original/community_areas_igwz-8jzy/metadata/socrata_view.json",
    ),
}


def verify_frozen_socrata_snapshot(root: Path, source: RegistrySource) -> FrozenSocrataSnapshot:
    """Verify the inherited 2026-07-13 bytes and semantics without republishing them."""
    _validate_source(source)
    root = root.resolve(strict=True)
    checksums_path = root / "sources/public/CHECKSUMS.sha256"
    expected: dict[str, str] = {}
    try:
        for line in checksums_path.read_text(encoding="utf-8").splitlines():
            digest, separator, relative = line.partition("  ")
            if separator and len(digest) == 64:
                expected[relative] = digest
        paths = _LEGACY_FILES[source.source_id]
        for relative in paths:
            candidate = root / relative
            cursor = root
            has_symlink = False
            for part in Path(relative).parts:
                cursor /= part
                if cursor.is_symlink():
                    has_symlink = True
                    break
            if has_symlink or candidate.resolve(strict=True) != candidate:
                raise SocrataResponseError("frozen Socrata snapshot path is unsafe")
            if expected.get(relative) != sha256_file(candidate):
                raise SocrataResponseError("frozen Socrata snapshot checksum differs")
        metadata_path = root / paths[-1]
        parse_socrata_metadata(json.loads(metadata_path.read_text(encoding="utf-8")), source)
        data_path = root / paths[0]
        if source.source_id == "cdc_places_current_tract":
            places_rows = _parse_csv_rows(data_path.read_bytes(), "frozen PLACES")
            required = set(_PLACES_FIELDS)
            if len(places_rows) != 3258:
                raise SocrataResponseError("frozen PLACES Illinois row inventory differs")
            if not places_rows or not required.issubset(places_rows[0]):
                raise SocrataResponseError("frozen PLACES required measure fields differ")
            header = set(places_rows[0])
            if any(set(row) != header for row in places_rows):
                raise SocrataResponseError("frozen PLACES row field sets differ")
            for places_row in places_rows:
                _validate_places_domain(places_row, cook_only=False)
            if not any(places_row["countyfips"] == "17031" for places_row in places_rows):
                raise SocrataResponseError("frozen PLACES snapshot lacks Cook County tracts")
            if len({places_row["tractfips"] for places_row in places_rows}) != len(places_rows):
                raise SocrataResponseError("frozen PLACES primary keys are not unique")
            row_count = len(places_rows)
        else:
            payload = json.loads(data_path.read_text(encoding="utf-8"))
            chicago_rows, _ = _parse_page(_canonical_json(payload), source)
            for chicago_row in chicago_rows:
                _validate_row_fields(chicago_row, source, geojson=True)
            area_ids = {str(chicago_row["area_numbe"]) for chicago_row in chicago_rows}
            if len(chicago_rows) != 77 or area_ids != {str(value) for value in range(1, 78)}:
                raise SocrataResponseError("frozen Chicago community-area inventory differs")
            row_count = len(chicago_rows)
        return FrozenSocrataSnapshot(source.source_id, "2026-07-13", len(paths), row_count)
    except SocrataResponseError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, KeyError):
        raise SocrataResponseError("frozen Socrata snapshot verification failed") from None
