# The clock a cycle can still act on

- **Cycle**: 2026-08-10 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-next-2` Ship `cycle_wallclock elapsed`
- **Phase**: P5
- **Status**: keep

## What I tried

- Added `cycle_wallclock elapsed`: `in_flight()` picks the unpaired tail run out
  of today's wrapper log, `budget_room()` grades the elapsed seconds into
  `SUITE_AFFORDABLE` / `SUITE_UNAFFORDABLE` / `OVER_BUDGET`, and
  `elapsed_reading()` prints one line naming how long is left to start a suite.
- `suite_deadline()` = `BUDGET_SECONDS - SUITE_SECONDS - MIN_OVERHEAD_SECONDS`
  = 1143s (19m03), derived rather than typed so it tracks a repriced suite.
- Dispatched `elapsed` **before** the branch/journal git joins in `main()`, so
  the reading is one file read; wired it into the constitution's Phase 3
  "Do the work" as the pre-suite check.
- 15 tests in a new `TestElapsed` class; full module 89 passed.

## What worked / what failed

- The reading is real and cheap: taken on this cycle at minute 4 it printed
  `SUITE_AFFORDABLE … 14m46 left to reach it` in **0.024s**, which is the
  ~0.0s STATE promised and the reason it can be polled rather than budgeted.
- It reproduces the failure it was built for: `budget_room(49*60+11)` on the
  19:00 run this cycle's REVIEW graded returns `OVER_BUDGET`, and the deadline
  it would have hit — minute 19:03 — is ~30 minutes before that run pushed.
- Two things this cycle did **not** do, and both are the honest reading rather
  than a defect: `MIN_OVERHEAD_SECONDS` is documented as a *lower* bound on
  non-suite work, so the deadline it yields is the latest arithmetic allows —
  passing it means the suite is certainly unaffordable, sitting inside it
  guarantees nothing. And a reading is not a behaviour: nothing forces a cycle
  to take it, which is the same weakness every advisory here has.
- `_clock()` had to be added — the `49m11` format was inlined in three places.
  I used it only in the new code rather than refactoring the three, to keep the
  diff at one thrust.
- **The instrument found its own constant stale on the cycle that shipped it.**
  This cycle's suite ran **1091.01s**, not the `SUITE_SECONDS = 717` measured
  on 2026-08-06/07 — the suite has grown 2260 → 2324 tests since. So the real
  deadline is `2100 - 1091 - 240` = **769s (12m49)**, not the 19m03 the tool
  printed. This cycle started its suite at ~6m30 and is inside both numbers, so
  nothing was mis-decided here, but the error is in the **optimistic**
  direction: a cycle starting a suite at minute 15 would have been told
  `SUITE_AFFORDABLE` and would have overrun. That is the one direction
  `suite_deadline`'s docstring claims it does not fail in, and the claim is
  true only of the arithmetic, not of the input.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics or sim code; `unsafe_rate` 0.0000 / `min_clearance` 0.3579 /
  `success_rate` 1.0000 unchanged, census attribution still 0/6.
- Twentieth-plus consecutive instrument cycle. What it buys is scope control:
  the last two cycles mis-scoped on a self-estimated clock (18:00 judged
  "~28 min" at minute 6; 19:00 blew 35 min to 49m11), and this is the reading
  that refuses that estimate.

## Key learnings

- **The two wall-clock questions have opposite gate-abilities and it is the
  same reason both times.** `review` is rc=0 because its subject already ended;
  `elapsed` is rc=0 because its subject cannot go back. Neither can be cleared,
  so neither may be a gate (D-044) — but only one of them is *actionable*, and
  that is the axis that was missing.
- **A cycle's estimate of its own elapsed time runs ~3× long** (D-154's finding
  about TSV stamps) — the same defect that made 40 rows unrepairable was
  silently pricing every scope decision. Reading the wrapper's own start line
  costs nothing and removes the estimate entirely.
- The cheap instrument was ranked #2 behind Q-129 and taking it first was the
  right call under an OVERRUN advisory: Q-129 is the larger change and is the
  one that most needs a live clock to fit inside a budget.

## Recommended next 1–3 priorities

1. **Reprice `SUITE_SECONDS` 717 → 1091 and derive it, don't type it.** The
   constant is 374s stale and wrong in the optimistic direction, which makes
   the deadline shipped today too late by 6m14. `push_preflight record` already
   writes the measured duration into every receipt — the constant should read
   the last receipt rather than carry a date-stamped literal that goes stale
   every time the suite grows. Same shape as D-047 (a set that already states
   itself, stated a second time by hand).
2. **Answer Q-129** — record the receipt's tree hash and give `changed_paths` a
   base, so D-180's diff-conditional receipt scope stops being inert. Now with
   `elapsed` available to keep it inside budget. One suite run.
3. **Point the constitution's Phase-3 pin check at `inert_surface pins`** and
   correct the stale 4a-ter prose (D-047's shape) — doc-only, unchanged for
   seven cycles.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/cycle_wallclock.py, eval/mppi_sandbox/tests/test_cycle_wallclock.py, scripts/prompts/auto_research.md
- TSV row appended: yes (`results/p3-epistemic-shadow-cost-critic.tsv`, sandbox:pass=2324/2324, keep)
- Suite: 2324 passed, 158 skipped, 1 xfailed, rc=0, 1091.01s
