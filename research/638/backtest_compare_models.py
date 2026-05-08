import csv
import json
from collections import Counter
from pathlib import Path

from lib_dataset import RESEARCH_638_DIR, build_payload, load_draws
from lib_features import number_features
from models import ALL_MODELS
from models.model_bayesian_smoothing import generate_predictions as generate_bayesian_smoothing
from models.model_basic_heuristic import generate_predictions as generate_basic_heuristic
from models.model_deficit_only import generate_predictions as generate_deficit_only
from models.model_gap_deficit_lr import generate_predictions as generate_gap_deficit_lr
from models.model_gap_deficit_recent_lr import generate_predictions as generate_gap_deficit_recent_lr
from models.model_gap_deficit_recent_time_lr_v2 import generate_predictions as generate_gap_deficit_recent_time_lr_v2
from models.model_gap_only import generate_predictions as generate_gap_only
from models.model_historical_frequency import generate_predictions as generate_historical_frequency
from models.model_markov_transition import generate_predictions as generate_markov_transition
from models.model_recent_window import generate_predictions as generate_recent_window
from models.model_time_decay import generate_predictions as generate_time_decay
from models.model_uniform_random import generate_predictions as generate_uniform_random


RECENT_DRAW_COUNT = 100
MIN_TRAIN_DRAWS = 120
PREDICTION_COUNT = 6
ATTEMPTS_PER_MODEL = 4000

OUTPUT_DIR = RESEARCH_638_DIR / "outputs" / "recent100"
DETAIL_DIR = OUTPUT_DIR / "details"
MODEL_CATALOG_PATH = RESEARCH_638_DIR / "model_catalog.md"
SUMMARY_JSON_PATH = OUTPUT_DIR / "model_comparison_summary.json"
SUMMARY_CSV_PATH = OUTPUT_DIR / "model_comparison_summary.csv"
SUMMARY_MD_PATH = OUTPUT_DIR / "model_comparison_summary.md"

MODEL_RUNNERS = {
    "uniform_random_v1": generate_uniform_random,
    "historical_frequency_v1": generate_historical_frequency,
    "bayesian_smoothing_v1": generate_bayesian_smoothing,
    "recent_window_v1": generate_recent_window,
    "time_decay_v1": generate_time_decay,
    "markov_transition_v1": generate_markov_transition,
    "gap_only_v1": generate_gap_only,
    "deficit_only_v1": generate_deficit_only,
    "gap_deficit_lr_v1": generate_gap_deficit_lr,
    "gap_deficit_recent_lr_v1": generate_gap_deficit_recent_lr,
    "gap_deficit_recent_time_lr_v2": generate_gap_deficit_recent_time_lr_v2,
    "basic_heuristic_v1": generate_basic_heuristic,
}


def match_count(predicted: list[int], actual: list[int]) -> int:
    return len(set(predicted) & set(actual))


def overlap_numbers(predicted: list[int], actual: list[int]) -> list[int]:
    return sorted(set(predicted) & set(actual))


def classify_failure(top1_main_hits: int, top1_second_hit: int, predicted_features: dict, actual_features: dict) -> list[str]:
    tags = []
    if top1_main_hits == 0:
        tags.append("main_zero_hit")
    elif top1_main_hits == 1:
        tags.append("main_one_hit")
    elif top1_main_hits >= 3:
        tags.append("main_good_hit")

    tags.append("second_hit" if top1_second_hit else "second_miss")

    if predicted_features["max_run"] != actual_features["max_run"]:
        tags.append("run_pattern_mismatch")
    if abs(predicted_features["odd_count"] - actual_features["odd_count"]) >= 2:
        tags.append("odd_even_bias")
    if abs(predicted_features["low_count"] - actual_features["low_count"]) >= 2:
        tags.append("low_high_bias")
    if abs(predicted_features["sum"] - actual_features["sum"]) >= 25:
        tags.append("sum_gap_large")
    if abs(predicted_features["spread"] - actual_features["spread"]) >= 10:
        tags.append("spread_gap_large")
    return tags


def evaluate_prediction_set(predictions: list[dict], actual_numbers: list[int], actual_second: int) -> dict:
    top1 = predictions[0]
    top1_overlap = overlap_numbers(top1["main_numbers"], actual_numbers)
    top1_main_hits = len(top1_overlap)
    top1_second_hit = int(top1["second_zone"] == actual_second)

    best_main_hits = 0
    any_second_hit = 0
    best_total_hits = 0
    for candidate in predictions:
        main_hits = match_count(candidate["main_numbers"], actual_numbers)
        second_hit = int(candidate["second_zone"] == actual_second)
        best_main_hits = max(best_main_hits, main_hits)
        any_second_hit = max(any_second_hit, second_hit)
        best_total_hits = max(best_total_hits, main_hits + second_hit)

    predicted_features = number_features(top1["main_numbers"])
    actual_features = number_features(actual_numbers)

    return {
        "top1_main_hits": top1_main_hits,
        "top1_second_hit": top1_second_hit,
        "best_of_6_main_hits": best_main_hits,
        "any_of_6_second_hit": any_second_hit,
        "best_of_6_total_hits": best_total_hits,
        "top1_prediction": top1,
        "top1_overlap_numbers": top1_overlap,
        "predicted_features": predicted_features,
        "actual_features": actual_features,
        "failure_tags": classify_failure(top1_main_hits, top1_second_hit, predicted_features, actual_features),
    }


