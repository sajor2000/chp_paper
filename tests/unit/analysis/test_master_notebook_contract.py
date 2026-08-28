from __future__ import annotations

import ast
from pathlib import Path


NOTEBOOK = Path(__file__).parents[3] / "notebooks" / "00_master_chicago_healthmap_pipeline.py"
PAPER_DISPLAYS = Path(__file__).parents[3] / "src/chicagohealthmap/analysis/paper_displays.py"
DESCRIPTIVE_ADDENDUM = (
    Path(__file__).parents[3]
    / "docs/analysis/descriptive_complementarity_analysis_addendum_draft.md"
)


def _source() -> str:
    return NOTEBOOK.read_text(encoding="utf-8")


def _display_source() -> str:
    return PAPER_DISPLAYS.read_text(encoding="utf-8")


def _cells() -> list[ast.FunctionDef]:
    tree = ast.parse(_source())
    return [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and any(
            isinstance(decorator, ast.Attribute) and decorator.attr == "cell"
            for decorator in node.decorator_list
        )
    ]


def _app_function_source(name: str) -> str:
    source = _source()
    tree = ast.parse(source)
    node = next(
        item
        for item in ast.walk(tree)
        if isinstance(item, ast.FunctionDef)
        and item.name == name
    )
    return ast.get_source_segment(source, node) or ""


def test_master_notebook_has_exact_paper_sequence_and_short_cells() -> None:
    source = _source()
    headings = [line.strip()[3:] for line in source.splitlines() if line.startswith("    ## ")]
    assert headings[:5] == [
        "1. Introduction",
        "2. Methods",
        "3. Results",
        "4. Discussion",
        "5. Supplementary analyses and reproducibility artifacts",
    ]
    assert len(_cells()) >= 100
    assert max(cell.end_lineno - cell.lineno + 1 for cell in _cells()) <= 40


def test_notebook_has_jama_front_matter_with_review_results_and_closed_import_gate() -> None:
    source = _source()
    required = (
        "### Provisional JAMA Health Forum Original Investigation",
        "Added Geographic Information From Tract-Level Health System Data in Chicago",
        "### Key Points",
        "**Question:**",
        "**Findings:** {review_summary",
        "**Meaning:**",
        "### Structured Abstract",
        "#### Importance",
        "#### Objective",
        "#### Design",
        "#### Setting",
        "#### Participants",
        "#### Exposures",
        "#### Main Outcomes and Measures",
        "#### Results",
        "#### Conclusions and Relevance",
        "results_authorized=false",
    )
    assert all(text in source for text in required)


def test_notebook_uses_jama_methods_results_discussion_order() -> None:
    source = _source()
    required = (
        "## 2. Methods",
        "### Study design and data sources",
        "### Study population, geography, and measures",
        "### Geographic-resolution statistical analysis",
        "#### Descriptive complementarity analyses",
        "### Ethics and reporting",
        "## 3. Results",
        "### Chicago Health Map data resource",
        "Table 1. Chicago Health Map community-area data coverage, 2019–2024",
        "Figure 1. Chicago Health Map geographic coverage and data quality",
        "### Geographic alignment and cross-scale classification",
        "Figure 2. Added geographic information from tract-level measures",
        "Figure 3. Direct cross-frame classification differences and stability",
        "Table 2. Geographic alignment and direct cross-frame classification differences by condition",
        "## 4. Discussion",
        "### Principal finding and scientific contribution",
        "### Limitations",
        "### Conclusions",
        "## 5. Supplementary analyses and reproducibility artifacts",
        "### Cardiometabolic model gate and diagnostic analyses",
        "### COPD association analysis",
    )
    cursor = source.index("## 2. Methods")
    for text in required:
        cursor = source.index(text, cursor)

    discussion = source.index("## 4. Discussion")
    assert source.index("### COPD association analysis") > discussion


