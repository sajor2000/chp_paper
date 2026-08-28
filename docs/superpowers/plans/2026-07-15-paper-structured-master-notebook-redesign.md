# Paper-Structured Master Notebook Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `notebooks/00_master_chicago_healthmap_pipeline.py` into the deterministic, paper-structured, end-to-end Chicago Health Map analysis while preserving governance and the existing dataset CLI.

**Architecture:** Keep statistical calculations in the tested analysis modules and use the master marimo notebook as the visible orchestration, interpretation, and export layer. Extend the dataset builder with a backward-compatible output stem and auditable data-book/source-join artifacts, then make the notebook build or checksum-reuse its own `00_master_analytic_dataset` before analysis. Bind all narrative and displays to governed result objects and keep `results_authorized=false` fail-closed.

**Tech Stack:** Python 3.12+, pandas, GeoPandas, statsmodels, SciPy, Matplotlib, Great Tables, marimo, Pydantic, pytest, Ruff, mypy, Paperclip/PubMed, Ref, Tavily snapshot fallback.

## Global Constraints

- Preserve the 22,540-row, 90-column contract, including 20,692 tract and 1,848 community-area records, periods 2019-2024, 4 condition IDs, and a unique geography-period-condition key.
- Preserve direct, uninterpolated Chicago Health Map disease values.
- Default dataset output stem remains `chicago_case_studies_analytic`; the master notebook uses `00_master_analytic_dataset`.
- Keep `results_authorized=false`; C1 is audit-only because maximum VIF is 5.016 (>5); C2 is a freeze candidate, not an authorized manuscript result.
- Exactly 5 main displays: Table 1, Figures 1-3, and Table 2. Do not duplicate exact primary evidence across a main table and figure.
- Every marimo cell is at most 30 lines. Script mode is deterministic and noninteractive.
- Use complementarity language; do not claim prediction, validation, population prevalence, causality, underdiagnosis, unmet need, access failure, error, or service need.
- Tavily live author-instruction extraction was quota-blocked on 2026-07-15; use the verified 2026-07-14 project snapshot and do not claim live JAMA compliance.

---

### Task 1: Extend the dataset artifact interface

**Files:**
- Modify: `tests/unit/analysis/test_dataset.py`
- Modify: `src/chicagohealthmap/analysis/dataset.py`
- Modify: `src/chicagohealthmap/cli.py`

**Interfaces:**
- `build_chicago_case_study_dataset(root, output_dir, output_stem="chicago_case_studies_analytic") -> AnalyticDatasetArtifacts`
- New artifact paths: data-book CSV/HTML and source-join manifest JSON.

- [ ] Add failing tests for custom/default stems, all artifact names, checksums, data-book rows, source/join roles, and CLI compatibility.
- [ ] Run `uv run pytest tests/unit/analysis/test_dataset.py -k 'stem or data_book or source_join' -v` and verify the expected API/artifact failures.
- [ ] Implement the minimal stem validation and artifact serialization; make schema and manifest dataset IDs match the selected stem while preserving the default.
- [ ] Run `uv run pytest tests/unit/analysis/test_dataset.py tests/unit/test_cli.py -q`.
- [ ] Commit with `feat: add governed master dataset artifacts`.

### Task 2: Add checksum reuse and rebuild governance

**Files:**
- Modify: `tests/unit/analysis/test_dataset.py`
- Modify: `src/chicagohealthmap/analysis/dataset.py`
- Modify: `notebooks/00_master_chicago_healthmap_pipeline.py`

**Interfaces:**
- `ensure_chicago_case_study_dataset(root, output_dir, output_stem, rebuild=False) -> DatasetBuildDecision`

- [ ] Add failing tests proving checksum-matching reuse, source-change rebuild, explicit rebuild, and rejection of partial/stale artifact sets.
- [ ] Verify RED with focused pytest.
- [ ] Implement fail-closed checksum comparison and deterministic decision metadata.
- [ ] Update notebook parameters with a deliberate rebuild control and script-mode default `False`; analyze the artifact produced or reused in the same run.
- [ ] Verify focused dataset and notebook contract tests.
- [ ] Commit with `feat: govern master dataset reuse and rebuild`.

