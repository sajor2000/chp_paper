from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.config import PROJECT_ROOT_ENV
from chicagohealthmap.governance.s4_dictionary import build_s4_dictionary_packet


ROOT = Path(__file__).parents[2]


def _copy_s4_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "fixture"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
    for relative in [
        "config/first_party_schemas.yml",
        "sources/literature/web/snapshots/2026-07-14/chicagohealthmap_data_glossary.json",
    ]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def test_s4_dictionary_packet_treats_website_glossary_as_authoritative() -> None:
    packet = build_s4_dictionary_packet(ROOT)

    assert packet.status == "website_dictionary_authoritative"
    assert packet.authority["url"] == "https://chicagohealthmap.com/data-glossary"
    assert packet.authority["decision"] == "accepted_for_s4_methods_dictionary"
    assert set(packet.concepts) == {
        "capture_rate",
        "capture_rate_metric",
        "geography",
        "small_cell_suppression",
        "standardized_mean_difference",
    }
    assert packet.candidate_mappings["geography"]["candidate_tables"]
    assert (
        "fact_tract_condition_stats.text"
        in packet.candidate_mappings["geography"]["candidate_tables"]
    )
    assert packet.analysis_authorized is False


def test_s4_dictionary_packet_records_city_of_chicago_case_study_frame() -> None:
    packet = build_s4_dictionary_packet(ROOT)

    assert packet.source_scope["geographic_scope"] == "six-county Chicagoland"
    assert packet.case_study_spatial_frame == {
        "frame": "City of Chicago",
        "primary_geography": "census tract",
        "secondary_geography": "Chicago community area",
        "rule": (
            "Restrict case-study analytic shapefiles and mapped outputs to City of Chicago "
            "geographies while preserving six-county source provenance."
        ),
    }


def test_s4_dictionary_packet_records_defensible_position_mapping() -> None:
    packet = build_s4_dictionary_packet(ROOT)

    mappings = packet.position_mappings
    assert mappings["geography"]["status"] == "accepted_for_case_study_mapping"
    assert mappings["geography"]["positions"]["fact_tract_condition_stats.text"] == {
        "position_02": "census_tract_geography_key"
    }
    assert mappings["geography"]["positions"]["fact_zcta_condition_stats.text"] == {
        "position_02": "zcta_geography_key"
    }
    assert mappings["geography"]["positions"]["dim_zcta.text"] == {
        "position_01": "zcta_geography_key",
        "position_15": "zcta_geometry_ewkb",
    }
    assert mappings["geography"]["positions"]["dim_zcta_reliability_crosswalk.text"] == {
        "position_01": "zcta_geography_key"
    }
    assert mappings["time_period"]["positions"]["fact_tract_condition_stats.text"] == {
        "position_03": "year"
    }
    assert mappings["phenotype"]["positions"]["fact_tract_condition_stats.text"] == {
        "position_04": "condition"
    }
    assert mappings["numerator"]["positions"]["fact_tract_condition_stats.text"] == {
        "position_05": "overall_diagnosed_condition_count",
        "position_range_06_24": "subgroup_count_block_guarded",
    }
    assert mappings["denominator"]["positions"]["fact_tract_condition_stats.text"] == {
        "position_25": "overall_denominator_candidate_guarded",
        "position_range_26_44": "subgroup_denominator_block_guarded",
    }
    assert mappings["capture_rate"]["positions"]["dim_tract_reliability_crosswalk.text"] == {
        "position_02": "capture_rate"
    }
    assert mappings["denominator"]["status"] == "methods_semantics_accepted_positions_guarded"
    assert (
        mappings["small_cell_suppression"]["status"] == "methods_semantics_accepted_display_guarded"
    )
    assert "standardized_mean_difference" not in mappings


def test_s4_dictionary_packet_cli_writes_json(tmp_path: Path, monkeypatch) -> None:
    root = _copy_s4_fixture(tmp_path)
    monkeypatch.setenv(PROJECT_ROOT_ENV, str(root))
    output = root / "docs/analysis/s4_methods_mapping.json"

    result = CliRunner().invoke(
        app, ["governance", "s4-dictionary", "build", "--output", str(output)]
    )

    assert result.exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "website_dictionary_authoritative"
    assert payload["case_study_spatial_frame"]["frame"] == "City of Chicago"
    assert payload["position_mappings"]["capture_rate"]["positions"][
        "dim_tract_reliability_crosswalk.text"
    ] == {"position_02": "capture_rate"}
    assert payload["candidate_mappings"]["small_cell_suppression"]["dictionary_support"] == "direct"
    assert json.loads(result.stdout)["output_path"].endswith(
        "docs/analysis/s4_methods_mapping.json"
    )