def test_geographic_results_are_complete_before_discussion_and_models_follow_it() -> None:
    """The reader should finish the geographic argument before seeing model evidence."""
    source = _source()
    results = source.index("## 3. Results")
    figure_2 = source.index("Figure 2. Added geographic information from tract-level measures", results)
    figure_3 = source.index("Figure 3. Direct cross-frame classification differences", figure_2)
    table_2 = source.index("Table 2. Geographic alignment and direct cross-frame classification differences", figure_3)
    discussion = source.index("## 4. Discussion", table_2)
    supplement = source.index("## 5. Supplementary analyses", discussion)
    assert figure_2 < figure_3 < table_2 < discussion < supplement
    model_marker = source.index("fit_primary_models", results)
    assert model_marker > discussion


def test_main_display_interpretations_follow_their_rendered_outputs() -> None:
    source = _source()
    figure_2 = source.index("Figure 2. Added geographic information from tract-level measures")
    figure_3 = source.index("Figure 3. Direct cross-frame classification differences")
    table_2 = source.index("Table 2. Geographic alignment and direct cross-frame classification differences")
    for start, end in ((figure_2, figure_3), (figure_3, table_2)):
        segment = source[start:end]
        assert "Biostatistical interpretation" in segment
        assert "Coauthor interpretation" in segment
    discussion = source.index("## 4. Discussion", table_2)
    segment = source[table_2:discussion]
    assert "Biostatistical interpretation" in segment
    assert "Coauthor interpretation" in segment


def test_figure_2_results_prose_uses_governed_evidence_schema() -> None:
    source = _source()
    assert "alignment_eligible_n" not in source
    assert "geographic_main_evidence" in source
    assert "combined-component\\nsemantics not approved" in source


def test_statistician_results_are_numeric_while_manuscript_import_stays_closed() -> None:
    source = _source()
    results = source[source.index("## 3. Results") : source.index("## 5. Supplementary analyses")]
    assert "[WITHHELD" not in results
    assert 'review_summary["alignment"]' in results
    assert 'review_summary["classification"]' in results
    assert "ineligible for manuscript import while `results_authorized=false`" in results


def test_geographic_labels_do_not_overstate_literal_aggregation() -> None:
    source = _source()
    assert "Figure 3. Direct cross-frame classification differences and stability" in source
    assert "eFigure 11. Direct cross-frame classification differences" in source
    assert "literal geographic aggregation" in source


def test_result_orienter_iterates_reader_card_payloads() -> None:
    source = _source()
    assert "for card in reader_cards.values()" in source


def test_figure_1_labels_capture_as_source_published() -> None:
    source = _source()
    assert 'ylabel="Source-published capture (%)"' in source
    assert "D. Source-published capture distributions" in source


def test_reader_orienter_is_governed_and_main_displays_are_adjacent() -> None:
    source = _source()
    results = source.index("## 3. Results")
    assert source.index("How to read these results", 0, results) < results
    assert "reader_cards" in source
    table_1 = source.index("Table 1. Chicago Health Map community-area data coverage")
    figure_1 = source.index("Figure 1. Chicago Health Map geographic coverage and data quality")
    figure_2 = source.index("Figure 2. Added geographic information from tract-level measures")
    table_1_segment = source[table_1:figure_1]
    figure_1_segment = source[figure_1:figure_2]
    for segment in (table_1_segment, figure_1_segment):
        assert "Biostatistical interpretation" in segment
        assert "Coauthor interpretation" in segment
    gallery = source[source.index("### Artifact gallery") :]
    assert "editorial_curation_manifest.json" in gallery
    assert "mo.md(resource_coauthor_interpretation)" not in source


def test_jama_methods_include_required_reporting_elements() -> None:
    source = _source()
    for text in (
        "two-sided",
        "Python Software Foundation",
        "statsmodels",
        "STROBE",
        "RECORD",
        "ethics determination",
        "analysis dates",
        "not population prevalence",
    ):
        assert text in source


def test_main_table_2_is_driven_by_geographic_evidence_not_models() -> None:
    table_cell = next(
        cell for cell in _cells() if "build_geographic_main_evidence" in ast.unparse(cell)
    )
    rendered = ast.unparse(table_cell)

    assert "geographic_main_evidence" in rendered
    assert "primary_rows" not in rendered
    assert "spatial_error_summary" not in rendered


