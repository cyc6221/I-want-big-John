import subprocess

scripts = [
    "scripts/build_instants_all.py",
    "scripts/build_instants_chosen_number_json.py",
    "scripts/build_instants_per_month_json.py",
]

for s in scripts:
    print(f"Running {s} ...")
    try:
        subprocess.run(["python", s], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed: {s} (exit code: {e.returncode})")