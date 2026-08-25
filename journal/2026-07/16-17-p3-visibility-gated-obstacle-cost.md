# Visibility-gated obstacle cost — occlusion finally moves a collision outcome

- **Cycle**: 2026-07-16 17:00 KST
- **Branch**: `autoresearch/p3-visibility-gated-obstacle-cost`
- **TODO**: `vg-obscost` Visibility-gated obstacle cost (STATE Next-actionable #1)
- **Phase**: P3
- **Status**: keep

## What I tried
- Added `VisibilityGatedMPPI` (`vg_mppi`): a `StockMPPI` variant that, each control
  step, filters the obstacle set to those the robot *observes* — nearest surface
  within `sensing_range` AND not in the line-of-sight shadow of a nearer disc —
  and lets the inherited cost act on that subset. Gate geometry mirrors
  `GTBevProducer._occlusion` (D-012).
- New on-main scenario `cafe_blind_approach_v0` (single hazard, straight 0.9 m/s
  approach) — independent of the still-unmerged `cafe_blind_corner_v0` (#68), so no
  branch-stacking.
- 7 pytest cases: LoS occlusion gate, sensing-range gate, byte-for-byte ablation,
  aggregate collision-rate, run_scenario JSON path.

## What worked / what failed
- **Worked**: occlusion now moves a *collision* outcome. `vg_mppi(sensing_range=1.0)`
  collides on seeds 4/5/7 (clearance −0.23 m) while `stock_mppi` clears all 8 seeds.
  The true Q-017 unblock the bottleneck asked for.
- **Worked**: ablation invariant holds — `vg_mppi(inf)` on a single-obstacle scene
  reproduces `stock_mppi` byte-for-byte, so behaviour deltas are attributable to the gate.
- **Failed (informative)**: min-clearance alone does *not* separate oracle from gated on
  late reveal — the agile diff-drive + `w_collision=1e4` barrier make both graze the
  ~few-cm barrier floor once the hazard is seen. The separating signal is the raised
  **collision rate**, not surviving clearance. A single disc can't reproduce a persistent
  blind corner either: swerving to avoid the near occluder de-occludes the hazard early
  (why I switched the closed-loop demo from inter-obstacle occlusion to a sensing-range gate).

## North-star delta
- **+ occlusion now changes a collision metric** (0/8 → 3/8) — the first sandbox scene
  where a non-oracle observation model produces a measurable safety failure. This is the
  baseline an epistemic-aware controller must beat.
- + a reusable `vg_mppi` controller + `cafe_blind_approach_v0` scenario on main.

## Key learnings
- The right occlusion-cost metric on this plant is **collision rate over seeds**, not
  min-clearance (which saturates at the barrier floor). P5's occlusion axis should score
  collision/near-miss rate, not surviving clearance.
- Pure inter-obstacle (single-disc) occlusion is self-defeating for closed-loop demos:
  avoiding the occluder reveals the shadow. A persistent blind corner needs the L-wall
  geometry of #68, or a range gate (used here) that doesn't depend on approach angle.

## Recommended next 1–3 priorities
1. **Epistemic-aware controller vs `vg_mppi` on `cafe_blind_approach_v0`** — does widening
   berth into the unobserved region (RiskInflationCritic `k·σ`, or a beyond-range frontier
   term) recover the oracle's 0/8 collision rate? This is the payoff experiment.
2. **Once #66/#67/#68 land**: port `vg_mppi` onto `cafe_blind_corner_v0` (L-wall) to test
   the persistent-occlusion geometry where the range gate isn't needed.
3. **P5 occlusion metric**: adopt collision/near-miss *rate over seeds* as the occlusion-
   sensitivity score (min-clearance saturates).

## Artifacts
- PR: #69 (autoresearch/p3-visibility-gated-obstacle-cost)
- Files touched: eval/mppi_sandbox/controllers/visibility_gated_mppi.py, controllers/__init__.py, eval/scenarios/cafe_blind_approach_v0.yaml, eval/mppi_sandbox/tests/test_visibility_gated_mppi.py, results/p3-visibility-gated-obstacle-cost.tsv
- TSV row appended: yes (`sandbox:vg_collide=3/8;stock_collide=0/8`, keep)
- Note: full sandbox suite 63 pass / 1 fail — the 1 is the pre-existing `test_risk_mppi` occlusion-margin red (fixed by #66/#67), not introduced here.
