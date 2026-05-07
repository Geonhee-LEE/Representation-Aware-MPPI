# auto_research.md: explicit Open the PR step after push

- **Cycle**: 2026-05-07 10:00 KST
- **Branch**: `autoresearch/p0-auto-research-md-gh-pr-create-step`
- **TODO**: `359c5d39` [infra] auto_research.md EXECUTE phase: make `gh pr create` an explicit step after push
- **Phase**: P0
- **Status**: keep

## What I tried

- Inserted a new `### Open the PR` section into `scripts/prompts/auto_research.md` Phase 3, immediately after `### Push the branch (never main)`.
- Section captures `${PR_URL}` via `gh pr create` with a HEREDOC body (Summary / Test plan / Closes-TODO refs) and skips re-creating if a PR is already open for the branch.
- Updated Phase 4d Telegram cycle-summary template to reference `${PR_URL}` instead of the bare branch name; documented `pending` fallback.
- Dogfooded the new step in this cycle: PR #9 opened via `gh pr create` exactly as the new section prescribes.

## What worked / what failed

- Net diff: +33 LOC, doc-only — well under the 50-LOC simplicity threshold.
- The `EXISTING=$(gh pr list --head ... --json number --jq '.[0].number')` skip-if-exists guard is idempotent — safe to re-run within a cycle if a partial run already opened the PR.
- Telegram template change is minimal: same line shape, just `${PR_URL}` interpolation. No format breakage for downstream consumers.
- No code touched, so colcon build + test loop unnecessary; saved EXECUTE budget.

## North-star delta

- No measurable movement toward "perfect MPPI in all envs" — pure infra change.
- Indirect benefit: future cycles spend zero budget on push-without-PR housekeeping (cycle 2026-05-07 08:00 burned ~5 min cleaning up PR #7 retrospectively); that budget now goes to north-star work.

## Key learnings

- The decision-tree fallback (P3 user-blocked → take next claude-actionable) interacted cleanly with the Today queue: STATE.md priority #3 was already pre-positioned by the previous cycle as a claude-actionable item, so PLAN was a 30-second pick.
- Dogfooding new prompt instructions in the same cycle that authors them is high signal — exposed that `${PR_URL}` needed an explicit `pending` fallback wording for Phase 4d, which I would have missed if I'd just edited and not exercised the path.
- Mechanical-but-real cycles like this one are worth keeping. The ratchet of friction-removal compounds across 24/day cron ticks.

## Recommended next 1–3 priorities

1. **(user)** Merge PR #7 + PR #8 + PR #9 → unblock first quantitative number AND lock in the new Open-the-PR cycle discipline.
2. **(claude, post-merge-and-sim)** Calibrate v0 metric thresholds in `docs/path_tracking_metrics.md` against the captured `runs/cafe-001.json`.
3. **(claude)** Author follow-up TODO: `scripts/aggregate_results.sh` should also surface PR # / merge status per branch so STATE.md "Open experiments" table stops needing manual annotation.

## Artifacts

- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/9
- Files touched: `scripts/prompts/auto_research.md`, `results/p0-auto-research-md-gh-pr-create-step.tsv`, `RESULTS.md`
- TSV row appended: yes (`qual:doc-only`, status=keep)
