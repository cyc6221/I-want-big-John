import csv
import json
from pathlib import Path

from lib_dataset import PREDICTOR_DATA_PATH, RESEARCH_638_DIR, build_payload, load_draws, write_payload
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


OUTPUT_DIR = RESEARCH_638_DIR / "outputs" / "latest"
JSON_PATH = OUTPUT_DIR / "model_latest_predictions.json"
CSV_PATH = OUTPUT_DIR / "model_latest_predictions.csv"
MD_PATH = OUTPUT_DIR / "model_latest_predictions.md"

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


def main() -> None:
    draws = load_draws()
    payload = build_payload(draws)
    write_payload(payload, PREDICTOR_DATA_PATH)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    export_rows = []
    export_payload = {
        "summary": payload["summary"],
        "models": {},
    }

    md_lines = [
        "# Latest Predictions By Model",
        "",
        f"資料期間：`{payload['summary']['date_start']}` -> `{payload['summary']['date_end']}`",
        "",
    ]

    for model in ALL_MODELS:
        model_id = model["id"]
        predictions = MODEL_RUNNERS[model_id](payload, seed=payload["summary"]["draw_count"], attempts=4000, output_count=6)
        export_payload["models"][model_id] = {
            "meta": model,
            "predictions": predictions,
        }

        md_lines.extend([
            f"## `{model_id}`",
            f"- Label: {model['label']}",
            f"- Family: {model['family']}",
            "",
        ])

        for index, prediction in enumerate(predictions, start=1):
            export_rows.append(
                {
                    "model_id": model_id,
                    "rank": index,
                    "main_numbers": " ".join(f"{n:02d}" for n in prediction["main_numbers"]),
                    "second_zone": f"{prediction['second_zone']:02d}",
                    "score": round(prediction["score"], 4),
                    "max_run": prediction["max_run"],
                    "top_signals": " ".join(prediction["top_signals"]),
                }
            )
            md_lines.append(
                f"{index}. 第一區 `{ ' '.join(f'{n:02d}' for n in prediction['main_numbers']) }` "
                f"第二區 `{prediction['second_zone']:02d}` "
                f"分數 `{prediction['score']:.4f}` 最大連號 `{prediction['max_run']}`"
            )

        md_lines.append("")

    JSON_PATH.write_text(json.dumps(export_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["model_id", "rank", "main_numbers", "second_zone", "score", "max_run", "top_signals"],
        )
        writer.writeheader()
        writer.writerows(export_rows)

    MD_PATH.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Latest predictions JSON: {JSON_PATH}")
    print(f"Latest predictions CSV: {CSV_PATH}")
    print(f"Latest predictions MD: {MD_PATH}")


if __name__ == "__main__":
    main()
