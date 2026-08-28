# Agentic JAMA Manuscript Control Plane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, fail-closed manuscript control plane that freezes JAMA rules, agent roles, claim/number/AI ledgers, scientific gate status, mirrored case-study packets, and submission audits without drafting unapproved results.

**Architecture:** Add a focused `chicagohealthmap.manuscript` package backed by versioned YAML contracts and CSV/JSON ledgers. Typer commands generate and verify manuscript-control artifacts from immutable project evidence, while every results-bearing operation remains blocked until S5-S7 pass. The post-S7 prose and document assembly workflow is deliberately deferred to a second implementation plan created only after the analytic dataset and outputs are frozen.

**Tech Stack:** Python 3.12, Pydantic 2, PyYAML, pandas, Typer, pytest, Ruff, mypy, Markdown, CSV, JSON.

## Global Constraints

- Target JAMA Health Forum Original Investigation: no more than 3000 main-text words, 350 abstract words, 100 title characters, 100 Key Points words, and 5 combined main tables/figures; revalidate official rules within 30 days of submission.
- ChicagoHealthMap.com/CAPriCORN remains the primary clinical and spatial base; public sources cannot replace or relabel its outcome, denominator, geography, phenotype, or suppression semantics.
- Anticipated cardiometabolic and COPD cases remain provisional until outcome-blinded S5 approval.
- No Results prose, result packet, abstract finding, Key Points finding, or conclusion may be generated before S7 passes and frozen artifact checksums exist.
- Result claims require frozen artifact identifiers; material non-result claims require a verified Paperclip or official-primary-source record.
- EHR measures must retain source-qualified diagnosed-proportion semantics and cannot be relabeled as population prevalence.
- Null or inconvenient findings cannot trigger case substitution, estimand changes, or stronger causal language.
- FQHC/CBO outputs remain questions and planning demonstrations unless implementation outcomes were evaluated.
- Agent-generated references are prohibited; every citation must be independently verified by identifier, title, authors, year, and exact supporting location.
- Protected paths, row-level protected data, credentials, and secrets must not enter manuscript artifacts or agent prompts.
- AI assistance must be logged contemporaneously with platform/model, manufacturer, dates, use, affected artifact, and human verification; unavailable version details are recorded as unavailable, never inferred.
- Tests follow strict RED-GREEN-REFACTOR; every task ends with focused verification, full regression checks proportional to risk, independent review, and a focused commit.

---

## File responsibility map

| Path | Responsibility |
|---|---|
| `config/manuscript/jama_health_forum.yml` | Dated journal limits, headings, required files, and revalidation policy |
| `config/manuscript/style_contract.yml` | Approved CLIF-informed voice, measure language, and prohibited inference rules |
| `config/manuscript/agents.yml` | Agent roles, permitted inputs/outputs, prohibited actions, and human authority |
| `config/manuscript/gates.yml` | M0-M7 manuscript gates and S4-S8 dependencies |
| `src/chicagohealthmap/manuscript/models.py` | Strict immutable Pydantic contract models |
| `src/chicagohealthmap/manuscript/contracts.py` | YAML loading, canonical serialization, and contract verification |
| `src/chicagohealthmap/manuscript/ledgers.py` | Claim, number, AI-use, and issue ledger schemas and validation |
| `src/chicagohealthmap/manuscript/gates.py` | Fail-closed scientific/manuscript gate evaluation |
| `src/chicagohealthmap/manuscript/packets.py` | Deterministic outline and mirrored case-study packet generation |
| `src/chicagohealthmap/manuscript/audit.py` | Cross-artifact JAMA, traceability, language, and disclosure audit |
| `docs/manuscript/` | Human-readable outline, case template, language lexicon, and checklist |
| `outputs/manuscript/control/` | Ignored generated contracts, ledgers, gate reports, packets, and audit reports |
| `tests/unit/manuscript/` | Contract, ledger, gate, packet, and audit behavior tests |
| `tests/integration/test_manuscript_control_cli.py` | End-to-end offline CLI tests |

---

### Task 1: Freeze machine-readable JAMA, style, agent, and gate contracts

**Files:**
- Create: `config/manuscript/jama_health_forum.yml`
- Create: `config/manuscript/style_contract.yml`
- Create: `config/manuscript/agents.yml`
- Create: `config/manuscript/gates.yml`
- Create: `src/chicagohealthmap/manuscript/__init__.py`
- Create: `src/chicagohealthmap/manuscript/models.py`
- Create: `src/chicagohealthmap/manuscript/contracts.py`
- Create: `tests/unit/manuscript/conftest.py`
- Create: `tests/unit/manuscript/test_contracts.py`

**Interfaces:**
- Consumes: approved design `docs/superpowers/specs/2026-07-14-agentic-jama-manuscript-blueprint-design.md`.
- Produces: `ManuscriptContracts` and `load_manuscript_contracts(root: Path) -> ManuscriptContracts`.

- [ ] **Step 1: Write failing strict-contract tests**

```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from chicagohealthmap.manuscript.contracts import load_manuscript_contracts
from chicagohealthmap.manuscript.models import JournalContract


def test_repository_contracts_freeze_approved_limits() -> None:
    root = Path(__file__).resolve().parents[3]
    contracts = load_manuscript_contracts(root)
    assert contracts.journal.article_type == "Original Investigation"
    assert contracts.journal.main_text_words == 3000
    assert contracts.journal.abstract_words == 350
    assert contracts.journal.title_characters == 100
    assert contracts.journal.key_points_words == 100
    assert contracts.journal.max_main_displays == 5
    assert contracts.journal.reference_range == (50, 75)
    assert contracts.style.required_measure_phrase == (
        "EHR-diagnosed proportion among observed CAPriCORN adults"
    )
    assert set(contracts.agents) == {
        "orchestrator_editor", "artifact_lineage_agent", "methods_reporting_agent",
        "results_agent", "case_study_1_agent", "case_study_2_agent",
        "evidence_claims_agent", "discussion_policy_agent", "statistical_qa_agent",
        "jama_style_qa_agent",
    }
    assert contracts.gates["M1"].requires == ("S4", "S5", "S6", "S7")


def test_journal_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        JournalContract.model_validate(
            {
                "article_type": "Original Investigation",
                "main_text_words": 3000,
                "abstract_words": 350,
                "title_characters": 100,
                "key_points_words": 100,
                "max_main_displays": 5,
                "reference_range": [50, 75],
                "abstract_headings": ["Importance", "Objective", "Design", "Setting", "Participants", "Exposures", "Main Outcomes and Measures", "Results", "Conclusions and Relevance"],
                "key_point_headings": ["Question", "Findings", "Meaning"],
                "official_url": "https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors",
                "accessed": "2026-07-14",
                "revalidate_days_before_submission": 30,
                "unexpected": True,
            }
        )
```

