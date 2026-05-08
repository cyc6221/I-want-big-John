import csv
import json
from pathlib import Path

from lib_dataset import RESEARCH_638_DIR, build_payload, load_draws
from models.model_deficit_only import generate_predictions_with_config as generate_deficit_only_with_config
from models.model_gap_deficit_recent_lr import generate_predictions_with_config as generate_gap_deficit_recent_with_config


RECENT_DRAW_COUNT = 100
MIN_TRAIN_DRAWS = 120
OUTPUT_DIR = RESEARCH_638_DIR / "outputs" / "search"
SUMMARY_JSON_PATH = OUTPUT_DIR / "mean_reversion_search_summary.json"
SUMMARY_CSV_PATH = OUTPUT_DIR / "mean_reversion_search_summary.csv"
SUMMARY_MD_PATH = OUTPUT_DIR / "mean_reversion_search_summary.md"


def match_count(predicted: list[int], actual: list[int]) -> int:
    return len(set(predicted) & set(actual))


def evaluate_predictions(predictions: list[dict], actual_numbers: list[int], actual_second: int) -> dict:
    top1 = predictions[0]
    top1_main_hits = match_count(top1["main_numbers"], actual_numbers)
    top1_second_hit = int(top1["second_zone"] == actual_second)

    best_main_hits = 0
    any_second_hit = 0
    for candidate in predictions:
        best_main_hits = max(best_main_hits, match_count(candidate["main_numbers"], actual_numbers))
        any_second_hit = max(any_second_hit, int(candidate["second_zone"] == actual_second))

    return {
        "top1_main_hits": top1_main_hits,
        "best6_main_hits": best_main_hits,
        "top1_second_hit": top1_second_hit,
        "any6_second_hit": any_second_hit,
    }


def summarize(results: list[dict]) -> dict:
    total = len(results)
    return {
        "tested_draws": total,
        "top1_avg_main_hits": round(sum(row["top1_main_hits"] for row in results) / total, 4) if total else 0.0,
        "best6_avg_main_hits": round(sum(row["best6_main_hits"] for row in results) / total, 4) if total else 0.0,
        "top1_second_hit_rate": round(sum(row["top1_second_hit"] for row in results) / total, 4) if total else 0.0,
        "any6_second_hit_rate": round(sum(row["any6_second_hit"] for row in results) / total, 4) if total else 0.0,
        "top1_at_least_3_main_rate": round(sum(row["top1_main_hits"] >= 3 for row in results) / total, 4) if total else 0.0,
        "any6_at_least_3_main_rate": round(sum(row["best6_main_hits"] >= 3 for row in results) / total, 4) if total else 0.0,
    }


def build_payload_cache(draws: list[dict]) -> dict[int, dict]:
    start_index = max(MIN_TRAIN_DRAWS, len(draws) - RECENT_DRAW_COUNT)
    cache = {}
    for index in range(start_index, len(draws)):
        cache[index] = build_payload(draws[:index])
    return cache


def evaluate_config(draws: list[dict], payload_cache: dict[int, dict], generator) -> list[dict]:
    start_index = max(MIN_TRAIN_DRAWS, len(draws) - RECENT_DRAW_COUNT)
    rows = []
    for index in range(start_index, len(draws)):
        actual = draws[index]
        payload = payload_cache[index]
        predictions = generator(payload)
        if not predictions:
            continue
        rows.append(evaluate_predictions(predictions, actual["numbers"], actual["second_zone"]))
    return rows


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    draws = load_draws()
    payload_cache = build_payload_cache(draws)

    search_rows = []
    payload = {"deficit_only": [], "gap_deficit_recent_lr": []}

    deficit_windows = [None, 30, 50, 100, 150]
    normalize_modes = ["raw", "z", "ratio"]
    for window in deficit_windows:
        for normalize_mode in normalize_modes:
            label = f"deficit_only(window={window or 'all'}, norm={normalize_mode})"
            results = evaluate_config(
                draws,
                payload_cache,
                lambda cached_payload, window=window, normalize_mode=normalize_mode: generate_deficit_only_with_config(
                    cached_payload,
                    window=window,
                    normalize_mode=normalize_mode,
                    output_count=6,
                ),
            )
            summary = summarize(results)
            row = {
                "group": "deficit_only",
                "config": label,
                "window": window or "all",
                "normalize_mode": normalize_mode,
                "recent_window": "",
                **summary,
            }
            search_rows.append(row)
            payload["deficit_only"].append(row)

    lr_windows = [15, 30, 50, 100]
    lr_norms = ["raw", "z", "ratio"]
    for recent_window in lr_windows:
        for deficit_mode in lr_norms:
            label = f"gap_deficit_recent_lr(window={recent_window}, norm={deficit_mode})"
            results = evaluate_config(
                draws,
                payload_cache,
                lambda cached_payload, recent_window=recent_window, deficit_mode=deficit_mode: generate_gap_deficit_recent_with_config(
                    cached_payload,
                    recent_window=recent_window,
                    deficit_mode=deficit_mode,
                    epochs=6,
                    learning_rate=0.08,
                    output_count=6,
                ),
            )
            summary = summarize(results)
            row = {
                "group": "gap_deficit_recent_lr",
                "config": label,
                "window": "",
                "normalize_mode": deficit_mode,
                "recent_window": recent_window,
                **summary,
            }
            search_rows.append(row)
            payload["gap_deficit_recent_lr"].append(row)

    search_rows.sort(key=lambda row: (-row["best6_avg_main_hits"], -row["top1_avg_main_hits"], row["group"], row["config"]))

    SUMMARY_JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with SUMMARY_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "group", "config", "window", "recent_window", "normalize_mode",
                "tested_draws", "top1_avg_main_hits", "best6_avg_main_hits",
                "top1_second_hit_rate", "any6_second_hit_rate",
                "top1_at_least_3_main_rate", "any6_at_least_3_main_rate",
            ],
        )
        writer.writeheader()
        writer.writerows(search_rows)

    lines = [
        "# Mean Reversion Parameter Search",
        "",
        "| Group | Config | Top1 Avg Main | Best6 Avg Main | Top1 2nd Hit | Any6 2nd Hit |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in search_rows:
        lines.append(
            f"| `{row['group']}` | `{row['config']}` | {row['top1_avg_main_hits']:.4f} | "
            f"{row['best6_avg_main_hits']:.4f} | {row['top1_second_hit_rate']:.2%} | {row['any6_second_hit_rate']:.2%} |"
        )
    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Parameter search CSV: {SUMMARY_CSV_PATH}")
    print(f"Parameter search JSON: {SUMMARY_JSON_PATH}")
    print(f"Parameter search MD: {SUMMARY_MD_PATH}")


if __name__ == "__main__":
    main()
