# The temperature was never reachable, and there is an operating point behind it

- **Cycle**: 2026-08-15 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bcc5d39` [sandbox] freezing-lam-calibration: `cafe_freezing_v0` 에 `calibrate_lam` 적용 후 D-266 ratio ladder 재취득
- **Phase**: P3
- **Status**: keep

## What I tried

- D-268 left the suspicion that `cafe_freezing_v0`'s all-rung ESS degeneracy was
  caused by an uncalibrated temperature, and never tested it. Checked the
  suspicion against `eval/scenarios/lam_windows.yaml`, which already records
  this cell as admissible at `lam ∈ (0.2, 0.4, 0.8)` — a window whose floor is
  **twice** the shipped `MPPIParams.lam = 0.1`.
- Re-took both readings — median ESS and D-266's audibility ratio — across all
  three calibrated rungs × the five ladder weights (25 closed-loop runs), in
  the same `ess_at_peak.ISOLATION` D-266 and D-268 used, so temperature is the
  only thing that moved.
- Landed `eval/mppi_sandbox/calibrated_ladder.py` (recorded table + `Point`
  grading + `verdict` + re-take `sweep`) with 15 tests, and fixed the plumbing
  gap in `ess_at_peak.sweep_ess` / `arm_audibility.sweep_ratio`.

## What worked / what failed

- **`lam` was not reachable from any sweep in this branch.** It lives on
  `MPPIParams`, and neither `StockMPPI` nor `RiskMPPI` accepts it as a keyword,
  so `ab.run_arm(..., lam=0.4)` raises `TypeError`. That is the mechanical
  reason four cycles of ladders all ran at `0.1` — not a step anyone forgot,
  but a parameter the sweep API did not expose. Both sweeps now forward `params`.
- **`(lam = 0.8, w_voo = 5)` is in band *and* audible** — ESS `31.23` inside
  `(12.8, 128.0)`, ratio `0.2285` over the `0.1` bar, goal reached. It is the
  first co-satisfying operating point this branch has measured, and it is
  unique across the 15 cells.
- **The ladder can now address D-027.** At `lam = 0.8` ESS holds band at `w = 5`
  and is out by `w = 20` — an in-band rung to fall from, which is exactly what
  D-268 said the uncalibrated ladder lacked.
- **Two test failures caught me overclaiming, and both stuck.** I wrote "every
  rung moves under recalibration"; `w = 20` moves 6.8% and `w = 50` 7.9%. And
  `window_is_keyed` crashed on a `None` weight. The docstring now claims only
  the two rungs that actually move (`w = 5`: +37%, `w = 200`: −23%) and a
  second test pins the middle as *stable*.

## North-star delta

- **First usable `(temperature, weight)` cell on this branch** — every prior
  audibility number was taken on a planner following one rollout. This is one
  scene at one seed, so it is a foothold, not a scale pick.
- D-266's headline `3.2644` and D-268's degeneracy verdict are both now
  scope-limited to `lam = 0.1`; neither is overturned, and D-268's verdict is
  re-asserted by a test at its own temperature.

## Key learnings

- **An unreachable parameter looks exactly like a forgotten step.** Four cycles
  "never called `calibrate_lam`"; none of them could have. The pin
  `test_lam_is_unreachable_as_a_controller_kwarg` exists so the workaround gets
  deleted rather than fossilised if `lam` ever becomes a real kwarg.
- **A calibration window is keyed to a cost field.** This one is graded
  `UNKEYED` — the shipped table records no `calibration_weight` — and it was
  taken with the epistemic channels off, while this ladder walks `w_voo` to
  `200`. The window is what made `0.8` worth trying; the ESS readings are the
  evidence it weights. `window_is_keyed` reports that rather than hiding it.
- **The pin tax is cheaper paid before the suite than after.** `inert_surface
  staged` returned rc=1 (5 pins withdrawn — this cycle added a reader), so all
  report writes were done *ahead* of the stamp instead of after it. Last cycle
  paid for the other order twice.

## Recommended next 1–3 priorities

1. **Seed-ensemble the operating point** — `(0.8, 5)` is seed 0 alone, and D-019
   showed per-seed ESS spans ~5×. One cell surviving one seed is not a window.
2. **Re-take the other two scenes' ladders at their own calibrated windows** —
   D-266's disjoint-bracket conclusion rests on three uncalibrated curves.
3. **Record `calibration_weight:` in `lam_windows.yaml`** so `lam_window_key`
   can grade these lookups `ON_KEY`/`OFF_KEY` instead of `UNKEYED`.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67 open)
- Files touched: `eval/mppi_sandbox/calibrated_ladder.py`, `eval/mppi_sandbox/tests/test_calibrated_ladder.py`, `eval/mppi_sandbox/ess_at_peak.py`, `eval/mppi_sandbox/arm_audibility.py`, `docs/decisions.md`
- TSV row appended: pending