- [ ] **Step 2: Run the tests and observe RED**

Run: `uv run pytest tests/unit/manuscript/test_contracts.py -v`  
Expected: collection fails because `chicagohealthmap.manuscript` does not exist.

- [ ] **Step 3: Implement strict immutable models**

```python
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator


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
    required_measure_phrase: str
    paragraph_pattern: Literal["finding -> boundary -> implication"]
    prohibited_observational_verbs: tuple[str, ...]
    unsupported_superlatives: tuple[str, ...]
    policy_boundary: str


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
    agents: dict[str, AgentRole]
    gates: dict[str, GateContract]

    @field_validator("gates")
    @classmethod
    def require_all_manuscript_gates(cls, value: dict[str, GateContract]) -> dict[str, GateContract]:
        expected = {f"M{index}" for index in range(8)}
        if set(value) != expected:
            raise ValueError(f"gates must be exactly {sorted(expected)}")
        return value
```

- [ ] **Step 4: Write the four YAML contracts with exact approved values**

Write `jama_health_forum.yml` exactly as:

```yaml
article_type: Original Investigation
main_text_words: 3000
abstract_words: 350
title_characters: 100
key_points_words: 100
max_main_displays: 5
reference_range: [50, 75]
abstract_headings:
  - Importance
  - Objective
  - Design
  - Setting
  - Participants
  - Exposures
  - Main Outcomes and Measures
  - Results
  - Conclusions and Relevance
key_point_headings: [Question, Findings, Meaning]
official_url: https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors
accessed: 2026-07-14
revalidate_days_before_submission: 30
```

Write `style_contract.yml` exactly as:

```yaml
required_measure_phrase: EHR-diagnosed proportion among observed CAPriCORN adults
paragraph_pattern: finding -> boundary -> implication
prohibited_observational_verbs: [cause, caused, causes, drive, drives, drove, effect, effects, impact, impacts, impacted, improve, improves, improved, lead, leads, led, prevent, prevents, prevented, reduce, reduces, reduced]
unsupported_superlatives: [actionable, comprehensive, first, novel, representative, robust, scalable, unique, validated]
policy_boundary: Findings may formulate planning questions but do not establish need, access, capacity, underdiagnosis, optimal allocation, care improvement, or outcomes.
```

Write `agents.yml` with exactly these role keys and no aliases:

```yaml
agents:
  orchestrator_editor:
    responsibility: [Own outline, assignments, budgets, integration, issue log, and gates]
    permitted_inputs: [contracts, gate reports, ledgers, authorized section packets]
    permitted_outputs: [integrated control packet, issue entries]
    prohibited_actions: [Invent results, silently resolve scientific conflicts]
    human_approval_required: [Scientific conflicts, final integration]
  artifact_lineage_agent:
    responsibility: [Map every number and variable to frozen sources, transformations, and outputs]
    permitted_inputs: [study manifest, frozen outputs, provenance reports]
    permitted_outputs: [number ledger, lineage findings]
    prohibited_actions: [Interpret findings, alter frozen outputs]
    human_approval_required: [Lineage exceptions]
  methods_reporting_agent:
    responsibility: [Draft from the signed SAP and maintain reporting, ethics, and sharing crosswalks]
    permitted_inputs: [signed SAP, source contracts, reporting rules]
    permitted_outputs: [methods packet, reporting matrix]
    prohibited_actions: [Back-fit methods to observed results]
    human_approval_required: [Method deviation]
  results_agent:
    responsibility: [Convert frozen outputs into factual statements and maintain the number ledger]
    permitted_inputs: [S7-approved artifacts, number ledger]
    permitted_outputs: [results packet]
    prohibited_actions: [Add literature interpretation, use causal wording]
    human_approval_required: [Result discrepancy]
  case_study_1_agent:
    responsibility: [Populate the selected first case template]
    permitted_inputs: [S5 decision, S7-approved case artifacts]
    permitted_outputs: [case 1 packet]
    prohibited_actions: [Change estimands, outcomes, candidate, or multiplicity]
    human_approval_required: [Case conflict]
  case_study_2_agent:
    responsibility: [Populate the selected second case template]
    permitted_inputs: [S5 decision, S7-approved case artifacts]
    permitted_outputs: [case 2 packet]
    prohibited_actions: [Change estimands, outcomes, candidate, or multiplicity]
    human_approval_required: [Case conflict]
  evidence_claims_agent:
    responsibility: [Verify sources and maintain claim support, conflicts, gaps, and language bounds]
    permitted_inputs: [evidence matrix, Paperclip repository, official primary sources]
    permitted_outputs: [claim ledger, citation findings]
    prohibited_actions: [Use abstracts alone for material claims, generate references from memory]
    human_approval_required: [Conflicting evidence, novelty language]
  discussion_policy_agent:
    responsibility: [Interpret within evidence bounds and synthesize the selected cases]
    permitted_inputs: [verified claims, S7-approved results packets]
    permitted_outputs: [discussion packet]
    prohibited_actions: [Claim implementation benefit, need, allocation, access, or outcomes]
    human_approval_required: [Policy interpretation]
  statistical_qa_agent:
    responsibility: [Independently verify estimates, denominators, intervals, diagnostics, and reconciliation]
    permitted_inputs: [frozen artifacts, SAP, code, number ledger]
    permitted_outputs: [numerical review report]
    prohibited_actions: [Strengthen narrative by changing scientific content]
    human_approval_required: [Unresolved numerical discrepancy]
  jama_style_qa_agent:
    responsibility: [Enforce live journal rules, reporting, files, disclosures, and voice]
    permitted_inputs: [official rules, draft package, ledgers, checklists]
    permitted_outputs: [compliance audit]
    prohibited_actions: [Change scientific content without a logged query]
    human_approval_required: [Rule ambiguity, submission authorization]
```

Write `gates.yml` exactly as:

```yaml
gates:
  M0:
    requires: []
    artifacts: [journal contract, style contract, agent contract, gate contract]
    acceptance: [Contracts validate and the journal audit is dated]
  M1:
    requires: [S4, S5, S6, S7]
    artifacts: [analytic dataset, study manifest, frozen outputs, checksums]
    acceptance: [Every primary number has a frozen artifact ID]
  M2:
    requires: [S4]
    artifacts: [evidence matrix, Paperclip claim repository, novelty update search]
    acceptance: [Every material non-result claim is verified or labeled a gap]
  M3:
    requires: [M0, M1, M2]
    artifacts: [outline, case packets, disclosure inputs]
    acceptance: [Methods and Results shells have matching order]
  M4:
    requires: [M3]
    artifacts: [section packets, number ledger, claim ledger, deviation log]
    acceptance: [Integrated draft has no duplicated or inconsistent claim]
  M5:
    requires: [M4, S7, S8]
    artifacts: [numerical review, traceability review, privacy and equity review]
    acceptance: [Independent QA has no unresolved critical or important issue]
  M6:
    requires: [M5]
    artifacts: [live journal recheck, reporting matrices, disclosure package]
    acceptance: [Submission package passes the complete JAMA audit]
  M7:
    requires: [M6]
    artifacts: [author approvals, closed issue log]
    acceptance: [Named human authors authorize submission]
```

