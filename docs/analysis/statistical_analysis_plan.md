# ChicagoHealthMap Statistical Analysis Plan

**Protocol identifier:** CHM-SAP-001

**Version:** 0.2-implementation/freeze-candidate

**Date:** 2026-07-13

**Status:** Implementation/freeze-candidate addendum recorded; independent S7 review and human authorization remain open

**Target journal:** JAMA Health Forum, Original Investigation

**Study type:** Cross-sectional, repeated-period ecological analysis and informatics resource evaluation

**Primary population:** Adults aged 18 years or older represented in CAPriCORN contributing systems

**Primary geography:** City of Chicago census tracts, compared with direct community-area labels

**Primary period:** 2022–2024

> This document prespecifies the analysis intended after the EHR semantic audit and outcome-blinded case-study selection. It does not authorize outcome modeling. Confirmatory analyses remain blocked until Gates S4, S5, and S6 pass in sequence and this SAP is signed and frozen.

### Implementation/freeze-candidate addendum (2026-07-15)

This dated addendum preserves the original SAP intent. The initial implementation commit was
`5a92a04`; the work is maintained on branch `codex/chm-paper-master-redesign`, and the final verified commit
is recorded in each deterministic master-notebook run manifest. The study remains an ecological,
cross-sectional/repeated-period
analysis and resource evaluation. Its central claim is complementarity of direct CHM EHR-diagnosed
tract patterns with secondary public comparators and community-area life-expectancy summaries.
This is not a claim of predictive superiority, validation, prevalence, causality, or service need.

The implementation records a proposed primary-aim amendment. This implementation-status addendum
is not a signed deviation record and does not authorize manuscript import:

- The full-design VIF gate is now explicit. C1 is `withheld_vif_above_5`; any fitted C1 estimate
  is `audit_only_exploratory` and cannot produce manuscript-facing prose. C2 is
  `freeze_candidate_primary_model_unsecured` and remains unauthorized. Rationale: the gate
  prevents unstable collinear adjusted inference while preserving a transparent audit path.
- Adjusted candidate fits and diagnostics may have executed for audit/diagnostic purposes. The
  run manifest records this execution separately from authorization; `results_authorized=false`
  remains binding, and no Results/Abstract/Key Points/Discussion text is authorized.
- Robustness variants (HC3 sensitivity, weighted and leave-one-out checks, disruption and annual
  checks, alternative rook/distance topology, spatial diagnostics, and bootstrap) are governed
  audit artifacts. Rationale: quantify direction, fragility, and spatial/temporal dependence
  without changing the primary estimand or authorizing a model.
- The proposed primary question is whether tract-level EHR-diagnosed proportions add geographic
  information beyond direct community-area labels. Exact quartile agreement, disagreement,
  highest-quartile movement, and within-community variance are the principal descriptive
  estimands. ZCTA labels form a sensitivity analysis. CHM-PLACES agreement and life-expectancy
  models are secondary or supplementary. A signed amendment must specify the period, phenotype,
  linkage, pooling, and display rules before this hierarchy can govern manuscript claims.
- New outputs are named in the evidence and display ledgers, bound to source snapshots, units,
  denominators, periods, uncertainty, code, and commit. Generated result directories remain local
  and untracked.
- Three transportability-strengthening modules are now explicit. A checksum-verified 2023-2024
  Healthy Chicago Survey community-area hypertension triangulation may execute for independent
  review. Combined diabetes remains blocked by its EHR semantic gate. A frozen 2025 CHM extract
  is reserved as an out-of-time holdout and must not enter the 2022-2024 development pool. An
  external metropolitan EHR analysis must reproduce the same direct tract-versus-direct-coarser-
  area estimand; a tract-only EHR-versus-PLACES comparison is contextual replication only.
- Human S7 authorization remains open. The official JAMA Health Forum instructions were checked
  directly on July 15, 2026; Tavily's separate quota failure remains recorded. This SAP makes no
  submission-readiness claim.

The original pending S4/S5/S6 language below is retained as historical intent. This addendum is
the current implementation/freeze-candidate status and requires a signed deviation record before
any future authorization change.

## 1. Governance and document hierarchy

The approved scientific-pipeline design and the final scientific-analysis planning document govern this SAP. If documents conflict, the hierarchy is: signed post-audit SAP; approved design; final scientific plan; source registry; implementation configuration. A post-freeze change requires a deviation record and cannot be justified by statistical significance, effect direction, visual appeal, or manuscript convenience.

This draft deliberately leaves case-study-dependent fields in the state **Pending Gate S4** or **Pending Gate S5** rather than filling them from outcome data. Pending fields are blockers, not analyst discretion.

### 1.1 Freeze sequence

| Gate | Required evidence | Authorization after pass |
|---|---|---|
| S4 EHR semantics | Signed numerator, denominator, suppression, phenotype, capture, and reliability audit | Outcome-blinded candidate scoring may begin |
| S5 selection | Signed scorecard produced without life-expectancy or mortality data | Outcome data may be linked for SAP review only |
| S6 SAP | Signed SAP with final variables, estimands, models, weights, multiplicity, and sensitivities | Confirmatory model execution may begin |
| S7 validation | Reproducible outputs, diagnostics, independent numerical review | Results may be frozen for manuscript use |

### 1.2 Roles and blinding

