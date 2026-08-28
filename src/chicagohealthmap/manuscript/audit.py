"""Fail-closed manuscript-control audits for JAMA Health Forum preparation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.manuscript.contracts import load_manuscript_contracts
from chicagohealthmap.manuscript.gates import evaluate_manuscript_gates
from chicagohealthmap.manuscript.ledgers import verify_ledgers
from chicagohealthmap.manuscript.models import ManuscriptContracts


class ManuscriptAuditError(ValueError):
    """Raised when a manuscript artifact violates an audit rule."""


@dataclass(frozen=True, slots=True)
class AuditReport:
    """Summary of deterministic manuscript-control checks."""

    checks: int
    failures: tuple[str, ...]


_PLACEHOLDER_TOKENS = ("TBD", "TODO", "FIXME")
_PROTECTED_PATHS = (
    "/users/",
    "sources/first_party/capricorn/snapshots",
)
_UNQUALIFIED_PREVALENCE = re.compile(
    r"\b(?:hypertension|diabetes|copd|disease|condition)\s+prevalence\b",
    re.IGNORECASE,
)


def audit_text(text: str, contracts: ManuscriptContracts) -> None:
    """Reject unsafe manuscript-control prose before it reaches drafting."""
    lowered = text.casefold()
    for protected in _PROTECTED_PATHS:
        if protected in lowered:
            raise ManuscriptAuditError("protected path")
    if _UNQUALIFIED_PREVALENCE.search(text):
        raise ManuscriptAuditError("unqualified prevalence")
    for verb in contracts.style.prohibited_observational_verbs:
        if re.search(rf"\b{re.escape(verb.casefold())}\b", lowered):
            raise ManuscriptAuditError(f"prohibited observational verb: {verb}")
    for term in contracts.style.unsupported_superlatives:
        if re.search(rf"\b{re.escape(term.casefold())}\b", lowered):
            raise ManuscriptAuditError(
                f"unsupported superlative requires claim-ledger approval: {term}"
            )
    for token in _PLACEHOLDER_TOKENS:
        if re.search(rf"\b{re.escape(token.casefold())}\b", lowered):
            raise ManuscriptAuditError(f"placeholder token: {token}")


def _assert_recent_journal_check(control: Path, contracts: ManuscriptContracts) -> None:
    submission_target = control / "submission_target_date.txt"
    if not submission_target.is_file():
        return
    try:
        target = date.fromisoformat(submission_target.read_text(encoding="utf-8").strip())
    except ValueError as error:
        raise ManuscriptAuditError("submission target date must use YYYY-MM-DD") from error
    age_at_submission = (target - contracts.journal.accessed).days
    if (
        age_at_submission < 0
        or age_at_submission > contracts.journal.revalidate_days_before_submission
    ):
        raise ManuscriptAuditError("official journal audit is not within 30 days of submission")


def audit_manuscript_control(paths: ProjectPaths) -> AuditReport:
    """Audit generated manuscript-control artifacts without authorizing results."""
    contracts = load_manuscript_contracts(paths.root)
    report = evaluate_manuscript_gates(paths)
    if "M0" in report.blocked:
        raise ManuscriptAuditError("M0 authority gate is blocked")

    control = paths.root / "outputs" / "manuscript" / "control"
    _assert_recent_journal_check(control, contracts)
    ledger_report = verify_ledgers(control, contracts)
    if ledger_report.open_critical_issues:
        raise ManuscriptAuditError("open critical manuscript issue")
    if ledger_report.open_important_issues:
        raise ManuscriptAuditError("open important manuscript issue")

    failures: list[str] = []
    checked = 0
    for path in sorted(control.glob("*.md")):
        checked += 1
        try:
            audit_text(path.read_text(encoding="utf-8"), contracts)
        except ManuscriptAuditError as error:
            failures.append(f"{path.name}: {error}")
    if failures:
        raise ManuscriptAuditError("; ".join(failures))
    return AuditReport(checks=checked, failures=())
