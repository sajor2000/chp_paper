from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "literature_queries.yml"
PROTOCOL_PATH = ROOT / "docs" / "methods" / "literature_search_protocol.md"

EXPECTED_QUERIES = {
    "ehr_public_health": '("Electronic Health Records"[MeSH] OR electronic health record*[Title/Abstract] OR EHR[Title/Abstract]) AND ("Public Health Surveillance"[MeSH] OR public health surveillance[Title/Abstract] OR population health surveillance[Title/Abstract])',
    "small_area_chronic_disease": '(neighborhood*[Title/Abstract] OR "small area"[Title/Abstract] OR census tract*[Title/Abstract] OR geospatial[Title/Abstract]) AND (chronic disease*[Title/Abstract] OR hypertension[Title/Abstract] OR diabetes[Title/Abstract] OR COPD[Title/Abstract]) AND (electronic health record*[Title/Abstract] OR health information exchange[Title/Abstract])',
    "urban_life_expectancy": '("Life Expectancy"[MeSH] OR life expectancy[Title/Abstract] OR premature mortality[Title/Abstract]) AND (Chicago[Title/Abstract] OR urban[Title/Abstract] OR neighborhood*[Title/Abstract]) AND (inequit*[Title/Abstract] OR disparit*[Title/Abstract] OR gap[Title/Abstract])',
    "clinical_network_surveillance": "(CAPriCORN[Title/Abstract] OR clinical data research network*[Title/Abstract] OR health information exchange*[Title/Abstract] OR PCORnet[Title/Abstract]) AND (surveillance[Title/Abstract] OR population health[Title/Abstract] OR public health[Title/Abstract])",
    "local_resource_planning": "(federally qualified health center*[Title/Abstract] OR FQHC[Title/Abstract] OR community-based organization*[Title/Abstract]) AND (geospatial[Title/Abstract] OR neighborhood data[Title/Abstract] OR resource allocation[Title/Abstract] OR service planning[Title/Abstract])",
    "candidate_conditions": "(hypertension[Title/Abstract] OR diabetes[Title/Abstract] OR chronic obstructive pulmonary disease[Title/Abstract] OR heart failure[Title/Abstract] OR stroke[Title/Abstract] OR substance use disorder*[Title/Abstract]) AND (life expectancy[Title/Abstract] OR premature mortality[Title/Abstract]) AND (neighborhood*[Title/Abstract] OR census tract*[Title/Abstract] OR small area[Title/Abstract])",
}

INITIAL_VERSION_FIELDS = {
    "version": 1,
    "status": "frozen",
    "frozen_on": "2026-07-14",
    "amendment_reason": "Initial prespecified query",
    "approval_status": "initial_prespecified_freeze",
    "approved_by": None,
    "screening_phase": "before_screening",
}
REQUIRED_VERSION_FIELDS = [
    "version",
    "query",
    "status",
    "frozen_on",
    "amendment_reason",
    "approved_by",
    "screening_phase",
]


def _validate_version_history(query: dict[str, object], required_fields: list[str]) -> None:
    versions = query["versions"]
    assert isinstance(versions, list)
    assert versions
    for version in versions:
        assert set(required_fields) <= set(version)
        assert type(version["version"]) is int
    numbers = [version["version"] for version in versions]
    assert numbers == list(range(1, len(versions) + 1))
    assert query["active_version"] in numbers

    for version in versions:
        assert isinstance(version["query"], str) and version["query"].strip()
        assert version["status"] == "frozen"
        assert isinstance(version["frozen_on"], str)
        date.fromisoformat(version["frozen_on"])
        assert isinstance(version["amendment_reason"], str)
        assert version["amendment_reason"].strip()
        assert version.get("screening_phase") in {
            "before_screening",
            "after_screening_started",
        }
        if version["version"] == 1:
            assert version.get("approval_status") == "initial_prespecified_freeze"
            assert version["approved_by"] is None
        else:
            assert isinstance(version["approved_by"], str)
            assert version["approved_by"].strip()


