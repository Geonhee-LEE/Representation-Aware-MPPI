# The freeze the grid was pricing was not there

- **Cycle**: 2026-08-14 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-read the `w_freeze` grid with the pre-arrival stall
- **Phase**: P5
- **Status**: keep

## What I tried

- Re-ran D-246's exact grid — 10 weights x 12 seeds, `social_mppi`,
  `cafe_freezing_v0`, `lam = PAIRED_LAM = 0.8` — computing **both** stall
  readings off each single run: whole-trajectory (`freeze_duration`, what
  D-244/D-245/D-246 graded) and cut at that run's own first-arrival time.
- Factored the truncation into `freeze_price.freeze_duration_before` so
  `arrival_spread.stall_split` and `freeze_weight.sweep` share one definition
  rather than two copies that can disagree.
- Put a `scope` axis on every verdict in `freeze_weight`, defaulting to
  `before`; kept `whole` reachable by name so D-244/245/246 reproduce.

## What worked / what failed

- **The whole-scope column reproduces D-246 digit-for-digit** — `12,12,12,12,
  12,12,8,6,12,12` exceed across the grid. So this is a re-read of that curve,
  not a different measurement glued onto its conclusion.
- **The verdict inverts**: `NONE_ADMISSIBLE` → **`NO_FREEZE_TO_PRICE`**. The
  ablation (`w_freeze = 0`) is **0/12 exceed** pre-arrival, median longest stall
  **0.40 s** against the declared **2.0 s**. There was no freeze to buy.
- Stronger than the ablation alone: **not one arrived run breaches the limit at
  any weight** — 0/12 among arrived runs in all ten cells. The pre-arrival
  exceedances that do appear (`1e5` 1/12, `3e5` 11/12, `1e6` 12/12) are
  **entirely arrival-censored** runs, where `before == whole` by construction.
- Turned up a second disagreement I did not go looking for: **`reached_goal` is
  12/12 at every weight while `time_to_goal` says 28/120 runs never arrived**,
  all 12 of them at `1e6`. Not a contradiction — `ab.reached_goal` tests the
  **final** timestep's xy, `time_to_goal` tests xy **and yaw** at any step. So
  those runs park on the goal without ever reaching the goal *pose*.

## North-star delta

- **Four cycles of `w_freeze` results are now denominated against a reading
  that measures the robot rather than the simulator.** D-243's headline
  (`2/3 → 0/3` at `1e4`) survives only as an artifact: the arm it "fixed" was
  never failing pre-arrival.
- `ProgressPriceCritic` moves from "inadmissible at every tested strength" to
  "answering a question this scene does not pose" — and the grid says pricing
  progress *hard* actively destroys the goal pose (`1e6`: 0/12 arrive).
- No movement on obstacle avoidance itself; this is a measurement correction.

## Key learnings

- **A cost term can pass its own acceptance test for four cycles because the
  metric it is graded on has no terminal condition.** The correction was
  available the whole time from a metric already on every run — first-arrival
  time — and nothing compared the two.
- The clean predicate is not "did it freeze" but "did it freeze *while it still
  had somewhere to go*". `scope_disagrees()` makes that a check a future
  scene's grid fires by itself.
- `reached_goal` and `time_to_goal` are **two different completion predicates**
  and the admissibility clause reads the weaker one. A cell can score
  "12/12 reached" with zero runs at the goal pose.

## Recommended next 1–3 priorities

1. **Re-grade `freeze_duration` itself as an arrival-scoped acceptance key** —
   the scene's `freeze_duration_max` is still computed whole-trajectory by
   `run.py`, so every *scene* carries the contamination this cycle removed from
   one grid.
2. **Sweep all 10 scenes for `duration_s >> time_to_goal`** (Q-145 lean (b)) —
   says immediately which other scenes' acceptance keys are latently contaminated.
3. **Resolve Q-146**: decide whether `ab.reached_goal` should require the goal
   pose, or whether the admissibility clause should read `n_arrived`.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/freeze_price.py`,
  `eval/mppi_sandbox/freeze_weight.py`, `eval/mppi_sandbox/arrival_spread.py`,
  `eval/mppi_sandbox/tests/test_freeze_weight.py`,
  `eval/mppi_sandbox/tests/test_freeze_duration.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: pending
