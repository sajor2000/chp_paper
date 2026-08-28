import hashlib
import json
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.sources.first_party import (
    FirstPartyValidationError,
    inventory_first_party,
    preserve_first_party,
)


def test_inventory_reports_missing_and_unexpected_text_files(tmp_path: Path) -> None:
    (tmp_path / "present.text").write_bytes(b"present")
    (tmp_path / "extra.text").write_bytes(b"extra")
    (tmp_path / "ignored.csv").write_bytes(b"not an export")

    inventory = inventory_first_party(tmp_path, ("present.text", "absent.text"))

    assert inventory.missing_files == ("absent.text",)
    assert inventory.unexpected_files == ("extra.text",)
    assert tuple(file.path for file in inventory.files) == ("present.text",)


def test_inventory_records_zero_byte_exports_for_methods_review(tmp_path: Path) -> None:
    expected = ("drug_providers.text", "wic_locations.text", "data.text")
    for name in expected[:2]:
        (tmp_path / name).touch()
    (tmp_path / "data.text").write_bytes(b"row")

    inventory = inventory_first_party(tmp_path, expected)

    assert inventory.observed_empty_files == expected[:2]
    assert inventory.methods_review_files == expected[:2]
    assert {file.path: file.byte_count for file in inventory.files} == {
        "drug_providers.text": 0,
        "wic_locations.text": 0,
        "data.text": 3,
    }


def test_inventory_records_byte_counts_and_detects_changed_hashes(tmp_path: Path) -> None:
    export = tmp_path / "data.text"
    export.write_bytes(b"first")

    before = inventory_first_party(tmp_path, (export.name,)).files[0]
    export.write_bytes(b"second version")
    after = inventory_first_party(tmp_path, (export.name,)).files[0]

    assert before.byte_count == 5
    assert before.sha256 == hashlib.sha256(b"first").hexdigest()
    assert after.byte_count == 14
    assert after.sha256 == hashlib.sha256(b"second version").hexdigest()
    assert after.sha256 != before.sha256


def test_preservation_fails_before_copying_when_an_expected_file_is_missing(
    tmp_path: Path,
) -> None:
    source = tmp_path / "exports"
    snapshots = tmp_path / "snapshot-root"
    source.mkdir()
    (source / "present.text").write_bytes(b"present")

    with pytest.raises(FirstPartyValidationError, match="missing expected export"):
        preserve_first_party(
            source,
            snapshots,
            date(2026, 5, 27),
            ("present.text", "missing.text"),
        )

    assert not snapshots.exists()
    assert (source / "present.text").read_bytes() == b"present"


def test_preservation_copies_all_expected_files_including_observed_empty(
    tmp_path: Path,
) -> None:
    source = tmp_path / "exports"
    snapshots = tmp_path / "snapshot-root"
    source.mkdir()
    expected = ("data.text", "drug_providers.text", "wic_locations.text")
    (source / "data.text").write_bytes(b"payload")
    (source / "drug_providers.text").touch()
    (source / "wic_locations.text").touch()

    manifest = preserve_first_party(source, snapshots, date(2026, 5, 27), expected)

    final = snapshots / "first_party/capricorn/snapshots/2026-05-27"
    assert tuple(file.path for file in manifest.files) == tuple(
        f"original/{name}" for name in expected
    )
    assert {path.name: path.read_bytes() for path in (final / "original").iterdir()} == {
        "data.text": b"payload",
        "drug_providers.text": b"",
        "wic_locations.text": b"",
    }
    assert (source / "data.text").read_bytes() == b"payload"
    assert all((source / name).exists() for name in expected)


def _write_first_party_config(root: Path) -> tuple[str, ...]:
    expected = ("data.text", "drug_providers.text", "wic_locations.text")
    config = root / "config"
    config.mkdir()
    (config / "first_party_sources.yml").write_text(
        "\n".join(
            (
                "source_id: capricorn_chicagohealthmap_export_2026_05_27",
                "organization: CAPriCORN and CONSCIENCE Project",
                'snapshot_date: "2026-05-27"',
                "files:",
                *(f"  - {name}" for name in expected),
                "",
            )
        )
    )
    return expected


