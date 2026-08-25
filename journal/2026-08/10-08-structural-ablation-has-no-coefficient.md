# The structural ablation: no coefficient to calibrate, and a screen that says so

- **Cycle**: 2026-08-10 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — spec the structural ablation (controller variant dropping the representation's input)
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Shipped `FrozenBevProducer` — `GTBevProducer` with `predict_samples = 1`, so
  the DYNAMIC channel is the obstacle blob at `t₀` and nowhere else. Every other
  producer setting (grid, resolution, sensing range, occlusion, `blob_scale`)
  and every other channel is untouched. `predict_samples` is popped rather than
  accepted, so a later caller cannot restore prediction on a `Frozen*` object.
- Shipped `FrozenRiskMPPI` — `RiskMPPI` overriding **only** which producer is
  constructed. `w_risk = 40.0`, the three critics, the cost slot and
  `_extra_cost` are all inherited verbatim, so the two arms cannot drift apart
  in the consuming path. Registered as `frozen_risk_mppi`.
- Shipped `structural_null.screen` — the 0-sim-run check that the "no
  coefficient to calibrate" claim is true of the *objects*, not just of the
  docstring. Two halves: `coefficient_parity` (every `MPPIParams` field
  including λ, plus the arm-level weights) and `prediction_parity` (producers
  differ in `n_pred` and in nothing else).
- 15 tests in `tests/test_structural_null.py`.

## What worked / what failed

- The shipped pair screens `STRUCTURAL_ABLATION`: `COEFFICIENTS_SHARED` +
  `PREDICTION_REMOVED`. So D-170's under-identification and D-171's circularity
  are not merely unobserved here — there is no ladder for either defect to live
  on, and that is now a reading rather than an argument.
- **The conjunction is load-bearing and the test proves it.** Parity alone is
  satisfied perfectly by comparing `risk_mppi` to *itself*
  (`test_parity_alone_is_not_the_screen` → `PREDICTION_PRESENT`), so a
  parity-only screen would certify a no-op as an ablation. Conversely nudging
  `w_risk` to 25.0 flips it to `COEFFICIENTS_DIVERGED` — which is exactly the
  path by which a future cycle "fixing" an ESS refusal would silently create a
  third calibrated null.
- **The cost is real and is asserted, not assumed**: swept DYNAMIC is a max over
  `predict_samples` blobs and frozen is one member of that max, so at equal
  `w_risk` the frozen arm's extra cost is pointwise ≤ the risk arm's
  (`test_frozen_arm_is_no_louder_than_the_risk_arm`). Its softmax is therefore
  flatter and `ab.ess_band` may refuse a rung **with no knob to fix it**.
- **The `default_lam_sites` census caught the first draft doing exactly what
  its own docstring warned about**, and then its headline claim flipped. The
  draft factored the operating point into a `params()` helper; `_classify`
  needs a *literal* `MPPIParams(...)` at the call site, so that billed
  `forwards` 23 → 43 while naming nothing. Inlining all 20 sites moved them to
  `decides` (55 → 76) with `defaults` and `forwards` unmoved — a decides-only
  bill. But 76 > 58 means `test_the_default_is_the_majority_choice_not_a_fallback`
  is now **false**: for eighteen cycles more sites took the shipped `lam = 0.1`
  than named a rung, and as of this file more name one. Renamed rather than
  inverted in place, with the margin (18) pinned, because a silent `<` would
  make eighteen cycles of history read as though nothing had happened.
  `migration_cost` is unmoved at 58 — the flip changed the denominator's
  composition, not the cost of making `lam` required.
- Two producer tests initially passed/failed for the wrong reason — the
  viewpoint put the probes inside the obstacle's own occlusion shadow, so the
  reading was about `_occlusion` rather than about prediction. Fixed by moving
  the viewpoint lateral to the line of sight. Worth recording: on this producer
  a "DYNAMIC channel" assertion is one occlusion-geometry mistake away from
  measuring a different channel's semantics.

## North-star delta

- No movement in the measured numbers: coverage stays **0/6**, `NO_GRADED_RUNG`,
  and no rung has been walked with this arm. The screen says the comparison is
  *well-posed*, not who wins.
- What did move is the branch's ability to spend: three cycles of calibration
  criteria produced no gradable rung, and this construction removes the
  calibration question rather than answering it a third time — for 0 sim runs.

## Key learnings

- **D-171's rule generalises one step further than it was written.** That cycle
  said: screen a match quantity for coupling to the verdict before walking a
  ladder in it. Where there is no match quantity, the thing to screen before
  walking is that the sentence "there is no match quantity" is true of the
  objects. Same price (0 runs), same failure it prevents.
- **A one-sided screen certifies the wrong thing.** "All coefficients equal" is
  maximally satisfied by an arm compared to itself. Any future ablation check on
  this branch needs both a sameness half and a difference half.
- **A pin is not redundant with the docstring that explains it.** The
  `params()`-helper trap was already written down, in the very test that
  charges for it, and this cycle's first draft walked into it anyway. The pin
  is what makes the warning get read.
- **Trading failure modes is not eliminating them.** This arm cannot be
  mis-calibrated because it cannot be calibrated; the same fact means an ESS
  refusal has no remedy. That trade is named (`LOUDNESS_UNCALIBRATABLE`) so a
  later cycle reads a refusal as a fact about the ablation rather than as an
  invitation to turn `w_risk` down.

## Recommended next 1–3 priorities

1. **8-seed ESS pre-read of the frozen arm** at `cafe_convoy_v0`,
   `w_obs_soft = 75`, λ = 0.8 — cheap, and per D-163 the 8-seed licence is the
   *permissive* one, so a band miss at 8 seeds is already decisive against 32.
   This is Q-123's gating measurement.
2. **Walk the rung** if the pre-read is in band: `frozen_risk_mppi` vs the
   recorded `risk_mppi` / `stock_mppi` arms at 32 seeds, head-to-head paired.
   Two thirds of the comparison is already on disk.
3. **Make `sandbox:pass=N` state which quantity it is** — `passed` vs `executed`
   (`passed + xfailed`). Carried ten cycles now.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/representations/frozen_bev.py, eval/mppi_sandbox/representations/__init__.py, eval/mppi_sandbox/controllers/frozen_risk_mppi.py, eval/mppi_sandbox/controllers/__init__.py, eval/mppi_sandbox/structural_null.py, eval/mppi_sandbox/tests/test_structural_null.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes
