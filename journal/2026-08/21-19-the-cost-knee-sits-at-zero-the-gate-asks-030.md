# `pass=0/5` is a knee-placement mismatch: the cost cliff is at 0.0 m, the gate asks for 0.30 m

- **Cycle**: 2026-08-21 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Diagnose `pass=0/5` at baseline
- **Phase**: P5
- **Status**: keep

## What I tried

- Ran `stock_mppi` at baseline (both critics at `0.0`, seed 0) on
  `cafe_obstacle_crossing_v0` and `cafe_cut_in_v0` and read the **per-check**
  acceptance dict rather than the rolled-up `pass` boolean — the read STATE's
  bottleneck asked for and that three weight-sweep cycles never took.
- Traced the failing check back to the term in `stock_mppi` that is supposed
  to produce it.

## What worked / what failed

- **One sub-condition fails, and it is the same one on both scenes.** On
  `cafe_obstacle_crossing_v0` six of seven hard checks pass —
  `goal_reached` ✓, `collision` ✓, `cte_rms` 0.124/0.4, `cte_max` 0.279/1.0,
  `heading_err_rms` 0.132/0.30, `completion` 0.992/0.95. The only failure is
  `min_distance_to_obstacle`: **0.0097 m measured against a 0.30 m gate**.
  On `cafe_cut_in_v0` clearance fails too (0.175/0.30), plus `goal_reached`.
- **The mechanism is a knee, not a weight.** `stock_mppi` charges
  `w_collision = 1.0e4` on `clear < 0.0` and `w_obs_soft = 10.0` on
  `exp(-clear / 0.3)`, where `clear` is already radius-subtracted (surface)
  clearance. So the cost landscape has a 10⁴ cliff at **exactly 0.0 m** and,
  across the whole 0 → 0.30 m band the gate grades, a nearly flat soft
  gradient worth ~6 cost units per step (9.68 at 0.0097 m vs 3.68 at 0.30 m).
  The planner parks on the cliff edge because that is where the goal and
  speed terms outbid the barrier. It is doing exactly what it was told.
- **`collision` is not an independent check.** `run.py:162` defines it as
  `clearance < 0.0` — the same scalar as `min_distance_to_obstacle`, at a
  looser threshold. It can never fail while the 0.30 m check passes, so it
  has never been able to contribute a distinct failure to any `pass` count.
- **`cafe_cut_in_v0`'s #2 declared success priority is ungraded.**
  `cut_in_detection_latency_max` comes back `'skipped'` and lands in
  `ungraded`. The scene names it second in `success_metric_priority` and
  nothing computes it.

## North-star delta

- **First non-zero movement in 37 cycles.** The obstacle-avoidance arm now has
  a located, quantified defect instead of a pinned metric: the avoidance cost
  and the avoidance gate disagree about where the boundary is, by 0.30 m.
- Refutes the framing STATE offered. `0/5` is neither "a genuine planner
  failure" nor "a threshold no run can meet" — it is a **third answer**: the
  planner meets the constraint it was given (no overlap) and is graded against
  one nobody priced into the cost. Both are individually reasonable.
- Explains D-405/D-407/D-408 retroactively. `w_epist` / `w_voo` add cost
  terms, but the binding constraint is *where `w_collision`'s knee sits*, and
  no epistemic weight moves it. `pass=0/5` at every weight was structural.

## Key learnings

- **Read the per-check dict, not the rolled-up boolean.** `pass` is an `all()`
  over seven checks; three cycles of 5-seed tables treated it as one signal
  while six of its seven inputs were green the whole time. The diagnosis cost
  two runs and no compute.
- **A weight sweep cannot find a knee-placement bug.** Sweeping the magnitude
  of a term whose *threshold* is wrong reproduces the failure at every rung,
  which reads exactly like "this knob doesn't matter" — D-408's conclusion,
  which was correct about the knob and wrong about why.
- Two acceptance keys measuring the same scalar at two thresholds is an audit
  hazard: `collision` inflates the apparent hard-check count by one.

## Recommended next 1–3 priorities

1. **Decide where the avoidance knee belongs** — move `w_collision`'s
   threshold to the acceptance margin (or add a second knee at 0.30 m) and
   re-measure `pass` on both scenes. This is the one change that can move
   `pass` off 0/5.
2. **Compute `cut_in_detection_latency_max` or drop it from the scene** — a
   declared #2 priority that grades `skipped` silently weakens every cut-in
   claim.
3. **Collapse or document `collision` vs `min_distance_to_obstacle`** — same
   scalar, subsumed threshold.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: journal/2026-08/21-19-*.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
