"""Strict ingestion for evidence-verified headerless pipe exports."""

from __future__ import annotations

import csv
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from chicagohealthmap.ingest.schemas import FieldSchema, TableSchema

MISSING_TOKEN = r"\N"
INTEGER_PATTERN = re.compile(r"[+-]?[0-9]+")
FLOAT_PATTERN = re.compile(r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:[eE][+-]?[0-9]+)?")
TIMESTAMP_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?"
    r"(?:Z|[+-][0-9]{2}:[0-9]{2})"
)


class PipeIngestionError(ValueError):
    """Raised when source bytes do not satisfy a verified table contract."""


def _parse_value(value: str, field: FieldSchema, row_number: int) -> Any:
    if value == MISSING_TOKEN:
        if not field.nullable:
            raise PipeIngestionError(
                f"missing value in nonnullable field {field.name!r} at row {row_number}"
            )
        return pd.NA

    try:
        if field.data_type == "string":
            return value
        if field.data_type == "integer":
            if INTEGER_PATTERN.fullmatch(value) is None:
                raise ValueError
            return int(value)
        if field.data_type == "float":
            if FLOAT_PATTERN.fullmatch(value) is None:
                raise ValueError
            parsed = float(value)
            if not math.isfinite(parsed):
                raise ValueError
            return parsed
        if field.data_type == "boolean":
            if value not in {"t", "f"}:
                raise ValueError
            return value == "t"
        if field.data_type == "timestamp":
            if TIMESTAMP_PATTERN.fullmatch(value) is None:
                raise ValueError
            parsed_timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return pd.Timestamp(parsed_timestamp.astimezone(timezone.utc))
    except (TypeError, ValueError, OverflowError) as error:
        raise PipeIngestionError(
            f"invalid {field.data_type} in field {field.name!r} at row {row_number}"
        ) from error
    raise PipeIngestionError(f"unsupported field type for {field.name!r}")


def _typed_series(values: list[Any], field: FieldSchema) -> pd.Series:
    if field.data_type == "string":
        return pd.Series(values, dtype="string")
    if field.data_type == "integer":
        return pd.Series(values, dtype="Int64")
    if field.data_type == "float":
        return pd.Series(values, dtype="Float64")
    if field.data_type == "boolean":
        return pd.Series(values, dtype="boolean")
    if field.data_type == "timestamp":
        return pd.to_datetime(pd.Series(values), utc=True)
    raise PipeIngestionError(f"unsupported field type for {field.name!r}")


def read_pipe_table(
    path: Path,
    schema: TableSchema,
    *,
    source_id: str,
    snapshot_id: str,
) -> pd.DataFrame:
    """Parse a headerless pipe table without inference or coercion.

    The source is not opened until every field has verified semantics. This makes the
    evidence gate independent of whether local protected bytes are present.
    """

    if not schema.analysis_usable:
        raise PipeIngestionError("table schema is not fully verified for analysis")
    if schema.empty_expected:
        raise PipeIngestionError("an expected-empty schema has no verified field contract")

    columns: dict[str, list[Any]] = {field.name: [] for field in schema.fields}
    try:
        with path.open("rt", encoding="utf-8", errors="strict", newline="") as handle:
            reader = csv.reader(handle, delimiter="|", quoting=csv.QUOTE_NONE, strict=True)
            for row_number, row in enumerate(reader, start=1):
                if len(row) != len(schema.fields):
                    raise PipeIngestionError(
                        f"field count mismatch at row {row_number}: "
                        f"expected {len(schema.fields)}, observed {len(row)}"
                    )
                for field, value in zip(schema.fields, row, strict=True):
                    columns[field.name].append(_parse_value(value, field, row_number))
    except UnicodeDecodeError as error:
        raise PipeIngestionError("source is not valid UTF-8") from error
    except csv.Error as error:
        raise PipeIngestionError("malformed pipe-delimited source") from error
    except OSError as error:
        raise PipeIngestionError("source file could not be read") from error

    frame = pd.DataFrame(
        {field.name: _typed_series(columns[field.name], field) for field in schema.fields}
    )
    primary_key = [field.name for field in schema.fields if field.key_role == "primary"]
    if primary_key:
        duplicate = frame.duplicated(primary_key, keep=False)
        if duplicate.any():
            rows = [
                str(position)
                for position in range(1, len(frame) + 1)
                if duplicate.iloc[position - 1]
            ]
            raise PipeIngestionError("duplicate primary key at source row(s): " + ", ".join(rows))

    frame["source_id"] = pd.Series([source_id] * len(frame), dtype="string")
    frame["snapshot_id"] = pd.Series([snapshot_id] * len(frame), dtype="string")
    frame["source_file"] = pd.Series([path.name] * len(frame), dtype="string")
    frame["source_row_number"] = pd.Series(range(1, len(frame) + 1), dtype="Int64")
    return frame


def write_validated_parquet(
    source: Path,
    schema: TableSchema,
    destination: Path,
    *,
    source_id: str,
    snapshot_id: str,
) -> pd.DataFrame:
    """Validate the complete source, then atomically publish a Parquet table."""

    try:
        resolved_alias = source.resolve(strict=False) == destination.resolve(strict=False)
        existing_alias = source.exists() and destination.exists() and source.samefile(destination)
    except OSError as error:
        raise PipeIngestionError("source/destination alias check failed") from error
    if resolved_alias or existing_alias:
        raise PipeIngestionError("source and Parquet destination alias the same file")

    frame = read_pipe_table(source, schema, source_id=source_id, snapshot_id=snapshot_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
    try:
        table = pa.Table.from_pandas(frame, preserve_index=False)
        pq.write_table(table, staging)
        with staging.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(staging, destination)
    finally:
        staging.unlink(missing_ok=True)
    return frame
