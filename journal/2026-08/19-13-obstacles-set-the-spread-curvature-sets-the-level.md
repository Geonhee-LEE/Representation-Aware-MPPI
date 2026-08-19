# Obstacles set the spread, curvature sets the level

- **Cycle**: 2026-08-19 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Measure whether any arm's attained CTE tracks the forced excursion
- **Phase**: P3
- **Status**: keep

## What I tried

- Joined the two harvests already pinned on disk — `cte_peak_vacuity.CTE_MAX_SEED0`
  (attained peak CTE, 8 scenes x 8 arms, seed 0) and `obstacle_reach.CENSUS`
  (forced excursion, D-362) — into `eval/mppi_sandbox/excursion_tracking.py`.
  Zero rollouts, as D-361 and D-362 were: both operands were already measured.
- Asked D-362 finding #3's dangling question at column scale: it saw `1.0272`
  attained against `0.5070` forced on one scene and declined to read the ratio
  as a predictor off a single point. The harvest has the other seven.
- 15 tests, one new `loop_reach.READING` row, tally + citation repairs.

## What worked / what failed

- **The question was pointed at the wrong statistic.** Forced excursion does
  *not* predict the attained level: `hi/forced` spans 5x across the four
  excited scenes (0.401 → 2.026). It **does** predict the arm **spread**, and
  there it separates with no overlap — excited min `0.1441` vs unexcited max
  `0.0730`, a 1.97x gap.
- **`cafe_convoy_v0` falsifies `obstacle_reach`'s own lower bound.** Every arm
  attains *less* cross-track (`0.1923`) than a perfect tracker is forced into
  (`0.4798`), by 2.5x. Not a contradiction — `forced` is derived at constant
  `target_speed_mps`, so it prices lateral metres only, and a convoy's cheap
  evasion is to slow behind the leader. Same mechanism D-352/D-353 named on
  this scene from the other side.
- **The residual is curvature, and it is large.** On the three obstacle-free
  scenes the attained level is monotone in D-361's ratio and spans 21x:
  `straight` 0.0 → `0.0215`, `figure8` 0.600 → `0.1081`, `curved` 0.733 →
  `0.4583`. `city_curved_v0` attains 90% of the graded scene's entire forced
  excursion with **nothing to avoid**.
- `census_preempt` caught 3 of 5 censuses drifted at the stage (~2 s): guard
  tally 124→126, an unrecorded `READING` row, and a citation collision. All
  three would have been the same red 22 minutes later.

## North-star delta

- The 경로추종 column's vacuity now has a **decomposition**, not just a cause:
  gradeability needs arm *spread*, spread comes from obstacles, level comes
  from curvature. That is the first statement covering all of D-360/361/362
  rather than superseding them.
- Corroborates STATE's standing repair on the statistic that decides it —
  `cafe_cut_in_v0` (spread `0.6173`) and `cafe_head_on_v0` (`0.2804`) are both
  in the excited partition, so a bar there has dispersion to cut.
- Adds a **warning** the prior three cycles could not have issued:
  `city_curved_v0` is the highest-attaining unbarred scene (`0.4583`) and
  spreads only `0.0730`, so a bar there cuts all eight arms or none. High
  attained CTE is not evidence of gradeability.

## Key learnings

- **Three cycles disagreed because each measured a different statistic.**
  D-360 found curvature ordering headroom (a *level* fact, correct), D-361
  refuted curvature as the gradeability mechanism (a *spread* fact, also
  correct), D-362 landed obstacles (spread again). The disagreement was never
  real. Reusable: before adjudicating two channels, check they are being read
  off the same statistic.
- **A derived lower bound is worth testing against the column that motivated
  it.** `forced` was defined as "what a perfect tracker must do" and read as a
  floor; one scene puts every arm underneath it, because the derivation fixed
  speed and the controller does not.
- `census_preempt` corrected the **choice** of `READING` row, not merely its
  absence — the first time. I registered the nested `excited() x unexcited()`
  loop on the reasoning that it is the sharper exposure; `assert_reach` grades
  that assertion `OTHER`, so the row retired a name the detector never names.

## Recommended next 1–3 priorities

1. **Widen the spread separation to 8 seeds on the four excited scenes** — the
   whole finding is seed-0 spread *across arms*; `SEED_SCOPE` says so. This is
   the same `WIDENING_UNBOUGHT` price D-358 left unpaid, now with a specific
   reason to pay it on a specific 4 scenes rather than all 8.
2. **Declare `cte_max` on `cafe_cut_in_v0` / `cafe_head_on_v0`** — user-blocked
   (bar value is scene intent), now corroborated on spread as well as forced.
3. **Q-168 — `--durations` on the next `push_preflight record`** — still free.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/excursion_tracking.py`, `eval/mppi_sandbox/tests/test_excursion_tracking.py`, `eval/mppi_sandbox/loop_reach.py`, `eval/mppi_sandbox/tests/test_guard_reflexivity.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
