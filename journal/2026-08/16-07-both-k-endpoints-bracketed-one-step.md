# Both `K` endpoints bracketed one step — and the approach to each is non-monotone

- **Cycle**: 2026-08-16 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<locate-the-k-endpoints>` (STATE #2 — the science item)
- **Phase**: P3
- **Status**: keep

## What I tried

- Bisected **both** of D-294's open endpoint intervals: `K = 80` in `(64, 96)`
  and `K = 192` in `(128, 256)`, at `lam = 1.15`, `w = 5`, census 16 seeds on
  `cafe_freezing_v0` — 32 closed-loop runs, ~4 min concurrent.
- Shipped both columns into `K_COLUMN_ROWS` and named the prior five-column
  grid `K_COLUMN_ROWS_D294`, the same treatment D-294 gave D-292's grid.
- Added `membership_monotone`, `near_edge_worse_than_far` and
  `interior_inadmissible_k` to `k_axis_bracket`'s payload.

## What worked / what failed

- **Both intervals halved, the run is unchanged.** `{96, 128}` stands;
  the lower endpoint moves to `(80, 96)` and the upper to `(128, 192)`.
  Neither is *located* — a bisection halves an interval, it does not close
  one, and `endpoints_located` stays `False`.
- **The upper neighbour is structurally inadmissible.** `K = 192` misses at
  **both** band edges and spans `12.19x` against a `10.0x` band, so D-283
  disqualifies it. `K = 512` was already like this but sits at the end of the
  axis; `192` is **interior**, one bisection above a `16/16` column. The run is
  bounded above by a column that cannot hold a seat, not one that lost a seat —
  so the admissible/inadmissible transition happens inside `(128, 192)`.
- **Membership is not monotone approaching either edge — the sharpest result.**
  Counts across `64, 80, 96, 128, 192, 256, 512` are
  `15, 14, 16, 16, 14, 15, 11`: on *both* sides the nearest walked neighbour
  outside the run is **worse** than the column beyond it. An endpoint search
  that assumed monotone decay outward would have stepped past both endpoints.
- **Two D-294 claims died, both pinned rather than quietly repointed.**
  (1) the `median ESS / K` slide is not monotone — `K = 80` reads `0.0861`
  against `K = 64`'s `0.1655` — and with it `repair_direction_in_k` goes
  `None`, so the axis loses a single repair direction; (2) the lower exit is
  not marginal — `K = 80` misses with **two** seeds at `1.21x` and `1.18x`
  against `K = 64`'s single `1.07x`. D-293's floor prediction survives on the
  new column; "marginal" was a property of `K = 64`, not of the edge.
- **Scope cut mid-cycle, and the pre-check is why it was cheap.** The first
  implementation shipped the findings as a new reading `k_endpoint_bisection`.
  `gd.unprobed_revocable()` (2 s) flagged it as a `DIFFERENCE`-shaped guard
  with a members-bearing reading and no probe — the fixture D-295 deferred as
  STATE #3. Two attempts to restructure it failed to clear the flag, at which
  point I was guessing at scanner spellings, which is the laundering-adjacent
  path D-045/D-047 name. **`k_axis_bracket` already reported the whole
  bisection for free** once the columns were in the grid, so the new function
  was deleted and only the two genuinely-new fields were added. Less code, no
  new guard.

## North-star delta

- **No obstacle, clearance, near-miss or CTE number moved.** Still one scene
  (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`.
- What moved: the operating window on the `K` axis is now bracketed to
  `(80, 96)` and `(128, 192)` — a factor-1.2 and factor-1.5 gap where D-294
  had 1.5 and 2.0 — and the *shape* of its boundary is now known to be
  non-monotone on both sides.

## Key learnings

- **A two-sided bracket hides the approach.** D-294 read `15, 16, 16, 15, 11`
  and called it a slide with an interval in the middle. The bisection shows
  the count dips immediately outside the run on both sides and partially
  recovers further out — invisible until the gaps were walked, and it
  invalidates bisection-by-monotonicity as a method on this axis.
- **Seconds-scale pre-checks keep paying, and their value is scope information,
  not just failure information.** `unprobed_revocable()` cost 2 s and told me
  the reading I was building carried an unbuilt fixture. The 02:00 and 03:00
  cycles spent ~24 min discovering the same class through the suite.
- **When a guard keeps firing after two restructures, the reading is in the
  wrong place.** The finding belonged in the payload that already computed it.

## Recommended next 1–3 priorities

1. **Bisect `(128, 192)` for the admissibility transition** — `K = 160`, 16
   runs (~2 min). The upper bound is now a *span* question, not a membership
   one, and that is a different mechanism than the lower edge.
2. **`<answer-q160-retire-self-blocked-pins>`** — unchanged from D-295, and
   this cycle is more evidence for it: the write-ordering did the job again.
3. **Register the `reprobe_block` probe fixture** (STATE #3) — this cycle hit
   the same missing fixture from a second direction and had to cut scope
   around it.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/calibrated_ladder.py`, `eval/mppi_sandbox/tests/test_calibrated_ladder.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
