"""尝试分析流，记得使用依赖注入，考虑celery等"""

from pathlib import Path
from typing import List

import yaml

from biorange.core.cache.cache_manager import CacheManagerFactory, GeneralCacheManager
from biorange.workflows.network_pharmacology.analyzers import (
    ComponentFinder,
    DiseaseTargetFinder,
    SmilesTargetPredictor,
)
from biorange.workflows.network_pharmacology.strategy import (
    CheMBLTargetPredictor,
    GenecardsTargetPredictor,
    OMIMTargetPredictor,
    STITCHTargetPredictor,
    TCMSPDrugComponentFinder,
    TCMSPTargetPredictor,
    TTDTargetPredictor,
)

cache_manager = GeneralCacheManager(CacheManagerFactory.create_cache_manager("redis"))

component_finder = ComponentFinder([TCMSPDrugComponentFinder()], cache_manager)
target_predictor = SmilesTargetPredictor(
    [CheMBLTargetPredictor(), STITCHTargetPredictor(), TCMSPTargetPredictor()],
    cache_manager,
)
disease_target_finder = DiseaseTargetFinder(
    [GenecardsTargetPredictor(), OMIMTargetPredictor(), TTDTargetPredictor()],
    cache_manager,
)


def run_analysis(config_manager):
    """
    运行分析过程，包括查找成分、预测靶点和查找疾病靶点。

    Args:
        config_manager (ConfigManager): 配置管理器对象，包含所有配置和参数。
    """
    # 从配置中获取参数
    drug_name: List[str] = config_manager.settings.drug_name
    disease_name: str = config_manager.settings.disease_name
    results_dir: Path = Path(config_manager.settings.results_dir)

    # 确保结果目录存在
    results_dir.mkdir(parents=True, exist_ok=True)

    # 将用到的参数写入 config.yaml 文件
    config_data = {
        "drug_name": drug_name,
        "disease_name": disease_name,
        "results_dir": str(results_dir),
    }
    with open(results_dir / "config.yaml", "wt", encoding="utf-8") as config_file:
        yaml.dump(config_data, config_file, allow_unicode=True)

    # Step 1: Find Components
    components = component_finder.execute(drug_name)
    components.to_csv(results_dir / "components_.csv", index=False)

    # Step 2: Predict Targets
    targets = target_predictor.execute(components)
    targets.to_csv(results_dir / "targets_.csv", index=False)

    # Step 3: Find Disease Targets
    disease_targets = disease_target_finder.execute(disease_name)
    disease_targets.to_csv(results_dir / "disease_targets_.csv", index=False)

    print("Analysis completed successfully.")
