"""日志配置管理"""

import logging
import logging.config
import os
from importlib import resources
from threading import Lock

import yaml


class ConfigLoader:
    """负责加载和验证日志配置的类。"""

    @staticmethod
    def load_config(config_path=None):
        """
        从指定路径、环境变量或默认的内部 logging_config.yaml 加载日志配置。

        Args:
            config_path (str, optional): 配置文件的路径。默认为 None。

        Returns:
            dict: 加载的日志配置。

        Raises:
            FileNotFoundError: 如果配置文件未找到。
            ValueError: 如果解析配置文件时出错。
        """
        config_path = config_path or os.getenv("LOGGING_CONFIG_PATH")

        if not config_path:
            try:
                # 使用 files() 方法替代 path() 方法
                default_path = resources.files("biorange.core.logger").joinpath(
                    "logging_config.yaml"
                )
                config_path = str(default_path)
            except FileNotFoundError as exc:
                raise FileNotFoundError("默认的日志配置文件在资源中未找到。") from exc

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"日志配置文件未找到: {config_path}")

        with open(config_path, "rt", encoding="utf-8") as file:
            try:
                config = yaml.safe_load(file)
                ConfigLoader.validate_config(config)
                return config
            except yaml.YAMLError as e:
                raise ValueError(f"解析日志配置文件时出错: {e}") from e

    @staticmethod
    def validate_config(config):
        """
        验证日志配置的正确性。
        """
        if not isinstance(config, dict):
            raise ValueError("日志配置应为字典类型。")
        if "version" not in config:
            raise ValueError("日志配置必须包含 'version' 键。")
        if "handlers" not in config or "loggers" not in config:
            raise ValueError("日志配置必须包含 'handlers' 和 'loggers' 键。")


class LogManager:
    """单例模式的 LogManager 类，用于管理应用程序的日志配置。"""

    _instance = None
    _lock = Lock()  # 确保单例访问的线程安全

    def __new__(cls, config_path=None):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(LogManager, cls).__new__(cls)
                    cls._instance._initialize(config_path)
        return cls._instance

    def _initialize(self, config_path):
        """
        使用提供的配置路径初始化日志配置。
        """
        config = ConfigLoader.load_config(config_path)
        logging.config.dictConfig(config)

    @staticmethod
    def get_logger(name):
        """
        返回具有指定名称的日志记录器。
        """
        return logging.getLogger(name)


# 示例用法
if __name__ == "__main__":
    log_manager = LogManager()
    logger = log_manager.get_logger(__name__)
    logger.info("LogManager 初始化成功。")
