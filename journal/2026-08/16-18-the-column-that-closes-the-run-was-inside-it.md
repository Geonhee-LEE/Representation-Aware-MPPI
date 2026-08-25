# The column that closes the run was inside it

- **Cycle**: 2026-08-16 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39` respan-k128-at-32
- **Phase**: P3
- **Status**: keep

## What I tried

- Committed the TSV row 17:00 appended but could not ship (STATE's
  next-actionable #1) as this cycle's first act — one `git add -- results/`.
- Walked seeds `16..31` at `K = 128`, same cell (`lam = 1.15`, `w = 5`), same
  scene, same `sweep_seeds` body. 17 runs including seed `0` as a provenance
  check. This is D-304's stated **prerequisite**: it extends the matched grid
  downward, which is the only way the attribution question gets a run to sit on.
- Read `k_axis_bracket` / `attribution_separability` on the four-column grid,
  with the frozen three-column D-304 grid as the control.

## What worked / what failed

- **Provenance holds**: seed `0` returned `24.7730`, identical to the recorded
  16-seed row, so the two halves are one column and not two populations.
- **`K = 128` changes state on both mechanisms.** `16/16` span `3.803x` at
  `n = 16` → **`31/32` span `10.142x`** at `n = 32` (seed `30` at `5.2944`,
  under the `6.4` floor). It is the first column on this axis that doubling the
  ensemble takes **out of the unanimous run**, not merely widens — and it was an
  interior member of `{96, 128, 160}`, the run every verdict since D-296 leans on.
- **The span failure is marginal and I am recording it as marginal**: `10.142x`
  against a `10.0x` band is `1.4%` over, one seed's placement. `K = 176`
  (`13.94x`) and `K = 192` (`25.70x`) are not close calls; this one is. No shape
  argument should stand on it without a third ensemble.
- **The attribution question moved one step, not two.** `SEPARABILITY_NOT_APPLICABLE`
  → **`SEPARABILITY_UNTESTABLE`**. The grid extension bought expressibility —
  `run_bounds_open_intervals` goes `(None, (160,176))` → `((128,160), (160,176))`
  — but the lower leg rests on a **single-seed** miss, which is exactly the
  condition D-301 named at `K = 176`/`n = 16`.
- **D-304's pin did its job**: `membership_monotone` flipped back `True → False`
  with the fourth column, confirming that cycle's call that the `True` was a
  3-point truncation artifact rather than a property of the axis.

## North-star delta

- **No movement in any robot-facing number.** 17 sim runs, all `reached_goal`,
  but they measure the sampler, not obstacle avoidance or path tracking.
- Still one scene (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`,
  still blocked on PR #68 for any A/B reading. Unchanged for 34 days.
- What did move: a decided-but-undecidable leg is now **stated** rather than
  unstatable, so the next measurement on it is a well-posed one.

## Key learnings

- **Untestability is not a property of a `K`. It attaches to whichever column
  sits nearest the boundary.** D-301 read it at `176`; D-302 bought that leg back
  by doubling the ensemble; the same condition reappeared at `128` the moment
  `128` became the boundary column. Doubling the ensemble again would likely move
  it rather than remove it.
- **D-299's position/spread split was an `n = 16` statement.** On the matched
  grid both legs attribute to `spread` (`attributions == ('spread','spread')`).
  A decomposition that names two mechanisms is worth re-taking at the ensemble
  the conclusion will be quoted at.
- **A column being *inside* the run is not evidence it is robustly inside.**
  `128` sat in the unanimous run across five decisions and left it on the first
  ensemble that looked. The remaining un-respanned run members (`96`, and `64`/`80`
  below) are the same kind of untested claim.
- **The write-ordering paid for itself.** `inert_surface staged` returned
  `STAGED_MOVED` for the 6th consecutive cycle; doing every report write before
  the receipt (rather than paying for a `probe`) kept this to one suite.

## Recommended next 1–3 priorities

1. **Respan `K = 96` at 32 seeds** — the last unexamined member of the `n = 16`
   unanimous run. If it also exits, the run is empty below `160` and the axis's
   central claim since D-296 is an `n = 16` artifact end to end. ~17 runs.
2. **Decide whether the `10.142x` marginal call gets a third ensemble** —
   `n = 48` at `K = 128` alone would settle whether the span disqualification is
   real or a boundary coincidence. Cheaper than respanning a new column.
3. **Q-160 / retire the self-blocked pins** — 13 cycles now, 6 consecutive
   `STAGED_MOVED`. Absorbed by write-ordering again this cycle, but it is a
   standing tax on every cycle's ordering freedom.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
