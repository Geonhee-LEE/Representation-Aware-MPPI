# city_figure8 0/16 is a scene defect: start==goal, one circle twice

- **Cycle**: 2026-09-30 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] heading_err_rms_max residual (city_figure8 diagnosis)
- **Phase**: P6
- **Status**: keep

## What I tried
- Traced one stock_mppi rollout on city_figure8 (seed 0, 240 s) with heading error, completion and polar angle per step.
- Ran all 8 registered controllers for 40 s and measured max displacement from the start and orbit fraction.
- Read the heading metric (segment tangent, not `yaw_target`) and the stock cost terms.

## What worked / what failed
- The robot never leaves the start. It dithers within 1 m of (-25, -2.5) for 240 s, yaw winds to -8.5 rad, and mean v is 0.05 m/s. The heading rms of 2.07 is spin-in-place.
- All 8 arms behave the same: max displacement 0.80 m (essps 0.41 m), and at most 5% of one orbit.
- Cause 1: start == goal. The cost prices `dist_goal` (speed ramp + terminal) and nothing prices progress, so staying put is optimal.
- Cause 2: the 17 waypoints are one r=2.5 circle driven twice, not a figure-8. The overlap aliases completion to 0 at the final waypoint, so the stop rule can never fire.

## North-star delta
- The last "no arm passes" scene is reclassified. It is a scene-definition defect, not a controller gap, so the 0/16 says nothing about tracking quality.
- 3 new tests (about 2.5 s). The lam census moved from 98 to 99.

## Key learnings
- A heading-rms failure near π with CTE rms at 0.025 means "not moving", not "tracking badly". Check displacement first.
- Goal-attractor MPPI cannot drive a closed loop. The closed-path scenes need an arclength-progress term or an intermediate goal.

## Recommended next 1–3 priorities
- Rewrite city_figure8_v0.yaml as a true two-lobe figure-8 whose goal is not the start (or add a progress critic), then re-measure.
- User policy call on the scoped w_heading_near default (D-508).

## Artifacts
- PR: none (branch continuation; PR #67 closed)
- Files touched: eval/mppi_sandbox/tests/test_figure8_start_is_goal.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, docs/decisions.md
- TSV row appended: yes
