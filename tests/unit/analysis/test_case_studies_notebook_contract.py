from __future__ import annotations

import ast
from pathlib import Path
import re


NOTEBOOK = Path(__file__).parents[3] / "notebooks" / "02_chicago_case_studies.py"

REQUIRED_OUTPUTS = {
    "table_1_resource_quality.csv",
    "table_1_resource_quality.html",
    "etable_1_resource_quality.csv",
    "etable_1_resource_quality.html",
    "table_2_model_readiness_sensitivities.csv",
    "table_2_model_readiness_sensitivities.html",
    "manuscript_results_handoff.json",
    "supplement_full_coefficient_table.csv",
    "supplement_full_coefficient_table.html",
    "supplement_model_gate_diagnostics.csv",
    "figure_1_data_flow_coverage.png",
    "figure_2_cardiometabolic_patterns.png",
    "figure_3_copd_patterns.png",
    "supplement_temporal_models.csv",
    "supplement_leave_one_year_out.csv",
    "supplement_disruption_audit.csv",
    "supplement_influence_c1.csv",
    "supplement_influence_c2.csv",
    "supplement_spatial_diagnostics.csv",
    "supplement_spatial_error_sensitivity.csv",
    "supplement_concordance_summary.csv",
    "supplement_discordance_quartile.csv",
    "supplement_discordance_tertile.csv",
    "supplement_multiplicity_inventory.csv",
    "notebook_run_manifest.json",
}


def _source() -> str:
    return NOTEBOOK.read_text()


def _cells() -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(_source())
    return [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(decorator, ast.Attribute) and decorator.attr == "cell"
            for decorator in node.decorator_list
        )
    ]


