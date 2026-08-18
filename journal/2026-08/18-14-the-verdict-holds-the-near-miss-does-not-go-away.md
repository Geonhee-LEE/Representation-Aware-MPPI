# The verdict holds; the near-miss does not go away

- **Cycle**: 2026-08-18 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-take `obstacle_crossing` at 16 seeds
- **Phase**: P3
- **Status**: keep

## What I tried

- Re-ran `retake_observables(seeds=16)` — 80 rollouts per arm, **152.9 s** — and
  recorded the result as `OBSERVED_16` / `CAUSAL_OBSERVED_16` beside the
  eight-seed tables rather than replacing them.
- Re-read the grade at 16 seeds through a **parallel** walk
  (`_visibility_from` / `_invisibility_reason_from`) instead of re-plumbing
  `scene_visibility` / `invisibility_reason`, so the control and the treatment
  do not share code. The equivalence is asserted, not assumed.
- Re-measured `deletion_fragile_negatives` on the 16-seed tables and added the
  intersection accessor `persistently_fragile_negatives`.

## What worked / what failed

- **The verdict holds.** `obstacle_crossing` is still `no_gap_anywhere` at 16
  seeds, and so is `convoy`. The invisible class has **two structural
  members**, not one — D-341's conclusion does not rest on a coin flip.
- **The re-take moved a scene it was not run for.** `freezing` goes
  `index_fragile` → `invisible` (`oracle_only`). It is the *only* grade in the
  census that doubling moves, and it is the class D-341 treated as the least
  interesting one.
- **The fragile population did not shrink — it churned.** Four
  deletion-fragile negatives at eight seeds, four at sixteen, half the
  membership new. More data did not settle the near-misses.
- **The motivating entry survived both.** `obstacle_crossing` / `lateralness`
  at first detection is fragile at 8 *and* 16. Persisting across a doubling is
  the opposite of sampling noise — so its verdict is stable while its margin
  stays one deletion from flipping. Both are true; quoting either alone
  misreads the scene.
- The 8-seed control walk reproduced all five recorded grades on the first run,
  so the parallel implementation is not silently a different rule.

## North-star delta

- **The branch's negative is now load-bearing rather than provisional.** The
  claim "three of five scenes are invisible to plan-time observables" survives
  a doubled sample on the two members that carry it.
- No planner movement. This is still representation *measurement*, not a
  controller change — but it is the measurement the last seven cycles were
  circling, and it is now settled in the direction that makes the negative
  quotable.

## Key learnings

- **Deletion and doubling are not two views of the same question.** Deleting a
  seed can only shrink a range, so it can only ever manufacture separations —
  it is one-directional by construction. Doubling is the only one of the two
  that can move a verdict either way, and it is what actually answers
  "is this the sample or the scene".
- **A stable count is not a stable population.** The fragile set stayed at four
  across the doubling and swapped half its members; a pin on the count would
  have been green through a 50% turnover. D-343 already chose populations over
  counts for this reason and the choice paid out one cycle later.
- **Parallel-implement, then assert equivalence, beats refactoring the
  control.** Re-plumbing `scene_visibility` to reach a new seed count would
  have put every existing pin on the same code as the new claim. A second copy
  plus one control test kept them separable and cost ~10 lines.

## Recommended next 1–3 priorities

1. **Ask why `freezing` alone is seed-unstable** — it is the one grade doubling
   moves, and `ttc@fixed_time` is its fragile entry at 16. Zero rollout cost
   against the tables now recorded.
2. **Stop re-taking.** The churn result bounds what a further count buys; the
   next question is a richer observable, not more seeds of these six.
3. **Close the `consumer_reach` gap in `census_preempt`** — carried from 12:00,
   still uncovered, and it has cost two red receipts.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/test_scene_separability.py
- TSV row appended: pending
