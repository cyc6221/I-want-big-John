"""Update the BINGO data files in a checkout of the `bingo-data` branch.

    python scripts/bingo/update_bingo.py --data-dir <bingo-data checkout> [--backfill-days N]

Fetches today's and yesterday's draws (plus N more days when backfilling),
keeps only draws that are not stored yet, and rewrites the JSON files only when
there is at least one new draw. With nothing new, no file is touched.

Layout under <data-dir>/data/bingo/:
    latest.json              newest draw
    history.json             rolling window of the newest HISTORY_WINDOW draws
    history/YYYY-MM-DD.json  full archive, one file per day
    stats.json               descriptive statistics over the full archive
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bingo_statistics import build_stats  # noqa: E402
from fetch_bingo import TAIPEI, BingoFetchError, fetch_day, today_taipei  # noqa: E402

HISTORY_WINDOW = 1000  # ~5 days of draws in history.json


def dumps_json(payload: dict) -> str:
    """Stable JSON; a "draws" list gets one compact draw per line (small, append-style diffs)."""
    compact = {"ensure_ascii": False, "sort_keys": True, "separators": (",", ":")}
    if "draws" not in payload:
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    head = [f"  {json.dumps(k)}: {json.dumps(v, **compact)}" for k, v in sorted(payload.items()) if k != "draws"]
    rows = ",\n".join("    " + json.dumps(d, **compact) for d in payload["draws"])
    return "{\n" + ",\n".join(head) + ',\n  "draws": [\n' + rows + "\n  ]\n}\n"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(dumps_json(payload), encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def read_shard(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))["draws"]


def shard_payload(day: date, draws: list[dict]) -> dict:
    return {"date": day.isoformat(), "count": len(draws), "draws": draws}


def load_all_draws(history_dir: Path) -> list[dict]:
    draws: list[dict] = []
    for path in sorted(history_dir.glob("*.json")):
        draws.extend(read_shard(path))
    return draws


def write_github_output(**values: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            for key, value in values.items():
                fh.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", required=True, type=Path, help="root of the bingo-data checkout")
    parser.add_argument("--backfill-days", type=int, default=0, help="also fetch this many days before yesterday")
    args = parser.parse_args()

    bingo_dir = args.data_dir / "data" / "bingo"
    history_dir = bingo_dir / "history"

    today = today_taipei()
    days = [today - timedelta(days=offset) for offset in range(0, 2 + max(args.backfill_days, 0))]

    # Fetch everything first: any failure raises here, before a single file is written.
    updated_shards: dict[date, list[dict]] = {}
    new_draws: list[dict] = []
    for day in days:
        fetched = fetch_day(day)
        shard_path = history_dir / f"{day.isoformat()}.json"
        stored = read_shard(shard_path)
        stored_by_no = {d["draw_no"]: d for d in stored}
        added = [d for d in fetched if d["draw_no"] not in stored_by_no]
        for d in fetched:
            old = stored_by_no.get(d["draw_no"])
            if old is not None and old["numbers"] != d["numbers"]:
                print(f"warning: draw {d['draw_no']} already stored with different numbers; keeping the stored one")
        print(f"{day}: fetched {len(fetched)} draws, {len(added)} new")
        if added:
            merged = sorted(stored + added, key=lambda d: int(d["draw_no"]))
            updated_shards[day] = merged
            new_draws.extend(added)

    if not new_draws:
        print("no new draws; nothing written")
        write_github_output(changed="false")
        return 0

    for day, draws in updated_shards.items():
        write_json(history_dir / f"{day.isoformat()}.json", shard_payload(day, draws))

    all_draws = sorted(load_all_draws(history_dir), key=lambda d: int(d["draw_no"]))
    newest_first = list(reversed(all_draws))
    latest = newest_first[0]
    now = datetime.now(TAIPEI).isoformat(timespec="seconds")

    write_json(bingo_dir / "latest.json", {**latest, "updated_at": now})
    recent = newest_first[:HISTORY_WINDOW]
    write_json(bingo_dir / "history.json", {"generated_at": now, "count": len(recent), "draws": recent})
    write_json(bingo_dir / "stats.json", {"generated_at": now, **build_stats(all_draws)})

    print(f"added {len(new_draws)} draws; latest draw {latest['draw_no']}")
    write_github_output(changed="true", draw_no=latest["draw_no"])
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BingoFetchError as exc:
        print(f"::error::BINGO fetch failed: {exc}")
        sys.exit(1)
