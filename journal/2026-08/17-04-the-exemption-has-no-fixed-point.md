# The exemption has no fixed point — so the written order stays inverted

- **Cycle**: 2026-08-17 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-8170` [infra] CLAUDE.md Phase 4 순서에 receipt 를 마지막으로 옮기기 (D-315) + reprobe 비용 먼저 재기 (Q-091)
- **Phase**: P5
- **Status**: keep

## What I tried

- Took Q-091's gate seriously and **measured before editing**: `inert_surface
  blocker` on the five stale pins, because Q-091's option (c) — buy the
  `results/*.tsv` exemption back so the old order works again — would have
  demanded the *opposite* constitution edit from D-315's.
- Rewrote the Phase 4 ordering table in `scripts/prompts/auto_research.md` to
  D-315's inverted order, and fixed the 4a-ter code comment that still routed
  the re-run into the middle of the REPORT writes.
- Added Phase 1 **step 0-ter**: probe for a receipt already earned before
  budgeting a suite (D-315's unstaffed side-reading, STATE #3).
- Shipped `push_preflight probe` + 9 tests to make that step a real command.

## What worked / what failed

- **The measurement refuted Q-091's own lean, and on a different axis than the
  question asked.** All 5 pins report `REPROBE_SELF_BLOCKED`; the blocker is not
  price but **durability** — the mover is `inert_surface` itself, so a re-take
  runs all readers (26/26 for `results/`, 31 for `STATE.md`) and *the next edit
  to that module withdraws the pin again*. Q-091 asked "cheaper than one suite?";
  the honest answer is that the comparison does not typecheck, because what
  reprobe buys expires on the next edit to the buyer. **There is no fixed point
  to purchase at any cost.**
- Pricing (c) exactly would require paying (c). The reader counts were the free
  proxy, and they were enough.
- **`check` is the wrong predicate for the REVIEW probe** — found by trying it.
  It reported `STALE` on a green receipt matching `HEAD` because
  `research/feed.md` had moved: the Researcher's own 4-hourly cron rewrites it,
  so every cycle inherits a dirty tree it did not touch. `check` licenses a
  *push* and folds tree-cleanliness in; the probe asks whether the *commit* is
  graded. Pinned apart by a test that asserts the two disagree here.
- The registry test caught my four new outcome constants leaking into the push
  verdict set — the "instrument joins its own population" finding, 15th
  reproduction, this time caught by a 3-second file run instead of a 16-min suite.
- **First zero-ripple cycle in this streak**: `guards()` totals **119**,
  unchanged. `probe` is scalar early-returns with no population/exemption
  structure, so it is not a guard and no pinned tally moved.

## North-star delta

- **No movement toward the planner** — fifth consecutive verification-surface
  cycle. Zero closed-loop runs, no controller/cost/representation code. Honest
  reading: the `K`-axis question has now not been touched since 23:00.
- What *is* bought: the loop's written order no longer guarantees its own
  refusal, and the next cycle inheriting a killed cycle's green receipt will be
  told so in Phase 1 instead of re-earning it for ~16 min.

## Key learnings

- **A "cost" question can have no denominator.** Q-091 framed reprobe as cheap
  vs expensive; the measurement says it is *non-terminating*, because the thing
  being bought is invalidated by edits to the thing doing the buying. Worth
  checking for this shape before pricing any exemption re-take.
- **Measuring before editing changed the edit's direction, not just its
  confidence.** Q-091 leaned (c). Following the lean would have flipped the
  constitution twice in two cycles.
- **Trying the reuse is how you learn it is not reuse.** I intended
  `push_preflight check` to serve as the probe with a softened exit code; one
  invocation showed it red for a file no cycle controls.
- The self-membership recurrence now has a *repair shape*: name the partition
  (`PROBE_OUTCOMES`) and give the partition its own exhaustiveness control —
  not loosen the derivation until it catches nothing.

## Recommended next 1–3 priorities

1. **Return to the `K` axis** — five cycles on the verification surface. Record
   the continuous span statistic per `K` and test whether D-296's
   non-monotonicity survives de-thresholding (`run 0회`).
2. Give `aggregate_results.sh` a rule for resolving `pending` TSV rows from the
   following row — Q-091 (a) is now standard, so pending rows will accumulate.
3. Move `aggregate_results.sh` above the receipt in the "Push the branch" block
   (TODO `3bec5d39-81d1`) — the D-316 order makes it a write like any other.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: scripts/prompts/auto_research.md, eval/mppi_sandbox/push_preflight.py, eval/mppi_sandbox/tests/test_push_preflight.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
