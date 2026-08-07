# The re-run refuted its own plan, and the one rung that worked is below the threshold

- **Cycle**: 2026-08-08 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-run D-119 / D-124's A/Bs above the relief threshold
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE's #1 literally: the two shipped mechanism claims were both A/B'd at
  `w_obs_soft = 10`, ~30× below where either arm can pass, so re-run them at the
  operating weight D-130 shipped (`cafe_head_on_v0` → **3000**).
- Built `comparison_headroom.py` first, because "neither arm can pass" needed a
  name before it could be a finding: `NO_HEADROOM_UNSAFE` / `NO_HEADROOM_SAFE` /
  `TIED` / `SEPARATED`, plus `shift(before, after)` to grade a re-run and
  `sub_margin` for a delta whose whole span sits on one side of the boundary.
- Measured the full ladder rather than just the two endpoints: λ = 0.8 (both
  arms admissible), 8 seeds, `w ∈ {10, 30, 100, 300, 3000}`, three arms.

## What worked / what failed

- 🔴 **The plan was wrong, and the measurement says so.** Re-running at the
  operating weight does **not** convert D-124's A/B into a test. At `w = 10`
  both arms are `unsafe_rate = 1.0000`; at `w = 3000` both are **0.0000**
  (`min_clearance` 1.1089 / 1.1143). `shift` → `STILL_UNSCORABLE`. One
  degenerate verdict swapped for the other — the barrier weight alone solves
  the scene at its own operating point, leaving the mechanism nothing to be
  measured against.
- 🔴 **The gap gate is unscorable at every rung on the ladder.** Its
  mean-clearance deltas alternate sign (0.0293/0.0289, 0.3035/0.3068,
  0.5806/0.5791). D-124's headline 1.7× on head_on was `sub_margin`: both ends
  ~50× below the scene's declared 0.40 m, so no run ever changed verdict. The
  number was real; the improvement was not a safety improvement.
- ✅ **The risk channel separates — at exactly one rung, `w = 100`:**
  stock **1.0000** → risk **0.2500** unsafe, both arms in the ESS band, 8/8
  reached. First mechanism claim this project has scored where the headline
  could have moved either way.
- 🔴 **And that rung is *below* the relief threshold (300).** The instruction
  STATE gave would have landed on 300 or 3000, both `NO_HEADROOM_SAFE`, and
  reported a null. This is structural, not bad luck: a threshold is the weight
  above which the **scene** passes, which is the weight above which a
  **comparison** stops discriminating. The scorable band *is* the transition,
  and the transition ends where relief begins.
- 🔴 **λ calibration is not weight-invariant.** At `w = 30`, stock and
  gap_gated both leave the ESS band at the same λ = 0.8 that is in-band at 10,
  100 and 300. `lam_windows.yaml` was measured at the shipped weight; any
  rescore at another weight owes a per-rung ESS check.

## North-star delta

- **First scored avoidance mechanism.** `risk_mppi` cuts `unsafe_rate` 1.0000 →
  0.2500 on `cafe_head_on_v0` at an operating point where the comparison is
  admissible. Not significant at n = 8 on its own, but it is the first such
  number that is not pinned by construction.
- **One shipped claim downgraded, honestly.** D-124's head_on 1.7× is
  `sub_margin` and directionless on re-measurement — it should not be carried
  as evidence the gate helps.
- Headline unchanged: the 5-cell / 40-seed `unsafe_rate = 0.0000` result is
  measured at each scene's own operating weight and this cycle did not touch it.

## Key learnings

- **"Run it above the threshold" and "run it where the arms can differ" are
  different instructions**, and on a saturating headline they are disjoint. Any
  future rescore should target the transition band, located by ladder walk, not
  the operating point.
- **A delta needs a boundary before it needs a p-value.** `sub_margin` catches
  the failure D-124 shipped, and it is one comparison against the margin.
- **A calibration table carries the operating point it was measured at.** λ
  windows measured at `w = 10` are not portable across the weight axis, which
  is the same extrapolation `operating_weight.measured_on` already names on the
  controller axis, one axis over.

## Recommended next 1–3 priorities

1. **Densify the transition band 100 → 300 and re-score `risk_mppi` there with
   more seeds.** The one scorable rung is the whole positive result; n = 8 at a
   single rung is thin, and the band's width is unmeasured.
2. **Give `lam_windows.yaml` a weight key** (or refuse rescores at weights it
   was not measured at) — the `w = 30` out-of-band rows are the warning.
3. **Repeat the ladder walk on `cafe_obstacle_crossing_v0` and
   `cafe_convoy_v0`** to see whether a scorable band exists there at all;
   convoy's ceiling is 30, so it may have none.

## Artifacts
- PR: #67 (branch already in queue)
- Files touched: `eval/mppi_sandbox/comparison_headroom.py`, `eval/mppi_sandbox/tests/test_comparison_headroom.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
