# 638 Research For AI

這份文件給之後接手的 AI / agent 快速定位 `research/638` 用。

## Scope

- 這裡是獨立研究區，不要把新東西接到 `docs/`、`scripts/run.py` 或其他資料夾。
- 目標是比較不同 `6/38` 預測模型，而不是宣稱可穩定預測中獎。
- 所有輸入資料都來自 `research/derived/638_all_years.csv`。

## Current State

- 已實作模型的註冊入口在 [models/__init__.py](./models/__init__.py)。
- 主比較腳本是 [backtest_compare_models.py](./backtest_compare_models.py)。
- 最新預測腳本是 [generate_model_predictions.py](./generate_model_predictions.py)。
- 目前最近 `100` 期回測最佳基準仍是 `uniform_random_v1`。
- `gap` 單獨訊號弱，`deficit` 比 `gap` 有用，`time` 類特徵只帶來小幅改善。

## Important Files

- [model_catalog.md](./model_catalog.md)
  已實作模型、命名規則、家族分類。
- [outputs/recent100/model_comparison_summary.md](./outputs/recent100/model_comparison_summary.md)
  最近 `100` 期的主比較表。
- [outputs/search/mean_reversion_search_summary.md](./outputs/search/mean_reversion_search_summary.md)
  mean-reversion 類模型參數搜尋結果。
- [outputs/hazard/gap_hazard_summary.md](./outputs/hazard/gap_hazard_summary.md)
  `gap` hazard 診斷摘要。
- [conclusion.md](./conclusion.md)
  對外可讀版結論。
- [note.md](./note.md)、[note2.md](./note2.md)
  原始研究想法與公式來源。

## Model Families

- `baseline`
  - `uniform_random_v1`
- `statistical`
  - `historical_frequency_v1`
  - `bayesian_smoothing_v1`
  - `recent_window_v1`
  - `time_decay_v1`
  - `markov_transition_v1`
- `mean_reversion`
  - `gap_only_v1`
  - `deficit_only_v1`
  - `gap_deficit_lr_v1`
  - `gap_deficit_recent_lr_v1`
  - `gap_deficit_recent_time_lr_v2`
- `heuristic`
  - `basic_heuristic_v1`

## Rules Shared By Predictions

- 第一區不能與歷史整組完全重複
- 不允許 `3` 連號以上
- `1` 和 `38` 視為相連
- 大多數腳本會輸出 `6` 組候選

## Regeneration Workflow

常用：

```bash
python research/638/generate_model_predictions.py
python research/638/backtest_compare_models.py
python research/638/hazard_gap_diagnostic.py
python research/638/parameter_search_mean_reversion.py
```

legacy 單模型流程：

```bash
python research/638/build_predictor_data.py
python research/638/predict_next_draw.py
```

## Performance Notes

- `backtest_compare_models.py` 慢是正常的。
- 它是 rolling backtest，不是一次性打分。
- 最近 `100` 期的每一期都只用當時之前的資料建模。
- 某些模型每期都要重新訓練或重新搜尋大量候選組合。
- 目前已做一層 payload cache，但主要耗時仍在 repeated scoring / repeated fitting。

## Cleanup Policy

- 可以清掉明顯過時的模型檔與其殘留輸出。
- 可以清掉 `__pycache__/`。
- 不要刪 `outputs/` 內仍被 README、結論、比較流程引用的主輸出。
- 若新增模型，記得同步更新：
  - `models/__init__.py`
  - `model_catalog.md`
  - `generate_model_predictions.py`
  - `backtest_compare_models.py`

## Recommended Next Steps

- 若要繼續做模型，優先從 `deficit_only` 或 `gap_deficit_recent_time_lr_v2` 往下做 `v2`。
- 若要提升研究效率，優先優化 backtest，而不是再加很多新模型。
- 若要做新的假說，先確保能塞進最近 `100` 期 rolling backtest，比單次預測更有意義。
