# v0 path-tracking scenarios — 4 spec YAMLs + schema README

- **Cycle**: 2026-05-06 01:10 KST
- **Branch**: `autoresearch/p1-eval-scenarios-yaml-v0`
- **TODO**: `8188a782` [north-star] eval/scenarios/*.yaml v0 — straight/curved/figure8/obstacle_crossing
- **Phase**: P1
- **Status**: keep

## What I tried

- Wrote 4 YAML scenario specs in `eval/scenarios/`: `cafe_straight_v0`, `city_curved_v0`, `city_figure8_v0`, `cafe_obstacle_crossing_v0`. Each defines start/goal poses, polyline waypoints, target speed, expected duration, and acceptance thresholds.
- Authored `eval/scenarios/README.md` documenting the schema (single-source-of-truth) and the run-time consumption pattern (`scenario:=…` arg into the launch file once it lands).
- Tied each scenario's `env_class` to `docs/environment_taxonomy.md` rows (A, B, B, D). Pulled acceptance numbers from `docs/path_tracking_metrics.md` v0 thresholds.
- Verified all 4 parse via `yaml.safe_load` + required-key check; appended `qual:yaml-parse-ok` row to `results/p1-eval-scenarios-yaml-v0.tsv`.

## What worked / what failed

- All 4 YAMLs parse and pass the required-key contract. The figure-8 waypoint table (17 rows of pi/4-spaced points across two lobes) is the only one with non-trivial geometry and it lints clean.
- Decision tree applied correctly: top-priority Today TODO (jackal_cafe launch flag, P0) was *aligned* with bottleneck but had a hard "depends on PR #4 + p1-eval-run-metrics-node merged" guard. Branching off main with stacked autoresearch deps would violate the "never branch off another autoresearch branch" rule, so I dropped to the next aligned Today item.
- No code build run — pure config files, no `src/` touched, `colcon` smoke step skipped per the prompt.

## North-star delta

- **+1**: `eval/run_metrics.py` (already shipped) now has a concrete consumer contract — start/goal/path are no longer abstract. The metric harness ↔ scenario boundary is defined.
- **+0** distance to the *first quantitative number* — that still requires PR #4 + run_metrics PR merge + a sim run. v0 scenarios do not change that gating.
- **−** future calibration debt: coordinates are educated guesses against `cafe3_jazzy.sdf.xacro` and `small_city.sdf.xacro` geometry. First sim run will overwrite them.

## Key learnings

- "Highest-Priority Today" picks *can* be silently blocked by un-merged-PR dependencies — the decision tree as written doesn't model dependency graphs. Going forward, when a P0 Today picks fails feasibility, fall through to the next Today item rather than skipping the cycle (this is what I did, but it's worth encoding in `auto_research.md` as an explicit decision-tree note).
- Scenario YAML schema usefully forces the next launch.py wiring TODO to be unambiguous: the launch file just needs to parse start/goal/waypoints and pass them to the run_metrics node.
- Pure-spec cycles (no code, no smoke) finish well under the 15-min EXECUTE budget — used the headroom for a thorough README + multi-scenario coverage.

## Recommended next 1–3 priorities

1. **PR-merge cluster** (user-blocked): merge PR #4 (`autoresearch/p1-path-tracking-metrics-v0`), then `autoresearch/p1-eval-run-metrics-node`, then this branch. After all three, `eval/run_metrics.py` + scenario YAMLs are jointly importable on main.
2. **`include_run_metrics:=true` launch flag** (claude autonomous, was blocked, becomes feasible after step 1): wire `jackal_cafe.launch.py` and `jackal_outdoor_sim.launch.py` to spawn the metrics node and accept `scenario:=`.
3. **Calibrate v0 thresholds against first sim** (user verification, then claude follow-up): run `cafe_straight_v0` once, snapshot the JSON, replace the hypothesis numbers in this branch's `acceptance:` blocks + `docs/path_tracking_metrics.md`.

## Artifacts

- PR: pending merge (`autoresearch/p1-eval-scenarios-yaml-v0`)
- Files touched: `eval/scenarios/{README.md,cafe_straight_v0.yaml,city_curved_v0.yaml,city_figure8_v0.yaml,cafe_obstacle_crossing_v0.yaml}`, `results/p1-eval-scenarios-yaml-v0.tsv`, `RESULTS.md`
- TSV row appended: yes (`qual:yaml-parse-ok`, status=keep)
