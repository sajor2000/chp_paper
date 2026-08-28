# Chicago Health Map Complementarity Evidence Ledger

This ledger is the audit trail for each display and support artifact. It records source artifact,
denominator, unit, period, uncertainty, analysis status, and authorization for each governed
entry. The implementation is an ecological, cross-sectional/repeated-period analysis and resource
evaluation. Its proposed primary claim is that direct CHM tract measures may retain geographic
information beyond direct community-area labels. ZCTA comparisons test dependence on the choice of
coarse geography. Public comparators and community-area life-expectancy summaries are secondary.
The analysis does not claim predictive superiority, validation, prevalence, causality, or service
need.

`results_authorized=false` remains binding. The geographic-resolution aim is proposed and
noncontrolling unless its SAP amendment is signed. Values and numeric evidence are
retained for audit and independent S7 review only; no row below authorizes Results/Abstract/Key
Points/Discussion prose.

| claim | source artifact | denominator | unit | period | uncertainty | analysis status | authorization | permitted language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CHM coverage and diagnosed-condition availability | `table_1_resource_quality.csv`; `etable_1_resource_quality.csv` | geographic-condition-year observations | counts, percentages, percentage points | 2019-2024; 2022-2024 primary pool | descriptive denominators and percentages | verified descriptive artifact | `results_authorized=false` | CHM coverage and data fitness; not unique patients |
| Atlas life-expectancy summaries | frozen Chicago Health Atlas snapshot; primary frame | eligible Chicago community areas | years | aligned 2022-2024 | producer estimate metadata | verified outcome artifact | `results_authorized=false` | area life-expectancy summaries |
| Cardiometabolic model gate | `supplement_model_gate_diagnostics.csv`; `etable_2_model_readiness_sensitivities.csv` | 0 approved C1 areas | explicit not-run status | aligned 2022-2024 | not applicable | `not_run_combined_diabetes_semantics_unapproved` | `results_authorized=false` | no coefficient, CI, influence, or residual result |
| C1 diagnostics | `supplement_full_coefficient_table.csv`; `supplement_adjusted_diagnostic_data.csv`; `supplement_spatial_diagnostics.csv` | no approved C1 analytic population | not run | aligned 2022-2024 | not applicable | `not_run_combined_diabetes_semantics_unapproved` | `results_authorized=false` | no fitted C1 diagnostic |
| COPD model gate and candidate | `supplement_model_gate_diagnostics.csv`; `etable_2_model_readiness_sensitivities.csv`; `manuscript_results_handoff.json` | 76 COPD-eligible community areas | life-expectancy years per frozen-IQR CHM COPD proportion | aligned 2022-2024 | HC3 covariance; 97.5% CI | `freeze_candidate_primary_model_unsecured` | `results_authorized=false` | candidate association pending human S7 |
| C2 adjusted diagnostics | `supplement_adjusted_diagnostic_data.csv`; `supplement_spatial_diagnostics.csv`; `supplement_spatial_error_sensitivity.csv` | C2 eligible areas and topology-specific subsets | residual, leverage, Moran, spatial-error sensitivity | aligned 2022-2024 | HC3 and 9999 conditional permutations | audit/diagnostic sensitivity | `results_authorized=false` | supportive diagnostic only |
| Robustness variants | `supplement_robustness_summary.csv`; `supplement_temporal_models.csv`; `supplement_leave_one_year_out.csv`; `supplement_disruption_audit.csv`; `supplement_influence_c1.csv`; `supplement_influence_c2.csv` | model-specific eligible areas or exact paired annual subsets | estimate direction, percentage change, CI status | 2019-2024; 2022-2024 primary | 95%/97.5% intervals and fragility flags | governed audit robustness | `results_authorized=false` | direction/fragility audit only |
| Alternative spatial topology | `supplement_alternative_spatial_weights.csv`; `supplement_spatial_error_sensitivity.csv` | eligible C2 topology-specific areas | topology, Moran, spatial-error estimate | aligned 2022-2024 | topology checksum; 9999 permutations; conditional CI | governed spatial sensitivity | `results_authorized=false` | spatial-dependence diagnostic |
| Tract complementarity and measurement discordance | `supplement_tract_complementarity.csv`; `supplement_concordance_summary.csv`; `supplement_discordance_quartile.csv`; `supplement_discordance_tertile.csv`; `supplement_multiplicity_inventory.csv` | pairwise-complete eligible tracts by condition | percentile rank gap, correlation, kappa, percentage-point difference | contemporary 2022-2024 tract period | rank-bin definitions; BH family metadata | `descriptive_measurement_discordance` | `results_authorized=false` | complementary descriptive triangulation; no gold standard |
| Within-community heterogeneity | `supplement_within_community_heterogeneity.csv` | eligible tracts nested within community areas | median rank, IQR, range, quartile shares | contemporary 2022-2024 | cluster/area denominators and explicit crossing rule | proposed primary descriptive evidence | `results_authorized=false` | retained tract information, not clinical correctness |
| Cluster bootstrap | `supplement_concordance_bootstrap.csv` | community-area clusters, not tracts | rank concordance and discordance summary | denominator-pooled 2022-2024 | seed `20260715`; 1000 requested replicates; 2.5th and 97.5th percentiles | seeded audit uncertainty | `results_authorized=false` | within-area dependence diagnostic; not complete spatial correction |
| Direct cross-frame classification differences | `supplement_geographic_consequence_transitions.csv`; `supplement_geographic_consequence_stability.csv`; `etable_8_geographic_consequences.csv` | eligible tracts and mean annual condition-record source denominators | highest-quartile transitions, mixed-extreme areas, annual Jaccard | 2022-2024 | descriptive annual and noncrossing sensitivity | direct community-area and direct ZCTA comparison | `results_authorized=false` | direct cross-frame comparison only; ZCTAs are not USPS ZIP Codes |
| Uncertainty-aware agreement | `etable_9_uncertainty_feasibility.csv` | pairwise-complete eligible tracts | comparator-rank discordance probability | contemporary 2022-2024 | 1000 seeded PLACES interval draws | PLACES-only available; joint denominator uncertainty not run | `results_authorized=false` | uncertainty in PLACES ranks only; no validation claim |
| FDR-controlled spatial classifications | `supplement_fdr_spatial_survival.csv` | 77 community areas per condition | raw and BH-FDR surviving local classifications | pooled 2022-2024 | 9999 seeded permutations within condition-period-statistic family | community-area diagnostic | `results_authorized=false` | local spatial pattern diagnostic; tract-level scan not inferred |
| Compact displays and legends | `table_1_resource_quality.html`; `table_2_geographic_resolution.html`; `figure_1_data_flow_coverage.png`; `figure_2_cardiometabolic_patterns.png`; `figure_3_copd_patterns.png`; `figure_legends.json` | display-specific denominators shown in captions and notes | counts, percentage points, years, rank summaries | 2019-2024 and 2022-2024 descriptive rank period | explicit suppression/missing states and display notes | proposed main presentation artifacts | `results_authorized=false` | aggregate evidence for independent review |

