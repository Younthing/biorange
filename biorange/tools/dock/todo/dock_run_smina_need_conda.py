# %%
# %conda install conda-forge::opencadd
# Python 3.9.19
import os
import subprocess

# 导入必要的库
import warnings
from pathlib import Path

import nglview as nv
from openbabel import pybel
from opencadd.structure.core import Structure

# %%
# 定义路径
# 这里定义了当前工作目录和数据目录。数据目录用于存储中间和最终的结果文件。
HERE = Path(_dh[-1])
DATA = HERE / "data"
DATA.mkdir(exist_ok=True)
DATA


# %%
# 下载 PDB 文件
def download_pdb(pdb_code: str, work_dir: str):
    import os

    import requests

    pdb_path = os.path.join(work_dir, f"{pdb_code}.pdb")

    if not os.path.exists(pdb_path):
        # 从蛋白质数据库 (PDB) 下载文件，如果文件不存在的话
        pdb_url = f"https://files.rcsb.org/download/{pdb_code}.pdb"
        response = requests.get(pdb_url)
        if response.status_code == 200:
            with open(pdb_path, "wt", encoding="utf-8") as pdb_file:
                pdb_file.write(response.text)

    return pdb_path if os.path.exists(pdb_path) else None


# %%


# 从字符串加载 PDB 文件
def from_string(cls, pdbid_or_path, **kwargs):
    if os.path.isfile(pdbid_or_path):
        return cls(pdbid_or_path, **kwargs)
    return cls.from_pdbid(pdbid_or_path, **kwargs)


# 将新的方法添加到 Structure 类中
Structure.from_string = classmethod(from_string)

# %%


# 从蛋白质数据库中检索结构
# 这里下载了指定的 PDB 文件并使用 Structure 类加载
pdb_id = "2ito"
download_pdb_dir = download_pdb(pdb_id, DATA)
structure = Structure.from_string(download_pdb_dir)
structure, download_pdb_dir

# %%


# 将 PDB 文件转换为 PDBQT 文件
def pdb_to_pdbqt(pdb_path, pdbqt_path, pH=7.4):
    """
    Convert a PDB file to a PDBQT file needed by docking programs of the AutoDock family.

    Parameters
    ----------
    pdb_path: str or pathlib.Path
        Path to input PDB file.
    pdbqt_path: str or pathlib.path
        Path to output PDBQT file.
    pH: float
        Protonation at given pH.
    """
    molecule = list(pybel.readfile("pdb", str(pdb_path)))[0]
    # 在给定的 pH 值下添加氢
    molecule.OBMol.CorrectForPH(pH)
    molecule.addh()
    # 为每个原子添加部分电荷
    for atom in molecule.atoms:
        atom.OBAtom.GetPartialCharge()
    # 将结果写入 PDBQT 文件
    molecule.write("pdbqt", str(pdbqt_path), overwrite=True)
    return


# %%


# 将蛋白质转换为 PDBQT 格式
# 这里将蛋白质 PDB 文件转换为对接所需的 PDBQT 格式
pdb_to_pdbqt(download_pdb_dir, DATA / "protein.pdbqt")

# %%


# 为蛋白质-配体复合物定义配体的 SMILES
# SMILES 是一种用于表示分子结构的字符串表示法
smiles = "COC1=C(C=C2C(=C1)N=CN=C2NC3=CC(=C(C=C3)F)Cl)OCCCN4CCOCC4"

# %%


# 将 SMILES 字符串转换为 PDBQT 文件
def smiles_to_pdbqt(smiles, pdbqt_path, pH=7.4):
    """
    Convert a SMILES string to a PDBQT file needed by docking programs of the AutoDock family.

    Parameters
    ----------
    smiles: str
        SMILES string.
    pdbqt_path: str or pathlib.path
        Path to output PDBQT file.
    pH: float
        Protonation at given pH.
    """
    molecule = pybel.readstring("smi", smiles)
    # 在给定的 pH 值下添加氢
    molecule.OBMol.CorrectForPH(pH)
    molecule.addh()
    # 生成 3D 坐标
    molecule.make3D(forcefield="mmff94s", steps=10000)
    # 为每个原子添加部分电荷
    for atom in molecule.atoms:
        atom.OBAtom.GetPartialCharge()
    # 将结果写入 PDBQT 文件
    molecule.write("pdbqt", str(pdbqt_path), overwrite=True)
    return


# %%


# 将配体转换为 PDBQT 格式
# 将配体的 SMILES 表示转换为 PDBQT 文件
smiles_to_pdbqt(smiles, DATA / "ligand.pdbqt")

