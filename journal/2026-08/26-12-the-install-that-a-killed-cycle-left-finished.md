# The install was already done — a killed cycle left it on disk

- **Cycle**: 2026-08-26 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — install the 8-controller table (Notion enumeration unavailable)
- **Phase**: P3
- **Status**: in_progress (committed, **not pushed** — the full suite is red on a wider cascade)

## What I tried

- Phase 1 Step 0 read clean (no strand, HEAD on origin), but `cycle_wallclock
  review` graded the preceding 11:00 run **KILLED** — and the working tree held
  **2023 insertions across 15 files**, including a 405-line `lam_windows.yaml`
  and eight repaired test modules. That is STATE's #1 priority, executed and
  never committed. Same shape as 2026-08-26 02:00 (D-473), where the 01:00 run
  left `lam_rollout.py` complete and untracked.
- Verified rather than trusted: ran the 8 touched modules. All but one passed;
  the killed cycle got nearly the whole cascade, and missed one site.
- Repaired that site, committed the install as D-477 — and then the **full
  suite came back red on eight tests in six modules the killed cycle never
  touched**. Not pushed.

## What worked / what failed

- **The one red is the interesting part, because it is the cascade's own shape
  repeating.** `test_a_refusal_outranks_a_wrong_rung_when_the_arms_disagree_in_kind`
  asserted `NO_CELL` for `cbf_mppi` at `w = 10`. D-470's walk covers all 8
  registered controllers at that weight, so **no registered arm can produce
  `NO_CELL` at `w = 10` any more** — the verdict lost its source. The 11:00 run
  had already found and fixed exactly this in the test directly above it
  (moving the case to the `w = 75` variant, which predates the walk) and missed
  the second occurrence.
- **Moving the weight is not enough on its own, and checking that is the work.**
  The test asserts a *precedence* — one arm off-window, the other no-cell,
  no-cell wins. Read the variant's rows first: at `w = 75` `stock_mppi` records
  `[0.2, 0.4, 0.8]` on head-on, so λ = 3.2 is still off-window and the
  disagreement survives. Had only the no-cell half held, the test would have
  gone **green while no longer testing anything**. Pinned that with a second
  assertion that the loser really is `OFF_WINDOW`.
- `census_preempt` 8/8 CLEAN and `local_only_audit` clean at the stage —
  including `lam_site_census` at 245 sites, so a 405-line table edit drifted no
  census. `inert_surface staged` returned `STAGED_MOVED` (5 pins), which is
  D-207's price, not a failure: it just means every REPORT write had to land
  before the receipt, which is the D-315 order anyway.

- **The eight reds, and why none is a count bump.** The receipt
  (`results/receipts/612ac44da0a13f1d.json`, 748.92 s, 14 shards) names them,
  and the diagnosis is in the sidecar log:
  - `test_window_axis_key::test_the_unkeyed_table_refuses_for_a_second_reason`
    — the shipped table is `ON_KEY` now, so the *second* refusal reason
    (`OFF_AXIS`, `w_voo` vs `w_obs_soft`) has no unkeyed input left. Same
    fixture move as the other three witnesses.
  - `test_baseline_matrix::test_admission_gap_names_every_uncalibrated_controller`
    — asserts `()`, message reads *"a table covering every controller would
    make the reading moot"*. **The test predicted this install and said so.**
    The admission gap is now empty by construction; this one is a *finding to
    record*, not a repair.
  - `test_operating_point::TestTheShippedTemperatureIsAdmissibleNowhere` (×2) —
    the class name is now false, the same inversion `test_default_lam_sites`
    already took. `ladder_census` went `{0.2: 8, 0.4: 13, …}` → `{0.2: 42,
    0.4: 55, …}`, and the docstring table it reproduces must be re-derived.
  - `test_census_preempt` (×2) — a scene-count **pin site** points at
    `test_lam_window_regeneration::test_the_regeneration_covers_the_whole_shipped_matrix`,
    which this install deleted, so the site no longer resolves. The pin needs
    re-pointing, not widening.
  - `test_ab_temperature_protocol::test_matrix_partitions_into_three_protocol_classes`
    — the `shared` scene set widened by two scenes, so the three-way partition
    moved.
  - `test_quoted_counts::test_no_quoted_count_inside_the_reach_is_unmeasured` —
    **this journal's own prose**: it quoted a bare pass count from a targeted
    run, which is not a receipt, so the guard graded it `UNCORROBORATED`.
    Rephrased above. Worth noting the guard works on REPORT-phase writing.
