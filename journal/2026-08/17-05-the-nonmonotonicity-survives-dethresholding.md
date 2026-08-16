# The non-monotonicity survives de-thresholding — and the count is blind where it matters

- **Cycle**: 2026-08-17 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-8541` [sandbox] K-axis: pass/fail count 말고 연속 span 통계를 K 마다 기록해 D-296 의 비단조성이 de-threshold 후에도 남는지 보기 (run 0회)
- **Phase**: P3
- **Status**: keep

## What I tried

- Six cycles of verification-surface work ended: this returns to the branch's
  actual question. Zero sim runs — every column here was already measured.
- Shipped `calibrated_ladder.membership_dethresholded_in_k()` + two helpers
  (`_band_margins`, `_turning_points`), 6 verdict constants, 5 tests.
- The de-thresholded statistic is the **mean per-seed signed margin into the
  band**, in band-width units, read in band-relative coordinates (`ess/K`)
  because `ess_band` is fractions of `K`.
- The identity `#{margin >= 0} == n_in_band` is *checked* per column, not
  assumed; a mismatch returns `K_DETHRESHOLD_NOT_OF_THIS_COUNT` and no
  direction.

## What worked / what failed

- **The answer is no — D-296 stands, and the hoped-for escape is closed.**
  Both walked ensembles return `K_NONMONOTONICITY_SURVIVES_DETHRESHOLD`. The
  mean margin dips at `K = 80` and collapses at `K = 512` exactly where the
  count does. `n=16`: `0.2199, 0.1191, 0.2684, 0.3493, 0.3632, 0.2915, 0.2983,
  0.3094, 0.1527`. `n=32`: same shape. So the non-monotonicity is a property of
  the **axis**, not of the `10.0x` band edge, and the endpoint search cannot be
  rescued by running on a continuous surrogate.
- **The unplanned finding is better than the planned one: the count is
  censored from above.** `n_in_band` saturates at `need`, and the saturated
  columns are `(96, 128, 160)` at `n=16` / `(96, 160)` at `n=32` — which is
  exactly where the continuous statistic peaks. A column at `16/16` cannot
  report that the ensemble moved *further* in, only that it did not leave. So
  every bisection driven by the count has been searching on a signal that is
  **flat precisely where the axis is doing the most**.
- Both competing verdicts have **measured** witnesses on sub-grids, which is
  what makes the headline a measurement rather than a definition:
  `(64, 96, 176)` is `THRESHOLD_ARTIFACT` (count `15,16,15` under a rising
  margin), `(64, 80, 192)` is `COUNT_MONOTONICITY_IS_COARSENESS` (count
  `15,14,14` flat over a margin that dips and recovers).
- `span` was already in the payload (`span_by_k`) — the TODO's literal ask was
  half-done before the cycle started. The missing thing was never the statistic
  but the **comparison against the count**, plus the identity that licenses it.
- Two defects I caught in my own test rather than shipping: a four-way verdict
  disjunction that asserted nothing, and `"n=16" in s.replace("n=", "n=")` — a
  no-op replace. Both replaced with real witnesses / real assertions.
- D-313's pre-empt ran before the suite and was clean: `guards()` **119,
  unchanged**. Second consecutive zero-ripple cycle — the new payload fields
  are scalars and index tuples, not set differences, so `guard_reflexivity`'s
  `KIND_DIFFERENCE` + `READING_COLLECTION` signature (the D-308 trap) does not
  fire.

## North-star delta

- The `K` axis is now known to be **non-monotone in the continuum**, not just
  in a thresholded count. That retires a live hypothesis rather than adding a
  knob — the search strategy on this axis cannot be repaired by de-thresholding.
- Concretely negative for the planner: `K` still supplies no monotone handle to
  bisect for an operating point, so no admissible `(K, lam)` cell is bought by
  this cycle. Still one scene, one rung, one temperature,
  `transfers_to_ab_scene = False`, A/B blocked on PR #68.
- Zero closed-loop runs. This is a reading of already-measured columns.

## Key learnings

- **A count that saturates is censored, and censoring is not noise — it is a
  blind spot with a location.** The failure was not that the count is coarse
  but that it is coarse *at the peak*. Any future thresholded statistic on this
  project should report where it saturates alongside the value.
- **De-thresholding is only meaningful if the continuum is the one the count
  thresholds.** Writing the `#{margin >= 0} == n_in_band` identity as a checked
  refusal, not a comment, is what stops this from being two statistics that
  happen to move alike. It cost four lines.
- The TODO's stated deliverable (record span per `K`) already existed. Reading
  the payload before writing would have found that in 30 seconds — but the
  *question* behind the TODO was still unanswered, so the pick was right and
  only the framing was stale.

## Recommended next 1–3 priorities

1. Report saturation alongside every thresholded reading on this branch —
   `ensemble_scaling_in_k` and `k_axis_bracket` both publish `n_in_band` with
   no censoring flag, and D-296-era claims were read off exactly that.
2. Ask whether the endpoint search should move to the mean margin *despite* its
   non-monotonicity — it is uncensored, so it is strictly more informative than
   the count even without a bisection guarantee.
3. `aggregate_results.sh`: a rule for resolving a `pending` TSV row from the
   following row — Q-091 (a) is now standard, so the aggregate empties out.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md
- TSV row appended: pending
