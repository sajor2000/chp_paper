"""Canonical, credential-free registry of authoritative public sources."""

from __future__ import annotations

import csv
import io
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml  # type: ignore[import-untyped]
from pydantic import Field, HttpUrl, field_validator, model_validator

from chicagohealthmap.sources.models import (
    ContractModel,
    ImmutableStringMapping,
    _reject_raw_credential_urls,
    _reject_raw_request_credentials,
)


REQUIRED_SOURCE_IDS = {
    "chicago_health_atlas_life_expectancy",
    "chicago_health_atlas_mortality",
    "census_acs_2019_5y",
    "census_acs_2022_5y",
    "census_acs_2024_5y",
    "census_tiger_2019_tract",
    "census_tiger_2020_tract",
    "census_tiger_2023_tract",
    "census_tiger_2024_tract",
    "census_zcta_2020_tract_relationship",
    "cdc_places_current_tract",
    "cdc_svi_2022_tract",
    "hrsa_health_centers_current",
    "chicago_community_areas_current",
    "metopio_catalog",
}

_IDENTIFIER = re.compile(r"^[a-z0-9_]+$")
_SOURCE_ALLOWED_DOMAINS: dict[str, frozenset[str]] = {
    "chicago_health_atlas_life_expectancy": frozenset({"chicagohealthatlas.org"}),
    "chicago_health_atlas_mortality": frozenset({"chicagohealthatlas.org"}),
    "census_acs_2019_5y": frozenset({"api.census.gov", "www.census.gov", "www2.census.gov"}),
    "census_acs_2022_5y": frozenset({"api.census.gov", "www.census.gov", "www2.census.gov"}),
    "census_acs_2024_5y": frozenset({"api.census.gov", "www.census.gov", "www2.census.gov"}),
    "census_tiger_2019_tract": frozenset({"www.census.gov", "www2.census.gov"}),
    "census_tiger_2020_tract": frozenset({"www.census.gov", "www2.census.gov"}),
    "census_tiger_2023_tract": frozenset({"www.census.gov", "www2.census.gov"}),
    "census_tiger_2024_tract": frozenset({"www.census.gov", "www2.census.gov"}),
    "census_zcta_2020_tract_relationship": frozenset({"www.census.gov", "www2.census.gov"}),
    "cdc_places_current_tract": frozenset({"data.cdc.gov"}),
    "cdc_svi_2022_tract": frozenset({"svi.cdc.gov", "www.atsdr.cdc.gov"}),
    "hrsa_health_centers_current": frozenset({"data.hrsa.gov", "gisportal.hrsa.gov"}),
    "chicago_community_areas_current": frozenset({"data.cityofchicago.org"}),
    "metopio_catalog": frozenset({"metop.io"}),
}


def _host_matches(host: str | None, allowed_domain: str) -> bool:
    if host is None:
        return False
    normalized = host.rstrip(".").casefold()
    allowed = allowed_domain.rstrip(".").casefold()
    return normalized == allowed or normalized.endswith(f".{allowed}")


class RegistryModel(ContractModel):
    """Registry contract with validated copy behavior and frozen nested fields."""


class RequestSpec(RegistryModel):
    method: str = "GET"
    url: HttpUrl
    parameters: ImmutableStringMapping = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def reject_raw_credentials(cls, value: Any) -> Any:
        return _reject_raw_request_credentials(value, title=cls.__name__)

    @field_validator("method")
    @classmethod
    def method_is_get(cls, value: str) -> str:
        if value.upper() != "GET":
            raise ValueError("registry requests must use GET")
        return "GET"


class FallbackSpec(RegistryModel):
    policy: str
    status: str
    reason: str
    url: HttpUrl | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_unsafe_url(cls, value: Any) -> Any:
        return _reject_raw_credential_urls(value, fields=("url",), title=cls.__name__)


class VerificationSpec(RegistryModel):
    status: str
    verified_at: date
    evidence_urls: tuple[HttpUrl, ...]
    notes: str
    ref_mcp_status: str
    tavily_status: str

    @model_validator(mode="before")
    @classmethod
    def reject_unsafe_urls(cls, value: Any) -> Any:
        return _reject_raw_credential_urls(value, fields=("evidence_urls",), title=cls.__name__)

    @field_validator("status")
    @classmethod
    def status_is_known(cls, value: str) -> str:
        if value not in {"verified", "unverified", "drift_detected"}:
            raise ValueError("unknown verification status")
        return value


