# Cruise-driven nominal: the screen's driver becomes an input the loop reads

- **Cycle**: 2026-08-03 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-derive `nominal_traversal` from `v_max` and `w_terminal / w_speed`
- **Phase**: P3
- **Status**: keep

## What I tried

- Took D-024's finding at face value: if `target_speed_mps` is not an input to
  the closed loop, then D-023's timing band is an error bar drawn around a
  declaration, and the repair is to drive the screen off something the loop
  actually reads.
- Added `speed_mps=` to `nominal_traversal` (default `None` → bit-identical)
  plus `cruise_traversal`, driven by `CRUISE_SPEED_MPS`, a **controller**
  constant calibrated once against `v_max` — not a per-scene measurement, so
  the screen stays simulation-free.
- Measured the resulting duration-ratio band on the same four reportable
  obstacle-carrying scenes D-023 used, against the declared-driver band.
- Swept the driving constant to find out how much of the band the choice of
  constant was responsible for.

## What worked / what failed

- ✅ **The swap works and it is free.** Band width **3.866× → 2.320×** (1.67×
  tighter) at identical zero simulation cost. The error also becomes
  **one-directional** — all 4 scenes read > 1, because the closed loop always
  pays an accel transient, a goal ramp and a detour against a pure-cruise walk.
  The declared band straddled 1.0, so its error had no sign to reason about.
- ✅ **Cruise really is a controller property, not a scene one.** Sweeping
  `v_max`: 0.6 → 0.600 (the limit binds exactly), 0.8 → 0.723 and 1.2 → 0.723
  (the weight ratio pins it, agreeing to the digit across a 1.5× change in the
  limit). That knee is what licenses calibrating once instead of per scene.
- 🔴 **The headline number is a floor, not a score.** Band width under *any*
  scene-independent driver is **exactly scale-invariant** in the driving speed:
  `ratio_i = cl_i · c / length_i`, so `c` cancels out of `max/min`
  algebraically. Verified to 1e-9 at c = 0.5 / 0.709 / 0.8 / 1.2. So 2.320× is
  a property of the scene set; tuning `CRUISE_SPEED_MPS` to narrow it is
  **guaranteed to fail**.
- 🔴 **Beating the floor costs a simulation.** Per-scene measured cruise reaches
  **1.663×** — which is precisely Q-044 option (a), the one D-023 rejected for
  ceasing to be a screen. Recorded with the price tag attached, not adopted.
- ⚠️ **Two more scenes look defective on the cruise statistic.** In the 8-scene
  scan `city_figure8_v0` cruises at **0.016 m/s** (3/4 reached) and
  `cafe_cut_in_v0` at 0.022 (0/4) — the latter is the known Q-037 defect, the
  former is new and was not visible in `mean_speed`.

## North-star delta

- **No capability movement — ninth consecutive methodology cycle.** Scenes able
  to contribute an avoidance number: **5**, reportable: **4** — unchanged.
- The cheapest screen in the repo got 1.67× more precise for free, and the
  remaining imprecision is now **bounded and explained** rather than open.
- One future line of work is closed off with a proof rather than a guess: no
  constant-speed timing model can do better than 2.320×.

## Key learnings

- **When you replace a driver, sweep it — the sweep tells you whether you
  bought precision or just moved the number.** Here the sweep showed the
  constant sets *where* the band sits and never *how wide* it is. Without it I
  would have shipped 2.320× as this constant's achievement and invited the next
  cycle to tune it.
- **An error with a sign is worth more than a smaller error without one.** The
  one-directional result is arguably the more useful half: a systematic bias
  can be reasoned about and eventually modelled; a two-directional one can only
  be widened around.
- **A refuted closed form does not have to be replaced by another closed form.**
  D-024 killed `analytic_cruise_speed`; the right successor at ESS ≈ 1.5 is a
  measured lookup that refuses to extrapolate, not a better derivation.
- **Changing the statistic re-screens the scenes.** `cruise_speed` surfaced a
  second near-stalling scene (`city_figure8_v0`) that `mean_speed` averaged away
  — the same class of defect Q-037 cost three results before it was caught.

## Recommended next 1–3 priorities

1. **Triage `city_figure8_v0`'s 0.016 m/s cruise** — is it a third scene defect
   (Q-037's class) or a genuine controller failure on a self-intersecting path?
   Bundle the verdict with the `cafe_cut_in_v0` fix-or-retire decision.
2. **Adopt `cruise_traversal` as `exposure_band`'s default driver** and
   re-derive D-018's contested fractions under it — the band is narrower now,
   so some of the 9 refused pairs may become orderable. Belongs on the
   re-baseline branch, not before the drain.
3. **Re-run the audible/deaf partition through `reach_on_trajectory`** — still
   unblocked, and `reach.py:176` still warm-starts its fan at `target_speed`,
   which D-024/D-025 now say is the wrong speed.

## Artifacts

- PR: #67 (already open — no new review bandwidth consumed)
- Files touched: `eval/mppi_sandbox/exposure.py`, `eval/mppi_sandbox/speed_audit.py`, `eval/mppi_sandbox/tests/test_cruise_driven_nominal.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- Suite: 273 → **285 passed** + 1 xfailed (230.9 s → 250.8 s)
- TSV row appended: yes
