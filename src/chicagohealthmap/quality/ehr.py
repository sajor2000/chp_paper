"""Column-parameterized quality checks for evidence-verified EHR tables."""

from __future__ import annotations

from collections.abc import Collection, Hashable
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from chicagohealthmap.quality.reports import QualityFinding, Severity


def _rows(mask: pd.Series) -> tuple[int, ...]:
    return tuple(position for position, failed in enumerate(mask.fillna(False), start=1) if failed)


def _fatal(code: str, message: str, rows: tuple[int, ...]) -> tuple[QualityFinding, ...]:
    if not rows:
        return ()
    return (
        QualityFinding(code=code, severity=Severity.fatal, message=message, affected_rows=rows),
    )


def validate_numerator_denominator(
    frame: pd.DataFrame, numerator: str, denominator: str
) -> tuple[QualityFinding, ...]:
    """Reject known numerators greater than known denominators."""

    mask = (
        frame[numerator].notna()
        & frame[denominator].notna()
        & (frame[numerator] > frame[denominator])
    )
    return _fatal("numerator_gt_denominator", "numerator exceeds denominator", _rows(mask))


def validate_ratio(
    frame: pd.DataFrame,
    numerator: str,
    denominator: str,
    ratio: str,
    *,
    tolerance: float = 1e-10,
) -> tuple[QualityFinding, ...]:
    """Reject known proportions inconsistent with their known count pair."""

    known = frame[[numerator, denominator, ratio]].notna().all(axis=1)
    expected = frame[numerator] / frame[denominator]
    mismatch = known & ((frame[denominator] == 0) | ((frame[ratio] - expected).abs() > tolerance))
    return _fatal(
        "ratio_mismatch", "ratio does not reconcile with numerator/denominator", _rows(mismatch)
    )


def validate_domain(
    frame: pd.DataFrame,
    column: str,
    allowed: Collection[Hashable],
    *,
    code: str,
) -> tuple[QualityFinding, ...]:
    """Reject nonmissing values outside a caller-supplied, evidence-backed domain."""

    mask = frame[column].notna() & ~frame[column].isin(allowed)
    return _fatal(code, f"{column} contains a value outside its verified domain", _rows(mask))


def validate_denominator_consistency(
    frame: pd.DataFrame, group_columns: tuple[str, ...], denominator: str
) -> tuple[QualityFinding, ...]:
    """Reject differing known denominators where the caller asserts they are shared."""

    counts = frame.groupby(list(group_columns), dropna=False)[denominator].transform("nunique")
    mask = frame[denominator].notna() & (counts > 1)
    return _fatal("denominator_inconsistency", "shared denominator is inconsistent", _rows(mask))


def validate_suppressed_zero(
    frame: pd.DataFrame,
    value_column: str,
    state_column: str,
    *,
    suppressed_states: Collection[Any] = ("suppressed", "unknown"),
) -> tuple[QualityFinding, ...]:
    """Reject analysis-ready numeric zero when cell state is suppressed or unknown."""

    mask = frame[state_column].isin(suppressed_states) & (frame[value_column] == 0)
    return _fatal(
        "suppressed_unknown_as_zero",
        "suppressed or unknown cell is represented as a known zero",
        _rows(mask),
    )


def required_checkpoint_findings() -> tuple[QualityFinding, ...]:
    """Declare the complete prespecified quality-code vocabulary.

    These declarations are not claims that a check ran. Real checks require verified
    semantic columns; the checkpoint keeps that distinction explicit.
    """

    fatal = {
        "schema_mismatch": "source shape does not match the verified schema",
        "duplicate_primary_key": "primary key is duplicated",
        "invalid_geography_domain": "geography is outside the verified domain",
        "invalid_year_domain": "year is outside the verified domain",
        "invalid_condition_domain": "condition is outside the verified domain",
        "numerator_gt_denominator": "numerator exceeds denominator",
        "ratio_mismatch": "ratio does not reconcile with numerator/denominator",
        "denominator_inconsistency": "asserted shared denominator differs within group",
        "suppressed_unknown_as_zero": "suppressed or unknown cell is a known zero",
    }
    warnings = {
        "expected_empty_file": "a source file expected in the delivery has no rows",
        "geographic_coverage_gap": "expected geography coverage is incomplete",
        "zero_suppressed_ambiguity": "zero and suppression states cannot be distinguished",
        "subgroup_nonreconciliation": "subgroups do not reconcile with the verified total",
        "low_capture": "healthcare capture is below the prespecified threshold",
        "demographic_misalignment": "source demographics differ from the comparator",
        "age_standardization_nonreconstructable": "age adjustment cannot be reconstructed",
        "below_reliability_threshold": "condition-period-geography cell is below threshold",
    }
    return tuple(
        QualityFinding(code=code, severity=Severity.fatal, message=message)
        for code, message in fatal.items()
    ) + tuple(
        QualityFinding(code=code, severity=Severity.warning, message=message)
        for code, message in warnings.items()
    )
