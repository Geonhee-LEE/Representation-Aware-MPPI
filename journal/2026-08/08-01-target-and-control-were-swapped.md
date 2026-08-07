# The first cost-term change acts on the scene that was meant to be its control

- **Cycle**: 2026-08-08 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #3 — attack `cafe_obstacle_crossing_v0`'s 8/8 unsafe directly
- **Phase**: P5
- **Status**: keep

## What I tried

- Ported MorphoCopter-MPC's (arXiv:2605.15999) **two-sided-gap cost-reduction
  factor** onto the sandbox's soft barrier — the 00:00 feed entry, and the
  first surfaced work landing on the same line of source as the bottleneck.
  `eval/mppi_sandbox/gap_gate.py`: barrier scaled by `1 − s·(μ²−1)²`, μ = 0 at
  a passage centreline, 1 for a single-sided obstacle.
- μ in **closed form** from the two nearest obstacle centres (analytic circles
  make the paper's DBSCAN + line-fit pipeline unnecessary), plus a
  distance-**imbalance** term the paper's μ does not carry — see below.
- Wired behind `StockMPPI.gap_gate_strength` (0 = legacy branch untouched),
  registered `gap_gated_mppi`, 14 tests.
- Measured against `stock_mppi` at a **matched λ = 0.8**, the yardstick D-123
  fixed, on `cafe_obstacle_crossing_v0` — then, once that came back inert, on
  `cafe_head_on_v0`, which the feed had nominated as the *null control*.

## What worked / what failed

- 🔴 **The borrow was aimed at the wrong scene, and the feed's own targeting
  argument inverted the quantity it rested on.** The entry read D-121's
  `required_corridor = 0.00 m` as *"the geometry admits passage with zero
  lateral slack — the feasible set is a single line"*. It means the opposite:
  `feasibility.required_corridor` is the **narrowest lateral budget at which
  the declared margin is attainable**, so 0.00 m says the robot can hold 0.30 m
  **without ever leaving the reference path** — maximum slack, not a knife
  edge. Crossing has no narrow lateral passage for a gap gate to open.
- 🔴 **And the measurement says exactly that.** On crossing, matched λ = 0.8,
  8 seeds: sign split **4/4**, `mean_clearance` 0.0368 → 0.0341,
  `min_clearance` 0.0146 → 0.0072. Directionless — the scene's difficulty is
  *when* to enter the walking band, not how to squeeze through it.
- ✅ **On `cafe_head_on_v0` — required corridor 1.00 m, the one scene with a
  genuine lateral squeeze — the gate is directional**: favoured on **6 of 8**
  seeds (1 tie, 1 against), `mean_clearance` **0.0056 → 0.0095** (1.7×),
  `min_clearance` 0.0009 → 0.0024, mean speed unchanged (0.047 both), ESS in
  band on both arms (116.5 / 115.7). 6/7 non-tied one-sided is **p = 0.0625**,
  **not significant**, and is reported as such.
- 🔴 **`unsafe_rate` = 1.0000 on both arms of both scenes — the headline does
  not move anywhere.** head_on's margin is 0.40 m and the arms are at 0.01 m;
  a 1.7× improvement three orders of magnitude below the bar changes no
  verdict. This is D-119's shape exactly (risk_mppi's 32× clearance, identical
  8/8), and the second time a scalar controller win has been operationally
  worthless at the declared bar.
- ✅ **The paper's μ needed a safety repair before it was portable.** A pure
  opposite-sidedness test reads μ = 0 whenever two obstacles straddle the
  robot — *including* when it is pressed against one and the other is far away
  — which would switch the soft barrier fully off next to a wall, leaving only
  `w_collision` to hold the margin (the feed's caveat 3). `μ = max(alignment,
  imbalance)` is zero only at a genuine centreline. Pinned, along with the
  hard term never being gated.

## North-star delta

- **First cost-term change in the project's history**, and it is measured, not
  argued: two scenes, matched temperature, paired by seed.
- **No movement on the safety headline.** `unsafe_rate` stays 8/8 on both
  scenes. The gate buys clearance where a squeeze exists and nothing where one
  does not, and neither amount reaches the declared margin.
- The A/B surface now takes a fourth arm at zero harness cost — `gap_gated_mppi`
  ran through `ab.seed_sweep` / `near_miss.score_runs` unmodified.

## Key learnings

- **A borrow's target assignment is a claim, and it can be wrong in the
  direction that wastes the whole cycle.** The feed named crossing the
  treatment and head_on "the control that isolates the mechanism"; the
  measurement swaps them. Cheap fix: read the *predicate's docstring*, not the
  prose about its output — one `grep` on `required_corridor` would have caught
  the inversion before the port.
- **Clearance gains and safety verdicts are close to decoupled at this
  operating point.** Two independent mechanisms (D-119's risk channel, this
  gate) have now produced multiplicative clearance wins with zero verdict
  movement. The next controller change should be judged on whether it can
  reach **0.40 m**, not on whether it beats the other arm.
- The imbalance term is the transferable part of the port: **a gate that can
  zero a safety cost has to be zero on a measure-zero set**, and
  opposite-sidedness alone is not.

## Recommended next 1–3 priorities

1. **Re-target the gate at head_on with more seeds** — 6/8 at p = 0.0625 is
   suggestive and 16 seeds costs ~80 s. Cheapest way to settle a real
   direction.
2. **Ask why both arms sit at ~0.01 m against a 0.40 m margin** (Q-110) — a
   1.7× win on a number 40× below the bar suggests the barrier is being
   out-competed by `w_path`, not mis-shaped. That is a *weights* question, and
   no cycle has asked it.
3. **Point `baseline_matrix` at `ab.lam_for`** (prior STATE #1, unchanged) —
   still halves the measured confound and deletes a duplicated statement.

## Artifacts

- PR: #67 (branch already open — zero new review bandwidth)
- Files touched: `eval/mppi_sandbox/gap_gate.py`,
  `eval/mppi_sandbox/controllers/gap_gated_mppi.py`,
  `eval/mppi_sandbox/controllers/stock_mppi.py`,
  `eval/mppi_sandbox/controllers/__init__.py`,
  `eval/mppi_sandbox/tests/test_gap_gate.py`, `docs/decisions.md`,
  `docs/deliberations.md`
- TSV row appended: yes
