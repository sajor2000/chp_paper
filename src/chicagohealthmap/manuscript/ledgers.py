from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Literal, Self, TypeVar

import pandas as pd  # type: ignore[import-untyped]
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    ValidationError,
    field_validator,
    model_validator,
)

from chicagohealthmap.manuscript.models import ManuscriptContracts


class LedgerError(ValueError):
    """Raised when a manuscript control ledger violates its contract."""


class LedgerModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def _validate_iso_date(value: object, *, optional: bool) -> object:
    if optional and value == "":
        return None
    if not isinstance(value, str) or _ISO_DATE.fullmatch(value) is None:
        raise ValueError("date must use YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("date must be a valid YYYY-MM-DD calendar date") from error
    return value


class ClaimRecord(LedgerModel):
    claim_id: str
    section: str
    draft_claim: str
    claim_class: Literal[
        "result",
        "method",
        "resource",
        "novelty",
        "prior_evidence",
        "interpretation",
        "policy",
        "limitation",
    ]
    source_or_artifact_id: str
    exact_support_location: str
    population_geography_measure_period_match: str
    support_strength: str
    conflict_or_gap: str
    allowed_wording: str
    prohibited_inference: str
    result_status: Literal["prespecified", "secondary", "exploratory", "post_hoc", "not_applicable"]
    owner: str
    verified_by: str
    verified_date: date | None
    final_text_location: str

    @field_validator("verified_date", mode="before")
    @classmethod
    def verified_date_is_iso_calendar_date(cls, value: object) -> object:
        return _validate_iso_date(value, optional=True)


class NumberRecord(LedgerModel):
    number_id: str
    artifact_id: str
    checksum: str
    artifact_field: str
    code_version: str
    population: str
    exclusions: str
    geography: str
    time_period: str
    measure: str
    unit: str
    denominator: str
    raw_value: str
    display_value: str
    uncertainty: str
    result_status: Literal["prespecified", "secondary", "exploratory", "post_hoc"]
    manuscript_locations: str

    @field_validator("checksum")
    @classmethod
    def checksum_is_canonical_sha256(cls, value: str) -> str:
        if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
            raise ValueError("checksum must use sha256:<64 lowercase hexadecimal characters>")
        return value


class AiUseRecord(LedgerModel):
    ai_use_id: str
    platform: str
    model: str
    manufacturer: str
    start_date: date
    end_date: date
    use: str
    affected_artifact: str
    human_verifier: str
    verified_date: date | None

    @field_validator("start_date", "end_date", "verified_date", mode="before")
    @classmethod
    def dates_use_iso_calendar_form(cls, value: object, info: ValidationInfo) -> object:
        return _validate_iso_date(value, optional=info.field_name == "verified_date")

    @model_validator(mode="after")
    def date_range_is_ordered(self) -> Self:
        if self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        return self


class IssueRecord(LedgerModel):
    issue_id: str
    severity: Literal["critical", "important", "minor"]
    gate: str
    description: str
    evidence: str
    owner: str
    status: Literal["open", "resolved", "accepted_by_human"]
    resolution: str


@dataclass(frozen=True)
class LedgerReport:
    claims: int
    numbers: int
    ai_uses: int
    open_critical_issues: int
    open_important_issues: int
    number_artifacts: tuple[tuple[str, str], ...]


_CLAIM_HEADERS = tuple(ClaimRecord.model_fields)
_NUMBER_HEADERS = tuple(NumberRecord.model_fields)
_AI_USE_HEADERS = tuple(AiUseRecord.model_fields)
_ISSUE_HEADERS = tuple(IssueRecord.model_fields)
LEDGER_MODELS: dict[str, type[LedgerModel]] = {
    "claim_ledger.csv": ClaimRecord,
    "number_ledger.csv": NumberRecord,
    "ai_use_ledger.csv": AiUseRecord,
    "issue_ledger.csv": IssueRecord,
}

_Record = TypeVar("_Record", bound=LedgerModel)


def _read_records(
    control_dir: Path,
    filename: str,
    headers: tuple[str, ...],
    model: type[_Record],
) -> list[_Record]:
    path = control_dir / filename
    if not path.is_file():
        raise LedgerError(f"{filename} is required")
    try:
        frame = pd.read_csv(path, keep_default_na=False, dtype=str)
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
    ) as error:
        raise LedgerError(f"{filename} is not a readable ledger: {error}") from error
    if tuple(frame.columns) != headers:
        raise LedgerError(f"{filename} headers must exactly match: {', '.join(headers)}")

    records: list[_Record] = []
    for row_number, row in enumerate(frame.to_dict("records"), start=1):
        try:
            records.append(model.model_validate(row))
        except ValidationError as error:
            raise LedgerError(f"{filename} row {row_number} is invalid: {error}") from error
    return records


def _require_unique(records: Sequence[LedgerModel], field: str, label: str) -> None:
    identifiers = [str(getattr(record, field)).strip() for record in records]
    if len(set(identifiers)) != len(identifiers):
        raise LedgerError(f"{label} IDs must be unique")


