"""main.py"""

from typing import Optional

import typer
from typer import Typer

from . import __version__

app = Typer(add_completion=True)  # add_completion=False 关闭自动补全


# 不给help参数时下面被装饰函数的注释会出现在help
@app.callback(invoke_without_command=True, help="BioRange 命令行工具")
def callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="显示版本号并退出"
    ),
):
    """
    Args:
        ctx (typer.Context): Typer上下文对象，包含命令行参数和其他上下文信息。
        version (Optional[bool]): 是否显示版本信息并退出。
    Raises:
        typer.Exit: 当没有子命令被调用时，退出程序并显示帮助信息。
    """
    if version:
        typer.echo(f"biorange version: {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()  # 我们希望程序显示帮助信息并立即退出，而不是继续执行其他代码
