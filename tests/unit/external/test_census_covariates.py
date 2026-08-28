from __future__ import annotations

import csv
import io
import zipfile

import pandas as pd
import pytest

from chicagohealthmap.external.census_covariates import (
    CensusCovariateError,
    assign_blocks_to_communities,
    build_block_weights,
    derive_community_covariates,
    read_pl_block_population,
    read_variance_replicates,
    standardize_acs_components,
    standardize_p12_block_counts,
    validate_community_covariates,
)


def _communities() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "community_area_id": ["01", "02"],
            "geometry_wkt": [
                "POLYGON ((-88 41, -87 41, -87 42, -88 42, -88 41))",
                "POLYGON ((-87 41, -86 41, -86 42, -87 42, -87 41))",
            ],
        }
    )


def test_assign_blocks_to_communities_uses_internal_points_one_to_one() -> None:
    blocks = pd.DataFrame(
        {
            "block_geoid": ["170310101001001", "170310101001002"],
            "tract_geoid": ["17031010100", "17031010100"],
            "internal_longitude": [-87.5, -86.5],
            "internal_latitude": [41.5, 41.5],
        }
    )

    result = assign_blocks_to_communities(blocks, _communities())

    assert result.to_dict("records") == [
        {
            "block_geoid": "170310101001001",
            "tract_geoid": "17031010100",
            "community_area_id": "01",
            "boundary_touch": False,
        },
        {
            "block_geoid": "170310101001002",
            "tract_geoid": "17031010100",
            "community_area_id": "02",
            "boundary_touch": False,
        },
    ]


def test_assign_blocks_to_communities_retains_unambiguous_boundary_touch() -> None:
    blocks = pd.DataFrame(
        {
            "block_geoid": ["170310101001001"],
            "tract_geoid": ["17031010100"],
            "internal_longitude": [-88.0],
            "internal_latitude": [41.5],
        }
    )

    result = assign_blocks_to_communities(blocks, _communities())

    assert result.loc[0, "community_area_id"] == "01"
    assert bool(result.loc[0, "boundary_touch"])


def test_assign_blocks_to_communities_rejects_unassigned_block() -> None:
    blocks = pd.DataFrame(
        {
            "block_geoid": ["170310101001001"],
            "tract_geoid": ["17031010100"],
            "internal_longitude": [-90.0],
            "internal_latitude": [41.5],
        }
    )

    with pytest.raises(CensusCovariateError, match="outside every community area"):
        assign_blocks_to_communities(blocks, _communities())


def test_assign_blocks_can_drop_outside_county_blocks_for_production_subset() -> None:
    blocks = pd.DataFrame(
        {
            "block_geoid": ["170310101001001", "170310101001002"],
            "tract_geoid": ["17031010100", "17031010100"],
            "internal_longitude": [-87.5, -90.0],
            "internal_latitude": [41.5, 41.5],
        }
    )

    assigned = assign_blocks_to_communities(blocks, _communities(), require_all=False)

    assert assigned["block_geoid"].tolist() == ["170310101001001"]


def test_assign_blocks_to_communities_rejects_duplicate_block_ids() -> None:
    blocks = pd.DataFrame(
        {
            "block_geoid": ["170310101001001", "170310101001001"],
            "tract_geoid": ["17031010100", "17031010100"],
            "internal_longitude": [-87.5, -87.4],
            "internal_latitude": [41.5, 41.6],
        }
    )

    with pytest.raises(CensusCovariateError, match="duplicate block GEOID"):
        assign_blocks_to_communities(blocks, _communities())


