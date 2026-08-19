# The pairing rider's precondition fails on the half of the census that matters

- **Cycle**: 2026-08-19 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: Phase 0 candidate — the `2026-08-19 16:00` feed rider on STATE #1
- **Phase**: P3
- **Status**: keep

## What I tried

- The freshest feed entry (Pairing Seeds, `2512.24145`) attached a rider to
  STATE's next-action #1: before spending its **256 rollouts**, estimate the
  per-seed correlation `rho` between arms, because paired evaluation beats
  unpaired at the same budget **iff `rho > 0`**. It named the data — the 8x8
  `clearance_census.SEED_ENSEMBLE` already on disk — and priced the check at
  **zero rollouts**.
- Took it. New module `eval/mppi_sandbox/pairing_precondition.py`: seed-level
  Pearson over all 28 arm pairs, the predicted `sd_ratio = sqrt(1 - rho)` from
  the source's Theorem 1, and a `branch_wide_verdict()`.
- Picked this over STATE #2 (`head_on`'s interval across 8 seeds, 64 rollouts)
  because the elapsed reading left ~6 min before the suite deadline and this
  one is arithmetic on a constant, not a run.

## What worked / what failed

- **The precondition fails, and not in the tail.** Of the 26 non-degenerate
  pairs, **9 correlate negatively**. Range `-0.7402` to `+0.7963` — it
  **straddles zero**, which is the regime the source's own limit #2 says
  *reverses* the variance comparison. Verdict `SIGN_VARIES`.
- **The failures land on the load-bearing comparison.** The four most negative
  pairs all involve the baseline column: `essps_mppi` and `gap_gated_mppi`
  against `stock_mppi` (and against `geometric_mppi`, its exact clone) at
  `-0.7402` / `-0.6984`. Three of six baseline pairs grade `PAIRED_HURTS`. At
  `rho = -0.7402` the predicted `sd_ratio` is **`1.319`** — pairing would
  *widen* that interval by 32 % at the same budget.
- **The feed's own transfer-risk caveat is confirmed past where it aimed.** It
  read the paper's `rho = 0.681-0.993` (economic ABM, arms sharing nearly all
  dynamics) as "a best case our setting will not match", reasoning that MPPI
  arms with different cost functions diverge and divergence decorrelates. The
  honest correction is that the caveat aimed at the wrong end: our *best* pair
  (`0.7963`) lands **inside** their `0.681-0.993` band, so the ceiling roughly
  transfers. What does not transfer is the **floor** — their range is entirely
  positive and ours reaches `-0.7402`. The risk was never that our correlations
  would be uniformly weaker; it is that they change sign.
- **A by-product that pays for itself.** The two pairs at exactly `+1.0000` are
  `geometric x stock` and `frozen_risk x risk` — precisely the two
  `clearance_census` documents by hand as inert channels. Perfect seed-level
  correlation *is* the inertness signature, so this statistic detects it
  independently. `DEGENERATE` excludes them so two constructed `1.0`s do not
  flatter the tally.
- Caught by `census_preempt` at the stage: guard pool `126` vs pin `125`. The
  entrant is `against_baseline` — the one function narrowing by **membership**
  (`BASELINE in (...)`) rather than by a float comparison. All four *findings*
  stayed out, exactly as the pool's own stated rule predicts.

## North-star delta

- **Zero rollouts, and it removes a 256-rollout mis-spend.** STATE #1 was about
  to be reported one way; there is now a measured reason that a branch-wide
  paired report would be wrong for at least three of six arm pairs.
- No new avoidance or tracking number. This buys **method**, not metres — it
  changes how the next measurement is read, not what it reads.

## Key learnings

- **The rider survives per-pair and dies as a policy.** There is no single
  answer to "report the widening paired?", only an answer per arm pair, and it
  must be taken on the scene being widened — this is `cafe_freezing_v0` only.
- **A free precondition check can be worth more than the measurement it
  guards.** The whole finding cost one `json`-free arithmetic pass over a
  constant that has been on disk since 2026-08-17.
- **The feed's caveats are load-bearing and were right.** Limit #3 (pairing
  cannot reach D-365's cross-*scene* pair) still stands untouched; limit #1 (no
  seed-count guidance) means this says nothing about whether 8 is enough.
- Three entrants running, the guard pool's rule has held verbatim: findings
  spelled as float comparisons stay out, narrowings spelled as set/membership
  tests come in — regardless of what either is *for*.

## Recommended next 1–3 priorities

1. **STATE #2 — does `cafe_head_on_v0`'s `0.1964` interval survive 8 seeds?**
   64 rollouts (~90 s by D-360's price), de-risks the top user-blocked repair.
2. **STATE #1 with the rider applied**: 8 seeds on the four excited scenes, and
   take `rho` per arm pair **on those scenes** before choosing paired vs
   independent reporting. This cycle's `SIGN_VARIES` says the choice is real.
3. **Q-168** — `--durations` on the next `push_preflight record`; the suite runs
   anyway and the top-10 table is free.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/pairing_precondition.py, eval/mppi_sandbox/tests/test_pairing_precondition.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md
- TSV row appended: yes