- [ ] **Step 5: Add shared test fixtures**

Create `tests/unit/manuscript/conftest.py` with the complete fixtures used by later tasks:

```python
from dataclasses import dataclass
import json
from pathlib import Path
import shutil

import pandas as pd
import pytest

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.manuscript.contracts import load_manuscript_contracts


@dataclass
class SandboxProject:
    root: Path

    @property
    def paths(self) -> ProjectPaths:
        return ProjectPaths.from_root(self.root)

    def write_gate(self, gate: str, status: str) -> None:
        destination = self.root / "outputs" / "governance" / "gates"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / f"{gate}.json").write_text(
            json.dumps({"gate": gate, "status": status}, sort_keys=True) + "\n",
            encoding="utf-8",
        )


@pytest.fixture
def tmp_project(tmp_path: Path) -> SandboxProject:
    root = Path(__file__).resolve().parents[3]
    (tmp_path / "config").mkdir()
    (tmp_path / "docs").mkdir()
    shutil.copytree(root / "config" / "manuscript", tmp_path / "config" / "manuscript")
    if (root / "docs" / "manuscript").is_dir():
        shutil.copytree(root / "docs" / "manuscript", tmp_path / "docs" / "manuscript")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\nversion='0'\n", encoding="utf-8")
    return SandboxProject(tmp_path)


@pytest.fixture
def authorized_project(tmp_project: SandboxProject) -> SandboxProject:
    for gate in ("S4", "S5", "S6", "S7", "S8"):
        tmp_project.write_gate(gate, "passed")
    return tmp_project


@pytest.fixture
def contracts():
    return load_manuscript_contracts(Path(__file__).resolve().parents[3])


@pytest.fixture
def control_dir(tmp_path: Path) -> Path:
    headers = {
        "claim_ledger.csv": ["claim_id", "section", "draft_claim", "claim_class", "source_or_artifact_id", "exact_support_location", "population_geography_measure_period_match", "support_strength", "conflict_or_gap", "allowed_wording", "prohibited_inference", "result_status", "owner", "verified_by", "verified_date", "final_text_location"],
        "number_ledger.csv": ["number_id", "artifact_id", "checksum", "artifact_field", "code_version", "population", "exclusions", "geography", "time_period", "measure", "unit", "denominator", "raw_value", "display_value", "uncertainty", "result_status", "manuscript_locations"],
        "ai_use_ledger.csv": ["ai_use_id", "platform", "model", "manufacturer", "start_date", "end_date", "use", "affected_artifact", "human_verifier", "verified_date"],
        "issue_ledger.csv": ["issue_id", "severity", "gate", "description", "evidence", "owner", "status", "resolution"],
    }
    for filename, columns in headers.items():
        pd.DataFrame(columns=columns).to_csv(tmp_path / filename, index=False)
    return tmp_path
```

- [ ] **Step 6: Implement canonical contract loading**

```python
from pathlib import Path
from typing import Any

import yaml

from chicagohealthmap.manuscript.models import ManuscriptContracts


def _read_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path.name} must contain a mapping")
    return loaded


def load_manuscript_contracts(root: Path) -> ManuscriptContracts:
    directory = root / "config" / "manuscript"
    return ManuscriptContracts.model_validate(
        {
            "journal": _read_yaml(directory / "jama_health_forum.yml"),
            "style": _read_yaml(directory / "style_contract.yml"),
            "agents": _read_yaml(directory / "agents.yml")["agents"],
            "gates": _read_yaml(directory / "gates.yml")["gates"],
        }
    )
```

- [ ] **Step 7: Run focused and static checks**

Run: `uv run pytest tests/unit/manuscript/test_contracts.py -v`  
Expected: PASS.  
Run: `uv run ruff check src/chicagohealthmap/manuscript tests/unit/manuscript`  
Expected: `All checks passed!`.  
Run: `uv run mypy src/chicagohealthmap/manuscript`  
Expected: success with no issues.

- [ ] **Step 8: Commit the contracts**

```bash
git add config/manuscript src/chicagohealthmap/manuscript tests/unit/manuscript/conftest.py tests/unit/manuscript/test_contracts.py
git commit -m "feat: freeze manuscript authority contracts"
```

---

### Task 2: Implement claim, number, AI-use, and issue ledgers

**Files:**
- Create: `src/chicagohealthmap/manuscript/ledgers.py`
- Create: `tests/unit/manuscript/test_ledgers.py`
- Create: `docs/manuscript/ledger_dictionary.md`

**Interfaces:**
- Consumes: `ManuscriptContracts` from Task 1.
- Produces: `ClaimRecord`, `NumberRecord`, `AiUseRecord`, `IssueRecord`, and `verify_ledgers(control_dir: Path, contracts: ManuscriptContracts) -> LedgerReport`.

- [ ] **Step 1: Write failing ledger tests**

```python
from pathlib import Path

import pandas as pd
import pytest

from chicagohealthmap.manuscript.ledgers import LedgerError, verify_ledgers


def test_result_claim_requires_frozen_artifact(control_dir: Path, contracts) -> None:
    claim = {
        "claim_id": "R-001",
        "section": "Results",
        "draft_claim": "x",
        "claim_class": "result",
        "source_or_artifact_id": "",
        "exact_support_location": "",
        "population_geography_measure_period_match": "exact",
        "support_strength": "frozen",
        "conflict_or_gap": "",
        "allowed_wording": "associated with",
        "prohibited_inference": "caused",
        "result_status": "prespecified",
        "owner": "results agent",
        "verified_by": "",
        "verified_date": "",
        "final_text_location": "",
    }
    pd.DataFrame(
        [claim]
    ).to_csv(control_dir / "claim_ledger.csv", index=False)
    with pytest.raises(LedgerError, match="result claim R-001 requires a frozen artifact"):
        verify_ledgers(control_dir, contracts)


def test_ai_use_requires_human_verification(control_dir: Path, contracts) -> None:
    pd.DataFrame(
        [{"ai_use_id": "AI-001", "platform": "OpenAI Codex", "model": "unavailable", "manufacturer": "OpenAI", "start_date": "2026-07-14", "end_date": "2026-07-14", "use": "outline design", "affected_artifact": "blueprint", "human_verifier": "", "verified_date": ""}]
    ).to_csv(control_dir / "ai_use_ledger.csv", index=False)
    with pytest.raises(LedgerError, match="AI-001 lacks human verification"):
        verify_ledgers(control_dir, contracts)
```

