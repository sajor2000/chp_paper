# S5 outcome-blinded scorecard template

## Problem

The project needed a concrete next step after guarded S4 mapping without
accidentally unblinding outcomes, selecting cases, or authorizing the analytic
dataset and marimo notebook too early.

## Evidence

- The SAP workbook source defines a fixed 100-point S5 scorecard with eight
  scoring domains and two zero-point portfolio/tie-break rules.
- The S4 mapping packet defines the City of Chicago case-study frame while
  preserving six-county source provenance.
- Existing S4, source-lineage, and literature artifacts provide admissible
  evidence pointers for scoring without exposing life-expectancy, mortality, or
  model results.
- Manuscript control code already requires a later
  `outputs/governance/case_selection.json` approval record before treating cases
  as S5-selected.

## Decision

Add `docs/analysis/s5_case_selection_scorecard.json` as a non-authorizing
scorecard template. It records:

- the fixed S5 scoring anchors;
- cardiometabolic and respiratory COPD candidate shells;
- forbidden outcome information;
- blocked actions for outcome unblinding, modeling, Results prose, final analytic
  dataset construction, and the combined marimo case-study notebook;
- required next evidence from two independent blinded scorers and a signed
  portfolio decision.

Add `docs/analysis/s5_blinded_scoring_artifacts.json` as the next
non-authorizing execution template. It records two blinded scorer worksheets,
a reconciliation shell, prefilled outcome-blinded evidence references for every
candidate-domain scoring row, and the exact
`outputs/governance/case_selection.json` approval-record format expected after
S5 is genuinely approved.

Add an S5 reconciliation-draft builder for future completed worksheets. The draft
computes deterministic scorer totals and reconciled totals, validates strict
outcome-blinded completion, and writes only a
`reconciled_pending_human_approval` record. It points to the required future
approval record but does not create or substitute for it.

## Rejected alternatives

- Passing S5 automatically was rejected because no scorer worksheets,
  reconciled scores, or signed portfolio decision exist.
- Computing scores from outcome or result data was rejected because the S5 gate
  is explicitly outcome-blinded.
- Leaving evidence references blank was rejected because it would force human
  scorers to rediscover admissible S4/source/literature records and increase the
  risk of accidental outcome leakage.
- Building the final analytic dataset or notebook now was rejected because S5
  and S6 remain incomplete.
- Writing `outputs/governance/case_selection.json` from agent-computed scores was
  rejected because that file is the human S5 approval record.

## Verification

- `uv run pytest tests/unit/test_s5_scorecard.py tests/unit/test_governance_readiness.py -q`
- `uv run chicagohealthmap governance s5-scorecard worksheets --output docs/analysis/s5_blinded_scoring_artifacts.json`
- `uv run chicagohealthmap governance s5-scorecard reconcile --input COMPLETED_WORKSHEETS --output outputs/governance/case_selection_reconciliation_draft.json`

## Reusable pattern

Separate a gate's template/readiness artifact from the gate-passing approval
record. A template can make the next human step executable without broadening
authorization.

Prefill only admissible evidence pointers in blinded scoring worksheets. Scores,
rationales, hard-gate dispositions, reconciled decisions, and approvals must
remain human-entered and pending until the gate is actually signed.

Use a separate reconciliation-draft record between completed worksheets and gate
approval. The draft may validate arithmetic and preserve scorer evidence, but the
approval record remains a distinct human-signed artifact.
