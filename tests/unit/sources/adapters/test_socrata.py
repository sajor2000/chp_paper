from __future__ import annotations

import json
from pathlib import Path

import pytest

from chicagohealthmap.sources.adapters.socrata import (
    PAGE_LIMIT,
    SocrataAdapter,
    SocrataResponseError,
    _validate_row_fields,
    parse_socrata_metadata,
    request_manifest_hash,
    verify_frozen_socrata_snapshot,
)
from chicagohealthmap.sources.registry import RequestSpec, load_registry


ROOT = Path(__file__).parents[4]


def _source(source_id: str):
    return load_registry(ROOT / "config/source_registry.yml").by_id[source_id]


def test_plan_uses_metadata_first_count_and_stable_primary_key_paging() -> None:
    source = _source("chicago_community_areas_current")

    plan = SocrataAdapter().plan(source)

    assert str(plan.url) == "https://data.cityofchicago.org/api/views/igwz-8jzy"
    assert plan.transport == "socrata"
    assert plan.required_environment_variables == ()
    assert plan.destination_paths == (
        "original/metadata/socrata_view.json",
        "original/count/count.json",
        "original/pages/",
        "requests/request_manifest.json",
    )
    first = dict(SocrataAdapter.page_parameters(source, offset=0))
    second = dict(SocrataAdapter.page_parameters(source, offset=PAGE_LIMIT))
    assert first["$limit"] == second["$limit"] == "50000"
    assert first["$offset"] == "0"
    assert second["$offset"] == "50000"
    assert first["$order"] == second["$order"] == "area_numbe ASC"
    assert dict(SocrataAdapter.count_parameters(source))["$select"] == "count(*) AS count"


def test_registry_limits_socrata_sources_to_approved_columns_filters_and_datasets() -> None:
    places = _source("cdc_places_current_tract")
    chicago = _source("chicago_community_areas_current")

    assert places.catalog_id == "yjkw-uj5s"
    assert dict(places.request.parameters) == {
        "$limit": "50000",
        "$order": "tractfips ASC",
        "$select": (
            "stateabbr,statedesc,countyname,countyfips,tractfips,totalpopulation,"
            "totalpop18plus,bphigh_crudeprev,bphigh_crude95ci,diabetes_crudeprev,"
            "diabetes_crude95ci,copd_crudeprev,copd_crude95ci"
        ),
        "$where": "stateabbr='IL' AND countyfips='17031'",
    }
    assert "model-based" in places.analytical_purpose
    assert "not observed ehr prevalence" in places.analytical_purpose.casefold()
    assert chicago.catalog_id == "igwz-8jzy"
    assert dict(chicago.request.parameters) == {
        "$limit": "50000",
        "$order": "area_numbe ASC",
        "$select": "the_geom,area_numbe,community,area_num_1,shape_area,shape_len",
    }


def test_request_manifest_hash_changes_for_any_registered_query_change() -> None:
    source = _source("cdc_places_current_tract")
    changed_parameters = dict(source.request.parameters)
    changed_parameters["$where"] = "stateabbr='IL'"
    changed_request = RequestSpec(
        method="GET", url=source.request.url, parameters=changed_parameters
    )
    changed = source.model_copy(update={"request": changed_request})

    assert request_manifest_hash(source) != request_manifest_hash(changed)


def test_metadata_parser_requires_exact_identity_schema_and_geometry() -> None:
    source = _source("chicago_community_areas_current")
    payload = json.loads((ROOT / "tests/fixtures/socrata/metadata.json").read_text())

    metadata = parse_socrata_metadata(payload, source)

    assert metadata.dataset_id == "igwz-8jzy"
    assert metadata.dataset_title == "Boundaries - Community Areas"
    assert metadata.department == "City of Chicago"
    assert metadata.license_name == "See Terms of Use"
    assert metadata.updated_at == 1745363197
    assert metadata.field_types["the_geom"] == "multipolygon"

    for field, replacement in (("id", "wrong-id"), ("name", "Wrong title")):
        bad = dict(payload)
        bad[field] = replacement
        with pytest.raises(SocrataResponseError, match="identity"):
            parse_socrata_metadata(bad, source)

    bad_schema = dict(payload)
    bad_schema["columns"] = payload["columns"][:-1]
    with pytest.raises(SocrataResponseError, match="schema"):
        parse_socrata_metadata(bad_schema, source)

    bad_geometry = json.loads(json.dumps(payload))
    bad_geometry["columns"][0]["dataTypeName"] = "text"
    with pytest.raises(SocrataResponseError, match="geometry"):
        parse_socrata_metadata(bad_geometry, source)

    malformed_column = json.loads(json.dumps(payload))
    malformed_column["columns"][0] = [1]
    with pytest.raises(SocrataResponseError, match="schema"):
        parse_socrata_metadata(malformed_column, source)

    drifted_type = json.loads(json.dumps(payload))
    drifted_type["columns"][1]["dataTypeName"] = "text"
    with pytest.raises(SocrataResponseError, match="schema"):
        parse_socrata_metadata(drifted_type, source)


@pytest.mark.parametrize(
    "source_id",
    [
        "chicago_health_atlas_life_expectancy",
        "cdc_svi_2022_tract",
        "hrsa_health_centers_current",
    ],
)
def test_adapter_refuses_every_non_registered_socrata_source(source_id: str) -> None:
    with pytest.raises(ValueError, match="approved Socrata"):
        SocrataAdapter().plan(_source(source_id))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(unexpected="field"),
        lambda row: row.pop("countyname"),
        lambda row: row.update(countyfips="17043"),
        lambda row: row.update(tractfips="1703101010"),
        lambda row: row.update(bphigh_crudeprev="NaN"),
    ],
)
def test_places_rows_reject_field_geography_geoid_and_measure_drift(mutation) -> None:
    source = _source("cdc_places_current_tract")
    row = {
        "stateabbr": "IL",
        "statedesc": "Illinois",
        "countyname": "Cook",
        "countyfips": "17031",
        "tractfips": "17031010100",
        "totalpopulation": "1000",
        "totalpop18plus": "800",
        "bphigh_crudeprev": "30.1",
        "bphigh_crude95ci": "(28,32)",
        "diabetes_crudeprev": "10.2",
        "diabetes_crude95ci": "(9,11)",
        "copd_crudeprev": "6.3",
        "copd_crude95ci": "(5,7)",
    }
    mutation(row)

    with pytest.raises(SocrataResponseError):
        _validate_row_fields(row, source, geojson=False)


@pytest.mark.parametrize(
    ("source_id", "expected_files", "expected_rows"),
    [
        ("cdc_places_current_tract", 3, 3258),
        ("chicago_community_areas_current", 2, 77),
    ],
)
def test_inherited_socrata_snapshots_match_global_hashes_and_semantics(
    source_id: str, expected_files: int, expected_rows: int
) -> None:
    result = verify_frozen_socrata_snapshot(ROOT, _source(source_id))

    assert result.snapshot_date == "2026-07-13"
    assert result.file_count == expected_files
    assert result.row_count == expected_rows
