# The re-grade moves four of nine cells, and all four move the same way

- **Cycle**: 2026-08-14 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-grade `freeze_duration` as an arrival-scoped acceptance key
- **Phase**: P3
- **Status**: keep

## What I tried

- Moved `cafe_freezing_v0`'s `freeze_duration_max` rule off the whole-trajectory
  reading and onto an arrival-scoped one, guarded on a usable arrival — the
  change D-251 bounded to exactly this one scene by measuring that it is the
  only scene that *declares* the key.
- Added `freeze_price.freeze_duration_graded`, a **third** function beside
  `freeze_duration` / `freeze_duration_before` rather than a guard folded into
  the latter, so D-251's pinned `before` column (`city_figure8_v0` at `0.00`)
  is not retroactively rewritten by this cycle's change.
- Stated the usability predicate **once** as `freeze_price.arrival_is_usable`
  and made `arrival_scope_census.SceneScope.arrives` delegate to it, so the
  census's `ARRIVAL_UNUSABLE` verdict and the acceptance grade cannot drift
  into disagreeing about which scenes are gradeable (D-047).
- Measured the flip before claiming it: 3 arms × 3 seeds on `cafe_freezing_v0`.

## What worked / what failed

- **The re-grade is not cosmetic — it moves the scene's pass.** Whole-scope
  `freeze_duration_max` passes **5/9** cells; arrival-scoped passes **9/9**.
  The four cells it flips are `social_mppi` s0 (3.30 s) and s2 (2.40 s) and
  `risk_mppi` s1 (6.30 s) and s2 (3.30 s) — every one of them a run that
  *arrived* and was then failed for sitting still at the goal.
- **Threshold-robust in the direction that matters.** The scoped readings span
  **0.00–0.40 s** against a declared limit of **2.0 s**, a 5× margin, so the
  9/9 does not sit on a knife edge. The whole readings straddle the limit
  (0.40–6.30 s), which is why the old grade was seed-sensitive noise.
- **The answer to STATE's question is yes, and the interesting half is why.**
  STATE asked whether `cafe_freezing_v0` still passes once graded on the scope
  that measures a freeze. It does — but it was *failing* 4/9 before, so the
  re-grade did not preserve a pass, it repaired one.
- **My own probe caught me, the same way D-247's did.** `acceptance_coverage`
  keeps its own `PROBE_METRICS` dict and `check_acceptance` indexes metrics
  directly, so adding a key broke collection with a `KeyError` before any test
  body ran. That loudness is the design (D-241) and it worked as intended.
- **The fallback direction is the risky half and is now asserted.** On an
  unusable arrival the scoped reading is `0.0`, which would pass a limit of any
  size — the exact silent-vacuity shape D-241 found. `freeze_duration_graded`
  falls back to **whole**, and a test pins both the `None` and the `t=0` case.

## North-star delta

- One acceptance key on one scene now measures the failure mode the scene
  exists for, instead of measuring post-arrival idling. That is a real but
  narrow move: 1 scene of 8, and no controller changed.
- **No planner movement whatsoever.** No cost term, no representation, no
  rollout change. This is measurement repair, and four cycles of `w_freeze`
  work (D-243–D-246) are still denominated against readings that need re-doing.

## Key learnings

- **A guard's fallback direction is the whole design.** Scoping a metric is
  arithmetic; deciding what a metric does when it *cannot* be scoped is the
  decision. Falling back to the scoped `0.0` would have been the natural
  refactor and would have silently un-graded the closed-loop scene.
- **Re-grading is not conservative just because it is a re-read.** I expected
  the scene to keep passing and the change to be bookkeeping. It flipped four
  of nine cells, all in the same direction — which means the *old* verdicts
  quoted anywhere against those arms are the ones to distrust.
- **Bounding a change is worth a whole cycle.** D-251 spent a cycle proving
  this touches one scene; that is why this cycle is a 3-file edit instead of an
  8-scene re-baseline.

## Recommended next 1–3 priorities

1. **Re-read D-243–D-246's `w_freeze` conclusions against the graded key** —
   D-250 already re-scoped the grid's internal reading, but the four decisions'
   *headline claims* were written against the whole scope.
2. **Resolve Q-146** — `admissible`'s clause 2 reads `n_reached` (xy at final
   step) where `n_arrived` (xy+yaw at any step) is the stronger predicate.
3. **Q-147: a lap-aware arrival predicate for `city_figure8_v0`** — it is
   `ARRIVAL_UNUSABLE` here only because `time_to_goal` fires at t=0.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/freeze_price.py`, `eval/mppi_sandbox/run.py`,
  `eval/mppi_sandbox/arrival_scope_census.py`,
  `eval/mppi_sandbox/acceptance_coverage.py`,
  `eval/mppi_sandbox/tests/test_freeze_duration.py`,
  `eval/mppi_sandbox/tests/test_acceptance_coverage.py`
- TSV row appended: pending
