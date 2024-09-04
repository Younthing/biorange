from typing import Optional

import typer

from biorange import __version__
from biorange.core.config.config_manager import (
    ConfigManager,
)  # TODO 记得使用依赖注入代替实例化，解耦

from .command import analyze, prepare
from .helpers import process_parameters  # 导入参数处理函数

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
def callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="显示版本号并退出"
    ),
):
    if version:
        typer.echo(f"BioRange version: {__version__}")
        raise typer.Exit()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(
    ctx: typer.Context,
    env: Optional[str] = typer.Option(None, help="环境配置文件路径"),
    config: Optional[str] = typer.Option(None, help="配置文件路径"),
):
    config_manager = process_parameters(ctx, env, config)
    progress(config_manager)


from biorange.cli.dependence import run_analysis


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def netparam(
    ctx: typer.Context,
    env: Optional[str] = typer.Option(None, help="环境配置文件路径"),
    config: Optional[str] = typer.Option(None, help="配置文件路径"),
):
    config_manager = process_parameters(ctx, env, config)
    run_analysis(config_manager)


def progress(config_manager: ConfigManager):
    """打印参数"""
    for key, value in config_manager.settings.model_dump().items():
        typer.echo(f"{key}: {value}")


if __name__ == "__main__":
    app()
