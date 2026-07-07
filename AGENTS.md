# Codex Instructions

This file records repository-specific workflow rules for Codex.

## General

- Start feature or data work from `main`.
- Create a new branch for each task.
- Use the `codex/{description}` prefix for Codex branches by default.
- Prefer draft PRs unless the user explicitly asks for a ready PR.
- After a PR is merged, switch back to local `main`, fast-forward it to the latest `origin/main`, then clean up both the local branch and the remote branch.
- Fetch and pull with `--prune` (or ensure `git config fetch.prune true` is set) so deleted remote branches do not linger as stale remote-tracking refs.
- When a branch has been rebased, use `git push --force-with-lease` to update the PR branch.
- On Windows, prefer running generation scripts with UTF-8 console output when needed.
- Do not run dependent commands in parallel. If one command relies on the result of another, run them sequentially. For example, finish `git add` before running `git commit`, and finish `git commit` before `git push`.

## Windows Shell Notes

- This repo's HTML and Markdown files are UTF-8. In Windows PowerShell 5.1, do not assume `Get-Content` will decode UTF-8 correctly when the file has no BOM.
- When reading UTF-8 files for inspection, prefer `Get-Content -Encoding utf8` or `[System.IO.File]::ReadAllLines($path, [System.Text.Encoding]::UTF8)` so Chinese text does not appear as mojibake.
- Codex can read and write Chinese in this repo, but file reads must explicitly use UTF-8. Do not treat garbled PowerShell output as proof that the file contents are broken.
- `chcp 65001` and UTF-8 console output do not fix a bad read-decoding step by themselves. If text still looks corrupted, verify the file bytes before editing.
- If terminal output looks garbled, confirm the file encoding before rewriting content. Avoid retyping whole files just because the shell display is wrong.
- In this Codex environment, writes under `.git` such as `git switch -c`, `git add`, `git commit`, and `git push` may need to be rerun with elevation in the Codex tool because of sandbox restrictions. If Git reports lock or permission errors under `.git`, retry with elevation instead of assuming the repository is broken.
- In this environment, `gh` is currently available as a shim on `PATH` and can be used directly.
- If `gh` is ever not recognized again, first check `where.exe gh`, then verify `C:\Program Files\GitHub CLI\gh.exe` exists before assuming GitHub CLI is missing.
- If `gh` exists but GitHub operations fail, run `gh auth status` to verify the saved login and token are still valid.

## Instant Data Update Workflow

Use this workflow when adding or correcting scratch-ticket (`instants`) records.

1. Create a new branch from `main`.
2. Update `raw-data/all-instants.csv`.
3. Update the matching article under `docs/_articles/all-instants/` when there is a manual test record to add or correct.
4. Run `python scripts/run.py`.
5. Review the generated changes.

Generated files commonly include:
- `docs/_list/instants-all.md`
- `docs/assets/data/instants-chosen-number.json`
- `docs/assets/data/instants-per-month.json`
- `docs/_list/instants-per-month.md`

## Instant Article Update Workflow

Use this workflow when adding or correcting scratch-ticket article pages without adding a manual purchase record.

1. Create a new branch from `main`.
2. Run `python scripts/new_instant_article.py {期別}`, for example `python scripts/new_instant_article.py 5157`.
   - The script fetches the official launch announcement and game data from the Taiwan Lottery API, computes all prize/expected-value math in Python, and writes the article, `raw-data/instant-prize-structures/{期別}.json`, `docs/_data/instants_compare.yml`, and `raw-data/instant-games.json`.
   - Do NOT hand-copy prize numbers from the web or compute the math yourself (as an agent or human); the prize structure and expected values must always come from this script. The official site is a JS SPA, so fetching the announcement URL directly returns an empty shell — the script uses the JSON API behind it instead.
   - If the announcement cannot be found automatically, pass `--news-url {公告網址}`. If parsing fails, the script saves a draft JSON under `raw-data/instant-prize-structures/`; fix it manually and rerun with `--from-json`.
   - To correct data in an existing article, rerun the script with `--force` (then `python scripts/run.py`). `--force` rewrites the whole file from official data, so custom prose outside the generated sections is not preserved — re-apply such edits manually afterwards.
3. Run `python scripts/run.py` (fills in `親自實測` / `published` from `raw-data/all-instants.csv`).
4. Run `bundle exec jekyll build` from `docs/`.
5. Review the article and comparison-list changes.

## Lotto Purchase Update Workflow

Use this workflow when adding or correcting draw-game purchase records such as Power Lottery (`638`). Keep these records separate from scratch-ticket (`instants`) data.

1. Create a new branch from `main`.
2. For Power Lottery (`638`), update `raw-data/lotto-purchases/638-purchases.csv`.
3. For Big Lotto (`649`), update `raw-data/lotto-purchases/649-purchases.csv`.
4. Do not add draw-game purchase records to `raw-data/all-instants.csv`.
5. Run `python scripts/run.py`.
6. Review the generated changes.

The `638` purchase CSV stores only the purchase basics:

`purchase_date,draw_no,line_no,price,number1,number2,number3,number4,number5,number6,special`

Prize rank and fixed prize amount are generated from draw results.

The `649` purchase CSV stores only the purchase basics:

`purchase_date,draw_no,line_no,price,number1,number2,number3,number4,number5,number6`

Prize rank and fixed prize amount are generated from draw results.

Generated files commonly include:
- `docs/_list/638-purchases.md`
- `docs/assets/data/638-purchases.json`
- `docs/_list/649-purchases.md`
- `docs/assets/data/649-purchases.json`

## Manual Lotto Result Workflow

Use this workflow when Taiwan Lottery official monthly result downloads have not yet caught up, but a draw result is known.

1. Keep official monthly downloaded files under `raw-data/lotto-result-downloads/` unchanged.
2. Add or correct manual draw results in `raw-data/manual-lotto-results/{game}-manual-results.csv`, for example `raw-data/manual-lotto-results/638-manual-results.csv` or `raw-data/manual-lotto-results/649-manual-results.csv`.
3. Keep manual records separated by game. Do not mix `638` and `649` rows in one file.
4. Run `python scripts/run.py`.
5. Review generated latest-draw, purchase-record, and stats changes.

Manual draw records are merged over official rows by `draw_no`. Manual records only store draw numbers, so they do not override official financial values and are excluded from sales statistics until official data is downloaded.

## Commit Style

When practical, keep commits separated by change type.

- Put manual source/data edits in one commit.
- Put generated output updates in a separate commit when that separation stays clear.
- Put script or workflow fixes in their own commit instead of mixing them into data-only changes.

## PR Review Workflow

When addressing GitHub PR review comments:

1. Make the requested code or content changes locally.
2. Commit the fix.
3. Push the updated branch.
4. Reply on the review thread with the fix summary and commit reference.
5. If the thread is fully addressed, mark it as resolved after replying.
