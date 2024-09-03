from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import anndata as ad
import scanpy as sc

from biorange.core.logger import get_logger

logger = get_logger(__name__)


class Handler(ABC):
    def __init__(
        self, next_handler: Optional["Handler"] = None, config: Dict[str, Any] = None
    ):
        self._next_handler = next_handler
        self.config = config or {}

    @abstractmethod
    def check(self, adata: ad.AnnData) -> bool:
        pass

    @abstractmethod
    def fix(self, adata: ad.AnnData) -> bool:
        pass

    def handle(self, adata: ad.AnnData) -> None:
        """
        处理给定的 AnnData 对象。

        如果条件不满足，尝试修复。如果修复失败，记录错误并返回。
        如果条件已满足，记录信息。
        如果存在下一个处理器，则传递 AnnData 对象给下一个处理器。

        Args:
            adata: 要处理的 AnnData 对象。

        Returns:
            None
        """
        if not self.check(adata):
            logger.info(
                f"{self.__class__.__name__}: Condition not met, attempting to fix."
            )
            if not self.fix(adata):
                logger.error(f"{self.__class__.__name__}: Failed to fix.")
                return
        else:
            logger.info(
                f"{self.__class__.__name__}: Condition already met, no need to fix."
            )
        if self._next_handler:
            self._next_handler.handle(adata)

    def set_next(self, next_handler: "Handler") -> "Handler":
        self._next_handler = next_handler
        return next_handler


class QualityControlHandler(Handler):
    def check(self, adata: ad.AnnData) -> bool:
        # 检查是否已经进行了质量控制
        return adata.uns.get("pipeline_processing_status", {}).get(
            "quality_control_applied", False
        )

    def fix(self, adata: ad.AnnData) -> bool:
        try:
            # 计算每个细胞的基因数目和每个基因的细胞数目
            adata.var["mt"] = adata.var_names.str.startswith(
                "MT-"
            )  # 人类线粒体基因前缀为 'MT-'
            sc.pp.calculate_qc_metrics(
                adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True
            )

            # 过滤掉低质量的细胞和基因
            adata = adata[
                adata.obs["n_genes_by_counts"] >= 200, :
            ]  # 至少有200个基因的细胞
            adata = adata[
                :, adata.var["n_cells_by_counts"] >= 3
            ]  # 至少在3个细胞中表达的基因

            # 保存过滤标记
            if "pipeline_processing_status" not in adata.uns:
                adata.uns["pipeline_processing_status"] = {}
            adata.uns["pipeline_processing_status"]["quality_control_applied"] = True
            logger.info("Quality control applied.")
            return True
        except Exception as e:
            logger.error(f"Failed to apply quality control: {e}")
            return False


class DoubletRemovalHandler(Handler):
    def check(self, adata: ad.AnnData) -> bool:
        # 检查是否已经进行了双细胞去除
        return adata.uns.get("pipeline_processing_status", {}).get(
            "doublet_removal_applied", False
        )

    def fix(self, adata: ad.AnnData) -> bool:
        try:
            import scrublet as scr

            scrub = scr.Scrublet(adata.X)
            doublet_scores, predicted_doublets = scrub.scrub_doublets()

            # 添加双细胞预测结果到.obs中
            adata.obs["doublet_score"] = doublet_scores
            adata.obs["predicted_doublet"] = predicted_doublets

            # 保存过滤标记
            if "pipeline_processing_status" not in adata.uns:
                adata.uns["pipeline_processing_status"] = {}
            adata.uns["pipeline_processing_status"]["doublet_removal_applied"] = True
            logger.info("Doublet removal applied.")
            return True
        except Exception as e:
            logger.error(f"Failed to remove doublets: {e}")
            return False


class NormalizationHandler(Handler):
    def check(self, adata: ad.AnnData) -> bool:
        # 检查是否已经进行了标准化
        return adata.uns.get("pipeline_processing_status", {}).get(
            "normalization_applied", False
        )

    def fix(self, adata: ad.AnnData) -> bool:
        try:
            # 保存原始计数数据
            if "counts" not in adata.layers:
                adata.layers["counts"] = adata.X.copy()

            # 归一化到每个细胞总计为1e4
            sc.pp.normalize_total(adata, target_sum=1e4)

            # 对数转换
            sc.pp.log1p(adata)

            # 保存归一化和对数转换后的数据
            adata.layers["normal"] = adata.X.copy()

            # 高度可变基因检测
            sc.pp.highly_variable_genes(
                adata, min_mean=0.0125, max_mean=3, min_disp=0.5
            )
            adata = adata[:, adata.var["highly_variable"]]

            # 保存过滤标记
            if "pipeline_processing_status" not in adata.uns:
                adata.uns["pipeline_processing_status"] = {}
            adata.uns["pipeline_processing_status"]["normalization_applied"] = True
            logger.info("Normalization and variable gene selection applied.")
            return True
        except Exception as e:
            logger.error(f"Failed to normalize data: {e}")
            return False


class SingleCellPP:
    def __init__(self):
        # 创建各个处理器实例
        self.handlers = [
            QualityControlHandler(),
            DoubletRemovalHandler(),
            NormalizationHandler(),
        ]
        # 链接处理器
        for i in range(len(self.handlers) - 1):
            self.handlers[i].set_next(self.handlers[i + 1])

    def run(self, adata: ad.AnnData) -> ad.AnnData:
        logger.info("Starting single-cell RNA-seq processing pipeline...")
        self.handlers[0].handle(adata)
        logger.info("Pipeline processing completed.")
        return adata


if __name__ == "__main__":
    # 加载AnnData对象
    adata = sc.read_h5ad("data/anndata_qc.h5ad")

    # 创建并运行数据处理工作流
    pipeline = SingleCellPP()
    processed_adata = pipeline.run(adata)

    # 保存处理后的AnnData对象
    processed_adata.write("data/anndata_res.h5ad")
