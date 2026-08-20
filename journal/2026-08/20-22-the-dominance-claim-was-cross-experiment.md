# The dominance claim did not survive its own operating point

- **Cycle**: 2026-08-20 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — answer Q-175
- **Phase**: P3
- **Status**: keep

## What I tried

- Answered **Q-175 with option (a)**: re-harvested the `cte_max` column under
  `tail_mean.retake`'s own construction (`lam=OPERATING_LAM` +
  `clearance_census.ISOLATION`) on the two cells `dominance_holds()` rests on —
  `cafe_convoy_v0` and `cafe_head_on_v0`. 128 rollouts, ~5 min.
- Harvested the **TVaR column in the same loop** so the run carries its own
  reproduction check rather than relying on prose.
- Pinned `CTE_MAX_AT_OPERATING_POINT` + `ALIGNED_CELLS`, added `retake_max()`
  as an executable path back to the construction, and wired it to a `--retake-max`
  operator entry point.

## What worked / what failed

- **Two reproduction checks ran before anything was read.** The TVaR column my
  loop produced reproduces `TVAR_ENSEMBLE` and `TVAR_ENSEMBLE_THIRD` **8/8 arms
  on both scenes** — so the construction *is* the pins' operating point. The
  `cte_max` column it produces matches `excursion_seed_width.SEED_ENSEMBLE`
  **0/8 on both**. Q-175's diagnosis reproduces from the opposite side.
- **`dominance_holds()` is refuted at one operating point.** Aligned:
  convoy `2.64` vs **`1.46`** (holds), head_on `3.88` vs **`4.93`** (**inverts**).
  1 of 2 is not a claim. This was D-388's replacement for the contrast D-383
  lost, so the branch's headline claim has now been subtracted twice.
- **`CONVOY_SPLIT`'s `0.96x` was an artifact, not a null result.** At the aligned
  point convoy's `cte_max` clears its own floor — `1.46x`, adversarial `1.31x`.
  Its stated premise ("holds scene, arms, operating point and seeds fixed and
  varies only which quantity is read") was false in exactly the term it named.
- **Both cells moved *upward*.** The old column was not a noisier reading of
  this one; the mismatch predicted no direction and got a consistent one.
- `census_preempt` earned its 2 s a **fifth** consecutive cycle — `retake_max`
  landed as a dead-code residue and was caught pre-commit. Fixed by wiring the
  caller, not by editing the pin.

## North-star delta

- **Negative again, and this is now a pattern worth naming**: three of the last
  four cycles subtracted a claim rather than added one. No planner behaviour has
  changed in 22 cycles on this branch.
- The one forward fact: at a *single* operating point, worst-case cross-track
  excursion is gradeable on **both** measured scenes (`1.46x`, `4.93x`), where
  the mismatched reading said one of them was ungradeable. 경로추종's worst case
  is more measurable than this branch believed, not less.

## Key learnings

- **A pin joined to another pin only by prose is not joined.** `drift()` compared
  the two columns' *arm names* and never their values, so a column taken at a
  different operating point read as agreement for four cycles. The repair that
  generalises is not this harvest — it is that a cross-module claim needs one
  executable re-derivation, which is why `retake_max()` is wired rather than
  described.
- **Harvest both columns in the same loop even when you only need one.** The TVaR
  half cost nothing extra and is the only reason this cycle can assert its
  construction is the right one instead of arguing it.
- The old column is still a legitimate measurement of a *different* operating
  point, so the retirement is by pin (`RETIRED_BY_ALIGNMENT`), not by deletion.

## Recommended next 1–3 priorities

1. **Re-price the citations that assume `dominance_holds()`** — `contrast_replicates`,
   `CONVOY_SPLIT`, `COLUMN_VERDICT`'s `cte_max` row and D-372/D-383/D-388 all
   quote a cross-experiment number.
2. **Decide whether `SEED_ENSEMBLE` is re-harvested wholesale** — `city_curved_v0`
   is the third `cte_max` cell and is still at the old operating point, so
   `COLUMN_VERDICT["cte_max"]` mixes two experiments.
3. **branch-scope decision (user, blocking)** — 22 cycles, zero planner change,
   queue frozen 39 days.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tail_mean.py, eval/mppi_sandbox/tests/test_column_alignment.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
