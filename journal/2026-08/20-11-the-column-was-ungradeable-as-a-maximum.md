# The column was never ungradeable — it was ungradeable as a maximum

- **Cycle**: 2026-08-20 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: research-flagged (Phase 0 candidate) — re-express the cross-track column as TVaR₀.₉
- **Phase**: P3
- **Status**: in_progress (receipt red on first take, repaired, **not pushed**)

## What I tried

- **Declined the three STATE next-actions.** All three were guard machinery
  (`review-reading-timing-audit`, `census-preempt-coverage`, `kd-shape-fix`),
  and taking any would have been the fourteenth consecutive zero-north-star
  cycle. Took the Phase 0 candidate instead: `research/feed.md`'s 04:00 entry
  (`2606.16511`) argues the cross-track column may be ungradeable **as a
  maximum** and gradeable **as a tail mean** at the same budget.
- Harvested TVaR₀.₉ (mean of the worst decile of `|cte|`) for 8 arms × 8 seeds
  on `cafe_convoy_v0` — 64 rollouts, 118 s — and graded it through the *same*
  `aa_calibration` null-gap floor machinery `cte_max` is graded through.
- Ran the source's **G5 threshold-stability gate** (`q ∈ [0.88, 0.92]`, a second
  64-rollout pass) before quoting anything, because finding #1 is exactly the
  shape threshold-shopping manufactures.
- `eval/mppi_sandbox/tail_mean.py` + 14 pytest cases.

## What worked / what failed

- **The re-expression works, and it is not marginal.** Same 64 rollouts:
  `cte_max` gap `0.0633` vs floor `0.0659` = **`0.96x`** (misses); TVaR₀.₉ gap
  `0.1381` vs floor `0.0523` = **`2.64x`** (clears). It also clears the
  adversarial `max_floor` at **`2.49x`**, which is the reading D-372/D-374
  grade on, so the rescue is not an artifact of floor choice.
- **Both halves of the ratio move, and the floor moves the right way.** The gap
  more than doubles (`2.18x`) while the floor *falls* (`0.79x`). A change of
  observable that only widened the numerator would look like a rescaling; this
  one separates arms further *and* is less seed-noisy — the estimator-class
  prediction.
- **G5 passes, and the failure mode is a continuum, not a cliff.** `2.80x` /
  `2.64x` / `2.45x` at `q = 0.88/0.90/0.92` — all clear, gap falling and floor
  rising monotonically. Extrapolating to `q → 1` (where TVaR *is* the maximum)
  lands on the `0.96x` `cte_max` actually measures. The observable was moved
  along an axis whose direction predicts the result.
- **A prose magnitude I estimated was wrong and a test caught it.** I wrote
  "`2.7x` between-cluster ratio" from the range endpoints; the cluster-mean
  ratio is **`3.0x`**. Same class as D-374's mixed denominators — caught
  pre-commit by pinning the partition rather than describing it.
- **`census_preempt` earned its 2 s twice**: `loop_reach.READING` missing my new
  test's row, and `tail_mean.retake` as consumer-reach residue (the *fourth*
  same-name `retake` — D-334's bare-name resolution again). Both would have
  been a red suite ~16 min later.
- **And then the suite went red anyway, on three pins the pre-empt reads as
  clean — the D-317/D-318 scope gap, third instance.** `3903 passed, 3 failed`
  in 1012 s. All three were my own arrivals: `default_lam_sites` `decides`
  104→105 and `total` 212→213 (`tail_mean.retake` names `lam = OPERATING_LAM`
  — the **sixth** consecutive D-274 bump), and `consumer_reach`'s *second*
  residue literal. The last one is the sharp one: `census_preempt`'s
  `consumer_reach_residue` returned CLEAN because it re-derives the population,
  while the failing test compares a **sorted literal** — I appended
  `tail_mean.retake` after `tail_stability.retake`, which is the wrong side of
  alphabetical. A census that re-derives cannot see an ordering defect in a
  hand-written list of the same members.
- **Not pushed.** The receipt is red and the gate refused, which is correct.
  All three pins are repaired and verified green (72 passed locally), but the
  repair created a new tree and the receipt on disk grades the old one — a
  second ~17 min suite is unaffordable at 40 min elapsed. The commit is left as
  a strand for the next cycle's REVIEW step 0, which is what that machinery is
  for (D-112/D-378): one suite discharges it, with no diagnosis left to do.

## North-star delta

- **First non-zero delta in fourteen cycles, and it is on the north star's
  경로추종 half.** Cross-track performance is *resolvable* at the budget already
  spent: eight arms partition into two clean clusters (`0.0548` vs `0.1649`
  cluster means, `3.0x`) with a `0.0960` divide that is `1.8x` the noise floor,
  while neither cluster's internal width reaches it.
- **The expensive prong of STATE's standing fork is retired at zero cost.** The
  512 rollouts were priced to buy a `2.10x` smaller floor so `cte_max` could be
  read. They are not needed to grade cross-track on this scene — and this is a
  *positive* result, not the §8 declared-margin equivalence fallback.
- Scope is one scene. `city_curved_v0` is unharvested for TVaR (118 s away).

## Key learnings

- **Six cycles read the `clearance`-clears / `cte_max`-fails asymmetry as
  evidence about scenes, bars, geometry, arms, seeds, and within-run samples.
  All six took the observable as given.** The seventh reading changed the
  observable and the asymmetry dissolved. When a column resists six explanations,
  suspect the column.
- **D-376 is not contradicted, it is relocated.** `tail_stability` refuted the
  estimator-class story on the *within-run* axis (`half_max/cte_max = 1.0000`,
  16/16). It is vindicated here on the *across-seed* axis. A maximum being
  stable inside a run and noisy across seeds is exactly what an order statistic
  should do — the two findings needed each other to be read correctly.
- **Running the source's own kill-gate before quoting the result changed what
  the result means.** G5 was budgeted as insurance against a shopped claim; it
  returned the monotone trend that turned finding #1 from "a luckier observable"
  into "a predictable position on an axis". The cheap check was the better find.
- **Thirteen cycles of guard machinery did not make this cycle possible** — the
  measurement used `aa_calibration`, which predates all of them. Worth weighing
  against the branch-scope question.

## Recommended next 1–3 priorities

1. **Harvest TVaR₀.₉ on `city_curved_v0`** (118 s) — the second endpoint. D-372
   showed the dividing line is the column, not the scene; one scene licenses
   nothing about the other.
2. **Restate the user-blocked cross-track claims on the graded observable** —
   `CLAIM_FORM` pins the only legal wording. The `0.96x` bars in STATE are about
   a statistic the branch can now stop trying to read.
3. **Retire `RESOLUTION_DEBT`'s 512-rollout prong from STATE** with this receipt
   attached, and put the branch-scope decision to the user with a non-zero
   delta on the table for the first time.

## Artifacts

- PR: #67 (already open — D-140: continuing on an open PR adds nothing to the queue)
- Files touched: `eval/mppi_sandbox/tail_mean.py`, `eval/mppi_sandbox/tests/test_tail_mean.py`, `eval/mppi_sandbox/loop_reach.py`, `eval/mppi_sandbox/tests/test_consumer_reach.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