- [ ] **Step 2: Run the tests and observe RED**

Run: `uv run pytest tests/unit/manuscript/test_ledgers.py -v`  
Expected: FAIL because the ledger module does not exist.

- [ ] **Step 3: Implement strict ledger records and verification**

```python
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, field_validator

from chicagohealthmap.manuscript.models import ManuscriptContracts


class LedgerError(ValueError):
    pass


class LedgerModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ClaimRecord(LedgerModel):
    claim_id: str
    section: str
    draft_claim: str
    claim_class: Literal["result", "method", "resource", "novelty", "prior_evidence", "interpretation", "policy", "limitation"]
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
    def empty_verified_date_is_none(cls, value: object) -> object:
        return None if value == "" else value


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

    @field_validator("verified_date", mode="before")
    @classmethod
    def empty_verified_date_is_none(cls, value: object) -> object:
        return None if value == "" else value


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


def verify_ledgers(control_dir: Path, contracts: ManuscriptContracts) -> LedgerReport:
    claims = [ClaimRecord.model_validate(row) for row in pd.read_csv(control_dir / "claim_ledger.csv", keep_default_na=False).to_dict("records")]
    numbers = [NumberRecord.model_validate(row) for row in pd.read_csv(control_dir / "number_ledger.csv", keep_default_na=False).to_dict("records")]
    ai_uses = [AiUseRecord.model_validate(row) for row in pd.read_csv(control_dir / "ai_use_ledger.csv", keep_default_na=False).to_dict("records")]
    issues = [IssueRecord.model_validate(row) for row in pd.read_csv(control_dir / "issue_ledger.csv", keep_default_na=False).to_dict("records")]
    for claim in claims:
        if claim.claim_class == "result" and (not claim.source_or_artifact_id or not claim.exact_support_location):
            raise LedgerError(f"result claim {claim.claim_id} requires a frozen artifact")
        if claim.claim_class != "result" and claim.support_strength == "verified" and not claim.verified_by:
            raise LedgerError(f"verified claim {claim.claim_id} lacks an independent verifier")
    number_ids = {record.number_id for record in numbers}
    if len(number_ids) != len(numbers):
        raise LedgerError("number IDs must be unique")
    for record in ai_uses:
        if not record.human_verifier or record.verified_date is None:
            raise LedgerError(f"{record.ai_use_id} lacks human verification")
    return LedgerReport(len(claims), len(numbers), len(ai_uses), sum(issue.severity == "critical" and issue.status == "open" for issue in issues))
```

- [ ] **Step 4: Add exact empty-ledger headers and the human dictionary**

Generate header-only CSV files only under ignored `outputs/manuscript/control/`; do not
commit generated ledgers. `docs/manuscript/ledger_dictionary.md` must define every field,
allowed enum, evidence rule, and responsible human role shown above.

- [ ] **Step 5: Run focused tests and commit**

Run: `uv run pytest tests/unit/manuscript/test_ledgers.py -v`  
Expected: PASS.

```bash
git add src/chicagohealthmap/manuscript/ledgers.py tests/unit/manuscript/test_ledgers.py docs/manuscript/ledger_dictionary.md
git commit -m "feat: enforce manuscript evidence ledgers"
```

---

### Task 3: Implement fail-closed scientific and manuscript gates

**Files:**
- Create: `src/chicagohealthmap/manuscript/gates.py`
- Create: `tests/unit/manuscript/test_gates.py`
- Modify: `src/chicagohealthmap/cli.py`

**Interfaces:**
- Consumes: `config/manuscript/gates.yml`, `docs/analysis/decision_log.md`, ignored gate evidence JSON, and ledger verification.
- Produces: `evaluate_manuscript_gates(paths: ProjectPaths) -> GateReport` and CLI `manuscript gates --check`.

- [ ] **Step 1: Write failing closed-gate and no-results tests**

```python
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.manuscript.gates import ManuscriptGateError, assert_results_authorized


def test_results_are_blocked_without_s7(tmp_project) -> None:
    tmp_project.write_gate("S4", "passed")
    tmp_project.write_gate("S5", "passed")
    tmp_project.write_gate("S6", "passed")
    tmp_project.write_gate("S7", "open")
    with pytest.raises(ManuscriptGateError, match="S7 must pass"):
        assert_results_authorized(tmp_project.paths)


def test_s7_pass_without_frozen_artifact_checksums_is_invalid(tmp_project) -> None:
    for gate in ("S4", "S5", "S6"):
        tmp_project.write_gate(gate, "passed")
    tmp_project.write_gate("S7", "passed")
    with pytest.raises(ManuscriptGateError, match="S7 requires frozen artifact checksums"):
        assert_results_authorized(tmp_project.paths)


def test_cli_returns_nonzero_for_open_required_gate(tmp_project, monkeypatch) -> None:
    monkeypatch.chdir(tmp_project.root)
    result = CliRunner().invoke(app, ["manuscript", "gates", "--check"])
    assert result.exit_code == 1
    assert "Manuscript gates failed" in result.output
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/unit/manuscript/test_gates.py -v`  
Expected: FAIL because gate functions and CLI do not exist.

- [ ] **Step 3: Implement exact gate evaluation**

