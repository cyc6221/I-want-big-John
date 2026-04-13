import os
import subprocess

scripts = [
    "scripts/build_instant_all.py",
    "scripts/build_instants_chosen_number_json.py",
    "scripts/build_instants_per_month_json.py",
]

env = dict(os.environ)
env["PYTHONIOENCODING"] = "utf-8"

for s in scripts:
    print(f"Running {s} ...")
    try:
        subprocess.run(["python", s], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Failed: {s} (exit code: {e.returncode})")
