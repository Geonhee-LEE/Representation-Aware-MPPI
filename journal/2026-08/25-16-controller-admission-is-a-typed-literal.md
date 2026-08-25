# Controller admission was never a controller property — it is a two-name literal from 2026-08-02

- **Cycle**: 2026-08-25 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `admission` Diagnose why 6 of 8 controllers are `LAM_UNCALIBRATED`
- **Phase**: P3
- **Status**: keep

## What I tried
- Took STATE's bottleneck at its word — "6 of 8 controllers fail `LAM` calibration" — and went looking for the calibration failure.
- There is no calibration failure. `calibrate_lam.DEFAULT_CONTROLLERS` was the hand-typed tuple `("stock_mppi", "risk_mppi")`; the other six were never handed to the sweep.
- Probed all six directly (`calibrate`, `cafe_straight_v0`, rungs 0.2/0.4, 2 seeds) to check whether the literal was hiding a real defect.
- Replaced the literal with `default_controllers()` deriving from `controllers.REGISTRY` (D-047), and shipped `test_calibration_offer_set.py` (4 tests).

## What worked / what failed
- ⭐ **All six calibrate.** Every one returns admissible `(0.2, 0.4)` — the *same* window `stock_mppi` gets. Nothing about them resists the sweep, so 100% of the exclusion was the literal.
- ⭐ **The staleness is dated, and it is mostly silent drift, not a judgement call.** The literal was written 2026-08-02. `gap_gated` (08-08), `frozen_risk` (08-10), `geometric` (08-10), `social` (08-13), `essps` (08-17) were each added to `REGISTRY` *after* it — un-offered on arrival, no test anywhere going red. Only `cbf_mppi` (07-11) predates the literal.
- ⭐ **`LAM_UNCALIBRATED` reads as a verdict and is not one.** `NO_ADMISSIBLE_LAM` means measured-and-unplaceable; `LAM_UNCALIBRATED` means never-asked. D-467 read the table (downstream) and correctly saw six holes; the offer set (upstream) is where the holes were made.
- ✅ Second D-047 instance **inside this module's own neighbourhood** — `baseline_matrix.admission_gap` and `default_scenarios` both already derive, each with a comment saying why. The one place that didn't is the one that fed the sweep.
- ⚠️ **The table is NOT regenerated this cycle**, so `admission_gap()` still returns six and the headline is still 2/8. Regeneration is 8 scenes+ × 8 controllers × 8 rungs × 8 seeds ≈ 4600 runs (~22 min) and `cycle_wallclock elapsed` read `SUITE_AFFORDABLE` with 6m48 to suite start — it does not fit beside a 1235 s receipt. Cut deliberately (D-181), filed as the next pick.
- ✅ `census_preempt` CLEAN 8/8; `lam_site_census` unchanged at 245 (the new test calls no lam site). 164 adjacent lam/matrix tests green in 63 s.

## North-star delta
- **Zero measured movement, and the honest reason is that the fix is upstream of the measurement.** No rollout, no controller line changed, avoidance still 8/56 on the admitted pair.
- What it buys is the *precondition*: the reason the matrix cannot discriminate is now known to be removable by a script run, not by controller work. Before this cycle the six were plausibly six broken controllers.
- The 2/8 headline stands until the table is regenerated. Nothing here licenses quoting a wider one.

## Key learnings
- A verdict name can carry an implication its mechanism does not support. `LAM_UNCALIBRATED` was read by STATE (and by me, for the first five minutes) as "calibration was attempted and failed" — the code never attempts it.
- D-047's failure mode is not "someone typed a list once"; it is that the typed list stays *correct* for a while. This one was accurate for six days and wrong for seventeen.
- The cheap diagnostic beat the expensive one: a 6-controller × 2-rung × 2-seed probe (~40 s) settled a question that a full matrix regeneration (~22 min) would also have settled, and it fit in the budget.

## Recommended next 1–3 priorities
1. **Regenerate `lam_windows.yaml` over all 8 controllers** — standalone ~22 min script run, no suite alongside. This is what actually moves the headline off 2/8.
2. **Re-read the avoidance number after regeneration** — 8/56 was measured on a quarter of the axis; expect it to move for reasons that are not controller quality.
3. **Q-201 audit** — script the "operational D-NNN never cited in `scripts/prompts/*.md`" check.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrate_lam.py, eval/mppi_sandbox/tests/test_calibration_offer_set.py, docs/decisions.md
- TSV row appended: yes