```python
from dataclasses import dataclass
from pathlib import Path

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.manuscript.contracts import load_manuscript_contracts


class ManuscriptGateError(ValueError):
    pass


@dataclass(frozen=True)
class GateReport:
    passed: tuple[str, ...]
    open: tuple[str, ...]
    blocked: tuple[str, ...]
    results_authorized: bool


def _read_scientific_gate(root: Path, gate: str) -> str:
    path = root / "outputs" / "governance" / "gates" / f"{gate}.json"
    if not path.is_file():
        return "missing"
    import json
    loaded = json.loads(path.read_text(encoding="utf-8"))
    status = loaded.get("status")
    return status if status in {"passed", "open", "blocked"} else "invalid"


def _validate_s7_artifacts(root: Path) -> None:
    from hashlib import sha256
    import json
    import re
    path = root / "outputs" / "governance" / "gates" / "S7.json"
    loaded = json.loads(path.read_text(encoding="utf-8"))
    artifacts = loaded.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ManuscriptGateError("S7 requires frozen artifact checksums")
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {"artifact_id", "path", "sha256"}:
            raise ManuscriptGateError("S7 requires frozen artifact checksums")
        artifact_id = artifact["artifact_id"]
        raw_path = artifact["path"]
        digest = artifact["sha256"]
        if not isinstance(artifact_id, str) or not artifact_id or not isinstance(raw_path, str) or not isinstance(digest, str):
            raise ManuscriptGateError("S7 requires frozen artifact checksums")
        relative = Path(raw_path)
        if relative.is_absolute() or ".." in relative.parts or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ManuscriptGateError("S7 requires frozen artifact checksums")
        source = (root / relative).resolve()
        try:
            source.relative_to(root.resolve())
        except ValueError:
            raise ManuscriptGateError("S7 artifact escapes repository root") from None
        if not source.is_file():
            raise ManuscriptGateError(f"S7 artifact checksum mismatch: {artifact_id}")
        hasher = sha256()
        with source.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
        if hasher.hexdigest() != digest:
            raise ManuscriptGateError(f"S7 artifact checksum mismatch: {artifact_id}")


def assert_results_authorized(paths: ProjectPaths) -> None:
    for gate in ("S4", "S5", "S6", "S7"):
        if _read_scientific_gate(paths.root, gate) != "passed":
            raise ManuscriptGateError(f"{gate} must pass before results are authorized")
    _validate_s7_artifacts(paths.root)


def evaluate_manuscript_gates(paths: ProjectPaths) -> GateReport:
    contracts = load_manuscript_contracts(paths.root)
    scientific = {gate: _read_scientific_gate(paths.root, gate) for gate in ("S4", "S5", "S6", "S7", "S8")}
    if scientific["S7"] == "passed":
        _validate_s7_artifacts(paths.root)
    passed: list[str] = []
    blocked: list[str] = []
    resolved = {name for name, status in scientific.items() if status == "passed"}
    for name in (f"M{index}" for index in range(8)):
        contract = contracts.gates[name]
        missing = [required for required in contract.requires if required not in resolved]
        if missing:
            blocked.append(name)
        else:
            passed.append(name)
            resolved.add(name)
    open_gates = tuple(gate for gate, status in scientific.items() if status != "passed")
    return GateReport(tuple(passed), open_gates, tuple(blocked), all(scientific[gate] == "passed" for gate in ("S4", "S5", "S6", "S7")))
```

- [ ] **Step 4: Wire a manuscript Typer group and `gates --check`**

Add these imports and registrations to `cli.py`:

```python
from chicagohealthmap.manuscript.contracts import load_manuscript_contracts
from chicagohealthmap.manuscript.gates import (
    ManuscriptGateError,
    evaluate_manuscript_gates,
)
from chicagohealthmap.manuscript.ledgers import LedgerError, verify_ledgers

manuscript_app = typer.Typer(no_args_is_help=True)
app.add_typer(manuscript_app, name="manuscript")
```

Add the exact command:

```python
@manuscript_app.command("gates")
def manuscript_gates_command(check: bool = typer.Option(False, "--check")) -> None:
    """Report manuscript/scientific gate state and fail on blocked authority."""
    if not check:
        raise typer.BadParameter("gate validation requires --check", param_hint="--check")
    try:
        paths = ProjectPaths.discover()
        report = evaluate_manuscript_gates(paths)
        control = paths.root / "outputs" / "manuscript" / "control"
        if (control / "issue_ledger.csv").is_file():
            contracts = load_manuscript_contracts(paths.root)
            ledger_report = verify_ledgers(control, contracts)
            if ledger_report.open_critical_issues:
                raise ManuscriptGateError("open critical manuscript issue")
    except (LedgerError, OSError, ValidationError, yaml.YAMLError, ValueError) as error:
        typer.echo(f"Manuscript gates failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(json.dumps(report.__dict__, indent=2, sort_keys=True))
    if "M0" in report.blocked or "M1" in report.blocked:
        typer.echo("Manuscript gates failed: required authority remains blocked", err=True)
        raise typer.Exit(code=1)
```

The command exits 1 whenever M0 or M1 is blocked or a gate record is invalid.

- [ ] **Step 5: Run focused tests and commit**

Run: `uv run pytest tests/unit/manuscript/test_gates.py tests/unit/test_cli.py -v`  
Expected: PASS.

```bash
git add src/chicagohealthmap/manuscript/gates.py src/chicagohealthmap/cli.py tests/unit/manuscript/test_gates.py
git commit -m "feat: enforce manuscript scientific gates"
```

---

### Task 4: Generate deterministic outline and mirrored case-study packets

**Files:**
- Create: `src/chicagohealthmap/manuscript/packets.py`
- Create: `tests/unit/manuscript/test_packets.py`
- Create: `docs/manuscript/outline.md`
- Create: `docs/manuscript/case_study_template.md`
- Create: `docs/manuscript/claim_language_lexicon.md`

**Interfaces:**
- Consumes: contracts, gate report, SAP, and case-selection record.
- Produces: `build_control_packets(paths: ProjectPaths) -> tuple[Path, ...]`; generated packets contain no result values while S7 is open.

- [ ] **Step 1: Write failing mirrored-structure and leakage tests**

```python
from chicagohealthmap.manuscript.packets import build_control_packets


def test_case_packets_are_mirrored_and_provisional_before_s5(tmp_project) -> None:
    paths = build_control_packets(tmp_project.paths)
    case_paths = [path for path in paths if path.name.startswith("case_")]
    assert [path.name for path in case_paths] == ["case_1.md", "case_2.md"]
    bodies = [path.read_text(encoding="utf-8") for path in case_paths]
    headings = [line for line in bodies[0].splitlines() if line.startswith("## ")]
    assert headings == [line for line in bodies[1].splitlines() if line.startswith("## ")]
    assert "PROVISIONAL — PENDING S5" in bodies[0]
    assert "PROVISIONAL — PENDING S5" in bodies[1]


def test_pre_s7_packets_contain_no_result_placeholders_or_values(tmp_project) -> None:
    for path in build_control_packets(tmp_project.paths):
        if not path.name.startswith("case_"):
            continue
        body = path.read_text(encoding="utf-8")
        assert "## Results" not in body
        assert "effect size" not in body.lower()
        assert "p =" not in body.lower()
        assert "TBD" not in body
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/unit/manuscript/test_packets.py -v`  
Expected: FAIL because packet generation does not exist.

- [ ] **Step 3: Implement the exact eight-section case template**

