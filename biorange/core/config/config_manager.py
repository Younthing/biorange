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


class APISettings(BaseModel):
    """
    API 设置类，定义了 API 相关的配置参数。

    Args:
        key (str): API 密钥，默认值为 "default_api_key"。
        url (str): API URL，默认值为 "https://api.default.com"。
    """

    key: str = Field("default_api_key", description="API 密钥")
    url: str = Field("https://api.default.com", description="API URL")


class DatabaseSettings(BaseModel):
    """
    数据库设置类，定义了数据库相关的配置参数。

    Args:
        url (str): 数据库 URL，默认值为 "default_database_url"。
        pool_size (int): 数据库连接池大小，默认值为 5。
    """

    url: str = Field("default_database_url", description="数据库 URL")
    pool_size: int = Field(5, description="数据库连接池大小")


class Settings(BaseModel):
    """
    配置设置类，定义了应用程序的各种配置参数。

    Args:
        api (APISettings): API 相关的配置参数。
        database (DatabaseSettings): 数据库相关的配置参数。
    """

    api: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)


class ConfigManager:
    def __init__(
        self, cli_args: dict[str, str] = None, config_loader: ConfigLoader = None
    ):
        self.cli_args = cli_args or {}
        self.config_loader = config_loader or ConfigLoader()

        self.config_file_values = self.config_loader.load_config_file()
        self.env_values = self.config_loader.load_env_vars()

        self.settings = self._validate_settings()

    def _validate_settings(self) -> Settings:
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
            return Settings()  # Settings(**self._defaults())

    def _defaults(self) -> dict[str, str]:
        return {key: field.default for key, field in Settings.model_fields.items()}

    def get(self, key: str) -> str:
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


# # core/business_logic.py 业务函数举例
# from core.config.config_manager import ConfigManager

# def perform_business_logic(config_manager: ConfigManager):
#     api_key = config_manager.settings.api.key
#     api_url = config_manager.settings.api.url
#     database_url = config_manager.settings.database.url
#     pool_size = config_manager.settings.database.pool_size

#     # 业务逻辑
#     print(f"Using API Key: {api_key}")
#     print(f"Connecting to API at: {api_url}")
#     print(f"Connecting to Database at: {database_url} with pool size: {pool_size}")
