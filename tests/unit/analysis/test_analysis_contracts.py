from __future__ import annotations

import math

import pandas as pd
import pytest

from chicagohealthmap.analysis.contracts import (
    A1_A7_ANALYSIS_NAMES,
    build_complementarity_frame,
    validate_analysis_result,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "geography_type": ["census_tract", "census_tract", "chicago_community_area"],
            "geography_id": ["t1", "t2", "01"],
            "community_area_id": ["01", "02", "01"],
            "time_period": ["2022", "2023", "2022"],
            "condition_id": ["copd", "copd", "copd"],
            "published_measure_value": [0.2, 0.3, 0.25],
            "public_comparator_estimate": [0.21, 0.29, None],
            "suppression_flag": [False, False, False],
            "is_crossing_tract": [False, False, False],
            "reliability_tier": ["High", "Good", "High"],
            "disease_value_derivation": [
                "direct_first_party_export_not_interpolated",
                "direct_first_party_export_not_interpolated",
                "direct_first_party_export_not_interpolated",
            ],
        }
    )


def test_analysis_registry_has_unique_descriptive_names() -> None:
    assert set(A1_A7_ANALYSIS_NAMES) == {"A1", "A2", "A3", "A4", "A5", "A6", "A7"}
    assert len(set(A1_A7_ANALYSIS_NAMES.values())) == 7


def test_shared_frame_freezes_scale_year_and_complete_case_rules() -> None:
    frame = build_complementarity_frame(
        _frame(),
        condition_id="copd",
        geography_type="census_tract",
        years=("2022",),
        require_public_comparator=True,
    )
    assert list(frame["geography_id"]) == ["t1"]
    assert set(frame["analysis_scale"]) == {"census_tract"}
    assert set(frame["analysis_condition_id"]) == {"copd"}
    assert set(frame["results_authorized"]) == {False}


def test_shared_frame_rejects_missing_required_columns() -> None:
    with pytest.raises(ValueError, match="missing columns"):
        build_complementarity_frame(pd.DataFrame({"condition_id": ["copd"]}), condition_id="copd")


def test_analysis_result_requires_governed_fields() -> None:
    result = {"analysis_id": "A3", "estimate": 0.5, "results_authorized": False}
    with pytest.raises(ValueError, match="missing fields"):
        validate_analysis_result(result)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_analysis_result_rejects_nonfinite_numeric_fields(value: float) -> None:
    result = {
        "analysis_id": "A3",
        "analysis_name": A1_A7_ANALYSIS_NAMES["A3"],
        "estimand": "rank agreement",
        "unit": "correlation",
        "denominator": 10,
        "period": "2022",
        "uncertainty": "descriptive",
        "diagnostic_status": "eligible",
        "sensitivity_status": "primary",
        "source_artifact": "fixture",
        "results_authorized": False,
        "estimate": value,
    }
    with pytest.raises(ValueError, match="not finite"):
        validate_analysis_result(result)


def test_shared_frame_rejects_interpolated_values_and_duplicate_keys() -> None:
    frame = _frame()
    frame.loc[0, "disease_value_derivation"] = "polygon_interpolation"
    with pytest.raises(ValueError, match="direct"):
        build_complementarity_frame(frame, condition_id="copd")
    duplicate = pd.concat([_frame(), _frame().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        build_complementarity_frame(duplicate, condition_id="copd")
