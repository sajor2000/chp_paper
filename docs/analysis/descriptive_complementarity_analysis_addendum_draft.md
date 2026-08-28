# Descriptive Complementarity Analysis Addendum — Chicago Health Map

**Protocol identifier:** CHM-SAP-001-DA1 (descriptive complementarity addendum)
**Version:** 0.2, proposed primary-aim amendment for statistician review
**Date:** 2026-08-27
**Target journal:** JAMA Health Forum — Original Investigation
**Design:** Cross-sectional, small-area ecological *measurement-comparison* study (informatics resource evaluation)
**Relationship to governed SAP:** This addendum proposes a new primary geographic-resolution aim. It becomes controlling only after statistician and author signatures. The life-expectancy analyses and all authorization gates remain in scope as supplementary analyses.

This draft is noncontrolling and does **not** supersede CHM-SAP-001 until those signatures are recorded.

> **Scope in one line:** determine whether direct CHM census-tract EHR-diagnosed proportions add geographic information beyond direct community-area labels. ZCTA labels test geographic sensitivity. CDC PLACES and life-expectancy analyses provide secondary context. A1 through A7 support no claim of prevalence, superiority, validation, causation, underdiagnosis, or unmet need.

---

## 1. Study overview

- **Aim (classification):** measurement comparison / informatics resource evaluation (not association, prediction, or validation against a gold standard).
- **Central question:** Do CHM census-tract EHR-diagnosed proportions add geographic information beyond Chicago community-area labels?
- **Population:** source-defined eligible, geocoded CAPriCORN adults in contributing systems,
  2019–2024. A documented diagnosis contributes to the condition numerator; it does not define
  the denominator.
- **Geography:** City of Chicago — **866 census tracts** (2024 TIGER vintage) and **77 community areas**. (CHM source records span the six-county region; analysis is restricted to Chicago.)
- **Primary period:** denominator-pooled **2022–2024**; annual 2019–2024 for temporal description/sensitivity.
- **Conditions:** hypertension and COPD are displayed because their current source semantics and
  denominators support the governed comparisons. Combined diabetes remains not run. No condition
  is selected or promoted because it has a larger, more favorable, or more visually compelling
  result.

---

## 2. Claims

| # | Claim (short label) | One-line estimand |
|---|---|---|
| **Claim 1** | Added geographic information | Within-community variance share, absolute tract-to-community percentile-rank gap, exact quartile disagreement, and Q4 movement. |
| **Claim 2** | Geographic sensitivity | Repetition of direct cross-frame classifications with Census ZCTAs, annual measures, and noncrossing tracts. |
| **Claim 3** | Source complementarity | Secondary CHM-PLACES rank concordance and categorical agreement without a gold standard. |
| **Claim 4** | Supplementary demonstrations | Community-area spatial patterns and life-expectancy associations, neither of which carries the primary claim. |

Every analysis below supports exactly one claim. Analyses with no claim are out of scope.

---

## 3. Datasets and grain

| Dataset | Role | Grain / unit | Denominator |
|---|---|---|---|
| CHM / CAPriCORN | Primary measure (EHR-diagnosed proportion) | geography–period–condition | observed adults with ≥1 encounter |
| CDC PLACES (2025 tract release, IL subset) | Comparator (model-based) | tract–condition | modeled adult population |
| ACS 5-year (2019, 2022, 2024) | Denominators, covariates, capture rate, MOEs | tract & community area | adult population |
| Census TIGER / City boundaries | Geography, join control, vintage | tract; 77 community areas | — |
| CDC/ATSDR SVI (2022) | Supportive context only | tract | — |

**Unit of analysis:** census tract (primary). Community area is the aggregation comparator. Frozen analytic dataset contract: 22,540 rows × 90 columns (20,692 tract + 1,848 community-area records); unique geography–period–condition key; **direct CHM values never interpolated**.

---

## 4. Measures and operational definitions

- **Primary measure:** direct exported EHR-diagnosed proportion = 100 × numerator / denominator. Label: "EHR-diagnosed proportion among observed CAPriCORN adults." Terms *prevalence, incidence, risk* are prohibited. Age standardization was not run because governed age-stratum inputs are unavailable; it requires new governed inputs and an approved deviation.
- **Pooling:** sum eligible 2022 through 2024 numerators and divide by the corresponding summed denominators. An unweighted mean of annual percentages is a sensitivity analysis only.
- **PLACES comparator:** crude/age-adjusted status, model vintage, and observation period recorded per measure; used for concordance/discordance only, never as validation of accuracy.
- **Reliability gating:** reliability qualification remains withheld and is not used to define a primary tract subset. Any future tier-restricted analysis requires a governed qualification decision; equity notes remain descriptive.
- **Suppression:** cells <10 suppressed (`<10`/N/A), with secondary suppression; suppressed ≠ zero; never imputed.
- **Diabetes combined-components sensitivity:** components are summed only when their published
  denominators match and the combined numerator does not exceed that denominator. This does not
  establish a phenotype-equivalent total-diabetes measure or a primary PLACES comparison.

