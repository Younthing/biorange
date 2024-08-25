import pandas as pd


def common_read(file_path):
    """
    从文件中读取单列数据并返回为列表。

    该函数尝试以Excel格式读取文件,如果失败则尝试以CSV格式读取。
    只保留第一列数据并返回为列表。

    Args:
        file_path: 要读取的文件路径。

    Returns:
        包含文件第一列数据的列表。

    Raises:
        IOError: 如果文件无法读取或格式不支持。
    """
    try:
        # 尝试读取Excel文件
        data = pd.read_excel(file_path, header=None)
    except ValueError:
        try:
            # 如果读取Excel失败,尝试读取CSV文件
            data = pd.read_csv(file_path, header=None, sep=None, engine="python")
        except Exception as csv_error:
            raise IOError(f"无法读取文件 {file_path}: {str(csv_error)}") from csv_error

    # 只保留第一列,并将其转换为列表
    return data.iloc[:, 0].tolist()
