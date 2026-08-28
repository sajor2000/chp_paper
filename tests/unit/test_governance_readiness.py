from __future__ import annotations

from hashlib import sha256
import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.config import PROJECT_ROOT_ENV
from chicagohealthmap.governance.readiness import assess_readiness
from chicagohealthmap.governance.s5_scorecard import (
    build_s5_scoring_artifacts_packet,
    write_s5_reconciliation_draft_packet,
)


ROOT = Path(__file__).parents[2]


def _copy_readiness_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "fixture"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
    for relative in [
        "docs/analysis/gate_2_evidence_packet_attestation.json",
        "docs/analysis/s4_methods_mapping.json",
        "docs/analysis/s5_blinded_scoring_artifacts.json",
        "docs/analysis/s5_case_selection_scorecard.json",
        "docs/analysis/statistical_analysis_plan.md",
        "outputs/quality/gate_3_decision.json",
        "sources/literature/pubmed/snapshots/2026-07-14/screening.csv",
    ]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def _write_completed_s5_artifacts(root: Path) -> Path:
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
    input_path = root / "docs/analysis/s5_blinded_scoring_artifacts_completed.json"
    input_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return input_path


def _write_approved_s5(root: Path) -> None:
    path = root / "outputs/governance/case_selection.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "record_type": "outcome_blinded_case_selection",
                "gate": "S5",
                "status": "approved",
                "outcome_blinded": True,
                "cases": [
                    {
                        "order": 1,
                        "case_id": "cardiometabolic_bundle",
                        "display_name": "Cardiometabolic bundle",
                    },
                    {
                        "order": 2,
                        "case_id": "respiratory_copd",
                        "display_name": "Respiratory COPD candidate",
                    },
                ],
                "approval": {
                    "human": "JC",
                    "date": "2026-07-15",
                    "decision": "approved",
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_s6_authority(root: Path) -> None:
    sap = root / "docs/analysis/statistical_analysis_plan.md"
    governance = root / "outputs/governance"
    governance.mkdir(parents=True, exist_ok=True)
    signed_sap = {
        "record_type": "signed_statistical_analysis_plan",
        "status": "signed",
        "version": "1.0.0",
        "path": "docs/analysis/statistical_analysis_plan.md",
        "sha256": sha256(sap.read_bytes()).hexdigest(),
        "case_ids": ["cardiometabolic_bundle", "respiratory_copd"],
        "approval": {"human": "JC", "date": "2026-07-15", "decision": "approved"},
    }
    (governance / "signed_sap.json").write_text(
        json.dumps(signed_sap, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for name, payload in {
        "s6_final_variable_dictionary.json": {"variables": ["source_id", "case_id"]},
        "s6_model_shells.json": {"models": ["descriptive", "spatial_screen"]},
        "s6_sensitivity_families.json": {"families": ["suppression", "reliability"]},
        "s6_multiplicity_rule.json": {"rule": "family-wise descriptive control"},
        "s6_software_manifest.json": {"python": "project-lock"},
    }.items():
        (governance / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    authority = {
        "record_type": "s6_analysis_authority",
        "gate": "S6",
        "status": "approved",
        "analysis_authorized": True,
        "results_authorized": False,
        "case_ids": ["cardiometabolic_bundle", "respiratory_copd"],
        "signed_sap_record": "outputs/governance/signed_sap.json",
        "artifacts": {
            "final_variable_dictionary": "outputs/governance/s6_final_variable_dictionary.json",
            "model_shells": "outputs/governance/s6_model_shells.json",
            "sensitivity_families": "outputs/governance/s6_sensitivity_families.json",
            "multiplicity_rule": "outputs/governance/s6_multiplicity_rule.json",
            "software_manifest": "outputs/governance/s6_software_manifest.json",
        },
        "approval": {"human": "JC", "date": "2026-07-15", "decision": "approved"},
    }
    (governance / "s6_analysis_authority.json").write_text(
        json.dumps(authority, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_readiness_records_gate_2_packet_attestation_but_blocks_analysis(
    tmp_path: Path,
) -> None:
    report = assess_readiness(_copy_readiness_fixture(tmp_path), through="S6")

    assert report.through == "S6"
    assert report.analysis_authorized is False
    assert report.results_authorized is False
    assert report.gates["Gate 2"]["evidence_packet_attestation"] == "accepted"
    assert report.gates["Gate 2"]["status"] == "packet_accepted_screening_pending"
    assert report.gates["Gate 2"]["pending_screening_decisions"] == 1178
    assert report.gates["Gate 3"]["status"] == "closed"
    assert report.gates["S4"]["status"] == "methods_dictionary_accepted_position_mapping_guarded"
    assert report.gates["S4"]["methods_dictionary_status"] == "website_dictionary_authoritative"
    assert report.gates["S4"]["case_study_spatial_frame"] == "City of Chicago"
    assert report.gates["S4"]["position_mapping_status"] == "partial_guarded"
    assert report.gates["S5"]["status"] == "scorecard_template_ready_scoring_pending"
    assert report.gates["S5"]["scorecard_status"] == "scorecard_template_ready"
    assert report.gates["S5"]["worksheet_status"] == "worksheets_ready_reconciliation_pending"
    assert report.gates["S6"]["status"] == "blocked"
    assert "no confirmatory modeling" in report.blocked_actions


def test_readiness_cli_emits_json_and_check_fails(tmp_path: Path, monkeypatch) -> None:
    root = _copy_readiness_fixture(tmp_path)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "readiness", "--through", "S6"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["gates"]["Gate 2"]["evidence_packet_attestation"] == "accepted"

    check = runner.invoke(app, ["governance", "readiness", "--through", "S6", "--check"])
    assert check.exit_code == 1
    assert "S4-S6 readiness remains blocked" in check.stderr


def test_readiness_reports_s5_human_approval_pending_for_valid_reconciliation_draft(
    tmp_path: Path,
) -> None:
    root = _copy_readiness_fixture(tmp_path)
    completed = _write_completed_s5_artifacts(root)
    write_s5_reconciliation_draft_packet(
        completed,
        root / "outputs/governance/case_selection_reconciliation_draft.json",
    )

    report = assess_readiness(root, through="S6")

    assert report.results_authorized is False
    assert report.gates["S5"]["status"] == "reconciled_pending_human_approval"
    assert report.gates["S5"]["reconciliation_status"] == ("reconciled_pending_human_approval")
    assert report.gates["S5"]["results_authorized"] is False
    assert report.gates["S5"]["approval_record_path"] == ("outputs/governance/case_selection.json")
    assert report.gates["S6"]["status"] == "blocked"
    assert "signed S5 portfolio decision" in report.gates["S5"]["blocked_by"]


def test_readiness_reports_human_approved_s5_before_s6(tmp_path: Path) -> None:
    root = _copy_readiness_fixture(tmp_path)
    _write_approved_s5(root)

    report = assess_readiness(root, through="S6")

    assert report.analysis_authorized is False
    assert report.results_authorized is False
    assert report.gates["S5"]["status"] == "approved"
    assert report.gates["S5"]["approval_record_path"] == "outputs/governance/case_selection.json"
    assert report.gates["S6"]["status"] == "blocked"
    assert report.gates["S6"]["blocked_by"] == ("S6 signed analysis authority",)


def test_readiness_reports_s6_approved_analysis_authority(tmp_path: Path) -> None:
    root = _copy_readiness_fixture(tmp_path)
    _write_approved_s5(root)
    _write_s6_authority(root)

    report = assess_readiness(root, through="S6")

    assert report.analysis_authorized is True
    assert report.results_authorized is False
    assert report.gates["S5"]["status"] == "approved"
    assert report.gates["S6"]["status"] == "approved"
    assert report.gates["S6"]["analysis_authorized"] is True
    assert report.gates["S6"]["results_authorized"] is False
    assert "no confirmatory modeling" not in report.blocked_actions
    assert "no final analytic dataset" not in report.blocked_actions
    assert "no combined marimo case-study notebook" not in report.blocked_actions
    assert "no Results prose before S7" in report.blocked_actions


def test_readiness_cli_check_passes_for_s6_analysis_authority(tmp_path: Path, monkeypatch) -> None:
    root = _copy_readiness_fixture(tmp_path)
    _write_approved_s5(root)
    _write_s6_authority(root)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))

    result = CliRunner().invoke(app, ["governance", "readiness", "--through", "S6", "--check"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["analysis_authorized"] is True
    assert payload["results_authorized"] is False
