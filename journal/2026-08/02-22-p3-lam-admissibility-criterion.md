# Q-042 answered from stored counts: the quantile criterion was a no-op, the interval one inverts the bias

- **Cycle**: 2026-08-02 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` Q-042 — compare the three admissibility criteria from existing probe data
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE item #1 on its own terms: it gated the whole cycle on "does
  `ab.LamProbe` retain per-seed ESS?". **It does not** — and the gate was the
  wrong question. Seeds are exchangeable, so `(n_in_band, n)` is a *sufficient
  statistic* for the per-seed in-band indicator vector, and all three Q-042
  criteria are functions of that pair. The in-band half was always re-scorable.
- Scored (a) all-seeds, (b) quantile ≥⌈0.9n⌉, (c) interval estimate on D-019's
  actual flip — `stock_mppi @ lam = 1.6` on `cafe_obstacle_crossing_v0`,
  measured **4/4 in band at n = 4, 7/8 at n = 8, 8/8 reaching at both**, so the
  case is about the band alone and nothing else moved.
- Shipped the criteria as `ab` API (`all_seeds`, `at_least_quantile`,
  `wilson_lower_at_least`, `wilson_lower`) with `admissible_lams(probes,
  criterion=...)`. Default stays `all_seeds` per D-019 — no window in the repo
  moves — with a test pinning that invariance.
- Added `LamProbe.n_reached`, sentinel `-1` for pre-existing probes.

## What worked / what failed

- **(b) is a no-op, not a near-miss.** `ceil(0.9n) == n` for every `n ≤ 9`, so
  at the only two seed counts this repo runs it is *pointwise identical* to
  (a) — same verdicts, same monotone bias. It becomes a distinct rule at
  n = 10. Arithmetic; zero simulation. One of the three options was never a
  different option.
- **(c) inverts D-019's bias instead of softening it.** At `k = n` the Wilson
  lower bound is exactly `n/(n+z²)`, strictly *increasing* in `n`: seeds that
  pass buy confidence rather than spend it, so a window can **grow** with
  evidence. On the measured flip: **0.510 at n = 4 → 0.529 at n = 8**. The one
  lost seed is more than paid for by the four extra draws, and the verdict
  holds for any threshold outside the sliver `(0.510, 0.529]`.
- **Three of my own claims failed their own tests and were corrected**, which
  is the part I'd have got wrong writing prose: `ceil(0.9·10) = 9` not 10 (the
  no-op range is n ≤ 9); `wilson_lower(0, 8)` is *exactly* 0.0, not merely
  small; and the bootstrap does **not** agree with the closed form at n = 8 —
  it reads 0.625 vs 0.529.
- That last disagreement is the cycle's one genuine surprise and it **argues
  for** (c)-as-closed-form: a resample of n draws lives on the lattice
  `{0, 1/n, …}`, so at n = 8 its step is 0.125 while the effect Q-042 must
  resolve is 0.019 — seven times smaller than the estimator's own granularity.
  Gap shrinks 0.096 → 0.036 → 0.001 at n = 8 / 40 / 1000. My first draft also
  claimed the gap is bounded by one lattice unit; n = 40 refutes that (Wilson's
  small-sample conservatism adds on top), and the test now says so.

## North-star delta

- **No capability movement** — still measurement methodology. Scenes able to
  contribute an avoidance number: **5**, reportable: **4**, unchanged.
- But the *protocol* debt shrank rather than grew for the first time in four
  cycles: Q-042 opened with three options and closes with one refuted, one
  retained-as-default, one shipped-and-evidenced. The re-baseline (STATE #7)
  now has a criterion to regenerate *into* rather than a question to answer.
- Cost: **two seed sweeps**, both of which D-019 had already paid for.
  Everything else in the new file is arithmetic on constructed probes.

## Key learnings

- **"Does the artifact retain X?" is usually the wrong gate — ask what the
  computation actually needs.** The per-seed ESS values were never required;
  a two-integer summary carries the whole in-band verdict. A cycle was queued
  behind a storage question that a sufficiency argument dissolves.
- **The asymmetry is where the real defect was.** `n_in_band`/`n` survived as
  counts; completion was collapsed to a boolean, and `all_reached=False` maps
  to anything in `[0, n)`. Same monotone-conjunction bug D-019 found, in the
  one field that could not be re-scored. Booleans derived from conjunctions
  should keep their count.
- **A criterion can be refuted by arithmetic before it is ever run.** (b) cost
  one `ceil` to kill. Worth screening options that way before costing runs.
- **Writing a claim as an executable assertion catches what prose does not.**
  Three of this file's headline numbers were wrong in the first draft and the
  tests said so within seconds; a docstring would have shipped all three.

## Recommended next 1–3 priorities

- **Ablate `w_epist` on the crossing scene** — now the only surviving lead on
  the mechanism rather than a correlate, and it is unblocked.
- **Re-baseline (STATE #7) regenerates windows under both (a) and (c)** and
  reports where they disagree; that disagreement set is the honest scope of
  D-019's `n` stamp.
- **Pick a threshold for (c) empirically** — this cycle deliberately picked
  none, and the criterion is not usable as a default until one is justified.

## Artifacts

- PR: #67 (already open — no new review bandwidth)
- Files touched: `eval/mppi_sandbox/ab.py`,
  `eval/mppi_sandbox/tests/test_lam_admissibility_criterion.py`,
  `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
