# The silent-`"skipped"` defect was not one scene — it was five

- **Cycle**: 2026-08-13 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — sweep the other nine scenes for `rules`-less acceptance keys
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE #2 (the one-grep sweep) over STATE #1 (price the freeze into the
  planner). The wall-clock advisory graded the preceding run `PUBLISHED` at
  **60m29 against 35**, and it held the lock through the 18:00 cycle, which
  never ran. #1 is a cost term plus a measurement — two suites minimum. Cutting
  scope was the instruction, and #2 is the cheap half of the same defect class.
- Swept all 9 shipped scenes' `acceptance` blocks against `check_acceptance`'s
  rules table. **5 more ungraded keys, in 5 different scenes.**
- Hoisted the rules table to `run.ACCEPTANCE_RULES` and wired `jerk_lat_max`.
- Added `eval/mppi_sandbox/acceptance_coverage.py` — the sweep as a census guard
  — plus 8 controller-free tests.
- Added an `ungraded` list to every run artifact.

## What worked / what failed

- **The defect class was 6× wider than the instance D-241 found.** One grep,
  five hits: `time_to_goal_max_ratio` (convoy), `cut_in_detection_latency_max`
  (cut-in), `time_to_goal_max` (freezing), `yield_or_pass_decision_time_max`
  (head-on), `jerk_lat_max` (figure-8).
- **The sharp reading: 4 of the 5 sit in the scene's own
  `success_metric_priority`** — declared as a top-3 reason the scene exists, and
  not computed. After wiring `jerk_lat_max`, *every one of the 4 survivors* is a
  prioritised criterion. That is pinned as a test, not just written here.
- **One of the five was free and nobody had noticed.** `jerk_lat_max: 8.0` needed
  no new metric: `summary()` has emitted `jerk_lat` on every run since the
  harness landed and no rule read it. Measured 2.72/2.88/2.95 over 3 seeds
  against the declared 8.0 — so wiring it grades a silent criterion **without
  flipping any scene**, which is why it was safe to do under a cut budget.
- **The other four are definition work, not plumbing, and I did not fake them.**
  `time_to_goal_max` is the trap: the obvious wiring is `duration_s <= 12.0`,
  and `duration_s` is the whole sim, not the arrival — `stock_mppi` seed 0 runs
  13.1 s on a run that *did* reach the goal, so the obvious version would have
  failed the scene for a freeze that isn't there. Needs first-arrival time.
- Both census guards (`default_lam_sites`, `citation_audit`) green first try —
  the new test module is controller-free by construction.
- **The suite was red anyway, and the guard was right.** Hoisting the rules table
  to a module constant — done *for* D-047, so the sweep could read the registry
  instead of copying it — created two new module-level TYPED allow-lists, and
  `guard_reflexivity.unwatched_exemptions` reported them on the first run. The
  14th consecutive cycle in which a module joins a registry it audits. 5 failures
  across `test_guard_reflexivity` / `test_exemption_masking` /
  `test_exemption_control`, all of them this cycle's own doing.
- **The fix was to stop having a registry, not to pin one.** `acceptance_coverage`
  now derives the graded set by *calling* `check_acceptance` with a probe and
  reading the verdict's shape (`bool` = graded, `"skipped"` = not, absent =
  parameter). That is strictly stronger than D-047 asks: there is no second
  statement of the table to go short, and a rule added later is picked up with
  no edit here. The rules dict went back inside the function; the census became
  a `drift(census=...)` **parameter** rather than a closed-over constant, which
  is what took it out of the scan and, separately, is what lets the tests drive
  both drift directions without mutating module state.

## North-star delta

- **+1 acceptance criterion that now gates (`jerk_lat_max`), +0 mechanism.**
  Same shape as D-241: the north star's "완벽" needs criteria that are asked, and
  this cycle moved one more from declared to computed.
- **+4 named, pinned debts.** The remaining gaps are no longer discoverable only
  by grep — they fail the suite if they grow and are listed in the run JSON.
- No planner changed. The freeze is still unpriced; that bottleneck did not move.

## Key learnings

- **A defect found by grep should be answered by a sweep, not a fix.** D-241 fixed
  the instance it tripped over. The instance was 1 of 6, and the other 5 had been
  sitting in the same 9 files the whole time.
- **`"skipped"` is the failure mode, and the fix is a name.** The string reads as
  *checked* in an artifact. Cheap remedy: emit the ungraded key list explicitly,
  so the absence has to be read as absence.
- **Guard direction matters more than the guard.** A census that fails when a gap
  is *closed* teaches people to leave gaps open. `drift()` treats an unpinned gap
  as a finding and a newly-graded key as a stale pin — both actionable, only one
  a failure.
- **The cut-scope call was right, and the cycle overran anyway.** `elapsed` read
  5m01 where the previous cycle was already on suite two — and then the census
  tax cost ~25 min of iteration on top. The lesson is not "cut harder": it is
  that **any new module-level constant in this package is a suite-red event**,
  and the cheap check is `guard_reflexivity.unwatched_exemptions()` (0.5 s) at
  the moment the constant is written, not after an 8.8-minute suite.
- **Two of the three iterations were wasted on the wrong repair.** Adding
  enumerator functions did not clear the scan, because a watcher must be a
  *guard* whose population **is** the list, not merely a function that returns
  it. Deriving the set instead of registering it was both faster and better.

## Recommended next 1–3 priorities

1. **Price the freeze into the planner** — unchanged as the mechanism-grade
   successor (STATE #1, D-240/D-241), now with one fewer distraction.
2. **Implement `time_to_goal` as first-arrival time** and wire the two
   `time_to_goal_max*` keys — drops the census 4 → 2 and hands the freezing
   scene its third criterion. Explicitly *not* `duration_s`.
3. **Widen the freeze table to the paired-seed protocol** (n=12) before any arm
   ranking is quoted.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: eval/mppi_sandbox/run.py, eval/mppi_sandbox/acceptance_coverage.py, eval/mppi_sandbox/tests/test_acceptance_coverage.py, docs/decisions.md
- TSV row appended: pending
