# The third row was never gradeable, and the marker named the wrong defect

- **Cycle**: 2026-08-21 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — re-harvest `city_curved_v0`'s `cte_max`
- **Phase**: P3
- **Status**: keep

## What I tried

- Bought the measurement STATE #1 named: `tail_mean.retake_max(scene=
  "city_curved_v0")`, 64 rollouts, **57.3 s**. Pinned as the third entry of
  `CTE_MAX_AT_OPERATING_POINT`.
- Read it the way `second_verdict` reads the TVaR column on the same scene —
  distinct-arm count first, headroom second — instead of quoting the ratio.
- Followed where that reading led: into `aa_calibration.column_verdict`, which
  has no notion of arm separation at all.

## What worked / what failed

- **The premise was wrong twice.** `MIXED_OPERATING_POINT_COLUMNS` said
  `COLUMN_VERDICT["cte_max"]`'s `1 of 3` straddled two harvests and that
  re-harvesting the third row would make it countable. Neither half survives:
  (a) `column_verdict` reads *every* `cte_max` row through `_ensemble` →
  `SEED_ENSEMBLE`, one harvest — what straddled two operating points was the
  **prose** quoting `1 of 3` beside the aligned `1.46x`/`4.93x`; (b) the
  re-take does not make it countable, because the cell is **degenerate at the
  operating point too** — 2 distinct arm rows of 8, exactly as at the old
  point. Marker retracted to `frozenset()`, not deleted.
- **The defect it was reaching for is real and one frame over.**
  `column_verdict` counts rows and floor-clearances with no `excited()` notion,
  while `tail_mean.second_verdict()` returns `UNTESTABLE` for that same cell
  and has done all along. D-389's shape a second time: two modules disagreeing
  about one cell because each derives from its own pin. Now named where it
  lives — `degenerate_tally_rows()`, deriving the threshold and the arm-count
  **across the boundary** from `tail_mean` (lazy import) rather than re-typing
  them, per Q-175.
- `gradeable_column_verdict("cte_max")` = `(2, 1, 1)` against the shipped
  `(3, 1, 1)`. The row that drops never cleared, so the **denominator** moves
  and the successes do not — the rate goes `1/3 → 1/2` and no result is gained.
- **`0/8` is not the signature it was taken for.** The two excited scenes agree
  with the old pin on no arm; this one agrees on **one**, and it is
  `essps_mppi` — the only arm the scene separates. The seven collapsed arms
  carry the disagreement. So the mismatch signature degrades toward agreement
  exactly as a cell degenerates, and it is evidence about construction only in
  proportion to excitation.
- `census_preempt` earned its 2 s a **sixth** consecutive cycle: `guard_tally`
  134 vs pin 133, caught before the commit. Entrant is
  `gradeable_column_verdict` — and its partner `degenerate_tally_rows` stayed
  out, because it *builds* the exempt set by magnitude comparison rather than
  differencing against a registry (D-072 again).

## North-star delta

- **Zero planner movement, 24 cycles.** No controller, scenario or cost term
  changed.
- **A fifth subtraction in six cycles, and the cheapest one yet.** 64 rollouts
  retired a marker and downgraded a tally's denominator. The branch's licensed
  claims did not grow.
- One thing was *added*: the degeneracy check `column_verdict` never had. It is
  a guard, not a result.

## Key learnings

- A next-action can be well-specified, correctly executed, and still rest on a
  misdiagnosis — STATE #1 was written from the marker's prose, and buying the
  measurement is what exposed the prose. Cheap measurements that can refute
  their own premise are worth more than their cost suggests.
- When a marker says "correcting this needs a measurement", check first whether
  the thing it marks actually reads the population it claims to. Here a `grep`
  for `_ensemble` would have answered half of it for free.
- Degeneracy is a property of the **scene**, not of an observable or a
  construction: `city_curved_v0` fails to separate arms in both columns at both
  operating points. Nothing bought on this scene will grade.

## Recommended next 1–3 priorities

1. **Stop buying cells on `city_curved_v0`** and record it as structurally
   ungradeable — it is `SECOND_SCENE`, so several claims are scoped around it.
2. **Audit the other typed markers for the same shape** — a marker whose stated
   repair path was never checked against what the marked statistic reads.
3. **Branch-scope decision (user)** — 24 cycles, zero planner change, five
   subtractions in six cycles.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tail_mean.py, eval/mppi_sandbox/aa_calibration.py, eval/mppi_sandbox/tests/test_column_alignment.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md
- TSV row appended: pending
