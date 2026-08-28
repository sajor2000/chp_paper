"""Schema-first data, claim, and geographic-resolution audits for the paper notebook."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import product
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import numpy as np

from chicagohealthmap.analysis.case_studies import CaseStudyAnalysisError
from chicagohealthmap.analysis.contracts import validate_analysis_result

PRIMARY_KEY = ("geography_type", "geography_id", "time_period", "condition_id")
CLAIM_EVIDENCE_COLUMNS = (
    "claim_id",
    "display_id",
    "question",
    "estimand",
    "estimate",
    "ci_low",
    "ci_high",
    "confidence_level",
    "eligible_n",
    "unit",
    "grain",
    "denominator",
    "period",
    "missingness_rule",
    "method",
    "uncertainty",
    "diagnostic",
    "sensitivity_status",
    "source_artifact",
    "analysis_status",
    "authorization",
    "verification_status",
)
DESCRIPTIVE_EVIDENCE_COLUMNS = (
    "analysis_id",
    "analysis_name",
    "question",
    "estimand",
    "unit",
    "grain",
    "denominator",
    "period",
    "missingness_rule",
    "method",
    "uncertainty",
    "diagnostic",
    "sensitivity_status",
    "source_artifact",
    "authorization",
    "display_id",
)


def _require_columns(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns - set(frame.columns))
    if missing:
        raise CaseStudyAnalysisError(f"{label} is missing columns: {missing}")


def _audit_row(
    check_id: str,
    domain: str,
    question: str,
    expected: str,
    observed: str,
    source_artifact: str,
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "domain": domain,
        "question": question,
        "expected": expected,
        "observed": observed,
        "status": "pass",
        "severity": "critical_if_failed",
        "source_artifact": source_artifact,
        "authorization": False,
    }


def build_data_quality_audit(
    dataset: pd.DataFrame,
    dataset_manifest: Mapping[str, Any],
    join_manifest: Mapping[str, Any],
    *,
    expected_rows: int = 20_536,
    expected_columns: int = 97,
) -> pd.DataFrame:
    """Validate the frozen analytic grain and return an inspectable audit table."""

    _require_columns(
        dataset,
        {
            *PRIMARY_KEY,
            "numerator",
            "suppression_flag",
            "disease_value_derivation",
            "public_comparator_role",
            "public_comparator_time_period",
            "census_covariate_time_period",
            "life_expectancy_time_period",
        },
        "analytic dataset",
    )
    if dataset.shape != (expected_rows, expected_columns):
        raise CaseStudyAnalysisError(
            f"dataset shape changed: {dataset.shape} != {(expected_rows, expected_columns)}"
        )
    manifest_key = tuple(dataset_manifest.get("primary_key", ()))
    if manifest_key != PRIMARY_KEY or dataset.duplicated(list(PRIMARY_KEY)).any():
        raise CaseStudyAnalysisError("analytic dataset primary key is not unique or changed")
    if int(dataset_manifest.get("row_count", -1)) != len(dataset):
        raise CaseStudyAnalysisError("dataset manifest row count does not match the artifact")
    derivations = set(dataset["disease_value_derivation"].dropna().astype(str))
    if derivations != {"direct_first_party_export_not_interpolated"}:
        raise CaseStudyAnalysisError("disease values are not uniformly direct first-party values")
    suppressed = dataset["suppression_flag"].astype(bool)
    if (dataset.loc[suppressed, "numerator"] >= 10).any():
        raise CaseStudyAnalysisError("suppression state conflicts with the fewer-than-10 rule")
    if (dataset.loc[~suppressed, "numerator"] < 10).any():
        raise CaseStudyAnalysisError("an unsuppressed numerator is below the source threshold")
    tract = dataset["geography_type"].eq("census_tract")
    expected_role = "tract_concordance_discordance_comparator"
    if dataset.loc[tract, "public_comparator_role"].dropna().ne(expected_role).any():
        raise CaseStudyAnalysisError("PLACES has an invalid role in tract records")
    if dataset.loc[~tract, "public_comparator_role"].notna().any():
        raise CaseStudyAnalysisError("PLACES comparator leaked into community-area records")
    joins = join_manifest.get("joins")
    if not isinstance(joins, list) or not joins:
        raise CaseStudyAnalysisError("source join ledger is missing or empty")
    validations = {str(row.get("validation")) for row in joins}
    if not validations.issubset({"many_to_one", "one_to_one"}):
        raise CaseStudyAnalysisError("source join cardinality is not fail-closed")
    if dataset_manifest.get("results_authorized") is not False:
        raise CaseStudyAnalysisError("results authorization must remain false")
    if not dataset_manifest.get("checksums"):
        raise CaseStudyAnalysisError("dataset manifest is missing checksums")

    periods = _source_period_text(dataset)
    rows = [
        _audit_row(
            "dataset_shape",
            "shape",
            "Does the artifact match its frozen shape?",
            f"{expected_rows} x {expected_columns}",
            f"{len(dataset)} x {len(dataset.columns)}",
            "analytic parquet",
        ),
        _audit_row(
            "primary_key_uniqueness",
            "grain",
            "Is one row retained per governed key?",
            "0 duplicate keys",
            "0 duplicate keys",
            "analytic parquet",
        ),
        _audit_row(
            "direct_values",
            "validity",
            "Are CHM disease values direct and uninterpolated?",
            "direct first-party values",
            next(iter(derivations)),
            "dataset lineage",
        ),
        _audit_row(
            "suppression_state",
            "validity",
            "Are suppression and observed values distinct?",
            "numerator <10 iff suppressed",
            f"{int(suppressed.sum())} suppressed rows",
            "analytic parquet",
        ),
        _audit_row(
            "source_roles",
            "integrity",
            "Are public-source roles geography-specific?",
            "PLACES comparator on tracts only",
            "role separation verified",
            "source/join manifest",
        ),
        _audit_row(
            "source_periods",
            "timeliness",
            "Are source periods explicit and noninterchangeable?",
            "source-specific periods",
            periods,
            "analytic parquet",
        ),
        _audit_row(
            "join_cardinality",
            "integrity",
            "Do joins avoid row multiplication?",
            "one-to-one or many-to-one",
            "|".join(sorted(validations)) or "no joins",
            "source/join manifest",
        ),
        _audit_row(
            "checksums",
            "provenance",
            "Are built artifacts checksum-bound?",
            "checksums present",
            f"{len(dataset_manifest['checksums'])} checksums",
            "dataset manifest",
        ),
        _audit_row(
            "authorization",
            "governance",
            "Is manuscript authorization closed?",
            "results_authorized=false",
            "results_authorized=false",
            "results authorization",
        ),
    ]
    return pd.DataFrame(rows)


def _source_period_text(dataset: pd.DataFrame) -> str:
    def values(column: str) -> str:
        observed = sorted(set(dataset[column].dropna().astype(str)))
        return ",".join(observed) if observed else "not_applicable"

    return (
        f"CHM={values('time_period')}; Atlas={values('life_expectancy_time_period')}; "
        f"ACS={values('census_covariate_time_period')}; "
        f"PLACES={values('public_comparator_time_period')}"
    )


def build_claim_evidence_audit(
    result_objects: Sequence[Mapping[str, Any]],
    display_registry: Mapping[str, str],
) -> pd.DataFrame:
    """Validate and render the SAP claim-to-evidence contract."""

    required = set(CLAIM_EVIDENCE_COLUMNS) - {"display_id"}
    records: list[dict[str, object]] = []
    for result in result_objects:
        missing = sorted(required - set(result))
        if missing:
            raise CaseStudyAnalysisError(f"claim evidence record is missing fields: {missing}")
        claim_id = str(result["claim_id"])
        if result["authorization"] is not False:
            raise CaseStudyAnalysisError("claim evidence authorization must remain false")
        numeric_fields = {"estimate", "ci_low", "ci_high", "p_value"}
        if claim_id == "C1" and any(result.get(field) is not None for field in numeric_fields):
            raise CaseStudyAnalysisError("C1 numeric result cannot enter claim evidence")
        if claim_id == "C2":
            eligible_fields = ("estimate", "ci_low", "ci_high", "confidence_level", "eligible_n")
            if any(result.get(field) is None for field in eligible_fields):
                raise CaseStudyAnalysisError("C2 claim evidence requires estimate, interval, and n")
        if claim_id not in display_registry:
            raise CaseStudyAnalysisError(f"claim {claim_id} has no registered display")
        record = dict(result)
        record["display_id"] = display_registry[claim_id]
        records.append({column: record[column] for column in CLAIM_EVIDENCE_COLUMNS})
    if not records:
        raise CaseStudyAnalysisError("claim evidence audit cannot be empty")
    return pd.DataFrame(records, columns=CLAIM_EVIDENCE_COLUMNS)


def build_descriptive_claim_evidence_audit(
    result_objects: Sequence[Mapping[str, Any]],
    display_registry: Mapping[str, str],
) -> pd.DataFrame:
    """Render A1–A7 results into a claim-to-evidence table without calculations."""

    records: list[dict[str, object]] = []
    for result in result_objects:
        normalized = dict(result)
        for field in ("estimate", "ci_low", "ci_high"):
            if field in normalized and pd.isna(normalized[field]):
                normalized[field] = None
        try:
            validated = validate_analysis_result(normalized)
        except ValueError as exc:
            raise CaseStudyAnalysisError(f"invalid descriptive claim record: {exc}") from exc
        analysis_id = str(validated["analysis_id"])
        if analysis_id not in display_registry:
            raise CaseStudyAnalysisError(f"descriptive analysis {analysis_id} has no display")
        records.append(
            {
                "analysis_id": analysis_id,
                "analysis_name": str(validated["analysis_name"]),
                "question": str(validated.get("question", validated["estimand"])),
                "estimand": validated["estimand"],
                "unit": validated["unit"],
                "grain": str(validated.get("scale", "source-defined geography")),
                "denominator": validated["denominator"],
                "period": validated["period"],
                "missingness_rule": str(
                    validated.get("missingness_rule", "suppressed and nonfinite values excluded")
                ),
                "method": str(validated.get("estimator", validated["analysis_name"])),
                "uncertainty": validated["uncertainty"],
                "diagnostic": validated["diagnostic_status"],
                "sensitivity_status": validated["sensitivity_status"],
                "source_artifact": validated["source_artifact"],
                "authorization": False,
                "display_id": display_registry[analysis_id],
            }
        )
    if not records:
        raise CaseStudyAnalysisError("descriptive claim evidence audit cannot be empty")
    return pd.DataFrame(records, columns=DESCRIPTIVE_EVIDENCE_COLUMNS)


def build_master_claim_records(
    readiness: pd.DataFrame,
    primary_contrasts: pd.DataFrame,
    aggregation_loss: pd.DataFrame,
) -> list[dict[str, object]]:
    """Assemble the three governed paper claims without manuscript authorization."""

    c1 = readiness.loc[readiness["model_id"].eq("C1")]
    c2 = primary_contrasts.loc[primary_contrasts["model_id"].eq("C2")]
    if len(c1) != 1 or len(c2) != 1 or aggregation_loss.empty:
        raise CaseStudyAnalysisError("master claim inputs are incomplete")
    c1_row, c2_row = c1.iloc[0], c2.iloc[0]
    c1_status = str(c1_row.get("status"))
    c1_vif_withheld = (
        c1_status == "withheld_vif_above_5"
        and np.isfinite(float(c1_row.get("maximum_vif", np.nan)))
        and float(c1_row["maximum_vif"]) > 5.0
    )
    c1_semantics_withheld = (
        c1_status == "withheld_insufficient_complete_areas"
        and int(c1_row.get("n_complete", -1)) == 0
    )
    if not (c1_vif_withheld or c1_semantics_withheld):
        raise CaseStudyAnalysisError("cardiometabolic gate is not verified as withheld")
    c2_values = [
        float(c2_row.get(name, np.nan))
        for name in ("estimate", "ci_low", "ci_high", "confidence_level", "n")
    ]
    if not all(np.isfinite(c2_values)) or not (
        c2_values[1] <= c2_values[0] <= c2_values[2]
        and c2_values[3] == 0.975
        and int(c2_values[4]) > 0
    ):
        raise CaseStudyAnalysisError("COPD candidate estimate contract is not verified")
    required_resolution = {"tract_sample_n", "results_authorized", "analysis_status"}
    if not required_resolution.issubset(aggregation_loss.columns):
        raise CaseStudyAnalysisError("geographic-resolution evidence contract is incomplete")
    if aggregation_loss["results_authorized"].ne(False).any() or set(
        aggregation_loss["analysis_status"].astype(str)
    ) != {"geographic_resolution_sensitivity"}:
        raise CaseStudyAnalysisError("geographic-resolution evidence is not verified")
    common = {
        "period": "CHM 2022-2024; source-specific public periods retained",
        "missingness_rule": "Complete case for the estimand; no imputation of suppressed values",
        "authorization": False,
        "verification_status": "verified_internal_audit",
    }
    return [
        {
            "claim_id": "C1",
            "question": "Are cardiometabolic CHM measures associated with life expectancy?",
            "estimand": "Joint one-frozen-IQR hypertension plus diabetes contrast",
            "estimate": None,
            "ci_low": None,
            "ci_high": None,
            "confidence_level": None,
            "eligible_n": int(c1_row["n_complete"]),
            "unit": "life-expectancy years",
            "grain": "Chicago community area",
            "denominator": (
                "0 eligible community areas" if c1_semantics_withheld
                else "77 eligible community areas"
            ),
            "method": "Not run" if c1_semantics_withheld else "Prespecified equal-area OLS with HC3 covariance",
            "uncertainty": "Not estimated",
            "diagnostic": (
                "Combined diabetes semantics unapproved"
                if c1_semantics_withheld else "Maximum VIF 5.016 (>5)"
            ),
            "sensitivity_status": (
                "not_run_combined_diabetes_semantics_unapproved"
                if c1_semantics_withheld else "audit_only_exploratory"
            ),
            "source_artifact": "table_2_model_readiness_sensitivities.csv",
            "analysis_status": c1_status,
            **common,
        },
        {
            "claim_id": "C2",
            "question": "Is the CHM COPD measure associated with life expectancy?",
            "estimand": "Life-expectancy difference per frozen-IQR COPD contrast",
            "estimate": float(c2_row["estimate"]),
            "ci_low": float(c2_row["ci_low"]),
            "ci_high": float(c2_row["ci_high"]),
            "confidence_level": float(c2_row["confidence_level"]),
            "eligible_n": int(c2_row["n"]),
            "unit": "life-expectancy years",
            "grain": "Chicago community area",
            "denominator": "76 eligible community areas",
            "method": "Equal-area OLS with HC3 covariance",
            "uncertainty": confidence_text(float(c2_row["confidence_level"])),
            "diagnostic": "Influence and adjusted residual Moran checks",
            "sensitivity_status": "freeze_candidate_supportive_sensitivities",
            "source_artifact": "table_2_model_readiness_sensitivities.csv",
            "analysis_status": "freeze_candidate_primary_model_unsecured",
            **common,
        },
        {
            "claim_id": "GR",
            "question": "What tract classifications change under direct coarser-area CHM ranks?",
            "estimand": "Highest-quartile tract transitions under community-area and ZCTA ranks",
            "estimate": None,
            "ci_low": None,
            "ci_high": None,
            "confidence_level": None,
            "eligible_n": int(aggregation_loss["tract_sample_n"].max()),
            "unit": "tracts and percentage",
            "grain": "Census tract linked to dominant community area or ZCTA",
            "denominator": "Condition-specific eligible tracts",
            "method": "Direct-rank transition classification",
            "uncertainty": "Descriptive annual stability; no inferential interval",
            "diagnostic": "All-tract, noncrossing-tract, and annual comparison",
            "sensitivity_status": "geographic_resolution_sensitivity",
            "source_artifact": "supplement_geographic_consequence_transitions.csv",
            "analysis_status": "descriptive_complementarity_not_validation",
            **common,
        },
    ]


def confidence_text(level: float) -> str:
    """Return a plain-language confidence-interval label for audit records."""

    percent = 100 * level
    digits = 0 if percent.is_integer() else 1
    return f"{percent:.{digits}f}% confidence interval"


def _quartile(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="raise")
    if numeric.isna().any() or ((numeric < 0) | (numeric > 1)).any():
        raise CaseStudyAnalysisError("geographic-resolution ranks must be between 0 and 1")
    return pd.Series(
        np.select(
            [numeric.le(0.25), numeric.le(0.50), numeric.le(0.75)],
            [1, 2, 3],
            default=4,
        ),
        index=values.index,
        dtype="int64",
    )


def build_geographic_resolution_matrix(
    tract_frame: pd.DataFrame,
    community_frame: pd.DataFrame,
    *,
    period: str = "CHM 2022-2024 pooled direct values",
    source_artifact: str = "00_master_analytic_dataset.parquet",
    source_checksum: str = "not_provided_in_frame",
) -> pd.DataFrame:
    """Cross-tabulate direct tract ranks against inherited community-area ranks."""

    forbidden = {
        "model_id",
        "model_key",
        "coefficient",
        "estimate",
        "ci_low",
        "ci_high",
        "adjustment_set",
        "readiness_status",
        "model_readiness",
        "residual_diagnostic",
    }
    leaked = sorted(forbidden & (set(tract_frame.columns) | set(community_frame.columns)))
    if leaked:
        raise CaseStudyAnalysisError(
            "geographic resolution matrix cannot contain model fields: " + ", ".join(leaked)
        )

    _require_columns(
        tract_frame,
        {"condition_id", "geography_id", "community_area_id", "ehr_rank"},
        "tract resolution frame",
    )
    _require_columns(
        community_frame,
        {"condition_id", "geography_id", "ehr_rank"},
        "community resolution frame",
    )
    if tract_frame.duplicated(["condition_id", "geography_id"]).any():
        raise CaseStudyAnalysisError("tract resolution frame contains duplicate tracts")
    community = community_frame.copy()
    if community.duplicated(["condition_id", "geography_id"]).any():
        raise CaseStudyAnalysisError("community resolution frame contains duplicate areas")
    community["community_quartile"] = _quartile(community["ehr_rank"])
    community = community.rename(columns={"geography_id": "community_area_id"})
    tract = tract_frame.copy()
    tract["tract_quartile"] = _quartile(tract["ehr_rank"])
    paired = tract.merge(
        community[["condition_id", "community_area_id", "community_quartile"]],
        on=["condition_id", "community_area_id"],
        how="inner",
        validate="many_to_one",
    )
    if paired.empty:
        raise CaseStudyAnalysisError("tract and community resolution frames have no paired rows")
    records: list[dict[str, object]] = []
    for condition_id, group in paired.groupby("condition_id", sort=True):
        counts = group.groupby(["community_quartile", "tract_quartile"]).size()
        denominator = len(group)
        for community_quartile, tract_quartile in product(range(1, 5), repeat=2):
            count = int(counts.get((community_quartile, tract_quartile), 0))
            records.append(
                {
                    "condition_id": condition_id,
                    "community_quartile": community_quartile,
                    "tract_quartile": tract_quartile,
                    "tract_count": count,
                    "tract_percent": 100 * count / denominator,
                    "comparison_geography_type": "chicago_community_area",
                    "period": period,
                    "source_artifact": source_artifact,
                    "source_checksum": source_checksum,
                    "field_role": "derived",
                    "annual_sensitivity_status": "reported_separately",
                    "noncrossing_sensitivity_status": "reported_separately",
                    "uncertainty_aware_agreement_status": "not_run",
                    "uncertainty_aware_agreement_reason": (
                        "Compatible PLACES intervals and denominator uncertainty were not available"
                    ),
                    "analysis_status": "geographic_resolution_sensitivity",
                    "results_authorized": False,
                }
            )
    return pd.DataFrame(records)