---

## 5. Analytic populations

1. **CHM-only tract population:** Chicago tracts with eligible, nonsuppressed CHM numerators and
   denominators for 2022 through 2024 and a dominant community-area link. A1 and A2 use this frame
   and do not require PLACES.
2. **CHM-PLACES comparison population:** CHM-eligible tracts with a compatible PLACES estimate and
   documented comparator period. Missing PLACES data exclude a tract only from A3 through A5.
3. **Direct cross-frame population:** eligible direct tract and linked direct community-area CHM
   records. This is a linked classification comparison, not literal tract aggregation.
4. **Temporal population:** tracts with eligible 2019–2024 observations (annual sensitivity).

Flow counts report exclusions separately: invalid/unmatched geography or vintage, suppressed numerator, missing denominator, failed reliability, missing comparator.

---

## 6. Analysis Overview

| ID | Claim | Analysis question (plain) | Estimand / statistic | Unit | Primary method | Diagnostics / sensitivity |
|---|---|---|---|---|---|---|
| A1 | 1 | How much tract variation remains within a community area? | Between-area VPC and within-area variance share per condition | tract in CA | One-way observed-scale method-of-moments decomposition with 1000 area-cluster bootstrap replicates | SA1a noncrossing cohort; SA1b annual estimates; SA1c reliability-gated subset if approved |
| A2 | 4 | How strongly does an area label separate empirically high tracts? | Exploratory descriptive area-label AUC | tract in CA | Mann-Whitney AUC from leave-one-tract-out community-area mean scores with the empirical threshold recomputed in 1000 area-cluster bootstrap replicates | SA2 alternative thresholds; remove if the construct is not approved |
| A3 | 2 | Do CHM and PLACES rank areas the same way? | Spearman rank correlation (primary); Pearson (supportive) | tract | Spearman ρ with bootstrap CI | per-condition; reliability-gated |
| A4 | 3 | Do CHM and PLACES agree categorically? | Exact quartile agreement and quadratic weighted κ; supplementary unweighted Gwet AC1 | tract | Exact agreement, weighted κ, and nominal AC1 sensitivity | SA4 tertile cut; marginal-distribution check; AC2 sign-off item |
| A5 | 2 | Are divergences larger than available uncertainty inputs imply? | Share of tracts discordant beyond combined uncertainty | tract | Monte-Carlo propagation only if compatible PLACES CIs and ACS MOEs are governed; otherwise not run | SA5 analytic-approximation cross-check if inputs become available |
| A6 | 1, 2 | Does direct tract classification differ from linked direct coarse-area classification? | Absolute rank gap, exact quartile disagreement, and Q4 movement | tract linked to CA or ZCTA | Rank each direct source at its own grain, then link classifications | noncrossing, annual, ZCTA, alternative categories |
| A7 | 4 | Is there supplementary community-area spatial structure? | Global and local spatial association | community area in current implementation | Local Moran I, bivariate local Moran I, and Getis-Ord Gi* with queen weights, 9999 conditional permutations, and within-family BH FDR | Spatial scan not run. No tract hotspot claim |

All p-values are secondary to estimates and CIs. Descriptive summaries and prespecified diagnostics are not multiplicity-corrected; the local-cluster tests in A7 use FDR control (see §8).

---

## 7. Draft methods summary (not manuscript-ready)

**Within-neighborhood heterogeneity (A1–A2).** For each condition, a one-way method-of-moments decomposition estimates the between-community and within-community components of the observed pooled tract proportions. The VPC is the between-community share. Its complement is the primary within-community variance share. The point estimate and all 1000 area-cluster bootstrap replicates use the same estimator. This describes geographic variation in tract estimates. It is not a patient-level ICC or a binomial multilevel disease model. Separately, a descriptive area-label AUC uses leave-one-tract-out community-area mean scores and a Mann-Whitney statistic to separate high-quartile tracts. The AUC is secondary and is not an externally validated prediction model.

