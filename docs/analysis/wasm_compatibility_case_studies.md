# WASM compatibility audit: combined Chicago case-study marimo notebook

Notebook: `notebooks/02_chicago_case_studies.py`  
Audit date: 2026-07-15  
Compatibility: **FAIL for browser/WASM deployment; PASS for intended local batch execution**

## Decision

The notebook is intentionally a local, auditable batch surface. It imports the local
`chicagohealthmap` package, reads a frozen local Parquet artifact, writes 18 governed
local outputs, and invokes `git rev-parse` to bind the run manifest to the checked-out
commit. Browser WASM cannot provide those repository and process assumptions. The
verified local command remains:

```bash
uv run notebooks/02_chicago_case_studies.py
```

No browser deployment change is required for this study deliverable.

## Package report

| Package | Status | Notes |
| --- | --- | --- |
| marimo | OK | Available in the marimo/Pyodide runtime. |
| pandas | OK | Pyodide built-in. |
| matplotlib | OK | Pyodide built-in. |
| geopandas | OK | Listed in the local Pyodide package snapshot; used for the official 77-area map. |
| pydantic | OK | Pyodide built-in. |
| scipy | OK | Pyodide built-in; imported by the local analysis package. |
| shapely | OK | Pyodide built-in; required by deterministic queen topology. |
| pyarrow | OK | Pyodide built-in snapshot; required indirectly for Parquet. |
| statsmodels | WARN | Imported by the local analysis package; not verified in the local Pyodide snapshot. |
| chicagohealthmap | FAIL | Local editable project package is not packaged or bundled for browser installation. |

## Code issues

| Pattern | Status | Recommendation for a future browser edition |
| --- | --- | --- |
| No PEP 723 dependency block | WARN | Add complete browser-installable metadata only after packaging the local module. |
| Reads `outputs/frozen/chicago_case_studies_analytic.parquet` | FAIL | Bundle a bounded artifact or fetch from a CORS-compatible immutable URL. |
| Uses `Path(__file__)` and repository-relative files | FAIL | Replace repository discovery with explicit browser assets. |
| Writes CSV, HTML, PNG, and JSON under `outputs/notebooks/` | FAIL | Render inline or expose browser download controls. |
| Calls `git rev-parse` and `git status` through `subprocess.run` | FAIL | Inject build-time commit and dirty-state identifiers; browsers cannot spawn processes. |

## Local batch verification

- Script-mode execution completed with all 18 required artifacts.
- `uvx marimo check --strict notebooks/02_chicago_case_studies.py` passed.
- Two isolated runs produced byte-identical CSV, HTML, PNG, and JSON hashes.
- Interactive cells explicitly render governed Tables 1–2 and Figures 1–3.
- The manifest records the frozen input hash, SAP hash, `uv.lock` hash, git commit,
  git dirty state, notebook and analysis-source hashes, fixed seed/permutations,
  `America/Chicago`, dynamically verified dual source provenance, topology checksums,
  manifest self-hash policy, and `results_authorized=false`.

The local PASS does not change the browser/WASM FAIL verdict.
