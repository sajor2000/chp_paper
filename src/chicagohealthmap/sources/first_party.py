"""Inventory and immutable preservation of first-party Health Map exports."""

from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath

from chicagohealthmap.sources.models import SnapshotFile, SnapshotManifest, SourceSpec, Transport
from chicagohealthmap.sources.snapshot import SnapshotWriter, sha256_file

SOURCE_ID = "capricorn_chicagohealthmap_export_2026_05_27"
SNAPSHOT_SUBDIR = "first_party/capricorn"
EXPECTED_EMPTY_FILES = ("drug_providers.text", "wic_locations.text")

SOURCE_SPEC = SourceSpec.model_validate(
    {
        "source_id": SOURCE_ID,
        "organization": "CAPriCORN and CONSCIENCE Project",
        "dataset_title": "Chicago Health Map data exports",
        "transport": Transport.documented_export,
        "landing_url": "https://capricorncdrn.org/",
        "documentation_url": "https://capricorncdrn.org/",
        "license": "Redistribution terms not established; local preservation only",
        "snapshot_subdir": SNAPSHOT_SUBDIR,
    }
)

WEBSITE_SOURCE_SPEC = SourceSpec.model_validate(
    {
        "source_id": "chicagohealthmap_website_methods",
        "organization": "CONSCIENCE Project",
        "dataset_title": "Chicago Health Map website methods capture",
        "transport": Transport.documented_export,
        "landing_url": "https://chicagohealthmap.com/",
        "documentation_url": "https://chicagohealthmap.com/data-glossary",
        "license": "Local evidentiary preservation; website terms govern reuse",
        "snapshot_subdir": "first_party/chicagohealthmap",
    }
)


@dataclass(frozen=True, slots=True)
class FirstPartyInventory:
    """Observed state of an exact expected first-party export set."""

    expected_files: tuple[str, ...]
    files: tuple[SnapshotFile, ...]
    missing_files: tuple[str, ...]
    unexpected_files: tuple[str, ...]
    observed_empty_files: tuple[str, ...]
    methods_review_files: tuple[str, ...]

    @property
    def expected_count(self) -> int:
        return len(self.expected_files)

    @property
    def observed_count(self) -> int:
        return len(self.files)

    @property
    def zero_byte_files(self) -> tuple[str, ...]:
        return self.observed_empty_files


class FirstPartyValidationError(RuntimeError):
    """Raised when first-party exports cannot be safely preserved."""

    def __init__(self, message: str, inventory: FirstPartyInventory) -> None:
        super().__init__(message)
        self.inventory = inventory


class ArchiveSafetyError(RuntimeError):
    """Raised when an archive cannot be inspected or extracted without ambiguity."""


@dataclass(frozen=True, slots=True)
class WebsiteArchive:
    """Checksum metadata for an original website archive."""

    path: str
    sha256: str
    byte_count: int


@dataclass(frozen=True, slots=True)
class WebsiteArchiveMember:
    """Checksum metadata for one regular file stored in a website archive."""

    archive_sha256: str
    path: str
    sha256: str
    byte_count: int


@dataclass(frozen=True, slots=True)
class DuplicateWebsiteContent:
    """A later member whose bytes duplicate the canonical earlier member."""

    member_sha256: str
    canonical_archive_sha256: str
    canonical_member_path: str
    duplicate_archive_sha256: str
    duplicate_member_path: str


@dataclass(frozen=True, slots=True)
class WebsiteArchiveInspection:
    """Safe inventory of one archive and all of its regular file members."""

    archive: WebsiteArchive
    members: tuple[WebsiteArchiveMember, ...]


@dataclass(frozen=True, slots=True)
class WebsiteArchiveReport:
    """Combined archive inventory with content-level duplicate records."""

    archives: tuple[WebsiteArchive, ...]
    members: tuple[WebsiteArchiveMember, ...]
    duplicate_contents: tuple[DuplicateWebsiteContent, ...]


@dataclass(frozen=True, slots=True)
class WebsiteArchiveExpectation:
    """Configured identity of one canonical website archive."""

    filename: str
    sha256: str


@dataclass(frozen=True, slots=True)
class WebsiteArchiveSettings:
    """Configured identity and shape contract for the website methods snapshot."""

    source_id: str
    snapshot_date: date
    expected_archive_count: int
    expected_member_count: int
    expected_duplicate_content_count: int
    archives: tuple[WebsiteArchiveExpectation, ...]


def is_safe_member(member: zipfile.ZipInfo) -> bool:
    """Return whether a ZIP member has one unambiguous relative destination."""
    path = PurePosixPath(member.filename)
    windows_path = PureWindowsPath(member.filename)
    return (
        bool(member.filename)
        and "\0" not in member.filename
        and "\\" not in member.filename
        and not path.is_absolute()
        and not windows_path.is_absolute()
        and not windows_path.drive
        and ".." not in path.parts
        and not stat.S_ISLNK(member.external_attr >> 16)
    )


