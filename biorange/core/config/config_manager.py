"""
config_manager.py

该模块定义了用于管理应用程序配置的类和方法。

Classes:
    Settings: 定义了应用程序的配置参数。
    ConfigManager: 用于管理应用程序的配置参数，从命令行参数、配置文件和环境变量中加载配置，并验证配置的有效性。

Usage:
    from config_manager import ConfigManager

    config_manager = ConfigManager(cli_args={"api_key": "my_api_key"})
    api_key = config_manager.get("api_key")
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field, ValidationError

from biorange.core.config.config_loader import ConfigLoader


class Settings(BaseModel):
    """
    Settings 类定义了应用程序的配置参数。

    Args:
        api_key (str): API 密钥。默认值为 "default_api_key"。
        database_url (str): 数据库 URL。默认值为 "default_database_url"。
    """

    api_key: str = Field("default_api_key", description="API 密钥")
    database_url: str = Field("default_database_url", description="数据库 URL")


class ConfigManager:
    """
    ConfigManager 类用于管理应用程序的配置参数。

    该类从命令行参数、配置文件和环境变量中加载配置，并验证配置的有效性。

    Args:
        cli_args (Optional[Dict[str, str]]): 命令行参数，默认为 None。
        config_loader (Optional[ConfigLoader]): 配置加载器实例，默认为 None。

    Attributes:
        cli_args (Dict[str, str]): 命令行参数。
        config_loader (ConfigLoader): 配置加载器实例。
        config_file_values (Dict[str, str]): 从配置文件中加载的配置参数。
        env_values (Dict[str, str]): 从环境变量中加载的配置参数。
        settings (Settings): 验证后的配置参数实例。
    """

    def __init__(
        self,
        cli_args: Optional[Dict[str, str]] = None,
        config_loader: Optional[ConfigLoader] = None,
    ):
        self.cli_args = cli_args or {}
        self.config_loader = config_loader or ConfigLoader()

        self.config_file_values = self.config_loader.load_config_file()
        self.env_values = self.config_loader.load_env_vars()

        self.settings = self._validate_settings()

    def _validate_settings(self) -> Settings:
        """
        验证并合并配置参数。

        Returns:
            Settings: 验证后的配置参数实例。

        Raises:
            ValidationError: 如果配置参数验证失败。
        """
        config = {
            **self._defaults(),
            **self.config_file_values,
            **self.env_values,
            **self.cli_args,
        }
        try:
            return Settings(**config)
        except ValidationError as e:
            print("配置验证错误:", e)
            return Settings(**self._defaults())

    def _defaults(self) -> Dict[str, str]:
        """
        获取配置参数的默认值。

        Returns:
            Dict[str, str]: 配置参数的默认值字典。
        """
        return {key: field.default for key, field in Settings.model_fields.items()}

    def get(self, key: str) -> str:
        """
        获取指定配置参数的值。

        Args:
            key (str): 配置参数的键。

        Returns:
            str: 配置参数的值。如果配置参数不存在，则返回空字符串。
        """
        return getattr(self.settings, key, "")


# 或者，如果你希望返回 None 而不是空字符串，可以这样修改返回类型声明：
# def get(self, key: str) -> Optional[str]:
#     """
#     获取指定配置参数的值。
#
#     Args:
#         key (str): 配置参数的键。
#
#     Returns:
#         Optional[str]: 配置参数的值。如果配置参数不存在，则返回 None。
#     """
#     return getattr(self.settings, key, None)
