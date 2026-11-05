"""Fail-closed manuscript-control audits for JAMA Health Forum preparation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import csv
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


@dataclass(frozen=True, slots=True)
class CitationAuditReport:
    """Summary of manuscript citation and companion-boundary checks."""

    references: int
    citations: int
    claims: int
    auc_pointers: int


_PLACEHOLDER_TOKENS = ("TBD", "TODO", "FIXME")
_PROTECTED_PATHS = (
    "/users/",
    "sources/first_party/capricorn/snapshots",
)
_UNQUALIFIED_PREVALENCE = re.compile(
    r"\b(?:hypertension|diabetes|copd|disease|condition)\s+prevalence\b",
    re.IGNORECASE,
)
_CITATION = re.compile(r"<sup>([0-9,\-\u2013\s]+)</sup>")
_REFERENCE = re.compile(r"^(\d+)\.\s+(.+)$", re.MULTILINE)
_IDENTIFIER_PATTERNS = {
    "doi": re.compile(r"\bdoi:\s*([^\s]+)", re.IGNORECASE),
    "pmid": re.compile(r"\bPMID:\s*(\d+)", re.IGNORECASE),
    "url": re.compile(r"https?://[^\s]+", re.IGNORECASE),
}


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


def _expand_citation_group(group: str) -> list[int]:
    values: list[int] = []
    for item in re.split(r"\s*,\s*", group.strip()):
        normalized = item.replace("\u2013", "-")
        if "-" in normalized:
            start_text, end_text = normalized.split("-", maxsplit=1)
            start, end = int(start_text), int(end_text)
            if end < start:
                raise ManuscriptAuditError(f"descending citation range: {item}")
            values.extend(range(start, end + 1))
        elif normalized:
            values.append(int(normalized))
    return values


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def audit_manuscript_citations(
    main_path: Path,
    companion_path: Path,
    references_path: Path,
    claims_path: Path,
) -> CitationAuditReport:
    """Fail closed on citation order, evidence ledgers, and AUC placement."""
    main_text = main_path.read_text(encoding="utf-8")
    companion_text = companion_path.read_text(encoding="utf-8")
    body, separator, references_and_trailing = main_text.partition("# References")
    if not separator:
        raise ManuscriptAuditError("main manuscript has no References section")
    references_text, trailing_separator, trailing_text = references_and_trailing.partition(
        "# Table Legends"
    )
    if not trailing_separator:
        raise ManuscriptAuditError("main manuscript has no Table Legends section")
    review_text = body + trailing_separator + trailing_text

    citation_numbers = [
        number
        for match in _CITATION.finditer(body)
        for number in _expand_citation_group(match.group(1))
    ]
    references = {
        int(match.group(1)): match.group(2).strip()
        for match in _REFERENCE.finditer(references_text)
    }
    if sorted(references) != list(range(1, len(references) + 1)):
        raise ManuscriptAuditError("reference list is not consecutively numbered")
    undefined = sorted(set(citation_numbers) - set(references))
    if undefined:
        raise ManuscriptAuditError(f"undefined references: {undefined}")
    uncited = sorted(set(references) - set(citation_numbers))
    if uncited:
        raise ManuscriptAuditError(f"uncited references: {uncited}")
    first_appearance = list(dict.fromkeys(citation_numbers))
    expected_order = list(range(1, len(references) + 1))
    if first_appearance != expected_order:
        raise ManuscriptAuditError(
            f"references are not numbered by first appearance: {first_appearance}"
        )

    for identifier_name, pattern in _IDENTIFIER_PATTERNS.items():
        seen: dict[str, int] = {}
        for reference_number, reference_text in references.items():
            match = pattern.search(reference_text)
            if not match:
                continue
            value = (match.group(1) if match.lastindex else match.group(0)).rstrip(".,").casefold()
            if value in seen:
                raise ManuscriptAuditError(
                    f"duplicate {identifier_name}: references {seen[value]} and {reference_number}"
                )
            seen[value] = reference_number

    reference_rows = _read_csv_rows(references_path)
    ledger_numbers = {int(row["reference_number"]) for row in reference_rows}
    if ledger_numbers != set(references):
        raise ManuscriptAuditError("reference verification ledger does not match References")
    claim_rows = _read_csv_rows(claims_path)
    claim_ids = [row.get("claim_id", "") for row in claim_rows]
    if not claim_ids or len(set(claim_ids)) != len(claim_ids):
        raise ManuscriptAuditError("claim evidence map has missing or duplicate claim IDs")
    if any(not row.get("verification_status", "").startswith("verified") for row in claim_rows):
        raise ManuscriptAuditError("claim evidence map contains an unverified claim")
    auc_claims = [row for row in claim_rows if row.get("claim_id") == "M09"]
    if len(auc_claims) != 1 or "companion" not in auc_claims[0].get(
        "manuscript_location", ""
    ).casefold():
        raise ManuscriptAuditError("AUC claim must be assigned to the statistician companion")

    auc_pointers = len(re.findall(r"\bAUC\b", review_text))
    if auc_pointers != 1:
        raise ManuscriptAuditError("main manuscript must contain exactly one nonnumeric AUC pointer")
    auc_context = next(
        line for line in review_text.splitlines() if re.search(r"\bAUC\b", line)
    )
    if re.search(r"\b0\.\d+\b|95% CI", auc_context):
        raise ManuscriptAuditError("main manuscript AUC pointer must be nonnumeric")
    if "RMD_chm_paper_r_Ashley.html" not in auc_context:
        raise ManuscriptAuditError("main manuscript AUC pointer must name the companion HTML")
    if "# Statistical Analysis Module 5: Exploratory Area-Label AUC" not in companion_text:
        raise ManuscriptAuditError("statistician companion is missing the AUC analysis")
    if "isFALSE(manifest$results_authorized)" not in main_text or "isFALSE(manifest$results_authorized)" not in companion_text:
        raise ManuscriptAuditError("results authorization must remain false in both review files")

    return CitationAuditReport(
        references=len(references),
        citations=len(citation_numbers),
        claims=len(claim_rows),
        auc_pointers=auc_pointers,
    )
