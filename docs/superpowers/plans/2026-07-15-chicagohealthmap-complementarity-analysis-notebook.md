# Chicago Health Map Complementarity Analysis Notebook Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Implement a tested CHM complementarity dataset and marimo notebook that executes adjusted C1/C2 ecological models, displays alpha/beta/gamma coefficients and uncertainty, and preserves S7 authorization gates.

**Architecture:** Keep the frozen parquet dataset as the source of truth. Extend tested analysis modules to propagate community-area covariates, fit centered/scaled HC3 primary models, compute covariance-correct contrasts and adjusted spatial diagnostics, and expose typed result bundles. Rebuild the notebook as a thin seven-section narrative that calls those modules and emits deterministic artifacts.

**Tech Stack:** Python 3.12+, pandas, NumPy, SciPy, validated repository OLS/HC3 math, GeoPandas/Shapely, matplotlib, marimo, pandas HTML/CSS styling, pytest, ruff, mypy, uv.

## Global Constraints

- Primary unit: one Chicago community area; C1 has 77 eligible areas when gates pass and C2 has the documented 76-area COPD subset.
- Primary adjustment set: pct_age_65_plus, pct_female, pct_below_fpl, and capture_rate_mean_2022_2024; acs_adult_population is descriptive/sensitivity-only.
- Primary estimator: equal-weighted OLS with HC3 covariance; CHM exposures use frozen model-specific IQR scaling; adjustment covariates use frozen SD scaling.
- C1 and C2 form one confirmatory family with two-sided 97.5% CIs; separate hypertension/diabetes coefficients use 95% CIs.
- C1 joint uncertainty uses the full covariance matrix, including the hypertension-diabetes covariance term.
- Moran diagnostics use adjusted residuals, 9999 conditional permutations, the frozen seed, and the frozen queen weights checksum.
- Spatial-error sensitivity is mandatory when abs(Moran I) is at least 0.10 and permutation P is less than .05; it never replaces OLS.
- EHR exposures are labeled “EHR-diagnosed proportion among observed CAPriCORN adults,” never population prevalence.
- No empirical Results, abstract findings, Key Points, or conclusions are authorized while results_authorized is false.
- Preserve untracked Downloads/ and tmp/; every task ends with a focused test and commit.

---

## Task 1: Propagate frozen ACS covariates into the 77-area frame

**Files:** Modify src/chicagohealthmap/analysis/case_studies.py lines 181-207; modify src/chicagohealthmap/analysis/sap_analyses.py lines 18-145; test tests/unit/analysis/test_case_studies.py and tests/unit/analysis/test_sap_analyses.py.

**Interfaces:** build_primary_community_frame(dataset: pandas.DataFrame) returns one row per community area with four primary adjustment columns, aligned capture, adult population, exposures, and outcome. ADJUSTMENT_COVARIATES becomes exactly pct_age_65_plus, pct_female, pct_below_fpl, capture_rate_mean_2022_2024. assess_primary_model_readiness reports adjusted complete n, design rank, gates, and status.

- [ ] Step 1: Write the failing frame test. Call build_primary_community_frame on the existing fixture and assert 2 unique areas, nonmissing pct_age_65_plus/pct_female/pct_below_fpl/acs_adult_population, nonmissing capture_rate_mean_2022_2024, and one value per area for pct_age_65_plus.
- [ ] Step 2: Run uv run pytest tests/unit/analysis/test_case_studies.py::test_build_primary_community_frame_carries_one_frozen_covariate_value_per_area -q. Expected: failure because the current frame drops covariates.
- [ ] Step 3: Implement deterministic covariate extraction. Group contemporary community rows by geography, reject within-area disagreement, join the four primary covariates plus adult population, and retain the existing mean capture. Raise CaseStudyAnalysisError for missing, duplicate, or conflicting values.
- [ ] Step 4: Run uv run pytest tests/unit/analysis/test_case_studies.py -q.
- [ ] Step 5: Write and run a failing readiness test asserting C1 design_columns equals 7, C2 equals 6, readiness is not withheld for missing covariates, and adult population is not in the primary set.
- [ ] Step 6: Update readiness numeric validation, eligibility columns, and metadata. Add capture to the required model fields and remove adult population from primary design columns.
- [ ] Step 7: Run uv run pytest tests/unit/analysis/test_sap_analyses.py -q and commit with message feat: propagate frozen covariates into primary frame.

## Task 2: Implement governed adjusted C1/C2 result bundles

**Files:** Modify src/chicagohealthmap/analysis/sap_analyses.py; test tests/unit/analysis/test_sap_analyses.py.

**Interfaces:** Add immutable GovernedModelResult with model_id, coefficients, contrasts, residuals, design_columns, scaling, and metadata. Add fit_primary_models(frame: pandas.DataFrame) returning dict[str, GovernedModelResult]. Add build_coefficient_table(results) returning pandas.DataFrame. Coefficient rows include model, term, role, estimate, robust SE, CI limits, confidence level, scale, unit, n, covariance type, and analysis status.