- The data-quality team may inspect EHR and public comparator availability but not life-expectancy or cause-specific mortality during candidate scoring.
- The scorecard approver signs the candidate ranking and substitution rule before outcome linkage.
- The analysis lead signs this SAP only after S4 and S5 evidence is attached.
- The outcome-unblinding timestamp, analyst, commit, and source snapshot identifiers are recorded in the study manifest.
- A person not responsible for the primary model code independently checks at least one primary contrast, its covariance-based confidence interval, and the Moran diagnostic.

## 2. Research objectives

### 2.1 Primary geographic-resolution objective

Determine whether direct census-tract EHR-diagnosed proportions provide geographic information
beyond the labels obtained from direct Chicago community-area summaries. Estimate absolute
percentile-rank gap, exact quartile agreement, quartile disagreement, movement into or out of the highest quartile, and the share of
observed tract variation that remains within community areas. Repeat the classification comparison
with direct ZCTA summaries as a prespecified sensitivity analysis.

### 2.2 Resource objective

Characterize the completeness, suppression, reliability, temporal stability, capture, and demographic representativeness of ChicagoHealthMap/CAPriCORN adult EHR-diagnosed proportions at community-area and census-tract scales.

### 2.3 Supplementary case-study objective 1: cardiometabolic burden

Estimate the ecological association of community-area hypertension and diabetes diagnosed proportions—jointly and separately—with aligned community-area life expectancy.

### 2.4 Supplementary case-study objective 2: respiratory burden

Estimate the ecological association of community-area COPD diagnosed proportion with aligned community-area life expectancy.

### 2.5 Secondary triangulation objective

Quantify concordance and discordance between EHR-diagnosed proportions and independent public measures from CDC PLACES or Chicago Health Atlas without treating either source as a gold standard or as interchangeable population prevalence.

For the Healthy Chicago Survey hypertension analysis, compare pooled 2022-2024 direct CHM
community-area proportions with unstratified 2023-2024 HCS community-area estimates. Report
Spearman rank correlation, median absolute percentile-rank gap, and exact within-source quartile
agreement. Display HCS standard errors, but do not construct a joint-source interval because
compatible CHM uncertainty is unavailable. HCS diabetes is availability-only until the CHM
combined-diabetes semantic gate passes.

### 2.6 Translation objective

Demonstrate how reliability-qualified patterns and source discordance can formulate questions for FQHCs and community-based organizations. The study does not evaluate implementation, care delivery, resource allocation, or health outcomes.

### 2.7 Transportability objective

Assess temporal transportability in a frozen 2025 CHM holdout after a source-comparability gate,
and assess geographic transportability in a second metropolitan multi-system EHR network after an
estimand-compatibility gate. Neither analysis is complete until its aggregate source data are
present, checksum-bound, and approved for the specified use.

## 3. Study design, setting, and units

The study is a repeated-period, small-area ecological analysis of adults aged 18 years or older in Chicago. The primary analysis unit is the census tract. Direct tract estimates are compared with linked labels from direct community-area exports. Tract values are not aggregated to recreate community-area exposures when direct exports exist. The direct ZCTA comparison is a sensitivity analysis.

Community-area life-expectancy models use the community area as the unit and remain supplementary. No tract-level life-expectancy analysis is permitted because no frozen authoritative tract-level life-expectancy outcome is available.

All quantities are area-level. No coefficient is interpreted as an individual-level association, causal effect, preventable life-expectancy loss, or intervention benefit.

## 4. Data sources and frozen releases

| Source | Role | Frozen scope or release | Critical interpretation |
|---|---|---|---|
| CAPriCORN/ChicagoHealthMap | EHR numerators, denominators, diagnosed proportions, capture and demographic fields | First-party snapshot identified in study manifest | Diagnosed proportions among observed adults, not population prevalence |
| Chicago Health Atlas | Annual community-area life expectancy, cause-specific mortality, and COPD context | All advertised periods for registered topics through 2024 | Retain producer, topic, period, unit, adjustment, and suppression metadata |
| Healthy Chicago Survey through Chicago Health Atlas | Independent community-area hypertension triangulation; diabetes availability audit only | Frozen HCSHYTP and HCSDIAP rolling 2023-2024 files and topic metadata in the 2026-07-13 snapshot | Self-reported clinician diagnosis among noninstitutionalized Chicago adults; retain source standard errors and `Organization` access metadata; not a validation standard |
| CDC PLACES | Tract hypertension, diabetes, and COPD comparators | 2025 tract GIS-friendly release, Illinois subset, catalog yjkw-uj5s | Model-based small-area estimates; release year is not observation year |
| ACS 5-year | Population and prespecified area covariates | 2019, 2022, and 2024 releases | Retain table, variable, universe, estimate, margin of error, and 60-month period |
| TIGER/Line | Boundary and tract-vintage control | 2019, 2020, 2023, and 2024 tracts | Never join incompatible tract vintages silently |
| CDC/ATSDR SVI | Supportive vulnerability context | 2022 Illinois corrected file | Release-specific ranks; not a stable longitudinal scale |
| HRSA | Planning-demonstration site layer | Daily site file frozen 2026-07-13 | Sites are not capacity, catchment, access, quality, or endorsement |
| City of Chicago | Community-area boundaries | Official 77-area layer, igwz-8jzy | Primary community-area geometry |
| Metopio | Discovery/access metadata only | Frozen unauthenticated public catalog | Original producer remains authoritative; authenticated catalog not run |

