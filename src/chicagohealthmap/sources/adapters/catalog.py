"""Fail-closed adapters for verified catalog, ArcGIS, and official bulk sources."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import stat
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from pydantic import HttpUrl

from chicagohealthmap.sources.adapters.base import AcquisitionPlan
from chicagohealthmap.sources.http import AcquisitionError, HttpAcquirer
from chicagohealthmap.sources.models import SnapshotManifest
from chicagohealthmap.sources.registry import RegistrySource
from chicagohealthmap.sources.snapshot import SnapshotWriter, sha256_file

_FROZEN_DATE = "2026-07-13"
_LEGACY_DIRS = {
    "chicago_health_atlas_life_expectancy": "chicago_health_atlas",
    "chicago_health_atlas_mortality": "chicago_health_atlas",
    "cdc_svi_2022_tract": "cdc_atsdr_svi",
    "hrsa_health_centers_current": "hrsa_health_centers",
}
_ATLAS_TOPICS = {
    "chicago_health_atlas_life_expectancy": "VRLE",
    "chicago_health_atlas_mortality": "VRDTHR",
}
_ATLAS_PERIODS = {
    "VRLE": tuple(str(year) for year in range(2010, 2025)),
    "VRDTHR": tuple(f"{year}-{year + 4}" for year in range(2010, 2021)),
}
_ATLAS_NAMES = {"VRLE": "Life expectancy", "VRDTHR": "All-cause mortality rate"}
_ATLAS_UNITS = {"VRLE": "years", "VRDTHR": "per 100,000 population"}
_ATLAS_GEOGRAPHY_HASH = "f5ad4b67fddc6a2c18dae6c8a0f48c3df9146eec47ae1fad73c3366a0782d809"
_ATLAS_DATASET = "Illinois Department of Public Health - Death Certificate Data Files"
_FAMILY_CONTRACT = {
    "chicago_health_atlas": (
        131,
        "a87c6c70e0953b9aa420dda589c9fd4a09be1e7f5d73e6baa37e9c07db9b4074",
    ),
    "cdc_atsdr_svi": (5, "c27f50dba19aad21224763da3aeb7289c3b15ea13db8f235032b8be57fd98884"),
    "hrsa_health_centers": (3, "2477cd2836d4a32e25700ffe160235ea02960e625a0cd14e5f5f6d5972b8dce3"),
}
_SVI_SCHEMA_HASH = "95f3e80e5a3cea7d96eade11624ebc8f4c409a528878c47ebaa95c88aaa36d9b"
_SVI_ID_HASH = "9ee993243efebae9f0fa92ddbbdfa2d1e245fbfc46d9914d90114c3b5bff4b4b"
_HRSA_SCHEMA_HASH = "8d239c28e4b5838a49a9b3bbf19db8f4c6a8e5717d11ad584a59cabf6aff76fe"
_HRSA_ID_HASH = "c00be37b849d686baec1a4f464125d7c9aebdb34b7040f69098bb85083e4e60f"
_ETAG = re.compile(r'^"[\x21\x23-\x7e\x80-\xff]*"$')
_SVI_REQUIRED = frozenset(
    {
        "ST",
        "STATE",
        "ST_ABBR",
        "FIPS",
        "MP_CROWD",
        "RPL_THEMES",
        "RPL_THEME1",
        "RPL_THEME2",
        "RPL_THEME3",
        "RPL_THEME4",
        "F_THEME1",
        "F_THEME2",
        "F_THEME3",
        "F_THEME4",
        "F_TOTAL",
    }
)
_HRSA_REQUIRED = frozenset(
    {
        "Health Center Type",
        "Health Center Number",
        "BPHC Assigned Number",
        "Site Name",
        "Site Address",
        "Site City",
        "Site State Abbreviation",
        "Site Postal Code",
        "Site Status Description",
        "Health Center Type Description",
        "Health Center Name",
        "Geocoding Artifact Address Primary X Coordinate",
        "Geocoding Artifact Address Primary Y Coordinate",
        "State and County Federal Information Processing Standard Code",
        "Data Warehouse Record Create Date",
    }
)


class CatalogResponseError(RuntimeError):
    """A disclosure-safe catalog transport or semantic validation failure."""


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _json_object(content: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(content)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CatalogResponseError(f"{label} is not valid JSON") from error
    if not isinstance(value, dict):
        raise CatalogResponseError(f"{label} must be a JSON object")
    if "error" in value:
        raise CatalogResponseError(f"{label} contains an ArcGIS error")
    return value


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _hash_lines(values: list[str] | tuple[str, ...] | set[str]) -> str:
    return hashlib.sha256("".join(f"{value}\n" for value in sorted(values)).encode()).hexdigest()


def _hash_ordered(values: list[str]) -> str:
    return hashlib.sha256("".join(f"{value}\n" for value in values).encode()).hexdigest()


class ArcGisAdapter:
    """Read layer metadata and retrieve an exact, deterministically ordered ID universe."""

    def __init__(
        self,
        *,
        source: RegistrySource,
        return_geometry: bool = False,
        client: httpx.Client | None = None,
    ) -> None:
        expected_url = "https://gisportal.hrsa.gov/server/rest/services/HealthCareFacilities/PrimaryHealthCareFacilities_FS/MapServer/0/"
        if (
            source.source_id != "hrsa_health_centers_current"
            or source.catalog_id != "PrimaryHealthCareFacilities_FS/MapServer/0"
            or str(source.fallback.url) != expected_url
            or str(source.endpoint_url)
            != "https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv"
            or source.official_domain != "data.hrsa.gov"
        ):
            raise ValueError("source does not match the registered HRSA ArcGIS layer")
        self.source = source
        self.service_url = expected_url.rstrip("/")
        self.expected_object_id_field = "OBJECTID"
        self.expected_layer_name = "Health Care Service Delivery Sites"
        self.return_geometry = return_geometry
        self._client = client

    def _request(self, url: str, parameters: tuple[tuple[str, str], ...]) -> bytes:
        try:
            return HttpAcquirer(
                client=self._client,
                expected_content_types=("application/json",),
                max_response_bytes=32 * 1024 * 1024,
                sleep=lambda _: None,
            ).request_bytes(method="GET", url=url, query=parameters)
        except AcquisitionError:
            raise CatalogResponseError("ArcGIS request failed") from None

    def fetch(self, writer: SnapshotWriter) -> SnapshotManifest:
        try:
            if writer.source_id != self.source.source_id:
                raise ValueError("snapshot writer source does not match ArcGIS source")
            metadata_parameters = (("f", "json"),)
            metadata_content = self._request(self.service_url, metadata_parameters)
            metadata = _json_object(metadata_content, "ArcGIS metadata")
            fields = metadata.get("fields")
            object_fields = (
                [
                    field.get("name")
                    for field in fields
                    if isinstance(field, dict) and field.get("type") == "esriFieldTypeOID"
                ]
                if isinstance(fields, list)
                else []
            )
            object_id_field = object_fields[0] if len(object_fields) == 1 else None
            maximum = metadata.get("maxRecordCount")
            if (
                object_id_field != self.expected_object_id_field
                or maximum != 2000
                or metadata.get("name") != self.expected_layer_name
                or metadata.get("id") != 0
            ):
                raise CatalogResponseError("ArcGIS metadata identity drift")
            writer.write_bytes("original/metadata/layer.json", metadata_content)

            query_url = f"{self.service_url}/query"
            ids_parameters = (("where", "1=1"), ("returnIdsOnly", "true"), ("f", "json"))
            ids_content = self._request(query_url, ids_parameters)
            ids_payload = _json_object(ids_content, "ArcGIS ID response")
            ids = ids_payload.get("objectIds")
            if (
                ids_payload.get("objectIdFieldName") != object_id_field
                or not isinstance(ids, list)
                or any(not isinstance(item, int) or isinstance(item, bool) for item in ids)
                or len(ids) != len(set(ids))
            ):
                raise CatalogResponseError("ArcGIS registered object IDs are invalid")
            ordered_ids = sorted(ids)
            writer.write_bytes("original/object_ids.json", ids_content)

            observed: list[int] = []
            page_number = 0
            for start in range(0, len(ordered_ids), maximum):
                page_number += 1
                page_ids = ordered_ids[start : start + maximum]
                parameters = (
                    ("where", "1=1"),
                    ("outFields", "*"),
                    ("returnGeometry", str(self.return_geometry).lower()),
                    ("orderByFields", f"{object_id_field} ASC"),
                    ("objectIds", ",".join(str(item) for item in page_ids)),
                    ("resultRecordCount", str(maximum)),
                    ("f", "json"),
                )
                content = self._request(query_url, parameters)
                payload = _json_object(content, "ArcGIS feature page")
                features = payload.get("features")
                if not isinstance(features, list) or len(features) > maximum:
                    raise CatalogResponseError("ArcGIS malformed or excess feature page")
                page_observed: list[int] = []
                for feature in features:
                    if not isinstance(feature, dict) or not isinstance(
                        feature.get("attributes"), dict
                    ):
                        raise CatalogResponseError("ArcGIS feature schema is invalid")
                    item = feature["attributes"].get(object_id_field)
                    if not isinstance(item, int) or isinstance(item, bool):
                        raise CatalogResponseError("ArcGIS feature object ID is invalid")
                    if self.return_geometry:
                        geometry = feature.get("geometry")
                        if not isinstance(geometry, dict) or not all(
                            _finite_number(geometry.get(axis)) for axis in ("x", "y")
                        ):
                            raise CatalogResponseError("ArcGIS geometry is invalid")
                    page_observed.append(item)
                if len(page_observed) != len(set(page_observed)):
                    raise CatalogResponseError("ArcGIS duplicate object ID is fatal")
                if page_observed != sorted(page_observed):
                    raise CatalogResponseError("ArcGIS object ID order is not deterministic")
                observed.extend(page_observed)
                if (
                    payload.get("exceededTransferLimit") not in {False, None}
                    and page_observed != page_ids
                ):
                    raise CatalogResponseError("ArcGIS page remained transfer-limited")
                path = f"original/pages/page-{page_number:04d}.json"
                writer.write_bytes(path, content)
                writer.annotate_file(path, row_count=len(features), page_count=1)

            if len(observed) != len(set(observed)):
                raise CatalogResponseError("ArcGIS duplicate object ID is fatal")
            missing = set(ordered_ids) - set(observed)
            extra = set(observed) - set(ordered_ids)
            if missing or extra:
                raise CatalogResponseError("ArcGIS missing registered object IDs")
            if observed != ordered_ids:
                raise CatalogResponseError("ArcGIS object ID order is not deterministic")
            request_manifest = {
                "service_url": self.service_url,
                "object_id_field": object_id_field,
                "max_record_count": maximum,
                "registered_id_count": len(ordered_ids),
                "page_count": page_number,
                "where": "1=1",
                "out_fields": "*",
                "return_geometry": self.return_geometry,
                "order_by_fields": f"{object_id_field} ASC",
            }
            writer.write_bytes("requests/request_manifest.json", _json_bytes(request_manifest))
            return writer.finalize()
        except BaseException:
            writer.cleanup()
            raise


class OfficialBulkAdapter:
    """Acquire one exact official file with strict response identity and provenance."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        max_bytes: int = 512 * 1024 * 1024,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._client = client
        self._max_bytes = max_bytes
        self._sleep = sleep

    def response(self, source: RegistrySource) -> tuple[bytes, dict[str, object]]:
        endpoint = str(source.endpoint_url)
        contracts = {
            "cdc_svi_2022_tract": (
                "svi.cdc.gov",
                "https://svi.cdc.gov/Documents/Data/2022/csv/states/Illinois.csv",
            ),
            "hrsa_health_centers_current": (
                "data.hrsa.gov",
                "https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv",
            ),
        }
        contract = contracts.get(source.source_id)
        if (
            contract is None
            or source.official_domain != contract[0]
            or endpoint != contract[1]
            or str(source.request.url) != contract[1]
            or source.request.method != "GET"
            or source.request.parameters
            or source.expected_media_types != ("text/csv",)
            or source.required_response_headers != ("ETag", "Last-Modified", "Content-Length")
        ):
            raise CatalogResponseError("official bulk registry identity drift")
        expected = source.expected_media_types
        metadata: dict[str, str] = {}
        try:
            content = HttpAcquirer(
                client=self._client,
                expected_content_types=expected,
                max_response_bytes=self._max_bytes,
                sleep=self._sleep,
            ).request_bytes(
                method=source.request.method,
                url=endpoint,
                query=tuple(source.request.parameters.items()),
                response_metadata=metadata,
            )
        except AcquisitionError as error:
            if "redirect" in str(error).casefold():
                raise CatalogResponseError("official bulk redirect is disabled") from None
            raise CatalogResponseError("official bulk request failed") from None
        resolved = metadata["resolved_url"]
        if resolved != endpoint or urlsplit(resolved).hostname != source.official_domain:
            raise CatalogResponseError("official bulk resolved URL drift")
        for name in ("etag", "last_modified", "content_length"):
            if not metadata[name].strip():
                raise CatalogResponseError(f"official bulk {name.replace('_', '-')} is missing")
        if not _ETAG.fullmatch(metadata["etag"]):
            raise CatalogResponseError("official bulk ETag syntax is invalid")
        try:
            modified = parsedate_to_datetime(metadata["last_modified"])
        except (TypeError, ValueError, OverflowError):
            raise CatalogResponseError("official bulk Last-Modified is invalid") from None
        if modified.tzinfo is None or modified.utcoffset() is None:
            raise CatalogResponseError("official bulk Last-Modified is invalid")
        try:
            length = int(metadata["content_length"])
        except ValueError:
            raise CatalogResponseError("official bulk content-length is invalid") from None
        if length <= 0 or length > self._max_bytes:
            raise CatalogResponseError("official bulk response exceeds byte bound")
        if len(content) != length:
            raise CatalogResponseError("official bulk content-length mismatch")
        provenance: dict[str, object] = {
            "requested_url": endpoint,
            "resolved_url": resolved,
            "content_type": metadata["content_type"],
            "content_length": length,
            "etag": metadata["etag"],
            "last_modified": metadata["last_modified"],
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        return content, provenance

    def fetch(self, source: RegistrySource, writer: SnapshotWriter) -> SnapshotManifest:
        try:
            if writer.source_id != source.source_id:
                raise ValueError("snapshot writer source does not match official bulk source")
            content, provenance = self.response(source)
            if source.source_id == "cdc_svi_2022_tract":
                validate_svi_csv(content)
            elif source.source_id == "hrsa_health_centers_current":
                validate_hrsa_csv(content)
            else:
                raise ValueError("source is not an approved catalog official bulk source")
            name = Path(urlsplit(str(source.endpoint_url)).path).name
            writer.write_bytes(f"original/data/{name}", content)
            writer.write_bytes("requests/acquisition.json", _json_bytes(provenance))
            return writer.finalize()
        except BaseException:
            writer.cleanup()
            raise


def validate_atlas_payload(payload: object, *, topic: str, period: str) -> int:
    if not isinstance(payload, dict) or not isinstance(payload.get("params"), dict):
        raise CatalogResponseError("Atlas payload schema is invalid")
    params = payload["params"]
    if params.get("topic") != topic:
        raise CatalogResponseError("Atlas topic identity drift")
    if (
        params.get("period") != period
        or params.get("population") != ""
        or params.get("layer") != "neighborhood"
    ):
        raise CatalogResponseError("Atlas geography, period, or population identity drift")
    results = payload.get("results")
    if not isinstance(results, list) or payload.get("count") != len(results):
        raise CatalogResponseError("Atlas result count mismatch")
    identifiers: set[str] = set()
    for row in results:
        if not isinstance(row, dict) or set(row) != {"g", "l", "a", "p", "d", "v", "se"}:
            raise CatalogResponseError("Atlas result schema is invalid")
        if row["a"] != topic or row["d"] != period or row["l"] != "neighborhood" or row["p"] != "":
            raise CatalogResponseError("Atlas row identity drift")
        if not isinstance(row["g"], str) or row["g"] in identifiers:
            raise CatalogResponseError("Atlas geography identifier is invalid")
        identifiers.add(row["g"])
        upper = 150 if topic == "VRLE" else 100_000
        if not _finite_number(row["v"]) or not 0 <= row["v"] <= upper:
            raise CatalogResponseError("Atlas estimate is invalid")
        if row["se"] is not None and (not _finite_number(row["se"]) or row["se"] < 0):
            raise CatalogResponseError("Atlas uncertainty is invalid")
    if len(results) != 77 or _hash_lines(identifiers) != _ATLAS_GEOGRAPHY_HASH:
        raise CatalogResponseError("Atlas registered geography universe differs")
    return len(results)


def _csv_rows(content: bytes, label: str) -> tuple[list[str], list[dict[str, str]]]:
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    except (UnicodeError, csv.Error) as error:
        raise CatalogResponseError(f"{label} CSV is malformed") from error
    if not fields or not rows:
        raise CatalogResponseError(f"{label} CSV is empty")
    return fields, rows


def validate_svi_csv(content: bytes) -> int:
    fields, rows = _csv_rows(content, "SVI")
    if _hash_ordered(fields) != _SVI_SCHEMA_HASH or not _SVI_REQUIRED.issubset(fields):
        raise CatalogResponseError("SVI schema differs from the exact registered schema")
    seen: set[str] = set()
    for row in rows:
        fips = row["FIPS"]
        if (
            row["ST"] != "17"
            or row["STATE"] != "Illinois"
            or row["ST_ABBR"] != "IL"
            or len(fips) != 11
            or not fips.isdigit()
            or not fips.startswith("17")
            or fips in seen
        ):
            raise CatalogResponseError("SVI tract GEOID is invalid")
        seen.add(fips)
        for field in ("RPL_THEMES", "RPL_THEME1", "RPL_THEME2", "RPL_THEME3", "RPL_THEME4"):
            try:
                value = float(row[field])
            except ValueError:
                raise CatalogResponseError("SVI rank value is invalid") from None
            if not math.isfinite(value) or value != -999 and not 0 <= value <= 1:
                raise CatalogResponseError("SVI rank value is invalid")
        try:
            crowd = float(row["MP_CROWD"])
        except ValueError:
            raise CatalogResponseError("SVI corrected MP_CROWD is invalid") from None
        if not math.isfinite(crowd) or crowd != -999 and crowd < 0:
            raise CatalogResponseError("SVI corrected MP_CROWD is invalid")
        flag_maxima = {"F_THEME1": 5, "F_THEME2": 4, "F_THEME3": 1, "F_THEME4": 5, "F_TOTAL": 15}
        for field, maximum in flag_maxima.items():
            raw = row[field]
            if not raw.lstrip("-").isdigit() or int(raw) != -999 and not 0 <= int(raw) <= maximum:
                raise CatalogResponseError("SVI flag value is invalid")
    return len(rows)


def validate_hrsa_csv(content: bytes) -> int:
    fields, rows = _csv_rows(content, "HRSA")
    if _hash_ordered(fields) != _HRSA_SCHEMA_HASH or not _HRSA_REQUIRED.issubset(fields):
        raise CatalogResponseError(
            "HRSA schema lacks registered site, status, geography, or program fields"
        )
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["Health Center Number"], row["BPHC Assigned Number"])
        if not all(key) or key in seen:
            raise CatalogResponseError("HRSA site identifier is invalid")
        seen.add(key)
        for field in (
            "Site Name",
            "Health Center Name",
            "Site State Abbreviation",
            "Site Status Description",
            "Health Center Type Description",
            "Data Warehouse Record Create Date",
        ):
            if not row[field].strip():
                raise CatalogResponseError("HRSA required site metadata is missing")
            if row[field].lstrip().startswith(("=", "+", "-", "@")):
                raise CatalogResponseError("HRSA text contains a spreadsheet formula")
        for field in ("Health Center Number", "BPHC Assigned Number"):
            if row[field].lstrip().startswith(("=", "+", "-", "@")):
                raise CatalogResponseError("HRSA identifier contains a spreadsheet formula")
        fips = row["State and County Federal Information Processing Standard Code"].strip()
        if fips and (len(fips) != 5 or not fips.isdigit()):
            raise CatalogResponseError("HRSA county FIPS is invalid")
        try:
            datetime.strptime(row["Data Warehouse Record Create Date"], "%m/%d/%Y")
        except ValueError:
            raise CatalogResponseError("HRSA update date is invalid") from None
        raw_x = row["Geocoding Artifact Address Primary X Coordinate"].strip()
        raw_y = row["Geocoding Artifact Address Primary Y Coordinate"].strip()
        if bool(raw_x) != bool(raw_y):
            raise CatalogResponseError("HRSA coordinate suppression is inconsistent")
        if not raw_x:
            continue
        try:
            x = float(raw_x)
            y = float(raw_y)
        except ValueError:
            raise CatalogResponseError("HRSA coordinate is invalid") from None
        if (
            not math.isfinite(x)
            or not math.isfinite(y)
            or not -180 <= x <= 180
            or not -90 <= y <= 90
        ):
            raise CatalogResponseError("HRSA coordinate is invalid")
    return len(rows)


