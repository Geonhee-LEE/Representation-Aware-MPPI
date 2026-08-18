# The census that was in neither list

- **Cycle**: 2026-08-18 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `census-preempt-consumer-reach` Close the `consumer_reach` gap in `census_preempt`
- **Phase**: P3
- **Status**: keep

## What I tried

- Added a fifth census to `census_preempt`: `consumer_reach_residue`, which
  re-derives both dead-code residues (`findings()` and `module_findings()`) and
  reconciles them against the list literals that pin them in
  `test_consumer_reach.py` — parsed out of the assertions, never restated (D-047).
- Gave it the four tampers the module's own docstring requires of every entry:
  entrant, departure, per-population separation, and fail-closed on a missing pin.
- Widened `Reading.line()`'s census column 18 → 22; the new name overflowed it.

## What worked / what failed

- The census reads **CLEAN at 16 pinned residue entries across 2 populations**
  and costs ~1.9 s, taking the whole pass from ~2 s to 3.9 s against the ~19 min
  suite it pre-empts.
- The two populations genuinely need separate pins: a definition can be
  unreached at function scope while its module is reached. Suffix matching would
  have let `module_findings` answer for `findings`, so `_calls_exactly` matches
  the call name exactly and a test asserts the two literals differ.
- **The gap was worse than an omission.** `consumer_reach` was in neither
  `CENSUSES` nor `UNCOVERED`. D-318 tells readers to read the `Not covered:`
  line to learn the pass's scope; a reader who did was still not told this one
  was absent. An admitted omission is a work list — an unlisted one is invisible.
- Wall clock: the elapsed reading said `SUITE_AFFORDABLE` with 10m11 to reach
  the suite-start mark, and the edit + tampers took ~19 min. I missed the mark
  and knew it at minute 14, but the suite cost is fixed for any push, so cutting
  scope after that point could only have cut the deliverable, not the clock.

## North-star delta

- No planner movement — this is verification-surface infra, honestly zero on the
  north star's measured numbers.
- It buys cycle time back: this exact census cost the branch two red receipts,
  one of them 1305 s at 12:00. A 1.9 s derivation now stands where a 20-minute
  red suite did.

## Key learnings

- **A census in neither list is strictly worse than one in `UNCOVERED`.** The
  scoped-out list is what makes a clean reading legible; absence from both makes
  the clean reading *look* total. That is the D-317 failure shape one level up,
  and it survived D-318 naming the hazard.
- **The fix for "narrower than it looks" has to be exact-matching.** Writing
  `endswith("findings")` inside the repair would have reproduced the defect it
  repairs — one pin silently covering two populations.
- Populations, not counts, again paid off (D-343): the DRIFT line names the
  entrant, so the repair direction is readable without re-deriving anything.

## Recommended next 1–3 priorities

1. **Ask why `freezing` alone is seed-unstable** — the one grade the doubling
   moved; zero rollout cost against `OBSERVED_16`/`CAUSAL_OBSERVED_16`. Carried
   unshipped from 14:00 and still the bottleneck's own question.
2. **Audit the remaining composite magnitude pins** — D-342's failure mode is a
   bound hand-tightened onto a two-ended quantity. Carried from 11:00.
3. **Re-derive `UNCOVERED` itself** — this cycle found a census in neither list
   by hand. Whatever found it should stand somewhere.

## Artifacts
- PR: #67 (already open — no new review bandwidth, D-140)
- Files touched: eval/mppi_sandbox/census_preempt.py, eval/mppi_sandbox/tests/test_census_preempt.py
- TSV row appended: yes
