# Asymmetric retreat price removes head_on's attractor-off regression

- **Cycle**: 2026-10-04 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` heading_err_rms_max under knee+shape (progress sub-thread)
- **Phase**: P6
- **Status**: keep

## What I tried
- Tested the STATE hypothesis that head_on backs up because `arclength_windowed` clips at `s_robot - back`. I extrapolated the first segment backward so that points behind the start read negative arclength. n=16 head_on median T went 42.1 → 40.4 s, so the clip was not the cause. Dropped.
- Per-seed trace: 11/16 seeds retreat to y≈+1.41 and stall for 15-23 s. The other 5 pass the pedestrian in ~14 s. The progress reward is symmetric, so ending 1 m behind `s_robot` costs only `w_progress`·1 m, which is less than the barrier cost of the oncoming pedestrian.
- Added an inert `retreat_gain` (`progress_retreat_gain`, default 1.0) that multiplies the cost of backward rollouts. Gain ladder on head_on: k=1 40.4 s (6/16 fast), k=10 13.9 s (12/16), k=100 12.3 s (16/16).

## What worked / what failed
- w10 + retreat_gain 100 at n=16 on 8 scenes: head_on T 42.1 → 12.3 s. crossing 16/16, curved cte .030, figure8_v1 16/16, and convoy/freezing/contested/straight 16/16 are all byte-identical in pass/T/cte.
- head_on still fails 0/16 on min_distance_to_obstacle and cte_rms. That is the same failure as with the attractor on (w0). It is a band/geometry issue, not a progress issue.
- The lam census moved (forwards 49→50, total 260→261). census_preempt caught it before the suite ran.

## North-star delta
- First arm that keeps all the D-511/D-512 tracking gains (crossing 6→16/16, curved cte .145→.030, figure8_v1 0→16/16) without the +32 s head_on regression. Residual cost: +2.4 s on head_on vs w0.
- `w_progress=10 + retreat_gain=100` is now a candidate tracking default.

## Key learnings
- Before pricing a geometry gap, read the trajectory. The retreat was a cost trade-off, not a free move: the robot was pushed back by the barrier because going back was cheap.
- An asymmetric progress price has a natural reading. Forward progress is a reward, and backward motion is a commitment violation priced much higher.

## Recommended next 1–3 priorities
- Promote `w_progress=10, progress_retreat_gain=100` as the knee+shape tracking default (all 9 shipped scenes × n=16, include cut_in / figure8_v0 for completeness).
- Sweep k ∈ {30, 100, 300} on crossing to check whether the yield survives at higher gains.
- head_on min_distance (0.30 band) is the remaining failure. It is common to all arms.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/critics/arclength_progress.py, eval/mppi_sandbox/controllers/stock_mppi.py, eval/mppi_sandbox/tests/test_retreat_price_removes_head_on_regression.py, eval/mppi_sandbox/tests/test_default_lam_sites.py
- TSV row appended: yes
