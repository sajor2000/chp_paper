from __future__ import annotations

import pandas as pd
import pytest

from chicagohealthmap.analysis.case_studies import CaseStudyAnalysisError
from chicagohealthmap.analysis.paper_audit import (
    CLAIM_EVIDENCE_COLUMNS,
    build_claim_evidence_audit,
    build_descriptive_claim_evidence_audit,
    build_data_quality_audit,
    build_geographic_resolution_matrix,
    build_master_claim_records,
)


def _dataset() -> pd.DataFrame:
    rows = [
        ("census_tract", "17031010100", "2022", "copd", 12, False),
        ("census_tract", "17031010200", "2022", "copd", 0, True),
        ("chicago_community_area", "01", "2022", "copd", 20, False),
    ]
    frame = pd.DataFrame(
        rows,
        columns=[
            "geography_type",
            "geography_id",
            "time_period",
            "condition_id",
            "numerator",
            "suppression_flag",
        ],
    )
    frame["disease_value_derivation"] = "direct_first_party_export_not_interpolated"
    frame["public_comparator_role"] = [
        "tract_concordance_discordance_comparator",
        "tract_concordance_discordance_comparator",
        pd.NA,
    ]
    frame["public_comparator_time_period"] = [
        "2023 BRFSS / 2025 release",
        "2023 BRFSS / 2025 release",
        pd.NA,
    ]
    frame["census_covariate_time_period"] = [pd.NA, pd.NA, "2020-2024"]
    frame["life_expectancy_time_period"] = [pd.NA, pd.NA, "2022"]
    return frame


def test_data_quality_audit_is_schema_and_period_explicit() -> None:
    dataset = _dataset()
    manifest = {
        "row_count": len(dataset),
        "primary_key": ["geography_type", "geography_id", "time_period", "condition_id"],
        "results_authorized": False,
        "checksums": {"analytic.parquet": "abc"},
    }
    joins = {"joins": [{"name": "public", "validation": "many_to_one"}]}

    audit = build_data_quality_audit(
        dataset,
        manifest,
        joins,
        expected_rows=3,
        expected_columns=len(dataset.columns),
    )

    assert set(audit["status"]) == {"pass"}
    assert {
        "dataset_shape",
        "primary_key_uniqueness",
        "suppression_state",
        "source_roles",
        "source_periods",
        "join_cardinality",
        "authorization",
    } <= set(audit["check_id"])
    periods = audit.loc[audit["check_id"].eq("source_periods"), "observed"].item()
    assert "PLACES=2023 BRFSS / 2025 release" in periods
    assert "ACS=2020-2024" in periods


def test_data_quality_audit_rejects_duplicate_grain() -> None:
    dataset = pd.concat([_dataset(), _dataset().iloc[[0]]], ignore_index=True)
    manifest = {
        "row_count": len(dataset),
        "primary_key": ["geography_type", "geography_id", "time_period", "condition_id"],
        "results_authorized": False,
        "checksums": {"analytic.parquet": "abc"},
    }

    with pytest.raises(CaseStudyAnalysisError, match="primary key"):
        build_data_quality_audit(
            dataset,
            manifest,
            {"joins": []},
            expected_rows=len(dataset),
            expected_columns=len(dataset.columns),
        )


def test_data_quality_audit_rejects_empty_join_ledger() -> None:
    dataset = _dataset()
    manifest = {
        "row_count": len(dataset),
        "primary_key": ["geography_type", "geography_id", "time_period", "condition_id"],
        "results_authorized": False,
        "checksums": {"analytic.parquet": "abc"},
    }
    with pytest.raises(CaseStudyAnalysisError, match="join ledger"):
        build_data_quality_audit(
            dataset,
            manifest,
            {"joins": []},
            expected_rows=len(dataset),
            expected_columns=len(dataset.columns),
        )


