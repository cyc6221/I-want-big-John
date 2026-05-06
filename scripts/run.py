import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUN_TASKS_DIR = ROOT / "scripts" / "run_tasks"

scripts = [
    RUN_TASKS_DIR / "build_latest_draws_data.py",
    RUN_TASKS_DIR / "build_instant_all.py",
    RUN_TASKS_DIR / "update_all_instants_articles_from_csv.py",
    RUN_TASKS_DIR / "build_instants_chosen_number_json.py",
    RUN_TASKS_DIR / "build_instants_per_month_json.py",
    RUN_TASKS_DIR / "build_539_stats_json.py",
    RUN_TASKS_DIR / "build_638_stats_json.py",
    RUN_TASKS_DIR / "build_649_stats_json.py",
]

env = dict(os.environ)
env["PYTHONIOENCODING"] = "utf-8"

failed = False

for script_path in scripts:
    script_label = script_path.relative_to(ROOT).as_posix()
    print(f"Running {script_label} ...")
    try:
        subprocess.run([sys.executable, str(script_path)], check=True, env=env, cwd=ROOT)
    except subprocess.CalledProcessError as exc:
        print(f"Failed: {script_label} (exit code: {exc.returncode})")
        failed = True

if failed:
    raise SystemExit(1)
