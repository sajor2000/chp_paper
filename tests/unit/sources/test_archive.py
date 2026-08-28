import hashlib
import json
import stat
import zipfile
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

import chicagohealthmap.sources.first_party as first_party
from chicagohealthmap.cli import app


def _write_zip(path: Path, members: list[tuple[str, bytes]]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members:
            archive.writestr(name, content)


def _write_website_config(
    root: Path,
    archives: tuple[Path, ...],
    *,
    filenames: tuple[str, ...] | None = None,
    hashes: tuple[str, ...] | None = None,
    expected_archive_count: int | None = None,
    expected_member_count: int,
    expected_duplicate_content_count: int,
    source_id: str = "chicagohealthmap_website_methods",
    snapshot_date: str = "2026-07-13",
) -> None:
    config = root / "config"
    config.mkdir(exist_ok=True)
    configured_names = filenames or tuple(archive.name for archive in archives)
    configured_hashes = hashes or tuple(
        hashlib.sha256(archive.read_bytes()).hexdigest() for archive in archives
    )
    payload = {
        "website_methods": {
            "source_id": source_id,
            "snapshot_date": snapshot_date,
            "expected_archive_count": (
                len(archives) if expected_archive_count is None else expected_archive_count
            ),
            "expected_member_count": expected_member_count,
            "expected_duplicate_content_count": expected_duplicate_content_count,
            "archives": [
                {"filename": name, "sha256": digest}
                for name, digest in zip(configured_names, configured_hashes, strict=True)
            ],
        }
    }
    (config / "first_party_sources.yml").write_text(yaml.safe_dump(payload, sort_keys=False))


def _invoke_preserve(root: Path, archives: tuple[Path, ...], date_value: str = "2026-07-13"):
    arguments = ["sources", "preserve-website-archives"]
    for archive in archives:
        arguments.extend(("--archive", str(archive)))
    arguments.extend(("--snapshot-date", date_value))
    return CliRunner().invoke(
        app,
        arguments,
        env={"CHICAGOHEALTHMAP_ROOT": str(root)},
    )


def _settings_for(
    archives: tuple[Path, ...], *, member_count: int, duplicate_count: int
) -> first_party.WebsiteArchiveSettings:
    return first_party.WebsiteArchiveSettings(
        source_id=first_party.WEBSITE_SOURCE_SPEC.source_id,
        snapshot_date=first_party.date(2026, 7, 13),
        expected_archive_count=len(archives),
        expected_member_count=member_count,
        expected_duplicate_content_count=duplicate_count,
        archives=tuple(
            first_party.WebsiteArchiveExpectation(
                filename=archive.name,
                sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            )
            for archive in archives
        ),
    )


@pytest.mark.parametrize("member_name", ["/absolute.md", "../traversal.md"])
def test_inspect_zip_rejects_absolute_and_traversal_members(
    tmp_path: Path, member_name: str
) -> None:
    archive = tmp_path / "unsafe.zip"
    _write_zip(archive, [(member_name, b"unsafe")])

    with pytest.raises(first_party.ArchiveSafetyError):
        first_party.inspect_zip(archive)


def test_inspect_zip_rejects_symlink_members(tmp_path: Path) -> None:
    archive = tmp_path / "symlink.zip"
    link = zipfile.ZipInfo("link.md")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "w") as destination:
        destination.writestr(link, "target.md")

    with pytest.raises(first_party.ArchiveSafetyError):
        first_party.inspect_zip(archive)


def test_inspect_zip_rejects_duplicate_member_destinations(tmp_path: Path) -> None:
    archive = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(archive, "w") as destination:
        destination.writestr("page.md", b"first")
        with pytest.warns(UserWarning, match="Duplicate name"):
            destination.writestr("page.md", b"second")

    with pytest.raises(first_party.ArchiveSafetyError, match="duplicate"):
        first_party.inspect_zip(archive)


def test_extract_zip_verified_never_overwrites_different_bytes(tmp_path: Path) -> None:
    archive = tmp_path / "safe.zip"
    _write_zip(archive, [("site/page.md", b"archived")])
    extracted = tmp_path / "extracted"
    destination = extracted / "site/page.md"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"local conflict")

    with pytest.raises(first_party.ArchiveSafetyError, match="different bytes"):
        first_party.extract_zip_verified(archive, extracted)

    assert destination.read_bytes() == b"local conflict"


