import os
import subprocess

scripts = [
    "scripts/build_latest_draws_data.py",
    "scripts/build_instant_all.py",
    "scripts/update_all_instants_articles_from_csv.py",
    "scripts/build_instants_chosen_number_json.py",
    "scripts/build_instants_per_month_json.py",
    "scripts/build_539_stats_json.py",
]

env = dict(os.environ)
env["PYTHONIOENCODING"] = "utf-8"

for s in scripts:
    print(f"Running {s} ...")
    try:
        subprocess.run(["python", s], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Failed: {s} (exit code: {e.returncode})")
