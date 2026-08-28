from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from chicagohealthmap.sources.adapters.catalog import (
    CatalogResponseError,
    frozen_catalog_snapshot,
    verify_frozen_catalog_snapshot,
)
from chicagohealthmap.sources.registry import load_registry


ROOT = Path(__file__).parents[3]


@pytest.mark.parametrize(
    "source_id,exact_files",
    [
        ("chicago_health_atlas_life_expectancy", 131),
        ("chicago_health_atlas_mortality", 131),
        ("cdc_svi_2022_tract", 5),
        ("hrsa_health_centers_current", 3),
    ],
)
def test_frozen_catalog_snapshots_are_hash_and_semantic_verified(
    source_id: str, exact_files: int
) -> None:
    source = load_registry(ROOT / "config/source_registry.yml").by_id[source_id]
    report = verify_frozen_catalog_snapshot(ROOT, source, "2026-07-13")
    assert report.file_count == exact_files
    assert report.snapshot_date == "2026-07-13"
    assert report.legacy_layout is True


def test_frozen_verifier_rejects_date_drift() -> None:
    source = load_registry(ROOT / "config/source_registry.yml").by_id["cdc_svi_2022_tract"]
    with pytest.raises(CatalogResponseError, match="2026-07-13"):
        verify_frozen_catalog_snapshot(ROOT, source, "2026-07-14")


def test_legacy_path_is_inside_public_root() -> None:
    source = load_registry(ROOT / "config/source_registry.yml").by_id["hrsa_health_centers_current"]
    path = frozen_catalog_snapshot(ROOT, source, "2026-07-13")
    assert path.relative_to(ROOT / "sources/public")
    assert not path.is_symlink()


@pytest.mark.parametrize("mutation", ["extra", "missing"])
def test_frozen_contract_rejects_exact_inventory_drift(tmp_path: Path, mutation: str) -> None:
    source = load_registry(ROOT / "config/source_registry.yml").by_id["cdc_svi_2022_tract"]
    destination = tmp_path / "sources/public/cdc_atsdr_svi/snapshots/2026-07-13"
    destination.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "sources/public/cdc_atsdr_svi/snapshots/2026-07-13", destination)
    shutil.copy2(ROOT / "sources/public/CHECKSUMS.sha256", tmp_path / "sources/public")
    if mutation == "extra":
        (destination / "unexpected.txt").write_text("unexpected")
    else:
        (destination / "original/2022/metadata/source_page.html").unlink()
    with pytest.raises(CatalogResponseError, match="inventory"):
        verify_frozen_catalog_snapshot(tmp_path, source)


@pytest.mark.parametrize("component", ["public", "family", "snapshot", "checksums"])
def test_frozen_contract_rejects_symlinked_or_broken_components_before_read(
    tmp_path: Path, component: str
) -> None:
    source = load_registry(ROOT / "config/source_registry.yml").by_id["cdc_svi_2022_tract"]
    (tmp_path / "sources").mkdir()
    public = tmp_path / "sources/public"
    if component == "public":
        public.symlink_to(tmp_path / "missing-public", target_is_directory=True)
    else:
        public.mkdir()
        family = public / "cdc_atsdr_svi"
        if component == "family":
            family.symlink_to(tmp_path / "missing-family", target_is_directory=True)
        else:
            (family / "snapshots").mkdir(parents=True)
            snapshot = family / "snapshots/2026-07-13"
            if component == "snapshot":
                snapshot.symlink_to(tmp_path / "missing-snapshot", target_is_directory=True)
            else:
                snapshot.mkdir()
            if component == "checksums":
                (public / "CHECKSUMS.sha256").symlink_to(tmp_path / "external-secret")
    with pytest.raises(CatalogResponseError, match="unsafe"):
        verify_frozen_catalog_snapshot(tmp_path, source)
