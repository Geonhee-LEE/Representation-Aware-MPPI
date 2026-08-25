# σ is exactly zero on the cloud — and bit-identity never implied that

- **Cycle**: 2026-08-19 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — reconstruct the σ field along the `obstacle_crossing` rollout cloud
- **Phase**: P3
- **Status**: keep

## What I tried

- Hooked `ShadowCostCritic.cost` to record, at **every planning step of every
  closed-loop run**, the epistemic field σ sampled at the rollout cloud points
  the critic itself scores — the same `bev.sample(EPISTEMIC, xy_flat)` call,
  not a re-derivation on a separate grid.
- 16 runs (2 scenes × 8 seeds) at `w_epist = 200`, `ISOLATION`,
  `OPERATING_LAM`. **~90 s**, zero new rollouts beyond the runs themselves.
- Recorded **two** columns, not one, because the inference being tested is
  under-determined (below): σ occupancy on the cloud, and the **across-rollout
  spread** of the per-rollout shadow cost `w_epist·Σσ`.
- Probe kept in `/tmp` (D-352/D-353 precedent) — adds no pins to the
  verification surface.

## What worked / what failed

- **σ ≡ 0 on `obstacle_crossing`. Exactly, not approximately.** `0` nonzero
  samples out of **6,604,800** cloud points across 8 seeds
  (`sigma_max = 0.0` on every seed). D-353's mechanism (a) is now a
  measurement, not an inference — the cost term is identically zero, so no
  `w_epist` can act on this scene at any magnitude.
- **The inference it replaces was under-determined, and that is the real
  finding.** MPPI's softmax is invariant to a constant added to every
  rollout's cost, so bit-identical trajectories admit **two** worlds:
  (a) σ = 0 on the cloud, and (a′) σ > 0 but **constant across rollouts**, so
  the signal exists and the softmax cannot see it. D-352/D-353 read
  bit-identity as (a) directly; it does not licence that. The spread column
  settles it — `steps_with_spread = 0 / 107.5` — so this scene is (a) proper.
  Had it been (a′) the prescription would have been the opposite one: not
  "move σ" but "stop summing σ over the horizon".
- **The instrument is not blind** — `convoy` reads σ > 0 on 0.102 % of cloud
  points with across-rollout spread on **20.8 of 661.5** planning steps.
- **But the `convoy` control column did NOT reproduce**, and that bounds this
  cycle's claim. Step count **661.5 here vs D-353's 151.6**, clearance
  **0.606 vs 0.5829**. Applying D-353's own lesson in the negative: without a
  reproduced control, **no `convoy` magnitude here may be quoted against
  D-353** — it serves only as evidence that the hook reads nonzero where the
  channel is known to act. The configuration gap is unexplained and is the
  first thing the next cycle should close.

## North-star delta

- 물체회피: no new movement this cycle. What moved is the **cost of future
  movement** — effort on `obstacle_crossing` should go to the sensing/occlusion
  geometry that would make σ nonzero there, and *not* to sweeping `w_epist`,
  which is now measured as exactly inert rather than assumed to be.
- One scene class is now known to be outside the epistemic channel's reach by
  construction, which is a scoping fact the P5 ablation table needs.

## Key learnings

- **Bit-identity is a claim about the softmax, not about the field.** A
  shift-invariant aggregator makes "no effect" and "constant effect"
  indistinguishable downstream; separating them costs one extra column at the
  same call site. D-353 called bit-identity across three readouts "a mechanism
  claim" — it was, but for a mechanism *pair*, one member of which it had
  already discarded.
- **A control that fails to reproduce is still a result**, provided it is
  allowed to void the claims it was there to license. The σ ≡ 0 finding
  survives because it needs no control — zero is zero at any configuration —
  while every `convoy` number here is suspended.
- Sparsity is the channel's operating regime even where it works: ~3 % of
  planning steps carry any across-rollout epistemic signal at all.

## Recommended next 1–3 priorities

1. **Close the `convoy` configuration gap** — 661.5 vs 151.6 steps between
   this probe and D-353 at nominally identical settings. Until it is
   explained, D-353's `+0.1856 m` and this cycle's spread numbers are not
   known to describe the same experiment. Cheap: diff the two call sites.
2. **Make σ nonzero on `obstacle_crossing`** — the scene's actors cross at
   y ∈ [-2, -3.8] well inside the 5 m sensing range, so nothing is ever
   shadowed. Shrink `sensing_range` or add a static occluder, then re-take.
3. **Price the horizon sum** — even on `convoy`, `Σσ` over the horizon
   discards where along the horizon the ignorance sits. A max- or
   discounted-σ readout is a one-line change to the same critic.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/19-01-sigma-is-exactly-zero-on-the-cloud.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
