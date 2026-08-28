# SAP-Complete Chicago Case-Study Analyses Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Regenerate every frozen-data-supported SAP analysis and governed display from one auditable dataset and one combined marimo notebook, while failing closed for unsupported adjusted estimands.

**Architecture:** Keep source-faithful dataset construction in `dataset.py`; put suppression-aware frames and concordance in `case_studies.py`; add focused SAP analysis and spatial modules; keep the notebook as a narrated presentation layer. Missing approved community-area covariates produce machine-readable withholding records, not substituted estimands.

**Tech Stack:** Python 3.12+, pandas, NumPy, SciPy, statsmodels, Shapely/GeoPandas, Matplotlib, Great Tables, marimo, Pydantic, pytest, uv.

## Global Constraints

- ChicagoHealthMap/CAPriCORN raw exports are the source of truth for disease values.
- Never manufacture, interpolate, or estimate disease values from census or community-area data.
- Use all 77 Chicago community areas as the primary analytic frame and preserve direct tract observations.
- The tract-community overlay supplies membership metadata only and never derives disease values.
- Preserve suppression, reliability, capture, numerator, denominator, source, snapshot, and lineage fields.
- Raw files, frozen datasets, credentials, and generated results remain local and untracked.
- Diabetes concordance compares PLACES diabetes with combined source-published EHR diabetes components.
- Results prose and manuscript drafting remain blocked while `results_authorized=false`.
- Every marimo cell is at most 30 source lines; every analytic cell has adjacent Markdown stating purpose, method, rationale, and audit role.
- External biomedical evidence uses Paperclip CLI or PubMed MCP; package/software documentation uses Tavily or Ref MCP.

---

### Task 1: Correct suppression and percentage semantics

**Files:**
- Modify: `src/chicagohealthmap/analysis/case_studies.py`
- Modify: `tests/unit/analysis/test_case_studies.py`

**Interfaces:**
- Produces: `build_primary_community_frame(dataset: DataFrame) -> DataFrame` with suppressed annual values excluded and explicit eligibility counts.
- Produces: `build_tract_concordance_frame(dataset: DataFrame) -> DataFrame` with `ehr_percent_mean_2022_2024` in percentage points and combined diabetes suppression propagated.

- [ ] Add a failing test proving a stored source measure `0.20` becomes `20.0` percentage points in tract concordance.
- [ ] Run `uv run pytest tests/unit/analysis/test_case_studies.py -q` and confirm the new test fails with the current `0.20` result.
- [ ] Implement one explicit proportion-to-percentage-point conversion after validating source units.
- [ ] Add a failing test proving a suppressed community condition-year is excluded and makes that pooled exposure incomplete.
- [ ] Add a failing test proving combined diabetes is unavailable when either source-published component is suppressed or missing.
- [ ] Implement minimal suppression-aware annual eligibility and component-completeness rules.
- [ ] Run focused tests, Ruff, mypy, and `git diff --check`; all must pass.
- [ ] Commit with `fix: correct analysis units and suppression handling`.

### Task 2: Complete concordance and resource audits

**Files:**
- Modify: `src/chicagohealthmap/analysis/case_studies.py`
- Modify: `tests/unit/analysis/test_case_studies.py`

**Interfaces:**
- Produces: `summarize_resource_quality(dataset: DataFrame) -> DataFrame`.
- Produces: `classify_discordance(frame: DataFrame, bins: Literal['quartile','tertile']='quartile') -> DataFrame`.
- Produces: `summarize_concordance(frame: DataFrame) -> DataFrame` including Spearman, Pearson, median differences, weighted kappa, common-set cut points, raw P values, and BH-adjusted P values.

- [ ] Add failing tests for median/IQR denominator and measure, suppression/missing/reliability percentages, and exact geography/year counts.
- [ ] Implement deterministic resource summaries without dropping zero-count states.
- [ ] Add failing boundary tests for all five frozen discordance categories and tertile sensitivity.
- [ ] Implement common-set percentile cut points, cross-tabs, quadratic weighted kappa, and category counts.
- [ ] Add failing tests for Benjamini-Hochberg adjustment within the comparator family.
- [ ] Implement stable BH adjustment while retaining raw P values and priority labels.
- [ ] Run focused tests, Ruff, mypy, and diff checks.
- [ ] Commit with `feat: complete resource and concordance audits`.

### Task 3: Add fail-closed SAP model and temporal engine

**Files:**
- Create: `src/chicagohealthmap/analysis/sap_analyses.py`
- Create: `tests/unit/analysis/test_sap_analyses.py`

**Interfaces:**
- Produces: `assess_primary_model_readiness(frame: DataFrame) -> DataFrame`.
- Produces: `fit_minimally_adjusted_sensitivities(frame: DataFrame) -> DataFrame`.
- Produces: `summarize_temporal_robustness(dataset: DataFrame) -> tuple[DataFrame, DataFrame]`.
- Produces: `summarize_influence(frame: DataFrame, model_id: str) -> tuple[DataFrame, DataFrame]`.