## Governed artifact inventory

The following names are the exact notebook output inventory. Each remains provenance-bound to the
input snapshot, SAP, code commit, lockfile, and authorization manifest; generated local outputs are
not tracked in Git.

| artifact | role | denominator | unit | period | uncertainty | analysis status | authorization |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `table_1_resource_quality.csv` | compact Table 1 | community-area-condition-year observations | counts and percentages | 2019-2024 | descriptive | descriptive artifact; not a patient table | `results_authorized=false` |
| `table_1_resource_quality.html` | rendered Table 1 | source rows/geography-period-condition rows | counts and percentages | 2019-2024 | display notes | presentation artifact | `results_authorized=false` |
| `etable_1_resource_quality.csv` | full eTable 1 QA | source rows/geography-period-condition rows | QA fields | 2019-2024 | missing/suppression fields | audit artifact | `results_authorized=false` |
| `etable_1_resource_quality.html` | rendered eTable 1 | source rows/geography-period-condition rows | QA fields | 2019-2024 | display notes | presentation artifact | `results_authorized=false` |
| `table_2_geographic_resolution.csv` | compact geographic Table 2 | complete 2022-2024 tract/community cohort with dominant link at least 0.99 | exact agreement, disagreement, within-community variance share, and Q4 movement | denominator-pooled 2022-2024 | metric-specific denominators and explicit not-run state | proposed primary display artifact | `results_authorized=false` |
| `table_2_geographic_resolution.html` | rendered geographic Table 2 | metric-specific eligible tract frames | rank agreement and quartile classification metrics | 2022-2024 descriptive rank period | display notes | presentation artifact | `results_authorized=false` |
| `table_2_model_readiness_sensitivities.csv` | compatibility alias for geographic Table 2 | same as `table_2_geographic_resolution.csv` | same as geographic Table 2 | 2022-2024 descriptive rank period | same as geographic Table 2 | compatibility artifact; not a model table | `results_authorized=false` |
| `table_2_model_readiness_sensitivities.html` | compatibility alias for rendered geographic Table 2 | same as `table_2_geographic_resolution.html` | same as geographic Table 2 | 2022-2024 descriptive rank period | display notes | compatibility artifact; not a model table | `results_authorized=false` |
| `manuscript_results_handoff.json` | governed handoff | artifact-specific | structured result metadata | aligned 2022-2024 | per-result authorization | handoff audit artifact | `results_authorized=false` |
| `figure_legends.json` | legend contract | figure-specific | units and role labels | aligned 2022-2024 | legend qualification notes | legend artifact | `results_authorized=false` |
| `supplement_full_coefficient_table.csv` | alpha/beta/gamma eTable | C2 model-specific areas; C1 not run | coefficient years | aligned 2022-2024 | HC3 CI for C2 | C1 not run/C2 candidate | `results_authorized=false` |
| `supplement_full_coefficient_table.html` | rendered coefficient eTable | model-specific areas | coefficient years | aligned 2022-2024 | display notes | presentation artifact | `results_authorized=false` |
| `supplement_model_gate_diagnostics.csv` | readiness gate | model-specific areas | eligibility, VIF, rank, HC3, status | aligned 2022-2024 | threshold and gate diagnostics where estimable | C1 not run/C2 candidate | `results_authorized=false` |
| `figure_1_data_flow_coverage.png` | resource/map figure | 77 community areas and source rows | counts and percentage points | 2019-2024; primary 2022-2024 | missing/suppression encodings | descriptive display | `results_authorized=false` |
| `figure_2_cardiometabolic_patterns.png` | geographic-resolution figure | eligible tracts and linked community areas | quartile transitions and percentile ranks | aligned 2022-2024 | display qualifications | proposed primary geography display with secondary comparator panels | `results_authorized=false` |
| `figure_3_copd_patterns.png` | C2/comparator figure | eligible tracts and community areas | percentages and rank gaps | aligned 2022-2024 | display qualifications | C2 candidate display | `results_authorized=false` |
| `supplement_coefficient_forest.pdf` | eFigure 1 C2 coefficient forest | 76 C2-eligible areas | coefficient years | aligned 2022-2024 | HC3 97.5% CI for exposure and adjustment terms, labeled per term | C2 candidate audit | `results_authorized=false` |
| `supplement_model_diagnostics.pdf` | eFigure 2 diagnostics and robustness | model/sensitivity-specific areas | residual, influence, Moran, and estimate scales | 2019-2024; primary 2022-2024 | diagnostic and sensitivity-specific | supportive audit | `results_authorized=false` |
| `supplement_temporal_models.csv` | annual temporal checks | exact paired annual subsets | years per frozen-IQR contrast | 2019-2024 | CI and eligibility fields | robustness audit | `results_authorized=false` |
| `supplement_leave_one_year_out.csv` | primary-period year omission | exact paired primary subsets | years per frozen-IQR contrast | 2022-2024 | CI and direction stability | robustness audit | `results_authorized=false` |
| `supplement_disruption_audit.csv` | disruption sensitivity | flagged-area and paired subsets | years per frozen-IQR contrast | 2020-2024 | CI and fragility | robustness audit | `results_authorized=false` |
| `supplement_influence_c1.csv` | C1 influence status | no approved C1 areas | explicit not-run row | aligned 2022-2024 | not applicable | combined-diabetes semantics unapproved | `results_authorized=false` |
| `supplement_influence_c2.csv` | C2 influence diagnostics | C2 eligible areas | Cook, leverage, leave-one-out | aligned 2022-2024 | fragility thresholds | C2 candidate audit | `results_authorized=false` |
| `supplement_spatial_diagnostics.csv` | queen Moran diagnostics | model-specific topology | Moran statistic | aligned 2022-2024 | 9999 permutations; seed | spatial audit | `results_authorized=false` |
| `supplement_spatial_error_sensitivity.csv` | conditional spatial-error checks | gate-crossing model/topology | spatial-error coefficient | aligned 2022-2024 | conditional CI and convergence | spatial sensitivity | `results_authorized=false` |
| `supplement_robustness_summary.csv` | governed robustness family | exact model/sensitivity subsets | estimates and percentage change | 2019-2024; primary 2022-2024 | CI overlap and fragility | robustness audit | `results_authorized=false` |
| `supplement_alternative_spatial_weights.csv` | rook/distance topology | eligible C2 topology | edges, checksum, Moran | aligned 2022-2024 | topology checksum and permutations | alternative spatial topology | `results_authorized=false` |
| `supplement_adjusted_diagnostic_data.csv` | adjusted diagnostic rows | model-specific areas | fitted/residual/leverage metrics | aligned 2022-2024 | HC3 diagnostic metadata | audit/diagnostic | `results_authorized=false` |
| `supplement_concordance_summary.csv` | tract concordance summary | pairwise-complete tracts | rank correlation/kappa/gaps | contemporary 2022-2024 | supportive intervals | descriptive triangulation | `results_authorized=false` |
| `supplement_discordance_quartile.csv` | quartile discordance | pairwise-complete tracts | rank-gap categories | contemporary 2022-2024 | category denominators | descriptive triangulation | `results_authorized=false` |
| `supplement_discordance_tertile.csv` | tertile sensitivity | pairwise-complete tracts | rank-gap categories | contemporary 2022-2024 | category denominators | descriptive triangulation | `results_authorized=false` |
| `supplement_multiplicity_inventory.csv` | comparator test family | named tract comparator tests | raw/BH-adjusted P values | contemporary 2022-2024 | BH denominator | multiplicity audit | `results_authorized=false` |
| `supplement_tract_complementarity.csv` | direct/public tract lens | eligible tracts by condition | percentile ranks and gaps | contemporary 2022-2024 | common-set cut points | `descriptive_measurement_discordance` | `results_authorized=false` |
| `supplement_within_community_heterogeneity.csv` | within-area distribution | tracts nested in community areas | IQR, range, quartile shares | contemporary 2022-2024 | cluster denominators | heterogeneity audit | `results_authorized=false` |
| `supplement_concordance_bootstrap.csv` | area-cluster bootstrap | community-area clusters | concordance summary | contemporary 2022-2024 | seed `20260715`; replicate count | bootstrap audit | `results_authorized=false` |
| `chicago_healthmap_zcta_sidecar.parquet` | direct ZCTA sensitivity sidecar | direct ZCTA-period-condition rows | CHM EHR-diagnosed proportion | 2019-2024 | source suppression retained | comparison-only; outside primary dataset | `results_authorized=false` |
| `supplement_geographic_consequence_transitions.csv` | highest-quartile transitions | eligible tracts | tract counts and mean annual source denominators | 2022-2024 | all-tract and noncrossing sensitivity | community-area and ZCTA comparison | `results_authorized=false` |
| `supplement_geographic_consequence_stability.csv` | annual classification stability | eligible annual tracts | Jaccard and 2-of-3 persistence | 2022-2024 | annual sensitivity | descriptive stability audit | `results_authorized=false` |
| `etable_8_geographic_consequences.html` | rendered direct cross-frame classifications | eligible tracts | classification counts | 2022-2024 | display notes | exploratory supplement | `results_authorized=false` |
| `etable_9_uncertainty_feasibility.html` | rendered uncertainty audit | pairwise-complete tracts | discordance probability | contemporary 2022-2024 | PLACES-only Monte Carlo | joint uncertainty explicitly not run | `results_authorized=false` |
| `supplement_fdr_spatial_survival.csv` | local spatial multiplicity audit | 77 community areas | raw and FDR-surviving counts | pooled 2022-2024 | 9999 seeded permutations | community-area diagnostic | `results_authorized=false` |

## Measure boundary

The published label is “EHR-diagnosed proportion among observed CAPriCORN adults.” CHM values
describe the clinical ascertainment lens available in participating systems and do not represent
the full community population, individual risk, or a population-wide disease estimate. The
analysis is ecological and noncausal. It does not establish underdiagnosis, unmet need, access
barriers, care quality, service failure, optimal allocation, or intervention benefit.

## Provenance and authorization boundary

CHM is the direct first-party exposure source; Chicago Health Atlas and PLACES are secondary public
comparators/outcome context. Neither source is a gold standard. Every artifact names its source
snapshot, denominator, unit, period, uncertainty, status, and authorization. The manifest and
`config/manuscript/results_authorization.json` preserve `results_authorized=false`; human S7
authorization and the live JAMA instruction check remain open.
