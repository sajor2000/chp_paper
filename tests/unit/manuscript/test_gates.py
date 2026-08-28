from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.manuscript.gates import (
    ManuscriptGateError,
    assert_results_authorized,
    evaluate_manuscript_gates,
)


def _write_gate(root: Path, gate: str, payload: object) -> None:
    directory = root / "outputs" / "governance" / "gates"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{gate}.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_manuscript_gate(root: Path, gate: str, payload: object) -> None:
    directory = root / "outputs" / "manuscript" / "control" / "gates"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{gate}.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
    )


def _artifact(root: Path, label: str, artifact_id: str, path: str) -> dict[str, str]:
    source = root / path
    return {
        "label": label,
        "artifact_id": artifact_id,
        "path": path,
        "sha256": sha256(source.read_bytes()).hexdigest(),
    }


def _passed_record(
    gate: str,
    artifacts: list[dict[str, str]],
    criterion: str,
) -> dict[str, object]:
    return {
        "gate": gate,
        "status": "passed",
        "artifacts": artifacts,
        "acceptance": [{"criterion": criterion, "state": "accepted"}],
        "approval": {
            "human": "J Doe",
            "date": "2026-07-14",
            "decision": "accepted",
        },
    }


def _write_m0(root: Path) -> None:
    paths = {
        "journal contract": "config/manuscript/jama_health_forum.yml",
        "style contract": "config/manuscript/style_contract.yml",
        "agent contract": "config/manuscript/agents.yml",
        "gate contract": "config/manuscript/gates.yml",
    }
    artifacts = [
        _artifact(root, label, f"m0-{index}", path)
        for index, (label, path) in enumerate(paths.items(), start=1)
    ]
    _write_manuscript_gate(
        root,
        "M0",
        _passed_record(
            "M0",
            artifacts,
            "Contracts validate and the journal audit is dated",
        ),
    )


def _empty_ledgers(root: Path) -> Path:
    control = root / "outputs" / "manuscript" / "control"
    control.mkdir(parents=True, exist_ok=True)
    headers = {
        "claim_ledger.csv": [
            "claim_id",
            "section",
            "draft_claim",
            "claim_class",
            "source_or_artifact_id",
            "exact_support_location",
            "population_geography_measure_period_match",
            "support_strength",
            "conflict_or_gap",
            "allowed_wording",
            "prohibited_inference",
            "result_status",
            "owner",
            "verified_by",
            "verified_date",
            "final_text_location",
        ],
        "number_ledger.csv": [
            "number_id",
            "artifact_id",
            "checksum",
            "artifact_field",
            "code_version",
            "population",
            "exclusions",
            "geography",
            "time_period",
            "measure",
            "unit",
            "denominator",
            "raw_value",
            "display_value",
            "uncertainty",
            "result_status",
            "manuscript_locations",
        ],
        "ai_use_ledger.csv": [
            "ai_use_id",
            "platform",
            "model",
            "manufacturer",
            "start_date",
            "end_date",
            "use",
            "affected_artifact",
            "human_verifier",
            "verified_date",
        ],
        "issue_ledger.csv": [
            "issue_id",
            "severity",
            "gate",
            "description",
            "evidence",
            "owner",
            "status",
            "resolution",
        ],
    }
    for filename, columns in headers.items():
        pd.DataFrame(columns=columns).to_csv(control / filename, index=False)
    return control


def _write_machine_passable_state(root: Path) -> Path:
    _write_m0(root)
    _empty_ledgers(root)
    frozen = root / "outputs" / "frozen"
    frozen.mkdir(parents=True, exist_ok=True)
    paths = {
        "analytic dataset": "outputs/frozen/analytic.csv",
        "study manifest": "outputs/frozen/study-manifest.yml",
        "frozen outputs": "outputs/frozen/results.json",
        "checksums": "outputs/frozen/checksums.sha256",
    }
    for index, path in enumerate(paths.values(), start=1):
        (root / path).write_text(f"artifact {index}\n", encoding="utf-8")
    artifacts = [
        _artifact(root, label, f"m1-{index}", path)
        for index, (label, path) in enumerate(paths.items(), start=1)
    ]
    control = root / "outputs/manuscript/control"
    number_columns = list(pd.read_csv(control / "number_ledger.csv").columns)
    number = {column: "value" for column in number_columns}
    number.update(
        {
            "number_id": "N-001",
            "artifact_id": artifacts[0]["artifact_id"],
            "checksum": "sha256:" + artifacts[0]["sha256"],
            "result_status": "prespecified",
        }
    )
    pd.DataFrame([number]).to_csv(control / "number_ledger.csv", index=False)
    for gate in ("S4", "S5", "S6"):
        _write_gate(root, gate, {"gate": gate, "status": "passed"})
    _write_gate(
        root,
        "S7",
        {
            "gate": "S7",
            "status": "passed",
            "artifacts": [
                {key: item[key] for key in ("artifact_id", "path", "sha256")} for item in artifacts
            ],
        },
    )
    _write_manuscript_gate(
        root,
        "M1",
        _passed_record(
            "M1",
            artifacts,
            "Every primary number has a frozen artifact ID",
        ),
    )
    return root / paths["analytic dataset"]


def _write_authorized_gates(root: Path) -> Path:
    artifact = root / "outputs" / "frozen" / "primary.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b'{"estimate": 0.12}\n')
    for gate in ("S4", "S5", "S6"):
        _write_gate(root, gate, {"gate": gate, "status": "passed"})
    _write_gate(
        root,
        "S7",
        {
            "gate": "S7",
            "status": "passed",
            "artifacts": [
                {
                    "artifact_id": "primary-estimate",
                    "path": "outputs/frozen/primary.json",
                    "sha256": sha256(artifact.read_bytes()).hexdigest(),
                }
            ],
        },
    )
    return artifact


def test_results_are_blocked_without_s7(tmp_project) -> None:
    for gate in ("S4", "S5", "S6"):
        tmp_project.write_gate(gate, "passed")
    tmp_project.write_gate("S7", "open")

    with pytest.raises(ManuscriptGateError, match="S7 must pass"):
        assert_results_authorized(tmp_project.paths)


def test_s7_pass_without_frozen_artifact_checksums_is_invalid(tmp_project) -> None:
    for gate in ("S4", "S5", "S6", "S7"):
        tmp_project.write_gate(gate, "passed")

    with pytest.raises(ManuscriptGateError, match="S7 requires frozen artifact checksums"):
        assert_results_authorized(tmp_project.paths)


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ("{", "S4 gate record is not valid JSON"),
        ("[]", "S4 gate record must be an object"),
        ('{"gate":"S4","status":"unknown"}', "S4 gate status is invalid"),
        ('{"gate":"S5","status":"passed"}', "S4 gate identity mismatch"),
    ],
)
def test_gate_records_fail_closed(tmp_project, raw: str, message: str) -> None:
    gate_path = tmp_project.root / "outputs" / "governance" / "gates" / "S4.json"
    gate_path.parent.mkdir(parents=True)
    gate_path.write_text(raw, encoding="utf-8")

    with pytest.raises(ManuscriptGateError, match=message):
        evaluate_manuscript_gates(tmp_project.paths)


@pytest.mark.parametrize("gate", ["S5", "S6", "S7"])
def test_passed_scientific_gate_requires_all_predecessors(tmp_project, gate: str) -> None:
    tmp_project.write_gate(gate, "passed")

    with pytest.raises(ManuscriptGateError, match=rf"{gate} cannot pass before"):
        evaluate_manuscript_gates(tmp_project.paths)


@pytest.mark.parametrize(
    "artifacts",
    [
        [],
        ["not-an-object"],
        [{"artifact_id": "a", "path": "a", "sha256": "0" * 64, "extra": "x"}],
        [{"artifact_id": "", "path": "a", "sha256": "0" * 64}],
        [
            {"artifact_id": "same", "path": "a", "sha256": "0" * 64},
            {"artifact_id": "same", "path": "b", "sha256": "0" * 64},
        ],
    ],
)
def test_s7_artifact_inventory_requires_exact_schema_and_unique_nonblank_ids(
    tmp_project, artifacts: object
) -> None:
    for gate in ("S4", "S5", "S6"):
        tmp_project.write_gate(gate, "passed")
    _write_gate(
        tmp_project.root,
        "S7",
        {"gate": "S7", "status": "passed", "artifacts": artifacts},
    )

    with pytest.raises(ManuscriptGateError, match="S7 requires frozen artifact checksums"):
        assert_results_authorized(tmp_project.paths)


@pytest.mark.parametrize("relative_path", ["../escape.txt", "/tmp/escape.txt"])
def test_s7_artifacts_cannot_escape_repository(tmp_project, relative_path: str) -> None:
    for gate in ("S4", "S5", "S6"):
        tmp_project.write_gate(gate, "passed")
    _write_gate(
        tmp_project.root,
        "S7",
        {
            "gate": "S7",
            "status": "passed",
            "artifacts": [{"artifact_id": "escape", "path": relative_path, "sha256": "0" * 64}],
        },
    )

    with pytest.raises(ManuscriptGateError, match="escapes repository root"):
        assert_results_authorized(tmp_project.paths)


