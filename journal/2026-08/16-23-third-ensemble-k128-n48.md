# The third ensemble: the span question had only one answerable direction

- **Cycle**: 2026-08-16 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39` [sandbox] third-ensemble-for-the-marginal-span: K=128 을 n=48 로
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked `K = 128` at seeds `32..47` — same cell (`lam = 1.15`, `w = 5`), same
  scene, same `sweep_seeds` body, 17 closed-loop runs including seed `0` for
  provenance. This is the third ensemble D-306 said its verdict needed.
- Recorded the result as `MEASURED_SEEDS_48_LAM115_K128_EXT` / `_K128`, kept
  beside the 16- and 32-seed tables rather than overwriting them, and
  deliberately **not** merged into `K_COLUMN_ROWS_N32`.
- Pinned both the run and the structural claim in
  `test_d311_third_ensemble_deepens_the_span_and_frees_the_leg`.

## What worked / what failed

- Seed `0` reproduced `24.7730` exactly, so all three halves are one column.
- **The question was malformed and I could have known before running.** `span`
  is `max/min` over the seed set, so extension can only raise the max and lower
  the min — span is monotone non-decreasing, and no third ensemble could have
  returned this column to the band. STATE named this the bottleneck for three
  cycles without anyone noticing the rescuing direction did not exist.
- What the run *could* buy, it bought: `10.142x` → `13.8185x`, i.e. `1.4%` over
  the band → `38.2%` over. "Marginal" was itself an `n = 32` property.
- The miss count goes `1` → `2` (seed `30`, plus the new minimum at seed `37`,
  `1.65x` under the floor). That frees the leg: the deletion reaching it is no
  longer the one erasing the exit, so `SEPARABILITY_UNTESTABLE` is gone at
  `n = 48` — **D-306 predicted relocation, and that is falsified.**
- Scope held: at `n = 48` only one column is walked, so the grid readers return
  `K_UNWALKED` and every run/puncture/bracket statement stays an `n = 32` one.

## North-star delta

- No obstacle-avoidance or path-tracking number moved. One scene, one rung, one
  temperature, `transfers_to_ab_scene = False`, A/B still gated on PR #68.
- What did move: the confidence under D-308/D-310's puncture. Those rested on a
  `1.4%`-over reading; that reading is now `38.2%` over and the leg supporting
  it is probeable rather than untestable.

## Key learnings

- **Check the monotonicity of a statistic before spending an ensemble on it.**
  This is the third finding of the same class as D-307/D-308 (a `min`/`max`
  over a growing set used in an interval test). The STATE follow-up to grep the
  axis for more of these is now clearly the highest-value cheap item, not the
  third-ranked one.
- A verdict can be "correct but not robust" in a direction its author did not
  check. D-306's refusal to build on the marginal span was right; its stated
  reason (the reading might flip back) was not available to it.
- Untestability at a boundary column is not conserved — it can be cleared by a
  larger ensemble, not only relocated.

## Recommended next 1–3 priorities

1. Grep the `K` axis for the remaining `min`/`max`-over-a-set interval
   assumptions — three instances found, the class is confirmed, and it costs
   zero runs.
2. Probe the now-free lower leg: `attribution_separability` was blocked at
   `n = 32` by the puncture, but the `n = 48` leg is probeable — decide whether
   a matched 48-seed pair (`96` + `128`, ~17 more runs) buys the decomposition.
3. Q-161 enumeration — still carried unexecuted from 21:00.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, journal/2026-08/16-23-third-ensemble-k128-n48.md
- TSV row appended: pending
