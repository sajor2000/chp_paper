from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
DOCS = ROOT / "docs/analysis"

GOVERNANCE_DOCS = (
    DOCS / "statistical_analysis_plan.md",
    DOCS / "sap_notebook_compliance_audit.md",
    DOCS / "chm_complementarity_s7_review.md",
    DOCS / "chm_complementarity_evidence_ledger.md",
    DOCS / "chm_complementarity_display_ledger.csv",
)

GOVERNED_OUTPUTS = (
    "table_1_resource_quality.csv",
    "table_1_resource_quality.html",
    "etable_1_resource_quality.csv",
    "etable_1_resource_quality.html",
    "table_2_model_readiness_sensitivities.csv",
    "table_2_model_readiness_sensitivities.html",
    "manuscript_results_handoff.json",
    "figure_legends.json",
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
    "supplement_robustness_summary.csv",
    "supplement_alternative_spatial_weights.csv",
    "supplement_adjusted_diagnostic_data.csv",
    "supplement_concordance_summary.csv",
    "supplement_discordance_quartile.csv",
    "supplement_discordance_tertile.csv",
    "supplement_multiplicity_inventory.csv",
    "supplement_tract_complementarity.csv",
    "supplement_within_community_heterogeneity.csv",
    "supplement_concordance_bootstrap.csv",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8").casefold()


def test_governance_documents_reconcile_current_model_authority() -> None:
    texts = {path.name: _text(path) for path in GOVERNANCE_DOCS}
    combined = "\n".join(texts.values())

    assert "ecological" in combined and "repeated-period" in combined
    assert "complementarity" in combined
    assert "direct chm ehr-diagnosed tract patterns" in combined
    assert "secondary public comparators" in combined
    assert "community-area life-expectancy summaries" in combined
    assert "predictive superiority" in combined
    assert "prevalence" in combined
    assert "causality" in combined
    assert "service need" in combined

    assert "withheld_vif_above_5" in combined
    assert "audit_only_exploratory" in combined
    assert "freeze_candidate_primary_model_unsecured" in combined
    assert "executed for audit/diagnostic purposes" in combined
    assert "results_authorized=false" in combined
    assert "adjusted models were not executed" not in combined
    assert "primary c1 result" not in combined
    assert "results authorized" not in combined


def test_governance_ledgers_bind_every_named_artifact_and_required_fields() -> None:
    evidence = _text(DOCS / "chm_complementarity_evidence_ledger.md")
    display_path = DOCS / "chm_complementarity_display_ledger.csv"
    with display_path.open(newline="", encoding="utf-8") as handle:
        display_rows = list(csv.DictReader(handle))
    display = display_path.read_text(encoding="utf-8").casefold()
    required_fields = {
        "source artifact",
        "denominator",
        "unit",
        "period",
        "uncertainty",
        "analysis status",
        "authorization",
    }
    evidence_header = next(line for line in evidence.splitlines() if line.startswith("| claim |"))
    assert required_fields <= set(evidence_header.casefold().split(" | "))
    assert {field.replace(" ", "_") for field in required_fields} <= set(display_rows[0])
    for artifact in GOVERNED_OUTPUTS:
        assert artifact.casefold() in evidence or artifact.casefold() in display
    assert all(
        term in evidence
        for term in (
            "model gate",
            "robustness",
            "alternative spatial topology",
            "tract complementarity",
            "heterogeneity",
            "bootstrap",
            "legends",
        )
    )


def test_results_manifest_preserves_false_authorization_and_journal_verification_trail() -> None:
    manifest = json.loads(
        (ROOT / "config/manuscript/results_authorization.json").read_text(encoding="utf-8")
    )
    assert manifest["results_authorized"] is False
    assert "s7" in manifest["status"].casefold()
    assert "blocker" in manifest
    assert "jama" in manifest["blocker"].casefold()
    assert "tavily" in manifest["blocker"].casefold()
    assert "checked directly" in manifest["blocker"].casefold()


def test_sap_and_s7_bind_implementation_commit_and_human_authorization() -> None:
    sap = _text(DOCS / "statistical_analysis_plan.md")
    s7 = _text(DOCS / "chm_complementarity_s7_review.md")
    assert "implementation/freeze-candidate" in sap
    assert "5a92a04" in sap
    assert "codex/chm-paper-master-redesign" in s7
    assert "5a92a04" in s7
    assert "human s7 authorization remains open" in s7
    assert "results/abstract/key points/discussion" in s7
    assert "official jama health forum instructions were checked directly" in s7
