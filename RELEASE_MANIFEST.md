# Public scientific repository manifest

## Included

- Complete Python package and command-line code.
- Marimo and R Markdown notebook source.
- Statistical analysis plan, decision log, data dictionary, evidence ledger,
  manuscript controls, and methods documentation.
- Tests and locked Python dependencies.
- Aggregate statistical tables, figures, diagnostics, and provenance manifests
  from the final independent-review run.
- Self-contained Marimo and R Markdown HTML review packages.
- A gzip-compressed aggregate geography-condition-year analytic CSV.
- Source metadata and checksum ledgers.

## Excluded

- Patient-level or row-level clinical data.
- Database connection strings, credentials, and access tokens.
- Raw first-party and public-source snapshots.
- Local Python and R environments, caches, temporary renders, and development
  output directories.
- The large ZCTA analytic sidecar, which is not required to render the final R
  biostatistical-review notebook.

## Governance state

- `results_authorized=false`.
- Aggregate numerical outputs are supplied for independent biostatistical review.
- Manuscript import, coauthor result narratives, publication claims, and
  submission readiness remain blocked pending S7 authorization.
- Combined diabetes remains blocked pending mutual-exclusivity and denominator
  equivalence evidence.

## Aggregate data archive

`outputs/notebooks/chicago_healthmap_master/00_master_analytic_dataset.csv.gz`
expands to a 20,536-row aggregate geography-condition-year CSV. The materializer
verifies the uncompressed SHA-256 digest before placing the file at the path used
by the R Markdown notebook.

## Verification before public release

- Governed environment: 1036 tests passed, including 2 deterministic executions
  of the master notebook.
- Public repository: 865 source-independent unit tests passed and 1 was skipped.
- Ruff, MyPy, and strict Marimo validation passed.
- JSON, YAML, Bash syntax, ShellCheck, and Git whitespace checks passed.
- Gitleaks directory and Git-history scans found no unallowlisted secrets.
- Both review HTML files contain no local external assets or execution-error
  markers.
- The compressed aggregate CSV expands to SHA-256
  `dc59dd5cef6a0671046b7666264084b8e4840165da67fee1e4b19091c4971dcf`.