```python
from pathlib import Path

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.manuscript.gates import evaluate_manuscript_gates


CASE_HEADINGS = (
    "Why this case",
    "Prespecified estimand",
    "Eligibility and data quality",
    "Pattern and comparator contract",
    "Primary estimate contract",
    "Supportive analyses contract",
    "Interpretive boundary",
    "Platform lesson",
)


def _case_packet(case_number: int, provisional_name: str, provisional: bool) -> str:
    status = "PROVISIONAL — PENDING S5" if provisional else "SELECTED AT S5"
    lines = [f"# Case Study {case_number}: {provisional_name}", "", f"**Status:** {status}", ""]
    for heading in CASE_HEADINGS:
        lines.extend([f"## {heading}", "", "Authorized inputs and required verification are defined by the signed SAP and manuscript contracts.", ""])
    return "\n".join(lines)


def build_control_packets(paths: ProjectPaths) -> tuple[Path, ...]:
    report = evaluate_manuscript_gates(paths)
    output = paths.root / "outputs" / "manuscript" / "control"
    output.mkdir(parents=True, exist_ok=True)
    case_names = ("Cardiometabolic hypertension and diabetes", "Respiratory COPD")
    case_paths: list[Path] = []
    for index, name in enumerate(case_names, start=1):
        path = output / f"case_{index}.md"
        path.write_text(_case_packet(index, name, "S5" in report.open), encoding="utf-8")
        case_paths.append(path)
    outline = output / "outline.md"
    outline.write_text((paths.root / "docs" / "manuscript" / "outline.md").read_text(encoding="utf-8"), encoding="utf-8")
    return (outline, *case_paths)
```

- [ ] **Step 4: Write exact human-readable templates**

`outline.md` must contain the approved 250-300/850-950/850-950/850-950 section
budgets, five displays, and supplement destinations. `case_study_template.md` must define
the eight headings and required fields. `claim_language_lexicon.md` must reproduce the
approved required measure phrase, associational verbs, prohibited causal verbs,
unsupported superlatives, and conditional planning language.

- [ ] **Step 5: Run focused tests and commit**

Run: `uv run pytest tests/unit/manuscript/test_packets.py -v`  
Expected: PASS.

```bash
git add src/chicagohealthmap/manuscript/packets.py tests/unit/manuscript/test_packets.py docs/manuscript
git commit -m "feat: generate gated case study packets"
```

---

### Task 5: Implement JAMA, traceability, language, and disclosure audits

**Files:**
- Create: `src/chicagohealthmap/manuscript/audit.py`
- Create: `tests/unit/manuscript/test_audit.py`
- Create: `docs/manuscript/submission_checklist.md`
- Create: `docs/manuscript/reporting_matrix.csv`
- Modify: `src/chicagohealthmap/cli.py`

**Interfaces:**
- Consumes: contracts, ledgers, gate report, packet files, and later manuscript Markdown.
- Produces: `audit_manuscript_control(paths: ProjectPaths) -> AuditReport` and CLI `manuscript audit --control`.

- [ ] **Step 1: Write failing audit tests**

```python
from pathlib import Path

import pandas as pd
import pytest

from chicagohealthmap.manuscript.audit import ManuscriptAuditError, audit_text


def test_audit_rejects_population_prevalence_label(contracts) -> None:
    with pytest.raises(ManuscriptAuditError, match="unqualified prevalence"):
        audit_text("COPD prevalence was highest in Area A.", contracts)


def test_audit_rejects_observational_causal_verb(contracts) -> None:
    with pytest.raises(ManuscriptAuditError, match="prohibited observational verb: drove"):
        audit_text("Higher diagnosed proportion drove lower life expectancy.", contracts)


def test_audit_accepts_approved_measure_language(contracts) -> None:
    audit_text(
        "A higher EHR-diagnosed proportion among observed CAPriCORN adults was associated with lower area life expectancy.",
        contracts,
    )


def test_reporting_matrix_declares_all_required_frameworks() -> None:
    root = Path(__file__).resolve().parents[3]
    matrix = pd.read_csv(root / "docs" / "manuscript" / "reporting_matrix.csv")
    assert set(matrix["framework"]) == {"JAMA Health Forum", "STROBE", "RECORD", "STROBE-Equity", "SAGER"}
    assert set(matrix["status"]) == {"not_assessed"}
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/unit/manuscript/test_audit.py -v`  
Expected: FAIL because audit functions do not exist.

- [ ] **Step 3: Implement deterministic text and control audits**

```python
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
    pass


@dataclass(frozen=True)
class AuditReport:
    checks: int
    failures: tuple[str, ...]


def audit_text(text: str, contracts: ManuscriptContracts) -> None:
    lowered = text.casefold()
    if "/users/" in lowered or "sources/first_party/capricorn/snapshots" in lowered:
        raise ManuscriptAuditError("protected path")
    if re.search(r"\b(?:hypertension|diabetes|copd|disease) prevalence\b", lowered):
        raise ManuscriptAuditError("unqualified prevalence")
    for verb in contracts.style.prohibited_observational_verbs:
        if re.search(rf"\b{re.escape(verb.casefold())}\b", lowered):
            raise ManuscriptAuditError(f"prohibited observational verb: {verb}")
    for term in contracts.style.unsupported_superlatives:
        if re.search(rf"\b{re.escape(term.casefold())}\b", lowered):
            raise ManuscriptAuditError(f"unsupported superlative requires claim-ledger approval: {term}")
    for term in ("TBD", "TODO", "FIXME"):
        if term.casefold() in lowered:
            raise ManuscriptAuditError(f"placeholder token: {term}")


def audit_manuscript_control(paths: ProjectPaths) -> AuditReport:
    contracts = load_manuscript_contracts(paths.root)
    gate_report = evaluate_manuscript_gates(paths)
    if "M0" in gate_report.blocked:
        raise ManuscriptAuditError("M0 authority gate is blocked")
    control = paths.root / "outputs" / "manuscript" / "control"
    submission_target = control / "submission_target_date.txt"
    if submission_target.is_file():
        target = date.fromisoformat(submission_target.read_text(encoding="utf-8").strip())
        age_at_submission = (target - contracts.journal.accessed).days
        if age_at_submission < 0 or age_at_submission > contracts.journal.revalidate_days_before_submission:
            raise ManuscriptAuditError("official journal audit is not within 30 days of submission")
    ledger_report = verify_ledgers(control, contracts)
    if ledger_report.open_critical_issues:
        raise ManuscriptAuditError("open critical manuscript issue")
    failures: list[str] = []
    for path in sorted(control.glob("*.md")):
        try:
            audit_text(path.read_text(encoding="utf-8"), contracts)
        except ManuscriptAuditError as error:
            failures.append(f"{path.name}: {error}")
    if failures:
        raise ManuscriptAuditError("; ".join(failures))
    return AuditReport(checks=len(tuple(control.glob("*"))), failures=())
```