def build_summary(rows: list[dict]) -> dict:
    total = len(rows)
    top1_main_distribution = Counter(row["top1_main_hits"] for row in rows)
    best6_main_distribution = Counter(row["best_of_6_main_hits"] for row in rows)
    failure_tag_counter = Counter(tag for row in rows for tag in row["failure_tags"])

    return {
        "tested_draws": total,
        "recent_draw_count": RECENT_DRAW_COUNT,
        "prediction_count_per_draw": PREDICTION_COUNT,
        "attempts_per_model": ATTEMPTS_PER_MODEL,
        "top1_avg_main_hits": round(sum(row["top1_main_hits"] for row in rows) / total, 4) if total else 0,
        "best6_avg_main_hits": round(sum(row["best_of_6_main_hits"] for row in rows) / total, 4) if total else 0,
        "top1_second_hit_rate": round(sum(row["top1_second_hit"] for row in rows) / total, 4) if total else 0,
        "any6_second_hit_rate": round(sum(row["any_of_6_second_hit"] for row in rows) / total, 4) if total else 0,
        "top1_at_least_3_main_rate": round(sum(row["top1_main_hits"] >= 3 for row in rows) / total, 4) if total else 0,
        "any6_at_least_3_main_rate": round(sum(row["best_of_6_main_hits"] >= 3 for row in rows) / total, 4) if total else 0,
        "top1_main_hit_distribution": dict(sorted(top1_main_distribution.items())),
        "best6_main_hit_distribution": dict(sorted(best6_main_distribution.items())),
        "failure_tag_counts": dict(sorted(failure_tag_counter.items())),
    }


