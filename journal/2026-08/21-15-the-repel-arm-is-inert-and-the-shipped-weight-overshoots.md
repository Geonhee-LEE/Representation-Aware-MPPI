# The repel arm is still inert, and the attract arm's shipped weight overshoots its own sweet spot

- **Cycle**: 2026-08-21 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c3c5d39` P3 rollout slice — break the 36-cycle zero-delta streak
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's bottleneck literally: after 36 cycles of zero planner movement, run a
  **rollout** and produce a number, accepting a small diff. A sandbox rollout costs
  **0.31 s**, so the measurement was never the expensive part — the 1550 s receipt is.
- Swept both epistemic arms of `RiskMPPI` on `cafe_obstacle_crossing_v0` (the D-021
  scene) via `--ctrl-arg`: `w_epist` (`ShadowCostCritic`, repel) and `w_voo`
  (`ObservationValueCritic`, attract). Coarse arm first (0/200/2000, seeds 0–2), then a
  finer `w_voo` grid (0/25/50/100/200/400/800, seeds 0–4).
- No code change. The deliverable is the measurement plus D-405.

## What worked / what failed

- **The repel arm is inert, and now at 10x the weight D-021 used.** `w_epist=200` and
  `w_epist=2000` produce `cte_rms` and `min_obstacle_clearance` **identical to baseline
  to 6 decimal places on all three seeds**. D-021's eleven-week-old "byte-identical
  trajectories" finding is not stale and is not a tuning artefact.
- **The attract arm is audible — and non-monotonic.** The coarse grid only sampled 200
  and 2000, where it looks purely destructive (`cte_rms` 0.199 -> 0.810 -> 2.961 on seed
  0). The finer grid found the opposite regime underneath it.
- **There is a Pareto point, and the shipped default is past it.** Mean over 5 seeds:

  | `w_voo` | cte_rms | clear(mean) | clear(min) |
  |---|---|---|---|
  | 0 | 0.2098 | 0.0479 | 0.0084 |
  | 25 | **0.1558** | 0.0536 | **0.0273** |
  | 50 | **0.1314** | **0.0656** | 0.0237 |
  | 100 | 0.3188 | 0.0459 | 0.0175 |
  | 200 | 1.0689 | 0.0862 | 0.0425 |
  | 400 | 1.5154 | **-0.0495** | **-0.3267** |
  | 800 | 2.5575 | 0.0137 | 0.0005 |

  `w_voo=50` improves cross-track error **37%** *and* worst-case clearance **2.8x** over
  baseline. `scale_match.py:7` records that **D-027 shipped this critic at `w_voo=200`** —
  4x past the useful regime, in the band where `cte_rms` has already degraded 5x.
- **Honest limit: no scenario flips to pass.** `min_distance_to_obstacle` is `0/5` at
  every weight including the sweet spot, and `pass=false` throughout. This moves two
  metrics, not the acceptance verdict.
- **`w_voo=400` yields negative clearance** (-0.327 min) — the robot penetrates an
  obstacle. An attract term that pulls the robot toward what it cannot see becomes a
  collision term before it becomes a useless one.

## North-star delta

- **First measured planner numbers in 36 cycles.** `sandbox:cte_rms=0.1314` at
  `w_voo=50` vs `0.2098` baseline; `sandbox:clearance=0.0237` vs `0.0084` worst-seed.
- A concrete, defensible weight change is now available (`w_voo` 200 -> 50) that no cycle
  could have proposed yesterday, because nobody had run the grid.
- Still zero movement on *acceptance*: the scene fails its clearance gate at every point
  measured.

## Key learnings

- **The coarse grid inverted the conclusion.** Sampling only 200/2000 says "the attract
  arm destroys tracking"; sampling 25/50 says "it is the best operating point found". Two
  extra minutes of rollouts flipped the sign of the finding — and the branch has spent
  eleven weeks arguing about this term's *sign in construction* while never sweeping its
  *magnitude in a rollout*.
- **A default inherited rather than measured is a bug with no test.** `w_voo=200` came in
  by inheritance (D-027) and every downstream analysis module read that number as given.
- **The cheap measurement was available the whole time.** 0.31 s per rollout, 35 rollouts
  for the whole grid. The 36-cycle drought was not a cost problem.

## Recommended next 1-3 priorities

1. Change `RiskMPPI`'s `w_voo` default from the D-027-inherited 200 toward the measured
   50, with the sweep as its justification — and a pytest pinning the Pareto claim.
2. Re-run the grid on a second scene (`cafe_cut_in_v0` / `city_curved_v0`) before
   generalising: one scene is one scene.
3. Decide whether `ShadowCostCritic`, inert at 2000 across two independent measurements
   11 weeks apart, should be retired rather than re-tuned.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/21-15-*.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
