# The clearance column joins the census — and a declaration rests on the window, not the gap

- **Cycle**: 2026-08-20 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` Extend `floor_reach.SITES` to the clearance column
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE #1 — the asymmetry D-373 left: cross-track claims bounded by a
  census a test runs, clearance claims bounded only by D-372's prose. D-373's
  own scope limit said joining clearance "would grow `SITES` without changing a
  verdict".
- Added five clearance sites to `floor_reach.SITES` — `declaration_gap.COMMON_WINDOW`
  plus all four `seed_debt.WINDOWS` entries — with a new `Site.reading` field so
  a bar window is graded as its **width** rather than an endpoint. Zero rollouts:
  both operands were already pinned.
- Scoped `tally()` to a column, added `CLEARANCE_TALLY`, `WINDOW_UNDER_GAP`,
  `THINNEST_WINDOW`, and a `window_vs_gap()` that derives both ratios from
  `aa_calibration.FLOOR_VERDICT` rather than re-typing D-372's numbers.
- Added the textual `floor_reach` cross-reference to both new claim-site modules
  so `carries_bound()` keeps `UNJOINED` empty.

## What worked / what failed

- **D-373's scope limit was wrong, and wrong in a way that matters.** Its
  reasoning graded the A-B gap between arm *means*; what sits in the user-blocked
  queue is a **bar window**, whose width is set by per-seed *extremes*. The
  window is the narrower object on **all five** scenes.
- **All five still clear** — `CLEARANCE_TALLY = (5, 5, 5)`, so the direction of
  the guess was right and 물체회피 stays licensed. The **margin** is what moves:
  `1.52x`–`5.44x` on the adversarial max reading, against `2.12x`–`5.76x` for
  the same scenes' gaps. `cafe_head_on_v0` is worst, `4.11x` → `2.31x`.
- **A units slip nearly manufactured most of the finding.** My first pass
  compared window-vs-`max` against D-372's published `2.44x`–`6.28x`, which are
  `p95`-based. Caught before the commit by recomputing the gaps rather than
  quoting them; `window_vs_gap()` now derives both sides from the same floor,
  and `test_both_ratios_use_the_same_floor` holds it there.
- Three of D-373's own tests went red on the change and were correct to —
  they pinned "only the `cte_max` column is joined", "exactly one row ABOVE",
  and a two-entry `carries_bound`. All three were rewritten to state the new
  scope rather than relaxed.
- `inert_surface staged` returned `STAGED_MOVED` again (the new test withdraws
  all five snapshot exemptions), so D-315's receipt-last ordering was mandatory.

## North-star delta

- 물체회피: **no metre moved, but the number to quote changed.** The two
  clearance bar declarations awaiting the user were carried by `6.28x` / `4.53x`;
  the honest figures for what they actually declare are `5.44x` and `2.31x`.
- `cafe_obstacle_crossing_v0`'s `1.52x` is now the thinnest clearance margin on
  the branch — previously invisible, since its gap ratio reads `2.97x`.
- 경로추종: unchanged. Still 5 of 6 endpoints below floor; the 512-rollout
  `RESOLUTION_DEBT` is untouched by this cycle.

## Key learnings

- **"Clears its floor" is not a property of a column, it is a property of a
  quantity.** D-372 established the column split and D-373 inherited it as a
  reason not to look. The same eight runs give a licensed gap and a tighter
  window, and only one of them is what a declaration rests on.
- **A ratio inherits its denominator.** Two `Nx` figures in the same prose meant
  two different floors, and nothing on the branch would have caught the mix —
  `citation_audit` polices magnitudes, not their denominators. The repair was to
  stop quoting and start deriving.
- A scope limit written to justify not doing work is the one worth re-reading:
  this one survived exactly one cycle.

## Recommended next 1–3 priorities

1. Tell the user the corrected margins for user-blocked #1/#2 — the
   declarations are still licensed, at `2.31x` and `5.44x`, not `4.53x`/`6.28x`.
2. Audit whether any other `Nx` on the branch mixes `p95` and `max` denominators
   — a `floor_reading` census, zero rollouts, same shape as `carries_bound()`.
3. `RESOLUTION_DEBT` (512 rollouts) remains the only lever on the cross-track
   column; still a user decision.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/floor_reach.py`, `eval/mppi_sandbox/declaration_gap.py`, `eval/mppi_sandbox/seed_debt.py`, `eval/mppi_sandbox/tests/test_floor_reach.py`
- TSV row appended: pending
