from __future__ import annotations

from pathlib import Path

import pytest

from chicagohealthmap.analysis.raw_data_contract import (
    FACT_COLUMNS,
    RawDataAudit,
    assert_primary_tract_contract,
    audit_first_party_snapshot,
    load_study_data_contract,
)


ROOT = Path(__file__).parents[3]


@pytest.fixture(scope="module")
def raw_audit() -> RawDataAudit:
    return audit_first_party_snapshot(ROOT)


def test_study_contract_names_all_67_database_fact_columns() -> None:
    contract = load_study_data_contract(ROOT)

    assert tuple(contract["condition_fact_columns"]) == FACT_COLUMNS
    assert len(FACT_COLUMNS) == 67
    assert FACT_COLUMNS[1:5] == (
        "geography_key",
        "dx_year",
        "condition_key",
        "total_count",
    )
    assert FACT_COLUMNS[24] == "denom_total_count"
    assert FACT_COLUMNS[44] == "prev_total_count"


def test_primary_tract_raw_data_contract_passes(raw_audit: RawDataAudit) -> None:
    tract = raw_audit.fact_audits[0]

    assert raw_audit.primary_tract_contract_passed is True
    assert tract.table == "fact_tract_condition_stats.text"
    assert tract.rows == 342273
    assert tract.conditions == 39
    assert tract.years == (2019, 2020, 2021, 2022, 2023, 2024)
    assert tract.duplicate_keys == 0
    assert tract.varying_denominator_geography_years == 0
    assert tract.published_measure_ratio_mismatch_rows == 0
    assert tract.positive_numerator_below_10_rows == 0


def test_higher_geography_estimands_remain_blocked(raw_audit: RawDataAudit) -> None:
    community = raw_audit.fact_audits[1]
    zcta = raw_audit.fact_audits[2]

    assert raw_audit.higher_geography_estimand_authorized is False
    assert community.varying_denominator_geography_years == 456
    assert community.published_measure_ratio_mismatch_rows == 1876
    assert community.positive_numerator_below_10_rows == 12
    assert zcta.varying_denominator_geography_years == 1765
    assert zcta.published_measure_ratio_mismatch_rows == 22008
    assert zcta.positive_numerator_below_10_rows == 2958


def test_geographies_and_chicago_rollup_are_internally_valid(raw_audit: RawDataAudit) -> None:
    assert raw_audit.chicago_rollup_exact_matches == raw_audit.chicago_rollup_rows == 234
    assert raw_audit.outside_six_county_tracts == 121
    assert raw_audit.outside_six_county_rows == 684
    assert raw_audit.outside_six_county_positive_numerator_rows == 0
    assert raw_audit.outside_six_county_positive_denominator_rows == 0
    assert all(item.duplicate_keys == 0 for item in raw_audit.geometry_audits)
    assert all(item.missing_geometry_rows == 0 for item in raw_audit.geometry_audits)
    assert all(item.invalid_geometry_rows == 0 for item in raw_audit.geometry_audits)


def test_assertion_wrapper_returns_verified_audit() -> None:
    audit = assert_primary_tract_contract(ROOT)

    assert audit.primary_tract_contract_passed is True
