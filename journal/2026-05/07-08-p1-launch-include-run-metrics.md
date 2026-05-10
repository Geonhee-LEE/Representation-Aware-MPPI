# Wire eval.run_metrics into jackal_cafe.launch.py via include_run_metrics flag

- **Cycle**: 2026-05-07 08:00 KST
- **Branch**: `autoresearch/p1-launch-include-run-metrics`
- **TODO**: `357c5d39` [north-star] Add include_run_metrics:=true option to jackal_cafe.launch.py
- **Phase**: P1
- **Status**: keep

## What I tried
- Added 5 LaunchConfiguration args to `jackal_cafe.launch.py`: `include_run_metrics`
  (default `false`), `run_id`, `target_speed`, `run_metrics_output_dir`,
  `run_metrics_pythonpath`. The flag is the gate; the rest are pass-through to
  `eval.run_metrics` parameters.
- Inside `launch_setup`, conditionally append an `ExecuteProcess` running
  `python3 -m eval.run_metrics --ros-args -p run_id:=… -p target_speed:=…
  -p output_dir:=…`. PYTHONPATH for the spawned process is composed from the
  optional override + process env (so `PYTHONPATH=$(pwd) ros2 launch …` works
  out of the box from the repo root).
- Added 6-test smoke suite (`eval/tests/test_launch_include_run_metrics.py`)
  that loads the launch file as a plain Python module and asserts arg
  defaults + a regression guard for the 10 legacy args.

## What worked / what failed
- `colcon build --packages-select representation_aware_mppi_bringup` clean in 0.6s.
- 32/32 tests pass (6 new + 17 path_tracking + 9 run_metrics).
- Default-off: same launch with `include_run_metrics:=false` is byte-identical
  to the previous launch entity list except for the trailing condition-gated
  ExecuteProcess (which `IfCondition('false')` drops at execution time). The
  test suite asserts the 10 legacy args are still declared.
- Discovered (and worked around) a shell pitfall: `PYTHONPATH=$(pwd) python3 -m
  pytest` overwrites the ROS-sourced PYTHONPATH and breaks `import launch`.
  Fix is `PYTHONPATH=$(pwd):$PYTHONPATH`. Worth surfacing in any future
  CI/`scripts/` path that runs eval tests.
- NOT verified in actual sim (out-of-cycle by hard limit on long-running sims).
  End-to-end "ros2 launch … include_run_metrics:=true → runs/<id>.json" stays
  on the user-verification side.

## North-star delta
- Last gate between "metric module exists on `main`" and "user can produce
  `runs/<id>.json` from a real sim run" is now closed in code. Distance to
  north star: still 0 measured numbers, but the recipe to produce the first
  one is one `git pull && bash` away.
- No regression to legacy launch behavior — opt-in flag.

## Key learnings
- `ExecuteProcess` + composed PYTHONPATH is the right call here vs. registering
  `eval.run_metrics` as a console_script in `setup.py` of the bringup package.
  The eval harness lives at repo root (not under any ROS2 package on purpose,
  so that pure-Python tests don't need ament). Keeping it that way preserves
  the offline test contract.
- Pytest's `importorskip` silently skips a whole module on import failure —
  including downstream `from launch.actions import …`. When a launch test is
  unexpectedly green-skipped, suspect a broken sys.path before suspecting test
  logic.

## Recommended next 1–3 priorities
1. **(user)** Merge PR for `autoresearch/p1-launch-include-run-metrics`, then
   run `cafe_straight_v0` 1회 with `include_run_metrics:=true` →
   `runs/jackal-cafe-001.json`. First quantitative number for the project.
2. **(claude, post-sim-verification)** Calibrate v0 metric thresholds in
   `docs/path_tracking_metrics.md` against the captured JSON (replace the
   "v0 가설" table with measured baselines).
3. **(claude)** Apply the same `include_run_metrics` pattern to
   `jackal_outdoor_sim.launch.py` so `cafe_straight_v0` and `city_curved_v0`
   both produce JSON via the same flag.

## Artifacts
- PR: pending merge (autoresearch/p1-launch-include-run-metrics)
- Files touched: `src/representation_aware_mppi_bringup/launch/jackal_cafe.launch.py`, `eval/tests/test_launch_include_run_metrics.py`, `results/p1-launch-include-run-metrics.tsv`, `RESULTS.md`
- TSV row appended: yes
