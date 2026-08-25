# The one-run rung was the seeds — and the sign reversed

- **Cycle**: 2026-08-09 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-walk `w = 250` at 16 seeds
- **Phase**: P3
- **Status**: keep

## What I tried

- Re-walked the published band's `w = 250` rung on `cafe_head_on_v0` (λ = 0.8,
  margin 0.40 m) over **32 seeds** — D-133's block 0–15 *and* a disjoint fresh
  block 16–31, both arms, 64 runs, ~6 min. Re-walking the old block first was
  the entitlement check: a pipeline that cannot re-derive the recorded answer
  is not entitled to a new one (D-139's rule).
- Shipped `separation_reproduction.py`: `SeedBlock` (a rung measured over a
  named seed set) + `Reproduction` (a reference graded against a **disjoint**
  replication), with the 64 measured clearances carried as the module's own
  record and 19 tests.
- Amended `scorable_band`'s docstring paragraph — not `PUBLISHED_LADDER`.

## What worked / what failed

- 🟢 **The reference block reproduced D-133 exactly** — stock 0/16, risk 1/16,
  and the witness run is 0.3472 m on `risk_mppi` seed 6, the same four decimals
  the `scorable_band` docstring quotes. Pinned in a test so the prose and the
  measurement stop being maintained separately.
- 🔴 **The separation did not reproduce — it reversed.** Fresh block: stock
  **1/16** (seed 18, 0.3811 m), risk **0/16**. Same size, opposite sign.
  Pooled over 32 seeds both arms are 1/32 and the rung is **`TIED`**.
- 🟢 **Two things retire at once, in opposite directions.** The sign that
  pointed *against* the mechanism — the objection D-133 recorded honestly and
  D-124's `sub_margin` could not touch — was seeds. And the rung retires as
  evidence for anything: `TIED` is a real null. `separation_runs` goes 1 → 0,
  so the pooled rung leaves `one_run_rungs`.
- 🟡 **The band's shape verdict is untouched.** `TIED` is in `SCORABLE`, so
  `w = 250` stays scorable and `published_band()` still grades `BAND_SPLIT`.
  What changed is what the split is *made of*, not whether it exists — worth
  stating plainly because "the one-run rung was noise" reads like it should
  have collapsed the split, and it does not.
- 🟢 **The vacuity guard was written before it was needed, this time.**
  `NO_SEPARATION_TO_REPRODUCE` covers the reference-never-separated case, which
  is the fifth instance of the empty denominator (D-107 / D-120 / D-127 /
  D-145 / D-150). Two tests hold it, including the `NO_HEADROOM_SAFE` reference
  where both blocks read identical in every field.
- 🟡 **`PUBLISHED_LADDER` left as written.** Rewriting a measurement in place
  because a later one disagreed is how a table stops being evidence. The
  replication is a second record graded against the first; `published_band()`
  rebuilds from the same input as yesterday.

## North-star delta

- The project's only recorded instance of the mechanism looking *harmful* is
  withdrawn — measured, not argued away. `risk_mppi` is not one run worse at
  `w = 250`; at 32 seeds it is not different at all.
- No new safety/tracking dynamics: headline stays `unsafe_rate` 0.0000 /
  `min_clearance` 0.3579 / `success_rate` 1.0000 over 5 cells / 40 seeds.
- Calibrated coverage unchanged (60 arm-cells, 5 weights). This cycle bought
  seeds, not weights.

## Key learnings

- **A one-run verdict needs a disjoint block, not a bigger one.** Fisher said
  p = 1.0 and calibration said λ = 0.8 is admissible; neither could move the
  rung, and a longer single block would only have diluted the run. The cheapest
  decisive experiment in the project so far was 64 runs.
- **Reproducing the old block was worth half the compute.** Without it the
  reversal is a pipeline difference and the cycle proves nothing. Any future
  re-measurement of a published number should pay this cost first.
- **A null can be a result.** `TIED` here is more useful than either
  `SEPARATED` would have been: it removes an objection *and* removes a claim.
- **The band-shape question (Q-115) has a third option nobody costed**: not a
  threshold and not a disclosure, but replication of the specific rung. It does
  not generalise cheaply — it is one rung per 64 runs — but it settled this one
  without the module deciding what counts as a real delta.

## Recommended next 1–3 priorities

1. **Replicate `w = 150`, the band's other thin rung** — 10/16 vs 1/16 is nine
   runs of separation, so it is not a one-run rung, but it is the rung whose
   `SEPARATED` sets the *upper* edge of the contiguous island and it has never
   been seen on a second block. ~64 runs, ~6 min. Same protocol.
2. **Fix `shift_census`'s absent-cell path (Q-121), and audit it for the
   compared-nothing verdict** — unchanged for three cycles, and now the fifth
   sibling of the empty-denominator family is on the books.
3. **Walk `gap_gated_mppi` at `w = 75`** — unchanged; widens `COMPARED_ARMS` to
   three and gives D-146's column its first weight contrast. ~512 runs.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: `eval/mppi_sandbox/separation_reproduction.py`,
  `eval/mppi_sandbox/tests/test_separation_reproduction.py`,
  `eval/mppi_sandbox/scorable_band.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes
