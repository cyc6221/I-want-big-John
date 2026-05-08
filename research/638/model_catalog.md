# 638 Models

以下依 `note.md` 與 `note2.md` 整理模型。先實作不依賴外部 ML 套件、可直接用現有資料落地的模型。

## Naming Rule

- 模型檔：`models/model_<name>.py`
- 明細輸出：`outputs/recent100/details/<model_id>_recent100_details.csv`
- 比較摘要：`outputs/recent100/model_comparison_summary.*`

## Implemented Models

### `uniform_random_v1`
- Label: Uniform Random V1
- Family: baseline
- Description: 均勻隨機抽號，作為理論隨機基準；遵守不重複歷史整組與禁止3連號以上。

### `historical_frequency_v1`
- Label: Historical Frequency V1
- Family: statistical
- Description: 使用全歷史出現次數作為機率分數，直接取 Top-6。

### `bayesian_smoothing_v1`
- Label: Bayesian Smoothing V1
- Family: statistical
- Description: 在歷史頻率上加入 Laplace smoothing，避免極端估計。

### `recent_window_v1`
- Label: Recent Window V1
- Family: statistical
- Description: 使用最近 30 期窗口頻率作為分數，較重視短期活躍度。

### `time_decay_v1`
- Label: Time Decay V1
- Family: statistical
- Description: 對較近期資料給較高權重的指數衰減模型。

### `markov_transition_v1`
- Label: Markov Transition V1
- Family: statistical
- Description: 估計上一期號碼到下一期號碼的轉移強度，並以轉移分數排序。

### `gap_only_v1`
- Label: Gap Only V1
- Family: mean_reversion
- Description: 只使用 gap = 距離上次出現多久，gap 越大分數越高。

### `deficit_only_v1`
- Label: Deficit Only V1
- Family: mean_reversion
- Description: 只使用標準化 deficit，越低於理論平均的號碼分數越高。

### `gap_deficit_lr_v1`
- Label: Gap Deficit LR V1
- Family: mean_reversion
- Description: 用 gap、標準化 deficit 做輕量 logistic regression。

### `gap_deficit_recent_lr_v1`
- Label: Gap Deficit Recent LR V1
- Family: mean_reversion
- Description: 用 gap、標準化 deficit、近期頻率做輕量 logistic regression。

### `gap_deficit_recent_time_lr_v2`
- Label: Gap Deficit Recent Time LR V2
- Family: mean_reversion
- Description: 在 gap、deficit、近期頻率之外，再加入月份、星期、年內期數位置的時間特徵。

### `basic_heuristic_v1`
- Label: Basic Heuristic V1
- Family: heuristic
- Description: 歷史頻率 + 近30/60期熱度 + 遺漏期數加權，並加上形狀分數。

## Deferred Models

以下模型在 `note.md` 有提到，但目前先不實作到這輪回測：

- `random_forest_v1` / `gradient_boosting_v1`
- `mlp_v1` / `rnn_v1` / `lstm_v1` / `gru_v1` / `transformer_encoder_v1`

原因：它們需要更完整的特徵管線、訓練流程、模型序列化或外部依賴，不適合先混進目前這套純研究 baseline 比較腳本。