- [ ] Step 1: Write the failing coefficient test. Assert C1 contains alpha, beta_h, beta_d, gamma_age65, gamma_female, gamma_poverty, and gamma_capture; roles are intercept/exposure/adjustment; the C1 contrast estimate equals beta_h plus beta_d after IQR scaling; and its confidence level is .975.
- [ ] Step 2: Run uv run pytest tests/unit/analysis/test_sap_analyses.py::test_primary_models_return_scaled_coefficients_and_joint_contrast -q. Expected: missing-function failure.
- [ ] Step 3: Implement model-specific complete-case fitting with frozen exposure centers/IQRs, covariate centers/SDs, positive-scale checks, transformed design, and existing validated HC3 math.
- [ ] Step 4: Implement covariance-correct contrast vectors and variance c @ covariance @ c. Report C1/C2 at 97.5% and separate hypertension/diabetes rows at 95%. Store scales, centers, eligible geography checksum, formula, and status.
- [ ] Step 5: Add fail-closed tests for missing covariates, zero IQR/SD, nonfinite HC3 covariance, n below 70, rank deficiency, and fewer than 10 distinct exposure values.
- [ ] Step 6: Run uv run pytest tests/unit/analysis/test_sap_analyses.py -q; uv run ruff check on changed files; uv run mypy src/chicagohealthmap/analysis/sap_analyses.py.
- [ ] Step 7: Commit with message feat: add governed adjusted primary models.

## Task 3: Compute adjusted residual diagnostics and spatial-error sensitivity

**Files:** Modify src/chicagohealthmap/analysis/spatial.py and src/chicagohealthmap/analysis/sap_analyses.py; test tests/unit/analysis/test_spatial.py and tests/unit/analysis/test_sap_analyses.py.

**Interfaces:** Add build_adjusted_residuals(results) returning model-keyed pandas Series. Add immutable SpatialErrorResult with lambda, coefficients, covariance, log likelihood, convergence, weights checksum, and metadata. Add fit_spatial_error_sensitivity(outcome, design, weights) using bounded concentrated likelihood over an admissible lambda interval. Existing permutation_moran must receive adjusted residuals and retain deterministic 9999-permutation metadata.

- [ ] Step 1: Write a failing test asserting C1/C2 residual IDs equal adjusted model populations and metadata says adjusted_primary_residual.
- [ ] Step 2: Run the focused test and verify current unadjusted residual behavior fails it.
- [ ] Step 3: Implement adjusted residual extraction and pass residuals through frozen queen weights.
- [ ] Step 4: Write a failing spatial-error test with a connected synthetic row-standardized matrix; assert finite coefficients, admissible lambda, convergence, and checksum.
- [ ] Step 5: Implement the estimator: for each admissible lambda transform y and X by I minus lambda W, solve GLS, estimate innovation variance, and maximize concentrated log likelihood. Reject islands, nonfinite matrices, nonconvergence, and unsafe bounds.
- [ ] Step 6: Add escalation-gate tests proving both thresholds are required.
- [ ] Step 7: Run uv run pytest tests/unit/analysis/test_spatial.py tests/unit/analysis/test_sap_analyses.py -q and commit with message feat: add adjusted residual and spatial error diagnostics.

## Task 4: Add publication-grade tables, figures, and language helpers

**Files:** Create src/chicagohealthmap/analysis/reporting.py and tests/unit/analysis/test_reporting.py.

**Interfaces:** render_styled_html(table, title, notes) returns deterministic accessible HTML. render_coefficient_sentence(row) returns noncausal unit-aware language. build_publication_coefficient_table(coefficients, contrasts) builds Table 2 rows while retaining full alpha/gamma rows for the supplement. build_complementarity_map_frame(geometry, primary_frame) retains all 77 areas and explicit availability states. save_figure_with_metadata writes deterministic PNGs.

- [ ] Step 1: Write failing tests for HTML title/caption/headers/units/notes, coefficient sentences containing associated, 1-IQR, exact CI and four covariates, rejection of causal/population-prevalence wording, and 77-area map-state preservation.
- [ ] Step 2: Run uv run pytest tests/unit/analysis/test_reporting.py -q and verify missing-module failure.
- [ ] Step 3: Implement fixed pandas HTML/CSS; keep CSV as the machine-readable source and HTML as the readable companion.
- [ ] Step 4: Implement sentence rendering from result fields; state n, exposure scale, adjustment set, estimate, confidence interval, and ecological boundary.
- [ ] Step 5: Implement map/figure helpers with colorblind-safe condition colors, direct labels, units, hatching for suppressed/missing states, and fixed metadata.
- [ ] Step 6: Run focused tests, ruff, and mypy; commit with message feat: add publication reporting helpers.

## Task 5: Rebuild the marimo notebook in the seven approved sections

**Files:** Modify notebooks/02_chicago_case_studies.py, tests/unit/analysis/test_case_studies_notebook_contract.py, and tests/integration/test_case_studies_notebook.py.

**Interfaces:** The notebook calls the frozen loader/frame/readiness/model/coefficient/residual/Moran/spatial-error/reporting/concordance helpers. Script mode accepts --output-dir and writes deterministic outputs; interactive mode only filters display views. The manifest records hashes, runtime metadata, America/Chicago, execution status, and authorization.

