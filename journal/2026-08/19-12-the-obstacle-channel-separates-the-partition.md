# The obstacle channel separates the cross-track partition exactly

- **Cycle**: 2026-08-19 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #3 — sweep the obstacle-side excitation channel
- **Phase**: P3
- **Status**: keep

## What I tried

- D-361 measured the **curvature** excitation channel and refuted it: the sole
  `DISCRIMINATING` cross-track scene is exactly straight. Its finding #1 named
  the surviving channel — obstacle avoidance — without measuring it. This cycle
  measures it, the same way and at the same price (zero rollouts; obstacle
  schedules and reference paths are both static yaml).
- New `eval/mppi_sandbox/obstacle_reach.py` + 10 tests. Per scene: place a
  *perfect* tracker at the station it would occupy at time `t` along the
  reference path at `target_speed_mps`, put every obstacle at `ob.position(t)`,
  and take the space-time closest approach `d_enc`. `forced =
  max(0, (ROBOT_RADIUS + ob.radius) - d_enc)` is the lateral shift that restores
  circle-to-circle contact.
- Also computed the **time-blind** alternative (obstacle track vs path polyline,
  ignoring when each is there) to check whether the cheaper measurement would
  have done.

## What worked / what failed

- **Finding #1 — the channel separates the partition exactly, which curvature
  never did.** Four scenes declare a `cte_max` bar. Of those four, **one** has
  any obstacle at all, and it is the graded one: `cafe_obstacle_crossing_v0`,
  `forced = 0.5070 m`. The other three (`cafe_straight_v0`, `city_curved_v0`,
  `city_figure8_v0`) carry **no obstacle whatsoever** — forced excursion
  identically `0.0`, so no bar value could be failed by avoidance. Curvature
  ordered the losers among themselves (0.733 / 0.600 / 0.000) but put the winner
  at the *bottom* of its own ordering; this channel reads `1 → 0, 0, 0` with the
  graded cell on the excited side.
- **Finding #2 — the two scenes that force *more* excursion than the graded one
  declare no `cte_max` at all.** `cafe_cut_in_v0` at `0.6000 m` (18% more than
  the graded scene) and `cafe_head_on_v0` at `0.5900 m`. The cross-track column
  is not short of excitation — it is short of **bars on the scenes that have
  it**. But the unbarred four are not uniformly excited: `convoy` is `0.4798`
  (just under) and `freezing` is `0.0000`, so declaring a bar on all four would
  re-create the vacuity somewhere else.
- **Finding #3 — sub-unity where it grades, so no threshold is claimed.**
  `0.5070` against the declared `1.0`, and the cell grades anyway (D-360:
  `cbf_mppi` peaks at `1.0272`). The attained excursion is ~2x the geometrically
  forced one — the controller swerves wider than it must. One non-zero point
  cannot locate a threshold, so `RATIO_NOT_A_THRESHOLD` pins the refusal rather
  than borrowing D-361's `1.0` line onto a channel that has not earned it.
- **The time-blind measurement would have been wrong.** `cafe_freezing_v0` reads
  `0.3000 m` time-blind and `0.7428 m` on the encounter — its actors sweep past
  before the robot arrives. The cheap version invents an excitation that does
  not happen; a test pins the disagreement so a refactor to it cannot pass.
- **`census_preempt` caught my own arithmetic error at the stage.** It flagged
  the unrecorded `loop_reach` row; writing that row forced me to re-read the
  count, and the test name said "three scenes" where the tuple holds **two**
  (`convoy` falls under the floor). ~2 s at the stage instead of a red suite.

## North-star delta

- 물체회피 column: the avoidance channel now has a **per-scene geometric
  magnitude**, which it did not before — clearance was measured as an outcome
  (D-353/356/357), never as the excitation the scene supplies.
- 경로추종 column: unchanged in what it grades (still 1 of 4), but the partition
  now has a **measured cause** rather than three refuted candidates. Two cycles
  of "is it the statistic / is it the threshold / is it curvature" close.
- No controller changed, no new cell became gradeable, zero rollouts.

## Key learnings

- **Two channels, and the registry uses one per scene.** The scenes with
  curvature have no obstacles; the scenes with obstacles are all straight. No
  scene in the suite excites both at once — which means the suite has never
  tested avoidance *on* a curved path, the case where Nav2 #5925's
  reference-point ambiguity and an avoidance swerve would interact.
- **A channel that separates is worth more than a channel that orders.** D-361's
  curvature ordering was monotone and correct and explained nothing, because it
  ran within one side of the partition. The test to apply to the next proposed
  mechanism is whether it puts the graded cell on the excited side.
- **The cheapest repair moved from "author a curved scene" to "declare a bar on
  a scene that already earns one".** D-361 priced the former at a new scene the
  registry cannot currently reach (ratio 0.733 < 1.0). Finding #2's repair needs
  no new scene and no rollouts — only a constant in `cut_in`/`head_on` yaml.
  Still scene-authoring (what the value should be is not measured here), so
  still user-blocked, but the price dropped by an order of magnitude.

## Recommended next 1–3 priorities

1. **Declare `cte_max` on `cafe_cut_in_v0` and `cafe_head_on_v0`** — the two
   scenes that out-force the graded cell and contribute nothing. User-blocked
   (bar value is scene intent), but zero-rollout and no new scene.
2. **A scene that excites both channels at once** — obstacles on a curved path.
   Nothing in the registry does, and it is the interaction the north star's two
   clauses need graded together.
3. **Q-168 — `--durations` on the next `push_preflight record`** — still the
   cheapest unclaimed claude-side item; the suite runs anyway.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/obstacle_reach.py, eval/mppi_sandbox/tests/test_obstacle_reach.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md
- TSV row appended: yes
