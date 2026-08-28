from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.config import PROJECT_ROOT_ENV
from chicagohealthmap.governance.s5_scorecard import (
    S5ScorecardError,
    build_s5_reconciliation_draft_packet,
    build_s5_scorecard_packet,
    build_s5_scoring_artifacts_packet,
    validate_s5_reconciliation_draft_payload,
    write_s5_reconciliation_draft_packet,
)


ROOT = Path(__file__).parents[2]


def _copy_s5_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "fixture"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
    for relative in [
        "docs/analysis/sap_workbook_spec.json",
        "docs/analysis/s4_methods_mapping.json",
    ]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def _completed_s5_artifacts_payload() -> dict[str, Any]:
    payload = build_s5_scoring_artifacts_packet(ROOT).to_jsonable()
    payload["status"] = "worksheets_completed_reconciliation_pending"
    for worksheet_index, worksheet in enumerate(payload["scorer_worksheets"]):
        worksheet["status"] = "completed"
        worksheet["outcome_information_used"] = False
        for row in worksheet["rows"]:
            row["outcome_information_used"] = False
            row["hard_gate_status"] = "met"
            row["rationale"] = (
                f"{worksheet['scorer_id']} blinded rationale for "
                f"{row['candidate_id']} / {row['domain']}."
            )
            row["score"] = (
                row["maximum_points"] if worksheet_index == 0 else (row["maximum_points"] - 1)
            )
    return payload


def _write_completed_s5_artifacts(tmp_path: Path) -> Path:
    path = tmp_path / "s5_blinded_scoring_artifacts_completed.json"
    path.write_text(
        json.dumps(_completed_s5_artifacts_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def test_s5_scorecard_packet_is_outcome_blinded_and_non_authorizing() -> None:
    packet = build_s5_scorecard_packet(ROOT)

    assert packet.gate == "S5"
    assert packet.status == "scorecard_template_ready"
    assert packet.outcome_blinded is True
    assert packet.results_authorized is False
    assert packet.analysis_authorized is False
    assert packet.case_study_spatial_frame["frame"] == "City of Chicago"
    assert packet.forbidden_information == (
        "life-expectancy values",
        "mortality values",
        "outcome maps",
        "outcome correlations",
        "model results",
        "outcome-linked residuals",
    )
    assert "no final analytic dataset" in packet.blocked_actions


def test_s5_scorecard_packet_preserves_fixed_100_point_anchors() -> None:
    packet = build_s5_scorecard_packet(ROOT)

    assert sum(domain.maximum_points for domain in packet.scoring_domains) == 100
    assert [domain.domain for domain in packet.scoring_domains] == [
        "Community-area usability",
        "Tract usability/precision",
        "Predictor temporal stability",
        "Phenotype interpretability",
        "Comparator definition/period",
        "Evidence and novelty gap",
        "Translation questionability",
        "Distinct portfolio contribution",
    ]
    assert all(
        domain.status in {"PENDING S5", "PENDING S4-S5"} for domain in packet.scoring_domains
    )
    assert packet.portfolio_rules[0].domain == "Cardiometabolic bundle"
    assert packet.portfolio_rules[1].domain == "Portfolio and tie-break"


def test_s5_scorecard_packet_records_candidate_shells_without_scores() -> None:
    packet = build_s5_scorecard_packet(ROOT)

    assert [candidate.case_id for candidate in packet.candidate_shells] == [
        "cardiometabolic_bundle",
        "respiratory_copd",
    ]
    assert all(
        candidate.score_status == "pending_two_blinded_scorers"
        for candidate in packet.candidate_shells
    )
    assert all(candidate.reconciled_score is None for candidate in packet.candidate_shells)
    assert packet.candidate_shells[0].component_conditions == ("hypertension", "diabetes")
    assert packet.candidate_shells[1].component_conditions == ("copd",)


def test_s5_scorecard_cli_writes_json(tmp_path: Path, monkeypatch) -> None:
    root = _copy_s5_fixture(tmp_path)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))
    output = root / "docs/analysis/s5_case_selection_scorecard.json"

    result = CliRunner().invoke(
        app,
        ["governance", "s5-scorecard", "build", "--output", str(output)],
    )

    assert result.exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["record_type"] == "outcome_blinded_case_selection_scorecard_template"
    assert payload["status"] == "scorecard_template_ready"
    assert payload["case_study_spatial_frame"]["frame"] == "City of Chicago"
    assert len(payload["scoring_domains"]) == 8
    assert json.loads(result.stdout)["output_path"].endswith(
        "docs/analysis/s5_case_selection_scorecard.json"
    )


