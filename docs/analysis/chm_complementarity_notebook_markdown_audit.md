# CHM Complementarity Notebook Markdown and Display Audit

Date: 2026-07-15

Notebook: `notebooks/00_master_chicago_healthmap_pipeline.py`

## Scope

This audit reviews the notebook markdown, tables, figures, and manuscript handoff for
statistical rigor, interpretive clarity, and JAMA-style scientific prose. The review uses
the JAMA Health Forum skill and the ChicagoHealthMap inference contract. The official journal
instructions were opened directly on July 15, 2026. Tavily separately returned
`monthly_cap_reached_bonus_eligible`; the tool failure remains recorded but did not block direct
official-page verification.

## Findings

No blocker was found in the notebook markdown or display logic after this pass.

Submission readiness still cannot be claimed because human S7 authorization and other
human-owned submission fields remain open. The official instructions must also be rechecked
within 30 days of submission.

## Changes Made

- Added an evidence-ladder opening that explains the sequence: data cleaning, quality
  checks, analytic data set, descriptive statistics, case study 1, case study 2, and
  displays.
- Revised scientific markdown into compressed, concrete prose modeled on JAMA Methods and
  Results sections.
- Labeled co-author interpretation blocks separately so plain-language teaching does not
  blur the manuscript-style prose.
- Added statistical-reading markdown for the ecological regression, including the outcome,
  CHM exposure estimand, and prespecified adjustment covariates.
- Added model sentences for C1 and C2 that define alpha, beta, gamma, the adjustment vector,
  and the frozen-IQR contrast scale.
- Expanded Table 2 notes to state CI levels, adjustment variables, noncausal interpretation,
  and the rule that P values are not reported alone.
- Added a JSON manuscript handoff containing governed result sentences, figure legends,
  table notes, P-value text, authorization status, and interpretation boundaries.
- Corrected the Figure 1 markdown so it describes the actual synchronized map panels.

## Statistical Rigor Check

The markdown preserves the approved senior-biostatistical decisions: equal-weighted
community-area OLS with HC3 covariance, prespecified adjustment for age 65 years or older,
female sex, poverty, and EHR capture, primary 97.5% CIs for C1/C2, 95% CIs for separate
hypertension and diabetes component contrasts, and supportive residual Moran diagnostics.
The text does not convert EHR-diagnosed proportions among observed CAPriCORN adults into
population prevalence or causal claims.

## Verification

- `uv run pytest tests/unit/analysis/test_reporting.py tests/unit/analysis/test_case_studies_notebook_contract.py -q`
- `uv run ruff check src/chicagohealthmap/analysis/reporting.py notebooks/02_chicago_case_studies.py tests/unit/analysis/test_reporting.py tests/unit/analysis/test_case_studies_notebook_contract.py tests/integration/test_case_studies_notebook.py`
- `uvx marimo check notebooks/02_chicago_case_studies.py`
- `uv run pytest tests/integration/test_case_studies_notebook.py -q`