def write_detail_csv(model_id: str, rows: list[dict]) -> Path:
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    path = DETAIL_DIR / f"{model_id}_recent100_details.csv"
    fieldnames = [
        "target_period", "target_date", "actual_main_numbers", "actual_second_zone",
        "predicted_main_numbers", "predicted_second_zone", "overlap_numbers",
        "top1_main_hits", "top1_second_hit", "best_of_6_main_hits", "any_of_6_second_hit",
        "best_of_6_total_hits", "predicted_odd_even", "actual_odd_even", "predicted_low_high",
        "actual_low_high", "predicted_sum", "actual_sum", "predicted_spread", "actual_spread",
        "predicted_max_run", "actual_max_run", "top1_score", "top_signals", "failure_tags",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            prediction = row["top1_prediction"]
            predicted = row["predicted_features"]
            actual = row["actual_features"]
            writer.writerow(
                {
                    "target_period": row["target_period"],
                    "target_date": row["target_date"],
                    "actual_main_numbers": " ".join(f"{n:02d}" for n in row["actual_main_numbers"]),
                    "actual_second_zone": f"{row['actual_second_zone']:02d}",
                    "predicted_main_numbers": " ".join(f"{n:02d}" for n in prediction["main_numbers"]),
                    "predicted_second_zone": f"{prediction['second_zone']:02d}",
                    "overlap_numbers": " ".join(f"{n:02d}" for n in row["top1_overlap_numbers"]),
                    "top1_main_hits": row["top1_main_hits"],
                    "top1_second_hit": row["top1_second_hit"],
                    "best_of_6_main_hits": row["best_of_6_main_hits"],
                    "any_of_6_second_hit": row["any_of_6_second_hit"],
                    "best_of_6_total_hits": row["best_of_6_total_hits"],
                    "predicted_odd_even": f"{predicted['odd_count']}-{predicted['even_count']}",
                    "actual_odd_even": f"{actual['odd_count']}-{actual['even_count']}",
                    "predicted_low_high": f"{predicted['low_count']}-{predicted['high_count']}",
                    "actual_low_high": f"{actual['low_count']}-{actual['high_count']}",
                    "predicted_sum": predicted["sum"],
                    "actual_sum": actual["sum"],
                    "predicted_spread": predicted["spread"],
                    "actual_spread": actual["spread"],
                    "predicted_max_run": predicted["max_run"],
                    "actual_max_run": actual["max_run"],
                    "top1_score": round(prediction["score"], 4),
                    "top_signals": " ".join(prediction["top_signals"]),
                    "failure_tags": ",".join(row["failure_tags"]),
                }
            )
    return path


def write_model_catalog() -> None:
    lines = [
        "# 638 Models",
        "",
        "以下依 `note.md` 與 `note2.md` 整理模型。先實作不依賴外部 ML 套件、可直接用現有資料落地的模型。",
        "",
        "## Naming Rule",
        "",
        "- 模型檔：`models/model_<name>.py`",
        "- 明細輸出：`outputs/recent100/details/<model_id>_recent100_details.csv`",
        "- 比較摘要：`outputs/recent100/model_comparison_summary.*`",
        "",
        "## Implemented Models",
        "",
    ]
    for model in ALL_MODELS:
        lines.extend([
            f"### `{model['id']}`",
            f"- Label: {model['label']}",
            f"- Family: {model['family']}",
            f"- Description: {model['description']}",
            "",
        ])
    lines.extend([
        "## Deferred Models",
        "",
        "以下模型在 `note.md` 有提到，但目前先不實作到這輪回測：",
        "",
        "- `random_forest_v1` / `gradient_boosting_v1`",
        "- `mlp_v1` / `rnn_v1` / `lstm_v1` / `gru_v1` / `transformer_encoder_v1`",
        "",
        "原因：它們需要更完整的特徵管線、訓練流程、模型序列化或外部依賴，不適合先混進目前這套純研究 baseline 比較腳本。",
    ])
    MODEL_CATALOG_PATH.write_text("\n".join(lines), encoding="utf-8")


def to_repo_relative(path: Path) -> str:
    return path.relative_to(RESEARCH_638_DIR).as_posix()


def write_summary_outputs(summary_rows: list[dict], summary_payload: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    SUMMARY_JSON_PATH.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with SUMMARY_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "model_id", "model_label", "family", "tested_draws",
                "top1_avg_main_hits", "best6_avg_main_hits", "top1_second_hit_rate",
                "any6_second_hit_rate", "top1_at_least_3_main_rate", "any6_at_least_3_main_rate",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    lines = [
        "# Recent 100 Draw Model Comparison",
        "",
        "| Model | Top1 Avg Main | Best6 Avg Main | Top1 2nd Hit | Any6 2nd Hit | Top1 Main>=3 | Any6 Main>=3 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| `{row['model_id']}` | {row['top1_avg_main_hits']:.4f} | {row['best6_avg_main_hits']:.4f} | "
            f"{row['top1_second_hit_rate']:.2%} | {row['any6_second_hit_rate']:.2%} | "
            f"{row['top1_at_least_3_main_rate']:.2%} | {row['any6_at_least_3_main_rate']:.2%} |"
        )
    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def build_payload_cache(draws: list[dict]) -> dict[int, dict]:
    start_index = max(MIN_TRAIN_DRAWS, len(draws) - RECENT_DRAW_COUNT)
    return {index: build_payload(draws[:index]) for index in range(start_index, len(draws))}


def run_backtest_for_model(model: dict, draws: list[dict], payload_cache: dict[int, dict]) -> tuple[list[dict], dict]:
    model_id = model["id"]
    runner = MODEL_RUNNERS[model_id]
    start_index = max(MIN_TRAIN_DRAWS, len(draws) - RECENT_DRAW_COUNT)
    results = []

    for index in range(start_index, len(draws)):
        actual = draws[index]
        payload = payload_cache[index]
        predictions = runner(payload, seed=index, attempts=ATTEMPTS_PER_MODEL, output_count=PREDICTION_COUNT)
        if not predictions:
            continue
        evaluation = evaluate_prediction_set(predictions, actual["numbers"], actual["second_zone"])
        results.append(
            {
                "target_period": actual["period"],
                "target_date": actual["date"],
                "actual_main_numbers": actual["numbers"],
                "actual_second_zone": actual["second_zone"],
                **evaluation,
            }
        )

    summary = build_summary(results)
    return results, summary


def main() -> None:
    draws = load_draws()
    payload_cache = build_payload_cache(draws)
    write_model_catalog()
    summary_rows = []
    summary_payload = {"config": {"recent_draw_count": RECENT_DRAW_COUNT, "min_train_draws": MIN_TRAIN_DRAWS, "attempts_per_model": ATTEMPTS_PER_MODEL}, "models": {}}

    for model in ALL_MODELS:
        results, summary = run_backtest_for_model(model, draws, payload_cache)
        detail_path = write_detail_csv(model["id"], results)
        summary_rows.append(
            {
                "model_id": model["id"],
                "model_label": model["label"],
                "family": model["family"],
                "tested_draws": summary["tested_draws"],
                "top1_avg_main_hits": summary["top1_avg_main_hits"],
                "best6_avg_main_hits": summary["best6_avg_main_hits"],
                "top1_second_hit_rate": summary["top1_second_hit_rate"],
                "any6_second_hit_rate": summary["any6_second_hit_rate"],
                "top1_at_least_3_main_rate": summary["top1_at_least_3_main_rate"],
                "any6_at_least_3_main_rate": summary["any6_at_least_3_main_rate"],
            }
        )
        summary_payload["models"][model["id"]] = {
            "meta": model,
            "summary": summary,
            "detail_csv": to_repo_relative(detail_path),
        }
        print(f"{model['id']}: Top1 avg main hits={summary['top1_avg_main_hits']}, Best6 avg main hits={summary['best6_avg_main_hits']}")

    write_summary_outputs(summary_rows, summary_payload)
    print(f"Model catalog: {MODEL_CATALOG_PATH}")
    print(f"Summary CSV: {SUMMARY_CSV_PATH}")
    print(f"Summary JSON: {SUMMARY_JSON_PATH}")
    print(f"Summary MD: {SUMMARY_MD_PATH}")


if __name__ == "__main__":
    main()
