# 專案現況總結（2026-07-11）

> 這是某個時間點的專案快照，供之後回顧「當時的狀態與判斷」用。若要看目前實際狀態，
> 以程式碼與 `todo` 為準；本文件不會隨程式碼更新而同步修改。

## 1. 主要目標
台灣彩券研究小站：把手動輸入的實際購買/開獎資料，轉成可視化的統計頁與期望值文章，
目前涵蓋三種開獎遊戲（威力彩638、大樂透649、今彩539）與刮刮樂（instants）。核心目的
是誠實記錄真實花費與中獎結果（而非行銷式報喜不報憂），並用資料回答「這些玩法/選號策
略到底划不划算」。research/638 另外有一條獨立的預測模型研究線，目前結論是「隨機基準
最強，沒有模型能穩定打敗它」。

## 2. 主要資料夾與檔案用途
- `raw-data/`：唯一資料源頭（人工維護）。`all-instants.csv`（刮刮樂購買）、
  `lotto-purchases/{539,638,649}-purchases.csv`（開獎遊戲購買，只存基本欄位，獎項/獎
  金由 script 算）、`lotto-result-downloads/`（官方下載檔，不可手改）、
  `manual-lotto-results/`（官方檔還沒更新前的暫存開獎號碼）、`instant-prize-structures/`
  + `instant-games.json`（刮刮樂獎金結構資料源）。
- `scripts/`：Python pipeline。`run.py` 依序執行 `run_tasks/` 下所有產檔腳本；
  `new_instant_article.py` 從官方 API 產生刮刮樂文章與期望值計算；
  `sync_lotto_research_data.py` 把官方下載檔同步進 `research/derived/`（`run.py` 實際讀
  的是這裡，不是 `lotto-result-downloads/` 原始檔）；`validate_lotto_stats.py` 驗證統計
  頁需要的檔案都齊全。
- `docs/`：Jekyll 網站本體。`pages/` 是 5 個主要頁面（638/649/539/instant/list），
  `_articles/`（30 篇：638 研究 2 篇、649 研究 1 篇、刮刮樂逐期文章 27 篇）、`_list/`
  （產生的購買/選號紀錄頁，多數由 script 產生，也有少數是手動維護的靜態表格如
  638/649-purchases）、`_includes/`（可重用元件：`lotto/stats.html` 銷售統計圖表、
  `instants/*` 刮刮樂選號/月統計圖表、`small-balls.html` 球號渲染）、`assets/data/`
  （前端 fetch 的 JSON）、`assets/js/recommender_{game}.js` + `tools/recommender_*.html`
  （選號推薦工具）。
- `research/`：`derived/` 與 `by-game/` 是官方開獎資料的整理版，餵給主 pipeline 也餵給
  `research/638/` 的獨立預測模型回測研究（12 個模型、4 個家族，純研究用，不進 Jekyll
  build）。
- `.github/workflows/`：`data-validation.yml`（PR/push 到 main 時重跑 `run.py` 並 diff，
  防止手改產生檔）、`pages.yml`（push main 後自動 build+deploy 到 GitHub Pages）。

## 3. 目前已完成的功能
- 三種開獎遊戲（539/638/649）的購買紀錄 → 自動判獎 → 統計 JSON → 網站圖表，三者功能
  對稱（539 是 2026-07-10 才補齊，此前只有 stats JSON）。
- 27 篇刮刮樂文章的全自動產生流程（官方 API 抓公告 → 算期望值 → 產文章/JSON/比較表），
  含「親自實測」中獎紀錄回填與月度/選號統計圖表。
- 638/649 選號推薦工具（含連續號碼限制邏輯），539 版本也已存在。
- CI 防手改產生檔的紅燈機制（`data-validation.yml`），以及自動部署到 GitHub Pages。
- `research/638` 的完整回測框架與明確結論文件（`conclusion.md`）。

## 4. 目前可執行的測試 / CLI / scripts
- **沒有真正的自動化測試**（無 pytest/unittest，無 `tests/` 目錄，無 linter/pre-commit
  設定）。「測試」等同於重跑 pipeline 比對 diff。
- 主要 CLI：
  - `python scripts/run.py`（重建所有產生檔，日常開發後一定要跑）
  - `python scripts/new_instant_article.py {期別}`（產生刮刮樂文章）
  - `python scripts/download_lotto_results.py` → `extract_lotto_results.py` →
    `sync_lotto_research_data.py`（刷新官方開獎資料，三步缺一不可，順序固定）
  - `python scripts/validate_lotto_stats.py`（驗證統計頁資產）
  - `cd docs && bundle exec jekyll build`（驗證網站能建置）
  - `research/638/` 下的回測腳本（`backtest_compare_models.py` 等）是獨立研究工具，
    不影響網站。

## 5. 當時判斷的最重要待辦
（後續移到 `todo` 追蹤實際進度，這裡只留存判斷當下的理由）
1. **【中】產生檔加「請勿手改」標頭** — CI 已經會擋手改，但要等 PR 才發現；加標頭能
   讓人打開檔案當下就知道，屬於低成本、高可用性的改善。
2. **【低】研究成果上網站** — `research/638` 的「隨機基準最強」結論目前只存在 repo
   內，638 頁的研究區塊只有 2 篇文章，沒有連結到這個結論。屬於錦上添花，不影響資料
   正確性。
3. **【新發現】`assets/data/{539,638,649}-purchases.json` 疑似死碼** —
   Explore 掃描發現這三個 JSON 由 pipeline 產生，但前端沒有任何頁面引用它們（實際購
   買紀錄頁 `_list/*-purchases.md` 是靜態表格），值得確認是規劃中的未來功能還是可以砍
   掉的產出，避免維護負擔。
4. **【新發現】Chart.js 來源不一致** — `lotto/stats.html` 用本地 vendor 檔
   （`assets/vendor/chart.umd.min.js`），但 `instants/*` 系列改用 jsDelivr CDN，兩套
   圖表系統載入方式不一致，之後若要離線可用或鎖版本會是隱患。

## 6. 建議的後續開發順序
1. 先確認「待辦 3」（購買 JSON 是否真的沒人用）——這是理解現況、不影響現有功能的低風
   險確認，能避免之後改錯方向。
2. 若確認是死碼，評估是否要接上前端（例如取代 `_list/*-purchases.md` 現有的靜態表格，
   改成跟刮刮樂一樣的 JSON-driven 頁面，統一資料展示方式）或乾脆從 `run.py` pipeline
   移除以減少維護面。
3. 處理「產生檔標頭」，成本低、立即提升可維護性，適合當作暖身任務。
4. 之後再排「研究成果上網站」與 Chart.js 來源統一，兩者都是體驗面的打磨，非阻塞性。
5. 若之後常態性有回歸疑慮（例如判獎規則、期望值計算），可考慮補上最小可行的 pytest
   單元測試（針對 `build_{game}_purchases.py` 的固定獎項判定邏輯、`new_instant_article.py`
   的期望值計算），目前完全靠 CI diff 撐著，邏輯本身沒有單元測試覆蓋。
