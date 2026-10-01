# city_figure8_v1: true two-lobe figure-8, but stock MPPI shortcuts to the goal

- **Cycle**: 2026-10-01 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략 (D-509 follow-up: rewrite city_figure8)
- **Phase**: P6
- **Status**: keep

## What I tried
- Resumed the killed 10:00 cycle, which left `city_figure8_v1.yaml` and `test_figure8_v1_scene.py` staged and uncommitted (the `tree_provenance declared` gate flagged them as UNDECLARED drift).
- Re-ran the 4 new tests (green in 1.9 s) and committed the scene (D-510).
- `census_preempt` flagged a lam_site_census drift (defaults 99→100) from the new test's `stock_mppi` build. I bumped the four pins in `test_default_lam_sites.py` the same way D-509 did.

## What worked / what failed
- v1 fixes all three yaml defects: two lobes, the stop rule is reachable at the final waypoint, and goal != start.
- It still measures nothing as a tracking scene. The goal must sit near the start for a figure-8, so stock MPPI drives straight to it and never reaches the right lobe (pinned: travel < 3 m).
- The 10:00 run's docstring also reports that 8 arms × 4 seeds give 0/32 and that `w_freeze = 1e4` drives the loop but does not pass. This cycle did not re-measure either claim. They stay reported, not pinned.

## North-star delta
- The matrix now has a geometrically valid closed-loop tracking scene. Its first finding is a controller gap: goal-attractor costs do not track a path that returns near its start.

## Key learnings
- A cycle killed after a suite still leaves useful work in the index. `tree_provenance declared` is what surfaced it.
- Every new test that builds a controller without `lam` moves 4 lam pins. Run `census_preempt` before the commit, not after.

## Recommended next 1–3 priorities
1. Add an arclength-progress critic (inert by default) and measure it on city_figure8_v1 against `w_freeze`.
2. User policy call on the scoped `w_heading_near` default (D-508).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/scenarios/variants/city_figure8_v1.yaml, eval/mppi_sandbox/tests/test_figure8_v1_scene.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, docs/decisions.md
- TSV row appended: yes
