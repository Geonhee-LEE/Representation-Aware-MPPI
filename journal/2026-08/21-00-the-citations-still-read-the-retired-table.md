# The citations still read the retired table — and one of them was a guard

- **Cycle**: 2026-08-21 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-price the `dominance_holds()` / `CONVOY_SPLIT` citations
- **Phase**: P5
- **Status**: keep

## What I tried

- Zero rollouts by design. D-390 already bought the aligned measurement
  (`ALIGNED_CELLS`, `RETIRED_BY_ALIGNMENT`, `dominance_at_operating_point()`);
  this cycle only moved the **readers** onto it.
- `tail_mean.report()` now renders `dominance_at_operating_point()` plus two
  derived counts (`aligned_contrast_count()`, `aligned_dominance_count()`), and
  prints each retired reading beside its replacement instead of in place of it.
- `COLUMN_CLAIM_FORM` re-worded to the aligned numbers; `aa_calibration`'s
  `CONVOY_SPLIT` Q-175 block replaced with the resolution *and* its own headline
  retraction; `COLUMN_VERDICT["cte_max"]` marked via a new
  `MIXED_OPERATING_POINT_COLUMNS` rather than silently re-tallied.
- `docs/decisions.md`: D-391 prepended; D-372 / D-383 / D-388 Status lines
  re-priced in place.

## What worked / what failed

- **The guard was one of the citation sites.** `drift()` required the literal
  string `"cafe_convoy_v0 only"` in `COLUMN_CLAIM_FORM` whenever the column was
  licensed — so writing the *correct* aligned wording turned the guard red. This
  was not prose cleanup; it was a guard repair, and it is the finding of the
  cycle. The replacement clause checks the wording against a **re-derived
  count** (`aligned_contrast_count() == 0` ⟺ the string says "survives on zero
  cells") rather than against a remembered phrase — the same cross-boundary
  re-derivation Q-175 said was missing.
- **The direction was not what D-388 predicted.** D-388 ruled the contrast
  *scene-specific* — true on convoy, false on head-on. At one operating point it
  is true on **neither**: both aligned cells clear (`1.46x`, `4.93x`), so
  `aligned_contrast_count()` is `0`. Convoy's `0.96x`, the only cell that ever
  supported the contrast, was the mismatch itself.
- Three tests were also citation sites (`DOMINANCE HOLDS: True`,
  `"scene-specific"`, `"cafe_convoy_v0 only"`) and were re-priced with the
  reason recorded inline. 143 tests green on the five touched modules.
- Not fixed: `COLUMN_VERDICT["cte_max"]`'s `1 of 3` is still a mixed tally.
  Correcting it needs `city_curved_v0` re-harvested (~64 rollouts), which
  re-typing cannot buy — so it is marked, not edited.

## North-star delta

- **Zero planner movement, and this is a subtraction — the third in five
  cycles.** No controller, scenario, or cost term changed. What changed is that
  the branch's shipped census stopped printing a claim its own module knew was
  refuted.
- The surviving licensed claim is now narrower than at any point in the last
  five cycles: the TVaR column is gradeable on two excited scenes, and nothing
  about `cte_max`'s relative standing is licensed at all.

## Key learnings

- **A measurement can land and its citations stay stale, and nothing goes red.**
  D-390 was correct and complete as a measurement; the defect it left behind was
  entirely in who reads the result. There is no guard for "a pin exists that
  something else should now be reading" — the one guard in the area actively
  enforced the old reading.
- **A guard that pins prose by literal string encodes the claim, not the check.**
  `"cafe_convoy_v0 only"` made the correct re-wording expensive. Pin the
  *relation between the wording and a derived number* instead; then a correct
  re-wording passes and a drifting one fails, which is the intended direction.
- Retiring by pin rather than deletion (D-387) paid off twice here: the retired
  values were still available to print *beside* their replacements, so a reader
  who reaches the old `0.96x` in an older doc now meets the retraction.

## Recommended next 1–3 priorities

1. **Re-harvest `city_curved_v0`'s `cte_max` at the operating point**
   (~64 rollouts, `tail_mean.retake_max(scene=...)`) so
   `COLUMN_VERDICT["cte_max"]` stops being a mixed tally and
   `MIXED_OPERATING_POINT_COLUMNS` can empty.
2. **Generalise the cross-column values guard** — the `drift()` clause added
   here checks one wording against one count. Any future column pair repeats
   Q-175's defect until something re-derives across the module boundary by
   construction.
3. **branch-scope decision (user, blocking)** — 23 cycles, zero planner change,
   four subtractions in five cycles.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/tail_mean.py`, `eval/mppi_sandbox/aa_calibration.py`, `eval/mppi_sandbox/tests/test_tail_mean.py`, `eval/mppi_sandbox/tests/test_column_alignment.py`, `docs/decisions.md`
- TSV row appended: yes
