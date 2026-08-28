# Census Community-Area Covariates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and integrate four reproducible 2020–2024 ACS covariates for Chicago's 77 community areas from frozen official Census tract, block, and replicate inputs.

**Architecture:** A focused `census_covariates` module will own variable mappings, whole-block community assignment, sex-age population weights, replicate propagation, validation, and artifact writing. Existing public-source normalization will freeze the additional block and variance inputs, and the analytic dataset builder will join the finished 77-row artifact without executing models or changing authorization.

**Tech Stack:** Python 3.13, pandas, GeoPandas/Shapely, pyarrow, httpx, pytest, Typer, existing snapshot/provenance contracts.

## Global Constraints

- Never area-weight percentages or disease values.
- Derive percentages only after allocating and summing numerator and denominator counts.
- Use the B17001 universe “population for whom poverty status is determined.”
- Preserve `results_authorized=false`; do not execute adjusted primary models.
- Chicago Health Atlas and the separate City ACS product are comparison sources only.
- All acquired official bytes require immutable snapshot identity and SHA-256 provenance.

---

### Task 1: Deterministic allocation and replicate engine

**Files:**
- Create: `src/chicagohealthmap/external/census_covariates.py`
- Create: `tests/unit/external/test_census_covariates.py`

**Interfaces:**
- Produces: `assign_blocks_to_communities(blocks, communities) -> pd.DataFrame`
- Produces: `build_block_weights(block_counts, assignments) -> pd.DataFrame`
- Produces: `derive_community_covariates(acs, weights, replicates=None) -> tuple[pd.DataFrame, pd.DataFrame]`
- Produces: `validate_community_covariates(frame) -> None`

- [ ] **Step 1: Write failing tests for whole-block assignment**

  Test that Census internal points produce exactly one community ID per block, preserve tract and block GEOIDs, reject points outside all communities, and retain a boundary-touch diagnostic.

- [ ] **Step 2: Run the focused assignment tests and confirm RED**

  Run: `uv run pytest tests/unit/external/test_census_covariates.py -q`

  Expected: collection/import failure because `census_covariates` does not exist.

- [ ] **Step 3: Implement whole-block point assignment**

  Parse community WKT through GeoPandas, build block points from `INTPTLON20` and `INTPTLAT20`, spatially join using `within`, and fail unless every eligible Chicago block maps one-to-one.

- [ ] **Step 4: Write failing tests for sex-age block weights**

  Cover B01001-to-P12 one-to-one leaf mappings, B17001 sex-age bins formed from one or more P12 leaves, nonnegative weights, within-tract/component sums of one, and the zero-ancillary rule.

- [ ] **Step 5: Implement mapping constants and block weights**

  Use B01001 leaf cells `003`–`025` and `027`–`049`; align each with the same P12 sex-age leaf. Represent B17001 below- and at/above-poverty leaf cells by explicit P12 cell tuples matching sex and age. Allocate every ACS leaf estimate through its matching block ancillary count.

- [ ] **Step 6: Write failing tests for estimates, ratios, and replicates**

  Assert exact community sums, `pct_female`, `pct_age_65_plus`, `pct_below_fpl`, `acs_adult_population`, 80-replicate standard errors, and missing-replicate reason codes. Verify poverty never uses total population as its denominator.

- [ ] **Step 7: Implement derived covariates and uncertainty**

  Apply fixed weights to published and replicate leaf estimates, aggregate by community, derive all four covariates, and calculate replicate SE as `sqrt(4/80 * sum((replicate - estimate)^2))`. Emit 90% MOE as `1.645 * SE` and explicit uncertainty status.

- [ ] **Step 8: Add validation failures and run GREEN**

  Reject anything other than 77 IDs `01`–`77` in production validation, duplicate IDs, missing/nonfinite fields, negative counts, percentages outside `[0,100]`, adult counts above total population, or failed allocation reconciliation.

  Run: `uv run pytest tests/unit/external/test_census_covariates.py -q`

- [ ] **Step 9: Commit Task 1**

  Commit: `feat: add Census community covariate engine`

### Task 2: Freeze official block inputs and build governed artifacts

**Files:**
- Modify: `config/source_registry.yml`
- Modify: `src/chicagohealthmap/sources/adapters/census.py`
- Modify: `src/chicagohealthmap/external/normalize.py`
- Modify: `src/chicagohealthmap/cli.py`
- Modify: `tests/unit/sources/adapters/test_census.py`
- Modify: `tests/unit/external/test_normalize.py`
- Create: `tests/integration/test_census_community_covariates.py`

