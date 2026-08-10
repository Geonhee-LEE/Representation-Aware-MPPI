# The rung carries its own seed count — and both walked rungs select through the looser gate

- **Cycle**: 2026-08-11 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — make the census carry `n` and refuse cross-`n` comparison
- **Phase**: P3
- **Status**: in_progress

## What I tried

- `NullRung` gains `walk_n` / `ladder_n` / `selection_predicate` /
  `predicate_direction`: the seed count each admissibility predicate was taken
  at, **derived** from the recorded arrays (`len(clearances)`,
  `len(clearance_ladder[w])`) rather than stored beside them (D-047).
- `NullCensus` gains `seed_counts` / `predicate_readings` / `cross_n_selected`
  / `comparable_predicate`, read **per rung** instead of off D-184's two module
  constants, and surfaced in `__str__`.
- Six tests in `test_geometric_null.py`, including two negative controls: a
  seed-matched rung must read `SAME_PREDICATE`, and a walk truncated *below*
  its ladder must read `WALK_LOOSER` — a direction this census never produces.

## What worked / what failed

- 🟢 The reading reproduces D-184's `PREDICATE_DIFFERS_BY_N` from the rungs
  themselves: both walked rungs are `(ladder_n, walk_n) = (16, 32)`,
  `LADDER_LOOSER`, `comparable_predicate` False.
- 🟢 **`ladder_n` is read off `clearance_ladder`, not off `ladder_admissibility`
  — and that is a widening of D-184's finding.** `_ladder_arms()` truncates the
  recorded 32-seed arms to the ladder prefix, so *every* ladder verdict is
  computed at 16 seeds, not only the in-band counts. The cross-`n` conflation
  reaches `matched_verdict_identification` and hence `admissible` itself, one
  level deeper than the admissibility counts D-184 named.
- 🔴 **The guard D-184 paid for fired again on this cycle, one cycle later**:
  two of the six new tests loop over a population, so `loop_reach`'s
  `test_recorded_reading_covers_exactly_todays_targets` went red for the two
  missing `READING` rows. The ~90 s re-measurement is the price, and this is
  the second consecutive cycle to pay it — the guard is working as designed.
- 🔴 **Scope was cut on the wall clock.** `cycle_wallclock elapsed` read
  `SUITE_AFFORDABLE` with 3m02 to the deadline while the first `loop_reach`
  reading was still running; the second reading pushed the suite start past it.
  D-181's instrument did exactly its job — the overrun was seen at minute 11,
  not at minute 34.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics or sim code; 0 sim runs. `unsafe_rate` / `min_clearance` /
  `success_rate` unchanged, census coverage still **0/6** `NO_GRADED_RUNG`.
- What moved is that the census can no longer quote an admissibility reading
  without its `n`, and the one it quotes is now known to differ *in the verdict
  arms too*, not only in the in-band counts.

## Key learnings

- **A seed count read off the wrong field would have understated the problem.**
  Keying `ladder_n` to `ladder_admissibility` would report `NO_LADDER_PREDICATE`
  for a rung whose ladder verdicts are still computed on truncated arms. The
  conflation lives in `_ladder_arms`, which no admissibility constant names.
- **Replacing a correct constant is still worth doing.** D-184's
  `CENSUS_LADDER_SEEDS` / `CENSUS_WALK_SEEDS` agree with the derived reading on
  this data — that agreement is what makes the swap *safe*, not what makes it
  unnecessary. A rung walked at another ensemble size moves one and not the other.
- **Two consecutive cycles have now been caught by `loop_reach`.** The cost is
  ~90 s per cycle that adds a looping population claim, and it is worth paying;
  but a cycle that plans one should budget the reading *before* the suite, not
  discover it from a red test.

## Recommended next 1–3 priorities

1. **Decide what `comparable_predicate == False` should *do*.** It currently
   reports; `separates_scene_from_rung` downgrades the verdict. The census is
   `NO_GRADED_RUNG`, so the question is unanswerable by measurement today and
   is a design choice — a Q, not a D.
2. **Recover the two missing per-seed ESS populations** (convoy `w=75`,
   head_on `w=75`) so D-184's magnitude interval narrows from a single `k=1/32`.
   Re-read of recorded runs, no new sim.
3. **Point the constitution's Phase-3 pin check at `inert_surface pins`** and
   correct the stale 4a-ter prose (unchanged for eleven cycles, doc-only).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/geometric_null.py, eval/mppi_sandbox/tests/test_geometric_null.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
