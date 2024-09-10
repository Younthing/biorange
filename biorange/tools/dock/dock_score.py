import re
import subprocess


def smina_score(receptor_file, ligand_file):
    # 构建 smina 命令
    command = ["smina", "-r", receptor_file, "-l", ligand_file, "--score_only"]

    try:
        # 运行 smina 命令
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output = result.stdout

        # 提取 Affinity 和 Intramolecular energy
        affinity_match = re.search(r"Affinity:\s*([-\d.]+)", output)
        intra_energy_match = re.search(r"Intramolecular energy:\s*([-\d.]+)", output)

        affinity = float(affinity_match.group(1)) if affinity_match else None
        intra_energy = (
            float(intra_energy_match.group(1)) if intra_energy_match else None
        )

        return {"affinity": affinity, "intramolecular_energy": intra_energy}

    except subprocess.CalledProcessError as e:
        print(f"Error running smina: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# 使用示例
receptor_file = "results/complex_0/6w70.pdb"
ligand_file = "results/complex_0/rank1_confidence-1.18.sdf"

results = smina_score(receptor_file, ligand_file)
print(results)
