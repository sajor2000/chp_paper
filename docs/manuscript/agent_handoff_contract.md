# Manuscript Agent Handoff Contract

Each handoff must name one manuscript role and one bounded task. The role contract
defines permitted inputs, permitted outputs, prohibited actions, and human approvals.

Required handoff contents:

- Role name from `config/manuscript/agents.yml`.
- One task objective and one report path.
- Exact artifact IDs, claim IDs, or ledger paths used by the task.
- Explicit prohibited actions copied from the role contract.
- Status value: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.
- Verification commands and observed outcomes.
- Human-decision escalation for scientific conflicts, missing evidence, rule ambiguity,
  privacy questions, or any result discrepancy.

Result-bearing roles remain blocked until S7 artifact checksums authorize frozen outputs.
No handoff may include protected local paths, row-level protected data, credentials, or
unverified manuscript claims.
