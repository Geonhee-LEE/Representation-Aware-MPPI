# Research State — auto-generated each cycle

_Last updated: 2026-05-07 09:00 KST · cycle p1-outdoor-launch-include-run-metrics_

## North star distance

Two parallel `include_run_metrics:=true` PRs now sit at the door of `main`: **PR #7** (cafe) and **PR #8** (outdoor: city + cafe-via-outdoor). Together they cover all four scenarios in `eval/scenarios/*.yaml`. Distance to north-star: still **0 measured numbers**, but every claude-side gate to the first JSON is now in code review. Single command after merge: `PYTHONPATH=$(pwd) ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py include_run_metrics:=true run_id:=cafe-001`.

## Current bottleneck

**User PR-merge throughput.** Two PRs (#7, #8) sit unmerged with no prior reviews; user merge unblocks both the first quantitative number AND the next claude-autonomous task (calibrate v0 thresholds against captured JSON). After PR-merge, single `ros2 launch` command produces `runs/cafe-001.json`; everything else is downstream of that.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p1-launch-include-run-metrics` | 2026-05-07 08:05 | qual:tests-32pass | 0 (PR #7 pending) |
| `autoresearch/p1-outdoor-launch-include-run-metrics` | 2026-05-07 09:06 | qual:tests-32pass | 0 (PR #8 pending) |

## Recent learnings (last 3 cycles)

- **(이번 cycle)** Co-evolving same-file PRs need separate test paths. Refactor-to-share-base looks clean but creates an artificial merge dependency. Sibling files with intentional duplication beat a shared-base + rebase dance.
- **(이번 cycle)** Always check what's actually on `main` before refactoring. The cafe test file existed in my mental model only because I'd just seen it on the cafe branch — checking it out on a fresh `main`-based branch surfaced the truth and a sibling-file pivot resolved the conflict before commit.
- **(cycle p1-launch-include-run-metrics)** `ExecuteProcess` + composed PYTHONPATH is the right wiring for keeping `eval/` at repo root (not in any ROS2 package). Preserves the offline-test contract while still launching the node from a single `ros2 launch`.

## Next 3 priorities (actionable)

1. **(user)** Merge PR #7 + PR #8 → run `cafe_straight_v0` with `include_run_metrics:=true` → `runs/cafe-001.json`. First quantitative number.
2. **(claude, post-merge-and-sim)** Calibrate v0 metric thresholds in `docs/path_tracking_metrics.md` against the captured JSON (replace "v0 가설" table with measured baselines).
3. **(claude)** Tighten EXECUTE phase spec in `scripts/prompts/auto_research.md`: make `gh pr create` an explicit step after push, so future cycles never push-without-PR (this cycle had to clean up after the previous one).

## Cycles to date

- 이번 주: **5** (5-phase 루프 cycle 1–5)
- 프로젝트 통합: **5**
