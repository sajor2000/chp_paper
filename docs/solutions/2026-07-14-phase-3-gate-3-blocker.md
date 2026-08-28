# Phase 3 Gate 3 blocker: preserve shape without inventing semantics

## Problem

The 21 first-party exports are headerless. Their archived website glossary documents
concepts but does not establish the positional column order, and the repository contains
no data-owner export specification or correspondence that does. Treating repeated values
or plausible subgroup order as field identity would make later quality checks and models
scientifically unauditable.

## Evidence

- The preserved snapshot contains 19 nonempty exports and two zero-byte exports.
- Source-derived inspection reconciles every file to one observed field count and row count.
- The 19 nonempty contracts contain 549 ordered positions in total.
- Documentary review verified zero positional meanings; all 549 remain `unverified` and
  no table is analysis-usable.
- Both real CLI commands report 21 tables, 549 unverified positions, zero rows read, and
  zero Parquet outputs, then exit nonzero.
- The marimo review consumes only the disclosure-safe quality checkpoint and emits a
  machine-readable closed Gate 3 decision with the same counts.

Implementation and hardening are recorded in commits `31536ea`, `4dd9e30`, `7e408a6`,
`e6874dd`, `51793f6`, `69258eb`, and `0e663ba`.

## Decision

Record observed shape separately from semantic identity. Generic names such as
`unverified_position_01` describe only position and are blocked by the schema API.
Strict parsing, validation, provenance, quality, and Parquet publication are implemented
and tested against synthetic verified schemas, while real first-party ingestion fails
before opening a source file. Gate 3 remains closed.

The review notebook is a deterministic governance view, not a cleaning notebook. Its
resolved input and output paths must remain beneath the canonical repository
`outputs/quality` directory; direct paths, descendant aliases, a redirected quality root,
and report/decision aliases are rejected before writing.

## Rejected alternatives

- Infer positional names from value patterns or glossary ordering: rejected because these
  sources do not prove column order.
- Parse all positions as strings and resolve them later: rejected because it creates a
  misleading analysis-ready artifact and weakens the scientific stop.
- Skip engineering until owner clarification: rejected because fail-closed primitives and
  deterministic governance outputs can be safely implemented and tested now.
- Permit arbitrary notebook output paths: rejected because review artifacts must not be
  redirected into raw sources or other repository areas.

## Verification

At the final Task 10 checkpoint:

```text
233 tests passed
Ruff lint and format passed
mypy passed for 14 source files
marimo check passed
direct notebook execution passed
git diff --check passed
worktree clean
```

The real `ehr ingest` and `ehr quality` commands continue to exit `1`, read zero source
rows, and create no Parquet files.

## Reusable pattern

When raw files are structurally observable but semantically undocumented:

1. checksum and preserve the bytes;
2. inventory row counts, field counts, and positions without semantic labels;
3. attach evidence status to every field and block unverified fields in code;
4. implement parser and quality behavior against synthetic verified contracts;
5. make real-data commands fail before source access;
6. publish a disclosure-safe, machine-readable blocker decision; and
7. require owner evidence before promoting any positional meaning.

## Gate status and unblock condition

Gate 3 is **closed**. It can advance only after the data owner supplies an authoritative
positional specification covering identifiers, time, geography, conditions, numerator,
denominator, proportions, subgroup order, suppression/unknown encoding, reliability,
capture, and the intended schemas of the two empty exports. The evidence source and
decision date must accompany every promoted field.
