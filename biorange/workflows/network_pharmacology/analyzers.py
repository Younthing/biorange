from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import pandas as pd

from biorange.core.cache.cache_manager import CacheManagerFactory, GeneralCacheManager
from biorange.core.logger import get_logger
from biorange.workflows.network_pharmacology.abstract import BaseDataFetcher


class ComponentFinder:
    def __init__(
        self,
        strategies: List[BaseDataFetcher],
        cache_manager: GeneralCacheManager,
        max_workers: int = 5,
    ):
        self.strategies = strategies
        self.cache_manager = cache_manager
        self.max_workers = max_workers
        self.logger = get_logger("component_finder")

    def execute(self, drug_names: str | List[str]) -> pd.DataFrame:
        all_components = []
        if isinstance(drug_names, str):
            drug_names = [drug_names]
        for drug_name in drug_names:
            cache_key = f"components_{drug_name}"
            cached_data = self.cache_manager.get(cache_key)
            if cached_data is not None:
                self.logger.info(f"Cache hit for components of drug: {drug_name}")
                all_components.append(cached_data)
                continue

            self.logger.info(f"Finding components for drug: {drug_name}")
            components = self._run_strategies(drug_name)
            self.cache_manager.save(cache_key, components)
            all_components.append(components)

        # Combine all components into a single DataFrame
        return (
            pd.concat(all_components, ignore_index=True)
            if all_components
            else pd.DataFrame()
        )

    def _run_strategies(self, input_data: str) -> pd.DataFrame:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(strategy.fetch, input_data)
                for strategy in self.strategies
            ]
            results = [future.result() for future in as_completed(futures)]

        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


class SmilesTargetPredictor:
    def __init__(
        self,
        strategies: List[BaseDataFetcher],
        cache_manager: GeneralCacheManager,
        max_workers: int = 5,
    ):
        self.strategies = strategies
        self.cache_manager = cache_manager
        self.max_workers = max_workers
        self.logger = get_logger("target_predictor")

    def execute(self, components: pd.DataFrame) -> pd.DataFrame:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._predict_component_targets, component)
                for component in components["smiles"].unique()
            ]
            results = [future.result() for future in as_completed(futures)]

        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

    def _predict_component_targets(self, component: str) -> pd.DataFrame:
        cache_key = f"targets_{component}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.info(f"Cache hit for targets of component: {component}")
            return cached_data

        self.logger.info(f"Predicting targets for component: {component}")
        targets = self._run_strategies(component)
        self.cache_manager.save(cache_key, targets)
        return targets

    def _run_strategies(self, input_data: str) -> pd.DataFrame:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(strategy.fetch, input_data)
                for strategy in self.strategies
            ]
            results = [future.result() for future in as_completed(futures)]

        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


class DiseaseTargetFinder:
    def __init__(
        self,
        strategies: List[BaseDataFetcher],
        cache_manager: GeneralCacheManager,
        max_workers: int = 5,
    ):
        self.strategies = strategies
        self.cache_manager = cache_manager
        self.max_workers = max_workers
        self.logger = get_logger("disease_target_finder")

    def execute(self, disease_name: str) -> pd.DataFrame:
        cache_key = f"disease_targets_{disease_name}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.info(
                f"Cache hit for disease targets of disease: {disease_name}"
            )
            return cached_data

        self.logger.info(f"Finding disease targets for disease: {disease_name}")
        disease_targets = self._run_strategies(disease_name)
        self.cache_manager.save(cache_key, disease_targets)
        return disease_targets

    def _run_strategies(self, input_data: str) -> pd.DataFrame:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(strategy.fetch, input_data)
                for strategy in self.strategies
            ]
            results = [future.result() for future in as_completed(futures)]

        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


if __name__ == "__main__":
    from biorange.workflows.network_pharmacology.strategy import (
        CheMBLTargetPredictor,
        GenecardsTargetPredictor,
        OMIMTargetPredictor,
        STITCHTargetPredictor,
        TCMSPDrugComponentFinder,
        TCMSPTargetPredictor,
        TTDTargetPredictor,
    )

    cache_manager = GeneralCacheManager(
        CacheManagerFactory.create_cache_manager("redis")
    )

    component_finder = ComponentFinder([TCMSPDrugComponentFinder()], cache_manager)
    target_predictor = SmilesTargetPredictor(
        [CheMBLTargetPredictor(), STITCHTargetPredictor(), TCMSPTargetPredictor()],
        cache_manager,
    )
    disease_target_finder = DiseaseTargetFinder(
        [GenecardsTargetPredictor(), OMIMTargetPredictor(), TTDTargetPredictor()],
        cache_manager,
    )

    drug_name = ["大枣", "人参"]
    disease_name = "Lung cancer"

    # 定义结果目录
    from pathlib import Path

    results_dir = Path("results")

    # Step 1: Find Components
    components = component_finder.execute(drug_name)
    components.to_csv(results_dir / "components_.csv", index=False)

    # Step 2: Predict Targets
    targets = target_predictor.execute(components)
    targets.to_csv(results_dir / "targets_.csv", index=False)

    # Step 3: Find Disease Targets
    disease_targets = disease_target_finder.execute(disease_name)
    disease_targets.to_csv(results_dir / "disease_targets_.csv", index=False)
