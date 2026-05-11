# Run Tasks

這個資料夾收納 `scripts/run.py` 目前會依序執行的腳本。  
This folder contains the scripts currently executed by `scripts/run.py`.

## Included Scripts

- `build_latest_draws_data.py`
- `build_638_purchases.py`
- `build_instant_all.py`
- `update_all_instants_articles_from_csv.py`
- `build_instants_chosen_number_json.py`
- `build_instants_per_month_json.py`
- `build_539_stats_json.py`
- `build_638_stats_json.py`
- `build_649_stats_json.py`

## How To Use

平常建議直接跑：

```bash
python scripts/run.py
```

這樣會用固定順序一次更新目前已接入的 instant / lotto 產檔。  
This runs the current instant / lotto build tasks in the expected order.

如果真的要單獨執行，也請用這個資料夾底下的新路徑，例如：

```bash
python scripts/run_tasks/build_638_purchases.py
python scripts/run_tasks/build_instant_all.py
python scripts/run_tasks/update_all_instants_articles_from_csv.py
```

如果你不確定哪一支該先跑，優先用 `python scripts/run.py`。  
If you're not sure which one should run first, prefer `python scripts/run.py`.
