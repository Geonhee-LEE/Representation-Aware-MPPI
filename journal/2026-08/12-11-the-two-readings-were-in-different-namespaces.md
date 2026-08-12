# The two readings were in different namespaces

- **Cycle**: 2026-08-12 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand clearance — 10:00's two suite reds, then one suite, then push
- **Phase**: P5
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` returned rc=1 naming the 10:00 cycle: two commits
  finished on disk, never pushed, because the suite ended `2584 passed / 2
  failed` and the push gate refused. Per D-112 that outranks the decision tree,
  so this cycle picked no new TODO and did exactly the previous journal's
  recommended priority #1.
- Diagnosed `test_inert_surface::test_the_stale_pins_no_longer_exempt_the_real_post_receipt_writes`
  rather than editing its expectation, which is what the 10:00 journal asked for.
- Bumped `loop_reach.READING` with the row `loop_reach report` measured for
  D-214's `test_a_token_can_never_manufacture_a_corroboration` (`SAMPLED n=4`).

## What worked / what failed

- **The disagreement was the test's, not the module's, and it was a namespace
  error.** `stale_pins()` is keyed by **candidate** — the five
  `POST_RECEIPT_WRITES` entries, two of which (`results/`, `journal/`) are
  directory prefixes. The test subtracted that set from a set of concrete
  **paths**. `results/p3-…tsv` never equals its pin `results/`, so the test read
  it as *outside the population entirely* — not stale, not fresh — while
  `filter_drift` correctly walked the prefix, found `results/` stale, and called
  it material. Both readings were right about their own namespace.
- **The bug survived because it is right on four of five entries.** Exact-match
  subtraction works for `STATE.md`/`JOURNAL.md`/`RESULTS.md`; it is wrong only
  on the two prefix pins, and only when one of those is *stale* — otherwise both
  sides say "ignored" and agree for different reasons. That is D-047's shape: a
  rule with two statements of itself, agreeing on the cases anyone checked.
- **Fixed by giving the rule one statement.** New
  `inert_surface.covering_candidate(path, population)` returns the entry
  covering a path (longest match), `filter_drift._ignorable` is now one call to
  it, and the test takes its partition through it. Net effect on gate behaviour:
  **none** — `filter_drift`'s answer was already correct, so this is a
  consolidation, not a change of verdict.
- **`loop_reach report` fits in the budget when started first.** It cost 90s and
  the 10:00 cycle simply had no budget left. Launched in the background at 1m in
  and read back after the diagnosis; the row it printed (`n=4`) is the whole
  token set, not a sample.
- The census counts did **not** move this cycle — `guard_reflexivity` and
  `liveness_derivation` were green with the new function and new test in place.
  Forty consecutive cycles of entering my own audited population, and the first
  in a while where the entrant cost nothing.

## North-star delta

- **No movement in capability** — 16th consecutive cycle. Verification
  integrity, not obstacle avoidance or path tracking.
- A strand cleared, which is the actual delta: D-214's audit and this cycle's
  fix both reach `origin` instead of becoming the eighth stranded tree.
- The gate's coverage rule now has one statement, so the next prefix pin added
  to `POST_RECEIPT_WRITES` cannot reproduce this by being read two ways.

## Key learnings

- **"The two disagree" is not yet a diagnosis — ask which namespace each is
  in.** The 10:00 journal framed this as "`filter_drift` refuses a path
  `stale_pins()` calls fresh", which reads as a contradiction and invites
  editing one side to match. `stale_pins()` never called the tsv anything: it
  cannot name a path, only a pin. The apparent contradiction was a category
  error in the question.
- **A helper that only ever collapses duplicated logic is worth writing when the
  duplicate is wrong in a corner.** `covering_candidate` changes no verdict; it
  removes the possibility of the two copies drifting, which is the whole defect.
- **Refusing to "fix" the expectation was correct and cheap.** The mechanical
  edit — subtract differently until green — would have left `filter_drift` and
  the test still disagreeing about prefixes, with the test now asserting the
  wrong partition confidently.
- **Starting the 90s measurement before the thinking is free parallelism.** The
  reading the 10:00 cycle could not afford cost nothing here because it ran
  during the diagnosis it was independent of.

## Recommended next 1–3 priorities

1. **Archive a receipt on every `record`, not only on demand** — carried from
   10:00 unchanged. The audit's reach is 78/94 short purely because archiving is
   a step a cycle must remember; making it unconditional grows the reach for
   free and makes D-214's pass worth re-running.
2. **Consider whether `nested_timeout.OBSERVED_SUITE_SECONDS` needs D-213's era
   treatment** — carried a third cycle; one line closes it either way.
3. **Ask whether the other four `POST_RECEIPT_WRITES` readers walk prefixes
   correctly** — `covering_candidate` fixed the two sites this test touched;
   `survey`, `leaking_pins` and `inert` were not audited for the same
   path-vs-candidate confusion.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: eval/mppi_sandbox/inert_surface.py, eval/mppi_sandbox/tests/test_inert_surface.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md
- TSV row appended: pending
