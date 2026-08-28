from __future__ import annotations

import pandas as pd

from chicagohealthmap.quality.ehr import (
    required_checkpoint_findings,
    validate_denominator_consistency,
    validate_domain,
    validate_numerator_denominator,
    validate_ratio,
    validate_suppressed_zero,
)
from chicagohealthmap.quality.reports import QualityFinding, QualityReport, Severity


def test_ratio_mismatch_is_fatal_at_prespecified_tolerance() -> None:
    frame = pd.DataFrame(
        {"numerator": [20, 20], "denominator": [100, 100], "ratio": [0.2 + 1e-11, 0.3]}
    )
    findings = validate_ratio(frame, "numerator", "denominator", "ratio", tolerance=1e-10)
    assert len(findings) == 1
    assert findings[0].code == "ratio_mismatch"
    assert findings[0].severity is Severity.fatal
    assert findings[0].affected_rows == (2,)


def test_numerator_greater_than_denominator_is_fatal() -> None:
    frame = pd.DataFrame({"numerator": [101], "denominator": [100]})
    finding = validate_numerator_denominator(frame, "numerator", "denominator")[0]
    assert finding.code == "numerator_gt_denominator"
    assert finding.severity is Severity.fatal


def test_domain_validation_is_generic_and_fatal() -> None:
    frame = pd.DataFrame({"year": [2022, 1900]})
    finding = validate_domain(frame, "year", {2022, 2023, 2024}, code="invalid_year_domain")[0]
    assert finding.affected_rows == (2,)
    assert finding.severity is Severity.fatal


def test_shared_denominator_inconsistency_is_fatal() -> None:
    frame = pd.DataFrame({"geography": ["a", "a"], "year": [2024, 2024], "denominator": [100, 101]})
    finding = validate_denominator_consistency(frame, ("geography", "year"), "denominator")[0]
    assert finding.code == "denominator_inconsistency"
    assert finding.severity is Severity.fatal


def test_suppressed_or_unknown_known_zero_is_fatal() -> None:
    frame = pd.DataFrame({"value": [0, 0, 1], "state": ["suppressed", "unknown", "known"]})
    finding = validate_suppressed_zero(frame, "value", "state")[0]
    assert finding.code == "suppressed_unknown_as_zero"
    assert finding.affected_rows == (1, 2)


def test_checkpoint_exposes_all_required_fatal_and_warning_codes() -> None:
    findings = required_checkpoint_findings()
    by_severity = {
        severity: {finding.code for finding in findings if finding.severity is severity}
        for severity in Severity
    }
    assert by_severity[Severity.fatal] == {
        "schema_mismatch",
        "duplicate_primary_key",
        "invalid_geography_domain",
        "invalid_year_domain",
        "invalid_condition_domain",
        "numerator_gt_denominator",
        "ratio_mismatch",
        "denominator_inconsistency",
        "suppressed_unknown_as_zero",
    }
    assert by_severity[Severity.warning] == {
        "expected_empty_file",
        "geographic_coverage_gap",
        "zero_suppressed_ambiguity",
        "subgroup_nonreconciliation",
        "low_capture",
        "demographic_misalignment",
        "age_standardization_nonreconstructable",
        "below_reliability_threshold",
    }


def test_quality_report_serializes_gate_status_and_counts() -> None:
    report = QualityReport(
        source_id="fixture",
        snapshot_id="fixture_1",
        findings=(
            QualityFinding(code="schema_mismatch", severity=Severity.fatal, message="blocked"),
            QualityFinding(code="expected_empty_file", severity=Severity.warning, message="review"),
        ),
    )
    payload = report.to_dict()
    assert report.has_fatal is True
    assert payload["gate_3_status"] == "closed"
    assert payload["finding_counts"] == {"fatal": 1, "warning": 1}
