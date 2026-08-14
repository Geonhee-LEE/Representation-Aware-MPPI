# The sampler was already collapsed before the arm was turned up

- **Cycle**: 2026-08-14 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `ess-at-the-peak` (STATE #1, authored in PLAN step 4)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's #1: `cafe_freezing_v0` rises monotonically to ratio `3.2644` at
  `w_voo = 200` with no ratio collapse (D-266), so it should be the one scene
  that separates D-027's **ESS/softmax** ceiling from D-265's **ratio**
  collapse — the reference scene cannot, because its ratio dies at `200` for an
  unrelated denominator reason.
- Shipped `eval/mppi_sandbox/ess_at_peak.py`: reads ESS off `ab.run_arm` in
  D-266's exact isolation (`risk_mppi`, seed 0, `w_epist=0`, `w_risk=0`,
  `k_margin=0`) and **pairs** each rung with D-266's recorded ratio, so a rung
  carries both numbers or neither. The bar (`AUDIBLE_RATIO`) is imported from
  `arm_audibility`, never restated (D-047).
- Walked the five-rung ladder — five closed-loop runs — and pinned the result
  as `MEASURED_ESS`. 16 new tests.

## What worked / what failed

- **The premise was refuted, and not in the direction the question assumed.**
  Median ESS is `1.0000` at `w ∈ {20, 50, 200}`, `1.0053` at `5`, `1.8749` at
  `1`, against a `K = 256` band of `(12.8, 128.0)`. The softmax is weighting
  **one rollout at every rung** — including `w = 1`, where the attract channel
  is inaudible (`ratio 0.0581`) and the arm is doing almost nothing.
- **So this is not D-027's ceiling**, and my first verdict vocabulary would
  have said it was. `ESS_COLLAPSED` claims a weight pushed the sampler out of
  its band, which requires an in-band rung to have been pushed *from*; there is
  none. Added `ESS_DEGENERATE_THROUGHOUT` plus `can_address_d027_ceiling`
  before recording, so the ladder reports that it cannot address D-027 rather
  than borrowing its name.
- **The direction of the one non-degenerate rung is the argument.** ESS is
  *highest* where the arm is quietest (`1.87` at `w=1`) and falls to exactly
  `1.0` as weight rises. If the arm drove the collapse, `w=1` would start in
  band; it starts 6.8x below the floor.
- All five runs still `reached_goal` — a degenerate sampler that arrives, so
  this is a measurement, not a crash.

## North-star delta

- **Negative but load-bearing**: D-266's separating scene is disqualified as an
  operating point. `cafe_freezing_v0`'s monotone rise to `3.2644` — the whole
  reason it was picked — was measured on runs whose planner followed a single
  rollout. The ratio arithmetic survives (leave-one-out on the cost field), but
  the trajectory those costs were evaluated along is not a planned one.
- No closed-loop safety metric moved. This removes a candidate rather than
  adding capability.

## Key learnings

- **A ladder's baseline rung is a control and I nearly did not read it.** The
  question was about the top rung; the finding is entirely in the bottom one.
  Had I swept only the audible rungs the answer would have looked exactly like
  D-027's ceiling and been wrong.
- **`lam` was never calibrated for this scene on this ladder.** `calibrate_lam`
  exists and D-266's sweep did not call it — that is the next measurement, and
  it is upstream of every `w_voo` number this branch has taken on `freezing`.
- Two collapses that produce the same symptom need two names before the
  measurement lands, not after — the vocabulary was the part that took thought.

## Recommended next 1–3 priorities

1. **`freezing-lam-calibration`** — run `calibrate_lam` on `cafe_freezing_v0`
   and re-take D-266's ratio ladder at the calibrated temperature. Decides
   whether `SCENE_CURVES["cafe_freezing_v0"]` is quotable at all.
2. **Re-check the other two scenes' ESS** — `cafe_obstacle_crossing_v0` and
   `cafe_cut_in_v0` ladders were taken in the same uncalibrated isolation, so
   D-266's disjoint-bracket finding may rest on the same defect.
3. Merge **PR #68** (unchanged, user-blocked) — still the sole route to Q-148.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/mppi_sandbox/ess_at_peak.py`,
  `eval/mppi_sandbox/tests/test_ess_at_peak.py`, `docs/decisions.md`
- TSV row appended: pending
