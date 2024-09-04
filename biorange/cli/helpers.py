from typing import Dict, Optional

import pandas as pd
import typer

from biorange.core.config.config_loader import ConfigLoader
from biorange.core.config.config_manager import ConfigManager


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


def process_parameters(
    ctx: typer.Context, env: Optional[str], config: Optional[str]
) -> ConfigManager:
    """
    处理命令行参数并返回配置管理器。

    Args:
        ctx (typer.Context): Typer上下文对象，包含命令行参数和其他上下文信息。
        env (Optional[str]): 环境配置文件路径。
        config (Optional[str]): 配置文件路径。

    Returns:
        ConfigManager: 配置管理器对象。
    """
    cli_args: Dict[str, str] = {}

    args = iter(ctx.args)
    for arg in args:
        if arg.startswith("--"):
            key = arg.lstrip("--")
            try:
                value = next(args)
                if value.startswith("--"):
                    raise ValueError(f"Value for {key} is missing.")
                cli_args[key] = value
            except StopIteration as exc:
                typer.echo(f"Value for {key} is missing.")
                raise typer.Exit(code=1) from exc
        else:
            typer.echo(f"Invalid argument format: {arg}")
            raise typer.Exit(code=1)

    config_loader = ConfigLoader(env_file=env, config_file=config)
    config_manager = ConfigManager(cli_args=cli_args, config_loader=config_loader)

    return config_manager