The frozen public Metopio catalog contains 19 topics, 8 categories, 91 datasets, 97 sources, 1551 stratifications, 142 stratification groupings, 989 periods, 44 benchmarks, 178 updates, 1 layer, and 1 geography. It contains no visible public hypertension, diabetes, or COPD topic. `METOPIO_API_TOKEN` was absent during this SAP audit, so authenticated discovery is recorded as not run. A later authenticated query may occur only through the approved bounded snapshot client and cannot replace an authoritative source without a logged source decision.

## 5. Study population and analytic populations

### 5.1 Base eligibility

An EHR area-period record is eligible when it represents adults aged 18 years or older, uses the audited overall-adult denominator, has a valid Chicago geography identifier, has an interpretable numerator state, and passes schema and proportion-reconciliation checks.

### 5.2 Analytic populations

1. **Resource population:** every eligible adult geography-year-condition record from 2019–2024.
2. **Primary tract-to-community population:** Chicago tracts on the approved common vintage with eligible EHR numerators and denominators in each year from 2022 through 2024 and a dominant community-area allocation of at least 0.99.
3. **Secondary comparator population:** primary eligible tracts with an aligned PLACES measure for the same condition construct and documented comparator period.
4. **Supplementary community-area population:** all 77 community areas with eligible 2022–2024 exposure data and aligned life expectancy.
5. **Temporal population:** areas with eligible observations in 2019 and at least one of 2020–2024. Paired summaries state the exact denominator.
6. **Planning-demonstration population:** only areas whose displayed EHR measure passes the frozen reliability rule and whose public site data are disclosure-safe.
7. **HCS triangulation population:** all direct Chicago community areas with complete pooled
   2022-2024 CHM hypertension numerators and denominators and a 2023-2024 unstratified HCS
   hypertension estimate and standard error. The frozen files provide 77 pairwise-complete areas.
8. **2025 temporal holdout population:** direct 2025 CHM tracts and direct community areas that
   pass the frozen primary eligibility and linkage rules after the source-comparability gate. This
   population is unavailable in the current frozen extract.
9. **External replication population:** aggregate areas from a second multi-system EHR network
   with direct tract and direct named coarser-area estimates for the same condition and period.
   If direct coarser-area outputs are unavailable, the dataset cannot replicate the primary aim.

The final phenotype-specific eligibility counts are **Pending Gate S4**. Flow counts must show reasons for exclusion separately: invalid geography, outside adult universe, suppressed/ambiguous numerator, missing denominator, failed proportion reconciliation, failed reliability, missing aligned outcome, or crosswalk failure.

## 6. EHR measure semantics

### 6.1 Numerator

The numerator is the exported number of observed adults meeting the condition-specific diagnosis definition for a geography and year. Exact code lists, lookback windows, encounter requirements, deduplication rules, and whether problem-list, billing, laboratory, medication, or vital-sign evidence contributes are **Pending Gate S4** and must be reproduced from first-party documentation or data-owner confirmation.

### 6.2 Denominator

The denominator is the exported adult denominator for the same geography-year, after person-level deduplication across contributing systems if the source performs it. The audit must test whether denominators are shared across conditions within geography-year, whether they reflect at least one encounter or another observation rule, and whether a person may appear in more than one contributing system.

### 6.3 Diagnosed proportion

The primary exposure is `100 × numerator / denominator`, expressed in percentage points. The published label is “EHR-diagnosed proportion among observed CAPriCORN adults.” The terms population prevalence, community prevalence, disease prevalence, incidence, risk, and population rate are prohibited unless a separate validated estimand supports them.

### 6.4 Suppression and zero

Until the data owner resolves the export convention, zero-valued disease cells that may encode suppression are classified `zero_or_suppressed`. They are not treated as true zero, not imputed, and not included in analyses requiring a known count. Missing, suppressed, unreliable, true zero, structurally not applicable, and unavailable are distinct states in every analytic table.

### 6.5 Capture and representativeness

For each geography-year, compute the EHR adult denominator divided by the aligned ACS adult population. Ratios are capture indicators, not sampling probabilities; values above 1 may reflect period definitions, duplication, movers, boundary mismatch, or denominator semantics and must not be truncated silently. Compare age, sex, and race/ethnicity distributions with ACS where definitions allow. Race and ethnicity are social and political classifications used to describe differential representation and exposure to structural racism, not biological attributes.

Demographic poststratification, coverage weighting, or multilevel regression and poststratification is not primary. Such methods may be supportive only if cell definitions and denominators pass S4, the target population margins are compatible, and the weighting model is frozen before outcomes are inspected. Weighting does not guarantee removal of nonignorable neighborhood-level selection bias.

## 7. Time alignment

The primary EHR exposure is the **denominator-weighted 2022–2024 annual EHR-diagnosed proportion among observed CAPriCORN adults**:

`100 × sum(eligible annual numerators) / sum(corresponding annual denominators)`.

It is not the unweighted mean of annual percentages. Annual 2022, 2023, and 2024 estimates are descriptive and support temporal robustness.

The pooled measure aggregates annual observed-adult records. An adult observed in more than one year may contribute to more than one annual numerator and denominator; therefore, this measure is not a unique-person 3-year prevalence. Gate S4 must document within-year person deduplication, cross-system deduplication, and whether a chronic diagnosis persists into later annual numerators.

Primary-period capture is:

`sum(eligible annual EHR adult denominators) / sum(matched annual ACS adult-population denominators)`.

Before outcome access, Gate S4 freezes an EHR-year-to-ACS mapping table containing EHR year, ACS release, ACS 60-month period, adult universe, geography vintage, and rationale. No interpolation, nearest-year substitution, or future-release substitution occurs unless that exact rule is frozen in the table. Capture remains a diagnostic and proposed adjustment variable, not a sampling probability.

