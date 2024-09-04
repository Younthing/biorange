import pandas as pd

from biorange.core.utils.package_fileload import get_data_file_path


class OmimDiseaseScraper:

    def __init__(
        self,
        file_path="morbidmap.txt",
    ):
        self.df = pd.read_table(get_data_file_path(file_path))

    def search(self, phenotypes):
        # 如果输入是字符串，则将其转换为包含一个元素的列表
        if isinstance(phenotypes, str):
            phenotypes = [phenotypes]
        # 创建一个空的DataFrame来存储匹配结果
        filtered_df = pd.DataFrame()

        # 遍历输入的Phenotype列表，进行部分匹配
        for phenotype in phenotypes:
            # 使用str.contains进行部分匹配，忽略大小写
            matches = self.df[
                self.df["Phenotype"].str.contains(phenotype, case=False, na=False)
            ]
            # 将匹配结果追加到filtered_df中
            filtered_df = pd.concat([filtered_df, matches])

        # 拆分“Gene Symbols”列中的多个基因名
        filtered_df["Gene Symbols"] = filtered_df["Gene Symbols"].str.split(",")

        # 使用explode方法将每行的列表元素拆分成多行
        exploded_df = filtered_df.explode("Gene Symbols")

        # 去除前后空格
        exploded_df["Gene Symbols"] = exploded_df["Gene Symbols"].str.strip()

        # 对“Gene Symbols”列进行去重
        exploded_df = exploded_df.drop_duplicates(subset=["Gene Symbols"])
        if exploded_df.empty:
            print("No matches found for the given phenotypes.")
            return pd.DataFrame(columns=["disease", "dis_targets", "source"])
        # 创建一个新的表格，并在第一列增加“data_source”列，内容为“OMIM”
        new_df = pd.DataFrame()
        new_df["disease"] = exploded_df["Phenotype"].values
        new_df["dis_targets"] = exploded_df["Gene Symbols"].values
        new_df["source"] = ["OMIM"] * len(exploded_df)

        return new_df


if __name__ == "__main__":
    searcher = OmimDiseaseScraper()
    result_df = searcher.search("Lung cancer")
    print(result_df)
