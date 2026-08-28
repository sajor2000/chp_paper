"""Evidence-qualified positional schemas for headerless first-party exports."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class SchemaContractError(ValueError):
    """Raised when a schema is structurally invalid or is used beyond its evidence."""


class EvidenceStatus(StrEnum):
    """Whether evidence establishes the semantic identity of a field."""

    verified = "verified"
    unverified = "unverified"


class FieldSchema(BaseModel):
    """One ordered source field and its evidence-qualified interpretation."""

    model_config = ConfigDict(frozen=True)

    position: int = Field(ge=1)
    name: str = Field(min_length=1)
    data_type: Literal["string", "integer", "float", "boolean", "timestamp"]
    nullable: bool
    key_role: Literal["none", "primary", "foreign"]
    unit: str = Field(min_length=1)
    evidence_status: EvidenceStatus
    evidence_source: str = Field(min_length=1)


class PositionalContract(BaseModel):
    """Compact declaration for semantically unknown, losslessly retained positions."""

    model_config = ConfigDict(frozen=True)

    count: int = Field(ge=1)
    data_type: Literal["string"] = "string"
    nullable: Literal[True] = True
    key_role: Literal["none"] = "none"
    unit: Literal["source_text"] = "source_text"
    evidence_status: Literal[EvidenceStatus.unverified]
    evidence_source: str = Field(min_length=1)

    def expand(self) -> tuple[FieldSchema, ...]:
        return tuple(
            FieldSchema(
                position=position,
                name=f"unverified_position_{position:02d}",
                data_type=self.data_type,
                nullable=self.nullable,
                key_role=self.key_role,
                unit=self.unit,
                evidence_status=self.evidence_status,
                evidence_source=self.evidence_source,
            )
            for position in range(1, self.count + 1)
        )


class TableSchema(BaseModel):
    """Complete source-shape contract for one export.

    Generic positional names preserve exact order without claiming undocumented semantics.
    """

    model_config = ConfigDict(frozen=True)

    observed_rows: int = Field(ge=0)
    observed_field_counts: tuple[int, ...]
    empty_expected: bool = False
    fields: tuple[FieldSchema, ...] = ()
    positional_contract: PositionalContract | None = Field(default=None, exclude=True)
    validated_field_count_exception: str | None = None
    suppression_semantics: str = "unverified"

    @model_validator(mode="after")
    def validate_contract(self) -> TableSchema:
        fields = self.fields
        if self.positional_contract is not None:
            if fields:
                raise ValueError("declare fields or positional_contract, not both")
            fields = self.positional_contract.expand()
            object.__setattr__(self, "fields", fields)

        if len(set(self.observed_field_counts)) != len(self.observed_field_counts):
            raise ValueError("observed_field_counts must be unique")
        if any(count < 1 for count in self.observed_field_counts):
            raise ValueError("observed field counts must be positive")
        if len(self.observed_field_counts) > 1 and not self.validated_field_count_exception:
            raise ValueError("multiple observed field counts require a validated exception")

        if self.empty_expected:
            if self.observed_rows != 0 or self.observed_field_counts or fields:
                raise ValueError("an expected-empty table cannot declare observed fields or rows")
            return self

        if self.observed_rows == 0:
            raise ValueError("an observed-empty table must set empty_expected: true")
        if not self.observed_field_counts or not fields:
            raise ValueError("a nonempty table requires fields and an observed field count")
        if [field.position for field in fields] != list(range(1, len(fields) + 1)):
            raise ValueError("field positions must be contiguous and one-based")
        if len({field.name for field in fields}) != len(fields):
            raise ValueError("field names must be unique")
        if max(self.observed_field_counts) != len(fields):
            raise ValueError("declared fields must match the largest observed field count")
        return self

    @property
    def analysis_usable(self) -> bool:
        """Return true only when every position has verified semantic evidence."""

        return bool(self.fields) and all(
            field.evidence_status is EvidenceStatus.verified for field in self.fields
        )

    def require_verified_fields(self, names: tuple[str, ...]) -> None:
        """Reject dependent work when a requested field lacks semantic evidence."""

        by_name = {field.name: field for field in self.fields}
        for name in names:
            field = by_name.get(name)
            if field is None:
                raise SchemaContractError(f"field is absent from schema: {name}")
            if field.evidence_status is EvidenceStatus.unverified:
                raise SchemaContractError(f"field is not verified for analysis: {name}")


class SchemaCatalog(BaseModel):
    """Versioned catalog of all first-party table contracts."""

    model_config = ConfigDict(frozen=True)

    schema_version: Literal[1]
    tables: dict[str, TableSchema]


def observed_table_shape(path: Path) -> tuple[int, set[int]]:
    """Return the row count and pipe-delimited field counts observed in source bytes."""

    rows = 0
    counts: set[int] = set()
    with path.open("rt", encoding="utf-8", newline="") as handle:
        for line in handle:
            rows += 1
            counts.add(len(line.rstrip("\r\n").split("|")))
    return rows, counts


def observed_field_counts(path: Path) -> set[int]:
    """Return all pipe-delimited field counts observed in a UTF-8 source file."""

    return observed_table_shape(path)[1]


def load_schema_catalog(path: Path) -> SchemaCatalog:
    """Load and validate a schema catalog, presenting one stable error type."""

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return SchemaCatalog.model_validate(payload)
    except (OSError, UnicodeError, yaml.YAMLError, ValidationError) as error:
        raise SchemaContractError(str(error)) from error
