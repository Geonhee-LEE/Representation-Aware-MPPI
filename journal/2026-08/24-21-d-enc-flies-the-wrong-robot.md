# `d_enc` flies a robot no arm runs — and the two obstacle scenes swap verdicts

- **Cycle**: 2026-08-24 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c5c5d39` Q-198 resolution — contested_v0 re-authoring vs column purchase
- **Phase**: P3
- **Status**: keep

## What I tried

- Took Q-198 as STATE framed it: move `cafe_obstacle_contested_v0`'s obstacle lane
  ~0.3 m toward the path (1-line yaml) so its `d_enc = 1.0849` / forced `0.0` stops
  reading `VACUOUS_PASS`.
- Before editing, checked what `d_enc` actually measures. `obstacle_reach.scene_reach`
  flies the nominal robot at `scenario.target_speed` — and this scene's yaml declares
  `target_speed_mps: 0.3` while documenting, in its own comment, that 0.3 is
  screen-only and the schedules are solved against the measured 0.723 m/s cruise.
- Re-measured every scene at 0.723 instead. Static geometry only, **zero rollouts**.
- Shipped the gap as a pinned census (`CRUISE_CENSUS`, `DECLARED_SPEEDS`,
  `SPEED_INVERTED`) + 6 tests, rather than repairing `scene_reach`.

## What worked / what failed

- **Q-198's premise is defective.** At the cruise, contested_v0 puts **all five actors
  within 0.003–0.010 m** of the nominal robot: `d_enc = 0.0028`, forced `0.5972 m`.
  The scene stages exactly the contest it advertises. The lane move would have been a
  repair to a working scene, and would have destroyed its measured 8-arm clearance
  column (0.4323–0.7314) on the way.
- **The error is an inversion, not a shift.** At declared speeds `crossing_v0` forces
  0.5070 and contested 0.0; at the cruise `crossing_v0` forces **0.0** (4 of its 5
  actors sit 1.8–3.0 m away) and contested forces 0.5972. The scene the module calls
  `DISCRIMINATING` and uses as its 0.5070 floor is the one that excites nothing at the
  speed the robot runs.
- **Stronger than expected, caught by my own test.** I asserted "every scene declares
  0.3"; `cafe_convoy_v0` declares 0.5. Real state: **four distinct declared speeds
  (0.3–0.6) across nine scenes, none equal to 0.723** — so `d_enc` is not
  scene-comparable either. Cost 0.6 s, before any suite.
- **The suite came back red on one test, and it was in the list `census_preempt`
  says it does not cover.** `test_key_discrimination` pins the narrow key's
  composition by hand; `measure_at` entered it as a LIVE name, so `(21, 15) ->
  (22, 16)` and the non-LIVE fraction the verdict rests on *fell* (0.173 -> 0.162).
  An ordinary join, re-pinned. Cost: a second 25-min suite, because a hand-pinned
  census is invisible to the 2-s instrument built to preempt exactly this.
- **Did not repair `scene_reach`.** Re-pointing it at the cruise moves `CENSUS`,
  `UNBARRED_EXCITED`, the 0.5070 floor and `threshold_vacuity` in one commit — the
  D-458 shape (16 reds that were really 24). Filed as Q-200.

## North-star delta

- **A false negative on the 다중-obstacle class is retracted.** contested_v0 was recorded
  as "placed but grading nothing"; it is in fact the most excited obstacle scene shipped
  (forced 0.5972 m). The 9-scene matrix is better than STATE believed.
- **A previously-unknown false positive is exposed**: `crossing_v0`, the single scene
  every cross-track finding is calibrated on, forces zero excursion at the real cruise.
  Findings #1/#2/#3 of `obstacle_reach` inherit that.
- No controller code, no rollouts, no measured physical quantity moved. The movement is
  that ~80 rollouts and a scene re-authoring were both priced and both refused.

## Key learnings

- **A space-time census has a speed argument, and nobody had asked which one it used.**
  `d_enc` looked like a property of the scene; it is a property of (scene, speed). The
  three cycles that reasoned from `1.0849` all treated it as the former.
- **The yaml said so.** contested_v0's own comment block states 0.3 is screen-only and
  names 0.723 as what the schedules solve against. The instrument read the field the
  comment disowns — the contradiction was in one file, readable without running anything.
- **Pin the gap, don't close it.** Making the disagreement a graded census keeps the
  repair a separate, costed decision instead of a cascade discovered by a 25-min suite.

## Recommended next 1–3 priorities

1. **Q-200**: re-point `scene_reach` at `CRUISE_SPEED` and absorb the cascade in one
   dedicated cycle — `CENSUS` (6 rows), `UNBARRED_EXCITED`, the 0.5070 floor,
   `threshold_vacuity` grades. Budget it as a census cycle, not a one-liner.
2. **Re-grade `threshold_vacuity` for contested_v0** once (1) lands: its `VACUOUS_PASS`
   rests on `attained()`, which is measured, so it may well survive — but its *stated
   reason* ("the band is not near the path") is now known false.
3. **Q-183, ninth instance** — `key_discrimination`'s narrow-key composition is
   named in `census_preempt`'s `UNCOVERED` line and still costs a full suite to
   catch. Deriving it is the standing fix nobody has priced.
4. **Re-read D-451's "meets 2 of 5"** against the cruise number: at 0.723 crossing_v0
   meets **1** of 5, not 2.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/obstacle_reach.py, eval/mppi_sandbox/tests/test_speed_load_bearing.py, eval/mppi_sandbox/tests/test_key_discrimination.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes
