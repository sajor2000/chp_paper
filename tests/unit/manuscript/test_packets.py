from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from chicagohealthmap.manuscript.packets import (
    CASE_HEADINGS,
    ManuscriptPacketError,
    build_control_packets,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _approve_s5(tmp_project, *, cases: list[dict[str, object]] | None = None) -> None:
    tmp_project.write_gate("S4", "passed")
    tmp_project.write_gate("S5", "passed")
    sap = tmp_project.root / "docs" / "analysis" / "signed_sap.md"
    sap.parent.mkdir(parents=True, exist_ok=True)
    sap.write_text("# Signed statistical analysis plan\n", encoding="utf-8")
    selected = cases or [
        {
            "order": 1,
            "case_id": "selected-alpha",
            "display_name": "Selected Alpha",
        },
        {
            "order": 2,
            "case_id": "selected-beta",
            "display_name": "Selected Beta",
        },
    ]
    _write_json(
        tmp_project.root / "outputs" / "governance" / "case_selection.json",
        {
            "record_type": "outcome_blinded_case_selection",
            "gate": "S5",
            "status": "approved",
            "outcome_blinded": True,
            "cases": selected,
            "approval": {
                "human": "Selection Approver",
                "date": "2026-07-14",
                "decision": "approved",
            },
        },
    )
    _write_json(
        tmp_project.root / "outputs" / "governance" / "signed_sap.json",
        {
            "record_type": "signed_statistical_analysis_plan",
            "status": "signed",
            "version": "1.0.0",
            "path": "docs/analysis/signed_sap.md",
            "sha256": sha256(sap.read_bytes()).hexdigest(),
            "case_ids": [case["case_id"] for case in selected],
            "approval": {
                "human": "SAP Approver",
                "date": "2026-07-14",
                "decision": "approved",
            },
        },
    )


def _case_paths(paths: tuple[Path, ...]) -> list[Path]:
    return [path for path in paths if path.name.startswith("case_")]


def test_case_packets_are_mirrored_and_provisional_before_s5(tmp_project) -> None:
    case_paths = _case_paths(build_control_packets(tmp_project.paths))

    assert [path.name for path in case_paths] == ["case_1.md", "case_2.md"]
    bodies = [path.read_text(encoding="utf-8") for path in case_paths]
    headings = [line for line in bodies[0].splitlines() if line.startswith("## ")]
    assert headings == [f"## {heading}" for heading in CASE_HEADINGS]
    assert headings == [line for line in bodies[1].splitlines() if line.startswith("## ")]
    assert all("PROVISIONAL — PENDING S5" in body for body in bodies)
    assert "Cardiometabolic hypertension and diabetes" in bodies[0]
    assert "Respiratory COPD" in bodies[1]


def test_s5_uses_only_blinded_approval_names_and_order(tmp_project) -> None:
    _approve_s5(tmp_project)

    bodies = [
        path.read_text(encoding="utf-8")
        for path in _case_paths(build_control_packets(tmp_project.paths))
    ]

    assert "# Case Study 1: Selected Alpha" in bodies[0]
    assert "# Case Study 2: Selected Beta" in bodies[1]
    assert all("SELECTED AT S5 — OUTCOME BLINDED" in body for body in bodies)
    assert all("Cardiometabolic" not in body and "COPD" not in body for body in bodies)


@pytest.mark.parametrize(
    ("missing", "message"),
    [
        ("case_selection.json", "case-selection record is required"),
        ("signed_sap.json", "signed SAP record is required"),
    ],
)
def test_s5_fails_closed_when_authority_record_is_missing(
    tmp_project, missing: str, message: str
) -> None:
    _approve_s5(tmp_project)
    (tmp_project.root / "outputs" / "governance" / missing).unlink()

    with pytest.raises(ManuscriptPacketError, match=message):
        build_control_packets(tmp_project.paths)


def test_s5_rejects_malformed_selection_before_writing(tmp_project) -> None:
    _approve_s5(tmp_project)
    record = tmp_project.root / "outputs" / "governance" / "case_selection.json"
    record.write_text("{", encoding="utf-8")

    with pytest.raises(ManuscriptPacketError, match="not valid JSON"):
        build_control_packets(tmp_project.paths)

    assert not (tmp_project.root / "outputs" / "manuscript" / "control").exists()


def test_s5_rejects_selection_record_under_symlinked_parent(tmp_project, tmp_path: Path) -> None:
    _approve_s5(tmp_project)
    outside = tmp_path / "outside"
    outside.mkdir()
    governance = tmp_project.root / "outputs" / "governance"
    governance.rename(outside / "governance")
    governance.symlink_to(outside / "governance", target_is_directory=True)

    with pytest.raises(ManuscriptPacketError, match="must not use symlinks"):
        build_control_packets(tmp_project.paths)


def test_s5_rejects_noncanonical_approval_date(tmp_project) -> None:
    _approve_s5(tmp_project)
    record = tmp_project.root / "outputs" / "governance" / "case_selection.json"
    payload = json.loads(record.read_text(encoding="utf-8"))
    payload["approval"]["date"] = "20260714"
    _write_json(record, payload)

    with pytest.raises(ManuscriptPacketError, match="approval date is invalid"):
        build_control_packets(tmp_project.paths)


def test_s5_rejects_selection_not_covered_by_signed_sap(tmp_project) -> None:
    _approve_s5(tmp_project)
    record = tmp_project.root / "outputs" / "governance" / "signed_sap.json"
    payload = json.loads(record.read_text(encoding="utf-8"))
    payload["case_ids"] = ["selected-alpha", "different-case"]
    _write_json(record, payload)

    with pytest.raises(ManuscriptPacketError, match="case order does not match"):
        build_control_packets(tmp_project.paths)


def test_s5_rejects_unsigned_or_changed_sap(tmp_project) -> None:
    _approve_s5(tmp_project)
    sap = tmp_project.root / "docs" / "analysis" / "signed_sap.md"
    sap.write_text("changed after signature\n", encoding="utf-8")

    with pytest.raises(ManuscriptPacketError, match="checksum does not match"):
        build_control_packets(tmp_project.paths)


@pytest.mark.parametrize(
    "display_name",
    [
        "Outcome improved",
        "Candidate p = 0.01",
        "Effect size candidate",
        "Candidate correlation r = 0.75",
        "TBD candidate",
        "Candidate estimate 0.01",
    ],
)
def test_pre_s7_rejects_suggestive_selected_case_names(tmp_project, display_name: str) -> None:
    _approve_s5(
        tmp_project,
        cases=[
            {"order": 1, "case_id": "alpha", "display_name": display_name},
            {"order": 2, "case_id": "beta", "display_name": "Neutral Beta"},
        ],
    )

    with pytest.raises(ManuscriptPacketError, match="result leakage"):
        build_control_packets(tmp_project.paths)


def test_pre_s7_packets_contain_no_result_language_or_values(tmp_project) -> None:
    forbidden = ("## Results", "effect size", "p =", "tbd", "placeholder")

    for path in _case_paths(build_control_packets(tmp_project.paths)):
        body = path.read_text(encoding="utf-8").lower()
        assert not any(term.lower() in body for term in forbidden)
        assert "associated with" not in body


def test_internal_pre_s7_leakage_guard_rejects_future_packet_regression(
    tmp_project, monkeypatch
) -> None:
    from chicagohealthmap.manuscript import packets

    monkeypatch.setattr(packets, "_SECTION_TEXT", "Estimated value: 0.12")

    with pytest.raises(ManuscriptPacketError, match="pre-S7 packet contains"):
        build_control_packets(tmp_project.paths)


def test_rerun_is_byte_deterministic_and_returns_fixed_order(tmp_project) -> None:
    first = build_control_packets(tmp_project.paths)
    first_bytes = {path.name: path.read_bytes() for path in first}
    second = build_control_packets(tmp_project.paths)

    assert [path.name for path in first] == ["outline.md", "case_1.md", "case_2.md"]
    assert [path.name for path in second] == [path.name for path in first]
    assert {path.name: path.read_bytes() for path in second} == first_bytes


def test_packet_writer_rejects_symlink_output_directory(tmp_project, tmp_path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    manuscript = tmp_project.root / "outputs" / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "control").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ManuscriptPacketError, match="must not use symlinks"):
        build_control_packets(tmp_project.paths)

    assert list(outside.iterdir()) == []


