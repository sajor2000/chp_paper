"""Immutable raw snapshot writing with verified integrity metadata."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path, PureWindowsPath
from types import TracebackType
from collections.abc import Iterable
from uuid import uuid4

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.sources.models import (
    SnapshotFile,
    SnapshotManifest,
    SnapshotAcquisition,
    SourceSpec,
    ValidationStatus,
)

HASH_CHUNK_SIZE = 1024 * 1024
_SOURCE_ID = re.compile(r"^[a-z0-9_]+$")


class SnapshotError(RuntimeError):
    """Base class for snapshot persistence failures."""


class SnapshotExistsError(SnapshotError):
    """Raised when a finalized snapshot already exists for a date."""


class CopyVerificationError(SnapshotError):
    """Raised when a copied file does not match its source hash."""


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of ``path`` using bounded-memory reads."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_staging_tree(root: Path) -> None:
    directories = [path for path in root.rglob("*") if path.is_dir()]
    for directory in sorted(directories, key=lambda path: len(path.parts), reverse=True):
        _fsync_directory(directory)
    _fsync_directory(root)


def _write_bytes_fsync(path: Path, content: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_directory(path.parent)


def copy_verified(source: Path, destination: Path) -> str:
    """Copy one file, fsync it, and reject a source/destination hash mismatch."""
    source = Path(source)
    destination = Path(destination)
    try:
        aliases_source = destination.samefile(source)
    except FileNotFoundError:
        aliases_source = False
    if aliases_source:
        raise CopyVerificationError("source and destination refer to the same file")

    destination.parent.mkdir(parents=True, exist_ok=True)
    created_destination = False
    try:
        with source.open("rb") as source_handle, destination.open("xb") as destination_handle:
            created_destination = True
            shutil.copyfileobj(source_handle, destination_handle, length=HASH_CHUNK_SIZE)
            destination_handle.flush()
            os.fsync(destination_handle.fileno())
        source_hash = sha256_file(source)
        destination_hash = sha256_file(destination)
        if source_hash != destination_hash:
            raise CopyVerificationError(
                f"copy hash mismatch for {source.name!r}: {source_hash} != {destination_hash}"
            )
        _fsync_directory(destination.parent)
        return destination_hash
    except BaseException:
        if created_destination:
            destination.unlink(missing_ok=True)
            _fsync_directory(destination.parent)
        raise


def _relative_snapshot_path(value: str) -> Path:
    if any(character in value for character in ("\r", "\n", "\0")):
        raise ValueError("snapshot file path must be checksum-safe and contain no CR, LF, or NUL")
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
        raise ValueError("snapshot file path must be repository-relative")
    return path


def _publish_no_replace(source: Path, destination: Path) -> None:
    """Atomically rename a directory without replacing ``destination``.

    Darwin and Linux expose native exclusive-rename operations. Other platforms fail closed
    rather than falling back to a check-then-rename sequence that could clobber a racing writer.
    """
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        rename = library.renameatx_np
        rename.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename.restype = ctypes.c_int
        result = rename(-2, os.fsencode(source), -2, os.fsencode(destination), 0x00000004)
    elif sys.platform.startswith("linux"):
        try:
            rename = library.renameat2
        except AttributeError as error:
            raise SnapshotError(
                "atomic no-replace publication is unavailable on this Linux libc"
            ) from error
        rename.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename.restype = ctypes.c_int
        result = rename(-100, os.fsencode(source), -100, os.fsencode(destination), 0x00000001)
    else:
        raise SnapshotError(
            f"atomic no-replace publication is unsupported on platform {sys.platform!r}"
        )

    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), destination)


class SnapshotWriter:
    """Stage and atomically finalize one immutable source snapshot."""

    def __init__(
        self,
        paths: Path | ProjectPaths,
        source: str | SourceSpec,
        snapshot_date: str | date,
    ) -> None:
        if isinstance(source, SourceSpec):
            self.source_id = source.source_id
            snapshot_subdir = source.snapshot_subdir
        else:
            if not _SOURCE_ID.fullmatch(source):
                raise ValueError(
                    "source must contain only lowercase letters, digits, and underscores"
                )
            self.source_id = source
            snapshot_subdir = source

        parsed_date = (
            date.fromisoformat(snapshot_date) if isinstance(snapshot_date, str) else snapshot_date
        )
        if isinstance(snapshot_date, str) and snapshot_date != parsed_date.isoformat():
            raise ValueError("snapshot_date must use ISO YYYY-MM-DD format")
        self.snapshot_date = parsed_date

        sources_root = paths.sources if isinstance(paths, ProjectPaths) else Path(paths)
        self.source_root = sources_root / snapshot_subdir
        self.snapshots_root = self.source_root / "snapshots"
        self.final_path = self.snapshots_root / parsed_date.isoformat()
        if self.final_path.exists():
            raise SnapshotExistsError(f"snapshot already finalized: {self.final_path}")

        self.staging_root = self.source_root / ".staging"
        self.staging_root.mkdir(parents=True, exist_ok=True)
        self.snapshots_root.mkdir(parents=True, exist_ok=True)
        self.staging_path = self.staging_root / str(uuid4())
        self.staging_path.mkdir()
        try:
            _fsync_directory(self.staging_root)
            _fsync_directory(self.source_root)
            self._started_at = datetime.now(timezone.utc)
            self._files: dict[str, SnapshotFile] = {}
            self._acquisitions: dict[str, SnapshotAcquisition] = {}
            self._finalized = False
        except BaseException:
            shutil.rmtree(self.staging_path)
            try:
                _fsync_directory(self.staging_root)
            except OSError:
                pass
            raise

    def __enter__(self) -> SnapshotWriter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not self._finalized:
            self.cleanup()

    def _destination(self, relative_path: str) -> Path:
        if self._finalized or not self.staging_path.exists():
            raise SnapshotError("snapshot writer is no longer active")
        relative = _relative_snapshot_path(relative_path)
        destination = self.staging_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        return destination

    def _record_file(self, relative_path: str, destination: Path, sha256: str) -> SnapshotFile:
        record = SnapshotFile(
            path=relative_path,
            sha256=sha256,
            byte_count=destination.stat().st_size,
        )
        self._files[relative_path] = record
        return record

    def write_bytes(self, relative_path: str, content: bytes) -> SnapshotFile:
        """Write and fsync raw bytes in staging without overwriting another file."""
        destination = self._destination(relative_path)
        try:
            _write_bytes_fsync(destination, content)
            return self._record_file(relative_path, destination, sha256_file(destination))
        except BaseException:
            self.cleanup()
            raise

    def write_chunks(self, relative_path: str, chunks: Iterable[bytes]) -> SnapshotFile:
        """Stream chunks into staging with a bounded-memory hash and no overwrite."""
        destination = self._destination(relative_path)
        digest = hashlib.sha256()
        created_destination = False
        try:
            with destination.open("xb") as handle:
                created_destination = True
                for chunk in chunks:
                    handle.write(chunk)
                    digest.update(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            _fsync_directory(destination.parent)
            return self._record_file(relative_path, destination, digest.hexdigest())
        except BaseException:
            if created_destination:
                destination.unlink(missing_ok=True)
                _fsync_directory(destination.parent)
            self._files.pop(relative_path, None)
            raise

    def annotate_file(
        self,
        relative_path: str,
        *,
        row_count: int | None = None,
        page_count: int | None = None,
    ) -> SnapshotFile:
        """Attach validated logical counts to a staged file record."""
        if self._finalized or relative_path not in self._files:
            raise SnapshotError("snapshot file is not available for annotation")
        record = self._files[relative_path].model_copy(
            update={"row_count": row_count, "page_count": page_count}
        )
        self._files[relative_path] = record
        return record

    def copy_file(self, source: Path, relative_path: str) -> SnapshotFile:
        """Copy a source file into staging and record its verified digest."""
        destination = self._destination(relative_path)
        try:
            digest = copy_verified(source, destination)
            return self._record_file(relative_path, destination, digest)
        except BaseException:
            self.cleanup()
            raise

    def record_acquisition(self, acquisition: SnapshotAcquisition) -> None:
        """Add immutable credential-free request provenance to the final manifest."""
        if self._finalized or not self.staging_path.exists():
            raise SnapshotError("snapshot writer is no longer active")
        validated = SnapshotAcquisition.model_validate(acquisition.model_dump(mode="json"))
        if validated.group in self._acquisitions:
            raise SnapshotError("snapshot acquisition group is already recorded")
        self._acquisitions[validated.group] = validated

    def finalize(self) -> SnapshotManifest:
        """Persist integrity metadata and atomically publish the staged snapshot."""
        if self._finalized or not self.staging_path.exists():
            raise SnapshotError("snapshot writer is no longer active")
        if not self._files:
            self.cleanup()
            raise SnapshotError("cannot finalize an empty snapshot")
        if self.final_path.exists():
            self.cleanup()
            raise SnapshotExistsError(f"snapshot already finalized: {self.final_path}")

        files = tuple(self._files[path] for path in sorted(self._files))
        completed_at = datetime.now(timezone.utc)
        manifest = SnapshotManifest(
            source_id=self.source_id,
            snapshot_id=f"{self.source_id}_{self.snapshot_date.isoformat()}",
            snapshot_date=self.snapshot_date,
            retrieval_started_at=self._started_at,
            retrieval_completed_at=completed_at,
            files=files,
            acquisitions=tuple(self._acquisitions[group] for group in sorted(self._acquisitions)),
            validation_status=ValidationStatus.passed,
        )
        manifest_bytes = (
            json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
        ).encode()
        checksums = "".join(f"{item.sha256}  {item.path}\n" for item in files).encode()

        try:
            _write_bytes_fsync(self.staging_path / "manifest.json", manifest_bytes)
            _write_bytes_fsync(self.staging_path / "checksums.sha256", checksums)
            _fsync_staging_tree(self.staging_path)
            if self.final_path.exists():
                raise SnapshotExistsError(f"snapshot already finalized: {self.final_path}")
            _publish_no_replace(self.staging_path, self.final_path)
            _fsync_directory(self.snapshots_root)
            _fsync_directory(self.source_root)
        except FileExistsError as error:
            self.cleanup()
            raise SnapshotExistsError(f"snapshot already finalized: {self.final_path}") from error
        except BaseException:
            self.cleanup()
            raise

        self._finalized = True
        return manifest

    def cleanup(self) -> None:
        """Remove this writer's unfinished UUID staging directory."""
        if self.staging_path.exists():
            shutil.rmtree(self.staging_path)
            _fsync_directory(self.staging_root)
