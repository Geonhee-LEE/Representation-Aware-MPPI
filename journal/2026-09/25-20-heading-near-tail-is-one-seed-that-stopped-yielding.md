# The w_heading_near=64 cte tail is one seed that stopped yielding

- **Cycle**: 2026-09-25 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략
- **Phase**: P6 (TODO tagged P5)
- **Status**: keep

## What I tried
- Per-seed cross-track (seeds 0–31) on the knee+shape arm, `cafe_obstacle_crossing_v0`, w_heading_near ∈ {0, 64}. I used a scratch script (`/tmp/tail.py`) with `_polyline_distance` over `traj[:, 1:3]`. It is not committed, because a census-sensitive in-tree `MPPIParams` site broke two lam-census invariants in 09-24's attempt.
- Traced seed 27 step-by-step (x, y, θ) against the five crossing obstacles' positions for both arms.

## What worked / what failed
- The tail is **seed 27 alone**. Its cte_rms goes 0.16→2.20 and cte_max 0.44→3.93 m, and it still reaches the goal. That reproduces D-501's 2.202 / 3.930 exactly.
- Excluding seed 27, w=64's cte_rms_max is 0.51 and cte_max 0.99, both **below** the w=0 baseline (0.54 / 1.47). On 29/32 seeds w=64 tracks tighter.
- Mechanism: at w=0, seed 27 yields to obstacle #1 (crossing +x at y=-2.0) by **spinning in place one full turn** (θ -0.52→5.69 rad). That spin is the heading error the gated term prices. At w=64 the spin is expensive, so the robot runs **ahead of the crosser in the same +x direction**. It reaches x=3.93 m at 0.34 m clearance, then returns around the obstacles' parking spots.
- Weaker cases of the same mode: seeds 0 and 6 (cte_max 0.99 / 0.88, also +x side, clearance 0.31 / 0.37).
- Failed: a first run read `traj[:, :2]` as xy. Column 0 is time, so that output was discarded.

## North-star delta
- The only blocker to promoting w=64 is now a named mode ("outrun the crosser instead of yielding"), 1 severe + 2 mild in 32 seeds, rather than an unexplained tail. No default change yet.

## Key learnings
- The heading residual the knob removes is partly *yield-by-rotation*. Pricing heading near obstacles removes the robot's cheapest yield manoeuvre, so the cost of fixing heading shows up as a new passing mode, not as noise.
- That points at a speed gate (weaken the near-heading price when |v| is low, i.e. while yielding) rather than a lateral-offset cap.
- `ArmRun.traj` is (t, x, y, θ). Always slice `[:, 1:3]` for xy.

## Recommended next 1–3 priorities
1. Add a speed gate to `w_heading_near` (price only when |v| > v_gate, inert default) and re-measure seeds 0–31: heading fails and cte_max.
2. Or bound the mode directly: penalise same-direction travel ahead of a crosser (a dynamic-risk-channel candidate for P4).
3. Pin seed 27's excursion as a regression test once a census-safe test site exists (see TODO 3e5c5d39).

## Artifacts
- PR: none (PR #67 closed by user 09-21; branch push only)
- Files touched: docs/decisions.md, journal/2026-09/25-20-heading-near-tail-is-one-seed-that-stopped-yielding.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
