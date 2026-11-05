"""Fail-closed manuscript-control audits for JAMA Health Forum preparation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import csv
import html
import json
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
    companion_references: int
    companion_citations: int


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
_REFERENCE = re.compile(r"^(\d+)\.\s+(.+)$")
_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_EQUATION_DIV = re.compile(
    r'<div\s+class=["\']equation["\'][^>]*>.*?</div>',
    re.DOTALL | re.IGNORECASE,
)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_DOI = re.compile(
    r"(?:\bdoi:\s*|https?://(?:dx\.)?doi\.org/)(10\.\d{4,9}/[^\s<]+)",
    re.IGNORECASE,
)
_PMID = re.compile(r"\bPMID:\s*(\d+)", re.IGNORECASE)
_URL = re.compile(r"https?://[^\s<]+", re.IGNORECASE)
_ALLOWED_AUC_POINTER = (
    "Exploratory AUC analyses are reported only in the statistician review companion, "
    "`RMD_chm_paper_r_Ashley.html`."
)
_FORBIDDEN_MAIN_AUC = re.compile(
    r"\bAUC\b|\bAUROC\b|\bROC\b|area\s+under\s+(?:the\s+)?(?:receiver\s+operating\s+characteristic\s+)?curve|"
    r"\bC[- ]statistic\b|auc_value|supplement_descriptive_complementarity_methods|\b0\.(?:939|813)\b",
    re.IGNORECASE,
)
_REFERENCE_LEDGER_FIELDS = (
    "reference_number",
    "stable_identifier",
    "identifier_type",
    "verification_source",
    "verification_status",
    "support_status",
    "supported_claim_or_method",
)
_CLAIM_LEDGER_FIELDS = (
    "claim_id",
    "manuscript_location",
    "claim",
    "source_artifact",
    "denominator_or_unit",
    "period",
    "uncertainty",
    "verification_status",
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


def _expand_citation_group(group: str) -> list[int]:
    values: list[int] = []
    items = re.split(r"\s*,\s*", group.strip())
    if not items or any(not item.strip() for item in items):
        raise ManuscriptAuditError(f"malformed citation group: {group}")
    for item in items:
        normalized = item.replace("\u2013", "-")
        if not re.fullmatch(r"\d+(?:\s*-\s*\d+)?", normalized):
            raise ManuscriptAuditError(f"malformed citation item: {item}")
        if "-" in normalized:
            start_text, end_text = normalized.split("-", maxsplit=1)
            start, end = int(start_text), int(end_text)
            if end < start:
                raise ManuscriptAuditError(f"descending citation range: {item}")
            values.extend(range(start, end + 1))
        else:
            values.append(int(normalized))
    return values


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _strip_nonprose(text: str) -> str:
    text = _CODE_FENCE.sub("", text)
    text = _EQUATION_DIV.sub("", text)
    return _HTML_COMMENT.sub("", text)


def _find_heading(text: str, heading: str, label: str) -> re.Match[str]:
    match = re.search(rf"(?m)^{re.escape(heading)}\s*$", text)
    if not match:
        raise ManuscriptAuditError(f"{label} has no {heading.removeprefix('# ')} section")
    return match


def _canonical_url(value: str) -> str:
    return value.rstrip(".,);]/").casefold()


def _canonical_doi(value: str) -> str:
    return value.rstrip(".,);]").casefold()


def _reference_identifiers(reference_text: str) -> set[str]:
    identifiers = {
        f"doi:{_canonical_doi(match.group(1))}" for match in _DOI.finditer(reference_text)
    }
    identifiers.update(f"pmid:{match.group(1)}" for match in _PMID.finditer(reference_text))
    for match in _URL.finditer(reference_text):
        url = _canonical_url(match.group(0))
        doi_match = re.fullmatch(r"https?://(?:dx\.)?doi\.org/(10\.\d{4,9}/.+)", url)
        identifiers.add(
            f"doi:{_canonical_doi(doi_match.group(1))}"
            if doi_match
            else f"url:{url}"
        )
    return identifiers


def _audit_bibliography(
    text: str,
    *,
    label: str,
    trailing_heading: str,
) -> tuple[list[int], dict[int, str]]:
    references_heading = _find_heading(text, "# References", label)
    trailing = _find_heading(text[references_heading.end() :], trailing_heading, label)
    trailing_start = references_heading.end() + trailing.start()
    references_text = text[references_heading.end() : trailing_start]
    review_text = text[: references_heading.start()] + text[trailing_start:]
    prose = _strip_nonprose(review_text)

    all_superscripts = re.findall(r"<sup\b[^>]*>.*?</sup>", prose, re.DOTALL | re.IGNORECASE)
    if any(_CITATION.fullmatch(item) is None for item in all_superscripts):
        raise ManuscriptAuditError(f"{label} contains unsupported superscript citation syntax")
    if re.search(r"\^[0-9,\-\u2013\s]+\^", prose):
        raise ManuscriptAuditError(f"{label} contains unsupported caret citation syntax")
    citation_numbers = [
        number
        for match in _CITATION.finditer(prose)
        for number in _expand_citation_group(match.group(1))
    ]

    reference_pairs: list[tuple[int, str]] = []
    for line in references_text.splitlines():
        if not line.strip():
            continue
        match = _REFERENCE.fullmatch(line.strip())
        if not match:
            raise ManuscriptAuditError(f"{label} contains a malformed reference line: {line}")
        reference_pairs.append((int(match.group(1)), match.group(2).strip()))
    numbers = [number for number, _ in reference_pairs]
    if len(numbers) != len(set(numbers)):
        raise ManuscriptAuditError(f"{label} contains duplicate reference numbers")
    references = dict(reference_pairs)
    if numbers != list(range(1, len(numbers) + 1)):
        raise ManuscriptAuditError(f"{label} reference list is not consecutively numbered")
    undefined = sorted(set(citation_numbers) - set(references))
    if undefined:
        raise ManuscriptAuditError(f"{label} has undefined references: {undefined}")
    uncited = sorted(set(references) - set(citation_numbers))
    if uncited:
        raise ManuscriptAuditError(f"{label} has uncited references: {uncited}")
    first_appearance = list(dict.fromkeys(citation_numbers))
    if first_appearance != numbers:
        raise ManuscriptAuditError(
            f"{label} references are not numbered by first appearance: {first_appearance}"
        )

    seen: dict[str, int] = {}
    for reference_number, reference_text in references.items():
        for identifier in _reference_identifiers(reference_text):
            if identifier in seen:
                raise ManuscriptAuditError(
                    f"{label} duplicate identifier: references {seen[identifier]} and "
                    f"{reference_number}"
                )
            seen[identifier] = reference_number
    return citation_numbers, references


def _ledger_identifier(row: dict[str, str]) -> str:
    identifier_type = row["identifier_type"].strip().casefold()
    stable_identifier = row["stable_identifier"].strip()
    if identifier_type == "doi":
        return f"doi:{_canonical_doi(stable_identifier)}"
    if identifier_type == "pmid":
        return f"pmid:{stable_identifier}"
    if identifier_type == "official_url":
        return f"url:{_canonical_url(stable_identifier)}"
    if identifier_type == "bibliographic_title":
        return f"title:{stable_identifier.removeprefix('title:').casefold()}"
    raise ManuscriptAuditError(f"unsupported ledger identifier type: {identifier_type}")


def _audit_reference_ledger(
    rows: list[dict[str, str]],
    references: dict[int, str],
) -> None:
    if not rows:
        raise ManuscriptAuditError("reference verification ledger is empty")
    missing_columns = [field for field in _REFERENCE_LEDGER_FIELDS if field not in rows[0]]
    if missing_columns:
        raise ManuscriptAuditError(
            f"reference verification ledger is missing columns: {missing_columns}"
        )
    if any(any(not row.get(field, "").strip() for field in _REFERENCE_LEDGER_FIELDS) for row in rows):
        raise ManuscriptAuditError("reference verification ledger contains blank required fields")
    numbers = [int(row["reference_number"]) for row in rows]
    if len(numbers) != len(set(numbers)):
        raise ManuscriptAuditError("reference verification ledger contains duplicate numbers")
    if set(numbers) != set(references):
        raise ManuscriptAuditError("reference verification ledger does not match References")
    if any(not row["verification_status"].startswith("verified_") for row in rows):
        raise ManuscriptAuditError("reference verification ledger contains an unverified source")
    if any(row["support_status"] != "verified_support" for row in rows):
        raise ManuscriptAuditError("reference verification ledger contains unsupported citations")

    seen: dict[str, int] = {}
    for row in rows:
        number = int(row["reference_number"])
        canonical = _ledger_identifier(row)
        if canonical in seen:
            raise ManuscriptAuditError(
                f"duplicate ledger identifier: references {seen[canonical]} and {number}"
            )
        seen[canonical] = number
        if canonical.startswith("title:"):
            title_tokens = [
                token.strip().casefold()
                for token in canonical.removeprefix("title:").split(",")
                if token.strip()
            ]
            if not all(token in references[number].casefold() for token in title_tokens):
                raise ManuscriptAuditError(
                    f"ledger identifier does not match reference {number}"
                )
        elif canonical not in _reference_identifiers(references[number]):
            raise ManuscriptAuditError(f"ledger identifier does not match reference {number}")


def _has_active_authorization_guard(text: str) -> bool:
    for chunk in re.findall(r"```\{r[^\n]*\}\n(.*?)```", text, re.DOTALL):
        uncommented = "\n".join(line.split("#", maxsplit=1)[0] for line in chunk.splitlines())
        if re.search(
            r"stopifnot\(\s*isFALSE\(manifest\$results_authorized\)\s*\)",
            uncommented,
        ) or (
            "stopifnot(" in uncommented
            and re.search(
                r"(?m)^\s*isFALSE\(manifest\$results_authorized\),?\s*$",
                uncommented,
            )
        ):
            return True
    return False


def _audit_auc_boundary(text: str, *, rendered: bool = False) -> int:
    review_text = text
    pointer = _ALLOWED_AUC_POINTER
    if rendered:
        review_text = html.unescape(re.sub(r"<[^>]+>", " ", text))
        review_text = re.sub(r"\s+", " ", review_text)
        review_text = re.sub(r"\s+([.,;:])", r"\1", review_text)
        pointer = (
            "Exploratory AUC analyses are reported only in the statistician review companion, "
            "RMD_chm_paper_r_Ashley.html."
        )
    if review_text.count(pointer) != 1:
        raise ManuscriptAuditError("main manuscript must contain the exact nonnumeric AUC pointer")
    remaining = review_text.replace(pointer, "", 1)
    if _FORBIDDEN_MAIN_AUC.search(remaining):
        raise ManuscriptAuditError("main manuscript contains companion-only AUC content")
    return 1


def audit_manuscript_citations(
    main_path: Path,
    companion_path: Path,
    references_path: Path,
    claims_path: Path,
    manifest_path: Path,
    rendered_main_path: Path | None = None,
) -> CitationAuditReport:
    """Fail closed on citation order, evidence ledgers, and AUC placement."""
    main_text = main_path.read_text(encoding="utf-8")
    companion_text = companion_path.read_text(encoding="utf-8")
    citation_numbers, references = _audit_bibliography(
        main_text,
        label="main manuscript",
        trailing_heading="# Table Legends",
    )
    companion_citations, companion_references = _audit_bibliography(
        companion_text,
        label="statistician companion",
        trailing_heading="# Reproducibility Record",
    )

    reference_rows = _read_csv_rows(references_path)
    _audit_reference_ledger(reference_rows, references)
    claim_rows = _read_csv_rows(claims_path)
    if not claim_rows or any(field not in claim_rows[0] for field in _CLAIM_LEDGER_FIELDS):
        raise ManuscriptAuditError("claim evidence map has an incomplete schema")
    if any(any(not row.get(field, "").strip() for field in _CLAIM_LEDGER_FIELDS) for row in claim_rows):
        raise ManuscriptAuditError("claim evidence map contains blank required fields")
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

    auc_pointers = _audit_auc_boundary(main_text)
    if rendered_main_path is not None:
        _audit_auc_boundary(rendered_main_path.read_text(encoding="utf-8"), rendered=True)
    if not re.search(
        r"(?m)^# Statistical Analysis Module 5: Exploratory Area-Label AUC\s*$",
        _strip_nonprose(companion_text),
    ):
        raise ManuscriptAuditError("statistician companion is missing the AUC analysis")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("results_authorized") is not False:
        raise ManuscriptAuditError("results authorization manifest must be exactly false")
    if not _has_active_authorization_guard(main_text) or not _has_active_authorization_guard(
        companion_text
    ):
        raise ManuscriptAuditError("results authorization guard must be active in both review files")

    return CitationAuditReport(
        references=len(references),
        citations=len(citation_numbers),
        claims=len(claim_rows),
        auc_pointers=auc_pointers,
        companion_references=len(companion_references),
        companion_citations=len(companion_citations),
    )
