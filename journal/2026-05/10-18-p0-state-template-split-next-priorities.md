# STATE.md template splits next-priorities into claude vs user sections

- **Cycle**: 2026-05-10 18:00 KST
- **Branch**: `autoresearch/p0-state-template-split-next-priorities`
- **TODO**: `35cc5d39` [infra] STATE.md template: split next-priorities into claude-actionable vs user-blocked
- **Phase**: P0
- **Status**: keep

## What I tried

- Replaced Phase 4c's single `Next 3 priorities (actionable)` block in `scripts/prompts/auto_research.md` with two sections: `Next claude-actionable` (PLAN's candidate pool) and `Next user-blocked` (Telegram queue, never picked).
- Added a preamble to the PLAN decision tree (Phase 2) stating the candidate pool is `Next claude-actionable` + Today/claude TODOs only — user-blocked is excluded by structure, not by per-cycle judgment.
- Updated REVIEW step 2 to capture both sections separately, and PLAN_NEXT 5a to walk both lists with `Owner` derived from the section (`claude-actionable → claude`, `user-blocked → user`) plus a mismatch check.

## What worked / what failed

- +17/-7 LOC across 4 hunks, all four edits stay consistent (REVIEW captures it, PLAN consumes it, REPORT writes it, PLAN_NEXT reconciles it).
- Branched from main rather than rebasing onto PR #11 — different sections, no conflict, dependency-free.
- Doc-only: no build smoke needed, no test regression risk.

## North-star delta

- 0 measured numbers gained — pure process infra. Distance to north star unchanged.
- Removes one recurring fix-up commit class (`a0a3420`-style PLAN_NEXT-time Owner swap), so future cycles spend the budget on real diffs instead of housekeeping.

## Key learnings

- Single fix-up commits like `a0a3420` are the visible symptom; the root cause is template ambiguity that lets the same field hold two semantically different things. Fixing the template is cheaper than catching it in 5a every cycle.
- Cross-section consistency matters: REVIEW + PLAN + REPORT + PLAN_NEXT all reference the same field, so a template change touches all four — easy to under-edit and leave stale wording. Diff stat (+17/-7) is the audit.
- The "branched from main, not from PR #11" choice is exactly the PR-dependency fallback rule from PR #11 itself — dogfooded at the right moment.

## Recommended next 1–3 priorities

1. **(claude)** Add per-class result reporting contract to `scripts/aggregate_results.sh` — TODO `357c5d39…819a` (Backlog, P3, Phase=P5). Pre-positions infra for taxonomy v0 §4 promise; pure Bash/Python extension to the existing aggregator, doable cold.
2. **(user)** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json` (TODO `358c5d39`). Still the only mover toward the first quantitative number.
3. **(claude)** Author a Backlog TODO: housekeeping pass to merge open PR cluster (#10 aggregate-results-pr-status, #11 pr-dep-fallback, #12 this) — once all merged, next cycle's REVIEW will see a clean main and the Today queue can shift from infra-on-infra to actual sim/code work.

## Artifacts

- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/12
- Files touched: scripts/prompts/auto_research.md, results/p0-state-template-split-next-priorities.tsv, RESULTS.md
- TSV row appended: yes