@dataclass(frozen=True, slots=True)
class FrozenCatalogReport:
    source_id: str
    snapshot_date: str
    file_count: int
    row_count: int
    legacy_layout: bool = True


def frozen_catalog_snapshot(root: Path, source: RegistrySource, snapshot_date: str) -> Path:
    if snapshot_date != _FROZEN_DATE:
        raise CatalogResponseError("catalog reuse is limited to frozen 2026-07-13 artifacts")
    legacy = _LEGACY_DIRS.get(source.source_id)
    if legacy is None:
        raise CatalogResponseError("source has no registered frozen catalog snapshot")
    public = root / "sources/public"
    path = root / "sources/public" / legacy / "snapshots" / snapshot_date
    for candidate in (
        root / "sources",
        public,
        public / legacy,
        public / legacy / "snapshots",
        path,
    ):
        try:
            mode = os.lstat(candidate).st_mode
        except OSError:
            raise CatalogResponseError("frozen catalog snapshot path is unsafe") from None
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise CatalogResponseError("frozen catalog snapshot path is unsafe")
    if path.resolve(strict=True).parent.parent.parent != public.resolve(strict=True):
        raise CatalogResponseError("frozen catalog snapshot path is unsafe")
    return path


def _checksum_inventory(root: Path) -> dict[str, str]:
    checksum_path = root / "sources/public/CHECKSUMS.sha256"
    for candidate in (root / "sources", root / "sources/public", checksum_path):
        try:
            mode = os.lstat(candidate).st_mode
        except OSError:
            raise CatalogResponseError("public checksum inventory path is unsafe") from None
        if stat.S_ISLNK(mode):
            raise CatalogResponseError("public checksum inventory path is unsafe")
    result: dict[str, str] = {}
    for line in checksum_path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        digest, relative = line.split("  ", 1)
        if len(digest) != 64 or relative in result:
            raise CatalogResponseError("public checksum inventory is invalid")
        result[relative] = digest
    return result