**Source complementarity (A3–A5).** Concordance between CHM and PLACES tract measures is summarized by Spearman rank correlation (primary; Pearson supportive) and categorical quartile agreement by weighted κ and Gwet's AC1. Because CHM (diagnosed-among-observed) and PLACES (modeled population) are non-equivalent estimands, neither is treated as a gold standard. Monte-Carlo uncertainty propagation is labeled not run unless compatible governed PLACES confidence intervals and ACS margins of error are available.

**Scale sensitivity (A6).** Within each condition-year, assign tract quartiles among eligible
linked tract records and community-area quartiles once among eligible direct community-area
records; then propagate the latter label to linked tracts. Community values are never duplicated
before ranking. Ties preserve equality at a boundary; fewer than 4 nonempty rank groups produces
`not_assignable_insufficient_or_tied_distribution`. The heterogeneity and concordance metrics are
recomputed at tract and community-area scales (and ZIP groupings if they can be constructed cleanly
from source records), quantifying direct cross-frame classification differences rather than literal
aggregation [Thomas 2024; Jones & Kulldorff 2012].

**Local spatial structure (A7).** The current implementation reports community-area local Moran I, bivariate local Moran I, and standard Getis-Ord Gi* on row-standardized queen-contiguity weights. Each test uses 9999 conditional permutations that hold the focal value fixed while permuting neighbor values. Two-sided permutation P values are centered on the conditional permutation distribution. Benjamini-Hochberg adjustment is applied within each condition-period-statistic family. A spatial scan statistic and tract-level local clustering were not run.

All spatial software uses documented PySAL components (`libpysal`, `esda`) or an equivalently validated implementation; weight transformation, seeds, and permutation counts are recorded.

---

## 8. Multiplicity

A1 and A6 define the proposed primary descriptive family. They emphasize estimates, confidence intervals, and explicit denominators. No single omnibus P value is used. A2 through A5 and A7 are secondary or supplementary. Benjamini-Hochberg false-discovery-rate control is applied within each implemented A7 condition-period-statistic family. This amendment does not alter the separate C1/C2 confidence-interval rule.

---

## 9. Missing data and suppression

Complete-case for exposures and comparators. No suppressed CHM numerator and no missing comparator is imputed. Covariate missingness ≤5% → complete-case; >5–20% → prespecified multiple imputation only if frozen before analysis; >20% → drop/replace with a prespecified alternative. Imputation never crosses geographic vintages and never converts suppressed/unreliable values into observed values. Included vs excluded tracts are compared on population, capture, and geography.

---

## 10. Reproducibility and governance

Frozen source snapshots with checksums; locked environment; deterministic two-run byte-identical outputs; per-tract reliability tiers and equity notes; complete lineage, source-join manifest, and data book. Every reported number traces to a frozen output and a code commit. Analysis logic lives in tested modules; the marimo notebook is the presentation layer only.

---

## 11. Candidate supplementary outputs

| Output | Claim(s) | Contents | Interpretation |
|---|---|---|---|
| **eTable A1** | 1, 2, 3 | Variance partition, AUC, Spearman, kappa/AC1, and geographic-resolution summaries | Quantitative complementarity review summary |
| **eFigure A1** | 1, 3 | Tract heterogeneity and geographic-resolution sensitivity | Information retained at tract resolution |
| **eFigure A2** | 2 | CHM–PLACES concordance and discordance | Aligned but noninterchangeable measurement lenses |
| **eFigure A3** | 4 | Local spatial diagnostics and explicit not-run statuses | Exploratory spatial structure |
| Additional eTables/eFigures | all | Annual trends, reliability strata, uncertainty status, and diagnostics | Supporting exploratory analyses |

Figures use color-vision-safe, grayscale-distinguishable encodings; suppressed/missing/unreliable have distinct encodings and are never rendered as zero.

---

## 12. Decision–Evidence

