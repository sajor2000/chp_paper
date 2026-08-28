# Gate 2 evidence audit control surface

## Problem

The project had a frozen PubMed/Paperclip checkpoint, but Gate 2 remained open
and the next session needed a safe way to distinguish preserved evidence from
completed screening.

## Evidence

The 2026-07-14 artifacts contain 1,178 unique PubMed records, 1,165 retrieved
metadata records, 13 unavailable metadata records, 1,178 pending screening rows,
45 Paperclip workflow candidates, 41 successful maps, 4 map timeouts, and 6
verified Paperclip `[OK]` claims. Tavily MCP successfully captured the official
ChicagoHealthMap data glossary after the earlier cap failure, preserving
first-party methods facts about capture rate, tract geography, suppression, and
standardized mean difference.

## Decision

Add `chicagohealthmap evidence audit --gate 2 --snapshot-date 2026-07-14` as a
fail-closed, disclosure-safe JSON audit. The command validates frozen queries,
PMID reconciliation, pending screening status, Paperclip verification status,
current official-web source preservation, and tool-failure preservation.
`--check` exits nonzero until Gate 2 is accepted.

## Rejected alternatives

- Closing Gate 2 from artifact existence alone: rejected because investigator
  screening and novelty adjudication are still pending.
- Counting Paperclip candidates as verified evidence: rejected because only
  `verification_status == OK` can support material claims.
- Building analytic datasets or notebooks now: rejected because S6/Gate
  prerequisites remain unmet.

## Verification

Focused tests cover the real frozen snapshot, CLI JSON output, `--check`
failure, symlink rejection, PMID mismatch rejection, query-drift rejection, and
configured-root execution.

## Reusable pattern

Gate checkpoints should expose a deterministic audit command that validates
artifact contracts and names blockers without silently advancing scientific
authority.
