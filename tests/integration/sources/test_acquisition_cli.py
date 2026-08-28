from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.sources.snapshot import SnapshotWriter
from chicagohealthmap.sources.adapters.socrata import FrozenSocrataSnapshot
from chicagohealthmap.sources.adapters.catalog import FrozenCatalogReport


ROOT = Path(__file__).parents[3]


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "config").mkdir()
    (tmp_path / "sources" / "public" / "_registry").mkdir(parents=True)
    shutil.copy2(ROOT / "config" / "source_registry.yml", tmp_path / "config")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='fixture'\nversion='0'\n")
    monkeypatch.setenv("CHICAGOHEALTHMAP_ROOT", str(tmp_path))
    return tmp_path


def test_fetch_dry_run_is_deterministic_credential_free_and_writes_nothing(project: Path) -> None:
    runner = CliRunner()
    args = [
        "sources",
        "fetch",
        "--source",
        "census_tiger_2024_tract",
        "--snapshot-date",
        "2026-07-14",
        "--dry-run",
    ]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == second.exit_code == 0, first.output
    assert first.output == second.output
    assert "census_tiger_2024_tract" in first.output
    assert "tl_2024_17_tract.zip" in first.output
    assert "authorization" not in first.output.casefold()
    assert "cookie" not in first.output.casefold()
    assert "api_key" not in first.output.casefold()
    assert not list((project / "sources").glob("**/.staging/*"))
    assert not list((project / "sources").glob("**/snapshots/2026-07-14"))


def test_census_dry_run_uses_exact_adapter_contract_and_live_fetch_is_disabled(
    project: Path,
) -> None:
    runner = CliRunner()

    dry_run = runner.invoke(
        app,
        [
            "sources",
            "fetch",
            "--source",
            "census_acs_2024_5y",
            "--snapshot-date",
            "2026-07-14",
            "--dry-run",
        ],
    )
    live = runner.invoke(
        app,
        [
            "sources",
            "fetch",
            "--source",
            "census_tiger_2024_tract",
            "--snapshot-date",
            "2026-07-14",
        ],
    )

    assert dry_run.exit_code == 0, dry_run.output
    assert "https://api.census.gov/data/2024/acs/acs5" in dry_run.output
    assert "NAME,group(B01001)" in dry_run.output
    assert "state:17 county:031" in dry_run.output
    assert "CENSUS_API_KEY" in dry_run.output
    assert live.exit_code == 1
    assert live.output == (
        "Census live fetch is disabled; verify and reuse the frozen 2026-07-13 snapshot\n"
    )
    assert not list((project / "sources").glob("**/.staging/*"))


