from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from chicagohealthmap.ingest.pipe import (
    PipeIngestionError,
    read_pipe_table,
    write_validated_parquet,
)
from chicagohealthmap.ingest.schemas import EvidenceStatus, FieldSchema, TableSchema


def _schema(*, verified: bool = True) -> TableSchema:
    evidence = EvidenceStatus.verified if verified else EvidenceStatus.unverified
    fields = (
        FieldSchema(
            position=1,
            name="record_id",
            data_type="string",
            nullable=False,
            key_role="primary",
            unit="identifier",
            evidence_status=evidence,
            evidence_source="fixture contract",
        ),
        FieldSchema(
            position=2,
            name="count",
            data_type="integer",
            nullable=True,
            key_role="none",
            unit="people",
            evidence_status=evidence,
            evidence_source="fixture contract",
        ),
        FieldSchema(
            position=3,
            name="ratio",
            data_type="float",
            nullable=False,
            key_role="none",
            unit="proportion",
            evidence_status=evidence,
            evidence_source="fixture contract",
        ),
        FieldSchema(
            position=4,
            name="active",
            data_type="boolean",
            nullable=False,
            key_role="none",
            unit="flag",
            evidence_status=evidence,
            evidence_source="fixture contract",
        ),
        FieldSchema(
            position=5,
            name="observed_at",
            data_type="timestamp",
            nullable=False,
            key_role="none",
            unit="timestamp",
            evidence_status=evidence,
            evidence_source="fixture contract",
        ),
    )
    return TableSchema(observed_rows=2, observed_field_counts=(5,), fields=fields)


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_read_pipe_table_parses_verified_types_missing_and_provenance(tmp_path: Path) -> None:
    source = _write(
        tmp_path / "fixture.text",
        "001|7|0.25|t|2024-01-02T03:04:05Z\n002|\\N|1.5|f|2024-02-03T00:00:00Z\n",
    )

    frame = read_pipe_table(source, _schema(), source_id="fixture", snapshot_id="fixture_1")

    assert frame["record_id"].tolist() == ["001", "002"]
    assert frame["count"].tolist()[0] == 7
    assert pd.isna(frame["count"].tolist()[1])
    assert frame["active"].tolist() == [True, False]
    assert isinstance(frame["observed_at"].dtype, pd.DatetimeTZDtype)
    assert str(frame["observed_at"].dtype.tz) == "UTC"
    assert frame[["source_id", "snapshot_id", "source_file"]].drop_duplicates().to_dict(
        "records"
    ) == [{"source_id": "fixture", "snapshot_id": "fixture_1", "source_file": "fixture.text"}]
    assert frame["source_row_number"].tolist() == [1, 2]


def test_only_literal_backslash_n_is_missing(tmp_path: Path) -> None:
    source = _write(tmp_path / "fixture.text", "001||0.25|t|2024-01-02T03:04:05Z\n")
    with pytest.raises(PipeIngestionError, match="invalid integer"):
        read_pipe_table(source, _schema(), source_id="fixture", snapshot_id="fixture_1")


def test_field_count_mismatch_is_rejected(tmp_path: Path) -> None:
    source = _write(tmp_path / "fixture.text", "001|7|0.25|t\n")
    with pytest.raises(PipeIngestionError, match="field count.*row 1"):
        read_pipe_table(source, _schema(), source_id="fixture", snapshot_id="fixture_1")


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("001|seven|0.25|t|2024-01-02T03:04:05Z", "invalid integer"),
        ("001|7|quarter|t|2024-01-02T03:04:05Z", "invalid float"),
        ("001|7|0.25|true|2024-01-02T03:04:05Z", "invalid boolean"),
        ("001|7|0.25|t|not-a-time", "invalid timestamp"),
    ],
)
def test_invalid_typed_values_are_never_coerced_to_missing(
    tmp_path: Path, row: str, message: str
) -> None:
    source = _write(tmp_path / "fixture.text", row + "\n")
    with pytest.raises(PipeIngestionError, match=message):
        read_pipe_table(source, _schema(), source_id="fixture", snapshot_id="fixture_1")


def test_malformed_utf8_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "fixture.text"
    source.write_bytes(b"001|7|0.25|t|2024-01-02T03:04:05Z\n\xff")
    with pytest.raises(PipeIngestionError, match="UTF-8"):
        read_pipe_table(source, _schema(), source_id="fixture", snapshot_id="fixture_1")


def test_duplicate_primary_key_is_rejected(tmp_path: Path) -> None:
    source = _write(
        tmp_path / "fixture.text",
        "001|7|0.25|t|2024-01-02T03:04:05Z\n001|8|0.5|f|2024-02-03T00:00:00Z\n",
    )
    with pytest.raises(PipeIngestionError, match="duplicate primary key"):
        read_pipe_table(source, _schema(), source_id="fixture", snapshot_id="fixture_1")


