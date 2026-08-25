# The island's interior rung reproduces — and one of its arms was never free to move

- **Cycle**: 2026-08-09 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — replicate `w = 100` on a disjoint seed block
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked the published band's `w = 100` rung on `cafe_head_on_v0` (λ = 0.8,
  margin 0.40 m) over **32 seeds** — D-133's block 0–15 and a fresh disjoint
  block 16–31, both arms, 64 runs. Protocol unchanged from D-151/D-152,
  including re-walking the old block first as the entitlement check (D-139).
- Recorded the 64 clearances as `W100_CLEARANCES`; added `w100_reproduction()`
  and the census row. Coverage 2/4 → **3/4**.
- Shipped `SeedBlock.censored` / `.censoring` after the data made it necessary:
  the constants `FLOOR` / `CEILING` / `UNCENSORED` / `ONE_ARM_CENSORED` /
  `BOTH_ARMS_CENSORED`. 8 new tests (32 → 40 in the file).

## What worked / what failed

- 🟢 **The reference block reproduced D-133 exactly on both arms** — stock
  16/16 sub-margin, risk 6/16. Third walk in three cycles where the
  entitlement check passed; the pipeline is not drifting.
- 🟢 **The rung reproduced and the island survived.** Fresh block: stock
  **16/16**, risk **2/16** — `SEPARATED`, same direction. Pooled n = 32: stock
  32/32, risk 8/32, `separation_runs` **24**, the band's widest separation.
  This is the rung where a reversal would have *split* `{75, 100, 150}` rather
  than trimmed an edge, which is why it was picked ahead of `w = 75`.
- 🔴 **But `stock_mppi` was never free to move.** Its rate is 1.0 in *both*
  blocks — the best stock run anywhere in the 32 is **0.3705 m**, still under
  the margin — so it did not replicate so much as have nowhere else to be, and
  the entire separation is carried by the risk arm. `REPRODUCED` here is a
  statement about one arm, not two. That is what `censoring` now names, and it
  applies to `w = 250` too (stock 0/16, a `FLOOR`): of the three replicated
  rungs, **only `w = 150` is a two-sided test of both arms**.
- 🟡 **The effect size moved the *other* way this time.** At `w = 150` the
  separation shrank between blocks (stock 10/16 → 5/16), which alone reads as
  regression to the mean; here it **grew** (risk 6/16 → 2/16). Two rungs moving
  opposite directions makes "the verdict grades sign, not size" a property of
  the grade rather than an apology for one unlucky walk. Pinned in its own test.
- 🟢 **The census got its third row and stayed uncomfortable**: 3/4 covered,
  `held (100, 150)`, `overturned (250,)`, `unreplicated (75,)`. Reported, never
  thresholded (`one_run_rungs` discipline). `w = 75` is the last rung nobody
  has looked at twice.
- 🟡 **I mis-stated the walk's cost mid-cycle and caught it off the file
  timestamps.** The 64 runs took **~3 min** (09:02 → 09:05:26), not the ~18 min
  I had written into this journal from a wall-clock feeling; the `w = 150` walk
  is on record at ~9 min, so if anything this rung was *cheaper*, and the
  "near-misses make episodes longer" story I had attached to it was invented.
  Two unreliable readings crossed: elapsed time inside a cycle is not something
  to estimate, and a cost comparison against another cycle's prose figure is
  not a measurement either. Corrected before the suite receipt was stamped.

## North-star delta

- The mechanism's evidence base is now 3 of 4 separated rungs replicated, and
  the strongest of them holds at n = 32: `risk_mppi` 8/32 sub-margin against
  `stock_mppi` **32/32**, all 64 runs reaching goal.
- No new safety/tracking dynamics: headline stays `unsafe_rate` 0.0000 /
  `min_clearance` 0.3579 / `success_rate` 1.0000 over 5 cells / 40 seeds.
- Calibrated coverage unchanged (60 arm-cells, 5 weights) — bought seeds again,
  not weights.

## Key learnings

- **A rate at 0 or 1 is not a strong result, it is a censored one.** The
  replication programme has been reading `REPRODUCED` as "both arms behaved the
  same way twice", and at two of its three rungs one arm had no room to behave
  any other way. This was invisible for two cycles because the verdict and
  every other field read identically under censoring.
- **Interior vs edge is the right way to order a replication queue.** `w = 150`
  could only trim the island; `w = 100` could break it. Picking by what a
  negative result would *cost* beat picking by rung size.
- **Do not estimate elapsed time from inside the cycle.** I wrote a ~18 min
  walk cost and a mechanism for it into this journal; `ls --time-style` said
  ~3 min. The reflex to explain a number should fire *after* reading it, and
  `cycle_wallclock` exists precisely because in-cycle time perception is bad.

## Recommended next 1–3 priorities

1. **Replicate `w = 75`** — the last unreplicated rung; closes the census to
   4/4 and it is the *lower* edge of the island. ~64 runs, ~3–9 min.
2. **Fix `shift_census`'s absent-cell path (Q-121)** — unchanged for six
   cycles; needs `shift_census` promoted to a dataclass.
3. **Walk `gap_gated_mppi` at `w = 75`** — first weight contrast for D-146's
   column; widens `COMPARED_ARMS` to three. ~512 runs, ~6 min.

## Artifacts

- PR: #67 (open, continued per D-140)
- Files touched: `eval/mppi_sandbox/separation_reproduction.py`,
  `eval/mppi_sandbox/tests/test_separation_reproduction.py`,
  `docs/decisions.md`
- TSV row appended: yes