- [ ] **Step 4: Add the CLI command and submission checklist**

Add the audit imports and exact command to `cli.py`:

```python
from chicagohealthmap.manuscript.audit import (
    ManuscriptAuditError,
    audit_manuscript_control,
)


@manuscript_app.command("audit")
def manuscript_audit_command(control: bool = typer.Option(False, "--control")) -> None:
    """Audit manuscript-control artifacts without authorizing results."""
    if not control:
        raise typer.BadParameter("control audit requires --control", param_hint="--control")
    try:
        report = audit_manuscript_control(ProjectPaths.discover())
    except (ManuscriptAuditError, OSError, ValidationError, yaml.YAMLError) as error:
        typer.echo(f"Manuscript control audit failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(json.dumps(report.__dict__, indent=2, sort_keys=True))
```

The command exits nonzero on missing contracts, missing ledgers, open critical issues,
invalid gates, placeholder markers, prohibited language, protected paths, or an out-of-date
journal audit. `submission_checklist.md` must include all 12 approved QA domains and
explicit human sign-off fields; it must not mark any item passed by default.

Create `reporting_matrix.csv` with exact columns
`framework,item_id,requirement,planned_location,source_artifact,owner,status,verified_by,verified_date`.
It must contain at least one `not_assessed` row for each of JAMA Health Forum, STROBE,
RECORD, STROBE-Equity, and SAGER. No row may be marked complete until its exact checklist
item, manuscript destination, and verifier are recorded.

- [ ] **Step 5: Run focused tests and commit**

Run: `uv run pytest tests/unit/manuscript/test_audit.py tests/unit/test_cli.py -v`  
Expected: PASS.

```bash
git add src/chicagohealthmap/manuscript/audit.py src/chicagohealthmap/cli.py tests/unit/manuscript/test_audit.py docs/manuscript/submission_checklist.md docs/manuscript/reporting_matrix.csv
git commit -m "feat: audit manuscript controls"
```

---

### Task 6: Add agent handoff manifests and the AI-use/disclosure workflow

**Files:**
- Create: `src/chicagohealthmap/manuscript/handoffs.py`
- Create: `tests/unit/manuscript/test_handoffs.py`
- Create: `docs/manuscript/agent_handoff_contract.md`
- Create: `docs/manuscript/ai_disclosure_template.md`

**Interfaces:**
- Consumes: agent contracts, gate report, ledgers, and packet paths.
- Produces: `build_agent_handoff(paths: ProjectPaths, role: str) -> Path`; disclosure-safe JSON contains only authorized paths and evidence identifiers.

- [ ] **Step 1: Write failing authorization and path-redaction tests**

```python
import json
import pytest

from chicagohealthmap.manuscript.handoffs import HandoffError, build_agent_handoff


def test_results_agent_is_blocked_before_s7(tmp_project) -> None:
    with pytest.raises(HandoffError, match="results-agent handoff requires S7"):
        build_agent_handoff(tmp_project.paths, "results_agent")


def test_handoff_contains_no_absolute_or_protected_paths(authorized_project) -> None:
    path = build_agent_handoff(authorized_project.paths, "methods_reporting_agent")
    payload = json.loads(path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload)
    assert str(authorized_project.root) not in serialized
    assert "/Users/" not in serialized
    assert "sources/first_party/capricorn/snapshots" not in serialized
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/unit/manuscript/test_handoffs.py -v`  
Expected: FAIL because handoff functions do not exist.

- [ ] **Step 3: Implement role-scoped handoff manifests**

```python
import json
from pathlib import Path

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.manuscript.contracts import load_manuscript_contracts
from chicagohealthmap.manuscript.gates import assert_results_authorized


class HandoffError(ValueError):
    pass


RESULT_ROLES = {"results_agent", "case_study_1_agent", "case_study_2_agent", "discussion_policy_agent"}


def build_agent_handoff(paths: ProjectPaths, role: str) -> Path:
    contracts = load_manuscript_contracts(paths.root)
    if role not in contracts.agents:
        raise HandoffError(f"unknown manuscript role: {role}")
    if role in RESULT_ROLES:
        try:
            assert_results_authorized(paths)
        except ValueError:
            raise HandoffError(f"{role.replace('_', '-')} handoff requires S7") from None
    output = paths.root / "outputs" / "manuscript" / "control" / "handoffs"
    output.mkdir(parents=True, exist_ok=True)
    role_contract = contracts.agents[role]
    payload = {
        "role": role,
        "responsibility": role_contract.responsibility,
        "permitted_inputs": role_contract.permitted_inputs,
        "permitted_outputs": role_contract.permitted_outputs,
        "prohibited_actions": role_contract.prohibited_actions,
        "human_approval_required": role_contract.human_approval_required,
    }
    path = output / f"{role}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
```

- [ ] **Step 4: Write the human handoff and AI disclosure templates**

The handoff contract must require one role, one bounded task, explicit artifact IDs,
prohibited actions, report path, status enum, and human-decision escalation. The AI
template must include platform, model/version or explicit unavailable state,
manufacturer, extensions, dates, purpose, manuscript sections/artifacts, reference-use
prohibition, human verifier, and responsibility statement.

- [ ] **Step 5: Run focused tests and commit**

Run: `uv run pytest tests/unit/manuscript/test_handoffs.py -v`  
Expected: PASS.

```bash
git add src/chicagohealthmap/manuscript/handoffs.py tests/unit/manuscript/test_handoffs.py docs/manuscript/agent_handoff_contract.md docs/manuscript/ai_disclosure_template.md
git commit -m "feat: build gated manuscript agent handoffs"
```

---

### Task 7: Integrate the complete offline manuscript-control workflow

**Files:**
- Create: `tests/integration/test_manuscript_control_cli.py`
- Modify: `src/chicagohealthmap/cli.py`
- Modify: `src/chicagohealthmap/manuscript/ledgers.py`
- Modify: `.gitignore`
- Create: `docs/solutions/2026-07-14-agentic-manuscript-control-plane.md`

**Interfaces:**
- Consumes: all Task 1-6 interfaces.
- Produces CLI commands `manuscript init`, `manuscript gates --check`, `manuscript packets --build`, `manuscript handoff --role ROLE`, and `manuscript audit --control`.

- [ ] **Step 1: Write a failing end-to-end offline CLI test**