def test_main_figures_are_geographic_and_model_free() -> None:
    figure_2_cell = next(
        cell
        for cell in _cells()
        if "Figure 2. Added geographic information from tract-level measures" in ast.unparse(cell)
        and "plt.subplots" in ast.unparse(cell)
    )
    figure_3_cell = next(
        cell
        for cell in _cells()
        if "Figure 3. Direct cross-frame classification differences" in ast.unparse(cell)
        and "plt.subplots" in ast.unparse(cell)
    )
    figure_2_source = ast.unparse(figure_2_cell)
    figure_2_helper = next(
        cell for cell in _cells() if "def draw_figure_2_column" in ast.unparse(cell)
    )
    figure_2_source += ast.unparse(figure_2_helper)
    figure_3_source = ast.unparse(figure_3_cell)

    assert "tract_percentile" in figure_2_source
    assert "geographic_resolution_matrix" in figure_2_source
    assert "primary_frame" not in figure_2_source
    assert "geographic_consequence_panels" in figure_3_source
    assert "c2_prediction" not in figure_3_source
    assert "primary_results" not in figure_3_source


def test_results_prose_uses_governed_objects_and_peer_descriptive_section() -> None:
    source = _source()
    assert 'review_summary["c2"]' in source
    assert "Aggregate findings are shown for biostatistical review" in source
    results_start = source.index("## 3. Results")
    geographic = source.index(
        "### Geographic alignment and cross-scale classification", results_start
    )
    supplement = source.index("## 5. Supplementary analyses", geographic)
    model = source.index("### COPD association analysis", supplement)
    assert geographic < supplement < model


def test_notebook_builds_data_driven_coauthor_interpretation_guide() -> None:
    source = _source()
    for required in (
        "How to interpret Table 1",
        "How to interpret tract complementarity",
        "How to interpret COPD sensitivity analyses",
        "descriptive_coauthor_interpretation",
        "c2_sensitivity_interpretation",
        "coauthor_interpretation_guide.json",
    ):
        assert required in source
    assert "spatial_error_sensitivity" in source
    assert "robustness_summary" in source
    assert "Residual Moran I was" in source


def test_notebook_serializes_main_reader_guide_and_editorial_manifest() -> None:
    source = _source()
    for artifact in (
        "main_display_reader_guide.json",
        "model_interpretation_guide.json",
        "editorial_display_manifest.json",
    ):
        assert artifact in source
    assert "build_main_display_reader_guide" in source
    assert "build_main_display_reader_cards" in source
    assert "card_values =" not in source
    assert "build_editorial_display_manifest" in source
    assert "results_authorized=bool(results_authorized)" in source


def test_descriptive_addendum_does_not_supersede_governed_sap() -> None:
    addendum = DESCRIPTIVE_ADDENDUM.read_text(encoding="utf-8")
    assert "noncontrolling" in addendum
    assert "does **not** supersede CHM-SAP-001" in addendum
    assert "life-expectancy analyses and all authorization gates remain in scope" in addendum
    assert "results_authorized=false" in addendum


def test_reader_facing_tables_use_great_tables_only() -> None:
    source = _source()
    assert "build_great_table" in source
    assert "mo.ui.table" not in source
    assert ".to_html(" not in source
    assert "great_tables" in source


def test_methods_and_interpretation_state_full_inference_contract() -> None:
    source = _source()
    normalized_source = " ".join(source.split())
    for text in (
        "EHR-diagnosed proportion among observed CAPriCORN adults",
        "y_i = alpha + beta x_i + gamma Z_i + error_i",
        "HC3",
        "97.5%",
        "maximum VIF",
        "multiplicity",
        "influence",
        "spatial",
        "temporal",
        "capture",
        "weighting",
        "results_authorized=false",
            "complementarity rather than interchangeability",
    ):
        assert text in source
    assert "combined cardiometabolic model was not run" in normalized_source
    assert "candidate adjusted estimate; not authorized for manuscript import" in source


