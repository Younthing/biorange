# biorange/cli/config/config_manager.py
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigManager:
    """配置器"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config = self.load_config(config_path)

    def load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        if config_path and config_path.exists():
            with config_path.open("r") as file:
                return yaml.safe_load(file)
        return {}

    def get_param(
        self, key: str, cli_value: Optional[Any], default_value: Optional[Any] = None
    ) -> Any:
        return cli_value or self.config.get(key, default_value)
