# Chicago Health Map Complementarity Analysis and Marimo Notebook Design

**Date:** 2026-07-15

**Status:** Approved conversational design; written specification pending author review

**Target journal and article type:** JAMA Health Forum Original Investigation

**Study design:** Ecological, cross-sectional community-area analysis with descriptive,
spatial, and external-triangulation components

**Primary observational unit:** Chicago community area

**Governing analysis document:** `docs/analysis/statistical_analysis_plan.md`

## 1. Purpose

Build a reproducible analytic dataset and a publication-quality marimo notebook that show
what Chicago Health Map (CHM) adds to existing public-health data about Chicago's
community-area life-expectancy differences.

The manuscript's novelty is not another description of the Chicago Health Atlas. The Atlas
establishes the public-health outcome pattern. CHM contributes a distinct clinical lens:
EHR-diagnosed proportions among observed CAPriCORN adults, together with explicit coverage,
capture, suppression, and reliability information. Census and public-health sources provide
context, adjustment, and triangulation. They do not replace CHM phenotypes or denominators.

The notebook must be both:

1. an auditable computational record whose displays resolve to frozen inputs and tested code;
2. a guided scientific narrative that teaches readers how each analytic decision changes the
   interpretation.

## 2. Evidence and authority contract

### 2.1 Authority order

When sources disagree, use this order:

1. verified data, signed governance artifacts, and the approved SAP;
2. live JAMA Health Forum author instructions;
3. project-specific manuscript contracts and frozen dictionaries;
4. verified biomedical and statistical literature;
5. exemplar patterns and stylistic preferences.

No notebook cell may invent a result, denominator, confidence interval, citation, ethics
determination, or unresolved scientific choice. Unavailable evidence must remain a labeled
shell, warning, or blocker.

### 2.2 Research basis

The design is grounded in verified source records maintained in the Paperclip repository
`chicago-ecological-model-s7`:

- Prospective statistical analysis plans improve transparency by prespecifying covariate
  adjustment and multiplicity decisions (DEBATE guidance; DOI
  `10.1186/s12874-019-0879-5`).
- EHR poststratification and related methods can reduce selection bias, but residual
  neighborhood bias can remain under nonignorable selection (Conderino et al; DOI
  `10.1136/bmjph-2024-001666`). This supports adjustment for capture while prohibiting claims
  that capture adjustment makes CHM population-representative.
- HC3 covariance is appropriate for heteroskedasticity-robust inference in many small-sample
  settings but does not address spatial dependence (DOI `10.3758/s13428-025-02801-4`).
- Residual spatial-autocorrelation results depend on the spatial-weights definition, supporting
  a frozen queen specification and prespecified alternative weights (DOI
  `10.1371/journal.pone.0146865`).

References must be resolved from Paperclip, PubMed, or another verified source record. They
must never be formatted from model memory.

### 2.3 Journal requirements

The live JAMA Health Forum Instructions for Authors were verified in the browser on
2026-07-15; the page reports `Last Updated: June 30, 2026`. The verified requirements include:

- Original Investigation main text: no more than 3000 words;
- structured abstract: no more than 350 words;
- Key Points: no more than 100 words;
- research title: no more than 100 characters including spaces;
- no more than 5 main tables and/or figures and 50 to 75 references for a cross-sectional
  study;
- separate Design, Setting, and Participants abstract headings;
- exact estimates and uncertainty for every primary outcome in text or a table, not only a
  figure;
- observational unit and number of observations stated explicitly;
- STROBE reporting and a Data Sharing Statement;
- disclosure of qualifying AI assistance, including tool, version, manufacturer, dates, work
  performed, and confirmation that authors take responsibility for the content.

The official instructions remain the controlling authority and must be checked again before
manuscript finalization or any submission-readiness claim.

## 3. Central evidence ladder

The notebook and eventual manuscript must progress through the following claims in order:

1. **Known public-health pattern:** Chicago Health Atlas documents community-area
   life-expectancy differences.
2. **CHM data fitness:** CHM coverage, denominators, capture, suppression, and reliability are
   sufficient for the prespecified uses, with limitations displayed beside the findings.
3. **Distinct clinical lens:** CHM describes diagnosed proportions among adults observed in
   participating health systems; it is not population prevalence.
