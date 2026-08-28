# Manuscript Ledger Dictionary

The four CSV ledgers in `outputs/manuscript/control/` are the manuscript's
machine-readable evidence controls. Their filenames, headers, and header order
are fixed. Blank ledgers retain the full header row. Generated ledger files are
local outputs and are not committed.

All identifiers must be nonblank after trimming and unique after trimming within
their ledger. Dates use the exact lexical form `YYYY-MM-DD` and must be valid
calendar dates; datetime strings and alternate date formats are rejected. Fields
described as free text still must preserve exact artifact, source, or manuscript
locations rather than informal summaries.

## Claim ledger

File: `claim_ledger.csv`. The evidence claims agent maintains this ledger. A
named scientific author verifies evidence judgments and wording boundaries;
the results agent supplies frozen result-artifact locations.

| Field | Definition and evidence rule | Allowed values | Responsible human role |
|---|---|---|---|
| `claim_id` | Stable, nonblank, unique claim identifier. | Free text; recommended prefixes include `R-`, `M-`, and `E-`. | Orchestrator/editor |
| `section` | Intended manuscript section. | Free text matching the controlled outline. | Section's author |
| `draft_claim` | Current atomic claim, limited to one supportable assertion. | Free text. | Section's author |
| `claim_class` | Evidence class that determines the applicable verification rule. | `result`, `method`, `resource`, `novelty`, `prior_evidence`, `interpretation`, `policy`, `limitation` | Evidence lead |
| `source_or_artifact_id` | Stable identifier for the supporting source or frozen artifact. For a result claim, the trimmed identifier must match at least one `artifact_id` in the number ledger. | Free text. | Evidence lead for sources; artifact-lineage lead for results |
| `exact_support_location` | Exact table cell, field, page, section, figure, or verified full-text line supporting the claim. Required for result claims. | Free text. | Evidence or artifact-lineage lead |
| `population_geography_measure_period_match` | Records whether the support matches the claim's population, geography, measure, and period and describes any mismatch. | Free text; use `exact` only when all four dimensions match. | Scientific author with relevant domain expertise |
| `support_strength` | Status of the support assessment. Result claims must use `frozen`; non-result claims labeled `verified` require an independent verifier. Other values describe an explicit evidence state rather than imply verification. | Controlled workflow labels `frozen` and `verified`; otherwise documented free text such as `gap` or `conflict`. | Evidence lead; statistical lead for frozen results |
| `conflict_or_gap` | Preserves contradictory evidence, inaccessibility, or a support gap. Blank only when none is known. | Free text. | Evidence lead |
| `allowed_wording` | Strongest wording authorized by the cited evidence or frozen artifact. | Free text. | Scientific author |
| `prohibited_inference` | Causal, policy, equity, representativeness, or other inference the support does not authorize. | Free text. | Scientific author and equity/privacy reviewer as applicable |
| `result_status` | Prespecification status. Result claims cannot use `not_applicable`; every non-result claim must use `not_applicable`. | `prespecified`, `secondary`, `exploratory`, `post_hoc`, `not_applicable` | Statistical lead |
| `owner` | Agent or section owner responsible for resolving the row. Mandatory and nonblank for a verified non-result claim. | Free text matching an authorized assignment. | Orchestrator/editor |
| `verified_by` | Independent named verifier. When a non-result claim's `support_strength` is `verified`, this field is mandatory and cannot equal `owner` after trimming and case normalization. | Human name or stable author identifier; blank only when verification is not claimed. | Independent scientific author |
| `verified_date` | Date independent verification was completed. Mandatory for a verified non-result claim. | Exact `YYYY-MM-DD` calendar date, or blank when verification is not claimed. | Independent scientific author |
| `final_text_location` | Exact location of the approved claim in the integrated manuscript. | Free text; blank until integration. | Orchestrator/editor |

Evidence rules: every result claim must identify a matching number-ledger
artifact, an exact support location, and `support_strength=frozen`; the matched
number record supplies its checksum, field, and code version. Every material
non-result claim accepted as verified must name its owner, a different human
verifier, and the verification date. Claim class and result status must agree in
both directions. Conflicts and unavailable full text remain explicit gaps
rather than negative evidence.

## Number ledger

File: `number_ledger.csv`. The artifact-lineage agent maintains this ledger.
The statistical lead independently verifies values, uncertainty, denominators,
and reconciliation against the frozen outputs.

