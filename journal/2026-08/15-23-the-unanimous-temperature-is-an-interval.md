# The unanimous temperature is an interval — and its two ends are different boundaries

- **Cycle**: 2026-08-15 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<walk-w5-at-a-lower-temperature>` (STATE next-actionable #1)
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's #1 asked for `w_voo = 5` walked **below** `lam = 1.2` on the 16-seed
  census, to close the sole miss (seed 5 at `143.41`, above the `128.0`
  ceiling). Before walking anything I stacked the `w = 5` census columns the
  branch **already had** — and the answer to the literal question was on disk:
  `lam = 1.0` is `MEASURED_SEEDS_16_LAM10`, `16/16`, a shipped and tested
  `UNANIMOUS_WINDOW`.
- Shipped `calibrated_ladder.unanimity_bracket()` — the first reader on this
  branch that takes band membership across temperatures at a **fixed rung**
  instead of one temperature at a time.
- Then walked the two temperatures the stack actually left open: `lam ∈
  {0.9, 1.1}` at `w = 5`, 16 seeds each. 32 closed-loop runs, concurrent by
  temperature, **~4 min**.

## What worked / what failed

- **`BRACKET_CLOSED_BOTH_EDGES`, and the two closures are different walls.**
  `0.8 → 1.2` gives `15, 14, 16, 16, 15` in band. The unanimous run is
  `{1.0, 1.1}`, contiguous; the neighbour below misses at the **floor** and the
  neighbour above at the **ceiling**. Floor-then-ceiling can only happen if the
  ensemble crossed the band — a walk that merely stopped early shows one wall
  twice.
- **`lam = 1.1` is a second `UNANIMOUS_WINDOW`** (`16/16`, span `5.92x`), which
  is exactly what the bottleneck wanted. The branch had one; it now has two,
  adjacent.
- **`lam = 0.9` is *worse* than `0.8`** — `14/16` against `15/16`, two misses
  (seeds 3, 11) instead of one. So membership is not monotone **and not
  unimodal**. This is the one result that could not have been guessed: a
  unimodal reader extrapolates the lower endpoint below `0.8`, and it is
  actually in `(0.9, 1.0)`.
- **The endpoints have different mechanisms**, separated by D-283's
  admissibility test. Below the run the span *exceeds* the band (`16.56x` at
  `0.9`, `17.34x` at `0.8`, vs `10.0x`) — no common factor puts those columns
  in band at all, so the lower endpoint is where the spread becomes admissible.
  Above the run the span still fits (`6.90x` at `1.2`); that column is
  admissible and merely slid off the ceiling. Structural on one side,
  repairable-in-principle on the other.
- What I did **not** do: locate the endpoints. They are reported as the open
  intervals `(0.9, 1.0)` and `(1.1, 1.2)`, never as a width — `endpoints_located`
  is returned `False`.

## North-star delta

- A **two-rung-wide operating window in temperature** now exists at `w = 5`,
  verified on 16 seeds: `lam ∈ {1.0, 1.1}` both put every seed in band. That is
  the first tolerance statement this branch can make about an operating point,
  as opposed to a single lucky cell.
- Still one scene (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`.
  No obstacle, clearance or near-miss number moved. PR #68 remains the blocker.

## Key learnings

- **Read the columns you already have before walking a new one.** The literal
  question STATE asked was answered by a table shipped several cycles ago; the
  walk was still worth taking, but for the two temperatures the stack left
  open, not the one it named.
- **Span, not median, predicts unanimity.** The span collapses `16.56x → 5.46x`
  exactly at the lower endpoint while the median barely moves (`40.12 → 54.77`).
  D-284 measured that `lam` compresses rather than translates; here that
  compression is visibly *what buys* the window.
- **"Not monotone" and "not unimodal" are different defects**, and only the
  second one forbids placing an endpoint by extrapolation. The `0.9` dip is
  what makes the difference, and one column is what bought it.

## Recommended next 1–3 priorities

1. Walk `w = 5` at `lam ∈ {1.15, 1.25}` — the upper endpoint is in `(1.1, 1.2)`
   and it is the *repairable* side (`translated_out_of_band`), so it is the one
   a common factor can actually move. ~32 runs, ~4 min.
2. Ask whether the `{1.0, 1.1}` window survives at a **second rung**. `w = 8` is
   retired (D-289: `22.91x` span), but `w = 12` is admissible at `5.79x` and has
   never been walked as a temperature column.
3. Re-probe the 5 withdrawn `inert_surface` pins — **twelfth** consecutive cycle
   paying the all-writes-before-suite tax.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
