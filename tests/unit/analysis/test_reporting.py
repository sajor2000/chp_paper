from __future__ import annotations

import pandas as pd
import pytest

from chicagohealthmap.analysis.case_studies import CaseStudyAnalysisError
from chicagohealthmap.analysis.reporting import (
    build_editorial_display_manifest,
    build_great_table,
    build_main_display_reader_cards,
    build_main_display_reader_guide,
    build_blocked_word_handoff,
    build_manuscript_results_handoff,
    build_supplement_registry,
    figure_accessibility_passes,
    format_jama_p_value,
    parse_results_authorization,
    render_coefficient_sentence,
    render_styled_html,
)


def test_figure_accessibility_gate_fails_closed() -> None:
    accessibility = {
        "palette_simulations": {"cividis": {"grayscale": {"minimum_pairwise_rgb_distance": 0.06}}},
        "secondary_encodings_verified": {"hatching": {"passed": True}},
    }
    figures = {
        "figure.png": {
            "grayscale_renderable": True,
            "simulations": {"grayscale": {"nonblank": True, "luminance_range": 0.6}},
        }
    }
    assert figure_accessibility_passes(figures, accessibility)
    accessibility["secondary_encodings_verified"]["hatching"]["passed"] = False
    assert not figure_accessibility_passes(figures, accessibility)
    accessibility["secondary_encodings_verified"]["hatching"]["passed"] = True
    accessibility["palette_simulations"]["cividis"]["grayscale"][
        "minimum_pairwise_rgb_distance"
    ] = 0.01
    assert not figure_accessibility_passes(figures, accessibility)


def test_great_table_html_is_deterministic_accessible_and_editable() -> None:
    table = pd.DataFrame(
        {
            "section": ["Coverage", "Coverage"],
            "condition": ["Hypertension", "COPD"],
            "records": [462, 457],
            "eligible": ["462 (100.0)", None],
        }
    )

    first = build_great_table(
        table,
        title="Table 1. Chicago Health Map community-area data coverage, 2019–2024",
        subtitle="Geographic-condition-year observations",
        notes=("Counts are not unique patients.", "Suppression is not statistical censoring."),
        table_id="table_1_chm_community",
        rowname_col="condition",
        groupname_col="section",
        spanners={"Data availability": ("records", "eligible")},
    ).as_raw_html()
    second = build_great_table(
        table,
        title="Table 1. Chicago Health Map community-area data coverage, 2019–2024",
        subtitle="Geographic-condition-year observations",
        notes=("Counts are not unique patients.", "Suppression is not statistical censoring."),
        table_id="table_1_chm_community",
        rowname_col="condition",
        groupname_col="section",
        spanners={"Data availability": ("records", "eligible")},
    ).as_raw_html()

    assert first == second
    assert "table_1_chm_community" in first
    assert "Data availability" in first
    assert "Counts are not unique patients." in first
    assert "Suppression is not statistical censoring." in first
    assert "<table" in first and "<td" in first


def test_great_table_serializes_nested_provenance_cells() -> None:
    frame = pd.DataFrame(
        {"step": ["join"], "source_ids": [["acs", "chm"]], "detail": [{"key": "geography_id"}]}
    )
    html = build_great_table(frame, title="Join ledger", table_id="join_ledger").as_raw_html()
    assert '["acs", "chm"]' in html
    assert '{"key": "geography_id"}' in html


def test_render_styled_html_contains_accessible_title_units_and_notes() -> None:
    table = pd.DataFrame({"estimate": [1.25], "unit": ["years"]})

    html = render_styled_html(
        table, "Table 2. Primary estimates", "Suppressed values remain distinct."
    )

    assert "Table 2. Primary estimates" in html
    assert "gt_heading" in html
    assert "estimate" in html
    assert "Suppressed values remain distinct." in html
    assert "<table" in html


def test_parse_results_authorization_fails_closed_on_non_boolean_values() -> None:
    with pytest.raises(CaseStudyAnalysisError, match="JSON boolean"):
        parse_results_authorization(
            {
                "results_authorized": "false",
                "status": "withheld_pending_s7_independent_review",
            }
        )


def test_parse_results_authorization_requires_withheld_false_state() -> None:
    assert (
        parse_results_authorization(
            {
                "results_authorized": False,
                "status": "withheld_pending_s7_independent_review",
            }
        )
        is False
    )
    with pytest.raises(CaseStudyAnalysisError, match="must remain false"):
        parse_results_authorization({"results_authorized": True, "status": "authorized"})


