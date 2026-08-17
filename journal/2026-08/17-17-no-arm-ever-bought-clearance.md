# No arm on this branch ever bought clearance — plain MPPI out-clears all five

- **Cycle**: 2026-08-17 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — run the clearance column across the shipped arms
- **Phase**: P3
- **Status**: keep

## What I tried

- Took D-326's 8th column (min surface-to-surface clearance) across the **whole
  controller registry** instead of the one pair it was measured on — the
  bottleneck asks about the *branch*, and a pairwise reading cannot answer that.
- Three of the eight arms refused the epistemic kwargs (`TypeError:
  unexpected keyword argument 'w_voo'`); measured them in the configuration
  their constructors accept and recorded the split rather than dropping them.
- Shipped `eval/mppi_sandbox/clearance_census.py` + 9 tests: recorded census,
  `grade()` → `Verdict`, and `takes_epistemic_kwargs()` which **derives** the
  population split so a future `REGISTRY` line cannot land on the wrong side.

## What worked / what failed

- **The answer is no, and the baseline is why.** `stock_mppi` — no
  representation channel of any kind — clears `0.5152 m`, and all five
  representation arms sit below it (`−0.10` to `−0.18 m`). The three arms this
  branch spent the most cycles on (`risk` / `frozen_risk` / `essps`) are the
  registry's **bottom three**.
- The one arm that beats the baseline is `cbf_mppi` (`0.7856`, `+0.27`) — a
  **constraint** method, not a representation. Counting it as evidence for the
  core hypothesis would credit the win to the wrong mechanism, so it is
  excluded from `REPRESENTATION_ARMS` and the exclusion is a test.
- ⚠️ **I typed two assertions from memory and both were wrong** — `social_mppi`
  as best representation arm (it is `gap_gated_mppi`, `0.4126` vs `0.4050`) and
  a line count off by one. The measured values corrected them within 30 s
  because the test ran against the numbers rather than my recollection of them;
  had the census been prose, both would have shipped.
- **The obvious confound does not hold.** Arms split into a fast class
  (110–158 steps) and a slow one (932–1011), and the high clearances are in the
  slow class — but min-over-episode can only *fall* as an episode lengthens, so
  length works against the winners. The ranking survives in the direction that
  matters.
- Side finding: `geometric_mppi` reproduces `stock_mppi` in **all three**
  columns — the signature of an inert channel, not agreement. Pinned as a test.
- ⚠️ **The suite came back red at minute 26**, on three census pins my own new
  module moved: `default_lam_sites` (`decides` 99→101, total 207→209, margin
  31→33 — both `MPPIParams(lam=OPERATING_LAM)` sites in `clearance_census`) and
  `consumer_reach`'s module residue (`retake` has no production caller, same
  shape as `essps.compare_arms`). All three were principled moves, but they
  cost a **second 14-minute suite** and pushed the cycle to ~45 min.
  `census_preempt` ran clean twice and was right to — its own `UNCOVERED` line
  names `inert_surface pins` and `extremum_reading.SITE_CLASSES`, and these
  three live in exactly that uncovered set. The reading was honest; the gap is
  that no cheap check on this path covers the pins a *new module* moves.

## North-star delta

- **First measurement on this branch that prices its own premise against the
  no-representation baseline.** Every prior clearance/ESS reading here compared
  representation arms to *each other*; against plain MPPI, the branch's
  avoidance work is `0.17 m` in the wrong direction on this scene/seed.
- Obstacle avoidance is half the north star, and the branch now has a ranked,
  reproducible census of where each arm stands on it (8/8 arms, one command).
- Honest bound: one scene, one seed. The *sign* is claimable (gaps are 13–14×
  the `0.0128 m` D-326 declined to claim); the *magnitude* is not.

## Key learnings

- **A pairwise verdict cannot answer a branch-level question.** D-326 was
  correct and its scope was one pair; the bottleneck sentence needed a census,
  and the census inverted the framing — the interesting comparison was never
  between two representation arms.
- **Optimizing a sampler property does not move a robot property.** Many cycles
  went into ESS band compliance; the arms with the best compliance have the
  worst clearance. That is D-274/D-326's lesson at branch scale.
- **This is the first result here worth a seed ensemble.** D-326 cancelled one
  because there was no trade to price. There is now a `0.17 m` deficit to
  confirm or refute — Q-159, leaning at the cheap pair first (~8 min) rather
  than the full 8×8 (~32 min).

## Recommended next 1–3 priorities

1. **Q-159 (c)** — `essps_mppi` vs `stock_mppi` across 8 seeds; measure per-arm
   seconds first, since D-326's cost self-estimate was 15× high.
2. **Ask why `cbf_mppi` wins** — if the clearance comes from the constraint and
   not the input, the branch's hypothesis needs the CBF arm as its control, not
   `risk_mppi`.
3. **Extend `census_preempt` to the pins a new module moves** — this cycle paid
   14 min for three pins its `UNCOVERED` line already named. A module-count /
   lam-site delta is derivable in seconds from the staged diff, and it is the
   one drift class a *new file* reliably causes.

## Artifacts
- PR: #67 (existing, reused — queue stays at 6)
- Files touched: `eval/mppi_sandbox/clearance_census.py`,
  `eval/mppi_sandbox/tests/test_clearance_census.py`, `docs/decisions.md`
  (D-327), `docs/deliberations.md` (Q-159), `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