def test_duplicate_composite_primary_key_is_rejected(tmp_path: Path) -> None:
    base = _schema()
    fields = (
        base.fields[0],
        base.fields[1].model_copy(update={"nullable": False, "key_role": "primary"}),
        *base.fields[2:],
    )
    schema = TableSchema(observed_rows=3, observed_field_counts=(5,), fields=fields)
    source = _write(
        tmp_path / "fixture.text",
        "001|7|0.25|t|2024-01-02T03:04:05Z\n"
        "001|8|0.25|t|2024-01-02T03:04:05Z\n"
        "001|7|0.50|f|2024-01-03T03:04:05Z\n",
    )
    with pytest.raises(PipeIngestionError, match="duplicate primary key.*1, 3"):
        read_pipe_table(source, schema, source_id="fixture", snapshot_id="fixture_1")


@pytest.mark.parametrize("value", ["1_000", "nan", "NaN", "inf", "-Infinity"])
def test_float_lexical_contract_rejects_nonfinite_and_python_extensions(
    tmp_path: Path, value: str
) -> None:
    source = _write(tmp_path / "fixture.text", f"001|7|{value}|t|2024-01-02T03:04:05Z\n")
    with pytest.raises(PipeIngestionError, match="invalid float"):
        read_pipe_table(source, _schema(), source_id="fixture", snapshot_id="fixture_1")


@pytest.mark.parametrize(
    "value",
    [
        "2024-01-02",
        "2024-01-02T03:04:05",
        "01/02/2024 03:04:05Z",
        "now",
        "2024-01-02 03:04:05Z",
    ],
)
def test_timestamp_requires_deterministic_zoned_iso_8601(tmp_path: Path, value: str) -> None:
    source = _write(tmp_path / "fixture.text", f"001|7|0.25|t|{value}\n")
    with pytest.raises(PipeIngestionError, match="invalid timestamp"):
        read_pipe_table(source, _schema(), source_id="fixture", snapshot_id="fixture_1")


def test_unverified_schema_is_rejected_before_source_is_read(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.text"
    with pytest.raises(PipeIngestionError, match="not fully verified"):
        read_pipe_table(
            missing, _schema(verified=False), source_id="fixture", snapshot_id="fixture_1"
        )


def test_parquet_is_written_only_after_validation(tmp_path: Path) -> None:
    bad = _write(tmp_path / "bad.text", "001|invalid|0.25|t|2024-01-02T03:04:05Z\n")
    destination = tmp_path / "table.parquet"
    with pytest.raises(PipeIngestionError):
        write_validated_parquet(
            bad, _schema(), destination, source_id="fixture", snapshot_id="fixture_1"
        )
    assert not destination.exists()

    good = _write(tmp_path / "good.text", "001|7|0.25|t|2024-01-02T03:04:05Z\n")
    write_validated_parquet(
        good, _schema(), destination, source_id="fixture", snapshot_id="fixture_1"
    )
    assert pd.read_parquet(destination)["record_id"].tolist() == ["001"]


def test_parquet_rejects_direct_source_destination_alias_without_modifying_source(
    tmp_path: Path,
) -> None:
    source = _write(tmp_path / "fixture.text", "001|7|0.25|t|2024-01-02T03:04:05Z\n")
    original = source.read_bytes()
    with pytest.raises(PipeIngestionError, match="alias"):
        write_validated_parquet(
            source, _schema(), source, source_id="fixture", snapshot_id="fixture_1"
        )
    assert source.read_bytes() == original


def test_parquet_rejects_resolved_symlink_alias_without_modifying_source(tmp_path: Path) -> None:
    source = _write(tmp_path / "fixture.text", "001|7|0.25|t|2024-01-02T03:04:05Z\n")
    destination = tmp_path / "alias.parquet"
    destination.symlink_to(source)
    original = source.read_bytes()
    with pytest.raises(PipeIngestionError, match="alias"):
        write_validated_parquet(
            source, _schema(), destination, source_id="fixture", snapshot_id="fixture_1"
        )
    assert source.read_bytes() == original
    assert destination.is_symlink()


def test_parquet_rejects_hardlink_alias_without_modifying_source(tmp_path: Path) -> None:
    source = _write(tmp_path / "fixture.text", "001|7|0.25|t|2024-01-02T03:04:05Z\n")
    destination = tmp_path / "alias.parquet"
    destination.hardlink_to(source)
    original = source.read_bytes()
    with pytest.raises(PipeIngestionError, match="alias"):
        write_validated_parquet(
            source, _schema(), destination, source_id="fixture", snapshot_id="fixture_1"
        )
    assert source.read_bytes() == original
    assert destination.read_bytes() == original