def _write_exports(root: Path, expected: tuple[str, ...]) -> Path:
    exports = root / "exports"
    exports.mkdir()
    (exports / expected[0]).write_bytes(b"payload")
    for name in expected[1:]:
        (exports / name).touch()
    return exports


def test_preserve_first_party_dry_run_reports_inventory_without_writes(tmp_path: Path) -> None:
    expected = _write_first_party_config(tmp_path)
    exports = _write_exports(tmp_path, expected)

    result = CliRunner().invoke(
        app,
        [
            "sources",
            "preserve-first-party",
            "--source-root",
            str(exports),
            "--snapshot-date",
            "2026-05-27",
            "--dry-run",
        ],
        env={"CHICAGOHEALTHMAP_ROOT": str(tmp_path)},
    )

    assert result.exit_code == 0
    assert "Expected files: 3" in result.stdout
    assert "Observed empty files: 2" in result.stdout
    assert "Missing files: 0" in result.stdout
    assert "Unexpected files: 0" in result.stdout
    assert "Dry run: no files written" in result.stdout
    assert not (tmp_path / "sources").exists()


def test_preserve_and_verify_first_party_snapshot(tmp_path: Path) -> None:
    expected = _write_first_party_config(tmp_path)
    exports = _write_exports(tmp_path, expected)
    runner = CliRunner()

    preserve = runner.invoke(
        app,
        [
            "sources",
            "preserve-first-party",
            "--source-root",
            str(exports),
            "--snapshot-date",
            "2026-05-27",
        ],
        env={"CHICAGOHEALTHMAP_ROOT": str(tmp_path)},
    )
    verify = runner.invoke(
        app,
        [
            "sources",
            "verify",
            "--source",
            "capricorn_chicagohealthmap_export_2026_05_27",
        ],
        env={"CHICAGOHEALTHMAP_ROOT": str(tmp_path)},
    )

    assert preserve.exit_code == 0
    assert "Preserved files: 3" in preserve.stdout
    assert verify.exit_code == 0
    assert "Matching checksums: 3" in verify.stdout
    assert "Unexpected files: 0" in verify.stdout


def _preserve_cli_snapshot(tmp_path: Path) -> tuple[CliRunner, Path, Path]:
    expected = _write_first_party_config(tmp_path)
    exports = _write_exports(tmp_path, expected)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "sources",
            "preserve-first-party",
            "--source-root",
            str(exports),
            "--snapshot-date",
            "2026-05-27",
        ],
        env={"CHICAGOHEALTHMAP_ROOT": str(tmp_path)},
    )
    assert result.exit_code == 0
    snapshot = tmp_path / "sources/first_party/capricorn/snapshots/2026-05-27"
    return runner, exports, snapshot


def _verify_cli_snapshot(runner: CliRunner, root: Path):
    return runner.invoke(
        app,
        [
            "sources",
            "verify",
            "--source",
            "capricorn_chicagohealthmap_export_2026_05_27",
        ],
        env={"CHICAGOHEALTHMAP_ROOT": str(root)},
    )


def test_verify_rejects_manifest_and_snapshot_truncated_together(tmp_path: Path) -> None:
    runner, _, snapshot = _preserve_cli_snapshot(tmp_path)
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"] = [
        record for record in manifest["files"] if record["path"] != "original/data.text"
    ]
    manifest_path.write_text(json.dumps(manifest))
    (snapshot / "original/data.text").unlink()

    result = _verify_cli_snapshot(runner, tmp_path)

    assert result.exit_code == 1
    assert "Manifest missing entries: 1" in result.output
    assert "Missing files: 1" in result.output
    assert "Matching checksums: 2" in result.output


