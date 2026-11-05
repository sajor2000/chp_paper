from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.manuscript.audit import (
    ManuscriptAuditError,
    audit_manuscript_citations,
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


def _write_citation_audit_fixture(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, Path]:
    main = tmp_path / "main.Rmd"
    companion = tmp_path / "companion.Rmd"
    references = tmp_path / "references.csv"
    claims = tmp_path / "claims.csv"
    manifest = tmp_path / "manifest.json"
    main.write_text(
        "```{r setup}\n"
        "stopifnot(\n"
        "  isFALSE(manifest$results_authorized)\n"
        ")\n"
        "```\n"
        "First claim.<sup>1</sup> Second claim.<sup>2</sup>\n"
        "Exploratory AUC analyses are reported only in the statistician review companion, "
        "`RMD_chm_paper_r_Ashley.html`.\n"
        "# References\n"
        "1. First source. doi:10.1000/first\n"
        "2. Second source. PMID:12345.\n"
        "# Table Legends\n"
        "Table 1. Example.\n",
        encoding="utf-8",
    )
    companion.write_text(
        "```{r setup}\n"
        "stopifnot(\n"
        "  isFALSE(manifest$results_authorized)\n"
        ")\n"
        "```\n"
        "Companion AUC 0.939.<sup>1</sup>\n"
        "# Statistical Analysis Module 5: Exploratory Area-Label AUC\n"
        "# References\n"
        "1. Companion source. doi:10.1000/companion\n"
        "# Reproducibility Record\n"
        "Review record.\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "reference_number": 1,
                "stable_identifier": "10.1000/first",
                "identifier_type": "doi",
                "verification_source": "DOI metadata",
                "verification_status": "verified_test",
                "support_status": "verified_support",
                "supported_claim_or_method": "First claim",
            },
            {
                "reference_number": 2,
                "stable_identifier": "12345",
                "identifier_type": "pmid",
                "verification_source": "PubMed",
                "verification_status": "verified_test",
                "support_status": "verified_support",
                "supported_claim_or_method": "Second claim",
            },
        ]
    ).to_csv(references, index=False)
    pd.DataFrame(
        [
            {
                "claim_id": "M09",
                "manuscript_location": "Statistician review companion",
                "claim": "Area-label AUC is 0.939",
                "source_artifact": "companion.csv",
                "denominator_or_unit": "Aggregate tracts",
                "period": "2022-2024",
                "uncertainty": "Percentile interval",
                "verification_status": "verified_exact",
                "evidence_binding_id": "M09",
                "reference_numbers": "[]",
            }
        ]
    ).to_csv(claims, index=False)
    pd.DataFrame([{"condition_id": "example", "auc": 0.939}]).to_csv(
        tmp_path / "companion.csv",
        index=False,
    )
    (tmp_path / "claim_evidence_bindings.json").write_text(
        """{
  "schema_version": 1,
  "claims": {
    "M09": {
      "claim_value_tokens": ["0.939"],
      "evidence": {
        "kind": "csv",
        "path": "companion.csv",
        "rows": [
          {"where": {"condition_id": "example"}, "expect": {"auc": 0.939}}
        ]
      },
      "source_tokens": {"companion": ["Companion AUC 0.939."]},
      "rendered_tokens": {"companion": ["Companion AUC 0.939."]},
      "references": [],
      "reference_support": {}
    }
  }
}
""",
        encoding="utf-8",
    )
    manifest.write_text('{"results_authorized": false}\n', encoding="utf-8")
    return main, companion, references, claims, manifest


def test_citation_audit_accepts_ordered_references_and_companion_auc(
    tmp_path: Path,
) -> None:
    report = audit_manuscript_citations(*_write_citation_audit_fixture(tmp_path))

    assert report.references == 2
    assert report.companion_references == 1
    assert report.auc_pointers == 1


def test_citation_audit_rejects_claim_value_drift(tmp_path: Path) -> None:
    main, companion, references, claims, manifest = _write_citation_audit_fixture(tmp_path)
    claims.write_text(
        claims.read_text(encoding="utf-8").replace("AUC is 0.939", "AUC is 0.999"),
        encoding="utf-8",
    )

    with pytest.raises(ManuscriptAuditError, match="recorded values"):
        audit_manuscript_citations(main, companion, references, claims, manifest)


def test_citation_audit_rejects_claim_source_artifact_drift(tmp_path: Path) -> None:
    main, companion, references, claims, manifest = _write_citation_audit_fixture(tmp_path)
    artifact = tmp_path / "companion.csv"
    artifact.write_text(
        artifact.read_text(encoding="utf-8").replace("0.939", "0.813"),
        encoding="utf-8",
    )

    with pytest.raises(ManuscriptAuditError, match="evidence value mismatch"):
        audit_manuscript_citations(main, companion, references, claims, manifest)


