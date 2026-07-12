# Epistemic shadow-cost critic — implemented, proven geometrically redundant for single obstacles

- **Cycle**: 2026-07-13 01:11 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: (resume in-flight) Q-017 epistemic shadow-entry cost critic (`w_epist`·σ)
- **Phase**: P3
- **Status**: keep

## What I tried
- Resumed an interrupted in-flight branch: `ShadowCostCritic` (additive `w_epist·σ`
  on the EPISTEMIC channel, Q-017 answer (a)) wired into `risk_mppi`, but with a
  RED test and no unit coverage / no commit.
- Empirically diagnosed why `w_epist` was closed-loop inert, then converted the
  branch into a green, honestly-documented slice: unit tests for the critic
  contract, an extended baseline-invariance case, and an honest finding test
  replacing the false RED one.
- Registered Q-017 in `docs/deliberations.md` (it was STATE's #1 bottleneck but had
  never been committed as a deliberation).

## What worked / what failed
- **Critic mechanism is correct**: `_extra_cost` returns up to 220 (differential,
  per-rollout σ-sum spread 0–11) near a shadowing obstacle; unit tests confirm
  `w_epist·σ`, add-only, pessimistic out-of-grid prior, and `w_epist=0` no-op.
- **But closed-loop inert for a single convex obstacle** (Δ min_clearance = 1.9e-12
  at `w_epist` 0→200). Root cause is geometric, not a bug: a single obstacle's
  occlusion shadow is exactly its ray-cone; a rollout enters it only by heading
  toward the obstacle, where stock soft/collision cost already dominates →
  shadow-avoidance ⊆ obstacle-avoidance. At a pre-obstacle pose the softmax-weighted
  E_w[σ] is already ≈0 at `w_epist=0` (uniform mean 1.234) — nothing to redistribute.
- The prior cycle's RED test asserted the *margin* critic (k·σ) widens berth here; it
  does not (Q-017's original finding). Additive cost does **not** fix it either.

## North-star delta
- + 1 runnable representation-consuming critic (`ShadowCostCritic`) with 4 new tests;
  full sandbox suite 60/60 green.
- Negative but load-bearing result: epistemic gain **cannot** be judged on single-
  obstacle benches — occluded-obstacle avoidance (a core north-star class) needs a
  blind-corner/wall scenario. This redirects the P3 epistemic track.

## Key learnings
- For any single convex obstacle, epistemic shadow cost is redundant with obstacle
  cost — provable, not tunable. Turning up `w_epist` will never help there.
- The only geometries where additive σ adds information: multi-obstacle/wall occluders
  whose shadow hides a **low-obstacle-cost shortcut** (blind corner), or a
  beyond-range frontier that differs across rollouts (currently common-mode:
  r_sense=5 m ≫ rollout reach 1.2 m, so it cancels in the softmax).
- Ship the mechanism + the honest inertness guard now; defer the blind-corner
  scenario that would make it move the needle.

## Recommended next 1–3 priorities
1. Add a wall/L-corner occlusion scenario to `eval/scenarios/` where the shadow is a
   free-space shortcut; target `test_shadow_cost_moves_needle_in_blind_corner` GREEN.
2. Investigate a beyond-range frontier term (differential across rollouts) so epistemic
   cost bites even without an occluder.
3. Cross-check against reachability risk-region formulation (2503.04563, feed 159.md).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/critics/shadow_cost.py, critics/__init__.py,
  controllers/risk_mppi.py, tests/test_risk_mppi.py, docs/deliberations.md
- TSV row appended: yes