def verify_frozen_catalog_snapshot(
    root: Path, source: RegistrySource, snapshot_date: str = _FROZEN_DATE
) -> FrozenCatalogReport:
    snapshot = frozen_catalog_snapshot(root, source, snapshot_date)
    topic = _ATLAS_TOPICS.get(source.source_id)
    checksums = _checksum_inventory(root)
    family = _LEGACY_DIRS[source.source_id]
    prefix = f"sources/public/{family}/snapshots/{snapshot_date}/"
    family_checksums = {
        path: digest for path, digest in checksums.items() if path.startswith(prefix)
    }
    expected_count, expected_inventory_hash = _FAMILY_CONTRACT[family]
    inventory_lines = [f"{digest}  {path}" for path, digest in family_checksums.items()]
    if (
        len(family_checksums) != expected_count
        or _hash_lines(inventory_lines) != expected_inventory_hash
    ):
        raise CatalogResponseError("frozen catalog compatibility contract differs")
    observed: set[str] = set()
    for directory, directories, filenames in os.walk(snapshot, followlinks=False):
        directory_path = Path(directory)
        for name in [*directories, *filenames]:
            candidate = directory_path / name
            try:
                mode = os.lstat(candidate).st_mode
            except OSError:
                raise CatalogResponseError("frozen catalog file path is unsafe") from None
            if stat.S_ISLNK(mode):
                raise CatalogResponseError("frozen catalog file path is unsafe")
            if name in filenames and stat.S_ISREG(mode):
                observed.add(candidate.relative_to(root).as_posix())
    if observed != set(family_checksums):
        raise CatalogResponseError("frozen catalog file inventory differs")
    files = [root / path for path in sorted(observed)]
    for path in files:
        relative = path.relative_to(root).as_posix()
        expected = checksums.get(relative)
        if expected is None or sha256_file(path) != expected:
            raise CatalogResponseError("frozen catalog checksum verification failed")
    row_count = 0
    if topic:
        periods = _ATLAS_PERIODS[topic]
        coverage = json.loads((snapshot / "original/coverage" / f"{topic}.json").read_text())
        coverages = coverage.get("coverages", {}).get("neighborhood")
        if coverage.get("params") != {"topic": topic} or not isinstance(coverages, list):
            raise CatalogResponseError("Atlas coverage metadata drift")
        blank_periods = tuple(
            item.get("period") for item in coverages if item.get("population") == ""
        )
        if set(blank_periods) != set(periods) or len(blank_periods) != len(periods):
            raise CatalogResponseError("Atlas coverage and data periods differ")
        for period in periods:
            path = snapshot / "original/data" / topic / f"{period}.json"
            row_count += validate_atlas_payload(
                json.loads(path.read_text()), topic=topic, period=period
            )
        topics = json.loads((snapshot / "original/metadata/topics.json").read_text()).get(
            "results", []
        )
        entry = next((item for item in topics if item.get("key") == topic), None)
        datasets = entry.get("datasets") if isinstance(entry, dict) else None
        dataset = (
            datasets[0].get("dataset")
            if isinstance(datasets, list) and len(datasets) == 1 and isinstance(datasets[0], dict)
            else None
        )
        if (
            not isinstance(entry, dict)
            or entry.get("name") != _ATLAS_NAMES[topic]
            or entry.get("units") != _ATLAS_UNITS[topic]
            or entry.get("privacy") != "Organization"
            or entry.get("is_count") is not False
            or not isinstance(dataset, dict)
            or dataset.get("name") != _ATLAS_DATASET
        ):
            raise CatalogResponseError("Atlas indicator organization metadata is missing")
    elif source.source_id == "cdc_svi_2022_tract":
        content = (snapshot / "original/2022/data/Illinois.csv").read_bytes()
        fields, rows = _csv_rows(content, "SVI")
        if (
            _hash_ordered(fields) != _SVI_SCHEMA_HASH
            or len(rows) != 3263
            or _hash_lines({row["FIPS"] for row in rows}) != _SVI_ID_HASH
        ):
            raise CatalogResponseError("SVI frozen schema or ID universe differs")
        row_count = validate_svi_csv(content)
    elif source.source_id == "hrsa_health_centers_current":
        content = (
            snapshot / "original/data/Health_Center_Service_Delivery_and_LookAlike_Sites.csv"
        ).read_bytes()
        fields, rows = _csv_rows(content, "HRSA")
        identifiers = {
            f"{row['Health Center Number']}\x1f{row['BPHC Assigned Number']}" for row in rows
        }
        if (
            _hash_ordered(fields) != _HRSA_SCHEMA_HASH
            or len(rows) != 18940
            or len(identifiers) != 18940
            or _hash_lines(identifiers) != _HRSA_ID_HASH
            or {row["Data Warehouse Record Create Date"] for row in rows} != {"07/13/2026"}
        ):
            raise CatalogResponseError("HRSA frozen schema, IDs, or update date differs")
        row_count = validate_hrsa_csv(content)
    return FrozenCatalogReport(source.source_id, snapshot_date, len(files), row_count)


class CatalogAdapter:
    """Plan the exact Task 11 catalog route and verify frozen compatibility snapshots."""

    def plan(self, source: RegistrySource) -> AcquisitionPlan:
        if source.source_id not in _LEGACY_DIRS:
            raise ValueError("source is not an approved Task 15 catalog source")
        topic = _ATLAS_TOPICS.get(source.source_id)
        destinations = (
            (f"original/coverage/{topic}.json", f"original/data/{topic}/", "original/metadata/")
            if topic
            else (
                f"original/data/{Path(urlsplit(str(source.endpoint_url)).path).name}",
                "requests/acquisition.json",
            )
        )
        return AcquisitionPlan(
            source_id=source.source_id,
            url=HttpUrl(str(source.endpoint_url)),
            parameters=tuple(source.request.parameters.items()),
            transport=source.transport,
            destination_paths=destinations,
            required_environment_variables=(),
            fallback_status=source.fallback.status,
        )
