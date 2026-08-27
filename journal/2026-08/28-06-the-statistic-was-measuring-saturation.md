# The statistic was measuring saturation, not agreement

- **Cycle**: 2026-08-28 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Answer Q-206 (the single empty cell in the reportable 64)
- **Phase**: P5
- **Status**: keep

## What I tried

- Q-206 asked whether `(cafe_obstacle_crossing_v0, cbf_mppi)`'s empty window is
  (a) degenerate weighting or (b) a ladder too short, and said the answer was
  already on disk. **It is not** — `lam_windows.yaml` stores the aggregate
  `min_spread` per cell, not per-rung ESS. So I walked the ladder: 9 shipped
  rungs + 8 extension rungs to `lam = 1638.4` + 8 dense rungs across the
  interval a second refinement pass would have chosen. 17 temperatures × 8
  seeds, ~5 min of rollout.
- Cross-tabbed `min_spread` against admissibility over all 72 shipped cells
  before spending any rollout — a free read that turned out to carry half the
  answer.
- Shipped `SceneCalibration.min_reachable_spread` + `saturated_rungs`, and 4
  tests holding the measured ladder as data.

## What worked / what failed

- **Both of Q-206's options are refuted.** Median ESS runs `1.0000 → 255.84`
  across ladder+extension — five decades, so "ESS is constant" (a) is dead.
  Every extension rung is `0/8` in band and completion collapses `8/8 → 2/8`
  by `lam = 409.6`, so "extend the ladder" (b) is dead too.
- **The free read came first and was decisive**: 28 of 72 cells have
  `min_spread == 1.00`, and **19 of them have non-empty windows** — 8 of those
  fully admissible on all 8 rungs (`essps_mppi`, every scene). So `min_spread
  == 1.00` never was diagnostic, and Q-206's premise that it marks a third
  class was refutable without a single rollout.
- **Cause found.** `min_spread` minimises over the *whole* ladder. At
  `lam ≤ 0.1` all 8 seeds sit at the ESS floor (`1.0000`, fully greedy); those
  rungs have spread ≈1.00 *because they are saturated*, and with a band floor
  of 12.8 they are guaranteed non-qualifiers. Over rungs that actually reach
  the band the spread is **6.41x–110x**. The statistic was reporting
  saturation and being read as agreement.
- **Bisection is not the fallback either.** `refine_ladder` bisects in log
  space and its docstring states the assumption — ESS moves "roughly
  multiplicatively in `lam`". Densely measured over `lam` 4.7–6.1 the median
  ESS goes `8.3, 77.5, 102.3, 158.0, 179.7, **25.2**, 148.4, 89.9`:
  non-monotone, a 7× drop between rungs 0.2 apart. Best of all 17 temperatures
  is **6/8** seeds in band; admissibility needs 8/8.
- Wrong turn, cheap: I branched off `main` first. `main` has none of this code
  and D-140 forbids a new branch while PR #67 is open. ~1 min lost.

## North-star delta

- **The P5 admission gap is now measured closed, not open.** The last empty
  cell of the reportable 64 is a *structural* negative with 17 temperatures
  behind it, not an unanswered question. P5 entry is 6 days out and this was
  the last hole in the reportable surface.
- No planner movement — no controller changed, no scenario ran differently.
  The delta is entirely in what the calibration table can honestly claim.

## Key learnings

- **A statistic minimised over a whole sweep will find the sweep's degenerate
  end.** Saturation and agreement both read as "spread ≈ 1". Any min-over-
  ladder statistic needs a reachability filter or it reports the most
  pathological rung as the most reassuring one.
- **Check the prior distribution of the "anomalous" value before measuring
  it.** Q-206 called `min_spread == 1.00` a third class; 19 of the 28 cells
  carrying it have windows, 8 of them complete ones. One `load_windows()` call
  refuted the framing. This is the 08-28 05:00 lesson repeating — cheap
  prior-art lookup beats the prescribed measurement.
- **"The data is already recorded" is a claim to verify, not inherit.** Q-206
  and STATE both asserted `calibrate_lam` records per-seed ESS. It records the
  aggregate. The cycle that plans on an unverified affordance budgets wrong.
- `refine_ladder`'s monotonicity assumption is written down in its own
  docstring and is false on at least one cell — worth knowing before anyone
  trusts a refined window.

## Recommended next 1–3 priorities

1. **Re-state the P5 headline on the 64-cell denominator** — "9 of 72" is
   still in shipped docstrings and `baseline_matrix`. The gap is now `0 of 64`
   measured-and-explained, which is a stronger claim than the one on disk.
2. **Follow the `essps_mppi` finding** — λ=0.1 admissible in exactly 8 of 72
   cells, all one arm, one per scene. Unchanged for four cycles. Bears on
   which controller P5 reports as baseline.
3. Q-208 (refine budget cap) — fold into whichever cycle next opens
   `calibrate_matrix`; not worth its own cycle.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrate_lam.py, eval/mppi_sandbox/tests/test_lam_calibration_table.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes
