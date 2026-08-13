# The grid closed — and the curve turned around

- **Cycle**: 2026-08-13 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — extend the `w_freeze` grid to `3e5` / `1e6` at `lam = 0.8`
- **Phase**: P3
- **Status**: keep

## What I tried

- Ran `freeze_weight --lam 0.8 --weights 0.0 3e4 1e5 3e5 1e6 --seeds 12` (60
  runs) — the measurement D-245 named as its own alternative (c) and deferred
  for budget, and the exact "다음 action" Q-142 asked for.
- Included `3e4` and `1e5` rather than only the two new cells, so the extension
  reproduces D-245's top two readings instead of being glued to them.
- Extended `GRID` to `3e5` / `1e6` and added `optimum_is_bracketed` — the
  reading that says whether a `NONE_ADMISSIBLE` is an answer or a stopping point.

## What worked / what failed

- **The trend closed, in the direction nobody extrapolated.** `3e4 → 8/12`,
  `1e5 → 6/12`, then `3e5 → 12/12` and `1e6 → 12/12`. Exceedance **turns
  around**: `1e5` is an interior minimum and pricing progress harder makes the
  freezing *worse*, not better. Verdict `NONE_ADMISSIBLE`, threshold-robust
  across all four `EPS_LADDER` rungs.
- **The two reproduced cells reproduced exactly** — `3e4` 8/12 / 6.65 s /
  0.9056 m and `1e5` 6/12 / 2.05 s / 0.8537 m, digit-for-digit against D-245.
  The extension is on the same curve, not a re-measurement of a different one.
- **Clearance never recovers**: 0.9372 → 0.9056 → 0.8537 → 0.8387 → 0.8369.
  The term pays clearance monotonically across the whole grid while buying
  freeze only up to `1e5`. Above the optimum it pays and buys nothing.
- **`trend_is_open` was right and is now retired from this grid.** It said "the
  grid stops here", the extension confirmed the grid stopped there, and the
  answer past it was worse. Worth stating: the predicate was never a forecast,
  and this is the case against reading it as one.

## North-star delta

- **A capability claim is closed rather than narrowed.** Four cycles have now
  worked on `w_freeze`; this is the first that ends with a *measured* negative
  instead of a smaller positive. `ProgressPriceCritic` does not buy
  `cafe_freezing_v0`'s declared freeze at any tested strength at the paired
  temperature, and the grid now measures failure on **both sides** of its best
  cell, so that sentence is licensed.
- No movement on the north star's numbers — this removes a candidate setting
  rather than adding one. The honest framing: the branch had a quotable
  `w_freeze` for exactly one cycle (D-243), and three cycles of narrowing have
  now taken it back to zero.

## Key learnings

- **The exceedance curve is non-monotone, so "walk up until it stops improving"
  is not a valid stopping rule for this sweep.** That invalidates the obvious
  extension policy, not just this grid's endpoint.
- **`optimum_is_bracketed` is strictly stronger than `not trend_is_open`**, and
  the gap is real: a grid ending `8, 6, 6` reads *closed* on the two-cell
  comparison while its best cell is still its last. The guard D-245 added
  catches the sloping case only; this one catches the flat-topped case too.
- **The census streak broke, and honestly.** Sixteen consecutive cycles landed
  a new module in a census its own package takes; this cycle's tests are pure
  arithmetic over `WeightCell`s and construct no controller, so `decides` /
  `defaults` / `forwards` all hold at (92, 61, 32). Nil earned, not re-pinned.
- **Q-142 stays open by its own criterion.** It said it becomes an observation
  only if an `exceed = 0` cell appears and fails on clause 3 alone. None
  appeared, so clause 3 was never binding anywhere on this grid and the
  frozen-denominator suspicion remains inference.

## Recommended next 1–3 priorities

1. **Implement `time_to_goal` as first-arrival time** and wire the two
   `time_to_goal_max*` keys — 12/12 `reached` beside an 82 s ablation stall is
   now the fifth appearance of this blindness, and it is the one instrument gap
   that every freeze reading on this branch has had to work around.
2. **Ask why the price reverses above `1e5`** — cost saturation flattening the
   softmax weights is the obvious hypothesis and is cheap to test by reading the
   rollout cost spread at `1e5` vs `3e5`. It decides whether the term is
   mis-scaled or mis-specified.
3. **Take the freeze reading at a third temperature** — every `w_freeze` number
   now lives at either 0.1 or 0.8, and the two disagree by 40×.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/freeze_weight.py`,
  `eval/mppi_sandbox/tests/test_freeze_weight.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
