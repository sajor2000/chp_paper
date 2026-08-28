# Chicago Health Map Geographic-Resolution Manuscript Outline

**Status:** author-facing planning aid; not a controlling SAP or authorization to draft empirical Results.

The controlling document is `docs/analysis/statistical_analysis_plan.md`. The proposed primary
geographic-resolution aim is documented in
`docs/analysis/descriptive_complementarity_analysis_addendum_draft.md`. The signed SAP remains
controlling until that amendment is approved. `results_authorized=false` is binding.

## Front matter

- Nondeclarative title, Key Points, and structured abstract remain shells until independent S7
  review authorizes Results prose.
- Keep the main text within the current JAMA Health Forum word and display limits only after a
  live Instructions for Authors check at submission.

## Word planning envelopes

These planning envelopes total 2900 words and reserve 100 words for final edits; the manuscript
must be edited to <=2900 words before submission. Introduction: 250-300 words. Methods:
850-950 words. Results: 700-800 words. Discussion: 850-950 words.

## Introduction

1. Begin with the complementary evidence problem. Population-based public health data support
   population inference, while health-system EHR data can add a selected clinical lens at tract
   scale.
2. Introduce ChicagoHealthMap.com as a multi-institution EHR resource that combines tract-level
   diagnosed-condition measures with capture, suppression, and provenance metadata.
3. State the boundary: diagnosed proportions among observed adults are neither population
   prevalence nor a gold-standard comparator and cannot replace public health surveillance.
4. State the novelty as a testable question: whether the tract layer retains geographic
   information not retained by linked direct community-area or ZCTA classifications.
5. Keep CHM-PLACES alignment secondary because it evaluates cross-source ordering, not the added
   value of tract resolution.

## Methods

1. Describe the direct CHM/CAPriCORN condition streams, period, direct geography, and source
   status handling.
2. Describe the direct tract-to-community-area linkage and prohibit interpolation or polygon
   aggregation of CHM disease values.
3. State that the primary 2022–2024 tract ranks use pooled eligible numerators divided by pooled
   denominators; unweighted annual means are labeled sensitivity analyses.
4. Define exact tract/community quartile agreement, disagreement, within-community variance
   share, and Q4 movement as the primary descriptive estimands.
5. Define the ZCTA comparison, annual and noncrossing analyses, VPC, area-label AUC, and
   CHM-PLACES agreement as sensitivity or secondary estimands.
6. Keep combined diabetes explicitly not run until mutual exclusivity and denominator equivalence
   are approved.

## Results and Discussion

The statistician-review notebook shows provisional aggregate results, but manuscript and coauthor
handoffs remain nonnumeric pending independent S7 review. The eventual Results must begin with the
direct tract/community estimands and their exact denominators. The Discussion should state that
the scientific contribution is evidence of retained geographic information, not the novelty of a
website or proof of clinical validity. It should define the source roles directly: population-based
sources remain the basis for population inference, while health-system data may supplement them by
showing within-area clinical variation. It must prioritize EHR selection, cross-frame,
construct/period, reliability/suppression, and uncertainty limitations.

## Five main displays

1. **Table 1:** Chicago Health Map community-area data coverage, 2019–2024.
2. **Figure 1:** Chicago Health Map geographic coverage and data quality.
3. **Figure 2:** Added geographic information from tract-level measures, with direct
   tract/community comparisons above secondary CHM-PLACES comparisons.
4. **Figure 3:** Direct cross-frame classification differences and stability.
5. **Table 2:** Geographic alignment and direct cross-frame classification differences by condition.

## Supplementary displays

- Source flow, annual resource-quality checks, geographic-resolution sensitivity, concordance,
  uncertainty status, and spatial diagnostic displays support the proposed primary geography aim.
- Cardiometabolic and COPD model coefficients, gates, residuals, influence, temporal, and spatial
  diagnostics are QC-only model artifacts. They are not part of the five main displays.
- `table_2_model_readiness_sensitivities.*` is retained as a compatibility alias for the
  geographic Table 2; `etable_2_model_readiness_sensitivities.*` is the model-QC table.
