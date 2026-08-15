# `K = 160` is `16/16` and spans `3.05x` — the axis is narrowest right before the cliff

- **Cycle**: 2026-08-16 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bdc5d39` [sandbox] locate-the-k-endpoints (STATE #1 — the science item)
- **Phase**: P3
- **Status**: keep

## What I tried

- Bisected D-296's remaining open upper interval `(128, 192)` at **`K = 160`**,
  `lam = 1.15`, `w = 5`, census 16 seeds on `cafe_freezing_v0` — 16 closed-loop
  runs, ~5 min.
- Shipped the column into `K_COLUMN_ROWS` and froze the seven-column grid as
  `K_COLUMN_ROWS_D296`, the same treatment D-296 gave D-294's and D-294 gave
  D-292's.
- Repointed the three D-296 tests the new column falsifies or extends; added
  four D-297 tests against the full eight-column axis.

## What worked / what failed

- **The run moved for the first time on this axis.** `K = 160` comes back
  `16/16`, so the unanimous set is **`{96, 128, 160}`**, not `{96, 128}`, and
  the upper bound is `(160, 192)` — one bisection wide. Every previous `K`
  bisection halved an interval and left the run alone; this one extended it.
- **STATE's question — is the upper edge set by spread or by membership? —
  has an answer, and it is neither, yet.** At the midpoint *neither* has begun
  to degrade. `K = 160` spans **`3.05x`**, the **tightest column anywhere on
  the axis** (`128` is `3.80x`, `96` is `5.37x`), sitting one bisection below a
  column that spans `12.19x` and is structurally disqualified by D-283. The
  spread does not widen into inadmissibility gradually — a **4.0×** jump
  happens inside a single bisection step. Calling `(128, 192)` a transition to
  be *walked* presumed a slope; it is a cliff.
- **One D-296 claim died and it is pinned, not repointed.** "Both bounds
  halved, the run is unchanged" was true of the seven-column grid and is now
  asserted against `K_COLUMN_ROWS_D296`; the falsification is its own test on
  the full grid. D-296's other two headlines are untouched — `K = 192` is
  still the interior span-inadmissible column, and membership is still
  non-monotone approaching both edges (`15, 14, 16, 16, 16, 14, 15, 11`), with
  the same two sides flagged.
- **No new payload field, deliberately.** The finding is expressible from
  `span_by_k` and `unanimous_k`, which `k_axis_bracket` already returns. Last
  cycle spent its scope cut discovering that a new reading needs a probe
  fixture that does not exist (D-295/STATE #3); this cycle avoided the class
  by not adding one. `gd.unprobed_revocable()` returns `()`.

## North-star delta

- **No obstacle, clearance, near-miss or CTE number moved.** Still one scene
  (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`, still blocked on
  PR #68 for any A/B-scene reading.
- What moved: the operating window on `K` is now **`{96, 128, 160}`** with
  bounds `(80, 96)` and `(160, 192)` — a factor-1.2 gap each side, down from
  1.2 and 1.5. The window is 1.67× wider in `K` than it was believed to be
  this morning.

## Key learnings

- **A structural disqualification is not approached — it is arrived at.** The
  D-283 span test flipped between two adjacent walked columns with the
  narrower one *below* every other column on the axis. So "where does the
  spread cross the band" is not a bisection-friendly question here: there is
  no monotone spread to bisect on, exactly as membership turned out not to be
  bisectable in D-296. Two of two searchable properties on this axis are now
  measured non-monotone.
- **The cheap grid-freeze pattern is now routine and it keeps paying.** Three
  cycles running, the falsified claim survives as a test against its own named
  grid and costs one dict literal. Nothing had to be re-argued, and nothing
  silently absorbed a column it was never about.
- **Sub-5-minute science still fits when it goes first.** 16 runs, then the
  writes. Third cycle in a row that ordering held.

## Recommended next 1–3 priorities

1. **Walk `K = 176` in `(160, 192)`** — 16 runs, ~5 min. With the span jump
   localised to one step, this asks whether the cliff is at `176` or whether
   `192`'s spread is itself the outlier; a `16/16` at `176` would put the run
   at four columns and the disqualification at a single column's width.
2. **Answer Q-160 — retire the self-blocked pins.** Unchanged from D-295 and
   still dictating this cycle's write order.
3. **Register the reprobe-block probe fixture** (STATE #3) — still blocking
   any new `DIFFERENCE`-shaped reading; this cycle avoided it by not adding
   one, which is a workaround, not a fix.

## Artifacts
- PR: #67 (open, continuing per D-140/D-269)
- Files touched: `eval/mppi_sandbox/calibrated_ladder.py`,
  `eval/mppi_sandbox/tests/test_calibrated_ladder.py`
- TSV row appended: pending
