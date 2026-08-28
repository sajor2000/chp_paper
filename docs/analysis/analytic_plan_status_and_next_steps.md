# Chicago Health Map — Analytic Plan: Done vs. To-Do

**Date:** 2026-07-16
**Branch:** `codex/chm-paper-master-redesign`
**Governing documents:** `statistical_analysis_plan.md` (CHM-SAP-001, v0.2 freeze-candidate), `master_notebook_manuscript_plan.md`, `2026-07-15-paper-structured-master-notebook-redesign.md`
**Standing constraints:** `results_authorized=false`; complementarity claim only (no prediction, validation, prevalence, causality, underdiagnosis, unmet need, access failure, error, service need); C1 withheld (max VIF 5.016 > 5); C2 freeze-candidate; exactly 5 main displays; 22,540×90 dataset contract; direct CHM disease values uninterpolated.

> This is a *delta plan*: it inventories what the current implementation already does and specifies the remaining analytic work, including method additions grounded in the 2026-07-16 literature pass. It does not change the frozen SAP; items marked **[SAP deviation]** require a signed deviation record before implementation.

---

## Part A — Status inventory

### A1. Complete and committed

| Component | Evidence | Notes |
|---|---|---|
| Governed dataset builder + artifacts | commits `de9313e`, `b2173d9`; `outputs/frozen/*` | Parquet/CSV/schema/lineage/manifest/source-join/data-book; checksum reuse + rebuild control; default stem `chicago_case_studies_analytic`, master stem `00_master_analytic_dataset`. Contract verified at 22,540 rows × 90 cols, 20,692 tract + 1,848 community-area, 2019–2024, 4 condition IDs. |
| Paper-structured master notebook | commit `7656ee2` + follow-ups | Introduction → Methods → Results → Interpretation/So-What → Artifact gallery; two interpretation layers per case; C1/C2 governance wording bound to result objects. |
| Five main displays + supplement split | `paper_displays.py`; display-redesign commits | Table 1, Figures 1–3, Table 2; forest plot + diagnostics moved to supplement; JAMA-oriented Matplotlib styling; deterministic PDF/PNG. |
| Provenance / gallery / two-run verification | `outputs/notebooks/master-test-*-first/-second`; provenance CSVs | Source/join manifest, output registry, byte-identical two-run scaffolding. |
| **Tract complementarity (descriptive)** | `tract_complementarity.py` | Percentile concordance (Spearman primary, Pearson supportive), discordance categories, quadratic-weighted kappa, within-community heterogeneity (rank-based), community-area aggregation loss (rank-based), cluster bootstrap concordance. |
| **Spatial (community-area models)** | `spatial.py` | Queen/rook/distance weights, global permutation Moran's I (9999 perms), spatial-error sensitivity + stability classification. |
| **C1 / C2 primary models** | `case_studies.py`, `sap_analyses.py`, `robustness.py` | Unweighted OLS + HC3, frozen-IQR scaling, VIF gate, influence diagnostics, robustness suite (weights, LOO, disruption, annual, topology). **C1 audit-only (withheld); C2 freeze-candidate; not manuscript-importable.** |
| Static quality gates (partial) | this session | `ruff check` ✅ pass; `mypy` ✅ pass (55 files). |

### A2. Partially done / not yet verified this session

| Component | Status | Gap |
|---|---|---|
| `ruff format --check` | ❌ fails | 14 files need reformatting (notebooks/02, dataset_artifacts, paper_displays, reporting, sap_analyses, census_covariates, pipeline, several tests). |
| `pytest -q` full suite | ⏳ not run | Needs a clean run + record. |
| `marimo check --strict` | ⏳ unverified | Confirm exit status on master notebook. |
| Two-run byte-identical checksum compare | ⏳ scaffolded, not re-verified | Execute script mode twice, diff governed hashes. |
| Compound Engineering code review | ⏳ not done | Final review + resolve verified findings. |

### A3. Open by governance (not a coding gap)

- SAP freeze gates **S4 (EHR semantics), S5 (blinded selection), S6 (SAP sign-off), S7 (validation)** remain open; phenotype/suppression semantics unresolved.
- `results_authorized=false` remains binding — no Results/Abstract/Key Points/Discussion prose is authorized.
- Live JAMA Instructions-for-Authors: Tavily quota-blocked (2026-07-15); using verified 2026-07-14 snapshot; no live-compliance claim.

---

## Part B — Remaining analytic work

### B0. Strategic reframing decision (blocks display emphasis) — **[SAP deviation]**
Current rhetorical weight sits on the community-area life-expectancy models (C1/C2), which are withheld/candidate. The strongest *authorized* and *data-supported* evidence is the tract within-community-area heterogeneity + EHR/PLACES concordance–discordance lens.
- **Action:** SAP owners decide whether to elevate the descriptive tract complementarity as the primary contribution and present C1/C2 as withheld/candidate "so-what" bridges. Record deviation; update `master_notebook_manuscript_plan.md`.
- **Rationale from data (2026-07-16, directional):** within-community-area share of tract variance ≈ 24% (HTN), 51% (diabetes), 45% (COPD); EHR–PLACES Spearman 0.85 / 0.60 / 0.69; dispersion ratio 1.00 / 1.34 / 0.64 — micro-community signal strong for diabetes & COPD, weak for HTN; "smoothing/compression" is **condition-specific**, not general.

