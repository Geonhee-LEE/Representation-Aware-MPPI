# The matrix admits two controllers of eight

- **Cycle**: 2026-08-25 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `controller-cycle` (STATE #3) — spend a cycle on a rollout, not a guard
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's bottleneck at its word — "43 cycles of instrument work and zero
  rollouts" — and spent the cycle running the P5 headline instrument
  (`baseline_matrix`) instead of writing another guard.
- Ran the full cafe matrix: **8 controllers × 7 scenes × 8 seeds = 448 rollouts**.
- Pinned the cause of the exclusions programmatically rather than in prose:
  `baseline_matrix.admission_gap()` + 2 tests.
- Recorded the headline durably at
  `results/readings/2026-08-25-12-baseline-matrix-admission.json`.

## What worked / what failed

- **The bottleneck's premise is false.** A rollout costs **0.31 s**; the whole
  448-run matrix finished in **~5 min**. Forty-three cycles did not skip
  rollouts because rollouts were expensive.
- **The real blocker is admission, not execution.** `lam_windows.yaml` carries
  **16 cells over 2 controllers** (`stock_mppi`, `risk_mppi`) while
  `controllers.REGISTRY` carries **8**. Six controllers have no calibration row
  at all, so `baseline_matrix` refuses their cells before running them.
- **The arithmetic**: **10/56 tracking-reportable, 8/56 avoidance-reportable**.
  Of 48 exclusions, **44 are `LAM_UNCALIBRATED`** — **42** of those are the six
  uncalibrated controllers (6 × 7), and the other 2 are the calibrated pair on
  `cafe_obstacle_contested_v0`, the D-453 scene the table never grew a row for.
- **The headline cannot discriminate, and not because of a tie.** Both admitted
  controllers score `8/8` success and `0` collisions on every graded cell. The
  controllers that would separate the matrix — every representation-aware one
  this project exists to evaluate — contribute zero cells.
- `min_clearance = 0.0016 m` and `unsafe_rate = 0.6667` over the 6-cell
  near-miss population: the cells that *do* run are mostly unsafe by their own
  declared margin.

## North-star delta

- **First rollout numbers in 43 cycles**: `sandbox:pass=10/56` (tracking),
  `sandbox:clearance=0.0016`, `unsafe_rate=0.6667`. These are measured, not
  restated.
- Converts the standing bottleneck from an unsized complaint ("spend a cycle on
  the controller") into a sized task: **6 controllers × 7 scenes of λ
  calibration**, with `calibrate_lam --out` already the tool that writes it.
- No controller improved. This cycle measured the instrument, not the planner.

## Key learnings

- **A bottleneck sentence repeated for six weeks was never priced.** "Zero
  rollouts" read as a cost problem and was an admission problem; one 90-second
  run distinguished them. The cheap measurement was available every one of
  those 43 cycles.
- **A per-cell verdict hides a per-axis absence.** 44 `LAM_UNCALIBRATED` cells
  read as a sparse grid; they are six controllers restating one missing row
  seven times each. That is why `admission_gap()` reports the controller axis
  and not the cell grid.
- **The calibration table does not grow with the registry or the scene set.**
  Adding a controller (six times) and adding a scene (`contested_v0`, D-453)
  both silently shrank the headline's denominator. The new test asserts the
  set relation against `REGISTRY`, so the next such addition is named in its
  own commit.

## Recommended next 1–3 priorities

1. **`calibrate-six-controllers`** — run `calibrate_lam` for the six missing
   controllers over the 7 cafe scenes; this is the single edit that takes the
   headline from 8/56 to a discriminating matrix. Sized, not speculative.
2. **`calibrate-contested-v0-row`** — the D-453 scene has no row for either
   calibrated controller; 2 cells for one sweep.
3. **`admission-gap-in-the-headline`** — `render()` prints 44 exclusion lines
   where one sentence ("6 of 8 controllers uncalibrated") is the reading.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/baseline_matrix.py, eval/mppi_sandbox/tests/test_baseline_matrix.py, results/readings/2026-08-25-12-baseline-matrix-admission.json, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
