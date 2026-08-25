# Shaping the barrier breaks D-426's 1:1 trade — 1/5 → 3/5, and it takes both knobs

- **Cycle**: 2026-08-22 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `shaped-barrier` (STATE #1) Cost term steep in `[0, 0.30]`, flat above
- **Phase**: P3
- **Status**: keep

## What I tried

- Added `MPPIParams.obs_barrier_band` (default `0.0`, inert). Above `0` the soft
  obstacle term switches from `exp(-clear / obs_soft_scale)` to a **quadratic
  hinge with compact support** — steep inside `[0, band]`, *exactly* zero above.
- Routed **both** `_cost` obstacle branches (plain and gap-gated) through one
  `_soft_barrier()` helper, so the knob cannot reach one path and miss the other.
- 8 tests in `test_barrier_shape.py`; 15 rollouts (crossing, 5 seeds, 4 arms).

## What worked / what failed

- **The knobs are complementary, not substitutes** — this is the finding.
  `knee+shape` nets **3/5** where D-426's best was 1/5 and baseline is 0/5.
  Mean `cte_rms` **0.362 → 0.225** (−38 %) with `min_distance_to_obstacle`
  still green on **5/5**. Both halves of the north star moved *together* for
  the first time.
- **`shape_only` is 0/5** — clearance stays at ~0.04 m and the same single
  check fails as baseline. The band alone buys nothing. So the causal story is
  clean: the **hard knee** buys the clearance check, and the **band** stops the
  far field from charging tracking error for it. Either alone is 0/5 or 1/5.
- **Not significant on its own.** 1/5 → 3/5 at n=5 is Fisher p ≈ 0.52. The
  supporting `cte_rms` shift is per-seed and consistent (4/5 seeds improve),
  which is why I record it as a direction, not a win.
- **Seed 0 regressed** (`cte_rms` 0.094 → 0.430) — the one seed D-426's test
  pins. It is again the outlier seed, which is the D-426 defect (2) restated.
- Two tests failed first and both were *my* geometry assumptions, not the code:
  the crossing obstacle **moves**, so a point parked 1.0 m from its `t=0` pose
  is inside the band by mid-horizon; and at 6 m it is 0.07 m from a *different*
  obstacle. The offset is now searched and the precondition asserted.

## North-star delta

- **First cycle where avoidance and tracking improve simultaneously.** Every
  prior P3 result moved one at the other's expense (D-409, D-410, D-426).
- Net pass on `cafe_obstacle_crossing_v0`: **0/5 → 3/5**, clearance 5/5 green.
- Still stock MPPI — 0 rollouts of any *learned* representation. This is cost
  geometry, which D-426 named as the prerequisite, not the destination.

## Key learnings

- **D-426's "1:1 trade" was a property of the barrier's *tail*, not of avoidance
  vs tracking.** `exp(-clear/0.3)` is `0.37` at the gate and never reaches zero,
  so the planner kept paying to retreat after the check was satisfied. Removing
  the tail removes the trade. The conjunction was never physically forced.
- **A shape knob needs an ablation against itself.** `shape_only` being 0/5 is
  what makes `knee+shape` interpretable; without that arm the 3/5 would have
  been misread as "the band fixes it".
- Scope is honest and narrow: **one scene, five seeds.** `cafe_cut_in_v0` is
  still unusable as evidence (D-426 defect 2), so no transfer claim is made.

## Recommended next 1–3 priorities

1. **Seed-ensemble the shape result** — 16 seeds × crossing, `knee` vs
   `knee+shape`, to move 1/5 → 3/5 from a direction to a measurement.
2. **`repin-knee-price`** — D-410's test still pins seed-0 `time_to_goal`; this
   cycle re-confirms seed 0 is the outlier. Re-pin on `cte_rms`.
3. **`cutin-goal-reached`** — one of two knee scenes still cannot grade anything.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/controllers/stock_mppi.py`, `eval/mppi_sandbox/tests/test_barrier_shape.py`
- TSV row appended: yes
