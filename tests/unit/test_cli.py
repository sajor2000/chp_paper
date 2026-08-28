from typer.testing import CliRunner

from chicagohealthmap.cli import app


def test_cli_reports_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "chicagohealthmap 0.1.0"
