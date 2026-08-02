# The directional reach screen works — and it falsified the timing model it rides on

- **Cycle**: 2026-08-03 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (landed in place on PR #67 — 18th consecutive cycle, zero new review bandwidth)
- **TODO**: STATE claude-actionable **#1** — directional reach screen over all 8 scenes
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/reach.py`: from a pose, generate the MPPI rollout fan
  using the **same** `dynamics.step` plant, `MPPIParams` noise and warm-start
  `StockMPPI.__init__` installs; render σ with the **same** `GTBevProducer`;
  compute the per-sample cost vector `ShadowCostCritic` would, and report its
  **spread**. Spread, not intersection — D-021 established a constant cancels
  exactly in the softmax, so a cloud fully *inside* the shadow is as inaudible
  as one fully outside.
- Ran it over the 8-scene matrix at the shipped `H = 30`. 0.6 s, no simulation.
- Checked it against D-021's measured ground truth. **It disagreed** — 5/35 live
  on `cafe_obstacle_crossing_v0` where the closed loop measured 0/92.
- Localised the disagreement instead of tuning it away: re-ran the identical
  computation driven by the **measured** closed-loop states and times.

## What worked / what failed

- ✅ **The geometry model is exact.** Driven from the measured trajectory,
  `reach_on_trajectory` reproduces D-021 to the step: `live 0/92`,
  `max spread 0.00`, and the `H = 60` wake with it. Same code, both directions
  of D-018's intervention.
- 🔴 **The `nominal_traversal` timing model is falsified.** All the error is in
  the pose sequence. The closed loop finishes the crossing scene in **9.2 s
  against a 16.7 s nominal**, so the nominal robot is in the wrong place at
  every instant an actor casts a shadow. Across the matrix the closed-loop /
  nominal duration ratio spans **0.56× to 15×, in both directions**.
- 🔴 **This reaches past this module.** `exposure.py` is built on the same
  function, and D-018's headline comparison — crossing 74% vs convoy 43%
  contested fraction — is computed for those two scenes at **0.56× and 1.63×**,
  i.e. wrong in *opposite* directions, a ~2.9× relative skew between exactly
  the pair the statistic exists to separate. D-018 already refuted exposure as
  a predictor on a controlled intervention, so no live conclusion inverts; what
  weakens is the recorded finding that it survives as a cheap screen. Its own
  docstring names the standard it fails: *"the hazard is a rendezvous, not a
  place."*
- 🔴 **D-021's closing attribution is unsupported.** It blamed the crossing
  scene's short reach on `target_speed_mps: 0.3`. The controller does not track
  that setting — measured plan speed 0.36 m/s, realized traversal 0.54 m/s
  (~1.8×). The measured reach stands; only the explanation goes.
- ✅ **The directional claim is pinned by a constructed counterexample**, not by
  the aggregate: an obstacle *behind* the start pose casts a shadow well inside
  the fan's max reach — so the refuted scalar's inequality holds — while the
  spread is exactly 0, because no forward rollout point enters it.
- ✅ Shipped as two drivers over one core loop, differing only in the
  `poses`/`speeds` arrays, so "geometry exact, timing not" is a checkable
  statement rather than a hedge.

## North-star delta

- **No capability movement — sixth consecutive methodology cycle.** Honest
  reading: this cycle *subtracts* again. A screen that was asked for as a
  cheap pre-filter turned out to inherit a falsified timing model, and the
  scenes it calls audible (5 of 8) are **not yet citable**.
- What was gained is a validated **measurement** path (`reach_on_trajectory`
  reproduces the closed-loop verdict from scenario yaml + trajectory alone)
  and a named defect with a bounded blast radius (`nominal_traversal`, hence
  `exposure.py`).
- Scenes able to contribute an avoidance number: **5**, reportable: **4** —
  unchanged. No tracking metric improved.

## Key learnings

- **A screen that agrees with the measurement is not validated; a screen whose
  *disagreement* you can localise is.** The instinct on the 5/35-vs-0/92 gap
  was to tune the fan. Splitting the driver from the core loop showed the fan
  was already exact, and turned a discrepancy into a finding about a
  *different* module.
- **Two cycles have now found a knob doing something other than its name.**
  D-021: `target_speed_mps` silently gated a channel. Here: the controller does
  not even track it. Anything reasoning from a scenario yaml's declared speed
  should be assumed wrong until it is checked against a trajectory.
- **A derived quantity inherits its input's error budget, and nobody re-derives
  it.** `exposure.py` was reviewed as geometry and its timing was never
  questioned, because `nominal_traversal` reads like an obviously-correct
  helper. The check that caught it costs one `simulate` call per scene.
- **Spread, not intersection, is the right liveness criterion for any additive
  per-sample cost.** Generalises past `w_epist` to every critic on the
  additive path.

## Recommended next 1–3 priorities

1. **Decide what `exposure.py` should be driven by** — a realized-trajectory
   timing model (costs one sim per scene, kills its "millisecond screen"
   claim) or an explicitly-declared nominal with the error bar stated. Filed
   as the successor question to Q-043; the contested-fraction numbers in
   D-018's record should not be cited until this is answered.
2. **Explain why the controller overshoots `target_speed_mps` by 1.8× on the
   crossing scene** — `w_terminal = 30.0` against `w_speed = 2.0` is the
   leading suspect (the terminal goal-distance term rewards arriving sooner
   than `v_ref` allows). Cheap: a weight sweep on one scene, no new scenario.
3. **Re-run the audible/deaf partition through `reach_on_trajectory`** once (1)
   lands, so STATE #1's actual deliverable — which scenes can hear the
   epistemic channel — is answered on measured input rather than nominal.

## Artifacts

- PR: #67 (in place, existing queue entry)
- Files touched: `eval/mppi_sandbox/reach.py` (new), `eval/mppi_sandbox/tests/test_epistemic_reach_screen.py` (new), `docs/decisions.md` (D-022), `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