def test_packet_writer_rejects_symlink_destination(tmp_project, tmp_path) -> None:
    target = tmp_path / "outside.md"
    target.write_text("preserve\n", encoding="utf-8")
    control = tmp_project.root / "outputs" / "manuscript" / "control"
    control.mkdir(parents=True)
    (control / "case_1.md").symlink_to(target)

    with pytest.raises(ManuscriptPacketError, match="must not overwrite symlinks"):
        build_control_packets(tmp_project.paths)

    assert target.read_text(encoding="utf-8") == "preserve\n"


def test_human_templates_freeze_budgets_displays_and_language(contracts) -> None:
    root = Path(__file__).resolve().parents[3]
    outline = (root / "docs" / "manuscript" / "outline.md").read_text(encoding="utf-8")
    template = (root / "docs" / "manuscript" / "case_study_template.md").read_text(encoding="utf-8")
    lexicon = (root / "docs" / "manuscript" / "claim_language_lexicon.md").read_text(
        encoding="utf-8"
    )

    for budget in ("250-300", "850-950"):
        assert budget in outline
    for display in ("Table 1", "Figure 1", "Figure 2", "Figure 3", "Table 2"):
        assert display in outline
    assert "Supplement" in outline
    assert [line[3:] for line in template.splitlines() if line.startswith("## ")] == list(
        CASE_HEADINGS
    )
    assert contracts.style.required_measure_phrase in lexicon
    assert contracts.style.policy_boundary in lexicon
    for term in contracts.style.prohibited_observational_verbs:
        assert f"`{term}`" in lexicon
    for term in contracts.style.unsupported_superlatives:
        assert f"`{term}`" in lexicon


def test_outline_reconciles_section_envelopes_with_word_reserve(contracts) -> None:
    root = Path(__file__).resolve().parents[3]
    outline = (root / "docs" / "manuscript" / "outline.md").read_text(encoding="utf-8")

    assert "planning envelopes" in outline
    assert "must be edited to <=2900 words" in outline
    assert "100 words for final edits" in outline
