"""单元测试"""

import logging

import pytest

from biorange.core.logger import LogManager


class TestLogManager:
    """日志系统初始化测试"""
    

    @pytest.fixture(autouse=True)
    def setup(self):
        """在每个测试用例之前运行的设置方法。"""
        self.log_manager = LogManager()

    def test_log_manager_get_logger(self):
        """测试LogManager的get_logger方法是否返回正确的logger对象。"""
        logger1 = self.log_manager.get_logger("test_module1")
        logger2 = self.log_manager.get_logger("test_module2")

        assert logger1 is not None
        assert logger2 is not None
        assert logger1 != logger2

    def test_log_manager_singleton(self):
        """测试LogManager是否为单例模式。"""
        log_manager2 = LogManager()

        assert self.log_manager is log_manager2

    def test_logger_name(self):
        """测试获取的logger名称是否正确。"""
        logger = self.log_manager.get_logger("test_module")

        assert logger.name == "test_module"

    def test_multiple_loggers(self):
        """测试多次获取相同名称的logger是否返回同一个对象。"""
        logger1 = self.log_manager.get_logger("test_module")
        logger2 = self.log_manager.get_logger("test_module")

        assert logger1 is logger2


class TestLoggingOutput:
    """日志输出测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """在每个测试用例之前运行的设置方法。"""
        self.log_manager = LogManager()

    def test_logging_output_with_different_levels(self, caplog):
        """测试不同日志级别的输出。"""
        logger = self.log_manager.get_logger(__name__)
        logger.setLevel(logging.INFO)  # 确保日志级别为 INFO

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        assert "Debug message" not in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text

    def test_logging_with_exception(self, caplog):
        """测试异常日志记录。"""
        logger = self.log_manager.get_logger(__name__)
        logger.setLevel(logging.INFO)  # 确保日志级别为 INFO

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")

        assert "An error occurred" in caplog.text
        assert "ValueError: Test exception" in caplog.text

    def test_logging_with_formatting(self, caplog):
        """测试带有格式化的日志记录。"""
        logger = self.log_manager.get_logger(__name__)
        logger.setLevel(logging.INFO)  # 确保日志级别为 INFO

        user_name = "Alice"
        user_id = 456
        logger.info("User %s (ID: %d) logged in", user_name, user_id)

        assert "User Alice (ID: 456) logged in" in caplog.text

    def test_logging_with_custom_level(self, caplog):
        """测试自定义日志级别。"""
        logger = self.log_manager.get_logger(__name__)
        logger.setLevel(logging.INFO)  # 确保日志级别为 INFO

        custom_level = 25
        logging.addLevelName(custom_level, "CUSTOM")
        logger.log(custom_level, "Custom level message")

        assert "Custom level message" in caplog.text

    def test_log_manager_initialization(self):
        """测试LogManager初始化是否成功。"""
        logger = self.log_manager.get_logger(__name__)
        assert logger is not None

    def test_logging_output(self, caplog):
        """测试日志输出是否正确。"""
        logger = self.log_manager.get_logger(__name__)
        logger.setLevel(logging.INFO)  # 确保日志级别为 INFO
        logger.info("Test log message")

        assert "Test log message" in caplog.text
