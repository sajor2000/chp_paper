"""Deterministic publication tables, figures, and noncausal interpretation helpers."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
import json
import math
from pathlib import Path
from typing import Any

import geopandas as gpd  # type: ignore[import-untyped]
from great_tables import GT
import pandas as pd  # type: ignore[import-untyped]

from chicagohealthmap.analysis.case_studies import CaseStudyAnalysisError

_PROHIBITED_TERMS = {
    "caused",
    "drove",
    "explained",
    "attributable",
    "preventable years",
    "impact",
    "effect",
    "would improve",
    "population prevalence",
}
_ALLOWED_WITHHELD_RESULTS_STATUSES = {
    "withheld_pending_s7_independent_review",
    "withheld_pending_independent_review",
    "withheld_pending_live_journal_verification",
}

_DISPLAY_ROLES = {"manuscript_candidate", "supplement", "qc_only"}
_EDITORIAL_PLACEMENT_MAP = {
    "eTable 1": "submitted",
    "eTable 5": "submitted",
    "eTable 6": "submitted",
    "eTable 8": "submitted",
    "eTable 9": "submitted",
    "eFigure 1": "submitted",
    "eFigure 2": "submitted",
    "eFigure 5": "submitted",
    "eFigure 11": "submitted",
    "eFigure 12": "submitted",
    "eFigure 3": "reserve",
    "eFigure 4": "reserve",
    "eTable 4": "not_citable_pending_authorization",
    "eFigure 7": "not_citable_pending_authorization",
    "eFigure 9": "not_citable_pending_authorization",
    "eFigure 10": "not_citable_pending_authorization",
    "eTable 2": "qc_only",
    "eTable 3": "qc_only",
    "eTable 7": "qc_only",
    "eFigure 6": "qc_only",
    "eFigure 8": "qc_only",
}


def figure_accessibility_passes(
    figures: Mapping[str, Mapping[str, Any]], accessibility: Mapping[str, Any]
) -> bool:
    """Fail closed unless rendered, palette, and secondary-encoding checks all pass."""

    render_checks = [
        bool(details.get("grayscale_renderable"))
        and all(
            bool(metric.get("nonblank")) and float(metric.get("luminance_range", 0)) > 0.5
            for metric in details.get("simulations", {}).values()
        )
        and bool(details.get("simulations"))
        for details in figures.values()
    ]
    palette_checks = [
        float(metric.get("minimum_pairwise_rgb_distance", 0)) > 0.05
        for palette in accessibility.get("palette_simulations", {}).values()
        for metric in palette.values()
    ]
    encoding_checks = [
        bool(details.get("passed"))
        for details in accessibility.get("secondary_encodings_verified", {}).values()
    ]
    return bool(
        render_checks
        and palette_checks
        and encoding_checks
        and all(render_checks + palette_checks + encoding_checks)
    )


def _great_table_scalar(value: Any) -> Any:
    """Serialize provenance containers without changing ordinary scalar cells."""

    if isinstance(value, set):
        value = sorted(value)
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, sort_keys=True, default=str)
    if type(value).__module__ == "numpy" and hasattr(value, "tolist"):
        return json.dumps(value.tolist(), sort_keys=True, default=str)
    return value


def build_great_table(
    table: pd.DataFrame,
    *,
    title: str,
    table_id: str,
    subtitle: str | None = None,
    notes: tuple[str, ...] = (),
    rowname_col: str | None = None,
    groupname_col: str | None = None,
    spanners: Mapping[str, tuple[str, ...]] | None = None,
) -> GT:
    """Build deterministic, editable Great Tables output for notebook and HTML export."""

    if table.empty:
        raise CaseStudyAnalysisError("cannot render an empty publication table")
    display_table = table.copy()
    for column in display_table.select_dtypes(include=["object", "str"]).columns:
        display_table[column] = display_table[column].map(_great_table_scalar)
    result = GT(
        display_table,
        rowname_col=rowname_col,
        groupname_col=groupname_col,
        id=table_id,
    ).tab_header(title=title, subtitle=subtitle)
    for label, columns in (spanners or {}).items():
        result = result.tab_spanner(label=label, columns=list(columns))
    result = result.sub_missing(missing_text="—")
    for note in notes:
        result = result.tab_source_note(note)
    return result.tab_options(
        table_font_names=["Arial", "Helvetica", "sans-serif"],
        table_font_size="12px",
        heading_title_font_size="14px",
        heading_subtitle_font_size="11px",
        column_labels_background_color="#E8EEF5",
        column_labels_font_weight="bold",
        table_body_hlines_color="#D9E2EC",
        table_body_vlines_style="none",
        row_group_background_color="#F5F7FA",
        row_group_font_weight="bold",
        source_notes_font_size="10px",
        container_overflow_x="auto",
    )


def build_supplement_registry(
    numbered_displays: Mapping[str, Mapping[str, str]],
    reproducibility_files: list[str] | tuple[str, ...],
) -> dict[str, list[dict[str, str]] | list[str]]:
    """Separate numbered manuscript supplements from machine-readable files.

    Numbered entries are intentionally structured records so legends and
    manuscript references can be generated from one source.  Reproducibility
    files remain an ordered list and are never assigned eTable/eFigure labels.
    """

    entries: list[dict[str, str]] = []
    artifacts: set[str] = set()
    for display_id, payload in numbered_displays.items():
        if not (display_id.startswith("eTable ") or display_id.startswith("eFigure ")):
            raise CaseStudyAnalysisError(f"invalid numbered supplement id: {display_id}")
        if set(payload) != {"title", "artifact", "display_role"}:
            raise CaseStudyAnalysisError(
                f"numbered supplement {display_id} requires title, artifact, and display_role"
            )
        artifact = str(payload["artifact"])
        if not artifact or artifact in artifacts:
            raise CaseStudyAnalysisError("numbered supplement artifacts must be unique")
        artifacts.add(artifact)
        display_role = str(payload["display_role"])
        if display_role not in _DISPLAY_ROLES:
            raise CaseStudyAnalysisError(f"invalid supplement display role: {display_role}")
        entries.append(
            {
                "id": display_id,
                "title": str(payload["title"]),
                "artifact": artifact,
                "display_role": display_role,
            }
        )
    machine_files = [str(path) for path in reproducibility_files]
    if len(machine_files) != len(set(machine_files)):
        raise CaseStudyAnalysisError("reproducibility file names must be unique")
    if artifacts.intersection(machine_files):
        raise CaseStudyAnalysisError("supplement artifact cannot also be a reproducibility file")
    entries.sort(key=lambda row: (row["id"].split()[0], int(row["id"].split()[1])))
    return {
        "numbered_manuscript_displays": entries,
        "machine_readable_reproducibility_files": machine_files,
    }


_MAIN_READER_GUIDE_FIELDS = {
    "question",
    "observed_pattern",
    "exact_value_location",
    "unit_denominator",
    "uncertainty_not_run",
    "sensitivity",
    "authorization",
    "inference_boundary",
}

_MAIN_READER_MODEL_FIELDS = {
    "adjustment_set",
    "ci_high",
    "ci_low",
    "coefficient",
    "estimate",
    "model_ci_high",
    "model_ci_low",
    "model_id",
    "model_key",
    "model_readiness",
    "readiness_status",
    "residual_diagnostic",
}


def build_main_display_reader_cards(
    resource_table: pd.DataFrame,
    geographic_evidence: pd.DataFrame,
    consequence_display: pd.DataFrame,
    results_authorized: bool,
) -> dict[str, dict[str, str]]:
    """Derive reader cards from governed resource and geographic result frames."""

    if results_authorized:
        raise CaseStudyAnalysisError("main reader cards require results_authorized=false")
    authorization = "Descriptive; results_authorized=false"
    return {
        "table_1": _reader_card(
            "What CHM community-area records are available?",
            "The audit display reports four direct condition streams across Chicago community areas.",
            "Table 1 cells and editable CSV",
            "geographic-condition-year observations; not unique patients",
            "Suppression/missingness; no inferential interval",
            "Annual quality in eFigure 2",
            authorization,
            "Not population prevalence or individual risk",
        ),
        "figure_1": _reader_card(
            "Where are CHM records available and qualified?",
            "Coverage, suppression, capture, and reliability are shown.",
            "Figure 1 panels and eFigure 1 flow",
            "geography-condition-year records",
            "No inferential interval; source states retained",
            "Annual quality in eFigure 2",
            authorization,
            "Coverage is not representativeness",
        ),
        "figure_2": _reader_card(
            "How do direct tract CHM ranks align across frames?",
            "The audit display shows rank alignment and direct cross-frame classification differences.",
            "Figure 2 panels; exact metrics in Table 2",
            "eligible census tracts by condition",
            "Uncertainty-aware agreement not run if inputs are unavailable",
            "Annual/noncrossing supplement",
            authorization,
            "Alignment is not validation or superiority",
        ),
        "figure_3": _reader_card(
            "What classifications change under direct community-area linkage?",
            "The audit display shows Q4 transitions, repeated source denominators, and stability checks.",
            "Figure 3 panels and consequence CSV",
            "eligible tracts and repeated source observations",
            "Classification intervals not run",
            "Annual/noncrossing eFigures",
            authorization,
            "Direct-frame differences are not causal aggregation effects",
        ),
        "table_2": _reader_card(
            "What is the compact cross-condition evidence?",
            "The audit display contains exact cross-condition measures with metric-specific denominators.",
            "Table 2 cells and editable CSV",
            "condition-specific eligible census tracts",
            "Metric-specific uncertainty/not-run states are explicit",
            "Full diagnostics are supplementary",
            authorization,
            "No prevalence, causality, validation, or service-need claim",
        ),
    }


def _reader_card(
    question: str,
    observed_pattern: str,
    exact_value_location: str,
    unit_denominator: str,
    uncertainty_not_run: str,
    sensitivity: str,
    authorization: str,
    inference_boundary: str,
) -> dict[str, str]:
    return {
        "question": question,
        "observed_pattern": observed_pattern,
        "exact_value_location": exact_value_location,
        "unit_denominator": unit_denominator,
        "uncertainty_not_run": uncertainty_not_run,
        "sensitivity": sensitivity,
        "authorization": authorization,
        "inference_boundary": inference_boundary,
    }


def build_main_display_reader_guide(
    displays: Mapping[str, Mapping[str, Any]],
    *,
    model_guidance: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] = (),
) -> dict[str, list[dict[str, Any]]]:
    """Build a complete reader guide while keeping model guidance separate.

    Main-display cards are deliberately descriptive: model estimates and model
    gates belong in ``model_guidance`` and cannot be attached to a main card.
    """

    ordered = ("table_1", "figure_1", "figure_2", "figure_3", "table_2")
    if set(displays) != set(ordered):
        raise CaseStudyAnalysisError("reader guide must cover exactly five main displays")
    rows: list[dict[str, Any]] = []
    for display_id in ordered:
        payload = dict(displays[display_id])
        missing = sorted(_MAIN_READER_GUIDE_FIELDS - set(payload))
        if missing:
            raise CaseStudyAnalysisError(f"reader guide {display_id} is missing fields: {missing}")
        leaked = sorted(_MAIN_READER_MODEL_FIELDS & set(payload))
        if leaked:
            raise CaseStudyAnalysisError(
                f"main reader guide {display_id} cannot contain model fields: {leaked}"
            )
        rows.append({"display_id": display_id, **payload})
    return {"main_displays": rows, "model_guidance": [dict(row) for row in model_guidance]}


def build_editorial_display_manifest(
    numbered_displays: Mapping[str, Mapping[str, Any]],
    *,
    results_authorized: bool = False,
    main_display_ids: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """Assign deterministic editorial placement without changing compatibility fields."""

    main_ids = set(main_display_ids)
    rows: list[dict[str, Any]] = []
    ordered_displays = sorted(
        numbered_displays.items(), key=lambda item: (item[0].split()[0], int(item[0].split()[1]))
    )
    for order, (display_id, payload) in enumerate(ordered_displays, start=1):
        role = str(payload.get("display_role", ""))
        if role not in _DISPLAY_ROLES:
            raise CaseStudyAnalysisError(f"invalid supplement display role: {role}")
        if display_id in main_ids:
            placement, rationale = "submitted", "Primary manuscript display"
        elif display_id in _EDITORIAL_PLACEMENT_MAP:
            placement = _EDITORIAL_PLACEMENT_MAP[display_id]
            rationale = {
                "submitted": "Designated manuscript supplement",
                "reserve": "Reserve supplementary evidence",
                "not_citable_pending_authorization": "Model evidence requires results authorization",
                "qc_only": "Quality-control diagnostic",
            }[placement]
        elif role == "qc_only":
            placement, rationale = "qc_only", "Quality-control diagnostic"
        elif role == "supplement":
            placement, rationale = "reserve", "Numbered supplementary evidence"
        elif results_authorized:
            placement, rationale = "submitted", "Supplementary display available for submission"
        else:
            placement, rationale = (
                "not_citable_pending_authorization",
                "Results authorization is closed",
            )
        rows.append(
            {
                "id": display_id,
                "title": str(payload.get("title", "")),
                "artifact": str(payload.get("artifact", "")),
                "display_role": role,
                "editorial_placement": placement,
                "rationale": rationale,
                "citable_status": (
                    "citable"
                    if placement == "submitted" and results_authorized
                    else "not_citable_pending_authorization"
                    if placement == "submitted"
                    else placement
                ),
                "authorization_requirement": "results_authorized=true"
                if placement == "submitted" or placement == "not_citable_pending_authorization"
                else "none",
                "first_mention_order": order,
                "duplicate_main_evidence": bool(payload.get("duplicate_main_evidence", False)),
            }
        )
    return rows


def render_styled_html(table: pd.DataFrame, title: str, notes: str) -> str:
    """Compatibility wrapper around the deterministic Great Tables renderer."""

    table_id = "chm_" + "_".join(title.casefold().split())[:48]
    rendered = build_great_table(
        table,
        title=title,
        notes=(notes,),
        table_id=table_id,
    ).as_raw_html()
    return rendered.replace("<table", f'<table aria-label="{escape(title)}"', 1)


def parse_results_authorization(governance: Mapping[str, Any]) -> bool:
    """Parse manuscript authorization strictly and fail closed on malformed values."""

    if "results_authorized" not in governance:
        raise CaseStudyAnalysisError("governance is missing results_authorized")
    value = governance["results_authorized"]
    if not isinstance(value, bool):
        raise CaseStudyAnalysisError("results_authorized must be a JSON boolean")
    status = str(governance.get("status", ""))
    if value:
        raise CaseStudyAnalysisError("results_authorized must remain false for this notebook")
    if status not in _ALLOWED_WITHHELD_RESULTS_STATUSES:
        raise CaseStudyAnalysisError(
            f"governance status is not an allowed withheld state: {status}"
        )
    return value


def render_coefficient_sentence(row: Mapping[str, Any]) -> str:
    """Generate an exact, noncausal ecological association sentence."""

    text = " ".join(str(value).casefold() for value in row.values())
    prohibited = sorted(term for term in _PROHIBITED_TERMS if term in text)
    if prohibited:
        raise CaseStudyAnalysisError(f"prohibited statistical language: {prohibited}")
    condition = str(row.get("condition", "condition"))
    n = int(row["n"])
    estimate = float(row["estimate"])
    ci_low = float(row["ci_low"])
    ci_high = float(row["ci_high"])
    confidence = 100 * float(row["confidence_level"])
    scale = str(row["scale"])
    adjustment_set = str(row["adjustment_set"])
    return (
        f"Among {n} eligible Chicago community areas, CHM EHR-diagnosed {condition} "
        f"proportions among observed CAPriCORN adults were associated with a "
        f"{estimate:.2f}-year difference in aligned community-area life expectancy per "
        f"{scale} after adjustment for {adjustment_set} ({confidence:.1f}% CI, "
        f"{ci_low:.2f} to {ci_high:.2f}). These estimates are ecological associations "
        "and do not represent individual risk, causal claims, or population disease prevalence."
    )


def format_jama_p_value(p_value: float) -> str:
    """Format a 2-sided P value for JAMA-style manuscript text."""

    if not math.isfinite(p_value) or p_value < 0 or p_value > 1:
        raise CaseStudyAnalysisError("P value must be a finite number between 0 and 1")
    if p_value < 0.001:
        return "P < .001"
    if p_value > 0.99:
        return "P > .99"
    rounded = f"{p_value:.3f}"
    if rounded == "0.000":
        return "P < .001"
    return f"P = {rounded.removeprefix('0')}"


def build_blocked_word_handoff(
    *, title: str, methods: str, provenance_keys: tuple[str, ...]
) -> dict[str, str | bool]:
    """Create a nonnumeric, paste-ready manuscript shell while S7 is closed."""

    provenance = ", ".join(sorted(provenance_keys)) or "[SOURCE LEDGER KEYS REQUIRED]"
    markdown = "\n".join(
        (
            f"# {title}",
            "",
            "## Key Points",
            "Question: How do direct CHM tract patterns compare with public measures and linked community-area classifications?",
            "Findings: [WITHHELD pending independent S7 review.]",
            "Meaning: Direct CHM and public measures are interpreted as complementary, not interchangeable.",
            "",
            "## Abstract",
            "### Importance",
            "[AUTHOR: insert claim-linked background from the verified source ledger.]",
            "### Objective",
            "To describe geographic alignment and cross-frame classification differences in direct CHM condition measures.",
            "### Design",
            "Ecological, repeated-period analysis of Chicago geographic-condition-year records, 2019-2024.",
            "### Setting",
            "Chicago, Illinois.",
            "### Participants",
            "Geographic-condition-year records; no patient-level cohort is reported.",
            "### Exposures",
            "Direct CHM EHR-diagnosed condition proportions, with linked public comparator metadata where compatible.",
            "### Main Outcomes and Measures",
            "Rank alignment and direct tract/community-area classification differences; no causal or prevalence estimands.",
            "### Results",
            "[WITHHELD pending independent S7 review.]",
            "### Conclusions and Relevance",
            "[WITHHELD pending independent S7 review.]",
            "",
            "## Introduction",
            "[AUTHOR: insert claim-linked introduction from the verified source ledger.]",
            "",
            "## Methods",
            methods.strip(),
            "",
            "## Results",
            "[WITHHELD pending independent S7 review.]",
            "",
            "## Discussion",
            "[WITHHELD pending independent S7 review.]",
            "",
            "## Limitations",
            "[WITHHELD pending independent S7 review.]",
            "",
            "## Conclusions",
            "[WITHHELD pending independent S7 review.]",
            "",
            "## Display insertion markers",
            "[INSERT Table 1: CHM community-area coverage]",
            "[INSERT Figure 1: CHM coverage and data quality]",
            "[INSERT Figure 2: alignment and classification]",
            "[INSERT Figure 3: classification consequences and stability]",
            "[INSERT Table 2: geographic evidence]",
            "",
            f"Verified source-ledger keys: {provenance}",
            "Results authorization is closed: results_authorized=false; S7 is required before numerical results, tables, figures, or legends may be exported.",
        )
    )
    html = "<html><body><pre>" + escape(markdown) + "</pre></body></html>"
    return {
        "status": "blocked_pending_s7",
        "results_authorized": False,
        "markdown": markdown + "\n",
        "html": html + "\n",
    }


def build_manuscript_results_handoff(
    primary_contrasts: pd.DataFrame,
    spatial_diagnostics: pd.DataFrame,
    *,
    results_authorized: bool,
    live_journal_verification: str,
) -> dict[str, Any]:
    """Build structured, evidence-bound text for later Word/JSON manuscript assembly."""

    if not results_authorized:
        return {
            "results_authorized": False,
            "manuscript_import_allowed": False,
            "manuscript_import_block_reason": "withheld_pending_independent_review",
            "live_journal_verification": live_journal_verification,
            "interpretation_boundary": (
                "EHR-diagnosed proportions are measured among observed CAPriCORN adults; "
                "they are not population prevalence, individual risk, or causal effects."
            ),
            "primary_result_sentences": [],
            "spatial_diagnostic_sentences": [],
            "audit_only": {
                "c1_result_records": [],
                "c1_spatial_diagnostic_records": [],
                "manuscript_import_allowed": False,
            },
            "withheld_result_status": {
                "cardiometabolic": "not_run_combined_diabetes_semantics_unapproved",
                "copd": "withheld_pending_independent_review",
            },
            "model_gate_findings": {
                "cardiometabolic": "not_run_combined_diabetes_semantics_unapproved",
                "copd": "candidate_adjusted_estimate_not_authorized",
            },
            "complementarity_metrics": {"manuscript_import_allowed": False},
            "robustness_results": {"manuscript_import_allowed": False},
            "per_result_import_authorization": {
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
            },
            "figure_legends": {
                "figure_1": "[WITHHELD pending independent S7 review.]",
                "figure_2": "[WITHHELD pending independent S7 review.]",
                "figure_3": "[WITHHELD pending independent S7 review.]",
            },
        }

    required = {"estimand_id", "estimate", "ci_low", "ci_high", "confidence_level", "n"}
    missing = sorted(required - set(primary_contrasts.columns))
    if missing:
        raise CaseStudyAnalysisError(f"primary contrasts are missing columns: {missing}")
    adjustment_set = "age composition, sex composition, poverty, and mean 2022-2024 EHR capture"
    analysis_name = {"C1": "Cardiometabolic joint analysis", "C2": "COPD association analysis"}
    scale_by_estimand = {
        "C1": "joint 1-frozen-IQR hypertension and diabetes contrast",
        "C1-H": "1-frozen-IQR hypertension contrast conditional on diabetes",
        "C1-D": "1-frozen-IQR diabetes contrast conditional on hypertension",
        "C2": "1-frozen-IQR COPD contrast",
    }
    condition_by_estimand = {
        "C1": "hypertension and diabetes",
        "C1-H": "hypertension",
        "C1-D": "diabetes",
        "C2": "COPD",
    }
    text_rows: list[dict[str, Any]] = []
    audit_only_rows: list[dict[str, Any]] = []
    for row in primary_contrasts.sort_values("estimand_id", kind="mergesort").to_dict("records"):
        estimand_id = str(row["estimand_id"])
        sentence = render_coefficient_sentence(
            {
                "condition": condition_by_estimand.get(estimand_id, estimand_id),
                "n": row["n"],
                "estimate": row["estimate"],
                "ci_low": row["ci_low"],
                "ci_high": row["ci_high"],
                "confidence_level": row["confidence_level"],
                "scale": scale_by_estimand.get(estimand_id, "1 frozen IQR"),
                "adjustment_set": adjustment_set,
            }
        )
        result_row = {
            "estimand_id": estimand_id,
            "analysis_name": analysis_name.get(estimand_id, estimand_id),
            "source_artifact": "table_2_model_readiness_sensitivities.csv",
            "denominator": "eligible_chicago_community_areas",
            "period": "2022-2024",
            "unit": "life_expectancy_years",
            "estimate": float(row["estimate"]),
            "ci_low": float(row["ci_low"]),
            "ci_high": float(row["ci_high"]),
            "n": int(row["n"]),
            "confidence_level": float(row["confidence_level"]),
            "scale": scale_by_estimand.get(estimand_id, "1 frozen IQR"),
            "adjustment_set": adjustment_set,
            "analysis_status": str(
                row.get("analysis_status", "freeze_candidate_primary_model_unsecured")
            ),
            "sentence": sentence,
            "authorization_status": (
                "withheld_pending_independent_review"
                if not results_authorized
                else "authorized_for_manuscript_drafting"
            ),
        }
        # The authorization gate is deliberately fail-closed. The cardiometabolic analysis
        # is retained as a numeric audit record, but no sentence may enter the manuscript-importable
        # section under any authorization state because its VIF gate failed.
        if estimand_id.startswith("C1"):
            audit_only_rows.append(
                {
                    **result_row,
                    "authorization_status": "withheld_audit_only",
                    "manuscript_import_allowed": False,
                }
            )
        else:
            text_rows.append(result_row)
    if not any(str(row.get("estimand_id", "")).startswith("C1") for row in audit_only_rows):
        audit_only_rows.append(
            {
                "estimand_id": "C1",
                "source_artifact": "supplement_model_gate_diagnostics.csv",
                "analysis_status": "audit_only_exploratory",
                "withholding_reason": "maximum VIF exceeds 5",
                "manuscript_import_allowed": False,
            }
        )
    moran_rows = []
    audit_only_spatial_rows = []
    for row in spatial_diagnostics.sort_values("model_id", kind="mergesort").to_dict("records"):
        diagnostic_row = {
            "model_id": row["model_id"],
            "source_artifact": "supplement_spatial_diagnostics.csv",
            "diagnostic": "adjusted_residual_global_moran_i",
            "observed_i": float(row["observed_i"]),
            "permutation_p_value": float(row["permutation_p_value"]),
            "permutation_p_value_text": format_jama_p_value(float(row["permutation_p_value"])),
            "escalation_decision": row["escalation_decision"],
        }
        if str(row["model_id"]).startswith("C1"):
            audit_only_spatial_rows.append({**diagnostic_row, "manuscript_import_allowed": False})
        else:
            moran_rows.append(diagnostic_row)
    diagnostics_by_model = {
        str(row["model_id"]): row for row in [*moran_rows, *audit_only_spatial_rows]
    }
    for result in [*text_rows, *audit_only_rows]:
        model_id = "C1" if str(result["estimand_id"]).startswith("C1") else "C2"
        result["diagnostics"] = diagnostics_by_model.get(model_id, {"model_id": model_id})
        result["sensitivity_status"] = "supportive_sensitivity_not_primary"
        result["authorization"] = {
            "results_authorized": bool(results_authorized and model_id == "C2"),
            "manuscript_import_allowed": bool(results_authorized and model_id == "C2"),
        }
    model_gate_findings = {
        "C1": {
            "status": "not_run_combined_diabetes_semantics_unapproved",
            "reason": "mutual exclusivity and denominator equivalence are unapproved",
            "manuscript_import_allowed": False,
            "analysis_name": "Cardiometabolic joint analysis",
            "analysis_role": "diagnostic_only",
        },
        "C2": {
            "status": "ready_for_adjusted_primary_model",
            "reason": "prespecified readiness gate passed",
            "manuscript_import_allowed": bool(results_authorized),
            "analysis_name": "COPD association analysis",
            "analysis_role": "candidate_adjusted_estimate_not_authorized",
        },
    }
    figure_legends = {
        "figure_1": (
            "Figure 1. Chicago Health Map geographic coverage and data quality. Panel A shows "
            "866 Chicago-intersecting census tracts with 77 community-area boundaries. Panel B "
            "summarizes condition-year availability at both geographic levels; panel C reports "
            "suppression by condition and geography; panel D shows capture and reliability distributions. "
            "The resource spans 2019-2024; the analysis-focused period is 2022-2024. No model "
            "coefficient or confidence interval is presented in this resource display. Counts are geographic-condition-year "
            "observations, not unique patients. CHM indicates Chicago Health Map; EHR, electronic "
            "health record."
        ),
        "figure_2": (
            "Figure 2. Cross-condition tract alignment and community classification differences. "
            "Panels A and C compare CHM and PLACES percentile ranks for hypertension and COPD "
            "among condition-specific eligible tracts; the dashed line denotes equal ranks. "
            "Panel B is not run because total-diabetes phenotype and period mapping have not "
            "been approved. Panels D-F compare direct tract quartiles with linked direct community-area "
            "CHM quartiles. Cell labels are percentages of the condition-specific comparison "
            "frame; off-diagonal cells represent cross-scale classification differences. Missing "
            "and suppressed CHM values were not imputed. PLACES is a convergent external "
            "comparator, not a validation standard. CHM indicates Chicago Health Map; COPD, "
            "chronic obstructive pulmonary disease. The 2022-2024 comparison uses descriptive "
            "rank statistics; confidence intervals are reported only where compatible source "
            "uncertainty is available in the supplement."
        ),
        "figure_3": (
            "Figure 3. Direct cross-frame classification differences and stability. Panel A reports "
            "highest-quartile tract transitions under linked direct community-area CHM ranks. "
            "Panel B reports the corresponding mean annual source denominators; these repeated "
            "denominators are not unique people. Panel C maps community areas containing both "
            "Q1 and Q4 tracts, by number of conditions. Panel D reports annual Q4 overlap using "
            "the Jaccard percentage and noncrossing-tract quartile disagreement using star "
            "markers; these are different descriptive estimands on a common percentage scale. "
            "The results describe direct cross-frame differences and do not establish accuracy, "
            "prevalence, individual risk, or service need. Q indicates "
            "quartile; CHM, Chicago Health Map. The 2022-2024 stability summaries are descriptive; "
            "confidence intervals are not implied for cross-frame classifications."
        ),
    }
    per_result_import_authorization = {
        str(row["estimand_id"]): {
            "results_authorized": bool(results_authorized),
            "manuscript_import_allowed": bool(results_authorized)
            and not str(row["estimand_id"]).startswith("C1"),
            "audit_only": str(row["estimand_id"]).startswith("C1"),
        }
        for row in primary_contrasts.to_dict("records")
    }
    per_result_import_authorization.setdefault(
        "C1",
        {
            "results_authorized": bool(results_authorized),
            "manuscript_import_allowed": False,
            "audit_only": True,
        },
    )
    return {
        "results_authorized": bool(results_authorized),
        "manuscript_import_allowed": bool(results_authorized),
        "manuscript_import_block_reason": (
            "" if results_authorized else "withheld_pending_independent_review"
        ),
        "live_journal_verification": live_journal_verification,
        "interpretation_boundary": (
            "EHR-diagnosed proportions are measured among observed CAPriCORN adults; "
            "they are not population prevalence, individual risk, or causal effects."
        ),
        "adjustment_set": adjustment_set,
        "primary_result_sentences": text_rows,
        "audit_only": {
            "c1_result_records": audit_only_rows,
            "c1_spatial_diagnostic_records": audit_only_spatial_rows,
            "withholding_reason": "maximum VIF exceeds 5",
            "manuscript_import_allowed": False,
        },
        "spatial_diagnostic_sentences": moran_rows,
        "model_gate_findings": model_gate_findings,
        "complementarity_metrics": {
            "source_artifact": "supplement_concordance_summary.csv",
            "status": "descriptive_secondary_comparator",
            "manuscript_import_allowed": bool(results_authorized),
            "metric_families": [
                "percentile_rank_concordance",
                "within_area_heterogeneity",
                "discordance",
            ],
        },
        "robustness_results": {
            "source_artifacts": [
                "supplement_robustness_summary.csv",
                "supplement_spatial_diagnostics.csv",
                "supplement_spatial_error_sensitivity.csv",
            ],
            "status": "supportive_sensitivity_not_primary",
            "manuscript_import_allowed": bool(results_authorized),
        },
        "per_result_import_authorization": per_result_import_authorization,
        "table_notes": {
            "table_1": (
                "Report source rows, eligible rows, suppression, missingness, reliability "
                "availability, and qualification withholding as separate states."
            ),
            "table_2": (
                "Report condition-specific CHM-PLACES alignment, community-area partitioning, "
                "direct tract/community quartile differences, and Q4 movement. Retain metric-specific "
                "eligible denominators and do not include outcome-model estimates."
            ),
        },
        "figure_legends": figure_legends,
    }


def build_publication_coefficient_table(
    coefficients: pd.DataFrame, contrasts: pd.DataFrame
) -> pd.DataFrame:
    """Build a compact Table 2 while retaining coefficient detail in the supplement."""

    required = {"model_id", "term", "role", "estimate", "ci_low", "ci_high"}
    missing = sorted(required - set(coefficients.columns))
    if missing:
        raise CaseStudyAnalysisError(f"coefficient table is missing columns: {missing}")
    primary = contrasts[contrasts["estimand_id"].isin(["C1", "C2", "C1-H", "C1-D"])].copy()
    primary["row_type"] = "estimand"
    exposure_coefficients = coefficients[coefficients["role"] == "exposure"].copy()
    exposure_coefficients["estimand_id"] = exposure_coefficients["term"]
    exposure_coefficients["row_type"] = "exposure_coefficient"
    return pd.concat([primary, exposure_coefficients], ignore_index=True, sort=False)


def build_complementarity_map_frame(
    geometry: gpd.GeoDataFrame, primary_frame: pd.DataFrame
) -> gpd.GeoDataFrame:
    """Join Atlas outcome and CHM exposures while retaining explicit availability states."""

    required_geometry = {"geography_id", "geometry"}
    if not required_geometry.issubset(geometry.columns):
        raise CaseStudyAnalysisError("map geometry is missing geography_id or geometry")
    required_primary = {
        "geography_id",
        "life_expectancy_mean_2022_2024",
        "hypertension_ehr_percent_2022_2024",
        "diabetes_ehr_percent_2022_2024",
        "copd_ehr_percent_2022_2024",
    }
    missing = sorted(required_primary - set(primary_frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"map frame is missing primary columns: {missing}")
    if geometry["geography_id"].duplicated().any():
        raise CaseStudyAnalysisError("map geometry has duplicate geography IDs")
    output = geometry.merge(primary_frame[list(required_primary)], on="geography_id", how="left")
    output["atlas_status"] = (
        output["life_expectancy_mean_2022_2024"].notna().map({True: "observed", False: "missing"})
    )
    for condition in ("hypertension", "diabetes", "copd"):
        output[f"{condition}_status"] = (
            output[f"{condition}_ehr_percent_2022_2024"]
            .notna()
            .map({True: "observed", False: "missing_or_suppressed"})
        )
    return gpd.GeoDataFrame(output, geometry="geometry", crs=geometry.crs)


def save_figure_with_metadata(figure: Any, path: Path, metadata: Mapping[str, str]) -> None:
    """Save a figure with fixed metadata and no runtime-dependent fields."""

    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, bbox_inches="tight", metadata=dict(metadata))
