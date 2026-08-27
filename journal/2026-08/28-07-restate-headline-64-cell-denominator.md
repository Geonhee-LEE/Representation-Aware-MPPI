# The P5 headline's denominator was counting geometry's verdict as a gap

- **Cycle**: 2026-08-28 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` Re-state the P5 headline on the 64-cell denominator
- **Phase**: P5
- **Status**: keep

## What I tried

- Added `baseline_matrix.reportable_surface()` — derives the admission-gap
  denominator instead of quoting it: controllers from the calibration table's
  own keys, completability from `scene_eligibility.screen`, neither typed.
- Reconciled the two docstrings that carried "9 of 72" into headline territory
  (`baseline_matrix.admission_gap`, `calibrate_lam`), keeping 72 where it is
  true (table size) and naming 64 where the claim is admission.
- Wrote `tests/test_reportable_surface.py` — 11 tests pinning the *relationship*
  (excluded cells == the blocked scene's row) rather than the integer.

## What worked / what failed

- The derivation reproduces STATE's hand-measured claim exactly and independently:
  **63 of 64 admissible, 1 empty (`cbf_mppi` × `cafe_obstacle_crossing_v0`),
  8 excluded on `cafe_cut_in_v0`**. D-481's number was measured by hand via
  `load_windows()`; this is a second route to it that a test can re-run.
- `test_it_agrees_with_the_scene_axis_gap` cross-checks against
  `scene_admission_gap`, which finds the same scene by a completely different
  path (every controller declined it, vs. geometry proves it blocked). They
  agree, which is the reason to trust either.
- `inert_surface staged` returned `STAGED_MOVED` — this cycle added a reader, so
  the five root-snapshot pins lost their exemptions (D-207's tax). Not a failure;
  the receipt-last ordering (D-315) already absorbs it, and it cost nothing here.
- What I did **not** do: touch the two tests asserting `len(cells) == 72`. Those
  are correct statements about table size and changing them would have been the
  same conflation in the opposite direction.

## North-star delta

- **No planner movement.** Zero new numbers about MPPI behaviour; no rollout run.
- The delta is in what P5 may honestly claim, 6 days from entry: the admission
  gap is now **1 of 64 and explained**, not **9 of 72 and open**. That is a
  strictly stronger and strictly more defensible headline, and it is now
  defended by a test rather than by three docstrings agreeing with each other.
- The denominator can no longer drift back: a scene that becomes blocked leaves
  the count automatically, and a scene that becomes completable fails
  `test_the_blocked_scene_really_is_blocked_by_proof` by name.

## Key learnings

- **A denominator is a claim, and it inherits.** "9 of 72" was never a false
  sentence — it was a true sentence about the table, re-used for a question the
  table does not answer. The error propagated by *quotation*, not by
  measurement, which is why no test caught it: every number in it was right.
- **Two independent derivations of one fact are worth more than one careful
  one.** `scene_admission_gap` (nobody admitted it) and `reportable_surface`
  (geometry forbids it) reach `cafe_cut_in_v0` from opposite directions; the
  cross-check is cheaper than either measurement and catches a stale table.
- Pinning an integer would have been the easy test and the wrong one. The
  substitution worth blocking is "8 cells vanished" — not "the number 64
  changed" — and only the relational assertion sees it.

## Recommended next 1–3 priorities

1. **Follow the `essps_mppi` finding** — λ=0.1 admissible in exactly 8 of 72
   cells, all one arm, one per scene. Unchanged for five cycles now and it bears
   on which controller P5 reports as its baseline.
2. **Sweep the remaining consumers of the 72** — this cycle fixed the two
   docstrings that made a headline claim; a grep for downstream prose (docs/,
   journal digests) would confirm nothing else quotes it as an admission gap.
3. **Q-208 — refine-budget cap on `calibrate_matrix`**: record refine passes per
   cell so "1 pass sufficed" and "cut off at 1 pass" stop reading alike.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/baseline_matrix.py, eval/mppi_sandbox/calibrate_lam.py, eval/mppi_sandbox/tests/test_reportable_surface.py
- TSV row appended: yes
