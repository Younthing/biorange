from typing import Optional
import typer
from biorange import __version__
from .command import prepare, analyze

# 初始化 Typer 应用，设置无参数时自动显示帮助信息
app = typer.Typer(
    add_completion=True,  # add_completion=True 表示启用自动补全
    no_args_is_help=True,  # no_args_is_help=True 表示无参数时自动显示帮助信息
)

# 添加子命令组
app.add_typer(prepare.app, name="prepare")
app.add_typer(analyze.app, name="analyze")


# 回调函数，用于处理全局选项和显示帮助信息
@app.callback(invoke_without_command=True, help="BioRange 命令行工具 made in china")
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="显示版本号并退出"
    ),
):
    """
    BioRange 命令行工具，用于执行各种生物信息学分析和准备任务。

    Args:
        ctx (typer.Context): Typer上下文对象，包含命令行参数和其他上下文信息。
        version (Optional[bool]): 是否显示版本信息并退出。
    """
    if version:
        typer.echo(f"BioRange version: {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