def test_master_claim_records_reject_unverified_model_gate() -> None:
    readiness = pd.DataFrame(
        [{"model_id": "C1", "n_complete": 77, "status": "ready", "maximum_vif": 5.016}]
    )
    contrasts = pd.DataFrame(
        [
            {
                "model_id": "C2",
                "estimate": -2.6,
                "ci_low": -4.8,
                "ci_high": -0.4,
                "confidence_level": 0.975,
                "n": 76,
            }
        ]
    )
    resolution = pd.DataFrame(
        [
            {
                "tract_sample_n": 800,
                "results_authorized": False,
                "analysis_status": "geographic_resolution_sensitivity",
            }
        ]
    )
    with pytest.raises(CaseStudyAnalysisError, match="cardiometabolic gate"):
        build_master_claim_records(readiness, contrasts, resolution)


def test_claim_evidence_audit_requires_complete_unauthorized_records() -> None:
    record = {
        "claim_id": "C2",
        "question": "Is the area-level COPD measure associated with life expectancy?",
        "estimand": "Life-expectancy difference per frozen-IQR COPD contrast",
        "estimate": -2.60,
        "ci_low": -4.83,
        "ci_high": -0.37,
        "confidence_level": 0.975,
        "eligible_n": 76,
        "unit": "life-expectancy years",
        "grain": "Chicago community area",
        "denominator": "76 eligible community areas",
        "period": "CHM and Atlas 2022-2024",
        "missingness_rule": "Complete case; no imputation of suppressed values",
        "method": "Equal-area OLS with HC3 covariance",
        "uncertainty": "97.5% confidence interval",
        "diagnostic": "Adjusted residual Moran I and influence checks",
        "sensitivity_status": "supportive_sensitivity_not_primary",
        "source_artifact": "table_2_model_readiness_sensitivities.csv",
        "analysis_status": "freeze_candidate_primary_model_unsecured",
        "authorization": False,
        "verification_status": "verified_internal_audit",
    }

    audit = build_claim_evidence_audit([record], {"C2": "table_2"})

    assert list(audit.columns) == list(CLAIM_EVIDENCE_COLUMNS)
    assert audit.loc[0, "display_id"] == "table_2"
    assert bool(audit.loc[0, "authorization"]) is False


def test_claim_evidence_audit_rejects_missing_fields_and_c1_numbers() -> None:
    with pytest.raises(CaseStudyAnalysisError, match="missing fields"):
        build_claim_evidence_audit([{"claim_id": "C2"}], {"C2": "table_2"})
    c1 = {
        column: "value"
        for column in CLAIM_EVIDENCE_COLUMNS
        if column not in {"display_id", "authorization"}
    }
    c1.update({"claim_id": "C1", "authorization": False, "estimate": -3.2})
    with pytest.raises(CaseStudyAnalysisError, match="C1 numeric"):
        build_claim_evidence_audit([c1], {"C1": "table_2"})


def test_descriptive_claim_evidence_audit_preserves_analysis_name_and_gate() -> None:
    result = {
        "analysis_id": "A1",
        "analysis_name": "Variance partitioning / VPC-ICC",
        "estimand": "between-area share of direct tract variance",
        "unit": "proportion",
        "denominator": 20,
        "period": "2022-2024 pooled direct tract measures",
        "uncertainty": "95% cluster bootstrap interval",
        "diagnostic_status": "eligible",
        "sensitivity_status": "primary",
        "source_artifact": "supplement_descriptive_complementarity_methods.csv",
        "results_authorized": False,
    }
    audit = build_descriptive_claim_evidence_audit([result], {"A1": "etable_7"})
    assert audit.loc[0, "analysis_name"] == result["analysis_name"]
    assert audit.loc[0, "display_id"] == "etable_7"
    assert bool(audit.loc[0, "authorization"]) is False