| ID | Decision | Rationale | Citations (verify full text before freeze) |
|---|---|---|---|
| D1 | Observed-scale one-way method-of-moments variance partition with a secondary area-label AUC | Uses one estimator for the point estimate and bootstrap replicates. The within-area share directly answers the geographic-resolution question | Nakagawa et al 2017, doi:10.1098/rsif.2017.0213; Hanley and McNeil 1982, doi:10.1148/radiology.143.1.7063747 |
| D2 | Report 1000 area-cluster bootstrap replicates and percentile CIs for review | Resampling the 77 community areas preserves tract clustering within sampled areas. Ranks and rank categories are recomputed within each replicate. A 5000-replicate final run remains a sign-off option | Efron 1979, doi:10.1214/aos/1176344552 |
| D3 | Spearman primary concordance; exclude gold-standard/agreement-on-scale claims | Sources are non-equivalent estimands (diagnosed-among-observed vs modeled) | Winkelman 2026 (PMID 42097616); Nielsen 2024 (PMID 38447855) |
| D4 | Use exact agreement and quadratic weighted kappa, with AC1 as a nominal sensitivity | Weighted kappa respects quartile distance. AC1 addresses marginal concentration but does not encode ordinal distance | Cohen 1968, doi:10.1037/h0026256; Gwet 2008, doi:10.1348/000711006X126600 |
| D5 | Monte-Carlo uncertainty propagation for discordance | Divergence must exceed combined measurement uncertainty to count | Srebotnjak 2010 (PMC2958154) — *verify*; Chen 2022 (PMID 35945537) |
| D6 | MAUP scale-sensitivity across tract/CA/(ZIP) | Coarsening preserves detection but destroys localization | Thomas 2024 (PMID 39806634); Jones & Kulldorff 2012 (PMC3480474) |
| D7 | Local Moran I, bivariate local Moran I, and standard Getis-Ord Gi* with queen weights | Standard local spatial association statistics with an explicit conditional randomization scheme | Anselin 1995, doi:10.1111/j.1538-4632.1995.tb00338.x; Getis and Ord 1992, doi:10.1111/j.1538-4632.1992.tb00261.x |
| D8 | BH FDR within each condition-period-statistic family | Controls the expected false-discovery proportion within each declared family | Benjamini and Hochberg 1995, doi:10.1111/j.2517-6161.1995.tb02031.x |
| D9 | Do not age-standardize the current CHM measure | Governed age-stratum numerators and denominators are unavailable. A new standardized estimand requires new inputs and an approved deviation | No citation added until a standardization analysis is specified |
| D10 | Do not reliability-gate the primary population until the source algorithm is approved | Capture and reliability strata are reported as sensitivity information. They are not evidence of representativeness | CONSCIENCE reliability framework (internal); Chen 2022 (PMID 35945537) |

---

## 13. Open decisions requiring Ashley's sign-off

1. **A1/A2 estimator:** approve observed-scale method-of-moments VPC as primary, within-area variance share as the main interpretation, and AUC as exploratory. Approve the empirical AUC threshold rule.
2. **Bootstrap:** approve community-area clustering, recomputation of ranks in each replicate, the 2.5th and 97.5th percentile interval, and 1000 versus 5000 final replicates.
3. **A4 agreement:** approve exact agreement and weighted κ as ordinal summaries. Decide whether to retain nominal AC1, replace it with weighted AC2, or report no second chance-corrected coefficient.
4. **A5 uncertainty:** Monte-Carlo (recommended) vs analytic approximation.
5. **A7 spatial:** weight specification, conditional permutation rule, and FDR family definition. Retain the spatial scan as not run unless governed counts and population at risk become available.
6. **A6 ZCTA:** confirm the direct ZCTA comparison and its tract linkage. Use ZCTA, not USPS ZIP Code, in all reporting.
7. **A3/A4 comparator alignment:** confirm the PLACES release, BRFSS observation period, condition
   phenotype mapping, and whether pooled versus annual CHM comparisons are admissible; otherwise
   retain `not_run_pending_comparator_semantics`.

Recommended defaults are marked. Each remains provisional until the independent biostatistician
and authors sign the amendment.

---

## 14. Reporting and language

STROBE + RECORD (routinely collected data), STROBE-Equity, and SAGER as applicable; report estimates with CIs, not p-values alone. Permitted: "was associated with," "aligned but not interchangeable," "diagnosed proportion among observed adults." Prohibited: caused, prevalence, underdiagnosis, unmet need, access failure, error, service need, superiority, validation. Area racial composition, if used, is framed as a marker of racialized social conditions, not biology.

---

## 15. Relationship to CHM-SAP-001

- **Retained:** both governed community-area life-expectancy analyses, their VIF/readiness gates, the 97.5% primary CI family, and `results_authorized=false`.
- **Proposed primary:** direct tract-to-community exact agreement, disagreement, highest-quartile movement, and within-community variance share.
- **Secondary or supplementary:** ZCTA sensitivity, descriptive AUC, CHM-PLACES agreement, uncertainty propagation when inputs permit it, local spatial diagnostics, and life-expectancy models.
- **Not authorized:** A1 through A7 do not become manuscript-importable results until the open decisions in Section 13 are resolved, the amendment is signed, and S7 is complete.
- **Unchanged:** measure semantics, reliability framework, suppression, provenance/reproducibility, and noncausal language.