def test_statistician_review_guide_exposes_every_open_method_decision() -> None:
    source = _source()
    for required in (
        "### Statistician Review Guide",
        "Scientific question, design, and evidence hierarchy",
        "Analysis hierarchy and review status",
        "Controlling statistical decision registry for independent sign-off",
        "Restricted statistician review outputs — not for manuscript import",
        "observed-scale one-way method-of-moments estimator",
        "1000 replicates for review",
        "Normal and t critical values require an explicit sensitivity comparison",
        "Combined diabetes",
        "Mutual exclusivity, denominator equivalence",
    ):
        assert required in source


def test_every_numbered_display_has_a_biostatistical_review_annotation() -> None:
    source = _source()
    for display in (
        "Table 1", "Figure 1", "Figure 2", "Figure 3", "Table 2",
        "eTable 1", "eTable 2", "eTable 3", "eTable 4", "eTable 5",
        "eTable 6", "eTable 7", "eTable 8", "eTable 9",
        "eFigure 1", "eFigure 2", "eFigure 3", "eFigure 4", "eFigure 5",
        "eFigure 6", "eFigure 7", "eFigure 8", "eFigure 9", "eFigure 10",
        "eFigure 11", "eFigure 12",
    ):
        assert f'(\"{display}\",' in source
    assert "Biostatistical review matrix for every table and figure" in source
    assert "biostatistical_display_review.csv" in source


def test_primary_geographic_comparisons_use_the_chm_only_tract_frame() -> None:
    source = NOTEBOOK.read_text(encoding="utf-8")

    matrix_start = source.index("geographic_resolution_matrix = pd.concat")
    matrix_end = source.index("return community_rank_frame, geographic_resolution_matrix")
    matrix_source = source[matrix_start:matrix_end]
    assert "tract_chm_direct," in matrix_source
    assert "tract_chm_direct_noncrossing," in matrix_source
    assert "tract_percentile," not in matrix_source

    comparison_start = source.index("aggregation_loss = pd.concat")
    comparison_end = source.index("return (aggregation_loss,)")
    comparison_source = source[comparison_start:comparison_end]
    assert "summarize_community_area_aggregation_loss(analytic, tract_chm_direct)" in comparison_source
    assert "analytic, tract_chm_direct_noncrossing" in comparison_source
    assert "tract_percentile" not in comparison_source
    assert "Needed supplement or decision" in source


def test_statistical_methods_are_reconstructable_and_reference_linked() -> None:
    source = _source()
    for required in (
        "Eligibility, exclusions, and analytic denominators",
        "Time pooling, scale, and rank construction",
        "Rank alignment and ordinal agreement",
        "Variance partition and area-label separation",
        "Resampling and uncertainty",
        "Supplementary community-area outcome models",
        "Regression diagnostics, spatial structure, and multiplicity",
        "Missingness, sensitivities, and interpretation rules",
        "P_{gc}=100\\sum_t n_{gct}/\\sum_t d_{gct}",
        "w_{ab}=[(a-b)/3]^2",
        "Bootstrap intervals address",
        "Benjamini-\n    Hochberg",
    ):
        assert required in source


def test_notebook_has_verified_numbered_method_and_reporting_references() -> None:
    source = _source()
    for required in (
        "### References",
        "#### Statistical method references",
        "#### Reporting guidance and data-source references",
        "10.1037/h0026256",
        "10.1348/000711006X126600",
        "10.1080/00031305.2000.10474549",
        "10.1093/biomet/37.1-2.17",
        "10.1111/j.2517-6161.1995.tb02031.x",
        "10.1371/journal.pmed.0040296",
        "10.1371/journal.pmed.1001885",
        "Accessed August 27, 2026",
    ):
        assert required in source


def test_master_notebook_explains_source_streams_and_join_ledger() -> None:
    source = _source()
    for text in (
        "Statistical Analysis Module 0: governed data assembly and sample flow",
        "Source-to-analysis assembly",
        "Stepwise join ledger",
        "fact_community_area_condition_stats.text",
        "fact_tract_condition_stats.text",
        "census_acs_2024_community_area_covariates.parquet",
        "chicago_health_atlas_life_expectancy.parquet",
        "cdc_places_current_tract.parquet",
        "community_area_id",
        "geography_id, time_period",
        "disease values are never interpolated",
        "direct cross-frame classification consequences",
        "ZCTAs are Census statistical areas, not USPS ZIP Codes",
        "fact_zcta_condition_stats.text",
        "20,536",
        "18,688 tract",
        "1,848",
    ):
        assert text in source