def test_render_coefficient_sentence_is_unit_aware_and_noncausal() -> None:
    row = {
        "condition": "diabetes",
        "n": 77,
        "estimate": -1.25,
        "ci_low": -2.10,
        "ci_high": -0.40,
        "confidence_level": 0.975,
        "scale": "1 frozen IQR",
        "adjustment_set": "age composition, sex composition, poverty, and EHR capture",
    }

    sentence = render_coefficient_sentence(row)

    assert "associated" in sentence
    assert "1 frozen IQR" in sentence
    assert "97.5% CI" in sentence
    assert "age composition" in sentence
    assert "ecological associations" in sentence
    assert "population prevalence" not in sentence


@pytest.mark.parametrize("term", ["caused", "explained", "population prevalence"])
def test_render_coefficient_sentence_rejects_forbidden_language(term: str) -> None:
    row = {
        "condition": "diabetes",
        "n": 77,
        "estimate": -1.25,
        "ci_low": -2.10,
        "ci_high": -0.40,
        "confidence_level": 0.975,
        "scale": term,
        "adjustment_set": "age composition, sex composition, poverty, and EHR capture",
    }

    with pytest.raises(CaseStudyAnalysisError, match="prohibited"):
        render_coefficient_sentence(row)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.0004, "P < .001"), (0.0452, "P = .045"), (0.991, "P > .99")],
)
def test_format_jama_p_value_uses_no_leading_zero(value: float, expected: str) -> None:
    assert format_jama_p_value(value) == expected


def test_format_jama_p_value_rejects_invalid_values() -> None:
    with pytest.raises(CaseStudyAnalysisError, match="P value"):
        format_jama_p_value(1.2)


def test_build_manuscript_results_handoff_is_structured_and_noncausal() -> None:
    primary = pd.DataFrame(
        {
            "estimand_id": ["C1", "C2"],
            "estimate": [-1.25, -0.50],
            "ci_low": [-2.10, -1.20],
            "ci_high": [-0.40, 0.20],
            "confidence_level": [0.975, 0.975],
            "n": [77, 76],
        }
    )
    spatial = pd.DataFrame(
        {
            "model_id": ["C1", "C2"],
            "observed_i": [0.17, 0.02],
            "permutation_p_value": [0.0109, 0.80],
            "escalation_decision": ["mandatory_spatial_error_sensitivity", "no_escalation"],
        }
    )

    handoff = build_manuscript_results_handoff(
        primary,
        spatial,
        results_authorized=False,
        live_journal_verification="blocked_tavily_monthly_cap",
    )

    assert handoff["results_authorized"] is False
    assert handoff["manuscript_import_allowed"] is False
    assert handoff["manuscript_import_block_reason"] == "withheld_pending_independent_review"
    assert handoff["live_journal_verification"] == "blocked_tavily_monthly_cap"
    assert "observed CAPriCORN adults" in handoff["interpretation_boundary"]
    assert handoff["primary_result_sentences"] == []
    assert handoff["spatial_diagnostic_sentences"] == []
    assert handoff["audit_only"]["c1_result_records"] == []
    assert handoff["audit_only"]["c1_spatial_diagnostic_records"] == []
    assert handoff["audit_only"]["manuscript_import_allowed"] is False
    assert handoff["withheld_result_status"] == {
        "cardiometabolic": "not_run_combined_diabetes_semantics_unapproved",
        "copd": "withheld_pending_independent_review",
    }
    assert {
        "model_gate_findings",
        "complementarity_metrics",
        "robustness_results",
        "per_result_import_authorization",
    } <= set(handoff)
    assert handoff["per_result_import_authorization"] == {
        "C1": {
            "results_authorized": False,
            "manuscript_import_allowed": False,
            "audit_only": True,
        },
        "C2": {
            "results_authorized": False,
            "manuscript_import_allowed": False,
            "audit_only": False,
        },
    }


def test_blocked_word_handoff_has_methods_and_no_result_bearing_content() -> None:
    handoff = build_blocked_word_handoff(
        title="Geographic Resolution of Electronic Health Record–Diagnosed Condition Measures",
        methods="Methods text.",
        provenance_keys=("chm_glossary", "places_metadata"),
    )

    assert handoff["status"] == "blocked_pending_s7"
    assert handoff["results_authorized"] is False
    assert "## Methods" in handoff["markdown"]
    assert "## Abstract" in handoff["markdown"]
    assert "## Results" in handoff["markdown"]
    assert "[WITHHELD pending independent S7 review.]" in handoff["markdown"]
    assert "chm_glossary" in handoff["markdown"]
    assert "-2.10" not in handoff["markdown"]
    assert "P =" not in handoff["markdown"]
    assert "<html" in handoff["html"].lower()