def _cell_source(cell: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    lines = _source().splitlines()
    assert cell.end_lineno is not None
    return "\n".join(lines[cell.lineno - 1 : cell.end_lineno])


def _is_explanatory_narration(cell: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    source = _cell_source(cell).casefold()
    return any(
        term in source
        for term in (
            "co-author interpretation:",
            "co-author callout",
            "withheld_pending_reliability_rule",
            "deterministic artifact",
            "ecological community-area regression",
            "sensitivity analyses",
            "temporal diagnostics",
            "residual spatial autocorrelation",
            "moran diagnostics",
            "mandatory spatial-error sensitivity",
            "table 2 renders",
            "manuscript handoff",
            "coefficient supplement",
            "secondary public comparator",
            "figures are rendered",
            "figure 1 displays",
            "figure 2 displays",
            "figure 3 applies",
            "the manifest binds",
        )
    )


def test_notebook_has_exact_governed_evidence_ladder_and_adjacent_callouts() -> None:
    source = _source()
    headings = re.findall(r"^\s{4}## (.+)$", source, flags=re.MULTILINE)
    assert headings[:7] == [
        "Data cleaning",
        "Data quality checks",
        "Analytic data set",
        "Descriptive statistics",
        "Case study 1",
        "Case study 2",
        "Tables and figures for both case studies",
    ]
    assert "## Case study one:" not in source
    assert "## Case study two:" not in source
    assert source.count("Co-author callout") >= 7
    for term in ("estimand", "observational unit", "alpha", "beta", "gamma", "adjustment set", "missing", "suppressed", "hc3", "noncausal"):
        assert term in source.casefold()


def test_notebook_declares_legend_artifact_and_false_import_governance() -> None:
    source = _source()
    assert "figure_legends.json" in source
    assert '"model_gate_findings"' in source or "model_gate_findings" in source
    assert "complementarity_metrics" in source
    assert "robustness_results" in source
    assert "per_result_import_authorization" in source
    assert 'results_authorized=false' in source
    assert "audit_only" in source
    assert "C1" in source and "withheld" in source.casefold()


def test_task4_display_contract_has_truthful_scales_and_compact_table() -> None:
    source = _source().casefold()
    for required in (
        "rank_iqr",
        "rank_range",
        "within-area heterogeneity",
        "colorbar",
        "signed percentile-rank gap",
        "rd_bu_r",
        "qualification_outline",
        "suppression_or_missing",
        "compact_columns",
        "etable_1_resource_quality.csv",
    ):
        assert required in source
    assert "hatched gray/red areas indicate missing, suppressed, or qualification-withheld" not in source


def test_notebook_declares_governed_output_inventory_and_manifest_contract() -> None:
    source = _source()
    assert REQUIRED_OUTPUTS <= {name for name in REQUIRED_OUTPUTS if name in source}
    for key in {
        "input_sha256",
        "output_sha256",
        "sap_sha256",
        "git_commit",
        "git_dirty",
        "dirty_source_binding",
        "notebook_sha256",
        "analysis_source_sha256",
        "manifest_self_hash_policy",
        "uv_lock_sha256",
        "handoff_ledger_sha256",
        "America/Chicago",
        "results_authorized",
        "manuscript_results_handoff.json",
        "full_77_weights_checksum",
        "eligible_c2_weights_checksum",
    }:
        assert key in source


def test_notebook_cells_are_short_and_explanatory_narration_is_explicit() -> None:
    cells = _cells()
    assert cells
    for cell in cells:
        assert cell.end_lineno is not None
        assert cell.end_lineno - cell.lineno + 1 <= 30


def test_each_helper_and_governed_display_has_adjacent_audit_narration() -> None:
    cells = _cells()
    helper_names = {
        "load_analytic_dataset",
        "summarize_resource_quality",
        "build_primary_community_frame",
        "assess_primary_model_readiness",
        "build_model_gate_diagnostics",
        "fit_audit_only_exploratory_models",
        "fit_minimally_adjusted_sensitivities",
        "fit_primary_models",
        "build_coefficient_table",
        "build_adjusted_residuals",
        "summarize_influence",
        "summarize_temporal_robustness",
        "build_queen_weights",
        "permutation_moran",
        "build_spatial_error_sensitivity_table",
        "build_tract_concordance_frame",
        "summarize_concordance",
        "classify_discordance",
    }
    display_names = {"table_1_display", "table_2_display", "figure_1", "figure_2", "figure_3"}
    targets: list[int] = []
    for index, cell in enumerate(cells):
        called = {
            node.func.id
            for node in ast.walk(cell)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        displayed = {
            node.value.id
            for node in cell.body
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Name)
        }
        if called & helper_names or displayed & display_names:
            targets.append(index)
    assert targets
    for index in targets:
        neighbors = [cells[item] for item in (index - 1, index + 1) if 0 <= item < len(cells)]
        assert any(_is_explanatory_narration(cell) for cell in neighbors), _cell_source(
            cells[index]
        )


def test_notebook_scientific_prose_uses_jama_style_not_a_template() -> None:
    source = _source().casefold()
    assert "purpose:" not in source
    assert "method:" not in source
    assert "rationale:" not in source
    assert "audit role:" not in source
    assert "co-author interpretation:" in source


def test_governed_tables_and_figures_have_explicit_interactive_displays() -> None:
    cells = _cells()
    displayed = {
        node.value.id
        for cell in cells
        for node in cell.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Name)
    }
    assert {"table_1_display", "table_2_display", "figure_1", "figure_2", "figure_3"} <= displayed


def test_notebook_is_a_thin_noncausal_orchestration_layer() -> None:
    source = _source()
    normalized_source = " ".join(source.casefold().split())
    for helper in (
        "summarize_resource_quality",
        "assess_primary_model_readiness",
        "fit_minimally_adjusted_sensitivities",
        "summarize_influence",
        "summarize_temporal_robustness",
        "build_queen_weights",
        "permutation_moran",
        "build_spatial_error_sensitivity_table",
        "summarize_concordance",
        "classify_discordance",
    ):
        assert f"{helper}(" in source
    assert "sm.OLS" not in source
    assert "multipletests" not in source
    assert "config/manuscript/results_authorization.json" in source
    assert "fit_primary_models(" in source
    assert "fit_audit_only_exploratory_models(" in source
    assert "build_model_gate_diagnostics(" in source
    assert "build_coefficient_table(" in source
    assert "build_adjusted_residuals(" in source
    assert "supplement_model_gate_diagnostics.csv" in source
    assert "diagnostic_results =" not in source
    assert source.index("assess_primary_model_readiness(primary_frame)") < source.index(
        "fit_primary_models(primary_frame)"
    )
    for label in (
        "supported_sensitivity_not_primary",
        "supportive_sensitivity_not_primary",
        "mandatory_spatial_sensitivity_run",
        "withheld_pending_reliability_rule",
        "Chicago Health Atlas\n    supplies the secondary public life-expectancy outcome",
        "P values alone",
        "age 65 years or older, female sex, poverty, and EHR capture",
    ):
        assert label in source
    assert (
        "live jama instruction verification is blocked by the tavily keyless cap"
        in normalized_source
    )
    for prohibited in ("gold standard", "causes", "causal effect"):
        assert prohibited not in source.casefold()


def test_notebook_prose_matches_frozen_model_gate_decision() -> None:
    normalized_source = " ".join(_source().casefold().replace("`", "").split())

    for required in (
        "c1 adjusted model is withheld because its maximum vif exceeds 5",
        "c1 remains audit_only_exploratory",
        "c2 is the sole adjusted primary freeze candidate",
    ):
        assert required in normalized_source
    for stale_claim in (
        "primary c1/c2 contrasts",
        "adjusted c1/c2 estimates remain freeze candidates",
        "adjusted c1/c2 freeze candidates were executed",
        "separate hypertension and diabetes contrasts use 95% cis",
        "the joint c1 estimate is",
    ):
        assert stale_claim not in normalized_source


def test_notebook_pins_model_populations_and_spatial_topologies() -> None:
    source = _source()
    assert '"C1": 0' in source
    assert '"C2": 76' in source
    assert "f1a9b8ade1bf4ed1258b54f97dd78a8c710dc51cc03350053c99df59b2de7922" in source
    assert "927384844fbace67e43cd79a2aa757420e026cac1a063f7b4968b784c7e417b5" in source


def test_notebook_manifest_uses_the_governed_sap_path() -> None:
    source = _source()
    assert 'project_root / "docs/analysis/statistical_analysis_plan.md"' in source


def test_figure_one_declares_exact_coverage_and_map_status_contracts() -> None:
    source = _source().casefold()
    for label in (
        "eligible rows / exact source rows",
        "withheld_pending_reliability_rule",
        "suppressed_or_incomplete_c2",
        "unavailable_or_missing",
        "qualification_withheld_areas",
    ):
        assert label in source
    assert '"map_population_areas": 77' in source
    assert '"map_c2_complete_areas": 76' in source
    assert "axis.set_axis_off()" in source
