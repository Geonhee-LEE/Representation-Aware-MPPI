# The retirement holds, but only below the isotropic split

- **Cycle**: 2026-08-23 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-take D-446's lever ladder in the robot frame
- **Phase**: P5
- **Status**: keep

## What I tried

- Re-scored `avoidance_budget.lever_over_bands` against the robot-origin
  tangential share (`crossing_geometry.SeedCPA.measured_from_robot`) instead of
  the foot-origin `SeedBudget.bearing_tangent_frac`, on the **same 32 runs**
  (2 arms × 16 seeds, `cafe_obstacle_crossing_v0`). Zero new scenarios.
- Added `lever(..., shares_by_seed=...)` — a seed-keyed override of *which
  number the band is applied to*, leaving the excursion filter and the 2:1
  majority rule stated once, where they already live.
- Added `crossing_geometry.robot_frame_shares()` as the supplier, plus 6 unit
  pins (both frames, both directions, the abstention rule, the seam end-to-end).

## What worked / what failed

- **The verdict is not band-stable, and both arms agree exactly.** Foot frame:
  TIMING at 0.50 / 0.707 / 0.85. Robot frame: TIMING at 0.50 and 0.707,
  **PREDICTION at 0.85**.
- **The flip is not marginal — it is unanimous.** In the robot frame **0 of 16
  seeds in each arm** reach 0.85; in the foot frame 16/16 (w=0) and 13/16
  (w=32) do. Population means: 0.956 → 0.741 and 0.929 → 0.729.
- At 0.707 the robot frame still returns TIMING on 12/16 and 11/16 tangential
  (3:1 and ~2.75:1), so the two lower rungs are held with margin, not barely.
- The re-score needed no new sim, as STATE predicted — but it did need one new
  seam, because `lever` had the foot number hard-coded inside the count.

## North-star delta

- No acceptance metric moved — this is measurement validity, like the two
  cycles before it.
- The scope of a **retired branch of work** is now correct: D-430 / D-433 /
  D-440 were retired on TIMING, and TIMING is now known to be a claim at
  bands ≤ 0.707, not at 0.85. Cost-side tuning on this scene is narrowed, not
  closed at every threshold.

## Key learnings

- **D-445's discipline caught its own author.** "A verdict that flips with its
  own threshold was never a verdict" was written about the ladder; the ladder
  was then read in a frame where it does not flip. Sweeping the band and
  sweeping the frame are two different sweeps, and only one was being done.
- **The frame bias and the top rung are the same size, which is why nothing
  looked wrong.** D-447 measured the foot-vs-robot gap at +0.215 / +0.200; the
  distance from the isotropic split 0.707 to the top rung 0.85 is 0.143. A bias
  larger than the rung spacing can carry a whole population across a rung
  without any single value looking implausible.
- **Re-scoring beat re-implementing.** The override is ~10 lines and the
  electorate rule stayed in one place; a parallel robot-frame `lever` would
  have been a second copy of the 2:1 majority to keep in sync.

## Recommended next 1–3 priorities

1. **Restate D-430 / D-433 / D-440's retirement with its band** — they cite
   TIMING without one. One doc pass, no sim.
2. **Q-191** — `target_speed_mps: 0.3` declared vs 0.70–0.80 observed; grep the
   field's consumers in the sandbox path first.
3. **Q-192 + Q-183** — delete one of option (c)'s two conflicting triggers.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/avoidance_budget.py, eval/mppi_sandbox/crossing_geometry.py, eval/mppi_sandbox/tests/test_avoidance_budget.py, eval/mppi_sandbox/tests/test_crossing_geometry.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes
