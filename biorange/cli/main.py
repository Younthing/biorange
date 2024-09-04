from typing import Optional

import typer

from biorange import __version__
from biorange.core.config.config_loader import ConfigLoader
from biorange.core.config.config_manager import ConfigManager

from .command import analyze, prepare

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


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(
    ctx: typer.Context,
    env: Optional[str] = typer.Option(None, help="环境配置文件路径"),
    config: Optional[str] = typer.Option(None, help="配置文件路径"),
):

    cli_args = {}

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

    for key in cli_args:
        final_value = config_manager.get(key)
        typer.echo(f"{key}: {final_value}")


if __name__ == "__main__":
    app()
