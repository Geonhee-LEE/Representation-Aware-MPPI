# eval/scenarios — v0 path-tracking scenarios

> Each YAML here defines **one repeatable evaluation episode**: world + start + goal + reference path + acceptance thresholds. `eval/run_metrics.py` (the ROS2 node from `autoresearch/p1-eval-run-metrics-node`) will consume these once both PRs land on `main`. Until then the YAMLs are spec-only — **the schema is the deliverable for v0**.

## v0 scope

Four scenarios, deliberately picked to span the four north-star regimes once but minimally:

| File | Path shape | World | env_class (per `docs/environment_taxonomy.md`) |
|---|---|---|---|
| `cafe_straight_v0.yaml` | straight | cafe3 (jackal_cafe.launch.py) | A — indoor-narrow |
| `city_curved_v0.yaml` | S-curve | small_city (jackal_outdoor_sim, world:=city) | B — outdoor-open |
| `city_figure8_v0.yaml` | figure-8 | small_city | B — outdoor-open |
| `cafe_obstacle_crossing_v0.yaml` | straight through actor walking lane | cafe3 (5 baked actors) | A→D — indoor-narrow + light crowd |

Coordinates are educated guesses against the existing world geometry; the **first sim run will calibrate them** (named TODO: `[north-star] Calibrate v0 metric thresholds...`). Treat the v0 YAML values as a starting point, not ground truth.

## Schema (single-source-of-truth)

```yaml
name: <unique-id>                    # filename stem; used as run_id seed
description: <one-line>              # human prose
env_class: A | B | C | D | E         # per docs/environment_taxonomy.md
launch:
  file: <pkg launch filename>        # e.g. jackal_cafe.launch.py
  args:                              # passed verbatim to ros2 launch
    headless: 'false'
    use_rviz: 'true'
    # ...
world: <world filename>              # informational; the launch arg controls
                                     # the actual gz world.
start: { x: 0.0, y: 0.0, yaw: 0.0 }  # spawn pose; matches launch x/y/yaw args
goal:  { x: 0.0, y: 0.0, yaw: 0.0 }  # target pose used for goal_reached check
reference_path:
  type: straight | curved | figure8 | obstacle_crossing
  waypoints:                         # M >= 2 rows of [x, y, yaw_target]; the
    - [x, y, yaw]                    # path-tracking metrics consume exactly
    - ...                            # this list as the (M, 3) `path` array.
target_speed_mps: 0.5                # used for time_deviation expected-time.
expected_duration_s: 30              # informational; soft timeout for runner.
acceptance:                          # per docs/path_tracking_metrics.md v0
  cte_rms_max: 0.2                   # m
  cte_max: 0.5                       # m
  heading_err_rms_max: 0.15          # rad
  completion_min: 0.99               # [0, 1]
  goal_xy_tol: 0.2                   # m
  goal_yaw_tol: 0.3                  # rad
notes: <free-form>                   # known caveats, calibration TODOs.
```

### Field semantics

- **`reference_path.waypoints`** — explicit polyline. The metrics module
  (`eval.path_tracking_metrics.summary`) takes this exact shape `(M, 3)`. v0
  is piecewise-linear; spline interpolation is v1.
- **`acceptance`** — pulled from `docs/path_tracking_metrics.md` § "완벽" 의
  임계 (v0 가설). Indoor scenarios use the indoor row; outdoor uses outdoor.
  These are **hypotheses** — calibration round will overwrite them.
- **`launch.args`** — `run_metrics.py` will eventually read `start`/`goal` and
  pass them as launch args (`x:=…`, `y:=…`, `yaw:=…`). For now the YAML
  duplicates them under `launch.args` only when the launch defaults differ.

## How a future runner consumes this

```bash
ros2 launch representation_aware_mppi_bringup jackal_cafe.launch.py \
  include_run_metrics:=true \
  scenario:=eval/scenarios/cafe_straight_v0.yaml \
  run_id:=cafe-straight-001
# -> runs/cafe-straight-001.json with the metric scalar dict.
```

Wiring the `scenario:=` arg into the launch file is the **next** TODO
(`[north-star] Add include_run_metrics:=true option to jackal_cafe.launch.py`),
which is gated on PR #4 + the run_metrics PR landing.

## v0 limitations (deliberate)

- All paths are piecewise-linear — sharp cusps will show artificial CTE.
- No multi-waypoint sequence (single goal). Multi-leg routes are v1.
- Coordinates are pre-calibration; first real sim run will replace them.
- Obstacle scenario does not encode actor schedules — it relies on the
  five baked `<actor>` walks in `cafe3_jazzy.sdf.xacro`. Reproducibility is
  approximate (actors loop deterministically but phase depends on launch
  time). Better repeatability is a P4 problem.
