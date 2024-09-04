from typer.testing import CliRunner

from biorange.cli.main import app

runner = CliRunner()



def test_run_with_config():
    result = runner.invoke(
        app,
        [
            "run",
            "--config",
            "config.yaml",
            "--api.key",
            "my_api_key",
            "--database.url",
            "my_database_url",
        ],
    )
    assert result.exit_code == 0
    assert "api.key: my_api_key" in result.output
    assert "database.url: my_database_url" in result.output


def test_run_with_env():
    result = runner.invoke(
        app,
        [
            "run",
            "--env",
            ".env",
            "--api.key",
            "my_api_key",
            "--database.url",
            "my_database_url",
        ],
    )
    assert result.exit_code == 0
    assert "api.key: my_api_key" in result.output
    assert "database.url: my_database_url" in result.output


def test_run_with_nested_params():
    result = runner.invoke(
        app,
        [
            "run",
            "--config",
            "config.yaml",
            "--api.key",
            "my_api_key",
            "--database.url",
            "my_database_url",
            "--database.pool_size",
            "10",
        ],
    )
    assert result.exit_code == 0
    assert "api.key: my_api_key" in result.output
    assert "database.url: my_database_url" in result.output
    assert "database.pool_size: 10" in result.output