def test_figure_2_legend_reflects_unavailable_diabetes_comparator() -> None:
    primary = pd.DataFrame(
        {
            "estimand_id": ["C2"],
            "estimate": [-0.50],
            "ci_low": [-1.20],
            "ci_high": [0.20],
            "confidence_level": [0.975],
            "n": [76],
        }
    )
    spatial = pd.DataFrame(
        {
            "model_id": ["C2"],
            "observed_i": [0.02],
            "permutation_p_value": [0.80],
            "escalation_decision": ["no_escalation"],
        }
    )

    handoff = build_manuscript_results_handoff(
        primary, spatial, results_authorized=True, live_journal_verification="direct"
    )

    assert "not run" in handoff["figure_legends"]["figure_2"].lower()
    assert "hypertension and COPD" in handoff["figure_legends"]["figure_2"]


def test_supplement_registry_separates_numbered_and_machine_files() -> None:
    registry = build_supplement_registry(
        {
            "eFigure 2": {
                "title": "Model diagnostics",
                "artifact": "supplement_model_diagnostics.pdf",
                "display_role": "qc_only",
            },
            "eTable 6": {
                "title": "Geographic-resolution sensitivity",
                "artifact": "supplement_aggregation_loss.csv",
                "display_role": "supplement",
            },
        },
        ["supplement_claim_evidence_audit.csv", "manifest.json"],
    )
    assert [row["id"] for row in registry["numbered_manuscript_displays"]] == [
        "eFigure 2",
        "eTable 6",
    ]
    assert registry["machine_readable_reproducibility_files"] == [
        "supplement_claim_evidence_audit.csv",
        "manifest.json",
    ]
    assert {row["display_role"] for row in registry["numbered_manuscript_displays"]} == {
        "qc_only",
        "supplement",
    }
    with pytest.raises(CaseStudyAnalysisError, match="invalid numbered"):
        build_supplement_registry(
            {
                "supplement 1": {
                    "title": "x",
                    "artifact": "x.csv",
                    "display_role": "supplement",
                }
            },
            [],
        )


def test_main_display_reader_guide_is_complete_and_model_separate() -> None:
    guide = build_main_display_reader_guide(
        {
            "table_1": {
                "question": "What CHM community-area records are available?",
                "observed_pattern": "Four conditions are represented across 77 areas.",
                "exact_value_location": "Table 1 cells and editable CSV",
                "unit_denominator": "geographic-condition-year observations",
                "uncertainty_not_run": "No inferential interval; suppression is source-defined",
                "sensitivity": "Annual coverage in eFigure 2",
                "authorization": "descriptive; results_authorized=false",
                "inference_boundary": "Not unique patients or population prevalence",
            },
            **{
                display_id: {
                    "question": "q",
                    "observed_pattern": "p",
                    "exact_value_location": "location",
                    "unit_denominator": "unit",
                    "uncertainty_not_run": "not run",
                    "sensitivity": "supplement",
                    "authorization": "closed",
                    "inference_boundary": "descriptive only",
                }
                for display_id in ("figure_1", "figure_2", "figure_3", "table_2")
            },
        },
        model_guidance=[{"analysis": "COPD association analysis", "reader_facing": True}],
    )
    assert [row["display_id"] for row in guide["main_displays"]] == [
        "table_1",
        "figure_1",
        "figure_2",
        "figure_3",
        "table_2",
    ]
    required = {
        "question",
        "observed_pattern",
        "exact_value_location",
        "unit_denominator",
        "uncertainty_not_run",
        "sensitivity",
        "authorization",
        "inference_boundary",
    }
    assert required <= set(guide["main_displays"][0])
    assert guide["model_guidance"][0]["analysis"] == "COPD association analysis"


@pytest.mark.parametrize(
    "leaked_field",
    (
        "model_readiness",
        "readiness_status",
        "adjustment_set",
        "residual_diagnostic",
        "model_ci_low",
        "model_ci_high",
    ),
)
def test_main_display_reader_guide_rejects_all_model_fields(leaked_field: str) -> None:
    cards = {
        display_id: {
            "question": "q",
            "observed_pattern": "p",
            "exact_value_location": "location",
            "unit_denominator": "unit",
            "uncertainty_not_run": "not run",
            "sensitivity": "supplement",
            "authorization": "closed",
            "inference_boundary": "descriptive only",
        }
        for display_id in ("table_1", "figure_1", "figure_2", "figure_3", "table_2")
    }
    cards["figure_2"][leaked_field] = "leak"

    with pytest.raises(CaseStudyAnalysisError, match="cannot contain model fields"):
        build_main_display_reader_guide(cards)


