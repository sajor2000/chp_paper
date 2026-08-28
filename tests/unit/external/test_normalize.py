import json
from pathlib import Path

import pandas as pd
import pytest

from chicagohealthmap.external.normalize import (
    NormalizationError,
    normalize_acs,
    normalize_atlas,
    normalize_first_party,
    normalize_places,
    write_normalized_table,
)
from chicagohealthmap.cli import app
from typer.testing import CliRunner


PROVENANCE = {
    "source_id": "cdc_places_current_tract",
    "snapshot_id": "cdc_places_current_tract_2026-07-13",
    "release_vintage": "2025",
}


def test_places_preserves_model_based_estimand_and_required_provenance() -> None:
    raw = pd.DataFrame(
        {
            "tractfips": ["17031010100"],
            "bphigh_crudeprev": [31.2],
            "bphigh_crude95ci": ["(28.0, 34.5)"],
        }
    )

    result = normalize_places(raw, **PROVENANCE)

    assert result.loc[0, "measure_type"] == "model_based_estimate"
    assert result.loc[0, "measure_id"] == "bphigh_crudeprev"
    assert result.loc[0, "model_based_estimate"] == 31.2
    assert result.loc[0, "geography_id"] == "17031010100"
    assert result.loc[0, "source_field_map"] == {
        "measure_id": "bphigh_crudeprev",
        "measure_type": "bphigh_crudeprev",
        "model_based_estimate": "bphigh_crudeprev",
        "confidence_interval": "bphigh_crude95ci",
    }
    assert "prevalence" not in result.columns
    assert {
        "source_id",
        "snapshot_id",
        "source_record_id",
        "source_field_map",
        "release_vintage",
        "geography_type",
        "geography_id",
        "time_period",
    } <= set(result.columns)


def test_acs_keeps_estimate_and_moe_as_a_pair() -> None:
    raw = pd.DataFrame(
        {"GEO_ID": ["1400000US17031010100"], "B19013_E001": [72100], "B19013_M001": [2100]}
    )

    result = normalize_acs(
        raw,
        source_id="census_acs_2024_5y",
        snapshot_id="census_acs_2024_5y_2026-07-13",
        release_vintage="2024 ACS 5-year",
        time_period="2020-2024",
    )

    assert result.loc[0, ["estimate", "margin_of_error"]].tolist() == [72100, 2100]
    assert result.loc[0, "source_field_map"] == {
        "variable_id": "B19013_E001",
        "estimate": "B19013_E001",
        "estimate_state": "B19013_E001",
        "margin_of_error": "B19013_M001",
        "margin_of_error_state": "B19013_M001",
    }
    assert "prevalence" not in result.columns


def test_numeric_normalizers_reject_malformed_source_values() -> None:
    with pytest.raises(NormalizationError, match="bphigh_crudeprev.*malformed"):
        normalize_places(
            pd.DataFrame(
                {
                    "tractfips": ["17031010100"],
                    "bphigh_crudeprev": ["not-a-number"],
                    "bphigh_crude95ci": ["(28.0, 34.5)"],
                }
            ),
            **PROVENANCE,
        )


def test_acs_documented_sentinels_are_states_not_measurements() -> None:
    raw = pd.DataFrame(
        {
            "GEO_ID": [
                "1400000US17031010100",
                "1400000US17031010200",
                "1400000US17031010300",
            ],
            "B19013_E001": ["-666666666", "-333333333", "-222222222"],
            "B19013_M001": ["-666666666", "1200", "1300"],
        }
    )
    result = normalize_acs(
        raw,
        source_id="census_acs_2024_5y",
        snapshot_id="census_acs_2024_5y_2026-07-13",
        release_vintage="2024 ACS 5-year",
        time_period="2020-2024",
    )
    assert result["estimate"].isna().all()
    assert result["estimate_state"].tolist() == [
        "unavailable",
        "median_below_lower_bound",
        "median_above_upper_bound",
    ]
    assert pd.isna(result.loc[0, "margin_of_error"])
    assert result.loc[0, "margin_of_error_state"] == "unavailable"


