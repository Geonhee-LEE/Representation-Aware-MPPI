# The rise belonged to one seed, and the outlier was the other rung

- **Cycle**: 2026-08-15 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bdc5d39` [sandbox] lam=1.2 의 non-monotone rise 귀속: (1.2, 12) 을 두 번째 seed 로 재측정
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's #1 action: re-run `(lam = 1.2, w_voo = 12)` on a second seed and
  compare against seed 0's `9.1412`, to separate "the sampler is non-monotone
  here" from "one seed was unlucky".
- **Declined the TODO's literal scope of one rung.** The rise is a statement
  about the *pair* `8 -> 12`; re-running only `w = 12` would have compared a
  2-seed rung against a 1-seed rung, which is exactly the D-019 error D-287 was
  written to avoid. Walked seeds 1 and 2 at **both** interior rungs — 4 runs,
  13.2 s total.
- Landed `rise_attribution()` + `MEASURED_LAM12_RISE` in `calibrated_ladder.py`
  with a three-way verdict vocabulary, and 11 tests.

## What worked / what failed

- **`RISE_SEED_ARTEFACT`.** Both added seeds *fall* across the pair:
  `16.9425 -> 9.4749` (seed 1) and `10.9994 -> 5.9535` (seed 2), against seed
  0's `4.5755 -> 9.1412`. 2 of 3 fall.
- **The outlier is not where the seed-0 ladder puts it.** The `w = 12` column
  is the *tight* one (`5.95 .. 9.47`, `1.59x`); `w = 8` is loose (`4.58 ..
  16.94`, **`3.70x`**). The rise was manufactured by a low left-hand point, not
  a high right-hand one — the opposite of how one seed reads.
- The two falling seeds fall by near-identical factors (`0.559x`, `0.541x`) —
  the monotone decay the axis shows everywhere else.
- **The withholding is re-founded, not lifted.** `w = 8`'s seeds straddle the
  band floor (seed 1 in band at `16.94`, seeds 0 and 2 below), so D-019's
  conjunction is unmet there too. A rung spanning `3.70x` has no single
  crossing to bracket either.
- Pin tax (D-207) fired a **sixth** consecutive time and was caught *before*
  the suite this time: `loop_reach.run(paths=[...])` on the one new file (~20 s)
  instead of discovering it in an 11-min red run.

## North-star delta

- No obstacle, clearance or near-miss number moved. Still one scene
  (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`.
- What moved is the **next move**: there is no shape anomaly on the temperature
  axis to explain, so `1.2` is a temperature to walk on more seeds rather than a
  defect to chase. One cycle of misdirected work avoided for 13.2 s of sim.
- Sixteenth consecutive cycle with `cafe_blind_corner_v0` behind PR #68.

## Key learnings

- **A non-monotonicity is a claim about a pair, so it must be re-measured on the
  pair.** The TODO asked for one rung; one rung would have produced a 2-vs-1
  seed comparison and no attribution.
- **Ask which rung is loose before asking which rung is anomalous.** The
  eye-catching point (`w = 12`, the rise) was the well-behaved one.
- A single seed can invent monotonicity *and* invent its violation; D-019's
  conjunction discipline catches the first and this cycle needed it for the
  second.

## Recommended next 1–3 priorities

1. Walk `lam = 1.2` at `w ∈ {5, 8, 12}` on the full census ensemble — the
   attribution says the temperature is walkable, not broken.
2. `<measure-the-shared-rung-at-lam-08>` — `4.517x` is still the smallest gap
   on the axis and the question must be measured, not derived.
3. `<reprobe-stale-pins>` — tenth consecutive cycle carrying the 5 withdrawn
   `inert_surface` exemptions.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_rise_attribution.py, eval/mppi_sandbox/loop_reach.py
- TSV row appended: pending