def test_s7_artifacts_reject_symlinks(tmp_project, tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-artifact.txt"
    outside.write_text("outside\n", encoding="utf-8")
    linked = tmp_project.root / "outputs" / "frozen" / "linked.txt"
    linked.parent.mkdir(parents=True)
    linked.symlink_to(outside)
    for gate in ("S4", "S5", "S6"):
        tmp_project.write_gate(gate, "passed")
    _write_gate(
        tmp_project.root,
        "S7",
        {
            "gate": "S7",
            "status": "passed",
            "artifacts": [
                {
                    "artifact_id": "linked",
                    "path": "outputs/frozen/linked.txt",
                    "sha256": sha256(outside.read_bytes()).hexdigest(),
                }
            ],
        },
    )

    with pytest.raises(ManuscriptGateError, match="must not use symlinks"):
        assert_results_authorized(tmp_project.paths)


def test_s7_artifact_checksum_must_match(tmp_project) -> None:
    artifact = _write_authorized_gates(tmp_project.root)
    artifact.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(
        ManuscriptGateError, match="S7 artifact checksum mismatch: primary-estimate"
    ):
        assert_results_authorized(tmp_project.paths)


def test_s7_rejects_duplicate_normalized_paths_before_file_access(tmp_project) -> None:
    for gate in ("S4", "S5", "S6"):
        tmp_project.write_gate(gate, "passed")
    _write_gate(
        tmp_project.root,
        "S7",
        {
            "gate": "S7",
            "status": "passed",
            "artifacts": [
                {"artifact_id": "a", "path": "outputs/frozen/missing.json", "sha256": "0" * 64},
                {"artifact_id": "b", "path": "outputs/frozen/./missing.json", "sha256": "1" * 64},
            ],
        },
    )

    with pytest.raises(ManuscriptGateError, match="S7 artifact paths must be unique"):
        assert_results_authorized(tmp_project.paths)


@pytest.mark.parametrize("raw_path", ["   ", " artifact.txt", "artifact.txt "])
def test_s7_rejects_blank_or_untrimmed_paths_even_when_file_exists(
    tmp_project, raw_path: str
) -> None:
    source = tmp_project.root / raw_path
    source.write_text("artifact\n", encoding="utf-8")
    for gate in ("S4", "S5", "S6"):
        tmp_project.write_gate(gate, "passed")
    _write_gate(
        tmp_project.root,
        "S7",
        {
            "gate": "S7",
            "status": "passed",
            "artifacts": [
                {
                    "artifact_id": "bad-path",
                    "path": raw_path,
                    "sha256": sha256(source.read_bytes()).hexdigest(),
                }
            ],
        },
    )

    with pytest.raises(ManuscriptGateError, match="S7 requires frozen artifact checksums"):
        assert_results_authorized(tmp_project.paths)


def test_valid_s7_authorizes_results_and_report_is_deterministic(tmp_project) -> None:
    _write_authorized_gates(tmp_project.root)

    assert_results_authorized(tmp_project.paths)
    report = evaluate_manuscript_gates(tmp_project.paths)

    assert report.passed == ("S4", "S5", "S6", "S7")
    assert report.missing == ("S8", "M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7")
    assert report.open == ()
    assert report.blocked == ()
    assert report.results_authorized is True


def test_explicit_manuscript_open_and_blocked_states_are_preserved(tmp_project) -> None:
    _write_manuscript_gate(tmp_project.root, "M0", {"gate": "M0", "status": "open"})
    _write_manuscript_gate(tmp_project.root, "M1", {"gate": "M1", "status": "blocked"})
    _empty_ledgers(tmp_project.root)

    report = evaluate_manuscript_gates(tmp_project.paths)

    assert report.open == ("M0",)
    assert report.blocked == ("M1",)
    assert report.missing == ("S4", "S5", "S6", "S7", "S8", "M2", "M3", "M4", "M5", "M6", "M7")


def test_valid_m0_requires_canonical_contract_artifacts(tmp_project) -> None:
    _write_m0(tmp_project.root)

    report = evaluate_manuscript_gates(tmp_project.paths)

    assert report.passed == ("M0",)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing-artifacts", "M0 passed record fields are invalid"),
        ("wrong-acceptance", "M0 acceptance does not match contract"),
        ("blank-approval", "M0 approval is invalid"),
        ("wrong-canonical-path", "M0 artifact path does not match canonical contract"),
    ],
)
def test_m0_passed_evidence_is_exact_and_human_approved(
    tmp_project, mutation: str, message: str
) -> None:
    _write_m0(tmp_project.root)
    path = tmp_project.root / "outputs/manuscript/control/gates/M0.json"
    payload = json.loads(path.read_text())
    if mutation == "missing-artifacts":
        del payload["artifacts"]
    elif mutation == "wrong-acceptance":
        payload["acceptance"][0]["criterion"] = "close enough"
    elif mutation == "blank-approval":
        payload["approval"]["human"] = "   "
    else:
        payload["artifacts"][0]["path"] = "config/manuscript/style_contract.yml"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ManuscriptGateError, match=message):
        evaluate_manuscript_gates(tmp_project.paths)