def test_build_block_weights_uses_population_within_tract_and_group() -> None:
    assignments = pd.DataFrame(
        {
            "block_geoid": ["170310101001001", "170310101001002", "170310102001001"],
            "tract_geoid": ["17031010100", "17031010100", "17031010200"],
            "community_area_id": ["01", "02", "02"],
            "boundary_touch": [False, False, False],
        }
    )
    counts = pd.DataFrame(
        {
            "block_geoid": [
                "170310101001001",
                "170310101001002",
                "170310101001001",
                "170310101001002",
                "170310102001001",
            ],
            "tract_geoid": [
                "17031010100",
                "17031010100",
                "17031010100",
                "17031010100",
                "17031010200",
            ],
            "allocation_group": ["male_18_19", "male_18_19", "female_18_19", "female_18_19", "male_18_19"],
            "ancillary_count": [30, 70, 80, 20, 10],
        }
    )

    result = build_block_weights(counts, assignments)

    observed = result.set_index(["tract_geoid", "allocation_group", "block_geoid"])[
        "weight"
    ].to_dict()
    assert observed[("17031010100", "male_18_19", "170310101001001")] == pytest.approx(0.3)
    assert observed[("17031010100", "male_18_19", "170310101001002")] == pytest.approx(0.7)
    assert observed[("17031010100", "female_18_19", "170310101001001")] == pytest.approx(0.8)
    assert observed[("17031010100", "female_18_19", "170310101001002")] == pytest.approx(0.2)
    assert observed[("17031010200", "male_18_19", "170310102001001")] == pytest.approx(1.0)
    assert result.groupby(["tract_geoid", "allocation_group"])["weight"].sum().eq(1).all()


def test_build_block_weights_rejects_zero_ancillary_population() -> None:
    assignments = pd.DataFrame(
        {
            "block_geoid": ["170310101001001", "170310101001002"],
            "tract_geoid": ["17031010100", "17031010100"],
            "community_area_id": ["01", "02"],
            "boundary_touch": [False, False],
        }
    )
    counts = pd.DataFrame(
        {
            "block_geoid": ["170310101001001", "170310101001002"],
            "tract_geoid": ["17031010100", "17031010100"],
            "allocation_group": ["male_18_19", "male_18_19"],
            "ancillary_count": [0, 0],
        }
    )

    with pytest.raises(CensusCovariateError, match="zero ancillary population"):
        build_block_weights(counts, assignments)


def test_build_block_weights_rejects_negative_or_unassigned_counts() -> None:
    assignments = pd.DataFrame(
        {
            "block_geoid": ["170310101001001"],
            "tract_geoid": ["17031010100"],
            "community_area_id": ["01"],
            "boundary_touch": [False],
        }
    )
    negative = pd.DataFrame(
        {
            "block_geoid": ["170310101001001"],
            "tract_geoid": ["17031010100"],
            "allocation_group": ["male_18_19"],
            "ancillary_count": [-1],
        }
    )
    with pytest.raises(CensusCovariateError, match="nonnegative"):
        build_block_weights(negative, assignments)

    unassigned = negative.assign(
        block_geoid="170310101001999", ancillary_count=1
    )
    with pytest.raises(CensusCovariateError, match="without a community assignment"):
        build_block_weights(unassigned, assignments)


def _component_fixture() -> tuple[pd.DataFrame, pd.DataFrame]:
    groups = {
        "total_population": ("all", 100.0, 0.4),
        "female_population": ("female", 60.0, 0.5),
        "age_65_plus_population": ("age65", 20.0, 0.25),
        "adult_population": ("adult", 80.0, 0.3),
        "poverty_numerator": ("poverty_num", 30.0, 0.2),
        "poverty_denominator": ("poverty_den", 90.0, 0.4),
    }
    components = pd.DataFrame(
        [
            {
                "tract_geoid": "17031010100",
                "component": component,
                "allocation_group": allocation_group,
                "estimate": estimate,
            }
            for component, (allocation_group, estimate, _) in groups.items()
        ]
    )
    weights = pd.DataFrame(
        [
            {
                "tract_geoid": "17031010100",
                "allocation_group": allocation_group,
                "block_geoid": f"17031010100{index:04d}",
                "community_area_id": community_id,
                "weight": weight,
                "boundary_touch": False,
                "ancillary_count": weight * 100,
            }
            for index, (_, (allocation_group, _, first_weight)) in enumerate(groups.items(), 1)
            for community_id, weight in (("01", first_weight), ("02", 1 - first_weight))
        ]
    )
    return components, weights


