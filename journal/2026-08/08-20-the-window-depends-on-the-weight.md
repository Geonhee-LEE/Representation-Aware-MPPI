# The window depends on the weight — 6 of 14 arm-cells move from w=10 to w=75

- **Cycle**: 2026-08-08 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-key D-132's band `{75, 100, 150}` (Q-119 lean (b))
- **Phase**: P5
- **Status**: keep

## What I tried

- Walked the **first rung of D-132's band**: the full calibration matrix at
  `--w-obs-soft 75` (8 scenes × 2 controllers × 8 rungs × 8 seeds = **1024
  closed-loop runs**, 16 jobs) into `eval/scenarios/variants/lam_windows_w75.yaml`.
- Compared it cell-for-cell against D-141's `w = 10` regeneration — same ladder,
  same seed count, so the contrast isolates the weight and nothing else.
- Shipped `lam_window_key.table_shift_census(reference, remeasured)` grading
  every arm-cell of two tables through the **existing** `window_shift`, plus
  `NEVER_OPEN` for cells that had no window in the reference either.

## What worked / what failed

- 🔴 **The λ window is not weight-invariant, and this is the first matrix-scale
  evidence of it.** Of the 14 arm-cells that had a window at `w = 10`, **8 held
  and 6 moved**: `WINDOW_SHIFTED` ×3 (convoy/stock, freezing/risk,
  head_on/risk), `WINDOW_DISJOINT` ×2 (convoy/risk, crossing/stock),
  `WINDOW_CLOSED` ×1 (crossing/risk).
- 🔴 **One cell lost its window outright**: `cafe_obstacle_crossing_v0`/risk
  records `[1.6, 3.2]` at `w = 10` and is admissible at **no** rung at `w = 75`.
  D-134 saw the same arm move to `{0.8}` at `w = 150` from an independent
  16-seed walk, so that row describes `w = 10` rather than drifting with weight.
- 🟢 **D-132's operating point survives the retraction test.** λ = 0.8 is
  admissible on **both** `cafe_head_on_v0` arms at `w = 75`, so the project's one
  significant mechanism claim keeps its temperature at the bottom rung of its own
  band. The risk arm grades `SHIFTED` — it drops λ = 0.2 — but not through 0.8.
- 🟡 **D-136's `FACTOR_INERT` on the weight axis is now bounded, not wrong.** It
  read head_on at `w = 100` / `w = 150`, and head_on/stock is exactly one of the
  8 cells that still holds here. The inference that generalised from it does not.
- 🟡 `convoy/risk` moved *up* (`[0.2, 0.4] → [0.8]`) and `crossing/stock` moved to
  a bisected off-ladder rung (`[4.5255]`), so movement is not a uniform drift in
  one direction — there is no correction factor to apply.
- 🟢 Q-036 survives the new weight: `shared_window` is empty at `w = 75` too, so
  "calibrate once, run everywhere" is not rescued by a different barrier weight.
- 🟡 Cost note: the sweep took ~16 min, longer than D-141's `w = 10` pass because
  empty windows trigger bisection refine passes — and `w = 75` produced more of
  them (3 non-calibratable cells vs 2).

## North-star delta

- A consumer running at `w = 75` now has a **keyed** table to read instead of
  reading the `w = 10` table off key — 13 cells answer `ON_KEY`, 3 `EMPTY_WINDOW`.
- The guard shipped in D-134 is now backed by a **matrix-scale** witness rather
  than three hand-walked cells: `OFF_KEY` demonstrably costs something on 6 of 14
  cells, not on one pathological scene.
- No new safety/tracking numbers — this cycle bought provenance and a refutation,
  not a better controller.

## Key learnings

- **A control and a measurement are not interchangeable.** D-141's `w = 10`
  regeneration agreeing on 16/16 cells was evidence about the *code path*; it was
  read in STATE as if it also licensed the windows. The first table written at a
  weight the matrix had never seen moved 6 cells.
- **Generalising from the reassuring cell is the recurring error here.** head_on
  held at `w = 100` and `w = 150`, and head_on is genuinely one of the stable
  cells — the mistake was letting one stable cell speak for the matrix. The same
  shape as D-139→D-141's "narrow cells were the real test".
- **`window_shift` could not tell "closed" from "never open"**, and a census that
  did not separate them would have reported 8/16 moved with 2 of those being
  cells that never had an operating point at any weight — the empty-denominator
  shape this repo keeps booking. Hence `NEVER_OPEN`.
- Seed count is the standing caveat: this table is 8 seeds where `REMEASURED` is
  16, so a `HELD` here is the weaker claim and a move is the stronger one.

## Recommended next 1–3 priorities

1. **Re-key `w = 100`** — the middle rung of D-132's band, and the one weight
   where a 16-seed hand walk (D-135) already exists to cross-check the 8-seed
   table against. It prices the seed-count caveat directly.
2. **Re-key `w = 150`** — completes the band; D-134/D-136 both have independent
   16-seed cells there to check against.
3. **Point a consumer at the keyed tables** — two weights now answer `ON_KEY` and
   nothing reads them; a rescore that picks λ per `(scene, weight)` from `lookup`
   turns the guard from available into load-bearing.

## Artifacts

- PR: #67 (open, continuing per D-140)
- Files touched: `eval/scenarios/variants/lam_windows_w75.yaml`,
  `eval/mppi_sandbox/lam_window_key.py`,
  `eval/mppi_sandbox/tests/test_lam_window_weight_dependence.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
