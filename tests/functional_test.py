from typer.testing import CliRunner

from biorange.cli.main import app

runner = CliRunner()


## 运行biorange analyz ppi


# PPI ANALYSIS
def test_ppi_analysis():
    result = runner.invoke(
        app,
        ["analyze", "ppi"],
    )
    assert "PPI analysis completed." in result.output
