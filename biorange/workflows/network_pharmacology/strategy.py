"""
specific strategies for querying and normalizing data from various biomedical databases.

Classes:
    TCMSPDrugComponentFinder: 
    CheMBLTargetPredictor: 
    STITCHTargetPredictor: 
    TCMSPTargetPredictor: 
    GenecardsTargetPredictor: 
    OMIMTargetPredictor: 
    TTDTargetPredictor: 
"""

# TODO 以后要实现延迟导入
import pandas as pd

# Import abstract base classes for different types of predictors
from .abstract import ComponentTargetPredictor, DiseaseTargetFinder, DrugComponentFinder
from .script.component_tcmsp_local import TCMSPComponentLocalScraper
from .script.disease_genecards import GenecardsDiseaseScraper
from .script.disease_omim import OmimDiseaseScraper
from .script.disease_ttd import TTDDiseaseScraper
from .script.target_from_smiles_chembal import ChEMBLTargetScraper
from .script.target_from_smiles_tcmsp import TCMSPTargetScraper

# Implement specific strategies for querying and normalizing data from different databases


class TCMSPDrugComponentFinder(DrugComponentFinder):
    """
    A concrete implementation of DrugComponentFinder for querying the TCMSP database.
    """

    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """
        Query the TCMSP database for components of a given drug.

        Args:
            name (str): The name of the drug to query.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            pd.DataFrame: DataFrame containing the queried components.
        """

        self.logger.info("query %s from TCMSP", name)
        # 实现 TCMSP 数据库查询逻辑
        data = TCMSPComponentLocalScraper(use_remote=True).search_herb(name)
        # MOL_ID,pubchem_cid,molecule_ID,molecule_name,tpsa,rbn,
        # inchikey,ob,dl,bbb,caco2,mw,hdon,hacc,alogp,halflife,FASA

        return data

    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize the raw data from the TCMSP database.

        Args:
            raw_data (pd.DataFrame): Raw data DataFrame.

        Returns:
            pd.DataFrame: Normalized DataFrame.
        """
        column_mapping = {
            "molecule_name": "component_name",  # 将molecule_name改成component_name
            "smiles": "smiles",
            "inchikey": "inchikey",
            "ob": "oral_bioavailability",
            "dl": "drug_likeness",
        }

        # 重命名的时候顺手过滤了
        return raw_data.rename(columns=column_mapping)[list(column_mapping.values())]

    def post_process(self, data: pd.DataFrame) -> pd.DataFrame:
        """负责过滤等操作的钩子"""
        # 将列转换为数值型
        try:
            data.loc[:, "oral_bioavailability"] = pd.to_numeric(
                data["oral_bioavailability"], errors="coerce"
            )
        except Exception as e:
            self.logger.error(
                "Error converting 'oral_bioavailability' to numeric: %s", str(e)
            )

        try:
            data.loc[:, "drug_likeness"] = pd.to_numeric(
                data["drug_likeness"], errors="coerce"
            )
        except Exception as e:
            self.logger.error("Error converting 'drug_likeness' to numeric: %s", str(e))

        # 过滤掉DL<0.18的
        try:
            drug_likeness_min = 0.18
            self.logger.info("filter data with drug_likeness< %s", drug_likeness_min)
            data = data[data["drug_likeness"] >= drug_likeness_min]
        except Exception as e:
            self.logger.error("Error filtering data by 'drug_likeness': %s", str(e))

        # 过滤掉OD<30
        try:
            data = data[data["oral_bioavailability"] >= 30]
        except Exception as e:
            self.logger.error(
                "Error filtering data by 'oral_bioavailability': %s", str(e)
            )
        return data


class CheMBLTargetPredictor(ComponentTargetPredictor):
    """
    A concrete implementation of ComponentTargetPredictor for querying the CheMBL database.
    """

    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """
        Query the CheMBL database for targets of a given component.

        Args:
            name (str): The name of the component to query.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            pd.DataFrame: DataFrame containing the queried targets.
        """
        # Implement CheMBL database query logic here
        return ChEMBLTargetScraper().search_smiles(name)

    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize the raw data from the CheMBL database.

        Args:
            raw_data (pd.DataFrame): Raw data DataFrame.

        Returns:
            pd.DataFrame: Normalized DataFrame.
        """
        # smiles,target_chemblid,organism,pref_name,70%,80%,90%,threshold,gene_name,source

        column_mapping = {
            "smiles": "smiles",
            "gene_name": "targets",
            "source": "source",
        }
        if raw_data.empty:
            return pd.DataFrame(columns=list(column_mapping.values()))

        return raw_data.rename(columns=column_mapping)[list(column_mapping.values())]