def inspect_zip(archive_path: Path) -> WebsiteArchiveInspection:
    """Reject unsafe ZIP layouts and hash every regular file without extracting it."""
    archive_path = Path(archive_path)
    archive_hash = sha256_file(archive_path)
    archive_record = WebsiteArchive(
        path=archive_path.name,
        sha256=archive_hash,
        byte_count=archive_path.stat().st_size,
    )
    members: list[WebsiteArchiveMember] = []
    destinations: set[str] = set()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            if not is_safe_member(member):
                raise ArchiveSafetyError(f"unsafe ZIP member: {member.filename!r}")
            destination = PurePosixPath(member.filename).as_posix()
            destination_key = destination.casefold()
            if destination_key in destinations:
                raise ArchiveSafetyError(f"duplicate ZIP member destination: {destination!r}")
            destinations.add(destination_key)
            if member.is_dir():
                continue
            content = archive.read(member)
            members.append(
                WebsiteArchiveMember(
                    archive_sha256=archive_hash,
                    path=destination,
                    sha256=hashlib.sha256(content).hexdigest(),
                    byte_count=len(content),
                )
            )
    return WebsiteArchiveInspection(archive=archive_record, members=tuple(members))


def extract_zip_verified(archive_path: Path, destination_root: Path) -> WebsiteArchiveInspection:
    """Safely extract one inspected archive without replacing different bytes."""
    inspection = inspect_zip(archive_path)
    destination_root = Path(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)
    resolved_root = destination_root.resolve()
    records = {record.path: record for record in inspection.members}
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            relative = PurePosixPath(member.filename)
            destination = destination_root.joinpath(*relative.parts)
            if not destination.resolve(strict=False).is_relative_to(resolved_root):
                raise ArchiveSafetyError(f"ZIP member escapes extraction root: {member.filename!r}")
            if any(
                parent.is_symlink() for parent in destination.parents if parent != resolved_root
            ):
                raise ArchiveSafetyError(f"ZIP member traverses a symlink: {member.filename!r}")
            content = archive.read(member)
            record = records[relative.as_posix()]
            if destination.exists() or destination.is_symlink():
                if destination.is_file() and not destination.is_symlink():
                    if sha256_file(destination) == record.sha256:
                        continue
                raise ArchiveSafetyError(
                    f"refusing to overwrite existing member with different bytes: {record.path!r}"
                )
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                with destination.open("xb") as handle:
                    handle.write(content)
            except FileExistsError as error:
                raise ArchiveSafetyError(
                    f"refusing to overwrite existing member with different bytes: {record.path!r}"
                ) from error
            if sha256_file(destination) != record.sha256:
                destination.unlink(missing_ok=True)
                raise ArchiveSafetyError(f"extracted member hash mismatch: {record.path!r}")
    return inspection


def inspect_website_archives(archive_paths: tuple[Path, ...]) -> WebsiteArchiveReport:
    """Inspect archives in order and report later members with duplicate content."""
    inspections = tuple(inspect_zip(path) for path in archive_paths)
    members = tuple(member for inspection in inspections for member in inspection.members)
    canonical_by_hash: dict[str, WebsiteArchiveMember] = {}
    duplicates: list[DuplicateWebsiteContent] = []
    for member in members:
        canonical = canonical_by_hash.setdefault(member.sha256, member)
        if canonical is member:
            continue
        duplicates.append(
            DuplicateWebsiteContent(
                member_sha256=member.sha256,
                canonical_archive_sha256=canonical.archive_sha256,
                canonical_member_path=canonical.path,
                duplicate_archive_sha256=member.archive_sha256,
                duplicate_member_path=member.path,
            )
        )
    return WebsiteArchiveReport(
        archives=tuple(inspection.archive for inspection in inspections),
        members=members,
        duplicate_contents=tuple(duplicates),
    )


