# The sign question was answered eleven weeks ago — twice, in opposite directions

- **Cycle**: 2026-08-14 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `feed-0814` Decide the shadow critic's sign before writing a line of it (research feed, PA-MPPI `2509.14978`)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the 08:00 feed's top entry at its word. PA-MPPI (RA-L 2026) adds a soft
  perception cost to MPPI whose sign is **attract** — it pulls toward the
  unknown to resolve it — and the feed's suggested TODO says
  `p3-epistemic-shadow-cost-critic` "has never stated which of the two it is",
  attract or repel, and that the two cannot be reconciled by tuning a weight.
- Before writing the declaration the TODO asks for, read the branch's own
  critics. Found **both signs already shipped**: `ShadowCostCritic`
  (`w_epist·Σσ`, charges σ at the rollout point) and `ObservationValueCritic`
  (`w_voo·Σ(1−V)`, charges the shadow you fail to reveal).
- Shipped `eval/mppi_sandbox/epistemic_sign.py`: reads each critic's sign off
  its **own cost function** on one blind-corner geometry, at one shared weight,
  with no planner in the loop. 14 tests.

## What worked / what failed

- **The feed's premise is false and the measurement says so cleanly.** On one
  disc-shadow geometry at `w = 10`: `ShadowCostCritic` **REPEL** (mean cost
  10.000 in shadow vs 0.000 outside), `ObservationValueCritic` **ATTRACT**
  (2.000 in shadow vs 5.587 outside — the shadow is **2.8× cheaper**). Opposed,
  same geometry, same weight, so the split cannot be explained as tuning. Holds
  at `w ∈ {1, 10, 200}`.
- **The statistic had to be chosen, and the obvious one is wrong.** Pearson
  correlation against σ is exactly `+1.0000` for `ShadowCostCritic` and only
  `−0.2078` for `ObservationValueCritic` — because `V(q)` is an aggregate over
  rays from `q`, **not a function of σ at `q`**. Letting corr decide would
  report the attract arm as nearly signless. `SIGN_STATISTIC = "mean_split"`,
  declared before dividing by it; corr is returned as a secondary diagnostic
  and pinned as weak-by-construction.
- **Silence is a third verdict, not a weak sign.** D-021 measured
  `ShadowCostCritic` signal-free on `cafe_obstacle_crossing_v0`. `SILENT` fires
  on spread **before** the mean split is consulted, so a float wobble cannot
  pick a sign out of a constant cost — pinned with a constant *non-zero* cost,
  where the split is 0.0 either way.
- **No census bill.** 198 pins across the six pin files pass unmoved — unusual
  for a new module, and checked rather than assumed.

## North-star delta

- **No planner movement, and this cycle did not attempt any.** What moved is a
  false-novelty claim retired before it was published: the feed was one abstract
  from having the branch assert an open question that its own code closed.
- The `soft + MPPI-native + repel` cell the feed calls the branch's novelty
  locus **is occupied — by this branch, `ShadowCostCritic`, since Q-017** — and
  D-021 measured it inert. That is a materially different claim from "empty".

## Key learnings

- **Read the code before accepting a literature-derived gap.** Three consecutive
  feed cycles have now produced corrections; this one corrects the feed *from
  the repo* rather than from another fetch. The feed reads papers, not
  `critics/`.
- **This branch reached PA-MPPI's sign by measurement, eleven weeks before the
  citation.** D-021 killed the repel arm on evidence (byte-identical
  trajectories at `w_epist = 200` vs `0`) and wrote the attract arm as its
  replacement. The convergence is the strongest thing here and none of it was
  written down as a *sign* decision — which is exactly why the feed could ask.
- **A sign read off a cost function is not a claim about audibility.**
  Conflating "which sign is it" with "is it audible on this scene" is what made
  an answered question look open. The three-valued return exists to keep them
  apart.

## Recommended next 1–3 priorities

1. **Q-148** — the branch now holds two opposed arms and no rule for choosing.
   Decide by measurement on an occlusion scene, not by citation.
2. The standing planner question (STATE #1): with no admissible `w_freeze`,
   is the freeze priced elsewhere or does `cafe_freezing_v0` not freeze?
3. Spend one deep fetch on PA-MPPI's **full text** — this cycle has the sign
   but not the perception cost's functional form, and the form is what a
   head-to-head against `ObservationValueCritic` would need.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/epistemic_sign.py, eval/mppi_sandbox/tests/test_epistemic_sign.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