def test_main_display_reader_cards_use_governed_frames() -> None:
    resource = pd.DataFrame(
        {
            "Condition": ["COPD", "Diabetes"],
            "Condition-year records, No.": [462, 462],
            "Community areas represented, No.": [77, 77],
        }
    )
    evidence = pd.DataFrame(
        {
            "condition_id": ["hypertension", "diabetes", "copd"],
            "quartile_disagree_pct": [35.0, 38.7, 49.0],
            "q4_movers_n": [100, 110, 125],
        }
    )
    consequences = pd.DataFrame(
        {
            "comparison_geography_type": ["chicago_community_area"],
            "moves_into_highest_quartile": [85],
            "moves_out_of_highest_quartile": [40],
            "mixed_coarser_areas": [12],
        }
    )

    cards = build_main_display_reader_cards(resource, evidence, consequences, False)

    assert cards["table_1"]["observed_pattern"] == (
        "The audit display reports four direct condition streams across Chicago community areas."
    )
    assert "direct cross-frame classification differences" in cards["figure_2"]["observed_pattern"]
    assert "Q4 transitions" in cards["figure_3"]["observed_pattern"]
    assert cards["table_2"]["authorization"] == "Descriptive; results_authorized=false"


def test_editorial_manifest_maps_roles_and_blocks_unauthorized_citation() -> None:
    manifest = build_editorial_display_manifest(
        {
            "eFigure 1": {
                "title": "Coverage",
                "artifact": "coverage.pdf",
                "display_role": "manuscript_candidate",
            },
            "eFigure 7": {
                "title": "Coefficient forest",
                "artifact": "coef.pdf",
                "display_role": "manuscript_candidate",
            },
            "eFigure 8": {"title": "QC", "artifact": "qc.pdf", "display_role": "qc_only"},
        },
        results_authorized=False,
    )
    rows = {row["id"]: row for row in manifest}
    assert rows["eFigure 1"]["editorial_placement"] == "submitted"
    assert rows["eFigure 1"]["citable_status"] == "not_citable_pending_authorization"
    assert rows["eFigure 1"]["rationale"] == "Designated manuscript supplement"
    assert rows["eFigure 1"]["authorization_requirement"] == "results_authorized=true"
    assert rows["eFigure 7"]["citable_status"] == "not_citable_pending_authorization"
    assert rows["eFigure 8"]["editorial_placement"] == "qc_only"
    assert rows["eFigure 7"]["duplicate_main_evidence"] is False
    assert [row["id"] for row in manifest] == ["eFigure 1", "eFigure 7", "eFigure 8"]


def test_c1_is_audit_only_even_if_authorization_argument_is_true() -> None:
    primary = pd.DataFrame(
        {
            "estimand_id": ["C1", "C2"],
            "estimate": [-1.25, -0.50],
            "ci_low": [-2.10, -1.20],
            "ci_high": [-0.40, 0.20],
            "confidence_level": [0.975, 0.975],
            "n": [77, 76],
        }
    )
    spatial = pd.DataFrame(
        {
            "model_id": ["C1", "C2"],
            "observed_i": [0.17, 0.02],
            "permutation_p_value": [0.0109, 0.80],
            "escalation_decision": ["mandatory_spatial_error_sensitivity", "no_escalation"],
        }
    )
    handoff = build_manuscript_results_handoff(
        primary, spatial, results_authorized=True, live_journal_verification="test"
    )
    assert {row["estimand_id"] for row in handoff["primary_result_sentences"]} == {"C2"}
    assert {row["estimand_id"] for row in handoff["audit_only"]["c1_result_records"]} == {"C1"}
    assert {row["authorization_status"] for row in handoff["audit_only"]["c1_result_records"]} == {
        "withheld_audit_only"
    }
    assert {row["model_id"] for row in handoff["spatial_diagnostic_sentences"]} == {"C2"}
    figure_2_legend = handoff["figure_legends"]["figure_2"]
    assert "CHM and PLACES percentile ranks" in figure_2_legend
    assert "direct tract quartiles" in figure_2_legend
    assert "linked direct community-area CHM quartiles" in figure_2_legend
    assert "validation standard" in figure_2_legend
    assert "VIF" not in figure_2_legend
    figure_1_legend = handoff["figure_legends"]["figure_1"]
    assert "capture and reliability distributions" in figure_1_legend
    figure_3_legend = handoff["figure_legends"]["figure_3"]
    assert "highest-quartile tract transitions" in figure_3_legend
    assert "mean annual source denominators" in figure_3_legend
    assert "not unique people" in figure_3_legend
    assert "annual Q4 overlap" in figure_3_legend
    assert "adjusted estimate" not in figure_3_legend
    assert "C2" not in figure_3_legend
    assert "freeze candidate" not in figure_3_legend
    assert "primary freeze C2" not in figure_3_legend
