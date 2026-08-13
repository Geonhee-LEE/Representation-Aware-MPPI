# The freezing scene was never the only contaminated one

- **Cycle**: 2026-08-14 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — sweep all 10 scenes for `duration_s ≫ time_to_goal` (Q-145 lean (b))
- **Phase**: P5
- **Status**: keep

## What I tried

- Swept every shipped scene (8 — `lam_windows.yaml` is a variant table, not a
  scene) at `stock_mppi` seed 0, taking **both** stall readings off each single
  run: `freeze_duration` whole-trajectory and `freeze_duration_before` scoped to
  that run's own first arrival. D-250's method, applied one level down.
- Reported Q-145's requested `duration_s / time_to_goal` ratio beside the scope
  disagreement, so the two could be compared rather than assumed to agree.
- Shipped `arrival_scope_census.py` + 17 tests: per-scene verdict census,
  `ratio_ranks_contamination()` as a live predicate, and a third verdict
  category for arrivals that are not measurements.

## What worked / what failed

- **`cafe_freezing_v0` is not special.** All **6** arriving scenes are
  contaminated, post-arrival share **25.0 %** (`cafe_convoy_v0`) to **100.0 %**
  (`cafe_head_on_v0`, `cafe_obstacle_crossing_v0`). What makes the freezing scene
  look unique is only that it is the one scene that *declares*
  `freeze_duration_max` — the defect is in the metric, and the single
  declaration is all that has been containing it.
- **Q-145's own lean is refuted by its own sweep.** The ratio does **not**
  rank-order contamination (`ratio_ranks_contamination` → `False`):
  `city_curved_v0` has the *lowest* ratio of any arriving scene (**1.06**) and
  is **56.5 %** post-arrival, while the two 100 % cells sit at ratios 1.21 and
  1.73. Any threshold clearing the lowest-ratio scene also clears a scene whose
  reading is *entirely* post-arrival — no tuning recovers it. The precondition
  census would have cleared exactly the wrong scenes.
- **Arrival-scoping is not uniformly an improvement**, and two scenes say so.
  `city_figure8_v0` is a **closed loop** — start pose *is* goal pose,
  `(-25.0, -2.5, 0.0)` both — so `time_to_goal` fires at **t = 0.0** before the
  robot moves, and the arrival-scoped reading is `0.00` for any controller on
  any seed against `29.60` whole. `cafe_cut_in_v0` never arrives, so the scopes
  coincide by construction. Both are `ARRIVAL_UNUSABLE`, deliberately disjoint
  from `CLEAN`.

## North-star delta

- The blast radius of the pending re-grade is now **measured, not guessed**: 6
  scenes change reading, 2 cannot be graded on either scope until they get a
  lap-aware / never-arrived arrival predicate.
- No planner behaviour moved — this is a measurement-integrity cycle. Honest
  zero on avoidance and tracking.

## Key learnings

- **A precondition is not a predictor.** The ratio measures how much time is
  left after arrival; contamination measures whether *the longest stall* falls
  in that window. A run can idle briefly in a long tail it never enters, and
  park hard in a short one. Cheap declarative censuses need their predictive
  claim measured before they are believed — this one cost one sweep to refute.
- **`time_to_goal` has a degenerate case nothing had hit yet**: on a closed-loop
  path it is satisfied at t=0. Any arrival-scoped quantity inherits that, so the
  re-grade cannot be a blanket substitution.
- The re-grade (STATE #1) should be scoped to scenes that **declare** the key
  and have a usable arrival — today that is exactly `cafe_freezing_v0`, which
  makes it a much smaller change than the bottleneck sentence implied.

## Recommended next 1–3 priorities

1. Re-grade `freeze_duration` arrival-scoped in `run.py`, guarded on a usable
   arrival — the census says only `cafe_freezing_v0` grades it today, so this is
   now a bounded change rather than an 8-scene re-baseline.
2. Give `city_figure8_v0` a lap-aware arrival predicate (first return to goal
   pose after leaving it) — `goal_reached` is vacuously true there too.
3. Resolve Q-146 — `admissible`'s clause 2 from `n_reached` to `n_arrived`.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/arrival_scope_census.py, eval/mppi_sandbox/tests/test_arrival_scope_census.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