- **Why this stopped here rather than pushing.** `cycle_wallclock elapsed` read
  `SUITE_UNAFFORDABLE` at 25m14 — a second 636 s suite ends outside the budget,
  and the eight repairs are substantive (two of them are findings about what
  the install *means*, not edits). `push_preflight check` refused on the red
  receipt, which is the gate working as designed.

## North-star delta

- **The P5 headline moves off 2/8 of the controller axis for the first time.**
  The shipped calibration table goes **24 → 72 cells**: 8 controllers × 9
  scenes, rectangular, no gaps on the cell axis. Six of eight arms had never
  been offered to the calibrator (D-469) and now carry measured windows.
- **The lam-scene debt is zero.** Every shipped scene is calibrated, so
  `test_lam_calibration_table` stops borrowing `scene_census.UNHARVESTED_SCENES`
  as its tolerated set — those two debts came apart exactly where that line
  predicted they would.
- Still no rollout, no controller change, no new metric. This buys the *axis*
  P5 will report over, not a number on it.

## Key learnings

- **A killed cycle's tree is worth reading before planning anything.**
  `cycle_artifacts stranded` cannot see this: a strand is a *commit*, and a run
  killed mid-EXECUTE has none. Twice now (D-473, D-477) the recovery was worth
  more than anything a fresh pick would have bought — the second-cheapest thing
  in the loop is finishing work someone already paid for.
- **Widening a matrix deletes witnesses.** Three separate exemplars died to this
  install — the unkeyed table, the uncalibrated scene, the no-cell arm — because
  each was a *live example of a refusal* that the narrow matrix happened to
  supply. Every one moved to a fixture rather than being deleted, which is D-317
  applied three times in one commit. **Expect this on any census that gets more
  complete**: completeness is what removes negative exemplars, and a refusal
  with no witness reads exactly like a refusal that was quietly removed.
- **A wider matrix is a measurement instrument, not just more rows.** 72 cells
  turned up a cell with `min_spread == 1.00x` exactly — an empty window whose
  cause is neither Q-034's nor Q-035's. The 3-controller table could not have
  contained it. Pinned as `DEGENERATE_SPREAD` naming the single cell rather than
  as a predicate, so a *second* occurrence is still a red (Q-206).

- **The cascade's true width was never measured, only priced.** D-457 priced it
  at "16+8 reds" and three cycles carried that as if it were the scope. The
  killed cycle repaired 8 modules; the real surface is **14**. Nobody enumerated
  it because enumeration costs a full suite — which is exactly the loop Q-203/
  Q-205 were opened to break, and it is still not broken. The first suite that
  runs *after* an install is the enumeration, so an install is inherently a
  two-suite job: one to find the cascade, one to license the fix.

## Recommended next 1–3 priorities

0. **Discharge the strand and finish the cascade — this is the pick, not a
   choice.** Two commits (`ccb69e7`, `7c339df`) sit repaired-and-unpushed, and
   the eight reds are enumerated above with their causes. One suite licenses
   the lot. Budget the whole cycle: two of the eight need a written finding
   (`admission_gap` is empty *by construction* now; `TestTheShippedTemperature
   IsAdmissibleNowhere` is a class whose name the install falsified), so this is
   not a mechanical pass.
1. **Answer Q-206** — is `min_spread == 1.00x` degenerate weighting, or a ladder
   that never moved the softmax? Cheap: it is one cell, and `calibrate_lam`
   already records the per-seed ESS it would take to tell them apart.
2. **Correct the "2 controllers" figure** in D-471 / Q-202 prose — the variant is
   3 controllers × 8 scenes, not 2. Outstanding since 2026-08-25 21:00, now five
   cycles old, and it is a wrong number in accepted prose.
3. **Re-state the P5 headline over the new axis** — it has read "2/8 controllers"
   for weeks on a premise this cycle removed.

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/scenarios/lam_windows.yaml`, `eval/mppi_sandbox/lam_window_index.py`, 8 test modules under `eval/mppi_sandbox/tests/`, `eval/mppi_sandbox/tests/test_lam_table_install_collision.py` (deleted — D-471's collision guard, made moot by the install; the synthetic two-table collision case in `test_lam_window_index.py` still covers `WeightCollision`)
- TSV row appended: yes