The primary life-expectancy outcome is the arithmetic mean of annual community-area life expectancy at birth for 2022, 2023, and 2024, conditional on the outcome audit confirming comparable annual definitions and units. If any year uses a materially different method or is unavailable for a community area, the prespecified fallback is the most recent common annual period with at least 70 eligible community areas; use of the fallback requires a pre-model deviation entry.

The primary unweighted area model treats audited community-area life-expectancy estimates as observed outcomes. The outcome audit records whether comparable standard errors or confidence intervals are available. When compatible uncertainty is available, report its distribution and run a precision-weighted sensitivity, explicitly stating that weighting changes the estimand. When uncertainty is unavailable or incompatible, record that fact and the resulting measurement-precision limitation. Precision weighting never replaces the unweighted principal model.

2019 is the pre-pandemic baseline. Years 2020–2021 are disruption years and are not pooled into the primary exposure. They are described separately and used in disruption sensitivity analyses.

## 8. Geography and vintage harmonization

Community-area models use the official direct 77-area boundary and direct community-area EHR observations. Tracts must carry the source vintage. The PLACES 2025 tract release is aligned to its documented 2023 tract boundary vintage. EHR tract identifiers are compared with 2019, 2020, 2023, and 2024 TIGER inventories before any join.

If an EHR tract cannot be matched one-to-one to the primary tract vintage, the record is excluded from primary tract concordance. A supportive crosswalk may allocate counts only when an official relationship file exists and both numerator and denominator are allocated using the same population-based weights. Percentages are never area-weighted directly. Crosswalked estimates are labeled and cannot be mixed with direct estimates without an indicator.

Tract-to-community-area relationships are many-to-many. Tract results are not assigned to a community area by centroid for modeling. If a descriptive crosswalk is necessary, report the allocation method, split tracts, allocation shares, and sensitivity to excluding split tracts.

## 9. Outcomes, exposures, and covariates

### 9.1 Primary outcome

Community-area life expectancy at birth, in years, aligned as specified in Section 7. Values must retain annual topic identifier, estimate type, period, geography, suppression state, and source lineage.

### 9.2 Primary exposures

- Cardiometabolic: pooled hypertension and diabetes EHR-diagnosed proportions, entered together.
- Respiratory: pooled COPD EHR-diagnosed proportion.

Final condition names, diagnosis definitions, and available years are **Pending Gate S4**. Confirmation of the case studies is **Pending Gate S5**.

### 9.3 Adjustment set

The smallest sufficient adjustment set is frozen at S6 from variables available before outcome inspection. The proposed set is: percentage aged 65 years or older, percentage female if sex composition is available and compatible, percentage below the federal poverty level, and EHR capture ratio. Median household income is not entered with poverty in the same primary model. Racial composition is not included as a routine confounder; if analyzed, it is framed as a measure of racialized residential structure and reported in an equity-focused supportive model.

To preserve degrees of freedom with 77 areas, a primary model may contain no more than 6 nonintercept parameters. Correlation greater than 0.80, variance inflation factor greater than 5, rank deficiency, or unstable standard errors triggers covariate consolidation before unblinding or model withholding after unblinding—not significance-based deletion.

## 10. Estimands

### 10.1 Cardiometabolic joint estimand C1

Among eligible Chicago community areas, the adjusted mean difference in aligned 2022–2024 life expectancy, in years, associated with simultaneous one-IQR increases in both pooled hypertension and pooled diabetes diagnosed proportions, conditional on the frozen covariates.

If fitted coefficients are `βH` and `βD`, and frozen IQRs are `IH` and `ID`, the contrast is `βH×IH + βD×ID`. Its variance is `IH²Var(βH) + ID²Var(βD) + 2×IH×ID×Cov(βH,βD)`. The confidence interval must use this full covariance expression.

### 10.2 Respiratory estimand C2

Among eligible Chicago community areas, the adjusted mean difference in aligned 2022–2024 life expectancy, in years, associated with a one-IQR increase in pooled COPD diagnosed proportion, conditional on the frozen covariates.

### 10.3 Secondary cardiometabolic estimands

- One-IQR hypertension contrast conditional on diabetes and covariates.
- One-IQR diabetes contrast conditional on hypertension and covariates.
- Per-10-percentage-point contrasts when a 10-point change lies within the observed central support and does not imply extrapolation.

### 10.4 Interpretation

Estimands are ecological adjusted associations. Permitted wording is “a higher area diagnosed proportion was associated with a difference in area life expectancy.” Prohibited wording includes caused, drove, explained, attributable, preventable years, impact, effect, and would improve.

## 11. Descriptive and resource analyses

Report the number of source files, records, years, conditions, geographies, contributing systems when available, eligible adults, and unique geography-year-condition records. For each condition and geography scale, report median and IQR denominator, diagnosed proportion, capture ratio, suppression percentage, missing percentage, and reliability-qualified percentage.

Maps use the same frozen classification for comparable panels. Suppressed, missing, and unreliable observations have distinct visual encodings and are not assigned to the lowest disease category. Tract hotspot or cluster maps are exploratory and are not used to select case studies.

## 12. Outcome-blinded case-study selection

Selection uses a 100-point scorecard completed independently by two blinded scorers before life-expectancy or mortality data are accessible. Original scores, evidence references, disagreements, and reconciled scores are retained. Reconciliation applies the fixed anchors below and occurs before outcome unblinding.

