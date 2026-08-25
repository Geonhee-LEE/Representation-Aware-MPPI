# `K` is the repair axis `lam` was not — and the repair is to use *fewer* samples

- **Cycle**: 2026-08-16 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<move-the-ensemble-off-the-lam-axis>` (STATE #1)
- **Phase**: P3
- **Status**: keep

## What I tried

- D-291 closed the `lam` axis on the upper endpoint of the `w = 5` unanimous
  window: every miss above the run is over the *ceiling*, so repair means
  moving the ensemble **down**, and median ESS rises strictly with `lam` there.
  It named the successor question — find a common factor that is not `lam` —
  and `K` was the first untested candidate.
- Walked `K ∈ {128, 512}` at `lam = 1.15`, `w = 5`, the census 16 seeds
  (32 closed-loop runs, ~4 min concurrent by column). `K = 256` is the existing
  `MEASURED_SEEDS_16_LAM115`, reused rather than re-walked.
- Shipped `ensemble_scaling_in_k()` — the first reader on this branch that
  fixes the temperature and walks the sampler count.

## What worked / what failed

- **The repair exists and it is measured, not arithmetic.** `K = 128` is
  **`16/16`** at `lam = 1.15` — the temperature that misses at `K = 256`. This
  is the first thing on this axis that is an actual unanimous cell rather than
  a statement that some common factor would suffice.
- **The direction is downward in `K`, which is backwards from the intuition.**
  The band is `(0.05K, 0.5K)`, so membership lives in `median ESS / K`; that
  coordinate *rises* with `K` (`0.2396, 0.3093, 0.3705`). Fewer samples, not
  more, is what puts the ensemble back inside the window.
- **`K` is not a common factor at all.** A common factor leaves `span`
  (a ratio) fixed. `K` does not: `3.80x → 5.37x → 18.63x`. At `K = 512` the
  span **exceeds the `10.0x` band**, so D-283 disqualifies that column
  structurally, and it is the first column on this branch to miss at *both*
  edges. Raising `K` does not translate this ensemble — it pulls it apart.
- Membership decays monotonically (`16, 15, 11`) but the two failures differ in
  kind: `256` slid off the ceiling (span still admissible), `512` came apart.

## North-star delta

- The `w = 5` operating window has its first cell that is unanimous at a
  temperature previously recorded as failing — `(lam, K) = (1.15, 128)`.
- Still one scene (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`.
  No obstacle-avoidance, clearance or near-miss number moved.
- A negative result worth as much as the positive one: the "more samples is
  better" reflex is false on this axis at this cell, and `K = 512` is
  structurally unusable.

## Key learnings

- **Check whether the axis moves the ruler too.** `K` scales the band and the
  ensemble together, so raw median ESS points the wrong way for the membership
  question. Both sequences are returned so neither can be quoted for the other.
- **"Common factor" is a testable property, not a synonym for "knob".** Three
  cycles reasoned about repairs using common-factor arithmetic; the first axis
  actually walked turns out not to be one. `span` is the test and it is cheap.
- **A measured unanimous column beats a direction.** D-291 caught STATE quoting
  `translated_out_of_band` as if it were actionable; the flag here is
  `repair_is_measured_not_arithmetic` for exactly that reason.

## Recommended next 1–3 priorities

- Walk the temperature column at `K = 128`: is the unanimous `lam` run *wider*
  at lower `K`, or just shifted? The bracket `{1.0, 1.1}` was measured at 256.
- Bracket `K` between 128 and 256 (e.g. 192), and below 128 — is there a floor
  where the ensemble falls out the bottom?
- `w_obs_soft`, the remaining untested candidate, and the only one still
  plausibly a true common factor.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, journal/2026-08/16-02-k-is-the-repair-axis-lam-was-not.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
