# Statistical Review Remediation Plan

## Goal

Resolve every actionable statistical and reporting concern identified in the statistician and adversarial reviews while preserving the paper's primary question: whether tract-level Chicago Health Map estimates add information beyond community-area labels. The deliverable remains a statistician-review draft until independent S7 review and study-owner governance confirmations are complete.

## Decisions

- Keep hypertension and COPD as the two primary use cases. Do not add a mortality-condition expansion in this remediation because it would introduce a new scientific aim, new multiplicity, and new source-validation requirements.
- Keep the leave-one-tract-out community-area comparator and the 4 prespecified information-loss estimands as the primary analysis.
- Keep unshrunk tract estimates primary. Retain empirical-Bayes shrinkage, direct source geographies, suppression scenarios, and C2 life-expectancy models as sensitivity or supplementary analyses.
- Keep `results_authorized=false`. Passing computational checks does not complete independent S7 review or authorize manuscript import.
- Do not infer or invent IRB determinations, participating-system counts, source-owner definitions, or data-sharing permissions. Replace vague placeholders with an explicit sign-off register and submission blockers.

## Requirements and implementation

### R1. C2 capture sensitivity

Add a C2 model that omits `capture_rate_mean_2022_2024` while retaining age 65 years or older, female sex, and poverty covariates. Use the same complete community-area population, frozen COPD IQR scaling, HC3 covariance, residual-degrees-of-freedom t critical value, and 95% interval as the other C2 sensitivity models. Display it beside the capture-adjusted and population-weighted variants and interpret differences as sensitivity, not robustness.

**Files:** `src/chicagohealthmap/analysis/robustness.py`, notebook exports, R Markdown displays, tests.

**Acceptance:** the governed robustness artifact contains a `no_capture_adjustment` C2 row with an explicit adjustment set, estimator, eligible n, estimate, and 95% interval. An independent statsmodels fit agrees within numerical tolerance.

### R2. Age-stratum reconciliation

Replace statements that age-stratum fields are absent. Produce an aggregate reconciliation artifact that records field availability, completeness, additive consistency with total numerators and denominators, and zero-cell frequency by condition. The manuscript must state that age fields exist but their semantics and additive integrity do not support a defensible standardized estimand without source-owner confirmation and a compatible standard population.

**Files:** analysis helper, master notebook, companion R Markdown, manuscript, data dictionary and decision log, tests.

**Acceptance:** the rendered review package distinguishes field availability from analytic usability and records a fail-closed `not_run_age_standardization_unreconciled` status.

### R3. Included-versus-excluded tract audit

Add an aggregate selection audit for hypertension and COPD comparing tracts retained after 3-year completeness and dominant-area overlap with those excluded at each stage. Report counts and aggregate denominator, crude proportion, suppression, and reliability summaries without exporting tract identifiers or patient-level rows.

**Files:** `src/chicagohealthmap/analysis/case_studies.py`, master notebook, companion R Markdown, manuscript supplement, tests.

**Acceptance:** the audit reconstructs the frozen cohort flow, includes no geography identifiers, and highlights COPD selection without implying representativeness.

### R4. Noise-reference interpretation

Report the observed-minus-noise-median value already produced by the 1000-replicate binomial simulation for each primary estimand and condition. Add the explicit limitation that the null assumes independent binomial variation and does not model repeated adults across years, coding heterogeneity, overdispersion, care selection, geocoding error, or spatial dependence.

**Files:** master notebook, companion R Markdown, main manuscript, claim-evidence bindings, tests.

**Acceptance:** every reported excess-over-null number is bound to the governed noise artifact and appears with the simulation definition and limitation.

### R5. Governance sign-off register

Replace bracketed ethics and data-sharing placeholders with review-draft language that identifies the exact unresolved owner decisions: IRB determination and protocol language, waiver or consent language, participating-system count, annual denominator and MRAIA deduplication definition, zero/suppression semantics, reliability-tier mapping, and repository/data-sharing permissions.

**Files:** manuscript, companion R Markdown, S7 review record, submission checklist, decision log.

**Acceptance:** no manuscript placeholder falsely resembles final text. The package states which facts are known, which require confirmation, who must confirm them, and that submission is blocked until confirmation.

### R6. Supplement display contracts

Verify that ZCTA, noncrossing-boundary, HCS correlation interval, reliability-stratified, suppression-scenario, and shrinkage analyses are present in generated artifacts and rendered supplementary displays. Remove any narrative claim whose analysis is absent.

**Files:** notebook contract tests, R Markdown rendering tests, manuscript claim audit.

**Acceptance:** automated tests fail when a named sensitivity or its interval columns disappear.

### R7. Scope and authorization protections

Preserve the combined-diabetes gate, noncausal language, crude EHR-diagnosed proportion label, and `results_authorized=false`. Record mortality supplementation and suppression tipping-point expansion as deferred analyses rather than silently adding them.

**Acceptance:** public-release and authorization tests pass and no unauthorized manuscript/coauthor export contains governed findings.

## Verification

1. Run focused unit and integration tests for robustness, cohort flow, notebook contracts, manuscript claims, and authorization leakage.
2. Run Ruff, MyPy, strict Marimo validation, and the full pytest suite.
3. Execute the master notebook twice in fresh output directories and compare governed checksums.
4. Render the R Markdown review package twice and compare governed outputs.
5. Inspect the HTML for equations, tables, figure labels, navigation, warnings, line wrapping, and the revised limitations and sign-off register.
6. Run `git diff --check` and inspect the complete branch diff.

## Completion boundary

Code, artifacts, and prose can be review-complete when all checks pass. The paper cannot be called submission-ready until the study owner supplies the pending governance language and the independent statistician completes S7 review.