# TODO stich
class STITCHTargetPredictor(ComponentTargetPredictor):
    """
    A concrete implementation of ComponentTargetPredictor for querying the STITCH database.
    """

    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """
        Query the STITCH database for targets of a given component.

        Args:
            name (str): The name of the component to query.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            pd.DataFrame: DataFrame containing the queried targets.
        """
        # Implement STITCH database query logic here
        return pd.DataFrame(
            {
                "smiles": [name, name],
                "gene_name": ["Protein1", "Protein2"],
                "source": ["stich", "stich"],
            }
        )

    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize the raw data from the CheMBL database.

        Args:
            raw_data (pd.DataFrame): Raw data DataFrame.

        Returns:
            pd.DataFrame: Normalized DataFrame.
        """
        # smiles,target_chemblid,organism,pref_name,70%,80%,90%,threshold,gene_name

        column_mapping = {
            "smiles": "smiles",
            "gene_name": "targets",
            "source": "source",
        }
        if raw_data.empty:
            return pd.DataFrame(columns=list(column_mapping.values()))

        return raw_data.rename(columns=column_mapping)[list(column_mapping.values())]


class TCMSPTargetPredictor(ComponentTargetPredictor):
    """
    A concrete implementation of ComponentTargetPredictor for querying the TCMSP database.
    """

    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """
        Query the TCMSP database for targets of a given component.

        Args:
            name (str): The name of the component to query.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            pd.DataFrame: DataFrame containing the queried targets.
        """
        # Implement TCMSP database query logic here
        return TCMSPTargetScraper().search_smiles(name)

    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:

        column_mapping = {
            "smiles": "smiles",
            "targets": "targets",
            "source": "source",
        }
        if raw_data.empty:
            return pd.DataFrame(columns=list(column_mapping.values()))

        return raw_data.rename(columns=column_mapping)[list(column_mapping.values())]


class GenecardsTargetPredictor(DiseaseTargetFinder):
    """
    A concrete implementation of DiseaseTargetFinder for querying the Genecards database.
    """

    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """
        Query the Genecards database for targets associated with a given disease.

        Args:
            name (str): The name of the disease to query.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            pd.DataFrame: DataFrame containing the queried targets.
        """
        # Implement Genecards database query logic here
        return GenecardsDiseaseScraper().search(name)

    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize the raw data from the Genecards database.

        Args:
            raw_data (pd.DataFrame): Raw data DataFrame.

        Returns:
            pd.DataFrame: Normalized DataFrame.
        """
        column_mapping = {
            "disease": "name",
            "dis_targets": "target_name",
            "source": "source",
        }
        return raw_data.rename(columns=column_mapping)[list(column_mapping.values())]


class OMIMTargetPredictor(DiseaseTargetFinder):
    """
    A concrete implementation of DiseaseTargetFinder for querying the OMIM database.
    """

    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """
        Query the OMIM database for targets associated with a given disease.

        Args:
            name (str): The name of the disease to query.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            pd.DataFrame: DataFrame containing the queried targets.
        """
        # Implement OMIM database query logic here
        return OmimDiseaseScraper().search(name)

    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize the raw data from the OMIM database.

        Args:
            raw_data (pd.DataFrame): Raw data DataFrame.

        Returns:
            pd.DataFrame: Normalized DataFrame.
        """
        column_mapping = {
            "disease": "name",
            "dis_targets": "target_name",
            "source": "source",
        }
        return raw_data.rename(columns=column_mapping)[list(column_mapping.values())]


class TTDTargetPredictor(DiseaseTargetFinder):
    """
    A concrete implementation of DiseaseTargetFinder for querying the TTD database.
    """

    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """
        Query the TTD database for targets associated with a given disease.

        Args:
            name (str): The name of the disease to query.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            pd.DataFrame: DataFrame containing the queried targets.
        """
        # Implement TTD database query logic here
        return TTDDiseaseScraper().search(name)

    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize the raw data from the TTD database.

        Args:
            raw_data (pd.DataFrame): Raw data DataFrame.

        Returns:
            pd.DataFrame: Normalized DataFrame.
        """
        column_mapping = {
            "disease": "name",
            "dis_targets": "target_name",
            "source": "source",
        }
        return raw_data.rename(columns=column_mapping)[list(column_mapping.values())]
