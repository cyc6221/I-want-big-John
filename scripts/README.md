# Scripts README

這份文件整理 `scripts/` 目錄內目前可用的腳本、用途與建議使用方式。  
This document describes the scripts under `scripts/`, what they do, and how they are expected to be used.

## Lotto Result Download Workflow

建議的順序是先下載、再解壓、最後視需要補修檔名或路徑。  
The recommended order is download first, then extract, and finally fix filenames or paths if needed.

### 1. Download annual zip files

```bash
python scripts/download_lotto_results.py --from-year 2007 --to-year 2026
```

這支腳本會從台灣彩券下載各年度的開獎結果 zip 檔，存到 `raw-data/lotto-result-downloads/zip/`。  
This script downloads annual Taiwan Lottery result zip files into `raw-data/lotto-result-downloads/zip/`.

### 2. Extract annual zip files

```bash
python scripts/extract_lotto_results.py --from-year 2007 --to-year 2026 --overwrite
```

這支腳本會把各年度 zip 解壓到 `raw-data/lotto-result-downloads/{Year}/`，並在解壓後自動修正多包一層資料夾的問題。  
This script extracts each annual zip into `raw-data/lotto-result-downloads/{Year}/` and automatically fixes single nested-folder issues after extraction.

### 3. Fix nested folder paths only

```bash
python scripts/fix_lotto_result_paths.py --from-year 2007 --to-year 2026
```

這支腳本只修正目錄結構，適合處理像 `2007/96/` 或 `2024/2024/` 這種多包一層的舊資料。  
This script only fixes directory structure, which is useful for older extracted data such as `2007/96/` or `2024/2024/`.

### 4. Normalize filenames to `{Game}_{Year}.csv`

```bash
python scripts/fix_lotto_result_filenames.py --from-year 2007 --to-year 2026
```

這支腳本會把檔名統一成 `{Game}_{Year}.csv`，例如把 `38樂合彩_201801_201812.csv` 改成 `38樂合彩_2018.csv`。  
This script normalizes filenames to `{Game}_{Year}.csv`, for example changing `38樂合彩_201801_201812.csv` to `38樂合彩_2018.csv`.

如果只想先預覽，不要真的改名，可以加上 `--dry-run`。  
If you only want to preview changes, add `--dry-run`.

## Run Tasks

`python scripts/run.py` 目前會依序呼叫的腳本，已整理到 `scripts/run_tasks/`。  
The scripts currently orchestrated by `python scripts/run.py` are now grouped under `scripts/run_tasks/`.

如果你不確定某支 build script 能不能單獨跑，優先直接執行：

```bash
python scripts/run.py
```

更完整的清單與說明可看：

```text
scripts/run_tasks/README.md
```

## Instant Data Scripts

### 5. Build instants all markdown

```bash
python scripts/run_tasks/build_instant_all.py
```

這支腳本會根據 `raw-data/all-instants.csv` 產生 `docs/_list/instants-all.md`。  
This script generates `docs/_list/instants-all.md` from `raw-data/all-instants.csv`.

### 6. Build instants per-month JSON

```bash
python scripts/run_tasks/build_instants_per_month_json.py
```

這支腳本會產生 `docs/assets/data/instants-per-month.json`。  
This script generates `docs/assets/data/instants-per-month.json`.

### 7. Build instants chosen-number JSON

```bash
python scripts/run_tasks/build_instants_chosen_number_json.py
```

這支腳本會產生 `docs/assets/data/instants-chosen-number.json`。  
This script generates `docs/assets/data/instants-chosen-number.json`.

### 8. Run all current instant build scripts

```bash
python scripts/run.py
```

這支腳本會依序執行目前已接入的 instant 相關產檔腳本。  
This script runs the currently wired instant-related build scripts in sequence.

## Lotto Stats Validation

### 9. Validate lotto stats assets and page wiring

```bash
python scripts/validate_lotto_stats.py
```

這支腳本會檢查樂透統計頁需要的關鍵檔案是否齊全，包括 `docs/assets/vendor/chart.umd.min.js`、`docs/assets/data/{539,638,649}-stats.json`，以及 `docs/pages/{539,638,649}.md` 內是否包含正確的 stats include。  
This script validates the required lotto stats assets and page wiring, including `docs/assets/vendor/chart.umd.min.js`, `docs/assets/data/{539,638,649}-stats.json`, and the expected stats include inside `docs/pages/{539,638,649}.md`.

它不會重建資料，只會驗證檔案存在與 JSON / include 結構是否合理。  
It does not rebuild data; it only validates file presence and the expected JSON / include structure.