**Interfaces:**
- Produces normalized tables `census_decennial_2020_p12_block`, `census_tiger_2020_block`, and optional `census_acs_2024_5y_variance_replicates`.
- Produces artifact files `data/processed/public/census_acs_2024_community_area_covariates.parquet`, schema JSON, allocation diagnostics, and comparison CSV.

- [ ] **Step 1: Write failing adapter tests for P12 blocks**

  Require Cook County block geography fields, unique 15-digit block GEOIDs, P12 estimate fields, raw-string preservation, deterministic request metadata, and rejection of non-Cook or duplicate rows.

- [ ] **Step 2: Implement block API acquisition and TIGER block validation**

  Extend the Census adapter with a block-grain P12 request and an exact 2020 Cook County TIGER block archive contract. Keep credentials out of persisted request records.

- [ ] **Step 3: Register and acquire official inputs**

  Add exact Census landing, documentation, endpoint, release, geography, license, request, fallback, verification, and citation metadata. Freeze the P12 response and TIGER archive under dated public snapshots and update the public checksum inventory.

- [ ] **Step 4: Write failing normalization and integration tests**

  Use miniature frozen fixtures to require normalized block IDs/internal points/P12 leaves, source lineage, deterministic 77-row output, schemas, diagnostics, and `results_authorized=false` separation.

- [ ] **Step 5: Implement normalization and artifact build**

  Normalize only the required P12 estimates and Cook County block fields, run the Task 1 engine against the already-normalized 2024 ACS B01001/B17001 tracts and community boundaries, and write deterministic artifacts.

- [ ] **Step 6: Attempt official variance-replicate acquisition**

  If 2024 B01001/B17001 tract replicate tables are available at the documented Census summary level, freeze and normalize all 80 replicates. Otherwise emit `unavailable_no_variance_replicates` and retain ordinary ACS MOEs only as diagnostics.

- [ ] **Step 7: Verify Task 2 GREEN**

  Run: `uv run pytest tests/unit/sources/adapters/test_census.py tests/unit/external/test_normalize.py tests/integration/test_census_community_covariates.py -q`

- [ ] **Step 8: Commit Task 2**

  Commit: `feat: build governed Census community covariates`

### Task 3: Integrate covariates and preserve governance

**Files:**
- Modify: `src/chicagohealthmap/analysis/dataset.py`
- Modify: `tests/unit/analysis/test_dataset.py`
- Modify: `tests/unit/analysis/test_sap_analyses.py`
- Modify: `docs/analysis/data_dictionary.md`
- Modify: `docs/methods/data_sources.md`
- Modify: `docs/analysis/sap_notebook_compliance_audit.md`

**Interfaces:**
- Consumes: `data/processed/public/census_acs_2024_community_area_covariates.parquet`
- Produces: community rows containing `pct_age_65_plus`, `pct_female`, `pct_below_fpl`, and `acs_adult_population` plus source, period, universe, method, and uncertainty fields.

- [ ] **Step 1: Write failing dataset tests**

  Require a one-to-one join for all primary community rows, no covariate inheritance by tract rows, exact source/method labels, failure on missing or duplicate covariate IDs, and manifest checksums for the covariate artifact.

- [ ] **Step 2: Implement fail-closed dataset integration**

  Load and validate the 77-row artifact, join by normalized ID, add covariate columns and lineage, and keep all tract covariate fields null because the primary adjustment set is community-area grain.

- [ ] **Step 3: Verify readiness without model execution**

  Update tests so the reconstructed fixture moves C1/C2 readiness to mechanical readiness while `primary_adjusted_models_executed=false` and `results_authorized=false` remain unchanged.

- [ ] **Step 4: Update methods and audit documentation**

  Document the official inputs, formulas, block weighting, replicate status, Atlas comparison role, assumptions, diagnostics, checksums, and remaining human S7/reliability actions.

- [ ] **Step 5: Run focused and full verification**

  Run:

  - `uv run pytest tests/unit/external/test_census_covariates.py tests/integration/test_census_community_covariates.py tests/unit/analysis/test_dataset.py tests/unit/analysis/test_sap_analyses.py -q`
  - `uv run pytest -q`
  - `uv run ruff check .`
  - `uv run mypy src`
  - `git diff --check`

- [ ] **Step 6: Commit Task 3**

  Commit: `feat: integrate reconstructed ACS covariates`

### Task 4: Finish the feature branch

**Files:**
- Review all task diffs and generated artifact manifests.

- [ ] **Step 1: Re-run fresh verification required for completion claims**

  Confirm test counts, lint/type results, artifact row counts, checksum reconciliation, and authorization flags from current HEAD.

- [ ] **Step 2: Use `superpowers:finishing-a-development-branch`**

  Present the verified branch disposition without merging, pushing, or changing authorization unless the user explicitly requests it.
