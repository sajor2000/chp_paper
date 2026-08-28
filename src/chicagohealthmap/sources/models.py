"""Validated, credential-free source and raw snapshot contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from copy import deepcopy
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from types import MappingProxyType
from typing import Annotated, Any, Self
from urllib.parse import parse_qsl, unquote, unquote_plus, urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    PlainSerializer,
    StringConstraints,
    ValidateAs,
    ValidationError,
    field_validator,
    model_validator,
)

Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z0-9_]+$")]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SECRET_HEADERS = frozenset(
    {"authorization", "cookie", "proxy-authorization", "x-api-key", "x-app-token"}
)
_CREDENTIAL_NAMES = frozenset(
    {
        "apikey",
        "apitoken",
        "auth",
        "authorization",
        "bearer",
        "clientsecret",
        "cookie",
        "credential",
        "key",
        "password",
        "privatekey",
        "secret",
        "secretkey",
        "subscriptionkey",
        "token",
        "accesstoken",
        "accesskey",
        "xapikey",
    }
)
_CREDENTIAL_NAME_SUFFIXES = (
    "accesstoken",
    "apikey",
    "authorization",
    "clientsecret",
    "cookie",
    "credential",
    "password",
    "privatekey",
    "secret",
    "secretkey",
    "subscriptionkey",
    "token",
)


def _freeze_string_mapping(values: Mapping[str, str] | None = None) -> Mapping[str, str]:
    """Copy values behind a slotless, immutable standard-library proxy."""
    return MappingProxyType(dict(values or {}))


ImmutableStringMapping = Annotated[
    Mapping[str, str],
    ValidateAs(dict[str, str], _freeze_string_mapping),
    PlainSerializer(lambda value: dict(value.items()), return_type=dict[str, str]),
]


def _normalize_credential_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _is_credential_name(value: str) -> bool:
    normalized = _normalize_credential_name(value)
    return normalized in _CREDENTIAL_NAMES or normalized.endswith(_CREDENTIAL_NAME_SUFFIXES)


def _repeated_unquote(value: str, *, plus: bool = False) -> str:
    decoder = unquote_plus if plus else unquote
    decoded = value
    for _ in range(3):
        candidate = decoder(decoded)
        if candidate == decoded:
            break
        decoded = candidate
    return decoded


def _sanitized_field_error(
    title: str, field_name: str, message: str, input_description: str
) -> ValidationError:
    return ValidationError.from_exception_data(
        title,
        [
            {
                "type": "value_error",
                "loc": (field_name,),
                "input": f"<redacted {input_description}>",
                "ctx": {"error": ValueError(message)},
            }
        ],
        hide_input=True,
    )


def _credential_url_message(value: Any) -> str | None:
    """Inspect a raw URL without placing it in a Pydantic validation error."""
    raw_value = str(value)
    raw_query = raw_value.partition("?")[2].partition("#")[0]
    for parameter in re.split(r"[&;]", raw_query):
        raw_name = parameter.partition("=")[0]
        if raw_name and _is_credential_name(_repeated_unquote(raw_name, plus=True)):
            return "URL must not contain credential-like query parameters"

    try:
        parsed = urlsplit(raw_value)
    except (TypeError, ValueError):
        authority = raw_value.partition("://")[2].split("/", 1)[0]
        if "@" in authority:
            return "URL must not contain user information"
        return None
    if parsed.username is not None or parsed.password is not None:
        return "URL must not contain user information"
    if any(
        _is_credential_name(name) for name, _ in parse_qsl(parsed.query, keep_blank_values=True)
    ):
        return "URL must not contain credential-like query parameters"
    decoded_path = _repeated_unquote(parsed.path)
    if (
        any(ord(character) < 32 or ord(character) == 127 for character in decoded_path)
        or "\\" in decoded_path
        or any(segment == ".." for segment in decoded_path.split("/"))
    ):
        return "URL must not contain unsafe path encodings"
    return None


def _reject_raw_credential_urls(value: Any, *, fields: tuple[str, ...], title: str) -> Any:
    """Reject credential URLs before Pydantic retains the raw field input."""
    if not isinstance(value, Mapping):
        return value
    for field_name in fields:
        if field_name not in value:
            continue
        candidate = value[field_name]
        candidates = (
            candidate if isinstance(candidate, (list, tuple, set, frozenset)) else (candidate,)
        )
        for item in candidates:
            message = _credential_url_message(item)
            if message is not None:
                raise _sanitized_field_error(title, field_name, message, "unsafe URL")
    return value


def _is_secret_header_name(value: str) -> bool:
    return value.casefold() in _SECRET_HEADERS


def _reject_raw_request_credentials(value: Any, *, title: str) -> Any:
    """Reject all request credentials before Pydantic retains raw inputs."""
    value = _reject_raw_credential_urls(value, fields=("url",), title=title)
    if not isinstance(value, Mapping):
        return value

    checks = (
        ("query", _is_credential_name, "query must not contain credential parameters"),
        ("parameters", _is_credential_name, "parameters must not contain credentials"),
        ("headers", _is_secret_header_name, "headers must not contain credential values"),
    )
    for field_name, is_forbidden, message in checks:
        candidate = value.get(field_name)
        if isinstance(candidate, Mapping) and any(is_forbidden(str(key)) for key in candidate):
            raise _sanitized_field_error(
                title, field_name, message, "credential-bearing request metadata"
            )
    return value


def _validate_relative_path(value: str, field_name: str) -> str:
    path = Path(value)
    windows_path = PureWindowsPath(value)
    if (
        not value.strip()
        or "\\" in value
        or path.is_absolute()
        or ".." in path.parts
        or bool(windows_path.drive)
        or ".." in windows_path.parts
    ):
        raise ValueError(f"{field_name} must be a non-empty repository-relative path")
    return value


class ContractModel(BaseModel):
    """Strict immutable base for persisted and loggable contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    def model_copy(self, *, update: Mapping[str, Any] | None = None, deep: bool = False) -> Self:
        """Copy safely, revalidating every requested field update."""
        if update is None and not deep:
            return super().model_copy()
        values = self.model_dump(round_trip=True)
        if update is not None:
            values.update(update)
        if deep:
            values = deepcopy(values)
        return type(self).model_validate(values)


