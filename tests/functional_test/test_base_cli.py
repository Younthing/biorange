from typer.testing import CliRunner

from biorange.cli.main import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "BioRange version:" in result.output


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage: " in result.output


# PPI ANALYSIS
def test_ppi_analysis():
    result = runner.invoke(
        app,
        ["analyze", "ppi"],
    )
    assert "PPI analysis completed." in result.output
