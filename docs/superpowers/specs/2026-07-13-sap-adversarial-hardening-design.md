# ChicagoHealthMap SAP Adversarial Hardening Design

**Date:** 2026-07-13

**Status:** Approved for implementation planning

## Purpose

Harden the ChicagoHealthMap statistical analysis plan (SAP) workbook so an independent biostatistician can execute it without resolving contradictions, consulting undocumented analyst conventions, or choosing among unstated alternatives. Preserve the approved scientific direction, the reference workbook's compact visual pattern, and the S4-S7 authorization gates.

The JSON study specification remains the editable workbook source. The narrative SAP remains the complete scientific protocol. The regenerated Excel workbook must be a faithful, self-contained operational handoff rather than a lossy summary of that protocol.

## Scope

Modify only the SAP specification, narrative SAP where necessary for consistency, reusable workbook builder/validator when required for usability controls, regenerated ChicagoHealthMap workbook, generic skill/template if the general contract changes, and directly related design/plan records. Do not write analysis or pipeline code and do not pass any scientific gate.

## Scientific decisions

### Primary inference

The cardiometabolic joint estimand C1 and COPD estimand C2 form one confirmatory family. Both receive two-sided 97.5% Bonferroni-compatible confidence intervals. Nominal 95% intervals may appear only as explicitly labeled estimation context or for prespecified secondary estimates. Every Overview, Outputs, Estimands, Analysis Methods, Multiplicity, and Tables/Figures row must use this rule consistently.

### Spatial analysis