def test_m1_pass_requires_s7_and_ledger_reconciliation(tmp_project) -> None:
    _write_machine_passable_state(tmp_project.root)
    control = tmp_project.root / "outputs/manuscript/control"
    frame = pd.read_csv(control / "number_ledger.csv", dtype=str)
    row = {column: "value" for column in frame.columns}
    row.update(
        {
            "number_id": "N-001",
            "artifact_id": "not-in-s7",
            "checksum": "sha256:" + "0" * 64,
            "result_status": "prespecified",
        }
    )
    pd.DataFrame([row]).to_csv(control / "number_ledger.csv", index=False)

    with pytest.raises(
        ManuscriptGateError, match="number ledger artifact not-in-s7 is absent from S7"
    ):
        evaluate_manuscript_gates(tmp_project.paths)


def test_m1_artifact_ids_must_all_occur_in_s7_inventory(tmp_project) -> None:
    _write_machine_passable_state(tmp_project.root)
    path = tmp_project.root / "outputs/manuscript/control/gates/M1.json"
    payload = json.loads(path.read_text())
    payload["artifacts"][0]["artifact_id"] = "not-in-s7"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ManuscriptGateError, match="M1 artifact not-in-s7 is absent from S7"):
        evaluate_manuscript_gates(tmp_project.paths)


def test_m1_artifact_path_and_digest_must_equal_s7_entry(tmp_project) -> None:
    _write_machine_passable_state(tmp_project.root)
    replacement = tmp_project.root / "outputs/frozen/replacement.csv"
    replacement.write_text("replacement\n", encoding="utf-8")
    path = tmp_project.root / "outputs/manuscript/control/gates/M1.json"
    payload = json.loads(path.read_text())
    payload["artifacts"][0]["path"] = "outputs/frozen/replacement.csv"
    payload["artifacts"][0]["sha256"] = sha256(replacement.read_bytes()).hexdigest()
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        ManuscriptGateError, match="M1 artifact m1-1 does not match S7 path and digest"
    ):
        evaluate_manuscript_gates(tmp_project.paths)


def test_m1_artifact_digest_must_equal_s7_entry(tmp_project) -> None:
    _write_machine_passable_state(tmp_project.root)
    path = tmp_project.root / "outputs/manuscript/control/gates/M1.json"
    payload = json.loads(path.read_text())
    payload["artifacts"][0]["sha256"] = "0" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        ManuscriptGateError, match="M1 artifact m1-1 does not match S7 path and digest"
    ):
        evaluate_manuscript_gates(tmp_project.paths)


def test_m1_requires_at_least_one_number_record(tmp_project) -> None:
    _write_machine_passable_state(tmp_project.root)
    control = tmp_project.root / "outputs/manuscript/control"
    frame = pd.read_csv(control / "number_ledger.csv")
    frame.iloc[0:0].to_csv(control / "number_ledger.csv", index=False)

    with pytest.raises(ManuscriptGateError, match="M1 requires at least one number record"):
        evaluate_manuscript_gates(tmp_project.paths)


def test_m1_number_checksum_must_equal_s7_digest(tmp_project) -> None:
    _write_machine_passable_state(tmp_project.root)
    control = tmp_project.root / "outputs/manuscript/control"
    frame = pd.read_csv(control / "number_ledger.csv", dtype=str)
    frame.loc[0, "checksum"] = "sha256:" + "0" * 64
    frame.to_csv(control / "number_ledger.csv", index=False)

    with pytest.raises(
        ManuscriptGateError, match="number ledger artifact m1-1 checksum does not match S7"
    ):
        evaluate_manuscript_gates(tmp_project.paths)


def test_m1_fully_matching_artifact_and_number_linkage_passes(tmp_project) -> None:
    _write_machine_passable_state(tmp_project.root)

    report = evaluate_manuscript_gates(tmp_project.paths)

    assert "M1" in report.passed


