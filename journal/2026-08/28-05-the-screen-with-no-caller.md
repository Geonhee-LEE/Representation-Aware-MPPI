# The screen that was red on disk for five days, and the bottleneck it retires

- **Cycle**: 2026-08-28 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Diagnose `cafe_cut_in_v0`'s empty window across all 8 arms
- **Phase**: P3
- **Status**: keep

## What I tried

- Cleared the strand first (D-112). The 08-26 17:00 cycle committed its code
  (`e6cb7b6`) and died before committing *any* REPORT artifact and before
  pushing. `c70a1c4` carries its four durable files unchanged — D-480, Q-207,
  the journal, the TSV row it had already appended.
- Then took STATE's #1 actionable — diagnose `cafe_cut_in_v0`. STATE said to
  check `DEFAULT_LADDER` against the recorded per-seed ESS **before** spending
  rollout budget. I did something cheaper first: looked for prior art. There was
  some, and it was decisive.
- Shipped the fix that follows from it: `bottleneck_scope` gets a caller.

## What worked / what failed

- **The pick was already refuted, by a module written to refute exactly it.**
  `bottleneck_scope` (D-412, 2026-08-21) screens STATE's bottleneck sentence
  against the eligibility census. Run by hand this cycle it returned rc=1 on the
  first try: `RETIRED cafe_cut_in_v0: GOAL_BALL_BLOCKED (best goal clearance
  -0.20 m)`. `feasibility` proved on 08-02 that the goal ball is permanently
  occupied, so `goal_reached: 1` and `collision: 0` are unsatisfiable *by
  construction*. No ladder, no rollout, no temperature overturns a geometric
  fact about the yaml.
- **The screen had no caller, and that is the actual defect.** It shipped with
  15 tests, and every one builds its own STATE in `tmp_path`. So the machinery
  was covered and the live file was never read by anybody: the suite stayed
  green while `STATE.md` carried a `RETIRED` bottleneck for three consecutive
  cycles (08-22 → 08-26). This is D-318's shape with the scope narrowed to
  zero — a clean pass over-stating what it covered, because what it covered was
  fixtures.
- **The near-miss is the measurement.** STATE 08-26 17:00 wrote "the instrument
  thrust is finished. Do not open another" and ranked `cafe_cut_in_v0` first.
  The next PLAN had no remaining reason to defer it. The screen's own docstring
  prices the outcome: "a retired scene named here spends a whole cycle
  re-measuring an infeasibility that costs milliseconds to look up." It cost
  milliseconds.
- **The pin fired before the fix.** `TestLoopWiring` was written first and
  failed against the unedited prompt with the exact defect in its message. It
  passes now, 20/20 on the file.

## North-star delta

- **The P5 admission gap is 1 cell, not 9.** 8 of the 9 empty cells are
  `cafe_cut_in_v0`, uncompletable by proof — those are not a gap, they are the
  eligibility screen's verdict already recorded in the table. Over the 8 scenes
  any controller *can* complete, the shipped table reads **63 of 64 cells
  admissible**, one empty (`cbf_mppi` × `cafe_obstacle_crossing_v0`, Q-206).
  That is a materially different P5 headline than "9 of 72 empty", and it was
  derivable this whole time from two numbers already on disk.
- One cycle of P5-axis budget preserved, 6 days before P5 entry (2026-09-03),
  in a stretch where every cycle is suite-bound.
- Zero rollouts, zero new planner numbers. The delta is in the denominator, not
  in the controller.

## Key learnings

- **A screen with no caller is not a screen.** Tests that cover the machinery
  and never the live artifact produce a green suite and zero protection. Ask of
  any new guard: *what invokes this, and would a careless rewrite silently stop
  invoking it?* Both halves shipped here — the prompt step, and a derived pin
  on the prompt step.
- **Where a check cannot live is itself a design fact.** `STATE.md` is
  local-only under D-011, so CI can never take this reading; only the loop can.
  That asymmetry is not a limitation to route around, it is the argument for
  putting the call in the prompt and pinning the call rather than the verdict.
- **Cheap prior-art lookup before the planned measurement.** STATE prescribed a
  ladder-vs-ESS check. A grep for the scene name found `arrival_scope_census`
  ("never arrives"), `bottleneck_scope`, and `feasibility` inside a minute — all
  of which already answered it. The prescribed measurement would have been
  correct and worthless.
- Corollary for STATE-writing: the bottleneck sentence is an input to the next
  cycle's PLAN, so it deserves the same screening as code. It now gets it.

## Recommended next 1–3 priorities

1. **Answer Q-206** — the one genuinely empty cell in the reportable 64:
   `cbf_mppi` × `cafe_obstacle_crossing_v0`, `min_spread == 1.00x`,
   `completes_anywhere: true`. Degenerate weighting, or a ladder that never
   moved the softmax? One cell, no rollout, and it is now the whole admission
   gap.
2. **Re-state the P5 headline on the 64-cell denominator** — the "9 of 72"
   figure is in shipped docstrings and in `baseline_matrix`. It is not wrong,
   but it is the wrong denominator for an admission-gap claim, and P5 entry is
   6 days out.
3. **Follow the `essps_mppi` finding** — λ=0.1 admissible in 8 of 72 cells, all
   one arm. Bears on which controller P5 reports as baseline. Unchanged and
   still unaddressed.

## Artifacts

- PR: #67 (open, updated)
- Files touched: `eval/mppi_sandbox/bottleneck_scope.py`, `eval/mppi_sandbox/tests/test_bottleneck_scope.py`, `scripts/prompts/auto_research.md`, plus the 08-26 17:00 strand discharge
- TSV row appended: yes