def test_geographic_resolution_matrix_counts_quartile_reclassification() -> None:
    tract = pd.DataFrame(
        {
            "condition_id": ["copd"] * 4,
            "geography_id": ["t1", "t2", "t3", "t4"],
            "community_area_id": ["01", "01", "02", "02"],
            "ehr_rank": [0.1, 0.8, 0.2, 0.9],
        }
    )
    community = pd.DataFrame(
        {
            "condition_id": ["copd", "copd"],
            "geography_id": ["01", "02"],
            "ehr_rank": [0.2, 0.8],
        }
    )

    matrix = build_geographic_resolution_matrix(tract, community)

    assert matrix.shape[0] == 16
    assert matrix.shape[1] >= 16
    assert int(matrix["tract_count"].sum()) == 4
    assert matrix["tract_percent"].sum() == pytest.approx(100.0)
    disagree = matrix.loc[matrix["tract_quartile"].ne(matrix["community_quartile"])]
    assert int(disagree["tract_count"].sum()) == 2
    assert set(matrix["analysis_status"]) == {"geographic_resolution_sensitivity"}
    assert not matrix["results_authorized"].any()


def test_geographic_resolution_quartile_boundaries_match_aggregation_loss() -> None:
    tract = pd.DataFrame(
        {
            "condition_id": ["copd"] * 4,
            "geography_id": ["t1", "t2", "t3", "t4"],
            "community_area_id": ["01"] * 4,
            "ehr_rank": [0.25, 0.50, 0.75, 1.0],
        }
    )
    community = pd.DataFrame({"condition_id": ["copd"], "geography_id": ["01"], "ehr_rank": [0.25]})

    matrix = build_geographic_resolution_matrix(tract, community)
    observed = matrix.loc[matrix["tract_count"].gt(0)].sort_values("tract_quartile")

    assert observed["tract_quartile"].tolist() == [1, 2, 3, 4]
    assert observed["community_quartile"].tolist() == [1, 1, 1, 1]


def test_geographic_resolution_matrix_fails_closed_without_a_paired_row() -> None:
    tract = pd.DataFrame(
        {
            "condition_id": ["copd"],
            "geography_id": ["t1"],
            "community_area_id": ["01"],
            "ehr_rank": [0.5],
        }
    )
    community = pd.DataFrame(
        {"condition_id": ["diabetes"], "geography_id": ["01"], "ehr_rank": [0.5]}
    )
    with pytest.raises(CaseStudyAnalysisError, match="no paired rows"):
        build_geographic_resolution_matrix(tract, community)


def test_geographic_resolution_matrix_records_comparison_and_provenance_roles() -> None:
    tract = pd.DataFrame(
        {
            "condition_id": ["copd", "copd"],
            "geography_id": ["t1", "t2"],
            "community_area_id": ["01", "01"],
            "ehr_rank": [0.2, 0.8],
        }
    )
    community = pd.DataFrame(
        {"condition_id": ["copd"], "geography_id": ["01"], "ehr_rank": [0.5]}
    )

    matrix = build_geographic_resolution_matrix(tract, community)

    required = {
        "comparison_geography_type",
        "period",
        "source_artifact",
        "source_checksum",
        "annual_sensitivity_status",
        "noncrossing_sensitivity_status",
        "uncertainty_aware_agreement_status",
        "uncertainty_aware_agreement_reason",
        "field_role",
        "results_authorized",
    }
    assert required <= set(matrix.columns)
    assert set(matrix["comparison_geography_type"]) == {"chicago_community_area"}
    assert set(matrix["field_role"]) == {"derived"}
    assert matrix["results_authorized"].eq(False).all()


def test_geographic_resolution_matrix_rejects_model_fields() -> None:
    tract = pd.DataFrame(
        {
            "condition_id": ["copd"],
            "geography_id": ["t1"],
            "community_area_id": ["01"],
            "ehr_rank": [0.5],
            "estimate": [1.2],
        }
    )
    community = pd.DataFrame(
        {"condition_id": ["copd"], "geography_id": ["01"], "ehr_rank": [0.5]}
    )
    with pytest.raises(CaseStudyAnalysisError, match="cannot contain model fields"):
        build_geographic_resolution_matrix(tract, community)
