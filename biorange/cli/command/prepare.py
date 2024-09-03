import typer

app = typer.Typer(
    add_completion=True,  # add_completion=True 表示启用自动补全
    no_args_is_help=True,  # no_args_is_help=True 表示无参数时自动显示帮助信息
)


@app.command()
def load(herbs, output="liuyan.csv"):
    """
    进行PPI（蛋白质-蛋白质相互作用）分析。
    """

    typer.echo(f"PPI分析 from {herbs} to {output}")


if __name__ == "__main__":
    app()
