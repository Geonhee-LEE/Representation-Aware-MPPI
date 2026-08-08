# The gap gate's arm is measured — the last standing refusal against a published claim clears

- **Cycle**: 2026-08-09 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (continuing PR #67 per D-140)
- **TODO**: STATE `Next claude-actionable` #1 — calibrate `gap_gated_mppi`
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked `gap_gated_mppi` across all 8 scenes at `--w-obs-soft 10` — the weight
  D-124's A/B was actually published at — 8 rungs × 8 seeds = **512 closed-loop
  runs**, ~6 min at 16 jobs.
- Shipped `calibrate_lam.merge_tables`: a column measured into its own file is
  joined into an existing table with named refusals (`WEIGHT_MISMATCH`,
  `PROTOCOL_MISMATCH`, `DUPLICATE_CELL`). The two alternatives were re-walking
  the 16 cells D-141 measured to reproduce *exactly* (~1000 runs of pure cost)
  or hand-editing a file whose own header says not to.
- Merged into `lam_windows_w10.yaml` (16 → **24 cells**) and re-graded D-124's
  published row through `comparison_headroom.certify`.

## What worked / what failed

- **`gap_gated_mppi` on head_on is admissible at `[0.2, 0.4, 0.8]`** — the same
  window as both other arms. D-124's row `(head_on, w = 10, λ = 0.8)` now grades
  **`CERTIFIED`**, down from `NO_CELL`. This could have gone the other way: the
  arm could have been admissible nowhere near 0.8, and this cycle would have
  recorded a retraction instead.
- **The merge had to be provably conservative, and that is the test that
  matters.** `merge_tables(base, empty)` reproduces the base **byte-for-byte**.
  Without that, adding a column silently re-renders 16 measurements through a
  different code path, and the `min_spread` a caller reads becomes this
  process's opinion rather than the run's record.
- **Buying a column at one weight broke a cross-weight census.**
  `table_shift_census` refuses tables covering different cells, and `w = 10` now
  has a column `w = 75` does not. That refusal is correct and I did not weaken
  it — the census takes an explicit `arms` scope, and the dropped column is
  asserted by name in the test rather than intersected away silently.
- **The census scope could not be allowed to shrink itself.** `arms` refuses a
  controller absent from either table, so a typo cannot quietly reduce the
  denominator — the contaminated-population shape D-142 had to split
  `NEVER_OPEN` out of.

## North-star delta

- No new safety/tracking numbers — `unsafe_rate` / `min_clearance` /
  `success_rate` are untouched. What moved is **standing**: of the project's two
  published mechanism claims, both were uncertified two cycles ago; D-145
  cleared one, and this cycle clears the *other's* temperature objection.
- Calibrated coverage: **48 → 56 arm-cells**, 3 weights. `gap_gated_mppi` goes
  from appearing in no table at any weight to a full 8-scene column at `w = 10`.
- Honest limit: this does **not** make D-124's claim scorable. `sub_margin`
  still says the delta sits below the margin. The claim now fails for exactly
  one reason instead of two, and the remaining one is about effect size, not
  about whether the temperature was ever measured.

## Key learnings

- **A refusal that names a missing measurement is a purchase order.** `NO_CELL`
  named the arm, so clearing it was a bounded ~6 min run rather than a research
  question. The three `certify` refusals have now each been cleared or priced
  by the cycle that read them — the vocabulary is doing the work it was built
  for.
- **Adding a column is an operation on a table, not on a matrix.** The instinct
  was to re-walk everything; D-141's exact-reproduction result is precisely what
  makes that unnecessary, and a merge with named refusals is cheaper *and*
  stricter than a re-walk (a re-walk cannot detect a protocol mismatch — it
  imposes one).
- **Asymmetric coverage propagates.** One new column at one weight broke a
  consumer two modules away. Expect every future single-weight column purchase
  to owe the same scope statement, and prefer naming the gap in a test over
  widening a guard.

## Recommended next 1–3 priorities

1. **Point the sweep drivers at `assert_certified`** — `certify` exists and only
   `comparison_headroom` calls it; `scorable_band` and the ladder walks still
   take λ as a free argument. Pure code + tests, no sweep. Note the bootstrap
   caveat: the walk that *builds* a table cannot require one.
2. **Walk `gap_gated_mppi` at `w = 75`** — would give the new column a weight
   contrast and let `COMPARED_ARMS` widen to three (the test above fails on
   purpose when it does). ~512 runs.
3. **Hand-walk `convoy` at 16 seeds** — still the one cell grading
   `WINDOW_DISJOINT` on both weight contrasts, and `seed_census` still has one
   comparable cell.

## Artifacts
- PR: #67 (continuing; D-140)
- Files touched: `eval/mppi_sandbox/calibrate_lam.py`, `eval/mppi_sandbox/lam_window_key.py`, `eval/mppi_sandbox/tests/test_table_merge.py`, `eval/mppi_sandbox/tests/test_operating_point_certification.py`, `eval/mppi_sandbox/tests/test_lam_window_weight_dependence.py`, `eval/scenarios/variants/lam_windows_w10.yaml`
- TSV row appended: yes