def test_s5_scoring_artifacts_create_two_blinded_worksheets() -> None:
    packet = build_s5_scoring_artifacts_packet(ROOT)

    assert packet.record_type == "outcome_blinded_s5_scoring_artifacts_template"
    assert packet.status == "worksheets_ready_reconciliation_pending"
    assert packet.outcome_blinded is True
    assert packet.results_authorized is False
    assert len(packet.scorer_worksheets) == 2
    assert [worksheet.scorer_id for worksheet in packet.scorer_worksheets] == [
        "blinded_scorer_1",
        "blinded_scorer_2",
    ]
    for worksheet in packet.scorer_worksheets:
        assert worksheet.status == "pending_completion"
        assert worksheet.outcome_information_used is False
        assert len(worksheet.rows) == 16
        assert all(row.score is None for row in worksheet.rows)
        assert all(row.evidence_references for row in worksheet.rows)
        assert all(row.outcome_information_used is False for row in worksheet.rows)
    first_row = packet.scorer_worksheets[0].rows[0]
    assert "docs/analysis/s4_methods_mapping.json" in first_row.evidence_references
    assert "outputs/provenance/variable_lineage.csv" in first_row.evidence_references


def test_s5_scoring_artifacts_define_reconciliation_and_approval_format() -> None:
    packet = build_s5_scoring_artifacts_packet(ROOT)

    assert packet.reconciliation_template.status == "pending_reconciliation"
    assert packet.reconciliation_template.outcome_information_used is False
    assert [entry.case_id for entry in packet.reconciliation_template.entries] == [
        "cardiometabolic_bundle",
        "respiratory_copd",
    ]
    assert all(
        entry.reconciled_total_score is None for entry in packet.reconciliation_template.entries
    )
    assert packet.approval_record_format.destination == "outputs/governance/case_selection.json"
    assert packet.approval_record_format.required_fields == (
        "record_type",
        "gate",
        "status",
        "outcome_blinded",
        "cases",
        "approval",
    )
    assert packet.approval_record_format.case_fields == ("order", "case_id", "display_name")
    assert packet.approval_record_format.approval_fields == ("human", "date", "decision")


def test_s5_scoring_artifacts_preserve_pending_domains_without_approval() -> None:
    packet = build_s5_scoring_artifacts_packet(ROOT)

    rows = packet.scorer_worksheets[0].rows
    by_domain = {(row.candidate_id, row.domain): row for row in rows}
    phenotype = by_domain[("cardiometabolic_bundle", "Phenotype interpretability")]
    novelty = by_domain[("respiratory_copd", "Evidence and novelty gap")]
    assert "docs/analysis/methods_discrepancies.md" in phenotype.evidence_references
    assert "docs/methods/literature_search_protocol.md" in novelty.evidence_references
    assert phenotype.hard_gate_status == "pending"
    assert novelty.hard_gate_status == "pending"


def test_s5_scoring_artifacts_exclude_broad_planning_references() -> None:
    packet = build_s5_scoring_artifacts_packet(ROOT)

    forbidden = {
        "docs/analysis/s5_case_selection_scorecard.json",
        "docs/analysis/statistical_analysis_plan.md",
    }
    row_references = {
        reference
        for worksheet in packet.scorer_worksheets
        for row in worksheet.rows
        for reference in row.evidence_references
    }

    assert row_references.isdisjoint(forbidden)


def test_s5_scoring_artifacts_cli_writes_json(tmp_path: Path, monkeypatch) -> None:
    root = _copy_s5_fixture(tmp_path)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))
    scorecard = root / "docs/analysis/s5_case_selection_scorecard.json"
    scorecard_result = CliRunner().invoke(
        app,
        ["governance", "s5-scorecard", "build", "--output", str(scorecard)],
    )
    assert scorecard_result.exit_code == 0
    output = root / "docs/analysis/s5_blinded_scoring_artifacts.json"

    result = CliRunner().invoke(
        app,
        ["governance", "s5-scorecard", "worksheets", "--output", str(output)],
    )

    assert result.exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["record_type"] == "outcome_blinded_s5_scoring_artifacts_template"
    assert len(payload["scorer_worksheets"]) == 2
    assert payload["approval_record_format"]["destination"] == (
        "outputs/governance/case_selection.json"
    )
    assert json.loads(result.stdout)["output_path"].endswith(
        "docs/analysis/s5_blinded_scoring_artifacts.json"
    )


