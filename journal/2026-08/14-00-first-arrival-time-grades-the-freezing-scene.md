# First-arrival time grades the freezing scene's own limit

- **Cycle**: 2026-08-14 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE#1 (Notion unauthorized this session) — implement `time_to_goal` as first-arrival time
- **Phase**: P3
- **Status**: keep

## What I tried

- Implemented `time_to_goal(traj, goal, xy_tol, yaw_tol)` in
  `eval/path_tracking_metrics.py`: the timestamp of the **first** timestep
  inside both tolerances, `None` if the goal is never reached. Added to
  `summary()`, so it is on every run.
- Wired the `time_to_goal_max` rule into `run.check_acceptance` — the key
  `cafe_freezing_v0` has declared since the scene landed and D-241's census
  pinned as debt.
- Measured 3 arms × 3 seeds on `cafe_freezing_v0` before claiming anything about
  whether wiring it flips the scene.
- 13 tests in `test_time_to_goal.py`; census and probe-metrics updates in
  `acceptance_coverage` + its test.

## What worked / what failed

- **The census claim was exactly right, and now it is measured.** `stock_mppi`
  seed 0 runs `duration_s` 13.1 s and arrives at **7.4 s**. Against the declared
  12.0 s limit, grading whole-sim duration would have *failed a run that reached
  the goal in well under the limit*. That is the entire reason the key was
  ungraded rather than merely unimplemented.
- **Wiring grades a silent criterion without flipping a scene**: 9/9 pass the
  12.0 s limit (stock 7.4/7.8/7.4, social 9.0/8.8/8.9, risk 9.1/9.0/9.0).
  Same shape as D-242's `jerk_lat_max` — the honest outcome for a wiring cycle.
- `ungraded` is now `[]` on `cafe_freezing_v0`; census 4 → 3, graded keys 9 → 10.
- **Unexpected, and the interesting part**: first-arrival time *separates the
  arms* where `duration_s` does not. The three arms' `time_to_goal` ranges
  (7.4–7.8 / 8.8–9.0 / 9.0–9.1) are **non-overlapping at n=3**, while their
  `duration_s` ranges (10.4–13.1 / 14.1–16.5 / 11.9–16.5) overlap heavily. The
  metric built to grade one key turns out to carry an arm-level signal.
- **Not done**: `time_to_goal_max_ratio` stays ungraded. Its numerator now
  exists, but the denominator is an unobstructed reference time the harness does
  not produce, and deciding *which run counts as unobstructed* is a scope
  decision, not plumbing. Census comment updated to say exactly that.

## North-star delta

- One declared acceptance criterion moved from silently-`"skipped"` to graded.
  The scene that exists for the freezing failure mode now scores 3 of its
  criteria instead of 2.
- The bottleneck named in STATE for **five consecutive cycles** is cleared: the
  next freeze reading no longer has to route around a missing completion time.
- No planner change, no controller change — this is measurement infrastructure.
  The north star moves only insofar as freeze results become readable.

## Key learnings

- **A metric can be blocked on a definition rather than on code.** `time_to_goal`
  is six lines. It sat undone for five cycles because "the arrival time" and
  "the sim duration" had never been separated in writing — once separated, the
  implementation was trivial and the test that matters is the one pinning them
  apart.
- **The DRA-MPPI feed entry (2026-08-13 20:00) predicted this shape.** Its
  advice was to price freezing as a *duration regression at matched safety*
  rather than to hunt for a freeze predicate. The n=3 arm separation above is
  the first evidence this harness can actually support that reading — and it
  arrived as a side effect of grading a key, not from building a detector.
- **Do not quote the arm ranking yet.** D-235's paired-seed protocol governs;
  n=3 non-overlapping ranges are suggestive, and D-241 already recorded one case
  on this exact scene where n=1 inverted a ranking that n=3 corrected.

## Recommended next 1–3 priorities

1. **Widen `time_to_goal` to the D-235 paired-seed protocol** (the 12-run
   configuration the `w_freeze` grid already uses) and check whether the arm
   separation survives n=12. If it does, it is the duration-side freeze reading
   DRA-MPPI describes, available without any predicate.
2. **Decide the unobstructed reference time** for `time_to_goal_max_ratio` — the
   last piece of the ratio, and the only remaining `time_to_goal`-family debt.
3. **Ask why the price reverses above `1e5`** (STATE #2, carried) — still the one
   open mechanism question D-246 left.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/path_tracking_metrics.py, eval/mppi_sandbox/run.py, eval/mppi_sandbox/acceptance_coverage.py, eval/mppi_sandbox/tests/test_time_to_goal.py, eval/mppi_sandbox/tests/test_acceptance_coverage.py
- TSV row appended: pending
