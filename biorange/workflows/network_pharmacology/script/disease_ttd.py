import pandas as pd

from biorange.core.utils.package_fileload import get_data_file_path


class TTDDiseaseScraper:

    def __init__(self, file_path="TTD_combinez_data.csv"):
        self.df = pd.read_csv(get_data_file_path(file_path))

    def search(self, diseases):
        # 如果输入是字符串，则将其转换为包含一个元素的列表
        if isinstance(diseases, str):
            diseases = [diseases]

        # 创建一个空的DataFrame来存储匹配结果
        filtered_df = pd.DataFrame()

        # 遍历输入的diseases列表，进行部分匹配
        for disease in diseases:
            # 使用str.contains进行部分匹配，忽略大小写
            matches = self.df[
                self.df["Disease Entry"].str.contains(disease, case=False, na=False)
            ]
            # 将匹配结果追加到filtered_df中
            filtered_df = pd.concat([filtered_df, matches])

        # 创建一个新的表格，并在第一列增加“data_source”列，内容为“TTD”
        if filtered_df.empty:
            return pd.DataFrame(cloumns=["disease", "dis_targets", "source"])
        new_df = pd.DataFrame()
        new_df["disease"] = filtered_df["Disease Entry"].values
        new_df["dis_targets"] = filtered_df["GENENAME"].values
        new_df["source"] = ["TTD"] * len(filtered_df)

        return new_df


if __name__ == "__main__":
    searcher = TTDDiseaseScraper()
    result_df = searcher.search("Lung cancer")
    print(result_df)