def preserve_website_archives(
    archive_paths: tuple[Path, ...],
    sources_root: Path,
    snapshot_date: date,
    settings: WebsiteArchiveSettings,
) -> WebsiteArchiveReport:
    """Copy canonical archives, then inspect and extract only their staged bytes."""
    if settings.source_id != WEBSITE_SOURCE_SPEC.source_id:
        raise ArchiveSafetyError(
            f"configured website source must be {WEBSITE_SOURCE_SPEC.source_id!r}"
        )
    if settings.snapshot_date != snapshot_date:
        raise ArchiveSafetyError(
            f"snapshot date must match configuration {settings.snapshot_date.isoformat()}"
        )
    if settings.expected_archive_count != len(settings.archives):
        raise ArchiveSafetyError("configured archive count does not match archive identities")
    if len(archive_paths) != settings.expected_archive_count:
        raise ArchiveSafetyError(
            f"expected {settings.expected_archive_count} archives, observed {len(archive_paths)}"
        )

    observed_names = tuple(Path(path).name for path in archive_paths)
    expected_names = tuple(expected.filename for expected in settings.archives)
    if observed_names != expected_names:
        raise ArchiveSafetyError("archive filenames do not match configuration")
    if len(set(name.casefold() for name in observed_names)) != len(observed_names):
        raise ArchiveSafetyError("duplicate archive destination")
    for archive_path, expected in zip(archive_paths, settings.archives, strict=True):
        if sha256_file(Path(archive_path)) != expected.sha256:
            raise ArchiveSafetyError(
                f"archive SHA-256 does not match configuration: {expected.filename!r}"
            )

    with SnapshotWriter(sources_root, WEBSITE_SOURCE_SPEC, snapshot_date) as writer:
        staged_archives: list[Path] = []
        for archive_path, expected in zip(archive_paths, settings.archives, strict=True):
            copied = writer.copy_file(Path(archive_path), f"original/{Path(archive_path).name}")
            if copied.sha256 != expected.sha256:
                raise ArchiveSafetyError(
                    f"archive changed during preservation: {Path(archive_path).name!r}"
                )
            staged_archives.append(writer.staging_path / copied.path)

        report = inspect_website_archives(tuple(staged_archives))
        if len(report.members) != settings.expected_member_count:
            raise ArchiveSafetyError(
                f"expected {settings.expected_member_count} website members, "
                f"observed {len(report.members)}"
            )
        if len(report.duplicate_contents) != settings.expected_duplicate_content_count:
            raise ArchiveSafetyError(
                f"expected {settings.expected_duplicate_content_count} duplicate content "
                f"records, observed {len(report.duplicate_contents)}"
            )

        inventory = {
            "source_id": WEBSITE_SOURCE_SPEC.source_id,
            "snapshot_date": snapshot_date.isoformat(),
            "unsafe_members": [],
            "archives": [asdict(record) for record in report.archives],
            "members": [asdict(record) for record in report.members],
            "duplicate_contents": [asdict(record) for record in report.duplicate_contents],
        }
        inventory_bytes = (json.dumps(inventory, indent=2, sort_keys=True) + "\n").encode()
        members_by_archive = {
            archive.sha256: tuple(
                member for member in report.members if member.archive_sha256 == archive.sha256
            )
            for archive in report.archives
        }
        for staged_archive, archive_record in zip(staged_archives, report.archives, strict=True):
            if sha256_file(staged_archive) != archive_record.sha256:
                raise ArchiveSafetyError(
                    f"staged archive changed during preservation: {archive_record.path!r}"
                )
            with zipfile.ZipFile(staged_archive) as archive:
                for member in members_by_archive[archive_record.sha256]:
                    content = archive.read(member.path)
                    if (
                        len(content) != member.byte_count
                        or hashlib.sha256(content).hexdigest() != member.sha256
                    ):
                        raise ArchiveSafetyError(
                            f"staged archive member changed during preservation: {member.path!r}"
                        )
                    extracted = writer.write_bytes(f"extracted/{member.path}", content)
                    if extracted.sha256 != member.sha256:
                        raise ArchiveSafetyError(f"extracted member hash mismatch: {member.path!r}")
        writer.write_bytes("archive_inventory.json", inventory_bytes)
        writer.finalize()
    return report


def inventory_first_party(source_root: Path, expected: tuple[str, ...]) -> FirstPartyInventory:
    """Hash present expected exports and report missing, extra, and empty files."""
    source_root = Path(source_root)
    expected_set = frozenset(expected)
    observed_names = frozenset(path.name for path in source_root.glob("*.text") if path.is_file())
    missing = tuple(name for name in expected if name not in observed_names)
    unexpected = tuple(sorted(observed_names - expected_set))

    files = tuple(
        SnapshotFile(
            path=name,
            sha256=sha256_file(source_root / name),
            byte_count=(source_root / name).stat().st_size,
        )
        for name in expected
        if name in observed_names
    )
    observed_empty = tuple(file.path for file in files if file.byte_count == 0)
    methods_review = tuple(name for name in EXPECTED_EMPTY_FILES if name in observed_empty)
    return FirstPartyInventory(
        expected_files=expected,
        files=files,
        missing_files=missing,
        unexpected_files=unexpected,
        observed_empty_files=observed_empty,
        methods_review_files=methods_review,
    )


def preserve_first_party(
    source_root: Path,
    snapshot_root: Path,
    snapshot_date: date,
    expected: tuple[str, ...],
) -> SnapshotManifest:
    """Validate all expected exports, then copy and atomically publish them."""
    inventory = inventory_first_party(source_root, expected)
    if inventory.missing_files:
        missing = ", ".join(inventory.missing_files)
        raise FirstPartyValidationError(f"missing expected export(s): {missing}", inventory)

    expected_records = {record.path: record for record in inventory.files}
    with SnapshotWriter(snapshot_root, SOURCE_SPEC, snapshot_date) as writer:
        for name in expected:
            copied = writer.copy_file(Path(source_root) / name, f"original/{name}")
            if copied.sha256 != expected_records[name].sha256:
                raise FirstPartyValidationError(
                    f"source export changed during preservation: {name}", inventory
                )
        return writer.finalize()
