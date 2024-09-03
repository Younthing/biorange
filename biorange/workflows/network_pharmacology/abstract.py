"""
数据获取策略模块。

该模块定义了数据获取、规范化和保存的基类以及具体实现类。基类提供了基本的
数据处理流程，并定义了钩子方法供子类覆盖以添加额外的处理逻辑。

类:
    BaseDataFetcher: 数据获取策略的抽象基类。
    DrugComponentFinder: 查找药物成分的具体实现类。
    ComponentTargetPredictor: 预测成分靶点的具体实现类。
    DiseaseTargetFinder: 查找疾病靶点的具体实现类。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import pandas as pd

from biorange.core.logger import get_logger

RESUILTS_DIR = "./results"


class BaseDataFetcher(ABC):
    """数据获取策略的抽象基类。

    该类定义了数据获取、规范化和保存的基本流程，并提供了钩子方法供子类定制额外的处理逻辑。
    """

    def __init__(self):
        """初始化BaseDataFetcher实例，创建一个空的DataFrame以存储数据。"""
        self.data = pd.DataFrame()
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """查询数据库并返回原始结果。

        该方法必须在子类中实现。

        参数:
            name (str): 查询的名称。
            *args: 可变长度参数列表。
            **kwargs: 关键字参数。

        返回:
            pd.DataFrame: 包含查询结果的数据框。
        """

    @abstractmethod
    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """将原始数据规范化为标准格式。

        该方法必须在子类中实现。

        参数:
            raw_data (pd.DataFrame): 包含原始数据的数据框。

        返回:
            pd.DataFrame: 规范化后的数据框。
        """

    def fetch(self, name: str, save_results: bool = True) -> pd.DataFrame:
        """执行策略：查询并规范化数据。

        参数:
            name (str): 数据名称，用于保存文件。
            save_results (bool): 是否保存结果到CSV文件，默认为True。

        返回:
            pd.DataFrame: 规范化后的数据框。
        """
        parent_class_name = self.__class__.__bases__[0].__name__
        directory = Path(RESUILTS_DIR) / parent_class_name / self.__class__.__name__
        file_path = directory / f"{name}.csv"

        if file_path.exists():
            self.logger.info(
                f"File {file_path} already exists. Loading data from file."
            )
            self.data = pd.read_csv(file_path)
            return self.data

        self.logger.info(
            f"File {file_path} does not exist. Querying and processing data."
        )
        raw_data = self.query(name)
        self.data = self.normalize(raw_data)
        self.data = self.post_process(self.data)  # 调用钩子方法
        if save_results:
            self.save_to_csv(name)
        return self.data

    def save_to_csv(self, name: str):
        """将规范化后的数据保存到CSV文件。

        参数:
            name (str): 数据名称，用于保存文件。
        """
        parent_class_name = self.__class__.__bases__[0].__name__
        directory = Path(RESUILTS_DIR) / parent_class_name / self.__class__.__name__
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{name}.csv"
        self.data.to_csv(file_path, index=False)
        self.logger.info(f"Data saved to {file_path}")

    @staticmethod
    def merge_results(results: List[pd.DataFrame]) -> pd.DataFrame:
        """合并多个数据框的结果。

        参数:
            results (List[pd.DataFrame]): 数据框列表。

        返回:
            pd.DataFrame: 合并且去重的数据框。
        """
        return pd.concat(results, ignore_index=True).drop_duplicates()

    def post_process(self, data: pd.DataFrame) -> pd.DataFrame:
        """对规范化后的数据进行额外处理的钩子方法。

        子类可以覆盖此方法以添加自定义处理逻辑。

        参数:
            data (pd.DataFrame): 规范化后的数据框。

        返回:
            pd.DataFrame: 处理后的数据框。
        """
        return data


class DrugComponentFinder(BaseDataFetcher):
    """查找药物成分的具体实现类。"""

    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """查询数据库并返回药物成分的原始结果。

        参数:
            name (str): 药物名称。
            *args: 可变长度参数列表。
            **kwargs: 关键字参数。

        返回:
            pd.DataFrame: 包含查询结果的数据框。
        """
        raw_data = pd.DataFrame()  # 假设这是查询结果
        return raw_data

    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """将药物成分的原始数据规范化为标准格式。

        参数:
            raw_data (pd.DataFrame): 包含原始数据的数据框。

        返回:
            pd.DataFrame: 规范化后的数据框。
        """
        normalized_data = raw_data  # 假设这是规范化后的数据
        return normalized_data

    def post_process(self, data: pd.DataFrame) -> pd.DataFrame:
        """对规范化后的药物成分数据进行额外处理。

        参数:
            data (pd.DataFrame): 规范化后的数据框。

        返回:
            pd.DataFrame: 处理后的数据框。
        """
        processed_data = data  # 这里可以添加自定义处理逻辑

        return processed_data


class ComponentTargetPredictor(BaseDataFetcher):
    """预测成分靶点的具体实现类。"""

    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """查询数据库并返回成分靶点的原始结果。

        参数:
            name (str): 成分名称。
            *args: 可变长度参数列表。
            **kwargs: 关键字参数。

        返回:
            pd.DataFrame: 包含查询结果的数据框。
        """
        raw_data = pd.DataFrame()  # 假设这是查询结果
        return raw_data

    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """将成分靶点的原始数据规范化为标准格式。

        参数:
            raw_data (pd.DataFrame): 包含原始数据的数据框。

        返回:
            pd.DataFrame: 规范化后的数据框。
        """
        normalized_data = raw_data  # 假设这是规范化后的数据
        return normalized_data

    def post_process(self, data: pd.DataFrame) -> pd.DataFrame:
        """对规范化后的成分靶点数据进行额外处理。

        参数:
            data (pd.DataFrame): 规范化后的数据框。

        返回:
            pd.DataFrame: 处理后的数据框。
        """
        processed_data = data  # 这里可以添加自定义处理逻辑
        return processed_data


class DiseaseTargetFinder(BaseDataFetcher):
    """查找疾病靶点的具体实现类。"""

    def query(self, name: str, *args, **kwargs) -> pd.DataFrame:
        """查询数据库并返回疾病靶点的原始结果。

        参数:
            name (str): 疾病名称。
            *args: 可变长度参数列表。
            **kwargs: 关键字参数。

        返回:
            pd.DataFrame: 包含查询结果的数据框。
        """
        raw_data = pd.DataFrame()  # 假设这是查询结果
        return raw_data

    def normalize(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """将疾病靶点的原始数据规范化为标准格式。

        参数:
            raw_data (pd.DataFrame): 包含原始数据的数据框。

        返回:
            pd.DataFrame: 规范化后的数据框。
        """
        normalized_data = raw_data  # 假设这是规范化后的数据
        return normalized_data

    def post_process(self, data: pd.DataFrame) -> pd.DataFrame:
        """对规范化后的疾病靶点数据进行额外处理。

        参数:
            data (pd.DataFrame): 规范化后的数据框。

        返回:
            pd.DataFrame: 处理后的数据框。
        """
        processed_data = data  # 这里可以添加自定义处理逻辑
        return processed_data
