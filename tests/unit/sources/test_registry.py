from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.sources.registry import (
    REQUIRED_SOURCE_IDS,
    SourceRegistry,
    export_acquisition_matrix_bytes,
    load_registry,
)


ROOT = Path(__file__).parents[3]
REGISTRY_PATH = ROOT / "config" / "source_registry.yml"
MATRIX_PATH = ROOT / "sources" / "public" / "_registry" / "acquisition_matrix.csv"

AUTHORITATIVE_DOMAINS = {
    "api.census.gov",
    "chicagohealthatlas.org",
    "data.cdc.gov",
    "data.cityofchicago.org",
    "data.hrsa.gov",
    "gisportal.hrsa.gov",
    "metop.io",
    "svi.cdc.gov",
    "www.atsdr.cdc.gov",
    "www.census.gov",
    "www2.census.gov",
}


@pytest.fixture(scope="module")
def registry() -> SourceRegistry:
    return load_registry(REGISTRY_PATH)


def test_registry_contains_exact_required_source_ids(registry: SourceRegistry) -> None:
    assert {source.source_id for source in registry.sources} == REQUIRED_SOURCE_IDS


def test_every_source_has_complete_acquisition_contract(registry: SourceRegistry) -> None:
    for source in registry.sources:
        assert source.organization
        assert source.dataset_title
        assert source.analytical_purpose
        assert source.transport
        assert source.official_domain
        assert source.landing_url
        assert source.documentation_url
        assert source.endpoint_url
        assert source.release
        assert source.years
        assert source.geography
        assert source.license
        assert source.access_date <= registry.registry_date
        assert source.citation
        assert source.citation_url
        assert source.expected_grain
        assert source.primary_key
        assert source.request.method == "GET"
        assert source.request.url == source.endpoint_url
        assert source.fallback.policy
        assert source.fallback.status
        assert source.verification.status in {"verified", "unverified", "drift_detected"}
        assert source.verification.evidence_urls


def test_urls_use_declared_authoritative_domains(registry: SourceRegistry) -> None:
    for source in registry.sources:
        assert source.official_domain in AUTHORITATIVE_DOMAINS
        for url in (
            source.landing_url,
            source.documentation_url,
            source.endpoint_url,
            source.citation_url,
            source.request.url,
            *(() if source.fallback.url is None else (source.fallback.url,)),
            *source.verification.evidence_urls,
        ):
            hostname = urlsplit(str(url)).hostname
            assert hostname in AUTHORITATIVE_DOMAINS, (source.source_id, url)


def test_service_sources_have_catalog_ids(registry: SourceRegistry) -> None:
    by_id = registry.by_id
    assert by_id["chicago_health_atlas_life_expectancy"].catalog_id == "VRLE"
    assert by_id["chicago_health_atlas_mortality"].catalog_id == "VRDTHR"
    assert by_id["cdc_places_current_tract"].catalog_id == "yjkw-uj5s"
    assert by_id["chicago_community_areas_current"].catalog_id == "igwz-8jzy"
    assert (
        by_id["hrsa_health_centers_current"].catalog_id
        == "PrimaryHealthCareFacilities_FS/MapServer/0"
    )


def test_registered_vintages_tables_and_methods_are_exact(registry: SourceRegistry) -> None:
    by_id = registry.by_id
    tables = {"B01001", "B03002", "B15003", "B17001", "B19013", "B23025", "B25044", "B27001"}
    for year in (2019, 2022, 2024):
        source = by_id[f"census_acs_{year}_5y"]
        assert source.years == (str(year),)
        assert set(source.request.parameters["tables"].split(",")) == tables
    for year in (2019, 2020, 2023, 2024):
        assert by_id[f"census_tiger_{year}_tract"].years == (str(year),)

    places = by_id["cdc_places_current_tract"]
    assert places.release == "2025 release; BRFSS model inputs 2023/2022; 2023 tract boundaries"
    assert places.request.parameters == {
        "$select": (
            "stateabbr,statedesc,countyname,countyfips,tractfips,totalpopulation,"
            "totalpop18plus,bphigh_crudeprev,bphigh_crude95ci,diabetes_crudeprev,"
            "diabetes_crude95ci,copd_crudeprev,copd_crude95ci"
        ),
        "$where": "stateabbr='IL' AND countyfips='17031'",
        "$order": "tractfips ASC",
        "$limit": "50000",
    }
    assert "model-based" in places.analytical_purpose.lower()

    svi = by_id["cdc_svi_2022_tract"]
    assert "MP_CROWD" in svi.verification.notes
    assert "2024-12-11" in svi.verification.notes