### B1. Tier 1 — descriptive, `results_authorized`-compatible, adds now

1. **Variance-share headline statistic.** Add between-/within-community-area variance share alongside existing rank summaries in `tract_complementarity.py`. Age-standardize (2000 US std), pool 2022–2024 per SAP §7, handle crossing tracts (dominant-assignment primary + many-to-many sensitivity).
   *Acceptance:* per-condition within-CA share with bootstrap CI; sensitivity excluding crossing tracts.
2. **Multilevel VPC/ICC + discriminatory accuracy (MAIHDA framing).** Two-level model, tracts nested in community areas, per condition. Report VPC/ICC and area-level discriminatory accuracy (AUC: how well community-area membership classifies high/low tract burden).
   *Grounding:* Merlo/Kaufman/Leckie 2026 (PMID 41734011); Persmark 2019 (PMID 31454361); Wilkes/Karimi 2024 critique (PMID 38401177). *Caveat:* n=77 upper units → limited precision; state it.
   *Acceptance:* new `sap_analyses`/`tract_complementarity` function + tests; VPC and AUC per condition.
3. **MAUP / scale-sensitivity table.** Recompute concordance + dispersion + discordance shares at tract vs community-area (and ZIP if constructible from frozen sources).
   *Grounding:* Jones & Kulldorff resolution study (PMC3480474); Thomas 2024 (already in SAP register).
   *Acceptance:* scale × condition metric table; supplement figure.
4. **Uncertainty-propagated concordance.** Monte-Carlo propagate PLACES 95% CI (+ ACS MOE; optional EHR small-count uncertainty) into discordance classification; only label "discordant" when the gap exceeds combined uncertainty.
   *Grounding:* Srebotnjak/Mokdad/Murray (PMC2958154); Goodman (PMC2831787).
   *Acceptance:* uncertainty-aware discordance categories + share of gaps exceeding uncertainty.

### B2. Tier 2 — spatial descriptive, supplement-strength

5. **Bivariate LISA (EHR × PLACES) + univariate LISA/Gi\*.** Map spatial agreement vs divergence; recover local hotspots invisible at community-area scale. SAP §11 permits exploratory tract pattern (bars only hotspot-driven case selection).
   *Acceptance:* bivariate + univariate cluster maps; cluster counts by significance; supplement only.
6. **Spatial scan statistic (SaTScan / flexible scan).** Significant EHR clusters; test survival under community-area aggregation.
   *Grounding:* COPD precedent Iwahara 2025 (PMC12004005); resolution Jones & Kulldorff.
   *Acceptance:* cluster table (RR, p, size) per condition; aggregation-survival note.

### B3. Tier 3 — governance conversations (touch withheld models) — **[SAP deviation]**

7. **Composite cardiometabolic index to unblock C1.** Combine HTN + diabetes a priori (standardized sum or first PC) into one exposure → removes the collinearity that triggered VIF 5.016. Changes estimand; requires prespecified deviation.
8. **Small-n stable estimator.** Bayesian regression with weakly-informative priors / partial pooling as a supportive estimator for the 77-area models (more stable than OLS+HC3; handles residual collinearity).
9. **Index of Concentration at the Extremes (ICE).** Equity-framed descriptor + narrative bridge to life expectancy (SAP §22 structural-racism framing).
   *Grounding:* Mitchell 2022 ICE↔life expectancy (PMID 35125487); Larrabee Sonderlund 2022 review (PMC8797220).

### B4. Small upgrades

10. **Gwet's AC1/AC2 alongside weighted kappa** for quartile agreement (kappa paradox under skewed HTN marginals). Keep Spearman primary.

### B5. Quality gate + review (finish Task 6)
- `ruff format` the 14 files; re-run `ruff check`, `mypy`.
- Full `pytest -q`; `marimo check --strict`; twice-run byte-identical checksum compare.
- Compound Engineering code review; resolve verified Critical/Important findings; rerun affected gates.
- Clean working tree; **do not push or open a PR unless explicitly requested.**

### B6. Manuscript/provenance obligations
- Claim-to-source verification (Paperclip `repo add`/`commit`) for every new method citation before it enters prose.
- Recheck JAMA Instructions within 14 days of submission; record any live vs snapshot status.
- Update STROBE / RECORD / STROBE-Equity / SAGER crosswalks for added analyses.

---

## Part C — Sequencing

1. **Decide B0 reframing** (SAP owners) — gates display emphasis.
2. **Implement B1 (Tier 1)** — TDD, all authorized/descriptive; carries the reframed thesis with no dependence on withheld models.
3. **Implement B2 (Tier 2)** — supplement spatial evidence.
4. **Run B5 quality gate + CE review.**
5. **Hold B3 (Tier 3)** for SAP-owner governance decisions (deviation records) — do not implement silently.
6. **B6 provenance** runs continuously; no citation enters prose unverified.

**Acceptance for "analysis complete (pre-authorization)":** B1+B2 implemented and tested; B5 all-green including two-run determinism and CE review; B0 decision recorded; `results_authorized` unchanged until human S7 authorization.