def test_archive_report_retains_archive_hashes_and_deduplicates_glossary_content(
    tmp_path: Path,
) -> None:
    glossary = b"# Data glossary\nCanonical methods evidence.\n"
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    _write_zip(
        first,
        [
            ("capture-a/chicagohealthmap.com_data-glossary.md", glossary),
            ("capture-a/chicagohealthmap.com_about.md", b"# About\n"),
        ],
    )
    _write_zip(
        second,
        [("capture-b/chicagohealthmap.com_data-glossary.md", glossary)],
    )

    report = first_party.inspect_website_archives((first, second))

    expected_archive_hashes = {
        hashlib.sha256(first.read_bytes()).hexdigest(),
        hashlib.sha256(second.read_bytes()).hexdigest(),
    }
    assert {record.sha256 for record in report.archives} == expected_archive_hashes
    assert len(report.members) == 3
    assert len(report.duplicate_contents) == 1
    duplicate = report.duplicate_contents[0]
    assert duplicate.member_sha256 == hashlib.sha256(glossary).hexdigest()
    assert duplicate.canonical_member_path.endswith(
        "capture-a/chicagohealthmap.com_data-glossary.md"
    )
    assert duplicate.duplicate_member_path.endswith(
        "capture-b/chicagohealthmap.com_data-glossary.md"
    )
    assert duplicate.canonical_archive_sha256 in expected_archive_hashes
    assert duplicate.duplicate_archive_sha256 in expected_archive_hashes


def test_preserve_website_archives_cli_copies_extracts_and_persists_inventory(
    tmp_path: Path,
) -> None:
    glossary = b"# Data glossary\n"
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    _write_zip(
        first,
        [
            ("capture-a/chicagohealthmap.com_data-glossary.md", glossary),
            ("capture-a/chicagohealthmap.com_about.md", b"# About\n"),
        ],
    )
    _write_zip(
        second,
        [("capture-b/chicagohealthmap.com_data-glossary.md", glossary)],
    )
    original_bytes = {archive.name: archive.read_bytes() for archive in (first, second)}
    _write_website_config(
        tmp_path,
        (first, second),
        expected_member_count=3,
        expected_duplicate_content_count=1,
    )

    result = _invoke_preserve(tmp_path, (first, second))

    assert result.exit_code == 0, result.output
    assert "Archive records: 2" in result.stdout
    assert "Website members: 3" in result.stdout
    assert "Duplicate content records: 1" in result.stdout
    snapshot = tmp_path / "sources/first_party/chicagohealthmap/snapshots/2026-07-13"
    assert {
        path.name: path.read_bytes() for path in (snapshot / "original").iterdir()
    } == original_bytes
    assert (
        snapshot / "extracted/capture-a/chicagohealthmap.com_about.md"
    ).read_bytes() == b"# About\n"
    inventory = json.loads((snapshot / "archive_inventory.json").read_text())
    assert len(inventory["archives"]) == 2
    assert len(inventory["members"]) == 3
    assert len(inventory["duplicate_contents"]) == 1
    assert {archive.name: archive.read_bytes() for archive in (first, second)} == original_bytes


def test_preservation_uses_copied_bytes_when_source_changes_after_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "capture.zip"
    initial = b"initial"
    _write_zip(archive, [("capture/page.md", initial)])
    initial_archive_bytes = archive.read_bytes()
    settings = _settings_for((archive,), member_count=1, duplicate_count=0)
    original_copy = first_party.SnapshotWriter.copy_file

    def copy_then_change(writer: first_party.SnapshotWriter, source: Path, relative_path: str):
        copied = original_copy(writer, source, relative_path)
        _write_zip(source, [("capture/page.md", b"changed")])
        return copied

    monkeypatch.setattr(first_party.SnapshotWriter, "copy_file", copy_then_change)

    first_party.preserve_website_archives(
        (archive,),
        tmp_path / "sources",
        first_party.date(2026, 7, 13),
        settings,
    )

    snapshot = tmp_path / "sources/first_party/chicagohealthmap/snapshots/2026-07-13"
    assert (snapshot / "original/capture.zip").read_bytes() == initial_archive_bytes
    assert (snapshot / "extracted/capture/page.md").read_bytes() == initial


