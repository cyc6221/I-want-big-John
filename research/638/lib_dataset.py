import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH_638_DIR = ROOT / "research" / "638"
CSV_PATH = ROOT / "research" / "derived" / "638_all_years.csv"
PREDICTOR_DATA_PATH = RESEARCH_638_DIR / "638-predictor.json"

MAIN_NUMBER_FIELDS = ["獎號1", "獎號2", "獎號3", "獎號4", "獎號5", "獎號6"]
MIN_NUMBER = 1
MAX_NUMBER = 38
SECOND_ZONE_MIN = 1
SECOND_ZONE_MAX = 8
RECENT_WINDOWS = (30, 60, 120)


def pad2(value: int) -> str:
    return f"{value:02d}"


def load_draws(path: Path = CSV_PATH) -> list[dict]:
    draws = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            numbers = sorted(int(raw[field]) for field in MAIN_NUMBER_FIELDS)
            draws.append(
                {
                    "period": str(raw.get("期別", "")).strip(),
                    "date": str(raw.get("開獎日期", "")).strip(),
                    "numbers": numbers,
                    "second_zone": int(str(raw.get("第二區", "")).strip()),
                }
            )
    return draws


def build_main_stats(draws: list[dict]) -> list[dict]:
    total_draws = len(draws)
    counts = {n: 0 for n in range(MIN_NUMBER, MAX_NUMBER + 1)}
    recent_counts = {
        window: {n: 0 for n in range(MIN_NUMBER, MAX_NUMBER + 1)}
        for window in RECENT_WINDOWS
    }
    last_seen_index = {n: None for n in range(MIN_NUMBER, MAX_NUMBER + 1)}

    for index, draw in enumerate(draws):
        numbers = set(draw["numbers"])
        for n in numbers:
            counts[n] += 1
            last_seen_index[n] = index

        remaining = total_draws - index
        for window in RECENT_WINDOWS:
            if remaining <= window:
                for n in numbers:
                    recent_counts[window][n] += 1

    stats = []
    for n in range(MIN_NUMBER, MAX_NUMBER + 1):
        last_seen = last_seen_index[n]
        draws_ago = total_draws - 1 - last_seen if last_seen is not None else total_draws
        stats.append(
            {
                "number": n,
                "total_count": counts[n],
                "recent_30_count": recent_counts[30][n],
                "recent_60_count": recent_counts[60][n],
                "recent_120_count": recent_counts[120][n],
                "last_seen_draws_ago": draws_ago,
            }
        )
    return stats


def build_second_zone_stats(draws: list[dict]) -> list[dict]:
    total_draws = len(draws)
    counts = {n: 0 for n in range(SECOND_ZONE_MIN, SECOND_ZONE_MAX + 1)}
    recent_counts = {
        window: {n: 0 for n in range(SECOND_ZONE_MIN, SECOND_ZONE_MAX + 1)}
        for window in RECENT_WINDOWS
    }
    last_seen_index = {n: None for n in range(SECOND_ZONE_MIN, SECOND_ZONE_MAX + 1)}

    for index, draw in enumerate(draws):
        second_zone = draw["second_zone"]
        counts[second_zone] += 1
        last_seen_index[second_zone] = index

        remaining = total_draws - index
        for window in RECENT_WINDOWS:
            if remaining <= window:
                recent_counts[window][second_zone] += 1

    stats = []
    for n in range(SECOND_ZONE_MIN, SECOND_ZONE_MAX + 1):
        last_seen = last_seen_index[n]
        draws_ago = total_draws - 1 - last_seen if last_seen is not None else total_draws
        stats.append(
            {
                "number": n,
                "total_count": counts[n],
                "recent_30_count": recent_counts[30][n],
                "recent_60_count": recent_counts[60][n],
                "recent_120_count": recent_counts[120][n],
                "last_seen_draws_ago": draws_ago,
            }
        )
    return stats


def build_payload(draws: list[dict]) -> dict:
    history_main = [",".join(pad2(n) for n in draw["numbers"]) for draw in draws]
    history_draw = [
        f"{','.join(pad2(n) for n in draw['numbers'])}|{pad2(draw['second_zone'])}"
        for draw in draws
    ]
    latest_draw = draws[-1] if draws else None

    return {
        "summary": {
            "draw_count": len(draws),
            "date_start": draws[0]["date"] if draws else "",
            "date_end": draws[-1]["date"] if draws else "",
            "latest_period": latest_draw["period"] if latest_draw else "",
            "latest_numbers": latest_draw["numbers"] if latest_draw else [],
            "latest_second_zone": latest_draw["second_zone"] if latest_draw else None,
        },
        "rules": {
            "main_numbers": 6,
            "number_min": MIN_NUMBER,
            "number_max": MAX_NUMBER,
            "second_zone_min": SECOND_ZONE_MIN,
            "second_zone_max": SECOND_ZONE_MAX,
            "forbid_history_duplicate": True,
            "max_circular_run_allowed": 2,
            "circular_adjacent_note": "1 與 38 視為相連",
        },
        "number_stats": build_main_stats(draws),
        "second_zone_stats": build_second_zone_stats(draws),
        "history_main_combos": history_main,
        "history_draw_combos": history_draw,
        "history_dates": [draw["date"] for draw in draws],
        "history_periods": [draw["period"] for draw in draws],
    }


def write_payload(payload: dict, out_path: Path = PREDICTOR_DATA_PATH) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
