from collections.abc import Callable
from copy import deepcopy
import json
from pathlib import Path
import shutil
from typing import Any
import warnings

import pytest
from pydantic import ValidationError
import yaml  # type: ignore[import-untyped]

from chicagohealthmap.manuscript.contracts import load_manuscript_contracts
from chicagohealthmap.manuscript.models import JournalContract, ManuscriptContracts


def _repository_payload() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    directory = root / "config" / "manuscript"
    return {
        "journal": yaml.safe_load((directory / "jama_health_forum.yml").read_text()),
        "style": yaml.safe_load((directory / "style_contract.yml").read_text()),
        "agents": yaml.safe_load((directory / "agents.yml").read_text())["agents"],
        "gates": yaml.safe_load((directory / "gates.yml").read_text())["gates"],
    }


def _remove_results_agent(payload: dict[str, Any]) -> None:
    del payload["agents"]["results_agent"]


def _alter_results_agent_actions(payload: dict[str, Any]) -> None:
    payload["agents"]["results_agent"]["prohibited_actions"] = ["Invent results"]


def _alter_required_measure_phrase(payload: dict[str, Any]) -> None:
    payload["style"]["required_measure_phrase"] = "EHR-diagnosed prevalence"


def _alter_prohibited_verbs(payload: dict[str, Any]) -> None:
    payload["style"]["prohibited_observational_verbs"].remove("cause")


def _alter_unsupported_superlatives(payload: dict[str, Any]) -> None:
    payload["style"]["unsupported_superlatives"].append("groundbreaking")


def _alter_m1_prerequisites(payload: dict[str, Any]) -> None:
    payload["gates"]["M1"]["requires"] = ["S4", "S5", "S7"]


def _alter_gate_artifacts_and_acceptance(payload: dict[str, Any]) -> None:
    payload["gates"]["M6"]["artifacts"] = ["live journal recheck"]
    payload["gates"]["M6"]["acceptance"] = ["Editor review pending"]


def test_repository_contracts_freeze_approved_limits() -> None:
    root = Path(__file__).resolve().parents[3]
    contracts = load_manuscript_contracts(root)
    assert contracts.journal.article_type == "Original Investigation"
    assert contracts.journal.main_text_words == 3000
    assert contracts.journal.abstract_words == 350
    assert contracts.journal.title_characters == 100
    assert contracts.journal.key_points_words == 100
    assert contracts.journal.max_main_displays == 5
    assert contracts.journal.reference_range == (50, 75)
    assert contracts.style.required_measure_phrase == (
        "EHR-diagnosed proportion among observed CAPriCORN adults"
    )
    assert set(contracts.agents) == {
        "orchestrator_editor",
        "artifact_lineage_agent",
        "methods_reporting_agent",
        "results_agent",
        "case_study_1_agent",
        "case_study_2_agent",
        "evidence_claims_agent",
        "discussion_policy_agent",
        "statistical_qa_agent",
        "jama_style_qa_agent",
    }
    assert contracts.gates["M1"].requires == ("S4", "S5", "S6", "S7")


def test_journal_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        JournalContract.model_validate(
            {
                "article_type": "Original Investigation",
                "main_text_words": 3000,
                "abstract_words": 350,
                "title_characters": 100,
                "key_points_words": 100,
                "max_main_displays": 5,
                "reference_range": [50, 75],
                "abstract_headings": [
                    "Importance",
                    "Objective",
                    "Design",
                    "Setting",
                    "Participants",
                    "Exposures",
                    "Main Outcomes and Measures",
                    "Results",
                    "Conclusions and Relevance",
                ],
                "key_point_headings": ["Question", "Findings", "Meaning"],
                "official_url": "https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors",
                "accessed": "2026-07-14",
                "revalidate_days_before_submission": 30,
                "unexpected": True,
            }
        )


def test_loaded_authority_mappings_reject_mutation() -> None:
    contracts = load_manuscript_contracts(Path(__file__).resolve().parents[3])

    for mapping, key in (
        (contracts.agents, "results_agent"),
        (contracts.gates, "M1"),
    ):
        original = mapping[key]
        with pytest.raises(TypeError):
            mapping[key] = original
        with pytest.raises(TypeError):
            del mapping[key]
        with pytest.raises(AttributeError):
            mapping.pop(key)
        assert mapping[key] == original

    for field in ("agents", "gates"):
        with pytest.raises(ValidationError):
            setattr(contracts, field, {})


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(_remove_results_agent, id="missing-results-agent"),
        pytest.param(_alter_results_agent_actions, id="altered-results-agent-actions"),
        pytest.param(_alter_required_measure_phrase, id="altered-measure-phrase"),
        pytest.param(_alter_prohibited_verbs, id="altered-prohibited-verbs"),
        pytest.param(
            _alter_unsupported_superlatives,
            id="altered-unsupported-superlatives",
        ),
        pytest.param(_alter_m1_prerequisites, id="altered-m1-prerequisites"),
        pytest.param(
            _alter_gate_artifacts_and_acceptance,
            id="altered-gate-artifacts-and-acceptance",
        ),
    ],
)
def test_contracts_reject_altered_authority(
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    payload = deepcopy(_repository_payload())
    mutate(payload)

    with pytest.raises(ValidationError):
        ManuscriptContracts.model_validate(payload)


def test_contracts_model_dump_json_mode_is_warning_free() -> None:
    contracts = load_manuscript_contracts(Path(__file__).resolve().parents[3])

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        dumped = contracts.model_dump(mode="json")

    assert dumped["agents"]["results_agent"]["permitted_outputs"] == ["results packet"]
    assert dumped["gates"]["M1"]["requires"] == ["S4", "S5", "S6", "S7"]


def test_contracts_model_dump_json_returns_valid_json() -> None:
    contracts = load_manuscript_contracts(Path(__file__).resolve().parents[3])

    dumped = json.loads(contracts.model_dump_json())

    assert dumped["style"]["required_measure_phrase"] == (
        "EHR-diagnosed proportion among observed CAPriCORN adults"
    )
    assert set(dumped["agents"]) == set(contracts.agents)


def test_contracts_deep_copy_remains_equal_and_immutable() -> None:
    contracts = load_manuscript_contracts(Path(__file__).resolve().parents[3])

    copied = contracts.model_copy(deep=True)

    assert copied == contracts
    assert copied is not contracts
    assert copied.agents is not contracts.agents
    assert copied.gates is not contracts.gates
    for mapping, key in ((copied.agents, "results_agent"), (copied.gates, "M1")):
        with pytest.raises(TypeError):
            mapping[key] = mapping[key]


@pytest.mark.parametrize(
    ("filename", "payload", "message"),
    [
        ("agents.yml", {}, "agents.yml must contain an agents mapping"),
        ("agents.yml", {"agents": []}, "agents.yml must contain an agents mapping"),
        ("gates.yml", {}, "gates.yml must contain a gates mapping"),
        ("gates.yml", {"gates": []}, "gates.yml must contain a gates mapping"),
    ],
)
def test_contract_wrapper_errors_are_normalized(
    tmp_path: Path,
    filename: str,
    payload: object,
    message: str,
) -> None:
    source = Path(__file__).resolve().parents[3] / "config" / "manuscript"
    destination = tmp_path / "config" / "manuscript"
    shutil.copytree(source, destination)
    (destination / filename).write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_manuscript_contracts(tmp_path)
