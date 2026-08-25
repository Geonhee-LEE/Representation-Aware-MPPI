# Per-cell temperature turns 8 of 24 cells on — and the first clean controller signal is 3/3 on clearance

- **Cycle**: 2026-08-07 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Re-run the matrix at per-scene admissible `lam`
- **Phase**: P5
- **Status**: keep

## What I tried

- `run_matrix` resolved **no** temperature, so D-118's 24 cells all ran at
  `MPPIParams().lam = 0.1` (median ESS ≈ 1.01 of 256 — a greedy argmin). It now
  resolves each cell's admissible rung from `eval/scenarios/lam_windows.yaml`
  via `calibrate_lam.load_windows` — the reader that already exists for that
  file (D-047; D-118 shipped that exact duplication one cycle earlier).
- `pick_lam` takes the **log-space middle** rung of the admissible window, not
  an endpoint: an endpoint is one ladder step from inadmissible.
- Two table verdicts decided **before** any sweep is paid for —
  `NO_ADMISSIBLE_LAM` (empty window: Q-035 already settled that no tested
  temperature makes the cell reportable) and `LAM_UNCALIBRATED` (no table row).
  Both join `NOT_REACHED` in a named `UNRUN` set.

## What worked / what failed

- ✅ **`avoidance_reportable` 0/24 → 8/24.** The first non-zero avoidance
  measurement the project has produced. All 12 `ESS_OUT_OF_BAND` cells that
  had a calibration row converted; `cafe_head_on` is the pinned live case —
  median ESS **2.98 → 69.75**, `ESS_OUT_OF_BAND → OK`.
- 🔴 **`collision_rate = 0.0000` over 64 seeds, and `min_clearance = 0.0016 m`.**
  Both are true and only one is reassuring. Nothing collided; something passed
  within **1.6 mm**. `stock_mppi/cafe_head_on` is 0.002 m. The collision metric
  is saturated at exactly the regime the north star calls "near-miss ≤ Y", and
  nothing in the harness measures that — STATE #3, now with a number.
- ✅ **First clean controller signal, and it is directional**: `risk_mppi` holds
  more clearance than `stock_mppi` in **4 of 4** shared avoidance cells —
  convoy 0.830 / 0.358, freezing 0.903 / 0.477, head_on 0.064 / 0.002,
  obstacle_crossing 0.035 / 0.015. **Three of those ran at the same `lam=0.4`**,
  so they are matched-temperature comparisons; the fourth is not (below). 3/3
  same-direction is p = 0.125 one-sided — suggestive, **not** significant, and
  reported as such.
- 🔴 **8 of 24 cells were never calibrated at all.** `lam_windows.yaml` holds
  16 rows = 2 controllers × 8 scenes; `cbf_mppi` appears **zero** times. A
  third of the matrix is unreportable for a reason that has nothing to do with
  temperature admissibility — the table was simply never extended to the third
  controller, and D-118's 0/24 hid this behind a uniform `ESS_OUT_OF_BAND`.
- 🔴 **The matrix walks straight past a guard built to refuse it.**
  `cafe_obstacle_crossing`'s windows are **disjoint** (stock `{0.8}`, risk
  `{3.2}`); `ab.ab_temperature` grades the scene `per_arm` and
  `assert_single_lam_ab` exists to reject exactly that pairing. `pick_lam` is
  per-cell, so it ran the two arms 4× apart and the headline summed them
  without complaint. That cell's delta confounds controller with temperature —
  **Q-107**, and the reason the clearance claim above is stated as 3/3 and not
  4/4.
- 🔴 Wrote `lam=` as a controller kwarg first; `StockMPPI.__init__` takes
  `params`, so the injection is `params=MPPIParams(lam=...)` — what
  `ab.lam_probe` has always used and what I did not look up before writing.

## North-star delta

- **First avoidance number that describes a cost term rather than a
  temperature**: 8 reportable cells, 64 seeds, 0 collisions.
- **The safety margin is the finding, not the collision count.** 1.6 mm minimum
  clearance means "0 collisions" is one grid cell away from meaningless.
- Path tracking unchanged in substance: `success_rate = 1.0000` over 14 cells
  (was 18 — four cells left the denominator because `UNRUN` now excludes cells
  that never executed, which is a correction, not a regression).

## Key learnings

- **A repair is legible as a population change, not as a number moving.**
  `lam_dependence`'s non-test-site list went 2 → 3 → 2 across two cycles; the
  entry existed for exactly one cycle, and that cycle is the one whose matrix
  reported 0/24. That round trip is better evidence the fix landed than any
  count.
- **Short-circuiting on the table is not just a speed win.** Skipping cells the
  calibration already answers is what made `NO_ADMISSIBLE_LAM` and
  `LAM_UNCALIBRATED` distinct verdicts instead of both arriving as
  `ESS_OUT_OF_BAND` — the uncalibrated-controller finding is visible *because*
  the cell was never run.
- **I misjudged my own elapsed time again, in the cycle after the one that
  logged doing it.** At 20:07 I believed it was ~20:57 and started cutting
  scope against a budget I had not spent. The clock is cheap; my sense of it
  has now been wrong twice in two cycles in the same direction.
- **`tracking_reportable` was `status != NOT_REACHED`** — an open predicate, so
  both new verdicts would have defaulted *into* the tracking denominator with
  `n_seeds=0`. Naming the excluded set (`UNRUN`) rather than the excluded
  member is what makes the next verdict safe by default.

## Recommended next 1–3 priorities

1. **Add a near-miss metric.** 1.6 mm minimum clearance with 0 collisions is
   the measurement that demands it; the north star names "near-miss ≤ Y".
2. **Calibrate `cbf_mppi`** — `python3 -m eval.mppi_sandbox.calibrate_lam`
   covering the third controller. Unblocks 8 of 24 cells.
3. **Answer Q-107** by measuring first: run `stock_mppi` on
   `cafe_obstacle_crossing` at both 0.8 and 3.2 and see whether the 4× gap
   moves the delta at all.

## Artifacts

- PR: #67 (branch already open — adds no new review-queue depth)
- Files touched: `eval/mppi_sandbox/baseline_matrix.py`,
  `eval/mppi_sandbox/tests/test_baseline_matrix.py`,
  `eval/mppi_sandbox/tests/test_default_lam_sites.py`,
  `eval/mppi_sandbox/tests/test_lam_dependence.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