4. **Adjusted ecological association:** CHM diagnosed-condition measures are evaluated in
   relation to area life expectancy after adjustment for prespecified demographic context and
   EHR capture.
5. **Triangulation and diagnostics:** PLACES, temporal checks, influence diagnostics, and
   spatial analyses assess agreement, discordance, and model sensitivity without designating a
   gold standard.
6. **Bounded complementarity claim:** CHM may add clinically grounded questions for local
   review; the analyses do not establish causation, community need, service failure, or optimal
   allocation.

## 4. Source roles and measure semantics

| Source | Frozen role | Permitted interpretation | Prohibited substitution |
| --- | --- | --- | --- |
| Chicago Health Map/CAPriCORN | Primary novel exposures, denominators, capture, coverage, suppression, reliability | EHR-diagnosed proportion among observed CAPriCORN adults | Population prevalence, individual risk, incidence, or inferred CHM values |
| Chicago Health Atlas | Primary community-area life-expectancy outcome and public-health context | Aligned community-area outcome with producer metadata | Gold standard for CHM diagnosis or capture |
| ACS/Census | Prespecified demographic adjustment and population context | Area composition and adult-population context | Clinical phenotype or health-system denominator |
| CDC PLACES | External triangulation | Definition-qualified concordance or discordance | Replacement CHM exposure or independent source when Atlas republishes the same estimate |
| City of Chicago geometry | Mapping, contiguity, and geographic validation | Frozen boundary topology | Centroid assignment of split tracts for primary modeling |

Missing, suppressed, unreliable, withheld, structural-zero, and observed-zero states remain
distinct through cleaning, analysis, tables, figures, and exports.

## 5. Analytic-data architecture

### 5.1 Separation of concerns

The notebook is a presentation and orchestration layer. Reusable cleaning, validation,
modeling, spatial, table, and figure logic belongs in tested modules under
`src/chicagohealthmap/`. Notebook cells call those functions and display their returned,
typed artifacts. No inferential result may depend on hidden notebook-only transformations.

The frozen master dataset remains the source of truth. Derived datasets must record the input
manifest checksum, configuration hash, code commit, environment-lock hash, run timestamp and
time zone, random seeds, analytic-population checksum, spatial-weights checksum when
applicable, and output checksum.

### 5.2 Required derived datasets

1. **Validated master view:** source records with normalized geography, period, units,
   suppression state, lineage, and analytic role.
2. **Primary community-area frame:** one row for each of 77 community areas, containing the
   aligned life-expectancy outcome, pooled CHM hypertension and diabetes diagnosed
   proportions, prespecified covariates, and provenance fields.
3. **Respiratory frame:** the documented COPD-eligible population, expected to contain 76
   areas unless the frozen eligibility artifact changes.
4. **Descriptive resource frame:** disease-by-period-by-geography summaries for Table 1 and
   notebook quality displays.
5. **Triangulation frames:** definition- and period-compatible CHM/public-source pairs at the
   approved geography.
6. **Sensitivity frames:** explicit copies or views with immutable identifiers for population
   weighting, annual periods, capture alternatives, influence exclusions, and spatial models.

The implementation must update `build_primary_community_frame()` or its replacement to carry
one exact value per community area for:

- percentage aged 65 years or older;
- percentage female;
- percentage below the federal poverty level;
- aligned ACS adult population;
- pooled-period EHR capture ratio.

ACS adult population is retained for description and sensitivity weighting, not included in
the primary adjustment set.

### 5.3 Cleaning contract

Cleaning must:

- verify all registered source and manifest checksums before transformation;
- normalize community-area identifiers without lossy name-based matching;
- retain original identifiers and labels for audit;
- align periods using the frozen EHR-year-to-ACS and life-expectancy mapping rules;
- harmonize units without converting incompatible universes into a common measure;
- preserve numerators and denominators beside every derived proportion;
- preserve suppression and reliability states;
- avoid direct averaging of percentages when pooled numerator/denominator construction is
  required;
- prohibit tract-to-community-area aggregation as a way to manufacture missing CHM values;
- emit a deterministic record-flow artifact for every exclusion and transformation.

### 5.4 Fail-closed data checks

Primary analysis cannot execute unless all applicable checks pass:

