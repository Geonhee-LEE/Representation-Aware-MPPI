# Windowed arclength-progress critic: city_figure8_v1 goes from 0/4 to 4/4

- **Cycle**: 2026-10-02 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략 (D-510 follow-up: arclength-progress critic)
- **Phase**: P6
- **Status**: keep

## What I tried
- Diagnosed why the existing D-243 freeze price (`ProgressPriceCritic`, `w_freeze`) cannot fix the D-510 shortcut. Its `arclength_along` projects onto the *nearest* segment. On a figure-8 the goal lies on the path's last segment, so driving 1.74 m to the goal reads as ~15 m of progress. That projection is now pinned by a test.
- Added `critics/arclength_progress.py`, which does three things:
  - It projects rollouts onto the window `[s_robot-0.5, s_robot+3.5]` and keeps a monotone robot arclength.
  - It rewards each rollout by `w_progress·(s_end - s_robot)`.
  - It gates the terminal goal attractor until ≤3 m of path remain.
- Wired it into `StockMPPI` as `w_progress` (default 0: no projection, goal gate open, byte-identical runs).
- Ran a sweep on city_figure8_v1 × seeds 0-3 with `w_progress` ∈ {0, 10, 30, 100, 300}.

## What worked / what failed
- stock (w=0): 0/4, heading rms 2.20-2.53. The robot takes the shortcut. Completion reads 1.000, which is the same nearest-segment aliasing.
- w=10: **4/4**, cte_rms 0.020-0.022, cte_max ≤0.081, heading rms 0.10-0.14, 25.9-27.0 s.
- w=30: 4/4 (cte_rms 0.039-0.055, heading 0.11-0.16, ~24-25 s). w=100: 4/4 (cte_rms 0.11-0.14, heading 0.20-0.23, ~23.5 s).
- w=300: 0/1 (seed 0, heading 0.43). It overdrives.
- Trade-off: higher weight is faster but tracks worse. w=10 tracks best.
- For comparison (not re-measured): D-510's `w_freeze=1e4` drove the loop in 52-59 s with heading 1.04-1.16 and did not pass.

## North-star delta
- This is the first closed-loop path-tracking pass on a self-intersecting path. Path-tracking metrics (CTE/heading) on city_figure8_v1 are now measurable and inside acceptance.
- No movement on the obstacle scenes. The term is inert by default, and none of the 9 shipped scenes has been measured with it.

## Key learnings
- On a path that returns near its start, a goal attractor and a nearest-segment progress term are aliased the same way. The fix is to make the projection topological (windowed + monotone), not to raise a weight.
- The sandbox's own `completion_percent` metric has the same aliasing (stock reads 1.000 while skipping the loop). A completion-based pass is unreliable on self-intersecting paths.

## Recommended next 1–3 priorities
1. Cross-scene check: `w_progress=10` on the 9 shipped scenes × 4 seeds. Does the goal gate or the progress reward regress avoidance (crossing/cut_in/freezing)?
2. Make the `completion_percent` metric window-aware (or monotone), so a shortcut cannot read completion=1.0.
3. User policy call (still open): promote the scoped heading arm (D-508) and/or `w_progress`.

## Artifacts
- PR: none (branch continuation; PR #67 closed, new-PR work deferred by user)
- Files touched: eval/mppi_sandbox/critics/arclength_progress.py, critics/__init__.py, controllers/stock_mppi.py, tests/test_arclength_progress.py, tests/test_default_lam_sites.py
- TSV row appended: yes