def test_socrata_dry_run_uses_adapter_and_non_dry_only_reuses_verified_frozen_snapshot(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def verified(root: Path, source) -> FrozenSocrataSnapshot:
        calls.append(source.source_id)
        return FrozenSocrataSnapshot(source.source_id, "2026-07-13", 2, 77)

    monkeypatch.setattr("chicagohealthmap.cli.verify_frozen_socrata_snapshot", verified)
    runner = CliRunner()
    dry_run = runner.invoke(
        app,
        [
            "sources",
            "fetch",
            "--source",
            "chicago_community_areas_current",
            "--snapshot-date",
            "2026-07-13",
            "--dry-run",
        ],
    )
    reuse = runner.invoke(
        app,
        [
            "sources",
            "fetch",
            "--source",
            "chicago_community_areas_current",
            "--snapshot-date",
            "2026-07-13",
        ],
    )

    assert dry_run.exit_code == 0, dry_run.output
    assert '"transport": "socrata"' in dry_run.output
    assert '"$limit", "50000"' in dry_run.output
    assert "area_numbe ASC" in dry_run.output
    assert "SOCRATA_APP_TOKEN" not in dry_run.output
    assert reuse.exit_code == 0, reuse.output
    assert reuse.output == (
        "Reused verified frozen chicago_community_areas_current snapshot 2026-07-13: "
        "2 file(s), 77 row(s); no live download performed\n"
    )
    assert calls == ["chicago_community_areas_current"]
    assert not list((project / "sources").glob("**/.staging/*"))


def test_catalog_dry_run_uses_adapter_and_non_dry_reuses_frozen_snapshot(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str]] = []

    def verified(root: Path, source, snapshot_date: str) -> FrozenCatalogReport:
        calls.append((source.source_id, snapshot_date))
        return FrozenCatalogReport(source.source_id, snapshot_date, 22, 1155)

    monkeypatch.setattr("chicagohealthmap.cli.verify_frozen_catalog_snapshot", verified)
    runner = CliRunner()
    dry_run = runner.invoke(
        app,
        [
            "sources",
            "fetch",
            "--source",
            "chicago_health_atlas_life_expectancy",
            "--snapshot-date",
            "2026-07-13",
            "--dry-run",
        ],
    )
    reuse = runner.invoke(
        app,
        [
            "sources",
            "fetch",
            "--source",
            "chicago_health_atlas_life_expectancy",
            "--snapshot-date",
            "2026-07-13",
        ],
    )

    assert dry_run.exit_code == 0, dry_run.output
    assert '"transport": "documented_export"' in dry_run.output
    assert "VRLE" in dry_run.output and "VRDTHR" not in dry_run.output
    assert reuse.exit_code == 0, reuse.output
    assert reuse.output == (
        "Reused verified frozen chicago_health_atlas_life_expectancy snapshot 2026-07-13: "
        "22 file(s), 1155 row(s); legacy layout retained; no live download performed\n"
    )
    assert calls == [("chicago_health_atlas_life_expectancy", "2026-07-13")]


def test_fetch_refuses_unknown_source_all_plus_source_and_bad_date(project: Path) -> None:
    runner = CliRunner()
    unknown = runner.invoke(
        app,
        ["sources", "fetch", "--source", "unknown", "--snapshot-date", "2026-07-14", "--dry-run"],
    )
    conflict = runner.invoke(
        app,
        [
            "sources",
            "fetch",
            "--all",
            "--source",
            "census_tiger_2024_tract",
            "--snapshot-date",
            "2026-07-14",
            "--dry-run",
        ],
    )
    bad_date = runner.invoke(
        app,
        [
            "sources",
            "fetch",
            "--source",
            "census_tiger_2024_tract",
            "--snapshot-date",
            "07/14/2026",
            "--dry-run",
        ],
    )

    assert unknown.exit_code != 0 and "unknown source" in unknown.output.casefold()
    assert conflict.exit_code != 0 and "exactly one" in conflict.output.casefold()
    assert bad_date.exit_code != 0 and "yyyy-mm-dd" in bad_date.output.casefold()


def test_fetch_all_refuses_any_invalid_registry_before_output(project: Path) -> None:
    registry = project / "config" / "source_registry.yml"
    registry.write_text(
        registry.read_text().replace(
            "https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_17_tract.zip",
            "https://evil.example/data.zip",
        )
    )

    result = CliRunner().invoke(
        app, ["sources", "fetch", "--all", "--snapshot-date", "2026-07-14", "--dry-run"]
    )

    assert result.exit_code != 0
    assert result.output == "Canonical source registry is missing or invalid\n"


def test_fetch_refuses_a_finalized_snapshot_date(project: Path) -> None:
    finalized = (
        project / "sources" / "public" / "census_tiger_2024_tract" / "snapshots" / "2026-07-14"
    )
    finalized.mkdir(parents=True)

    result = CliRunner().invoke(
        app,
        [
            "sources",
            "fetch",
            "--source",
            "census_tiger_2024_tract",
            "--snapshot-date",
            "2026-07-14",
            "--dry-run",
        ],
    )

    assert result.exit_code != 0
    assert "already finalized" in result.output.casefold()


