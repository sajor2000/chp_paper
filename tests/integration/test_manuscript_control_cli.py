from pathlib import Path
import shutil

from typer.testing import CliRunner

from chicagohealthmap.cli import app


def test_control_plane_initializes_and_fails_closed_before_s7(tmp_path: Path, monkeypatch) -> None:
    root = Path(__file__).resolve().parents[2]
    (tmp_path / "config").mkdir()
    (tmp_path / "docs").mkdir()
    shutil.copytree(root / "config" / "manuscript", tmp_path / "config" / "manuscript")
    shutil.copytree(root / "docs" / "manuscript", tmp_path / "docs" / "manuscript")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='test'\nversion='0'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CHICAGOHEALTHMAP_ROOT", str(tmp_path))
    runner = CliRunner()

    init = runner.invoke(app, ["manuscript", "init"])
    assert init.exit_code == 0
    assert (tmp_path / "outputs/manuscript/control/contract_digest.sha256").is_file()

    packets = runner.invoke(app, ["manuscript", "packets", "--build"])
    assert packets.exit_code == 0
    case_1 = tmp_path / "outputs/manuscript/control/case_1.md"
    assert "PROVISIONAL" in case_1.read_text(encoding="utf-8")

    methods_handoff = runner.invoke(
        app, ["manuscript", "handoff", "--role", "methods_reporting_agent"]
    )
    assert methods_handoff.exit_code == 0
    assert "outputs/manuscript/control/handoffs/methods_reporting_agent.json" in (
        methods_handoff.output
    )

    results_handoff = runner.invoke(app, ["manuscript", "handoff", "--role", "results_agent"])
    assert results_handoff.exit_code == 1
    assert "requires S7" in results_handoff.output

    gates = runner.invoke(app, ["manuscript", "gates", "--check"])
    assert gates.exit_code == 1
    assert "required authority remains blocked" in gates.output

    audit = runner.invoke(app, ["manuscript", "audit", "--control"])
    assert audit.exit_code == 0
    assert '"failures": []' in audit.output