def test_frozen_svi_missing_sentinels_are_not_published_as_ranks() -> None:
    from chicagohealthmap.config import ProjectPaths
    from chicagohealthmap.external.normalize import _svi_table

    result = _svi_table(ProjectPaths.discover())
    assert -999 not in set(result["svi_percentile_rank"].dropna())
    missing = result.loc[result["geography_id"] == "17031980000"]
    assert not missing.empty
    assert missing["svi_percentile_rank"].isna().all()
    assert set(missing["svi_percentile_rank_state"]) == {"not_available"}
    with pytest.raises(NormalizationError, match="B19013_M001.*malformed"):
        normalize_acs(
            pd.DataFrame(
                {
                    "GEO_ID": ["1400000US17031010100"],
                    "B19013_E001": [72100],
                    "B19013_M001": ["bad-moe"],
                }
            ),
            source_id="census_acs_2024_5y",
            snapshot_id="census_acs_2024_5y_2026-07-13",
            release_vintage="2024 ACS 5-year",
            time_period="2020-2024",
        )
    with pytest.raises(NormalizationError, match="bphigh_crude95ci.*malformed"):
        normalize_places(
            pd.DataFrame(
                {
                    "tractfips": ["17031010100"],
                    "bphigh_crudeprev": [31.2],
                    "bphigh_crude95ci": ["not-an-interval"],
                }
            ),
            **PROVENANCE,
        )


def test_atlas_retains_exact_published_indicator_label() -> None:
    result = normalize_atlas(
        [
            {
                "g": "1714000-14",
                "l": "neighborhood",
                "a": "VRLE",
                "p": "",
                "d": "2024",
                "v": 81.5,
                "se": None,
            }
        ],
        source_id="chicago_health_atlas_life_expectancy",
        snapshot_id="chicago_health_atlas_life_expectancy_2026-07-13",
        release_vintage="frozen 2026-07-13",
        indicator_label="Life expectancy",
    )

    assert result.loc[0, "indicator_label"] == "Life expectancy"
    assert result.loc[0, "indicator_id"] == "VRLE"
    assert result.loc[0, "estimate"] == 81.5
    assert "prevalence" not in result.columns


def test_normalized_parquet_has_companion_schema_metadata(tmp_path: Path) -> None:
    table = normalize_places(
        pd.DataFrame(
            {
                "tractfips": ["17031010100"],
                "copd_crudeprev": [7.2],
                "copd_crude95ci": ["(6.1, 8.4)"],
            }
        ),
        **PROVENANCE,
    )

    parquet = write_normalized_table(table, tmp_path / "places.parquet")

    metadata = json.loads(parquet.with_suffix(".schema.json").read_text())
    assert metadata["row_count"] == 1
    assert metadata["columns"]["source_field_map"] == "json"
    assert pd.read_parquet(parquet).loc[0, "measure_type"] == "model_based_estimate"


def test_normalized_table_rejects_invented_or_missing_input_field_lineage(tmp_path: Path) -> None:
    table = pd.DataFrame(
        {
            "source_id": ["source"],
            "snapshot_id": ["source_2026-07-13"],
            "source_record_id": ["record"],
            "source_field_map": [{}],
            "release_vintage": ["release"],
            "geography_type": ["tract"],
            "geography_id": ["17031010100"],
            "time_period": ["2024"],
            "estimate": [1.0],
        }
    )
    with pytest.raises(NormalizationError, match="source_field_map.*estimate"):
        write_normalized_table(table, tmp_path / "invalid.parquet")


def test_glossary_cannot_promote_unverified_first_party_positions(tmp_path: Path) -> None:
    source = tmp_path / "fact_tract_condition_stats.text"
    source.write_text("secret,row,that,must,not,be,read\n")

    with pytest.raises(NormalizationError, match="Gate 3 closed.*549"):
        normalize_first_party(source, glossary_path=tmp_path / "data-glossary.md")


def test_cli_exposes_offline_normalization_and_provenance_commands() -> None:
    runner = CliRunner()
    external = runner.invoke(app, ["external", "normalize", "--help"])
    provenance = runner.invoke(app, ["provenance", "build", "--help"])
    verify = runner.invoke(app, ["provenance", "verify", "--help"])
    citations = runner.invoke(app, ["sources", "citations", "--help"])
    assert (
        external.exit_code == provenance.exit_code == verify.exit_code == citations.exit_code == 0
    )
    assert "--all" in external.output
    assert "--all" in provenance.output
    assert "--all" in verify.output
    assert "--format" in citations.output