- exactly 77 unique community-area identifiers in the primary frame;
- expected model-specific eligibility counts and no unexplained duplicate rows;
- complete primary outcome, exposure, and adjustment data for at least 70 areas;
- at least 10 distinct nonsuppressed values for each required exposure;
- one compatible covariate value per area and no incompatible geography vintage;
- values, units, and denominators within frozen allowable ranges;
- suppression and missingness counts reconcile to source artifacts;
- frozen input, population, and output checksums match their manifests.

Nonfatal warnings remain visible and flow to captions and limitations. Fatal checks stop the
model with a machine-readable reason and a plain-language notebook explanation.

## 6. Statistical architecture

### 6.1 Primary model specification

The primary estimator is equal-area ordinary least squares with HC3 robust covariance and one
row per eligible community area.

Cardiometabolic model:

\[
LE_i = \alpha + \beta_H H_i^* + \beta_D D_i^*
+ \gamma_1 Age65_i^* + \gamma_2 Female_i^*
+ \gamma_3 Poverty_i^* + \gamma_4 Capture_i^* + \epsilon_i.
\]

Respiratory model:

\[
LE_i = \alpha + \beta_C COPD_i^*
+ \gamma_1 Age65_i^* + \gamma_2 Female_i^*
+ \gamma_3 Poverty_i^* + \gamma_4 Capture_i^* + \epsilon_i.
\]

The frozen primary adjustment set is percentage aged 65 years or older, percentage female,
percentage below the federal poverty level, and EHR capture ratio. This resolves the current
implementation discrepancy in which `acs_adult_population` appears in
`ADJUSTMENT_COVARIATES` despite SAP section 9.3.

### 6.2 Scaling and parameter definitions

- CHM exposures are centered and divided by model-specific IQRs computed once in the frozen
  primary complete-case population.
- Adjustment covariates are centered and divided by their frozen standard deviations.
- Scaling constants, centers, eligible population identifiers, and checksums are stored in the
  data dictionary and model artifact.
- Directly comparable sensitivity models reuse the frozen exposure IQRs.

Parameter meanings:

- `alpha` is expected area life expectancy at the mean CHM exposure and covariate values. It is
  primarily a model anchor.
- `beta_h`, `beta_d`, and `beta_c` are adjusted differences in life-expectancy years associated
  with one frozen-IQR higher CHM diagnosed proportion.
- `gamma_1` through `gamma_4` are adjustment slopes per 1-SD difference in the corresponding
  area characteristic. They are nuisance parameters, not headline estimands.

The primary cardiometabolic contrast is `beta_h + beta_d` after IQR scaling. Its standard
error and confidence interval must use the full model covariance matrix, including
`2 * Cov(beta_h, beta_d)`.

### 6.3 Estimands and multiplicity

- **C1:** adjusted mean difference in area life expectancy associated with simultaneous
  one-IQR increases in hypertension and diabetes CHM diagnosed proportions.
- **C2:** adjusted mean difference in area life expectancy associated with a one-IQR increase
  in COPD CHM diagnosed proportion.
- C1 and C2 form one confirmatory family and use two-sided 97.5% confidence intervals.
- Separate hypertension and diabetes coefficients are secondary and use 95% confidence
  intervals.
- P values are secondary to estimates and uncertainty.
- Exploratory analyses cannot replace or relabel a primary estimand based on sign, magnitude,
  P value, or visual appeal.

### 6.4 Model outputs

Every fitted model returns a typed result bundle containing:

- model, estimand, population, period, outcome, and exposure identifiers;
- formula and complete adjustment set;
- alpha, beta, and gamma coefficients;
- coefficient role, scale, estimate, robust standard error, confidence level, confidence
  limits, and P value;
- C1 covariance-correct joint contrast where applicable;
- number of observations and degrees of freedom;
- R-squared and adjusted R-squared as descriptive fit measures;
- design-matrix rank, correlations, VIFs, and condition diagnostics;
- influence flags and leave-one-area-out ranges;
- residuals keyed to geography;
- checksums and software/environment provenance;
- authorization status and any withholding reason.

A context-only versus CHM-added model comparison may report incremental R-squared and adjusted
R-squared only as a clearly labeled exploratory, post-unblinding analysis. It may not be
described as causal variance explained.

