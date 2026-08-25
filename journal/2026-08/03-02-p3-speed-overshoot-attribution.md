# The overshoot was a property of the yaml file, not the controller

- **Cycle**: 2026-08-03 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE claude-actionable #1 — explain the 1.8× `target_speed_mps` overshoot (Q-045)
- **Phase**: P3
- **Status**: keep

## What I tried

- Q-045 named three candidate defects for D-022's "the loop does not track
  `target_speed_mps`": (a) the scenario setting, (b) the cost weights
  (`w_terminal = 30.0` vs `w_speed = 2.0`), (c) a missing speed-tracking term.
  Tested all three on `cafe_obstacle_crossing_v0`, seeds 0–3.
- **Registered the analytic prediction before running**: the one-segment
  stationary point `Δ* = w_terminal·T·D / (w_speed·H + w_terminal·T²)`, which
  says the terminal term buys speed until `v_max` binds.
- Swept `w_terminal`, `w_speed`, `v_max`, and `target_speed_mps` independently,
  and compared measured cruise against the registered prediction.
- Shipped `eval/mppi_sandbox/speed_audit.py` + 15 tests.

## What worked / what failed

- ✅ **(c) is false by inspection** — `w_speed·Σ(v−v_ref)²` has been in
  `_cost` since the baseline. Also excluded the weaker reading (D-021's
  `w_epist` failure mode: term present, softmax no-op): raising `w_speed`
  alone moves the loop.
- ✅ **(b) is true and two-directional** (D-018 discipline): `w_terminal = 0`
  drops realized speed 0.519 → **0.146**; `w_speed = 60` drops it to **0.237**.
  Both arms still reach the goal, so neither bought the reduction by stalling.
- 🔴 **(a) is false, and it is the finding.** A **4× sweep** of
  `target_speed_mps` (0.15/0.30/0.60) moves realized speed **3 %**
  (0.508/0.519/0.523). The declaration enters only via the warm start
  `U[:, 0]` and the `v_ref` cap; neither survives the first few updates.
- 🔴 **So "the loop overshoots by 1.8×" is not a controller property.** The
  same controller on the same scene at `target_speed_mps: 0.6` reads
  realized/declared = **0.87** — undershoot. The ratio straddles 1.0 under a
  change to a field the loop never reads. D-023's band is real; its cause is
  not a tracking failure to fix, it is that `nominal_traversal` is driven by a
  quantity the closed loop does not read.
- 🔴 **Q-045's option set was missing the actual ceiling.** Cruise is
  `min(v_max, f(w_terminal/w_speed))`: at `v_max` 0.4 → cruise/`v_max` 0.84,
  at 0.6 → 1.00 (the limit binds); at 0.8 and 1.2 cruise pins at **0.709 both
  times** (the ratio binds). `target_speed_mps = 0.3` is the ceiling in
  neither regime.
- 🔴 **My registered analytic model was refuted** — measured 0.714 vs predicted
  0.462 near the goal, 0.215 vs 0.576 far away at `w_terminal = 3`, and the
  **error sign flips** with `w_terminal`. Cause is D-021's again: median ESS is
  **1.46 of K = 256**, so the update is argmin-over-draws, not a step toward a
  stationary point. Kept in the module *as refuted*, pinned by test.
- ✅ **The statistic was wrong too.** `ab.mean_speed` averages accel transient
  + cruise + goal ramp. Binning by `d_goal` does **not** fix it — on a
  single-pass path large `d_goal` *is* early time, so the far bin is mostly
  transient. That confound is exactly what made the closed form look plausible
  at one `w_terminal`. `cruise_speed` cuts both ends and returns NaN for a
  stall rather than crediting it with a speed.

## North-star delta

- **No capability movement — eighth consecutive methodology cycle.** What it
  buys is a *retraction with a replacement*: D-022's attribution is corrected,
  D-023's band survives with a different cause, and a reusable correct speed
  statistic now exists where three prior cycles hand-rolled a confounded one.
- Scenes able to contribute an avoidance number: **5**, reportable: **4** —
  unchanged. No tracking metric improved, no repo default touched.

## Key learnings

- **A ratio whose denominator nobody reads is not a measurement.** The
  cheapest test of "X does not track Y" is to sweep Y: if the output does not
  move, Y was never an input, and the ratio was describing a declaration.
- **Registering a closed form before the sweep is what made its refutation
  cheap** — and the refutation is more useful than a fit would have been,
  because it names the precondition ("MPPI optimises its cost") that ESS ≈ 1
  denies. Any closed form derived from the objective is suspect in this repo
  until the ESS it ran at is quoted.
- **A confounded statistic can validate a wrong model.** Distance-binning felt
  like the fix for the transient and is not one on a single-pass path; it
  produced agreement at one `w_terminal` and disagreement at another, which is
  the signature to look for.
- **Q-045's three options were an incomplete partition.** The real ceiling
  (`v_max`, then the weight ratio) was in none of them. Worth checking that an
  option set is exhaustive before treating "not (a), not (c)" as evidence
  for (b).

## Recommended next 1–3 priorities

1. **Decide whether `nominal_traversal` should be driven by `v_max` and the
   weight ratio instead of `target_speed_mps`.** D-024 says the current driver
   is not an input to the loop; the two quantities that *are* inputs are both
   available without simulating. This could shrink D-023's band at its source.
2. **Re-run the audible/deaf partition through `reach_on_trajectory`** — still
   unblocked, still the original STATE #1 deliverable, and `reach.py` warm-starts
   its fan at `target_speed` (`reach.py:176`), which D-024 just showed the closed
   loop abandons. The fan may be built at the wrong speed.
3. **Decide whether `cafe_cut_in_v0` gets fixed or retired** — unchanged, and
   now the cheapest scene-level debt in the repo.

## Artifacts

- PR: #67 (in place — 20th consecutive cycle on an already-queued branch)
- Files touched: `eval/mppi_sandbox/speed_audit.py` (new),
  `eval/mppi_sandbox/tests/test_speed_overshoot_attribution.py` (new),
  `docs/decisions.md` (D-024), `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
