import pytest

from biorange.core.config.config_loader import ConfigLoader
from biorange.core.config.config_manager import ConfigManager


@pytest.fixture
def empty_config_files(tmp_path):
    """创建空的 .env 和 config.yaml 文件"""
    env_file = tmp_path / ".env"
    config_file = tmp_path / "config.yaml"
    env_file.write_text("")
    config_file.write_text("{}")
    return env_file, config_file


@pytest.fixture
def populated_config_files(tmp_path):
    """创建带有内容的 .env 和 config.yaml 文件"""
    env_file = tmp_path / ".env"
    config_file = tmp_path / "config.yaml"
    env_file.write_text("API_KEY=your_api_key\nAPI_URL=https://api.example.com\n")
    config_file.write_text(
        """
        api:
            key: "your_api_key"
            url: "https://api.example.com"
        database:
            url: "postgresql://user:password@localhost/dbname"
            pool_size: 10
        """
    )
    return env_file, config_file


def test_config_manager_defaults(empty_config_files):
    """验证 ConfigManager 的默认配置是否正确加载"""
    env_file, config_file = empty_config_files
    config_loader = ConfigLoader(env_file=str(env_file), config_file=str(config_file))
    config_manager = ConfigManager(config_loader=config_loader)
    assert config_manager.get("api.key") == "default_api_key"
    assert config_manager.get("api.url") == "https://api.default.com"
    assert config_manager.get("database.url") == "default_database_url"
    assert config_manager.get("database.pool_size") == 5


def test_config_manager_with_cli_args(empty_config_files):
    """验证 ConfigManager 能否正确加载命令行参数"""
    env_file, config_file = empty_config_files
    cli_args = {
        "api": {"key": "cli_api_key", "url": "cli_api_url"},
        "database": {"url": "cli_database_url", "pool_size": 20},
    }
    config_loader = ConfigLoader(env_file=str(env_file), config_file=str(config_file))
    config_manager = ConfigManager(cli_args=cli_args, config_loader=config_loader)
    assert config_manager.get("api.key") == "cli_api_key"
    assert config_manager.get("api.url") == "cli_api_url"
    assert config_manager.get("database.url") == "cli_database_url"
    assert config_manager.get("database.pool_size") == 20


def test_config_manager_with_config_file(populated_config_files):
    """验证 ConfigManager 能否正确加载配置文件中的配置"""
    env_file, config_file = populated_config_files
    config_loader = ConfigLoader(config_file=str(config_file))
    config_manager = ConfigManager(config_loader=config_loader)
    assert config_manager.get("api.key") == "your_api_key"
    assert config_manager.get("api.url") == "https://api.example.com"
    assert (
        config_manager.get("database.url")
        == "postgresql://user:password@localhost/dbname"
    )
    assert config_manager.get("database.pool_size") == 10


def test_load_env_vars_with_env_file(populated_config_files, monkeypatch):
    """验证 ConfigLoader 能否正确加载 .env 文件中的环境变量"""
    env_file, config_file = populated_config_files

    monkeypatch.setenv("DATABASE_URL", "env_database_url")
    monkeypatch.setenv("POOL_SIZE", "15")

    config_loader = ConfigLoader(env_file=str(env_file))
    env_vars = config_loader.load_env_vars()

    assert env_vars["API_KEY"] == "your_api_key"
    assert env_vars["API_URL"] == "https://api.example.com"
    assert env_vars["DATABASE_URL"] == "env_database_url"
    assert env_vars["POOL_SIZE"] == "15"


def test_load_env_vars_without_env_file(monkeypatch):
    """验证 ConfigLoader 能否在 .env 文件不存在时正确加载当前环境变量"""
    monkeypatch.setenv("API_KEY", "env_api_key")
    monkeypatch.setenv("API_URL", "env_api_url")
    monkeypatch.setenv("DATABASE_URL", "env_database_url")
    monkeypatch.setenv("POOL_SIZE", "15")

    config_loader = ConfigLoader(env_file="non_existent.env")
    env_vars = config_loader.load_env_vars()

    assert env_vars["API_KEY"] == "env_api_key"
    assert env_vars["API_URL"] == "env_api_url"
    assert env_vars["DATABASE_URL"] == "env_database_url"
    assert env_vars["POOL_SIZE"] == "15"
