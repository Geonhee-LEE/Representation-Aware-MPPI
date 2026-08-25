# The 0.6667 headline was an operating point, not a controller

- **Cycle**: 2026-08-08 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-run the 8-cell matrix at each cell's own admissible `w_obs_soft`
- **Phase**: P5
- **Status**: keep

## What I tried

- Shipped `operating_weight.py`: the map from one scene's D-126 `ReliefInterval`
  to the `w_obs_soft` its matrix cells run at. `PER_SCENE_REQUIRED` was a
  verdict about a rung *set*; this is what it means operationally.
- Taught `baseline_matrix` a per-scene weight: `Cell.w_obs_soft`,
  `run_cell(w_obs_soft=)`, `run_matrix(weights=)`, a `w_obs` render column, and
  a `--per-scene-weight` flag that runs the survey and the matrix in one
  command so the operating point is reproducible rather than hand-assembled.
- Re-ran the 8-cell matrix (2 controllers × 4 obstacle scenes, 8 seeds) at the
  resulting per-scene weights: head_on **1000**, crossing **1000**, convoy
  **10** (unmoved), freezing **10** (unswept).

## What worked / what failed

- ✅ **The headline correction lands: `unsafe_rate` 0.6667 → 0.0000**, and
  `min_clearance` over the avoidance population reads **0.3579** where D-120's
  footnote was 0.0016. Every scored cell is 0/8 near-miss, every cell is 8/8
  success, zero collisions. D-120's two-thirds-unsafe headline was substantially
  a statement about the weight the matrix happened to run at.
- 🔴 **But 8 of the 32 unsafe seeds left the denominator instead of being
  answered.** `risk_mppi/cafe_obstacle_crossing_v0` — one of D-120's four 8/8
  cells — now grades `ESS_OUT_OF_BAND` and is excluded, so the near-miss
  population shrinks from **6 cells / 48 seeds to 5 cells / 40 seeds**. The
  honest split is **24 of 32 unsafe seeds demonstrably relieved, 8 unanswered**.
  A 0.0000 over a denominator that dropped the hardest cell is exactly the
  empty-population failure D-107/D-120 both booked, and it must not be reported
  as a clean sweep.
- 🔴 **The extrapolation named in the module docstring bit on the first run.**
  The rung table is measured on `stock_mppi`; applying a scene's weight to
  `risk_mppi` — which runs the same scene at λ=3.2, its own calibrated rung —
  put 1000 far enough above that arm's cost scale to leave the ESS band. The
  cell that dropped out is the *only* cell where the scene-keyed weight met a
  materially different temperature. `measured_on` exists for this and now has a
  live instance behind it.
- 🔴 **A test caught a real defect in the resolver's central branch, and the
  defect was invisible to the type system.** The first draft decided "keep the
  shipped weight" with `shipped in permits`. `DEFAULT_LADDER` starts at 30 and
  the shipped weight is 10, so that test is **unconditionally false** — every
  no-relief scene would have graded `REPAIRED` and been moved to the ladder's
  floor. `cafe_convoy_v0`, whose veto *is* D-126's disjointness finding, was
  moved off the weight it voted for by the branch whose docstring says it
  prevents exactly that. Fixed by carrying `ReliefInterval.baseline_admissible`
  from `SweepResult.baseline.admissible` — a measured fact, not set membership.
- ✅ The fix is visible in the measurement: convoy reads `SHIPPED w_obs_soft=10`
  and `moved off shipped: 2/4`. Under the pre-fix resolver the same run printed
  `REPAIRED w_obs_soft=30` and `3/4`.
- ✅ The survey re-run reproduces D-126 exactly (head_on 300/3000, crossing
  300/1000, convoy no-relief/30, freezing refused) — the rung table is stable
  across cycles, so the correction rests on a repeated measurement.

## North-star delta

- The project's headline safety number now describes an operating point its
  scenes admit. `unsafe_rate` **0.6667 → 0.0000** over 40 seeds, `success_rate`
  1.0000, `collision_rate` 0.0000, `min_clearance` **0.3579** against declared
  margins of 0.30–0.40.
- Honest discount: one of the two hardest cells is no longer in the denominator.
  The north star's "near-miss ≤ Y" is met on the cells that remain measurable,
  not on the cells that were failing.

## Key learnings

- **A membership test against a ladder cannot answer a question about a value
  that is not on the ladder.** The shipped weight is not a rung, so no rung set
  can say whether a scene tolerates it. This typechecks, reads correctly, and is
  false for every input — the failure mode a unit test catches and review does
  not.
- **Fixing an operating point can move a cell out of the population instead of
  into compliance.** The weight that relieves a scene on one arm can de-band it
  on another, so a per-scene knob applied across a controller axis needs its
  denominator watched, not just its verdict.
- **A per-scene table is not a repin, and the difference is the scene that
  needed nothing.** Two of the four scenes moved; the other two are on the
  shipped weight for two different, named reasons.

## Recommended next 1–3 priorities

1. **Answer Q-113 — is the weight per-scene or per-cell?** `risk_mppi/crossing`
   left the band because a scene-keyed weight met an arm-specific temperature.
   A per-arm survey (3× the sim) would say whether the excluded cell has an
   admissible weight of its own.
2. **Re-run D-119 / D-124's A/Bs above the relief threshold** — still open from
   last cycle, and now the operating points to run them at are shipped.
3. **Densify the ladder between 100 and 300** (Q-112) — head_on and crossing
   share a threshold of 300 on a 3× ladder.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: `eval/mppi_sandbox/operating_weight.py`, `eval/mppi_sandbox/baseline_matrix.py`, `eval/mppi_sandbox/relief_interval.py`, `eval/mppi_sandbox/tests/test_operating_weight.py`, `eval/mppi_sandbox/tests/test_default_lam_sites.py`
- TSV row appended: yes