### Task 3: Enforce paper sequence, result contracts, and inference boundaries

**Files:**
- Modify: `tests/unit/analysis/test_master_notebook_contract.py`
- Modify: `tests/unit/analysis/test_reporting.py`
- Modify: `src/chicagohealthmap/analysis/reporting.py`
- Modify: `notebooks/00_master_chicago_healthmap_pipeline.py`

**Interfaces:**
- Paper sections in exact order: Introduction; Methods; Results; Interpretation and So What?; Artifact gallery and deterministic manifest.
- Governed result objects contain estimand, estimate/CI/n when eligible, diagnostics, sensitivity, authorization, and inference boundary.

- [ ] Add failing contract tests for the paper order, both interpretation layers after each case, C1 manuscript exclusion, C2 freeze-candidate wording, and required equation/parameter explanations.
- [ ] Verify RED with focused pytest.
- [ ] Rewrite notebook markdown in JAMA style using only verified project/PubMed claims and adjacent technical explanations.
- [ ] Keep C1 numeric diagnostics out of manuscript-importable Results prose and preserve all prohibitions.
- [ ] Verify focused reporting and notebook contract tests.
- [ ] Commit with `feat: restructure master notebook as paper`.

### Task 4: Rebuild the 5 main displays and supplement split

**Files:**
- Modify: `tests/unit/analysis/test_master_notebook_contract.py`
- Modify: `tests/integration/test_master_notebook.py`
- Modify: `notebooks/00_master_chicago_healthmap_pipeline.py`

**Interfaces:**
- Main: editable Table 1, vector/raster Figures 1-3, editable Table 2.
- Supplement: coefficient forest, residual, Q-Q, leverage, influence, weight, annual, and extended-sensitivity displays.

- [ ] Add failing tests for exactly 5 main displays, required panel content, complete legends/notes, no C1 primary coefficient in Figure 2, and supplement-only diagnostics.
- [ ] Verify RED.
- [ ] Implement centralized JAMA-oriented Matplotlib styling and mirrored case-study visual grammar.
- [ ] Export deterministic PDF/PNG and editable CSV/HTML tables.
- [ ] Verify focused contract/integration tests and inspect journal-size, grayscale, and color-vision simulation renders.
- [ ] Commit with `feat: rebuild journal display set`.

### Task 5: Complete provenance, gallery, and two-run verification

**Files:**
- Modify: `tests/integration/test_master_notebook.py`
- Modify: `notebooks/00_master_chicago_healthmap_pipeline.py`
- Create: `docs/analysis/master_notebook_research_provenance.md`

- [ ] Add failing integration assertions for the master dataset contract, source/join manifest, gallery, output registry, `results_authorized=false`, and byte-identical two-run outputs.
- [ ] Record Ref documentation URLs, PubMed records, verified Paperclip claims, and the Tavily quota blocker.
- [ ] Execute script mode twice and compare all governed hashes.
- [ ] Run strict marimo check and an interactive render smoke test.
- [ ] Commit with `test: verify paper-structured master notebook`.

### Task 6: Full quality gate and review

- [ ] Run `uv run ruff format --check src tests notebooks`.
- [ ] Run `uv run ruff check src tests notebooks`.
- [ ] Run `uv run mypy`.
- [ ] Run `uv run pytest -q`.
- [ ] Run `uv run marimo check --strict notebooks/00_master_chicago_healthmap_pipeline.py`.
- [ ] Run the notebook top to bottom twice and compare checksums.
- [ ] Run the manuscript auditor and inspect the final displays.
- [ ] Request code review using the Compound Engineering workflow; fix verified Critical/Important findings and rerun affected gates.
- [ ] Open the final notebook in marimo, verify a clean working tree, and keep the branch without pushing or opening a PR.
