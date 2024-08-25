from typer.testing import CliRunner
from biorange.__main__ import app

runner = CliRunner()

def test_biorange_prints_helloworld():
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert result.output.strip() == "helloworld"
