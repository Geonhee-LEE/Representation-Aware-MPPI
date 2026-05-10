# aggregate_results.sh surfaces PR # / merge status per branch

- **Cycle**: 2026-05-10 16:00 KST
- **Branch**: `autoresearch/p0-aggregate-results-pr-merge-status`
- **TODO**: `359c5d39` [infra] aggregate_results.sh: surface per-branch PR # / merge status in RESULTS.md
- **Phase**: P0
- **Status**: in_progress (PR #10 pending merge)

## What I tried
- Added a bash pre-pass: for each `results/<slug>.tsv`, call `gh pr list --head autoresearch/<slug> --state all --json number,state,url --jq '.[0] // empty'` and write `<slug>\t<num>\t<state>\t<url>` lines into a tempfile.
- Extended the embedded python to consume that tempfile, build a `pr_by_slug` dict, and inject `_PR [#N](url) · <state>_` under each section header. Falls back to `_no PR_` when the entry is absent.
- Verified: script run resolves all 9 prior branches correctly; 11th TSV row (this cycle's own) renders as PR #10 · open after push.

## What worked / what failed
- Worked: 9/9 historical branches matched correct PR # and `merged` state with no manual upkeep. The `--state all` flag is the load-bearing detail — default `--state open` would have shown 0 results for this repo.
- Worked: `command -v gh && gh auth status` guard short-circuits cleanly on environments without gh, leaving behavior identical to pre-change (verified by reasoning, not exec).
- Did not gold-plate: ignored the case of multiple PRs per branch (`--jq '.[0]'` picks first) — fine for our convention of one PR per branch.

## North-star delta
- Zero direct movement toward "perfect MPPI in all envs" — pure cycle-infra. STATE.md upkeep cost drops from manual `(PR #N pending)` typing to zero next cycle, freeing budget that would otherwise eat into PLAN/REVIEW.

## Key learnings
- The decision tree behaves correctly even on cycles where the bottleneck has just shifted: PRs #7/#8/#9 merged ≤10 min before this cycle started, and the right pick was the next-priority infra item rather than waiting for the user-owned sim run.
- `gh pr list --head <branch> --state all` is the right shape for branch→PR resolution; `--search "head:<branch>"` is fuzzier and was unneeded here.

## Recommended next 1–3 priorities
1. **(user)** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json`. Now unblocked (PR #7+#8 on main). First quantitative number.
2. **(claude, post-sim)** Calibrate v0 metric thresholds in `docs/path_tracking_metrics.md` against captured `runs/cafe-001.json` (replace v0 hypothesis table with measured baselines).
3. **(claude)** [infra] auto_research.md decision tree: encode PR-dependency fallback (top-priority Today blocked by unmerged-branch import → drop to next-priority, do not branch-stack). Backlog P2 doc-only; small but plugs the gap exposed by cycle p1-eval-scenarios-yaml-v0.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/10
- Files touched: scripts/aggregate_results.sh, RESULTS.md (regenerated), results/p0-aggregate-results-pr-merge-status.tsv
- TSV row appended: yes
