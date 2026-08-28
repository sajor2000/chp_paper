from collections.abc import Iterator, Mapping
from copy import deepcopy
from datetime import date
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, HttpUrl, field_serializer, field_validator


_Key = TypeVar("_Key")
_Value = TypeVar("_Value")


class _ImmutableMapping(Mapping[_Key, _Value]):
    def __init__(self, value: Mapping[_Key, _Value]) -> None:
        self._data = dict(value)

    def __getitem__(self, key: _Key) -> _Value:
        return self._data[key]

    def __iter__(self) -> Iterator[_Key]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Mapping):
            return NotImplemented
        return self._data == dict(other)

    def __deepcopy__(self, memo: dict[int, Any]) -> "_ImmutableMapping[_Key, _Value]":
        copied = _ImmutableMapping(deepcopy(self._data, memo))
        memo[id(self)] = copied
        return copied


_APPROVED_PROHIBITED_VERBS = (
    "cause",
    "caused",
    "causes",
    "drive",
    "drives",
    "drove",
    "effect",
    "effects",
    "impact",
    "impacts",
    "impacted",
    "improve",
    "improves",
    "improved",
    "lead",
    "leads",
    "led",
    "prevent",
    "prevents",
    "prevented",
    "reduce",
    "reduces",
    "reduced",
)
_APPROVED_UNSUPPORTED_SUPERLATIVES = (
    "actionable",
    "comprehensive",
    "first",
    "novel",
    "representative",
    "robust",
    "scalable",
    "unique",
    "validated",
)
_APPROVED_AGENTS = {
    "orchestrator_editor": {
        "responsibility": (
            "Own outline",
            "assignments",
            "budgets",
            "integration",
            "issue log",
            "and gates",
        ),
        "permitted_inputs": (
            "contracts",
            "gate reports",
            "ledgers",
            "authorized section packets",
        ),
        "permitted_outputs": ("integrated control packet", "issue entries"),
        "prohibited_actions": (
            "Invent results",
            "silently resolve scientific conflicts",
        ),
        "human_approval_required": ("Scientific conflicts", "final integration"),
    },
    "artifact_lineage_agent": {
        "responsibility": (
            "Map every number and variable to frozen sources",
            "transformations",
            "and outputs",
        ),
        "permitted_inputs": ("study manifest", "frozen outputs", "provenance reports"),
        "permitted_outputs": ("number ledger", "lineage findings"),
        "prohibited_actions": ("Interpret findings", "alter frozen outputs"),
        "human_approval_required": ("Lineage exceptions",),
    },
    "methods_reporting_agent": {
        "responsibility": (
            "Draft from the signed SAP and maintain reporting",
            "ethics",
            "and sharing crosswalks",
        ),
        "permitted_inputs": ("signed SAP", "source contracts", "reporting rules"),
        "permitted_outputs": ("methods packet", "reporting matrix"),
        "prohibited_actions": ("Back-fit methods to observed results",),
        "human_approval_required": ("Method deviation",),
    },
    "results_agent": {
        "responsibility": (
            "Convert frozen outputs into factual statements and maintain the number ledger",
        ),
        "permitted_inputs": ("S7-approved artifacts", "number ledger"),
        "permitted_outputs": ("results packet",),
        "prohibited_actions": ("Add literature interpretation", "use causal wording"),
        "human_approval_required": ("Result discrepancy",),
    },
    "case_study_1_agent": {
        "responsibility": ("Populate the selected first case template",),
        "permitted_inputs": ("S5 decision", "S7-approved case artifacts"),
        "permitted_outputs": ("case 1 packet",),
        "prohibited_actions": (
            "Change estimands",
            "outcomes",
            "candidate",
            "or multiplicity",
        ),
        "human_approval_required": ("Case conflict",),
    },
    "case_study_2_agent": {
        "responsibility": ("Populate the selected second case template",),
        "permitted_inputs": ("S5 decision", "S7-approved case artifacts"),
        "permitted_outputs": ("case 2 packet",),
        "prohibited_actions": (
            "Change estimands",
            "outcomes",
            "candidate",
            "or multiplicity",
        ),
        "human_approval_required": ("Case conflict",),
    },
    "evidence_claims_agent": {
        "responsibility": (
            "Verify sources and maintain claim support",
            "conflicts",
            "gaps",
            "and language bounds",
        ),
        "permitted_inputs": (
            "evidence matrix",
            "Paperclip repository",
            "official primary sources",
        ),
        "permitted_outputs": ("claim ledger", "citation findings"),
        "prohibited_actions": (
            "Use abstracts alone for material claims",
            "generate references from memory",
        ),
        "human_approval_required": ("Conflicting evidence", "novelty language"),
    },
    "discussion_policy_agent": {
        "responsibility": ("Interpret within evidence bounds and synthesize the selected cases",),
        "permitted_inputs": ("verified claims", "S7-approved results packets"),
        "permitted_outputs": ("discussion packet",),
        "prohibited_actions": (
            "Claim implementation benefit",
            "need",
            "allocation",
            "access",
            "or outcomes",
        ),
        "human_approval_required": ("Policy interpretation",),
    },
    "statistical_qa_agent": {
        "responsibility": (
            "Independently verify estimates",
            "denominators",
            "intervals",
            "diagnostics",
            "and reconciliation",
        ),
        "permitted_inputs": ("frozen artifacts", "SAP", "code", "number ledger"),
        "permitted_outputs": ("numerical review report",),
        "prohibited_actions": ("Strengthen narrative by changing scientific content",),
        "human_approval_required": ("Unresolved numerical discrepancy",),
    },
    "jama_style_qa_agent": {
        "responsibility": (
            "Enforce live journal rules",
            "reporting",
            "files",
            "disclosures",
            "and voice",
        ),
        "permitted_inputs": ("official rules", "draft package", "ledgers", "checklists"),
        "permitted_outputs": ("compliance audit",),
        "prohibited_actions": ("Change scientific content without a logged query",),
        "human_approval_required": ("Rule ambiguity", "submission authorization"),
    },
}
_APPROVED_GATES = {
    "M0": {
        "requires": (),
        "artifacts": (
            "journal contract",
            "style contract",
            "agent contract",
            "gate contract",
        ),
        "acceptance": ("Contracts validate and the journal audit is dated",),
    },
    "M1": {
        "requires": ("S4", "S5", "S6", "S7"),
        "artifacts": (
            "analytic dataset",
            "study manifest",
            "frozen outputs",
            "checksums",
        ),
        "acceptance": ("Every primary number has a frozen artifact ID",),
    },
    "M2": {
        "requires": ("S4",),
        "artifacts": (
            "evidence matrix",
            "Paperclip claim repository",
            "novelty update search",
        ),
        "acceptance": ("Every material non-result claim is verified or labeled a gap",),
    },
    "M3": {
        "requires": ("M0", "M1", "M2"),
        "artifacts": ("outline", "case packets", "disclosure inputs"),
        "acceptance": ("Methods and Results shells have matching order",),
    },
    "M4": {
        "requires": ("M3",),
        "artifacts": (
            "section packets",
            "number ledger",
            "claim ledger",
            "deviation log",
        ),
        "acceptance": ("Integrated draft has no duplicated or inconsistent claim",),
    },
    "M5": {
        "requires": ("M4", "S7", "S8"),
        "artifacts": (
            "numerical review",
            "traceability review",
            "privacy and equity review",
        ),
        "acceptance": ("Independent QA has no unresolved critical or important issue",),
    },
    "M6": {
        "requires": ("M5",),
        "artifacts": (
            "live journal recheck",
            "reporting matrices",
            "disclosure package",
        ),
        "acceptance": ("Submission package passes the complete JAMA audit",),
    },
    "M7": {
        "requires": ("M6",),
        "artifacts": ("author approvals", "closed issue log"),
        "acceptance": ("Named human authors authorize submission",),
    },
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class JournalContract(StrictModel):
    article_type: Literal["Original Investigation"]
    main_text_words: Literal[3000]
    abstract_words: Literal[350]
    title_characters: Literal[100]
    key_points_words: Literal[100]
    max_main_displays: Literal[5]
    reference_range: tuple[Literal[50], Literal[75]]
    abstract_headings: tuple[str, ...]
    key_point_headings: tuple[Literal["Question", "Findings", "Meaning"], ...]
    official_url: HttpUrl
    accessed: date
    revalidate_days_before_submission: Literal[30]


class StyleContract(StrictModel):
    required_measure_phrase: Literal["EHR-diagnosed proportion among observed CAPriCORN adults"]
    paragraph_pattern: Literal["finding -> boundary -> implication"]
    prohibited_observational_verbs: tuple[str, ...]
    unsupported_superlatives: tuple[str, ...]
    policy_boundary: Literal[
        "Findings may formulate planning questions but do not establish need, access, "
        "capacity, underdiagnosis, optimal allocation, care improvement, or outcomes."
    ]

    @field_validator("prohibited_observational_verbs")
    @classmethod
    def require_approved_prohibited_verbs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != _APPROVED_PROHIBITED_VERBS:
            raise ValueError("prohibited observational verbs must match approved authority")
        return value

    @field_validator("unsupported_superlatives")
    @classmethod
    def require_approved_superlatives(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != _APPROVED_UNSUPPORTED_SUPERLATIVES:
            raise ValueError("unsupported superlatives must match approved authority")
        return value


class AgentRole(StrictModel):
    responsibility: tuple[str, ...]
    permitted_inputs: tuple[str, ...]
    permitted_outputs: tuple[str, ...]
    prohibited_actions: tuple[str, ...]
    human_approval_required: tuple[str, ...]


class GateContract(StrictModel):
    requires: tuple[str, ...]
    artifacts: tuple[str, ...]
    acceptance: tuple[str, ...]


class ManuscriptContracts(StrictModel):
    journal: JournalContract
    style: StyleContract
    agents: Mapping[str, AgentRole]
    gates: Mapping[str, GateContract]

    @field_validator("agents")
    @classmethod
    def require_approved_agents(cls, value: Mapping[str, AgentRole]) -> Mapping[str, AgentRole]:
        actual = {
            name: {
                "responsibility": role.responsibility,
                "permitted_inputs": role.permitted_inputs,
                "permitted_outputs": role.permitted_outputs,
                "prohibited_actions": role.prohibited_actions,
                "human_approval_required": role.human_approval_required,
            }
            for name, role in value.items()
        }
        if actual != _APPROVED_AGENTS:
            raise ValueError("agents must match approved authority exactly")
        return _ImmutableMapping(value)

    @field_validator("gates")
    @classmethod
    def require_approved_gates(
        cls, value: Mapping[str, GateContract]
    ) -> Mapping[str, GateContract]:
        actual = {
            name: {
                "requires": gate.requires,
                "artifacts": gate.artifacts,
                "acceptance": gate.acceptance,
            }
            for name, gate in value.items()
        }
        if actual != _APPROVED_GATES:
            raise ValueError("gates must match approved authority exactly")
        return _ImmutableMapping(value)

    @field_serializer("agents")
    def serialize_agents(self, value: Mapping[str, AgentRole]) -> dict[str, AgentRole]:
        return dict(value)

    @field_serializer("gates")
    def serialize_gates(self, value: Mapping[str, GateContract]) -> dict[str, GateContract]:
        return dict(value)