def test_preservation_uses_staged_archive_bytes_if_source_changes_before_extraction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "capture.zip"
    initial = b"initial member bytes"
    _write_zip(archive, [("capture/page.md", initial)])
    initial_archive_bytes = archive.read_bytes()
    settings = _settings_for((archive,), member_count=1, duplicate_count=0)
    original_inspect = first_party.inspect_zip
    source_inspections = 0

    def inspect_then_mutate(path: Path):
        nonlocal source_inspections
        inspection = original_inspect(path)
        candidate = Path(path)
        if candidate == archive:
            source_inspections += 1
            if source_inspections == 2:
                _write_zip(archive, [("capture/page.md", b"changed after inspection")])
        else:
            _write_zip(archive, [("capture/page.md", b"changed after staged inspection")])
        return inspection

    monkeypatch.setattr(first_party, "inspect_zip", inspect_then_mutate)

    first_party.preserve_website_archives(
        (archive,),
        tmp_path / "sources",
        first_party.date(2026, 7, 13),
        settings,
    )

    snapshot = tmp_path / "sources/first_party/chicagohealthmap/snapshots/2026-07-13"
    assert (snapshot / "original/capture.zip").read_bytes() == initial_archive_bytes
    assert (snapshot / "extracted/capture/page.md").read_bytes() == initial
    inventory = json.loads((snapshot / "archive_inventory.json").read_text())
    assert inventory["members"][0]["sha256"] == hashlib.sha256(initial).hexdigest()


def _canonical_archives(tmp_path: Path) -> tuple[Path, Path]:
    glossary = b"# glossary\n"
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    _write_zip(first, [("capture-a/glossary.md", glossary), ("capture-a/about.md", b"about")])
    _write_zip(second, [("capture-b/glossary.md", glossary)])
    return first, second


def test_cli_rejects_one_archive_against_configured_pair(tmp_path: Path) -> None:
    archives = _canonical_archives(tmp_path)
    _write_website_config(
        tmp_path,
        archives,
        expected_member_count=3,
        expected_duplicate_content_count=1,
    )

    result = _invoke_preserve(tmp_path, archives[:1])

    assert result.exit_code == 1
    assert "expected 2 archives" in result.output
    assert not (tmp_path / "sources").exists()


def test_cli_rejects_wrong_archive_filename(tmp_path: Path) -> None:
    archives = _canonical_archives(tmp_path)
    _write_website_config(
        tmp_path,
        archives,
        filenames=("canonical-first.zip", "second.zip"),
        expected_member_count=3,
        expected_duplicate_content_count=1,
    )

    result = _invoke_preserve(tmp_path, archives)

    assert result.exit_code == 1
    assert "archive filenames do not match configuration" in result.output
    assert not (tmp_path / "sources").exists()


def test_cli_rejects_wrong_archive_sha256(tmp_path: Path) -> None:
    archives = _canonical_archives(tmp_path)
    _write_website_config(
        tmp_path,
        archives,
        hashes=("0" * 64, hashlib.sha256(archives[1].read_bytes()).hexdigest()),
        expected_member_count=3,
        expected_duplicate_content_count=1,
    )

    result = _invoke_preserve(tmp_path, archives)

    assert result.exit_code == 1
    assert "archive SHA-256 does not match configuration" in result.output
    assert not (tmp_path / "sources").exists()


def test_cli_rejects_extra_archive(tmp_path: Path) -> None:
    archives = _canonical_archives(tmp_path)
    extra = tmp_path / "extra.zip"
    _write_zip(extra, [("capture-c/page.md", b"extra")])
    _write_website_config(
        tmp_path,
        archives,
        expected_member_count=3,
        expected_duplicate_content_count=1,
    )

    result = _invoke_preserve(tmp_path, (*archives, extra))

    assert result.exit_code == 1
    assert "expected 2 archives" in result.output
    assert not (tmp_path / "sources").exists()


def test_cli_rejects_wrong_member_count(tmp_path: Path) -> None:
    archives = _canonical_archives(tmp_path)
    _write_website_config(
        tmp_path,
        archives,
        expected_member_count=4,
        expected_duplicate_content_count=1,
    )

    result = _invoke_preserve(tmp_path, archives)

    assert result.exit_code == 1
    assert "expected 4 website members, observed 3" in result.output
    assert not (tmp_path / "sources/first_party/chicagohealthmap/snapshots/2026-07-13").exists()


def test_cli_rejects_wrong_duplicate_content_count(tmp_path: Path) -> None:
    archives = _canonical_archives(tmp_path)
    _write_website_config(
        tmp_path,
        archives,
        expected_member_count=3,
        expected_duplicate_content_count=2,
    )

    result = _invoke_preserve(tmp_path, archives)

    assert result.exit_code == 1
    assert "expected 2 duplicate content records, observed 1" in result.output
    assert not (tmp_path / "sources/first_party/chicagohealthmap/snapshots/2026-07-13").exists()
