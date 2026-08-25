# The cliff was the gap — and both ends of the K run exit through the floor

- **Cycle**: 2026-08-16 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<walk-k176-in-the-last-interval>` (STATE #1 — the science item)
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked `K = 176` — the midpoint of D-297's remaining upper interval
  `(160, 192)` — at `lam = 1.15`, `w = 5`, census 16 seeds on
  `cafe_freezing_v0`. 16 closed-loop runs, ~90 s.
- The question STATE posed: is the admissibility cliff real at `176`, or is
  `K = 192`'s `12.19x` spread simply an outlier column?
- Added the column to `K_COLUMN_ROWS`, froze the eight D-297 columns as
  `K_COLUMN_ROWS_D297`, and repointed every statement the new column falsifies
  rather than deleting it.

## What worked / what failed

- **`K = 176` is `15/16`, span `7.74x`.** The run does **not** extend a second
  time — it stays `{96, 128, 160}` and the upper bound halves to `(160, 176)`.
- **The cliff is gone, and it was never on the axis.** `7.74x` sits between
  `3.05x` and `12.19x`, so D-297's "4.0x jump in one step" resolves into a
  monotone ramp with sub-steps of `2.54x` and `1.58x`. The jump was the width
  of a 32-wide gap. One bisection retired a structural claim made one cycle
  earlier.
- **What replaces it is sharper than it was.** `K = 176` is span-*admissible*
  (`7.74 < 10.0`) and membership-*inadmissible* (`15/16`) — the first column
  where the two disqualification mechanisms disagree. That orders them:
  membership fails in `(160, 176]`, span not until `(176, 192)`. The upper
  edge of the window is set by membership, so D-297's span framing was
  watching the boundary that comes second.
- **The structural casualty is the verdict, not the span.**
  `K_BRACKET_CLOSED_BOTH_EDGES → K_BRACKET_CLOSED_SAME_EDGE`. D-293 read the
  run as closed at *opposite* band edges (floor below, ceiling above) — the
  D-290 shape, an interval held by two different mechanisms. That reading took
  `K = 192` as the upper neighbour: a column 32 away and itself
  span-disqualified. The real neighbour, `176`, exits through the **floor**,
  same as `80` below.
- **The upper exit is confirmed in margin, unlike the lower one.** Seed 0 sits
  at `7.5295` against a floor of `8.8` — `1.17x` to re-enter, outside
  `MARGINAL_MISS_TOLERANCE`. D-293's lower exit cleared by only `1.07x` and had
  to be reported direction-only.
- `near_edge_worse_than_far` drops from `("below", "above")` to `("below",)`:
  `176` holds more seeds than `192` beyond it, so D-296's two-sided shape claim
  survives only on the grids it was read on. Non-monotonicity itself is
  untouched — the lower side alone (`15, 14, 16`) still carries it.

## North-star delta

- **No movement in any robot-facing number.** No clearance, near-miss, CTE or
  obstacle figure moved; still one scene, still `transfers_to_ab_scene =
  False`, still blocked on PR #68 for any A/B reading.
- The operating window in `K` is now `{96, 128, 160}` with bounds `(80, 96)` /
  `(160, 176)` — the upper bound is one bisection from located.
- A negative result that constrains method: the window is closed by **one**
  mechanism on both sides, not two opposing ones.

## Key learnings

- **A "cliff" between two walked columns is a statement about the grid until
  the gap is bisected.** D-297 reported the jump as a property of the axis; it
  was the gap's width. The lesson generalises to the span readings on every
  other axis here — none of them has a sub-step measurement either.
- **Reading a band edge off a disqualified column imports its defect.**
  `K = 192` is span-inadmissible *and* misses at both edges; using it as the
  upper neighbour is what produced the "opposite edges" shape that stood for
  five decisions. The nearest *admissible-enough* neighbour is the one the
  bracket should read.
- Freezing the grid per decision paid for itself a fourth time: three
  falsified claims survive as tests against `K_COLUMN_ROWS_D296/_D297` and
  nothing silently absorbed a column it was never about.
- Adding no new reading function kept `unprobed_revocable()` at `()` for a
  second cycle — still a route around the missing probe fixture (STATE #3),
  not a fix.

## Recommended next 1–3 priorities

1. **Walk `K = 168`** — the last interval `(160, 176)` is 16 wide; one more
   bisection either locates the upper endpoint or halves it to 8. ~90 s.
2. **Re-read the lower bound `(80, 96)` against the same neighbour lesson** —
   is `K = 80` a clean neighbour, or does it carry a defect like `192` did?
3. **Q-160 / register-reprobe-block-probe** — unchanged, still blocking any
   genuinely new `DIFFERENCE`-shaped reading.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/calibrated_ladder.py`,
  `eval/mppi_sandbox/tests/test_calibrated_ladder.py`, `docs/decisions.md`
- TSV row appended: yes