| Domain | Points | Fixed scoring rule |
|---|---:|---|
| Community-area usability | 15 | 15 for at least 98%; 12 for 95%-97.9%; 8 for 90%-94.9%; hard fail below 90% |
| Tract usability/precision | 15 | 15 for at least 90%; 12 for 80%-89.9%; 8 for 70%-79.9%; 4 for 60%-69.9%; hard fail below 60% unless community-area-only is predeclared |
| Predictor temporal stability | 10 | 10 when median area rank correlation across 2022-2024 is at least 0.80 with no system discontinuity; 7 for 0.60-0.79; 3 below 0.60; 0 with unexplained discontinuity |
| Phenotype interpretability | 15 | 15 for a validated stable definition and exclusions; 10 for a stable diagnosis-only definition with documented sensitivity; 5 for material coding ambiguity; hard fail if unresolved |
| Comparator definition/period availability | 15 | 15 for an aligned crude adult comparator at tract and community-area levels; 10 for one level; 5 for a materially different but interpretable comparator; 0 for none |
| Evidence and novelty gap | 15 | 15 for direct rationale plus a search-bounded gap; 10 for supportive rationale/gap; 5 for crowded literature with limited distinct contribution; 0 for no rationale |
| Translation questionability | 10 | 10 for concrete FQHC/CBO questions supported by measure semantics; 5 for general public-health relevance; 0 when only speculative action claims are available |
| Distinct portfolio contribution | 5 | 5 for a different phenotype, ascertainment, or reliability lesson; 2 for partial overlap; 0 for duplication |

Hard gates remain: resolved numerator, denominator, phenotype, and suppression; at least 90% of 231 community-area-years usable and no year below 85%; tract displayability at 60% or higher unless community-area-only is predeclared; an independent comparator or aligned supportive mortality construct; a defensible literature rationale; distinct contribution; and disclosure feasibility. Hypertension and diabetes must each pass and score at least 70. The joint bundle additionally requires at least 85% usable joint community-area-years and predictor-only VIF below 5. Promote the bundle if it passes, then select the highest-scoring nonduplicative second candidate scoring at least 70; COPD remains the expected respiratory candidate.

Exact tie-breakers are, in order: phenotype score, community-area usability, comparator-definition alignment, portfolio distinctiveness, then investigator adjudication with a written rationale. No outcome statistic, map, correlation, regression, mortality measure, or outcome-linked residual may enter scoring or adjudication.

## 13. Primary statistical models

### 13.1 Baseline estimator

Fit unweighted ordinary least squares with one row per community area. Report HC3 heteroskedasticity-robust standard errors and confidence intervals. Unweighted analysis is primary because the estimand describes the distribution of Chicago community areas, not the average individual. Population-weighted analysis is supportive and answers a different question.

### 13.2 Model forms

Cardiometabolic:

`LE = α + βH(H/IQRH) + βD(D/IQRD) + γ'X + ε`.

Respiratory:

`LE = α + βC(COPD/IQRC) + γ'X + ε`.

Exposures are scaled using IQRs computed once in the primary complete-case analytic population and then held fixed for all directly comparable sensitivities. Covariates are centered and scaled as recorded in the frozen data dictionary.

### 13.3 Functional form

Primary exposures are linear. Before outcomes are inspected, exposure distributions and scatterplots against covariates may be examined. After unblinding, restricted cubic splines are exploratory only and require at least 10 complete areas per parameter. A nonlinear result cannot replace the primary linear estimand.

## 14. Spatial diagnostics and escalation

Construct row-standardized queen-contiguity weights from the official community-area geometry. Islands or invalid polygons are documented and resolved before modeling; no silent nearest-neighbor connection is allowed. Rook contiguity and distance-band weights that connect every area are sensitivities.

For each primary OLS model, calculate residual Global Moran’s I with 9999 conditional random permutations. Record the observed statistic, expected value, permutation P value, seed, number of permutations, and weights checksum.

When both `|Moran's I| ≥ 0.10` and permutation `P < .05`, fit the prespecified spatial-error model as a mandatory sensitivity. A spatial-lag outcome model is not primary because it changes the estimand and can encode outcome spillover without a defensible causal mechanism.

OLS remains the principal estimator. The spatial-error model uses the same outcome, exposures, and covariates and never replaces OLS because of observed coefficient sign, magnitude, statistical significance, or visual appeal. If its primary contrast changes sign or differs in absolute magnitude by more than 20% from OLS, label the conclusion `model-sensitive`, display both estimates with equal prominence, and prohibit a definitive single-model interpretation.

Software implementation must use documented PySAL components or an equivalently validated implementation. The exact package versions, weight transformation, optimizer, convergence criterion, and log-likelihood diagnostics are frozen at S6.

## 15. Influence, fit, and model withholding

Flag an area when Cook’s distance exceeds `4/n`, leverage exceeds `2p/n`, or the absolute externally studentized residual exceeds 3. Areas remain in the primary model. Report leave-one-area-out ranges and repeat the model excluding all flagged areas as sensitivity analyses.

A primary association is labeled fragile if any single-area deletion changes its sign or its absolute magnitude by more than 30%. Statistical significance is not a robustness criterion.

Withhold model interpretation if fewer than 70 community areas are complete, the design matrix is rank deficient, a required exposure has fewer than 10 distinct nonsuppressed values, convergence fails, covariance cannot be estimated, or diagnostics show a result dominated by an unresolved data error. Report the withholding reason and descriptive results only.

## 16. Concordance and discordance analyses

For each compatible EHR/public pair at the same geography:

