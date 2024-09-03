# tests/test_config_manager.py
from biorange.core.config.config_loader import ConfigLoader
from biorange.core.config.config_manager import ConfigManager


def test_config_manager_defaults():
    config_manager = ConfigManager()
    assert config_manager.get("api_key") == "default_api_key"
    assert config_manager.get("database_url") == "default_database_url"


def test_config_manager_with_cli_args():
    cli_args = {"api_key": "cli_api_key", "database_url": "cli_database_url"}
    config_manager = ConfigManager(cli_args=cli_args)
    assert config_manager.get("api_key") == "cli_api_key"
    assert config_manager.get("database_url") == "cli_database_url"


def test_config_manager_with_env_vars(monkeypatch):
    monkeypatch.setenv("api_key", "env_api_key")
    monkeypatch.setenv("database_url", "env_database_url")
    config_loader = ConfigLoader()
    config_manager = ConfigManager(config_loader=config_loader)
    assert config_manager.get("api_key") == "env_api_key"
    assert config_manager.get("database_url") == "env_database_url"


def test_config_manager_with_config_file(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
    settings:
        api_key: "file_api_key"
        database_url: "file_database_url"
    """
    )
    config_loader = ConfigLoader(config_file=config_file)
    config_manager = ConfigManager(config_loader=config_loader)
    assert config_manager.get("api_key") == "file_api_key"
    assert config_manager.get("database_url") == "file_database_url"
