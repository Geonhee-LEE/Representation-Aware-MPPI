# The censored rungs are the ones that separate most

- **Cycle**: 2026-08-10 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: Phase 0 candidate — re-grade the censored scenes with margin-free statistics (feed 2026-08-10, arxiv 2605.18045)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the feed's 2026-08-10 suggestion (2605.18045) over STATE #1's min-lidar
  ablation: both target the same bottleneck, but this one runs on the
  **already-recorded** per-seed clearances at zero sim cost, and the branch has
  just spent two cycles proving the threshold route cannot be repaired.
- New `eval/mppi_sandbox/margin_free.py`: for each of the 6 walked rungs, the
  rank statistic `A = P(risk > stock) + ½·P(=)` over all 32×32 cross pairs, plus
  a **paired** bootstrap CI on the mean per-seed difference and a TOST verdict
  (`EQUIVALENT` / `SUPERIOR` / `INFERIOR` / `INDETERMINATE`).
- Built the population off `derived_margin.walked_rungs()` rather than a second
  copy, so the coverage contrast between the two censuses shares a denominator.
- 25 tests, including the invariance property the margin-freeness claim rests on.

## What worked / what failed

- 🟢 **Coverage 6/6 rungs, 3/3 scenes** against the derived route's 2/6 and 1/3.
  Every rung both threshold censuses had to drop has a margin-free reading. The
  population was never the limit — `A` is defined on any two non-empty samples.
- 🔴 **The censoring is anti-informative, strictly.** Rank the six rungs by
  `|A − ½|` and the three the margin route calls `NO_TWO_SIDED_TO_SPREAD` are the
  three **largest**: convoy `w=75` at `A = 1.0000` (clearance ranges disjoint),
  head_on `w ∈ {75,100}` at `0.9980`. The three it can score are `0.9473`,
  `0.8457`, `0.4980`. `min |A−½|` over censored = `0.4980` > `max` over scored =
  `0.4473`. A rung is unscoreable **because** the arms separate so completely
  that no threshold has both interior — so "0/3 two-sided" (D-164) was a
  statement about the instrument, and the censuses were discarding their own
  strongest evidence.
- 🟢 **D-164's most threshold-dependent rung is the measured tie.** Crossing
  `w=250` — 46 thresholds, four verdicts, no majority — is `A = 0.4980` with a
  paired CI of `[-0.0231, +0.0183]` containing zero. `MARGIN_DECIDES_VERDICT`
  and "no effect exists" are one fact: with no signal the threshold picks the
  answer. It now reads `EQUIVALENT` at ε = 0.05 m, a positive verdict where the
  census had an absence.
- 🟢 **Margin-freeness is proved as a property, not by example**: `A` is pinned
  invariant under four strictly increasing warps (`v³`, `log`, affine, `tanh`)
  on all six rungs. A numeric-only test would pass on a statistic that was not
  rank-based.
- 🟡 `INFERIOR` and `CENSORING_ALIGNED`/`MIXED`/`UNCOMPARABLE` have no shipped
  witness (nothing favours stock; the population is two-sided), so each is
  proved synthetically — including the one-sided-population case, which is
  D-107's shape: a group-separation test on an empty group is vacuously true and
  must not print as a finding.
- 🟡 First draft of `CENSORING_ALIGNED` was **not** the mirror of the ANTI
  branch — it tested `max(scoreable) > max(censored)` rather than
  `min(scoreable) > max(censored)`, so a single strong scoreable rung would have
  claimed group separation. Caught while writing its reachability test.

## North-star delta

- **First margin-independent, all-three-scene evidence for the mechanism**: 5 of
  6 rungs favour the risk arm, 1 is a tie, none favour stock. Every prior
  positive reading in this branch sat on the one published scene.
- **Headline unmoved and this cycle does not claim otherwise**: `unsafe_rate`
  **0.0000** / `min_clearance` **0.3579** / `success_rate` **1.0000**. `A` orders
  two clearance *distributions*; it is not a safety claim. `unsafe_rate` is zero
  at the declared margins precisely because both arms clear those floors — the
  same censoring seen from the other side.
- No controller / representation / dynamics code, no sim runs.

## Key learnings

- **"Unscoreable" and "no effect" were being read as the same thing and are
  opposites here.** Two censuses closed on `0/3` and `1/3`; the rungs they
  dropped carry the largest effects in the population. Any future census should
  report the effect size of what it censors before concluding anything from the
  censoring.
- **The threshold was never load-bearing for this comparison.** Six rungs, three
  scenes, zero sim runs, and a verdict on every one — after two cycles spent
  looking for a threshold that could host it. Cheaper instruments were available
  the whole time.
- **This does not rescue the epistemic quantity.** The 2607.16591 ablation
  (STATE #1) asks whether a plain min-lidar term does the same job in the same
  cost slot; a positive `A` for the risk arm is consistent with that too. The
  ablation is now the discriminating experiment, not a redundant one.

## Recommended next 1–3 priorities

1. Run the feed's one-variable ablation (2607.16591) — plain min-lidar term in
   the epistemic term's cost slot, graded with `margin_free.superiority` rather
   than a threshold, on the walked rungs. Now discriminating.
2. Re-measure the `w = 250` crossing cell at 16 seeds (carried, D-163) — it is
   the tie rung, so the seed licence matters most there.
3. Make `sandbox:pass=N` state `passed` vs `executed` (carried four cycles).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/margin_free.py, eval/mppi_sandbox/tests/test_margin_free.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
