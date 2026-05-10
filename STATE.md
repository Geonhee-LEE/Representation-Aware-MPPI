# Research State — auto-generated each cycle

_Last updated: 2026-05-10 16:00 KST · cycle p0-aggregate-results-pr-merge-status_

## North star distance

PRs #7 (cafe-launch-flag), #8 (outdoor-launch-flag), #9 (executor-prompt-discipline) all merged today (2026-05-10 ~15:18 KST), so the path to the **first quantitative number** is now fully unblocked end-to-end. A single `ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py include_run_metrics:=true run_id:=cafe-001` should produce `runs/cafe-001.json`. Distance: still **0 measured numbers**, but the next gate is a 1-shot user sim run rather than any code work.

## Current bottleneck

**User-owned sim run for `runs/cafe-001.json`** — the `(user) Run cafe_straight_v0 sim` TODO (`358c5d39`, NeedsUserTest=true, Today, P0). Until it lands, calibration of `docs/path_tracking_metrics.md` against measured baselines stays gated. All claude-side blockers cleared.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p0-aggregate-results-pr-merge-status` | 2026-05-10 16:05 | qual:script-syntax-ok | 0 (PR #10 pending) |

(All prior `autoresearch/*` branches merged — see `RESULTS.md` for per-branch PR/state, now auto-surfaced.)

## Recent learnings (last 3 cycles)

- **(이번 cycle)** Decision tree handled a freshly-shifted bottleneck cleanly: 3 blocking PRs merged ≤10 min before cycle start, the executor still picked the highest-aligned claude-actionable item (Backlog promotion #3 from prior STATE.md). Bottleneck recomputation in REVIEW > stale STATE.md content.
- **(이번 cycle)** `gh pr list --head <branch> --state all` is the load-bearing detail — default `--state open` returns 0 for any merged repo and would have silently produced "no PR" for every section.
- **(cycle p0-auto-research-md-gh-pr-create-step)** Dogfooding new prompt instructions in the same cycle that authors them surfaces gaps that pure inspection misses.

## Next 3 priorities (actionable)

1. **(user)** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json` (TODO `358c5d39`). First quantitative number.
2. **(claude, post-sim)** Calibrate v0 metric thresholds in `docs/path_tracking_metrics.md` against captured `runs/cafe-001.json` (replace v0 hypothesis table with measured baselines).
3. **(claude)** [infra] auto_research.md decision tree: encode PR-dependency fallback (top-priority Today blocked by unmerged-branch import → drop to next-priority by Priority, never branch-stack). Backlog P2 doc-only.

## Cycles to date

- 이번 주 (Mon 2026-05-04 시작): **7** (5-phase 루프 cycle 1–7)
- 프로젝트 통합: **7**
