import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

import pandas as pd
import requests


# 缓存请求结果以提高效率
@lru_cache(maxsize=10000)
def inchikey_to_smiles(inchikey):
    """
    将InChIKey转换为SMILES表示法。
    Args:
        inchikey (str): 要转换的InChIKey。
    Returns:
        str or None: 如果成功，返回对应的SMILES字符串；如果失败，返回None。
    """
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/{inchikey}/property/CanonicalSMILES/JSON"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        try:
            return data["PropertyTable"]["Properties"][0]["CanonicalSMILES"]
        except (KeyError, IndexError):
            return None
    else:
        return None


def process_row(row):
    if pd.isna(row["smiles"]) or row["smiles"] == "":
        row["smiles"] = inchikey_to_smiles(row["inchikey"])
    return row


def process_csv(input_file: str, output_file: str, max_workers: int = None):
    if max_workers is None:
        max_workers = os.cpu_count() * 2  # 根据系统 CPU 核心数设置默认线程数

    # 读取输入文件
    df = pd.read_csv(input_file)

    # 使用并行处理来补全缺失的 SMILES
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_row, row): index for index, row in df.iterrows()
        }

        for future in as_completed(futures):
            index = futures[future]
            try:
                # 更新数据框中的行
                df.iloc[index] = future.result()
            except Exception as e:
                print(f"Error processing row at index {index}: {e}")

    # 保存处理后的数据到输出文件
    df.to_csv(output_file, index=False, encoding="utf-8")


import glob

import pandas as pd


def merge_csv_files(file_pattern: str, output_file: str):
    # 获取所有符合模式的文件列表
    files = glob.glob(file_pattern)

    # 读入所有文件并合并
    df_list = [pd.read_csv(file) for file in files]
    merged_df = pd.concat(df_list).drop_duplicates(subset="MOL_ID")

    # 保留最完整的SMILES列
    merged_df = merged_df.sort_values(by="smiles", na_position="last").drop_duplicates(
        subset="MOL_ID", keep="first"
    )
    merged_df = merged_df.sort_values(by="MOL_ID")

    # 将结果保存到输出文件
    merged_df.to_csv(output_file, index=False)


if __name__ == "__main__":
    process_csv("data/TCMSP_mol.csv", "data/mol2.csv", max_workers=50)

    merge_csv_files("data/mol*.csv", "data/TCMSP_mol.csv")
