"""
测试文件：test_config_manager.py

该测试文件使用 Pytest 框架对 ConfigManager 和 ConfigLoader 类进行单元测试。

测试目标：
1. 验证 ConfigManager 的默认配置是否正确加载。
2. 验证 ConfigManager 能否正确加载命令行参数。
3. 验证 ConfigManager 能否正确加载配置文件confg.yaml 中的配置。
4. 验证 ConfigLoader 能否正确加载 .env 文件中的环境变量。
5. 验证 ConfigLoader 能否在 .env 文件不存在时正确加载当前环境变量。

业务代码传参逻辑：
1. ConfigLoader 类：
   - 初始化参数：
     - env_file：指定 .env 文件的路径，默认为 .env。
     - config_file：指定 YAML 配置文件的路径，默认为 config.yaml。
   - 方法：
     - load_env_vars：加载环境变量，优先从指定的 .env 文件中加载，如果文件不存在，则从当前环境中加载。
     - load_config_file：加载 YAML 配置文件中的变量，返回包含配置文件中 settings 部分的字典。

2. ConfigManager 类：
   - 初始化参数：
     - cli_args：命令行参数的字典，默认为空字典。
     - config_loader：ConfigLoader 实例，用于加载配置文件和环境变量。
   - 方法：
     - _validate_settings：合并默认配置、配置文件、环境变量和命令行参数，并验证配置的有效性。
     - _defaults：返回默认配置的字典。
     - get：获取指定配置参数的值。

测试用例：
1. test_config_manager_defaults：验证 ConfigManager 的默认配置是否正确加载。
2. test_config_manager_with_cli_args：验证 ConfigManager 能否正确加载命令行参数。
3. test_config_manager_with_config_file：验证 ConfigManager 能否正确加载配置文件中的配置。
4. test_load_env_vars_with_env_file：验证 ConfigLoader 能否正确加载 .env 文件中的环境变量。
5. test_load_env_vars_without_env_file：验证 ConfigLoader 能否在 .env 文件不存在时正确加载当前环境变量。
"""

import pytest

from biorange.core.config.config_loader import ConfigLoader
from biorange.core.config.config_manager import ConfigManager


@pytest.fixture
def empty_config_files(tmp_path):
    """创建空的 .env 和 config.yaml 文件"""
    env_file = tmp_path / ".env"
    config_file = tmp_path / "config.yaml"
    env_file.write_text("")
    config_file.write_text("settings: {}")
    return env_file, config_file


@pytest.fixture
def populated_config_files(tmp_path):
    """创建带有内容的 .env 和 config.yaml 文件"""
    env_file = tmp_path / ".env"
    config_file = tmp_path / "config.yaml"
    env_file.write_text("API_KEY=your_api_key\nAPI_URL=https://api.example.com\n")
    config_file.write_text(
        """
        settings:
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
    assert config_manager.settings.api.key == "default_api_key"
    assert config_manager.settings.api.url == "https://api.default.com"
    assert config_manager.settings.database.url == "default_database_url"
    assert config_manager.settings.database.pool_size == 5


def test_config_manager_with_cli_args(empty_config_files):
    """验证 ConfigManager 能否正确加载命令行参数"""
    env_file, config_file = empty_config_files
    cli_args = {
        "api": {"key": "cli_api_key", "url": "cli_api_url"},
        "database": {"url": "cli_database_url", "pool_size": 20},
    }
    config_loader = ConfigLoader(env_file=str(env_file), config_file=str(config_file))
    config_manager = ConfigManager(cli_args=cli_args, config_loader=config_loader)
    assert config_manager.settings.api.key == "cli_api_key"
    assert config_manager.settings.api.url == "cli_api_url"
    assert config_manager.settings.database.url == "cli_database_url"
    assert config_manager.settings.database.pool_size == 20


def test_config_manager_with_config_file(populated_config_files):
    """验证 ConfigManager 能否正确加载配置文件中的配置"""
    env_file, config_file = populated_config_files
    config_loader = ConfigLoader(config_file=str(config_file))
    config_manager = ConfigManager(config_loader=config_loader)
    assert config_manager.settings.api.key == "your_api_key"
    assert config_manager.settings.api.url == "https://api.example.com"
    assert (
        config_manager.settings.database.url
        == "postgresql://user:password@localhost/dbname"
    )
    assert config_manager.settings.database.pool_size == 10


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
