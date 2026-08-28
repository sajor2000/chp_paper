from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest
from typer.testing import CliRunner

from chicagohealthmap.cli import app
from chicagohealthmap.pipeline import rebuild_through_phase_4


def _deny_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked_socket(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError("offline rebuild attempted to open a network socket")

    monkeypatch.setattr(socket, "socket", blocked_socket)


def test_offline_rebuild_report_is_deterministic_and_uses_no_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _deny_network(monkeypatch)
    root = Path(__file__).parents[2]

    report = rebuild_through_phase_4(root, offline=True)

    assert report.through_phase == 4
    assert report.offline is True
    assert report.gates["Gate 2"] == "open"
    assert report.gates["Gate 3"] == "closed"
    assert report.gates["Gate 4"] in {"passed", "open", "blocked"}
    assert report.row_counts["source_inventory"] == 15
    assert report.row_counts["chicago_community_areas_current"] == 77
    assert report.row_counts["tract_community_overlay_2020"] > 0
    assert report.provenance_artifacts == (
        "data_source_inventory.csv",
        "data_sources.bib",
        "data_sources.csl.json",
        "table_figure_sources.csv",
        "variable_lineage.csv",
    )
    assert "data/processed/public/source_inventory.schema.json" in report.schema_hashes
    assert "outputs/provenance/data_source_inventory.csv" in report.provenance_hashes


def test_offline_rebuild_rejects_authorizing_network() -> None:
    root = Path(__file__).parents[2]

    with pytest.raises(ValueError, match="offline=False is not authorized"):
        rebuild_through_phase_4(root, offline=False)


def test_rebuild_cli_emits_json_summary_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _deny_network(monkeypatch)
    root = Path(__file__).parents[2]

    result = CliRunner().invoke(
        app,
        ["rebuild", "--through-phase", "4", "--offline", "--root", str(root)],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["through_phase"] == 4
    assert payload["offline"] is True
    assert payload["gates"]["Gate 2"] == "open"
    assert payload["gates"]["Gate 3"] == "closed"
    assert payload["row_counts"]["source_inventory"] == 15
    assert "outputs/provenance/variable_lineage.csv" in payload["provenance_hashes"]