def test_s5_reconciliation_draft_averages_completed_blinded_scores(
    tmp_path: Path,
) -> None:
    input_path = _write_completed_s5_artifacts(tmp_path)

    draft = build_s5_reconciliation_draft_packet(input_path)
    payload = draft.to_jsonable()

    assert payload["record_type"] == "outcome_blinded_case_selection_reconciliation_draft"
    assert payload["gate"] == "S5"
    assert payload["status"] == "reconciled_pending_human_approval"
    assert payload["outcome_blinded"] is True
    assert payload["results_authorized"] is False
    assert payload["approval_required"] is True
    assert payload["approval_record_path"] == "outputs/governance/case_selection.json"
    assert payload["blocked_actions"] == [
        "no outcome unblinding",
        "no confirmatory modeling",
        "no Results prose",
        "no case promotion",
        "no final analytic dataset",
        "no combined marimo case-study notebook",
    ]
    assert payload["entries"] == [
        {
            "case_id": "cardiometabolic_bundle",
            "display_name": "Cardiometabolic bundle",
            "scorer_totals": {
                "blinded_scorer_1": 100,
                "blinded_scorer_2": 92,
            },
            "reconciled_total_score": 96.0,
            "reconciliation_status": "averaged_two_blinded_scores",
            "hard_gate_disposition": "all_met",
        },
        {
            "case_id": "respiratory_copd",
            "display_name": "Respiratory COPD candidate",
            "scorer_totals": {
                "blinded_scorer_1": 100,
                "blinded_scorer_2": 92,
            },
            "reconciled_total_score": 96.0,
            "reconciliation_status": "averaged_two_blinded_scores",
            "hard_gate_disposition": "all_met",
        },
    ]


def test_s5_reconciliation_draft_uses_identical_score_rule(tmp_path: Path) -> None:
    payload = _completed_s5_artifacts_payload()
    for worksheet in payload["scorer_worksheets"]:
        for row in worksheet["rows"]:
            row["score"] = row["maximum_points"]
    input_path = tmp_path / "completed.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    draft = build_s5_reconciliation_draft_packet(input_path)

    assert {
        (entry.case_id, entry.reconciled_total_score, entry.reconciliation_status)
        for entry in draft.entries
    } == {
        ("cardiometabolic_bundle", 100.0, "identical_blinded_scores"),
        ("respiratory_copd", 100.0, "identical_blinded_scores"),
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda payload: payload["scorer_worksheets"].pop(),
            "exactly two scorer worksheets",
        ),
        (
            lambda payload: payload["scorer_worksheets"][0].__setitem__(
                "outcome_information_used", True
            ),
            "outcome information",
        ),
        (
            lambda payload: payload["scorer_worksheets"][0].__setitem__(
                "status", "pending_completion"
            ),
            "worksheet status",
        ),
        (
            lambda payload: payload["scorer_worksheets"][0]["rows"][0].__setitem__("score", None),
            "score",
        ),
        (
            lambda payload: payload["scorer_worksheets"][0]["rows"][0].__setitem__(
                "score", payload["scorer_worksheets"][0]["rows"][0]["maximum_points"] + 1
            ),
            "score",
        ),
        (
            lambda payload: payload["scorer_worksheets"][0]["rows"][0].__setitem__(
                "rationale", " "
            ),
            "rationale",
        ),
        (
            lambda payload: payload["scorer_worksheets"][0]["rows"][0].__setitem__(
                "evidence_references", []
            ),
            "evidence",
        ),
        (
            lambda payload: payload["scorer_worksheets"][0]["rows"].pop(),
            "expected S5 scoring grid",
        ),
        (
            lambda payload: [worksheet["rows"].pop() for worksheet in payload["scorer_worksheets"]],
            "expected S5 scoring grid",
        ),
        (
            lambda payload: [
                worksheet["rows"][0].__setitem__(
                    "evidence_references", ["docs/analysis/statistical_analysis_plan.md"]
                )
                for worksheet in payload["scorer_worksheets"]
            ],
            "evidence",
        ),
        (
            lambda payload: payload["scorer_worksheets"][0]["rows"][0].__setitem__(
                "hard_gate_status", "pending"
            ),
            "hard-gate status",
        ),
        (
            lambda payload: payload.__setitem__("results_authorized", True),
            "must not authorize results",
        ),
        (
            lambda payload: payload.__setitem__("status", "approved"),
            "must not claim S5 approval",
        ),
        (
            lambda payload: payload.__setitem__(
                "status", "worksheets_ready_reconciliation_pending"
            ),
            "must be completed",
        ),
    ],
)
def test_s5_reconciliation_draft_fails_closed(tmp_path: Path, mutation, message: str) -> None:
    payload = _completed_s5_artifacts_payload()
    mutation(payload)
    input_path = tmp_path / "bad.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(S5ScorecardError, match=message):
        build_s5_reconciliation_draft_packet(input_path)