def test_reader_facing_notebook_removes_internal_analysis_labels() -> None:
    source = _source()
    forbidden = (
        "Case Study 1:",
        "Case Study 2:",
        "freeze candidate",
        "C1 eligible; withheld",
        "C2 eligible; freeze candidate",
    )
    for text in forbidden:
        assert text not in source


def test_master_notebook_declares_manuscript_and_vector_outputs() -> None:
    source = _source()
    for required in (
        "manuscript_result_narratives.json",
        "coauthor_interpretation_guide.json",
        "supplement_table_of_contents.json",
        "etable_2_model_readiness_sensitivities.html",
        "figure_1_submission.pdf",
        "figure_2_submission.pdf",
        "figure_3_submission.pdf",
        "figure_qa.json",
        "color_vision_palette_review",
        '"grayscale", "protanopia", "deuteranopia"',
        "simulate_accessibility",
        "circle_triangle_markers_and_dot_slash_map_hatching",
        "manuscript_import_allowed",
        "results_authorized",
        "supplement_aggregation_loss.csv",
        "geographic_resolution_sensitivity",
        "direct_zcta_comparison",
        "supplement_geographic_consequence_transitions.csv",
        "supplement_geographic_consequence_stability.csv",
        "etable_8_geographic_consequences.html",
    ):
        assert required in source
    assert '"C1": {' in source and '"C2": {' in source


def test_exact_five_main_displays_and_required_panel_roles() -> None:
    source = _source()
    rendered_source = source + _display_source()
    assert "MAIN_DISPLAY_IDS = (" in source
    for display_id in (
        '"table_1"',
        '"figure_1"',
        '"figure_2"',
        '"figure_3"',
        '"table_2"',
    ):
        assert source.count(display_id) == 1
    for panel_role in (
        "Chicago tract and community-area footprint",
        "Condition-year availability",
        "Suppression by condition and geography",
        "Source-published capture distributions",
        "CHM vs PLACES ranks",
        "tract vs community quartiles",
        "Highest-quartile tract transitions",
        "Represented mean annual source denominator",
        "Mixed-extreme community areas",
        "Annual Q4 overlap and noncrossing results",
        "Noncrossing quartile difference",
    ):
        assert panel_role in rendered_source
    assert "supplement_coefficient_forest.pdf" in source
    assert "supplement_model_diagnostics.pdf" in source


def test_master_notebook_builds_and_analyzes_its_named_dataset() -> None:
    source = _source()
    assert "ensure_chicago_case_study_dataset" in source
    assert 'output_stem="00_master_analytic_dataset"' in source
    assert "rebuild: bool = Field(" in source and "default=False" in source
    assert "dataset_build_decision.artifacts.parquet_path" in source
    assert "dataset_build_decision.action" in source
    assert "00_master_analytic_dataset_data_book.html" in source
    assert "00_master_analytic_dataset_source_join_manifest.json" in source
    assert "_artifacts.data_book_html_path.read_text" not in source
    assert "source_stream_display" in source
    assert "source_join_compact" in source
    assert "descriptive_complementarity_results[_columns].copy()" in source
    assert "mo.Html(coefficient_html)" not in source
    assert source.count("mo.download(") >= 3
    assert "etable_7_path.read_bytes()" in source
    assert "coefficient_html.encode" in source
    assert "_bytes_written = etable_7_path.write_text" in source


def test_master_notebook_declares_schema_first_claim_and_display_audits() -> None:
    source = _source()
    for required in (
        "build_data_quality_audit",
        "build_claim_evidence_audit",
        "build_geographic_resolution_matrix",
        "supplement_data_quality_audit.csv",
        "supplement_claim_evidence_audit.csv",
        "supplement_geographic_resolution_matrix.csv",
        "geographic_resolution_sensitivity",
        "direct_zcta_comparison",
    ):
        assert required in source