- [ ] Add failing tests that missing `pct_age_65_plus`, `pct_female`, `pct_below_fpl`, and `acs_adult_population` yield `withheld_missing_covariates` for C1 and C2.
- [ ] Implement model gate records for `n < 70`, fewer than 10 distinct exposures, rank deficiency, missing covariates, and covariance failure.
- [ ] Add failing tests for the joint C1 covariance formula, C1-H/C1-D conditional contrasts, C2 IQR contrast, 97.5% primary-family intervals, and 95% secondary intervals.
- [ ] Implement HC3 sensitivity estimates with frozen IQRs and explicit `supported_sensitivity_not_primary` labels.
- [ ] Add failing tests for Cook `4/n`, leverage `2p/n`, externally studentized residual `3`, leave-one-area-out ranges, sign changes, and 30% fragility.
- [ ] Implement influence summaries without deleting areas from the principal frame.
- [ ] Add failing tests for annual 2022/2023/2024, 2019 baseline, leave-one-year-out, and 2020-2021 disruption flags.
- [ ] Implement temporal outputs using exact paired denominators and no primary-period contamination by disruption years.
- [ ] Run focused tests, Ruff, mypy, and diff checks.
- [ ] Commit with `feat: add fail-closed SAP analysis engine`.

### Task 4: Add deterministic spatial diagnostics

**Files:**
- Create: `src/chicagohealthmap/analysis/spatial.py`
- Create: `tests/unit/analysis/test_spatial.py`

**Interfaces:**
- Produces: `build_queen_weights(frame: DataFrame) -> SpatialWeights` with ordered IDs, row-standardized matrix, neighbors, and SHA-256 checksum.
- Produces: `permutation_moran(residuals: Series, weights: SpatialWeights, permutations: int=9999, seed: int=20260715) -> MoranResult`.

- [ ] Add failing tests for queen neighbors on simple polygons, deterministic ordering/checksum, and rejection of invalid polygons or islands.
- [ ] Implement Shapely-based queen contiguity with no silent nearest-neighbor repair.
- [ ] Add failing hand-calculation tests for Moran I, expected value, deterministic conditional permutation P value, and seed/permutation metadata.
- [ ] Implement seeded permutation diagnostics and exact run metadata.
- [ ] Add a test for the SAP escalation gate `abs(I) >= 0.10 and p < 0.05` and supportive labeling when primary adjusted models are withheld.
- [ ] Run focused tests, Ruff, mypy, and diff checks.
- [ ] Commit with `feat: add deterministic spatial diagnostics`.

### Task 5: Rebuild the combined marimo analysis surface

**Files:**
- Modify: `notebooks/02_chicago_case_studies.py`
- Modify: `docs/analysis/wasm_compatibility_case_studies.md`
- Create or modify notebook-focused contract tests under `tests/unit/analysis/`.

**Interfaces:**
- Consumes all Task 1-4 helpers.
- Produces local Table 1, Figures 1-3, Table 2, supplementary CSV/HTML/PNG outputs, and `notebook_run_manifest.json`.

- [ ] Add failing source-contract tests for required output filenames, adjacent audit Markdown, `results_authorized=false`, and maximum 30 source lines per cell.
- [ ] Replace notebook-local statistical logic with calls to tested modules.
- [ ] Add narrated cells for resource/flow, primary frame, readiness/withholding, supported sensitivities, spatial/influence/temporal diagnostics, concordance/discordance, and multiplicity inventory.
- [ ] Render Table 1 and Table 2 with exact denominators, units, CI level, suppression distinctions, and withholding labels.
- [ ] Render Figure 1 with distinct unavailable/suppressed/unreliable encodings; render Figures 2-3 with EHR/public comparator roles and no gold-standard language.
- [ ] Write deterministic supplementary artifacts and a manifest containing input/output checksums, SAP hash, git commit, uv lock hash, seed, time zone, and authorization flags.
- [ ] Run notebook contract tests, `uvx marimo check`, script-mode execution, cell-length audit, Ruff, mypy, and diff checks.
- [ ] Re-run the WASM audit and preserve the local-batch FAIL/browser and PASS/local conclusions unless evidence changes.
- [ ] Commit with `feat: regenerate SAP-auditable notebook outputs`.

### Task 6: Independent audit, freeze candidate, and PR checkpoint

**Files:**
- Modify: `docs/solutions/2026-07-15-analytic-dataset-and-marimo-notebook.md`
- Create: `docs/analysis/sap_notebook_compliance_audit.md`
- Keep result-bearing generated files untracked.

**Interfaces:**
- Produces a requirement-by-requirement compliance matrix and a verified PR checkpoint; does not set `results_authorized=true`.

- [x] Rebuild the frozen dataset and verify manifest checksums, the 22,540-row/90-column schema, 1,848 community-area records and 20,692 census-tract records (2019-2024), zero duplicate keys, and all disease rows labeled direct/not interpolated.
- [ ] Run the notebook twice and compare deterministic result artifact checksums, excluding explicitly documented runtime timestamp fields.
- [ ] Run `uv run pytest -q`, Ruff lint/format, mypy, dataset build, notebook script, marimo check, cell audit, WASM audit, secret/path audit, and `git diff --check`.
- [ ] Dispatch a scoped reviewer against the implementation plan and full branch diff; fix every Critical/Important finding and re-review.
- [ ] Record surprising results, especially any direction reversals after unit correction, without converting them into manuscript claims.
- [ ] Commit the compliance audit and solution update.
- [ ] Push `feature/marimo-scientific-pipeline`, update PR #1's description with fresh validation evidence, and leave S7/results freeze open for human independent review.
