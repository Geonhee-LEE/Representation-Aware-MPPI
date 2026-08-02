# Q-041 refuted — and the separation verdict turns out to be a function of the seed count

- **Cycle**: 2026-08-02 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-item-1` Close the Q-040 2×2 within a single parent
- **Phase**: P3
- **Status**: keep

## What I tried

- Completed the (staggered timing) × (counter-flow actors) 2×2 **inside one parent**
  instead of across two, adding `cafe_obstacle_crossing_noflow_v0` (stagger ✓, flow ✗)
  and `cafe_obstacle_crossing_sync_noflow_v0` (✗, ✗). Robot, path, `target_speed_mps`,
  lanes, actor speeds and the acceptance block are byte-identical to the parent.
- Registered both predictions (**shared**, and `sync_noflow` landing on `sync`'s
  `[1.6, 3.2]`) in the yaml headers and **committed them before paying for any run**
  (D-018 (b)).
- Calibrated all four variant scenes × 2 controllers (8 cells, 8 rungs, 8 seeds).
- Adversarially probed my own new positive: three extra rungs in the gap between the
  two adjacent rungs the decisive cell landed on.

## What worked / what failed

- 🔴 **Prediction refuted.** `..._noflow_v0` keeps the stagger, drops the counter-flow,
  and its arms are **still disjoint** (`stock` [3.2] vs `risk` [1.6]). Within one parent
  both staggered cells are `per_arm` and both synchronised cells are `shared`,
  **regardless of direction** — a plain main effect of timing, no interaction.
- ✅ **20:00's "interaction" was a parent artifact**, exactly the alternative its header
  named. `cafe_convoy_staggered_v0` and `cafe_obstacle_crossing_noflow_v0` sit at
  *identical* factor levels and disagree (`shared` vs `per_arm`).
- ✅ **The direction flip is exposure-neutral by construction** — reversing an actor maps
  `x(t) → −x(t)` with the robot on `x = 0`, so the clearance matrix is bit-identical
  (`max|diff| = 0.0`). The 2×2's two factors are therefore orthogonal, one moving
  exposure and one provably not.
- 🔴 **…yet direction still moved the windows** (`sync` shares {1.6, 3.2}, `sync_noflow`
  only {3.2}). So `exposure.py` is **provably incomplete** as a screen, not merely
  unlucky on Q-040. The second registered prediction was wrong too.
- 🔴 **The finding that outranks the whole 2×2**: `admissible` requires *every* seed in
  band, so a window is a **conjunction over seeds** and can only shrink as `n` grows.
  The parent scene reads **`shared` at n = 4 and `per_arm` at n = 8** — `stock_mppi`
  holds `lam = 1.6` on four seeds, loses it on eight, and 1.6 is the rung `risk_mppi`
  keeps at both counts. No geometry changed.
- ✅ The refinement held: three extra rungs between 1.6 and 3.2 left the arms disjoint at
  n = 8 (`stock` admits 2.26, `risk` admits 2.6, no shared rung). So the noflow verdict
  is not a ladder-density artifact — it is the **seed count** that moves it.

## North-star delta

- **No capability movement.** Measurement methodology again — but this cycle retired the
  *question*, not just an answer: Q-040 and Q-041 both asked which **scene property**
  predicts separation, and separation is not a scene property.
- Two prior headlines now need a qualifier: 18:00's "the only `per_arm` cell in the
  matrix" and D-017's disjoint-window protocol both read "at n = 8".
- Scenes able to contribute an avoidance number: **5**, reportable: **4** — unchanged.

## Key learnings

- **A criterion that is a conjunction over samples is a moving target.** "Every seed must
  pass" looks like a quality bar and behaves like a monotone function of sample size.
  Any pair of arms separates eventually if you draw enough seeds — the verdict encodes
  the budget as much as the physics.
- **Registering a prediction is worth most when it is wrong.** Both registered predictions
  failed, and because they were committed first, "still disjoint" read as a refutation
  instead of a number to reinterpret. This is the second consecutive cycle where D-018's
  protocol converted a would-be confirmation into a real result.
- **Naming a confound in the artifact makes the follow-up one experiment instead of a
  search.** 20:00 wrote "the off-diagonal cells come from different parents" into the
  test docstring; that sentence is the entire reason this cycle was 2 yaml files.
- **An orthogonal-by-construction factor is the cheapest thing to add to a design.** The
  direction flip cost nothing in exposure terms and is what proved the screen incomplete.

## Recommended next 1–3 priorities

1. **Q-042 — recompute the three admissibility criteria from existing probe data.** Check
   whether `ab.LamProbe` retains per-seed ESS; if so, all-seeds vs quantile vs bootstrap
   can be compared with **zero new runs**, on the re-baseline branch.
2. **Ablate `w_epist` on the crossing scene** (STATE #2) — still the only test of the
   *mechanism* rather than of a correlate, and now the only surviving lead after two
   scene-property hypotheses died.
3. **Re-baseline must stamp `n` on every verdict** it regenerates (STATE #6), per D-019.

## Artifacts

- PR: #67 (already in queue — this cycle added no new review bandwidth)
- Files touched: `eval/scenarios/variants/cafe_obstacle_crossing_noflow_v0.yaml`,
  `eval/scenarios/variants/cafe_obstacle_crossing_sync_noflow_v0.yaml`,
  `eval/scenarios/variants/lam_windows_variants.yaml`,
  `eval/mppi_sandbox/tests/test_lam_separation_interaction.py`,
  `eval/mppi_sandbox/tests/test_hazard_exposure.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- Suite: **181 → 193 passed + 1 xfailed**, 165.1 s → 169.8 s (11 of 12 new tests
  simulate nothing)
- TSV row appended: yes
