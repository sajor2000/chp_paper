"""Role-scoped, disclosure-safe manuscript agent handoff manifests."""

from __future__ import annotations

import json
from pathlib import Path

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.manuscript.contracts import load_manuscript_contracts
from chicagohealthmap.manuscript.gates import ManuscriptGateError, assert_results_authorized


class HandoffError(ValueError):
    """Raised when a manuscript handoff is unauthorized or unsafe."""


RESULT_ROLES = {
    "results_agent",
    "case_study_1_agent",
    "case_study_2_agent",
    "discussion_policy_agent",
}


def _handoff_output_dir(paths: ProjectPaths) -> Path:
    output = paths.root / "outputs" / "manuscript" / "control" / "handoffs"
    cursor = paths.root
    for part in output.relative_to(paths.root).parts:
        cursor /= part
        if cursor.is_symlink():
            raise HandoffError("handoff output path must not use symlinks")
    output.mkdir(parents=True, exist_ok=True)
    return output


def build_agent_handoff(paths: ProjectPaths, role: str) -> Path:
    """Build one role-scoped handoff manifest without protected local paths."""
    contracts = load_manuscript_contracts(paths.root)
    if role not in contracts.agents:
        raise HandoffError(f"unknown manuscript role: {role}")
    if role in RESULT_ROLES:
        try:
            assert_results_authorized(paths)
        except ManuscriptGateError:
            raise HandoffError(f"{role.replace('_', '-')} handoff requires S7") from None

    role_contract = contracts.agents[role]
    payload = {
        "role": role,
        "responsibility": role_contract.responsibility,
        "permitted_inputs": role_contract.permitted_inputs,
        "permitted_outputs": role_contract.permitted_outputs,
        "prohibited_actions": role_contract.prohibited_actions,
        "human_approval_required": role_contract.human_approval_required,
        "report_contract": {
            "status_values": ["DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"],
            "must_include": [
                "artifact identifiers used",
                "verification commands and outcomes",
                "human decisions required",
                "unresolved evidence gaps",
            ],
        },
    }
    path = _handoff_output_dir(paths) / f"{role}.json"
    if path.is_symlink():
        raise HandoffError("handoff destination must not be a symlink")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
