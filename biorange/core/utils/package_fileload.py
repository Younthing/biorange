from importlib import resources

from biorange.core.logger import get_logger

logger = get_logger(__name__)


def get_data_file_path(filename):
    """
    获取数据文件的路径。

    Args:
        filename (str): 要获取路径的文件名。

    Returns:
        pathlib.Path: 数据文件的完整路径。

    Raises:
        FileNotFoundError: 如果指定的文件不存在。
    """
    with resources.path("biorange.data", filename) as path:
        return path


import os
from shutil import copyfile


def copy_config_if_not_exists(target_dir=".", filename="config.yaml"):
    """
    如果目标目录不存在指定文件，则从包内复制该文件。

    Args:
        target_dir (str): 目标目录路径，默认为当前目录。
        filename (str): 要复制的文件名。
    """
    target_file = os.path.join(target_dir, filename)
    if not os.path.exists(target_file):
        logger.warning(f"未找到 {filename}，新建默认配置config.yaml...")
        with resources.path("biorange.data", filename) as path:
            copyfile(path, target_file)
            logger.info(f"{filename} 配置成功")
