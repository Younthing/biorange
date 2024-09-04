import pandas as pd

from biorange.core.logger import get_logger
from biorange.core.utils.package_fileload import get_data_file_path

logger = get_logger(__name__)


class TCMSPTargetScraper:
    def __init__(self, molecules_csv="TCMSP_mol.csv", targets_csv="TCMSP_tar.csv"):
        logger.info("Initializing MoleculeSearcher")
        self.molecules_df = pd.read_csv(get_data_file_path(molecules_csv))
        self.targets_df = pd.read_csv(get_data_file_path(targets_csv))
        self.merged_df = self._merge_dataframes()

    def _merge_dataframes(self):
        logger.info("Merging molecules and targets dataframes")
        merged_df = self.molecules_df.merge(
            self.targets_df, left_on="molecule_ID", right_on="molecule_ID", how="left"
        )
        logger.debug(f"Merged dataframe shape: {merged_df.shape}")
        return merged_df

    def search_smiles(self, input_smiles):
        logger.info(f"Searching for SMILES: {input_smiles}")

        # 筛选输入的smiles
        filtered_df = self.merged_df[self.merged_df["smiles"] == input_smiles].copy()
        filtered_df["source"] = "TCMSP"

        if filtered_df.empty:
            logger.warning(f"No matches found for SMILES: {input_smiles}")
            # 如果没有匹配的smiles
            results_df = pd.DataFrame(
                {"smiles": [input_smiles], "targets": [None], "source": ["TCMSP"]}
            )
        else:
            logger.info(f"Matches found for SMILES: {input_smiles}")
            # 选择需要的列并重命名
            results_df = filtered_df[["smiles", "Gene Names", "source"]].rename(
                columns={"Gene Names": "targets"}
            )

        return results_df


# 示例使用
if __name__ == "__main__":
    searcher = TCMSPTargetScraper()

    single_smiles = "CCO"
    result = searcher.search_smiles(single_smiles)
    result.to_csv("single_smiles.csv", index=False)