class Transport(StrEnum):
    """Supported ways to acquire a source."""

    local = "local"
    census_api = "census_api"
    socrata = "socrata"
    arcgis = "arcgis"
    http_file = "http_file"
    documented_export = "documented_export"


class SourceSpec(ContractModel):
    """Authoritative origin and acquisition metadata for one source."""

    source_id: Identifier
    organization: NonEmptyText
    dataset_title: NonEmptyText
    transport: Transport
    landing_url: HttpUrl
    documentation_url: HttpUrl
    license: NonEmptyText
    snapshot_subdir: str

    @field_validator("snapshot_subdir")
    @classmethod
    def validate_snapshot_subdir(cls, value: str) -> str:
        return _validate_relative_path(value, "snapshot_subdir")

    @model_validator(mode="before")
    @classmethod
    def reject_url_credentials(cls, value: Any) -> Any:
        return _reject_raw_credential_urls(
            value,
            fields=("landing_url", "documentation_url"),
            title=cls.__name__,
        )


class RequestRecord(ContractModel):
    """Credential-free metadata safe to persist in acquisition provenance."""

    method: str
    url: HttpUrl
    query: ImmutableStringMapping = Field(default_factory=_freeze_string_mapping)
    headers: ImmutableStringMapping = Field(default_factory=_freeze_string_mapping)

    @model_validator(mode="before")
    @classmethod
    def reject_url_credentials(cls, value: Any) -> Any:
        return _reject_raw_request_credentials(value, title=cls.__name__)

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("method must not be blank")
        return normalized

    @field_validator("query")
    @classmethod
    def reject_secret_query_parameters(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        forbidden = sorted(key for key in value if _is_credential_name(key))
        if forbidden:
            raise ValueError(f"query contains credential parameter(s): {', '.join(forbidden)}")
        return value

    @field_validator("headers")
    @classmethod
    def reject_secret_headers(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        forbidden = sorted(key for key in value if _is_secret_header_name(key))
        if forbidden:
            raise ValueError(f"headers contain credential value(s): {', '.join(forbidden)}")
        return value


class SnapshotFile(ContractModel):
    """Integrity and size metadata for one immutable raw snapshot file."""

    path: str
    sha256: Sha256
    byte_count: int = Field(ge=0)
    row_count: int | None = Field(default=None, ge=0)
    page_count: int | None = Field(default=None, ge=0)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _validate_relative_path(value, "path")


class ValidationStatus(StrEnum):
    """Outcome of validating a completed snapshot."""

    pending = "pending"
    passed = "passed"
    failed = "failed"


class SnapshotAcquisition(ContractModel):
    """Credential-free per-request provenance embedded in a snapshot manifest."""

    group: Annotated[str, StringConstraints(pattern=r"^[A-Z]\d{5}$")]
    url: HttpUrl
    parameters: tuple[tuple[str, str], ...] = ()
    row_count: int = Field(ge=0)
    header_sha256: Sha256

    @model_validator(mode="before")
    @classmethod
    def reject_url_credentials(cls, value: Any) -> Any:
        value = _reject_raw_credential_urls(value, fields=("url",), title=cls.__name__)
        if isinstance(value, Mapping):
            parameters = value.get("parameters")
            contains_credentials = isinstance(parameters, Mapping) and any(
                _is_credential_name(str(name)) for name in parameters
            )
            if isinstance(parameters, (list, tuple)):
                contains_credentials = contains_credentials or any(
                    isinstance(item, (list, tuple))
                    and len(item) == 2
                    and _is_credential_name(str(item[0]))
                    for item in parameters
                )
            if contains_credentials:
                raise _sanitized_field_error(
                    cls.__name__,
                    "parameters",
                    "acquisition parameters must not contain credentials",
                    "credential-bearing acquisition metadata",
                )
        return value

    @field_validator("parameters")
    @classmethod
    def reject_credential_parameters(
        cls, value: tuple[tuple[str, str], ...]
    ) -> tuple[tuple[str, str], ...]:
        if any(_is_credential_name(name) for name, _ in value):
            raise ValueError("acquisition parameters must not contain credentials")
        return value


class SnapshotManifest(ContractModel):
    """Provenance manifest for a complete immutable raw snapshot."""

    source_id: Identifier
    snapshot_id: NonEmptyText
    snapshot_date: date
    retrieval_started_at: datetime
    retrieval_completed_at: datetime
    files: tuple[SnapshotFile, ...] = Field(min_length=1)
    acquisitions: tuple[SnapshotAcquisition, ...] = ()
    validation_status: ValidationStatus

    @field_validator("acquisitions")
    @classmethod
    def acquisition_groups_are_unique(
        cls, value: tuple[SnapshotAcquisition, ...]
    ) -> tuple[SnapshotAcquisition, ...]:
        groups = [item.group for item in value]
        if len(groups) != len(set(groups)):
            raise ValueError("acquisition groups must be unique")
        return value

    @field_validator("snapshot_date", mode="before")
    @classmethod
    def require_iso_snapshot_date(cls, value: Any) -> Any:
        if isinstance(value, str) and not _ISO_DATE.fullmatch(value):
            raise ValueError("snapshot_date must use ISO YYYY-MM-DD format")
        return value

    @field_validator("retrieval_started_at", "retrieval_completed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("retrieval timestamps must include a timezone")
        return value

    @model_validator(mode="after")
    def check_retrieval_order(self) -> SnapshotManifest:
        if self.retrieval_completed_at < self.retrieval_started_at:
            raise ValueError("retrieval_completed_at must not precede retrieval_started_at")
        return self
