import hashlib
import json
import os
from pathlib import Path

import pytest

import chicagohealthmap.sources.snapshot as snapshot_module
from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.sources.models import SourceSpec, Transport, ValidationStatus
from chicagohealthmap.sources.snapshot import (
    CopyVerificationError,
    SnapshotExistsError,
    SnapshotWriter,
    copy_verified,
    sha256_file,
)


def test_snapshot_finalization_is_immutable(tmp_path: Path) -> None:
    writer = SnapshotWriter(tmp_path, "example", "2026-07-13")
    writer.write_bytes("original/page-0001.json", b'{"value": 1}')
    manifest = writer.finalize()

    snapshot = tmp_path / "example" / "snapshots" / "2026-07-13"
    assert manifest.files[0].sha256 == sha256_file(snapshot / "original" / "page-0001.json")
    with pytest.raises(SnapshotExistsError):
        SnapshotWriter(tmp_path, "example", "2026-07-13")


def test_sha256_file_hashes_files_larger_than_one_chunk(tmp_path: Path) -> None:
    content = b"a" * (1024 * 1024) + b"tail"
    source = tmp_path / "large.bin"
    source.write_bytes(content)

    assert sha256_file(source) == hashlib.sha256(content).hexdigest()


def test_copy_verified_rejects_a_destination_hash_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.bin"
    destination = tmp_path / "destination.bin"
    source.write_bytes(b"source bytes")
    hashes = iter(("a" * 64, "b" * 64))
    hashed_paths: list[Path] = []

    def mismatched_hashes(path: Path) -> str:
        hashed_paths.append(path)
        return next(hashes)

    monkeypatch.setattr("chicagohealthmap.sources.snapshot.sha256_file", mismatched_hashes)

    with pytest.raises(CopyVerificationError, match="hash mismatch"):
        copy_verified(source, destination)

    assert hashed_paths == [source, destination]
    assert not destination.exists()


def test_copy_verified_rejects_identical_source_and_destination_without_deleting_it(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"preserve me")

    with pytest.raises(CopyVerificationError, match="same file"):
        copy_verified(source, source)

    assert source.read_bytes() == b"preserve me"


def test_copy_verified_rejects_hardlink_alias_without_deleting_either_path(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    destination = tmp_path / "alias.bin"
    source.write_bytes(b"preserve both names")
    try:
        os.link(source, destination)
    except OSError as error:
        pytest.skip(f"hard links unavailable: {error}")

    with pytest.raises(CopyVerificationError, match="same file"):
        copy_verified(source, destination)

    assert source.read_bytes() == b"preserve both names"
    assert destination.read_bytes() == b"preserve both names"


def test_copy_verified_preserves_a_preexisting_unrelated_destination(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    destination = tmp_path / "destination.bin"
    source.write_bytes(b"new data")
    destination.write_bytes(b"existing data")

    with pytest.raises(FileExistsError):
        copy_verified(source, destination)

    assert source.read_bytes() == b"new data"
    assert destination.read_bytes() == b"existing data"


def test_failed_write_removes_staging_and_never_finalizes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = SnapshotWriter(tmp_path, "example", "2026-07-13")
    original_open = Path.open

    def fail_snapshot_write(path: Path, *args: object, **kwargs: object):
        if path.name == "page.json":
            raise OSError("disk full")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_snapshot_write)

    with pytest.raises(OSError, match="disk full"):
        writer.write_bytes("original/page.json", b"payload")

    assert not (tmp_path / "example" / "snapshots" / "2026-07-13").exists()
    assert not writer.staging_path.exists()


def test_constructor_removes_uuid_staging_after_post_creation_fsync_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging_root = tmp_path / "example" / ".staging"
    original_fsync = snapshot_module._fsync_directory
    failed = False

    def fail_once(path: Path) -> None:
        nonlocal failed
        if path == staging_root and not failed:
            failed = True
            raise OSError("fsync failed")
        original_fsync(path)

    monkeypatch.setattr(snapshot_module, "_fsync_directory", fail_once)

    with pytest.raises(OSError, match="fsync failed"):
        SnapshotWriter(tmp_path, "example", "2026-07-13")

    assert staging_root.exists()
    assert list(staging_root.iterdir()) == []


def test_finalize_refuses_a_destination_created_during_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = SnapshotWriter(tmp_path, "example", "2026-07-13")
    writer.write_bytes("original/page.json", b"payload")
    original_publish = snapshot_module._publish_no_replace

    def create_collision(source: Path, destination: Path) -> None:
        destination.mkdir()
        original_publish(source, destination)

    monkeypatch.setattr(snapshot_module, "_publish_no_replace", create_collision)

    with pytest.raises(SnapshotExistsError):
        writer.finalize()

    assert writer.final_path.is_dir()
    assert list(writer.final_path.iterdir()) == []
    assert not writer.staging_path.exists()


@pytest.mark.parametrize(
    "unsafe_path", ["original/line\nbreak.json", "original/line\rbreak.json", "x\0y"]
)
def test_snapshot_paths_reject_checksum_control_characters_before_writing(
    tmp_path: Path, unsafe_path: str
) -> None:
    writer = SnapshotWriter(tmp_path, "example", "2026-07-13")

    with pytest.raises(ValueError, match="checksum-safe"):
        writer.write_bytes(unsafe_path, b"payload")

    assert list(writer.staging_path.iterdir()) == []


def test_finalize_writes_manifest_and_checksums_using_source_contracts(tmp_path: Path) -> None:
    spec = SourceSpec(
        source_id="example_source",
        organization="Example Agency",
        dataset_title="Example Data",
        transport=Transport.http_file,
        landing_url="https://example.org/data",
        documentation_url="https://example.org/docs",
        license="Public domain",
        snapshot_subdir="example/raw",
    )
    paths = ProjectPaths.from_root(tmp_path)
    source_file = tmp_path / "download.json"
    source_file.write_bytes(b'{"rows": [1, 2]}')
    writer = SnapshotWriter(paths, spec, "2026-07-13")
    writer.copy_file(source_file, "original/download.json")

    manifest = writer.finalize()

    snapshot = paths.sources / spec.snapshot_subdir / "snapshots" / "2026-07-13"
    persisted = json.loads((snapshot / "manifest.json").read_text())
    checksum = (snapshot / "checksums.sha256").read_text()
    assert manifest.source_id == spec.source_id
    assert manifest.validation_status is ValidationStatus.passed
    assert persisted == manifest.model_dump(mode="json")
    assert checksum == f"{manifest.files[0].sha256}  original/download.json\n"
    assert list((paths.sources / spec.snapshot_subdir / ".staging").iterdir()) == []
