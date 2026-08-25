# The K slide continues below 128 — and exits through the floor it was predicted to

- **Cycle**: 2026-08-16 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<bracket-the-k-axis-below-128>` (STATE #2) + `3bcc5d39` zombie close
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked `K ∈ {64, 96}` at `lam = 1.15`, `w = 5`, census 16 seeds on
  `cafe_freezing_v0` — 32 closed-loop runs, ~40 s — extending the `K` axis from
  three columns to five.
- Shipped `k_axis_bracket()`, which scores D-293's slide prediction against the
  edge that decision named **in advance**, rather than re-reading the
  `256 → 128` step the prediction came from.
- Closed a zombie `Doing` TODO (`3bcc5d39`) after verifying its three commits
  were already on `origin` and the `UNMEASURED` renderer had shipped.

## What worked / what failed

- **The prediction is confirmed in direction.** `K = 64` pushes `lam = 1.15`
  out through the **floor** — seed 0 at `2.9886` against a floor of `3.2`. That
  is the sign flip: at `K = 256` the ensemble sits nearer the *ceiling*, so a
  noise story predicts ceiling misses. The floor is the edge only the slide
  reaches for.
- **It is not confirmed in margin, and the reader says so.** Seed 0 needs
  `1.07x` to re-enter. `exit_is_marginal` is returned beside the verdict so no
  caller can quote a 7% miss as a decisive exit.
- **`K = 96` came back `16/16`** — unplanned as a headline, but it is what turns
  a prediction into a bracket. The unanimous set is the interval `{96, 128}`,
  closed at **opposite** band edges (floor below, ceiling above). Walking only
  `K = 64` would have confirmed the exit and left the run open at the bottom.
- The slide is monotone across all five walked `K` (`median ESS / K`:
  `0.1655 → 0.1734 → 0.2396 → 0.3093 → 0.3705`), so the new columns extend the
  mechanism rather than complicating it. Both are span-admissible; `K = 512`
  remains the only inadmissible column.
- **The suite went red on 4 tests, and all four were falsifications rather than
  regressions.** Extending the axis killed two D-292-era claims: membership is
  *not* monotone in `K` once `64` is walked (`15, 16, 16, 15, 11` — it rises
  before it falls, because the run is an interval and `64` sits below its lower
  edge), and neither is span (`5.14x` at `64` vs `3.80x` at `128`). Handled by
  repointing the original tests at `K_COLUMN_ROWS_D292` — the three columns they
  were actually measured on — and pinning the falsifications as three new tests
  against the full axis, so neither statement can be quoted without the other.
  The conclusion the span reading supported (`K` is not a common factor)
  survives and strengthens.
- **The pin tax fired exactly where STATE #1 said it would.** `inert_surface
  staged` returned `STAGED_MOVED` on 5 withdrawn exemptions. Mitigated by
  ordering — every report write was done *before* the receipt so the tree is
  still across it — which bought one suite instead of last cycle's three, but
  did not remove the debt.

## North-star delta

- No obstacle, clearance, near-miss or path-tracking number moved. Still one
  scene (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`.
- What did move is the **shape** of the operating window: it is now known to be
  an interval on a *second* axis, closed by two different mechanisms. The `lam`
  axis (D-290) and the `K` axis both bracket, which is a constraint on any
  future story about where this window comes from.
- A falsifiable prediction was stated by one cycle and scored by the next
  against the edge it named. That is the first genuine pre-registration on this
  branch, and it survived.

## Key learnings

- **The edge carries the argument; the count does not.** `16/16 → 15/16` is
  consistent with one unlucky seed. *Which side* it leaves by is not — and
  because D-293 named the side before the walk, the reading is a test rather
  than a fit.
- **Walking the interior point is cheap and converts a confirmation into a
  bracket.** `K = 96` cost 16 runs and was the difference between "the run is
  open below" and "the run is `{96, 128}`". Future axis walks should include the
  interior point by default.
- **Direction and margin are separate verdicts.** The confirming miss is `1.07x`
  — real but thin. Returning both prevents the next cycle inheriting a stronger
  claim than was measured.
- The pin debt is now costing ordering discipline every cycle. It is avoidable
  once (`reprobe`) and paid forever otherwise.

## Recommended next 1–3 priorities

1. `<reprobe-stale-pins>` — now **seventeen** cycles deferred and it dictated
   this cycle's entire write order. It is the standing tax.
2. `<locate-the-k-endpoints>` — both bounds are open intervals, `(64, 96)` and
   `(128, 256)`. Bisecting either is ~16 runs.
3. `<walk-lam-1.1-at-k128>` — still the one cell that turns the three-point
   `K = 128` grid into a real run-length comparison.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/calibrated_ladder.py`,
  `eval/mppi_sandbox/tests/test_calibrated_ladder.py`
- TSV row appended: yes
