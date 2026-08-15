# The narrowing was a turning point

- **Cycle**: 2026-08-15 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `walk-lam-1.2-ceiling` Third rung for the narrowing ceiling gap
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's first priority, and the cheapest decisive thing on the board: D-284
  left D-027's ceiling gap falling `16.33x → 11.96x` toward a `10.0x` band and
  explicitly declined to project where it closes. Only a third rung can say
  whether it closes or asymptotes — so I took one.
- Walked `lam = 1.2` at `w_voo ∈ {5, 20}` — the **bracketing pair only**, not
  the full five-rung ladder — on `cafe_freezing_v0`, seed 0, in the same
  `ess_at_peak.ISOLATION` as D-266/D-268/D-284. 2 closed-loop runs + 2
  leave-one-out cost-field reads, **6.4 s**.
- Landed `MEASURED_LAM12` / `MEASURED_ALL_LAMS` (concatenations, never retyped)
  and `gap_trend()`, with the verdict vocabulary fixed before the counts were
  read, plus 6 tests.

## What worked / what failed

- **The gap does not close — it turns.** `16.33x` (`lam 0.8`) → `11.96x`
  (`1.0`) → **`37.76x`** (`1.2`), against a band `10.0x` wide. The third rung
  is wider than *either* of the first two, so this is a reversal and not a
  re-reading of noise. `GAP_NON_MONOTONE`.
- **D-284's "direction of travel is toward the window" was a two-point
  artifact, and it was hedged correctly.** That cycle set `extrapolates=False`
  and refused to name a closing temperature. Had it projected, it would have
  been wrong — this is the first time on this branch that the no-extrapolation
  discipline has been *paid off* rather than merely observed.
- **The answer to the question D-284 left open is no.** `any_lam_fits_band` is
  `False`: the minimum gap over every walked rung is `11.96x` at `lam = 1.0`,
  still above `10.0x`. No walked temperature holds both sides of the ceiling in
  band at once, and the direction no longer promises a later one.
- **A second bound showed up unlooked-for, on the repair axis itself.** The
  band has a *top* (`128.0` at `K = 256`). At `lam = 1.2` the in-band side sits
  at `88.59`, leaving `1.44x` of headroom — having just been lifted `2.82x` by
  the step that got there. The next comparable temperature step pushes `w = 5`
  out of the band from **above**. So temperature is nearly spent as a knob here
  for a reason that has nothing to do with `w_voo`.
- **The per-rung lifts do not merely differ, they oppose.** `0.8 → 1.0` lifted
  `w=5` by `1.006x` and `w=20` by `1.374x`; `1.0 → 1.2` lifted `w=5` by
  `2.820x` and moved `w=20` by `0.893x` — *down*. `ceiling_gap`'s common-factor
  premise is not just violated in magnitude, it is violated in sign.
- **No pin tax this cycle.** `loop_reach` found no new population claims in the
  new tests (census unchanged: the same 2 targets), and `guard_reflexivity`
  passed. The three preceding cycles each paid a re-pin.

## North-star delta

- **The temperature axis is now bounded from both ends on this scene**, by
  measurement: raising `lam` does not widen the usable `w_voo` region (D-284),
  does not close the ceiling gap (this cycle), and runs out of band from above
  within `1.44x`. The one-rung-wide operating region `{w = 5}` is unchanged at
  all three temperatures.
- No obstacle, clearance or near-miss number moved. Still one scene, still
  `transfers_to_ab_scene = False`.

## Key learnings

- **Two points are a segment, not a direction.** D-283 wrote `extrapolates` as
  a discipline and D-284 applied it to a narrowing that looked like it was
  going somewhere. The third rung says it was a minimum. The rule earned its
  keep here.
- **A stale interpretation retires as silently as a caveat.** The existing
  two-point test still passes — it was never wrong about the two temperatures
  it names — but its docstring said "direction of travel is toward the window".
  That is now false, so it is corrected in place rather than left for a future
  reader to re-derive (D-047).
- **Check the band's far edge, not just the one you are falling through.**
  Every prior cycle on this axis read the band as a floor to stay above. It is
  a window, and the in-band rung is now closer to the top of it than to the
  next temperature step.

## Recommended next 1–3 priorities

- **Stop walking temperature on this axis.** Three rungs say it does not widen
  the region, does not close the gap, and is nearly out of band. The remaining
  lever on a one-rung-wide operating region is the cost field's *shape*, not
  its scale — e.g. re-taking the ceiling under a different `w_voo` rung
  spacing between `5` and `20`, where the crossing actually lives.
- **`<reprobe-stale-pins>`** — seventh consecutive cycle carrying this; it
  again forced an all-writes-before-suite ordering this cycle.
- **PR #68 merge** (user) — thirteenth consecutive cycle blocked on Q-148's A/B
  scene.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py
- TSV row appended: yes
