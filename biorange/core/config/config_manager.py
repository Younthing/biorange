"""
config_manager.py

该模块定义了用于管理应用程序配置的类和方法。

Classes:
    Settings: 定义了应用程序的配置参数。
    ConfigManager: 用于管理应用程序的配置参数，从命令行参数、配置文件和环境变量中加载配置，并验证配置的有效性。

Usage:
    from config_manager import ConfigManager

    config_manager = ConfigManager()

    api_key = config_manager.settings.api.key
    api_url = config_manager.settings.api.url
    database_url = config_manager.settings.database.url
    pool_size = config_manager.settings.database.pool_size

"""

from typing import Dict

from pydantic import ValidationError

from biorange.core.config.config_loader import ConfigLoader
from biorange.core.config.config_model import Settings


class ConfigManager:
    """
    ConfigManager类用于管理配置设置，支持从默认值、配置文件、环境变量和命令行参数中加载配置，并根据优先级进行合并。

    配置优先级（从低到高）：
    1. 默认值
    2. 配置文件值
    3. 环境变量值
    4. 命令行参数

    Attributes:
        cli_args (dict[str, str]): 命令行参数字典。
        config_loader (ConfigLoader): 用于加载配置的ConfigLoader实例。
        config_file_values (dict): 从配置文件加载的配置值。
        env_values (dict): 从环境变量加载的配置值。
        settings (Settings): 验证后的最终配置设置。

    Methods:
        get(key: str) -> str:
            获取指定配置键的值。
    """

    def __init__(
        self,
        cli_args: dict[str, str] | None = None,
        config_loader: ConfigLoader | None = None,
    ):
        """
        初始化ConfigManager实例。

        Args:
            cli_args: 命令行参数字典，默认为None。
            config_loader: ConfigLoader实例，默认为None。

        Returns:
            None
        """
        self.cli_args = cli_args or {}
        self.config_loader = config_loader or ConfigLoader()

        self.config_file_values = self.config_loader.load_config_file()
        self.env_values = self.config_loader.load_env_vars()

        self.settings = self._validate_settings()

    def _validate_settings(self) -> Settings:
        """
        验证并合并配置设置。

        将默认设置、配置文件值、环境变量值和命令行参数按优先级顺序合并，并返回验证后的Settings实例。

        Returns:
            Settings: 验证后的配置设置实例。
        """
        config = {
            **self._defaults(),
            **self.config_file_values,
            **self.env_values,
            **self._parse_cli_args(self.cli_args),
        }
        try:
            return Settings(**config)
        except ValidationError as e:
            print("配置验证错误:", e)
            return Settings()

    def _defaults(self) -> Dict[str, str]:
        """
        获取默认配置设置。

        Returns:
            dict[str, str]: 默认配置设置字典。
        """
        return {key: field.default for key, field in Settings.model_fields.items()}

    def _parse_cli_args(self, cli_args: Dict[str, str]) -> Dict[str, str]:
        """
        解析命令行参数中的嵌套键，并将其合并到配置字典中。

        Args:
            cli_args: 命令行参数字典。

        Returns:
            dict[str, str]: 解析后的命令行参数字典。
        """
        parsed = {}
        for key, value in cli_args.items():
            keys = key.split(".")
            d = parsed
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = value
        return parsed

    def get(self, key: str) -> str | Settings:
        """
        获取指定配置键的值。

        Args:
            key: 要获取的配置键。

        Returns:
            str: 指定配置键的值。如果键不存在，返回空字符串。
        """
        keys = key.split(".")
        value = self.settings
        for k in keys:
            value = getattr(value, k, "")
        return value
