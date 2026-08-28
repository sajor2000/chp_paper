import json

import pytest

from chicagohealthmap.manuscript.handoffs import HandoffError, build_agent_handoff


def test_results_agent_is_blocked_before_s7(tmp_project) -> None:
    with pytest.raises(HandoffError, match="results-agent handoff requires S7"):
        build_agent_handoff(tmp_project.paths, "results_agent")


def test_non_result_handoff_contains_no_absolute_or_protected_paths(tmp_project) -> None:
    path = build_agent_handoff(tmp_project.paths, "methods_reporting_agent")
    payload = json.loads(path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload)

    assert payload["role"] == "methods_reporting_agent"
    assert "report_contract" in payload
    assert str(tmp_project.root) not in serialized
    assert "/Users/" not in serialized
    assert "sources/first_party/capricorn/snapshots" not in serialized


def test_unknown_role_is_rejected(tmp_project) -> None:
    with pytest.raises(HandoffError, match="unknown manuscript role"):
        build_agent_handoff(tmp_project.paths, "not_a_role")


def test_handoff_writer_rejects_symlinked_output_parent(tmp_project, tmp_path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    control = tmp_project.root / "outputs" / "manuscript" / "control"
    control.mkdir(parents=True)
    (control / "handoffs").symlink_to(outside)

    with pytest.raises(HandoffError, match="must not use symlinks"):
        build_agent_handoff(tmp_project.paths, "methods_reporting_agent")
