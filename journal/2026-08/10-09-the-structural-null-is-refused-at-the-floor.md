# The structural null walks, reproduces 95% of the gain, and is refused — at the floor, not the ceiling

- **Cycle**: 2026-08-10 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE #1` 8-seed ESS pre-read of `frozen_risk_mppi`, then the 32-seed head-to-head
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Spent Q-123's gating measurement: 8 seeds of `frozen_risk_mppi` at
  `cafe_convoy_v0`, `w_obs_soft = 75`, λ = 0.8. It came back **in band** —
  median ESS **108.61** against the risk arm's 105.07 on the same ensemble,
  8/8 in band, 8/8 at goal — so the cheap read did not refute, and STATE's
  in-band branch fired.
- Walked the 32-seed head-to-head immediately (the risk/stock arms are already
  on disk, so the rung cost one walk of 32 runs, ~80 s).
- Recorded both as constants and shipped `StructuralRung` — shaped after
  `geometric_null.NullRung` and **short one field**, because there is no
  `w_geom`. Per-seed ESS is carried alongside per-seed clearance so the rung
  can be asked *which* seeds refused and on which side of the band.
- 12 new tests, including the reachability probes for the three head-to-head
  verdicts (no shipped witness — the one walked rung is refused).

## What worked / what failed

- 🔴 **The rung is refused: 31/32 in band.** All-seeds, not most-seeds — the
  same rule, at the same count, that refused head_on `w = 75`. And per
  `LOUDNESS_UNCALIBRATABLE` there is **no knob**: the construction's whole
  claim is that no coefficient exists, so the refusal cannot be answered by
  re-calibrating anything. Q-123 resolves in exactly the direction it feared.
- 🔴 **But not by the mechanism it named, and that is the finding.**
  `frozen_risk_mppi`'s docstring argues the frozen arm must be *flatter* — a
  max over `predict_samples` blobs covers more cells at value ≥ any single
  sample's, so the frozen cost is pointwise ≤ the swept one, softmax flatter,
  ESS higher — which refuses at the **ceiling**. Measured, the single
  offending seed is at ESS **11.78** against a floor of **12.8**: too
  *peaked*. A pointwise-smaller cost is not a less-spread one, and ESS reads
  the spread. `price_direction` reads `PRICE_PAID_OTHER_SIDE`, pinned, with the
  predicted side kept as its own constant so prediction and measurement are two
  objects that can disagree.
- 🔴 **The refused reading is the strongest evidence yet against the
  representation.** `residual_share = 0.9539` — the frozen arm reproduces
  **95%** of the mechanism's clearance gain, against the geometric null's
  0.7725 — and the head-to-head is `A = 0.5317`, paired CI
  `[-0.0117, +0.0267]` ∋ 0, `EQUIVALENT` at ε = 0.05 m with an equivalence
  margin of **0.0267 m**. Kept as data and never as a verdict (`LOUDER_NULL`'s
  rule): `verdict()` returns `WALK_INADMISSIBLE` and a test asserts it still
  does while reading the share.
- 🟢 **The null is not inert**, so the small residual is not the uninteresting
  kind: frozen-vs-stock is `A = 0.9951`, Δ **+0.1412 m** against the
  mechanism's **+0.1480 m**. Two arms that both do nothing also have a small
  residual; these both do nearly everything.
- 🟢 **The re-run of `risk_mppi` at 8 seeds reproduced
  `CONVOY_W75_CLEARANCES["risk_mppi"][:8]` exactly**, so this cycle's runs and
  the recorded walk sit on one footing rather than being asserted to.
- 🟡 **The 8-seed licence bit a third time, in D-163's direction** — 8/8 in
  band, 31/32 on the walk. Recorded as a *reading* (`seed_licence` →
  `LICENCE_PERMISSIVE`) rather than as prose, because the branch has now
  re-learned this by surprise three times (crossing's `WINDOW_SHIFTED`,
  `geometric_null`'s `w_geom = 5.0`, this).
- 🟡 `loop_reach` charged the new pairing test as an unregistered
  population claim and the reading was re-taken rather than the test reshaped.

## North-star delta

- **No movement, and this cycle argues the branch's remaining attribution claim
  is weaker than the last one left it.** Headline unchanged: `unsafe_rate`
  **0.0000** / `min_clearance` **0.3579** / `success_rate` **1.0000**. No
  controller or representation code changed — `FrozenRiskMPPI` shipped last
  cycle; this one only measured it.
- Attribution census coverage is **still 0/6**: this rung is refused, so it
  does not enter it. What it adds is a *second* refused rung whose refused
  number points the same way as the first (0.9539 here, 0.9130 at
  `geometric_null`'s `LOUDER_NULL`).

## Key learnings

- **A pointwise inequality on cost does not transport to the softmax.** The
  construction's cost argument is correct and its ESS conclusion does not
  follow — ESS is a functional of the cost *spread across rollouts*, and a
  uniformly smaller cost can be more sharply spread. Any future "this arm will
  be quieter" claim on this branch needs the spread measured, not the level.
- **Naming a price does not price it correctly.** The docstring predicted the
  bill and got the reason wrong; separating `PRICE_PAID_AS_PREDICTED` from
  `PRICE_PAID_OTHER_SIDE` matters because only the first would license reusing
  the argument on the next arm.
- **Three nulls, three refusals, one direction.** ESS-matched geometry (0.7725,
  admissible), louder geometry (0.9130, refused), frozen prediction (0.9539,
  refused). The admissible one is the only one that leaves room for the
  representation, and it is the quietest null of the three. That ordering is
  itself a hypothesis worth testing directly.

## Recommended next 1–3 priorities

1. **Ask whether the refusals are correlated with the residual** — three nulls
   ordered by loudness give residuals ordered the same way, and if quieter
   nulls are systematically both admissible and more favourable to the
   representation, then admissibility is selecting the answer. Cheap: all three
   rungs are on disk.
2. **Re-walk the frozen rung on a second scene** (`cafe_head_on_v0` `w = 75`)
   — one refused rung is not a result, and the frozen arm needs no calibration
   run, so a second scene costs one 32-seed walk.
3. **Make `sandbox:pass=N` state which quantity it is** — `passed` vs
   `executed`; carried eleven cycles.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/structural_null.py, eval/mppi_sandbox/tests/test_structural_null.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md, docs/deliberations.md, journal/2026-08/10-09-the-structural-null-is-refused-at-the-floor.md
- TSV row appended: pending
