"""S4 methods dictionary packet using ChicagoHealthMap as first-party authority."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


class S4DictionaryError(ValueError):
    """S4 methods dictionary evidence is missing or invalid."""


@dataclass(frozen=True, slots=True)
class S4DictionaryPacket:
    """Auditable S4 methods dictionary packet."""

    status: str
    analysis_authorized: bool
    authority: dict[str, Any]
    source_scope: dict[str, str]
    case_study_spatial_frame: dict[str, str]
    concepts: dict[str, dict[str, str]]
    candidate_mappings: dict[str, dict[str, Any]]
    position_mappings: dict[str, dict[str, Any]]
    unresolved_requirements: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""

        return asdict(self)


def _safe_file(root: Path, relative_path: str) -> Path:
    path = root / relative_path
    if path.is_symlink():
        raise S4DictionaryError(f"S4 dictionary evidence is a symlink: {relative_path}")
    if not path.is_file():
        raise S4DictionaryError(f"S4 dictionary evidence is missing: {relative_path}")
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError) as error:
        raise S4DictionaryError(
            f"S4 dictionary evidence escapes repository: {relative_path}"
        ) from error
    return path


def _read_json(root: Path, relative_path: str) -> dict[str, Any]:
    try:
        payload = json.loads(_safe_file(root, relative_path).read_text(encoding="utf-8"))
    except JSONDecodeError as error:
        raise S4DictionaryError(
            f"S4 dictionary evidence is invalid JSON: {relative_path}"
        ) from error
    if not isinstance(payload, dict):
        raise S4DictionaryError(f"S4 dictionary evidence must be an object: {relative_path}")
    return payload


def _read_yaml(root: Path, relative_path: str) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(_safe_file(root, relative_path).read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise S4DictionaryError(
            f"S4 dictionary evidence is invalid YAML: {relative_path}"
        ) from error
    if not isinstance(payload, dict):
        raise S4DictionaryError(f"S4 dictionary evidence must be a mapping: {relative_path}")
    return payload


def _concepts(glossary: dict[str, Any]) -> dict[str, dict[str, str]]:
    facts = glossary.get("verified_facts")
    if not isinstance(facts, list) or not facts:
        raise S4DictionaryError("ChicagoHealthMap glossary artifact contains no verified facts")
    concepts: dict[str, dict[str, str]] = {}
    for fact in facts:
        if not isinstance(fact, dict):
            raise S4DictionaryError("ChicagoHealthMap glossary fact is malformed")
        concept = fact.get("concept")
        text = fact.get("fact")
        if not isinstance(concept, str) or not isinstance(text, str) or not concept or not text:
            raise S4DictionaryError("ChicagoHealthMap glossary fact is incomplete")
        concepts[concept] = {"definition": text, "source": "ChicagoHealthMap data glossary"}
    required = {
        "capture_rate",
        "capture_rate_metric",
        "geography",
        "small_cell_suppression",
        "standardized_mean_difference",
    }
    if set(concepts) != required:
        raise S4DictionaryError("ChicagoHealthMap glossary concepts do not match S4 contract")
    return dict(sorted(concepts.items()))


def _table_names(root: Path) -> set[str]:
    catalog = _read_yaml(root, "config/first_party_schemas.yml")
    tables = catalog.get("tables")
    if not isinstance(tables, dict) or not tables:
        raise S4DictionaryError("first-party schema catalog contains no tables")
    return set(tables)


def _require_tables(tables: set[str], names: tuple[str, ...]) -> tuple[str, ...]:
    missing = [name for name in names if name not in tables]
    if missing:
        raise S4DictionaryError("candidate mapping references absent table: " + missing[0])
    return names


def _candidate_mappings(tables: set[str]) -> dict[str, dict[str, Any]]:
    tract_stats = (
        "fact_tract_condition_stats.text",
        "fact_community_area_condition_stats.text",
        "fact_ward_condition_stats.text",
        "fact_zcta_condition_stats.text",
        "fact_congress_condition_stats.text",
    )
    return {
        "capture_rate": {
            "dictionary_support": "direct",
            "candidate_tables": _require_tables(
                tables,
                (
                    "dim_tract_reliability_crosswalk.text",
                    "dim_community_area_reliability_crosswalk.text",
                    "dim_ward_reliability_crosswalk.text",
                    "dim_zcta_reliability_crosswalk.text",
                ),
            ),
            "candidate_positions": "reliability crosswalk positions require generated mapping review",
        },
        "capture_rate_metric": {
            "dictionary_support": "direct",
            "candidate_tables": _require_tables(
                tables,
                (
                    "dim_tract_reliability_crosswalk.text",
                    "dim_census_tracts.text",
                ),
            ),
            "candidate_positions": "health-system patient and ACS adult population positions require mapping review",
        },
        "geography": {
            "dictionary_support": "direct",
            "candidate_tables": _require_tables(
                tables,
                (
                    "dim_census_tracts.text",
                    "fact_tract_condition_stats.text",
                    "dim_tract_reliability_crosswalk.text",
                ),
            ),
            "candidate_positions": {
                "dim_census_tracts.text": ("position_01",),
                "fact_tract_condition_stats.text": ("position_02",),
                "dim_tract_reliability_crosswalk.text": ("position_01",),
            },
        },
        "small_cell_suppression": {
            "dictionary_support": "direct",
            "candidate_tables": _require_tables(tables, tract_stats),
            "candidate_positions": "condition-stat count cells require suppression-state mapping review",
        },
        "standardized_mean_difference": {
            "dictionary_support": "direct",
            "candidate_tables": _require_tables(
                tables,
                (
                    "dim_tract_reliability_crosswalk.text",
                    "dim_community_area_reliability_crosswalk.text",
                    "dim_ward_reliability_crosswalk.text",
                    "dim_zcta_reliability_crosswalk.text",
                ),
            ),
            "candidate_positions": "age, sex, and race/ethnicity SMD positions require mapping review",
        },
    }


def _position_mappings(tables: set[str]) -> dict[str, dict[str, Any]]:
    condition_stat_tables = _require_tables(
        tables,
        (
            "fact_tract_condition_stats.text",
            "fact_community_area_condition_stats.text",
            "fact_ward_condition_stats.text",
            "fact_zcta_condition_stats.text",
            "fact_congress_condition_stats.text",
        ),
    )
    reliability_tables = _require_tables(
        tables,
        (
            "dim_tract_reliability_crosswalk.text",
            "dim_community_area_reliability_crosswalk.text",
            "dim_ward_reliability_crosswalk.text",
            "dim_zcta_reliability_crosswalk.text",
        ),
    )
    geography_positions = {
        "dim_census_tracts.text": {"position_01": "census_tract_geography_key"},
        "dim_community_areas.text": {"position_01": "community_area_geography_key"},
        "dim_zcta.text": {
            "position_01": "zcta_geography_key",
            "position_15": "zcta_geometry_ewkb",
        },
        "dim_tract_reliability_crosswalk.text": {"position_01": "census_tract_geography_key"},
        "dim_community_area_reliability_crosswalk.text": {
            "position_01": "community_area_geography_key"
        },
        "dim_zcta_reliability_crosswalk.text": {"position_01": "zcta_geography_key"},
        "fact_tract_condition_stats.text": {"position_02": "census_tract_geography_key"},
        "fact_community_area_condition_stats.text": {"position_02": "community_area_geography_key"},
        "fact_zcta_condition_stats.text": {"position_02": "zcta_geography_key"},
    }
    return {
        "geography": {
            "status": "accepted_for_case_study_mapping",
            "evidence_basis": (
                "ChicagoHealthMap glossary defines census tract as the primary geography and "
                "community area as the Chicago aggregate geography; source profiles show stable "
                "geography-key positions across dimensions, condition facts, and reliability "
                "crosswalks."
            ),
            "positions": geography_positions,
        },
        "time_period": {
            "status": "accepted_for_case_study_mapping",
            "evidence_basis": (
                "ChicagoHealthMap glossary defines the 2019-2024 reporting period; condition "
                "fact profiles show a stable four-digit year position."
            ),
            "positions": {
                **{table: {"position_03": "year"} for table in condition_stat_tables},
                "fact_chicago_condition_prevalence.text": {"position_02": "year"},
            },
        },
        "phenotype": {
            "status": "accepted_for_case_study_mapping",
            "evidence_basis": (
                "ChicagoHealthMap glossary lists the tracked conditions and ICD-10 phenotype "
                "definitions; condition fact profiles show a stable 39-condition position."
            ),
            "positions": {
                **{table: {"position_04": "condition"} for table in condition_stat_tables},
                "dim_conditions.text": {"position_01": "condition"},
                "fact_chicago_condition_prevalence.text": {"position_01": "condition"},
            },
        },
        "numerator": {
            "status": "accepted_for_case_study_mapping",
            "evidence_basis": (
                "ChicagoHealthMap glossary defines diagnosed condition counts. Source profiles "
                "show integer count blocks; aggregate checks identify position 05 as the total "
                "diagnosed-condition count in condition-stat tables and position 03 in the "
                "Chicago-wide prevalence table."
            ),
            "positions": {
                **{
                    table: {
                        "position_05": "overall_diagnosed_condition_count",
                        "position_range_06_24": "subgroup_count_block_guarded",
                    }
                    for table in condition_stat_tables
                },
                "fact_chicago_condition_prevalence.text": {
                    "position_03": "diagnosed_condition_count"
                },
            },
        },
        "published_measure": {
            "status": "accepted_for_case_study_mapping",
            "evidence_basis": (
                "ChicagoHealthMap glossary describes diagnosis percent/rate display; source "
                "profiles show paired count, denominator-like, and rate/proportion-like blocks. "
                "Downstream labels must preserve source-specific measure wording."
            ),
            "positions": {
                **{
                    table: {
                        "position_45": "overall_published_condition_measure",
                        "position_range_46_64": "subgroup_measure_block_guarded",
                    }
                    for table in condition_stat_tables
                },
                "fact_chicago_condition_prevalence.text": {
                    "position_04": "published_condition_measure"
                },
            },
        },
        "capture_rate": {
            "status": "accepted_for_case_study_mapping",
            "evidence_basis": (
                "ChicagoHealthMap glossary defines capture rate as health-system patients "
                "divided by ACS adult population; reliability crosswalk profiles show a stable "
                "rate-like position immediately after the geography key."
            ),
            "positions": {table: {"position_02": "capture_rate"} for table in reliability_tables},
        },
        "reliability": {
            "status": "label_positions_accepted_description_guarded",
            "evidence_basis": (
                "ChicagoHealthMap glossary defines reliability tiers and equity notes. "
                "Reliability crosswalk profiles show stable label/description positions after "
                "capture rate, but downstream code must retain source text until display labels "
                "are audited."
            ),
            "positions": {
                table: {
                    "position_03": "reliability_tier_or_label",
                    "position_04": "equity_or_alignment_label",
                    "position_05": "combined_reliability_label",
                    "position_06": "public_reliability_description",
                }
                for table in reliability_tables
            },
        },
        "denominator": {
            "status": "methods_semantics_accepted_positions_guarded",
            "evidence_basis": (
                "ChicagoHealthMap glossary defines the ACS adult-population denominator. Source "
                "profiles show a paired denominator-like block, with position 25 as the overall "
                "candidate and positions 26-44 as subgroup candidates. Denominator "
                "reconstruction remains guarded until aggregate denominator semantics are "
                "audited."
            ),
            "positions": {
                table: {
                    "position_25": "overall_denominator_candidate_guarded",
                    "position_range_26_44": "subgroup_denominator_block_guarded",
                }
                for table in condition_stat_tables
            },
        },
        "small_cell_suppression": {
            "status": "methods_semantics_accepted_display_guarded",
            "evidence_basis": (
                "ChicagoHealthMap glossary defines fewer-than-10 suppression and suppressed "
                "values as N/A or <10, not zero. No dedicated raw suppression flag is mapped; "
                "display/output code must apply the glossary rule before public reporting."
            ),
            "positions": {},
        },
    }


def build_s4_dictionary_packet(root: Path) -> S4DictionaryPacket:
    """Build an S4 packet that treats the website glossary as authoritative methods evidence."""

    resolved_root = root.resolve()
    glossary = _read_json(
        resolved_root,
        "sources/literature/web/snapshots/2026-07-14/chicagohealthmap_data_glossary.json",
    )
    if glossary.get("url") != "https://chicagohealthmap.com/data-glossary":
        raise S4DictionaryError("ChicagoHealthMap glossary URL is not authoritative")
    tables = _table_names(resolved_root)
    return S4DictionaryPacket(
        status="website_dictionary_authoritative",
        analysis_authorized=False,
        authority={
            "source_id": glossary["source_id"],
            "title": glossary["title"],
            "url": glossary["url"],
            "access_date": glossary["access_date"],
            "decision": "accepted_for_s4_methods_dictionary",
            "decision_basis": (
                "User instructed Codex to treat the ChicagoHealthMap website data dictionary "
                "as the authoritative S4 methods dictionary."
            ),
        },
        source_scope={
            "clinical_source": "CAPriCORN seven-system diagnosis data",
            "geographic_scope": "six-county Chicagoland",
            "time_period": "2019-2024",
        },
        case_study_spatial_frame={
            "frame": "City of Chicago",
            "primary_geography": "census tract",
            "secondary_geography": "Chicago community area",
            "rule": (
                "Restrict case-study analytic shapefiles and mapped outputs to City of Chicago "
                "geographies while preserving six-county source provenance."
            ),
        },
        concepts=_concepts(glossary),
        candidate_mappings=_candidate_mappings(tables),
        position_mappings=_position_mappings(tables),
        unresolved_requirements=(
            "keep adult-denominator reconstruction guarded unless explicitly audited",
            "audit subgroup count/rate blocks before race/ethnicity-, age-, or sex-stratified analysis",
            "apply fewer-than-10 suppression before public reporting or manuscript tables",
            "keep confirmatory modeling blocked until S6",
        ),
    )


def write_s4_dictionary_packet(root: Path, output: Path) -> Path:
    """Write the S4 methods dictionary packet as deterministic JSON."""

    packet = build_s4_dictionary_packet(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(packet.to_jsonable(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output