def _require_nonblank_identifiers(records: Sequence[LedgerModel], field: str, label: str) -> None:
    if any(not str(getattr(record, field)).strip() for record in records):
        raise LedgerError(f"{label} ID is required")


def verify_ledgers(control_dir: Path, contracts: ManuscriptContracts) -> LedgerReport:
    """Validate all manuscript ledgers and return their gate-relevant counts."""
    if not isinstance(contracts, ManuscriptContracts):
        raise TypeError("contracts must be a ManuscriptContracts instance")

    claims = _read_records(control_dir, "claim_ledger.csv", _CLAIM_HEADERS, ClaimRecord)
    numbers = _read_records(control_dir, "number_ledger.csv", _NUMBER_HEADERS, NumberRecord)
    ai_uses = _read_records(control_dir, "ai_use_ledger.csv", _AI_USE_HEADERS, AiUseRecord)
    issues = _read_records(control_dir, "issue_ledger.csv", _ISSUE_HEADERS, IssueRecord)

    _require_nonblank_identifiers(claims, "claim_id", "claim")
    _require_nonblank_identifiers(numbers, "number_id", "number")
    _require_nonblank_identifiers(ai_uses, "ai_use_id", "AI-use")
    _require_nonblank_identifiers(issues, "issue_id", "issue")
    _require_unique(claims, "claim_id", "claim")
    _require_unique(numbers, "number_id", "number")
    _require_unique(ai_uses, "ai_use_id", "AI-use")
    _require_unique(issues, "issue_id", "issue")

    for number in numbers:
        for field in ("artifact_id", "checksum", "artifact_field", "code_version"):
            if not str(getattr(number, field)).strip():
                raise LedgerError(f"number {number.number_id} requires nonblank {field}")

    number_artifact_ids = {number.artifact_id.strip() for number in numbers}
    for claim in claims:
        if claim.claim_class == "result" and claim.result_status == "not_applicable":
            raise LedgerError(
                f"result claim {claim.claim_id} cannot use not_applicable result status"
            )
        if claim.claim_class != "result" and claim.result_status != "not_applicable":
            raise LedgerError(
                f"non-result claim {claim.claim_id} must use not_applicable result status"
            )
        if claim.claim_class == "result" and (
            not claim.source_or_artifact_id.strip()
            or not claim.exact_support_location.strip()
            or claim.support_strength != "frozen"
        ):
            raise LedgerError(f"result claim {claim.claim_id} requires a frozen artifact")
        if (
            claim.claim_class == "result"
            and claim.source_or_artifact_id.strip() not in number_artifact_ids
        ):
            raise LedgerError(f"result claim {claim.claim_id} has no matching number artifact")
        if claim.claim_class != "result" and claim.support_strength == "verified":
            if not claim.owner.strip():
                raise LedgerError(f"verified claim {claim.claim_id} requires an owner")
            if not claim.verified_by.strip():
                raise LedgerError(f"verified claim {claim.claim_id} lacks an independent verifier")
            if claim.verified_date is None:
                raise LedgerError(f"verified claim {claim.claim_id} lacks a verification date")
            if claim.verified_by.strip().casefold() == claim.owner.strip().casefold():
                raise LedgerError(f"verified claim {claim.claim_id} cannot be self-verified")

    for record in ai_uses:
        if not record.human_verifier.strip() or record.verified_date is None:
            raise LedgerError(f"{record.ai_use_id} lacks human verification")

    for issue in issues:
        if issue.status in {"resolved", "accepted_by_human"}:
            for field in ("evidence", "owner", "resolution"):
                if not str(getattr(issue, field)).strip():
                    raise LedgerError(
                        f"issue {issue.issue_id} with status {issue.status} "
                        f"requires nonblank {field}"
                    )

    return LedgerReport(
        claims=len(claims),
        numbers=len(numbers),
        ai_uses=len(ai_uses),
        open_critical_issues=sum(
            issue.severity == "critical" and issue.status == "open" for issue in issues
        ),
        open_important_issues=sum(
            issue.severity == "important" and issue.status == "open" for issue in issues
        ),
        number_artifacts=tuple((number.artifact_id.strip(), number.checksum) for number in numbers),
    )


def initialize_ledgers(control_dir: Path, contracts: ManuscriptContracts) -> tuple[Path, ...]:
    """Create empty manuscript ledgers and a contract digest without overwrites."""
    if not isinstance(contracts, ManuscriptContracts):
        raise TypeError("contracts must be a ManuscriptContracts instance")
    control_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for filename, model in LEDGER_MODELS.items():
        destination = control_dir / filename
        if destination.exists() and destination.stat().st_size > 0:
            raise LedgerError(f"refusing to overwrite nonempty {filename}")
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        pd.DataFrame(columns=list(model.model_fields)).to_csv(temporary, index=False)
        temporary.replace(destination)
        created.append(destination)

    canonical = json.dumps(
        contracts.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    digest_path = control_dir / "contract_digest.sha256"
    digest_path.write_text(
        sha256(canonical.encode("utf-8")).hexdigest() + "\n",
        encoding="utf-8",
    )
    return (*created, digest_path)
