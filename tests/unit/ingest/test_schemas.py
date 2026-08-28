from __future__ import annotations

from pathlib import Path

import pytest

from chicagohealthmap.ingest.schemas import (
    EvidenceStatus,
    SchemaContractError,
    load_schema_catalog,
    observed_field_counts,
    observed_table_shape,
)


ROOT = Path(__file__).parents[3]
CONFIG = ROOT / "config" / "first_party_schemas.yml"
SNAPSHOT = ROOT / "sources" / "first_party" / "capricorn" / "snapshots" / "2026-05-27" / "original"

EXPECTED_FILES = {
    "community_area_description_facts.text": (77, {20}),
    "dim_aldermanic.text": (50, {18}),
    "dim_census_tracts.text": (3265, {20}),
    "dim_community_area_reliability_crosswalk.text": (77, {7}),
    "dim_community_areas.text": (77, {17}),
    "dim_conditions.text": (39, {11}),
    "dim_congressional_districts.text": (17, {17}),
    "dim_tract_reliability_crosswalk.text": (3265, {7}),
    "dim_ward_reliability_crosswalk.text": (50, {7}),
    "dim_zcta.text": (400, {16}),
    "dim_zcta_reliability_crosswalk.text": (400, {7}),
    "drug_providers.text": (0, set()),
    "fact_chicago_condition_prevalence.text": (234, {7}),
    "fact_community_area_condition_stats.text": (17836, {67}),
    "fact_community_area_vulnerability.text": (77, {40}),
    "fact_congress_condition_stats.text": (3096, {67}),
    "fact_tract_condition_stats.text": (342273, {67}),
    "fact_ward_condition_stats.text": (11698, {67}),
    "fact_zcta_condition_stats.text": (66903, {67}),
    "svi_2020.text": (3263, {20}),
    "wic_locations.text": (0, set()),
}


def test_catalog_covers_all_exports_with_observed_shapes() -> None:
    catalog = load_schema_catalog(CONFIG)

    assert set(catalog.tables) == set(EXPECTED_FILES)
    for filename, (rows, counts) in EXPECTED_FILES.items():
        schema = catalog.tables[filename]
        assert schema.observed_rows == rows
        assert set(schema.observed_field_counts) == counts
        assert observed_table_shape(SNAPSHOT / filename) == (rows, counts)


def test_observed_table_shape_detects_row_drift(tmp_path: Path) -> None:
    source = tmp_path / "source.text"
    source.write_text("a|b\nc|d\n", encoding="utf-8")

    assert observed_table_shape(source) == (2, {2})

    source.write_text("a|b\n", encoding="utf-8")
    assert observed_table_shape(source) == (1, {2})


def test_nonempty_schemas_have_exact_ordered_field_contracts() -> None:
    catalog = load_schema_catalog(CONFIG)

    for filename, schema in catalog.tables.items():
        if schema.empty_expected:
            continue
        count = next(iter(EXPECTED_FILES[filename][1]))
        assert len(schema.fields) == count
        assert [field.position for field in schema.fields] == list(range(1, count + 1))
        assert [field.name for field in schema.fields] == [
            f"unverified_position_{position:02d}" for position in range(1, count + 1)
        ]
        for field in schema.fields:
            assert field.data_type == "string"
            assert field.nullable is True
            assert field.key_role == "none"
            assert field.unit == "source_text"
            assert field.evidence_source


def test_observed_empty_exports_are_explicitly_expected() -> None:
    catalog = load_schema_catalog(CONFIG)

    empty = {name for name, schema in catalog.tables.items() if schema.empty_expected}
    assert empty == {"drug_providers.text", "wic_locations.text"}
    for name in empty:
        assert catalog.tables[name].fields == ()


def test_unverified_fields_are_blocked_from_use() -> None:
    schema = load_schema_catalog(CONFIG).tables["fact_tract_condition_stats.text"]

    assert all(field.evidence_status is EvidenceStatus.unverified for field in schema.fields)
    assert schema.analysis_usable is False
    with pytest.raises(SchemaContractError, match="unverified_position_01"):
        schema.require_verified_fields(("unverified_position_01",))


def test_multiple_observed_field_counts_require_documented_exception(tmp_path: Path) -> None:
    source = tmp_path / "ragged.text"
    source.write_text("a|b\nc|d|e\n", encoding="utf-8")
    assert observed_field_counts(source) == {2, 3}

    payload = """
schema_version: 1
tables:
  ragged.text:
    observed_rows: 2
    observed_field_counts: [2, 3]
    empty_expected: false
    positional_contract:
      count: 3
      evidence_status: unverified
      evidence_source: observed positions only
"""
    config = tmp_path / "schemas.yml"
    config.write_text(payload, encoding="utf-8")
    with pytest.raises(SchemaContractError, match="validated exception"):
        load_schema_catalog(config)


def test_documented_field_count_exception_is_retained(tmp_path: Path) -> None:
    payload = """
schema_version: 1
tables:
  ragged.text:
    observed_rows: 2
    observed_field_counts: [2, 3]
    validated_field_count_exception: owner specification permits a trailing field
    empty_expected: false
    positional_contract:
      count: 3
      evidence_status: unverified
      evidence_source: observed positions only
"""
    config = tmp_path / "schemas.yml"
    config.write_text(payload, encoding="utf-8")
    schema = load_schema_catalog(config).tables["ragged.text"]
    assert schema.validated_field_count_exception.startswith("owner specification")


def test_data_dictionary_lists_every_table_and_unverified_position() -> None:
    catalog = load_schema_catalog(CONFIG)
    dictionary = (ROOT / "docs" / "analysis" / "data_dictionary.md").read_text(encoding="utf-8")

    for filename, schema in catalog.tables.items():
        assert f"`{filename}`" in dictionary
        for field in schema.fields:
            assert f"`{filename}:{field.name}`" in dictionary
    assert "Gate 3: CLOSED" in dictionary
    assert "website dictionary" in dictionary
    assert "guarded, defensible" in dictionary
    assert "position mappings" in dictionary
    assert "City of Chicago geographies" in dictionary
    assert "Adult-denominator reconstruction and subgroup" in dictionary