```python
from pathlib import Path
import shutil

from typer.testing import CliRunner

from chicagohealthmap.cli import app


def test_control_plane_initializes_and_fails_closed_before_s7(tmp_path: Path, monkeypatch) -> None:
    root = Path(__file__).resolve().parents[2]
    (tmp_path / "config").mkdir()
    (tmp_path / "docs").mkdir()
    shutil.copytree(root / "config" / "manuscript", tmp_path / "config" / "manuscript")
    shutil.copytree(root / "docs" / "manuscript", tmp_path / "docs" / "manuscript")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\nversion='0'\n", encoding="utf-8")
    monkeypatch.setenv("CHICAGOHEALTHMAP_ROOT", str(tmp_path))
    runner = CliRunner()
    assert runner.invoke(app, ["manuscript", "init"]).exit_code == 0
    packets = runner.invoke(app, ["manuscript", "packets", "--build"])
    assert packets.exit_code == 0
    assert "PROVISIONAL" in (tmp_path / "outputs/manuscript/control/case_1.md").read_text()
    results_handoff = runner.invoke(app, ["manuscript", "handoff", "--role", "results_agent"])
    assert results_handoff.exit_code == 1
    assert "requires S7" in results_handoff.output
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/integration/test_manuscript_control_cli.py -v`  
Expected: FAIL because the integrated CLI surface is incomplete.

- [ ] **Step 3: Implement the exact CLI orchestration**

Add this initializer to `ledgers.py`:

```python
import json
from hashlib import sha256

from chicagohealthmap.manuscript.models import ManuscriptContracts


LEDGER_MODELS = {
    "claim_ledger.csv": ClaimRecord,
    "number_ledger.csv": NumberRecord,
    "ai_use_ledger.csv": AiUseRecord,
    "issue_ledger.csv": IssueRecord,
}


def initialize_ledgers(control_dir: Path, contracts: ManuscriptContracts) -> tuple[Path, ...]:
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
    canonical = json.dumps(contracts.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    digest_path = control_dir / "contract_digest.sha256"
    digest_path.write_text(sha256(canonical.encode("utf-8")).hexdigest() + "\n", encoding="utf-8")
    return (*created, digest_path)
```

Add these imports to `cli.py`:

```python
from chicagohealthmap.manuscript.contracts import load_manuscript_contracts
from chicagohealthmap.manuscript.handoffs import HandoffError, build_agent_handoff
from chicagohealthmap.manuscript.ledgers import LedgerError, initialize_ledgers
from chicagohealthmap.manuscript.packets import build_control_packets
```

Add the exact commands:

```python
@manuscript_app.command("init")
def manuscript_init_command() -> None:
    """Initialize empty, version-bound manuscript control ledgers."""
    paths = ProjectPaths.discover()
    try:
        contracts = load_manuscript_contracts(paths.root)
        created = initialize_ledgers(paths.root / "outputs" / "manuscript" / "control", contracts)
    except (LedgerError, OSError, ValidationError, yaml.YAMLError, ValueError) as error:
        typer.echo(f"Manuscript initialization failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Initialized manuscript control artifacts: {len(created)}")


@manuscript_app.command("packets")
def manuscript_packets_command(build: bool = typer.Option(False, "--build")) -> None:
    """Build deterministic pre-result outline and case packets."""
    if not build:
        raise typer.BadParameter("packet generation requires --build", param_hint="--build")
    try:
        created = build_control_packets(ProjectPaths.discover())
    except (OSError, ValidationError, yaml.YAMLError, ValueError) as error:
        typer.echo(f"Manuscript packet build failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Built manuscript control packets: {len(created)}")


@manuscript_app.command("handoff")
def manuscript_handoff_command(role: str = typer.Option(..., "--role")) -> None:
    """Build one role-scoped, disclosure-safe agent handoff."""
    try:
        path = build_agent_handoff(ProjectPaths.discover(), role)
    except (HandoffError, OSError, ValidationError, yaml.YAMLError, ValueError) as error:
        typer.echo(f"Manuscript handoff failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(path.relative_to(ProjectPaths.discover().root).as_posix())
```

Every command catches only documented manuscript/configuration errors, prints one
actionable message, and exits 1 on incomplete authority.

- [ ] **Step 4: Ignore generated control artifacts**

Add exactly these generated paths to `.gitignore`:

```gitignore
outputs/manuscript/control/
```

Do not ignore `docs/manuscript/`, `config/manuscript/`, tests, or source code.

- [ ] **Step 5: Run all verification**

```bash
uv run pytest tests/unit/manuscript tests/integration/test_manuscript_control_cli.py -v
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run chicagohealthmap manuscript init
uv run chicagohealthmap manuscript packets --build
uv run chicagohealthmap manuscript gates --check
uv run chicagohealthmap manuscript audit --control
git diff --check
git status --short
```

Expected:

- all focused and full tests pass with no warnings;
- Ruff and mypy pass;
- `init` and pre-result packet construction pass;
- `gates --check` truthfully exits nonzero while S4-S7 remain open;
- the control audit passes for authorized pre-result artifacts and reports the open gate;
- no protected path, credential, row-level source data, or generated artifact is tracked;
- the worktree contains only the intended Task 7 changes before commit.

- [ ] **Step 6: Write the solution record**

Document the problem, evidence, chosen control-plane architecture, rejected alternatives,
gate behavior, verification commands/results, the approved style pattern, and the reusable
pattern. State explicitly that manuscript prose assembly is a separate post-S7 project.

- [ ] **Step 7: Commit the integrated control plane**

```bash
git add .gitignore src/chicagohealthmap/cli.py src/chicagohealthmap/manuscript/ledgers.py tests/integration/test_manuscript_control_cli.py docs/solutions/2026-07-14-agentic-manuscript-control-plane.md
git commit -m "feat: integrate manuscript control plane"
```

---

## Post-S7 planning boundary

Do not add a manuscript-drafting task to this plan. After S4-S7 pass and the analytic
dataset, two case-study notebooks, primary tables/figures, study manifest, and output
checksums are frozen, use `superpowers:brainstorming` only if the scientific scope changed;
otherwise use `superpowers:writing-plans` to create
`docs/superpowers/plans/YYYY-MM-DD-jama-manuscript-assembly.md` from the then-current
artifacts. That second plan must name the actual selected cases, exact artifact IDs,
approved claims, author/disclosure inputs, and output filenames. This boundary is required
because inventing those values now would violate the approved no-premature-drafting rule.

## Final verification for this plan

- [ ] Every approved design requirement maps to a task or the explicit post-S7 boundary.
- [ ] All models and function names are identical across producing and consuming tasks.
- [ ] No task generates result prose, result numbers, references, conclusions, or policy claims.
- [ ] Gate, ledger, packet, handoff, language, protected-path, and CLI failures are tested.
- [ ] Current JAMA values are versioned and require live revalidation.
- [ ] Placeholder scanning finds only the deliberate audit-test literals; no unresolved plan value or unspecified error-handling step remains.
- [ ] Each implementation task ends in an independently reviewable commit.
