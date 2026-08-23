# The heading term that was never there

- **Cycle**: 2026-08-23 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — heading residual 의 *원인* (cost shape swap)
- **Phase**: P5
- **Status**: keep

## What I tried

- Picked STATE #1: the feed's cheap shape swap — hold every weight fixed, swap
  the heading term's shape from `w·e_θ²` to something non-quadratic, and see if
  the residual's *shape* moves. First control-touching pick in seven cycles.
- Before swapping the shape, read `StockMPPI._cost` to find the term. **There
  is no heading term.** The stage cost is `w_path·d_path²` + `w_speed·(v−v_ref)²`
  + `w_omega·ω²` + obstacle pair + `w_terminal·dist_goal²` + progress price.
  Nothing in it reads `traj[..., 2]`.
- So the planned experiment was not runnable, and the prior question was
  cheaper: does pricing heading *at all* move the metric? Added `w_heading`
  (wrapped `e_θ²` against the path tangent, default `0.0`, branch skipped at 0
  so every recorded run stays byte-identical), then ran paired n=16 sweeps at
  `w_heading ∈ {0, 2, 8, 32}` on two scenes.

## What worked / what failed

- **The metric was unpriced, and on every arm.** `heading_err_rms_max` has been
  an acceptance threshold since P5 scoping while nothing in the cost read the
  angle it scores. `w_omega` prices the rotation *rate*, `w_path` the *lateral
  offset* — a rollout sitting on the path, turning slowly, pointed the wrong
  way pays zero. No subclass overrides `_cost` (they add `_extra_cost` only),
  so this held for all 8 controllers.
- **Obstacle-free scene: it converts.** `cafe_straight_v0`, 0→32 improves
  **16/16 seeds**, heading_rms 0.0639→0.0399 (−38%), monotone across all four
  weights, cross-track pays 0.0115→0.0145, 16/16 still reach goal. A 16/0 sign
  split is a different kind of result from D-430's 9/7 and D-433's 12/4.
- **Residual scene: it half-works, and the other half is informative.** On
  `cafe_obstacle_crossing_v0` — the scene D-430/D-433 actually measured — the
  same swing reads **11/5**, only −13%, the per-seed spread *widens*
  (0.0417→0.0513), and cross-track gets **worse** (0.1516→0.1812, +20%).
- **This retro-explains both failed sweeps for free.** They were not evidence
  about cost shape; they were two knobs that do not point at the metric, and
  "reshuffles rather than converts" is exactly what an unrelated knob does to a
  noisy per-seed score. Neither sweep was mis-run.
- **It also disqualifies the queued experiment.** The feed's shape swap
  presumes a heading term exists to reshape. The shape question only becomes
  askable now that one exists and is shown to move the metric.

## North-star delta

- 경로추종: **first lever found that converts rather than reshuffles** —
  −38% heading_err_rms, 16/16 seeds, obstacle-free. Three cycles of "there is
  no lever" had a mechanical cause, and it is fixed.
- 물체회피: untouched by design — default 0.0, clearance and reach identical.
- Honest limit: on the scene the bottleneck was *reported* on, this is a −13%
  partial that costs +20% cross-track. The bottleneck is **not** closed.

## Key learnings

- **Read the cost before tuning it.** Two sweeps and a literature intake went
  looking for the right *value* of a term that did not exist. The check that
  would have caught it was one `grep` for `traj[..., 2]`, available at any
  point in three cycles.
- **A metric in the acceptance set is not a metric in the objective.** Nothing
  in this repo connected the two, and nothing went red about it — the threshold
  graded a quantity the planner was never asked to optimise.
- **The +20% cross-track is the interesting number, not the −13%.** Heading
  improving while cross-track degrades means the two terms competed for the
  same degree of freedom, which is Q-181's "residual is the price of
  avoidance", now with numbers on both sides. → Q-185.

## Recommended next 1–3 priorities

1. **Q-185 / Q-181 in one shot**: per-seed `heading_err` vs clearance/detour
   correlation at **both** `w_heading ∈ {0, 32}`. Tight at 32 ⇒ the crossing
   residual is definitional and the *threshold* moves, not the cost. Both arms
   already exist, so the added cost is the correlation only.
2. **Now the shape question is askable**: with a heading term in place, swap
   quadratic → non-quadratic (feed 04:00). Do this only *after* #1 — if the
   crossing residual is definitional, no shape fixes it.
3. **Calibrate `w_heading` per scene** rather than shipping a global default;
   the two scenes disagree by 3× on how much it buys.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/controllers/stock_mppi.py`,
  `eval/mppi_sandbox/tests/test_heading_price_absence.py`,
  `docs/decisions.md` (D-440), `docs/deliberations.md` (Q-185),
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
