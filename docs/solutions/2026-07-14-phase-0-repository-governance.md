# Phase 0 repository and research governance

## Problem

Engineering Phase 0 needed a trustworthy foundation for later scientific pipeline work without
confusing infrastructure readiness with research readiness. The repository initially lacked a
locked Python package and test convention, canonical project paths, strict source/provenance
contracts, and a write-once raw-snapshot primitive. It also needed an explicit boundary preventing
tested credential categories from entering persistable request metadata or appearing in validation
errors.

## Evidence

- `f294e3d` bootstrapped the Python 3.12+ package, lockfile, CLI, development tools, ignore rules,
  and first unit test. Task 1's report records the missing-package RED state and the passing focused
  and full-suite GREEN states.
- `3dcb952` introduced repository-root discovery, canonical source/data/output paths, and strict,
  frozen source, request, file, and snapshot-manifest models. `e52e099`, `35dff8b`, and `939f803`
  successively hardened cross-platform paths, name-based credential detection, immutable request
  mappings, revalidated copies, and redaction of tested secret-bearing inputs in string, structured,
  and JSON validation errors. Task 2's report records each regression test failing before its
  corresponding fix.
- `3d7aa61` added staged snapshot writing, streaming SHA-256 verification, fsync-backed metadata,
  and atomic finalization. `a1aeda4` hardened same-file and hardlink handling, destination cleanup,
  initialization cleanup, checksum-safe paths, and native no-replace publication. Task 3's report
  records the initial missing-module RED state and the eight-failure hardening RED state.
- The three task reports record focused and full test runs, Ruff formatting and lint checks, mypy,
  and whitespace checks at their respective completion points.

## Decisions

- Use one locked `uv` environment and the repository-wide conventions in `pyproject.toml`: tests
  live under `tests`, Ruff targets Python 3.12 with a 100-character line length, and mypy checks the
  `chicagohealthmap` package under `src`.
- Derive all working paths from one resolved repository root. `CHICAGOHEALTHMAP_ROOT` is the sole
  explicit override; discovery otherwise walks to the nearest `pyproject.toml` and creates no
  directories.
- Treat source identity, acquisition authority, request metadata, checksums, file counts,
  timestamps, and validation status as strict immutable contracts. Reject extra fields, traversal
  and cross-platform absolute-path forms, forbidden header names, normalized credential-like query
  names, URL userinfo, tested credential markers in malformed URLs, and non-ISO snapshot dates
  before persistence.
- Redact inputs rejected by those tested credential categories from normal, structured, and JSON
  error representations. Validate model updates and deep copies through the same contract boundary
  used for initial construction.
- Build raw snapshots in UUID staging directories, verify copied bytes, write manifests and
  checksums, fsync the staged tree, and publish with a native atomic no-replace operation. Refuse an
  existing date and fail closed where an exclusive atomic primitive is unavailable.
- Keep raw snapshots, derived data, and outputs out of version control. The repository records the
  code and contracts needed for reproducibility, not the sensitive or bulky source bytes.

Gate 0 passed only for repository paths, contracts, privacy/credential boundaries, test
conventions, and immutable snapshot primitives.

## Rejected alternatives

- Ad hoc current-working-directory paths were rejected because they make execution location part of
  the pipeline's behavior.
- Mutable dictionaries inside frozen models were rejected because callers could add forbidden
  header names or credential-like query names after validation. A custom tuple-backed mapping was
  also rejected after review exposed a replaceable backing slot; copied `MappingProxyType` values
  provide a narrower public boundary.
- Relying only on Pydantic's normal string-error hiding was rejected because tested secret-bearing
  inputs could still appear in structured `errors()` and JSON output. Sanitized pre-validation
  errors are required for the tested rejected categories.
- A check-then-rename fallback was rejected because it cannot guarantee no-replace publication
  under concurrency. Unsupported platforms raise instead of silently weakening immutability.
- Committing raw snapshots or generated data was rejected because reproducibility metadata and
  source bytes have different privacy, size, and lifecycle requirements.
- Treating the new infrastructure as evidence that scientific or acquisition gates passed was
  rejected. The primitives enforce structure; they do not supply, interpret, harmonize, review, or
  analyze data.

## Verification

At Phase 0 closeout, the locked environment, full suite, static checks, formatting, typing, and
whitespace checks were rerun from the feature worktree:

```text
uv lock --check
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
uv run mypy
git diff --check
```

All commands completed successfully before the closeout commit. The full suite passed 121 tests;
Ruff reported all checks passed and 10 files already formatted; mypy reported no issues in 6 source
files; the lock and whitespace checks produced no errors.

## Remaining boundaries

- First-party preservation has not passed: Phase 0 provides snapshot primitives but does not prove
  that any required source was acquired, preserved, licensed, or independently recoverable.
- EHR semantics have not passed: numerator, denominator, phenotype, deduplication, suppression,
  capture, reliability, geography, and the diagnosed-adult interpretation remain unresolved.
- Evidence review has not passed; source documentation and scientific claims still require formal
  review.
- Public-data harmonization has not passed; geography, time, variable definitions, missingness, and
  cross-source comparability remain to be established.
- SAP freeze has not passed, and confirmatory analysis is not authorized.
- No analysis gate has passed. These foundations do not validate estimands, models, diagnostics,
  results, causal claims, or population-prevalence claims.
- Credential detection is name-based and limited to the forbidden header names, normalized
  credential-like query names, URL userinfo, and malformed-URL markers covered by the contracts and
  tests. A future credential using an unrecognized name requires a central policy update; arbitrary
  opaque URL path or fragment content is not classified as credential material.
- Native atomic no-replace publication currently supports Darwin and Linux. Other platforms fail
  closed, and deliberate Python reflection or memory-level mutation remains outside the validated
  public model boundary.

## Reusable patterns

- Pair every persistable contract with tests for ordinary construction, mutation attempts, copy
  paths, serialization, malformed input, and error redaction; a frozen model alone is not a complete
  immutability or secrecy boundary.
- Separate staging from publication, verify content before finalization, fsync both files and
  directories, and require an atomic no-replace primitive for write-once artifacts.
- Make repository-root discovery explicit and side-effect free so the same code works in tests,
  notebooks, CLIs, and scheduled jobs.
- Record gate scope in the same durable decision record as the implementation. Passing an
  engineering foundation gate must never be allowed to imply that source, semantic, evidence, SAP,
  or analysis gates have passed.
