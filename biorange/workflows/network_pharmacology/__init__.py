# 定义结果目录
from pathlib import Path

results_dir = Path("results")

# 确保结果目录存在
results_dir.mkdir(parents=True, exist_ok=True)
