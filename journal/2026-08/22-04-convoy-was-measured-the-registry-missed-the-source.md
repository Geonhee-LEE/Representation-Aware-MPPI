# The scene the bottleneck sent me to measure was already measured

- **Cycle**: 2026-08-22 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `convoy-meas` Record per-seed clearance for `cafe_convoy_v0` — screened out
- **Phase**: P3
- **Status**: keep

## What I tried

- Picked STATE's #1 claude-actionable, `convoy-meas`: record per-seed clearance
  for `cafe_convoy_v0`, described there as "genuinely unmeasured".
- Before spending the measurement, checked the TODO DB for prior convoy work —
  the D-315 probe habit ("look for a receipt you have already earned") applied
  one layer up, to the measurement rather than the suite.
- Found a 2026-08-18 TODO reporting convoy's declared `0.30` graded against
  **8 seeds** of achieved clearance. Traced it to `scene_census.PAIRED_ENSEMBLE`
  — 8 seeds × 2 arms on `cafe_convoy_v0`, and another on `cafe_cut_in_v0`.
- Registered that source in `recorded_clearance.SOURCES` instead of measuring.

## What worked / what failed

- **The pick was a false lead and the tree could say so in 4 minutes.** No
  rollouts were needed: every input was already a constant. Had I run the
  measurement first it would have reproduced numbers taken four days earlier.
- **`drift()` read `IN_SYNC` the whole time, correctly and uselessly.**
  `scene_eligibility.RECORDED_SCENES` is *derived from* the same readers, so a
  missing reader moves derived and declared together. A census cannot see the
  one error that moves both of its sides — the guard was live, green, and
  structurally blind to this.
- This is D-413's own finding one layer down. That cycle replaced a one-element
  literal with a derivation and stopped; the derivation then read two of the
  tree's four ensembles. Deriving a set narrows the failure, it does not end it.
- `cafe_cut_in_v0` is the same omission with the harm masked — excluded
  `GOAL_BALL_BLOCKED`, so its absence changed no printed count. Same masking
  the D-413 docstring named for `cafe_freezing_v0`, and it recurred inside the
  fix for it.
- Six pins failed on the corrected census, all in the under-reporting
  direction. Every one was a test asserting the wrong number confidently.

## North-star delta

- **Measured coverage moves `1/3 → 2/3`** with zero rollouts — the number was
  wrong, not the world. `cafe_obstacle_crossing_v0` is now the only eligible
  scene genuinely unwalked.
- A queued cycle of avoidance measurement is refunded, and the next one points
  at the single remaining cell instead of one of two.
- No controller touched; obstacle-avoidance behaviour is unchanged.

## Key learnings

- **A derived census is only as wide as its reader registry, and the registry
  is still typed.** D-413 moved the typing from the *members* to the *sources*.
  That is a real narrowing — a re-pinned source now follows — but an unread
  module is still invisible, and this is the second time the same set was wrong.
- **When a bottleneck names a scene to go measure, check the tree for the
  measurement before buying it.** The bottleneck sentence is derived from a
  census, so it inherits every gap the census has, stated with full confidence.
- The cheap check that found this was the TODO DB, not the code: the 2026-08-18
  title said "convoy 의 0.30 은 아무것도 grade 하지 않는다", which is not
  something you can write about an unmeasured scene.

## Recommended next 1–3 priorities

- `crossing-meas` — record per-seed clearance for `cafe_obstacle_crossing_v0`,
  now the *only* unmeasured eligible scene. Verify against the tree first.
- `source-reach` — grade `recorded_clearance.SOURCES` against the modules that
  actually hold per-seed clearance rows, so an unregistered reader is loud.
  Twice-wrong warrants a census of the census.
- `convoy-0.30-vacuity` — convoy's declared `0.30` against its own 8 seeds:
  `threshold_vacuity` says `DISCRIMINATING` over the full registry but
  `VACUOUS_PASS` on the D-356 pair. Those disagree and the pair is the ensemble.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/recorded_clearance.py, eval/mppi_sandbox/tests/test_recorded_clearance.py, eval/mppi_sandbox/tests/test_scene_eligibility.py
- TSV row appended: yes