def test_derive_community_covariates_uses_allocated_count_ratios() -> None:
    components, weights = _component_fixture()

    result, diagnostics = derive_community_covariates(components, weights)
    result = result.set_index("community_area_id")

    assert result.loc["01", "total_population"] == pytest.approx(40.0)
    assert result.loc["01", "pct_female"] == pytest.approx(75.0)
    assert result.loc["01", "pct_age_65_plus"] == pytest.approx(12.5)
    assert result.loc["01", "pct_below_fpl"] == pytest.approx(100 * 6 / 36)
    assert result.loc["01", "acs_adult_population"] == pytest.approx(24.0)
    assert result.loc["02", "pct_female"] == pytest.approx(50.0)
    assert result.loc["02", "pct_age_65_plus"] == pytest.approx(25.0)
    assert result.loc["02", "pct_below_fpl"] == pytest.approx(100 * 24 / 54)
    assert result.loc["02", "acs_adult_population"] == pytest.approx(56.0)
    assert set(result["uncertainty_status"]) == {"unavailable_no_variance_replicates"}
    assert result.filter(like="_standard_error").isna().all().all()
    assert diagnostics["allocated_estimate"].sum() == pytest.approx(
        components["estimate"].sum()
    )


def test_derive_community_covariates_propagates_80_replicates() -> None:
    components, weights = _component_fixture()
    replicates = pd.DataFrame(
        [
            {
                **row._asdict(),
                "replicate_id": replicate,
                "replicate_estimate": row.estimate * (0.9 if replicate % 2 else 1.1),
            }
            for row in components.itertuples(index=False)
            for replicate in range(1, 81)
        ]
    ).drop(columns="estimate")

    result, _ = derive_community_covariates(components, weights, replicates)
    result = result.set_index("community_area_id")

    assert set(result["uncertainty_status"]) == {"available_variance_replicates"}
    assert result.loc["01", "pct_female_standard_error"] == pytest.approx(0.0, abs=1e-12)
    assert result.loc["01", "pct_age_65_plus_standard_error"] == pytest.approx(0.0, abs=1e-12)
    assert result.loc["01", "pct_below_fpl_standard_error"] == pytest.approx(0.0, abs=1e-12)
    assert result.loc["01", "acs_adult_population_standard_error"] == pytest.approx(4.8)
    assert result.loc["01", "acs_adult_population_moe90"] == pytest.approx(7.896)


def test_derive_community_covariates_requires_exactly_80_complete_replicates() -> None:
    components, weights = _component_fixture()
    incomplete = pd.DataFrame(
        [
            {
                **row._asdict(),
                "replicate_id": replicate,
                "replicate_estimate": row.estimate,
            }
            for row in components.itertuples(index=False)
            for replicate in range(1, 80)
        ]
    ).drop(columns="estimate")

    with pytest.raises(CensusCovariateError, match="exactly 80"):
        derive_community_covariates(components, weights, incomplete)


def test_validate_community_covariates_enforces_77_area_contract() -> None:
    frame = pd.DataFrame(
        {
            "community_area_id": [f"{index:02d}" for index in range(1, 78)],
            "total_population": [100.0] * 77,
            "pct_female": [50.0] * 77,
            "pct_age_65_plus": [15.0] * 77,
            "pct_below_fpl": [20.0] * 77,
            "acs_adult_population": [80.0] * 77,
        }
    )

    validate_community_covariates(frame)

    with pytest.raises(CensusCovariateError, match="exactly IDs 01 through 77"):
        validate_community_covariates(frame.iloc[:-1])
    with pytest.raises(CensusCovariateError, match="adult population exceeds total"):
        validate_community_covariates(frame.assign(acs_adult_population=101.0))


def test_standardize_acs_components_maps_b01001_leaf_cells() -> None:
    raw = pd.DataFrame(
        {
            "geography_id": ["17031010100"] * 6,
            "source_variable_id": [
                "B01001_E003",
                "B01001_E007",
                "B01001_E020",
                "B01001_E027",
                "B01001_E031",
                "B01001_E044",
            ],
            "estimate": [10, 20, 30, 40, 50, 60],
            "estimate_state": ["reported"] * 6,
        }
    )

    result = standardize_acs_components(raw)

    by_variable = {
        variable: set(group["component"])
        for variable, group in result.groupby("source_variable_id")
    }
    assert by_variable["B01001_E003"] == {"total_population"}
    assert by_variable["B01001_E007"] == {"total_population", "adult_population"}
    assert by_variable["B01001_E020"] == {
        "total_population",
        "adult_population",
        "age_65_plus_population",
    }
    assert by_variable["B01001_E027"] == {"total_population", "female_population"}
    assert by_variable["B01001_E031"] == {
        "total_population",
        "female_population",
        "adult_population",
    }
    assert by_variable["B01001_E044"] == {
        "total_population",
        "female_population",
        "adult_population",
        "age_65_plus_population",
    }
    assert set(result.loc[result["source_variable_id"].eq("B01001_E044"), "allocation_group"]) == {
        "p12_044"
    }