class RegistrySource(RegistryModel):
    source_id: str
    organization: str
    dataset_title: str
    analytical_purpose: str
    transport: str
    expected_media_types: tuple[str, ...] = ()
    required_response_headers: tuple[str, ...] = ()
    official_domain: str
    landing_url: HttpUrl
    documentation_url: HttpUrl
    endpoint_url: HttpUrl
    catalog_id: str | None = None
    release: str
    years: tuple[str, ...]
    geography: str
    license: str
    access_date: date
    citation: str
    citation_url: HttpUrl
    expected_grain: str
    primary_key: tuple[str, ...]
    request: RequestSpec
    fallback: FallbackSpec
    verification: VerificationSpec

    @model_validator(mode="before")
    @classmethod
    def reject_unsafe_urls(cls, value: Any) -> Any:
        return _reject_raw_credential_urls(
            value,
            fields=("landing_url", "documentation_url", "endpoint_url", "citation_url"),
            title=cls.__name__,
        )

    @field_validator(
        "organization",
        "dataset_title",
        "analytical_purpose",
        "transport",
        "official_domain",
        "release",
        "geography",
        "license",
        "citation",
        "expected_grain",
    )
    @classmethod
    def text_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value.strip()

    @field_validator("source_id")
    @classmethod
    def source_id_is_safe(cls, value: str) -> str:
        if not _IDENTIFIER.fullmatch(value):
            raise ValueError("source_id must be a lowercase identifier")
        return value

    @field_validator("years", "primary_key")
    @classmethod
    def tuples_are_nonempty_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or any(not item.strip() for item in value) or len(set(value)) != len(value):
            raise ValueError("values must be nonempty and unique")
        return value

    @field_validator("expected_media_types", "required_response_headers")
    @classmethod
    def policy_values_are_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value) or len(value) != len(set(value)):
            raise ValueError("response policy values must be nonempty and unique")
        return value

    @model_validator(mode="after")
    def urls_use_frozen_authoritative_domains(self) -> RegistrySource:
        allowed_domains = _SOURCE_ALLOWED_DOMAINS.get(self.source_id)
        if allowed_domains is None or self.official_domain not in allowed_domains:
            raise ValueError("source does not declare a frozen authoritative domain")
        endpoint_host = urlsplit(str(self.endpoint_url)).hostname
        if not _host_matches(endpoint_host, self.official_domain):
            raise ValueError("endpoint URL does not use the declared authoritative domain")
        if self.request.url != self.endpoint_url:
            raise ValueError("request URL must equal endpoint_url")
        urls = (
            self.landing_url,
            self.documentation_url,
            self.endpoint_url,
            self.citation_url,
            self.request.url,
            *(() if self.fallback.url is None else (self.fallback.url,)),
            *self.verification.evidence_urls,
        )
        for url in urls:
            hostname = urlsplit(str(url)).hostname
            if not any(_host_matches(hostname, domain) for domain in allowed_domains):
                raise ValueError("source URL does not use an authoritative domain")
        return self

    def to_review_row(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "organization": self.organization,
            "dataset_title": self.dataset_title,
            "analytical_purpose": self.analytical_purpose,
            "transport": self.transport,
            "official_domain": self.official_domain,
            "catalog_id": self.catalog_id or "",
            "release": self.release,
            "years": "|".join(self.years),
            "geography": self.geography,
            "expected_grain": self.expected_grain,
            "primary_key": "|".join(self.primary_key),
            "verification_status": self.verification.status,
            "access_date": self.access_date.isoformat(),
            "endpoint_url": str(self.endpoint_url),
            "fallback_status": self.fallback.status,
        }


class SourceRegistry(RegistryModel):
    schema_version: int = Field(ge=1)
    registry_date: date
    sources: tuple[RegistrySource, ...]

    @model_validator(mode="after")
    def source_ids_are_exact_and_unique(self) -> SourceRegistry:
        ids = [source.source_id for source in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("source_id values must be unique")
        observed = set(ids)
        if observed != REQUIRED_SOURCE_IDS:
            missing = sorted(REQUIRED_SOURCE_IDS - observed)
            unexpected = sorted(observed - REQUIRED_SOURCE_IDS)
            raise ValueError(
                f"registry source IDs differ: missing={missing}, unexpected={unexpected}"
            )
        return self

    @property
    def by_id(self) -> dict[str, RegistrySource]:
        return {source.source_id: source for source in self.sources}


MATRIX_COLUMNS = (
    "source_id",
    "organization",
    "dataset_title",
    "analytical_purpose",
    "transport",
    "official_domain",
    "catalog_id",
    "release",
    "years",
    "geography",
    "expected_grain",
    "primary_key",
    "verification_status",
    "access_date",
    "endpoint_url",
    "fallback_status",
)


def load_registry(path: Path) -> SourceRegistry:
    """Load and strictly validate the canonical YAML registry."""
    payload: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SourceRegistry.model_validate(payload)


def export_acquisition_matrix_bytes(registry: SourceRegistry) -> bytes:
    """Render stable UTF-8 CSV bytes ordered by source ID."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=MATRIX_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for source in sorted(registry.sources, key=lambda item: item.source_id):
        writer.writerow(source.to_review_row())
    return output.getvalue().encode("utf-8")


def export_acquisition_matrix(registry: SourceRegistry, path: Path) -> None:
    """Write the deterministic human-review acquisition matrix."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(export_acquisition_matrix_bytes(registry))