- report Spearman rank correlation as primary concordance;
- report Pearson correlation as supportive;
- report median signed and absolute percentage-point differences only when units and universes are sufficiently compatible;
- report cross-tabulated quartiles and weighted kappa as supportive;
- display Bland–Altman-style differences only when the measures are on a comparable scale, with a warning that neither is a gold standard.

Discordance categories are frozen as:

1. concordant high: both measures at or above their 75th percentiles;
2. concordant low: both at or below their 25th percentiles;
3. EHR-high/public-not-high: EHR at or above the 75th percentile and public below the 50th;
4. public-high/EHR-not-high: public at or above the 75th percentile and EHR below the 50th;
5. intermediate: all other combinations.

Percentile cut points are computed within the common eligible geography set. Discordance may reflect diagnosis, care seeking, system capture, survey response, model covariates, period mismatch, measurement error, or chance. It is not labeled underdiagnosis, error, unmet need, or service failure.

Primary tract comparisons use PLACES hypertension, diabetes, and COPD measures whose definitions, adult universe, crude/age-adjusted status, model vintage, and observation period are recorded. Healthy Chicago Survey community-area hypertension and diabetes are contextual comparators when rolling periods align. COPD/PLACES obtained through Chicago Health Atlas is not counted as an independent second comparator if it is the same underlying PLACES estimate.

The primary HCS analysis uses hypertension only. HCS and CHM are ranked separately within the 77
pairwise-complete areas with average ranks divided by 77. Quartiles use fixed percentile-rank
boundaries at 0.25, 0.50, and 0.75. HCS pointwise error bars use the displayed estimate plus or
minus 1.96 times the source-provided standard error, bounded to 0% through 100%, and are labeled as
HCS-only uncertainty. Do not test equality of source levels, draw an identity line as a calibration
target, or describe HCS as validating CHM. Before manuscript import, confirm publication permission
for topic files marked `Organization` and the preferred CDPH/Chicago Health Atlas citation.

## 17. Temporal disruption and longitudinal sensitivities

Annual values are displayed from 2019–2024. A geography-condition is flagged as disrupted in 2020 or 2021 when the absolute annual change exceeds 10 percentage points and is more than twice the median absolute year-to-year change for that geography-condition, while denominator and capture do not show an unresolved discontinuity. The flag is descriptive and is not used to remove observations from the primary 2022–2024 pool.

Sensitivities include: 2019 cross-sectional association with 2019 life expectancy when available; 2022, 2023, and 2024 annual associations; exclusion of areas with disruption flags; and alternative outcome alignment using the most recent common annual life-expectancy year. No difference-in-differences, interrupted time-series, or causal pandemic estimate is planned.

The first frozen 2025 CHM extract is a strict out-of-time holdout. Before analysis, compare the
phenotype, lookback, observed-adult denominator, deduplication, contributing systems, suppression,
reliability, tract vintage, direct community-area export, and linkage rules with 2022-2024. If the
gate passes, compute the frozen within-area variance share, median absolute rank gap, exact quartile
disagreement, and Q4 movement using within-2025 ranks and a community-area cluster bootstrap. A
separate sensitivity applies frozen 2022-2024 raw-value quartile cut points. Do not add 2025 to the
primary pool or call a definition-changing release temporal replication.

The preferred external candidate is the Minnesota EHR Consortium Health Trends Across Communities
program because it reports aggregate multi-system EHR data at tract and coarser geographic levels.
The external extract must include geography identifier and vintage, condition, numerator,
denominator, diagnosed proportion, suppression and reliability flags, reporting period, adult
eligibility, contributing systems, deduplication, death/residency rules, and direct-versus-derived
geography status. Direct tract and direct coarser-area values are required to replicate the primary
geographic-resolution estimands. Tract-level EHR-versus-PLACES concordance alone is labeled
contextual cross-source replication.

## 18. Missingness, suppression, and imputation

No suppressed EHR disease numerator and no missing life-expectancy outcome is imputed. Primary analyses use complete areas for exposures and outcomes.

For a prespecified covariate:

- up to 5% missing: complete-case primary;
- greater than 5% through 20% missing: multiple imputation is permitted only if a plausible missing-at-random model, predictors, number of imputations, transformations, and pooling rules were frozen before outcome modeling;
- greater than 20% missing: replace the covariate with a prespecified compatible alternative or withhold the adjusted model.

Imputation does not cross incompatible geographic vintages and does not convert suppressed or unreliable values into observed values. Compare included and excluded areas on available population, capture, and geographic characteristics.

## 19. Multiplicity and confidence intervals

The two primary case-study estimands, C1 and C2, form one confirmatory family. Report two-sided 97.5% confidence intervals, equivalent to Bonferroni control of familywise alpha at .05. Emphasize estimates and uncertainty; P values are secondary and reported consistently with JAMA style.

The separate hypertension and diabetes contrasts are secondary and use 95% confidence intervals without claims of familywise confirmation. Supportive families—spatial alternatives, annual periods, comparator metrics, and equity models—are labeled separately and use Benjamini–Hochberg false-discovery-rate adjustment within each named family only when more than one formal test is reported. Descriptive summaries and prespecified diagnostics are not subjected to multiplicity correction.

## 20. Sensitivity and robustness analyses

The following are prespecified:

