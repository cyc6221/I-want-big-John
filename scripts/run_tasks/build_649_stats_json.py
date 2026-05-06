import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _utils.lotto_stats_builder import main_for_paths


if __name__ == "__main__":
    main_for_paths("research/derived/649_all_years.csv", "docs/assets/data/649-stats.json")
