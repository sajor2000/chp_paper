from __future__ import annotations

import io
import json
import warnings
import zipfile
from pathlib import Path

import pytest

from chicagohealthmap.sources.adapters.census import (
    ArchiveSafetyError,
    CensusAcsAdapter,
    CensusResponseError,
    CensusTigerAdapter,
    parse_acs_group_response,
    validate_tiger_archive,
)
from chicagohealthmap.sources.registry import load_registry


ROOT = Path(__file__).parents[4]


def _zip_bytes(*names: str) -> bytes:
    output = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(output, "w") as archive:
            for name in names:
                archive.writestr(name, b"fixture")
    return output.getvalue()


def test_acs_plan_has_exact_release_group_queries_and_no_key() -> None:
    source = load_registry(ROOT / "config" / "source_registry.yml").by_id["census_acs_2024_5y"]

    plan = CensusAcsAdapter(year=2024, groups=("B01001", "B17001")).plan(source)

    assert str(plan.url) == "https://api.census.gov/data/2024/acs/acs5"
    assert plan.parameters == (
        ("get", "NAME,group(B01001)"),
        ("for", "tract:*"),
        ("in", "state:17 county:031"),
        ("get", "NAME,group(B17001)"),
        ("for", "tract:*"),
        ("in", "state:17 county:031"),
    )
    assert plan.destination_paths == (
        "original/2024/acs5/groups/B01001.json",
        "original/2024/acs5/groups/B17001.json",
    )
    assert plan.required_environment_variables == ("CENSUS_API_KEY",)
    assert all(name != "key" for name, _ in plan.parameters)
    assert "fixture-secret-key" not in str(plan.model_dump(mode="json"))


def test_acs_parser_preserves_geoid_and_margin_of_error() -> None:
    payload = json.loads((ROOT / "tests/fixtures/census/acs_group_response.json").read_text())

    parsed = parse_acs_group_response(payload)

    assert parsed.header[2] == "B01001_001M"
    assert parsed.rows[0].geoid == "17031010100"
    assert parsed.rows[0].values["B01001_001M"] == "207"
    assert parsed.rows[1].geoid == "17031010200"


def test_acs_parser_rejects_duplicate_geoids() -> None:
    payload = json.loads((ROOT / "tests/fixtures/census/acs_group_response.json").read_text())
    payload.append(payload[1].copy())

    with pytest.raises(CensusResponseError, match="duplicate"):
        parse_acs_group_response(payload)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        [["NAME", "state", "county", "tract"]],
        [["NAME", "state", "county", "tract"], ["x", "17", "031"]],
        [["NAME", "state", "county", "tract"], ["x", "17", "032", "010100"]],
        [["NAME", "state", "county", "tract"], ["x", "017", "031", "010100"]],
        [["NAME", "state", "county", "tract"], ["x", "17", "31", "010100"]],
        [["NAME", "state", "county", "tract"], ["x", "17", "031", "10100"]],
    ],
)
def test_acs_parser_fails_closed_on_malformed_or_wrong_grain(payload: object) -> None:
    with pytest.raises(CensusResponseError):
        parse_acs_group_response(payload)


@pytest.mark.parametrize("year", [2019, 2020, 2023, 2024])
def test_tiger_plan_uses_exact_official_name_for_every_registered_year(year: int) -> None:
    source = load_registry(ROOT / "config" / "source_registry.yml").by_id[
        f"census_tiger_{year}_tract"
    ]

    plan = CensusTigerAdapter(year=year).plan(source)

    assert str(plan.url).endswith(f"/TIGER{year}/TRACT/tl_{year}_17_tract.zip")
    assert plan.destination_paths[0] == f"original/{year}/tract/tl_{year}_17_tract.zip"


@pytest.mark.parametrize(
    "members",
    [
        ("../escape.shp",),
        ("/absolute.shp",),
        ("safe/a.shp", "SAFE/A.SHP"),
        ("tl_2024_17_tract.shp", "tl_2024_17_tract.shp"),
    ],
)
def test_tiger_archive_rejects_traversal_absolute_and_duplicate_members(
    tmp_path: Path, members: tuple[str, ...]
) -> None:
    archive = tmp_path / "unsafe.zip"
    archive.write_bytes(_zip_bytes(*members))

    with pytest.raises(ArchiveSafetyError):
        validate_tiger_archive(archive)


def test_tiger_archive_rejects_symlinks_and_excessive_expansion(tmp_path: Path) -> None:
    symlink = tmp_path / "symlink.zip"
    with zipfile.ZipFile(symlink, "w") as archive:
        info = zipfile.ZipInfo("link.shp")
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        archive.writestr(info, "target")
    with pytest.raises(ArchiveSafetyError):
        validate_tiger_archive(symlink)

    bomb = tmp_path / "bomb.zip"
    with zipfile.ZipFile(bomb, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("large.dbf", b"0" * 2_000_000)
    with pytest.raises(ArchiveSafetyError):
        validate_tiger_archive(bomb, max_compression_ratio=10)


@pytest.mark.parametrize(
    "members",
    [
        (
            "one/tl_2024_17_tract.shp",
            "two/tl_2024_17_tract.shx",
            "one/tl_2024_17_tract.dbf",
            "one/tl_2024_17_tract.prj",
        ),
        (
            "tl_2024_17_tract.shp",
            "tl_2024_17_tract.shx",
            "tl_2024_17_tract.dbf",
            "other.prj",
        ),
        (
            "tl_2024_17_tract.shp",
            "tl_2024_17_tract.shx",
            "tl_2024_17_tract.dbf",
            "tl_2024_17_tract.prj",
            "other.shp",
        ),
        (
            "tl_2024_17_tract.shp",
            "tl_2024_17_tract.shx",
            "tl_2024_17_tract.dbf",
            "tl_2024_17_tract.prj",
            "tl_2024_17_tract.CPG",
            "TL_2024_17_TRACT.cpg",
        ),
    ],
)
def test_tiger_archive_requires_one_coherent_component_set(
    tmp_path: Path, members: tuple[str, ...]
) -> None:
    archive = tmp_path / "conflicting.zip"
    archive.write_bytes(_zip_bytes(*members))

    with pytest.raises(ArchiveSafetyError):
        validate_tiger_archive(archive, expected_stem="tl_2024_17_tract")