- [ ] Step 1: Update notebook tests first. Require headings Data cleaning, Data quality checks, Analytic data set, Descriptive statistics, Case study one, Case study two, and Tables and figures; require alpha/beta/gamma language, corrected adjustment text, adjusted residual wording, 97.5% intervals, and an unauthorized banner.
- [ ] Step 2: Run uv run pytest tests/unit/analysis/test_case_studies_notebook_contract.py -q and verify current notebook fails.
- [ ] Step 3: Rewrite cells in the approved order. Keep every cell under the existing 30-line contract; each section has adjacent Question/Data/Method/Equation or glossary/Why/Assumptions markdown; cells orchestrate only.
- [ ] Step 4: Implement sections 1–4: manifests/checksums, source roles, record flow, coverage, suppression, missingness, capture, covariate completeness, 77/76 frames, schema, Table 1, distributions, and nonranked context summaries.
- [ ] Step 5: Implement sections 5–6: adjusted C1/C2 candidates when ready, full alpha/beta/gamma tables, covariance-correct contrasts, generated sentences, influence, adjusted Moran, spatial-error sensitivity when gated, and external concordance.
- [ ] Step 6: Implement section 7: Table 1, complementary Atlas/CHM Figure 1, cardiometabolic Figure 2, respiratory Figure 3, Table 2, supplement CSVs, and one result ledger.
- [ ] Step 7: Preserve authorization. Replace literal assignment with read-only governance state; candidate execution may be true while manuscript use remains false; show freeze candidate — manuscript use unauthorized.
- [ ] Step 8: Run uvx marimo check notebooks/02_chicago_case_studies.py, run the notebook in script mode with a manual output directory, and run the notebook unit/integration tests.
- [ ] Step 9: Commit with message feat: build seven-section CHM complementarity notebook.

## Task 6: Add evidence, display, and AI-accountability contracts

**Files:** Create docs/analysis/chm_complementarity_evidence_ledger.md, docs/analysis/chm_complementarity_display_ledger.csv, and tests/unit/test_complementarity_contract.py. Modify docs/manuscript/reporting_matrix.csv and docs/manuscript/ai_disclosure_template.md.

- [ ] Step 1: Write failing ledger tests requiring every primary claim to have source artifact, denominator, unit, period, uncertainty, analysis status, and permitted language; prohibit population-prevalence and causal labels.
- [ ] Step 2: Run uv run pytest tests/unit/test_complementarity_contract.py -q and verify missing-artifact failure.
- [ ] Step 3: Create the ledgers from the frozen specification, leaving empirical estimates as explicit freeze candidates until the governed notebook emits them.
- [ ] Step 4: Record tool-assisted implementation disclosure with human-author responsibility and verified Paperclip/PubMed/source-record references.
- [ ] Step 5: Run the contract tests and commit with message docs: add CHM complementarity evidence contracts.

## Task 7: Deterministic rebuild, independent review, and verification

**Files:** Create docs/analysis/chm_complementarity_s7_review.md. Modify tests/integration/test_offline_rebuild.py only if output inventory changes.

- [ ] Step 1: Run uv run pytest -q and record exact count and elapsed time.
- [ ] Step 2: Run ruff on src/tests/notebook, mypy src/chicagohealthmap, and uvx marimo check.
- [ ] Step 3: Run two clean notebook builds with PYTHONHASHSEED=0; compare every checksum, population, CI level, and authorization field.
- [ ] Step 4: Independently reconstruct the C1 transformed design, HC3 covariance, and beta_h plus beta_d; compare within tolerance.
- [ ] Step 5: Independently reproduce adjusted Moran with frozen residuals, queen weights, seed, and 9999 permutations.
- [ ] Step 6: Review five displays for units, CIs, source-role wording, suppression/missingness, no duplicate results, and no forbidden causal terms.
- [ ] Step 7: Write S7 review separating verified, author decision needed, and not checked; retain results_authorized=false unless governance explicitly changes it.
- [ ] Step 8: Commit review artifact with message test: verify CHM complementarity rebuild and S7 artifacts.

## Plan self-review

- Tasks 1–2 cover frozen covariates, alpha/beta/gamma, scaling, HC3, C1/C2, multiplicity, and fail-closed readiness.
- Task 3 covers adjusted residual Moran diagnostics and spatial-error escalation.
- Task 4 covers tables, figures, and interpretation sentences.
- Task 5 covers all seven notebook sections and deterministic outputs.
- Task 6 covers JAMA evidence/display contracts and AI disclosure.
- Task 7 covers deterministic rebuild and independent numerical checks.
- The plan uses exact paths, interfaces, tests, commands, and commits; no TBD/TODO placeholders remain.
- Ref MCP was queried for marimo, Great Tables, statsmodels, and PySAL. Marimo official docs were found; Great Tables and statsmodels searches returned no result; PySAL returned repository documentation only. The plan therefore retains validated in-repository HC3/spatial math unless current official package APIs are verified before adding dependencies.