def test_s5_reconciliation_draft_cli_writes_draft_without_approval_record(
    tmp_path: Path, monkeypatch
) -> None:
    root = _copy_s5_fixture(tmp_path)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))
    input_path = root / "docs/analysis/s5_blinded_scoring_artifacts_completed.json"
    input_path.write_text(
        json.dumps(_completed_s5_artifacts_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output = root / "outputs/governance/case_selection_reconciliation_draft.json"

    result = CliRunner().invoke(
        app,
        [
            "governance",
            "s5-scorecard",
            "reconcile",
            "--input",
            str(input_path),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["record_type"] == "outcome_blinded_case_selection_reconciliation_draft"
    assert payload["status"] == "reconciled_pending_human_approval"
    assert payload["results_authorized"] is False
    assert payload["source_worksheet_path"] == (
        "docs/analysis/s5_blinded_scoring_artifacts_completed.json"
    )
    assert not (root / "outputs/governance/case_selection.json").exists()
    assert json.loads(result.stdout)["output_path"].endswith(
        "outputs/governance/case_selection_reconciliation_draft.json"
    )


def test_s5_reconciliation_draft_validation_preserves_blocked_actions(tmp_path: Path) -> None:
    payload = build_s5_reconciliation_draft_packet(
        _write_completed_s5_artifacts(tmp_path)
    ).to_jsonable()
    payload["blocked_actions"] = ["no outcome unblinding"]

    with pytest.raises(S5ScorecardError, match="blocked actions"):
        validate_s5_reconciliation_draft_payload(payload)


def test_s5_reconciliation_draft_validation_recomputes_arithmetic(
    tmp_path: Path,
) -> None:
    payload = build_s5_reconciliation_draft_packet(
        _write_completed_s5_artifacts(tmp_path)
    ).to_jsonable()
    payload["entries"][0]["reconciled_total_score"] = 999

    with pytest.raises(S5ScorecardError, match="reconciled score"):
        validate_s5_reconciliation_draft_payload(payload)


def test_s5_reconciliation_draft_cli_rejects_external_input(tmp_path: Path, monkeypatch) -> None:
    root = _copy_s5_fixture(tmp_path)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))
    external = tmp_path / "external_completed.json"
    external.write_text(json.dumps(_completed_s5_artifacts_payload()), encoding="utf-8")
    output = root / "outputs/governance/case_selection_reconciliation_draft.json"

    result = CliRunner().invoke(
        app,
        [
            "governance",
            "s5-scorecard",
            "reconcile",
            "--input",
            str(external),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 1
    assert "outside repository" in result.stderr
    assert not output.exists()


def test_s5_reconciliation_draft_writer_rejects_approval_record_path(
    tmp_path: Path,
) -> None:
    input_path = _write_completed_s5_artifacts(tmp_path)
    output = tmp_path / "outputs/governance/drafts/../case_selection.json"

    with pytest.raises(S5ScorecardError, match="approval record path"):
        write_s5_reconciliation_draft_packet(input_path, output)

    assert not (tmp_path / "outputs/governance/case_selection.json").exists()
