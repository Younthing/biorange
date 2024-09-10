import py3Dmol


def visualize_molecule_complex(
    sdf_file, pdb_file, width=1200, height=900
) -> py3Dmol.view:
    """
    可视化分子复合物。

    该函数加载并可视化蛋白质（PDB文件）和小分子（SDF文件），并设置相关的样式和显示参数。

    Args:
        sdf_file (str): 指定小分子SDF文件的路径。
        pdb_file (str): 指定蛋白质PDB文件的路径。
        width (int, optional): 视图窗口的宽度，默认为1200。
        height (int, optional): 视图窗口的高度，默认为900。

    Returns:
        py3Dmol.view: 返回包含已加载和可视化模型的py3Dmol视图对象。
    """
    viewer = py3Dmol.view(width=width, height=height)

    # 加载蛋白质和小分子
    with open(pdb_file, "r") as f:
        viewer.addModel(f.read(), "pdb")
    with open(sdf_file, "r") as f:
        viewer.addModel(f.read(), "sdf")

    # 设置蛋白质样式
    viewer.setStyle(
        {"model": 0},  # 第一个模型，蛋白质
        {
            "cartoon": {
                "color": "spectrum",
                "opacity": 1,
            },  # 以光谱颜色显示蛋白质的卡通样式
            "surface": {"opacity": 1},  # 设置蛋白质表面为不透明
        },
    )

    # 设置小分子样式
    viewer.setStyle(
        {"model": 1},  # 第二个模型，小分子
        {
            "stick": {
                "colorscheme": "blueCarbon",
                "radius": 0.2,
            },  # 设置小分子的棒状样式，颜色为蓝色碳
            "sphere": {
                "colorscheme": "blueCarbon",
                "radius": 0.5,
            },  # 设置小分子的球状样式，颜色为蓝色碳
        },
    )

    # 外层棉花糖效果
    viewer.addSurface(
        {"model": 0},  # 第一个模型，蛋白质
        {
            "opacity": 0.6,  # 设置表面透明度
            "color": "white",  # 设置表面颜色为白色
            "opacityType": "maximum",
            "colorType": "maximum",
            "style": "surface",
            "wireframe": False,  # 不显示线框
        },
    )

    # # 添加相互作用（这需要您知道具体的相互作用位置）
    # viewer.addLine({"start": {"x": 0, "y": 0, "z": 0}, "end": {"x": 3, "y": 4, "z": 5}})

    # # 添加标签（这需要您知道具体的残基位置）
    # viewer.addLabel(
    #     "Lys101", {"position": {"x": 10, "y": 20, "z": 30}, "backgroundColor": "white"}
    # )

    # # 添加高亮区域，电荷分布等等 都需要相应的数据或者计算

    viewer.zoomTo()  # 自动调整视角以适应所有模型
    return viewer


if __name__ == "__main__":

    # 使用示例
    viewer_ = visualize_molecule_complex(
        "results/complex_0/rank1_confidence-1.18.sdf", "results/complex_0/6w70.pdb"
    )
    viewer_.show()  # 交互式环境可用
    # view.display(gui=True, style="ipywidgets")
    viewer_.write_html("results/docker_plot.html", fullpage=True)
