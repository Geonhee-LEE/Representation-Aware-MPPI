# The gap changed axis

- **Cycle**: 2026-08-26 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Re-state the P5 headline over 8 controllers
- **Phase**: P5
- **Status**: keep

## What I tried

- Measured the calibration table **before** restating anything: 72 cells,
  8 controllers × 9 scenes, rectangular, `admission_gap()` = `()`, `REGISTRY` = 8.
- Replaced the two stale prose sites — `baseline_matrix.admission_gap`
  ("16 cells over 2 controllers … 2/8 of the controller axis") and
  `calibrate_lam.default_controllers` ("a quarter of the controller axis") —
  with the measured reading, keeping the old numbers **dated** rather than
  deleted so the D-469 staleness lineage survives.
- Added `baseline_matrix.scene_admission_gap()`, returning
  `(uncalibrated, inadmissible)` as two tuples, plus two tests.
- Bumped the `guard_tally` pin 143 → 144 with its running-prose entry.

## What worked / what failed

- ✅ **The restatement turned up a finding rather than being bookkeeping.** Nine
  of the 72 cells still record an empty window and they are not scattered:
  **eight are one scene** (`cafe_cut_in_v0`, empty for all 8 arms) and the ninth
  is `cbf_mppi` × `cafe_obstacle_crossing_v0`. The residual gap is **scene-axis**,
  and `admission_gap` — being controller-grained — returns `()` on the very
  table that carries it. That is the same grain error its own docstring
  diagnoses (18 of 20 exclusions read as holes), read off the other axis.
- ✅ `census_preempt` returned the `guard_tally` 143 → 144 drift in **~2 s**,
  before the stage. The entrant was the new function itself. Fifth recorded
  D-199/D-318 collection; it would otherwise have been a red 742 s suite.
- ✅ `assert_reach.moved()` = `()` — D-478's cascade did not recur despite this
  cycle appending to `test_baseline_matrix.py` and `test_guard_reflexivity.py`.
- ⚠️ **"Needs no suite" was wrong, and predictably so.** STATE budgeted this as
  pure prose, but the prose lives in `.py` docstrings, so the tree moves and the
  receipt goes stale — a suite was owed either way. That is what licensed
  shipping the runnable slice alongside (D-016) instead of a docstring-only diff.
- ⚠️ The `probe` receipt was green at `c99b0bea` on entry and is now spent. The
  saving was real but it bought planning headroom, not a free push.

## North-star delta

- **The P5 headline's controller axis is now correctly described in the code
  that computes it.** No rollout, no controller change — but the axis P5 reports
  over no longer carries prose contradicting its own return value.
- **A previously-unnamed gap is now named and guarded**: one scene that no
  temperature can place for any of 8 arms. It was invisible to every existing
  instrument because they are all controller- or cell-grained.
- Still zero rollouts and no new metric. `cafe_cut_in_v0` being unplaceable is a
  measured fact about the *scene*, and whether it is a scene defect or a real
  limit is unanswered.

## Key learnings

- **A stale number is worth re-measuring rather than re-typing, because the
  measurement can disagree with the update you planned.** The task was "change
  2/8 to 8/8". The table said the axis was closed *and* that the gap had moved
  somewhere no existing census looks. Restating from STATE's prose would have
  produced a correct sentence and missed the finding entirely.
- **Closing a census can relocate what it was watching instead of ending it.**
  `admission_gap` going to `()` reads as "done"; it actually means the
  controller-grained instrument can no longer see the remaining gap. A census
  that reaches its goal state should be asked what it stopped being able to see.
- **"Needs no suite" is a claim about the tree, not about the work.** Any edit to
  a tracked `.py` — docstring or not — invalidates the receipt. Cycles budgeting
  prose work as suite-free should check which file the prose is in.

## Recommended next 1–3 priorities

1. **Answer why `cafe_cut_in_v0` admits no temperature for any arm** — it is 8 of
   the table's 9 empty cells and now has a name and a test. Either the ladder's
   range is wrong for it (the D-2026-08-02 "wrong decade" failure again) or the
   scene is genuinely unplaceable, and those have opposite consequences for P5.
2. **Add `assert_reach` to `census_preempt`** — still in neither the covered set
   nor the `UNCOVERED` line, now the fifth consecutive cycle with a census
   moving under an edit. Cheap and mechanical.
3. **Follow the `essps_mppi` finding** — re-measured here: λ=0.1 is admissible in
   exactly 8 of 72 cells and all 8 are `essps_mppi`, one per scene. Unchanged by
   this cycle and still bears on which arm P5 reports as baseline.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/baseline_matrix.py`, `eval/mppi_sandbox/calibrate_lam.py`, `eval/mppi_sandbox/tests/test_baseline_matrix.py`, `eval/mppi_sandbox/tests/test_guard_reflexivity.py`, `docs/decisions.md`
- TSV row appended: yes