def test_m2_passed_fails_until_task_validator_exists(tmp_project) -> None:
    _empty_ledgers(tmp_project.root)
    tmp_project.write_gate("S4", "passed")
    _write_manuscript_gate(
        tmp_project.root,
        "M2",
        {"gate": "M2", "status": "passed", "artifacts": [], "acceptance": [], "approval": {}},
    )

    with pytest.raises(ManuscriptGateError, match="M2 validator is unavailable"):
        evaluate_manuscript_gates(tmp_project.paths)


def test_later_manuscript_passed_record_requires_dependencies_first(tmp_project) -> None:
    _empty_ledgers(tmp_project.root)
    _write_manuscript_gate(
        tmp_project.root,
        "M3",
        {"gate": "M3", "status": "passed", "artifacts": [], "acceptance": [], "approval": {}},
    )

    with pytest.raises(ManuscriptGateError, match="M3 cannot pass before M0, M1, M2"):
        evaluate_manuscript_gates(tmp_project.paths)


def test_any_control_ledger_activates_complete_ledger_validation(tmp_project) -> None:
    control = _empty_ledgers(tmp_project.root)
    for filename in ("number_ledger.csv", "ai_use_ledger.csv", "issue_ledger.csv"):
        (control / filename).unlink()

    with pytest.raises(ManuscriptGateError, match="number_ledger.csv is required"):
        evaluate_manuscript_gates(tmp_project.paths)


def test_any_m1_to_m7_record_activates_complete_ledger_validation(tmp_project) -> None:
    _write_manuscript_gate(tmp_project.root, "M2", {"gate": "M2", "status": "open"})

    with pytest.raises(ManuscriptGateError, match="claim_ledger.csv is required"):
        evaluate_manuscript_gates(tmp_project.paths)


def test_cli_returns_nonzero_for_open_required_gate(tmp_project, monkeypatch) -> None:
    monkeypatch.chdir(tmp_project.root)

    result = CliRunner().invoke(app, ["manuscript", "gates", "--check"])

    assert result.exit_code == 1
    assert "Manuscript gates failed" in result.output


def test_cli_requires_check_flag(tmp_project, monkeypatch) -> None:
    monkeypatch.chdir(tmp_project.root)

    result = CliRunner().invoke(app, ["manuscript", "gates"])

    assert result.exit_code != 0
    assert "gate validation requires --check" in result.output


def test_cli_prints_deterministic_valid_report(tmp_project, monkeypatch) -> None:
    _write_machine_passable_state(tmp_project.root)
    monkeypatch.chdir(tmp_project.root)

    result = CliRunner().invoke(app, ["manuscript", "gates", "--check"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "blocked": [],
        "missing": ["S8", "M2", "M3", "M4", "M5", "M6", "M7"],
        "open": [],
        "passed": ["S4", "S5", "S6", "S7", "M0", "M1"],
        "results_authorized": True,
    }


def test_cli_fails_for_open_critical_issue(tmp_project, monkeypatch) -> None:
    _write_machine_passable_state(tmp_project.root)
    control = tmp_project.root / "outputs" / "manuscript" / "control"
    pd.DataFrame(
        [
            {
                "issue_id": "I-001",
                "severity": "critical",
                "gate": "M5",
                "description": "Numerical discrepancy",
                "evidence": "",
                "owner": "",
                "status": "open",
                "resolution": "",
            }
        ]
    ).to_csv(control / "issue_ledger.csv", index=False)
    monkeypatch.chdir(tmp_project.root)

    result = CliRunner().invoke(app, ["manuscript", "gates", "--check"])

    assert result.exit_code == 1
    assert "open critical manuscript issue" in result.output


def test_cli_fails_for_open_important_issue(tmp_project, monkeypatch) -> None:
    _write_machine_passable_state(tmp_project.root)
    control = tmp_project.root / "outputs/manuscript/control"
    pd.DataFrame(
        [
            {
                "issue_id": "I-002",
                "severity": "important",
                "gate": "M5",
                "description": "Traceability discrepancy",
                "evidence": "",
                "owner": "",
                "status": "open",
                "resolution": "",
            }
        ]
    ).to_csv(control / "issue_ledger.csv", index=False)
    monkeypatch.chdir(tmp_project.root)

    result = CliRunner().invoke(app, ["manuscript", "gates", "--check"])

    assert result.exit_code == 1
    assert "open important manuscript issue" in result.output


def test_cli_normalizes_malformed_contract_wrapper(tmp_project, monkeypatch) -> None:
    (tmp_project.root / "config/manuscript/agents.yml").write_text("{}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_project.root)

    result = CliRunner().invoke(app, ["manuscript", "gates", "--check"])

    assert result.exit_code == 1
    assert "Manuscript gates failed: agents.yml must contain an agents mapping" in result.output
