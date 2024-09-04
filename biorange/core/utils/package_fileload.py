from importlib import resources


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
