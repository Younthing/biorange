# biorange/core/logger/__init__.py

"""导入时就初始化日志配置"""

from pathlib import Path

from .logging_config import LogManager

# 定义日志目录
logs_dir = Path(".logs")
logs_dir.mkdir(parents=True, exist_ok=True)

# 初始化日志配置
log_manager = LogManager()

# 提供一个全局的 get_logger 函数
get_logger = log_manager.get_logger
