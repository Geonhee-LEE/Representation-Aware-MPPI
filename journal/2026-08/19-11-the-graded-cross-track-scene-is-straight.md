# The graded cross-track scene is straight — curvature refuted as the gradeability mechanism

- **Cycle**: 2026-08-19 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — measure the curvature claim
- **Phase**: P3
- **Status**: keep

## What I tried

- Discharged D-360's `CURVATURE_UNMEASURED` pin: per scene, minimum curvature
  radius of `Scenario.waypoints` (circumradius over interior triples) against
  the sampler's reach (`horizon 30 x dt 0.1 x target_speed`).
- Shipped `eval/mppi_sandbox/path_curvature.py` + 11 tests. **Zero rollouts** —
  reference paths are static yaml, so this cost ~1 s of compute, not 64 rollouts.
- Checked the collinearity result segment by segment before believing it (turn
  angle at every interior vertex, segment lengths) rather than trusting an
  `inf` that a degenerate/duplicate waypoint could have manufactured.

## What worked / what failed

- **The hypothesis is refuted in the direction that matters.** Six of eight
  scenes have `R_min = inf` — authored paths exactly collinear, all six running
  down `x = 0` with `0.000°` turn at every vertex. One of those six is
  `cafe_obstacle_crossing_v0`, the **sole `DISCRIMINATING` scene on both**
  `cte_rms_max` (D-358) and `cte_max` (D-360). A perfectly straight path grades
  a cross-track bar, so curvature is not what makes one gradeable here.
- **What buys the graded cell is the obstacle, not the path**: `cbf_mppi` swerves
  to a `1.0272 m` peak around the crossing pedestrian on a path with no
  curvature. Path curvature and obstacle avoidance are two independent
  excitation channels and the registry's only graded cell uses the second.
- **D-360's ordering survives, but strictly narrower than it was stated.** Among
  the three vacuous declaring scenes the ratio is monotone in the predicted
  direction — `city_curved_v0` 0.733 > `city_figure8_v0` 0.600 >
  `cafe_straight_v0` 0.000, matching headroom 2.18x < 9.25x < 23.26x. It orders
  the ungraded scenes among themselves and says nothing about the graded/ungraded
  boundary.
- **Third finding, and it re-prices the obvious repair**: no scene reaches the
  excitation ratio at all. Max is `0.733`; Nav2 #5925 reports the mode at a ratio
  well above 1 (0.6 m radius against an 8 s horizon) and our horizon is 3.0 s.
  So "add a curved scene" would not excite the mode at these radii either.

## North-star delta

- 물체회피 / 경로추종 tension sharpened: the one cross-track cell this suite can
  actually grade is measuring **avoidance-induced** excursion, not tracking on a
  demanding path. The 경로추총 column has no scene that tests tracking-under-
  curvature at all.
- No controller changed, no new cell became gradeable. What moved is that one
  of the two surviving explanations for D-358's five vacuous cells is now
  **measured and eliminated as stated**, leaving scene-authoring narrower and
  better specified than "add curvature".

## Key learnings

- **Measure the geometry before borrowing the mechanism.** The Nav2 #5925
  borrow was well-argued, corroborated by two independent statistics, and
  survived three cycles of prose — and the first actual radius computation
  refuted it in one second. The 3-point ordering was real but was ordering only
  the scenes that already agreed.
- **A monotone ordering among the losers is not a boundary explanation.** The
  ordering held perfectly within the vacuous three; the failure was extending it
  to the partition. That is a reusable error shape for this branch's census work.
- **A pinned silence is worth more than a hedged claim.** D-360 could have
  asserted curvature and moved on; it wrote `CURVATURE_UNMEASURED` instead, which
  is exactly what made this cycle a one-second discharge rather than an
  archaeology run.

## Recommended next 1–3 priorities

1. **Author a scene with `R_min` small relative to reach** (ratio > 1) — the
   scenario-authoring decision this measurement now specifies numerically. This
   is user-blocked (scene intent), but the *target* is no longer a judgement
   call: it is a ratio.
2. **Q-168 — enable `--durations` on the next `push_preflight record`**; the
   suite runs anyway, so the top-10 table is free.
3. **Widen `city_curved_v0` to 8 seeds** — at 2.18x headroom it is still the
   cheapest vacuous cell to make grade (448 rollouts, `WIDENING_UNBOUGHT`).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/path_curvature.py, eval/mppi_sandbox/tests/test_path_curvature.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
