# The count was computed on every walk and thrown away by `all()`

- **Cycle**: 2026-08-11 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — record the two refused walks' per-seed ESS
- **Phase**: P3
- **Status**: keep

## What I tried

- Screened STATE #1 against its estimator's signature before planning the
  recovery — the step D-186 made a rule after three cycles of wrong-direction
  pricing. The screen passed on the first question (`out_of_band` really does
  consume per-seed ESS) and then failed on the second: **`ab.summarize`
  already computes the count.** Line 235 builds `per_seed_band`, a list of 32
  per-seed booleans, and `all()` collapses it to one bool on the way out.
- So the missing quantity was never on the far side of a sim run. `k` existed
  in memory on every walk this branch has taken and was discarded by the
  aggregation, which is why `geometric_null`'s two refused rungs carry
  `ess_in_band=False` and nothing else.
- Shipped `SweepStats.n_in_band` (+ derived `n_out_of_band`), populated from
  the same list, sticky-`None` on the same rule as `ess_in_band`, with a
  `__post_init__` that refuses a record whose count and verdict disagree.
- Shipped `WalkCount.from_sweep`, which returns `COUNT_EXACT` when the walk
  kept its count and otherwise degrades to the flag's asymmetric bounds.

## What worked / what failed

- A counted refusal now pools as a **point**: `pooled_reading` on a 3/32
  counted walk reads `POOLED_IDENTIFIED`, the verdict that was unreachable by
  any action before this cycle (D-138's shape — a reader-only state).
- The historical half **failed, and stays failed**. The two refused rungs
  discarded their counts at walk time; no re-read reaches them.
  `recorded_pooled_reading()` is still `POOLED_FLOOR_ONLY` and a test now pins
  that it is. STATE priced this ask as "re-read of runs already taken, 0 new
  sim" — it is a **re-walk**, 64 closed-loop runs, and that is a different
  price than the one on the plan.
- Prose was ambiguous exactly where it mattered: `LOUDER_NULL` says "8/8 seeds
  were in band on the calibration ensemble and 32/32 were not on the walk",
  which reads as either `k = 1` or `k = 32` — the two **ends** of the
  identified set. The module was already right to refuse comments as
  measurements.
- `None` needed its own source: an unmeasured walk does not even pin `k ≥ 1`,
  so folding it into the refused case would have read weaker evidence as
  stronger. `FROM_FLAG_UNKNOWN` keeps them apart.

## North-star delta

- No movement, and this cycle claims none. No controller, representation, or
  dynamics code; `unsafe_rate` / `min_clearance` / `success_rate` unchanged;
  0 sim runs; census attribution coverage still 0/6.
- What moved is prospective: the next walk taken on this branch identifies its
  own rate instead of bounding it. The 0/6 coverage problem is not fixed, but
  it stops compounding.

## Key learnings

- **Screening the estimator's signature is necessary, not sufficient.** D-186's
  rule asks what the estimator consumes. It does not ask whether the producer
  already computes it. Both questions are free; this cycle needed the second.
- **A conjunction discards its own witness.** `all()` over a per-seed predicate
  is the exact point where a magnitude becomes a direction. Any place this repo
  reduces a per-seed list to one bool is a place a future cycle will be unable
  to quote a rate — worth a sweep for other instances.
- **Four for four on cheap-direction pricing**, and this one is the cheapest
  yet: the ask was sized at "recover floats from disk" when the true fix was
  one `sum` at the producer. The pattern is now costed as prospective-vs-
  historical, which is the distinction the plan kept eliding.

## Recommended next 1–3 priorities

1. **Sweep for other `all()`-over-per-seed reductions** that destroy a count
   the same way (`assert_all_reached` / `all_reached` is the obvious next one —
   it is the other half of the same admissibility gate).
2. **Decide whether the two refused rungs are worth re-walking** (64 runs) now
   that the price is stated honestly. If yes it is a user-run, not an executor
   one — it exceeds the 2-min sim limit.
3. **Point the constitution's Phase-3 pin check at `inert_surface pins`** —
   unchanged, doc-only, now thirteen cycles old.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/ab.py, eval/mppi_sandbox/seed_count_licence.py, eval/mppi_sandbox/tests/test_seed_count_licence.py, docs/decisions.md, journal/2026-08/11-03-the-count-was-computed-then-discarded.md
- TSV row appended: pending