### 6.5 Model diagnostics and withholding

Withhold interpretation when any SAP condition fails, including:

- fewer than 70 complete areas;
- rank deficiency;
- correlation greater than 0.80 or VIF greater than 5 without a prespecified resolution;
- inadequate exposure variation;
- nonfinite HC3 covariance;
- unstable standard errors;
- unresolved data error dominating the estimate.

Flag but retain areas with Cook's distance greater than `4/n`, leverage greater than `2p/n`,
or absolute externally studentized residual greater than 3. Label a primary result fragile if
a single-area deletion changes its sign or absolute magnitude by more than 30%.

### 6.6 Spatial diagnostics

- Construct row-standardized queen-contiguity weights from frozen official geometry.
- Document invalid polygons and islands; never silently connect an island.
- Calculate residual Global Moran's I on each **adjusted primary OLS** model with 9999
  conditional random permutations and a frozen seed.
- Store the observed statistic, expected statistic, permutation P value, seed, permutations,
  and weights checksum.
- If both `abs(I) >= 0.10` and `P < .05`, fit the prespecified spatial-error model as a
  mandatory sensitivity using the identical outcome, exposures, and adjustment set.
- Use rook contiguity and a connected distance band as supportive weight specifications.
- OLS remains primary. If the spatial-error contrast changes sign or differs by more than 20%
  in absolute magnitude, label the finding `model-sensitive` and display both estimates.

PySAL components or an equivalently validated implementation must be selected only after Ref
MCP review of current official package documentation. Package versions, weight
transformation, optimizer, convergence rule, and log-likelihood diagnostics must be frozen in
the implementation plan.

### 6.7 Sensitivity hierarchy

Prespecified sensitivity outputs include:

1. mandatory spatial-error model when the escalation gate is crossed;
2. rook and connected distance-band weights;
3. ACS-adult-population-weighted OLS, explicitly changing the estimand;
4. annual 2022, 2023, and 2024 alignments and the approved 2019 baseline;
5. exclusion of disruption-flagged areas;
6. leave-one-area-out and exclusion of all influence-flagged areas;
7. capture as continuous, quartiles, and exclusion of frozen implausible-ratio areas;
8. minimally and fully adjusted models;
9. approved complete-case versus imputation comparison, if applicable;
10. tertile rather than quartile comparator classification.

Aligned ACS adult population may additionally enter a clearly labeled log-population
sensitivity if added to the signed analysis plan before execution. It is not a primary
adjustment variable.

## 7. Marimo notebook architecture

The visible notebook order is frozen:

1. Data cleaning
2. Data quality checks
3. Analytic data set
4. Descriptive statistics
5. Case study one
6. Case study two
7. Tables and figures for both case studies

### 7.1 Repeated reader-facing pattern

Every major section begins with:

1. scientific question;
2. data sources and source roles;
3. method and estimand;
4. equation and parameter glossary where relevant;
5. why the step matters;
6. assumptions and limitations.

The next cell calls tested code. The following cell displays an audit table and a concise,
plain-language interpretation. Markdown explains scientific choices and transformations; it
does not narrate trivial Python syntax line by line.

Interactive controls may filter or choose display layers and prespecified sensitivity views.
They may not alter the frozen primary formula, eligible population, scaling constants,
multiplicity rules, random seeds, or spatial gate.

### 7.2 Section 1: Data cleaning

Display:

- source-role table;
- checksum and manifest verification;
- record-flow table;
- geographic and period-alignment table;
- variable/unit dictionary;
- deterministic cleaning audit.

### 7.3 Section 2: Data quality checks

Display structural integrity, geographic completeness, value-range, unit, missingness,
suppression, reliability, capture, model-eligibility, cross-source linkage, and reproducibility
checks. Fatal failures must show what failed, why inference is blocked, and which artifact must
be repaired.

### 7.4 Section 3: Analytic data set

Display the final 77-area table and its schema with safe filters for variable family and source
role. Each variable must show denominator, period, transformation, source, intended analytic
role, and missing/suppression semantics. The 76-area COPD eligibility view must be visibly
reconciled to the master frame.

### 7.5 Section 4: Descriptive statistics

