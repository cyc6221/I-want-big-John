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