Unweighted OLS with HC3 uncertainty remains the permanent principal estimator for the area-distribution estimand. Residual Global Moran's I uses 9999 conditional random permutations with a recorded seed and weights checksum. If both `|Moran's I| ≥ 0.10` and permutation `P < .05`, the spatial-error model is a mandatory sensitivity using the identical outcome, exposures, and adjustment set.

Observed coefficient sign or magnitude must never switch the principal estimator. If the spatial-error contrast changes sign or differs by more than 20% in absolute magnitude from OLS, label the conclusion `model-sensitive`, display both estimates with equal prominence, and prohibit a single-model definitive interpretation. Rook and connected distance-band weights remain sensitivities.

### Outcome-blinded case-study selection

Replace the generic domain scorecard with the already-approved fixed score rules in the scientific-analysis plan:

- community-area usability: 15 points with 98%, 95%, and 90% anchors;
- tract usability/precision: 15 points with 90%, 80%, 70%, and 60% anchors;
- predictor temporal stability: 10 points using the fixed rank-correlation and discontinuity rules;
- phenotype interpretability: 15 points using validated/stable, documented sensitivity, ambiguity, and hard-fail anchors;
- comparator definition/period availability: 15 points using two-level, one-level, materially different, and unavailable anchors;
- evidence and novelty gap: 15 points using direct, supportive, crowded, and absent-rationale anchors;
- translation questionability: 10 points using concrete, general, and speculative-action anchors;
- distinct portfolio contribution: 5 points using distinct, partial, and duplicate anchors.

Retain all hard gates. Hypertension and diabetes must each pass and score at least 70; the joint bundle additionally requires at least 85% usable joint community-area-years and predictor-only VIF below 5. The highest-scoring nonduplicative second candidate with score at least 70 is selected, with COPD the expected respiratory candidate. Exact tie-breakers are phenotype score, community-area usability, comparator alignment, portfolio distinctiveness, then documented investigator adjudication. Outcome information is never used.

Two blinded scorers score independently. Disagreements are reconciled against the fixed anchors before outcome unblinding; original and reconciled scores remain in the audit record.

### Pooled EHR measure

Define the primary 2022-2024 exposure as:

`100 × sum(eligible annual condition numerators) / sum(matched eligible annual observed-adult denominators)`.

Label it the `denominator-weighted 2022-2024 annual EHR-diagnosed proportion among observed CAPriCORN adults`. It is an aggregation of annual observed-adult records and may count the same person in more than one year. It is not a unique-person three-year prevalence. Gate S4 must document within-year person deduplication, cross-system deduplication, and whether chronic diagnoses persist across years.

### Capture aggregation and ACS alignment

Define primary-period capture as:

`sum(eligible annual EHR adult denominators) / sum(matched annual ACS adult-population denominators)`.

The exact EHR-year-to-ACS-release mapping is frozen at S4 before outcome access. Each mapping row must include EHR year, ACS release, ACS 60-month period, universe, geography vintage, and rationale. No interpolation, nearest-year substitution, or future-release substitution occurs unless explicitly frozen in that table. Capture is a diagnostic/proposed adjustment variable, not a sampling probability.

### Life-expectancy uncertainty

The primary unweighted area model treats audited community-area life-expectancy estimates as observed outcomes. The outcome audit must record whether comparable standard errors or confidence intervals exist. If compatible uncertainty is available, report its distribution and run a precision-weighted sensitivity while stating that it changes the estimand. If unavailable or incompatible, record that fact and state the resulting measurement-precision limitation. Precision weighting never replaces the unweighted principal model.

### Missing data and weighting

Copy the narrative SAP's exact missingness thresholds, imputation restrictions, complete-case rules, and model-withholding criteria into Excel. Define population-weighted sensitivity weights as aligned ACS adult population, normalized only for numerical convenience. Imputation never creates suppressed EHR numerators, life-expectancy outcomes, or cross-vintage values.

## Workbook design

The first three tabs remain `Overview`, `Outputs`, and `Master Variables`. Add `Biostat Handoff` immediately after them. It contains:

- protocol/version/status and the narrative SAP path;
- required reading order;
- primary estimands and 97.5% CI rule;
- permanent OLS principal-model rule and spatial sensitivity gate;
- model-withholding rules;
- unresolved S4-S6 blockers with owner and required evidence;
- an explicit `DO NOT ANALYZE` state until S6 passes.

Expand scientific annex rows so critical thresholds and formulas are directly visible. Add a `Narrative SAP Section` or `Decision Reference` column wherever a rule is summarized. Preserve the Calibri 10, dark-blue header, alternating-row, section-band, and category-color reference pattern.

Add these usability controls without turning the workbook into a dashboard:

- filters on operational table headers;
- frozen header regions;
- controlled status values with list data validation on editable status cells;
- accessible status fills that are supplemental to, not substitutes for, status text;
- explicit units, formulas, and interpretation labels;
- no decorative charts.

## Reproducible data flow

1. Edit the narrative SAP and `docs/analysis/sap_workbook_spec.json`.
2. Run semantic contradiction tests against the JSON and narrative.
3. Regenerate the workbook with the repository-owned SAP builder.
4. Validate required sheets, columns, formulas, status fields, and cross-artifact scientific rules.
5. Render every sheet and visually inspect it at readable scale.
6. Run the same adversarial audit against the regenerated workbook.
7. Commit source and generated artifacts together only after all checks pass.

No hand edits to the `.xlsx` are permitted.

## Acceptance tests

The repair is complete only when all of the following pass:

1. No workbook primary-result row requests 95% CIs without explicitly labeling them nominal estimation context; all confirmatory rows request 97.5% CIs.
2. No narrative or workbook rule can replace OLS as principal based on observed coefficient sign, size, significance, or visual appeal.
3. The workbook contains every fixed selection-score anchor, hard gate, bundle rule, and tie-breaker.
4. The pooled EHR measure and primary-period capture formulas and interpretations are explicit.
5. Spatial thresholds, missing-data thresholds, model-withholding rules, weighting definition, and life-expectancy uncertainty rule are visible in Excel.
6. Every summarized critical rule points to its narrative SAP section or decision reference.
7. The first three reference-pattern sheets remain unchanged in order; `Biostat Handoff` is fourth.
8. Structural validation and spreadsheet error scans pass.
9. Every sheet renders without clipped critical text, unreadable status colors, or inflated used ranges.
10. A final adversarial review finds no high- or medium-severity ambiguity that would allow two competent biostatisticians to implement materially different primary analyses.

## Non-goals

- Passing S4, S5, S6, or S7.
- Filling unknown EHR phenotype, suppression, reliability, or outcome-audit facts.
- Running outcome models or inspecting outcome results.
- Claiming population prevalence, causality, implementation benefit, or generalizability to all cities.
