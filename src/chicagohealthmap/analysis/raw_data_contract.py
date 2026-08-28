"""Study-specific raw ChicagoHealthMap aggregate-data contract and gates."""

from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml  # type: ignore[import-untyped]
from shapely import from_wkb  # type: ignore[import-untyped]

from chicagohealthmap.analysis.dataset_artifacts import AnalyticDatasetError


SNAPSHOT = Path("sources/first_party/capricorn/snapshots/2026-05-27")
ORIGINAL = SNAPSHOT / "original"
CONTRACT_PATH = Path("config/chm_study_data_contract.yml")
SIX_COUNTY_FIPS = frozenset({"17031", "17043", "17089", "17097", "17111", "17197"})

FACT_COLUMNS = (
    "id",
    "geography_key",
    "dx_year",
    "condition_key",
    "total_count",
    "age_18_34",
    "age_35_44",
    "age_45_54",
    "age_55_64",
    "age_65_74",
    "age_75_84",
    "age_85_above",
    "sex_male",
    "sex_female",
    "sex_other_unknown",
    "race_white",
    "race_black",
    "race_asian",
    "race_other",
    "race_unknown",
    "hispanic_yes",
    "hispanic_no",
    "hispanic_other",
    "hispanic_unknown",
    "denom_total_count",
    "denom_age_18_34",
    "denom_age_35_44",
    "denom_age_45_54",
    "denom_age_55_64",
    "denom_age_65_74",
    "denom_age_75_84",
    "denom_age_85_above",
    "denom_sex_male",
    "denom_sex_female",
    "denom_sex_other_unknown",
    "denom_race_white",
    "denom_race_black",
    "denom_race_asian",
    "denom_race_other",
    "denom_race_unknown",
    "denom_hispanic_yes",
    "denom_hispanic_no",
    "denom_hispanic_other",
    "denom_hispanic_unknown",
    "prev_total_count",
    "prev_age_18_34",
    "prev_age_35_44",
    "prev_age_45_54",
    "prev_age_55_64",
    "prev_age_65_74",
    "prev_age_75_84",
    "prev_age_85_above",
    "prev_sex_male",
    "prev_sex_female",
    "prev_sex_other_unknown",
    "prev_race_white",
    "prev_race_black",
    "prev_race_asian",
    "prev_race_other",
    "prev_race_unknown",
    "prev_hispanic_yes",
    "prev_hispanic_no",
    "prev_hispanic_other",
    "prev_hispanic_unknown",
    "data_source",
    "loaded_at",
    "is_active",
)


@dataclass(frozen=True, slots=True)
class FactAudit:
    """Aggregate quality findings for one geography-level fact table."""

    table: str
    rows: int
    geographies: int
    years: tuple[int, ...]
    conditions: int
    duplicate_keys: int
    invalid_numeric_rows: int
    negative_count_rows: int
    numerator_greater_than_denominator_rows: int
    prevalence_outside_unit_interval_rows: int
    zero_denominator_rows: int
    zero_numerator_positive_denominator_rows: int
    positive_numerator_below_10_rows: int
    geography_years: int
    varying_denominator_geography_years: int
    published_measure_ratio_mismatch_rows: int


@dataclass(frozen=True, slots=True)
class GeometryAudit:
    """Aggregate geometry validation for one dimension."""

    table: str
    rows: int
    duplicate_keys: int
    missing_geometry_rows: int
    invalid_geometry_rows: int