def _synthetic_version_history() -> dict[str, object]:
    return {
        "active_version": 2,
        "versions": [
            {
                "version": 1,
                "query": "original query",
                "status": "frozen",
                "frozen_on": "2026-07-14",
                "amendment_reason": "Initial prespecified query",
                "approval_status": "initial_prespecified_freeze",
                "approved_by": None,
                "screening_phase": "before_screening",
            },
            {
                "version": 2,
                "query": "amended query",
                "status": "frozen",
                "frozen_on": "2026-08-01",
                "amendment_reason": "Add a prespecified synonym",
                "approved_by": "Investigator approval record S6-001",
                "screening_phase": "after_screening_started",
            },
        ],
    }


def _load_config() -> dict[str, object]:
    return yaml.safe_load(CONFIG_PATH.read_text())


def test_initial_pubmed_queries_are_exact_and_versioned() -> None:
    config = _load_config()
    assert config["protocol_status"] == "executed_pending_investigator_review"
    queries = config["queries"]
    assert isinstance(queries, list)
    assert {query["id"] for query in queries} == set(EXPECTED_QUERIES)
    required_fields = config["amendment_policy"]["required_fields"]

    for query in queries:
        assert query["id"]
        assert query["purpose"]
        assert query["rationale"]
        assert query["planned_evidence_use"]
        assert query["concepts"]
        assert all(concept.strip() for concept in query["concepts"])
        _validate_version_history(query, required_fields)
        initial_version = query["versions"][0]
        assert initial_version["query"] == EXPECTED_QUERIES[query["id"]]
        for field, expected in INITIAL_VERSION_FIELDS.items():
            assert initial_version[field] == expected


def test_query_amendment_policy_is_append_only() -> None:
    config = _load_config()
    policy = config["amendment_policy"]
    assert policy["mode"] == "append_only"
    assert policy["replace_existing_versions"] is False
    assert policy["required_fields"] == REQUIRED_VERSION_FIELDS
    assert policy["nullable_exceptions"] == {
        "approved_by": {
            "version": 1,
            "approval_status": "initial_prespecified_freeze",
        }
    }


def test_version_history_accepts_a_valid_append_and_active_version() -> None:
    _validate_version_history(_synthetic_version_history(), REQUIRED_VERSION_FIELDS)


def test_version_history_rejects_invalid_appends_and_active_version() -> None:
    invalid_active = _synthetic_version_history()
    invalid_active["active_version"] = 3

    nonconsecutive = _synthetic_version_history()
    nonconsecutive["versions"][1]["version"] = 3

    missing_approver = _synthetic_version_history()
    missing_approver["versions"][1]["approved_by"] = None

    invalid_phase = _synthetic_version_history()
    invalid_phase["versions"][1]["screening_phase"] = "unknown"

    for query in (invalid_active, nonconsecutive, missing_approver, invalid_phase):
        with pytest.raises(AssertionError):
            _validate_version_history(query, REQUIRED_VERSION_FIELDS)


@pytest.mark.parametrize("missing_field", REQUIRED_VERSION_FIELDS)
def test_version_history_rejects_missing_required_fields(missing_field: str) -> None:
    query = deepcopy(_synthetic_version_history())
    del query["versions"][1][missing_field]

    with pytest.raises(AssertionError):
        _validate_version_history(query, REQUIRED_VERSION_FIELDS)


def test_screening_protocol_prespecifies_required_rules() -> None:
    protocol = " ".join(PROTOCOL_PATH.read_text().split()).casefold()
    required_text = (
        "English-language human studies",
        "relevant methods papers",
        "urban or subregional geography",
        "EHR, claims, HIE, or clinical-network surveillance",
        "disease mapping",
        "life expectancy or mortality",
        "representativeness",
        "local planning",
        "purely individual prediction models",
        "include",
        "exclude",
        "background",
        "awaiting_full_text",
        "exactly one explicit exclusion reason",
    )
    for text in required_text:
        assert text.casefold() in protocol
