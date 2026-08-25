# Two axes because two questions — and the day's log proved it by disagreeing with itself

- **Cycle**: 2026-08-07 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — answer Q-105 (issued as `Q-104`): is budget-compliance a second axis or a sub-grade of `PUBLISHED`?
- **Phase**: P5 (first cycle of P5 by the date→phase map; the work is still P3-era instrumentation)
- **Status**: keep

## What I tried

- Implemented Q-105's lean **(b)**: `budget_grade` as an axis *independent* of
  `grade`, with `BUDGET_SECONDS = 35*60`, `WITHIN_BUDGET`/`OVER_BUDGET`/`UNKNOWN`.
  The existing grade vocabulary is untouched — a test pins that.
- Made the axis a **measurement rather than a rule**: `parse_skips` reads the
  wrapper's `executor already running; skipping this tick` line and `displaced`
  attributes each skipped tick to the run holding the lock.
- Wired the clause into `advisory` (all grades, not just `PUBLISHED`) and a
  second summary line into `report`. 21 new tests.
- Repaired an **ID collision**: `Q-104` was issued twice on the same day.

## What worked / what failed

- ✅ **The decisive evidence is a disagreement, not an argument.** Run against the
  full 2026-08-07 log, the `grade` axis says `budget-exhaustion hypothesis:
  NO_EVIDENCE` (PREMATURE=0, OVERRUN=0) — completely silent about budgets. The
  budget axis on the *same log* finds **OVER_BUDGET=5 of 15**. If one were a
  refinement of the other this could not happen. That is a stronger warrant for
  (b) than the reasoning that motivated it.
- ✅ **`flock -n` makes the attribution exact rather than statistical.** A tick can
  only print the skip line if some run held the lock at that instant, and the
  brackets say which. The 12:00 run (99m40) **deleted the 13:00 cycle**. So the
  advisory says "1 cycle that never ran", not "over budget" — the first invites
  *so what, it published*; the second does not.
- 🔴 **My own test asserted `OVER_BUDGET=1` and the instrument corrected it to 2**:
  the 11:00 run was 39m40, also over. I had eyeballed the log for the dramatic
  99m40 and missed the mundane violation four lines up. Kept the correction
  visible in the test comment.
- 🔴 **`grade` is not stable over time and I only saw it because I re-ran it.**
  `published_hours` is evaluated *now*, so 12:00's retroactive strand clearing
  re-graded 03/07/09:00 from `PREMATURE` to `PUBLISHED`. D-113's `MIXED`
  verdict, recorded this morning, **does not reproduce** against the same log.
  Wall clock never changes, so the budget axis is stable — a third independent
  argument for separating them, and new **Q-106**.
- 🔴 Two `Q-104`s existed: 11:00 (`fed40b6`) and 14:00 (`e2c6dd2`). The
  "strict increment" convention fails against a *prepend* procedure that only
  looks at the top of the file. Renumbered the later one to `Q-105`.

- 🔴 **The census bill was not nil, and I bought it knowingly.** Pool 91 → 92:
  `over_budget_grades` entered because it is spelled as a set difference.
  D-115's `finding_grades` solves the same problem and did *not* enter — it is a
  plain comprehension. The subtraction is what makes the derivation falsifiable
  (an inverted comparison flips the set instead of renaming its member), so this
  is the first of the 38 consecutive entries where **the syntax that makes a
  derivation testable is the same syntax the census detects**. That is a trade,
  not an accident. `unwatched_exemptions` stays at five.
- 🔴 **The full suite went red at 1 failure and the receipt wrapper hid which one** —
  `push_preflight record` reports only counts, so finding it cost three narrowing
  runs. The failing test was the census pin, which is the *expected* bill; the
  cost was entirely in locating it.

## North-star delta

- **Zero.** No planner, representation, or avoidance metric moved. This is
  executor-reliability instrumentation, same as the six cycles before it.
- Indirect and now *quantified*: over-budget cycles cost real cycles — 1 destroyed
  today out of 15, with 5 runs over. That is the first time this cost has been a
  number rather than a worry.
- The merge queue (6 PRs, 26 days) remains the only thing between this project
  and a real avoidance number. Unchanged by this cycle and unchangeable by it.

## Key learnings

- **The strongest evidence that two things are different axes is finding a case
  where they disagree.** I could have shipped (b) on the Q-105 reasoning alone;
  running it against the whole day gave a fact instead of a preference.
- **Make a compliance signal report its externality, not its violation.** The
  displaced-tick count is what makes this axis unarguable, and it was available
  in the log the whole time.
- **A test that asserts the current value would have shipped D-115's defect
  again.** `test_over_budget_grades_tracks_an_inverted_comparison` perturbs the
  predicate; the value-asserting test beside it passes either way.
- **Instrument gradings can be retroactively rewritten by unrelated repairs.** Any
  verdict this module recorded is a claim about *when it was asked*.

## Recommended next 1–3 priorities

1. **Answer Q-106** — mark per-axis stability in the reading, or persist gradings.
   D-113's `MIXED` currently does not reproduce and nothing says so at the callsite.
2. **Answer Q-104 (the surviving one)** — the 34-min `OVERRUN` mode: raise the
   budget or take the suite off the critical path. Today added 5 more over-budget
   runs to its sample, so the "sample is only 2" objection is gone.
3. **Make `readings()` degrade per-guard** — measured blast radius 15 tests for one
   omitted probe registration.

## Artifacts

- PR: #67 (already open — this branch is in the review queue)
- Files touched: `eval/mppi_sandbox/cycle_wallclock.py`,
  `eval/mppi_sandbox/tests/test_cycle_wallclock.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes
