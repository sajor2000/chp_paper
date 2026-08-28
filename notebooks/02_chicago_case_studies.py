import marimo

# LEGACY NOTE: This notebook is retained for compatibility only. The live,
# reader-facing pipeline is notebooks/00_master_chicago_healthmap_pipeline.py.

__generated_with = "0.23.14"
app = marimo.App(width="medium")


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
    from pydantic import BaseModel, Field

    return (
        BaseModel,
        Field,
        Path,
        asdict,
        json,
        mo,
        pd,
        plt,
        sha256,
        subprocess,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.case_studies import (
        build_primary_community_frame,
        build_tract_concordance_frame,
        classify_discordance,
        load_analytic_dataset,
        summarize_concordance,
        summarize_resource_quality,
    )
    from chicagohealthmap.analysis.tract_complementarity import (
        BOOTSTRAP_SEED,
        build_tract_percentile_concordance,
        cluster_bootstrap_concordance,
        summarize_concordance_metrics,
        summarize_within_community_heterogeneity,
    )

    return (
        build_primary_community_frame,
        build_tract_concordance_frame,
        classify_discordance,
        load_analytic_dataset,
        summarize_concordance,
        summarize_resource_quality,
        BOOTSTRAP_SEED,
        build_tract_percentile_concordance,
        cluster_bootstrap_concordance,
        summarize_concordance_metrics,
        summarize_within_community_heterogeneity,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.sap_analyses import (
        assess_primary_model_readiness,
        build_adjusted_residuals,
        build_coefficient_table,
        build_model_gate_diagnostics,
        build_unadjusted_sensitivity_residuals,
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
        build_unadjusted_sensitivity_residuals,
        fit_audit_only_exploratory_models,
        fit_primary_models,
        fit_minimally_adjusted_sensitivities,
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
        permutation_moran,
    )

    return (
        build_queen_weights,
        build_rook_weights,
        build_smallest_connected_distance_weights,
        build_spatial_error_sensitivity_table,
        build_topology_summary,
        permutation_moran,
    )


@app.cell
def _():
    from chicagohealthmap.analysis.reporting import (
        build_complementarity_map_frame,
        build_manuscript_results_handoff,
        build_publication_coefficient_table,
        parse_results_authorization,
        render_coefficient_sentence,
        render_styled_html,
        save_figure_with_metadata,
    )

    return (
        build_complementarity_map_frame,
        build_manuscript_results_handoff,
        build_publication_coefficient_table,
        parse_results_authorization,
        render_coefficient_sentence,
        render_styled_html,
        save_figure_with_metadata,
    )


@app.cell
def _():
    import geopandas as gpd
    from matplotlib.patches import Patch

    return Patch, gpd


@app.cell
def _(BaseModel, Field):
    class NotebookParams(BaseModel):
        dataset_path: str = Field(
            default="outputs/frozen/chicago_case_studies_analytic.parquet",
            description="Frozen analytic dataset path inside the repository.",
        )
        output_dir: str = Field(
            default="outputs/notebooks/chicago_case_studies",
            description="Local untracked output directory inside the repository.",
        )

    return (NotebookParams,)


@app.cell
def _(NotebookParams, mo):
    controls = (
        mo.md("{dataset_path}\n{output_dir}")
        .batch(
            dataset_path=mo.ui.text(value=NotebookParams.model_fields["dataset_path"].default),
            output_dir=mo.ui.text(value=NotebookParams.model_fields["output_dir"].default),
        )
        .form()
    )
    controls
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
    dataset_path = resolve_inside(project_root, params.dataset_path)
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
        dataset_path,
        expected_model_n,
        full_checksum_expected,
        output_dir,
        permutations,
        project_root,
        results_authorized,
        governance,
        governance_path,
        seed,
    )


@app.cell
def _(mo):
    mo.md("""
    # Chicago Health Map complementarity evidence ladder

    This notebook executes one deterministic analysis against the frozen analytic data set.
    It writes editable tables, figures, diagnostics, and JSON-ready result language for
    later manuscript assembly.

    CHM/CAPriCORN supplies the EHR-diagnosed condition measures. Chicago Health Atlas
    supplies the secondary public life-expectancy outcome, and public comparator data
    contextualize the patterns without replacing the CHM measure. The manuscript gate
    remains closed: `results_authorized=false`.

    **Co-author interpretation:** read the notebook as an evidence ladder. It starts with
    cleaning and quality checks, freezes the analytic data set, describes the data, and
    then estimates the 2 case-study associations.
    """)
    return


@app.cell
def _(dataset_path, load_analytic_dataset):
    analytic = load_analytic_dataset(dataset_path)
    if analytic["disease_value_derivation"].ne("direct_first_party_export_not_interpolated").any():
        raise ValueError("disease values must remain direct and uninterpolated")
    return (analytic,)


@app.cell
def _(mo):
    mo.md("""
    ## Data cleaning

    Technical specification: The purpose is to preserve direct first-party disease values
    while constructing one row per source geography-condition-period record. The estimand is
    the observed EHR-diagnosed proportion among CAPriCORN adults; the observational unit is a
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
    ## Data quality checks

    Technical specification: The purpose is to audit capture, suppression, missingness,
    reliability availability, and qualification status before analysis. The estimand remains
    the observed source-row proportion and the unit is one source geography-condition-period
    row. No alpha/beta/gamma equation is fit; later models use y_i = alpha + beta x_i + gamma Z_i
    + error_i. The prespecified adjustment set is age 65 years or older, female sex, poverty,
    and mean 2022-2024 EHR capture. Exact denominators and units are reported; missing and
    suppressed rows are not imputed. Descriptive checks use counts, while model CIs use HC3
    with 97.5% primary and 95% component intervals. Reliability qualification is withheld
    pending the rule; sensitivity status is quality-audit only, and no causal or
    population-prevalence inference is allowed. Uncertainty/CI method is not applicable to
    capture counts; model HC3 intervals are reported only in later sections.
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
def _(resource_quality):
    table_1_full = resource_quality.copy()
    table_1_full["disease_measure_unit"] = "percentage_points"
    table_1_full["denominator_unit"] = "source_person_rows"
    community_map_contract = {
        "map_population_areas": 77,
        "map_c2_complete_areas": 76,
        "map_c2_incomplete_areas": 1,
        "map_unavailable_areas": 0,
        "qualification_withheld_areas": 77,
    }
    community_mask = table_1_full["geography_type"].eq("chicago_community_area")
    for column, value in community_map_contract.items():
        table_1_full[column] = None
        table_1_full.loc[community_mask, column] = value
    compact_columns = [
        "geography_type", "condition_id", "rows", "geographies", "years", "disease_measure_eligible_rows",
        "percentage_denominator_rows", "missing_rows", "missing_percentage_denominator_rows",
        "suppressed_rows", "suppression_percentage_denominator_rows", "reliability_available_rows",
        "reliability_available_percentage_denominator_rows",
        "reliability_qualification_status", "disease_measure_unit", "denominator_unit",
        "map_population_areas", "map_c2_complete_areas", "map_c2_incomplete_areas", "map_unavailable_areas",
        "qualification_withheld_areas",
    ]
    table_1 = table_1_full.loc[:, compact_columns].copy()
    return table_1, table_1_full


@app.cell
def _(output_dir, table_1, table_1_full):
    table_1_caption = "<h3>Table 1. Resource quality, eligibility, and source audit</h3>"
    table_1_notes = (
        "<p><strong>Notes:</strong> Eligible rows / exact source rows are reported with "
        "suppression, missingness, reliability availability, and qualification withholding "
        "kept distinct. Disease measures use percentage points. Wide QA fields are in "
        "eTable 1 (`etable_1_resource_quality.html`).</p>"
    )
    table_1_html = table_1_caption + table_1.to_html(index=False, border=0) + table_1_notes
    table_1.to_csv(output_dir / "table_1_resource_quality.csv", index=False, float_format="%.12g")
    (output_dir / "table_1_resource_quality.html").write_text(table_1_html, encoding="utf-8")
    table_1_full.to_csv(output_dir / "etable_1_resource_quality.csv", index=False, float_format="%.12g")
    (output_dir / "etable_1_resource_quality.html").write_text(
        "<h3>eTable 1. Full resource-quality QA fields</h3>" + table_1_full.to_html(index=False, border=0), encoding="utf-8"
    )
    return (table_1_html,)


@app.cell
def _(mo):
    mo.md("""
    Table 1 renders the same labeled HTML written to the deterministic artifact. It
    reports exact numerators, denominators, units, and source notes. Qualification remains
    withheld and is not presented as reliability.
    """)
    return


@app.cell
def _(mo, table_1_html):
    table_1_display = mo.Html(table_1_html)
    table_1_display
    return


@app.cell
def _(mo):
    mo.md("""
    ## Analytic data set

    Technical specification: The purpose is to freeze the complete-case analysis frame before
    fitting models. The estimand is an area-level association in y_i = alpha + beta x_i + gamma
    Z_i + error_i; the observational unit is one Chicago community area. Alpha is the centered
    intercept, beta is the life-expectancy difference per frozen-IQR CHM exposure, and gamma is
    the slope for each adjustment covariate. Z_i is age 65 years or older, female sex, poverty,
    and mean 2022-2024 EHR capture. Missing covariates or disease values exclude a row only from
    that governed model; no tract overlay or imputation is used. Readiness uses VIF, rank,
    finite HC3, sample-size, and exposure-variation diagnostics. C1 is withheld for VIF >5;
    The C1 adjusted model is withheld because its maximum VIF exceeds 5. C2 is the sole
    adjusted primary freeze candidate. C1 remains `audit_only_exploratory`; its component
    contrasts are `supported_sensitivity_not_primary` only when explicitly labeled audit.
    Uncertainty uses finite HC3 covariance and 97.5% primary/95% component CIs; sensitivity
    status is freeze-candidate primary versus audit-only C1. Inference is ecological and noncausal.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — Analytic data set:** We lock the rows that can answer each model's
    question and show why one cardiometabolic model is not allowed through the gate. C2 can be
    a freeze candidate; C1 stays in the audit drawer because the covariates overlap too much.
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
def _(mo):
    mo.md("""
    ## Descriptive statistics

    Technical specification: The purpose is to describe distributions and denominators without
    ranking neighborhoods as health winners or losers. The estimand is a descriptive mean,
    median, range, or percentile; the unit is a community area or tract summary. Alpha, beta,
    and gamma are not interpreted here, although the model equation remains y_i = alpha + beta
    x_i + gamma Z_i + error_i. The adjustment set is reported for context but not applied to
    descriptive summaries. Missing and suppressed observations remain labeled and are excluded
    only from the corresponding denominator. No CI is used to imply a causal comparison; model
    HC3 CIs are reserved for governed contrasts. Diagnostics and sensitivity outputs are
    supportive only; sensitivity status is descriptive-only, and no C1 numeric result is
    manuscript-importable. The inference boundary is noncausal area description.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — Descriptive statistics:** These summaries show the shape of the data,
    not a league table. A tract-level comparator can disagree with an EHR measure because the
    sources describe different things; that disagreement is itself an audit finding.
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
    ## Case study 1

    Technical specification: The purpose is to estimate the prespecified cardiometabolic
    community-area association. The estimand is beta_h + beta_d at one frozen IQR each in
    y_i = alpha + beta_h hypertension_i + beta_d diabetes_i + gamma Z_i + error_i; the unit is
    one area. Alpha is the centered life-expectancy intercept, beta_h and beta_d are adjusted
    exposure contrasts, and gamma denotes slopes for age 65 years or older, female sex, poverty,
    and EHR capture. C1 is withheld because maximum VIF exceeds 5; its estimate is audit-only.
    Missing or suppressed exposures define the complete-case denominator; no imputation is used.
    HC3 covariance gives 97.5% CIs for the joint candidate and 95% CIs for component sensitivities.
    Cook distance, leverage, studentized residuals, and leave-one-area-out checks are supportive;
    no post hoc exclusion or causal inference is permitted.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — Case study 1:** We ask whether places with higher recorded hypertension
    and diabetes proportions also have different area-level life expectancy. The answer is about
    neighborhoods and data sources, not about what happened to an individual patient. C1 is kept
    visible as an audit blocker, not written up as a primary result.
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
    return (
        c1_influence,
        c2_influence,
        c2_influence_summary,
    )


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
    BOOTSTRAP_SEED,
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
    return cut_point_text, governed_capture_cut_points, tract_percentile, tract_percentile_noncrossing


@app.cell
def _(
    BOOTSTRAP_SEED,
    cluster_bootstrap_concordance,
    cut_point_text,
    pd,
    summarize_concordance_metrics,
    summarize_within_community_heterogeneity,
    tract_percentile,
    tract_percentile_noncrossing,
):
    complementarity_summary = pd.concat(
        [summarize_concordance_metrics(tract_percentile).assign(noncrossing_only=False),
         summarize_concordance_metrics(tract_percentile_noncrossing).assign(noncrossing_only=True)],
        ignore_index=True, sort=False,
    )
    heterogeneity_summary = pd.concat(
        [summarize_within_community_heterogeneity(tract_percentile).assign(noncrossing_only=False),
         summarize_within_community_heterogeneity(tract_percentile_noncrossing).assign(noncrossing_only=True)],
        ignore_index=True, sort=False,
    )
    for output in (complementarity_summary, heterogeneity_summary):
        output["capture_quartile_cut_points"] = cut_point_text
        output["capture_quartile_cut_point_source"] = "governed_community_area_eligible_population"
    bootstrap = cluster_bootstrap_concordance(tract_percentile, n_replicates=250, seed=BOOTSTRAP_SEED)
    bootstrap["capture_quartile_cut_points"] = cut_point_text
    bootstrap["capture_quartile_cut_point_source"] = "governed_community_area_eligible_population"
    return bootstrap, complementarity_summary, heterogeneity_summary


@app.cell
def _(
    bootstrap,
    complementarity_summary,
    heterogeneity_summary,
    cut_point_text,
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
    bootstrap.to_csv(
        output_dir / "supplement_concordance_bootstrap.csv", index=False, float_format="%.12g"
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ### Temporal and fragility diagnostics

    Temporal diagnostics use exact paired denominators and frozen IQRs to assess annual,
    2019 baseline, leave-one-year-out, and disruption-year sensitivity. The 2022-2024
    primary period is kept distinct from 2020-2021 disruption checks. CHM exposure and
    Atlas outcome lineage remain attached to every row.
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
def _(
    analytic,
    build_adjusted_diagnostic_data,
    build_adjusted_temporal_robustness,
    build_governed_robustness_summary,
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
    adjusted_diagnostic_data.to_csv(
        output_dir / "supplement_adjusted_diagnostic_data.csv",
        index=False,
        float_format="%.12g",
    )
    return adjusted_diagnostic_data, adjusted_temporal_robustness, robustness_summary


@app.cell
def _(mo):
    mo.md("""
    ## Case study 2

    Technical specification: The purpose is to estimate the prespecified COPD association and
    test whether adjusted residuals retain geographic structure. The estimand is beta_c per
    frozen-IQR COPD proportion in y_i = alpha + beta_c COPD_i + gamma Z_i + error_i; the unit is
    one community area. Alpha is the centered intercept, beta_c is the adjusted COPD contrast,
    and gamma covers age 65 years or older, female sex, poverty, and EHR capture. C2 uses 76
    complete areas; missing or suppressed COPD values are not imputed. HC3 gives a 97.5% CI, and
    fixed-seed permutation Moran's I is a supportive diagnostic. A mandatory spatial-error
    sensitivity is run only when both prespecified Moran thresholds are met; it never replaces
    the primary estimand. C1 residuals remain audit-only and cannot enter manuscript prose.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — Case study 2:** This is the same neighborhood-level question with COPD
    as the recorded condition. The map and residual check ask whether geography changes how we
    read the pattern; they do not turn an area association into an individual or causal claim.
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
    Model-specific Moran diagnostics align the internal audit-only C1 residuals to the full
    queen weights and the adjusted primary C2 residuals to the eligible C2 queen weights.
    The C2 residual population excludes the 1 community area with incomplete COPD exposure.
    Only C2 diagnostics enter manuscript-facing artifacts; C1 remains
    `audit_only_exploratory` and internal.
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
def _(asdict, build_rook_weights, build_smallest_connected_distance_weights, build_topology_summary, c2_geometry, c2_residuals, permutation_moran, permutations, seed):
    alternative_weights = {
        "rook": build_rook_weights(c2_geometry),
        "smallest_connected_distance_band": build_smallest_connected_distance_weights(c2_geometry),
    }
    topology = build_topology_summary(alternative_weights)
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
    return alternative_weights, moran_records, topology


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
    topology,
):
    spatial_error_runs = []
    for _weights_definition2, _weights2 in sorted(alternative_weights.items()):
        _diagnostic2 = next(record for record in moran_records if record["weights_definition"] == _weights_definition2)
        gate = pd.DataFrame([{"model_id": "C2", "escalation_required": _diagnostic2["escalation_required"]}])
        spatial_error_runs.append(build_spatial_error_sensitivity_table(primary_results, gate, {"C2": _weights2}).assign(weights_definition=_weights_definition2))
    alternative_spatial_weights = topology.merge(
        pd.DataFrame.from_records(moran_records),
        on="weights_definition",
        how="left",
        suffixes=("", "_moran"),
        validate="one_to_one",
    )
    alternative_spatial_weights["topology_analysis_status"] = alternative_spatial_weights["analysis_status"]
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
    return alternative_spatial_error_contrasts


@app.cell
def _(alternative_spatial_weights, alternative_spatial_error_contrasts, output_dir):
    merged_alternative_spatial_weights = alternative_spatial_weights.merge(alternative_spatial_error_contrasts[["weights_definition", "spatial_error_status", "spatial_error_estimate", "spatial_error_standard_error", "spatial_error_ci_low", "spatial_error_ci_high", "lambda_hat", "converged", "spatial_error_weights_checksum", "model_sensitivity_status"]], on="weights_definition", how="left", validate="one_to_one")
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
def _(sensitivities):
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
        ci_label=sensitivities["confidence_level"].map({0.975: "97.5% CI", 0.95: "95% CI"}),
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
        ci_label="97.5% CI",
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
def _(pd, primary_results):
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
        ci_label=primary_rows["confidence_level"].map({0.975: "97.5% CI", 0.95: "95% CI"}),
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
    table_2 = pd.concat(
        [primary_rows, readiness_rows, sensitivity_rows], ignore_index=True, sort=False
    )
    table_2 = (
        table_2.merge(diagnostic_summary.loc[:, diagnostic_columns], on="model_key", how="left")
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
    table_2["moran_gate"] = "abs(I)>=0.10_and_p<0.05"
    return (table_2,)


@app.cell
def _():
    display_columns = [
        "row_type",
        "estimand_id",
        "readiness_status",
        "withholding_reason",
        "contrast_definition",
        "estimate",
        "estimate_unit",
        "scale_iqr",
        "ci_label",
        "ci_low",
        "ci_high",
        "n",
        "adjustment_status",
        "analysis_status",
        "model_choice",
        "moran_escalation_required",
        "spatial_error_status",
        "model_sensitivity_status",
        "influence_fragile",
    ]
    return (display_columns,)


@app.cell
def _(display_columns, output_dir, table_2):
    table_2_caption = "<h3>Table 2. Primary adjusted estimates and supported sensitivities</h3>"
    table_2_notes = (
        "<p><strong>Notes:</strong> The C1 adjusted model is withheld because its maximum VIF "
        "exceeds 5; no adjusted C1 joint, hypertension, or diabetes contrast is reported. "
        "C2 is the sole adjusted primary freeze candidate and uses a 97.5% CI. The estimate "
        "is noncausal and ecological and adjusts for age 65 years or older, female sex, "
        "poverty, and mean 2022-2024 EHR capture. The C2 alpha/beta/gamma coefficients are "
        "retained in the supplement. P values are not reported alone.</p>"
    )
    table_2_html = (
        table_2_caption + table_2[display_columns].to_html(index=False, border=0) + table_2_notes
    )
    table_2.to_csv(
        output_dir / "table_2_model_readiness_sensitivities.csv", index=False, float_format="%.12g"
    )
    (output_dir / "table_2_model_readiness_sensitivities.html").write_text(
        table_2_html, encoding="utf-8"
    )
    return (table_2_html,)


@app.cell
def _(mo):
    mo.md("""
    Table 2 reports the C1 withholding decision without C1 numeric estimates and reports C2
    as the sole adjusted primary freeze candidate. C1 remains `audit_only_exploratory` and
    outside manuscript-facing contrasts, diagnostics, and coefficient tables. No sensitivity
    estimate is relabeled as an adjusted primary estimand.
    """)
    return


@app.cell
def _(mo, table_2_html):
    table_2_display = mo.Html(table_2_html)
    table_2_display
    return


@app.cell
def _(mo):
    mo.md("""
    The manuscript handoff serializes only the governed C2 adjusted primary estimate and C2
    spatial diagnostic, with table notes, figure legends, and JAMA-style P-value text. C1 is
    withheld because its maximum VIF exceeds 5 and contributes no numeric handoff result.
    Live JAMA instruction verification is blocked by the Tavily keyless cap; the local July
    14, 2026 snapshot is used as orientation only.
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
        live_journal_verification="blocked_tavily_monthly_cap_ref_no_result_2026-07-15",
    )
    (output_dir / "manuscript_results_handoff.json").write_text(
        json.dumps(manuscript_results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    figure_legends = manuscript_results["figure_legends"]
    (output_dir / "figure_legends.json").write_text(
        json.dumps(figure_legends, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return figure_legends, manuscript_results


@app.cell
def _(coefficient_table, output_dir, render_styled_html):
    coefficient_html = render_styled_html(
        coefficient_table,
        "Supplement eTable. Full alpha, beta, and gamma coefficients",
        "The sole adjusted primary C2 exposure contrast uses frozen IQR scaling; its adjustment coefficients use 1-SD scaling. C1 is withheld because its maximum VIF exceeds 5.",
    )
    coefficient_table.to_csv(
        output_dir / "supplement_full_coefficient_table.csv", index=False, float_format="%.12g"
    )
    (output_dir / "supplement_full_coefficient_table.html").write_text(
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
    coefficient_display = mo.Html(coefficient_html)
    coefficient_display
    return


@app.cell
def _(mo):
    mo.md("""
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
    ## Tables and figures for both case studies

    Technical specification: The purpose is to display source-to-analysis flow, compact model
    status, and complementary spatial summaries without duplicating regression estimates. The
    observational units are source rows, community areas, and tracts; descriptive estimands are
    counts, percentages, ranks, and rank gaps. Alpha, beta, and gamma remain in the coefficient
    supplement, not in figures. Color scales use exact units and visible labels; missing,
    suppression, and qualification withholding are separate encodings. Table 2 reports C2's
    97.5% HC3 interval and C1's VIF blocker; figures show no C1 estimate. Legends state source
    roles, geography, period, n, and CI meaning. All displays are descriptive, noncausal, and
    subject to the false authorization gate.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    **Co-author callout — Tables and figures:** The displays are a map for the reader, not a
    second results section. Table 1 says what was available, Table 2 says what model gate was
    reached, and Figures 1-3 show how the two source lenses line up or disagree. C1 stays visibly
    withheld, and `results_authorized=false` remains on every manuscript handoff.
    """)
    return


@app.cell
def _(plt):
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 150,
            "font.size": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    png_metadata = {"Software": "ChicagoHealthMap deterministic marimo pipeline"}
    return (png_metadata,)


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
def _(geometry_frame, gpd, primary_frame):
    map_source = geometry_frame.merge(
        primary_frame[
            [
                "geography_id",
                "life_expectancy_mean_2022_2024",
                "hypertension_ehr_percent_2022_2024",
                "diabetes_ehr_percent_2022_2024",
                "copd_ehr_percent_2022_2024",
                "copd_exposure_complete",
            ]
        ],
        on="geography_id",
        how="left",
    )
    map_source["qualification_status"] = "withheld_pending_reliability_rule"
    map_source["c2_coverage_status"] = map_source["copd_exposure_complete"].map(
        {True: "complete_c2", False: "suppressed_or_incomplete_c2"}
    )
    map_source["availability_status"] = "available"
    coverage_map = gpd.GeoDataFrame(
        map_source, geometry=gpd.GeoSeries.from_wkt(map_source["geometry_wkt"]), crs="EPSG:4326"
    )
    return (coverage_map,)


@app.function
def draw_flow_panel(axis, coverage):
    source_rows = int(coverage["rows"].sum())
    suppressed_rows = int(coverage["suppressed_rows"].sum())
    eligible_rows = int(coverage["disease_measure_eligible_rows"].sum())
    stages = [
        ("Source rows", source_rows, "#2166AC"),
        ("Cleaning\n(direct values)", source_rows, "#67A9CF"),
        ("QA eligible", eligible_rows, "#1A9850"),
        ("Analytic\nC1=77 / C2=76", 153, "#762A83"),
    ]
    axis.set_xlim(-0.5, len(stages) - 0.5)
    axis.set_ylim(0, 1)
    for index, (label, count, color) in enumerate(stages):
        axis.text(index, 0.56, f"{count:,}", ha="center", va="center", fontsize=10, fontweight="bold", color="white",
                  bbox={"boxstyle": "round,pad=0.45", "facecolor": color, "edgecolor": "#333333"})
        axis.text(index, 0.22, label, ha="center", va="center", fontsize=7)
        if index < len(stages) - 1:
            axis.annotate("", xy=(index + 0.38, 0.56), xytext=(index + 0.18, 0.56),
                          arrowprops={"arrowstyle": "->", "color": "#333333", "lw": 1.2})
    axis.text(0.02, 0.95, f"Capture: {eligible_rows:,}/{source_rows:,} eligible; suppressed/missing={suppressed_rows:,}",
              transform=axis.transAxes, fontsize=6.5, va="top")
    axis.set_title("A. Source → cleaning → QA → analytic flow", fontsize=9)
    axis.set_axis_off()


@app.function
def draw_map_panel(axis, coverage, column, title, cmap):
    from matplotlib.patches import Patch

    observed = coverage.loc[coverage[column].notna()]
    missing = coverage.loc[coverage[column].isna()]
    qualification_outline = coverage.loc[
        coverage["qualification_status"].eq("withheld_pending_reliability_rule")
    ]
    suppression_or_missing = missing
    coverage.plot(ax=axis, color="#eef2f6", edgecolor="white", linewidth=0.4)
    if not observed.empty:
        observed.plot(ax=axis, column=column, cmap=cmap, edgecolor="white", linewidth=0.4,
                      legend=True, legend_kwds={"label": title, "orientation": "horizontal", "shrink": 0.75})
    if not suppression_or_missing.empty:
        suppression_or_missing.plot(ax=axis, color="#fecaca", edgecolor="#991b1b", hatch="xxx", linewidth=0.6)
    if not qualification_outline.empty:
        qualification_outline.boundary.plot(ax=axis, color="#762A83", linewidth=0.7, linestyle=(0, (2, 1)))
    axis.set_title(title)
    axis.set_axis_off()
    axis.legend(handles=[Patch(facecolor="#fecaca", edgecolor="#991b1b", hatch="xxx", label="Suppressed/missing"), Patch(facecolor="none", edgecolor="#762A83", linestyle="--", label="Qualification withheld")], frameon=False, fontsize=5.5, loc="lower left")
    axis.text(0.02, 0.02, "Hatch = suppression/missing; purple dashed outline = qualification withheld", transform=axis.transAxes, fontsize=5.5)


@app.cell
def _(coverage_map, draw_flow_panel, draw_map_panel, flow_coverage, plt):
    figure_1, axes = plt.subplots(2, 3, figsize=(11, 7), constrained_layout=True)
    draw_flow_panel(axes[0, 0], flow_coverage)
    panels = [
        ("life_expectancy_mean_2022_2024", "Atlas life expectancy (years)", "viridis"),
        ("hypertension_ehr_percent_2022_2024", "CHM hypertension (%)", "Reds"),
        ("diabetes_ehr_percent_2022_2024", "CHM diabetes (%)", "Oranges"),
        ("copd_ehr_percent_2022_2024", "CHM COPD (%)", "Purples"),
    ]
    for _map_axis, (_map_column, title, cmap) in zip(
        [axes[0, 1], axes[0, 2], axes[1, 0], axes[1, 1]], panels, strict=True
    ):
        draw_map_panel(_map_axis, coverage_map, _map_column, title, cmap)
    axes[1, 2].axis("off")
    figure_1.suptitle("Figure 1. Complementary Atlas and Chicago Health Map geographic lenses")
    return (figure_1,)


@app.cell
def _(mo):
    mo.md("""
    Figure 1 displays an actual source-to-analysis flow (panel A) followed by synchronized
    community-area maps (panels B-E) for Atlas life expectancy and CHM measures. Color scales
    are labeled in years or percentage points. Suppressed, unavailable, and
    qualification-withheld states remain distinct; all 77 areas remain
    `withheld_pending_reliability_rule`.
    """)
    return


@app.cell
def _(figure_1):
    figure_1
    return


@app.cell
def _(heterogeneity_summary, plt, primary_frame, tract_percentile):
    # rd_bu_r is the color-vision-safe diverging palette for signed rank gaps.
    figure_2, axes_2 = plt.subplots(2, 3, figsize=(11, 6), constrained_layout=True)
    for axis, condition in zip(axes_2[0, :2], ["hypertension", "diabetes"], strict=True):
        exposure = f"{condition}_ehr_percent_2022_2024"
        axis.scatter(primary_frame[exposure], primary_frame["life_expectancy_mean_2022_2024"], s=16, color="#0072B2", edgecolor="white", linewidth=0.25)
        axis.set(xlabel=f"EHR {condition} (%)", ylabel="Atlas life expectancy (years)")
    for axis, condition in zip(axes_2[1, :2], ["hypertension", "diabetes"], strict=True):
        rows = tract_percentile.loc[tract_percentile["condition_id"].eq(condition)]
        axis.scatter(rows["public_comparator_estimate"], rows["ehr_percent"], s=8, c=rows["paired_percentile_rank_gap"], cmap="RdBu_r", vmin=-1, vmax=1)
        axis.set(xlabel="Public comparator (%)", ylabel=f"EHR {condition} (%)")
        axis.text(0.03, 0.95, "color = percentile-rank gap", transform=axis.transAxes, fontsize=6, va="top")
    gap_rows = tract_percentile.loc[tract_percentile["condition_id"].isin(["hypertension", "diabetes"])]
    axes_2[1, 2].scatter(gap_rows["ehr_rank"], gap_rows["public_rank"], s=7, c=gap_rows["absolute_percentile_rank_gap"], cmap="cividis", vmin=0, vmax=1)
    axes_2[1, 2].plot([0, 1], [0, 1], color="#333333", linewidth=0.8, linestyle="--")
    axes_2[1, 2].set(xlabel="CHM percentile rank", ylabel="Public percentile rank")
    axes_2[1, 2].set_title("Rank concordance; color = absolute gap", fontsize=8)
    hetero = heterogeneity_summary.loc[heterogeneity_summary["condition_id"].isin(["hypertension", "diabetes"]) & heterogeneity_summary["noncrossing_only"].eq(False)]
    for condition, color in [("hypertension", "#0072B2"), ("diabetes", "#D55E00")]:
        rows = hetero.loc[hetero["condition_id"].eq(condition)]
        axes_2[0, 2].scatter(rows["rank_iqr"], rows["rank_range"], s=14, color=color, label=condition.title())
    axes_2[0, 2].set(xlabel="Within-area tract rank IQR", ylabel="Within-area rank range", title="Heterogeneity; n=" + str(len(hetero)))
    axes_2[0, 2].legend(frameon=False, fontsize=6)
    axes_2[0, 2].text(0.03, 0.95, "C1 withheld: maximum VIF > 5", transform=axes_2[0, 2].transAxes, color="#B2182B", fontsize=7, va="top")
    figure_2.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(-1, 1), cmap="RdBu_r"), ax=axes_2[1, :2], orientation="horizontal", fraction=0.08, pad=0.18, label="Signed percentile-rank gap (CHM − public)")
    figure_2.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(0, 1), cmap="cividis"), ax=axes_2[1, 2], orientation="vertical", fraction=0.08, pad=0.08, label="Absolute percentile-rank gap")
    figure_2.suptitle("Figure 2. Cardiometabolic community and tract comparator patterns")
    return (figure_2,)


@app.cell
def _(mo):
    mo.md("""
    Figure 2 displays cardiometabolic community outcome patterns, tract percentile-rank
    concordance, and within-area heterogeneity context. EHR and public comparator roles remain
    explicit, and the C1 withholding is visible. The panels are descriptive and do not support
    causal interpretation.
    """)
    return


@app.cell
def _(figure_2):
    figure_2
    return


@app.cell
def _(coverage_map, gpd, plt, primary_frame, tract_concordance, tract_percentile):
    figure_3, axes_3 = plt.subplots(1, 3, figsize=(11, 3.8), constrained_layout=True)
    axes_3[0].scatter(primary_frame["copd_ehr_percent_2022_2024"], primary_frame["life_expectancy_mean_2022_2024"], s=14, color="#0072B2", edgecolor="white", linewidth=0.25)
    axes_3[0].set(xlabel="EHR COPD (%)", ylabel="Atlas life expectancy (years)")
    copd_rows = tract_concordance.loc[tract_concordance["condition_id"].eq("copd")]
    axes_3[1].scatter(copd_rows["public_comparator_estimate"], copd_rows["ehr_percent_mean_2022_2024"], s=8, color="#D55E00", edgecolor="white", linewidth=0.25)
    axes_3[1].set(xlabel="Public comparator COPD (%)", ylabel="EHR COPD (%)")
    copd_gap = tract_percentile.loc[tract_percentile["condition_id"].eq("copd")]
    gap_map = copd_gap.groupby("community_area_id", as_index=False)["paired_percentile_rank_gap"].mean().rename(columns={"community_area_id": "geography_id"})
    gap_map = coverage_map[["geography_id", "geometry", "qualification_status"]].merge(gap_map, on="geography_id", how="left")
    gap_map = gpd.GeoDataFrame(gap_map, geometry="geometry", crs=coverage_map.crs)
    gap_map.plot(ax=axes_3[2], color="#eef2f6", edgecolor="white", linewidth=0.4)
    gap_map.dropna(subset=["paired_percentile_rank_gap"]).plot(ax=axes_3[2], column="paired_percentile_rank_gap", cmap="RdBu_r", vmin=-1, vmax=1, edgecolor="white", linewidth=0.4, legend=True, legend_kwds={"label": "Signed tract percentile-rank gap (CHM − public)", "orientation": "horizontal", "shrink": 0.8})
    missing_gap_map = gap_map.loc[gap_map["paired_percentile_rank_gap"].isna()]
    if not missing_gap_map.empty:
        missing_gap_map.plot(ax=axes_3[2], color="#fecaca", edgecolor="#991b1b", hatch="xxx", linewidth=0.6)
    gap_map.loc[gap_map["qualification_status"].eq("withheld_pending_reliability_rule")].boundary.plot(ax=axes_3[2], color="#762A83", linewidth=0.7, linestyle=(0, (2, 1)))
    axes_3[2].set_title("Rank-gap map; n=77 areas", fontsize=8)
    axes_3[2].set_axis_off()
    figure_3.suptitle("Figure 3. COPD community and tract comparator patterns")
    return (figure_3,)


@app.cell
def _(mo):
    mo.md("""
    Figure 3 applies the same visual structure to COPD, adding a tract percentile-rank-gap
    map with a labeled diverging RdBu_r color scale. Hatched areas are unavailable/missing;
    qualification withholding is shown by a purple dashed outline where applicable. The
    source-role boundary remains unchanged. The display is descriptive, nonprimary, and noncausal.
    """)
    return


@app.cell
def _(figure_3):
    figure_3
    return


@app.cell
def _(figure_1, figure_2, figure_3, output_dir, png_metadata):
    figure_1.savefig(
        output_dir / "figure_1_data_flow_coverage.png", bbox_inches="tight", metadata=png_metadata
    )
    figure_2.savefig(
        output_dir / "figure_2_cardiometabolic_patterns.png",
        bbox_inches="tight",
        metadata=png_metadata,
    )
    figure_3.savefig(
        output_dir / "figure_3_copd_patterns.png", bbox_inches="tight", metadata=png_metadata
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
    ### Deterministic output manifest

    The manifest binds each local artifact to the frozen input, SAP, code, topology, and
    run controls. The notebook hashes byte-complete files after deterministic writes and
    serializes sorted JSON. A second execution can detect numerical or rendering drift.
    Authorization remains false, and the manifest contains no runtime timestamp or credential.
    """)
    return


@app.cell
def _():
    output_names = ["table_1_resource_quality.csv", "table_1_resource_quality.html", "etable_1_resource_quality.csv", "etable_1_resource_quality.html", "table_2_model_readiness_sensitivities.csv", "table_2_model_readiness_sensitivities.html", "manuscript_results_handoff.json", "figure_legends.json", "supplement_full_coefficient_table.csv", "supplement_full_coefficient_table.html", "supplement_model_gate_diagnostics.csv", "figure_1_data_flow_coverage.png", "figure_2_cardiometabolic_patterns.png", "figure_3_copd_patterns.png", "supplement_temporal_models.csv", "supplement_leave_one_year_out.csv", "supplement_disruption_audit.csv", "supplement_influence_c1.csv", "supplement_influence_c2.csv", "supplement_spatial_diagnostics.csv", "supplement_spatial_error_sensitivity.csv", "supplement_robustness_summary.csv", "supplement_alternative_spatial_weights.csv", "supplement_adjusted_diagnostic_data.csv", "supplement_concordance_summary.csv", "supplement_discordance_quartile.csv", "supplement_discordance_tertile.csv", "supplement_multiplicity_inventory.csv", "supplement_tract_complementarity.csv", "supplement_within_community_heterogeneity.csv", "supplement_concordance_bootstrap.csv"]
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
def _(project_root):
    notebook_path = project_root / "notebooks/02_chicago_case_studies.py"
    analysis_source_paths = [
        project_root / "src/chicagohealthmap/analysis/case_studies.py",
        project_root / "src/chicagohealthmap/analysis/sap_analyses.py",
        project_root / "src/chicagohealthmap/analysis/robustness.py",
        project_root / "src/chicagohealthmap/analysis/spatial.py",
        project_root / "src/chicagohealthmap/analysis/reporting.py",
        project_root / "src/chicagohealthmap/analysis/tract_complementarity.py",
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
        "input_path": dataset_path.relative_to(project_root).as_posix(),
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
    audit_only_results,
    c2_weights,
    full_weights,
    permutations,
    primary_results,
    results_authorized,
    run_hashes,
    seed,
):
    manifest = {
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
        "results_authorized": results_authorized,
        "primary_adjusted_models_executed": bool(primary_results),
        "primary_adjusted_model_ids": sorted(primary_results),
        "audit_only_exploratory_model_ids": sorted(audit_only_results),
    }
    return (manifest,)


@app.cell
def _(json, manifest, output_dir):
    (output_dir / "notebook_run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return


@app.cell
def _(manifest, mo):
    mo.md(
        f"""
    ### Run complete

    The governed inventory contains **{len(manifest["output_inventory"])}** local artifacts.
    C1 remains `audit_only_exploratory` because its maximum VIF exceeds 5. C2 is the sole
    adjusted primary freeze candidate executed under the prespecified gates. Manuscript
    authorization remains governed separately and `results_authorized=false` remains in force.
    The JSON manuscript handoff is ready for later Word assembly after independent S7 review.
    """
    )
    return


if __name__ == "__main__":
    app.run()
