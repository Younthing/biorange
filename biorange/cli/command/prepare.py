import typer

import biorange.core.load_data as load_data


app = typer.Typer(
    add_completion=True,  # add_completion=True 表示启用自动补全
    no_args_is_help=True,  # no_args_is_help=True 表示无参数时自动显示帮助信息
)


@app.command()
def load(herbs, output="liuyan.csv"):
    """
    进行PPI（蛋白质-蛋白质相互作用）分析。
    """
    # herbs_list = herbs.split(",")
    # tcmsp.main(herbs_list, output)
    # chembal.fetch_target_predictions(herbs, output)
    # chembal_.add_gene_name_to_predictions(herbs) #TODO 有错误

    # 逻辑代码
    # typer.echo(f"PPI分析 from {input_} to {output}")


@app.command()
def mybaby():
    msmd.my_ana()


@app.command()
def hhh(x):
    x = int(x)
    msmd.ddd(x)


@app.command()
def other(type_: str, input_: str, output: str):
    """
    执行其他类型的分析。
    """
    # 逻辑代码
    typer.echo(f"{type_}分析 from {input_} to {output}")


if __name__ == "__main__":
    app()
