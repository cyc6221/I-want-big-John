# 638 Research

這個資料夾是威力彩 `6/38` 預測研究區，目標不是直接產出正式產品，而是把不同想法做成可回測、可比較、可重跑的研究流程。

目前已經做過的方向包括：

- 純隨機基準
- 歷史頻率、近期窗口、時間衰減、Markov transition
- gap / deficit / mean-reversion 類模型
- 加入時間特徵與期數位置的 `v2` 模型

## 目前結論

截至目前最近 `100` 期回測，`uniform_random_v1` 仍然是最強基準，沒有任何已實作模型穩定打贏它。

重點不是「完全沒有訊號」，而是：

- `gap` 單獨使用幾乎沒用
- `deficit` 比 `gap` 有用
- 加入 `recent`、`time`、`period phase` 後有些微改善
- 但改善幅度仍不足以超過隨機基準

可直接看：

- 模型總覽：[model_catalog.md](./model_catalog.md)
- 最近 100 期比較：[outputs/recent100/model_comparison_summary.md](./outputs/recent100/model_comparison_summary.md)
- 結論摘要：[conclusion.md](./conclusion.md)

## 目錄

- `models/`
  每個模型一個檔案，命名規則是 `model_<name>.py`。
- `outputs/latest/`
  各模型對下一期的最新候選號碼。
- `outputs/recent100/`
  最近 `100` 期 rolling backtest 的比較結果與逐期明細。
- `outputs/hazard/`
  `gap` 與下一期開出機率的 hazard 診斷。
- `outputs/search/`
  mean-reversion 類模型的參數搜尋結果。
- `note.md`
  第一批模型研究筆記。
- `note2.md`
  gap / deficit / mean-reversion 延伸想法。

## 主要腳本

- `generate_model_predictions.py`
  產生所有已註冊模型的最新預測。
- `backtest_compare_models.py`
  用最近 `100` 期做模型比較，輸出摘要與逐期明細。
- `hazard_gap_diagnostic.py`
  檢查「gap 越大，下一期越容易開」是否真的有資料支持。
- `parameter_search_mean_reversion.py`
  對 mean-reversion 類模型測不同 `window` 與標準化設定。
- `build_predictor_data.py`
  建立早期單模型流程使用的中介資料 `638-predictor.json`。
- `predict_next_draw.py`
  早期基本模型的單獨預測腳本，現在可視為 legacy helper。

## 常用指令

```bash
python research/638/generate_model_predictions.py
python research/638/backtest_compare_models.py
python research/638/hazard_gap_diagnostic.py
python research/638/parameter_search_mean_reversion.py
```

如果要更新早期單模型資料：

```bash
python research/638/build_predictor_data.py
python research/638/predict_next_draw.py
```

## 輸出怎麼看

- `outputs/latest/model_latest_predictions.*`
  看各模型目前給出的候選號碼。
- `outputs/recent100/model_comparison_summary.*`
  看模型整體表現排名。
- `outputs/recent100/details/<model_id>_recent100_details.csv`
  看某個模型最近 `100` 期逐期失效模式。
- `outputs/hazard/gap_hazard_summary.md`
  看 `gap` 假說是否站得住腳。
- `outputs/search/mean_reversion_search_summary.md`
  看 mean-reversion 模型最佳參數。

## 目前保留原則

- 研究筆記、結論、模型程式與最新輸出保留
- 明顯過時的模型檔、陳舊 detail 輸出、`__pycache__` 清掉
- 這個資料夾只在 `research/638/` 內運作，不接到 `docs/` 或網站流程