def test_verify_all_checks_every_finalized_public_snapshot(project: Path) -> None:
    # No public snapshots is a valid deterministic inventory checkpoint.
    result = CliRunner().invoke(app, ["sources", "verify", "--all"])

    assert result.exit_code == 0, result.output
    assert result.output == "Verified public snapshots: 0\n"


def test_verify_rejects_conflicting_selectors_and_invalid_manifest(project: Path) -> None:
    runner = CliRunner()
    conflict = runner.invoke(
        app,
        ["sources", "verify", "--all", "--source", "census_tiger_2024_tract"],
    )
    snapshot = (
        project / "sources" / "public" / "census_tiger_2024_tract" / "snapshots" / "2026-07-14"
    )
    snapshot.mkdir(parents=True)
    (snapshot / "manifest.json").write_text(json.dumps({"secret": "must-not-print"}))
    invalid = runner.invoke(app, ["sources", "verify", "--source", "census_tiger_2024_tract"])

    assert conflict.exit_code != 0 and "exactly one" in conflict.output.casefold()
    assert invalid.exit_code != 0
    assert invalid.output == "Public snapshot verification failed\n"
    assert "must-not-print" not in invalid.output


def test_verify_rejects_a_snapshot_directory_symlink(project: Path, tmp_path: Path) -> None:
    source_id = "census_tiger_2024_tract"
    external = tmp_path / "external"
    writer = SnapshotWriter(external, source_id, "2026-07-14")
    writer.write_bytes("original/data.zip", b"not trusted through a symlink")
    writer.finalize()
    snapshots = project / "sources" / "public" / source_id / "snapshots"
    snapshots.mkdir(parents=True)
    (snapshots / "2026-07-14").symlink_to(
        external / source_id / "snapshots" / "2026-07-14", target_is_directory=True
    )

    result = CliRunner().invoke(app, ["sources", "verify", "--source", source_id])

    assert result.exit_code != 0
    assert result.output == "Public snapshot verification failed\n"


def test_verify_rejects_symlinked_snapshots_collection_without_reading_external_files(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_id = "census_tiger_2024_tract"
    external = tmp_path / "external-snapshots"
    (external / "2026-07-14").mkdir(parents=True)
    sentinel = external / "2026-07-14" / "manifest.json"
    sentinel.write_text("external sentinel must not be read")
    source_root = project / "sources" / "public" / source_id
    source_root.mkdir(parents=True)
    (source_root / "snapshots").symlink_to(external, target_is_directory=True)
    original_read_text = Path.read_text

    def reject_external_read(path: Path, *args: object, **kwargs: object) -> str:
        if path == sentinel:
            raise AssertionError("external sentinel was read")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", reject_external_read)
    result = CliRunner().invoke(app, ["sources", "verify", "--source", source_id])

    assert result.exit_code != 0
    assert result.output == "Public snapshot verification failed\n"


@pytest.mark.parametrize("broken_component", ["public", "source", "snapshots"])
def test_verify_rejects_broken_public_snapshot_path_symlinks(
    project: Path, tmp_path: Path, broken_component: str
) -> None:
    source_id = "census_tiger_2024_tract"
    public_root = project / "sources" / "public"
    source_root = public_root / source_id
    snapshots = source_root / "snapshots"
    broken_target = tmp_path / f"missing-{broken_component}"

    if broken_component == "public":
        shutil.rmtree(public_root)
        public_root.symlink_to(broken_target, target_is_directory=True)
    elif broken_component == "source":
        source_root.symlink_to(broken_target, target_is_directory=True)
    else:
        source_root.mkdir(parents=True)
        snapshots.symlink_to(broken_target, target_is_directory=True)

    result = CliRunner().invoke(app, ["sources", "verify", "--source", source_id])

    assert result.exit_code != 0
    assert result.output == "Public snapshot verification failed\n"