The principal output is Table 1, centered on CHM coverage and analytic fitness. Additional
notebook-only displays include distributions, capture diagnostics, source-qualified
correlations, maps, and nonranked area summaries.

No community league table or stigmatizing rank display is permitted. Suppressed, missing, and
unreliable areas receive separate visual encodings rather than the lowest disease category.

### 7.6 Section 5: Case study one

Scientific question: What do CHM diagnosed hypertension and diabetes proportions add to the
public-data lens on community-area life expectancy?

Display:

- eligibility and frozen model-specification table;
- alpha, beta, and gamma coefficient table;
- covariance-correct `beta_h + beta_d` contrast;
- adjusted partial-relationship displays;
- exposure and joint-contrast forest display;
- influence diagnostics;
- adjusted residual map and Moran diagnostic;
- exploratory context-only versus CHM-added fit comparison;
- prespecified sensitivity summary.

### 7.7 Section 6: Case study two

Scientific question: What does the CHM diagnosed COPD proportion add to the public-data lens
on community-area life expectancy?

Mirror Section 5's grammar, including eligibility, full coefficient table, adjusted
relationship, coefficient display, influence diagnostics, adjusted residual map, Moran
diagnostic, PLACES triangulation, and sensitivity summary. Mirroring prevents result-driven
emphasis.

### 7.8 Section 7: Publication outputs

Render and export the five main-display candidates and supplement-ready artifacts from the
same result bundles. This section is an output registry: each display lists its source artifact,
population, period, checksum, manuscript destination, and authorization state.

## 8. Main and supplemental displays

### 8.1 Main displays

1. **Table 1 — Chicago Health Map coverage and analytic fitness.** Resource size, observed
   population, disease-specific availability, denominators, capture, suppression, missingness,
   reliability, and model eligibility.
2. **Figure 1 — Complementary geographic lenses on community health.** Aligned Chicago Health
   Atlas life expectancy and CHM hypertension, diabetes, and COPD maps using a shared visual
   grammar, with reliability and analytic-inclusion states encoded explicitly. The detailed
   record flow and capture diagnostics remain in the notebook and supplement so the main
   figure stays legible.
3. **Figure 2 — Cardiometabolic case study.** Adjusted hypertension and diabetes patterns,
   covariance-correct joint contrast, uncertainty, and definition-qualified public comparator.
4. **Figure 3 — Respiratory case study.** Adjusted COPD pattern, uncertainty, comparator
   concordance, and the same visual grammar as Figure 2.
5. **Table 2 — Primary estimates and robustness.** Primary unadjusted and adjusted contrasts,
   97.5% intervals for C1/C2, secondary 95% intervals, model population, Moran/spatial decision,
   and robustness classification.

The notebook displays full alpha/beta/gamma coefficient tables. The main Table 2 prioritizes
primary and secondary exposure contrasts; nuisance adjustment coefficients move to an eTable
to preserve interpretability and avoid duplicating Figure 2 or Figure 3.

### 8.2 Supplement-ready outputs

- complete coefficient and scaling dictionary;
- full inclusion, missingness, and suppression flow;
- source and phenotype definitions;
- correlations, VIFs, and design diagnostics;
- influence and leave-one-area-out analyses;
- residual Moran and spatial-error outputs;
- alternative spatial weights;
- population-weighted and capture sensitivities;
- annual and temporal-disruption analyses;
- PLACES concordance/discordance analyses;
- complete provenance and computational-environment table;
- reporting-guideline and claim-ledger crosswalks.

## 9. Reader-facing statistical language

The notebook generates sentences from typed result fields so displayed numbers and prose cannot
diverge. Templates must include the observational unit, eligible `n`, exposure scale,
adjustment set, estimate, confidence interval, and ecological boundary.

Approved template:

> Among [n] eligible Chicago community areas, a 1-IQR higher CHM EHR-diagnosed [condition]
> proportion among observed CAPriCORN adults was associated with a [beta]-year difference in
> aligned community-area life expectancy after adjustment for age composition, sex
> composition, poverty, and EHR capture ([confidence level]% CI, [lower] to [upper]).

Coefficient glossary template:

> The intercept alpha is the model-predicted life expectancy for an area at the mean exposure
> and covariate values. Beta coefficients quantify adjusted life-expectancy differences per
> frozen-IQR higher CHM diagnosed proportion. Gamma coefficients quantify adjustment slopes per
> 1-SD difference in the corresponding area characteristic and are not the primary estimands.

