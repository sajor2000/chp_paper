# S5/S6 authority validation and advisory AI review

## Problem

The project needed a way to proceed after explicit human S5/S6 approval while
preserving AI review concerns as limitations instead of silently discarding them
or letting them block the requested analytic-dataset and notebook phase.

## Evidence

- The S5 worksheet and reconciliation controls require two completed
  outcome-blinded scorer records, reconciled scores, and a signed S5 portfolio
  decision.
- S6 requires a signed SAP record plus final variable dictionary, model shells,
  sensitivity families, multiplicity rule, and software/version manifest.
- Two independent AI blinded scorers reviewed the available S5 evidence without
  using outcomes. They identified missing quantitative audits that should be
  retained as sensitivity and documentation concerns.

## Decision

Add readiness validation for approved S5 and approved S6 records. Human S5/S6
approval governs the analytic-dataset and notebook phase. A valid S6 authority
record authorizes analysis execution, the final analytic dataset, and the
combined marimo case-study notebook after S5 approval exists. It still does not
authorize Results prose or manuscript drafting before later result review.

## Rejected alternatives

- Treating AI scores as a blocking gate was rejected because the investigator
  explicitly removed that gate and approved proceeding absent catastrophic
  concerns.
- Discarding AI scoring concerns was rejected because they remain useful
  sensitivity and audit targets.
- Running confirmatory modeling or building the final analytic dataset before a
  valid S6 authority record was rejected.

## Verification

- `uv run pytest tests/unit/test_governance_readiness.py -q`
- `uv run pytest tests/unit/test_s5_scorecard.py tests/unit/test_governance_readiness.py -q`
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src`
- `git diff --check`

## Reusable pattern

Separate approval authority from advisory AI review. If a human owner explicitly
authorizes proceeding, retain AI concerns as limitations and sensitivity checks
without allowing them to invent, suppress, or overrule governance records.
