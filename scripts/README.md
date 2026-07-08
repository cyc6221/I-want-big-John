# Scripts README

這份文件整理 `scripts/` 目錄內目前可用的腳本、用途與建議使用方式。  
This document describes the scripts under `scripts/`, what they do, and how they are expected to be used.

## Subfolders

- `run_tasks/`
  收納 `python scripts/run.py` 目前會依序執行的腳本；細節可看 `scripts/run_tasks/README.md`。
- `templates/`
  放手動建立內容時可複製的模板；細節可看 `scripts/templates/README.md`。
- `_utils/`
  放共用 Python helper module，通常不是直接執行的入口；細節可看 `scripts/_utils/README.md`。

`__pycache__/` 是 Python 自動產生的快取資料夾，不需要額外文件。  
`__pycache__/` is a Python-generated cache folder and does not need separate documentation.

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

### 3.5 Sync research data from downloads

```bash
python scripts/sync_lotto_research_data.py
```

這支腳本會把 `raw-data/lotto-result-downloads/{Year}/` 的官方 CSV 同步到 `research/by-game/{game}/{game}_{Year}.csv`（獎號補零成兩位數），並重建 `research/derived/{game}_all_years.csv`。`scripts/run.py` 的統計、購買紀錄與最新開獎都是讀 `research/derived/`，所以每月更新下載檔後、跑 `run.py` 之前要先跑這一步。預設只同步當年度；歷史年度通常不需要重寫。
This script syncs the official CSVs under `raw-data/lotto-result-downloads/{Year}/` into `research/by-game/{game}/{game}_{Year}.csv` (zero-padding ball numbers) and rebuilds `research/derived/{game}_all_years.csv`. Since `scripts/run.py` reads `research/derived/` for stats, purchase records, and latest draws, run this after updating downloads and before `run.py`. It defaults to the current year only; historical years normally stay untouched.

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

## Manual Lotto Result Updates

如果台灣彩券官方下載檔還沒更新，但已經知道某一期開獎號碼，可以先補在：

```text
raw-data/manual-lotto-results/{game}-manual-results.csv
```

例如 `raw-data/manual-lotto-results/638-manual-results.csv` 或 `raw-data/manual-lotto-results/649-manual-results.csv`。不同遊戲的手動開獎資料分開存放，不要混在同一份 CSV。

欄位格式：

```text
draw_no,draw_date,number1,number2,number3,number4,number5,number6,special
```

這個檔案只補開獎號碼，用來更新最新開獎與購買紀錄比對；銷售統計仍等官方下載檔更新後才納入。

## 638 Purchase Prize Rules

`raw-data/lotto-purchases/638-purchases.csv` 只保留購買紀錄必要欄位：

```text
purchase_date,draw_no,line_no,price,number1,number2,number3,number4,number5,number6,special
```

只要對應期別已有開獎結果，`scripts/run_tasks/build_638_purchases.py` 會依威力彩固定獎項自動計算獎別與獎金：

- 參獎：第一區 5 個 + 第二區，150,000 元
- 肆獎：第一區 5 個，20,000 元
- 伍獎：第一區 4 個 + 第二區，4,000 元
- 陸獎：第一區 4 個，800 元
- 柒獎：第一區 3 個 + 第二區，400 元
- 捌獎：第一區 2 個 + 第二區，200 元
- 玖獎：第一區 3 個，100 元
- 普獎：第一區 1 個 + 第二區，100 元

頭獎與貳獎是浮動獎金；如果命中這兩種，產出會顯示待填獎金。

## 649 Purchase Prize Rules

`raw-data/lotto-purchases/649-purchases.csv` 只保留購買紀錄必要欄位：

```text
purchase_date,draw_no,line_no,price,number1,number2,number3,number4,number5,number6
```

只要對應期別已有開獎結果，`scripts/run_tasks/build_649_purchases.py` 會依大樂透固定獎項自動計算獎別與獎金：

- 伍獎：任 4 個主號，2,000 元
- 陸獎：任 3 個主號 + 特別號，1,000 元
- 柒獎：任 2 個主號 + 特別號，400 元
- 普獎：任 3 個主號，400 元

頭獎、貳獎、參獎與肆獎是浮動獎金；如果命中這些獎項，產出會顯示待填獎金。

## New Instant Article Generator

```bash
python scripts/new_instant_article.py 5157
```

這支腳本從台灣彩券官方 API 抓上市公告與遊戲資料，由程式計算全部期望值數學，一次產出：

- `docs/_articles/all-instants/{期別}.md`（文章，格式同 5155/5156）
- `raw-data/instant-prize-structures/{期別}.json`（獎金結構資料源，可重生文章）
- `docs/_data/instants_compare.yml`（自動新增/更新該期條目）
- `raw-data/instant-games.json`（自動加入期別對照）

獎金結構與期望值一律由這支腳本取得與計算，不要手抄官網數字或自己手算。官網是 JS SPA，直接抓公告網址只會拿到空殼；腳本走的是官網背後的 JSON API（`Instant/List`、`Instant/Detail`、`News/List`、`News/Detail/{newsId}`），並用 `Instant/Detail` 交叉驗證售價、張數、日期與中獎率。

常用參數：

- `--news-url {公告網址}`：自動搜尋找不到公告時，直接指定上市公告網址。
- `--from-json {路徑}`：跳過網路抓取，用（人工修正過的）JSON 重新產出。公告解析失敗時，腳本會把原始內容存成 `raw-data/instant-prize-structures/{期別}.draft.json` 供整理後重跑。
- `--output {路徑}`：只把文章寫到指定路徑，不動 repo 其他檔案（驗證比對用）。
- `--force`：覆寫既有文章。

產完後記得跑 `python scripts/run.py`，讓 `親自實測` 與 `published` 從 `raw-data/all-instants.csv` 回填。

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
