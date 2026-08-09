# The successor criterion is circular — gain-matching cannot report the representation adding anything

- **Cycle**: 2026-08-10 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — replace ESS-matching with a verdict-stability-validated criterion
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's second candidate quantity — match `w_geom` on the null's
  **achieved clearance gain over stock** rather than on its median ESS — and
  evaluated it off the two ladders already on disk. **Zero new sim runs**, as
  STATE predicted.
- Screened it before adopting it: `gain_effect_coupling` counts how tightly the
  criterion's own match residual tracks the verdict statistic `|A − ½|` across
  the ladder.
- Added `gain_target` / `gain_ladder` / `gain_residuals` /
  `gain_matched_w_geom` / `gain_matched_verdict` / `gain_effect_coupling` /
  `gain_match_circularity` to `NullRung`, with 5 tests.

## What worked / what failed

- 🔴 **The criterion is circular, and both rungs say so.** The verdict is read
  off the head-to-head `A` over the *same achieved clearances* the gain match
  is computed from, so the match residual and the verdict statistic are one
  quantity seen twice. Measured: `|A − ½|` orders with the residual on
  **13/15** convoy rung pairs and **10/10** head_on ones →
  `CRITERION_CIRCULAR` on both. Driving the criterion to its own optimum
  drives `|A − ½|` below `inert_effect`, which *is* `GEOMETRY_SUFFICES`.
- 🔴 **Consequence, stated as the thing that matters**: the one rung where the
  criterion **succeeds** is the one that cannot report the representation
  adding anything. Convoy matches to **0.41%** of the mechanism's gain and
  reads `GEOMETRY_SUFFICES`; head_on's ladder is too coarse to match closer
  than **13.5%** and reads `REPRESENTATION_ADDS`. So head_on's surviving
  `REPRESENTATION_ADDS` is a statement about its ladder's spacing, not about
  its representation. No seed count fixes this.
- 🟢 **It is not a refinement of the shipped criterion — it is a different
  answer.** On convoy ESS-matching published `w_geom = 2.5` →
  `REPRESENTATION_ADDS`; gain-matching picks `20` → `GEOMETRY_SUFFICES`. Both
  are 16/16 admissible and each is its own criterion's optimum, so neither
  pick is refusable as sloppy. "The criterion choice does not matter much" was
  an assumption a successor calibration would have inherited unexamined.
- 🟢 The pick honours D-169's filter: `w_geom = 40` matches nearly as well
  (residual 0.0070 vs 0.0041) and is **8/16 in band**, so it drops out and the
  pick stays at 20. A criterion that picks a coefficient the calibration would
  refuse has not picked one.
- 🟡 The screen is a concordance count at threshold 0.85, not a proof. The
  algebra says the coupling is exact in the limit; the measurement says 13/15
  and 10/10 on real ladders. Reported as a reading so it is refutable.

## North-star delta

- **No movement on the robot.** Headline unchanged and still ungraded:
  `unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000,
  census still 0/6.
- What moved is the **cost of the next step**: one of STATE's two candidate
  criteria is retired on evidence for zero sim runs, so the runs that would
  have gone to calibrating it do not get spent.
- The screening rule generalises: check whether a proposed match quantity is
  analytically coupled to the verdict statistic **before** walking a ladder in
  it. That test is cheap and this branch has now paid three times for skipping
  its equivalent (D-168's 0.0485, D-169's ladder, D-167's 0.7725).

## Key learnings

- **A calibration criterion has two failure modes, not one.** D-169/D-170
  found criteria that fail to *identify* the verdict. This is the opposite
  defect — a criterion that identifies it too well, by determining it. Both
  are disqualifying and neither is visible from the shipped coefficient.
- **The surviving candidate is the one that reads a different quantity.**
  STATE's remaining option — the null's across-rollout cost spread — is not a
  re-reading of achieved clearance, so it passes this screen a priori. It is
  also **not on disk**: no recorded ladder carries per-rollout cost, so it
  costs new runs. That is now the honest price of the next step.
- Worth deciding before paying it: whether *any* scalar-coefficient null can
  answer attribution, since the two criteria walked so far failed in opposite
  directions. A structural ablation — remove the representation's **input**
  rather than scale its weight — has no coefficient to calibrate and so has
  neither failure mode.

## Recommended next 1–3 priorities

1. Spec the structural ablation (drop the representation's input, no
   coefficient) and compare its cost against instrumenting per-rollout cost
   spread for the surviving match criterion. Decide which to walk.
2. If cost-spread matching is chosen: instrument per-rollout cost in the
   sandbox ladder walk first, then re-screen with `gain_effect_coupling`'s
   test before spending a calibration.
3. Carried, ninth cycle: make `sandbox:pass=N` state whether it is `passed` or
   `executed` (`passed + xfailed`).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/geometric_null.py, eval/mppi_sandbox/tests/test_geometric_null.py, docs/decisions.md, journal/2026-08/10-07-gain-matching-is-circular.md
- TSV row appended: pending