def test_health_atlas_indicators_are_not_conflated(registry: SourceRegistry) -> None:
    by_id = registry.by_id
    life = by_id["chicago_health_atlas_life_expectancy"]
    mortality = by_id["chicago_health_atlas_mortality"]
    assert life.catalog_id == "VRLE"
    assert life.years == tuple(str(year) for year in range(2010, 2025))
    assert life.geography == "77 Chicago community areas (API layer: neighborhood)"
    assert life.expected_grain == "community area × annual period × population stratum"
    assert "standard error may be null" in life.verification.notes
    assert mortality.catalog_id == "VRDTHR"
    assert mortality.years[-1] == "2020-2024"
    assert mortality.expected_grain == "community area × five-year period × population stratum"
    assert "standard error" in mortality.verification.notes


def test_no_unapproved_service_layers_are_registered(registry: SourceRegistry) -> None:
    serialized = "\n".join(
        f"{source.source_id} {source.dataset_title} {source.analytical_purpose}".lower()
        for source in registry.sources
    )
    for forbidden in ("police", "311", "pharmacy", "wic"):
        assert forbidden not in serialized


def test_duplicate_source_ids_are_rejected(registry: SourceRegistry) -> None:
    payload = registry.model_dump(mode="json")
    payload["sources"].append(payload["sources"][0])
    with pytest.raises(ValidationError, match="source_id values must be unique"):
        SourceRegistry.model_validate(payload)


def test_request_credentials_are_rejected(registry: SourceRegistry) -> None:
    payload = registry.model_dump(mode="json")
    payload["sources"][0]["request"]["parameters"]["api_key"] = "secret"
    with pytest.raises(ValidationError):
        SourceRegistry.model_validate(payload)


@pytest.mark.parametrize(
    "credential_name",
    (
        "api-key",
        "API_KEY",
        "auth.token",
        "client_secret",
        "session-cookie",
        "database_password",
        "oauth_authorization",
    ),
)
def test_request_credential_variants_are_rejected_and_redacted(
    registry: SourceRegistry, credential_name: str
) -> None:
    secret = "reviewer-secret-value-92741"
    payload = registry.model_dump(mode="json")
    payload["sources"][0]["request"]["parameters"][credential_name] = secret

    with pytest.raises(ValidationError) as captured:
        SourceRegistry.model_validate(payload)

    rendered = "\n".join(
        (
            str(captured.value),
            json.dumps(captured.value.errors(), default=str),
            captured.value.json(),
        )
    )
    assert secret not in rendered