Required boundary:

> These estimates are ecological associations and do not represent individual risk, causal
> effects, or population disease prevalence.

The terms `caused`, `drove`, `explained`, `attributable`, `preventable years`, `impact`,
`effect`, and `would improve` are prohibited for the primary ecological models. The notebook
also prohibits unsupported claims of underdiagnosis, unmet need, access barriers, care quality,
optimal allocation, or intervention benefit.

Before S7 authorization, result-bearing prose is labeled `freeze candidate — manuscript use
unauthorized`. The notebook may explain parameter meaning and methods but may not draft
empirical Results, Key Points, abstract findings, or conclusions.

## 10. Visual and interaction standard

- full-width responsive marimo layout;
- restrained Chicago-inspired accents within a colorblind-safe palette;
- stable condition colors across all outputs;
- direct labeling and minimal legend dependence;
- visible numerical and graphical confidence intervals;
- readable typography and adequate color contrast;
- units on every quantitative axis;
- captions that state population, period, measure semantics, adjustment set, and uncertainty;
- no pie charts, 3-dimensional graphs, decorative gradients, or unjustified stacked bars;
- no duplicate presentation of the same result in a main table and main figure;
- editable, exportable tables and deterministic vector or high-resolution figure outputs.

Great Tables or another already approved local table layer may be used. Current marimo,
Great Tables, and spatial-library behavior must be checked against current official package
documentation through Ref MCP before implementation decisions are frozen.

## 11. Error handling and authorization

Analysis execution and manuscript authorization are separate states:

- passing data/model gates permits generation of candidate adjusted-model artifacts;
- `results_authorized=false` remains until independent S7 numerical review succeeds;
- unauthorized estimates cannot populate manuscript Results, abstract, Key Points, or
  conclusions;
- every table, figure, sentence, and export displays or records its authorization state;
- a failed gate produces descriptive outputs only and records the withholding reason.

The current notebook's hard-coded `results_authorized=false` must be replaced by a read-only
governance artifact, not by a user-facing toggle or an inferred status.

## 12. Verification and acceptance criteria

### 12.1 Automated verification

- unit tests for cleaning, scaling, model gates, coefficient extraction, covariance contrasts,
  sentence rendering, display schemas, and authorization behavior;
- integration tests for the complete notebook in script and headless execution modes;
- deterministic rerun test with matching analytic and output checksums;
- formatting, lint, and static-type checks;
- offline rebuild from frozen sources;
- validation that interactive controls cannot mutate the primary specification;
- validation that no unauthorized result enters manuscript-facing prose.

### 12.2 Independent numerical checks

- reconstruct at least one primary OLS design matrix independently;
- verify coefficient estimates and HC3 covariance independently;
- manually reconstruct the C1 joint contrast and full covariance expression;
- reproduce Moran's I using frozen residuals, weights, seed, and permutations;
- verify spatial-error convergence and diagnostics when escalation occurs;
- reconcile every final display value to the result ledger.

### 12.3 Completion criteria

Implementation is complete only when:

1. all seven notebook sections execute in the approved order;
2. source roles and measure semantics remain visible and correct;
3. adjusted C1/C2 models either execute with all gates passed or fail closed with documented
   reasons;
4. alpha, beta, gamma, primary contrasts, uncertainty, and adjustment language are generated
   from one typed result source;
5. the five main-display candidates and supplement outputs are deterministic and traceable;
6. two clean runs produce identical checksums;
7. automated and independent numerical reviews pass;
8. authorization status remains false until the governed S7 decision changes it;
9. the live JAMA Health Forum instructions are rechecked before any compliance claim;
10. a subject-matter author reviews every empirical sentence, number, citation, and disclosure.

## 13. Planned implementation boundaries

This specification authorizes planning, not immediate result publication. The implementation
plan must use test-driven development, preserve the untracked `Downloads/` and `tmp/`
directories, and keep analysis logic outside notebook-only cells. It must identify exact files,
tests, package documentation to verify through Ref MCP, Paperclip/PubMed evidence tasks, and
the S7 independent-review handoff.

No substantive model result or manuscript claim is approved by this design document.
