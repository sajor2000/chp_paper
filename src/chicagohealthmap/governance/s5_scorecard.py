"""Outcome-blinded S5 case-selection scorecard template."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from json import JSONDecodeError
from pathlib import Path
from typing import Any


class S5ScorecardError(ValueError):
    """S5 scorecard evidence is missing or invalid."""


@dataclass(frozen=True, slots=True)
class ScorecardDomain:
    """One fixed S5 scorecard scoring domain."""

    domain: str
    maximum_points: int
    fixed_scoring_rule: str
    hard_gate: str
    required_evidence: str
    narrative_sap_section: str
    status: str


@dataclass(frozen=True, slots=True)
class CandidateShell:
    """Outcome-blinded candidate shell; no scores or result fields."""

    case_id: str
    display_name: str
    component_conditions: tuple[str, ...]
    score_status: str
    reconciled_score: int | None


@dataclass(frozen=True, slots=True)
class S5ScorecardPacket:
    """Machine-readable, non-authorizing S5 scorecard template."""

    record_type: str
    gate: str
    status: str
    outcome_blinded: bool
    analysis_authorized: bool
    results_authorized: bool
    case_study_spatial_frame: dict[str, str]
    source_scope: dict[str, str]
    scoring_domains: tuple[ScorecardDomain, ...]
    portfolio_rules: tuple[ScorecardDomain, ...]
    candidate_shells: tuple[CandidateShell, ...]
    forbidden_information: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    required_next_evidence: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""

        return asdict(self)


@dataclass(frozen=True, slots=True)
class WorksheetRow:
    """One scorer row for one candidate-domain combination."""

    candidate_id: str
    candidate_display_name: str
    domain: str
    maximum_points: int
    fixed_scoring_rule: str
    hard_gate: str
    required_evidence: str
    score: int | None
    evidence_references: tuple[str, ...]
    rationale: str | None
    hard_gate_status: str
    outcome_information_used: bool


@dataclass(frozen=True, slots=True)
class ScorerWorksheet:
    """One blinded scorer worksheet template."""

    scorer_id: str
    status: str
    outcome_blinded_attestation: str
    outcome_information_used: bool
    rows: tuple[WorksheetRow, ...]


@dataclass(frozen=True, slots=True)
class ReconciliationEntry:
    """One candidate reconciliation placeholder."""

    case_id: str
    reconciled_total_score: int | None
    disagreement_disposition: str | None
    hard_gate_disposition: str
    promoted: bool | None


@dataclass(frozen=True, slots=True)
class ReconciliationTemplate:
    """Outcome-blinded reconciliation record template."""

    status: str
    outcome_information_used: bool
    entries: tuple[ReconciliationEntry, ...]
    portfolio_decision: str


@dataclass(frozen=True, slots=True)
class ApprovalRecordFormat:
    """Case-selection approval record format expected by manuscript control."""

    destination: str
    required_fields: tuple[str, ...]
    case_fields: tuple[str, ...]
    approval_fields: tuple[str, ...]
    required_values: dict[str, Any]


@dataclass(frozen=True, slots=True)
class S5ScoringArtifactsPacket:
    """Two scorer worksheets plus reconciliation and approval-record templates."""

    record_type: str
    gate: str
    status: str
    source_scorecard_path: str
    source_scorecard_sha256: str
    outcome_blinded: bool
    results_authorized: bool
    scorer_worksheets: tuple[ScorerWorksheet, ...]
    reconciliation_template: ReconciliationTemplate
    approval_record_format: ApprovalRecordFormat
    forbidden_information: tuple[str, ...]
    blocked_actions: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""

        return json.loads(json.dumps(asdict(self)))


@dataclass(frozen=True, slots=True)
class S5ReconciliationDraftEntry:
    """One non-authorizing candidate reconciliation draft entry."""

    case_id: str
    display_name: str
    scorer_totals: dict[str, int]
    reconciled_total_score: float
    reconciliation_status: str
    hard_gate_disposition: str


@dataclass(frozen=True, slots=True)
class S5ReconciliationDraftPacket:
    """Outcome-blinded S5 reconciliation draft pending human approval."""

    record_type: str
    gate: str
    status: str
    outcome_blinded: bool
    results_authorized: bool
    approval_required: bool
    approval_record_path: str
    source_worksheet_path: str
    scorer_ids: tuple[str, str]
    entries: tuple[S5ReconciliationDraftEntry, ...]
    blocked_actions: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""

        return json.loads(json.dumps(asdict(self)))


_DOMAIN_EVIDENCE_REFERENCES: dict[str, tuple[str, ...]] = {
    "Community-area usability": (
        "docs/analysis/s4_methods_mapping.json",
        "outputs/provenance/variable_lineage.csv",
        "docs/analysis/data_dictionary.md",
    ),
    "Tract usability/precision": (
        "docs/analysis/s4_methods_mapping.json",
        "docs/analysis/methods_discrepancies.md",
        "outputs/provenance/variable_lineage.csv",
    ),
    "Predictor temporal stability": (
        "docs/analysis/s4_methods_mapping.json",
        "docs/analysis/methods_discrepancies.md",
        "docs/methods/data_sources.md",
    ),
    "Phenotype interpretability": (
        "docs/analysis/s4_methods_mapping.json",
        "docs/analysis/methods_discrepancies.md",
        "docs/analysis/data_dictionary.md",
    ),
    "Comparator definition/period": (
        "config/source_registry.yml",
        "docs/methods/data_sources.md",
        "outputs/provenance/variable_lineage.csv",
    ),
    "Evidence and novelty gap": (
        "docs/methods/literature_search_protocol.md",
        "sources/literature/pubmed/snapshots/2026-07-14/records.csv",
        "sources/literature/paperclip/snapshots/2026-07-14/verified_corpus.md",
    ),
    "Translation questionability": (
        "docs/analysis/s4_methods_mapping.json",
        "sources/public/_registry/acquisition_matrix.csv",
        "outputs/provenance/variable_lineage.csv",
    ),
    "Distinct portfolio contribution": (
        "docs/analysis/s4_methods_mapping.json",
        "docs/methods/literature_search_protocol.md",
        "sources/literature/pubmed/snapshots/2026-07-14/records.csv",
    ),
}

_EXPECTED_CANDIDATE_DISPLAY_NAMES = {
    "cardiometabolic_bundle": "Cardiometabolic bundle",
    "respiratory_copd": "Respiratory COPD candidate",
}
_EXPECTED_SCORING_GRID = frozenset(
    (candidate_id, domain)
    for candidate_id in _EXPECTED_CANDIDATE_DISPLAY_NAMES
    for domain in _DOMAIN_EVIDENCE_REFERENCES
)
_ALLOWED_HARD_GATE_STATUSES = frozenset({"met", "not_met", "not_applicable"})
_S5_APPROVAL_CLAIM_STATUSES = frozenset(
    {
        "approved",
        "passed",
        "s5_approved",
        "s5_passed",
        "case_selection_approved",
    }
)
_RECONCILIATION_DRAFT_RECORD_TYPE = "outcome_blinded_case_selection_reconciliation_draft"
_RECONCILIATION_DRAFT_STATUS = "reconciled_pending_human_approval"
_COMPLETED_WORKSHEET_STATUS = "worksheets_completed_reconciliation_pending"
_S5_APPROVAL_RECORD_PATH = "outputs/governance/case_selection.json"
_S5_APPROVAL_RECORD_PARTS = tuple(Path(_S5_APPROVAL_RECORD_PATH).parts)
_RECONCILIATION_BLOCKED_ACTIONS = (
    "no outcome unblinding",
    "no confirmatory modeling",
    "no Results prose",
    "no case promotion",
    "no final analytic dataset",
    "no combined marimo case-study notebook",
)


def _safe_file(root: Path, relative_path: str) -> Path:
    path = root / relative_path
    if path.is_symlink():
        raise S5ScorecardError(f"S5 scorecard evidence is a symlink: {relative_path}")
    if not path.is_file():
        raise S5ScorecardError(f"S5 scorecard evidence is missing: {relative_path}")
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError) as error:
        raise S5ScorecardError(
            f"S5 scorecard evidence escapes repository: {relative_path}"
        ) from error
    return path


def _read_json(root: Path, relative_path: str) -> dict[str, Any]:
    try:
        payload = json.loads(_safe_file(root, relative_path).read_text(encoding="utf-8"))
    except JSONDecodeError as error:
        raise S5ScorecardError(f"S5 scorecard evidence is invalid JSON: {relative_path}") from error
    if not isinstance(payload, dict):
        raise S5ScorecardError(f"S5 scorecard evidence must be an object: {relative_path}")
    return payload


def _read_json_file(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise S5ScorecardError(f"S5 scorecard evidence is a symlink: {path}")
    if not path.is_file():
        raise S5ScorecardError(f"S5 scorecard evidence is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as error:
        raise S5ScorecardError(f"S5 scorecard evidence is invalid JSON: {path}") from error
    if not isinstance(payload, dict):
        raise S5ScorecardError(f"S5 scorecard evidence must be an object: {path}")
    return payload


def _case_selection_rows(sap: dict[str, Any]) -> list[dict[str, Any]]:
    annexes = sap.get("annexes")
    if not isinstance(annexes, list):
        raise S5ScorecardError("SAP workbook spec contains no annexes")
    for annex in annexes:
        if isinstance(annex, dict) and annex.get("name") == "Case Selection":
            rows = annex.get("rows")
            if isinstance(rows, list) and rows:
                if all(isinstance(row, dict) for row in rows):
                    return rows
    raise S5ScorecardError("SAP workbook spec contains no Case Selection rows")


def _domain_from_row(row: dict[str, Any]) -> ScorecardDomain:
    try:
        maximum_points = int(row["Maximum Points"])
    except (KeyError, TypeError, ValueError) as error:
        raise S5ScorecardError("Case Selection row has invalid points") from error
    fields = {
        "domain": row.get("Domain"),
        "fixed_scoring_rule": row.get("Fixed Scoring Rule"),
        "hard_gate": row.get("Hard Gate"),
        "required_evidence": row.get("Required Evidence"),
        "narrative_sap_section": row.get("Narrative SAP Section"),
        "status": row.get("Status"),
    }
    if any(not isinstance(value, str) or not value for value in fields.values()):
        raise S5ScorecardError("Case Selection row is incomplete")
    return ScorecardDomain(maximum_points=maximum_points, **fields)  # type: ignore[arg-type]


def _validate_s4_packet(packet: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    if packet.get("status") != "website_dictionary_authoritative":
        raise S5ScorecardError("S4 methods dictionary is not accepted")
    if packet.get("analysis_authorized") is not False:
        raise S5ScorecardError("S4 packet must not authorize analysis")
    frame = packet.get("case_study_spatial_frame")
    scope = packet.get("source_scope")
    mappings = packet.get("position_mappings")
    if (
        not isinstance(frame, dict)
        or frame.get("frame") != "City of Chicago"
        or not isinstance(scope, dict)
        or scope.get("geographic_scope") != "six-county Chicagoland"
        or not isinstance(mappings, dict)
    ):
        raise S5ScorecardError("S4 packet does not define the Chicago case-study frame")
    required = {"geography", "time_period", "phenotype", "numerator", "capture_rate"}
    if not required.issubset(mappings):
        raise S5ScorecardError("S4 packet lacks core guarded position mappings")
    return (
        {str(key): str(value) for key, value in frame.items()},
        {str(key): str(value) for key, value in scope.items()},
    )


def build_s5_scorecard_packet(root: Path) -> S5ScorecardPacket:
    """Build the non-authorizing, outcome-blinded S5 scorecard template."""

    resolved_root = root.resolve()
    sap = _read_json(resolved_root, "docs/analysis/sap_workbook_spec.json")
    s4 = _read_json(resolved_root, "docs/analysis/s4_methods_mapping.json")
    frame, scope = _validate_s4_packet(s4)
    domains = tuple(_domain_from_row(row) for row in _case_selection_rows(sap))
    scoring = tuple(domain for domain in domains if domain.maximum_points > 0)
    portfolio = tuple(domain for domain in domains if domain.maximum_points == 0)
    if sum(domain.maximum_points for domain in scoring) != 100:
        raise S5ScorecardError("S5 scorecard scoring domains must sum to 100")
    if len(scoring) != 8 or len(portfolio) != 2:
        raise S5ScorecardError("S5 scorecard domain structure is invalid")
    return S5ScorecardPacket(
        record_type="outcome_blinded_case_selection_scorecard_template",
        gate="S5",
        status="scorecard_template_ready",
        outcome_blinded=True,
        analysis_authorized=False,
        results_authorized=False,
        case_study_spatial_frame=frame,
        source_scope=scope,
        scoring_domains=scoring,
        portfolio_rules=portfolio,
        candidate_shells=(
            CandidateShell(
                case_id="cardiometabolic_bundle",
                display_name="Cardiometabolic bundle",
                component_conditions=("hypertension", "diabetes"),
                score_status="pending_two_blinded_scorers",
                reconciled_score=None,
            ),
            CandidateShell(
                case_id="respiratory_copd",
                display_name="Respiratory COPD candidate",
                component_conditions=("copd",),
                score_status="pending_two_blinded_scorers",
                reconciled_score=None,
            ),
        ),
        forbidden_information=(
            "life-expectancy values",
            "mortality values",
            "outcome maps",
            "outcome correlations",
            "model results",
            "outcome-linked residuals",
        ),
        blocked_actions=(
            "no outcome unblinding",
            "no confirmatory modeling",
            "no Results prose",
            "no final analytic dataset",
            "no combined marimo case-study notebook",
        ),
        required_next_evidence=(
            "two independent blinded scorer worksheets",
            "original and reconciled scores",
            "disagreement disposition",
            "signed S5 portfolio decision",
        ),
    )


def _scorecard_path(root: Path) -> Path:
    return _safe_file(root, "docs/analysis/s5_case_selection_scorecard.json")


def _load_scorecard_packet(root: Path) -> S5ScorecardPacket:
    return build_s5_scorecard_packet(root)


def _worksheet_rows(packet: S5ScorecardPacket) -> tuple[WorksheetRow, ...]:
    return tuple(
        WorksheetRow(
            candidate_id=candidate.case_id,
            candidate_display_name=candidate.display_name,
            domain=domain.domain,
            maximum_points=domain.maximum_points,
            fixed_scoring_rule=domain.fixed_scoring_rule,
            hard_gate=domain.hard_gate,
            required_evidence=domain.required_evidence,
            score=None,
            evidence_references=_DOMAIN_EVIDENCE_REFERENCES[domain.domain],
            rationale=None,
            hard_gate_status="pending",
            outcome_information_used=False,
        )
        for candidate in packet.candidate_shells
        for domain in packet.scoring_domains
    )


def build_s5_scoring_artifacts_packet(root: Path) -> S5ScoringArtifactsPacket:
    """Build two blinded scorer worksheets plus reconciliation/approval templates."""

    resolved_root = root.resolve()
    scorecard_path = _scorecard_path(resolved_root)
    packet = _load_scorecard_packet(resolved_root)
    rows = _worksheet_rows(packet)
    worksheets = tuple(
        ScorerWorksheet(
            scorer_id=f"blinded_scorer_{index}",
            status="pending_completion",
            outcome_blinded_attestation=(
                "Complete without life-expectancy values, mortality values, outcome maps, "
                "outcome correlations, model results, or outcome-linked residuals."
            ),
            outcome_information_used=False,
            rows=rows,
        )
        for index in (1, 2)
    )
    return S5ScoringArtifactsPacket(
        record_type="outcome_blinded_s5_scoring_artifacts_template",
        gate="S5",
        status="worksheets_ready_reconciliation_pending",
        source_scorecard_path="docs/analysis/s5_case_selection_scorecard.json",
        source_scorecard_sha256=sha256(scorecard_path.read_bytes()).hexdigest(),
        outcome_blinded=True,
        results_authorized=False,
        scorer_worksheets=worksheets,
        reconciliation_template=ReconciliationTemplate(
            status="pending_reconciliation",
            outcome_information_used=False,
            entries=tuple(
                ReconciliationEntry(
                    case_id=candidate.case_id,
                    reconciled_total_score=None,
                    disagreement_disposition=None,
                    hard_gate_disposition="pending",
                    promoted=None,
                )
                for candidate in packet.candidate_shells
            ),
            portfolio_decision="pending_signed_S5_decision",
        ),
        approval_record_format=ApprovalRecordFormat(
            destination="outputs/governance/case_selection.json",
            required_fields=(
                "record_type",
                "gate",
                "status",
                "outcome_blinded",
                "cases",
                "approval",
            ),
            case_fields=("order", "case_id", "display_name"),
            approval_fields=("human", "date", "decision"),
            required_values={
                "record_type": "outcome_blinded_case_selection",
                "gate": "S5",
                "status": "approved",
                "outcome_blinded": True,
            },
        ),
        forbidden_information=packet.forbidden_information,
        blocked_actions=packet.blocked_actions,
    )


def _nonblank_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _validate_s5_scoring_artifacts_header(payload: dict[str, Any]) -> None:
    if payload.get("record_type") != "outcome_blinded_s5_scoring_artifacts_template":
        raise S5ScorecardError("S5 reconciliation input record type is invalid")
    if payload.get("gate") != "S5":
        raise S5ScorecardError("S5 reconciliation input gate is invalid")
    if payload.get("outcome_blinded") is not True:
        raise S5ScorecardError("S5 reconciliation input must be outcome-blinded")
    if payload.get("results_authorized") is not False:
        raise S5ScorecardError("S5 reconciliation input must not authorize results")
    status = str(payload.get("status", "")).strip().lower()
    if status in _S5_APPROVAL_CLAIM_STATUSES:
        raise S5ScorecardError("S5 reconciliation input must not claim S5 approval")
    if status != _COMPLETED_WORKSHEET_STATUS:
        raise S5ScorecardError("S5 reconciliation input worksheets must be completed")


def _validate_scoring_row(row: Any) -> tuple[str, str, str, int, int, str]:
    if not isinstance(row, dict):
        raise S5ScorecardError("S5 reconciliation scoring row is invalid")
    if row.get("outcome_information_used") is not False:
        raise S5ScorecardError("S5 reconciliation row used outcome information")
    candidate_id = _nonblank_string(row.get("candidate_id"))
    display_name = _nonblank_string(row.get("candidate_display_name"))
    domain = _nonblank_string(row.get("domain"))
    if candidate_id is None or display_name is None or domain is None:
        raise S5ScorecardError("S5 reconciliation row coverage is incomplete")
    if (
        candidate_id not in _EXPECTED_CANDIDATE_DISPLAY_NAMES
        or display_name != _EXPECTED_CANDIDATE_DISPLAY_NAMES[candidate_id]
        or domain not in _DOMAIN_EVIDENCE_REFERENCES
    ):
        raise S5ScorecardError("S5 reconciliation expected S5 scoring grid is invalid")
    maximum_points = row.get("maximum_points")
    if not isinstance(maximum_points, int) or isinstance(maximum_points, bool):
        raise S5ScorecardError("S5 reconciliation row maximum points are invalid")
    score = row.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or score < 0 or score > maximum_points:
        raise S5ScorecardError("S5 reconciliation row score is invalid")
    if _nonblank_string(row.get("rationale")) is None:
        raise S5ScorecardError("S5 reconciliation row rationale is missing")
    evidence = row.get("evidence_references")
    if not isinstance(evidence, list) or not evidence:
        raise S5ScorecardError("S5 reconciliation row evidence is missing")
    evidence_references = tuple(str(reference) for reference in evidence)
    if evidence_references != _DOMAIN_EVIDENCE_REFERENCES[domain] or any(
        _nonblank_string(reference) is None for reference in evidence_references
    ):
        raise S5ScorecardError("S5 reconciliation row evidence is invalid")
    hard_gate_status = _nonblank_string(row.get("hard_gate_status"))
    if hard_gate_status not in _ALLOWED_HARD_GATE_STATUSES:
        raise S5ScorecardError("S5 reconciliation hard-gate status is invalid")
    return candidate_id, display_name, domain, maximum_points, score, hard_gate_status


def _validated_scorer_rows(
    worksheet: Any,
) -> tuple[str, dict[tuple[str, str], tuple[str, int, int, str]]]:
    if not isinstance(worksheet, dict):
        raise S5ScorecardError("S5 reconciliation worksheet is invalid")
    scorer_id = _nonblank_string(worksheet.get("scorer_id"))
    if scorer_id is None:
        raise S5ScorecardError("S5 reconciliation scorer id is missing")
    if worksheet.get("status") != "completed":
        raise S5ScorecardError("S5 reconciliation worksheet status is invalid")
    if worksheet.get("outcome_information_used") is not False:
        raise S5ScorecardError("S5 reconciliation worksheet used outcome information")
    rows = worksheet.get("rows")
    if not isinstance(rows, list) or not rows:
        raise S5ScorecardError("S5 reconciliation worksheet rows are missing")
    validated: dict[tuple[str, str], tuple[str, int, int, str]] = {}
    for row in rows:
        candidate_id, display_name, domain, maximum_points, score, hard_gate_status = (
            _validate_scoring_row(row)
        )
        key = (candidate_id, domain)
        if key in validated:
            raise S5ScorecardError("S5 reconciliation row coverage is duplicated")
        validated[key] = (display_name, maximum_points, score, hard_gate_status)
    if set(validated) != _EXPECTED_SCORING_GRID:
        raise S5ScorecardError("S5 reconciliation expected S5 scoring grid is invalid")
    return scorer_id, validated


def _render_source_worksheet_path(input_path: Path, root: Path | None) -> str:
    if root is None:
        return input_path.name if input_path.is_absolute() else input_path.as_posix()
    try:
        return input_path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return input_path.as_posix()


def build_s5_reconciliation_draft_packet(
    input_path: Path, *, root: Path | None = None
) -> S5ReconciliationDraftPacket:
    """Build a non-authorizing S5 reconciliation draft from completed worksheets."""

    resolved_input = input_path.resolve()
    if root is not None:
        try:
            resolved_input.relative_to(root.resolve())
        except (OSError, ValueError):
            raise S5ScorecardError("S5 reconciliation input is outside repository") from None
    payload = _read_json_file(resolved_input)
    _validate_s5_scoring_artifacts_header(payload)
    worksheets = payload.get("scorer_worksheets")
    if not isinstance(worksheets, list) or len(worksheets) != 2:
        raise S5ScorecardError("S5 reconciliation requires exactly two scorer worksheets")
    first_scorer, first_rows = _validated_scorer_rows(worksheets[0])
    second_scorer, second_rows = _validated_scorer_rows(worksheets[1])
    if first_scorer == second_scorer:
        raise S5ScorecardError("S5 reconciliation scorer ids must be unique")
    if set(first_rows) != set(second_rows):
        raise S5ScorecardError("S5 reconciliation candidate/domain coverage differs")

    candidate_order: list[str] = []
    candidate_display_names: dict[str, str] = {}
    scorer_totals: dict[str, dict[str, int]] = {}
    hard_gate_statuses: dict[str, set[str]] = {}
    for candidate_id, domain in first_rows:
        display_name, maximum_points, first_score, first_hard_gate = first_rows[
            (candidate_id, domain)
        ]
        second_display_name, second_maximum_points, second_score, second_hard_gate = second_rows[
            (candidate_id, domain)
        ]
        if display_name != second_display_name or maximum_points != second_maximum_points:
            raise S5ScorecardError("S5 reconciliation candidate/domain coverage differs")
        if candidate_id not in candidate_order:
            candidate_order.append(candidate_id)
            candidate_display_names[candidate_id] = display_name
            scorer_totals[candidate_id] = {first_scorer: 0, second_scorer: 0}
            hard_gate_statuses[candidate_id] = set()
        scorer_totals[candidate_id][first_scorer] += first_score
        scorer_totals[candidate_id][second_scorer] += second_score
        hard_gate_statuses[candidate_id].update({first_hard_gate, second_hard_gate})

    entries = []
    for candidate_id in candidate_order:
        totals = scorer_totals[candidate_id]
        total_values = tuple(totals.values())
        reconciled_total = sum(total_values) / len(total_values)
        status = (
            "identical_blinded_scores"
            if len(set(total_values)) == 1
            else "averaged_two_blinded_scores"
        )
        hard_gate_disposition = (
            "all_met" if hard_gate_statuses[candidate_id] == {"met"} else "not_all_met"
        )
        entries.append(
            S5ReconciliationDraftEntry(
                case_id=candidate_id,
                display_name=candidate_display_names[candidate_id],
                scorer_totals=totals,
                reconciled_total_score=float(reconciled_total),
                reconciliation_status=status,
                hard_gate_disposition=hard_gate_disposition,
            )
        )

    return S5ReconciliationDraftPacket(
        record_type=_RECONCILIATION_DRAFT_RECORD_TYPE,
        gate="S5",
        status=_RECONCILIATION_DRAFT_STATUS,
        outcome_blinded=True,
        results_authorized=False,
        approval_required=True,
        approval_record_path=_S5_APPROVAL_RECORD_PATH,
        source_worksheet_path=_render_source_worksheet_path(input_path, root),
        scorer_ids=(first_scorer, second_scorer),
        entries=tuple(entries),
        blocked_actions=_RECONCILIATION_BLOCKED_ACTIONS,
    )


def validate_s5_reconciliation_draft_payload(
    payload: dict[str, Any],
) -> S5ReconciliationDraftPacket:
    """Validate a stored S5 reconciliation draft without treating it as approval."""

    if payload.get("record_type") != _RECONCILIATION_DRAFT_RECORD_TYPE:
        raise S5ScorecardError("S5 reconciliation draft record type is invalid")
    if payload.get("gate") != "S5":
        raise S5ScorecardError("S5 reconciliation draft gate is invalid")
    if payload.get("status") != _RECONCILIATION_DRAFT_STATUS:
        raise S5ScorecardError("S5 reconciliation draft status is invalid")
    if payload.get("outcome_blinded") is not True:
        raise S5ScorecardError("S5 reconciliation draft must be outcome-blinded")
    if payload.get("results_authorized") is not False:
        raise S5ScorecardError("S5 reconciliation draft must not authorize results")
    if payload.get("approval_required") is not True:
        raise S5ScorecardError("S5 reconciliation draft must require approval")
    if payload.get("approval_record_path") != _S5_APPROVAL_RECORD_PATH:
        raise S5ScorecardError("S5 reconciliation draft approval path is invalid")
    if tuple(payload.get("blocked_actions", ())) != _RECONCILIATION_BLOCKED_ACTIONS:
        raise S5ScorecardError("S5 reconciliation draft blocked actions are invalid")
    raw_scorer_ids = payload.get("scorer_ids")
    if (
        not isinstance(raw_scorer_ids, list)
        or len(raw_scorer_ids) != 2
        or any(_nonblank_string(scorer_id) is None for scorer_id in raw_scorer_ids)
    ):
        raise S5ScorecardError("S5 reconciliation draft scorer ids are invalid")
    if len(set(raw_scorer_ids)) != 2:
        raise S5ScorecardError("S5 reconciliation draft scorer ids are invalid")
    source_worksheet_path = payload.get("source_worksheet_path")
    if (
        _nonblank_string(source_worksheet_path) is None
        or Path(str(source_worksheet_path)).is_absolute()
    ):
        raise S5ScorecardError("S5 reconciliation draft source worksheet path is invalid")
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list) or len(raw_entries) != len(
        _EXPECTED_CANDIDATE_DISPLAY_NAMES
    ):
        raise S5ScorecardError("S5 reconciliation draft entries are missing")
    entries = []
    seen_case_ids: set[str] = set()
    for entry in raw_entries:
        if not isinstance(entry, dict):
            raise S5ScorecardError("S5 reconciliation draft entry is invalid")
        case_id = _nonblank_string(entry.get("case_id"))
        display_name = _nonblank_string(entry.get("display_name"))
        if case_id is None or display_name is None:
            raise S5ScorecardError("S5 reconciliation draft entry is incomplete")
        if (
            case_id not in _EXPECTED_CANDIDATE_DISPLAY_NAMES
            or display_name != _EXPECTED_CANDIDATE_DISPLAY_NAMES[case_id]
            or case_id in seen_case_ids
        ):
            raise S5ScorecardError("S5 reconciliation draft entry is invalid")
        seen_case_ids.add(case_id)
        scorer_totals = entry.get("scorer_totals")
        if (
            not isinstance(scorer_totals, dict)
            or set(scorer_totals) != set(raw_scorer_ids)
            or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 0
                for value in scorer_totals.values()
            )
        ):
            raise S5ScorecardError("S5 reconciliation draft scorer totals are invalid")
        reconciled_total_score = entry.get("reconciled_total_score")
        if not isinstance(reconciled_total_score, int | float) or isinstance(
            reconciled_total_score, bool
        ):
            raise S5ScorecardError("S5 reconciliation draft reconciled score is invalid")
        total_values = tuple(float(value) for value in scorer_totals.values())
        expected_reconciled_total = sum(total_values) / len(total_values)
        if float(reconciled_total_score) != expected_reconciled_total:
            raise S5ScorecardError("S5 reconciliation draft reconciled score is invalid")
        reconciliation_status = _nonblank_string(entry.get("reconciliation_status"))
        expected_status = (
            "identical_blinded_scores"
            if len(set(total_values)) == 1
            else "averaged_two_blinded_scores"
        )
        if reconciliation_status != expected_status:
            raise S5ScorecardError("S5 reconciliation draft status is invalid")
        hard_gate_disposition = _nonblank_string(entry.get("hard_gate_disposition"))
        if hard_gate_disposition not in {"all_met", "not_all_met"}:
            raise S5ScorecardError("S5 reconciliation draft hard-gate disposition is invalid")
        entries.append(
            S5ReconciliationDraftEntry(
                case_id=case_id,
                display_name=display_name,
                scorer_totals={str(key): int(value) for key, value in scorer_totals.items()},
                reconciled_total_score=float(reconciled_total_score),
                reconciliation_status=reconciliation_status,
                hard_gate_disposition=hard_gate_disposition,
            )
        )
    return S5ReconciliationDraftPacket(
        record_type=_RECONCILIATION_DRAFT_RECORD_TYPE,
        gate="S5",
        status=_RECONCILIATION_DRAFT_STATUS,
        outcome_blinded=True,
        results_authorized=False,
        approval_required=True,
        approval_record_path=_S5_APPROVAL_RECORD_PATH,
        source_worksheet_path=str(source_worksheet_path),
        scorer_ids=(str(raw_scorer_ids[0]), str(raw_scorer_ids[1])),
        entries=tuple(entries),
        blocked_actions=tuple(str(action) for action in payload.get("blocked_actions", ())),
    )


def write_s5_scoring_artifacts_packet(root: Path, output: Path) -> Path:
    """Write S5 blinded scorer worksheet artifacts as deterministic JSON."""

    packet = build_s5_scoring_artifacts_packet(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(packet.to_jsonable(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output


def write_s5_reconciliation_draft_packet(
    input_path: Path, output: Path, *, root: Path | None = None
) -> Path:
    """Write the non-authorizing S5 reconciliation draft as deterministic JSON."""

    if output.resolve(strict=False).parts[-3:] == _S5_APPROVAL_RECORD_PARTS:
        raise S5ScorecardError(
            "S5 reconciliation draft output must not be the approval record path"
        )
    packet = build_s5_reconciliation_draft_packet(input_path, root=root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(packet.to_jsonable(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def write_s5_scorecard_packet(root: Path, output: Path) -> Path:
    """Write the S5 scorecard template as deterministic JSON."""

    packet = build_s5_scorecard_packet(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(packet.to_jsonable(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output
