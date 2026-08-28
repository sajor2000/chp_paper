"""Credential-free acquisition plans and the public adapter protocol."""

from __future__ import annotations

from typing import Protocol

from pydantic import Field, HttpUrl, field_validator

from chicagohealthmap.sources.models import (
    ContractModel,
    Identifier,
    SnapshotManifest,
    SourceSpec,
    _is_credential_name,
    _validate_relative_path,
)
from chicagohealthmap.sources.snapshot import SnapshotWriter


class AcquisitionPlan(ContractModel):
    """Immutable, deterministic, and safe-to-display acquisition metadata."""

    source_id: Identifier
    url: HttpUrl
    parameters: tuple[tuple[str, str], ...] = ()
    transport: str
    destination_paths: tuple[str, ...] = Field(min_length=1)
    required_environment_variables: tuple[str, ...] = ()
    estimated_request_count: int | None = Field(default=None, ge=1)
    fallback_status: str

    @field_validator("parameters")
    @classmethod
    def parameters_are_ordered_and_credential_free(
        cls, value: tuple[tuple[str, str], ...]
    ) -> tuple[tuple[str, str], ...]:
        if any(_is_credential_name(name) for name, _ in value):
            raise ValueError("acquisition plan parameters must not contain credentials")
        return value

    @field_validator("destination_paths")
    @classmethod
    def destinations_are_relative(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for path in value:
            _validate_relative_path(path, "destination path")
        return value

    @field_validator("required_environment_variables")
    @classmethod
    def environment_names_are_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)) or any(not name.strip() for name in value):
            raise ValueError("required environment variable names must be nonempty and unique")
        return value


class SourceAdapter(Protocol):
    """Adapter boundary frozen by the Phase 4 design."""

    def plan(self, spec: SourceSpec) -> AcquisitionPlan:
        raise NotImplementedError

    def fetch(self, spec: SourceSpec, writer: SnapshotWriter) -> SnapshotManifest:
        raise NotImplementedError