@pytest.mark.parametrize(
    "malicious_url",
    (
        "https://alice:reviewer-secret-value-92741@chicagohealthatlas.org/",
        "https://chicagohealthatlas.org/?Client_Secret=reviewer-secret-value-92741",
        "https://chicagohealthatlas.org/%2e%2e/private",
        "https://chicagohealthatlas.org/safe%5c..%5cprivate",
        "https://chicagohealthatlas.org/%00private",
    ),
)
def test_all_registry_url_locations_reject_unsafe_values_without_leaking(
    registry: SourceRegistry, malicious_url: str
) -> None:
    secret = "reviewer-secret-value-92741"
    mutation_paths = (
        ("landing_url",),
        ("documentation_url",),
        ("endpoint_url",),
        ("citation_url",),
        ("request", "url"),
        ("fallback", "url"),
        ("verification", "evidence_urls"),
    )
    for mutation_path in mutation_paths:
        payload = registry.model_dump(mode="json")
        source = payload["sources"][0]
        if mutation_path == ("verification", "evidence_urls"):
            source["verification"]["evidence_urls"] = [malicious_url]
        elif len(mutation_path) == 1:
            source[mutation_path[0]] = malicious_url
            if mutation_path == ("endpoint_url",):
                source["request"]["url"] = malicious_url
        else:
            source[mutation_path[0]][mutation_path[1]] = malicious_url
            if mutation_path == ("request", "url"):
                source["endpoint_url"] = malicious_url

        with pytest.raises(ValidationError) as captured:
            SourceRegistry.model_validate(payload)
        rendered = "\n".join(
            (
                str(captured.value),
                json.dumps(captured.value.errors(), default=str),
                captured.value.json(),
            )
        )
        assert secret not in rendered


def test_source_identity_cannot_relabel_unofficial_domains(registry: SourceRegistry) -> None:
    payload = registry.model_dump(mode="json")
    source = payload["sources"][0]
    evil_url = "https://evil.example/data"
    source["official_domain"] = "evil.example"
    for field in ("landing_url", "documentation_url", "endpoint_url", "citation_url"):
        source[field] = evil_url
    source["request"]["url"] = evil_url
    source["fallback"]["url"] = evil_url
    source["verification"]["evidence_urls"] = [evil_url]

    with pytest.raises(ValidationError, match="authoritative domain"):
        SourceRegistry.model_validate(payload)


def test_unofficial_landing_url_is_rejected(registry: SourceRegistry) -> None:
    payload = registry.model_dump(mode="json")
    payload["sources"][0]["landing_url"] = "https://evil.example/official-looking-page"
    with pytest.raises(ValidationError, match="authoritative domain"):
        SourceRegistry.model_validate(payload)


def test_nested_registry_collections_are_deeply_immutable(registry: SourceRegistry) -> None:
    candidate = SourceRegistry.model_validate(registry.model_dump(mode="json"))
    with pytest.raises(TypeError):
        candidate.sources[0].request.parameters["api_key"] = "reviewer-secret-value-92741"
    with pytest.raises(AttributeError):
        candidate.sources[0].verification.evidence_urls.append("https://evil.example")


def test_model_copy_revalidates_nested_security_contracts(registry: SourceRegistry) -> None:
    request = registry.sources[0].request
    with pytest.raises(ValidationError):
        request.model_copy(update={"parameters": {"client-secret": "reviewer-secret-value-92741"}})

    source = registry.sources[0]
    with pytest.raises(ValidationError, match="authoritative domain"):
        source.model_copy(update={"landing_url": "https://evil.example"})


def test_matrix_ids_equal_yaml_ids_and_bytes_are_deterministic(registry: SourceRegistry) -> None:
    first = export_acquisition_matrix_bytes(registry)
    second = export_acquisition_matrix_bytes(registry)
    assert first == second == MATRIX_PATH.read_bytes()
    rows = list(csv.DictReader(io.StringIO(first.decode("utf-8"))))
    assert {row["source_id"] for row in rows} == REQUIRED_SOURCE_IDS
    assert [row["source_id"] for row in rows] == sorted(REQUIRED_SOURCE_IDS)


def test_sources_list_is_credential_free(registry: SourceRegistry) -> None:
    result = CliRunner().invoke(app, ["sources", "list"])
    assert result.exit_code == 0, result.output
    assert result.output.count("\n") == len(registry.sources)
    assert "chicago_health_atlas_life_expectancy" in result.output
    assert "verified" in result.output
    assert "token" not in result.output.casefold()
    assert "key=" not in result.output.casefold()


def test_sources_matrix_check_matches_tracked_bytes() -> None:
    result = CliRunner().invoke(app, ["sources", "matrix", "--check"])
    assert result.exit_code == 0, result.output
    assert "matches" in result.output.casefold()