def test_verify_rejects_duplicate_manifest_entries(tmp_path: Path) -> None:
    runner, _, snapshot = _preserve_cli_snapshot(tmp_path)
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"].append(manifest["files"][0])
    manifest_path.write_text(json.dumps(manifest))

    result = _verify_cli_snapshot(runner, tmp_path)

    assert result.exit_code == 1
    assert "Manifest duplicate entries: 1" in result.output


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source_id", "wrong_source", "Manifest source mismatch"),
        ("snapshot_date", "2026-05-26", "Manifest snapshot date mismatch"),
        (
            "snapshot_id",
            "capricorn_chicagohealthmap_export_2026_05_27_2026-05-26",
            "Manifest snapshot identity mismatch",
        ),
    ],
)
def test_verify_rejects_wrong_manifest_identity(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    runner, _, snapshot = _preserve_cli_snapshot(tmp_path)
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest[field] = value
    manifest_path.write_text(json.dumps(manifest))

    result = _verify_cli_snapshot(runner, tmp_path)

    assert result.exit_code == 1
    assert message in result.output


@pytest.mark.parametrize(
    ("mutation", "expected_message"),
    [
        ("missing", "Missing files: 1"),
        ("altered", "Mismatching checksums: 1"),
        ("unexpected", "Unexpected files: 1"),
    ],
)
def test_verify_rejects_missing_altered_and_unexpected_original_files(
    tmp_path: Path, mutation: str, expected_message: str
) -> None:
    runner, _, snapshot = _preserve_cli_snapshot(tmp_path)
    if mutation == "missing":
        (snapshot / "original/data.text").unlink()
    elif mutation == "altered":
        (snapshot / "original/data.text").write_bytes(b"altered")
    else:
        (snapshot / "original/unexpected.text").write_bytes(b"unexpected")

    result = _verify_cli_snapshot(runner, tmp_path)

    assert result.exit_code == 1
    assert expected_message in result.output


def test_preserve_rejects_snapshot_date_different_from_config(tmp_path: Path) -> None:
    expected = _write_first_party_config(tmp_path)
    exports = _write_exports(tmp_path, expected)

    result = CliRunner().invoke(
        app,
        [
            "sources",
            "preserve-first-party",
            "--source-root",
            str(exports),
            "--snapshot-date",
            "2026-05-26",
        ],
        env={"CHICAGOHEALTHMAP_ROOT": str(tmp_path)},
    )

    assert result.exit_code == 2
    assert "must match configured snapshot date" in result.output
    assert "2026-05-27" in result.output
    assert not (tmp_path / "sources").exists()


def test_preserve_existing_snapshot_returns_concise_error(tmp_path: Path) -> None:
    runner, exports, _ = _preserve_cli_snapshot(tmp_path)

    result = runner.invoke(
        app,
        [
            "sources",
            "preserve-first-party",
            "--source-root",
            str(exports),
            "--snapshot-date",
            "2026-05-27",
        ],
        env={"CHICAGOHEALTHMAP_ROOT": str(tmp_path)},
    )

    assert result.exit_code == 1
    assert "Snapshot already finalized for 2026-05-27" in result.output
    assert "Traceback" not in result.output
    assert type(result.exception) is SystemExit


def test_verify_missing_manifest_returns_concise_error(tmp_path: Path) -> None:
    runner, _, snapshot = _preserve_cli_snapshot(tmp_path)
    (snapshot / "manifest.json").unlink()

    result = _verify_cli_snapshot(runner, tmp_path)

    assert result.exit_code == 1
    assert "Snapshot metadata is missing or invalid" in result.output
    assert "Traceback" not in result.output
    assert type(result.exception) is SystemExit


def test_invalid_config_returns_concise_error(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.mkdir()
    (config / "first_party_sources.yml").write_text(
        "source_id: capricorn_chicagohealthmap_export_2026_05_27\n"
        "snapshot_date: not-a-date\n"
        "files: [data.text]\n"
    )

    result = CliRunner().invoke(
        app,
        [
            "sources",
            "verify",
            "--source",
            "capricorn_chicagohealthmap_export_2026_05_27",
        ],
        env={"CHICAGOHEALTHMAP_ROOT": str(tmp_path)},
    )

    assert result.exit_code == 1
    assert "First-party source configuration is missing or invalid" in result.output
    assert "Traceback" not in result.output
    assert type(result.exception) is SystemExit
