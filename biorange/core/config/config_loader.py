"""
该模块提供了一个 `ConfigLoader` 类，用于加载环境变量和 YAML 配置文件。

模块依赖:
    - os: 用于检查文件路径。
    - yaml: 用于解析 YAML 文件。
    - dotenv: 用于加载 .env 文件中的环境变量。

类:
    ConfigLoader: 配置加载器类，提供加载环境变量和 YAML 配置文件的方法。
"""

import os
from typing import Optional

import yaml
from dotenv import load_dotenv


class ConfigLoader:
    """配置加载器
    Attributes:
        env_file (str): .env 文件的路径，默认为 ".env"。
        config_file (str): YAML 配置文件的路径，默认为 "config.yaml"。

    Methods:
        load_env_vars: 加载环境变量。
        load_config_file: 加载 YAML 配置文件中的变量。
    """

    def __init__(
        self,
        env_file: Optional[str] = None,
        config_file: Optional[str] = None,
    ):
        self.env_file = env_file or ".env"
        self.config_file = config_file or "config.yaml"

    def load_env_vars(self) -> dict[str, str | None]:
        """加载环境变量。

        从指定的 .env 文件中加载环境变量，并返回一个包含所有环境变量的字典。

        Returns:
            dict[str, str | None]: 包含所有环境变量的字典，键为变量名，值为变量值或 None。

        Note:
            如果 .env 文件不存在，则只返回当前环境中的变量。
        """
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
        return {key: os.getenv(key) for key in os.environ}

    def load_config_file(self) -> dict[str, str]:
        """加载 YAML 配置文件中的变量。

        Returns:
            dict[str, str]: 包含配置文件中 'settings' 部分的字典。如果文件不存在或读取出错，返回空字典。

        Raises:
            yaml.YAMLError: 如果 YAML 文件格式不正确。
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "rt", encoding="utf-8") as file:
                    config = yaml.safe_load(file) or {}
                    return config
            else:
                return {}
        except yaml.YAMLError as e:
            print(f"读取配置文件 {self.config_file} 时出错: {e}")
            return {}
