import typer

app = typer.Typer(
    add_completion=True,  # add_completion=True 表示启用自动补全
    no_args_is_help=True,  # no_args_is_help=True 表示无参数时自动显示帮助信息
)


@app.command()  # 字符串传递命令名称
def ppi():
    """
    进行PPI（蛋白质-蛋白质相互作用）分析。
    """
    # 逻辑代码
    print("PPI analysis completed.")  # 打印出“PPT”


@app.command()
def other(type_: str, input_: str, output: str):
    """
    执行其他类型的分析。
    """
    # 逻辑代码
    typer.echo(f"{type_}分析 from {input_} to {output}")


if __name__ == "__main__":
    app()
