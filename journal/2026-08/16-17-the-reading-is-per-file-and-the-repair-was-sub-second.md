# The strand was budgeted at 12 minutes and cost 0.44 seconds

- **Cycle**: 2026-08-16 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39` clear-the-strand-and-repin-loop-reach
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` fired rc=1 naming the 16:00 journal, so per D-112
  this outranked the decision tree and was the whole cycle. Three commits
  (`84b7600`, `81625ed`, `7f3955d`) sat local against an `origin` at `05a3a07`.
- Re-ran the two pin files first to find out what was *actually* red. STATE said
  two pins; only **one** was — `81625ed` had already repaired
  `test_key_discrimination`, and the surviving failure was exactly
  `test_loop_reach::test_recorded_reading_covers_exactly_todays_targets` with a
  one-element diff: the new D-304 test missing from `READING`.
- STATE's budget note said the repair needs `loop_reach report`, a **full corpus
  pass** it timed at ~12 min and warned never to start late in the budget. I did
  not run it. `READING`'s own comment on the D-301 row records that its `n=2` was
  taken with `run(paths=...)` **scoped to the ladder test file** (D-079) — the
  same file this cycle needed. So I took the scoped reading instead.
- Validated the scoping rather than assuming it: the same scoped run re-graded
  the file's **eight already-recorded rows** and compared them against `READING`.

## What worked / what failed

- **8/8 recorded rows reproduced at their recorded grade and count** — `n=2`,
  `16`, `3`, `7`, `3`, `3`, `2`, `2`, every one `SAMPLED`. The scoped read is not
  an approximation of the corpus read for this file; it is the same numbers.
- The new target graded `SAMPLED n=2` and the `2` is exhaustive, not sampled:
  the loop is `for cols, need in ((sub16, 16), (K_COLUMN_ROWS_N32, 32))` and the
  matched grid has columns for exactly those two ensemble sizes.
- **The cost estimate was wrong by three orders of magnitude.** The scoped
  measurement is **0.44s**; the ladder file underneath it is 180 tests in
  **0.11s**, because they are assertions over precomputed tables and run nothing.
  The docstring's "~90 s" and STATE's "~12 min" are both about the *corpus*, and
  neither is what the repair needed.
- So the thing that stranded a cycle — the report that "was still running when
  the deadline passed" — was avoidable at the moment it was started, not by
  working faster but by scoping it to the one file that had changed.
- Pin verified green: `test_loop_reach.py` 29 passed.

## North-star delta

- **No movement in any robot-facing number, and none was reachable.** Zero sim
  runs, one scene, still blocked on PR #68 for any A/B reading. This was strand
  repair, which is upkeep.
- What did move: three commits of real D-303/D-304 findings went from local-only
  to pushed, i.e. from invisible to reviewable. That is the strand's whole cost
  and it is now paid.
- A recurring per-cycle tax dropped from "budget 12 minutes, or strand" to
  "0.44s" — the first thing this cycle produced that compounds.

## Key learnings

- **A guard that names an expensive repair is worth re-costing before paying
  it.** The failing assertion's message says "re-run `loop_reach report`", and
  both the docstring and STATE agreed. All three describe the corpus-wide
  operation; none of them is the cheapest operation that clears the assertion.
  The pointer to the cheap path was already in the codebase — in the comment on
  the row directly above where the new row goes.
- **Scoping a measurement is a claim, and it is checkable for free.** The
  reproduction of eight recorded rows is what separates "I measured a subset"
  from "I guessed the subset was representative". D-079 said don't type the
  count; the same logic says don't type the *scope's validity* either.
- The limits are real and I would not generalise past them: this holds because
  grades are per-`(file, line)` counts over targets in that file. A file holding
  a `SLOW_ONLY` row needs `extra=('-m','slow')` or it reads `NOT_RUN`, and a
  target whose loop count depends on cross-file state would not be scope-safe.
  The 8/8 reproduction is evidence for this file, not a theorem.
- STATE said "2 pins red" and one was already fixed. Reading the actual failure
  before planning the repair cost 142s and removed half the assumed work.

## Recommended next 1–3 priorities

1. **Respan `K = 128` at 32 seeds** — D-304 made this the *prerequisite*, not the
   follow-up: it is the only thing that makes the attribution re-read
   expressible. ~17 runs, ~2 min. Now unblocked, the strand is clear.
2. **Then re-read the consumers on the 4-column matched grid**, using D-304's
   control pattern (same columns, different `n_required`).
3. Unchanged from D-295, twelve cycles running: answer Q-160 (retire self-blocked
   pins). This cycle is the second consecutive one where a self-caused pin was
   the entire agenda.

## Artifacts

- PR: #67 (open)
- Files touched: `eval/mppi_sandbox/loop_reach.py`, `docs/decisions.md`, `journal/2026-08/16-16-the-regrid-is-the-prerequisite-not-the-repair.md`, `journal/2026-08/16-17-the-reading-is-per-file-and-the-repair-was-sub-second.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
