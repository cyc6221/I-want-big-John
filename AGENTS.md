# Codex Instructions

This file records repository-specific workflow rules for Codex.

## General

- Start feature or data work from `main`.
- Create a new branch for each task.
- In this repository, use the `codex-` prefix for Codex branches by default. Do not use `codex/` here, because the local Git ref layout rejects that branch naming pattern.
- Prefer draft PRs unless the user explicitly asks for a ready PR.
- After a PR is merged, switch back to local `main`, fast-forward it to the latest `origin/main`, then clean up both the local branch and the remote branch.
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
