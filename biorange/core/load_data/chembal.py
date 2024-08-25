import requests
import pandas as pd


def fetch_target_predictions(input_file, output_file):
    """
    从CSV文件读取SMILES字符串，获取靶点预测结果并保存到CSV文件。

    参数：
    input_file (str): 输入的CSV文件路径，包含SMILES字符串。
    output_file (str): 输出的CSV文件路径，用于保存预测结果。
    """

    def get_target_predictions(smiles):
        url = "https://www.ebi.ac.uk/chembl/target-predictions"
        headers = {"Content-Type": "application/json"}
        payload = {"smiles": smiles}

        # 发送POST请求
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df.insert(0, "smiles", smiles)
            return df
        else:
            print(
                f"Request failed for {smiles} with status code {response.status_code}"
            )
            return None

    # 从CSV文件读取SMILES字符串
    smiles_df = pd.read_csv(input_file)
    smiles_list = smiles_df["smiles"].tolist()

    # 创建一个空的DataFrame用于存储所有结果
    all_results = pd.DataFrame()

    # 遍历每个SMILES字符串并获取预测结果
    for smiles in smiles_list:
        df = get_target_predictions(smiles)
        if df is not None:
            all_results = pd.concat([all_results, df], ignore_index=True)

    # 保存结果到CSV文件
    if not all_results.empty:
        all_results.to_csv(output_file, index=False)
        print(f"Predictions saved to {output_file}")
    else:
        print("No predictions were obtained.")
