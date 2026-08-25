# The published delta inverts at a matched temperature — Q-107 answered, and by more than it asked

- **Cycle**: 2026-08-08 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — answer Q-107 (is the cross-controller delta on a per-arm-temperature scene a controller difference or a temperature difference?)
- **Phase**: P5
- **Status**: keep

## What I tried

- Ran the 2×2 grid Q-107 specified on `cafe_obstacle_crossing_v0`: both arms
  (`stock_mppi`, `risk_mppi`) at **both** rungs (`0.8`, `3.2`), 8 seeds each,
  32 runs, 27 s. The published cell pair is the diagonal; the off-diagonal is
  the counterfactual.
- Shipped the arithmetic as `temperature_confound.decompose()`: the reported
  delta splits **exactly** into a temperature-matched delta plus a
  same-controller temperature term, at each of the two rungs.
- Graded with a worst-first ladder — `SIGN_FLIP` → `MASKED` →
  `TEMPERATURE_DOMINATED` → `ROBUST` — so a delta whose *sign* is unstable is
  not additionally graded on what fraction of it temperature explains.
- Re-ran the whole thing at `ab.ABTemperature.lam_for`'s rungs (`0.8`/`1.6`,
  gap 2×) to price the matrix's choice of rung reader against the alternative
  already in the tree.

## What worked / what failed

- 🔴 **The confound is real and it inverts a sign.** On `min_clearance` the
  matrix publishes `risk − stock = +0.0205` (risk keeps 20 mm more room); run
  both arms at `0.8` and it is **−0.0078** — risk keeps 8 mm *less*. The
  temperature term is **138%** of the delta it lives inside. Verdict
  `SIGN_FLIP`.
- 🔴 **The headline safety scalar is masked.** `unsafe_rate` publishes
  **exactly 0.0000** (8/8 both arms), while at a matched `0.8` risk_mppi is
  **0.875 vs 1.000** — one seed in eight. A published zero was reporting *no
  difference* where a temperature-matched comparison finds one.
- 🟡 **`mean_clearance` survives, by 1.3 points.** Share 0.487 against a 0.500
  line, verdict `ROBUST`. That is a pass and it is not a comfortable one; the
  same controller reproduces nearly half of its rival's published advantage by
  changing nothing but λ.
- 🔴 **Q-107's trade-off was the wrong trade-off.** It framed (a) vs (b) as
  *confounded comparison vs sample retention*. But `verdict="per_arm"` means
  the windows are **disjoint**, so "both arms at one temperature" and "both
  arms in band" cannot both hold — every matched comparison above ran with an
  arm out of its Q-026 band, by construction, not by shortcut. Both available
  protocols are impure; they are impure in different *kinds*. Pinned as
  `test_crossing_admits_no_in_band_matched_comparison` (table-only, zero sims)
  and carried per-rung as `MatchedDelta.out_of_band`.
- 🟡 **The tree already holds two disagreeing answers to "which rung".**
  `baseline_matrix.pick_lam` (log-middle of the arm's own window) gives
  `stock 0.8 / risk 3.2`, gap **4×**; `ab.lam_for` (minimum log-gap to the
  other arm) gives `stock 0.8 / risk 1.6`, gap **2×**. Both shipped, both
  correct for what they optimise, and the matrix consults the one that carries
  twice the impurity.
- ✅ **The confound share tracks the gap, and only the quantitative part.**
  At 2× the `mean_clearance` share halves (0.487 → 0.252). `min_clearance`
  stays `SIGN_FLIP` and `unsafe_rate` stays `MASKED` — the inverting rung is
  `0.8`, which both protocols keep. Halving the gap is a real improvement and
  not a fix.

## North-star delta

- The first **falsification of a published cross-controller number** in this
  project: D-119's directional controller signal on this scene does not
  survive a temperature-matched re-read, and one of the three metrics reverses.
- Zero movement on `success_rate` / `unsafe_rate` themselves — no controller
  changed. What changed is which of the existing numbers may be attributed to
  the controller axis at all.
- The bottleneck's stated blocker is cleared: Q-107 blocked reading the
  cross-controller delta on `cafe_obstacle_crossing_v0`, and the answer is that
  on this scene the delta is not readable as a controller delta on two of
  three metrics — so a cost-term change there must be judged against its own
  arm at a fixed λ, not against the other arm.

## Key learnings

- **A zero delta is not evidence of no delta.** `unsafe_rate` published
  `0.0000` on a comparison whose matched counterpart is `−0.125`. The `MASKED`
  rung exists because "no difference found" and "difference cancelled by a
  confound" print identically and mean opposite things.
- **When a comparison has two impurities, naming the trade as one-vs-the-other
  hides that both branches are impure.** Q-107's own (a)/(b) framing did that;
  the measurement did not refute the lean toward (c), it refuted the axis the
  question laid the options on.
- **The sign is the cheap check and it is the one that fired.** Share-based
  thresholds need a line (0.5, arbitrary); a sign inversion needs none, and it
  was the sign that killed `min_clearance` while the share let it through at
  1.381 only because the ladder checks sign first.
- **Two shipped readers for one choice is a D-047 smell even when neither is
  wrong.** Nothing here is a bug; the cost is that the matrix silently picked
  the higher-impurity option and no reader compared them until now.

## Recommended next 1–3 priorities

1. **Point `baseline_matrix` at `ab.lam_for` instead of `pick_lam`** for
   `per_arm` cells — halves the measured confound on this scene for free, and
   removes the second statement of "which rung" (D-047).
2. **Split the headline axis (Q-107 option (c))** — report cross-controller
   deltas only for `ROBUST` cells and name the rest by verdict, the way
   `excluded` already names unrun cells. Now backed by measurement rather than
   by the lean.
3. **Attack `cafe_obstacle_crossing_v0`'s 8/8 unsafe directly** — unchanged
   from last cycle and now unambiguous: judge the change against `stock@0.8`
   itself, since the cross-arm comparison on this scene is not readable.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic → #67)
- Files touched: `eval/mppi_sandbox/temperature_confound.py`, `eval/mppi_sandbox/tests/test_temperature_confound.py`, `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
