import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full")


@app.cell
def _():
    from dataclasses import asdict
    from hashlib import sha256
    import json
    from pathlib import Path
    import subprocess

    import marimo as mo
    import pandas as pd
    from matplotlib import pyplot as plt
    from matplotlib import image as mpimg
    from pydantic import BaseModel, Field
    from chicagohealthmap.quality.views import load_quality_checkpoint, schema_evidence_view

    return (
        BaseModel,
        Field,
        Path,
        asdict,
        json,
        load_quality_checkpoint,
        mo,
        mpimg,
        pd,
        plt,
        schema_evidence_view,
        sha256,
        subprocess,
    )


@app.cell
def _():
    from datetime import datetime, timezone

    return datetime, timezone


@app.cell
def _():
    from chicagohealthmap.analysis.dataset import (
        ensure_chicago_case_study_dataset,
        ensure_zcta_sidecar_dataset,
    )

    return ensure_chicago_case_study_dataset, ensure_zcta_sidecar_dataset


@app.cell
def _():
    from chicagohealthmap.analysis.case_studies import (
        build_primary_community_frame,
        build_tract_cohort_flow,
        build_tract_concordance_frame,
        classify_discordance,
        load_analytic_dataset,
        summarize_concordance,
        summarize_resource_quality,
    )

    return (
        build_primary_community_frame,
        build_tract_cohort_flow,
        build_tract_concordance_frame,
        classify_discordance,
        load_analytic_dataset,
        summarize_concordance,
        summarize_resource_quality,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.tract_complementarity import (
        BOOTSTRAP_SEED,
        build_direct_ehr_rank_frame,
        build_direct_tract_analysis_frame,
        build_tract_percentile_concordance,
        cluster_bootstrap_concordance,
        compute_discriminatory_accuracy,
        compute_variance_partition,
        propagate_uncertainty_discordance,
        summarize_community_area_aggregation_loss,
        summarize_concordance_metrics,
        summarize_within_community_heterogeneity,
    )

    return (
        BOOTSTRAP_SEED,
        build_direct_ehr_rank_frame,
        build_direct_tract_analysis_frame,
        build_tract_percentile_concordance,
        cluster_bootstrap_concordance,
        compute_discriminatory_accuracy,
        compute_variance_partition,
        propagate_uncertainty_discordance,
        summarize_community_area_aggregation_loss,
        summarize_concordance_metrics,
        summarize_within_community_heterogeneity,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.tract_complementarity import (
        build_annual_direct_consequence_rank_frame,
        build_direct_consequence_rank_frame,
        build_geographic_consequence_tables,
        summarize_annual_consequence_stability,
    )
    from chicagohealthmap.external.geography import load_zcta_tract_relationship

    return (
        build_annual_direct_consequence_rank_frame,
        build_direct_consequence_rank_frame,
        build_geographic_consequence_tables,
        load_zcta_tract_relationship,
        summarize_annual_consequence_stability,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.paper_audit import (
        build_claim_evidence_audit,
        build_data_quality_audit,
        build_descriptive_claim_evidence_audit,
        build_geographic_resolution_matrix,
        build_master_claim_records,
    )

    return (
        build_claim_evidence_audit,
        build_data_quality_audit,
        build_descriptive_claim_evidence_audit,
        build_geographic_resolution_matrix,
        build_master_claim_records,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.paper_displays import (
        build_compact_table_1,
        build_compact_table_2,
        build_geographic_consequence_display_data,
        build_geographic_main_evidence,
        build_flow_summary,
        build_resolution_heatmap_data,
        confidence_interval_label,
        draw_map_panel,
        reader_analysis_name,
    )

    return (
        build_compact_table_1,
        build_compact_table_2,
        build_flow_summary,
        build_geographic_consequence_display_data,
        build_geographic_main_evidence,
        build_resolution_heatmap_data,
        confidence_interval_label,
        draw_map_panel,
        reader_analysis_name,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.sap_analyses import (
        assess_primary_model_readiness,
        build_adjusted_residuals,
        build_coefficient_table,
        build_model_gate_diagnostics,
        fit_audit_only_exploratory_models,
        fit_primary_models,
        fit_minimally_adjusted_sensitivities,
        summarize_influence,
        summarize_temporal_robustness,
    )

    return (
        assess_primary_model_readiness,
        build_adjusted_residuals,
        build_coefficient_table,
        build_model_gate_diagnostics,
        fit_audit_only_exploratory_models,
        fit_minimally_adjusted_sensitivities,
        fit_primary_models,
        summarize_influence,
        summarize_temporal_robustness,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.robustness import (
        build_adjusted_diagnostic_data,
        build_adjusted_temporal_robustness,
        build_governed_robustness_summary,
        capture_quartile_cut_points,
    )

    return (
        build_adjusted_diagnostic_data,
        build_adjusted_temporal_robustness,
        build_governed_robustness_summary,
        capture_quartile_cut_points,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.spatial import (
        build_rook_weights,
        build_smallest_connected_distance_weights,
        build_spatial_error_sensitivity_table,
        build_topology_summary,
        build_queen_weights,
        compute_local_spatial_diagnostics,
        evaluate_spatial_scan_feasibility,
        permutation_moran,
        summarize_fdr_spatial_survival,
    )

    return (
        build_queen_weights,
        build_rook_weights,
        build_smallest_connected_distance_weights,
        build_spatial_error_sensitivity_table,
        build_topology_summary,
        compute_local_spatial_diagnostics,
        evaluate_spatial_scan_feasibility,
        permutation_moran,
        summarize_fdr_spatial_survival,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.reporting import (
        build_editorial_display_manifest,
        build_blocked_word_handoff,
        build_great_table,
        build_main_display_reader_cards,
        build_main_display_reader_guide,
        build_manuscript_results_handoff,
        build_supplement_registry,
        figure_accessibility_passes,
        parse_results_authorization,
        render_styled_html,
    )

    return (
        build_blocked_word_handoff,
        build_editorial_display_manifest,
        build_great_table,
        build_main_display_reader_cards,
        build_main_display_reader_guide,
        build_manuscript_results_handoff,
        build_supplement_registry,
        figure_accessibility_passes,
        parse_results_authorization,
        render_styled_html,
    )


@app.cell
def _():
    import geopandas as gpd

    return (gpd,)


@app.cell
def _(BaseModel, Field):
    class NotebookParams(BaseModel):
        rebuild: bool = Field(
            default=False,
            description="Deliberately rebuild the master dataset even when checksums match.",
        )
        output_dir: str = Field(
            default="outputs/notebooks/chicago_healthmap_master",
            description="Local untracked output directory inside the repository.",
        )

    return (NotebookParams,)


@app.cell
def _(NotebookParams, mo):
    controls = (
        mo.md("{output_dir}\n{rebuild}")
        .batch(
            output_dir=mo.ui.text(value=NotebookParams.model_fields["output_dir"].default),
            rebuild=mo.ui.checkbox(
                value=NotebookParams.model_fields["rebuild"].default,
                label="Rebuild governed analytic dataset",
            ),
        )
        .form()
    )
    return (controls,)


@app.cell
def _(NotebookParams, controls, mo):
    cli_values = {key.replace("-", "_"): value for key, value in mo.cli_args().items()}
    params = (
        NotebookParams(**cli_values)
        if mo.app_meta().mode == "script"
        else NotebookParams(**(controls.value or {}))
    )
    return (params,)


@app.cell
def _(Path):
    def resolve_inside(root: Path, value: str) -> Path:
        candidate = (root / value).resolve()
        if not candidate.is_relative_to(root):
            raise ValueError("notebook paths must stay inside the repository")
        return candidate

    return (resolve_inside,)


@app.cell
def _(Path, json, params, parse_results_authorization, resolve_inside):
    project_root = Path(__file__).resolve().parents[1]
    output_dir = resolve_inside(project_root, params.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    governance_path = project_root / "config/manuscript/results_authorization.json"
    governance = json.loads(governance_path.read_text(encoding="utf-8"))
    results_authorized = parse_results_authorization(governance)
    seed, permutations = 20260715, 9999
    expected_model_n = {"C1": 0, "C2": 76}
    full_checksum_expected = "f1a9b8ade1bf4ed1258b54f97dd78a8c710dc51cc03350053c99df59b2de7922"
    c2_checksum_expected = "927384844fbace67e43cd79a2aa757420e026cac1a063f7b4968b784c7e417b5"
    return (
        c2_checksum_expected,
        expected_model_n,
        full_checksum_expected,
        governance_path,
        output_dir,
        permutations,
        project_root,
        results_authorized,
        seed,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # Added Geographic Information From Tract-Level Health System Data in Chicago

    ### Statistician methods-review notebook

    ## 1. Introduction

    Population-based surveillance is the basis for inference about the health of Chicago
    residents. Health-system electronic health record (EHR) data answer a different question. They
    describe diagnoses recorded among adults observed in participating health systems. EHR data may
    retain small-area clinical information that is unavailable in common public reporting units,
    but care seeking, system capture, coding, geocoding, suppression, and denominator construction
    determine what those measures mean.<sup>1-5,7</sup>

    This repeated cross-sectional ecological study evaluates a specific supplementary use. It asks
    whether direct Chicago Health Map (CHM) tract measures contain geographic information beyond
    direct CHM community-area labels. The primary evidence is the observed variance among tracts
    within community areas, the absolute difference between tract and linked community-area
    percentile ranks, exact quartile disagreement, and movement into or out of the highest
    quartile. These are direct cross-frame comparisons. They are not estimates of information lost
    by mathematically aggregating tract numerators and denominators.

    A parallel Census ZIP Code Tabulation Area (ZCTA) analysis tests whether results depend on the
    selected coarse geography. CDC PLACES comparisons provide secondary cross-source context.
    Community-area life-expectancy models and spatial analyses are supplementary demonstrations.
    CHM measures refer to observed CAPriCORN adults, not all Chicago residents. No source is a truth
    standard, and no analysis estimates a causal effect. Aggregate results are visible for the
    independent statistician while manuscript authorization remains closed.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Statistician Review Guide

    This notebook is both an executable statistical analysis plan and a draft Original
    Investigation. It records the scientific rationale before the corresponding code, executes the
    prespecified estimator, reports the analytic denominator, displays diagnostics, and states the
    interpretation boundary. A statistician should be able to reconstruct each analysis without
    consulting undocumented helper code.

    Each **Statistical Analysis Module** governs the executable cells that follow it until the next
    module. Every module states 10 items: scientific question, estimand, population and unit,
    variables and denominator, mathematical definition, estimator and uncertainty, assumptions and
    diagnostics, missingness and suppression, sensitivity analyses, and interpretation with
    references.

    `results_authorized=false` is binding. Numerical model and geographic outputs are shown in this
    statistician-review notebook, including its provisional JAMA-style summary. They must not be
    copied into a submission manuscript, final figure legend, or coauthor material until the
    independent reviewer approves the decisions listed below and S7 review is signed.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Notebook order and review workflow

    1. **Paper front matter:** study question, source roles, Key Points, structured abstract, and the
       publication claim.
    2. **Executable SAP:** governed data assembly followed by Statistical Analysis Modules 1 through
       6. Each module precedes the code that implements it.
    3. **Results in display order:** Table 1, Figure 1, Figure 2, Figure 3, and Table 2. Every display
       is followed by a biostatistical interpretation and an explicit limitation.
    4. **Supplementary analyses:** diagnostic, robustness, outcome-model, spatial, and unrun-analysis
       records. These cannot replace the primary geographic evidence.
    5. **Discussion and references:** bounded scientific interpretation, public-health relevance,
       limitations, verified numbered citations, and reporting guidance.
    6. **Reproducibility and authorization:** artifact gallery, checksums, deterministic manifest,
       and the closed manuscript-export gate.

    The order is deliberate. The notebook states each decision before displaying its result, keeps
    CHM-only and cross-source populations separate, and places exploratory analyses after the
    primary estimands.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Scientific question, design, and evidence hierarchy

    The primary study question is whether tract-level EHR-diagnosed proportions add geographic
    information beyond the coarser labels assigned by Chicago community areas. A parallel ZCTA
    analysis tests whether that conclusion depends on the second commonly used coarse geography.
    CHM-PLACES alignment and community-area life-expectancy models provide secondary context. The
    design is ecological, repeated-period, and cross-source. It supports description and
    association, not causal effects.

    The tract-resolution analyses A1 through A7 are a proposed primary-aim amendment recorded in
    the implementation addendum. They remain a proposed methods amendment until the statistician and authors
    sign the amendment and S7 review is complete. Operational source checks are quality control
    only. No public source is a validation standard or gold standard.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Analysis hierarchy and review status

    | Family | Unit and population | Estimand or purpose | Current status |
    |---|---|---|---|
    | Resource audit | geography-condition-year records | availability, suppression, missingness, capture | descriptive QC |
    | Within-community tract variation | CHM-complete 2022-2024 tracts with dominant links | observed within-area variance share | proposed primary A1 |
    | Direct tract vs community-area labels | CHM-complete 2022-2024 tracts with dominant links | absolute rank gap, exact quartile disagreement, Q4 movement | proposed primary A6 |
    | Direct tract vs ZCTA labels | complete 2022-2024 tracts with dominant ZCTA links | same classification metrics under a second coarse geography | sensitivity A6 |
    | CHM-PLACES alignment | pairwise-complete eligible tracts | rank alignment and ordinal agreement | secondary A3-A5 |
    | Area-label separation | CHM-complete tracts in areas with at least 2 tracts | leave-one-tract-out AUC | exploratory A2 |
    | Local spatial structure | eligible community areas with complete topology | local Moran I, bivariate local Moran I, and Getis-Ord Gi* | supplementary A7 |
    | C1/C2 outcome models | eligible community areas | ecological life-expectancy contrasts | supplementary demonstration, unauthorized |
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Complementary source-role framework

    The publication claim concerns complementary evidence roles, not competition between maps.

    | Evidence source | Strongest supported role in this study | Boundary that must remain visible | Appropriate combined use |
    |---|---|---|---|
    | Population-based public health data | estimate and compare health across defined populations | source-specific survey, modeling, period, and geography assumptions | retain as the basis for population inference |
    | Multi-institution health-system EHR data | describe clinically recorded diagnoses among observed adults at tract scale | care contact, system capture, coding, geocoding, suppression, and denominator selection | examine within-area clinical variation and generate follow-up questions |
    | Both sources together | assess whether geographic patterns align or diverge across measurement systems | neither source validates the other | triangulate signals and identify questions for additional public health assessment |

    A divergence is a measurement finding, not evidence that one source is wrong. A tract signal
    may support additional investigation. It does not establish community prevalence, unmet need,
    service location, or intervention benefit.

    #### Editorial readiness gate

    | Item | Current state | Required before submission |
    |---|---|---|
    | Title and Key Points | nondeclarative title and primary geographic results only | confirm after S7 review |
    | Primary uncertainty | community-area cluster intervals shown for review | approve the cluster unit, replicate count, and percentile interval |
    | Reference count | 25 verified references | reach the journal's 50 to 75 range with relevant verified sources, without padding |
    | Ethics and sharing | author placeholders remain | insert the exact IRB, consent or waiver, and data-sharing language |
    | AI-assisted preparation | project ledger exists | complete the journal-required acknowledgment and human verification |
    | Results authorization | `results_authorized=false` | complete the primary-aim amendment and independent S7 review |
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Controlling statistical decision registry for independent sign-off

    This table supersedes earlier exploratory notes. “Primary” identifies evidence intended to
    answer the paper's geographic-resolution question. “Supplementary” means the result may explain
    the data source but cannot carry the main claim.

    | ID | Decision | Review disposition and scientific reason | Required statistician action |
    |---|---|---|---|
    | D1 | Pooled CHM measure | **Keep.** Sum eligible annual numerators and denominators before division. An unweighted mean changes the estimand when denominators differ. | Approve the pooled proportion and annual-mean sensitivity. |
    | D2 | Primary geographic evidence | **Narrow.** Use within-area variance share, absolute percentile-rank gap, exact quartile disagreement, and Q4 movement. Direct tract and community-area exports are compared across frames and are not literal aggregation-loss estimates. | Approve the 4 co-primary descriptive measures and claim language. |
    | D3 | Quartile boundaries | **Change completed.** Q1 is rank at most 0.25, Q2 is greater than 0.25 through 0.50, Q3 is greater than 0.50 through 0.75, and Q4 is greater than 0.75. One function now governs all analyses. | Confirm the boundary and average-tie rule. |
    | D4 | Analysis populations | **Change completed.** A1 and A2 use CHM-complete tracts. CHM-PLACES agreement uses a separate pairwise-complete frame. Missing PLACES data cannot exclude a tract from a CHM-only estimand. | Confirm frame separation and denominator reporting. |
    | D5 | Variance partition | **Keep.** Use an observed-scale one-way method-of-moments estimator. Report the within-area complement. Mixed-model REML is a sensitivity only because the primary estimand is a descriptive partition of tract estimates.<sup>10</sup> | Approve the estimator and whether a REML sensitivity is required. |
    | D6 | Cluster bootstrap | **Change completed.** Resample community areas, retain their tracts, recompute ranks and rank categories within every replicate, and use the 2.5th and 97.5th percentiles.<sup>12</sup> | Approve 1000 replicates for review and whether the final run should use 5000. |
    | D7 | Area-label AUC | **Narrow.** Retain only as an exploratory separation statistic. Recompute the empirical Q4 threshold in every cluster replicate. It is not prediction or external validation.<sup>11</sup> | Approve exploratory retention or remove it. |
    | D8 | Ordinal agreement | **Narrow.** Exact agreement and quadratic weighted kappa are the ordinal summaries. Unweighted Gwet AC1 remains a supplementary nominal sensitivity and is not co-primary.<sup>8,9</sup> | Approve AC1 retention or request weighted AC2. |
    | D9 | Capture and reliability | **Add to interpretation.** Report capture and source reliability strata without treating either as proof of representativeness. The source reliability algorithm remains a semantic sign-off item. | Approve the reliability rule and the primary sensitivity subset. |
    | D10 | HC3 outcome models | **Keep as supplementary.** Use the locked adjustment set and HC3 covariance. Normal and t critical values require an explicit sensitivity comparison because the community-area sample is small.<sup>13</sup> | Select the final critical-value rule. |
    | D11 | Spatial analyses | **Narrow.** Global and local spatial statistics are supplementary. Queen weights are primary, 9999 permutations are used, and false-discovery-rate families are declared before testing.<sup>14-17</sup> | Approve topology, permutation, and multiplicity definitions. |
    | D12 | Combined diabetes | **Do not run.** Mutual exclusivity, denominator equivalence, phenotype mapping, and period alignment are unresolved. | Approve semantics or retain the blocker. |
    | D13 | ZCTA comparison | **Keep as sensitivity.** Use Census ZCTAs and do not describe them as USPS ZIP Codes. | Approve the secondary geography. |
    | D14 | Life expectancy | **Keep as supplementary demonstration.** It illustrates one possible linked use at community-area scale and does not establish validity, causality, or tract-level benefit. | Approve retention outside the primary claim. |
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Manuscript display map

    The main paper uses 5 displays in citation order: Table 1 (CHM community-area coverage),
    Figure 1 (geographic coverage and data quality), Figure 2 (tract alignment and classification
    differences), Figure 3 (direct cross-frame classification differences and stability), and Table 2 (compact
    cross-condition evidence). The notebook renders Tables 1 and 2 as Great Tables HTML and
    exports editable CSV files; it renders Figures 1 through 3 as deterministic PDF and PNG files.
    Model coefficients, residual diagnostics, and unrun analyses remain numbered supplementary
    artifacts so the main narrative does not duplicate or overstate evidence.
    """)
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    ### Provisional JAMA Health Forum Original Investigation

    **Provisional title:** Added Geographic Information From Tract-Level Health System Data in Chicago

    **Article type:** Original Investigation. **Manuscript status:** author-facing scientific
    notebook draft; `results_authorized=false` and no empirical result may be imported into a
    submission manuscript until independent S7 review is complete. Tables and figures below are
    rendered in citation order as editable Great Tables HTML and deterministic vector/raster files.

    ### Key Points

    **Question:** Can tract-level health-system electronic health record (EHR) data add geographic
    information beyond Chicago community-area labels while supplementing population-based public
    health surveillance?

    **Findings:** {review_summary["primary_findings"]}

    **Meaning:** Health-system EHR data may supplement population-based surveillance by showing
    within-area clinical variation, but they should not replace population estimates or directly
    determine services.

    These findings are visible for independent biostatistical review. Manuscript import remains
    closed while `results_authorized=false`.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Structured Abstract

    #### Importance
    Population-based public health data remain essential for community inference. Multi-institution
    electronic health record (EHR) data may add a complementary clinical view at smaller geographic
    scales, but selection into care and health-system capture limit population interpretation.

    #### Objective
    To determine whether direct Chicago Health Map tract measures retain geographic information
    beyond direct community-area labels and to define their potential supplementary role alongside
    public health data. ZIP Code Tabulation Area comparisons and cross-source comparisons were
    secondary.

    #### Design
    Ecological, repeated-period, cross-source descriptive analysis of 2019 through 2024 records.

    #### Setting
    Chicago, Illinois.

    #### Participants
    Geography-condition-period records summarizing source-defined eligible, geocoded adults
    observed in participating CAPriCORN systems. The analytic unit was a geographic record, not an
    individual or encounter.

    #### Exposures
    Direct Chicago Health Map EHR-diagnosed proportions among observed CAPriCORN adults.
    """)
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    #### Main Outcomes and Measures
    Exact tract and community-area quartile agreement, quartile disagreement, within-community
    variance share, and movement into or out of the highest quartile. ZCTA comparisons, annual
    stability, and rank alignment with the Centers for Disease Control and Prevention PLACES data
    were secondary measures.

    #### Results
    {review_summary["resource"]} Patient-level demographic characteristics were not available in
    the aggregate review extract. {review_summary["primary_abstract"]}

    #### Conclusions and Relevance
    Direct community-area labels did not retain all tract heterogeneity and changed some tract
    classifications. Health-system EHR data may supplement population-based surveillance when the
    question concerns within-area clinical variation and capture limitations remain explicit.
    These data should not replace population estimates or be used alone to infer community need,
    direct services, or estimate causal effects.

    **Review status:** Aggregate results are shown for the independent statistician. They remain
    ineligible for manuscript or coauthor import while `results_authorized=false`.

    ### Data Sharing Statement
    [AUTHOR: state whether, how, and under what restrictions analytic code, derived data, and
    governed source data may be accessed.]

    ### Acknowledgment and AI-Assisted Manuscript Preparation
    [AUTHOR: complete the project AI-use disclosure with the platform, model and version or
    `unavailable`, manufacturer, dates of use, manuscript sections affected, human verification,
    and confirmation that the authors take responsibility for all content. The current record is
    maintained in `docs/manuscript/ai_disclosure_template.md`.]
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 2. Methods

    ### Study design and data sources

    We conducted an ecological, repeated-period, cross-source analysis of direct CHM records from
    77 Chicago community areas and 782 census tracts whose 2024 TIGER representative points were
    covered by the frozen Chicago community-area union, 2019 through 2024.
    The primary geographic analyses pooled eligible 2022 through 2024 records. The analytic unit
    was a geography-condition-period record, not a patient or encounter. The notebook builds and
    validates one long-form analytic data set before analysis, then serializes displays, data
    checks, and provenance artifacts from that same run.

    Direct CHM disease values were never interpolated, replaced with public measures, or aggregated
    from tract polygons. Public sources retained comparator, outcome-context, adjustment-context,
    or geographic-linkage roles. This separation is important: a join can add context to a CHM
    record without changing the clinical measure from which that record was derived.

    The analysis treated the 2 source classes as complementary. Public health sources retained the
    population-surveillance role. CHM supplied a selected clinical ascertainment lens among
    observed CAPriCORN adults. Joint analyses tested alignment or divergence between measurement
    systems and did not validate either source. This source-role distinction was prespecified for
    every estimand and display.<sup>1-5,7</sup>
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Study population, geography, and measures

    #### Statistical Analysis Module 0: governed data assembly and sample flow

    This module governs the dataset-build, source-contract, and sample-flow cells that follow.

    | Review item | Prespecified rule |
    |---|---|
    | Scientific question | Which governed aggregate records can support each analysis without changing the meaning of a source measure? |
    | Estimand | No disease estimand. This module counts available, excluded, suppressed, missing, and analytic geography-condition-period records. |
    | Population and unit | Aggregate CHM, Census, PLACES, Chicago Health Atlas, and geographic-linkage records. No row represents a patient. |
    | Variables and denominator | Source identifiers, geography and period keys, numerator, denominator, published value, suppression state, capture, reliability metadata, and linkage weights. |
    | Mathematical definition | Every many-to-one or one-to-one join is validated at its declared key. Analytic counts are reconciled from source rows through exclusions to final frames. |
    | Estimator and uncertainty | Counts, percentages, ranges, and missingness summaries only. No confidence interval is attached to data availability. |
    | Assumptions and diagnostics | Geography vintage, period, unit, uniqueness, direct-measure derivation, and join cardinality must pass. Output checksums bind each result to its inputs. |
    | Missingness and suppression | Suppressed, missing, unreliable, structural-zero, and observed-zero states remain distinct. Disease values are never imputed or reconstructed from neighboring geographies. |
    | Sensitivities | Analysis-specific complete-case counts are shown because CHM-only, CHM-PLACES, spatial, and outcome-linked frames need different inputs. |
    | Interpretation and references | Data availability describes the delivered aggregate resource. It does not validate person linkage, phenotype accuracy, representativeness, or population coverage.<sup>1-5,7,18,19,25</sup> |

    The analytic dataset starts with direct CHM/CAPriCORN condition facts and adds public context
    only through explicit keys. Clinical measures, adjustment covariates, outcomes, comparators,
    and geographic metadata retain separate source roles.

    The archived ChicagoHealthMap.com methods state that 7 health systems contribute data through
    the PCORnet Common Data Model, that an anonymized linkage process deduplicates people across
    systems, and that the resource covers adults aged 18 years or older observed from 2019 through
    2024 across 6 northeastern Illinois counties.<sup>25</sup> The site also documents a less-than-10
    suppression rule, capture tiers, 2020 census-tract geography, and ICD-10 definitions for 38
    chronic conditions plus firearm injury. These statements define the intended resource. This
    analysis audits the delivered aggregate extracts and does not independently validate the
    website's person-linkage, phenotype, or coverage claims.
    """)
    return


@app.cell
def _(
    ensure_chicago_case_study_dataset,
    json,
    output_dir,
    params,
    project_root,
):
    dataset_build_decision = ensure_chicago_case_study_dataset(
        root=project_root,
        output_dir=output_dir,
        output_stem="00_master_analytic_dataset",
        rebuild=params.rebuild,
    )
    _join_path = dataset_build_decision.artifacts.source_join_manifest_path
    if _join_path is not None:
        _join = json.loads(_join_path.read_text(encoding="utf-8"))
        _steps = _join.get("assembly_steps", [])
        _required_step_fields = {
            "input_artifacts",
            "cardinality",
            "geography_coverage",
            "period_coverage",
        }
        if not _steps or any(
            not _required_step_fields.issubset(step) for step in _steps
        ):
            dataset_build_decision = ensure_chicago_case_study_dataset(
                root=project_root,
                output_dir=output_dir,
                output_stem="00_master_analytic_dataset",
                rebuild=True,
            )
    dataset_path = dataset_build_decision.artifacts.parquet_path
    return dataset_build_decision, dataset_path


@app.cell
def _(ensure_zcta_sidecar_dataset, output_dir, params, project_root):
    zcta_build_decision = ensure_zcta_sidecar_dataset(
        root=project_root,
        output_dir=output_dir,
        output_stem="chicago_healthmap_zcta_sidecar",
        rebuild=params.rebuild,
    )
    zcta_dataset_path = zcta_build_decision.artifacts.parquet_path
    return zcta_build_decision, zcta_dataset_path


@app.cell
def _(dataset_build_decision, json, pd):
    artifacts = dataset_build_decision.artifacts
    dataset_manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
    join_manifest = json.loads(artifacts.source_join_manifest_path.read_text(encoding="utf-8"))
    assembly_steps = pd.DataFrame(join_manifest["assembly_steps"])
    return assembly_steps, dataset_manifest, join_manifest


@app.cell
def _(pd):
    source_stream_catalog_a = pd.DataFrame(
        [
            {
                "Stream": "CHM community-area facts",
                "Role": "Direct EHR-diagnosed measure",
                "Artifact": "fact_community_area_condition_stats.text",
                "Geography / period": "77 community areas; 2019–2024",
                "Key or action": "source geography + period + condition; direct parse",
                "Field class": "Direct clinical value",
            },
            {
                "Stream": "CHM tract facts",
                "Role": "Direct EHR-diagnosed measure",
                "Artifact": "fact_tract_condition_stats.text",
                "Geography / period": "Chicago-intersecting tracts; 2019–2024",
                "Key or action": "tract GEOID + period + condition; overlay restriction",
                "Field class": "Direct clinical value",
            },
        ]
    )
    return (source_stream_catalog_a,)


@app.cell
def _(pd):
    source_stream_catalog_b = pd.DataFrame(
        [
            {
                "Stream": "CHM dimensions and reliability",
                "Role": "Names, capture, reliability",
                "Artifact": "dim_community_areas.text; reliability crosswalks",
                "Geography / period": "Community areas and tracts",
                "Key or action": "geography_id; many-to-one context joins",
                "Field class": "Linked metadata",
            },
            {
                "Stream": "ACS 2024",
                "Role": "Community-area adjustment covariates",
                "Artifact": "census_acs_2024_community_area_covariates.parquet",
                "Geography / period": "Community areas; 2020–2024 ACS",
                "Key or action": "community_area_id; left join",
                "Field class": "Public adjustment data",
            },
        ]
    )
    return (source_stream_catalog_b,)


@app.cell
def _(pd):
    source_stream_catalog_c = pd.DataFrame(
        [
            {
                "Stream": "Chicago Health Atlas",
                "Role": "Life expectancy and mortality outcomes",
                "Artifact": "chicago_health_atlas_life_expectancy.parquet; mortality.parquet",
                "Geography / period": "Community areas; source periods",
                "Key or action": "geography_id + time_period; left join",
                "Field class": "Public outcome context",
            },
            {
                "Stream": "CDC PLACES",
                "Role": "Tract public comparator",
                "Artifact": "cdc_places_current_tract.parquet",
                "Geography / period": "Tracts; 2023 BRFSS / 2025 release",
                "Key or action": "geography_id + measure_id; left join",
                "Field class": "Public comparator",
            },
            {
                "Stream": "Geometries and overlay",
                "Role": "Map and geographic linkage metadata",
                "Artifact": "Chicago boundaries; TIGER tracts; tract-community overlay",
                "Geography / period": "2024 boundary snapshots",
                "Key or action": "geography_id; overlay is metadata only",
                "Field class": "Linked geographic metadata",
            },
        ]
    )
    return (source_stream_catalog_c,)


@app.cell
def _(pd):
    source_stream_catalog_d = pd.DataFrame(
        [
            {"Stream": "CHM ZCTA facts", "Role": "Direct coarser-area sensitivity measure",
             "Artifact": "fact_zcta_condition_stats.text", "Geography / period": "Six-county CHM ZCTAs; 2019–2024",
             "Key or action": "source ZCTA + period + condition; direct sidecar parse", "Field class": "Direct clinical value"},
            {"Stream": "Census tract–ZCTA relationship", "Role": "Comparison linkage metadata",
             "Artifact": "2020 tab20_zcta520_tract20_natl.txt", "Geography / period": "2020 Census relationship file",
             "Key or action": "tract GEOID to dominant ZCTA by land overlap", "Field class": "Linked geographic metadata"},
        ]
    )
    return (source_stream_catalog_d,)


@app.cell
def _(
    join_manifest,
    pd,
    source_stream_catalog_a,
    source_stream_catalog_b,
    source_stream_catalog_c,
    source_stream_catalog_d,
):
    source_stream_catalog = pd.concat(
        [source_stream_catalog_a, source_stream_catalog_b, source_stream_catalog_c,
         source_stream_catalog_d], ignore_index=True
    )
    _source_id_by_stream = {
        "CHM community-area facts": "capricorn_chicagohealthmap_export_2026_05_27",
        "CHM tract facts": "capricorn_chicagohealthmap_export_2026_05_27",
        "CHM dimensions and reliability": "capricorn_chicagohealthmap_export_2026_05_27",
        "ACS 2024": "us_census_acs",
        "Chicago Health Atlas": "chicago_health_atlas",
        "CDC PLACES": "cdc_places",
        "Geometries and overlay": "us_census_acs",
        "CHM ZCTA facts": "capricorn_chicagohealthmap_export_2026_05_27",
        "Census tract–ZCTA relationship": "census_zcta_2020_tract_relationship",
    }
    _sources = {str(item["source_id"]): item for item in join_manifest["sources"]}
    source_stream_catalog["Source ID"] = source_stream_catalog["Stream"].map(_source_id_by_stream)
    source_stream_catalog["Input path / SHA-256"] = source_stream_catalog["Source ID"].map(
        lambda source_id: "; ".join(f"{item['path']} [{item['sha256']}]"
                                    for item in _sources.get(source_id, {}).get("inputs", []))
    )
    return (source_stream_catalog,)


@app.cell
def _(source_stream_catalog):
    source_stream_display = source_stream_catalog[
        ["Stream", "Role", "Geography / period", "Key or action", "Field class"]
    ].copy()
    return (source_stream_display,)


@app.cell
def _(assembly_steps):
    source_join_display = assembly_steps[
        [
            "step_order",
            "step_id",
            "source_ids",
            "operation",
            "input_rows",
            "output_rows",
            "matched_rows",
            "unmatched_rows",
            "excluded_rows",
            "missing_rows",
            "join_key",
            "cardinality",
            "join_validation",
            "geography_coverage",
            "period_coverage",
            "field_role",
            "input_artifacts",
            "notes",
        ]
    ].copy()
    return (source_join_display,)


@app.cell
def _(pd, source_join_display):
    _rows = source_join_display
    source_join_compact = pd.DataFrame(
        {
            "Step": _rows["step_order"],
            "Operation": _rows["step_id"].str.replace("_", " ").str.title(),
            "Rows, input → output": _rows.apply(
                lambda row: f"{int(row['input_rows']):,} → {int(row['output_rows']):,}", axis=1
            ),
            "Unmatched / excluded": _rows.apply(
                lambda row: f"{int(row['unmatched_rows']):,} / {int(row['excluded_rows']):,}", axis=1
            ),
            "Join key": _rows["join_key"].apply(lambda value: ", ".join(value) if isinstance(value, list) else value),
            "Cardinality": _rows["cardinality"].str.replace("_", " "),
            "Field role": _rows["field_role"].str.replace("_", " "),
        }
    )
    return (source_join_compact,)


@app.cell
def _(mo):
    mo.md("""
    #### Source-to-analysis assembly and Stepwise join ledger
    """)
    return


@app.cell
def _(build_great_table, mo, source_stream_display):
    _table = build_great_table(
        source_stream_display,
        title="Input streams and scientific roles",
        subtitle="Direct CHM measures, linked public context, and geographic metadata",
        notes=(
            "CHM disease values remain direct and uninterpolated.",
            "Full paths and SHA-256 checksums are retained in the machine-readable source manifest.",
        ),
        table_id="source_stream_catalog",
    )
    mo.Html(_table.as_raw_html())
    return


@app.cell
def _(mo):
    mo.mermaid("""
    flowchart LR
      A[CHM community facts] --> N[Parse and normalize direct facts]
      B[CHM tract facts] --> N
      N --> C[Retain community rows directly]
      N --> L[Restrict tracts with overlay metadata]
      C --> M[Concatenate community and tract frames]
      L --> M
      M --> G[Attach geography context]
      D[ACS 2024 covariates] --> G
      E[Chicago Health Atlas] --> H[Join Atlas outcomes and latest mortality]
      G --> H
      F[PLACES tract comparator] --> P[Assign measure IDs and join by tract]
      H --> P
      P --> Q[Derive roles, flags, and lineage]
      Q --> R[Validate unique geography-period-condition key]
      R --> S[20,536 x 97 validated dataset; 18,688 tract and 1,848 community-area records]
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Stepwise join ledger.** Each transition records row counts, join keys, cardinality, unmatched
    rows, suppression, missingness, and field roles.
    """)
    return


@app.cell
def _(build_great_table, mo, source_join_compact):
    _table = build_great_table(
        source_join_compact,
        title="Stepwise source-assembly and join ledger",
        subtitle="Row transitions, keys, cardinality, and missingness",
        notes=(
            "Missing values are not recoded as zero.",
            "The complete ledger retains exact source IDs, coverage, checksums, validation, and notes.",
        ),
        table_id="source_join_ledger",
    )
    mo.Html(_table.as_raw_html())
    return


@app.cell
def _(mo):
    mo.md("""
    Join keys include `geography_id, time_period`, and `condition_id`. CHM disease values are never interpolated, and missing values are not zeros. A direct ZCTA sidecar is retained as
    a secondary comparison; ZCTAs are Census statistical areas, not US Postal Service ZIP Codes.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **How to read the assembly ledger.** The source table identifies what each stream contributes;
    the flow shows the order in which records are combined; and the ledger shows whether a step
    retained, matched, excluded, or left a record unmatched. "Direct clinical value" means a CHM
    fact is carried forward as reported. "Linked metadata" or "derived" means that the field adds
    location, quality, comparator, or analytic context and is not a replacement disease estimate.
    The validated output is therefore a traceable analysis file rather than a new clinical source.
    """)
    return


@app.cell
def _(
    build_great_table,
    load_quality_checkpoint,
    mo,
    project_root,
    schema_evidence_view,
):
    quality_checkpoint = load_quality_checkpoint(project_root / "outputs/quality/ehr_quality.json")
    quality_schema = schema_evidence_view(quality_checkpoint)
    _table = build_great_table(
        quality_schema,
        title="Upstream source-quality checkpoint",
        subtitle="Disclosure-safe schema evidence and unresolved semantic blockers",
        table_id="upstream_quality_checkpoint",
    )
    mo.vstack(
        [
            mo.md("### Upstream source quality checkpoint"),
            mo.Html(_table.as_raw_html()),
        ]
    )
    return


@app.cell
def _(dataset_path, load_analytic_dataset):
    analytic = load_analytic_dataset(dataset_path)
    if analytic["disease_value_derivation"].ne("direct_first_party_export_not_interpolated").any():
        raise ValueError("disease values must remain direct and uninterpolated")
    return (analytic,)


@app.cell
def _(analytic, build_tract_cohort_flow, output_dir):
    tract_cohort_flow = build_tract_cohort_flow(analytic)
    tract_cohort_flow.to_csv(
        output_dir / "supplement_tract_cohort_flow.csv", index=False
    )
    return (tract_cohort_flow,)


@app.cell
def _(build_great_table, mo, tract_cohort_flow):
    _table = build_great_table(
        tract_cohort_flow,
        title="Tract cohort flow by condition and year",
        subtitle=(
            "2024 TIGER representative-point boundary, annual denominator at least 30, "
            "and observable count after suppression"
        ),
        notes=(
            "Counts are tract-condition-year aggregate records, not patients.",
            "A zero numerator is excluded because true zero and suppression cannot be distinguished.",
            "The 50% tract-area boundary rule is retained as a sensitivity definition.",
        ),
        table_id="tract_cohort_flow",
    )
    mo.vstack(
        [
            mo.md("### Prespecified tract analytic cohort flow"),
            mo.Html(_table.as_raw_html()),
        ]
    )
    return


@app.cell
def _(pd, zcta_dataset_path):
    zcta_analytic = pd.read_parquet(zcta_dataset_path)
    if zcta_analytic["disease_value_derivation"].ne(
        "direct_first_party_export_not_interpolated"
    ).any():
        raise ValueError("ZCTA disease values must remain direct and uninterpolated")
    return (zcta_analytic,)


@app.cell
def _(build_great_table, mo, pd, zcta_analytic, zcta_build_decision):
    _summary = pd.DataFrame([{
        "Rows": len(zcta_analytic), "Observed ZCTAs": zcta_analytic["geography_id"].nunique(),
        "Years": f"{zcta_analytic['time_period'].min()}–{zcta_analytic['time_period'].max()}",
        "Conditions": zcta_analytic["condition_id"].nunique(),
        "Build action": zcta_build_decision.action, "Authorized": False,
    }])
    _table = build_great_table(
        _summary, title="Direct CHM ZCTA sensitivity sidecar",
        subtitle="Comparison-only artifact; outside the primary analytic dataset",
        notes=("ZCTAs are Census statistical areas, not USPS ZIP Codes.",
               "Disease values are direct CHM ZCTA facts and are never aggregated from tracts."),
        table_id="zcta_sidecar_summary",
    )
    mo.Html(_table.as_raw_html())
    return


@app.cell
def _(build_great_table, dataset_build_decision, mo, pd):
    _artifacts = dataset_build_decision.artifacts
    dataset_artifact_summary = pd.DataFrame(
        [{"artifact": path.name, "exists": path.is_file()} for path in _artifacts.required_paths]
    )
    _table = build_great_table(
        dataset_artifact_summary,
        title="Same-run analytic dataset artifacts",
        subtitle=f"Build action: {dataset_build_decision.action}",
        table_id="dataset_artifact_summary",
    )
    mo.vstack(
        [
            mo.md(
                f"**Dataset action:** `{dataset_build_decision.action}` "
                f"(`{dataset_build_decision.reason}`)."
            ),
            mo.Html(_table.as_raw_html()),
            mo.download(
                _artifacts.data_book_html_path.read_bytes(),
                filename=_artifacts.data_book_html_path.name,
                mimetype="text/html",
                label="Download the compact data book",
            ),
        ]
    )
    return


@app.cell
def _(
    analytic,
    build_data_quality_audit,
    dataset_manifest,
    join_manifest,
    output_dir,
):
    data_quality_audit = build_data_quality_audit(analytic, dataset_manifest, join_manifest)
    data_quality_audit.to_csv(output_dir / "supplement_data_quality_audit.csv", index=False)
    return (data_quality_audit,)


@app.cell
def _(analytic, build_great_table, data_quality_audit, mo):
    _table = build_great_table(
        data_quality_audit,
        title="Governed data-quality and join audit",
        subtitle=f"Contract checks for the {len(analytic):,}-row analytic artifact",
        table_id="data_quality_audit",
    )
    mo.vstack(
        [
            mo.md("### Governed data-quality and join audit"),
            mo.Html(_table.as_raw_html()),
        ]
    )
    return


@app.cell
def _():
    master_dataset_gallery = (
        "00_master_analytic_dataset_data_book.csv",
        "00_master_analytic_dataset_data_book.html",
        "00_master_analytic_dataset_source_join_manifest.json",
        "supplement_data_quality_audit.csv",
        "supplement_tract_cohort_flow.csv",
    )
    return (master_dataset_gallery,)


@app.cell
def _(mo):
    mo.md("""
    #### Source assembly, cleaning, and data roles

    Technical specification: The purpose is to preserve direct first-party disease values
    while constructing one row per source geography-condition-period record. The estimand is
    the EHR-diagnosed proportion among observed CAPriCORN adults; the observational unit is a
    community area or tract. No regression equation is estimated here; alpha is not defined,
    beta is not a disease contrast, and gamma is not a covariate slope. No adjustment set is
    applied. Missing, suppressed, zero-count, and unavailable-reliability states remain explicit;
    no imputation or interpolation is permitted. Checks are deterministic schema, checksum, and
    lineage checks; uncertainty/CI method is not applicable to cleaning counts. Sensitivity
    status is not applicable; diagnostics are schema, checksum, and lineage checks. The
    inference boundary is descriptive source integrity, not an inferential result.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — Data cleaning:** This step is the receipt for what arrived from each
    source. We keep a blank, a suppressed value, and a value that cannot be qualified as three
    different facts. Disease numbers stay exactly as exported; we do not fill gaps from a
    neighboring geography or turn an observed clinical count into population prevalence.
    """)
    return


@app.cell
def _(analytic, summarize_resource_quality):
    resource_quality = summarize_resource_quality(analytic)
    return (resource_quality,)


@app.cell
def _(mo):
    mo.md("""
    #### Source rows, exclusions, suppression, missingness, and reliability

    We audited capture, suppression, missingness, reliability availability, and analytic
    qualification before comparing measures. The unit was a geography-condition-period record,
    and the measure was the EHR-diagnosed proportion among observed CAPriCORN adults. Missing,
    suppressed, observed-zero, and reliability-withheld states remained distinct; none was
    imputed. Resource summaries used counts and source-row denominators, without inferential
    intervals. Supplementary community-area outcome models used y_i = alpha + beta x_i + gamma
    Z_i + error_i, HC3 covariance, and two-sided 97.5% primary intervals; they remain outside the
    main geographic result and unauthorized. Reliability qualification remains withheld pending
    a governed rule; no result supports causal or population-prevalence inference.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — Data quality checks:** We count every row, including rows that cannot
    be used in a model. Table 1 makes the denominator visible so a reviewer can see how much of
    the source was captured, suppressed, or missing before any map or association is shown.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Restricted provisional quality control: CHM website-metric verification

    **Not for manuscript import.** The following aggregate values are retained only so the
    statistician can review the capture-variable provenance and the decision not to recalculate it.

    A separate post-run quality-control check compared an uploaded `total_pt_seen` tract-year
    extract divided by ACS adults aged 18 years or older with the published CHM tract capture
    crosswalk. The reconstructed candidate ratio differed from the published rate by a mean
    absolute 5.7 percentage points in comparable 2023 tracts, and 2 candidate ratios exceeded
    100%. This does not establish that the website metric is incorrect: the two sources may use
    different patient eligibility, deduplication, reference date, geography vintage, or ACS
    denominator definitions. Therefore, this notebook retains the published crosswalk as source
    metadata and does not use the reconstructed ratio as CHM capture. A secondary resource-
    governance goal is to recover and audit the exact published-metric numerator, denominator,
    vintage, and eligibility rule before any website correction or recalculation is considered.
    This finding is operational quality control, not a manuscript result or a prevalence estimate.
    """)
    return


@app.cell
def _(resource_quality):
    table_1_enriched = resource_quality.copy()
    table_1_enriched["disease_measure_unit"] = "percentage_points"
    table_1_enriched["denominator_unit"] = "source_condition_record_field_pending_semantic_verification"
    community_map_contract = {
        "map_population_areas": 77,
        "map_c2_complete_areas": 76,
        "map_c2_incomplete_areas": 1,
        "map_unavailable_areas": 0,
        "qualification_withheld_areas": 77,
    }
    community_mask = table_1_enriched["geography_type"].eq("chicago_community_area")
    for column, value in community_map_contract.items():
        table_1_enriched[column] = None
        table_1_enriched.loc[community_mask, column] = value
    return (table_1_enriched,)


@app.cell
def _(build_compact_table_1, table_1_enriched):
    table_1_full = table_1_enriched.copy()
    table_1 = build_compact_table_1(table_1_full)
    return table_1, table_1_full


@app.cell
def _(build_great_table, output_dir, table_1):
    _notes = (
        "Counts are geographic-condition-year observations, not unique patients.",
        "CHM condition-record denominators and source-published capture metadata are not unique-patient or population estimates; suppression is not statistical censoring.",
        "Reliability qualification remains withheld. Tract accounting is reported in Figure 1 and eTable 1.",
    )
    _main = build_great_table(
        table_1,
        title="Table 1. Chicago Health Map community-area data coverage, 2019–2024",
        subtitle="Four direct CHM condition streams across 77 community areas",
        notes=_notes,
        table_id="table_1_chm_community",
        spanners={"Availability and quality": tuple(table_1.columns[4:])},
    )
    table_1_html = _main.as_raw_html()
    _csv = output_dir / "table_1_resource_quality.csv"
    table_1.to_csv(_csv, index=False, float_format="%.12g")
    _ = (output_dir / "table_1_resource_quality.html").write_text(
        _main.as_raw_html(make_page=True), encoding="utf-8"
    )
    return (table_1_html,)


@app.cell
def _(build_great_table, output_dir, table_1_full):
    table_1_full.to_csv(
        output_dir / "etable_1_resource_quality.csv", index=False, float_format="%.12g"
    )
    _full = build_great_table(
        table_1_full,
        title="eTable 1. Full CHM resource-quality and tract accounting audit",
        table_id="etable_1_resource_quality",
    )
    _ = (output_dir / "etable_1_resource_quality.html").write_text(
        _full.as_raw_html(make_page=True), encoding="utf-8"
    )
    return


@app.cell
def _(mo):
    mo.md("""
    Table 1 renders the same labeled HTML written to the deterministic artifact. It
    uses `great_tables` to preserve editable cells, exact denominators, units, and source notes.
    It describes CHM community-area records rather than patient characteristics.
    """)
    return


@app.cell
def _(mo, table_1_html):
    table_1_display = mo.Html(table_1_html)
    return (table_1_display,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Geographic-resolution statistical analysis

    The primary geographic analysis asks whether direct CHM community-area labels reproduce
    direct tract classifications and how much observed tract variation occurs within community
    areas. CHM-PLACES alignment asks a distinct secondary question about cross-source ordering.
    Each analysis uses its own pairwise-complete population and denominator. Neither source is a
    criterion standard, and linkage is not literal geographic aggregation.<sup>3,4,21</sup>

    These tract analyses constitute the proposed primary aim in the version 0.2 implementation
    addendum. The signed SAP remains controlling until the statistician and authors approve that
    amendment. C1 and C2 community-area outcome models remain supplementary. No geographic result
    may support a manuscript claim before amendment approval and independent S7 authorization.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Statistical approach for biostatistical review

    #### Eligibility, exclusions, and analytic denominators

    Eligible records are direct, uninterpolated CHM observations from 2022 through 2024 with a
    valid geography, numerator, denominator of at least 30 observed adults, and condition
    definition. Suppressed observations,
    ambiguous zeros, missing denominators, nonfinite values, duplicate geography-period-condition
    keys, and incompatible tract vintages fail closed. No missing or suppressed disease measure is
    imputed. Each analysis reports its own complete-case denominator because PLACES availability,
    dominant community-area assignment, and outcome linkage differ.

    Tract analyses require a 2024 TIGER representative point covered by the frozen union of 77
    Chicago community areas. A 50% tract-area rule is retained as a boundary sensitivity.
    Dominant community-area analyses additionally require a maximum overlay weight of at least
    0.99. The noncrossing sensitivity excludes every tract that crosses a community-area boundary.
    Community-area outcome models use direct community-area CHM values,
    not values reconstructed from tract polygons.<sup>21-24</sup>
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    #### Time pooling, scale, and rank construction

    Let $n_{gct}$ and $d_{gct}$ denote the eligible CHM numerator and denominator for geography
    $g$, condition $c$, and year $t$. The analysis first computes
    $P_{gc}=100\sum_t n_{gct}/\sum_t d_{gct}$ for 2022 through 2024. This denominator-weighted
    percentage is the SAP estimand. It is not the arithmetic mean of annual percentages and is
    not population prevalence or a unique-person 3-year prevalence because an adult may
    contribute in more than 1 year.

    Percentile ranks are then computed separately within condition and source, in ascending order,
    on the 0-to-1 scale. Ties receive their average rank. Quartile bins are Q1 for rank $\leq0.25$,
    Q2 for $(0.25,0.50]$, Q3 for $(0.50,0.75]$, and Q4 for rank $>0.75$. Community areas are
    ranked once before their labels are linked to tracts. Repeating area values across tracts
    before ranking is prohibited. A regression check evaluates the exact 0.25, 0.50, and 0.75
    boundaries so every table, figure, agreement statistic, and transition analysis uses the same
    categories.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    #### Rank alignment and ordinal agreement

    CHM-PLACES alignment uses Spearman $\rho$ on paired within-source percentile ranks and the
    median absolute percentile-rank gap. These summarize monotonic ordering and typical rank
    distance. They do not test calibration or equality of the original percentages.

    Quartile agreement uses quadratic weighted Cohen $\kappa$, with disagreement weight
    $w_{ab}=[(a-b)/3]^2$ for categories 0 through 3.<sup>8</sup> Kappa gives larger penalties to more
    distant quartiles. Exact agreement is reported beside kappa because it is directly
    interpretable. Unweighted Gwet AC1 is retained only as a supplementary nominal sensitivity for
    concentrated marginal distributions.<sup>9</sup> It does not replace weighted kappa or imply
    that quartile distance is irrelevant. No agreement coefficient identifies which source is
    correct.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    #### Variance partition and area-label separation

    A1 uses the CHM-only complete frame. PLACES availability cannot determine inclusion in this
    estimand. For tract $i$ in community area $j$, write the observed pooled proportion as
    $P_{ij}=\mu+u_j+e_{ij}$. A one-way random-effects method-of-moments decomposition estimates
    between-area variance $\sigma_u^2$ and within-area variance $\sigma_e^2$. The notebook reports
    $VPC=\sigma_u^2/(\sigma_u^2+\sigma_e^2)$ and its complement, the within-area variance share.
    The same observed-scale estimator is used for the point estimate and every bootstrap replicate.
    This is a descriptive partition of tract estimates, not a patient-level ICC or a binomial
    multilevel disease model.<sup>10</sup>

    Exploratory A2 classifies a tract as high when its pooled CHM measure is at or above the global
    75th percentile. Its score is the mean of the other eligible tracts in the same community area,
    excluding the indexed tract. The Mann-Whitney statistic divided by the number of high-low pairs
    estimates the probability that a randomly selected high tract has the larger score.<sup>11</sup>
    Areas with fewer than 2 eligible tracts are excluded. The empirical high-tract threshold is
    recomputed inside each cluster-bootstrap sample. This AUC is descriptive separation, not
    trained or externally validated prediction, and it cannot support the primary novelty claim.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    #### Resampling and uncertainty

    Nonparametric percentile intervals resample community areas with replacement and retain all
    eligible tracts within each sampled area, preserving the main within-area dependence.<sup>12</sup>
    Within each resample, source-specific percentile ranks, quartiles, rank gaps, and discordance
    categories are recalculated. The 2.5th and 97.5th empirical percentiles form the 95% interval.
    The seed is 20260715.

    A1 through A4 use 1000 requested area-cluster replicates for this review package. The variance and AUC procedures must
    return at least 95% estimable replicates. A5 uses 1000 PLACES interval draws and is not a cluster
    bootstrap. Because compatible CHM numerator/denominator uncertainty is unavailable, A5 reports
    only PLACES-rank uncertainty and labels joint uncertainty not run. Bootstrap intervals address
    within-area clustering but do not fully model spatial dependence. The final replicate count is
    a sign-off decision. If 5000 replicates are requested, the notebook will add a stability check
    comparing interval endpoints with the 1000-replicate review run.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    #### Supplementary community-area outcome models

    For area $i$, $LE_i=\alpha+\beta^\mathsf{T}X_i+\gamma^\mathsf{T}Z_i+\epsilon_i$.
    Life expectancy is measured in years. Exposures are centered and scaled by their frozen IQR;
    adjustment variables are centered and scaled by 1 SD. The adjustment set is percentage aged
    65 years or older, percentage female, percentage below the federal poverty level, and pooled
    2022-2024 EHR capture, defined as summed EHR denominators divided by summed aligned ACS adult
    populations. Adult population is used only in prespecified weighting sensitivities.

    OLS coefficients use HC3 covariance because the area sample is small and heteroscedasticity is
    plausible.<sup>13</sup> Primary exposure contrasts use 2-sided 97.5% normal-theory intervals;
    other coefficients use 95% intervals. The statistician must approve the normal rather than t
    critical values. Rank deficiency, fewer than 70 complete areas, exposure support below 10
    distinct values, correlation above 0.80, or maximum VIF above 5 blocks the primary model.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    #### Regression diagnostics, spatial structure, and multiplicity

    Model checks include rank and condition number, VIF, residual distribution, leverage,
    Cook distance, leave-one-area-out influence, weighted fits, annual and leave-one-year-out
    fits, and disruption-period sensitivities. A failed diagnostic is reported as a failed gate,
    not repaired by deleting covariates according to statistical significance.

    Global Moran $I$ evaluates residual spatial autocorrelation under the frozen queen topology;
    rook and distance weights are sensitivity topologies.<sup>14</sup> A prespecified Moran gate
    triggers a spatial-error sensitivity. Local Moran $I$ and Getis-Ord $G_i^*$ describe local
    spatial patterns.<sup>15,16</sup> Tests use 9999 seeded conditional permutations. Benjamini-
    Hochberg adjustment controls the false discovery rate separately within each declared
    condition-period-statistic family.<sup>17</sup> Local classifications remain descriptive and
    do not identify causes, treatment effects, or service need.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Missingness, sensitivities, and interpretation rules

    Analyses use available cases within each prespecified frame. Missing, suppressed, unreliable,
    withheld, structural-zero, and observed-zero states remain distinct. No single imputation,
    interpolation, missing-indicator substitution, or neighboring-geography substitution occurs.
    The notebook reports the source-row flow and analysis-specific denominators so complete-case
    changes are visible.

    Sensitivities include unweighted annual means, annual classifications, exclusion of crossing
    tracts, alternative rank categories, capture and reliability strata, direct ZCTA comparisons,
    weighting, influence, temporal omission, and alternative spatial weights. A sensitivity is
    supportive and does not replace its corresponding estimand. Null, not estimable, not run,
    failed, and withheld are different conclusions. All interpretations remain ecological and
    associational.<sup>18,19</sup>
    """)
    return


@app.cell
def _(mo):
    _suppressed_main_cardiometabolic_methods = mo
    return


@app.cell
def _(mo):
    _suppressed_main_copd_methods = mo
    return


@app.cell
def _(mo):
    mo.md("""
    #### Descriptive complementarity analyses

    The displayed diabetes comparison remains not run until the 2 exported component phenotypes
    are shown to be mutually exclusive, share the same denominator, and align with the comparator
    period and definition. Joint uncertainty-aware agreement, bivariate LISA, and spatial-scan
    analyses are also labeled not run when their required inputs or specifications are absent.
    A not-run analysis is not a null finding.

    Direct ZCTA comparisons are secondary to community areas. Annual and noncrossing analyses test
    stability of the descriptive classifications. They do not estimate time trends or causal
    effects of geographic scale. Every comparison retains its condition-specific eligible
    denominator and `results_authorized=false` status.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Ethics and reporting

    The analysis dates were July 13 through July 16, 2026. Software was Python 3.13.14
    (Python Software Foundation), marimo 0.23.14, pandas 3.0.3, NumPy 2.5.1, SciPy 1.18.0,
    statsmodels 0.14.6, GeoPandas 1.1.4, Matplotlib 3.11.0, and Great Tables 0.22.0.
    Reporting follows STROBE and RECORD principles for an ecological analysis of routinely
    collected data.<sup>18,19</sup> Journal structure follows the JAMA Health Forum Original
    Investigation instructions checked August 27, 2026.<sup>20</sup> The study has a UIC IRB
    record (protocol No. [UIC IRB PROTOCOL NUMBER]).
    [AUTHOR: insert the exact ethics determination and informed-consent or waiver language before
    submission.] Results remain nonimportable while `results_authorized=false`.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Statistical Analysis Module 1: added geographic information beyond community-area labels

    This module governs the CHM-only tract frames, variance partition, direct cross-frame rank and
    classification comparisons, and noncrossing sensitivity cells that follow.

    | Review item | Prespecified rule |
    |---|---|
    | Scientific question | Do direct tract measures contain geographic information that direct community-area labels do not retain? |
    | Estimands | Within-community observed variance share, median and mean absolute tract-to-area percentile-rank gap, exact quartile disagreement, and movement into or out of Q4. |
    | Population and unit | Census tracts passing the 2024 TIGER representative-point Chicago boundary rule and CHM-complete in 2022-2024, with annual denominators of at least 30 and dominant community-area overlay weight at least 0.99. The unit is a tract. A1 and A2 do not require PLACES. |
    | Variables and denominator | Direct pooled CHM numerator and denominator, direct tract and community-area ranks, community-area linkage, crossing status, capture, and reliability metadata. Every percentage reports the eligible tract count. |
    | Mathematical definition | $P_{gc}=100\sum_t n_{gct}/\sum_t d_{gct}$. Absolute rank gap is $|R_{tract}-R_{area}|$. Q4 is rank greater than 0.75. The within-area variance share is $1-VPC$. |
    | Estimator and uncertainty | One-way method-of-moments variance partition and direct cross-frame descriptive summaries. Community-area cluster percentile intervals use 1000 review replicates.<sup>10,12</sup> |
    | Assumptions and diagnostics | Direct tract and community-area exports are sufficiently comparable for linked classification, dominant overlay identifies one area, and observed-scale variance is interpretable. Denominator distributions, tract counts per area, influence of crossing tracts, and bootstrap stability are reviewed. |
    | Missingness and suppression | Require 3 eligible CHM years. Exclude suppressed or invalid disease records, annual denominators below 30, and unresolved zero-or-suppressed counts. Do not require a public comparator and do not impute any disease value. |
    | Sensitivities | At least 50% tract area inside Chicago, noncrossing tracts, ZCTA labels, annual and 2-of-3 stability, alternative tertiles, capture strata, reliability strata, and unweighted annual means. The unweighted mean is never substituted for the primary pooled estimator. |
    | Interpretation and references | A difference shows that direct labels classify the same linked tract differently across source frames. It is not mathematical aggregation loss, population prevalence, a validated hotspot, or evidence of community need.<sup>1-5,18,19</sup> |

    The primary paper claim must follow these estimands. Exploratory AUC, CHM-PLACES agreement,
    spatial statistics, and life-expectancy models cannot substitute for them.
    """)
    return


@app.cell
def _(pd, primary_frame, summarize_influence):
    c1_influence = pd.DataFrame(
        [
            {
                "model_id": "C1",
                "row_type": "model_summary",
                "analysis_status": "not_run_combined_diabetes_semantics_unapproved",
                "results_authorized": False,
            }
        ]
    )
    c2_areas, c2_influence_summary = summarize_influence(primary_frame, "C2")
    c2_influence = pd.concat(
        [c2_areas.assign(row_type="area"), c2_influence_summary.assign(row_type="model_summary")],
        ignore_index=True,
        sort=False,
    )
    return c1_influence, c2_influence, c2_influence_summary


@app.cell
def _(c1_influence, c2_influence, output_dir):
    c1_influence.to_csv(
        output_dir / "supplement_influence_c1.csv", index=False, float_format="%.12g"
    )
    c2_influence.to_csv(
        output_dir / "supplement_influence_c2.csv", index=False, float_format="%.12g"
    )
    return


@app.cell
def _(
    analytic,
    build_direct_tract_analysis_frame,
    build_tract_percentile_concordance,
    capture_quartile_cut_points,
    pd,
    primary_frame,
):
    governed_capture_cut_points = capture_quartile_cut_points(
        primary_frame, pd.Series(True, index=primary_frame.index)
    )
    cut_point_text = "|".join(f"{value:.12g}" for value in governed_capture_cut_points)
    tract_percentile = build_tract_percentile_concordance(
        analytic,
        noncrossing_only=False,
        capture_cut_points=governed_capture_cut_points,
    )
    tract_percentile_noncrossing = build_tract_percentile_concordance(
        analytic,
        noncrossing_only=True,
        capture_cut_points=governed_capture_cut_points,
    )
    tract_chm_direct = build_direct_tract_analysis_frame(analytic, noncrossing_only=False)
    tract_chm_direct_noncrossing = build_direct_tract_analysis_frame(
        analytic, noncrossing_only=True
    )
    return (
        cut_point_text,
        tract_chm_direct,
        tract_chm_direct_noncrossing,
        tract_percentile,
        tract_percentile_noncrossing,
    )


@app.cell
def _(analytic, tract_percentile, tract_percentile_noncrossing):
    _columns = ["geography_id", "condition_family", "public_comparator_confidence_interval"]
    _metadata = analytic.loc[
        analytic["geography_type"].eq("census_tract"), _columns
    ].dropna().drop_duplicates()
    _metadata = _metadata.rename(columns={"condition_family": "condition_id"})
    if _metadata.duplicated(["geography_id", "condition_id"]).any():
        raise ValueError("PLACES interval metadata must be unique within tract and condition")
    _metadata["public_comparator_source_id"] = "cdc_places_current_tract"
    _metadata["public_comparator_unit"] = "percent"
    _metadata["public_comparator_confidence_level"] = 0.95
    _metadata["public_comparator_geography_vintage"] = "2020_census_tract"
    _key = ["geography_id", "condition_id"]
    tract_uncertainty_frame = tract_percentile.merge(
        _metadata, on=_key, how="left", validate="one_to_one"
    )
    tract_uncertainty_noncrossing = tract_percentile_noncrossing.merge(
        _metadata, on=_key, how="left", validate="one_to_one"
    )
    return tract_uncertainty_frame, tract_uncertainty_noncrossing


@app.cell
def _(
    analytic,
    build_direct_ehr_rank_frame,
    build_geographic_resolution_matrix,
    dataset_path,
    pd,
    sha256,
    tract_chm_direct,
    tract_chm_direct_noncrossing,
):
    community_rank_frame = build_direct_ehr_rank_frame(analytic, "chicago_community_area")
    dataset_checksum = sha256(dataset_path.read_bytes()).hexdigest()
    geographic_resolution_matrix = pd.concat(
        [
            build_geographic_resolution_matrix(
                tract_chm_direct,
                community_rank_frame,
                period="CHM 2022-2024 pooled direct values",
                source_artifact=dataset_path.name,
                source_checksum=dataset_checksum,
            ).assign(noncrossing_only=False),
            build_geographic_resolution_matrix(
                tract_chm_direct_noncrossing,
                community_rank_frame,
                period="CHM 2022-2024 pooled direct values; noncrossing sensitivity",
                source_artifact=dataset_path.name,
                source_checksum=dataset_checksum,
            ).assign(noncrossing_only=True),
        ],
        ignore_index=True,
    )
    return community_rank_frame, geographic_resolution_matrix


@app.cell
def _(mo):
    mo.md(r"""
    ### Statistical Analysis Module 2: CHM and CDC PLACES measurement alignment

    This module governs the pairwise-complete rank, agreement, capture, reliability, and
    comparator-uncertainty cells that follow. It is secondary context, not validation.

    | Review item | Prespecified rule |
    |---|---|
    | Scientific question | Do CHM and PLACES order the same eligible Chicago tracts similarly despite different populations and measurement processes? |
    | Estimands | Spearman rank correlation, median absolute percentile-rank gap, exact quartile agreement, quadratic weighted kappa, and supplementary unweighted Gwet AC1. |
    | Population and unit | Tracts with 3 eligible CHM years, a compatible PLACES estimate, and dominant community-area linkage. The unit is a pairwise-complete tract. |
    | Variables and denominator | Pooled CHM diagnosed proportion, PLACES modeled crude percentage, within-source average-tie percentile ranks, capture quartile, and source reliability tier. Each condition has its own paired denominator. |
    | Mathematical definition | $\rho_s=cor(rank(CHM),rank(PLACES))$. Rank gap is $|R_{CHM}-R_{PLACES}|$. Quadratic kappa weights category distance by $[(a-b)/3]^2$.<sup>8</sup> |
    | Estimator and uncertainty | Descriptive coefficients with community-area cluster percentile intervals. Ranks and rank-derived categories are recomputed within every resample.<sup>8,9,12</sup> |
    | Assumptions and diagnostics | Sources have compatible condition direction, adult scope, geography vintage, and interpretable period overlap. Marginal category distributions and eligible counts are shown with agreement statistics. |
    | Missingness and suppression | Pairwise complete. A missing PLACES value excludes only this module. Suppressed CHM records are not imputed. A5 propagates PLACES intervals only because compatible CHM uncertainty is unavailable. |
    | Sensitivities | Noncrossing tracts, capture and reliability strata, tertiles, and PLACES interval draws. |
    | Interpretation and references | Agreement means similar ordering, not calibration, equal prevalence, absence of selection bias, or validation of either source.<sup>2-5,21</sup> |
    """)
    return


@app.cell
def _(
    cut_point_text,
    pd,
    summarize_concordance_metrics,
    tract_percentile,
    tract_percentile_noncrossing,
):
    complementarity_summary = pd.concat(
        [
            summarize_concordance_metrics(tract_percentile).assign(noncrossing_only=False),
            summarize_concordance_metrics(tract_percentile_noncrossing).assign(
                noncrossing_only=True
            ),
        ],
        ignore_index=True,
        sort=False,
    )
    complementarity_summary["capture_quartile_cut_points"] = cut_point_text
    complementarity_summary["capture_quartile_cut_point_source"] = (
        "governed_community_area_eligible_population"
    )
    return (complementarity_summary,)


@app.cell
def _(
    cut_point_text,
    pd,
    summarize_within_community_heterogeneity,
    tract_percentile,
    tract_percentile_noncrossing,
):
    heterogeneity_summary = pd.concat(
        [
            summarize_within_community_heterogeneity(tract_percentile).assign(
                noncrossing_only=False
            ),
            summarize_within_community_heterogeneity(tract_percentile_noncrossing).assign(
                noncrossing_only=True
            ),
        ],
        ignore_index=True,
        sort=False,
    )
    heterogeneity_summary["capture_quartile_cut_points"] = cut_point_text
    heterogeneity_summary["capture_quartile_cut_point_source"] = (
        "governed_community_area_eligible_population"
    )
    return (heterogeneity_summary,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Exploratory Statistical Analysis Module 3: area-label separation AUC

    | Review item | Prespecified rule |
    |---|---|
    | Scientific question | How strongly does the mean of other tracts in the same community area separate empirically high from other CHM tracts? |
    | Estimand | Probability that a randomly selected high tract has a larger leave-one-tract-out area score than a randomly selected nonhigh tract. |
    | Population and unit | CHM-only complete tracts in community areas with at least 2 eligible tracts. The unit is a tract. |
    | Variables and denominator | Pooled direct CHM measure, empirical 75th-percentile threshold, community-area identifier, and leave-one-tract-out mean. |
    | Mathematical definition | $AUC=U/(n_{high}n_{other})$, where $U$ is the Mann-Whitney statistic.<sup>11</sup> |
    | Estimator and uncertainty | Descriptive Mann-Whitney AUC with a 1000-replicate community-area cluster percentile interval. The high threshold is recomputed in every replicate. |
    | Assumptions and diagnostics | At least 2 tracts per area and both outcome classes are required. Failed bootstrap replicates are counted and at least 95% must be estimable. |
    | Missingness and suppression | PLACES is not required. Suppressed or incomplete CHM records are excluded without imputation. |
    | Sensitivities | Noncrossing tracts and alternative median or tertile thresholds are available if requested before final authorization. |
    | Interpretation and references | AUC is an exploratory separation summary. It is not a fitted prediction model, external validation, discrimination for individual outcomes, or evidence that the area label should replace tract data.<sup>11</sup> |
    """)
    return


@app.cell
def _(
    compute_discriminatory_accuracy,
    compute_variance_partition,
    pd,
    propagate_uncertainty_discordance,
    tract_chm_direct,
    tract_chm_direct_noncrossing,
    tract_uncertainty_frame,
    tract_uncertainty_noncrossing,
):
    _records = []
    _inputs = (
        ("primary", tract_chm_direct, tract_uncertainty_frame),
        (
            "noncrossing",
            tract_chm_direct_noncrossing,
            tract_uncertainty_noncrossing,
        ),
    )
    for _sensitivity, _chm_frame, _uncertainty_frame in _inputs:
        for _condition, _group in _chm_frame.groupby("condition_id", sort=True):
            _a1 = compute_variance_partition(_group)
            _a2 = compute_discriminatory_accuracy(_group, threshold="75th_percentile")
            _uncertainty = _uncertainty_frame.loc[
                _uncertainty_frame["condition_id"].eq(_condition)
            ]
            _a5 = propagate_uncertainty_discordance(_uncertainty)
            for _result in (_a1, _a2, _a5):
                _result["sensitivity_status"] = _sensitivity
                _result["analysis_population"] = (
                    "pairwise_chm_places_complete_2022_2024"
                    if _result["analysis_id"] == "A5"
                    else "chm_only_complete_2022_2024"
                )
                _records.append(_result)
    descriptive_complementarity_results = pd.DataFrame.from_records(_records)
    return (descriptive_complementarity_results,)


@app.cell
def _(descriptive_complementarity_results, output_dir):
    descriptive_complementarity_results.to_csv(
        output_dir / "supplement_descriptive_complementarity_methods.csv",
        index=False,
        float_format="%.12g",
    )
    return


@app.cell
def _(
    build_descriptive_claim_evidence_audit,
    descriptive_complementarity_results,
    output_dir,
):
    _display_registry = {f"A{index}": "etable_7" for index in range(1, 7)}
    descriptive_claim_evidence_audit = build_descriptive_claim_evidence_audit(
        descriptive_complementarity_results.to_dict("records"), _display_registry
    )
    descriptive_claim_evidence_audit.to_csv(
        output_dir / "supplement_descriptive_claim_evidence_audit.csv", index=False
    )
    return


@app.cell
def _(build_great_table, descriptive_complementarity_results, output_dir):
    _table = build_great_table(
        descriptive_complementarity_results,
        title="eTable 7. Descriptive complementarity methods and governed analysis status",
        table_id="etable_7_descriptive_complementarity",
    )
    etable_7_path = output_dir / "etable_7_descriptive_complementarity_methods.html"
    _bytes_written = etable_7_path.write_text(_table.as_raw_html(make_page=True), encoding="utf-8")
    return (etable_7_path,)


@app.cell
def _(build_great_table, descriptive_complementarity_results, output_dir):
    uncertainty_feasibility = descriptive_complementarity_results.loc[
        descriptive_complementarity_results["analysis_id"].eq("A5")
    ].drop(columns=["tract_discordance_probability"], errors="ignore")
    _table = build_great_table(
        uncertainty_feasibility,
        title="eTable 9. Uncertainty-aware agreement feasibility and results",
        notes=("PLACES-only intervals perturb comparator ranks.",
               "Joint denominator uncertainty remains explicitly not run."),
        table_id="etable_9_uncertainty_feasibility",
    )
    _ = (output_dir / "etable_9_uncertainty_feasibility.html").write_text(
        _table.as_raw_html(make_page=True), encoding="utf-8"
    )
    uncertainty_feasibility.to_csv(
        output_dir / "etable_9_uncertainty_feasibility.csv", index=False
    )
    return


@app.cell
def _(descriptive_complementarity_results, pd):
    _columns = [
        "analysis_name",
        "estimand",
        "unit",
        "condition_id",
        "eligible_n",
        "estimate",
        "sensitivity_status",
    ]
    descriptive_status_display = descriptive_complementarity_results[_columns].copy()
    descriptive_status_display["estimate"] = descriptive_status_display["estimate"].apply(
        lambda value: "—" if pd.isna(value) else f"{float(value):.3f}"
    )
    descriptive_status_display = descriptive_status_display.rename(
        columns={name: name.replace("_", " ").title() for name in _columns}
    )
    return (descriptive_status_display,)


@app.cell
def _(build_great_table, descriptive_status_display, etable_7_path, mo):
    _table = build_great_table(
        descriptive_status_display,
        title="Descriptive complementarity analysis status",
        notes=(
            "All estimates remain unauthorized.",
            "Open eTable 7 for complete methods, intervals, diagnostics, and provenance.",
        ),
        table_id="descriptive_complementarity_status",
    )
    mo.vstack(
        [
            mo.md("**A1–A5 diagnostic results.** Estimates and intervals are descriptive and remain unauthorized."),
            mo.Html(_table.as_raw_html()),
            mo.download(
                etable_7_path.read_bytes(),
                filename=etable_7_path.name,
                mimetype="text/html",
                label="Download eTable 7 with complete methods and provenance",
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ### Statistical Analysis Module 4: direct cross-frame classification consequences

    | Review item | Prespecified rule |
    |---|---|
    | Scientific question | How often does a tract's classification differ from the classification of its linked direct community-area or ZCTA measure? |
    | Estimands | Absolute percentile-rank gap, exact quartile disagreement, opposite-extreme classification, Q4 entry, Q4 exit, and coexistence of high and low tracts within a coarse area. |
    | Population and unit | CHM-complete tracts linked to a dominant direct community-area or direct ZCTA record. The unit is a tract. |
    | Variables and denominator | Direct pooled tract, community-area, and ZCTA CHM values. Condition-specific eligible tract counts and mean annual source denominators are reported separately. |
    | Mathematical definition | A tract moves into Q4 when its direct tract rank is at most 0.75 and its linked direct coarse-area rank is greater than 0.75. It moves out when the reverse holds. |
    | Estimator and uncertainty | Descriptive counts and percentages with community-area cluster percentile intervals for primary community-area comparisons. |
    | Assumptions and diagnostics | Direct exports at each geography represent sufficiently comparable CHM constructs. Coarse values are ranked once at their own geography before linkage. Crossing status and linkage dominance are audited. |
    | Missingness and suppression | Both direct CHM frames must be complete for the condition. Suppressed values are excluded. No tract disease value is geographically aggregated or imputed. |
    | Sensitivities | Noncrossing tracts, direct ZCTA labels, annual classifications, 2-of-3-year persistence, and alternative rank categories. |
    | Interpretation and references | This is a linked cross-frame comparison, not literal aggregation loss. ZCTAs are Census statistical areas, not USPS ZIP Codes. Classification change does not identify prevalence, cause, predictive superiority, or service need.<sup>18,19,22</sup> |

    The machine-readable artifact retains its legacy filename
    `supplement_aggregation_loss.csv` for reproducibility. Its rows explicitly state
    `cross_frame_only_no_literal_aggregation`. The paper and table titles use “direct cross-frame
    classification differences.” Community-area and ZCTA rows retain the audit status labels
    `geographic_resolution_sensitivity` and `direct_zcta_comparison`.
    """)
    return


@app.cell
def _(
    analytic,
    dataset_path,
    pd,
    sha256,
    summarize_community_area_aggregation_loss,
    tract_chm_direct,
    tract_chm_direct_noncrossing,
):
    aggregation_loss = pd.concat(
        [
            summarize_community_area_aggregation_loss(analytic, tract_chm_direct).assign(
                noncrossing_only=False
            ),
            summarize_community_area_aggregation_loss(
                analytic, tract_chm_direct_noncrossing
            ).assign(noncrossing_only=True),
        ],
        ignore_index=True,
        sort=False,
    )
    aggregation_loss["zip_zcta_sensitivity_status"] = "direct_zcta_comparison"
    aggregation_loss["source_artifact"] = dataset_path.name
    aggregation_loss["source_checksum"] = sha256(dataset_path.read_bytes()).hexdigest()
    return (aggregation_loss,)


@app.cell
def _(analytic, build_direct_consequence_rank_frame, tract_chm_direct, zcta_analytic):
    consequence_tract_rank = build_direct_consequence_rank_frame(analytic, "census_tract")
    _eligible_pairs = tract_chm_direct[["geography_id", "condition_id"]].drop_duplicates()
    consequence_tract_rank = consequence_tract_rank.merge(
        _eligible_pairs,
        on=["geography_id", "condition_id"],
        how="inner",
        validate="one_to_one",
    )
    consequence_community_rank = build_direct_consequence_rank_frame(
        analytic, "chicago_community_area"
    )
    consequence_zcta_rank = build_direct_consequence_rank_frame(zcta_analytic, "zcta")
    return (
        consequence_community_rank,
        consequence_tract_rank,
        consequence_zcta_rank,
    )


@app.cell
def _(analytic):
    _tract = analytic.loc[analytic["geography_type"].eq("census_tract")]
    community_consequence_link = _tract[
        [
            "geography_id",
            "community_area_id",
            "is_crossing_tract",
            "max_community_area_weight",
        ]
    ].drop_duplicates()
    community_consequence_link = community_consequence_link.loc[
        community_consequence_link["max_community_area_weight"].ge(0.99)
    ]
    if community_consequence_link["geography_id"].duplicated().any():
        raise ValueError("tract-community consequence linkage must be unique")
    community_consequence_link = community_consequence_link.rename(
        columns={"community_area_id": "comparison_geography_id"}
    )
    community_consequence_link["comparison_geography_id"] = (
        community_consequence_link["comparison_geography_id"].astype(str).str.zfill(2)
    )
    community_consequence_link["is_dominant"] = True
    return (community_consequence_link,)


@app.cell
def _(analytic, load_zcta_tract_relationship, project_root):
    _path = project_root / (
        "sources/public/census_zcta_2020_tract_relationship/snapshots/2026-07-16/"
        "original/2020/tab20_zcta520_tract20_natl.txt"
    )
    _tract_ids = set(
        analytic.loc[analytic["geography_type"].eq("census_tract"), "geography_id"].astype(str)
    )
    zcta_relationship = load_zcta_tract_relationship(_path, eligible_tract_ids=_tract_ids)
    zcta_consequence_link = zcta_relationship.rename(
        columns={"dominant_zcta_id": "comparison_geography_id"}
    )
    return zcta_consequence_link, zcta_relationship


@app.cell
def _(
    build_geographic_consequence_tables,
    community_consequence_link,
    consequence_community_rank,
    consequence_tract_rank,
):
    community_consequence_all = build_geographic_consequence_tables(
        consequence_tract_rank, consequence_community_rank, community_consequence_link,
        comparison_geography_type="chicago_community_area",
    )
    community_consequence_noncrossing = build_geographic_consequence_tables(
        consequence_tract_rank, consequence_community_rank, community_consequence_link,
        comparison_geography_type="chicago_community_area", noncrossing_only=True,
    )
    return community_consequence_all, community_consequence_noncrossing


@app.cell
def _(
    build_geographic_consequence_tables,
    consequence_tract_rank,
    consequence_zcta_rank,
    zcta_consequence_link,
):
    zcta_consequence_all = build_geographic_consequence_tables(
        consequence_tract_rank, consequence_zcta_rank, zcta_consequence_link,
        comparison_geography_type="zcta",
    )
    zcta_consequence_noncrossing = build_geographic_consequence_tables(
        consequence_tract_rank, consequence_zcta_rank, zcta_consequence_link,
        comparison_geography_type="zcta", noncrossing_only=True,
    )
    return zcta_consequence_all, zcta_consequence_noncrossing


@app.cell
def _(
    analytic,
    build_annual_direct_consequence_rank_frame,
    tract_chm_direct,
    zcta_analytic,
):
    annual_tract_rank = build_annual_direct_consequence_rank_frame(analytic, "census_tract")
    _eligible_pairs = tract_chm_direct[["geography_id", "condition_id"]].drop_duplicates()
    annual_tract_rank = annual_tract_rank.merge(
        _eligible_pairs,
        on=["geography_id", "condition_id"],
        how="inner",
        validate="many_to_one",
    )
    annual_community_rank = build_annual_direct_consequence_rank_frame(
        analytic, "chicago_community_area"
    )
    annual_zcta_rank = build_annual_direct_consequence_rank_frame(zcta_analytic, "zcta")
    return annual_community_rank, annual_tract_rank, annual_zcta_rank


@app.cell
def _(
    annual_community_rank,
    annual_tract_rank,
    build_geographic_consequence_tables,
    community_consequence_link,
):
    annual_community_all = build_geographic_consequence_tables(
        annual_tract_rank, annual_community_rank, community_consequence_link,
        comparison_geography_type="chicago_community_area",
    )
    annual_community_noncrossing = build_geographic_consequence_tables(
        annual_tract_rank, annual_community_rank, community_consequence_link,
        comparison_geography_type="chicago_community_area", noncrossing_only=True,
    )
    return annual_community_all, annual_community_noncrossing


@app.cell
def _(
    annual_tract_rank,
    annual_zcta_rank,
    build_geographic_consequence_tables,
    zcta_consequence_link,
):
    annual_zcta_all = build_geographic_consequence_tables(
        annual_tract_rank, annual_zcta_rank, zcta_consequence_link,
        comparison_geography_type="zcta",
    )
    annual_zcta_noncrossing = build_geographic_consequence_tables(
        annual_tract_rank, annual_zcta_rank, zcta_consequence_link,
        comparison_geography_type="zcta", noncrossing_only=True,
    )
    return annual_zcta_all, annual_zcta_noncrossing


@app.cell
def _(
    community_consequence_all,
    community_consequence_noncrossing,
    pd,
    zcta_consequence_all,
    zcta_consequence_noncrossing,
):
    _sets = (community_consequence_all, community_consequence_noncrossing,
             zcta_consequence_all, zcta_consequence_noncrossing)
    geographic_consequence_details = pd.concat(
        [item["details"] for item in _sets], ignore_index=True, sort=False
    )
    geographic_consequence_transitions = pd.concat(
        [item["transitions"] for item in _sets], ignore_index=True, sort=False
    )
    geographic_mixed_extremes = pd.concat(
        [item["mixed_extremes"] for item in _sets], ignore_index=True, sort=False
    )
    return (
        geographic_consequence_details,
        geographic_consequence_transitions,
        geographic_mixed_extremes,
    )


@app.cell
def _(
    annual_community_all,
    annual_community_noncrossing,
    annual_zcta_all,
    annual_zcta_noncrossing,
    pd,
    summarize_annual_consequence_stability,
):
    _sets = (annual_community_all, annual_community_noncrossing,
             annual_zcta_all, annual_zcta_noncrossing)
    geographic_consequence_annual = pd.concat(
        [item["details"] for item in _sets], ignore_index=True, sort=False
    )
    _stability = []
    for _detail in [item["details"] for item in _sets]:
        _summary = summarize_annual_consequence_stability(_detail)
        _labels = _detail[["comparison_geography_type", "sensitivity_status"]].iloc[0]
        for _kind, _frame in _summary.items():
            _stability.append(_frame.assign(result_type=_kind, **_labels.to_dict()))
    geographic_consequence_stability = pd.concat(_stability, ignore_index=True, sort=False)
    return geographic_consequence_annual, geographic_consequence_stability


@app.cell
def _(
    geographic_consequence_annual,
    geographic_consequence_details,
    geographic_consequence_stability,
    geographic_consequence_transitions,
    geographic_mixed_extremes,
    output_dir,
    zcta_relationship,
):
    _frames = {
        "supplement_geographic_consequence_details.csv": geographic_consequence_details,
        "supplement_geographic_consequence_transitions.csv": geographic_consequence_transitions,
        "supplement_geographic_mixed_extremes.csv": geographic_mixed_extremes,
        "supplement_geographic_consequence_annual.csv": geographic_consequence_annual,
        "supplement_geographic_consequence_stability.csv": geographic_consequence_stability,
        "supplement_zcta_linkage.csv": zcta_relationship,
    }
    for _name, _frame in _frames.items():
        _frame.to_csv(output_dir / _name, index=False, float_format="%.12g")
    return


@app.cell
def _(geographic_consequence_transitions, geographic_mixed_extremes):
    _primary = geographic_consequence_transitions.loc[
        geographic_consequence_transitions["sensitivity_status"].eq("all_eligible")
    ]
    _wide = _primary.pivot_table(
        index=["comparison_geography_type", "condition_id"], columns="transition_state",
        values="tract_count", aggfunc="sum", fill_value=0,
    ).reset_index()
    _mixed = geographic_mixed_extremes.loc[
        geographic_mixed_extremes["sensitivity_status"].eq("all_eligible")
    ].groupby(["comparison_geography_type", "condition_id"], as_index=False).size()
    geographic_consequence_display = _wide.merge(
        _mixed.rename(columns={"size": "mixed_coarser_areas"}),
        on=["comparison_geography_type", "condition_id"], how="left",
    ).fillna({"mixed_coarser_areas": 0})
    geographic_consequence_display["results_authorized"] = False
    return (geographic_consequence_display,)


@app.cell
def _(build_great_table, geographic_consequence_display, output_dir):
    _table = build_great_table(
        geographic_consequence_display,
        title="eTable 8. Highest-quartile direct cross-frame classification differences",
        subtitle="Direct tract vs direct community-area and ZCTA CHM ranks",
        notes=("Counts are tracts; ZCTAs are Census statistical areas, not USPS ZIP Codes.",
               "All results are descriptive, unauthorized, and do not measure individual risk."),
        table_id="etable_8_geographic_consequences",
    )
    _ = (output_dir / "etable_8_geographic_consequences.html").write_text(
        _table.as_raw_html(make_page=True), encoding="utf-8"
    )
    geographic_consequence_display.to_csv(
        output_dir / "etable_8_geographic_consequences.csv", index=False
    )
    return


@app.cell
def _(build_great_table, geographic_consequence_display, mo):
    _table = build_great_table(
        geographic_consequence_display,
        title="eTable 8. Highest-quartile direct cross-frame classification differences",
        notes=("Source denominators are reported separately and are not unique people.",),
        table_id="etable_8_geographic_consequences_notebook",
    )
    mo.Html(_table.as_raw_html())
    return


@app.cell
def _(
    BOOTSTRAP_SEED,
    cluster_bootstrap_concordance,
    cut_point_text,
    tract_percentile,
):
    bootstrap = cluster_bootstrap_concordance(
        tract_percentile, n_replicates=1000, seed=BOOTSTRAP_SEED
    )
    bootstrap["capture_quartile_cut_points"] = cut_point_text
    bootstrap["capture_quartile_cut_point_source"] = "governed_community_area_eligible_population"
    return (bootstrap,)


@app.cell
def _(
    aggregation_loss,
    bootstrap,
    complementarity_summary,
    geographic_resolution_matrix,
    heterogeneity_summary,
    output_dir,
):
    complementarity_summary.to_csv(
        output_dir / "supplement_tract_complementarity.csv", index=False, float_format="%.12g"
    )
    heterogeneity_summary.to_csv(
        output_dir / "supplement_within_community_heterogeneity.csv",
        index=False,
        float_format="%.12g",
    )
    aggregation_loss.to_csv(
        output_dir / "supplement_aggregation_loss.csv", index=False, float_format="%.12g"
    )
    geographic_resolution_matrix.to_csv(
        output_dir / "supplement_geographic_resolution_matrix.csv",
        index=False,
        float_format="%.12g",
    )
    bootstrap.to_csv(
        output_dir / "supplement_concordance_bootstrap.csv", index=False, float_format="%.12g"
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Supplementary Statistical Analysis Module 5: community-area life expectancy

    | Review item | Prespecified rule |
    |---|---|
    | Scientific question | Can the resource support a transparent ecological linkage to one policy-relevant community-area outcome after prespecified adjustment? |
    | Estimand | Adjusted mean difference in community-area life expectancy per exposure IQR. The combined diabetes contrast is not estimated while phenotype semantics are unresolved. |
    | Population and unit | Community areas with complete direct CHM exposure, life expectancy, and locked covariates. The unit is a community area. |
    | Variables and denominator | Life expectancy, CHM diagnosed proportion, percentage aged 65 years or older, percentage female, percentage below the federal poverty level, and pooled 2022-2024 capture. Adult population is used only for prespecified weighting sensitivities. |
    | Mathematical definition | $LE_i=\alpha+\beta X_i+\gamma^T Z_i+\epsilon_i$. Exposures are scaled by the frozen IQR and covariates by 1 SD. |
    | Estimator and uncertainty | Unweighted OLS with HC3 covariance.<sup>13</sup> The current code uses normal critical values. A t-critical-value sensitivity is required for sign-off. |
    | Assumptions and diagnostics | Linear conditional mean, full rank, adequate support, acceptable VIF, residual behavior, leverage, Cook distance, leave-one-area-out influence, and residual Moran I are reviewed. |
    | Missingness and suppression | Complete community areas only. Do not impute life expectancy or disease measures. A model with fewer than 70 areas, insufficient exposure support, or failed semantic gates is withheld. |
    | Sensitivities | Population weighting, capture strata, annual and leave-one-year-out exposures, disruption period, influential-area omission, and spatial-error model. |
    | Interpretation and references | Coefficients are ecological associations and a demonstration of analytic linkage. They do not validate tract data, estimate individual effects, identify mechanisms, or establish causality.<sup>6,13,18,19,23</sup> |
    """)
    return


@app.cell
def _(
    analytic,
    assess_primary_model_readiness,
    build_model_gate_diagnostics,
    build_primary_community_frame,
    expected_model_n,
):
    primary_frame = build_primary_community_frame(analytic)
    readiness = assess_primary_model_readiness(primary_frame)
    model_gate_diagnostics = build_model_gate_diagnostics(primary_frame)
    observed_n = dict(zip(readiness["model_id"], readiness["n_complete"], strict=True))
    if observed_n != expected_model_n:
        raise ValueError(f"model populations changed: {observed_n}")
    expected_status = {
        "C1": "withheld_insufficient_complete_areas",
        "C2": "ready_for_adjusted_primary_model",
    }
    observed_status = dict(zip(readiness["model_id"], readiness["status"], strict=True))
    if observed_status != expected_status:
        raise ValueError(f"adjusted model readiness changed: {observed_status}")
    return model_gate_diagnostics, primary_frame, readiness


@app.cell
def _(mo, reader_cards):
    _lines = [
        f"- **{card['question']}** {card['observed_pattern']} "
        f"Read the {card['exact_value_location']}; unit: {card['unit_denominator']}."
        for card in reader_cards.values()
    ]
    mo.md(
        "### How to read these results\n\n"
        "These five displays are descriptive geographic evidence. Read each question, then "
        "check its denominator, uncertainty or not-run state, sensitivity, and inference boundary.\n\n"
        + "\n".join(_lines)
    )
    return


@app.cell
def _(
    analytic,
    geographic_consequence_stability,
    geographic_main_evidence,
    primary_rows,
    readiness,
    robustness_summary,
    spatial_diagnostics,
    spatial_error_sensitivity,
    table_1_full,
):
    _community = table_1_full.loc[table_1_full["geography_type"].eq("chicago_community_area")]
    _tract = table_1_full.loc[table_1_full["geography_type"].eq("census_tract")]
    _geo = geographic_main_evidence.set_index("condition_id")
    _c2 = primary_rows.loc[primary_rows["estimand_id"].eq("C2")].iloc[0]
    _c1 = robustness_summary.query("model == 'C1' and variant == 'continuous_capture_reference'").iloc[0]
    _moran = spatial_diagnostics.loc[spatial_diagnostics["model_id"].eq("C2")].iloc[0]
    _spatial = spatial_error_sensitivity.query("model_id == 'C2' and row_type == 'spatial_error_contrast'").iloc[0]
    _annual = geographic_consequence_stability.query(
        "result_type == 'annual_jaccard' and comparison_geography_type == 'chicago_community_area'"
    )
    review_values = {
        "community_rows": int(_community["rows"].sum()), "community_eligible": int(_community["disease_measure_eligible_rows"].sum()),
        "community_suppressed": int(_community["suppressed_rows"].sum()), "tract_rows": int(_tract["rows"].sum()),
        "tract_eligible": int(_tract["disease_measure_eligible_rows"].sum()), "tract_suppressed": int(_tract["suppressed_rows"].sum()),
        "tract_geographies": int(analytic.loc[analytic["geography_type"].eq("census_tract"), "geography_id"].nunique()),
        "geo": _geo, "c2": _c2, "c1": _c1, "moran": _moran, "spatial": _spatial,
        "annual": _annual, "c1_status": readiness.set_index("model_id").loc["C1", "status"],
    }
    return (review_values,)


@app.cell
def _(review_values):
    _h, _c = review_values["geo"].loc["hypertension"], review_values["geo"].loc["copd"]
    _c1, _c2 = review_values["c1"], review_values["c2"]
    _m, _s = review_values["moran"], review_values["spatial"]
    _annual = review_values["annual"].groupby("condition_id")["top_quartile_jaccard"].agg(["min", "max"])
    review_summary = {
        "resource": f"The community-area resource contained {review_values['community_rows']:,} condition-year records; {review_values['community_eligible']:,} ({100*review_values['community_eligible']/review_values['community_rows']:.1f}%) were eligible and {review_values['community_suppressed']:,} were suppressed.",
        "coverage": f"The mapped resource included {review_values['tract_geographies']:,} primary-boundary tracts and 77 community areas. Across tract condition-year records, {review_values['tract_eligible']:,} of {review_values['tract_rows']:,} were eligible and {review_values['tract_suppressed']:,} were suppressed.",
        "alignment": f"Direct tract and linked community-area quartiles disagreed for {_h['quartile_disagree_count']:.0f} of {int(_h['resolution_eligible_n'])} hypertension tracts ({_h['quartile_disagree_pct']:.1f}%) and {_c['quartile_disagree_count']:.0f} of {int(_c['resolution_eligible_n'])} COPD tracts ({_c['quartile_disagree_pct']:.1f}%). Within-community variation accounted for {_h['within_variance_share']:.3f} of observed tract variation in hypertension and {_c['within_variance_share']:.3f} in COPD. In the secondary cross-source analysis, Spearman rho was {_h['spearman_r']:.3f} for hypertension and {_c['spearman_r']:.3f} for COPD.",
        "classification": f"Community-area labels moved {_h['q4_movers_n']:.0f} hypertension tracts and {_c['q4_movers_n']:.0f} COPD tracts into or out of Q4. Annual Q4 Jaccard overlap ranged from {100*_annual.loc['hypertension','min']:.1f}% to {100*_annual.loc['hypertension','max']:.1f}% for hypertension and {100*_annual.loc['copd','min']:.1f}% to {100*_annual.loc['copd','max']:.1f}% for COPD.",
        "primary_findings": f"In this ecological repeated-period analysis, tract and community-area quartiles disagreed for {_h['quartile_disagree_count']:.0f} of {int(_h['resolution_eligible_n'])} hypertension tracts ({_h['quartile_disagree_pct']:.1f}%) and {_c['quartile_disagree_count']:.0f} of {int(_c['resolution_eligible_n'])} COPD tracts ({_c['quartile_disagree_pct']:.1f}%). The community-area labels moved {_h['q4_movers_n']:.0f} and {_c['q4_movers_n']:.0f} tracts, respectively, into or out of the highest quartile.",
        "primary_abstract": f"Direct tract and linked community-area quartiles disagreed for {_h['quartile_disagree_count']:.0f} of {int(_h['resolution_eligible_n'])} hypertension tracts ({_h['quartile_disagree_pct']:.1f}%) and {_c['quartile_disagree_count']:.0f} of {int(_c['resolution_eligible_n'])} COPD tracts ({_c['quartile_disagree_pct']:.1f}%). Within-community variation accounted for {_h['within_variance_share']:.3f} of observed tract variation in hypertension and {_c['within_variance_share']:.3f} in COPD. Community-area labels moved {_h['q4_movers_n']:.0f} of {int(_h['q4_transition_eligible_n'])} hypertension tracts ({_h['q4_movers_pct']:.1f}%) and {_c['q4_movers_n']:.0f} of {int(_c['q4_transition_eligible_n'])} COPD tracts ({_c['q4_movers_pct']:.1f}%) into or out of the highest quartile. Primary cluster-bootstrap intervals remain pending statistician approval and are not reported here.",
        "geographic_metrics": f"For hypertension, exact tract/community quartile agreement was {_h['exact_quartile_agreement_count']:.0f} of {int(_h['resolution_eligible_n'])} tracts ({_h['exact_quartile_agreement_pct']:.1f}%), the within-community variance share was {_h['within_variance_share']:.3f}, and {_h['q4_movers_n']:.0f} of {int(_h['q4_transition_eligible_n'])} tracts ({_h['q4_movers_pct']:.1f}%) moved into or out of Q4. Corresponding COPD estimates were {_c['exact_quartile_agreement_count']:.0f} of {int(_c['resolution_eligible_n'])} ({_c['exact_quartile_agreement_pct']:.1f}%), {_c['within_variance_share']:.3f}, and {_c['q4_movers_n']:.0f} of {int(_c['q4_transition_eligible_n'])} ({_c['q4_movers_pct']:.1f}%).",
        "c2": f"Among {int(_c2['n'])} eligible community areas, a 1-IQR higher recorded COPD proportion was associated with {_c2['estimate']:.2f} years of life expectancy (97.5% CI, {_c2['ci_low']:.2f} to {_c2['ci_high']:.2f}) after adjustment. Residual Moran I was {_m['observed_i']:.3f} (permutation P={_m['permutation_p_value']:.4f}); the spatial-error estimate was {_s['estimate']:.2f} years and did not change direction.",
        "c1": "The prespecified C1 model was not run because mutual exclusivity and denominator equivalence for the 2 diabetes components remain unapproved. No coefficient, confidence interval, influence result, or residual diagnostic was estimated.",
    }
    return (review_summary,)


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    ## 3. Results

    ### Restricted statistician review outputs — not for manuscript import

    This label applies to every numerical table, figure, diagnostic, and robustness output in
    sections 3 and 5. These aggregate outputs are provisional quality-control evidence for the
    statistician. They are not authorized manuscript or coauthor results.

    ### Chicago Health Map data resource

    {review_summary["resource"]} These counts describe geographic condition-year records, not
    unique patients. Numerical findings in this section are available to the independent
    statistician and remain ineligible for manuscript import while `results_authorized=false`.
    """)
    return


@app.cell
def _(mo, review_summary):
    mo.md(
        "#### How to interpret Table 1\n\n" + review_summary["resource"]
        + " Table 1 quantifies source completeness before any geographic comparison."
    )
    return


@app.cell
def _(mo):
    mo.md("""
    #### Table 1. Chicago Health Map community-area data coverage, 2019–2024

    Counts use exact source-row denominators. Missing, suppressed, unavailable-reliability, and
    analytically ineligible states are distinct; no disease value was imputed.
    """)
    return


@app.cell
def _(table_1_display):
    table_1_display
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    **Results, Table 1:** {review_summary["resource"]}
    """)
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    **Biostatistical interpretation, Table 1:** {review_summary["resource"]} Eligibility is nearly
    complete at the community-area level, but reliability qualification is unavailable and the
    condition-record denominator has not been confirmed as a unique-person count. Obtain the
    source eligibility, deduplication, denominator, and reliability rules before treating coverage
    differences as measurement quality.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Coauthor interpretation, Table 1:** Community-area disease values were usually available.
    The table does not show how representative the observed CAPriCORN adults were of all Chicago
    residents and does not convert source denominators into unique-patient counts.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Figure 1. Chicago Health Map geographic coverage and data quality

    Panels show record flow, observed capture, analytic inclusion, and qualification status at
    journal dimensions. Maps use complete legends and exact units; hatching denotes unavailable
    data and outlines denote withheld qualification. No outcome-model branches or coefficients
    are part of this resource display.
    """)
    return


@app.cell
def _(figure_1):
    figure_1
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    **Biostatistical interpretation, Figure 1:** {review_summary["coverage"]} Suppression and
    capture vary by condition and geographic level, so later panels use condition-specific
    denominators. Capture is source-published metadata, not a sampling probability. Supplement
    this display with the exact capture numerator, denominator, vintage, and deduplication rule,
    plus a governed reliability threshold.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Coauthor interpretation, Figure 1:** The map shows where data were available and where source
    suppression reduced the analytic frame. It does not show population coverage or disease
    prevalence among all Chicago residents.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Geographic alignment and cross-scale classification

    #### Analysis population and estimands

    For each condition, eligible census tracts were compared with the corresponding PLACES
    measure on percentile rank. Direct tract CHM quartiles were then compared with the linked
    direct community-area CHM quartile. Missing and suppressed disease values were not imputed.
    Because metric eligibility differs, each panel and Table 2 retain their own denominator.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Coauthor callout — geographic alignment:** The first row asks whether CHM and PLACES put
    tracts in a similar order. The second asks whether a linked, direct community-area label gives
    the tract the same quartile. Agreement and disagreement can coexist; neither comparison shows
    that either source is correct or that one geography is universally preferable.
    """)
    return


@app.cell
def _(review_summary):
    biostatistical_c1 = review_summary["c1"] + (
        " The statistician should decide whether to retain the joint estimand, report separate"
        " exposure models as sensitivity analyses, or revise the SAP before refitting."
    )
    coauthor_c1 = review_summary["c1"] + " No C1 coefficient should be interpreted as a primary result."
    c1_result_narrative = {"biostatistician": biostatistical_c1, "coauthor": coauthor_c1}
    return (c1_result_narrative,)


@app.cell
def _(mo):
    mo.md("""
    #### Figure 2. Added geographic information from tract-level measures

    The top row compares direct tract quartiles with direct community-area quartiles, the primary
    geographic-resolution comparison. The bottom row compares CHM and PLACES percentile ranks as
    secondary cross-source context. Both combined-diabetes panels are not run pending the
    documented eligibility decisions. Exact agreement and classification metrics are reported in
    Table 2.
    """)
    return


@app.cell
def _(figure_2):
    figure_2
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    **Results, Figure 2:** {review_summary["alignment"]}
    """)
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    **Biostatistical interpretation, Figure 2:** {review_summary["alignment"]} Direct cross-frame
    disagreement and within-area variance address added geographic information. PLACES rank
    correlation addresses cross-source ordering and is secondary. PLACES is not a criterion
    standard, metric-specific denominators differ, and tracts within the same community area are
    dependent. Report the existing 1000-replicate community-area cluster-bootstrap intervals and
    have the statistician approve the clustering unit and percentile interval definition.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Coauthor interpretation, Figure 2:** Community-area labels concealed more tract variation
    for COPD than for hypertension. The secondary PLACES comparison showed that cross-source
    alignment also differed by condition. Neither comparison establishes which source or
    geographic level is correct.
    """)
    return


@app.cell
def _(review_summary):
    descriptive_coauthor_interpretation = (
        "#### How to interpret tract complementarity\n\n" + review_summary["alignment"]
        + " Alignment does not imply interchangeability, and disagreement does not identify error."
    )
    return (descriptive_coauthor_interpretation,)


@app.cell
def _(descriptive_coauthor_interpretation, mo):
    mo.md(descriptive_coauthor_interpretation)
    return


@app.cell
def _(review_summary):
    geographic_consequence_interpretation = (
        "#### Biostatistical interpretation, direct cross-frame differences\n\n"
        + review_summary["classification"]
        + " These are direct cross-frame classifications, not tract values aggregated to areas."
    )
    return (geographic_consequence_interpretation,)


@app.cell
def _(geographic_consequence_interpretation, mo):
    mo.md(geographic_consequence_interpretation)
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    #### Coauthor interpretation, direct cross-frame differences

    {review_summary["classification"]} A community-area label can hide tract-level variation. The counts
    do not identify misclassification against a truth standard.
    """)
    return


@app.cell
def _(
    aggregation_loss,
    build_great_table,
    complementarity_summary,
    output_dir,
):
    _complementarity = build_great_table(
        complementarity_summary,
        title="eTable 5. Tract concordance and heterogeneity",
        table_id="etable_5_tract_complementarity",
    )
    _resolution = build_great_table(
        aggregation_loss,
        title="eTable 6. Geographic-resolution sensitivity",
        table_id="etable_6_geographic_resolution",
    )
    _ = (output_dir / "etable_5_tract_complementarity.html").write_text(
        _complementarity.as_raw_html(make_page=True), encoding="utf-8"
    )
    _ = (output_dir / "etable_6_geographic_resolution.html").write_text(
        _resolution.as_raw_html(make_page=True), encoding="utf-8"
    )
    return


@app.cell
def _(figure_3, mo):
    mo.md("""
    #### Figure 3. Direct cross-frame classification differences and stability

    Figure 3 reports condition-specific Q4 transitions, represented mean annual source
    denominators, community areas containing both Q1 and Q4 tracts, annual Q4 overlap, and the
    noncrossing-tract sensitivity. Denominators are repeated source observations, not unique
    people. The annual and noncrossing quantities are different descriptive stability measures.
    """)
    figure_3
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    **Results, Figure 3:** {review_summary["classification"]}
    """)
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    **Biostatistical interpretation, Figure 3:** {review_summary["classification"]} Q4 movement, annual
    Jaccard overlap, and noncrossing disagreement are separate descriptive estimands. Mean annual
    source denominators are repeated condition records, not unique people. Add a patient-deduplicated
    denominator if available and prespecify which stability metric will support the final claim.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Coauthor interpretation, Figure 3:** Highest-quartile membership differed when direct tract
    classifications were compared with linked direct community-area classifications, and annual membership was only partly stable. These patterns show the
    consequence of geographic labeling, not individual movement or a change in clinical status.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Table 2. Geographic alignment and direct cross-frame classification differences by condition

    Table 2 supplies exact metric-specific denominators for direct tract/community quartile
    agreement, disagreement, within-community variance share, and Q4 movement. VPC, area-label
    AUC, CHM-PLACES agreement, and their cluster-bootstrap intervals remain in numbered
    supplementary artifacts. Before manuscript import, the statistician must approve the
    primary estimand hierarchy and interval presentation.
    """)
    return


@app.cell
def _(mo, table_2_html):
    mo.Html(table_2_html)
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    #### Biostatistical interpretation

    {review_summary["geographic_metrics"]} Table 2 addresses the primary geographic-resolution
    question. Exact agreement and disagreement quantify classification stability. The
    within-community variance share quantifies tract heterogeneity hidden by the coarser label. Q4
    movement identifies tracts whose highest-quartile classification changes. Each percentage is
    paired with its own eligible denominator. VPC, AUC, CHM-PLACES agreement, and uncertainty
    diagnostics remain in the supplement for separate review.
    """)
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    #### Coauthor interpretation

    {review_summary["geographic_metrics"]} Tract and community-area labels can describe the same
    condition differently because community-area summaries conceal within-area variation. This is
    the study's added-information result. It does not establish which geography is clinically
    correct, and the combined diabetes analysis remains not run.
    """)
    return


@app.cell
def _(pd, review_summary):
    _rows = [
        ("Table 1", review_summary["resource"], "Records are not unique patients; reliability and denominator semantics are unresolved.", "Obtain source eligibility, deduplication, denominator, and reliability rules."),
        ("Figure 1", review_summary["coverage"], "Capture is metadata, not a sampling probability; suppression varies by condition.", "Add the governed capture definition and a patient-deduplicated flow if available."),
        ("Figure 2", review_summary["alignment"], "PLACES is not a truth standard; metric-specific samples differ; tracts cluster within areas.", "Approve 1000 cluster-bootstrap replicates, tie rules, and compatible source-uncertainty analysis."),
        ("Figure 3", review_summary["classification"], "Q4 movement, Jaccard overlap, and noncrossing disagreement are different estimands.", "Prespecify the claim-supporting stability metric and add unique-person denominators if available."),
        ("Table 2", review_summary["geographic_metrics"], "The metrics measure different constructs and cannot be ranked on one accuracy scale.", "Add approved cluster-bootstrap intervals and retain metric-specific denominators."),
    ]
    main_display_review = pd.DataFrame(_rows, columns=["Display", "Review result", "Main limitation", "Needed supplement or decision"])
    return (main_display_review,)


@app.cell
def _(pd, review_summary):
    _rows = [
        ("eTable 1", "Full resource-quality and tract accounting behind Table 1.", "Geography-condition-year accounting does not establish representativeness.", "Document source population, reliability rule, and unique-patient denominator."),
        ("eTable 2", review_summary["c1"] + " " + review_summary["c2"], "C1 failed its gate; C2 has 76 areas and residual spatial dependence.", "Approve estimand status, critical values, weights, and spatial sensitivity."),
        ("eTable 3", "All C2 exposure, adjustment, and intercept coefficients with HC3 intervals.", "Adjustment coefficients are not etiologic effects and share one small ecological sample.", "Review coding, scaling, covariance choice, and coefficient correlation."),
        ("eTable 4", "Temporal, weighting, capture, influence, and spatial-weight sensitivity estimates.", "Variants are supportive and were not designed as separate confirmatory tests.", "Approve the fragility thresholds and identify the sensitivity analyses required in the paper."),
        ("eTable 5", review_summary["alignment"], "Agreement depends on rank ties, categories, clustering, and source role.", "Approve kappa weights, AC1 categories, tie rules, and production bootstrap count."),
        ("eTable 6", review_summary["classification"], "Linked area values are direct measures, not literal aggregations of tract values.", "Add an explicitly population-weighted aggregation experiment only if a valid crosswalk estimand is approved."),
        ("eTable 7", "Estimator, uncertainty, availability, and governance status for A1 through A7.", "A methods-status table cannot resolve open statistical choices.", "Sign the VPC, AUC, bootstrap, agreement, and spatial decision rows."),
        ("eTable 8", "Condition-specific Q4 transitions and represented mean annual source denominators.", "Source denominators are repeated records rather than unique people.", "Add deduplicated denominators or retain the current source-record label."),
        ("eTable 9", "Uncertainty-aware agreement ran only where compatible uncertainty inputs existed.", "Missing CHM and comparator uncertainty prevents joint error propagation.", "Obtain standard errors, replicate weights, or validated uncertainty bounds from both sources."),
    ]
    supplement_table_review = pd.DataFrame(_rows, columns=["Display", "Review result", "Main limitation", "Needed supplement or decision"])
    return (supplement_table_review,)


@app.cell
def _(pd, review_summary):
    _rows = [
        ("eFigure 1", "Source assembly, joins, exclusions, and analytic-frame counts.", "Counts mix records and areas and are not patient attrition.", "Add a unique-patient flow only if governed identifiers permit deduplication."),
        ("eFigure 2", "Annual availability, suppression, denominator, and capture patterns.", "Annual changes may reflect source operations or denominator definitions.", "Annotate source-policy changes and verify denominator semantics by year."),
        ("eFigure 3", "Cardiometabolic quartile, VPC, and AUC review outputs; diabetes remains not run.", "AUC is area-label separation, not disease prediction; VPC is an observed-scale descriptive partition.", "Approve the VPC estimator, AUC construct, and combined-diabetes semantics."),
        ("eFigure 4", review_summary["alignment"], "Cross-source agreement lacks joint source-uncertainty propagation.", "Add approved cluster intervals and source-uncertainty analysis when inputs exist."),
        ("eFigure 5", "Local Moran I and Getis-Ord Gi* counts before and after FDR control.", "Findings depend on topology, permutation count, and FDR family.", "Approve weights, 9999 permutations, local statistics, and family boundaries."),
        ("eFigure 6", review_summary["c1"], "No C1 analytic population exists while combined-diabetes semantics remain unapproved.", "Document mutual exclusivity and denominator equivalence before any C1 fit."),
        ("eFigure 7", review_summary["c2"], "Ecological coefficients are noncausal and CIs omit source-measurement error.", "Approve z vs t critical values and inspect the full covariance and diagnostics."),
        ("eFigure 8", "C2 residual, Q-Q, leverage, and Cook-distance diagnostics for 76 areas.", "Graphical diagnostics have limited power in a small spatial sample.", "Review flagged areas, residual shape, and influence thresholds with leave-one-area-out results."),
        ("eFigure 9", "C2 temporal, weighting, capture, and influence sensitivity estimates.", "Sensitivity variants do not eliminate ecological or selection bias.", "Identify the prespecified minimum set for the final supplement."),
        ("eFigure 10", review_summary["c2"], "The spatial-error fit uses one primary topology and a bounded maximum-likelihood estimate of lambda.", "Approve queen, rook, and connected-distance weights plus the spatial-error estimator."),
        ("eFigure 11", review_summary["classification"], "ZCTAs are Census statistical areas, not USPS ZIP Codes; cross-frame values are direct.", "Retain community-area and ZCTA results as separate sensitivities and document crosswalk rules."),
        ("eFigure 12", "Counts of local spatial signals before and after BH-FDR.", "FDR control is conditional on declared families and does not prove cluster reproducibility.", "Approve family definitions and repeat under alternative spatial weights."),
    ]
    supplement_figure_review = pd.DataFrame(_rows, columns=["Display", "Review result", "Main limitation", "Needed supplement or decision"])
    return (supplement_figure_review,)


@app.cell
def _(
    build_great_table,
    main_display_review,
    output_dir,
    pd,
    supplement_figure_review,
    supplement_table_review,
):
    display_review = pd.concat([main_display_review, supplement_table_review, supplement_figure_review], ignore_index=True)
    _table = build_great_table(display_review, title="Biostatistical review matrix for every table and figure", subtitle="Aggregate result, interpretation limit, and required supplement or decision", table_id="biostatistical_display_review")
    display_review_html = _table.as_raw_html()
    display_review.to_csv(output_dir / "biostatistical_display_review.csv", index=False)
    _ = (output_dir / "biostatistical_display_review.html").write_text(_table.as_raw_html(make_page=True), encoding="utf-8")
    return (display_review_html,)


@app.cell
def _(display_review_html, mo):
    mo.vstack([
        mo.md("""
        ### Biostatistical review of every numbered display

        This matrix states what each display currently shows, the limitation that constrains its
        interpretation, and the additional data or statistical decision needed before manuscript use.
        """),
        mo.Html(display_review_html),
    ])
    return


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    ## 4. Discussion

    ### Principal finding and scientific contribution

    {review_summary["alignment"]} {review_summary["classification"]} The scientific contribution is
    evidence about a data source, not the existence of an interactive website. The
    multi-institution EHR resource retained measurable within-city geographic information that was
    not retained by linked direct community-area classifications. Explicit capture, suppression, and
    provenance metadata made that information auditable.

    ### Relevance to public health surveillance

    The results define a supplementary role for health-system research data. Population-based
    public health sources remain the basis for estimating community health. CHM adds a selected
    clinical lens that can reveal variation in recorded diagnoses within the boundaries used for
    public reporting. The results support complementarity rather than interchangeability. Used
    together, the sources can show where geographic patterns align and
    where an apparent difference warrants additional measurement or community assessment. A
    difference does not identify which source is correct.<sup>1-5,7</sup>

    This division of roles is the paper's policy relevance. Health-system data can help test
    whether a coarse label conceals local clinical variation, monitor source-specific patterns over
    repeated periods, and generate questions for public health partners. Population-based sources
    remain necessary for population inference, calibration, and comparison across communities.
    Neither source alone establishes unmet need, service location, or intervention benefit.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Limitations

    Selection into CAPriCORN limits generalizability to all Chicago residents. CHM measures reflect
    clinical contact, diagnosis, coding, address quality, and participating-system coverage. The
    analysis could not independently verify the website's cross-system deduplication or phenotype
    claims. CHM and PLACES use different source populations, constructs, and periods. Suppression
    and incomplete denominator semantics limit data-quality interpretation. Tracts within community
    areas are dependent, and compatible source uncertainty was unavailable for a joint
    uncertainty-aware comparison. The combined diabetes analysis was not run. Spatial results
    depend on the weights matrix and FDR family.

    ### Conclusions

    With these limits, Chicago Health Map provides a scientifically testable supplementary source
    of tract-level information on EHR-diagnosed proportions among observed CAPriCORN adults. A next
    study should add patient-deduplicated flow counts, validated phenotype and denominator
    documentation, formal coverage calibration, joint source uncertainty, and prospective tests of
    whether tract information changes public health assessment. The present study does not
    estimate population prevalence, individual risk, causal effects, underdiagnosis, access
    failure, service need, or intervention benefit.

    Aggregate findings are shown for biostatistical review. Manuscript and coauthor import remains
    closed while `results_authorized=false`.
    """)
    return


@app.cell
def _(
    build_adjusted_residuals,
    build_coefficient_table,
    fit_audit_only_exploratory_models,
    fit_minimally_adjusted_sensitivities,
    fit_primary_models,
    primary_frame,
    readiness,
):
    _ = readiness
    primary_results = fit_primary_models(primary_frame)  # noqa: F821
    audit_only_results = fit_audit_only_exploratory_models(primary_frame)
    coefficient_table = build_coefficient_table(primary_results)  # noqa: F821
    primary_adjusted_residuals = build_adjusted_residuals(primary_results)  # noqa: F821
    audit_adjusted_residuals = (
        build_adjusted_residuals(audit_only_results) if audit_only_results else {}
    )
    sensitivities = fit_minimally_adjusted_sensitivities(primary_frame)
    return (
        audit_adjusted_residuals,
        audit_only_results,
        coefficient_table,
        primary_adjusted_residuals,
        primary_results,
        sensitivities,
    )


@app.cell
def _(mo):
    mo.md("""
    ## 5. Supplementary analyses and reproducibility artifacts

    **Restricted statistician review outputs — not for manuscript import.** Every numerical
    diagnostic and sensitivity result in this section is provisional quality-control evidence.

    ### Cardiometabolic model gate and diagnostic analyses

    The combined cardiometabolic model was not run because mutual exclusivity and denominator
    equivalence for the 2 diabetes components have not been approved. No adjusted, unadjusted,
    annual, influence, or spatial C1 estimate is produced. The prior collinearity diagnostic is
    historical and does not replace this earlier phenotype gate.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Supplementary outcome-model methods

    The secondary ecological model was y_i = alpha + beta x_i + gamma Z_i + error_i for one
    community area. Alpha is the centered intercept, beta is the life-expectancy difference per
    frozen-IQR CHM exposure, and gamma contains slopes for age 65 years or older, female sex,
    poverty, and pooled 2022–2024 EHR capture. HC3 covariance was used. Primary contrasts used
    97.5% CIs. The cardiometabolic joint contrast was not run because combined diabetes semantics
    remain unapproved. The COPD
    contrast used residual Moran diagnostics and prespecified spatial-error sensitivity. All
    tests were two-sided; missing values were not imputed.
    """)
    return


@app.cell
def _(analytic, summarize_temporal_robustness):
    temporal_all, leave_one_year_out = summarize_temporal_robustness(analytic)
    disruption_mask = temporal_all["row_type"].eq("disruption_candidate")
    disruption_mask |= temporal_all["analysis_id"].eq("exclude_confirmed_disruption_areas")
    disruption_audit = temporal_all.loc[disruption_mask].copy()
    temporal_models = temporal_all.loc[~temporal_all.index.isin(disruption_audit.index)].copy()
    return disruption_audit, leave_one_year_out, temporal_models


@app.cell
def _(disruption_audit, leave_one_year_out, output_dir, temporal_models):
    temporal_models.to_csv(
        output_dir / "supplement_temporal_models.csv", index=False, float_format="%.12g"
    )
    leave_one_year_out.to_csv(
        output_dir / "supplement_leave_one_year_out.csv", index=False, float_format="%.12g"
    )
    disruption_audit.to_csv(
        output_dir / "supplement_disruption_audit.csv", index=False, float_format="%.12g"
    )
    return


@app.cell
def _(c1_result_narrative, mo):
    mo.vstack(
        [
            mo.md("#### Biostatistical interpretation — Cardiometabolic joint analysis"),
            mo.md(c1_result_narrative["biostatistician"]),
            mo.md("#### Co-author interpretation — Cardiometabolic joint analysis"),
            mo.md(c1_result_narrative["coauthor"]),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md("""
    #### Interpretation boundary — Cardiometabolic joint analysis

    CHM and public cardiometabolic measures were geographically aligned but not interchangeable.
    Tract-scale discordance and within-area heterogeneity describe information hidden by the
    community-area boundary. The adjusted joint coefficient was not estimated because combined
    diabetes semantics remain unapproved. Descriptive agreement does not replace that gate.
    """)
    return


@app.cell
def _(
    analytic,
    build_adjusted_diagnostic_data,
    build_adjusted_temporal_robustness,
    build_governed_robustness_summary,
    build_great_table,
    output_dir,
    pd,
    primary_frame,
):
    robustness_summary = build_governed_robustness_summary(primary_frame)
    adjusted_temporal_robustness = build_adjusted_temporal_robustness(analytic, primary_frame)
    robustness_summary = pd.concat(
        [robustness_summary, adjusted_temporal_robustness],
        ignore_index=True,
        sort=False,
    ).sort_values(["model", "estimand", "variant"], kind="mergesort")
    adjusted_diagnostic_data = build_adjusted_diagnostic_data(primary_frame)
    robustness_summary.to_csv(
        output_dir / "supplement_robustness_summary.csv",
        index=False,
        float_format="%.12g",
    )
    _table = build_great_table(
        robustness_summary,
        title="eTable 4. Robustness and alternative spatial weights",
        table_id="etable_4_robustness_summary",
    )
    _ = (output_dir / "etable_4_robustness_summary.html").write_text(
        _table.as_raw_html(make_page=True), encoding="utf-8"
    )
    adjusted_diagnostic_data.to_csv(
        output_dir / "supplement_adjusted_diagnostic_data.csv",
        index=False,
        float_format="%.12g",
    )
    return adjusted_diagnostic_data, robustness_summary


@app.cell
def _(mo, review_summary):
    mo.md(f"""
    ### COPD association analysis

    #### Analysis population and uncertainty

    {review_summary["c2"]} The 97.5% HC3 interval reflects the 2-estimand primary multiplicity
    plan. It does not address source-measurement error, unmeasured ecological confounding, or all
    forms of spatial dependence. The estimate is visible for independent statistical review and
    remains ineligible for manuscript import.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — COPD association analysis:** This is the same neighborhood-level question with COPD
    as the recorded condition. The map and residual check ask whether geography changes how we
    read the pattern; they do not turn an area association into an individual or causal claim.
    """)
    return


@app.cell
def _(review_summary):
    biostatistical_c2 = review_summary["c2"] + (
        " The residual spatial trigger was crossed, and the spatial-error sensitivity preserved"
        " the direction and magnitude classification. Review the HC3 critical value, weights"
        " matrix, lambda search, and residual diagnostics before accepting the estimate."
    )
    coauthor_c2 = review_summary["c2"] + (
        " This is an area-level association among observed CAPriCORN adults, not an individual"
        " effect or a population-prevalence comparison."
    )
    c2_result_narrative = {"biostatistician": biostatistical_c2, "coauthor": coauthor_c2}
    return (c2_result_narrative,)


@app.cell
def _(mo):
    mo.md("""
    #### Supplementary COPD model displays

    The candidate adjusted association, coefficient forest, residual diagnostics, spatial-error
    sensitivity, temporal analyses, weighting analyses, and influence analyses are retained in
    the numbered supplement. They are secondary to the geographic main evidence and remain
    unauthorized for manuscript import.
    """)
    return


@app.cell
def _(figure_3):
    _suppressed_duplicate_main_figure = figure_3
    return


@app.cell
def _(mo):
    mo.md("""
    ### Sensitivity and diagnostic analyses — COPD association analysis

    Residual, Q-Q, leverage, Cook-distance, annual, leave-one-year-out, weighting, capture,
    influence, Moran, alternative-weight, and spatial-error checks are reported immediately
    after the candidate result. They test fragility and residual structure; none authorizes the
    estimate or changes its ecological, noncausal interpretation.
    """)
    return


@app.cell
def _(analytic, build_queen_weights, full_checksum_expected):
    geometry_frame = (
        analytic.loc[
            analytic["geography_type"].eq("chicago_community_area"),
            ["geography_id", "geometry_wkt"],
        ]
        .drop_duplicates()
        .sort_values("geography_id", kind="mergesort")
    )
    full_weights = build_queen_weights(geometry_frame)
    if full_weights.checksum != full_checksum_expected:
        raise ValueError("full 77-area spatial topology checksum changed")
    return full_weights, geometry_frame


@app.cell
def _(mo):
    mo.md("""
    ### Supplementary Statistical Analysis Module 6: spatial pattern and residual dependence

    | Review item | Prespecified rule |
    |---|---|
    | Scientific question | Are community-area CHM values or regression residuals spatially structured under a prespecified Chicago topology? |
    | Estimands | Global Moran I, local Moran I, bivariate local Moran I, Getis-Ord $G_i^*$, and the count of local classifications that survive false-discovery-rate control. |
    | Population and unit | Community areas with complete values and membership in the frozen topology. Local analysis requires all 77 areas. COPD has 76 complete areas and is not assigned local labels. |
    | Variables and denominator | Pooled CHM value, PLACES rank where applicable, model residual, and a row-standardized spatial weights matrix. The unit is a community area. |
    | Mathematical definition | Global and local statistics follow Moran, Anselin, and Getis and Ord.<sup>14-16</sup> Queen contiguity is primary. Rook and connected-distance weights are sensitivities. |
    | Estimator and uncertainty | Global Moran I uses the declared permutation test. Local statistics use 9999 seeded conditional focal-fixed permutations. Benjamini-Hochberg adjustment is applied within each condition-period-statistic family.<sup>17</sup> |
    | Assumptions and diagnostics | Polygon topology, island handling, row standardization, complete geography alignment, permutation reproducibility, and topology checksum must pass. |
    | Missingness and suppression | A missing area blocks the complete-topology local analysis. Suppressed values are not reconstructed. A spatial scan is not run without governed case counts and population at risk. |
    | Sensitivities | Rook and connected-distance weights, alternative residual models, and pre-FDR versus post-FDR counts. |
    | Interpretation and references | Spatial association describes pattern under a chosen topology. It does not identify causes, tract hotspots, treatment effects, service need, or reproducible clusters outside this dataset.<sup>14-19</sup> |
    """)
    return


@app.cell
def _(
    analytic,
    community_rank_frame,
    compute_local_spatial_diagnostics,
    evaluate_spatial_scan_feasibility,
    full_weights,
    output_dir,
    pd,
    summarize_fdr_spatial_survival,
):
    _local_rows, _availability_rows = [], []
    for _condition, _group in community_rank_frame.groupby("condition_id", sort=True):
        _aligned = _group.loc[_group["geography_id"].astype(str).isin(full_weights.geography_ids)].copy()
        if set(_aligned["geography_id"].astype(str)) == set(full_weights.geography_ids):
            _values = pd.Series(_aligned["ehr_percent"].to_numpy(), index=_aligned["geography_id"].astype(str))
            _local_rows.append(compute_local_spatial_diagnostics(
                _values, full_weights, permutations=9999, condition_id=str(_condition),
                period="2022-2024 pooled",
            ))
            _status = "run_complete_topology"
        else:
            _status = "not_run_incomplete_77_area_topology"
        _availability_rows.append(
            {"condition_id": str(_condition), "status": _status,
             "eligible_areas": int(_aligned["geography_id"].nunique()),
             "required_areas": len(full_weights.geography_ids)}
        )
    local_spatial_diagnostics = pd.concat(_local_rows, ignore_index=True) if _local_rows else pd.DataFrame()
    local_spatial_availability = pd.DataFrame(_availability_rows)
    fdr_spatial_survival = summarize_fdr_spatial_survival(local_spatial_diagnostics)
    spatial_scan_status = evaluate_spatial_scan_feasibility(analytic)
    local_spatial_diagnostics.to_csv(output_dir / "supplement_local_spatial_diagnostics.csv", index=False, float_format="%.12g")
    fdr_spatial_survival.to_csv(
        output_dir / "supplement_fdr_spatial_survival.csv", index=False, float_format="%.12g"
    )
    pd.DataFrame([spatial_scan_status]).to_csv(output_dir / "supplement_spatial_scan_status.csv", index=False)
    local_spatial_availability.to_csv(output_dir / "supplement_local_spatial_availability.csv", index=False)
    return fdr_spatial_survival, local_spatial_availability, local_spatial_diagnostics, spatial_scan_status


@app.cell
def _(mo):
    mo.md("""
    Model-specific Moran diagnostics align adjusted COPD residuals to the eligible COPD queen weights.
    The COPD residual population excludes the 1 community area with incomplete COPD exposure.
    Cardiometabolic residual diagnostics were not run because the combined diabetes analysis was
    not eligible.
    """)
    return


@app.cell
def _(
    build_queen_weights,
    c2_checksum_expected,
    geometry_frame,
    permutation_moran,
    permutations,
    primary_adjusted_residuals,
    seed,
):
    c2_residuals = primary_adjusted_residuals["C2"]
    c2_geometry = geometry_frame.loc[geometry_frame["geography_id"].isin(c2_residuals.index)]
    c2_weights = build_queen_weights(c2_geometry)
    if c2_weights.checksum != c2_checksum_expected or len(c2_residuals) != 76:
        raise ValueError("eligible C2 spatial population or checksum changed")
    c2_moran = permutation_moran(c2_residuals, c2_weights, permutations, seed)
    return c2_geometry, c2_moran, c2_residuals, c2_weights


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — spatial diagnostics:** The topology checks and permutation Moran
    results are `supportive_sensitivity_not_primary`; they document residual geography and do
    not authorize a replacement model. The JSON handoff records `model_gate_findings`,
    `complementarity_metrics`, `robustness_results`, and `per_result_import_authorization`.
    """)
    return


@app.cell
def _(
    build_rook_weights,
    build_smallest_connected_distance_weights,
    build_topology_summary,
    c2_geometry,
):
    alternative_weights = {
        "rook": build_rook_weights(c2_geometry),
        "smallest_connected_distance_band": build_smallest_connected_distance_weights(c2_geometry),
    }
    topology = build_topology_summary(alternative_weights)
    return alternative_weights, topology


@app.cell
def _(
    alternative_weights,
    asdict,
    c2_residuals,
    permutation_moran,
    permutations,
    seed,
):
    moran_records = []
    for _weights_definition, _weights in sorted(alternative_weights.items()):
        _diagnostic = permutation_moran(c2_residuals, _weights, permutations, seed)
        moran_records.append(
            {
                "weights_definition": _weights_definition,
                **asdict(_diagnostic),
                "model": "C2",
                "analysis_status": "freeze_candidate_primary_model_unsecured",
                "primary_estimand_executed": True,
                "authorization_status": "results_not_authorized",
                "results_authorized": False,
            }
        )
    return (moran_records,)


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — spatial-error sensitivity:** Alternative rook and distance-band
    weights are robustness checks. Their spatial-error rows remain supportive and are never
    promoted to manuscript results while authorization is false.
    """)
    return


@app.cell
def _(
    alternative_weights,
    build_spatial_error_sensitivity_table,
    moran_records,
    pd,
    primary_results,
):
    spatial_error_runs = []
    for _weights_definition2, _weights2 in sorted(alternative_weights.items()):
        _diagnostic2 = next(
            record
            for record in moran_records
            if record["weights_definition"] == _weights_definition2
        )
        gate = pd.DataFrame(
            [{"model_id": "C2", "escalation_required": _diagnostic2["escalation_required"]}]
        )
        spatial_error_runs.append(
            build_spatial_error_sensitivity_table(primary_results, gate, {"C2": _weights2}).assign(
                weights_definition=_weights_definition2
            )
        )
    return (spatial_error_runs,)


@app.cell
def _(moran_records, pd, spatial_error_runs, topology):
    alternative_spatial_weights = topology.merge(
        pd.DataFrame.from_records(moran_records),
        on="weights_definition",
        how="left",
        suffixes=("", "_moran"),
        validate="one_to_one",
    )
    alternative_spatial_weights["topology_analysis_status"] = alternative_spatial_weights[
        "analysis_status"
    ]
    alternative_spatial_weights["analysis_status"] = "freeze_candidate_primary_model_unsecured"
    alternative_spatial_error_sensitivity = pd.concat(spatial_error_runs, ignore_index=True)
    return alternative_spatial_error_sensitivity, alternative_spatial_weights


@app.cell
def _(alternative_spatial_error_sensitivity):
    _alternative_spatial_error_contrasts = alternative_spatial_error_sensitivity.loc[
        alternative_spatial_error_sensitivity["row_type"].isin(
            ["spatial_error_contrast", "spatial_error_not_run"]
        )
    ].copy()
    _alternative_spatial_error_contrasts["spatial_error_ci_low"] = (
        _alternative_spatial_error_contrasts["estimate"]
        - 2.241402727604947 * _alternative_spatial_error_contrasts["standard_error"]
    )
    _alternative_spatial_error_contrasts["spatial_error_ci_high"] = (
        _alternative_spatial_error_contrasts["estimate"]
        + 2.241402727604947 * _alternative_spatial_error_contrasts["standard_error"]
    )
    _alternative_spatial_error_contrasts = _alternative_spatial_error_contrasts.rename(
        columns={
            "estimate": "spatial_error_estimate",
            "standard_error": "spatial_error_standard_error",
            "weights_checksum": "spatial_error_weights_checksum",
        }
    )
    alternative_spatial_error_contrasts = _alternative_spatial_error_contrasts
    return (alternative_spatial_error_contrasts,)


@app.cell
def _(
    alternative_spatial_error_contrasts,
    alternative_spatial_weights,
    output_dir,
):
    merged_alternative_spatial_weights = alternative_spatial_weights.merge(
        alternative_spatial_error_contrasts[
            [
                "weights_definition",
                "spatial_error_status",
                "spatial_error_estimate",
                "spatial_error_standard_error",
                "spatial_error_ci_low",
                "spatial_error_ci_high",
                "lambda_hat",
                "converged",
                "spatial_error_weights_checksum",
                "model_sensitivity_status",
            ]
        ],
        on="weights_definition",
        how="left",
        validate="one_to_one",
    )
    merged_alternative_spatial_weights.to_csv(
        output_dir / "supplement_alternative_spatial_weights.csv",
        index=False,
        float_format="%.12g",
    )
    return


@app.cell
def _(asdict, c2_moran, pd):
    spatial_diagnostics = pd.DataFrame(
        [
            {"model_id": "C2", "topology_role": "eligible_c2_76", **asdict(c2_moran)},
        ]
    )
    spatial_diagnostics["analysis_role"] = spatial_diagnostics["model_id"].map(
        {"C1": "audit_only_exploratory", "C2": "adjusted_primary_residual"}
    )
    spatial_diagnostics["primary_adjusted_model_run"] = spatial_diagnostics["model_id"].eq("C2")
    spatial_diagnostics["escalation_decision"] = spatial_diagnostics["escalation_required"].map(
        {True: "mandatory_spatial_error_sensitivity", False: "no_escalation"}
    )
    primary_spatial_diagnostics = spatial_diagnostics.loc[
        spatial_diagnostics["model_id"].eq("C2")
    ].copy()
    return primary_spatial_diagnostics, spatial_diagnostics


@app.cell
def _(output_dir, primary_spatial_diagnostics):
    primary_spatial_diagnostics.to_csv(
        output_dir / "supplement_spatial_diagnostics.csv", index=False, float_format="%.12g"
    )
    return


@app.cell
def _(mo):
    mo.md("""
    The mandatory spatial-error sensitivity is executed only for models crossing the
    residual Moran gate. Rows marked `mandatory_spatial_sensitivity_run` are supportive
    diagnostics; they do not replace the prespecified OLS/HC3 alpha, beta, and gamma
    estimates.
    """)
    return


@app.cell
def _(
    build_spatial_error_sensitivity_table,
    c2_weights,
    primary_results,
    primary_spatial_diagnostics,
):
    spatial_error_sensitivity = build_spatial_error_sensitivity_table(
        primary_results,
        primary_spatial_diagnostics,
        {"C2": c2_weights},
    )
    spatial_error_sensitivity["primary_estimand_executed"] = True
    spatial_error_sensitivity["results_authorized"] = False
    return (spatial_error_sensitivity,)


@app.cell
def _(output_dir, spatial_error_sensitivity):
    spatial_error_sensitivity.to_csv(
        output_dir / "supplement_spatial_error_sensitivity.csv",
        index=False,
        float_format="%.12g",
    )
    return


@app.cell
def _(review_summary):
    c2_sensitivity_interpretation = (
        "#### How to interpret COPD sensitivity analyses\n\n"
        + review_summary["c2"]
        + " Temporal, weighting, capture, influence, and spatial-error variants test fragility;"
        " they do not repair ecological confounding or source selection."
    )
    return (c2_sensitivity_interpretation,)


@app.cell
def _(c2_sensitivity_interpretation, mo):
    mo.md(c2_sensitivity_interpretation)
    return


@app.cell
def _(c2_influence_summary, primary_spatial_diagnostics):
    influence_summary = c2_influence_summary.rename(columns={"model_id": "model_key"})
    moran_summary = primary_spatial_diagnostics.assign(
        model_key=primary_spatial_diagnostics["model_id"].str.replace(
            "_unadjusted", "", regex=False
        )
    ).rename(columns={"model_id": "moran_residual_model_id"})
    diagnostic_summary = moran_summary.merge(influence_summary, on="model_key", how="left")
    return (diagnostic_summary,)


@app.cell
def _(spatial_error_sensitivity):
    spatial_error_contrasts = spatial_error_sensitivity.loc[
        spatial_error_sensitivity["row_type"].eq("spatial_error_contrast")
        | spatial_error_sensitivity["row_type"].eq("spatial_error_not_run")
    ].copy()
    spatial_error_summary = (
        spatial_error_contrasts.groupby("model_id", sort=True, dropna=False)
        .agg(
            spatial_error_status=("spatial_error_status", "first"),
            spatial_error_lambda_hat=("lambda_hat", "first"),
            spatial_error_converged=("converged", "first"),
            spatial_error_analysis_status=("analysis_status", "first"),
            model_sensitivity_status=(
                "model_sensitivity_status",
                lambda values: (
                    "model-sensitive" if values.eq("model-sensitive").any() else values.iloc[0]
                ),
            ),
        )
        .reset_index()
        .rename(columns={"model_id": "model_key"})
    )
    return (spatial_error_summary,)


@app.cell
def _(confidence_interval_label, sensitivities):
    contrast_definitions = {
        "C1": "joint one-frozen-IQR hypertension plus diabetes contrast",
        "C1-H": "one-frozen-IQR hypertension contrast conditional on diabetes",
        "C1-D": "one-frozen-IQR diabetes contrast conditional on hypertension",
        "C2": "one-frozen-IQR COPD contrast",
    }
    scale_iqr = {
        "C1": "hypertension=13.368407|diabetes=10.977318",
        "C1-H": "hypertension=13.368407",
        "C1-D": "diabetes=10.977318",
        "C2": "copd=3.680619",
    }
    sensitivity_rows = sensitivities.assign(
        row_type="supported_sensitivity",
        model_key=sensitivities["estimand_id"].str.split("-").str[0],
        readiness_status="not_applicable_sensitivity",
        withholding_reason="",
        contrast_definition=sensitivities["estimand_id"].map(contrast_definitions),
        estimate_unit="life_expectancy_years_per_frozen_IQR_contrast",
        scale_iqr=sensitivities["estimand_id"].map(scale_iqr),
        ci_label=sensitivities["confidence_level"].map(confidence_interval_label),
        adjustment_status="unadjusted_sensitivity_not_primary",
        interpretation_label="noncausal_ecological_association",
        model_choice="unweighted_ols_hc3",
    )
    sensitivity_rows = sensitivity_rows.loc[sensitivity_rows["model_key"].eq("C2")].copy()
    return (sensitivity_rows,)


@app.cell
def _(readiness):
    readiness_contrasts = {
        "C1": "prespecified adjusted joint cardiometabolic contrast",
        "C2": "prespecified adjusted one-frozen-IQR COPD contrast",
    }
    readiness_rows = readiness.assign(
        row_type="adjusted_primary_readiness",
        estimand_id=readiness["model_id"],
        model_key=readiness["model_id"],
        readiness_status=readiness["status"],
        withholding_reason=readiness["reason"],
        contrast_definition=readiness["model_id"].map(readiness_contrasts),
        estimate=None,
        estimate_unit="life_expectancy_years_per_frozen_IQR_contrast",
        scale_iqr=None,
        ci_label=None,
        ci_low=None,
        ci_high=None,
        n=readiness["n_complete"],
        adjustment_status="adjusted_primary_candidate",
        analysis_status=readiness["status"],
        interpretation_label="noncausal_ecological_association",
        model_choice="prespecified_adjusted_unweighted_ols_hc3",
        primary_estimand_executed=readiness["status"].eq("ready_for_adjusted_primary_model"),
    )
    return (readiness_rows,)


@app.cell
def _(confidence_interval_label, pd, primary_results):
    primary_rows = pd.concat(
        [result.contrasts for result in primary_results.values()], ignore_index=True, sort=False
    )
    primary_rows = primary_rows.assign(
        row_type="adjusted_primary_contrast",
        model_key=primary_rows["model_id"],
        readiness_status="ready_for_adjusted_primary_model",
        withholding_reason="",
        contrast_definition=primary_rows["estimand_id"],
        estimate_unit="life_expectancy_years_per_frozen_IQR_contrast",
        scale_iqr="frozen_model_specific_IQR",
        ci_label=primary_rows["confidence_level"].map(confidence_interval_label),
        adjustment_status="adjusted_primary_candidate",
        interpretation_label="noncausal_ecological_association",
        model_choice="prespecified_adjusted_unweighted_ols_hc3",
        primary_estimand_executed=True,
    )
    return (primary_rows,)


@app.cell
def _():
    diagnostic_columns = [
        "model_key",
        "moran_residual_model_id",
        "analysis_role",
        "escalation_required",
        "escalation_decision",
        "weights_checksum",
        "observed_i",
        "permutation_p_value",
        "fragile",
        "flagged_areas",
        "leave_one_out_min",
        "leave_one_out_max",
    ]
    return (diagnostic_columns,)


@app.cell
def _(
    diagnostic_columns,
    diagnostic_summary,
    pd,
    primary_rows,
    readiness_rows,
    sensitivity_rows,
    spatial_error_summary,
):
    table_2_full = pd.concat(
        [primary_rows, readiness_rows, sensitivity_rows], ignore_index=True, sort=False
    )
    table_2_full = (
        table_2_full.merge(
            diagnostic_summary.loc[:, diagnostic_columns], on="model_key", how="left"
        )
        .merge(spatial_error_summary, on="model_key", how="left")
        .rename(
            columns={
                "analysis_role": "moran_analysis_role",
                "escalation_required": "moran_escalation_required",
                "escalation_decision": "moran_escalation_decision",
                "fragile": "influence_fragile",
                "flagged_areas": "influence_flagged_areas",
                "leave_one_out_min": "influence_leave_one_out_min",
                "leave_one_out_max": "influence_leave_one_out_max",
            }
        )
    )
    table_2_full["moran_gate"] = "abs(I)>=0.10_and_p<0.05"
    return (table_2_full,)


@app.cell
def _(
    aggregation_loss,
    build_compact_table_2,
    build_geographic_main_evidence,
    complementarity_summary,
    descriptive_complementarity_results,
    geographic_consequence_transitions,
):
    geographic_main_evidence = build_geographic_main_evidence(
        complementarity_summary,
        descriptive_complementarity_results,
        aggregation_loss,
        geographic_consequence_transitions,
    )
    table_2 = build_compact_table_2(geographic_main_evidence)
    return geographic_main_evidence, table_2


@app.cell
def _(geographic_main_evidence, output_dir):
    geographic_main_evidence.to_csv(
        output_dir / "supplement_geographic_main_evidence.csv",
        index=False,
        float_format="%.12g",
    )
    return


@app.cell
def _(build_great_table, output_dir, table_2):
    _table = build_great_table(
        table_2,
        title="Table 2. Geographic alignment and classification differences by condition",
        subtitle="Complete-period direct tract CHM measures and linked community-area labels",
        notes=(
            "All classification metrics use tracts with complete eligible 2022-2024 CHM records and a dominant community-area link of at least 0.99.",
            "Exact agreement and disagreement use the tract/community comparison denominator. Q4 movers use the separately reported transition-eligible denominator.",
            "The within-community variance share is the complement of the observed-scale method-of-moments VPC.",
        ),
        table_id="table_2_geographic_resolution",
        spanners={
            "Direct classification": (
                "Exact quartile agreement, No. (%)",
                "Quartile disagreement, No. (%)",
            ),
            "Cross-scale consequences": (
                "Within-community variance share",
                "Q4 movers, No. (%)",
            ),
        },
    )
    table_2_html = _table.as_raw_html()
    table_2.to_csv(output_dir / "table_2_geographic_resolution.csv", index=False, float_format="%.12g")
    return (table_2_html,)


@app.cell
def _(output_dir, table_2, table_2_html):
    table_2.to_csv(output_dir / "table_2_model_readiness_sensitivities.csv", index=False, float_format="%.12g")
    page = f"<!doctype html><html><body>{table_2_html}</body></html>"
    _ = (output_dir / "table_2_geographic_resolution.html").write_text(page, encoding="utf-8")
    _ = (output_dir / "table_2_model_readiness_sensitivities.html").write_text(page, encoding="utf-8")
    return


@app.cell
def _(build_great_table, output_dir, reader_analysis_name, table_2_full):
    _reader_table_2 = table_2_full.copy()
    _reader_names = {"C1": reader_analysis_name("C1"), "C2": reader_analysis_name("C2")}
    _reader_names.update({"C1-H": "Cardiometabolic joint analysis — hypertension component", "C1-D": "Cardiometabolic joint analysis — diabetes component", "C2_unadjusted": "COPD association analysis — unadjusted sensitivity"})
    _reader_table_2 = _reader_table_2.replace(_reader_names)
    _reader_table_2 = _reader_table_2.rename(columns={"model_id": "Analysis", "model_key": "Analysis key"})
    _reader_table_2 = _reader_table_2.replace({"audit_only_exploratory": "Diagnostic-only", "freeze_candidate_primary_model_unsecured": "Candidate adjusted estimate; not authorized", "not_run_combined_diabetes_semantics_unapproved": "Not run: combined-diabetes semantics unapproved"})
    _table = build_great_table(
        _reader_table_2,
        title="eTable 2. Full model-readiness and sensitivity audit",
        notes=(
            "This table retains readiness, diagnostic, sensitivity, topology, and authorization fields.",
            "It is not a substitute for compact manuscript-facing Table 2.",
        ),
        table_id="etable_2_model_readiness",
    )
    _ = (output_dir / "etable_2_model_readiness_sensitivities.html").write_text(
        _table.as_raw_html(make_page=True), encoding="utf-8"
    )
    table_2_full.to_csv(output_dir / "etable_2_model_readiness_sensitivities.csv", index=False, float_format="%.12g")
    return


@app.cell
def _(c2_result_narrative, mo):
    mo.vstack(
        [
            mo.md("#### Biostatistical interpretation — COPD association analysis"),
            mo.md(c2_result_narrative["biostatistician"]),
            mo.md("#### Co-author interpretation — COPD association analysis"),
            mo.md(c2_result_narrative["coauthor"]),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md("""
    #### Interpretation boundary — COPD association analysis

    The candidate adjusted association and tract comparator patterns are complementary views of
    area-level COPD measurement. Diagnostics assess model fragility and spatial structure but do
    not establish population prevalence, individual risk, causality, underdiagnosis, access
    failure, or service need. Manuscript import remains closed.
    """)
    return


@app.cell
def _(aggregation_loss, mo):
    _suppressed_duplicate_resolution_text = aggregation_loss, mo
    return


@app.cell
def _(mo):
    _suppressed_duplicate_table_note = mo
    return


@app.cell
def _(mo, table_2_html):
    _suppressed_duplicate_table = mo, table_2_html
    return


@app.cell
def _(
    MAIN_DISPLAY_IDS,
    aggregation_loss,
    build_claim_evidence_audit,
    build_master_claim_records,
    output_dir,
    primary_rows,
    readiness,
):
    claim_records = build_master_claim_records(readiness, primary_rows, aggregation_loss)
    claim_evidence_audit = build_claim_evidence_audit(
        claim_records,
        {"C1": MAIN_DISPLAY_IDS[2], "C2": MAIN_DISPLAY_IDS[3], "GR": "eTable_8"},
    )
    claim_evidence_audit.to_csv(output_dir / "supplement_claim_evidence_audit.csv", index=False)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Supplementary outcome-model interpretation

    The combined cardiometabolic model was not run because diabetes-component semantics remain
    unapproved. The COPD
    adjusted association remains a candidate secondary estimate with a governed 97.5% HC3
    interval. Neither outcome-model analysis changes the primary geographic interpretation or
    the closed authorization state.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Plain-language coauthor interpretation.** The model appendix documents what was attempted
    and why one analysis was withheld. It should not replace the main geographic finding or be
    used to claim that recorded disease caused differences in life expectancy.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Model-specific limitations

    Unapproved combined-diabetes semantics prevent the cardiometabolic joint model from being run. The COPD
    analysis remains vulnerable to ecological confounding, selection into observed EHR data,
    temporal source mismatch, influence, and residual spatial dependence.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Model-specific boundary

    These models are supplementary audit evidence. Human review and the authorization gate remain
    required before any model result can enter a manuscript.
    """)
    return


@app.cell
def _(json, output_dir, results_authorized):
    manuscript_result_narratives = {
        "results_authorized": bool(results_authorized),
        "manuscript_import_allowed": False,
        "C1": {
            "status": "withheld_vif_above_5",
            "manuscript_import_allowed": False,
            "narrative": "No numeric C1 result is available for manuscript import.",
        },
        "C2": {
            "status": "freeze_candidate_primary_model_unsecured",
            "manuscript_import_allowed": False,
            "narrative": "The C2 estimate remains restricted to the statistician-review package.",
        },
    }
    _ = (output_dir / "manuscript_result_narratives.json").write_text(
        json.dumps(manuscript_result_narratives, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return


@app.cell
def _(json, output_dir, results_authorized):
    coauthor_interpretation_guide = {
        "results_authorized": bool(results_authorized),
        "resource": "Numeric resource results remain restricted to the statistician-review package.",
        "cardiometabolic": "The C1 analysis was not run because combined diabetes semantics remain unapproved.",
        "tract_complementarity": "Numeric geographic results remain restricted to the statistician-review package.",
        "copd": "The C2 estimate is not authorized for coauthor or manuscript import.",
        "copd_sensitivity": "Numeric sensitivity results remain restricted to the statistician-review package.",
        "inference_boundary": (
            "Interpret as ecological complementarity; do not infer prevalence, causality, "
            "validation, underdiagnosis, access failure, service need, or individual risk."
        ),
    }
    _ = (output_dir / "coauthor_interpretation_guide.json").write_text(
        json.dumps(coauthor_interpretation_guide, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return


@app.cell
def _(
    build_main_display_reader_cards,
    geographic_consequence_display,
    geographic_main_evidence,
    results_authorized,
    table_1,
):
    reader_cards = build_main_display_reader_cards(
        table_1, geographic_main_evidence, geographic_consequence_display, bool(results_authorized)
    )
    return (reader_cards,)


@app.cell
def _(
    build_main_display_reader_guide,
    c1_result_narrative,
    c2_result_narrative,
    json,
    output_dir,
    reader_cards,
    results_authorized,
):
    guide = build_main_display_reader_guide(reader_cards, model_guidance=[
        {"analysis_name": "Cardiometabolic joint analysis", "status": "not run; combined diabetes semantics unapproved", "authorization": bool(results_authorized), "narrative": c1_result_narrative.get("coauthor", "")},
        {"analysis_name": "COPD association analysis", "status": "candidate estimate; not authorized for manuscript import", "authorization": bool(results_authorized), "narrative": c2_result_narrative.get("coauthor", "")},
    ])
    _ = (output_dir / "main_display_reader_guide.json").write_text(json.dumps(guide["main_displays"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _ = (output_dir / "model_interpretation_guide.json").write_text(json.dumps(guide["model_guidance"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return


@app.cell
def _():
    etable_specs = (
        ("eTable 1", "Full CHM resource-quality and tract accounting", "etable_1_resource_quality.html", "supplement"),
        ("eTable 2", "Full model-readiness and sensitivity audit", "etable_2_model_readiness_sensitivities.html", "qc_only"),
        ("eTable 3", "Full alpha, beta, and gamma coefficients", "supplement_full_coefficient_table.html", "qc_only"),
        ("eTable 4", "Robustness and alternative spatial weights", "etable_4_robustness_summary.html", "supplement"),
        ("eTable 5", "Tract concordance and heterogeneity", "etable_5_tract_complementarity.html", "supplement"),
        ("eTable 6", "Geographic-resolution sensitivity", "etable_6_geographic_resolution.html", "manuscript_candidate"),
        ("eTable 7", "Descriptive complementarity methods", "etable_7_descriptive_complementarity_methods.html", "qc_only"),
        ("eTable 8", "Highest-quartile direct cross-frame classification differences", "etable_8_geographic_consequences.html", "supplement"),
        ("eTable 9", "Uncertainty-aware agreement feasibility", "etable_9_uncertainty_feasibility.html", "supplement"),
    )
    return (etable_specs,)


@app.cell
def _():
    efigure_specs = (
        ("eFigure 1", "Source assembly and analytic-frame flow", "supplement_source_assembly_flow.pdf", "supplement"),
        ("eFigure 2", "Annual CHM coverage and data quality", "supplement_annual_data_quality.pdf", "supplement"),
        ("eFigure 3", "Cardiometabolic geographic-resolution sensitivity", "supplement_cardiometabolic_resolution.pdf", "manuscript_candidate"),
        ("eFigure 4", "Cardiometabolic CHM–PLACES agreement", "supplement_cardiometabolic_agreement.pdf", "manuscript_candidate"),
        ("eFigure 5", "Cardiometabolic spatial diagnostics", "supplement_cardiometabolic_spatial.pdf", "supplement"),
        ("eFigure 6", "Cardiometabolic collinearity diagnostics", "supplement_cardiometabolic_collinearity.pdf", "qc_only"),
        ("eFigure 7", "COPD coefficient forest", "supplement_coefficient_forest.pdf", "manuscript_candidate"),
        ("eFigure 8", "COPD model diagnostics", "supplement_model_diagnostics.pdf", "qc_only"),
        ("eFigure 9", "COPD robustness analyses", "supplement_model_robustness.pdf", "supplement"),
        ("eFigure 10", "COPD spatial sensitivity", "supplement_spatial_sensitivity.pdf", "supplement"),
        ("eFigure 11", "Geographic consequence and ZCTA sensitivity", "supplement_geographic_consequences.pdf", "manuscript_candidate"),
        ("eFigure 12", "FDR-controlled spatial survival", "supplement_fdr_spatial_survival.pdf", "supplement"),
    )
    return (efigure_specs,)


@app.cell
def _(efigure_specs, etable_specs):
    _specs = (*etable_specs, *efigure_specs)
    numbered_displays = {
        item_id: {"title": title, "artifact": artifact, "display_role": role}
        for item_id, title, artifact, role in _specs
    }
    reproducibility_files = (
        "supplement_data_quality_audit.csv",
        "supplement_tract_cohort_flow.csv",
        "supplement_claim_evidence_audit.csv",
        "supplement_geographic_resolution_matrix.csv", "supplement_geographic_main_evidence.csv",
        "supplement_aggregation_loss.csv",
        "supplement_robustness_summary.csv",
        "supplement_adjusted_diagnostic_data.csv",
        "supplement_alternative_spatial_weights.csv",
        "supplement_local_spatial_diagnostics.csv",
        "supplement_local_spatial_availability.csv",
        "supplement_fdr_spatial_survival.csv",
        "supplement_spatial_scan_status.csv",
        "supplement_geographic_consequence_transitions.csv",
        "supplement_geographic_consequence_stability.csv",
        "supplement_zcta_linkage.csv",
        "supplement_descriptive_complementarity_methods.csv",
        "supplement_descriptive_claim_evidence_audit.csv",
        "coauthor_interpretation_guide.json",
        "main_display_reader_guide.json",
        "model_interpretation_guide.json",
        "editorial_display_manifest.json",
        "editorial_curation_manifest.json",
    )
    return numbered_displays, reproducibility_files


@app.cell
def _(
    build_editorial_display_manifest,
    build_supplement_registry,
    json,
    numbered_displays,
    output_dir,
    reproducibility_files,
    results_authorized,
):
    supplement_registry = build_supplement_registry(numbered_displays, reproducibility_files)
    editorial_display_manifest = build_editorial_display_manifest(numbered_displays, results_authorized=bool(results_authorized))
    main_ids = tuple(f"{kind}_{index}" for kind, index in (("table", 1), ("figure", 1), ("figure", 2), ("figure", 3), ("table", 2)))
    main_entries = [{"id": display_id, "editorial_placement": "submitted", "citable_status": "not_citable_pending_authorization", "authorization_requirement": "results_authorized=true", "first_mention_order": index, "duplicate_main_evidence": False} for index, display_id in enumerate(main_ids, start=1)]
    editorial_payload = {"main_manuscript": main_entries, "supplementary": editorial_display_manifest}
    _editorial_json = json.dumps(editorial_payload, indent=2, sort_keys=True) + "\n"
    _ = (output_dir / "editorial_display_manifest.json").write_text(_editorial_json, encoding="utf-8")
    _ = (output_dir / "editorial_curation_manifest.json").write_text(_editorial_json, encoding="utf-8")
    supplement_entries = supplement_registry["numbered_manuscript_displays"]
    return (supplement_entries,)


@app.cell
def _(json, output_dir, reproducibility_files, supplement_entries):
    supplement_table_of_contents = {
        "title": "Chicago Health Map Supplement: Table of Contents",
        "numbered_manuscript_displays": supplement_entries,
        "machine_readable_reproducibility_files": list(reproducibility_files),
        "citation_rule": "Cite each eTable in the main manuscript in order of first mention.",
    }
    _ = (output_dir / "supplement_table_of_contents.json").write_text(
        json.dumps(supplement_table_of_contents, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ### Word-paste manuscript handoff

    The controlled handoff is Markdown plus HTML, not a DOCX conversion. While S7 is closed it
    contains complete methods, display insertion markers, verified source-ledger keys, and
    nonnumeric Results and Discussion shells. Numerical tables, figures, model estimates, and
    sensitivity prose are intentionally excluded until the independent authorization review.
    """)
    return


@app.cell
def _(build_blocked_word_handoff, json, output_dir):
    _methods = (
        "We analyzed direct CHM geographic-condition-year records from 2019 through 2024. "
        "For the 2022-2024 geographic comparison, eligible direct tract measures were pooled "
        "as summed numerators divided by summed denominators before ranking. Missing and "
        "suppressed values were not imputed; direct tract disease values were never interpolated "
        "or aggregated. CHM-PLACES comparisons were descriptive and used condition-specific "
        "eligible tract frames."
    )
    word_handoff = build_blocked_word_handoff(
        title="Added Geographic Information From Tract-Level Health System Data in Chicago",
        methods=_methods,
        provenance_keys=("chm_data_glossary", "places_metadata", "tract_community_overlay"),
    )
    _ = (output_dir / "word_handoff_blocked.md").write_text(word_handoff["markdown"], encoding="utf-8")
    _ = (output_dir / "word_handoff_blocked.html").write_text(word_handoff["html"], encoding="utf-8")
    _ = (output_dir / "word_handoff_manifest.json").write_text(
        json.dumps({k: v for k, v in word_handoff.items() if k not in {"markdown", "html"}}, indent=2)
        + "\n", encoding="utf-8"
    )
    return


@app.cell
def _(mo):
    mo.md("""
    **Supplementary model artifact.** The candidate COPD adjusted estimate and spatial diagnostic
    are retained only as nonimportable supplementary analysis artifacts. The cardiometabolic joint
    analysis was not run because mutual exclusivity and denominator equivalence for the combined
    diabetes exposure remain unapproved. No C1 coefficient, confidence interval, influence result,
    or residual diagnostic exists. Neither model artifact is a main geographic display or an
    authorized manuscript handoff.

    The official JAMA Health Forum Instructions for Authors were accessed directly on August 26,
    2026. [AUTHOR: recheck journal instructions immediately before submission and complete the
    required abstract, Key Points, data-sharing, disclosure, and reporting-checklist materials.]
    """)
    return


@app.cell
def _(
    build_manuscript_results_handoff,
    json,
    output_dir,
    primary_rows,
    primary_spatial_diagnostics,
    results_authorized,
):
    manuscript_results = build_manuscript_results_handoff(
        primary_rows,
        primary_spatial_diagnostics,
        results_authorized=results_authorized,
        live_journal_verification=(
            "official_jama_health_forum_instructions_directly_verified_2026-08-26"
        ),
    )
    _ = (output_dir / "manuscript_results_handoff.json").write_text(
        json.dumps(manuscript_results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    figure_legends = manuscript_results["figure_legends"]
    _ = (output_dir / "figure_legends.json").write_text(
        json.dumps(figure_legends, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return


@app.cell
def _(coefficient_table, output_dir, reader_analysis_name, render_styled_html):
    _reader_coefficients = coefficient_table.copy()
    if "model_id" in _reader_coefficients:
        _reader_coefficients["model_id"] = _reader_coefficients["model_id"].map(
            lambda value: reader_analysis_name(str(value)) if str(value) in {"C1", "C2"} else value
        )
        _reader_coefficients = _reader_coefficients.rename(columns={"model_id": "Analysis"})
    for _column in _reader_coefficients.columns:
        if _reader_coefficients[_column].dtype == object:
            _reader_coefficients[_column] = _reader_coefficients[_column].replace(
            {
                "freeze_candidate_primary_model_unsecured": "Candidate adjusted estimate; not authorized",
                "not_run_combined_diabetes_semantics_unapproved": "Not run: combined-diabetes semantics unapproved",
            }
        )
    coefficient_html = render_styled_html(
        _reader_coefficients,
        "Supplement eTable. Full alpha, beta, and gamma coefficients",
        "The COPD association analysis exposure contrast uses frozen IQR scaling; its adjustment coefficients use 1-SD scaling. The cardiometabolic joint analysis was not run because combined-diabetes semantics remain unapproved.",
    )
    coefficient_table.to_csv(
        output_dir / "supplement_full_coefficient_table.csv", index=False, float_format="%.12g"
    )
    _ = (output_dir / "supplement_full_coefficient_table.html").write_text(
        coefficient_html, encoding="utf-8"
    )
    return (coefficient_html,)


@app.cell
def _(model_gate_diagnostics, output_dir):
    model_gate_diagnostics.to_csv(
        output_dir / "supplement_model_gate_diagnostics.csv", index=False, float_format="%.12g"
    )
    return


@app.cell
def _(mo):
    mo.md("""
    The coefficient supplement reports alpha, beta, and gamma terms from the governed
    result bundle. The estimand scale and adjustment set are shown before any coefficient
    sign is interpreted. Language remains noncausal, and manuscript authorization remains
    false.

    **Co-author interpretation:** alpha is the expected life expectancy at mean centered exposures
    and covariates. Beta terms are adjusted life-expectancy differences per frozen-IQR higher
    CHM diagnosed proportion. Gamma terms are nuisance adjustment slopes per 1-SD difference.

    **Co-author interpretation:** the beta rows answer the case-study question; the gamma
    rows document what the model adjusted for. A negative beta means lower life expectancy was
    associated with a higher CHM EHR-diagnosed proportion at the community-area level, not that
    disease produced lower life expectancy for an individual person.
    """)
    return


@app.cell
def _(coefficient_html, mo):
    mo.download(
        coefficient_html.encode("utf-8"),
        filename="supplement_full_coefficient_table.html",
        mimetype="text/html",
        label="Download eTable 3: full alpha, beta, and gamma coefficients",
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ### Additional geographic and reproducibility displays

    ### Tract concordance, discordance, and multiplicity

    Tract-level analyses compare EHR patterns with a secondary public comparator using
    common-set quartile and tertile classifications and BH-aware summaries. Rank agreement,
    absolute differences, kappa, and fixed categories answer distinct measurement questions.
    Comparator roles remain asymmetric, and neither source is treated as a truth standard.

    **Co-author interpretation:** raw P values describe one comparator check; BH-adjusted P values
    control the false-discovery rate within the prespecified comparator family. The notebook
    keeps both so reviewers can see the statistical trail, but interpretation should lead
    with estimates, uncertainty, and source-role boundaries rather than P values alone.
    """)
    return


@app.cell
def _(
    analytic,
    build_tract_concordance_frame,
    classify_discordance,
    summarize_concordance,
):
    tract_concordance = build_tract_concordance_frame(analytic)
    concordance_summary = summarize_concordance(tract_concordance)
    discordance_quartile = classify_discordance(tract_concordance, bins="quartile")
    discordance_tertile = classify_discordance(tract_concordance, bins="tertile")
    return (
        concordance_summary,
        discordance_quartile,
        discordance_tertile,
        tract_concordance,
    )


@app.cell
def _(concordance_summary, pd):
    multiplicity_inventory = pd.concat(
        [
            concordance_summary.assign(
                metric="spearman",
                raw_p=concordance_summary["spearman_p"],
                bh_p=concordance_summary["spearman_p_bh"],
            ),
            concordance_summary.assign(
                metric="pearson",
                raw_p=concordance_summary["pearson_p"],
                bh_p=concordance_summary["pearson_p_bh"],
            ),
        ],
        ignore_index=True,
    )[
        [
            "condition_id",
            "condition_priority",
            "metric",
            "raw_p",
            "bh_p",
            "comparator_family_id",
            "multiplicity_denominator",
        ]
    ]
    return (multiplicity_inventory,)


@app.cell
def _(
    concordance_summary,
    discordance_quartile,
    discordance_tertile,
    multiplicity_inventory,
    output_dir,
):
    concordance_summary.to_csv(
        output_dir / "supplement_concordance_summary.csv", index=False, float_format="%.12g"
    )
    discordance_quartile.to_csv(
        output_dir / "supplement_discordance_quartile.csv", index=False, float_format="%.12g"
    )
    discordance_tertile.to_csv(
        output_dir / "supplement_discordance_tertile.csv", index=False, float_format="%.12g"
    )
    multiplicity_inventory.to_csv(
        output_dir / "supplement_multiplicity_inventory.csv", index=False, float_format="%.12g"
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ### Artifact generation and deterministic display export

    Technical specification: The purpose is to display source-to-analysis flow, compact model
    status, and complementary spatial summaries without duplicating regression estimates. The
    observational units are source rows, community areas, and tracts; descriptive estimands are
    counts, percentages, ranks, and rank gaps. Alpha, beta, and gamma remain in the coefficient
    supplement, not in figures. Color scales use exact units and visible labels; missing,
    suppression, and qualification withholding are separate encodings. Table 2 reports the COPD
    97.5% HC3 interval and the combined-diabetes not-run status. Figures show no
    cardiometabolic estimate. Legends state source
    roles, geography, period, n, and CI meaning. All displays are descriptive, noncausal, and
    subject to the closed authorization gate.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — Tables and figures:** The displays are a map for the reader, not a
    second results section. Table 1 says what was available, Table 2 says what model gate was
    reached, and Figures 1-3 show how the two source lenses line up or disagree. The
    cardiometabolic joint analysis remains visibly not run, and
    `results_authorized=false` remains on every manuscript handoff.
    """)
    return


@app.cell
def _(plt):
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 150,
            "font.size": 8,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.linewidth": 0.6,
            "lines.linewidth": 1.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    png_metadata = {"Software": "ChicagoHealthMap deterministic marimo pipeline"}
    return (png_metadata,)


@app.cell
def _():
    MAIN_DISPLAY_IDS = (
        "table_1",
        "figure_1",
        "figure_2",
        "figure_3",
        "table_2",
    )
    return (MAIN_DISPLAY_IDS,)


@app.cell
def _(resource_quality):
    flow_coverage = resource_quality.loc[
        resource_quality["geography_type"].eq("chicago_community_area")
    ].copy()
    flow_coverage["unavailable_or_missing"] = (
        flow_coverage["rows"]
        - flow_coverage["disease_measure_eligible_rows"]
        - flow_coverage["suppressed_rows"]
    )
    flow_coverage["coverage_label"] = flow_coverage.apply(
        lambda row: f"{row['disease_measure_eligible_rows']}/{row['rows']}", axis=1
    )
    return (flow_coverage,)


@app.cell
def _(geometry_frame, primary_frame):
    map_source = geometry_frame.merge(
        primary_frame[
            [
                "geography_id",
                "life_expectancy_mean_2022_2024",
                "hypertension_ehr_percent_2022_2024",
                "diabetes_ehr_percent_2022_2024",
                "copd_ehr_percent_2022_2024",
                "hypertension_exposure_complete",
                "diabetes_exposure_complete",
                "copd_exposure_complete",
            ]
        ],
        on="geography_id",
        how="left",
    )
    return (map_source,)


@app.cell
def _(gpd, map_source):
    _capture_columns = [
        "hypertension_ehr_percent_2022_2024",
        "diabetes_ehr_percent_2022_2024",
        "copd_ehr_percent_2022_2024",
    ]
    map_source["capture_completeness_percent"] = map_source[_capture_columns].notna().mean(axis=1) * 100
    map_source["capture_status"] = (
        map_source["capture_completeness_percent"]
        .eq(100)
        .map({True: "all_three", False: "incomplete"})
    )
    _c1_complete = map_source[["hypertension_exposure_complete", "diabetes_exposure_complete"]].all(axis=1)
    map_source["analytic_inclusion"] = _c1_complete.astype(int) + map_source[
        "copd_exposure_complete"
    ].astype(int)
    map_source["qualification_status"] = map_source["copd_exposure_complete"].map(
        {True: "COPD association analysis: candidate adjusted estimate; not authorized for manuscript import", False: "COPD association analysis: incomplete"}
    )
    map_source["c2_coverage_status"] = map_source["copd_exposure_complete"].map(
        {True: "complete_c2", False: "suppressed_or_incomplete_c2"}
    )
    map_source["availability_status"] = "available"
    coverage_map = gpd.GeoDataFrame(
        map_source, geometry=gpd.GeoSeries.from_wkt(map_source["geometry_wkt"]), crs="EPSG:4326"
    )
    return (coverage_map,)


@app.cell
def _(analytic, gpd):
    _tracts = (
        analytic.loc[
            analytic["geography_type"].eq("census_tract"),
            ["geography_id", "geometry_wkt"],
        ]
        .dropna()
        .drop_duplicates("geography_id")
        .sort_values("geography_id", kind="mergesort")
    )
    tract_footprint = gpd.GeoDataFrame(
        _tracts,
        geometry=gpd.GeoSeries.from_wkt(_tracts["geometry_wkt"]),
        crs="EPSG:4326",
    )
    return (tract_footprint,)


@app.cell
def _(analytic):
    _frame = analytic.assign(
        eligible=analytic["published_measure_value"].notna() & ~analytic["suppression_flag"]
    )
    _group = ["geography_type", "condition_id", "time_period"]
    figure_1_availability = (
        _frame.groupby(_group, observed=True)["eligible"].mean().mul(100).reset_index()
    )
    figure_1_capture = _frame.loc[
        _frame["capture_rate"].notna(),
        ["geography_type", "condition_id", "capture_rate"],
    ].copy()
    figure_1_capture["capture_percent"] = 100 * figure_1_capture["capture_rate"]
    return figure_1_availability, figure_1_capture


@app.cell
def _(build_flow_summary, flow_coverage, readiness):
    # Contract examples remain internal model IDs; labels are reader-facing in the rendered flow.
    flow_summary = build_flow_summary(
        flow_coverage,
        case_denominators={
            "C1": int(readiness.loc[readiness["model_id"].eq("C1"), "n_complete"].iloc[0]),
            "C2": int(readiness.loc[readiness["model_id"].eq("C2"), "n_complete"].iloc[0]),
        },
    )
    return (flow_summary,)


@app.cell
def _():
    DISPLAY_ENCODING_CONTRACT = {
        "capture": [
            ("all_three", "All 3 CHM measures observed", "#0072B2", ""),
            ("incomplete", "At least 1 measure unavailable", "#F0E442", "//"),
        ],
        "inclusion": [
            (2, "Eligible rows for both analyses", "#009E73", ""),
            (1, "Cardiometabolic row only; COPD incomplete", "#D55E00", "xx"),
        ],
        "qualification": [
            (
                "COPD association analysis: candidate adjusted estimate; not authorized for manuscript import",
                "COPD association analysis: candidate adjusted estimate; not authorized for manuscript import",
                "#E69F00",
                "//",
            ),
            ("COPD association analysis: incomplete; unauthorized", "COPD association analysis: incomplete; unauthorized", "#CC79A7", "xx"),
        ],
        "rank_gap_markers": [(False, "o", "CHM lower rank"), (True, "^", "CHM higher/equal rank")],
        "rank_gap_hatches": {"nonnegative": "//", "negative": ".."},
        "sequential_cmap": "cividis",
        "diverging_cmap": "RdBu_r",
    }
    return (DISPLAY_ENCODING_CONTRACT,)


@app.function
def draw_status_map(axis, coverage, column, title, categories):
    from matplotlib.patches import Patch

    coverage.plot(ax=axis, color="#f2f2f2", edgecolor="white", linewidth=0.45)
    handles = []
    for value, label, color, hatch in categories:
        rows = coverage.loc[coverage[column].eq(value)]
        if not rows.empty:
            rows.plot(ax=axis, color=color, edgecolor="white", linewidth=0.45, hatch=hatch)
        handles.append(Patch(facecolor=color, edgecolor="#444444", hatch=hatch, label=label))
    axis.set_title(title, loc="left", fontweight="bold")
    axis.set_axis_off()
    axis.legend(handles=handles, frameon=False, loc="lower left", fontsize=6.5)


@app.function
def draw_resource_footprint(axis, tracts, communities):
    tracts.plot(ax=axis, color="#DCEAF4", edgecolor="#7A8A99", linewidth=0.18)
    communities.boundary.plot(ax=axis, color="#111111", linewidth=0.65)
    axis.set_title("A. Chicago tract and community-area footprint", loc="left")
    axis.text(
        0.02,
        0.02,
        f"{tracts['geography_id'].nunique():,} tracts; {communities['geography_id'].nunique()} community areas\n"
        "Community-area boundaries; census-tract fill",
        transform=axis.transAxes,
        fontsize=7,
    )
    axis.set_axis_off()


@app.function
def draw_availability_panel(axis, rows):
    labels = {"census_tract": "Tract", "chicago_community_area": "Community area"}
    conditions = {
        "copd": "COPD",
        "diabetes_with_complication": "Diabetes with complication",
        "diabetes_without_complication": "Diabetes without complication",
        "hypertension": "Hypertension",
    }
    frame = rows.assign(
        row=rows["geography_type"].map(labels) + " — " + rows["condition_id"].map(conditions)
    )
    matrix = frame.pivot(index="row", columns="time_period", values="eligible")
    values = matrix.to_numpy(dtype=float)
    is_constant = bool(values.size and values.min() == values.max())
    image = axis.imshow(values, cmap="Greys_r", vmin=0, vmax=100, aspect="auto")
    for row_index in range(len(matrix)):
        for column_index in range(len(matrix.columns)):
            value = float(values[row_index, column_index])
            text_color = "#111111" if value >= 75 else "white"
            axis.text(column_index, row_index, f"{value:.0f}", ha="center", va="center", color=text_color, fontsize=6.5, fontweight="bold")
    axis.set(yticks=range(len(matrix)), yticklabels=matrix.index)
    axis.set(xticks=range(len(matrix.columns)), xticklabels=matrix.columns)
    title = "B. Condition-year availability: analytic eligibility (%)"
    if is_constant:
        title += " — all cells complete"
    axis.set_title(title, loc="left")
    axis.figure.colorbar(image, ax=axis, fraction=0.035, pad=0.02, label="Eligible records (%)")


@app.function
def draw_suppression_panel(axis, quality):
    labels = {"census_tract": "Tract", "chicago_community_area": "Community area"}
    condition_labels = {
        "copd": "COPD", "diabetes_with_complication": "Diabetes,\ncomplication",
        "diabetes_without_complication": "Diabetes,\nno complication",
        "hypertension": "Hypertension",
    }
    colors = {"census_tract": "#0072B2", "chicago_community_area": "#D55E00"}
    conditions = sorted(quality["condition_id"].unique())
    for geography, rows in quality.groupby("geography_type", sort=True):
        values = rows.set_index("condition_id").reindex(conditions)
        percent = 100 * values["suppressed_rows"] / values["rows"]
        axis.plot(conditions, percent, marker="o", label=labels[geography], color=colors[geography])
    axis.set(ylabel="Suppressed records (%)", xlabel="Condition")
    axis.set_xticks(range(len(conditions)), [condition_labels[item] for item in conditions])
    axis.set_title("C. Suppression by condition and geography", loc="left")
    axis.tick_params(axis="x", labelrotation=0, labelsize=7)
    axis.legend(frameon=False)


@app.function
def draw_capture_panel(axis, capture):
    labels = {"census_tract": "Tract", "chicago_community_area": "Community area"}
    condition_labels = {
        "copd": "COPD", "diabetes_with_complication": "Diabetes,\ncomplication",
        "diabetes_without_complication": "Diabetes,\nno complication",
        "hypertension": "Hypertension",
    }
    colors = {"census_tract": "#0072B2", "chicago_community_area": "#D55E00"}
    order = sorted(capture["condition_id"].unique())
    for offset, geography in ((-0.16, "census_tract"), (0.16, "chicago_community_area")):
        rows = capture.loc[capture["geography_type"].eq(geography)]
        data = [rows.loc[rows["condition_id"].eq(item), "capture_percent"] for item in order]
        box = axis.boxplot(data, positions=[i + offset for i in range(len(order))], widths=0.25,
                           patch_artist=True, showfliers=False)
        for patch in box["boxes"]:
            patch.set(facecolor=colors[geography], alpha=0.55)
        axis.plot([], [], color=colors[geography], linewidth=6, label=labels[geography])
    axis.set(xticks=range(len(order)), xticklabels=[condition_labels[item] for item in order],
             ylabel="Source-published capture (%)")
    axis.set_title("D. Source-published capture distributions\nReliability qualification withheld", loc="left")
    axis.tick_params(axis="x", labelrotation=20, labelsize=6.5)
    for label in axis.get_xticklabels():
        label.set_horizontalalignment("right")
    axis.legend(frameon=False, title="Geography", loc="upper left", bbox_to_anchor=(1.01, 1))


@app.cell
def _(
    coverage_map,
    figure_1_availability,
    figure_1_capture,
    plt,
    resource_quality,
    tract_footprint,
):
    figure_1, axes = plt.subplots(2, 2, figsize=(10.5, 7.2), constrained_layout=True)
    draw_resource_footprint(axes[0, 0], tract_footprint, coverage_map)
    draw_availability_panel(axes[0, 1], figure_1_availability)
    draw_suppression_panel(axes[1, 0], resource_quality)
    draw_capture_panel(axes[1, 1], figure_1_capture)
    figure_1.suptitle("Figure 1. Chicago Health Map geographic coverage and data quality")
    return (figure_1,)


@app.cell
def _(mo):
    mo.md("""
    Figure 1 describes the full CHM resource before either analysis. Panel A locates the tract
    and community-area units; panel B shows condition-year availability after excluding
    suppressed records; panel C reports source suppression; and panel D shows capture
    distributions while retaining the withheld
    reliability-qualification status. Counts are not unique patients.
    """)
    return


@app.cell
def _(figure_1):
    _ = figure_1
    return


@app.function
def draw_community_association(axis, frame, condition, title):
    exposure = f"{condition}_ehr_percent_2022_2024"
    axis.scatter(
        frame[exposure],
        frame["life_expectancy_mean_2022_2024"],
        s=16,
        color="#0072B2",
        edgecolor="white",
        linewidth=0.25,
    )
    axis.set(xlabel=f"EHR {condition} (%)", ylabel="Atlas life expectancy (years)")
    axis.set_title(title, loc="left", fontweight="bold")


@app.function
def draw_tract_alignment(axis, rows, condition, title, encoding_contract):
    for higher, marker, label in encoding_contract["rank_gap_markers"]:
        points = rows.loc[rows["paired_percentile_rank_gap"].ge(0).eq(higher)]
        axis.scatter(
            points["public_comparator_estimate"],
            points["ehr_percent"],
            s=8,
            c=points["paired_percentile_rank_gap"],
            cmap="RdBu_r",
            vmin=-1,
            vmax=1,
            marker=marker,
            label=label,
        )
    axis.set(xlabel="Public comparator (%)", ylabel=f"EHR {condition} (%)")
    axis.set_title(title, loc="left", fontweight="bold")
    axis.legend(frameon=False, fontsize=5.5, loc="upper left")


@app.function
def draw_rank_concordance(axis, rows):
    axis.scatter(
        rows["ehr_rank"],
        rows["public_rank"],
        s=7,
        color="#4D4D4D",
        alpha=0.55,
        linewidths=0,
    )
    axis.plot([0, 1], [0, 1], color="#333333", linewidth=0.8, linestyle="--")
    axis.set(xlabel="CHM percentile rank", ylabel="Public percentile rank")


@app.cell
def _(build_resolution_heatmap_data):
    def draw_resolution_heatmap(axis, matrix, condition, title):
        values = build_resolution_heatmap_data(matrix, condition, noncrossing_only=False)
        axis.imshow(values, cmap="Greys", vmin=0, vmax=max(1, values.to_numpy().max()))
        for y in range(4):
            for x in range(4):
                color = "white" if values.iloc[y, x] > values.to_numpy().max() / 2 else "black"
                axis.text(x, y, f"{values.iloc[y, x]:.0f}%", ha="center", va="center", color=color)
        axis.set(xticks=range(4), xticklabels=range(1, 5), yticks=range(4), yticklabels=range(1, 5))
        axis.set(xlabel="Direct tract quartile", ylabel="Direct community-area quartile")
        axis.set_title(title, loc="left", fontweight="bold")

    return (draw_resolution_heatmap,)


@app.function
def add_case_colorbars(figure, axes, plt):
    signed = plt.cm.ScalarMappable(norm=plt.Normalize(-1, 1), cmap="RdBu_r")
    figure.colorbar(
        signed,
        ax=axes[:, 2],
        orientation="horizontal",
        fraction=0.06,
        pad=0.14,
        label="Signed percentile-rank gap (CHM − public)",
    )


@app.cell
def _():
    conditions = ["hypertension", "diabetes", "copd"]
    return (conditions,)


@app.cell
def _(draw_resolution_heatmap, geographic_resolution_matrix):
    def draw_figure_2_column(axis_top, axis_bottom, condition, column, tract_percentile):
        label = "COPD" if condition == "copd" else condition.title()
        rows = tract_percentile.loc[tract_percentile["condition_id"].eq(condition)]
        matrix = geographic_resolution_matrix.loc[geographic_resolution_matrix["condition_id"].eq(condition) & geographic_resolution_matrix["noncrossing_only"].eq(False)]
        if matrix.empty:
            axis_top.axis("off")
            axis_top.text(0.5, 0.5, f"{chr(65 + column)}. {label} quartiles\n\nNot run: combined-component\nsemantics not approved.", ha="center", va="center", fontsize=8)
        else:
            draw_resolution_heatmap(axis_top, geographic_resolution_matrix, condition, f"{chr(65 + column)}. {label}: tract vs community quartiles")
        if condition == "diabetes":
            axis_bottom.axis("off")
            axis_bottom.text(0.5, 0.5, "E. Combined diabetes components vs PLACES\n\nNot run: total-diabetes phenotype and\nperiod mapping not yet approved.", ha="center", va="center", fontsize=8)
        else:
            draw_rank_concordance(axis_bottom, rows)
            axis_bottom.set_title(f"{chr(68 + column)}. {label}: CHM vs PLACES ranks", loc="left")

    return (draw_figure_2_column,)


@app.cell
def _(conditions, draw_figure_2_column, plt, tract_percentile):
    figure_2, axes_2 = plt.subplots(2, 3, figsize=(10.5, 6.8), constrained_layout=True)
    for _column, condition in enumerate(conditions):
        draw_figure_2_column(axes_2[0, _column], axes_2[1, _column], condition, _column, tract_percentile)
    figure_2.suptitle(
        "Figure 2. Added geographic information from tract-level measures"
    )
    return (figure_2,)


@app.cell
def _(mo):
    mo.md("""
    The top row directly compares tract classifications with linked community-area CHM quartiles.
    Off-diagonal cells show information lost when a tract inherits the coarser label. The bottom
    row compares hypertension and COPD CHM ranks with CDC PLACES ranks as secondary convergent
    context. Both combined-diabetes panels are explicitly not run pending mutual-exclusivity,
    denominator-equivalence, phenotype, and period documentation. PLACES is not a validation
    standard, and off-diagonal cells do not establish that either geography is superior.
    """)
    return


@app.cell
def _(figure_2):
    _ = figure_2
    return


@app.cell
def _(
    aggregation_loss,
    build_geographic_consequence_display_data,
    geographic_consequence_stability,
    geographic_consequence_transitions,
    geographic_mixed_extremes,
):
    geographic_consequence_panels = build_geographic_consequence_display_data(
        geographic_consequence_transitions,
        geographic_mixed_extremes,
        geographic_consequence_stability,
        aggregation_loss,
    )
    return (geographic_consequence_panels,)


@app.cell
def _(coverage_map, geographic_consequence_panels):
    _mixed = geographic_consequence_panels["mixed_extremes"]
    _counts = _mixed.groupby("comparison_geography_id")["condition_id"].nunique()
    _counts.index = _counts.index.astype(int).astype(str).str.zfill(2)
    mixed_area_map = coverage_map.copy()
    mixed_area_map["mixed_condition_n"] = (
        mixed_area_map["geography_id"].astype(str).str.zfill(2).map(_counts).fillna(0).astype(int)
    )
    return (mixed_area_map,)


@app.function
def draw_consequence_bars(axis, rows, value, title, ylabel, show_legend=True):
    order = ["hypertension", "diabetes", "copd"]
    states = ["moves_into_highest_quartile", "moves_out_of_highest_quartile"]
    colors, hatches = ["#0072B2", "#D55E00"], ["", "//"]
    missing = set(order) - set(rows["condition_id"])
    width = 0.36
    for index, state in enumerate(states):
        values = rows.loc[rows["transition_state"].eq(state)].set_index("condition_id")
        heights = [float(values.loc[item, value]) if item in values.index else 0.0 for item in order]
        bars = axis.bar([x + (index - 0.5) * width for x in range(3)], heights,
                        width, color=colors[index], hatch=hatches[index],
                        label=("Moved into Q4" if index == 0 else "Moved out of Q4"))
        axis.bar_label(bars, labels=["" if item in missing else f"{height:.0f}" for item, height in zip(order, heights, strict=True)], fontsize=6, padding=2)
    for condition in missing:
        axis.text(order.index(condition), 0, "Not run", ha="center", va="bottom", fontsize=7)
    axis.set(xticks=range(3), xticklabels=["Hypertension", "Combined\ndiabetes components", "COPD"],
             ylabel=ylabel, title=title)
    if show_legend:
        axis.legend(frameon=False, fontsize=7)


@app.function
def draw_mixed_area_map(axis, frame):
    frame.plot(column="mixed_condition_n", ax=axis, cmap="cividis", vmin=0, vmax=3,
               edgecolor="white", linewidth=0.35, legend=True,
               legend_kwds={"label": "Conditions with both Q1 and Q4 tracts"})
    axis.set_title("C. Mixed-extreme community areas", loc="left", fontsize=9)
    axis.set_axis_off()


@app.function
def draw_stability_panel(axis, annual, noncrossing):
    order = ["hypertension", "diabetes", "copd"]
    colors = ["#0072B2", "#D55E00", "#009E73"]
    for condition, color in zip(order, colors, strict=True):
        rows = annual.loc[annual["condition_id"].eq(condition)].sort_values("time_period")
        if rows.empty:
            continue
        axis.plot(range(len(rows)), 100 * rows["top_quartile_jaccard"], marker="o",
                  color=color, label=("COPD" if condition == "copd" else condition.title()))
        noncrossing_value = noncrossing.loc[
            noncrossing["condition_id"].eq(condition), "quartile_disagree_pct"
        ]
        if not noncrossing_value.empty:
            axis.scatter(3, noncrossing_value.iloc[0], marker="*", s=75, color=color, edgecolor="black")
    axis.set(xticks=range(4), xticklabels=["2022", "2023", "2024", "Noncrossing\nquartile difference"],
             ylabel="Percent", ylim=(0, 100),
             title="D. Annual Q4 overlap and noncrossing results")
    axis.title.set_fontsize(9)
    axis.scatter([], [], marker="*", s=75, color="#4D4D4D", edgecolor="black",
                 label="Noncrossing quartile difference")
    axis.legend(frameon=False, fontsize=7, ncol=2)


@app.cell
def _(geographic_consequence_panels, mixed_area_map, plt):
    figure_3, axes_3 = plt.subplots(2, 2, figsize=(10.0, 7.2), constrained_layout=True)
    _transitions = geographic_consequence_panels["transitions"]
    draw_consequence_bars(axes_3[0, 0], _transitions, "tract_count",
                          "A. Highest-quartile tract transitions", "Tracts, No.")
    draw_consequence_bars(axes_3[0, 1], _transitions, "mean_annual_source_denominator",
                          "B. Represented mean annual source denominator",
                          "Source-observation denominator, mean annual No.", show_legend=False)
    draw_mixed_area_map(axes_3[1, 0], mixed_area_map)
    draw_stability_panel(axes_3[1, 1], geographic_consequence_panels["annual"],
                         geographic_consequence_panels["noncrossing"])
    figure_3.suptitle("Figure 3. Direct cross-frame classification differences and stability")
    return (figure_3,)


@app.cell
def _(mo):
    mo.md("""
    Figure 3 translates cross-scale classification differences into tract counts, repeated mean
    annual source denominators, mixed-extreme community areas, and sensitivity results. Source
    denominators are not unique people. Annual Jaccard percentages describe overlap in Q4 tract
    membership; the star markers show noncrossing-tract quartile disagreement, not the same
    estimand. These results inform descriptive geography choice, not service allocation.
    """)
    return


@app.cell
def _(figure_3):
    _ = figure_3
    return


@app.cell
def _(flow_summary, plt, source_join_display):
    source_flow_figure, _axes = plt.subplots(
        1, 2, figsize=(10, 5), constrained_layout=True, gridspec_kw={"width_ratios": [1.25, 1]}
    )
    _axes[0].axis("off")
    _steps = source_join_display.sort_values("step_order")
    _lines = [
        f"{int(row.step_order)}. {row.step_id.replace('_', ' ')}\n   {int(row.input_rows):,} → {int(row.output_rows):,} rows"
        for row in _steps.itertuples()
    ]
    _axes[0].text(0, 1, "Source assembly and joins\n\n" + "\n".join(_lines), va="top", fontsize=7)
    _stage_labels = {"source_condition_year_records": "Source records",
                     "eligible_condition_year_records": "Eligible records",
                     "pooled_community_areas": "Pooled areas", "case_eligible": "Analysis areas",
                     "suppressed_or_missing_records": "Suppressed/missing"}
    _branch_labels = {"shared": "shared", "C1": "Cardiometabolic", "C2": "COPD"}
    _labels = flow_summary["stage"].map(_stage_labels) + " — " + flow_summary["branch"].map(_branch_labels)
    _axes[1].barh(_labels, flow_summary["count"], color="#0072B2")
    _axes[1].set(xlabel="Geographic-condition-year records or areas", title="Analytic-frame accounting")
    source_flow_figure.suptitle("eFigure 1. Source assembly, joins, and analytic-frame flow")
    return (source_flow_figure,)


@app.cell
def _(analytic):
    _group = ["geography_type", "condition_id", "time_period"]
    annual_quality = analytic.assign(
        available=analytic["published_measure_value"].notna(),
        suppressed=analytic["suppression_flag"].fillna(False),
    ).groupby(_group, observed=True).agg(
        availability=("available", "mean"), suppression=("suppressed", "mean"),
        condition_record_denominator=("denominator", "median"), capture=("capture_rate", "median"),
    ).reset_index()
    return (annual_quality,)


@app.cell
def _(annual_quality, plt):
    annual_quality_figure, _grid = plt.subplots(2, 2, figsize=(9, 6), constrained_layout=True)
    _metrics = (("availability", "Availability, %"), ("suppression", "Suppressed, %"),
                ("condition_record_denominator", "CHM condition-record denominator, median"),
                ("capture", "Source-published capture, median, %"))
    _geo = {"census_tract": "Tract", "chicago_community_area": "Community area"}
    for _axis, (_metric, _label) in zip(_grid.ravel(), _metrics, strict=True):
        for (_geography, _condition), _rows in annual_quality.groupby(["geography_type", "condition_id"]):
            _scale = 100 if _metric in {"availability", "suppression", "capture"} else 1
            _label_text = f"{_geo[_geography]} — {_condition.replace('_', ' ').replace('copd', 'COPD')}"
            _axis.plot(_rows["time_period"].astype(str), _rows[_metric] * _scale,
                       marker="o", label=_label_text)
        _axis.set(xlabel="Year", ylabel=_label)
        _axis.tick_params(axis="x", labelrotation=30)
    _grid[0, 0].legend(frameon=False, fontsize=5, ncol=2)
    annual_quality_figure.suptitle("eFigure 2. Annual CHM coverage, denominator, suppression, and capture")
    return (annual_quality_figure,)


@app.cell
def _(
    descriptive_complementarity_results,
    draw_resolution_heatmap,
    geographic_resolution_matrix,
    plt,
):
    resolution_figure, _grid = plt.subplots(2, 2, figsize=(8.5, 6.5), constrained_layout=True)
    draw_resolution_heatmap(_grid[0, 0], geographic_resolution_matrix, "hypertension", "A. Hypertension quartiles")
    _diabetes = geographic_resolution_matrix.loc[
        geographic_resolution_matrix["condition_id"].eq("diabetes")
        & geographic_resolution_matrix["noncrossing_only"].eq(False)
    ]
    if _diabetes.empty:
        _grid[0, 1].axis("off")
        _grid[0, 1].text(0.5, 0.5, "B. Combined diabetes components quartiles\n\nNot run: combined-component\nsemantics not approved.", ha="center", va="center", fontsize=8)
    else:
        draw_resolution_heatmap(_grid[0, 1], geographic_resolution_matrix, "diabetes", "B. Combined diabetes components quartiles")
    _summary = descriptive_complementarity_results.query(
        "condition_id in ['hypertension', 'diabetes'] and sensitivity_status == 'primary'"
    )
    for _axis, _analysis, _label in ((_grid[1, 0], "A1", "VPC/ICC"), (_grid[1, 1], "A2", "AUC")):
        _rows = _summary.loc[_summary["analysis_id"].eq(_analysis)]
        _column = "vpc_icc" if _analysis == "A1" else "auc"
        _axis.bar(_rows["condition_id"].str.title(), _rows[_column], color=["#0072B2", "#E69F00"])
        _axis.set(ylabel=_label, ylim=(0, 1), title=f"{_label}; descriptive")
    resolution_figure.suptitle("eFigure 3. Cardiometabolic geographic-resolution sensitivity")
    return (resolution_figure,)


@app.cell
def _(complementarity_summary, plt):
    agreement_figure, _axes = plt.subplots(1, 2, figsize=(9, 4), constrained_layout=True)
    _rows = complementarity_summary.query(
        "condition_id in ['hypertension', 'diabetes'] and stratum == 'overall' and not noncrossing_only"
    ).set_index("condition_id")
    _metrics = ["spearman_r", "quadratic_weighted_kappa", "gwet_ac1"]
    _labels = ["Spearman", "Weighted kappa", "Gwet AC1"]
    _rows[_metrics].T.plot.bar(ax=_axes[0], color=["#0072B2", "#E69F00"])
    _axes[0].set(xticklabels=_labels, ylabel="Agreement statistic", ylim=(-0.1, 1))
    _axes[0].legend(title="Condition", frameon=False)
    _axes[1].axis("off")
    _axes[1].text(0, 1, "Uncertainty analysis status\n\nMonte Carlo: not run where compatible source uncertainty was unavailable.\nMissing results are not successful findings.", va="top")
    agreement_figure.suptitle("eFigure 4. Cardiometabolic CHM–PLACES concordance and agreement")
    return (agreement_figure,)


@app.cell
def _(local_spatial_diagnostics, plt, spatial_scan_status):
    spatial_local_figure, _axes = plt.subplots(1, 2, figsize=(9, 4), constrained_layout=True)
    _counts = local_spatial_diagnostics.groupby(
        ["condition_id", "statistic_family"], observed=True
    )["significant_fdr_05"].sum().unstack(fill_value=0)
    _counts.plot.bar(ax=_axes[0], color=["#0072B2", "#E69F00"])
    _axes[0].set(ylabel="FDR-significant areas, No.", xlabel="Condition")
    _axes[0].legend(title="Statistic", frameon=False)
    _axes[1].axis("off")
    _scan = {"not_run_no_governed_scan_population":
             "Spatial scan: not run; governed count and population inputs unavailable."}.get(
                 spatial_scan_status["status"], f"Spatial scan: {spatial_scan_status['status']}"
             )
    _axes[1].text(
        0, 1, _scan + "\n\nBivariate local Moran I is reported where paired inputs are complete.", va="top"
    )
    spatial_local_figure.suptitle("eFigure 5. Cardiometabolic spatial diagnostics")
    return (spatial_local_figure,)


@app.cell
def _(plt):
    collinearity_figure, _axes = plt.subplots(1, 2, figsize=(10, 4.5), constrained_layout=True)
    for _axis in _axes:
        _axis.axis("off")
    _axes[0].text(0, 1, "C1 model not run", va="top", fontweight="bold")
    _axes[1].text(
        0,
        1,
        "Combined diabetes requires documented mutual exclusivity and denominator equivalence.\n"
        "No VIF, coefficient, influence, residual, or spatial result was estimated.",
        va="top",
    )
    collinearity_figure.suptitle("eFigure 6. Cardiometabolic model status")
    return (collinearity_figure,)


@app.cell
def _(coefficient_table, confidence_interval_label, plt):
    _eligible = coefficient_table["model_id"].eq("C2") & coefficient_table["term"].ne("alpha")
    forest_rows = coefficient_table.loc[_eligible].sort_values("estimate")
    forest_y = list(range(len(forest_rows)))
    _term_labels = {
        "beta_c": "COPD exposure (1 frozen IQR)",
        "gamma_age65": "Age 65 years or older (1 SD)",
        "gamma_female": "Female sex (1 SD)",
        "gamma_poverty": "Below poverty level (1 SD)",
        "gamma_capture": "EHR capture (1 SD)",
    }
    forest_labels = [f"{_term_labels[term]} — {confidence_interval_label(float(level))}"
                     for term, level in zip(forest_rows["term"],
                                            forest_rows["confidence_level"], strict=True)]
    forest_figure, forest_axis = plt.subplots(figsize=(7.2, 4.5), constrained_layout=True)
    forest_axis.errorbar(
        forest_rows["estimate"],
        forest_y,
        xerr=[forest_rows["estimate"] - forest_rows["ci_low"],
              forest_rows["ci_high"] - forest_rows["estimate"]],
        fmt="o",
        color="#0072B2",
        ecolor="#333333",
        capsize=2,
    )
    forest_axis.axvline(0, color="#666666", linestyle="--", linewidth=0.8)
    forest_axis.set(yticks=forest_y, yticklabels=forest_labels,
                    xlabel="Life-expectancy difference (years)",
            title="eFigure 7. COPD coefficient forest; candidate estimate, not authorized")
    return (forest_figure,)


@app.function
def draw_diagnostic_top(axes, c2):
    axes[0].scatter(c2["fitted_value"], c2["residual"], s=10)
    axes[0].axhline(0, color="#555555")
    axes[0].set(title="A. Residuals", xlabel="Fitted", ylabel="Residual")
    axes[1].scatter(c2["qq_theoretical_quantile"], c2["qq_sample_quantile"], s=10)
    _qq = [c2["qq_theoretical_quantile"].min(), c2["qq_theoretical_quantile"].max()]
    axes[1].plot(_qq, _qq, color="#555555", linestyle="--")
    axes[1].set(title="B. Q-Q", xlabel="Theoretical", ylabel="Observed")
    axes[2].scatter(c2["leverage"], c2["externally_studentized_residual"], s=10)
    axes[2].axvline(12 / len(c2), color="#D55E00", linestyle="--")
    axes[2].axhline(3, color="#555555", linestyle=":")
    axes[2].axhline(-3, color="#555555", linestyle=":")
    axes[2].set(title="C. Leverage", xlabel="Leverage", ylabel="Studentized residual")
    axes[3].stem(range(len(c2)), c2["cooks_distance"], markerfmt=".")
    axes[3].axhline(4 / len(c2), color="#D55E00", linestyle="--")
    axes[3].set(title="D. Influence", xlabel="Area index", ylabel="Cook distance")


@app.function
def draw_diagnostic_bottom(axes, temporal, loo, area_loo, robust):
    axes[0].plot(temporal["time_period"].astype(str), temporal["estimate"], marker="o")
    axes[0].set(title="A. Annual", xlabel="Year", ylabel="Estimate")
    axes[0].tick_params(axis="x", labelrotation=30)
    axes[1].plot(loo["omitted_year"], loo["estimate"], marker="o")
    axes[1].set(title="B. Leave-one-year-out", xlabel="Omitted year", ylabel="Estimate")
    axes[2].scatter(range(len(area_loo)), area_loo["estimate"], s=10)
    axes[2].axhline(area_loo["estimate"].median(), color="#555555", linestyle="--")
    axes[2].set(title="C. Leave-one-area-out", xlabel="Omitted area index",
                ylabel="Adjusted estimate")
    axes[3].scatter(robust["estimate"], robust["variant_label"], s=12)
    axes[3].set(title="D. Extended sensitivities", xlabel="Estimate", ylabel="Variant")


@app.cell
def _(
    adjusted_diagnostic_data,
    leave_one_year_out,
    plt,
    robustness_summary,
    temporal_models,
):
    diagnostic_figure, _grid = plt.subplots(1, 4, figsize=(12, 3.5), constrained_layout=True)
    _diagnostic_axes = _grid.ravel()
    _c2 = adjusted_diagnostic_data.loc[adjusted_diagnostic_data["model"].eq("C2")]
    draw_diagnostic_top(_diagnostic_axes, _c2)
    diagnostic_figure.suptitle("eFigure 8. COPD residual, Q-Q, leverage, and influence diagnostics")
    robustness_figure, _robust_grid = plt.subplots(2, 2, figsize=(9, 6), constrained_layout=True)
    _temporal = temporal_models.loc[temporal_models["model_id"].eq("C2_unadjusted")]
    _loo = leave_one_year_out.loc[leave_one_year_out["model_id"].eq("C2_unadjusted")]
    _robust = robustness_summary.loc[robustness_summary["model"].eq("C2")].dropna(subset=["estimate"])
    _area_loo = _robust.loc[_robust["variant"].str.startswith("leave_one_area_out")].copy()
    _robust = _robust.loc[~_robust["variant"].str.startswith("leave_one_area_out")].copy()
    _variant_labels = {
        "continuous_capture_reference": "Continuous capture",
        "exclude_all_prespecified_flagged_areas": "Exclude flagged areas",
        "frozen_capture_quartiles": "Capture quartiles",
        "leave_one_primary_year_out:2022": "Omit 2022",
        "leave_one_primary_year_out:2023": "Omit 2023",
        "leave_one_primary_year_out:2024": "Omit 2024",
        "population_weighted_ols": "Population weighted",
    }
    _robust["variant_label"] = _robust["variant"].replace(_variant_labels)
    draw_diagnostic_bottom(_robust_grid.ravel(), _temporal, _loo, _area_loo, _robust)
    robustness_figure.suptitle("eFigure 9. COPD temporal, weighting, capture, and influence sensitivities")
    return diagnostic_figure, robustness_figure


@app.cell
def _(
    alternative_spatial_weights,
    plt,
    spatial_diagnostics,
    spatial_error_summary,
):
    spatial_sensitivity_figure, _axes = plt.subplots(1, 3, figsize=(10, 3.5), constrained_layout=True)
    _c2 = spatial_diagnostics.loc[spatial_diagnostics["model_id"].eq("C2")]
    _axes[0].bar(["Queen"], _c2["observed_i"], color="#0072B2")
    _axes[0].set(ylabel="Residual Moran I", title="A. Primary weights")
    _weight_labels = alternative_spatial_weights["weights_definition"].map(
        {"rook": "Rook", "smallest_connected_distance_band": "Connected distance band"}
    )
    _axes[1].bar(_weight_labels,
                 alternative_spatial_weights["observed_i"], color="#E69F00")
    _axes[1].set(ylabel="Residual Moran I", title="B. Alternative weights")
    _axes[1].tick_params(axis="x", labelrotation=30)
    _axes[2].axis("off")
    _row = spatial_error_summary.iloc[0]
    _status = {"mandatory_spatial_sensitivity_run":
               "Completed after the prespecified Moran trigger."}.get(
                   str(_row["spatial_error_status"]), str(_row["spatial_error_status"])
               )
    _robustness = {"not_model_sensitive":
                   "Direction and robustness classification were unchanged."}.get(
                       str(_row["model_sensitivity_status"]), str(_row["model_sensitivity_status"])
                   )
    _axes[2].text(0, 1, "Spatial-error sensitivity\n\n" + _status + "\n" + _robustness +
                  "\nCandidate result remains unauthorized.", va="top")
    spatial_sensitivity_figure.suptitle("eFigure 10. COPD residual spatial dependence and sensitivity")
    return (spatial_sensitivity_figure,)


@app.cell
def _(
    geographic_consequence_stability,
    geographic_consequence_transitions,
    plt,
):
    geographic_consequence_figure, _axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    _moves = geographic_consequence_transitions.query(
        "sensitivity_status == 'all_eligible' and "
        "transition_state in ['moves_into_highest_quartile', 'moves_out_of_highest_quartile']"
    )
    _pivot = _moves.pivot_table(index=["comparison_geography_type", "condition_id"],
                                columns="transition_state", values="tract_count", aggfunc="sum")
    _pivot.index = [
        f"{'Community' if geo == 'chicago_community_area' else 'ZCTA'}\n"
        f"{condition.upper() if condition == 'copd' else condition.title()}"
        for geo, condition in _pivot.index
    ]
    _pivot.columns = ["Moved into highest quartile", "Moved out of highest quartile"]
    _pivot.plot.bar(ax=_axes[0], color=["#0072B2", "#D55E00"], rot=0)
    _axes[0].set(ylabel="Tracts, No.", xlabel="Coarser geography and condition",
                 title="A. Highest-quartile transitions")
    _annual = geographic_consequence_stability.query(
        "result_type == 'annual_jaccard' and sensitivity_status == 'all_eligible'"
    )
    _names = {"chicago_community_area": "Community area", "zcta": "ZCTA"}
    for (_geo, _condition), _rows in _annual.groupby(["comparison_geography_type", "condition_id"]):
        _condition_label = _condition.upper() if _condition == "copd" else _condition.title()
        _axes[1].plot(_rows["time_period"], _rows["top_quartile_jaccard"], marker="o",
                      label=f"{_names[_geo]} — {_condition_label}")
    _axes[1].set(ylabel="Top-quartile Jaccard", xlabel="Year", ylim=(0, 1),
                 title="B. Annual classification stability")
    _axes[1].legend(frameon=False, fontsize=6.5, ncols=2, loc="lower right")
    geographic_consequence_figure.suptitle("eFigure 11. Direct cross-frame classification differences")
    return (geographic_consequence_figure,)


@app.cell
def _(fdr_spatial_survival, plt):
    fdr_survival_figure, _axis = plt.subplots(figsize=(8.5, 4.5), constrained_layout=True)
    _plot = fdr_spatial_survival.copy()
    _statistic_labels = {"getis_ord_gi_star": "Getis-Ord Gi*", "local_moran": "Local Moran I"}
    _plot["label"] = (
        _plot["condition_id"].str.title() + "\n" + _plot["statistic_family"].map(_statistic_labels)
    )
    _positions = list(range(len(_plot)))
    _axis.bar([value - 0.18 for value in _positions], _plot["raw_p_lt_05_count"],
              width=0.36, label="Raw $P$ < .05", color="#E69F00")
    _axis.bar([value + 0.18 for value in _positions], _plot["fdr_surviving_count"],
              width=0.36, label="Survived BH-FDR", color="#0072B2")
    _axis.set(xticks=_positions, xticklabels=_plot["label"], ylabel="Community areas, No.",
              title="Community-area local signals before and after FDR control")
    _axis.tick_params(axis="x", labelrotation=0)
    _axis.legend(frameon=False)
    fdr_survival_figure.suptitle("eFigure 12. Spatial classification survival after FDR control")
    return (fdr_survival_figure,)


@app.cell
def _(
    agreement_figure,
    annual_quality_figure,
    collinearity_figure,
    datetime,
    diagnostic_figure,
    fdr_survival_figure,
    forest_figure,
    geographic_consequence_figure,
    output_dir,
    png_metadata,
    resolution_figure,
    robustness_figure,
    source_flow_figure,
    spatial_local_figure,
    spatial_sensitivity_figure,
    timezone,
):
    supplements = [
        ("source_assembly_flow", source_flow_figure), ("annual_data_quality", annual_quality_figure),
        ("cardiometabolic_resolution", resolution_figure), ("cardiometabolic_agreement", agreement_figure),
        ("cardiometabolic_spatial", spatial_local_figure), ("cardiometabolic_collinearity", collinearity_figure),
        ("coefficient_forest", forest_figure), ("model_diagnostics", diagnostic_figure),
        ("model_robustness", robustness_figure), ("spatial_sensitivity", spatial_sensitivity_figure),
        ("geographic_consequences", geographic_consequence_figure),
        ("fdr_spatial_survival", fdr_survival_figure),
    ]
    pdf_metadata = {
        "Creator": "ChicagoHealthMap deterministic marimo pipeline",
        "CreationDate": datetime(2026, 7, 15, tzinfo=timezone.utc),
        "ModDate": datetime(2026, 7, 15, tzinfo=timezone.utc),
    }
    for _name, _figure in supplements:
        _figure.savefig(
            output_dir / f"supplement_{_name}.png", bbox_inches="tight", metadata=png_metadata
        )
        _figure.savefig(
            output_dir / f"supplement_{_name}.pdf", bbox_inches="tight", metadata=pdf_metadata
        )
    return


@app.cell
def _(figure_1, figure_2, figure_3, output_dir, png_metadata):
    figure_1.savefig(
        output_dir / "figure_1_data_flow_coverage.png", bbox_inches="tight", dpi=200,
        metadata=png_metadata
    )
    figure_2.savefig(
        output_dir / "figure_2_cardiometabolic_patterns.png",
        bbox_inches="tight",
        dpi=200,
        metadata=png_metadata,
    )
    figure_3.savefig(
        output_dir / "figure_3_copd_patterns.png", bbox_inches="tight", dpi=200,
        metadata=png_metadata
    )
    return


@app.cell
def _(datetime, figure_1, figure_2, figure_3, output_dir, timezone):
    for number, figure in ((1, figure_1), (2, figure_2), (3, figure_3)):
        figure.savefig(
            output_dir / f"figure_{number}_submission.pdf",
            bbox_inches="tight",
            metadata={
                "Creator": "ChicagoHealthMap deterministic marimo pipeline",
                "CreationDate": datetime(2026, 7, 15, tzinfo=timezone.utc),
                "ModDate": datetime(2026, 7, 15, tzinfo=timezone.utc),
            },
        )
    return


@app.cell
def _():
    accessibility_encoding_contract = {
        "simulations_generated": ["grayscale", "protanopia", "deuteranopia"],
        "manual_inspection_status": "manual_inspection_required_for_current_output_hashes",
        "sequential_map_encoding": "cividis_luminance_order",
        "rank_gap_secondary_encoding": "circle_triangle_markers_and_dot_slash_map_hatching",
        "categorical_secondary_encoding": "not_applicable_no_categorical_main_map_fill",
    }
    return (accessibility_encoding_contract,)


@app.function
def observed_hatches(figure):
    artists = [artist for axis in figure.axes for artist in (*axis.collections, *axis.patches)]
    return sorted(
        {
            artist.get_hatch()
            for artist in artists
            if hasattr(artist, "get_hatch") and artist.get_hatch()
        }
    )


@app.cell
def _(figure_1, figure_2, figure_3):
    categorical_hatches = observed_hatches(figure_1)
    transition_hatches = observed_hatches(figure_3)
    quartile_annotations = sum(
        text.get_text().endswith("%") for axis in figure_2.axes for text in axis.texts
    )
    _stability_axis = next(
        axis for axis in figure_3.axes if "Annual Q4 overlap" in axis.get_title()
    )
    stability_marker_vertices = sorted(
        {
            len(path.vertices)
            for collection in _stability_axis.collections
            for path in collection.get_paths()
        }
    )
    display_encoding_audit = {
        "categorical_hatching": {"observed": categorical_hatches, "passed": True,
                                  "status": "not_applicable_no_categorical_main_map_fill"},
        "transition_hatching": {"observed": transition_hatches,
                                 "passed": "//" in transition_hatches},
        "quartile_matrix_annotations": {"observed": quartile_annotations,
                                         "passed": quartile_annotations == 32},
        "stability_marker_shapes": {"observed_vertex_counts": stability_marker_vertices,
                                    "passed": bool(stability_marker_vertices)},
    }
    return (display_encoding_audit,)


@app.function
def simulate_accessibility(image, mode):
    import numpy as _np

    rgb = image[..., :3]
    if mode == "grayscale":
        gray = rgb @ _np.array([0.2126, 0.7152, 0.0722])
        return _np.repeat(gray[..., None], 3, axis=-1)
    matrices = {
        "protanopia": _np.array(
            [[0.56667, 0.43333, 0], [0.55833, 0.44167, 0], [0, 0.24167, 0.75833]]
        ),
        "deuteranopia": _np.array([[0.625, 0.375, 0], [0.7, 0.3, 0], [0, 0.3, 0.7]]),
    }
    return _np.clip(rgb @ matrices[mode].T, 0, 1)


@app.function
def evaluate_palette_accessibility(encoding_contract):
    import numpy as _np
    from matplotlib import colormaps as _colormaps, colors as _colors

    positions = [0.1, 0.5, 0.9]
    categorical = [
        row[2]
        for key in ("capture", "inclusion", "qualification")
        for row in encoding_contract[key]
    ]
    palettes = {
        "cividis": _colormaps[encoding_contract["sequential_cmap"]](positions)[:, :3],
        "RdBu_r": _colormaps[encoding_contract["diverging_cmap"]](positions)[:, :3],
        "categorical": _np.array([_colors.to_rgb(value) for value in categorical]),
    }
    results = {}
    for name, palette in palettes.items():
        results[name] = {}
        for mode in ("grayscale", "protanopia", "deuteranopia"):
            transformed = simulate_accessibility(palette, mode)
            distances = _np.linalg.norm(transformed[:, None] - transformed[None, :], axis=2)
            minimum = distances[_np.triu_indices(len(palette), 1)].min()
            results[name][mode] = {"minimum_pairwise_rgb_distance": float(minimum)}
    return results


@app.cell
def _(
    DISPLAY_ENCODING_CONTRACT,
    accessibility_encoding_contract,
    display_encoding_audit,
):
    figure_accessibility_qa = {
        **accessibility_encoding_contract,
        "palette_simulations": evaluate_palette_accessibility(DISPLAY_ENCODING_CONTRACT),
        "secondary_encodings_verified": display_encoding_audit,
    }
    return (figure_accessibility_qa,)


@app.cell
def _(figure_accessibility_qa, mpimg, output_dir):
    figure_qa = {}
    for name in (
        "figure_1_data_flow_coverage.png",
        "figure_2_cardiometabolic_patterns.png",
        "figure_3_copd_patterns.png",
    ):
        image = mpimg.imread(output_dir / name)
        simulations = {}
        for mode in figure_accessibility_qa["simulations_generated"]:
            transformed = simulate_accessibility(image, mode)
            luminance = (
                0.2126 * transformed[..., 0]
                + 0.7152 * transformed[..., 1]
                + 0.0722 * transformed[..., 2]
            )
            simulations[mode] = {
                "pixel_standard_deviation": float(transformed.std()),
                "luminance_range": float(luminance.max() - luminance.min()),
                "nonblank": bool(transformed.std() > 0.05),
            }
        figure_qa[name] = {
            "pixel_height": int(image.shape[0]),
            "pixel_width": int(image.shape[1]),
            "file_size_bytes": (output_dir / name).stat().st_size,
            "grayscale_renderable": image.ndim in {2, 3},
            "color_vision_palette_review": "cividis_and_RdBu_r_with_grayscale_distinguishable_states",
            "simulations": simulations,
        }
    return (figure_qa,)


@app.cell
def _(
    figure_accessibility_passes,
    figure_accessibility_qa,
    figure_qa,
    json,
    output_dir,
):
    automated_pass = figure_accessibility_passes(figure_qa, figure_accessibility_qa)
    _ = (output_dir / "figure_qa.json").write_text(
        json.dumps(
            {
                "status": "passed_automated_render_and_accessibility_smoke_check"
                if automated_pass
                else "failed_automated_render_and_accessibility_smoke_check",
                "submission_format": "PDF vector exports",
                "accessibility": figure_accessibility_qa,
                "figures": figure_qa,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return


@app.cell
def _(sha256):
    def file_sha256(path):
        digest = sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    return (file_sha256,)


@app.cell
def _(subprocess):
    def git_state(root):
        try:
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            return head, bool(status.strip())
        except (OSError, subprocess.CalledProcessError):
            return "unavailable_broken_or_absent_git_metadata", True

    return (git_state,)


@app.cell
def _(mo):
    mo.md("""
    ### References

    1. Ghildayal N, et al. Public health surveillance in electronic health records: lessons from PCORnet. *Prev Chronic Dis.* 2024;21:E51. [doi:10.5888/pcd21.230417](https://doi.org/10.5888/pcd21.230417)
    2. Chen T, et al. Small-area estimation for public health surveillance using electronic health record data: reducing the impact of underrepresentation. *BMC Public Health.* 2022;22(1):1515. [doi:10.1186/s12889-022-13809-2](https://doi.org/10.1186/s12889-022-13809-2)
    3. Allen KS, et al. Electronic health records for population health management: comparison of electronic health record-derived hypertension prevalence measures against established survey data. *Online J Public Health Inform.* 2024;16:e48300. [doi:10.2196/48300](https://doi.org/10.2196/48300)
    4. Winkelman TN, et al. Population estimates and hypertension and diabetes prevalence: cross-sectional quantitative study comparing electronic health record-derived counts, Census, and CDC PLACES. *JMIR Public Health Surveill.* 2026;12:e86337. [doi:10.2196/86337](https://doi.org/10.2196/86337)
    5. Klompas M, et al. State and local chronic disease surveillance using electronic health record systems. *Am J Public Health.* 2017;107(9):1406-1412. [doi:10.2105/AJPH.2017.303874](https://doi.org/10.2105/AJPH.2017.303874)
    6. Hunt BR, et al. Life expectancy varies in local communities in Chicago: racial and spatial disparities and correlates. *J Racial Ethn Health Disparities.* 2015;2(4):425-433. [doi:10.1007/s40615-015-0089-8](https://doi.org/10.1007/s40615-015-0089-8)
    7. Dixon BE, et al. Measuring population health using electronic health records: exploring biases and representativeness in a community health information exchange. *Stud Health Technol Inform.* 2015;216:1009. PMID:26262310.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Statistical method references

    8. Cohen J. Weighted kappa: nominal scale agreement with provision for scaled disagreement or partial credit. *Psychol Bull.* 1968;70(4):213-220. [doi:10.1037/h0026256](https://doi.org/10.1037/h0026256)
    9. Gwet KL. Computing inter-rater reliability and its variance in the presence of high agreement. *Br J Math Stat Psychol.* 2008;61(pt 1):29-48. [doi:10.1348/000711006X126600](https://doi.org/10.1348/000711006X126600)
    10. Nakagawa S, Johnson PCD, Schielzeth H. The coefficient of determination and intraclass correlation coefficient from generalized linear mixed-effects models revisited and expanded. *J R Soc Interface.* 2017;14(134):20170213. [doi:10.1098/rsif.2017.0213](https://doi.org/10.1098/rsif.2017.0213)
    11. Hanley JA, McNeil BJ. The meaning and use of the area under a receiver operating characteristic curve. *Radiology.* 1982;143(1):29-36. [doi:10.1148/radiology.143.1.7063747](https://doi.org/10.1148/radiology.143.1.7063747)
    12. Efron B. Bootstrap methods: another look at the jackknife. *Ann Stat.* 1979;7(1):1-26. [doi:10.1214/aos/1176344552](https://doi.org/10.1214/aos/1176344552)
    13. Long JS, Ervin LH. Using heteroscedasticity consistent standard errors in the linear regression model. *Am Stat.* 2000;54(3):217-224. [doi:10.1080/00031305.2000.10474549](https://doi.org/10.1080/00031305.2000.10474549)
    14. Moran PAP. Notes on continuous stochastic phenomena. *Biometrika.* 1950;37(1-2):17-23. [doi:10.1093/biomet/37.1-2.17](https://doi.org/10.1093/biomet/37.1-2.17)
    15. Anselin L. Local indicators of spatial association-LISA. *Geogr Anal.* 1995;27(2):93-115. [doi:10.1111/j.1538-4632.1995.tb00338.x](https://doi.org/10.1111/j.1538-4632.1995.tb00338.x)
    16. Getis A, Ord JK. The analysis of spatial association by use of distance statistics. *Geogr Anal.* 1992;24(3):189-206. [doi:10.1111/j.1538-4632.1992.tb00261.x](https://doi.org/10.1111/j.1538-4632.1992.tb00261.x)
    17. Benjamini Y, Hochberg Y. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *J R Stat Soc Series B.* 1995;57(1):289-300. [doi:10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    #### Reporting guidance and data-source references

    18. von Elm E, Altman DG, Egger M, et al. The STROBE statement: guidelines for reporting observational studies. *PLoS Med.* 2007;4(10):e296. [doi:10.1371/journal.pmed.0040296](https://doi.org/10.1371/journal.pmed.0040296)
    19. Benchimol EI, et al. The REporting of studies Conducted using Observational Routinely-collected health Data statement. *PLoS Med.* 2015;12(10):e1001885. [doi:10.1371/journal.pmed.1001885](https://doi.org/10.1371/journal.pmed.1001885)
    20. JAMA Health Forum. [Instructions for Authors](https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors). Accessed August 27, 2026.
    21. Centers for Disease Control and Prevention. [PLACES Census Tract Data, GIS Friendly Format, 2025 release, dataset yjkw-uj5s](https://data.cdc.gov/d/yjkw-uj5s).
    22. US Census Bureau. American Community Survey 5-Year Detailed Tables, 2019, 2022, and 2024 releases. Tables B01001, B03002, B15003, B17001, B19013, B23025, B25044, and B27001.
    23. Chicago Health Atlas. [Life expectancy, indicator VRLE](https://chicagohealthatlas.org/indicators/VRLE). Originating source: Illinois Department of Public Health Death Certificate Data Files. Accessed July 14, 2026.
    24. City of Chicago. [Boundaries-Community Areas, dataset igwz-8jzy](https://data.cityofchicago.org/d/igwz-8jzy). Accessed July 14, 2026.
    25. CONSCIENCE Project. [ChicagoHealthMap.com: CONnecting SCIence—ENgaging Chicago for Equity](https://chicagohealthmap.com). Chicago, IL: Rush University System for Health, Rush Health Equity Data Analytics Studio. Accessed July 13, 2026. Methods statements were preserved in the governed July 13, 2026 archive snapshot.

    References 1 through 7 were verified through PubMed or full-text evidence records. References
    8 through 19 were verified against primary journal records. Data-source citations reproduce
    the frozen source registry. Reference 20 was checked directly for this review package.
    Reference 25 reproduces the website-required citation and is tied to the governed archive.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Artifact gallery and deterministic manifest

    The gallery inventories aggregate review tables, vector and raster figures, supplemental
    diagnostics, and nonnumeric handoff files. Row-level analytic dataset carriers remain governed
    local files and are excluded from this rendered gallery. Every listed file is checksum-bound
    and governed by `results_authorized=false`.

    ### Deterministic output manifest

    The manifest binds each local artifact to the frozen input, SAP, code, topology, and
    run controls. The notebook hashes byte-complete files after deterministic writes and
    serializes sorted JSON. A second execution can detect numerical or rendering drift.
    Authorization remains false, and the manifest contains no runtime timestamp or credential.
    """)
    return


@app.cell
def _(build_great_table, dataset_output_names, mo, output_dir, output_names, pd):
    review_output_names = [name for name in output_names if name not in dataset_output_names]
    artifact_gallery = pd.DataFrame(
        {
            "artifact": review_output_names,
            "format": [name.rsplit(".", maxsplit=1)[-1].upper() for name in review_output_names],
            "bytes": [(output_dir / name).stat().st_size for name in review_output_names],
        }
    )
    _items = [f"- `{name}`" for name in review_output_names]
    _table = build_great_table(
        artifact_gallery,
        title="Aggregate statistician-review artifacts",
        subtitle="Checksum-bound outputs; results_authorized=false",
        table_id="artifact_gallery",
    )
    mo.vstack([_table, mo.md("\n".join(_items))])
    return


@app.cell
def _(master_dataset_gallery):
    dataset_output_names = [
        "00_master_analytic_dataset.parquet",
        "00_master_analytic_dataset.csv",
        "00_master_analytic_dataset.schema.json",
        "00_master_analytic_dataset_lineage.csv",
        "00_master_analytic_dataset_manifest.json",
        *master_dataset_gallery,
        "chicago_healthmap_zcta_sidecar.parquet",
        "chicago_healthmap_zcta_sidecar.csv",
        "chicago_healthmap_zcta_sidecar.schema.json",
        "chicago_healthmap_zcta_sidecar_lineage.csv",
        "chicago_healthmap_zcta_sidecar_manifest.json",
        "chicago_healthmap_zcta_sidecar_source_join_manifest.json",
        "chicago_healthmap_zcta_sidecar_data_book.csv",
        "chicago_healthmap_zcta_sidecar_data_book.html",
    ]
    return (dataset_output_names,)


@app.cell
def _():
    reader_guide_output_names = [
        "editorial_curation_manifest.json", "editorial_display_manifest.json",
        "main_display_reader_guide.json", "model_interpretation_guide.json",
    ]
    return (reader_guide_output_names,)


@app.cell
def _(reader_guide_output_names):
    table_output_names = [
        "biostatistical_display_review.csv", "biostatistical_display_review.html",
        "table_1_resource_quality.csv", "table_1_resource_quality.html",
        "etable_1_resource_quality.csv", "etable_1_resource_quality.html",
        "table_2_geographic_resolution.csv", "table_2_geographic_resolution.html",
        "table_2_model_readiness_sensitivities.csv", "table_2_model_readiness_sensitivities.html",
        "etable_2_model_readiness_sensitivities.html", "etable_2_model_readiness_sensitivities.csv", "etable_4_robustness_summary.html",
        "etable_5_tract_complementarity.html",
        "etable_6_geographic_resolution.html", "etable_7_descriptive_complementarity_methods.html",
        "etable_8_geographic_consequences.html", "etable_8_geographic_consequences.csv",
        "etable_9_uncertainty_feasibility.html", "etable_9_uncertainty_feasibility.csv",
    ]
    handoff_output_names = [
        "manuscript_results_handoff.json", "word_handoff_blocked.md", "word_handoff_blocked.html",
        "word_handoff_manifest.json", "manuscript_result_narratives.json",
        "coauthor_interpretation_guide.json", "supplement_table_of_contents.json",
        *reader_guide_output_names, "figure_legends.json", "figure_qa.json",
    ]
    paper_output_names = [
        *table_output_names, *handoff_output_names,
        "supplement_full_coefficient_table.csv", "supplement_full_coefficient_table.html",
        "supplement_model_gate_diagnostics.csv",
        "figure_1_data_flow_coverage.png",
        "figure_2_cardiometabolic_patterns.png",
        "figure_3_copd_patterns.png",
        "figure_1_submission.pdf",
        "figure_2_submission.pdf", "figure_3_submission.pdf",
    ]
    return (paper_output_names,)


@app.cell
def _():
    supplement_figure_stems = [
        "source_assembly_flow", "annual_data_quality", "cardiometabolic_resolution",
        "cardiometabolic_agreement", "cardiometabolic_spatial", "cardiometabolic_collinearity",
        "coefficient_forest", "model_diagnostics", "model_robustness", "spatial_sensitivity",
        "geographic_consequences", "fdr_spatial_survival",
    ]
    return (supplement_figure_stems,)


@app.cell
def _(supplement_figure_stems):
    supplement_output_names = [
        "supplement_temporal_models.csv", "supplement_leave_one_year_out.csv", "supplement_disruption_audit.csv",
        "supplement_influence_c1.csv", "supplement_influence_c2.csv",
        "supplement_spatial_diagnostics.csv", "supplement_spatial_error_sensitivity.csv", "supplement_robustness_summary.csv",
        "supplement_alternative_spatial_weights.csv",
        "supplement_adjusted_diagnostic_data.csv",
        "supplement_concordance_summary.csv", "supplement_discordance_quartile.csv",
        "supplement_discordance_tertile.csv",
        "supplement_multiplicity_inventory.csv",
        "supplement_tract_complementarity.csv",
        "supplement_within_community_heterogeneity.csv",
        "supplement_aggregation_loss.csv",
        "supplement_geographic_resolution_matrix.csv", "supplement_geographic_main_evidence.csv",
        "supplement_geographic_consequence_details.csv",
        "supplement_geographic_consequence_transitions.csv",
        "supplement_geographic_mixed_extremes.csv",
        "supplement_geographic_consequence_annual.csv",
        "supplement_geographic_consequence_stability.csv",
        "supplement_zcta_linkage.csv",
        "supplement_local_spatial_diagnostics.csv", "supplement_local_spatial_availability.csv",
        "supplement_fdr_spatial_survival.csv",
        "supplement_spatial_scan_status.csv", "supplement_descriptive_complementarity_methods.csv",
        "supplement_descriptive_claim_evidence_audit.csv",
        "etable_7_descriptive_complementarity_methods.html",
        "supplement_claim_evidence_audit.csv",
        "supplement_concordance_bootstrap.csv",
        *[f"supplement_{stem}.{suffix}" for stem in supplement_figure_stems
          for suffix in ("png", "pdf")],
    ]
    return (supplement_output_names,)


@app.cell
def _(dataset_output_names, paper_output_names, supplement_output_names):
    output_names = [*dataset_output_names, *paper_output_names, *supplement_output_names]
    return (output_names,)


@app.cell
def _(output_dir, output_names):
    missing_outputs = [name for name in output_names if not (output_dir / name).is_file()]
    if missing_outputs:
        raise ValueError(f"notebook output inventory incomplete: {missing_outputs}")
    allowed_outputs = {*output_names, "notebook_run_manifest.json"}
    unexpected_outputs = sorted(
        path.name
        for path in output_dir.iterdir()
        if path.is_file() and path.name not in allowed_outputs
    )
    if unexpected_outputs:
        raise ValueError(f"notebook output inventory has unexpected files: {unexpected_outputs}")
    return


@app.cell
def _(Path, project_root):
    notebook_path = Path(__file__).resolve()
    analysis_source_paths = [
        project_root / "src/chicagohealthmap/analysis/case_studies.py",
        project_root / "src/chicagohealthmap/analysis/sap_analyses.py",
        project_root / "src/chicagohealthmap/analysis/robustness.py",
        project_root / "src/chicagohealthmap/analysis/spatial.py",
        project_root / "src/chicagohealthmap/analysis/reporting.py",
        project_root / "src/chicagohealthmap/analysis/tract_complementarity.py",
        project_root / "src/chicagohealthmap/analysis/paper_audit.py",
        project_root / "src/chicagohealthmap/analysis/paper_displays.py",
    ]
    return analysis_source_paths, notebook_path


@app.cell
def _(analysis_source_paths, file_sha256, project_root):
    analysis_source_sha256 = {
        path.relative_to(project_root).as_posix(): file_sha256(path)
        for path in analysis_source_paths
    }
    return (analysis_source_sha256,)


@app.cell
def _(file_sha256, output_dir, output_names):
    artifact_binding = {
        "output_sha256": {name: file_sha256(output_dir / name) for name in output_names},
        "output_inventory": [*output_names, "notebook_run_manifest.json"],
    }
    return (artifact_binding,)


@app.cell
def _(file_sha256, governance_path, project_root):
    sap_path = project_root / "docs/analysis/statistical_analysis_plan.md"
    uv_lock_path = project_root / "uv.lock"
    handoff_ledger_paths = [
        project_root / "docs/analysis/chm_complementarity_evidence_ledger.md",
        project_root / "docs/analysis/chm_complementarity_display_ledger.csv",
        project_root / "docs/analysis/master_notebook_research_provenance.md",
        project_root / "config/manuscript/jama_health_forum.yml",
    ]
    source_hashes = {
        "sap_path": sap_path.relative_to(project_root).as_posix(),
        "sap_sha256": file_sha256(sap_path),
        "uv_lock_path": uv_lock_path.relative_to(project_root).as_posix(),
        "uv_lock_sha256": file_sha256(uv_lock_path),
        "governance_path": governance_path.relative_to(project_root).as_posix(),
        "governance_sha256": file_sha256(governance_path),
        "handoff_ledger_sha256": {
            path.relative_to(project_root).as_posix(): file_sha256(path)
            for path in handoff_ledger_paths
        },
    }
    return (source_hashes,)


@app.cell
def _(
    analysis_source_sha256,
    artifact_binding,
    dataset_path,
    file_sha256,
    git_state,
    notebook_path,
    project_root,
    source_hashes,
):
    git_commit, git_dirty = git_state(project_root)
    run_hashes = {
        **artifact_binding,
        "input_path": dataset_path.name,
        "input_sha256": file_sha256(dataset_path),
        "notebook_path": notebook_path.relative_to(project_root).as_posix(),
        "notebook_sha256": file_sha256(notebook_path),
        **source_hashes,
        "analysis_source_sha256": analysis_source_sha256,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "dirty_source_binding": (
            "explicit_source_sha256_git_metadata_unavailable"
            if git_commit == "unavailable_broken_or_absent_git_metadata"
            else "git_head_plus_explicit_source_sha256"
        ),
    }
    return (run_hashes,)


@app.cell
def _(temporal_models):
    provenance_columns = [
        "exposure_source_id",
        "exposure_snapshot_id",
        "outcome_source_id",
        "outcome_snapshot_id",
        "outcome_lineage_id",
    ]
    provenance_values = {
        column: sorted(temporal_models[column].dropna().astype(str).unique())
        for column in provenance_columns
    }
    if any(len(values) != 1 for values in provenance_values.values()):
        raise ValueError(f"temporal provenance is not singular: {provenance_values}")
    if provenance_values["outcome_source_id"] != ["chicago_health_atlas_life_expectancy"]:
        raise ValueError("registered Atlas outcome source changed")
    analysis_provenance = {key: values[0] for key, values in provenance_values.items()}
    return (analysis_provenance,)


@app.cell
def _(
    analysis_provenance,
    c2_weights,
    full_weights,
    permutations,
    run_hashes,
    seed,
):
    manifest_core = {
        **run_hashes,
        "seed": seed,
        "permutations": permutations,
        "time_zone": "America/Chicago",
        "chp_exposure_source_id": analysis_provenance["exposure_source_id"],
        "chp_exposure_snapshot_id": analysis_provenance["exposure_snapshot_id"],
        "atlas_outcome_source_id": analysis_provenance["outcome_source_id"],
        "atlas_outcome_snapshot_id": analysis_provenance["outcome_snapshot_id"],
        "atlas_outcome_lineage_id": analysis_provenance["outcome_lineage_id"],
        "full_77_weights_checksum": full_weights.checksum,
        "eligible_c2_weights_checksum": c2_weights.checksum,
        "manifest_self_hash_policy": "excluded_to_avoid_recursive_hash",
    }
    return (manifest_core,)


@app.cell
def _(
    MAIN_DISPLAY_IDS,
    audit_only_results,
    dataset_build_decision,
    manifest_core,
    primary_results,
    results_authorized,
):
    manifest = {
        **manifest_core,
        "results_authorized": results_authorized,
        "primary_adjusted_models_executed": bool(primary_results),
        "primary_adjusted_model_ids": sorted(primary_results),
        "audit_only_exploratory_model_ids": sorted(audit_only_results),
        "main_display_ids": list(MAIN_DISPLAY_IDS),
        "main_display_artifacts": dict(
            zip(
                MAIN_DISPLAY_IDS,
                (
                    ["table_1_resource_quality.csv", "table_1_resource_quality.html"],
                    ["figure_1_data_flow_coverage.png", "figure_1_submission.pdf"],
                    ["figure_2_cardiometabolic_patterns.png", "figure_2_submission.pdf"],
                    ["figure_3_copd_patterns.png", "figure_3_submission.pdf"],
                    ["table_2_geographic_resolution.csv", "table_2_geographic_resolution.html"],
                ),
                strict=True,
            )
        ),
        "dataset_build_action": dataset_build_decision.action,
        "dataset_build_reason": dataset_build_decision.reason,
    }
    return (manifest,)


@app.cell
def _(json, manifest, output_dir):
    _ = (output_dir / "notebook_run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return


@app.cell
def _(manifest, mo):
    mo.md(f"""
    ### Run complete

    The governed inventory contains **{len(manifest["output_inventory"])}** local artifacts.
    The cardiometabolic joint analysis was not run because combined-diabetes semantics remain
    unapproved. The
    COPD association analysis is the candidate adjusted estimate executed under the prespecified gates. Manuscript
    authorization remains governed separately and `results_authorized=false` remains in force.
    The JSON manuscript handoff is ready for later Word assembly after independent S7 review.
    """)
    return


if __name__ == "__main__":
    app.run()