def test_figure_redesign_uses_geographic_alignment_and_consequences() -> None:
    source = _source()
    assert "figure_2, axes_2 = plt.subplots(2, 3" in source
    assert "figure_3, axes_3 = plt.subplots(2, 2" in source
    assert "Condition-year availability" in source
    assert "Community-area boundaries; census-tract fill" in source
    assert "draw_rank_concordance" in source
    assert "draw_resolution_heatmap" in source
    assert "draw_consequence_bars" in source
    assert "draw_mixed_area_map" in source
    assert "draw_stability_panel" in source
    assert "c2_prediction" not in next(
        ast.unparse(cell)
        for cell in _cells()
        if "Figure 3. Direct cross-frame classification differences" in ast.unparse(cell)
        and "plt.subplots" in ast.unparse(cell)
    )


def test_figure_encoding_audit_has_no_stale_axis_indices() -> None:
    source = _source()
    audit = source.split("def observed_hatches", maxsplit=1)[1].split(
        "return (display_encoding_audit,)", maxsplit=1
    )[0]

    assert "figure_2.axes[" not in audit
    assert "figure_3.axes[" not in audit
    assert "quartile_matrix_annotations" in audit
    assert "transition_hatching" in audit


def test_geographic_figures_use_single_grayscale_alignment_encoding() -> None:
    rank = _app_function_source("draw_rank_concordance")
    heatmap = _app_function_source("draw_resolution_heatmap")

    assert 'color="#4D4D4D"' in rank
    assert "cividis" not in rank
    assert "set_title" not in rank
    assert 'cmap="Greys"' in heatmap


def test_availability_panel_shows_annotated_analytic_eligibility() -> None:
    source = _source()
    panel = _app_function_source("draw_availability_panel")
    assembly = source.split("figure_1_availability =", maxsplit=1)[0][-700:]
    assert '~analytic["suppression_flag"]' in assembly
    assert 'values="eligible"' in panel
    assert 'cmap="Greys_r"' in panel
    assert 'cmap="Blues"' not in panel
    assert 'cmap="cividis"' not in panel
    assert "axis.text(" in panel
    assert "analytic eligibility (%)" in panel


def test_supplement_series_has_ten_numbered_role_classified_figures() -> None:
    source = _source()
    for number in range(1, 11):
        assert f'("eFigure {number}",' in source
    assert '("eFigure 11", "Geographic consequence and ZCTA sensitivity"' in source
    assert '("eFigure 12", "FDR-controlled spatial survival"' in source
    for role in ("manuscript_candidate", "supplement", "qc_only"):
        assert role in source
    for artifact in (
        "supplement_source_assembly_flow.pdf",
        "supplement_annual_data_quality.pdf",
        "supplement_cardiometabolic_resolution.pdf",
        "supplement_cardiometabolic_agreement.pdf",
        "supplement_cardiometabolic_spatial.pdf",
        "supplement_cardiometabolic_collinearity.pdf",
        "supplement_coefficient_forest.pdf",
        "supplement_model_diagnostics.pdf",
        "supplement_model_robustness.pdf",
        "supplement_spatial_sensitivity.pdf",
        "supplement_geographic_consequences.pdf",
        "supplement_fdr_spatial_survival.pdf",
    ):
        assert artifact in source


def test_unauthorized_model_supplements_preserve_roles_but_remain_not_citable() -> None:
    source = _source()
    coefficient_spec = source.rsplit('("eFigure 7"', maxsplit=1)[1].split("\n", maxsplit=1)[0]
    assert '"manuscript_candidate"' in coefficient_spec
    assert '"eFigure 7": "not_citable_pending_authorization"' in Path(__file__).parents[3].joinpath(
        "src/chicagohealthmap/analysis/reporting.py"
    ).read_text(encoding="utf-8")


def test_supplement_index_separates_numbered_displays_from_machine_files() -> None:
    source = _source()
    assert '"numbered_manuscript_displays"' in source
    assert '"machine_readable_reproducibility_files"' in source
    assert '"eTable 6", "Geographic-resolution sensitivity"' in source
    for artifact in (
        "main_display_reader_guide.json",
        "model_interpretation_guide.json",
        "editorial_display_manifest.json",
        "editorial_curation_manifest.json",
    ):
        assert artifact in source