def test_standardize_acs_components_maps_poverty_leaves_to_exact_universe() -> None:
    raw = pd.DataFrame(
        {
            "geography_id": ["17031010100"] * 4,
            "source_variable_id": [
                "B17001_E004",
                "B17001_E018",
                "B17001_E033",
                "B17001_E047",
            ],
            "estimate": [5, 7, 20, 30],
            "estimate_state": ["reported"] * 4,
        }
    )

    result = standardize_acs_components(raw)

    below = result.loc[result["source_variable_id"].isin(["B17001_E004", "B17001_E018"])]
    above = result.loc[result["source_variable_id"].isin(["B17001_E033", "B17001_E047"])]
    assert set(below["component"]) == {"poverty_numerator", "poverty_denominator"}
    assert set(above["component"]) == {"poverty_denominator"}
    assert set(result.loc[result["source_variable_id"].str.contains("E004|E033"), "allocation_group"]) == {
        "p12_male_total"
    }
    assert set(result.loc[result["source_variable_id"].str.contains("E018|E047"), "allocation_group"]) == {
        "p12_female_total"
    }


def test_standardize_p12_block_counts_emits_leaf_and_sex_total_groups() -> None:
    raw = pd.DataFrame(
        {
            "block_geoid": ["170310101001001"],
            "tract_geoid": ["17031010100"],
            **{f"P12_{cell:03d}N": [cell] for cell in [*range(3, 26), *range(27, 50)]},
        }
    )

    result = standardize_p12_block_counts(raw)
    indexed = result.set_index("allocation_group")["ancillary_count"]

    assert indexed["p12_003"] == 3
    assert indexed["p12_049"] == 49
    assert indexed["p12_male_total"] == sum(range(3, 26))
    assert indexed["p12_female_total"] == sum(range(27, 50))
    assert len(result) == 48


def test_read_pl_block_population_joins_geo_and_segment_records(tmp_path) -> None:
    archive = tmp_path / "il2020.pl.zip"
    geo_rows = [
        ["PLST", "IL", "750", "00", "00", "000", "00", "0000001", "7500000US170310101001001"],
        ["PLST", "IL", "750", "00", "00", "000", "00", "0000002", "7500000US170430101001001"],
    ]
    segment_rows = [
        ["PLST", "IL", "000", "01", "0000001", "42"],
        ["PLST", "IL", "000", "01", "0000002", "99"],
    ]
    with zipfile.ZipFile(archive, "w") as output:
        for name, rows in (("ilgeo2020.pl", geo_rows), ("il000012020.pl", segment_rows)):
            buffer = io.StringIO()
            csv.writer(buffer, delimiter="|", lineterminator="\n").writerows(rows)
            output.writestr(name, buffer.getvalue())

    result = read_pl_block_population(archive)

    assert result.to_dict("records") == [
        {
            "block_geoid": "170310101001001",
            "tract_geoid": "17031010100",
            "ancillary_count": 42.0,
        }
    ]


def test_read_variance_replicates_preserves_all_80_cell_replicates(tmp_path) -> None:
    archive = tmp_path / "B01001_17.csv.zip"
    fields = [
        "TBLID",
        "GEOID",
        "NAME",
        "ORDER",
        "TITLE",
        "ESTIMATE",
        "MOE",
        "CME",
        "SE",
        *[f"Var_Rep{index}" for index in range(1, 81)],
    ]
    row = [
        "B01001",
        "1400000US17031010100",
        "Tract 101",
        "3",
        "Male under 5",
        "10",
        "2",
        "",
        "1.2",
        *[str(10 + index / 100) for index in range(1, 81)],
    ]
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(fields)
    writer.writerow(row)
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("140/B01001_17.csv", buffer.getvalue())

    point, replicates = read_variance_replicates(archive, "B01001")

    assert point.to_dict("records") == [
        {
            "geography_id": "17031010100",
            "source_variable_id": "B01001_E003",
            "estimate": 10.0,
            "estimate_state": "reported",
        }
    ]
    assert len(replicates) == 80
    assert set(replicates["replicate_id"]) == set(range(1, 81))
    assert replicates.iloc[-1]["replicate_estimate"] == pytest.approx(10.8)
