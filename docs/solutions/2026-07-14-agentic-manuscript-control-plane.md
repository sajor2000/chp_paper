# Agentic Manuscript Control Plane

## Problem

The project needs a JAMA Health Forum manuscript workflow that can use agents without
letting agents invent results, alter study semantics, expose protected data, or draft
past the scientific gates.

## Evidence

- Contracts freeze current JAMA Health Forum limits, agent roles, style boundaries, and
  manuscript gates.
- Gates fail closed until S4-S7 evidence exists and S7 artifacts reconcile by path and
  checksum.
- Ledgers require frozen artifacts for result claims and independent verification for
  material non-result claims.
- The global JAMA Health Forum writing skill is mandatory for manuscript work after
  marimo results and summaries are frozen.

## Decision

Use a small manuscript-control package with deterministic contracts, ledgers, gates,
case packets, audits, and handoffs. CLI commands initialize empty ledgers, build
pre-result packets, create role-scoped handoffs, and audit generated control artifacts.
Result-bearing handoffs remain blocked until S7 authorizes frozen outputs.

## Rejected Alternatives

- Free-form manuscript drafting before S7: rejected because it would invite result
  invention and retrospective interpretation.
- Broad handoff prompts containing local paths or source data: rejected because prompts
  must remain disclosure-safe and scoped to role contracts.
- Treating exemplar JAMA articles as submission rules: rejected because live official
  instructions and project contracts govern requirements.

## Verification Pattern

Each task used focused tests, Ruff, mypy where applicable, and a commit-sized change.
The reusable pattern is: freeze authority, initialize empty ledgers, generate only
non-result shells before S7, block result roles, audit text for unsafe claims, and log
every scientific or manuscript gap as an explicit blocker.

## Boundary

This control plane does not draft the paper. Manuscript prose assembly starts only after
S6/S7, the analytic dataset, the combined marimo case-study notebook, result summaries,
tables, figures, manifests, and checksums are frozen.
