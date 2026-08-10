# The admissibility screen runs, and neither population can answer it

- **Cycle**: 2026-08-10 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE `Next claude-actionable` #1 — screen admissibility against residual share
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/admissibility_selection.py`: Q-124's screen, taking
  D-171's concordance statistic over (admissibility, `residual_share`) instead
  of over (match residual, verdict). 0 sim runs — every rung is on disk.
- Made the statistic **directional**. D-171's was unsigned; here only one
  direction is the accusation (admissible ⇒ lower share ⇒ friendlier to the
  representation), so 0.5 is independence and the reversed ordering is 0.0.
- Screened **two** populations, not the three nulls STATE named: the walked
  32-seed nulls, and the 6-rung 16-seed `CONVOY_W75_CLEARANCE_LADDER`, whose
  per-rung admissibility was already recorded and never read this way.
- Added `min_achievable_p` — the p the population would return under *perfect*
  coupling, a function of the label split alone and not of the shares.

## What worked / what failed

- **The walked population couples perfectly and it is worth nothing.**
  `coupling = 1.0000`, and the best reading that population can produce is
  p = 0.3333: one admissible against two refused is three labellings. Without
  the power guard this module's first output would have been "selection
  confirmed" and the census would have been retracted on a coin that landed
  once.
- **The ladder is underpowered too, and only just** — 4 admissible / 2 refused
  is 15 labellings, min p = 0.0667, missing α = 0.05 by one rung. Measured
  `coupling = 0.6250`, p = 0.4000. So *nothing on disk* answers Q-124.
- **The one reading that survives points away from selection.**
  `span_reading` is an observation about the observed set, not a
  reference-distribution claim, so low power does not void it: the ladder's
  admissible rungs span shares **0.3302 → 1.0041** and *both* refused rungs
  (0.9172, 0.9930) sit inside. `w_geom = 20` is admitted at share 1.0041 — a
  null reproducing the entire mechanism gain, maximally unflattering to the
  representation, and the filter let it through.
- **A bug I shipped and caught**: the first `licence_split` joined the two
  populations on formatted labels, so `w_geom=5` vs `w_geom=5.0` silently
  dropped the single rung the populations disagree about. Re-keyed numerically;
  it now reads `LICENCE_SPLIT (5.0,)`.
- **`guard_reflexivity` caught a real defect, not just a registration.** It
  pulled `licence_split` into the `&`-shaped registry (ninth member, pool
  96 → 97) — and the reason that matters is what it exposed: an empty
  intersection returned `LICENCE_AGREED`, reporting "no disagreements"
  from a comparison that never ran. D-107's shape, sitting inside the
  screen written to catch exactly that. Now `LICENCE_NO_OVERLAP`.
- Two new tests were flagged by `loop_reach` as unregistered population claims
  before the suite ran. Measured and registered at their true widths (2 and 6)
  rather than exempted.

## North-star delta

- No movement in the metrics: `unsafe_rate` 0.0000, `min_clearance` 0.3579,
  `success_rate` 1.0000, attribution coverage still 0/6, `NO_GRADED_RUNG`.
- The census's one graded number is **not** cleared and **not** convicted. Its
  denominator is now stated as *uncharacterised*, which is weaker and more
  accurate than either previous reading.
- Negative-but-priced: `points_needed` says +1 ladder rung makes the 16-seed
  screen answerable and +3 nulls makes the census's own strictness askable.

## Key learnings

- **A concordance statistic needs a power reading attached or it is a trap at
  small n.** The branch has spent three cycles discovering that its instruments
  choose its answers; this one would have done it a fourth time in the opposite
  direction — manufacturing a retraction — if the guard had been added after
  the measurement instead of before.
- **Direct statements about the observed set outlive underpowered inference.**
  The span reading is the only thing this cycle can actually assert, and it is
  assertable precisely because it makes no claim about a reference
  distribution.
- **Admissibility is not one filter.** `w_geom = 5.0` is admissible at 16 seeds
  and refused at 32, so "the admissible set" is not well defined until the seed
  count is fixed. Any future census claim has to name its strictness.

## Recommended next 1–3 priorities

1. **Walk one more `w_geom` rung on the convoy ladder** (16 seeds) — the
   cheapest measurement on the board that converts an underpowered screen into
   an answerable one. `points_needed` says exactly +1.
2. **Fix the census's admissibility strictness at a stated seed count** — the
   `LICENCE_SPLIT` at `w_geom = 5.0` means the graded set currently depends on
   an unstated choice.
3. **Make `sandbox:pass=N` state which quantity it is** — `passed` vs
   `executed`; carried twelve cycles now.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/admissibility_selection.py, eval/mppi_sandbox/tests/test_admissibility_selection.py, eval/mppi_sandbox/loop_reach.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
