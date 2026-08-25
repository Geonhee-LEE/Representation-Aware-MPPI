# The robot parks on whatever knee you price it against

- **Cycle**: 2026-08-21 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Bound the blast radius of moving the avoidance knee
- **Phase**: P3
- **Status**: keep

## What I tried

- Made the knee a parameter: `MPPIParams.collision_margin`, default `0.0`,
  replacing the literal `0.0` in both `_cost` branches (gated and legacy).
  At the default this is byte-identical to every prior run — the same
  ablation invariant `w_freeze` and `gap_gate_strength` ship under.
- Measured the trade directly instead of re-calibrating the 8×3 matrix:
  2 scenes × margin {0.0, 0.15, 0.30} × seeds {0,1,2} = 18 runs, 22 s total.
- Pinned it with 7 tests: the default, the scene's threshold, the cost
  arithmetic, and the achieved-clearance claim.

## What worked / what failed

- **The knee is 1:1 with achieved clearance.** `min_obstacle_clearance` tracks
  `collision_margin` on both scenes across all three rungs — crossing
  `0.010/0.012/0.002 → 0.155/0.165/0.153 → 0.325/0.302/0.311`, cut_in
  `0.175/0.191/0.270 → 0.153/0.153/0.214 → 0.300/0.300/0.332`. The planner
  parks on the boundary it was priced against, wherever that is. D-409's
  diagnosis is now a *mechanism*, not an inference.
- **`min_distance_to_obstacle` flips green on both scenes at 0.30** — 6/6 runs
  clear the gate. First time this check has passed in the avoidance arm.
- **It is not free, and the bill lands on tracking.** On crossing, seed 0 goes
  to **full pass (1/3)** — the first `pass=true` the arm has produced — but
  seeds 1–2 trade the clearance failure for `heading_err_rms_max` (both) and
  `cte_rms_max`/`cte_max` (seed 2); `cte_rms` 0.122 → 0.323/0.505. Seed 0's
  `time_to_goal` goes 7.6 s → 17.7 s: it takes a real detour.
- **`cafe_cut_in_v0` has a second, independent blocker D-409 did not name.**
  `goal_reached` is false at *every* margin including 0.0 (`time_to_goal` null
  on all 9 runs). Its `pass=0/5` has two causes and the knee only fixes one —
  consistent with the 2026-08-02 row "cafe_cut_in never completes at any temp".
- The cost arithmetic came out exactly as predicted: moving the knee to 0.30
  changes `_cost` by precisely `w_collision` on rollouts inside the band and by
  exactly `0.0` outside it. Nothing else in the cost moves.

## North-star delta

- **First `pass=true` in the obstacle-avoidance arm** (crossing, seed 0, all
  seven hard checks). The 37-cycle `pass=0/5` streak is broken on one cell.
- The gate-relevant knob now exists and is measured, where before it was a
  literal no weight could reach.
- Blast radius of *shipping*: exactly zero (default is bit-inert). Blast radius
  of *using* it: measured on the two scenes that motivated it, not assumed.

## Key learnings

- **Parameterising first turns a blast-radius question into a measurement.**
  STATE asked for a 24-cell `lam` re-calibration *before* touching the knee.
  Shipping the knee at its current value makes that cost zero by construction,
  and the interesting half — what 0.30 buys and charges — then costs 22 s on
  the two scenes that matter. The 8×3 sweep is still owed, but only for cells
  that would actually run at a non-zero margin.
- **A failing rolled-up `pass` can have more than one cause, and fixing the
  located one does not flip it.** cut_in cleared the check D-409 named and still
  reads `pass=false`. The D-409 lesson (read the per-check dict) applies to its
  own fix.
- **Clearance and tracking are in direct tension at this knee.** Every metre of
  margin is bought with cross-track and heading error, so "where should the knee
  sit" is not answerable from the safety side alone — it needs the scene's
  `success_metric_priority`, which is exactly what cut_in leaves unmeasured.

## Recommended next 1–3 priorities

1. **Diagnose `cafe_cut_in_v0`'s `goal_reached=false` at every margin** — the
   second blocker, now isolated and independent of the knee.
2. **Re-measure the crossing `lam` window at `collision_margin=0.30`** — seeds
   1–2 fail on heading/cte, which is the classic under-damped-temperature
   signature; the knee may be affordable at a different `lam`.
3. **Decide whether `collision_margin` should default to the scene's declared
   `min_distance_to_obstacle`** rather than a global constant — the gate is
   per-scene, so a global knee is the wrong shape.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/controllers/stock_mppi.py`, `eval/mppi_sandbox/tests/test_collision_knee.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
