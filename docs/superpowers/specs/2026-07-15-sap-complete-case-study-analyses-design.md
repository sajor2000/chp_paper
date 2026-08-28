# SAP-Complete Chicago Case-Study Analyses Design

Date: 2026-07-15

## Objective

Extend the frozen Chicago case-study dataset and combined marimo notebook into a
human-auditable execution of every statistical analysis plan (SAP) requirement that
the frozen fields can support. When a prespecified analysis cannot be supported, the
pipeline must emit a machine-readable withholding decision rather than silently
substituting a different estimand or deriving unapproved values.

## Governing decisions

- The ChicagoHealthMap/CAPriCORN export remains the sole source of disease numerators,
  denominators, and published disease measures.
- Direct observations for all 77 community areas are the primary frame. Direct tract
  observations remain a sensitivity/concordance frame.
- The tract-community overlay supplies membership metadata only. It never creates a
  disease value and will not be used to manufacture community-area ACS covariates.
- Counts suppressed under the source rule are preserved locally but excluded from any
  calculation that requires a known disease count or value.
- Source proportions are converted to percentage points only through an explicit,
  tested `100 * value` transformation with units recorded in the output.
- Results prose remains blocked because `results_authorized=false` until independent
  S7 numerical review and freeze.

## Current defects and limitations

The existing tract concordance code labels source proportions as percentages without
multiplying by 100, so median difference summaries are off by a factor of 100 and can
have the wrong direction. The existing frames also include suppressed disease values.
The current notebook fits three unadjusted single-exposure models, whereas the signed
SAP requires joint/conditional IQR-scaled contrasts, HC3 confidence intervals,
withholding rules, spatial diagnostics, influence checks, temporal and concordance
sensitivities, multiplicity bookkeeping, and governed tables/figures.

The frozen dataset contains no approved community-area values for percentage aged 65
years or older, percentage female, percentage below the federal poverty level, or ACS
adult population. Area-weighting tract ACS counts through polygon-intersection shares
would change their meaning and is not an approved SAP transformation. Therefore the
fully adjusted primary C1/C2 estimands must be marked `withheld_missing_covariates`
until a separately governed direct or population-weighted community-area covariate
source is frozen. Supported unadjusted or capture-only models are sensitivity/descriptive
outputs and may not be presented as the adjusted primary estimands.

## Architecture

`dataset.py` continues to build the source-faithful long-form dataset and its lineage.
`case_studies.py` owns suppression-aware analytic frames and concordance metrics.
`sap_analyses.py` will own resource, temporal, model-readiness, HC3 contrast,
multiplicity, influence, and sensitivity outputs. `spatial.py` will build deterministic
queen weights from official community-area WKT and calculate seeded permutation Moran
diagnostics with a weights checksum. The marimo notebook remains a thin presentation
layer that calls these tested modules, writes local untracked artifacts, and pairs every
analytic cell with Markdown describing purpose, method, rationale, and audit role.

## Statistical behavior

Community exposures use denominator-weighted 2022-2024 sums after excluding any annual
row with a suppressed disease count. Combined diabetes uses the two source-published
components and treats an area-year as unavailable if either component is suppressed or
missing. Life expectancy is the arithmetic mean of complete annual 2022-2024 values.

The model engine first evaluates SAP gates: 70 complete areas, at least 10 distinct
exposure values, full rank, estimable covariance, and availability of the frozen
adjustment set. If adjusted covariates are absent, it emits an exact withholding record.
It may still calculate labeled minimally adjusted sensitivity estimates, including the
joint cardiometabolic covariance contrast, one-IQR conditional contrasts, COPD one-IQR
contrast, HC3 intervals, influence flags, and leave-one-area-out ranges. Primary-family
intervals use 97.5%; secondary conditional intervals use 95%.

Tract concordance uses combined diabetes components, excludes suppressed/incomplete
area-years, reports Spearman primary and Pearson supportive correlations, comparable-unit
median signed/absolute differences, quartile cross-tabs, weighted kappa, fixed
discordance categories, and tertile sensitivity. Formal multi-test families receive
Benjamini-Hochberg adjusted P values without changing the prespecified priority labels.

Spatial diagnostics use official community-area polygons, row-standardized queen
contiguity, a fixed seed, 9999 conditional permutations, and a SHA-256 checksum of the
ordered neighbor matrix. Islands and invalid polygons fail closed. Because the adjusted
primary model is withheld, any Moran diagnostic on a minimally adjusted sensitivity is
explicitly labeled supportive and cannot trigger a claim that the adjusted primary
estimand was executed.

## Outputs

The notebook will regenerate:

- Table 1 resource/eligibility/suppression/reliability/capture summaries;
- Figure 1 data flow and reliability-qualified community-area coverage;
- Figure 2 cardiometabolic patterns and tract comparator concordance;
- Figure 3 COPD patterns and tract comparator concordance;
- Table 2 primary-estimand readiness/withholding plus labeled supported sensitivities;
- supplementary flow, temporal, discordance, spatial, influence, multiplicity, and
  sensitivity CSV/HTML/PNG artifacts;
- a run manifest with input/output checksums, code/SAP identifiers, random seed,
  environment lock hash, run time zone, and `results_authorized=false`.

## Error handling and verification

Analysis helpers raise `CaseStudyAnalysisError` for missing columns, duplicate keys,
unit ambiguity, invalid geometry, islands, or unusable analytic populations. Every
behavioral change follows red-green-refactor TDD. Verification includes focused tests,
the full suite, Ruff lint/format, mypy, frozen dataset rebuild and checksum audit,
top-to-bottom notebook execution, marimo check, the documented WASM audit, cell-length
audit, `git diff --check`, independent scoped reviews, and final whole-branch review.

## Deferred source expansion

Freezing direct community-area demographic covariates from an authoritative public
source is a separate governed source-acquisition task. When completed, it can change
the primary adjusted estimands from withheld to executable without changing disease
values or reusing tract overlay weights as disease or population interpolation.