1. spatial-error model under the escalation rule;
2. rook and connected distance-band spatial weights;
3. population-weighted OLS using aligned ACS adult population weights, normalized only for numerical convenience and explicitly changing the target to a population-weighted area association;
4. annual 2022, 2023, and 2024 exposures and outcomes;
5. 2019 baseline alignment;
6. exclude disruption-flagged areas;
7. leave-one-area-out and exclude all influence-flagged areas;
8. alternative capture inclusion: continuous, categorical quartiles, and exclusion of implausible ratios identified at S4;
9. minimally adjusted and fully adjusted models;
10. exclusion of crosswalked tract estimates in tract comparisons;
11. complete-case versus permitted multiple-imputation covariate model;
12. external comparator classification using tertiles instead of quartiles.

When compatible life-expectancy standard errors or confidence intervals are available, add the prespecified precision-weighted sensitivity described in Section 7; it never replaces the unweighted principal model.

For each primary estimand, report direction stability, absolute percentage change from the principal estimate, confidence-interval overlap, eligible `n`, and whether any prespecified fragility threshold was crossed.

## 21. Negative controls

No valid negative-control exposure or outcome has been identified. A negative control will not be manufactured from an unrelated available variable. If a scientifically defensible control is proposed before S6, it must have a documented causal rationale, expected null relation, compatible measurement process, and analysis rule. Otherwise the signed SAP records “no valid negative control identified.”

## 22. Equity, sex, gender, race, and ethnicity

Reporting follows STROBE, RECORD, STROBE-Equity, SAGER, and current JAMA demographic-language guidance as applicable.

- Report whether source fields represent sex assigned at birth, legal sex, administrative sex, gender identity, or an unknown construct. Do not substitute the terms.
- If only binary administrative sex is available, state this limitation and do not imply a complete gender measure.
- Report missingness and categories as supplied; aggregation requires a disclosure and precision rationale.
- Explain who classified race and ethnicity, available categories, missingness, and why each variable is used.
- Interpret area racial composition as a marker of racialized social conditions and structural racism, not genetic or biological difference.
- Stratified or interaction models are supportive and require adequate support; absence of statistical interaction is not evidence of equity.
- Do not rank communities as deficient or imply that residents cause area conditions.

## 23. Cause-specific mortality context

Supportive community-area outcomes are 2020–2024 age-adjusted heart disease and diabetes mortality for the cardiometabolic case study, chronic lower respiratory disease mortality for the COPD case study, and all-cause mortality for context, subject to source audit and period compatibility.

Chronic lower respiratory disease mortality is not called COPD mortality. These outcomes do not replace life expectancy, are not part of candidate scoring, and are interpreted as ecological contextual alignment only.

## 24. FQHC/CBO planning demonstration

The demonstration may overlay public HRSA health-center and look-alike sites with reliability-qualified area patterns. A site point conveys listed location only. It does not identify capacity, catchment, patient origin, access, quality, utilization, performance, need, endorsement, or the nearest provider for residents.

Outputs may ask whether local partners wish to compare their panels, examine screening or diagnosis workflows, investigate access barriers, review partnerships, or interpret discordance with community knowledge. Outputs may not claim to identify unmet need, underdiagnosis, an intervention target, optimal allocation, improved care, or expected outcomes. Every display undergoes privacy, stigma, false-positive, and ecological-inference review before release.

## 25. Planned tables and figures

Main manuscript displays are capped at 5:

1. Table 1: resource, adult denominator, coverage, suppression, reliability, and representativeness by period and geography.
2. Figure 1: data flow and reliability-qualified resource coverage map, without outcome results.
3. Figure 2: tract patterns, CHM-PLACES rank alignment, and direct tract-to-community classification for hypertension and COPD.
4. Figure 3: direct tract-to-community classification consequences and temporal stability.
5. Table 2: condition-specific exact agreement, disagreement, within-community variance share, highest-quartile movement, and metric-specific eligible denominators.

Supplementary outputs include phenotype definitions, flow counts, source lineage, scorecard, missingness, geography crosswalk, annual trends, comparator metrics, spatial diagnostics, influence results, aligned mortality, sensitivity analyses, equity reporting, planning-demonstration boundaries, and reporting-checklist crosswalks.

The independent-review supplement additionally includes the HCS hypertension triangulation table
and figure, a 2025 holdout status/comparability table, and an external replication data contract.
The HCS outputs remain outside the 5 main displays unless the statistician and authors replace an
existing display. Unavailable holdout or replication data produce explicit status tables, not
synthetic estimates.

Tables show exact denominators and distinguish suppressed, unreliable, unavailable, and not applicable. Figures use color-vision-safe and grayscale-distinguishable encodings, show units and uncertainty, and never render missing or suppressed cells as zero.

## 26. JAMA Health Forum and reporting requirements

The journal audit on 2026-07-13 found current Original Investigation requirements of 3000 main-text words, no more than 5 tables and/or figures, a structured abstract, Key Points, a Data Sharing Statement, study type, and the applicable EQUATOR guideline. The cross-sectional study guidance also lists 50–75 references. Requirements are rechecked from the official JAMA page within 14 days before submission.

The manuscript package includes completed STROBE and RECORD checklists, a STROBE-Equity crosswalk, and SAGER review. RECORD items cover code/algorithm definitions, database population selection, linkage, data cleaning, and access. The manuscript uses noncausal language, reports estimates with confidence intervals, explains demographic-variable collection and use, and includes ethics, data-access, data-sharing, funding, conflicts, contributor roles, and AI disclosures.

Tavily MCP was attempted during the 2026-07-13 audit but was unavailable because its monthly keyless quota was exhausted. The official JAMA and EQUATOR/RECORD pages were checked directly as the fallback. Ref Context returned official PySAL project documentation describing `libpysal` weights, `esda` spatial autocorrelation, and `spreg` spatial regression; exact implementation APIs remain an S6 software freeze item.

