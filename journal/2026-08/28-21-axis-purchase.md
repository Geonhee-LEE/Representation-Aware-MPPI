# Buying the two uncensused north-star axes — and what they cost the obstacle line

- **Cycle**: 2026-08-28 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-bottleneck` Buy the `time_to_goal` per-arm-per-scene census
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE's bottleneck literally — *"check whether `runs/*.json` already
  carries a per-run time-to-goal that no census reads, before pricing a rollout
  sweep"* — and found the first cut looks in the wrong place.
- Measured the seed-0 census directly instead: 8 registry arms × the 4 joint
  scenes from `baseline_domination.coverage()`, at `clearance_census.retake`'s
  exact operating point so the cells are joinable with the existing columns.
- Shipped `eval/mppi_sandbox/axis_purchase.py` (+ 22 tests) recording the table,
  deriving the findings, and pinning them via `CENSUS`/`drift` like its siblings.
- Repaired the three censuses `census_preempt` flagged at the stage: guard tally
  153→155, `consumer_reach` residue +1, lam sites 107→108 / total 246→247.

## What worked / what failed

- **The bottleneck was a pricing question nobody had priced.** 32 rollouts,
  **58.6 s**. Several cycles deferred this census while calling it a "sweep";
  it fits inside a coffee break. Third time on this branch an unmeasured cost
  estimate changed a plan (D-326 15×, Q-159 19×).
- **`runs/*.json` cannot answer it.** Those 48 files carry four controller
  *labels* (`stock`/`risk`/`cbf-stock`/`cbf-risk`), not the eight-arm registry,
  and their `metrics` block predates `time_to_goal` entirely. What they do carry
  is `acceptance.time_to_goal_max` reading `"skipped"` — the acceptance layer
  recording that it wanted the number and did not have it.
- **The right route was cheaper than the one the bottleneck proposed.** Both
  axes are pure functions of `traj`, and `clearance_census.retake` already
  builds `traj` for all eight arms and throws it away. The census is the same
  rollouts with two more readers attached.
- **`census_preempt` earned its ~2 s again** — 3 of 10 censuses drifted at the
  stage, which is a red 12-minute suite avoided.

## North-star delta

- **+2 of the north star's 4 axes now have a per-arm-per-scene census.** Both
  `UNCENSUSED_AXES` are bought at seed 0 over the joint surface. The P5 report's
  measurable surface goes from 2 axes to 4.
- **The 물체회피 contract line now has a disclosed price.** `cbf_mppi` is
  **never the fastest arm** on any joint scene — 5/8, 7/8, **8/8**, 6/7 — and on
  `cafe_head_on_v0` it is dead last at 16.1 s against 8.4 s (**+92 %**). STATE
  predicted exactly this ("clearance is usually bought with time"); it is now
  measured rather than suspected.
- **A defect found in the tracking record**: `essps_mppi`, D-487's tracking
  plurality candidate, never reaches the goal on `cafe_obstacle_crossing_v0`
  (`time_to_goal is None`) yet holds a `cte_rms` of `0.0369` there — inside the
  column its 6/7 record was computed from. A cross-track RMS over a run that
  never arrives measures how tidily an arm failed.

## Key learnings

- **A bottleneck can name the wrong artifact and still be right about the gap.**
  The gap was real; `runs/*.json` was a dead end and the trajectory was the live
  one. Screen the *proposed route* separately from the question it serves.
- **Adding axes cannot overturn D-486.** Domination gets harder as axes are
  added, so "the frontier is the whole registry" is monotone in axis count. What
  new axes *can* do is price a per-class line — which is exactly what happened.
- **The inert-channel signature reproduced on a third and fourth column set.**
  `geometric_mppi ≡ stock_mppi` and `frozen_risk_mppi ≡ risk_mppi` are
  bit-identical in all four recorded columns on all four scenes.
- **A contract line and its price are different measurements.** D-487's obstacle
  line survives as *stated* (`CLASS_AXIS` instruments 물체회피 with clearance
  alone), but a report naming `cbf_mppi` without disclosing it is the slowest arm
  is one measurement short of honest.

## Recommended next 1–3 priorities

1. **Re-take D-487's tracking record with the unfinished cell dropped** —
   `essps_mppi @ cafe_obstacle_crossing_v0` is in the column its 3/4 was
   computed from. `axis_purchase.unfinished()` names the population.
2. **Decide whether `CLASS_AXIS` should instrument 경로추종 with all four of
   its `CLAUDE.md` clauses** — the north star names smoothness and time-to-goal
   under 경로추종, and both columns now exist.
3. **Widen to 8 seeds** — `WIDENING_UNBOUGHT = 224` rollouts, ~7 min at the
   measured rate. Cheap enough to stop deferring.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/axis_purchase.py`, `eval/mppi_sandbox/tests/test_axis_purchase.py`, `eval/mppi_sandbox/tests/test_guard_reflexivity.py`, `eval/mppi_sandbox/tests/test_consumer_reach.py`, `eval/mppi_sandbox/tests/test_default_lam_sites.py`, `docs/decisions.md`
- TSV row appended: yes