# %%


# 定义结合口袋的中心和大小
# 这里根据配体的位置计算结合口袋的中心和大小
ligand_resname = "IRE"
ligand = structure.select_atoms(f"resname {ligand_resname}")
pocket_center = (ligand.positions.max(axis=0) + ligand.positions.min(axis=0)) / 2
pocket_size = ligand.positions.max(axis=0) - ligand.positions.min(axis=0) + 5

# %%


# 进行对接计算
def run_smina(
    ligand_path,
    protein_path,
    out_path,
    pocket_center,
    pocket_size,
    num_poses=10,
    exhaustiveness=8,
):
    """
    Perform docking with Smina.

    Parameters
    ----------
    ligand_path: str or pathlib.Path
        Path to ligand PDBQT file that should be docked.
    protein_path: str or pathlib.Path
        Path to protein PDBQT file that should be docked to.
    out_path: str or pathlib.Path
        Path to which docking poses should be saved, SDF or PDB format.
    pocket_center: iterable of float or int
        Coordinates defining the center of the binding site.
    pocket_size: iterable of float or int
        Lengths of edges defining the binding site.
    num_poses: int
        Maximum number of poses to generate.
    exhaustiveness: int
        Accuracy of docking calculations.

    Returns
    -------
    output_text: str
        The output of the Smina calculation.
    """
    # 使用 Smina 进行对接计算
    output_text = subprocess.check_output(
        [
            "smina",
            "--ligand",
            str(ligand_path),
            "--receptor",
            str(protein_path),
            "--out",
            str(out_path),
            "--center_x",
            str(pocket_center[0]),
            "--center_y",
            str(pocket_center[1]),
            "--center_z",
            str(pocket_center[2]),
            "--size_x",
            str(pocket_size[0]),
            "--size_y",
            str(pocket_size[1]),
            "--size_z",
            str(pocket_size[2]),
            "--num_modes",
            str(num_poses),
            "--exhaustiveness",
            str(exhaustiveness),
        ],
        universal_newlines=True,  # 需要捕获输出文本
    )
    return output_text


# %%


# 打印对接结果
# 进行对接计算并打印结果
output_text = run_smina(
    DATA / "ligand.pdbqt",
    DATA / "protein.pdbqt",
    DATA / "docking_poses.sdf",
    pocket_center,
    pocket_size,
)
print(output_text)

# %%


# 检查输出文件是否已生成
# 确保对接结果文件已生成
(DATA / "docking_poses.sdf").exists()
# NBVAL_CHECK_OUTPUT


# %%
## 单独的亲和力提取
def extract_affinity(sdf_path):
    # 读取 SDF 文件
    sdf_molecules = pybel.readfile("sdf", sdf_path)

    # 提取亲和力信息
    affinities = []
    for mol in sdf_molecules:
        try:
            affinity = mol.data["minimizedAffinity"]  # Smina 的亲和力字段
            affinities.append(float(affinity))
        except KeyError:
            print("No affinity data found for one of the poses.")

    return affinities


# 示例使用
sdf_path = "data/docking_poses_2.sdf"
affinities = extract_affinity(sdf_path)
print(affinities)

# %%


# 将 SDF 文件拆分为单独的分子文件
def split_sdf_file(sdf_path):
    """
    Split an SDF file into seperate files for each molecule.
    Each file is named with consecutive numbers.

    Parameters
    ----------
    sdf_path: str or pathlib.Path
        Path to SDF file that should be split.
    """
    sdf_path = Path(sdf_path)
    stem = sdf_path.stem
    parent = sdf_path.parent
    molecules = pybel.readfile("sdf", str(sdf_path))
    # 将每个分子写入单独的 SDF 文件
    for i, molecule in enumerate(molecules, 1):
        molecule.write("sdf", str(parent / f"{stem}_{i}.sdf"), overwrite=True)
    return


# %%


# 拆分 SDF 文件
# 将对接结果的 SDF 文件拆分为单独的分子文件
split_sdf_file(DATA / "docking_poses.sdf")

# %%
# 可视化对接结果
# 使用 NGLView 可视化对接结果
docking_pose_id = 2
view = nv.show_structure_file(
    str(DATA / f"docking_poses_{docking_pose_id}.sdf"),
    representations=[{"params": {}, "type": "licorice"}],
)
view.add_pdbid(pdb_id)
view

# %%
# 图像
view.write_html("results/docker_plot.html", fullpage=True)
