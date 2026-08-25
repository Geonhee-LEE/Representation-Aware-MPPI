# A census repair is itself a census-moving event — so the pre-empt has to be taken twice

- **Cycle**: 2026-08-17 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-81e6` [sandbox] grep-the-axis-for-min-max-interval-assumptions
- **Phase**: P3
- **Status**: keep

## What I tried

- Phase 1's `cycle_artifacts stranded` fired rc=1 for the second consecutive
  cycle, now naming **two** journals (00:00 and 01:00) and warning that one tree
  was never graded. That outranks the decision tree, so this cycle picked nothing
  new — it finished the strand.
- The 01:00 cycle left a diagnosis rather than a receipt: three named tests, one
  root cause. Fixed all three — `REGISTRIES` 11 → 13 (D-313 added two entries),
  the `NOT_PATHS` layer 4 → 5, and the running guard tally 116 → 119.
- Took the one-line `guards()` self-membership pre-empt that two consecutive
  STATE files recommended — and took it **twice**: once against D-312's module,
  once against my own repair.

## What worked / what failed

- **The second reading is the one that mattered, and it is the half both prior
  cycles missed.** D-313's failure was not carelessness — it fixed all seven
  first-order tallies correctly, and the fix *was* the next event: growing
  `REGISTRIES` by two is exactly what the three surviving pins read. Running the
  check against the repair costs 0.3 s and answers "does the ripple continue".
  Here it does not: `pool 119 / REGISTRIES 13 / NOT_PATHS 5` are identical before
  and after my edits, because the repair touches test files only. **I knew the
  ripple stopped at frame 2 before spending the suite**, instead of after.
- **Pinning `NOT_PATHS` by name instead of by count paid immediately.** D-313's
  two-entry repair **split across two layers** — `SITE_CLASSES` into `NOT_PATHS`,
  `HULL_REPAIRED_BY` into `NO_REGISTRY`. A count pin would have read "5" and
  silently implied both landed here.
- **The AND set held at ten, and the usual coda would have called that "second-
  order cost nil". It was not.** None of D-312's three guards is `&`-shaped, but
  2 of 3 route to masking (20 → 22), unwatched went +2, `REGISTRIES` +2,
  `NOT_PATHS` +1. The five preceding entrants (all `calibrated_ladder`) were
  genuinely nil. An auditor cannot enter this pool cheaply — it has to name what
  it lets through, so its exemptions are typed by construction.
- Wall-clock discipline worked this time: `cycle_wallclock elapsed` read
  `SUITE_AFFORDABLE` with a start-by deadline, and I ran no parallel probes
  against the suite (the self-inflicted 4 min that cost 01:00 its push).

## North-star delta

- **No movement toward the north star.** Zero closed-loop runs; no controller,
  cost, or representation code changed. This is verification-surface repair.
- What it does buy is that **D-312's and D-313's science reaches `origin`** after
  two cycles stranded — four commits, and the branch's `K`-axis work can resume
  from main-visible state rather than from a local pile.

## Key learnings

- The recurrence this package has recorded twenty-odd times ("an instrument built
  to audit a population becomes a member of one") has a **second frame nobody was
  reading**: the *repair* is a member too. Twenty instances of the lemma and the
  fix loop still only ever applies it once.
- A guard census's cost should be read on four axes (AND-shape, masking,
  unwatched, registry layers), not on the AND set alone. Reading one axis is how
  "cost nil" got written five times running and then was wrong on the sixth.
- Two consecutive cycles recommended the pre-empt and neither made it standing;
  it took a third cycle paying the same bill to write it down as a decision
  (D-314) rather than a recommendation. A lesson repeated in prose is not a step.

## Recommended next 1–3 priorities

1. Return to the `K`-axis question the branch is actually about — three cycles
   have now gone to the census, and D-312 retired the bottleneck that justified
   the detour.
2. Answer Q-090 with Q-161 (both ask "add an axis/verdict to the scan?"). First
   count how many of the 8 unwatched lists are reconciled in both directions —
   pure reading, no sim.
3. Move the two-reading pre-empt from D-314 into `CLAUDE.md`'s EXECUTE step so it
   is a step rather than a decision entry.

## Artifacts
- PR: #67 (open) — `autoresearch/p3-epistemic-shadow-cost-critic`
- Files touched: eval/mppi_sandbox/tests/test_exemption_control.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, eval/mppi_sandbox/tests/test_liveness_derivation.py, docs/decisions.md
- TSV row appended: yes (`sandbox:pass=3433/3433`, status=keep)
- Receipt: `3433 passed, 1 xfailed, 163 skipped in 948.88s across 14 shards`, rc=0 — green, after 7 red (D-312) and 3 red (D-313)
