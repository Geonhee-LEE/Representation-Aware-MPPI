# Pricing the freeze into the planner — the term charges what the scene grades

- **Cycle**: 2026-08-13 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — price the freeze into the planner
- **Phase**: P5
- **Status**: keep

## What I tried

- Shipped `ProgressPriceCritic` (`eval/mppi_sandbox/critics/progress_price.py`):
  per rollout step, `deficit = max(0, stall_speed·dt − Δs)` along the reference
  polyline, `cost = w_freeze · Σ deficit²`. The threshold is **imported** from
  `freeze_price.STALL_SPEED_MPS`, not respelled — the cost term and the
  acceptance key it exists to move define "stalled" with one constant.
- Wired it on **`StockMPPI`**, not on `RiskMPPI`: the freeze is not a
  representation effect (the metric measured it on every arm), and a term only
  some arms can carry cannot be ablated against the others. `w_freeze = 0`
  default, returns zeros without projecting.
- Needed a vectorised arclength projection — `completion_percent` loops in
  Python over trajectory rows, which is fine for a `(T,6)` run record and
  unusable for the `K·H = 7680` rollout points priced every control step.
  `arclength_along` is `_polyline_distance`'s projection with the arclength kept
  instead of thrown away.
- Swept `w_freeze ∈ {1e2, 1e3, 1e4, 1e5}` on `social_mppi`, 3 seeds, freeze and
  clearance read together.

## What worked / what failed

- **The target was hit exactly.** `social_mppi` at `w_freeze = 1e4`: exceed
  **2/3 → 0/3**, longest stall `[3.30, 1.70, 2.40] → [0.50, 0.30, 0.50]` s,
  worst-case clearance **0.965 → 0.985 m**, reached 3/3. STATE asked for
  `stock_mppi`'s 0/3 exceed rate *at `social_mppi`'s clearance*; the clearance
  did not merely hold, it improved.
- **`w_freeze` is not monotone, and that is the more useful finding.** `1e2` →
  **3/3** (worse than not wiring it at all), `1e3` → 1/3, `1e4` → 0/3, `1e5` →
  3/3 with clearance collapsing to 0.844. Too small perturbs the trajectory
  without freeing it; too large fights the obstacle cost and loses both. This is
  an interior optimum found by a 4-point grid, which is weak evidence for a
  robust setting.
- The baseline half re-measured **identically** to D-241's recorded reading
  (0/3, 2/3, 2/3), which is the ablation invariant doing its job: the term was
  physically present and priced exactly zero.
- One test premise was wrong and the failure was informative: a rollout
  reversing off the **start** of the path prices identically to one standing
  still, because arclength clamps to the polyline. Pinned as a known edge rather
  than fixed — `freeze_duration` clamps the same way through
  `completion_percent`, so un-clamping the price alone would make it optimise a
  quantity the scene does not grade.

## North-star delta

- **First cycle on this branch to move a planner rather than an instrument.**
  The scene's second-ranked success criterion goes from measured-and-failing to
  passing on the arm that failed it, without paying clearance.
- 15 new tests, both directions: ablation invariant pinned as *byte-identical
  against the term physically absent* (not against `w_freeze = 0`), so a flipped
  default fails as loudly as leaked arithmetic.
- Still one scene, n=3, one arm. Nothing here says the setting transfers.

## Key learnings

- **Price what is graded, by importing the constant.** The whole design reduces
  to that. It also made the term cheap to justify: no new tuning knob was
  introduced, only a weight.
- **`w_speed` was never going to fix this** — it charges ground speed, and the
  freezing failure has ground speed. Arcing around a pedestrian is progress-free
  motion that the existing cost pays for happily.
- **Non-monotonicity means a named arm would have been premature.** D-225's
  precedent is measurement first, name second; `w_freeze` rides as a
  `StockMPPI` param so any arm can carry it via kwargs until a paired-seed
  protocol confirms the cell.
- The sweep cost 15 s of wall clock. The reason this cycle fit its budget is
  that sandbox runs are ~0.5 s and the suite is the only expensive thing here.

## Recommended next 1–3 priorities

1. **Widen the freeze result to the paired-seed protocol** (n=12, matched λ) and
   sweep `w_freeze` more finely between `1e3` and `1e5` — the interior optimum
   is the weakest part of this cycle's claim.
2. **Check the price on the other eight scenes** — a term defaulted off is safe,
   but its `1e4` setting has never been seen outside `cafe_freezing_v0`, and a
   progress cost could plausibly hurt scenes where stopping is correct.
3. **Implement `time_to_goal` as first-arrival time** (STATE #2, unchanged) —
   drops the `acceptance_coverage` census 4 → 2 and hands the freezing scene its
   third declared criterion.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/critics/progress_price.py, eval/mppi_sandbox/critics/__init__.py, eval/mppi_sandbox/controllers/stock_mppi.py, eval/mppi_sandbox/controllers/risk_mppi.py, eval/mppi_sandbox/tests/test_progress_price.py, docs/decisions.md
- TSV row appended: pending