@dataclass(frozen=True, slots=True)
class RawDataAudit:
    """Complete study-specific raw-data gate result."""

    contract_version: int
    primary_tract_contract_passed: bool
    higher_geography_estimand_authorized: bool
    chicago_rollup_exact_matches: int
    chicago_rollup_rows: int
    outside_six_county_tracts: int
    outside_six_county_rows: int
    outside_six_county_positive_numerator_rows: int
    outside_six_county_positive_denominator_rows: int
    fact_audits: tuple[FactAudit, ...]
    geometry_audits: tuple[GeometryAudit, ...]
    unresolved_signoff_items: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible representation."""

        return asdict(self)


def load_study_data_contract(root: Path) -> dict[str, Any]:
    """Load and minimally validate the study-specific source contract."""

    path = root / CONTRACT_PATH
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise AnalyticDatasetError(f"study data contract is unavailable or invalid: {path}") from error
    if not isinstance(payload, dict) or payload.get("contract_version") != 1:
        raise AnalyticDatasetError("study data contract must be a version 1 mapping")
    columns = payload.get("condition_fact_columns")
    if tuple(columns or ()) != FACT_COLUMNS:
        raise AnalyticDatasetError("study data contract condition-fact columns do not match code")
    return payload


def _pipe_rows(path: Path, expected_fields: int) -> Iterable[list[str]]:
    if not path.is_file():
        raise AnalyticDatasetError(f"required raw source is missing: {path}")
    csv.field_size_limit(sys.maxsize)
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.reader(handle, delimiter="|"):
            if not row or not any(value.strip() for value in row):
                continue
            if len(row) != expected_fields:
                raise AnalyticDatasetError(
                    f"{path.name} expected {expected_fields} fields, observed {len(row)}"
                )
            yield [value.strip() for value in row]


def _required_integer(value: str) -> int:
    if value == "":
        raise ValueError("missing integer")
    return int(value)


def _required_float(value: str) -> float:
    if value == "":
        raise ValueError("missing float")
    return float(value)


def _fact_audit(path: Path) -> tuple[FactAudit, dict[tuple[str, int], tuple[int, int]]]:
    keys: set[tuple[str, int, str]] = set()
    geographies: set[str] = set()
    years: set[int] = set()
    conditions: set[str] = set()
    denominators: dict[tuple[str, int], set[int]] = {}
    aggregates: dict[tuple[str, int], tuple[int, int]] = {}
    rows = duplicate_keys = invalid_numeric = negative_counts = 0
    numerator_gt_denominator = prevalence_outside = zero_denominator = 0
    zero_numerator_positive_denominator = positive_below_10 = ratio_mismatch = 0

    for row in _pipe_rows(path, len(FACT_COLUMNS)):
        rows += 1
        geography = row[1]
        condition = row[3]
        try:
            year = _required_integer(row[2])
            numerator = _required_integer(row[4])
            denominator = _required_integer(row[24])
            prevalence = _required_float(row[44])
        except ValueError:
            invalid_numeric += 1
            continue
        key = (geography, year, condition)
        if key in keys:
            duplicate_keys += 1
        keys.add(key)
        geographies.add(geography)
        years.add(year)
        conditions.add(condition)
        denominators.setdefault((geography, year), set()).add(denominator)
        aggregate_key = (condition, year)
        previous_n, previous_d = aggregates.get(aggregate_key, (0, 0))
        aggregates[aggregate_key] = (previous_n + numerator, previous_d + denominator)

        if numerator < 0 or denominator < 0:
            negative_counts += 1
        if numerator > denominator:
            numerator_gt_denominator += 1
        if prevalence < 0 or prevalence > 1:
            prevalence_outside += 1
        if denominator == 0:
            zero_denominator += 1
        if numerator == 0 and denominator > 0:
            zero_numerator_positive_denominator += 1
        if 0 < numerator < 10:
            positive_below_10 += 1
        if denominator > 0 and not math.isclose(
            prevalence, numerator / denominator, rel_tol=0.0, abs_tol=1e-12
        ):
            ratio_mismatch += 1

    audit = FactAudit(
        table=path.name,
        rows=rows,
        geographies=len(geographies),
        years=tuple(sorted(years)),
        conditions=len(conditions),
        duplicate_keys=duplicate_keys,
        invalid_numeric_rows=invalid_numeric,
        negative_count_rows=negative_counts,
        numerator_greater_than_denominator_rows=numerator_gt_denominator,
        prevalence_outside_unit_interval_rows=prevalence_outside,
        zero_denominator_rows=zero_denominator,
        zero_numerator_positive_denominator_rows=zero_numerator_positive_denominator,
        positive_numerator_below_10_rows=positive_below_10,
        geography_years=len(denominators),
        varying_denominator_geography_years=sum(len(values) > 1 for values in denominators.values()),
        published_measure_ratio_mismatch_rows=ratio_mismatch,
    )
    return audit, aggregates


def _tract_scope_audit(root: Path) -> tuple[int, int, int, int]:
    county_by_tract = {
        row[0]: row[2]
        for row in _pipe_rows(root / ORIGINAL / "dim_census_tracts.text", 20)
    }
    outside_tracts: set[str] = set()
    outside_rows = positive_numerator = positive_denominator = 0
    for row in _pipe_rows(root / ORIGINAL / "fact_tract_condition_stats.text", 67):
        if county_by_tract.get(row[1]) in SIX_COUNTY_FIPS:
            continue
        outside_rows += 1
        outside_tracts.add(row[1])
        try:
            positive_numerator += _required_integer(row[4]) > 0
            positive_denominator += _required_integer(row[24]) > 0
        except ValueError:
            positive_numerator += 1
            positive_denominator += 1
    return len(outside_tracts), outside_rows, positive_numerator, positive_denominator


def _geometry_audit(path: Path, expected_fields: int, geometry_position: int) -> GeometryAudit:
    keys: set[str] = set()
    rows = duplicate_keys = missing_geometry = invalid_geometry = 0
    for row in _pipe_rows(path, expected_fields):
        rows += 1
        key = row[0]
        if key in keys:
            duplicate_keys += 1
        keys.add(key)
        value = row[geometry_position - 1]
        if not value:
            missing_geometry += 1
            continue
        try:
            geometry = from_wkb(bytes.fromhex(value))
        except (TypeError, ValueError):
            invalid_geometry += 1
            continue
        if geometry.is_empty or not geometry.is_valid:
            invalid_geometry += 1
    return GeometryAudit(
        table=path.name,
        rows=rows,
        duplicate_keys=duplicate_keys,
        missing_geometry_rows=missing_geometry,
        invalid_geometry_rows=invalid_geometry,
    )


def _chicago_rollup_matches(
    path: Path, community_aggregates: dict[tuple[str, int], tuple[int, int]]
) -> tuple[int, int]:
    matches = rows = 0
    for row in _pipe_rows(path, 7):
        rows += 1
        condition = row[0]
        try:
            year = _required_integer(row[1])
            numerator = _required_integer(row[2])
            prevalence = _required_float(row[3])
        except ValueError:
            continue
        summed = community_aggregates.get((condition, year))
        if summed is None:
            continue
        summed_numerator, summed_denominator = summed
        expected = summed_numerator / summed_denominator if summed_denominator > 0 else 0.0
        if numerator == summed_numerator and math.isclose(
            prevalence, expected, rel_tol=0.0, abs_tol=1e-12
        ):
            matches += 1
    return matches, rows


def audit_first_party_snapshot(root: Path) -> RawDataAudit:
    """Run aggregate-only, deterministic gates against the frozen first-party snapshot."""

    root = root.resolve()
    contract = load_study_data_contract(root)
    fact_results: list[FactAudit] = []
    community_aggregates: dict[tuple[str, int], tuple[int, int]] = {}
    for table in (
        "fact_tract_condition_stats.text",
        "fact_community_area_condition_stats.text",
        "fact_zcta_condition_stats.text",
    ):
        result, aggregates = _fact_audit(root / ORIGINAL / table)
        fact_results.append(result)
        if table == "fact_community_area_condition_stats.text":
            community_aggregates = aggregates

    chicago_matches, chicago_rows = _chicago_rollup_matches(
        root / ORIGINAL / "fact_chicago_condition_prevalence.text", community_aggregates
    )
    outside = _tract_scope_audit(root)
    geometry_results = (
        _geometry_audit(root / ORIGINAL / "dim_census_tracts.text", 20, 19),
        _geometry_audit(root / ORIGINAL / "dim_community_areas.text", 17, 16),
        _geometry_audit(root / ORIGINAL / "dim_zcta.text", 16, 15),
    )
    tract = fact_results[0]
    primary_passed = all(
        (
            tract.rows == 342273,
            tract.years == (2019, 2020, 2021, 2022, 2023, 2024),
            tract.conditions == 39,
            tract.duplicate_keys == 0,
            tract.invalid_numeric_rows == 0,
            tract.negative_count_rows == 0,
            tract.numerator_greater_than_denominator_rows == 0,
            tract.prevalence_outside_unit_interval_rows == 0,
            tract.positive_numerator_below_10_rows == 0,
            tract.varying_denominator_geography_years == 0,
            tract.published_measure_ratio_mismatch_rows == 0,
            outside[2] == 0,
            outside[3] == 0,
            all(
                item.duplicate_keys == 0
                and item.missing_geometry_rows == 0
                and item.invalid_geometry_rows == 0
                for item in geometry_results
            ),
        )
    )
    unresolved = tuple(str(item) for item in contract["fail_closed_semantics"].keys())
    return RawDataAudit(
        contract_version=int(contract["contract_version"]),
        primary_tract_contract_passed=primary_passed,
        higher_geography_estimand_authorized=False,
        chicago_rollup_exact_matches=chicago_matches,
        chicago_rollup_rows=chicago_rows,
        outside_six_county_tracts=outside[0],
        outside_six_county_rows=outside[1],
        outside_six_county_positive_numerator_rows=outside[2],
        outside_six_county_positive_denominator_rows=outside[3],
        fact_audits=tuple(fact_results),
        geometry_audits=geometry_results,
        unresolved_signoff_items=unresolved,
    )


def assert_primary_tract_contract(root: Path) -> RawDataAudit:
    """Fail closed if the frozen tract facts drift from the verified primary contract."""

    audit = audit_first_party_snapshot(root)
    if not audit.primary_tract_contract_passed:
        raise AnalyticDatasetError("primary tract raw-data contract failed")
    return audit


def audit_json(root: Path) -> str:
    """Return stable formatted JSON for review or command-line use."""

    return json.dumps(audit_first_party_snapshot(root).to_jsonable(), indent=2, sort_keys=True)
