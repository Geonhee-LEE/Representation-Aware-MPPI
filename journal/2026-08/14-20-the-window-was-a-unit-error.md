# The window was a unit error — and the ratio walks back down

- **Cycle**: 2026-08-14 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `arm-scale-pick` (STATE #1) — close Q-151
- **Phase**: P3
- **Status**: keep

## What I tried

- Q-151's lean (b): pair D-264's audibility floor (`ratio ≥ 0.1`) with D-027's
  ESS-collapse ceiling (`6.19×`) into a window, on the stated ground that both
  are "multiples of the baseline spread".
- Before combining them, checked the premise the cheap way: `weight_units.measure`
  on `w_voo` at `1, 5, 20, 50, 200` on `cafe_obstacle_crossing_v0`, in exactly
  the isolation `arm_audibility.grade` uses.
- Landed the ladder as `MEASURED_CURVE` + `sweep_ratio` (re-take), and the
  reading as `window_verdict` / `ratio_is_monotone` / `inversion_error`, inside
  the existing `arm_audibility` module rather than a new one.

## What worked / what failed

- **The premise is false, twice over.** D-027's denominator is a *baseline*
  run's spread; `weight_units`' is the rest-of-cost on *the run the weight
  produced*. They agree only while the weight does not move the trajectory —
  which is precisely not where the ceiling lives.
- **The ratio is not monotone in the weight**: `0.02269 → 0.08354 → 0.3717 →
  0.6205 → 0.04876`. It peaks near `w=50` and falls back through the bar it had
  already cleared. `6.19` is never attained on the ladder, so it cannot bound
  an interval.
- **The collapse is in the denominator, not the numerator.** Per-unit spread
  moves 6.6% (`2.658 → 2.483`) — the numerator stays linear. `rest_median` goes
  `117 → 10183` (87×): a strong arm steers into geometry where `w_collision`
  fires, and drags its own ratio down.
- **D-264's `required_weight` is a prediction, not a measurement.** It said
  `5.428` for `ATTRACT_ONLY`; the measurement is still `FAINT` at `w=5`
  (`0.0835`) and crosses in `(5, 20]`. Overstates by up to `86.9×`.
- Scoping into `arm_audibility` instead of a new module avoided the nine-pin
  census tax that cost the 19:00 cycle a second full suite.

## North-star delta

- No closed-loop movement. But the arm strength that the Q-148 A/B would have
  been run at was about to be set by an inversion that overstates by up to two
  orders of magnitude — this is the second consecutive result that would have
  changed a run's outcome had the A/B been launched.
- The audible set now has a measured shape (bounded above by a *collapse*, not
  a value), which is what an eventual `ARM_SCALE` pick has to respect.

## Key learnings

- **A ratio whose denominator is measured on the perturbed run is not a
  transferable unit.** `weight_units`' own linearity licence is stated for a
  *fixed rollout batch*; `measure` reads a closed-loop run, and the two
  scopes silently diverge exactly where the knob starts mattering.
- **"Two measurements bracket a window" needs the quantity to be monotone**,
  and nobody checked. The check cost five sim runs (~65s) and refuted a
  decision the branch was one cycle from acting on.
- Q-151 falls back to option (a): declare the bar, sweep the weight. The sweep
  is now the honest instrument, not the inversion.

## Recommended next 1–3 priorities

- `voo-bar-crossing` — narrow `(5, 20]` to the weight where `w_voo` actually
  crosses `0.1`, and check whether the peak/collapse shape transfers to
  `cafe_freezing_v0` / `cafe_cut_in_v0` (D-260's non-transfer bites here too).
- `inert-probe-budget` — still open; this cycle dodged the tax by not adding a
  module, which is a workaround, not a decision.
- PR #68 merge remains the only route to a `w_epist` reading.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/arm_audibility.py, eval/mppi_sandbox/tests/test_arm_audibility.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
