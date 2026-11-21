# IWBJ

## I Want Big John

我的台灣彩券研究小站：誠實記錄真實的購買花費與中獎結果，整理玩法資訊、歷史開獎統計、刮刮樂期望值，並用資料回答「這些玩法與選號策略到底划不划算」。

## 網站內容

| 區塊 | 路徑 | 內容 |
| --- | --- | --- |
| 威力彩（6/38） | `/638/` | 最新開獎、研究文章、抽一組、統計資訊、購買紀錄、每月統計 |
| 大樂透（6/49） | `/649/` | 同上，另有歷年春節／端午／中秋加碼活動文章 |
| 今彩 539（5/39） | `/539/` | 最新開獎、抽一組、統計資訊、購買紀錄、每月統計 |
| 刮刮樂 | `/instant/` | 逐期文章（官方獎項結構與期望值）、全部比較、全紀錄、選號紀錄、每月統計 |
| 加碼 | `/bonus/` | 大樂透加碼活動辦法與開獎統計 |
| 紀錄 | `/list/` | 其他手動維護的紀錄（例如賓果 BINGO 三星加碼活動） |
| 全部文章 | `/all-articles/` | 全站文章，可依遊戲／標籤篩選 |

「抽一組」（`/{539,638,649}/pick/`）是選號推薦工具，含連續號碼限制。

## 運作方式

資料單向流動：`raw-data/`（唯一資料源頭）→ `scripts/run.py` → `docs/` 內的 Markdown 與 JSON → Jekyll 建置 → GitHub Pages。

```text
raw-data/                      人工維護的資料源頭
  all-instants.csv             刮刮樂購買紀錄
  lotto-purchases/             539 / 638 / 649 購買紀錄（只記基本欄位，獎項與獎金由腳本依開獎結果計算）
  lotto-result-downloads/      台彩官方年度開獎檔（勿手改）
  manual-lotto-results/        官方檔尚未更新時的暫存開獎號碼
  instant-prize-structures/    刮刮樂獎項結構（由腳本從官方 API 產生）
scripts/                       Python 資料管線
docs/                          Jekyll 網站（自帶 layout 與 SCSS，不依賴 theme gem）
research/                      官方開獎整理資料與離線研究（不進網站建置）
notes/                         某個時間點的專案快照
```

開獎結果多一道中繼：`lotto-result-downloads/` → `sync_lotto_research_data.py` → `research/derived/{game}_all_years.csv`，`run.py` 實際讀的是這裡。

`docs/_list/{539,638,649}-purchases.md`、`docs/_list/instants-all.md`、`docs/assets/data/*.json`、`docs/_data/latest_draws.json` 都是產生檔，請勿手改。

## 常用指令

```bash
# 編輯 raw-data/ 之後，重建所有衍生檔
python scripts/run.py

# 建置網站（在 docs/ 底下）
cd docs && bundle exec jekyll build

# 驗證統計頁資產與頁面串接
python scripts/validate_lotto_stats.py

# 由官方資料建立新的刮刮樂文章（獎項與期望值全由腳本計算，不要手抄）
python scripts/new_instant_article.py 5157

# 下市期別移到存檔區
python scripts/archive_instant_article.py 5123

# 更新官方開獎結果（sync 一步必須在 run.py 之前）
python scripts/download_lotto_results.py --from-year 2007 --to-year 2026
python scripts/extract_lotto_results.py --from-year 2007 --to-year 2026 --overwrite
python scripts/sync_lotto_research_data.py
```

專案沒有自動化測試；驗證方式是重跑 `python scripts/run.py`、檢視產生的 diff，再用 Jekyll 建置確認。

## 研究

- `research/638/`：威力彩第一區的預測模型回測（多種模型家族，rolling backtest）。目前結論是**隨機基準最強，沒有模型能穩定打敗它**，詳見 [`research/638/conclusion.md`](research/638/conclusion.md)。
- 威力彩頁另有兩篇統計研究文章（連號型態、走勢）。

## 自動化（GitHub Actions）

- `Data Validation`：PR／push 到 `main` 時重跑 `run.py` 並比對 diff，防止手改產生檔，同時執行 `validate_lotto_stats.py`。
- `Deploy Pages`：push 到 `main` 後建置 Jekyll 並部署到 GitHub Pages。
- `Update BINGO`：定時抓取 BINGO BINGO 開獎資料，寫入獨立的 `bingo-data` 分支（不經過 `main`、不屬於 `run.py`）。資料格式見 [`scripts/bingo/README.md`](scripts/bingo/README.md)。

## 相關文件

- [`CLAUDE.md`](CLAUDE.md) / [`AGENTS.md`](AGENTS.md)：分支、PR、commit 慣例與各類資料更新的步驟。
- [`scripts/README.md`](scripts/README.md)：各腳本用途與判獎規則。
- [`notes/`](notes/)：專案現況快照。

## 資料來源

- [台灣彩券官方網站](https://www.taiwanlottery.com/)
- [電腦型彩券「BINGO BINGO 賓果賓果」附加玩法發行事宜](https://lotto.ctbcbank.com/news990206.pdf)
