# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

"I Want Big John" (IWBJ) — a Taiwan Lottery research site published via GitHub Pages. Content is mostly Traditional Chinese. It covers draw games (威力彩 `638`, 大樂透 `649`, 今彩539 `539`) and scratch tickets (刮刮樂, "instants"). The core pattern is a data pipeline: hand-edited CSVs in `raw-data/` are transformed by Python scripts into Markdown pages and JSON assets inside `docs/`, which Jekyll builds into the site.

**Read `AGENTS.md` first** — it defines the branch/PR conventions (branch per task from `main`, `codex/{description}` prefix, draft PRs by default), commit style (separate manual data edits, generated output, and script changes into distinct commits), and the step-by-step workflows for each kind of data update.

## Commands

```bash
# Regenerate all derived files after editing anything in raw-data/
# (runs the scripts in scripts/run_tasks/ in the required order)
python scripts/run.py

# Build the Jekyll site (run from docs/; needed to verify article/layout changes)
cd docs && bundle exec jekyll build

# Validate lotto stats assets and page wiring (checks files exist; does not rebuild)
python scripts/validate_lotto_stats.py

# Create a new instants article from official Taiwan Lottery data
# (fetches the launch announcement via the JSON API, computes all EV math,
#  writes the article + raw-data/instant-prize-structures/{num}.json + compare-list wiring;
#  never hand-copy prize numbers or compute the math manually)
python scripts/new_instant_article.py 5157

# Refresh official draw results from Taiwan Lottery (rarely needed)
python scripts/download_lotto_results.py --from-year 2007 --to-year 2026
python scripts/extract_lotto_results.py --from-year 2007 --to-year 2026 --overwrite
```

There is no test suite or linter. Verification = rerun `python scripts/run.py`, review the generated diff, and build the site with Jekyll.

## Architecture

Data flows one way: `raw-data/` (sources of truth) → `scripts/run.py` → generated files in `docs/`.

- `raw-data/all-instants.csv` — scratch-ticket purchase records (`date,game,price,prize,chosen_num`). Never put draw-game purchases here.
- `raw-data/lotto-purchases/{638,649}-purchases.csv` — draw-game purchase records; only purchase basics. Prize rank/amount are *computed* by `build_638_purchases.py` / `build_649_purchases.py` from draw results (fixed-prize rules documented in `scripts/README.md`).
- `raw-data/lotto-result-downloads/` — official annual result files; never hand-edit.
- `raw-data/manual-lotto-results/{game}-manual-results.csv` — stopgap draw numbers when official downloads lag; merged over official rows by `draw_no`, excluded from sales stats.
- `scripts/run.py` — orchestrator; runs everything in `scripts/run_tasks/` in a fixed order. Prefer it over running individual task scripts. Shared helpers live in `scripts/_utils/`.
- `docs/` — Jekyll site (minima theme, `baseurl: /I-want-big-John`). Two collections: `_articles` (e.g. per-ticket pages in `_articles/all-instants/{num}.md`) and `_list` (record/listing pages). `docs/_data/instants_compare.yml` must be updated when adding an instants article so the comparison list picks it up.
- `research/` — offline prediction research (638 backtesting models); not part of the site build or run.py pipeline.

**Generated — do not hand-edit** (regenerate via `python scripts/run.py` instead): `docs/_list/instants-all.md`, `docs/_list/{638,649}-purchases.md`, `docs/assets/data/*.json`, `docs/_data/latest_draws.json`. `docs/_site/` is Jekyll build output. Note that `update_all_instants_articles_from_csv.py` also rewrites the manual-record sections of instants articles from the CSV.

New instants articles start from the template `scripts/templates/all-instants-article.md.example`, named by issue number (e.g. `docs/_articles/all-instants/5156.md`).

## Windows / encoding gotchas

All content files are UTF-8 (mostly without BOM) containing Chinese text. In Windows PowerShell 5.1, always read with explicit UTF-8 (`Get-Content -Encoding utf8`); garbled console output means a bad read decoding, not a corrupted file — verify bytes before rewriting anything. Run generation scripts with UTF-8 console output when needed (`run.py` already sets `PYTHONIOENCODING=utf-8` for its subprocesses).
