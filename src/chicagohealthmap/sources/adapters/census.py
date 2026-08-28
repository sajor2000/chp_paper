"""Fail-closed Census ACS group and TIGER/Line tract acquisition adapters."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import stat
import zipfile
import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pyogrio  # type: ignore[import-untyped]
from pydantic import HttpUrl

from chicagohealthmap.sources.adapters.base import AcquisitionPlan
from chicagohealthmap.sources.models import SnapshotAcquisition, SnapshotManifest
from chicagohealthmap.sources.registry import RegistrySource
from chicagohealthmap.sources.snapshot import SnapshotWriter, sha256_file

ACS_RELEASE = "acs/acs5"
ACS_API_ROOT = "https://api.census.gov/data"
STATE_FIPS = "17"
COOK_COUNTY_FIPS = "031"
_GROUP = re.compile(r"^[A-Z]\d{5}$")
_YEAR = re.compile(r"^\d{4}$")
_TRACT = re.compile(r"^\d{6}$")
_STATE = re.compile(r"^\d{2}$")
_COUNTY = re.compile(r"^\d{3}$")
_GEOID = re.compile(r"^\d{11}$")
_REQUIRED_TIGER_FIELDS = frozenset({"STATEFP", "COUNTYFP", "TRACTCE", "GEOID"})
_REQUIRED_TIGER_EXTENSIONS = frozenset({".shp", ".shx", ".dbf", ".prj"})
_MAX_ARCHIVE_MEMBERS = 64
_MAX_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024
_ZCTA_RELATIONSHIP_FIELDS = (
    "OID_ZCTA5_20",
    "GEOID_ZCTA5_20",
    "NAMELSAD_ZCTA5_20",
    "AREALAND_ZCTA5_20",
    "AREAWATER_ZCTA5_20",
    "MTFCC_ZCTA5_20",
    "CLASSFP_ZCTA5_20",
    "FUNCSTAT_ZCTA5_20",
    "OID_TRACT_20",
    "GEOID_TRACT_20",
    "NAMELSAD_TRACT_20",
    "AREALAND_TRACT_20",
    "AREAWATER_TRACT_20",
    "MTFCC_TRACT_20",
    "FUNCSTAT_TRACT_20",
    "AREALAND_PART",
    "AREAWATER_PART",
)


class CensusResponseError(RuntimeError):
    """A Census response violates the registered grain or response contract."""


class ArchiveSafetyError(RuntimeError):
    """A TIGER archive is unsafe or structurally invalid."""


@dataclass(frozen=True, slots=True)
class AcsRow:
    """One raw ACS response row with its canonical 11-digit tract identifier."""

    geoid: str
    values: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class AcsGroupResponse:
    """Validated header and raw string-valued rows for one ACS group."""

    header: tuple[str, ...]
    rows: tuple[AcsRow, ...]


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def parse_acs_group_response(payload: object) -> AcsGroupResponse:
    """Validate one Census group response without coercing estimates or margins of error."""
    if not isinstance(payload, list) or len(payload) < 2:
        raise CensusResponseError("ACS response must contain a header and at least one row")
    raw_header = payload[0]
    if (
        not isinstance(raw_header, list)
        or not raw_header
        or any(not isinstance(value, str) or not value for value in raw_header)
        or len(set(raw_header)) != len(raw_header)
    ):
        raise CensusResponseError("ACS response header is invalid")
    header = tuple(raw_header)
    required = {"NAME", "state", "county", "tract"}
    if not required.issubset(header):
        raise CensusResponseError("ACS response lacks required tract geography fields")

    rows: list[AcsRow] = []
    observed_geoids: set[str] = set()
    for raw_row in payload[1:]:
        if not isinstance(raw_row, list) or len(raw_row) != len(header):
            raise CensusResponseError("ACS response header/row length mismatch")
        if any(not isinstance(value, str) for value in raw_row):
            raise CensusResponseError("ACS response values must remain raw strings")
        values = dict(zip(header, raw_row, strict=True))
        if (
            not _STATE.fullmatch(values["state"])
            or not _COUNTY.fullmatch(values["county"])
            or values["state"] != STATE_FIPS
            or values["county"] != COOK_COUNTY_FIPS
        ):
            raise CensusResponseError("ACS response contains a tract outside Cook County")
        if not _TRACT.fullmatch(values["tract"]):
            raise CensusResponseError("ACS response tract must contain six digits")
        geoid = values["state"] + values["county"] + values["tract"]
        if not _GEOID.fullmatch(geoid):
            raise CensusResponseError("ACS response GEOID is invalid")
        if geoid in observed_geoids:
            raise CensusResponseError("ACS response contains a duplicate GEOID")
        observed_geoids.add(geoid)
        rows.append(AcsRow(geoid=geoid, values=values))
    return AcsGroupResponse(header=header, rows=tuple(rows))


class CensusAcsAdapter:
    """Acquire exact ACS group requests while keeping credentials out of provenance."""

    def __init__(
        self,
        *,
        year: int,
        groups: Sequence[str],
        release: str = ACS_RELEASE,
        client: httpx.Client | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        if not _YEAR.fullmatch(str(year)):
            raise ValueError("ACS year must contain four digits")
        normalized_groups = tuple(groups)
        if (
            not normalized_groups
            or any(not _GROUP.fullmatch(group) for group in normalized_groups)
            or len(set(normalized_groups)) != len(normalized_groups)
        ):
            raise ValueError("ACS groups must be unique detailed-table identifiers")
        if release != ACS_RELEASE:
            raise ValueError(f"unsupported ACS release: {release}")
        self.year = year
        self.groups = normalized_groups
        self.release = release
        self._client = client
        self._environ = environ if environ is not None else os.environ

    @property
    def api_url(self) -> str:
        return f"{ACS_API_ROOT}/{self.year}/{self.release}"

    def _validate_source(self, source: RegistrySource) -> None:
        if source.source_id != f"census_acs_{self.year}_5y" or source.years != (str(self.year),):
            raise ValueError("ACS adapter year does not match the registered source")

    def _parameters(self, group: str) -> tuple[tuple[str, str], ...]:
        return (
            ("get", f"NAME,group({group})"),
            ("for", "tract:*"),
            ("in", f"state:{STATE_FIPS} county:{COOK_COUNTY_FIPS}"),
        )

    def plan(self, source: RegistrySource) -> AcquisitionPlan:
        self._validate_source(source)
        return AcquisitionPlan(
            source_id=source.source_id,
            url=HttpUrl(self.api_url),
            parameters=tuple(
                parameter for group in self.groups for parameter in self._parameters(group)
            ),
            transport="census_api",
            destination_paths=tuple(
                f"original/{self.year}/acs5/groups/{group}.json" for group in self.groups
            ),
            required_environment_variables=("CENSUS_API_KEY",),
            estimated_request_count=len(self.groups),
            fallback_status=source.fallback.status,
        )

    def fetch(self, source: RegistrySource, writer: SnapshotWriter) -> SnapshotManifest:
        """Fetch and finalize one raw JSON file and redacted request record per group."""
        self._validate_source(source)
        if writer.source_id != source.source_id:
            writer.cleanup()
            raise ValueError("snapshot writer source does not match ACS source")
        key = self._environ.get("CENSUS_API_KEY")
        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=120.0, follow_redirects=False)
        try:
            for group in self.groups:
                safe_parameters = self._parameters(group)
                request_parameters = dict(safe_parameters)
                if key:
                    request_parameters["key"] = key
                response = client.get(
                    self.api_url, params=request_parameters, follow_redirects=False
                )
                if response.status_code != 200:
                    raise CensusResponseError(
                        f"ACS request failed with HTTP {response.status_code}"
                    )
                try:
                    payload = json.loads(response.content)
                except (UnicodeError, json.JSONDecodeError) as error:
                    raise CensusResponseError("ACS response is not valid JSON") from error
                parsed = parse_acs_group_response(payload)
                raw_path = f"original/{self.year}/acs5/groups/{group}.json"
                writer.write_bytes(raw_path, response.content)
                writer.annotate_file(raw_path, row_count=len(parsed.rows), page_count=1)
                header_hash = hashlib.sha256(
                    json.dumps(parsed.header, ensure_ascii=False, separators=(",", ":")).encode(
                        "utf-8"
                    )
                ).hexdigest()
                metadata = {
                    "group": group,
                    "url": self.api_url,
                    "query": dict(safe_parameters),
                    "row_count": len(parsed.rows),
                    "header_sha256": header_hash,
                }
                writer.write_bytes(
                    f"requests/{self.year}/acs5/groups/{group}.json",
                    _canonical_json(metadata),
                )
                writer.record_acquisition(
                    SnapshotAcquisition(
                        group=group,
                        url=HttpUrl(self.api_url),
                        parameters=safe_parameters,
                        row_count=len(parsed.rows),
                        header_sha256=header_hash,
                    )
                )
            return writer.finalize()
        except BaseException:
            writer.cleanup()
            raise
        finally:
            if owns_client:
                client.close()


def _safe_archive_member(info: zipfile.ZipInfo) -> None:
    name = info.filename
    path = Path(name)
    if (
        not name
        or "\\" in name
        or path.is_absolute()
        or ".." in path.parts
        or any(character in name for character in ("\x00", "\r", "\n"))
    ):
        raise ArchiveSafetyError("TIGER archive contains an unsafe member path")
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise ArchiveSafetyError("TIGER archive contains a symbolic link")
    if info.flag_bits & 0x1:
        raise ArchiveSafetyError("TIGER archive contains an encrypted member")


def validate_tiger_archive(
    archive_path: Path,
    *,
    expected_stem: str | None = None,
    max_compression_ratio: float = 1000.0,
) -> tuple[str, ...]:
    """Reject path escapes, links, duplicates, bombs, corruption, and incomplete shapefiles."""
    if max_compression_ratio <= 0:
        raise ValueError("max_compression_ratio must be positive")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > _MAX_ARCHIVE_MEMBERS:
                raise ArchiveSafetyError("TIGER archive member count is invalid")
            normalized: set[str] = set()
            total = 0
            component_sets: dict[tuple[str, str], list[str]] = {}
            for info in infos:
                _safe_archive_member(info)
                folded = info.filename.casefold()
                if folded in normalized:
                    raise ArchiveSafetyError("TIGER archive contains duplicate member names")
                normalized.add(folded)
                if info.is_dir():
                    continue
                total += info.file_size
                if total > _MAX_UNCOMPRESSED_BYTES:
                    raise ArchiveSafetyError("TIGER archive exceeds the expansion limit")
                if info.file_size and (
                    info.compress_size == 0
                    or info.file_size / info.compress_size > max_compression_ratio
                ):
                    raise ArchiveSafetyError("TIGER archive has an unsafe compression ratio")
                member = Path(info.filename)
                suffix = member.suffix.casefold()
                if expected_stem is not None and suffix in _REQUIRED_TIGER_EXTENSIONS:
                    identity = (member.parent.as_posix(), member.stem)
                    component_sets.setdefault(identity, []).append(suffix)
            if archive.testzip() is not None:
                raise ArchiveSafetyError("TIGER archive fails its CRC check")
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        raise ArchiveSafetyError("TIGER archive cannot be safely inspected") from error
    if expected_stem is not None:
        if len(component_sets) != 1:
            raise ArchiveSafetyError("TIGER archive contains conflicting shapefile components")
        (parent, stem), extensions = next(iter(component_sets.items()))
        if stem != expected_stem or sorted(extensions) != sorted(_REQUIRED_TIGER_EXTENSIONS):
            raise ArchiveSafetyError("TIGER archive lacks one coherent shapefile component set")
    return tuple(info.filename for info in infos if not info.is_dir())


def _zcta_relationship_row_count(content: bytes) -> int:
    try:
        reader = csv.reader(io.StringIO(content.decode("utf-8-sig")), delimiter="|")
        header = tuple(next(reader))
    except (StopIteration, UnicodeDecodeError, csv.Error) as error:
        raise CensusResponseError(
            "ZCTA relationship is not valid UTF-8 pipe-delimited text"
        ) from error
    if header != _ZCTA_RELATIONSHIP_FIELDS:
        raise CensusResponseError("ZCTA relationship record layout is not the frozen 2020 layout")
    row_count = 0
    for row in reader:
        if len(row) != len(header):
            raise CensusResponseError("ZCTA relationship row length does not match its header")
        zcta, tract = row[1].strip(), row[9].strip()
        if zcta and not re.fullmatch(r"\d{5}", zcta):
            raise CensusResponseError("ZCTA relationship contains a malformed ZCTA GEOID")
        if not _GEOID.fullmatch(tract):
            raise CensusResponseError("ZCTA relationship contains a malformed tract GEOID")
        for value in (row[11], row[12], row[15], row[16]):
            if not value.isdigit():
                raise CensusResponseError("ZCTA relationship contains a malformed area field")
        row_count += 1
    if row_count == 0:
        raise CensusResponseError("ZCTA relationship contains no data rows")
    return row_count


class CensusZctaRelationshipAdapter:
    """Acquire and preserve the official national 2020 ZCTA-to-tract relationship."""

    filename = "tab20_zcta520_tract20_natl.txt"

    def __init__(self, *, client: httpx.Client | None = None) -> None:
        self._client = client

    def _validate_source(self, source: RegistrySource) -> None:
        endpoint_name = Path(urlsplit(str(source.endpoint_url)).path).name
        if (
            source.source_id != "census_zcta_2020_tract_relationship"
            or source.years != ("2020",)
            or endpoint_name != self.filename
        ):
            raise ValueError("ZCTA relationship adapter does not match the registered source")

    def plan(self, source: RegistrySource) -> AcquisitionPlan:
        self._validate_source(source)
        return AcquisitionPlan(
            source_id=source.source_id,
            url=source.endpoint_url,
            parameters=(),
            transport="http_file",
            destination_paths=(f"original/2020/{self.filename}",),
            estimated_request_count=1,
            fallback_status=source.fallback.status,
        )

    def fetch(self, source: RegistrySource, writer: SnapshotWriter) -> SnapshotManifest:
        self._validate_source(source)
        if writer.source_id != source.source_id:
            writer.cleanup()
            raise ValueError("snapshot writer source does not match ZCTA relationship source")
        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=120.0, follow_redirects=False)
        try:
            response = client.get(str(source.endpoint_url), follow_redirects=False)
            if response.status_code != 200:
                raise CensusResponseError(
                    f"ZCTA relationship request failed with HTTP {response.status_code}"
                )
            row_count = _zcta_relationship_row_count(response.content)
            raw_path = f"original/2020/{self.filename}"
            writer.write_bytes(raw_path, response.content)
            writer.annotate_file(raw_path, row_count=row_count, page_count=1)
            return writer.finalize()
        except BaseException:
            writer.cleanup()
            raise
        finally:
            if owns_client:
                client.close()


class CensusTigerAdapter:
    """Preserve an Illinois TIGER ZIP and emit an original-CRS Cook County interim table."""

    def __init__(self, *, year: int, archive_path: Path | None = None) -> None:
        if not _YEAR.fullmatch(str(year)):
            raise ValueError("TIGER year must contain four digits")
        self.year = year
        self.archive_path = Path(archive_path) if archive_path is not None else None

    @property
    def filename(self) -> str:
        return f"tl_{self.year}_{STATE_FIPS}_tract.zip"

    def _validate_source(self, source: RegistrySource) -> None:
        expected_id = f"census_tiger_{self.year}_tract"
        endpoint_name = Path(urlsplit(str(source.endpoint_url)).path).name
        if (
            source.source_id != expected_id
            or source.years != (str(self.year),)
            or endpoint_name != self.filename
        ):
            raise ValueError("TIGER adapter does not match the exact registered source")

    def plan(self, source: RegistrySource) -> AcquisitionPlan:
        self._validate_source(source)
        return AcquisitionPlan(
            source_id=source.source_id,
            url=source.endpoint_url,
            parameters=(),
            transport="http_file",
            destination_paths=(
                f"original/{self.year}/tract/{self.filename}",
                f"interim/{self.year}/cook_county_tracts.parquet",
            ),
            estimated_request_count=1,
            fallback_status=source.fallback.status,
        )

    def fetch(self, source: RegistrySource, writer: SnapshotWriter) -> SnapshotManifest:
        """Validate local official bytes, preserve them, then filter with Pyogrio."""
        self._validate_source(source)
        if self.archive_path is None:
            writer.cleanup()
            raise ValueError("TIGER acquisition requires an explicit local archive path")
        try:
            archive = self.archive_path.resolve(strict=True)
            staging = writer.staging_path.resolve(strict=True)
            if archive == staging or archive.is_relative_to(staging):
                raise ValueError("TIGER source archive must not alias snapshot staging")
            if writer.source_id != source.source_id:
                raise ValueError("snapshot writer source does not match TIGER source")

            expected_stem = self.filename.removesuffix(".zip")
            members = validate_tiger_archive(archive, expected_stem=expected_stem)
            raw_path = f"original/{self.year}/tract/{self.filename}"
            writer.copy_file(archive, raw_path)
            staged_archive = writer.staging_path / raw_path
            virtual_path = f"/vsizip/{staged_archive}"
            info = pyogrio.read_info(virtual_path, force_feature_count=True)
            fields = {str(field) for field in info["fields"]}
            if not _REQUIRED_TIGER_FIELDS.issubset(fields) or not info.get("crs"):
                raise CensusResponseError("TIGER layer lacks required fields or CRS")
            frame = pyogrio.read_dataframe(virtual_path, use_arrow=True)
            if (
                frame.empty
                or frame.geometry.name not in frame
                or frame.geometry.isna().any()
                or frame.geometry.is_empty.any()
                or not frame.geometry.is_valid.all()
                or not frame.geometry.geom_type.isin({"Polygon", "MultiPolygon"}).all()
            ):
                raise CensusResponseError("TIGER layer lacks valid tract geometry")
            for field in _REQUIRED_TIGER_FIELDS:
                frame[field] = frame[field].astype("string")
                if frame[field].isna().any():
                    raise CensusResponseError("TIGER layer contains null geography identifiers")
            expected_geoid = frame["STATEFP"] + frame["COUNTYFP"] + frame["TRACTCE"]
            if (
                not frame["STATEFP"].str.fullmatch(_STATE).all()
                or not frame["STATEFP"].eq(STATE_FIPS).all()
                or not frame["COUNTYFP"].str.fullmatch(_COUNTY).all()
                or not frame["TRACTCE"].str.fullmatch(_TRACT).all()
                or not frame["GEOID"].str.fullmatch(_GEOID).all()
                or not frame["GEOID"].eq(expected_geoid).all()
                or not frame["GEOID"].is_unique
            ):
                raise CensusResponseError("TIGER geography identifiers are inconsistent")
            cook = frame.loc[frame["COUNTYFP"].eq(COOK_COUNTY_FIPS)].copy()
            if cook.empty:
                raise CensusResponseError("TIGER layer contains no Cook County tracts")
            cook["source_id"] = source.source_id
            cook["source_release"] = source.release
            buffer = io.BytesIO()
            cook.to_parquet(buffer, index=False, schema_version="1.0.0")
            writer.write_bytes(f"interim/{self.year}/cook_county_tracts.parquet", buffer.getvalue())
            metadata = {
                "source_id": source.source_id,
                "source_release": source.release,
                "official_filename": self.filename,
                "archive_sha256": sha256_file(staged_archive),
                "archive_members": list(members),
                "state_feature_count": len(frame),
                "cook_county_feature_count": len(cook),
                "original_crs": str(frame.crs),
                "inspection_engine": "pyogrio",
            }
            writer.write_bytes(
                f"requests/{self.year}/tract/archive.json", _canonical_json(metadata)
            )
            return writer.finalize()
        except BaseException:
            writer.cleanup()
            raise