## 27. Reproducibility and software

Later implementation will use immutable source snapshots, checksums, a locked environment, tested reusable modules, and marimo notebooks as transparent presentation layers. No analysis logic may exist only in a notebook cell. The official marimo-notebook and marimo-batch skills must be followed when implementation begins.

Every result records source snapshot identifiers, configuration hash, code commit, environment-lock hash, run timestamp and time zone, random seed, analytic population checksum, spatial-weights checksum, and output checksum. A clean offline rebuild from frozen sources is required before S7 passes.

## 28. Decision, deviation, and audit trail

A decision record contains identifier, timestamp, gate, question, alternatives, evidence, decision, rationale, owner, approver, files affected, outcome-blind status, and superseded decision. A post-freeze deviation additionally records whether outcomes were visible, analyses affected, possible bias direction, interpretation consequence, and approval.

Every manuscript number must trace to a frozen output; every external variable to a publisher, dataset/release, definition, universe, period, geography, URL, and transformation; and every scientific claim to a verified evidence-matrix entry.

## 29. Required approvals

| Role | Name | Decision | Date/time | Signature or immutable approval reference |
|---|---|---|---|---|
| EHR semantic-audit owner | Pending Gate S4 | Not approved | Pending Gate S4 | Pending Gate S4 |
| Outcome-blinded selection owner | Pending Gate S5 | Not approved | Pending Gate S5 | Pending Gate S5 |
| Statistical analysis lead | Pending Gate S6 | Not approved | Pending Gate S6 | Pending Gate S6 |
| Spatial-method reviewer | Pending Gate S6 | Not approved | Pending Gate S6 | Pending Gate S6 |
| Equity/reporting reviewer | Pending Gate S6 | Not approved | Pending Gate S6 | Pending Gate S6 |
| Principal investigator | Pending Gate S6 | Not approved | Pending Gate S6 | Pending Gate S6 |

## 30. Source-grounding register

| Evidence | SAP implication | Stable link |
|---|---|---|
| Winkelman et al., 2026, PMID 42097616 | EHR and PLACES may be similar and different; neither is assumed more accurate; spatial dependence must be addressed | https://pubmed.ncbi.nlm.nih.gov/42097616/ |
| Klompas et al., 2017, PMID 28727539 | EHR surveillance requires explicit validation and population definition | https://pubmed.ncbi.nlm.nih.gov/28727539/ |
| Chen et al., 2022, PMID 35945537 | Underrepresentation motivates coverage diagnostics and carefully bounded weighting/MRP | https://pubmed.ncbi.nlm.nih.gov/35945537/ |
| Conderino et al., 2024, PMID 39568629 | Demographic weighting may leave neighborhood bias under nonignorable selection | https://pubmed.ncbi.nlm.nih.gov/39568629/ |
| Gabert et al., 2016, PMID 27463641 | Small-cell suppression and ecological hypothesis-generating interpretation | https://pubmed.ncbi.nlm.nih.gov/27463641/ |
| Bishop-Royse et al., 2023, PMID 36973497 | Chicago life-expectancy inequities and cause contributions differ by sex | https://pubmed.ncbi.nlm.nih.gov/36973497/ |
| Blazel et al., 2024, PMID 39177999 | Neighborhood EHR hypertension patterns require care-access and structural-context limitations | https://pubmed.ncbi.nlm.nih.gov/39177999/ |
| Chicago Department of Public Health Healthy Chicago Survey, HCSHYTP and HCSDIAP | HCS provides an independent Chicago community-area survey perspective with source-provided standard errors; self-report and period differences prohibit level-equivalence claims | https://chicagohealthatlas.org/ |
| Minnesota EHR Consortium HTAC and Johnson et al., 2026, PMID 41743490 | A second multi-system EHR network can test geographic transportability only when direct tract and direct coarser-area aggregates are available under a compatible use agreement | https://pubmed.ncbi.nlm.nih.gov/41743490/ |
| Canfell et al., 2022, PMID 36434553 | Evidence of translation into policy or practice remains limited | https://pubmed.ncbi.nlm.nih.gov/36434553/ |
| Thomas et al., 2024, PMID 39806634 | MAUP, boundary problems, and ecological fallacy constrain tract interpretation | https://pubmed.ncbi.nlm.nih.gov/39806634/ |
| JAMA Health Forum instructions | Current article and submission rules | https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors |
| RECORD | Routinely collected health-data reporting extension | https://www.record-statement.org/ |
| STROBE | Observational-study reporting | https://www.equator-network.org/reporting-guidelines/strobe/ |
| STROBE-Equity | Equity-focused extension | https://www.equator-network.org/reporting-guidelines/strobe-equity/ |
| SAGER | Sex and gender reporting | https://www.equator-network.org/reporting-guidelines/sager-guidelines/ |
| PySAL project documentation | Planned spatial weights, diagnostics, and regression software family | https://github.com/pysal/pysal/blob/main/README.md |

## 31. Audit disposition

This SAP resolves the final-plan audit by converting narrative intentions into fixed estimands, formulas, model-escalation rules, withholding thresholds, analytic populations, multiplicity families, sensitivity analyses, and display shells. It does not resolve the EHR phenotype and suppression semantics or complete outcome-blinded case-study selection. Therefore its correct disposition is **detailed draft complete for review; not frozen; confirmatory analysis unauthorized**.
