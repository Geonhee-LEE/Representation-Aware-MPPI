# The queue reading stands up — and the second instrument was mislabelled

- **Cycle**: 2026-08-17 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — `queue_debt` reading (direct follow-through on D-323)
- **Phase**: P3
- **Status**: keep

## What I tried

- Moved D-323's hand measurement of the PR queue into a standing module,
  `eval/mppi_sandbox/queue_debt.py`, so gate 1 and Phase 1 REVIEW can print
  "6 open, 5 inside the envelope" instead of `6/6`.
- Reused `branch_debt`'s self-derived envelope (largest diff ever merged here:
  41 files / +9,543 over 58 merged commits) rather than inventing a threshold.
- Published **both** instruments per PR — three-dot review cost and two-dot
  merge effect — because D-323's two errors were both instrument-choice errors,
  in opposite directions.
- 11 tests, loop-free by construction so they owe no `loop_reach.READING` row.

## What worked / what failed

- The module reproduces D-323's hand numbers exactly (#66 4f/+98, #68 5f/+411,
  #23 7f/+347, #69 7f/+513, #44 9f/+413, #67 660f/+156,342), which is the
  check that mattered: the standing place agrees with the cycle that paid for
  the reading by hand.
- ⭐ **The second instrument was mislabelled, and I shipped it wrong first.**
  Bare `git diff main head` is *symmetric*, so once `main` advances past the
  merge point it reports `main`'s own progress as though the branch reverted it.
  #23 read **152 files** that way against the 7 it actually touched; #44 read
  126 against 9. A number labelled "merge effect" that is dominated by commits
  the branch never saw is the same mislabelling D-323 was about — I had encoded
  the lesson's *conclusion* and reproduced its *mechanism* one line lower.
- The fix is to scope the two-dot comparison to the branch's own paths: *of the
  files this branch changed, how many still differ from `main`*. #23 answers
  **4 of 7** — the other three are the `STATE`/`JOURNAL`/`RESULTS` files an
  earlier commit already reverted, which is exactly the fact that refuted
  D-323's false D-011 alarm. Merge effect is now bounded above by review cost,
  as a merge effect must be.
- ⚠️ Caught myself a second time: `measure()` initially returned
  `BEYOND_PRECEDENT` as a placeholder "the caller replaces this". That is a
  non-answer wearing an answer's vocabulary — the precise category error the
  module's own docstring refuses. Replaced with an explicit `UNGRADED` sentinel
  that `report()` may never publish.
- `census_preempt` 3/3 CLEAN before and after; targeted tests 18 passed.

## North-star delta

- **No movement on the robot.** Zero sim runs; no controller, representation or
  dynamics touched. Fourth consecutive meta cycle. The honest reading is that
  this cycle improved the executor's ability to describe its own blockage, not
  the planner's ability to avoid an obstacle.
- What it does buy toward the north star is indirect but real: the binding
  constraint is a human merge, the executor cannot merge, and the one lever it
  has is making the ask cheap to act on. The ask is now a ranked list with the
  cheapest merge on the first row, re-derived every cycle instead of every 36
  days.

## Key learnings

- **Encoding a lesson's conclusion does not immunise you against its
  mechanism.** I wrote a docstring about three-dot vs two-dot and then shipped a
  two-dot aggregate that was wrong for the same reason. The lesson only became
  safe once it was a *bounded* quantity (merge effect ≤ review cost) that a test
  can hold.
- **The dangerous zero here points the other way from `branch_debt`'s.** That
  module's `UNDECIDABLE` protects a *report*; this one's protects **gate 1**.
  `gh` unavailable yields zero PRs, and zero PRs read as a measurement authorise
  branch-opening precisely when the executor cannot see what it is adding to.
- Two of the last three cycles found their own error mid-cycle rather than in
  review. That is the measure-before-repair habit (D-186) working, but it also
  says these meta modules are being written faster than they are being thought
  through.

## Recommended next 1–3 priorities

1. **Wire `queue_debt` into the gate-1 snippet and the escalation message** —
   the module exists but the constitution's gate still prints a bare count. The
   reading is only standing once the place that needs it calls it.
2. **Break the meta streak: pick a sandbox science item next cycle.** Four
   consecutive zero-north-star cycles is itself a finding. Q-155 (`w_voo > 0`
   λ-window re-measure) is on-branch and needs no unmerged PR.
3. User merges any two of #66/#68/#23/#69/#44 — all five are inside the
   envelope; #67 need not be read at all to unblock the queue.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/queue_debt.py, eval/mppi_sandbox/tests/test_queue_debt.py, eval/mppi_sandbox/branch_debt.py, docs/decisions.md
- TSV row appended: yes
