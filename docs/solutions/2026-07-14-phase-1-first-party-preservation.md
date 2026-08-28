# Phase 1 immutable first-party preservation

## Problem

Phase 1 needed to preserve the supplied Chicago Health Map first-party exports and website
methods archives without changing source bytes, admitting a partial or noncanonical inventory, or
placing raw artifacts in Git. It also needed to retain historical methods provenance and observed
discrepancies without treating archived website statements as validated EHR semantics or resolving
questions that require later empirical work.

## Evidence

- `ccf5b8e` added preservation for the configured 21 CAPriCORN/ChicagoHealthMap `.text`
  exports. Task 4's report records 21 observed exports, including 2 observed-empty exports
  (`drug_providers.text` and `wic_locations.text`), with no missing or unexpected configured
  exports. It also records matching source and snapshot hashes for all 21 exports.
- `64b0e3a` anchored export verification to the configured source identity, snapshot date, exact
  expected paths, byte counts, SHA-256 hashes, and manifest membership. Task 4's follow-up report
  records zero missing, unexpected, duplicate, or mismatching entries in the real local snapshot.
- `c2ca69d` added safe preservation for 2 website ZIP archives and recorded their historical
  methods provenance. Task 5's report records 11 extracted regular members, 1 duplicate glossary
  content record, zero unsafe members, matching supplied/preserved archive hashes, and successful
  checksum verification of the inventory, both preserved ZIPs, and all extracted members.
- `d401664` bound website-archive preservation to the canonical configured source, date, archive
  filenames and hashes, member count, and duplicate-content count. It also made inspection,
  inventory, and extraction derive from one staged copy of each archive and verified every member's
  byte count and SHA-256 before publication.
- The Task 4 and Task 5 reports record focused RED/GREEN tests for incomplete or altered export
  inventories, invalid snapshot identity, unsafe archive members, duplicate destinations,
  conflicting extracted bytes, archive mutation races, and noncanonical archive sets.
- Git ignore and status audits in the task reports confirmed that original exports, original ZIPs,
  extracted members, snapshot manifests, and checksum artifacts remained ignored and untracked.

## Decisions

- Preserve original first-party bytes in dated, immutable local snapshots and keep those raw
  artifacts outside version control. Track only the configuration, implementation, tests, source
  metadata, methods provenance, and discrepancy records needed to describe and verify them.
- Require the export snapshot to match the configured source identity, snapshot date, exact set of
  21 expected paths, and each file's byte count and SHA-256. Preserve zero-byte expected files as
  observed artifacts rather than interpreting them as missing.
- Require the website snapshot to match the configured source identity, date, exact 2 archive
  filenames and hashes, 11 regular members, and 1 duplicate-content record. Preserve both archive
  identities while selecting one glossary member as canonical and recording the other as duplicate
  content.
- Copy each website archive once into a UUID staging directory, then inspect, inventory, and
  extract only from that staged copy. Reject absolute paths, parent traversal, symlinks, duplicate
  destinations, conflicting existing bytes, and member byte/hash disagreement before immutable
  publication.
- Retain archived website statements as historical methods provenance, not as independent
  validation. Record the four observed methods/data discrepancies explicitly as unresolved pending
  Tasks 8–9.

Gate 1 passed only for byte accounting, immutable local preservation, exact configured
inventories, safe archive extraction, historical methods provenance, and explicit unresolved
discrepancy records.

## Rejected alternatives

- Treating a self-consistent manifest as sufficient was rejected because a manifest and snapshot
  could be truncated together. Verification is anchored independently to the configured inventory.
- Reopening mutable source ZIPs during extraction was rejected because source bytes could change
  after inspection. All downstream work derives from the staged preserved copy, with member hashes
  checked again as bytes are written.
- Accepting arbitrary archive filenames, hashes, counts, or dates was rejected because successful
  extraction alone does not prove preservation of the intended first-party evidence.
- Dropping the 2 empty exports was rejected because zero-byte configured files are observed source
  artifacts, not evidence of absence. They are preserved and flagged for later methods review.
- Collapsing the 2 ZIP archives because they share glossary content was rejected because the
  archives have distinct identities and contents. The duplicate glossary bytes are recorded while
  both original archives remain preserved.
- Committing raw artifacts was rejected because the original exports, ZIPs, extracted members,
  manifests, and checksums are local preservation artifacts with separate redistribution, size,
  and lifecycle constraints.
- Resolving discrepancies from archived website language was rejected because provenance is not
  empirical validation.

## Verification

The Task 4 and Task 5 reports record full-suite, focused-test, Ruff, mypy, checksum, source-to-copy
hash, whitespace, ignored-file, and clean-status checks at their respective completion points. At
Phase 1 closeout, the repository-wide checks were rerun from the feature worktree:

```text
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
uv run mypy
git diff --check
```

All commands completed successfully before the closeout commit. The full suite passed 155 tests;
Ruff reported all checks passed and 13 files already formatted; mypy reported no issues in 7
source files; and the whitespace check produced no errors.

## Remaining boundaries

- EHR field semantics have not passed. Phase 1 does not establish numerator or denominator
  meaning, diagnosed-adult interpretation, encounter or person construction, cross-system
  deduplication semantics, capture meaning, reliability meaning, or geography semantics.
- Suppression interpretation has not passed. The relationship between exported zero values and
  the archived website's `<10` language remains unresolved.
- Phenotype validity has not passed. Archived claims about validated ICD-10 code sets do not
  validate the released condition fields or their implementation.
- Evidence review and the literature gap have not passed. Historical methods provenance is not a
  completed literature review or independent scientific validation.
- Public-data harmonization has not passed. Geography vintages, time periods, variable
  definitions, missingness, suppression, and cross-source comparability remain to be established.
- SAP freeze has not passed, and confirmatory analysis remains unauthorized.
- The 2 observed-empty exports, reconstructability of age standardization, stated versus observed
  condition counts, and exported-zero/suppression relationship remain explicit unresolved records
  for Tasks 8–9.
- The raw snapshots are intentionally local and ignored. Reproduction requires access to source
  artifacts matching the configured hashes and does not imply redistribution permission.

## Reusable patterns

- Anchor preservation verification to a separately configured canonical inventory; never let a
  generated manifest define its own completeness.
- Treat expected zero-byte files as first-class observations. Preserve them, hash them, and defer
  interpretation rather than silently dropping or imputing them.
- For mutable archives, copy once into staging and derive inspection, inventory, deduplication,
  and extraction from those staged bytes. Recheck member size and digest while extracting.
- Preserve container identity separately from content deduplication. Identical members do not make
  distinct source archives interchangeable.
- Separate provenance claims from validation claims, and carry unresolved discrepancies forward
  in an explicit record with a named future review point.
- State gate scope beside the preservation decisions so byte integrity cannot be mistaken for
  semantic validity, harmonization, SAP freeze, or authorization to analyze.
