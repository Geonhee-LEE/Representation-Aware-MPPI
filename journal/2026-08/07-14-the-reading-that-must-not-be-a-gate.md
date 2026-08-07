# The reading that must not be a gate

- **Cycle**: 2026-08-07 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Wire `cycle_wallclock` into REVIEW beside the stranding reading
- **Phase**: P5
- **Status**: keep

## What I tried

- Gave `cycle_wallclock` the caller it has been missing for three cycles. (Not
  Q-103's trade-off *(a)* — D-112 already paid that. What recurred is the
  **pattern** Q-103 named: the instrument gets fixed and nobody calls it. Q-103
  stays open; its *(c)* is still unpaid.)
  `preceding` / `actionable` / `advisory` + a `review` subcommand, wired into
  Phase 1 step 0-bis of `scripts/prompts/auto_research.md`.
- Deliberately built it as an **advisory (always rc=0)** rather than a second
  gate beside `cycle_artifacts stranded`, and scoped it to the **immediately
  preceding run** rather than the day.
- `finding_grades()` derived from `grade()` per D-104 rather than declared as a
  module-level `frozenset`.

## What worked / what failed

- ✅ **The advisory/gate distinction is the substance, not packaging.** A strand
  names finished work sitting on disk — clearing it is an action available right
  now, which is why it outranks the decision tree. A wall-clock grade names a
  run that has already ended; **no cycle can un-overrun its predecessor**. Give
  that gate semantics and you get one of two outcomes: cycles stall on an
  unrepairable fact, or the reader learns a non-zero exit is ignorable. The
  second is worse, and it does not stay confined to the check that taught it.
- ✅ **Day-scoping would have been born muted.** 2026-08-07 held three
  `PREMATURE` runs before 10:00. A day-scoped check goes red at 03:00 and stays
  red until midnight regardless of what any later cycle does — D-044's exact
  muting failure, and the pin `test_scoped_to_the_preceding_run_not_the_day`
  fixes it on the real log.
- 🔴 **My `finding_grades()` did not track what its docstring said it tracked.**
  I wrote it as a derivation specifically to avoid D-104's unwatched-allow-list
  bill, then called `grade(r, ...)` **without** the two constants — and `grade`
  binds them as *default arguments*, which resolve at definition time. So the
  "derivation" was insulated from `SUITE_SECONDS`/`MIN_OVERHEAD_SECONDS`
  exactly like the literal it was replacing. Caught by its own second test, not
  by review; the first test (`== {"PREMATURE","OVERRUN"}`) passed the whole
  time and would have shipped it.
- 🔴 **A second self-inflicted error, same class as the first cut's**: I
  asserted the 09:00 run's clock as `9m04` from memory when the log says
  `8m34`. Both of this cycle's failures were mine and both were population/
  arithmetic slips caught by running against the live fixture.
- 🔴 **The advisory's first live reading exposes its own blind spot.** It reports
  the preceding run (12:00) as `PUBLISHED — no budgeting finding`. That run took
  **99m40**, nearly 3× the 35-min constitutional budget. The grade axis is
  publish/don't-publish, so a run that publishes *at any cost* is invisible to
  the instrument built to read budgets. Logged as Q-104 rather than patched —
  changing the axis touches every existing grade and pin.

## North-star delta

- **No movement.** Seventy-ninth consecutive instrument cycle. No planner,
  representation, or avoidance metric changed. This is executor-reliability
  infrastructure, and it is honest to call that zero north-star delta.
- The one defensible claim: cycles that read this advisory should strand less
  often, and stranded cycles are what kept D-108…D-114 off `origin` for six
  cycles. Reliability is upstream of every real number, but it is not one.

## Key learnings

- **"Derived rather than declared" is not self-verifying.** D-104's repair is
  about *watchedness*, and a derivation can satisfy the spelling while being
  insulated from the thing it derives from. Default-argument binding is the
  concrete trap; the test that catches it must perturb the input, not assert
  the current value.
- **Repairability is the right axis for gate-vs-advisory**, and it is a cheaper
  test than importance. Both readings here are true and both matter; only one
  names something the reading cycle can act on. That question should be asked of
  every new check this package adds.
- **An instrument's first live reading is worth more than its test suite for
  finding scope errors.** The suite proved the grades; one real invocation
  surfaced Q-104, which no fixture would have raised because every fixture was
  built from runs that failed to publish.

## Suite

- `sandbox:pass=1424/1424` (156 skipped, 1 xfailed, rc=0, 746 s), re-taken after
  the 4a/4a-bis writes per D-043. 1410 + the 14 tests added here.
- **Census cost nil, 37th cycle.** Every pin held at pool **91** — no new member.
  D-089's across-function rule predicted again and held: `advisory` (the function
  the module gained) branches on string equality and is invisible; `preceding`
  narrows by `g != "IN_FLIGHT"`, an inequality; `actionable`'s one membership
  test reads DERIVED because `finding_grades()` is a call. `unwatched_exemptions`
  stayed at five, which is the bill D-104's spelling exists to avoid.

## Recommended next 1–3 priorities

1. **Answer Q-104** — decide whether budget-compliance is a second axis or a
   sub-grade of `PUBLISHED`. There is now a live 99m40 `PUBLISHED` run to test
   against.
2. **Make `readings()` degrade per-guard instead of raising on the first
   unprobed guard** — still standing from D-114; measured blast radius 15 tests
   for one omission.
3. **Decide `COMPOSITION_CAP`** — the 34-min tax recurs on every test-file
   addition at generation 2, and this cycle added no new test file, so the
   cheap window is still open.

## Artifacts

- PR: #67 (already open — this branch was already in the review queue)
- Files touched: `eval/mppi_sandbox/cycle_wallclock.py`,
  `eval/mppi_sandbox/tests/test_cycle_wallclock.py`,
  `scripts/prompts/auto_research.md`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes
