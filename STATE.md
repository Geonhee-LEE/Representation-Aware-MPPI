# Research State — auto-generated each cycle

_Last updated: 2026-05-07 08:00 KST · cycle p1-launch-include-run-metrics_

## North star distance

3 metric PRs (#4 path-tracking-metrics, #5 run_metrics ROS2 node, #6 scenarios YAML) **landed on `main`** at 07:25 KST. This cycle wired `include_run_metrics:=true` into `jackal_cafe.launch.py`, so a single `ros2 launch` command now boots sim + Jackal + Nav2 MPPI + the metrics recorder. Distance to north-star: still **0 measured numbers**, but the *recipe* to produce the first one is now one `git pull && PYTHONPATH=$(pwd) ros2 launch … include_run_metrics:=true run_id:=cafe-001` away.

## Current bottleneck

**First baseline sim run + JSON capture (user-blocked, 1 step).** Once the user merges `autoresearch/p1-launch-include-run-metrics` and runs `cafe_straight_v0`, the first concrete metrics drop into `runs/cafe-001.json` and the v0 hypothesis thresholds in `docs/path_tracking_metrics.md` can be calibrated. After that, the next claude-autonomous step (port the same flag to `jackal_outdoor_sim.launch.py`) is unblocked.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p1-launch-include-run-metrics` | 2026-05-07 08:05 | qual:tests-32pass | 0 (PR pending) |

## Recent learnings (last 3 cycles)

- **(이번 cycle)** `ExecuteProcess` + composed PYTHONPATH is the right wiring for keeping `eval/` at repo root (not in any ROS2 package). Preserves the offline-test contract while still launching the node from a single `ros2 launch`.
- **(이번 cycle)** `PYTHONPATH=$(pwd) python3 -m pytest` overwrites the ROS-sourced PYTHONPATH and silently breaks `import launch`. Use `:$PYTHONPATH` append in any future eval-test runner.
- **(cycle p1-eval-scenarios-yaml-v0)** Decision tree fallback when top pick is PR-blocked = drop to next aligned Today item. This cycle confirmed the inverse: when the PR-block clears, **resume in-flight Doing item** (decision tree step 1) is the right move.

## Next 3 priorities (actionable)

1. **(user)** Merge `autoresearch/p1-launch-include-run-metrics` + run `cafe_straight_v0` with the new flag → `runs/cafe-001.json`. First quantitative number for the project.
2. **(claude, post-merge-and-sim)** Calibrate v0 metric thresholds in `docs/path_tracking_metrics.md` against the captured JSON (replace "v0 가설" table with measured baselines).
3. **(claude)** Apply the same `include_run_metrics` pattern to `jackal_outdoor_sim.launch.py` so `city_curved_v0` / `city_figure8_v0` scenarios produce JSON via the same flag.

## Cycles to date

- 이번 주: **4** (5-phase 루프 cycle 1–4)
- 프로젝트 통합: **4**
