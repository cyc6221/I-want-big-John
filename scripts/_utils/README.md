# _utils

這個資料夾放的是共用 Python helper module，提供其他 scripts import 使用。  
This folder contains shared Python helper modules that other scripts import.

## Included Files

- `lotto_result_downloads.py`
  Used by download-related scripts to fetch Taiwan Lottery result files.
- `lotto_stats_builder.py`
  Shared builder logic for `539`, `638`, and `649` stats JSON generation.
- `plot_utils.py`
  Shared plotting helpers for scripts that need chart-related utilities.

## Notes

這裡的檔案通常不是拿來單獨呼叫的入口腳本。  
Files here are usually support modules, not standalone entry scripts.

如果你在整理 `scripts/` 目錄時要找真正的可執行入口，優先看：

- `scripts/run.py`
- `scripts/run_tasks/`
- `scripts/README.md`
