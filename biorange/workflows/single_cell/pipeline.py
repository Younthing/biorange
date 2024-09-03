# biorange/workflows/single_cell/pipeline.py
from celery import shared_task

from biorange.workflows.celery_task_executor import CeleryTaskExecutor
from biorange.workflows.single_cell.script.single_cell_pp import SingleCellPP


@shared_task
def process_single_cell_data(data):
    """处理单细胞数据的任务

    Args:
        data (adata): 输入数据

    Returns:
        str: 处理结果
    """
    # 实际的数据处理逻辑
    ## serial
    
    return "SingleCellPP 处理完成"


class SingleCellPipeline:
    def __init__(self):
        """初始化单细胞分析流程"""
        self.executor = CeleryTaskExecutor()

    def run(self, data: str) -> str:
        """运行单细胞分析流程

        Args:
            data (str): 输入数据

        Returns:
            str: 任务ID
        """
        import scanpy as sc

        # adata = sc.read_h5ad(data)

        return self.executor.execute(process_single_cell_data, data)
