from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.manuscript.audit import (
    ManuscriptAuditError,
    audit_manuscript_control,
    audit_text,
)


def test_audit_rejects_population_prevalence_label(contracts) -> None:
    with pytest.raises(ManuscriptAuditError, match="unqualified prevalence"):
        audit_text("COPD prevalence was highest in Area A.", contracts)


def test_audit_rejects_observational_causal_verb(contracts) -> None:
    with pytest.raises(ManuscriptAuditError, match="prohibited observational verb: drove"):
        audit_text("Higher diagnosed proportion drove lower life expectancy.", contracts)


def test_audit_accepts_approved_measure_language(contracts) -> None:
    audit_text(
        "A higher EHR-diagnosed proportion among observed CAPriCORN adults was "
        "associated with lower area life expectancy.",
        contracts,
    )


def test_reporting_matrix_declares_all_required_frameworks() -> None:
    root = Path(__file__).resolve().parents[3]
    matrix = pd.read_csv(root / "docs" / "manuscript" / "reporting_matrix.csv")

    assert set(matrix["framework"]) == {
        "JAMA Health Forum",
        "STROBE",
        "RECORD",
        "STROBE-Equity",
        "SAGER",
    }
    assert set(matrix["status"]) == {"not_assessed"}


def test_control_audit_rejects_markdown_with_protected_path(tmp_project) -> None:
    control = tmp_project.root / "outputs" / "manuscript" / "control"
    control.mkdir(parents=True)
    for filename in (
        "claim_ledger.csv",
        "number_ledger.csv",
        "ai_use_ledger.csv",
        "issue_ledger.csv",
    ):
        source = Path(__file__).resolve().parent.parent / filename
        if source.is_file():
            source.unlink()
    pd.DataFrame(
        columns=[
            "claim_id",
            "section",
            "draft_claim",
            "claim_class",
            "source_or_artifact_id",
            "exact_support_location",
            "population_geography_measure_period_match",
            "support_strength",
            "conflict_or_gap",
            "allowed_wording",
            "prohibited_inference",
            "result_status",
            "owner",
            "verified_by",
            "verified_date",
            "final_text_location",
        ]
    ).to_csv(control / "claim_ledger.csv", index=False)
    pd.DataFrame(
        columns=[
            "number_id",
            "artifact_id",
            "checksum",
            "artifact_field",
            "code_version",
            "population",
            "exclusions",
            "geography",
            "time_period",
            "measure",
            "unit",
            "denominator",
            "raw_value",
            "display_value",
            "uncertainty",
            "result_status",
            "manuscript_locations",
        ]
    ).to_csv(control / "number_ledger.csv", index=False)
    pd.DataFrame(
        columns=[
            "ai_use_id",
            "platform",
            "model",
            "manufacturer",
            "start_date",
            "end_date",
            "use",
            "affected_artifact",
            "human_verifier",
            "verified_date",
        ]
    ).to_csv(control / "ai_use_ledger.csv", index=False)
    pd.DataFrame(
        columns=[
            "issue_id",
            "severity",
            "gate",
            "description",
            "evidence",
            "owner",
            "status",
            "resolution",
        ]
    ).to_csv(control / "issue_ledger.csv", index=False)
    (control / "unsafe.md").write_text("Source: /Users/example/secret.csv\n", encoding="utf-8")

    with pytest.raises(ManuscriptAuditError, match="protected path"):
        audit_manuscript_control(tmp_project.paths)


def test_cli_audit_requires_control_flag() -> None:
    result = CliRunner().invoke(app, ["manuscript", "audit"])

    assert result.exit_code != 0
    assert "control audit requires --control" in result.output
