# The bottleneck named a scene the repo retired by proof three weeks ago

- **Cycle**: 2026-08-21 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-bot` STATE bottleneck — `cafe_cut_in_v0` goal_reached
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's bottleneck at face value and opened `cafe_cut_in_v0` to find why
  `goal_reached` fails at every collision margin.
- Read the yaml first: the pedestrian's terminal waypoint is `(0.0, -3.8)`,
  held forever; the goal is `(0.0, -4.0)` with `xy_tol 0.2`. The goal ball is
  parked inside the obstacle's keep-out.
- Found `eval/mppi_sandbox/feasibility.py` had already proved exactly this on
  2026-08-02 — best attainable clearance **−0.2 m**, so `goal_reached: 1` and
  `collision: 0` are mutually unsatisfiable *by construction* — and
  `scene_eligibility` has excluded the scene under `GOAL_BALL_BLOCKED` since.
- Shipped `bottleneck_scope`: screens STATE's `## Current bottleneck` for scenes
  the eligibility census already excludes. 15 tests.

## What worked / what failed

- The screen fires on the live tree: `RETIRED — 1 scene(s) named, 1 retired by
  proof`, `-0.20 m`, matching `feasibility`'s docstring value exactly.
- **The bottleneck sentence was not wrong in any clause.** "Fails `goal_reached`
  at every collision margin" is true; "the knee provably does not reach it" is
  true. The conclusion — that this is a *new P3 blocker* — is what fails. It is
  the screen's own verdict, re-derived from closed-loop runs by a cycle that did
  not know the screen had spoken.
- `census_preempt` caught my own entrant at the stage (`136 vs pin 135`) for the
  14th-plus cycle running; cost 2 s against a 23-min red suite.
- **The suite went red on my own pin edit, and `census_preempt` could not have
  caught it.** I anchored the tally bump on the literal that ends
  `tail_mean.both_columns_scenes` — which belongs to the *AND-shaped guards*
  set, not the pool tally — so `bottleneck_scope.scope` was registered as `&`-
  shaped when its exemption is sense `IN`. `3999 passed, 1 failed` after 1360 s.
  The `UNCOVERED` line had named this exact gap: the AND registry is one of the
  four censuses `census_preempt` says it does not read. It cost a second full
  suite, which is the honest price of the miss.
- The derivation guard caught a scene name in my module — but in a *function
  docstring*, where the citation is the motivating example, not a registry copy.
  Fixed by stripping docstrings via `ast` rather than splitting on quotes
  (D-390's shape: a guard grading its own prose).

## North-star delta

- **No movement in controller capability, and the honest reading is that one
  claimed blocker never existed.** P3's real remaining matrix is 3 eligible
  scenes of 8, 1 measured — `cafe_cut_in_v0` was never among them.
- Prevents a wasted cycle: PLAN consumes the bottleneck line as its candidate
  pool, so a retired scene named there spends ~35 min re-measuring an
  infeasibility that costs milliseconds to look up.

## Key learnings

- **D-047 one level up.** D-047 caught a *guard* hand-copying a registry that
  had grown. Here the hand-copy is the **bottleneck sentence**, and its reader
  is next cycle's PLAN — a more expensive reader than any grep.
- A cycle can measure carefully, report truthfully, and still hand its successor
  a false lead, because REPORT restates conclusions in prose that no guard reads.
  The screen closes that gap in the one direction that is a proof.
- The asymmetry is deliberate and worth keeping: `LIVE` claims nothing. Only
  `RETIRED` is a finding, so the screen can never retire a bottleneck a cycle
  could actually act on.

## Recommended next 1–3 priorities

1. Re-aim the bottleneck at the **eligible-but-unmeasured** scenes:
   `cafe_convoy_v0` and `cafe_obstacle_crossing_v0` (2 of 3 eligible, unmeasured).
2. `cafe_freezing_v0` is excluded only by `NO_DECLARED_MARGIN` — a one-line yaml
   decision, not a geometric proof. Decide whether it declares one.
3. Consider wiring `bottleneck_scope` into the REVIEW step so the screen runs
   before PLAN reads the line, not after.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/bottleneck_scope.py, eval/mppi_sandbox/tests/test_bottleneck_scope.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md
- TSV row appended: yes
