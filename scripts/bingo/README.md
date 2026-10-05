# scripts/bingo

BINGO BINGO draw-data crawler. It is **not** part of `scripts/run.py`: it does not read `raw-data/` or write into `docs/`. It runs from `.github/workflows/update-bingo.yml` and writes to the `bingo-data` branch.

| File | Role |
| --- | --- |
| `fetch_bingo.py` | Calls the official API (`api.taiwanlottery.com/TLCAPIWeB/Lottery/BingoResult`), validates and normalises draws. Any network/shape problem raises `BingoFetchError`. |
| `bingo_statistics.py` | Builds `stats.json` from the full history (named to avoid shadowing the stdlib `statistics`). |
| `update_bingo.py` | CLI: fetch today + yesterday (+ `--backfill-days N`), keep only unseen `draw_no`s, rewrite JSON only if something is new. |

## Data layout (on the `bingo-data` branch)

```
data/bingo/latest.json              newest draw
data/bingo/history.json             newest 1000 draws (rolling window, newest first)
data/bingo/history/YYYY-MM-DD.json  full archive, one file per day, oldest first
data/bingo/stats.json               descriptive stats over the whole archive
```

Draw object: `draw_no`, `draw_time`, `draw_time_derived`, `numbers` (20, sorted), `draw_order` (20, as drawn), `super_number`, `big_small` (大/小/和), `odd_even` (單/雙/和).

- The API returns no draw time. `draw_time` is derived from the schedule (07:05, then every 5 minutes, 203 draws a day, Asia/Taipei), hence `draw_time_derived: true`.
- 大 = at least 13 of the 20 numbers are 41–80; 小 = at least 13 are 1–40; 單/雙 likewise by parity; otherwise 和. The official value from the API is stored; a mismatch with this rule only prints a warning.
- The API only has roughly the last three years of draws.
- Stats describe past results only; they are not predictions.

## Create the `bingo-data` branch (once)

```bash
git switch --orphan bingo-data
git commit --allow-empty -m "chore: init bingo-data branch"
git push -u origin bingo-data
git switch main
```

The branch has no shared history with `main` and is never merged into it. Only the workflow pushes to it; the `main` ruleset does not apply (it targets `refs/heads/main` only).

## Run locally

```bash
mkdir /tmp/bingo-data && git -C /tmp/bingo-data init
python scripts/bingo/update_bingo.py --data-dir /tmp/bingo-data --backfill-days 1
python scripts/bingo/update_bingo.py --data-dir /tmp/bingo-data --backfill-days 1   # prints "no new draws; nothing written"
```

Exit code is non-zero (and nothing is written) if the API fails or returns malformed data.