| Field | Definition and evidence rule | Allowed values | Responsible human role |
|---|---|---|---|
| `number_id` | Stable, nonblank, unique identifier for one reported number. | Free text; recommended prefix `N-`. | Artifact-lineage lead |
| `artifact_id` | Nonblank identifier of the frozen source artifact. | Free text. | Artifact-lineage lead |
| `checksum` | Canonical SHA-256 checksum proving artifact identity and matching the verified S7 artifact with the same `artifact_id`. | Exact `sha256:<64 lowercase hexadecimal characters>`; no whitespace. | Reproducibility lead |
| `artifact_field` | Nonblank exact field, cell, row key, or structured path containing the raw value. | Free text. | Artifact-lineage lead |
| `code_version` | Nonblank immutable code revision that produced the artifact. | Commit hash or version identifier. | Reproducibility lead |
| `population` | Analytic population represented by the value. | Free text matching the frozen manifest/SAP. | Statistical lead |
| `exclusions` | Exclusions applied to the value. | Free text matching the frozen manifest/SAP. | Statistical lead |
| `geography` | Geographic unit and scope. | Free text matching the frozen artifact. | Spatial lead |
| `time_period` | Observation or analysis period. | Free text matching the frozen artifact. | Statistical lead |
| `measure` | Exact measure or estimand name. | Free text matching the SAP and artifact. | Statistical lead |
| `unit` | Unit used for interpretation and display. | Free text such as `proportion`, `percent`, `years`, or `count`. | Statistical lead |
| `denominator` | Exact denominator or denominator definition. | Free text; never inferred from the display value. | Statistical lead |
| `raw_value` | Unrounded value copied from the artifact. | Exact text representation from the artifact. | Artifact-lineage lead |
| `display_value` | Manuscript-formatted and rounded value. | Free text following the reporting contract. | Results author |
| `uncertainty` | Confidence/credible interval, standard error, or explicit reason none applies. | Free text. | Statistical lead |
| `result_status` | Prespecification status for the result. | `prespecified`, `secondary`, `exploratory`, `post_hoc` | Statistical lead |
| `manuscript_locations` | Every title, abstract, text, table, figure, or supplement location where the number appears. | Delimited free text. | Orchestrator/editor |

Evidence rule: every number row requires nonblank `artifact_id`, canonical
`checksum`, `artifact_field`, and `code_version`. M1 requires at least one number
row, and every number artifact/checksum pair must exactly match the verified S7
inventory. Values are transcribed only from those checksummed, frozen artifacts.
The raw value, displayed value, uncertainty,
denominator, analytic dimensions, and every repeated manuscript location must
reconcile before numerical signoff.

## AI-use ledger

File: `ai_use_ledger.csv`. The orchestrator/editor records every material AI
use. A named human author verifies the affected artifact and remains accountable
for its accuracy, attribution, confidentiality, and final inclusion.

| Field | Definition and evidence rule | Allowed values | Responsible human role |
|---|---|---|---|
| `ai_use_id` | Stable, nonblank, unique AI-use identifier. | Free text; recommended prefix `AI-`. | Orchestrator/editor |
| `platform` | Product or service used. | Free text. | Human user |
| `model` | Model/version reported by the platform; record `unavailable` when not exposed. | Free text. | Human user |
| `manufacturer` | Model or platform manufacturer. | Free text. | Human user |
| `start_date` | First date of the described use. | Exact `YYYY-MM-DD` calendar date. | Human user |
| `end_date` | Last date of the described use; cannot precede `start_date`. | Exact `YYYY-MM-DD` calendar date. | Human user |
| `use` | Specific task performed, without implying autonomous authorship. | Free text. | Human user |
| `affected_artifact` | Exact file, section, code component, or control artifact affected. | Free text. | Human user |
| `human_verifier` | Named human who reviewed the affected artifact. Mandatory. | Human name or stable author identifier. | Verifying author |
| `verified_date` | Date human verification was completed. Mandatory. | Exact `YYYY-MM-DD` calendar date. | Verifying author |

Evidence rule: every row requires both a named human verifier and a verification
date, and its date range must be ordered. AI output is never treated as evidence
and AI systems are not authors.

## Issue ledger

File: `issue_ledger.csv`. The orchestrator/editor maintains the issue log. The
human owner with the relevant scientific, statistical, privacy, equity, or
submission authority documents and approves resolution.

| Field | Definition and evidence rule | Allowed values | Responsible human role |
|---|---|---|---|
| `issue_id` | Stable, nonblank, unique issue identifier. | Free text; recommended prefix `I-`. | Orchestrator/editor |
| `severity` | Consequence if unresolved. Critical blocks the relevant gate; important requires correction before independent QA approval; minor is tracked for final review. | `critical`, `important`, `minor` | Orchestrator/editor with domain owner |
| `gate` | Scientific or manuscript gate affected. | Free text matching a defined gate such as `S7` or `M5`. | Orchestrator/editor |
| `description` | Atomic statement of the discrepancy, gap, or decision required. | Free text. | Issue reporter |
| `evidence` | Exact report, artifact, test, rule, or ledger location demonstrating the issue. Mandatory and nonblank for `resolved` or `accepted_by_human`. | Free text. | Issue reporter |
| `owner` | Named person accountable for disposition. Mandatory and nonblank for `resolved` or `accepted_by_human`. | Human name or stable author identifier. | Orchestrator/editor assigns; named owner accepts |
| `status` | Current disposition. | `open`, `resolved`, `accepted_by_human` | Named owner and gate approver |
| `resolution` | Evidence-backed correction or explicit rationale and authority for acceptance. Mandatory and nonblank for `resolved` or `accepted_by_human`. | Free text; may be blank only while open. | Named owner and gate approver |

Evidence rule: open critical and important issues are counted separately in
`LedgerReport` and block M5-relevant independent QA. A resolved or
human-accepted issue requires nonblank
evidence, owner, and resolution before it leaves that count. Conflicts are
preserved; `accepted_by_human` records an explicit accountable decision and is
not equivalent to silent resolution.
