# Both exits below the run survive the respan — and they fail differently

- **Cycle**: 2026-08-16 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39` [sandbox] respan-k64-and-k80-at-32
- **Phase**: P3
- **Status**: keep

## What I tried

- Respan `K = 64` and `K = 80` at 32 seeds (seeds `0` + `16..31`, cell
  `(1.15, 5.0)`, `PEAK_SCENE`) — 34 closed-loop runs, ~2 min. These are the two
  columns that *define* the run's exit below `96`, and after D-307 they were the
  last statements on the axis still resting on an `n = 16` ensemble.
- Recorded `MEASURED_SEEDS_32_LAM115_K64_EXT` / `_K80_EXT` + the full columns,
  extended `K_COLUMN_ROWS_N32` from 5 to 7 columns.
- Froze the 5-column grid as `K_COLUMN_ROWS_N32_D307` and repointed the D-307
  and D-308 tests there, per the precedent the TODO named.

## What worked / what failed

- **Both exits survive**: `64` → `30/32`, `80` → `29/32`. `unanimous_k` stays
  `(96, 160)`; neither column joins the run. The lower edge is now measured at
  the same ensemble as everything above it.
- **They fail by different mechanisms.** `64`'s new miss is marginal exactly as
  its `n = 16` miss was (`1.08x` under the floor vs seed 0's `1.07x`), while
  `80` picks up the **deepest floor violation on the walked axis** (seed 18 at
  `2.0596`, `1.94x` under). "Exit below" is two phenomena under one name.
- **D-303's proportionality claim gets its cleanest refutation.** `64` and `80`
  sit within `2.4%` of the same `n = 16` width (`5.139` / `5.020`) yet widen
  `x1.21` vs `x1.87`. Earlier counterexamples were non-monotone points; this is
  a matched-width pair, which no function of width alone can produce.
- **D-308's repair is stable under extension**: adding two columns below moves
  neither the verdict (`K_BRACKET_PUNCTURED_RUN`) nor the blocks `((96,), (160,))`.
- Two false starts cost ~2 min: the sweep script ran from `/tmp` (repo not on
  `sys.path`), then passed `PEAK_SCENE` as a bare string where a loaded
  `Scenario` was required. Both were harness errors, not measurement failures.

## North-star delta

- The `K` axis's lower edge is now a 32-seed reading rather than an inherited
  assertion — the bottleneck STATE has named for three cycles is closed.
- Still zero movement on obstacle avoidance or path tracking: one scene, one
  rung, one temperature, `transfers_to_ab_scene = False`. This buys confidence
  in a measurement, not robot behaviour.

## Key learnings

- Ensemble response is not a function of column width. Two columns of the same
  width responded 55% differently, which retires the last version of D-303's
  claim and means **no** column's `n = 16` span can be extrapolated.
- Extending the grid *downward* is not the lever for expressibility.
  `attribution_separability` stays `NOT_APPLICABLE`; D-306 bought a bound that
  way and D-307 lost it to the puncture — the blocker is the hole, not a bound.
- The verdict's stability under a 5→7 column extension is the first evidence
  D-308's repair describes the run rather than the grid's stopping point.

## Recommended next 1–3 priorities

- Fill the hole: respan nothing new, but ask what `K = 128`'s single-seed miss
  (`31/32`, span `10.142x` vs a `10.0x` band) needs to be decided — a third
  ensemble at `n = 48` is the only measurement that settles the puncture.
- Q-161 enumeration — `revocable_collections()` entries whose subject is not a
  repo path (carried from STATE #1, still unexecuted, zero runs).
- Grep the axis for other `min`/`max`-over-a-set interval assumptions (carried
  from 20:00; two findings of this class have now landed).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md
- TSV row appended: pending
