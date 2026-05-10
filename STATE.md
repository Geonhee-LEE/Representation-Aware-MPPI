# Research State — auto-generated each cycle

_Last updated: 2026-05-07 10:00 KST · cycle p0-auto-research-md-gh-pr-create-step_

## North star distance

Three claude-side PRs (#7 cafe-launch-flag, #8 outdoor-launch-flag, #9 executor-prompt-discipline) sit at the door of `main`. The first two close the gap to the **first quantitative number** (a single `ros2 launch ... include_run_metrics:=true` produces `runs/cafe-001.json`); the third locks in cycle discipline so future infra debt doesn't eat north-star budget. Distance: still **0 measured numbers**, but every claude-side blocker is now in PR review.

## Current bottleneck

**User PR-merge throughput** — same as last cycle, now with 3 PRs queued. PR #7 + #8 unlock first JSON; PR #9 is independent doc-only and can merge in any order. After PR #7/#8 merge, single `ros2 launch` produces the first measured baseline.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p1-launch-include-run-metrics` | 2026-05-07 08:05 | qual:tests-32pass | 0 (PR #7 pending) |
| `autoresearch/p1-outdoor-launch-include-run-metrics` | 2026-05-07 09:06 | qual:tests-32pass | 0 (PR #8 pending) |
| `autoresearch/p0-auto-research-md-gh-pr-create-step` | 2026-05-07 10:02 | qual:doc-only | 0 (PR #9 pending) |

## Recent learnings (last 3 cycles)

- **(이번 cycle)** Dogfooding new prompt instructions in the same cycle that authors them surfaces gaps that pure inspection misses — the `${PR_URL}` `pending` fallback wording was caught only by exercising the path.
- **(cycle p1-outdoor-launch-include-run-metrics)** Co-evolving same-file PRs need separate test paths. Sibling files with intentional duplication beat a shared-base + rebase dance.
- **(cycle p1-launch-include-run-metrics)** `ExecuteProcess` + composed PYTHONPATH is the right wiring for keeping `eval/` at repo root (not in any ROS2 package). Preserves the offline-test contract while still launching the node from a single `ros2 launch`.

## Next 3 priorities (actionable)

1. **(user)** Merge PR #7 + PR #8 → run `cafe_straight_v0` with `include_run_metrics:=true` → `runs/cafe-001.json`. First quantitative number. PR #9 (executor prompt) can merge in parallel.
2. **(claude, post-merge-and-sim)** Calibrate v0 metric thresholds in `docs/path_tracking_metrics.md` against the captured JSON (replace "v0 가설" table with measured baselines).
3. **(claude)** Extend `scripts/aggregate_results.sh` to surface per-branch PR # / merge status, so STATE.md "Open experiments" table stops needing manual `(PR #N pending)` annotations.

## Cycles to date

- 이번 주: **6** (5-phase 루프 cycle 1–6)
- 프로젝트 통합: **6**