def test_citation_audit_rejects_claim_reference_binding_drift(tmp_path: Path) -> None:
    main, companion, references, claims, manifest = _write_citation_audit_fixture(tmp_path)
    claims.write_text(
        claims.read_text(encoding="utf-8").replace(",M09,[]", ',M09,"[1]"'),
        encoding="utf-8",
    )

    with pytest.raises(ManuscriptAuditError, match="reference numbers"):
        audit_manuscript_citations(main, companion, references, claims, manifest)


def test_citation_audit_rejects_reference_order_drift(tmp_path: Path) -> None:
    main, companion, references, claims, manifest = _write_citation_audit_fixture(tmp_path)
    main.write_text(
        main.read_text(encoding="utf-8").replace(
            "First claim.<sup>1</sup> Second claim.<sup>2</sup>",
            "First claim.<sup>2</sup> Second claim.<sup>1</sup>",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ManuscriptAuditError, match="first appearance"):
        audit_manuscript_citations(main, companion, references, claims, manifest)


def test_citation_audit_rejects_numeric_auc_in_main(tmp_path: Path) -> None:
    main, companion, references, claims, manifest = _write_citation_audit_fixture(tmp_path)
    main.write_text(
        main.read_text(encoding="utf-8").replace(
            "Exploratory AUC analyses are reported only in the statistician review companion,",
            "Exploratory AUC 0.939 analyses are reported only in the statistician review companion,",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ManuscriptAuditError, match="exact nonnumeric"):
        audit_manuscript_citations(main, companion, references, claims, manifest)


def test_citation_audit_rejects_companion_reference_order_drift(tmp_path: Path) -> None:
    main, companion, references, claims, manifest = _write_citation_audit_fixture(tmp_path)
    companion.write_text(
        companion.read_text(encoding="utf-8")
        .replace("Companion AUC 0.939.<sup>1</sup>", "Second.<sup>2</sup> First.<sup>1</sup>")
        .replace(
            "1. Companion source. doi:10.1000/companion",
            "1. Companion source. doi:10.1000/companion\n"
            "2. Other source. doi:10.1000/other",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ManuscriptAuditError, match="statistician companion references"):
        audit_manuscript_citations(main, companion, references, claims, manifest)


def test_citation_audit_rejects_duplicate_reference_number(tmp_path: Path) -> None:
    main, companion, references, claims, manifest = _write_citation_audit_fixture(tmp_path)
    main.write_text(
        main.read_text(encoding="utf-8").replace(
            "2. Second source. PMID:12345.",
            "1. Second source. PMID:12345.",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ManuscriptAuditError, match="duplicate reference numbers"):
        audit_manuscript_citations(main, companion, references, claims, manifest)


def test_citation_audit_rejects_commented_authorization_guard(tmp_path: Path) -> None:
    main, companion, references, claims, manifest = _write_citation_audit_fixture(tmp_path)
    main.write_text(
        main.read_text(encoding="utf-8").replace(
            "  isFALSE(manifest$results_authorized)",
            "  TRUE # isFALSE(manifest$results_authorized)",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ManuscriptAuditError, match="guard must be active"):
        audit_manuscript_citations(main, companion, references, claims, manifest)


def test_citation_audit_rejects_doi_and_doi_url_duplicate(tmp_path: Path) -> None:
    main, companion, references, claims, manifest = _write_citation_audit_fixture(tmp_path)
    companion.write_text(
        companion.read_text(encoding="utf-8")
        .replace("Companion AUC 0.939.<sup>1</sup>", "First.<sup>1</sup> Second.<sup>2</sup>")
        .replace(
            "1. Companion source. doi:10.1000/companion",
            "1. Companion source. doi:10.1000/companion\n"
            "2. Duplicate source. https://doi.org/10.1000/companion",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ManuscriptAuditError, match="duplicate identifier"):
        audit_manuscript_citations(main, companion, references, claims, manifest)


def test_real_manuscript_citation_audit() -> None:
    root = Path(__file__).resolve().parents[3]

    report = audit_manuscript_citations(
        root / "manuscript" / "chicago_health_map_jama_health_forum_original_investigation.Rmd",
        root / "notebooks" / "RMD_chm_paper_r_Ashley.Rmd",
        root / "manuscript" / "reference_verification.csv",
        root / "manuscript" / "claim_evidence_map.csv",
        root / "config" / "manuscript" / "results_authorization.json",
    )

    assert report.references == 44
    assert report.companion_references == 33


def test_real_manuscript_uses_portable_equations_and_artifact_bound_flow_values() -> None:
    root = Path(__file__).resolve().parents[3]
    source = (
        root / "manuscript" / "chicago_health_map_jama_health_forum_original_investigation.Rmd"
    ).read_text(encoding="utf-8")

    assert "p_{" not in source
    assert "\\sum" not in source
    assert "MRAIA" not in source
    assert "resource_record_n <- sum(table_1$`Condition-year records, No.`)" in source
    assert "Chicago Health Map included `r resource_record_n`" in source
    assert "The community-area resource contained `r resource_record_n`" in source
    assert "The table summarizes `r resource_record_n`" in source
    assert "Chicago Health Map included 1848" not in source
    assert "The community-area resource contained 1848" not in source
    assert "The table summarizes 1848" not in source
