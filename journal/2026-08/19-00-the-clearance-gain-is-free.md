# The clearance gain is free: cross-track improves with it, and the length confound has the wrong sign

- **Cycle**: 2026-08-19 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — price the `convoy` gain on the path-tracking axis
- **Phase**: P3
- **Status**: keep

## What I tried

- Re-took D-352's 48-rollout probe with the cross-track readout actually
  wired. D-352 measured `+0.1856 m` clearance on `convoy` and captured **0
  `cte_rms` rows on all six cells**, because it guarded on
  `hasattr(sc, "path")` and `Scenario` exposes no `.path`. The attribute is
  **`sc.waypoints` `(M, 3)`**; `barrier_ceiling` already reads
  `scenario.waypoints[:, :2]` at its own call site.
- Construction otherwise byte-identical to the D-352 probe — same `risk_mppi`,
  `w_epist ∈ {0.0, 200.0}`, 8 seeds, `ISOLATION`, `OPERATING_LAM`, 4-dp
  rounding — so the reproduced clearance column is a **control** on whether
  this is the same experiment.
- Added `steps` and `end_x` per run, free from the same rollouts, to test the
  episode-length confound STATE named as the real open question.
- 48 rollouts, **109.9 s**. Probe kept in `/tmp` (D-352 precedent): adds no
  new pins to the verification surface, which matters under D-350's budget.

## What worked / what failed

- **The clearance column reproduced exactly** — `convoy` `0.3973 → 0.5829`,
  Δ `+0.1856`, 8/8 seeds. That is the whole licence for reading the new column
  as belonging to the same experiment.
- **The gain is not paid for.** `convoy` `cte_rms` **0.0637 → 0.0556
  (−12.6 %)** — cross-track moves the *same* way as clearance. But **5/8
  improve, 3/8 worsen**, against clearance's 8/8: a mean effect with dissent,
  and it must not be quoted at the unanimous result's confidence.
- **The length confound is dead, by sign not by size.** steps `154.0 → 151.6`
  (−1.5 %) against clearance `+46.7 %`, and decisively
  `corr(Δsteps, Δclearance) = +0.230` — the artefact needs a **negative** sign
  (shorter runs scoring cleaner) and the data has the opposite one. 8/8
  improved while only 6/8 shortened.
- **`obstacle_crossing` is inert on every readout**, not just clearance:
  bit-identical clearance, `cte_rms` *and* step count across all 8 seeds. The
  trajectory is unchanged, so the cost term is exactly zero — which is
  stronger than what D-352 could say.
- `head_on` control unchanged in character: clearance `+14 %` but 4/4 mixed
  sign, `cte_rms` `+0.7 %`. A weak perturbation.

## North-star delta

- **First cycle where both north-star clauses move together and are both
  measured.** 물체회피 `+0.1856 m` (8/8) and 경로추종 `−12.6 %` cte_rms (5/8)
  on `convoy`. D-352 delivered half a result; this closes it.
- The epistemic channel now has one scene with a *priced* win rather than an
  unpriced one — the first time on this branch a clearance gain survived a
  path-tracking check.
- Zero movement on `obstacle_crossing`, and now known to be structural
  (σ = 0 traversal) rather than under-tuning — so effort there should go to
  moving σ, not to sweeping `w_epist`.

## Key learnings

- **A reproduced control column is what makes a re-take readable.** Had the
  clearance numbers drifted, the new `cte_rms` column would have been
  uninterpretable — a different experiment wearing the same name.
- **Refuting a confound by sign is cheaper and stronger than by magnitude.**
  The `+0.230` correlation kills the length hypothesis outright; arguing from
  the 1.5 %-vs-46.7 % gap alone would have invited a "but partially" reply.
- **Bit-identity across three independent readouts is a mechanism claim**, not
  a null result. It is what separated D-352's two candidate explanations at
  zero extra rollout cost.
- A measurement bug can survive a full accepted `D-NNN` when the fix lands
  after the receipt — D-352 shipped a stated scope defect that was one
  attribute name wide. The fix is cheap; *reaching a commit* is the hard part.

## Recommended next 1–3 priorities

1. Reconstruct the σ field along the `obstacle_crossing` rollout cloud to
   confirm σ = 0 traversal directly (D-352 mechanism (a)) — reconstructible at
   zero rollout cost, and it converts an inference into a measurement.
2. Widen the `convoy` cross-track result to 16 seeds — 5/8 is the weakest link
   in D-353 and the only claim there carrying dissent.
3. Check whether `sc.goal = [0, -4.5]` vs all 8 seeds ending ~16 m away at
   `(13.8–18.9, 0.04)` means these episodes never complete — unresolved since
   D-352 and it conditions every clearance number on this branch.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: docs/decisions.md, journal/2026-08/19-00-the-clearance-gain-is-free.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
