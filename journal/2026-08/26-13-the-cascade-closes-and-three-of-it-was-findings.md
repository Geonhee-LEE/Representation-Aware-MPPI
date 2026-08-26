# The cascade closes — and three of the eight were findings, not repairs

- **Cycle**: 2026-08-26 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — discharge the strand + finish the D-477 cascade
- **Phase**: P3
- **Status**: keep

## What I tried

- Phase 1 Step 0 read `STRANDED` on the 12:00 cycle: three commits ahead of
  origin, held deliberately because the full suite came back `4279 passed,
  8 failed`. The pick was forced — the strand outranks the decision tree, and
  12:00 had already enumerated all eight reds with causes, so this cycle was
  the repair, not the diagnosis.
- Re-ran the eight named nodes first rather than trusting the receipt list.
  **Seven still failed; `test_quoted_counts` was already green** — 12:00
  rephrased its own prose in the same tree that produced the receipt, so the
  receipt over-reports by one. Worth doing: it is 12 s to check and it would
  have been a confusing red in the middle of a repair.
- Repaired the seven, re-verified targeted, committed as D-478, then took the
  receipt as the last act before push (D-315 order).

## What worked / what failed

- **Three of the eight were findings, and writing them as findings is the
  work.** 12:00 flagged two; the third only appeared under repair.
  - `admission_gap` is empty **by construction**. Its own failure message —
    *"a table covering every controller would make the reading moot"* — was a
    prediction, not a hedge, and the install is the event it predicted. So the
    test inverts to hold the gap *closed* (a registered controller with no
    window is a real regression) rather than being deleted. Added a non-vacuity
    pin: without `calibrated == set(REGISTRY)`, deleting every controller would
    make the gap empty and the test green.
  - `TestTheShippedTemperatureIsAdmissibleNowhere` is now false, and the
    replacement is **sharper than the claim it retires**. λ = 0.1 is admitted in
    8 of 80 cells — and all eight are `essps_mppi`, one per scene. Not a
    scattering of lucky cells: exactly one arm reaches the shipped temperature
    and it reaches it everywhere. Asserted as `admitting == {"essps_mppi"}`
    rather than `== 8`, so a new *scene* leaves it green while a second *arm*
    reaching the shipped rung goes red — which is the event worth hearing about.
  - **The third was not on 12:00's list.** Re-pointing the census decoy at the
    inverted regeneration test made `test_the_decoys_do_not_assert_the_scene_count`
    go red, and the guard's message named the two possibilities correctly. The
    install had inverted the containment that test asserts, and the inverted
    form picked up a *second* integer — the shipped scene count 9 — beside the
    frozen 8. So the site is a **live pin now, not a decoy**: it moved to
    `SCENE_COUNT_PINS`. First site to cross that boundary in either direction.
- **The re-point I planned was wrong, and a guard caught it inside one cycle.**
  My first edit kept the site in `SCENE_COUNT_DECOYS` with the reason string
  unchanged, reasoning that the mechanism ("counts the frozen regenerated
  table") still held. It did hold — and was no longer the *whole* truth, which
  is what the machine-checked reason strings exist to detect. D-457 built that
  check after four decoys turned out to have three unnamed mechanisms; this is
  the first time it fired on a *fresh* misclassification rather than a stale one.
- The remaining four were mechanical: the unkeyed-table witness moved into a
  `tmp_path` fixture (the **fourth** such move this install has forced, after
  the unkeyed table, the uncalibrated scene and the no-cell arm), the A/B
  partition gained `cafe_obstacle_contested_v0` in `shared`, and `ladder_census`
  was re-derived. On the fixture move I also left the shipped table asserted
  under its *new* verdict (`ON_KEY` + still `OFF_AXIS`), so the file that
  changed keeps a live assertion rather than only the fixture standing in.
- **A number in 12:00's own prose was wrong.** STATE and the journal both say
  the `shared` scene set "widened by two scenes". It widened by **one**
  (6 → 7, `cafe_obstacle_contested_v0`). Corrected in STATE this cycle.

## North-star delta

- **The 8-controller axis is now green, not merely installed.** 12:00 bought
  the table; this cycle bought the licence to push it. That is the difference
  between 72 measured cells sitting on disk and 72 cells the suite will defend.
- **First measured statement about the shipped operating point in P5 terms**:
  the temperature the robot actually runs at is admissible for exactly one of
  eight arms, and `stock_mppi` — the arm the default belongs to — admits it in
  no scene. That is a north-star-relevant finding, not harness bookkeeping: it
  says the shipped default is calibrated for a controller the project does not
  ship.
- Still zero rollouts and no new metric. The axis is ready for the P5 headline
  to be re-stated over it; that re-statement has not happened yet.

## Key learnings

- **A test whose failure message predicts its own obsolescence should be
  inverted, not deleted.** Both `admission_gap` and the operating-point class
  were written by cycles that knew the install was coming. The inverted forms
  are strictly more useful — they now guard the *goal state* against
  regression, which is the assertion the project actually wants for the next
  six months. Deleting them would have thrown away the guard along with the
  finding.
- **"Completeness deletes witnesses" has a second edge: it also *promotes*
  them.** 12:00 learned the first half — a wider matrix removes negative
  exemplars, three times over. This cycle found the converse: widening also
  makes a previously-inert site start tracking the live population. Both
  directions are invisible in a green run, and only the machine-checked
  classification catches either.
- **The receipt's failure list is a claim about a tree, and the tree moved
  inside the cycle that produced it.** One of the eight was already fixed by
  the same cycle that reported it red. Re-running the named nodes before
  repairing them cost 12 s and removed a phantom.
- **The two-suite rule (D-477) held exactly as stated.** The install cost one
  suite to enumerate and one to license. Nothing this cycle found a way to
  compress that, and Q-203/Q-205 remain open.

## Recommended next 1–3 priorities

1. **Re-state the P5 headline over 8 controllers.** The "2/8 controllers" figure
   appears in P5 prose and STATE history, and its premise is now gone in both
   directions — the table is complete *and* green. Eight days to P5 entry makes
   this the highest-value non-harness item, and it needs no suite.
2. **Answer Q-206** — is the `min_spread == 1.00x` cell degenerate weighting or a
   ladder that never moved the softmax? One cell, no rollout; `calibrate_lam`
   already records the per-seed ESS that separates them.
3. **Follow the `essps_mppi` finding.** It is the only arm admitting the shipped
   λ, which makes it either the right default or an outlier in how its cost
   scales. Cheap to check against its cost normalisation, and it bears directly
   on which controller P5 reports as baseline.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/mppi_sandbox/census_preempt.py`,
  `eval/mppi_sandbox/tests/test_operating_point.py`,
  `test_baseline_matrix.py`, `test_ab_temperature_protocol.py`,
  `test_window_axis_key.py`
- TSV row appended: yes
