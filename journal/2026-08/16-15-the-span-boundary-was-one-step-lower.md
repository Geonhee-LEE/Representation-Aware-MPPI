# The span boundary was one bisection step lower than the axis said

- **Cycle**: 2026-08-16 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39` re-span-the-k-axis-at-32
- **Phase**: P5
- **Status**: keep

## What I tried

- Re-walked seeds `16..31` at `K = 160` and `K = 192` on `cafe_freezing_v0`
  (`lam = 1.15`, `w = 5`, same `sweep_seeds` body as D-302), 34 runs. Seed `0`
  re-run in each column as a provenance check: `50.3213` and `60.8295`,
  identical to the recorded rows, so each pair of halves is one column.
- Added `K_COLUMN_ROWS_N32` — `{160, 176, 192}` at `n = 32` — the first `K`
  sub-axis on which spans are estimates rather than lower bounds, and the only
  grid where the two disqualification mechanisms can be compared without
  D-281's seed-count caveat.
- Read the matched grid through the existing `ensemble_scaling_in_k`
  (`n_required=32`) rather than a new predicate, so the n=16 and n=32 readings
  come out of one function.

## What worked / what failed

- **`K = 160` survives, and it is the only `K`-axis span claim that has been
  tested.** Still `32/32` — no new seed leaves `(8.0, 80.0)` — and the span
  moves `3.049x` → `3.601x`, an `18%` widening that leaves it the axis minimum
  and far inside the `10.0x` band. D-298 explicitly kept this statement live
  when the cliff died; it was the right call.
- **`K = 192`'s span doubles**: `12.187x` → `25.700x`. One new seed (`18`) lands
  at `3.8643`, under half the old minimum; the maximum is unchanged, so unlike
  `K = 176` this column widened at **one** end and still moved further.
- **The span-disqualification boundary is one bisection step lower than the
  axis said.** At `n = 16`, `inadmissible_k == (192,)` and the crossing sits in
  `(176, 192)`. At `n = 32`, `inadmissible_k == (176, 192)` and the crossing
  sits in `(160, 176)` — the interval membership already occupied.
- **Two more D-298 statements die.** (a) "Nothing on this axis jumps the band in
  one step" was an `n = 16` statement: the `160 → 176` step is `2.54x` at
  `n = 16` and `3.87x` at `n = 32`, and only the latter lands outside the band.
  The cliff returns at the *same* resolution, purely from ensemble size. (b) The
  **separation** — membership fails at `(160, 176]`, span not until
  `(176, 192)` — is gone as an axis property, not just at the one column D-302
  killed it at: both mechanisms now disqualify inside `(160, 176)`.
- **Membership barely moved and lost a distinction.** `(16, 15, 14)` →
  `(32, 29, 29)`: `176` and `192` are now tied, so membership no longer
  separates them while span separates them by `1.8x`.

## North-star delta

- No robot-facing number moved — no clearance, near-miss, CTE, one scene,
  `transfers_to_ab_scene = False`, still blocked on PR #68 for any A/B reading.
- What moved is a **method** correction with teeth: the `n = 16` span inflation
  is not a constant offset (`×1.180`, `×1.804`, `×2.109` at `160/176/192`), so a
  16-seed axis is systematically **flattened** rather than shifted. Orderings
  survive that; band crossings do not, and it is the crossing the admissibility
  verdict reads.

## Key learnings

- **A lower bound whose slack grows with the quantity cannot be thresholded,
  only ranked.** D-302 called the `n = 16` span "a lower bound, not an
  estimate"; this cycle measures the bias and it scales with the column's own
  width. That is why the ordering held while the crossing moved a step.
- **Doubling the ensemble is cheap and it should have come before three
  bisections.** D-296 through D-301 spent six cycles refining an axis whose
  every span was untested; the correction cost 34 runs and ~4 minutes.
- **The column that was most exposed was the one that survived.** `K = 160`
  carried the shape argument and was the reason this cycle existed; the
  falsification landed on its neighbours instead. Worth remembering the next
  time a re-measurement is scoped by "which claim would hurt most if wrong".

## Recommended next 1–3 priorities

- Re-walk `K = 128` at `n = 32` — the lower neighbour of the surviving run. If
  the run `{96, 128, 160}` is to mean anything at matched `n`, `128` is the
  next column that has to be an estimate rather than a lower bound.
- Re-read `k_axis_bracket` / `attribution_separability` against
  `K_COLUMN_ROWS_N32` — several verdicts downstream of `span_admissible` were
  computed on the `n = 16` grid and the crossing has since moved. Zero runs.
- Unchanged: answer Q-160 (self-blocked pins), and PR #68 is still the single
  north-star blocker.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, journal/2026-08/16-15-the-span-boundary-was-one-step-lower.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
