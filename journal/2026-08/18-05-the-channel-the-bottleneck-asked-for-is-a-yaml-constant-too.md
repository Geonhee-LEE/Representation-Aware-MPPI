# The channel the bottleneck asked for is a yaml constant too

- **Cycle**: 2026-08-18 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — add a path-relative lateral-velocity channel and re-run the three-index table
- **Phase**: P3
- **Status**: keep

## What I tried

- Added `path_lateral_speed` to both observable registries: the obstacle's
  velocity component **across the reference path**, `|v_obs · n_path|`, with the
  normal taken from the polyline segment nearest the robot. This is the channel
  D-335's bottleneck named, and the reason it looked promising is specific —
  `cafe_cut_in_v0`'s pedestrian is **piecewise** (2 s perpendicular, then a turn
  to travel along the robot's line), so unlike `obstacle_speed` the projection
  had a route to non-zero within-scene spread.
- Threaded `sc.waypoints` into both readers (`_critical_observables`,
  `_observables_at`) — neither previously received the path.
- Re-took all 40 baseline rollouts, all three index policies, six observables in
  one pass (**76.1 s**).

## What worked / what failed

- ✅ **The 15 pre-existing (scene, policy) columns reproduced exactly.** Checked
  before anything else, so D-336 is a *widening* of the table, not a
  re-measurement of it — the D-334/D-335 verdicts are untouched by construction
  rather than by assertion.
- ❌ **The channel fails on both counts.** It **never separates** `cut_in` at any
  index: at both causal indices it reads `0.75`, exactly
  `cafe_obstacle_crossing_v0`'s value, and at the critical index `0.0`, exactly
  `cafe_head_on_v0`'s. And where it *does* separate (`freezing` at all three
  indices, `head_on` at the causal ones) it has **zero within-scene spread**, so
  `constant_observables()` strikes it out. The informative tables are
  bit-identical to D-335's; `policies_that_separate_question_scene()` is still
  `()`.
- ⭐ **The general form is the result, not the one channel.** Both members of the
  new `OBSTACLE_SIDE_OBSERVABLES` census are built from the obstacle's scripted
  velocity and the reference path *alone*, and both are constant at every index.
  The reason is structural: every obstacle in the suite runs a piecewise-linear
  yaml schedule and every path is a fixed polyline, so whichever segment the read
  index lands on supplies a literal — seed moves the index, not the segment.
- ✅ **The zero-spread pin caught the entrant itself.** `constant_observables()
  == ("obstacle_speed",)` went red on the new column, which is exactly what
  D-334's docstring promised it would do ("a future observable that also fails
  to move is the same mistake, and this goes red when one is added"). First time
  that pin has been paid off by a later cycle.
- ⚠️ **The placement gap billed again, and the pre-empt still does not cover it.**
  `census_preempt` named the tally drift (121→122) at the stage in ~2 s, but the
  deep-only literal was invisible to it — caught only by running
  `test_guard_reflexivity.py` alone (**302 s**), which is the third consecutive
  cycle to pay for placement after a clean pre-empt.

## North-star delta

- **No movement toward the north star, and the negative is now general.** D-335
  closed the *index* degree of freedom; this closes the obvious half of the
  *observable* one. The switch D-333's 5/5 coverage needs still cannot be built,
  and the "미관측 분포" clause remains untouched.
- The delta that *is* real: the remaining search space is now named rather than
  open. Any further obstacle-side velocity channel is futile by construction, so
  a `cut_in` separator must read something the **robot** did — and the three
  robot-side channels already in the set are measured not to separate it.

## Key learnings

- **A channel can be "cut-in-specific" in its physics and still be a yaml
  constant in its measurement.** The piecewise schedule was a real reason to
  expect spread, and it was wrong for a reason no amount of thinking about the
  physics would have surfaced: the segments are long relative to the seed-induced
  jitter in the read index, so all eight seeds land on the same one.
- **`is_constant` is doing more work than the module claimed.** It was written as
  a control on `obstacle_speed`; it turns out to be a filter on an entire
  *construction class*. Recording it as `OBSTACLE_SIDE_OBSERVABLES` is what makes
  that reusable rather than a fact about two columns.
- **Running one test file beat running the suite, by ~9 min.** 302 s of
  `test_guard_reflexivity.py` found the deep-only placement that the 2 s pre-empt
  structurally cannot see. That is a cheaper standing move than either extreme.

## Recommended next 1–3 priorities

1. **Ask whether the scenario suite can even answer this question** — every
   obstacle is an open-loop yaml script, so obstacle-side observables carry no
   seed variance *by construction*. A scene with a reactive (robot-conditioned)
   obstacle is the precondition for any further separability work.
2. **Prune the `risk`/`frozen_risk` duplicate** — 40/40 identical arm-seed pairs;
   the evidence is maximal and the pair costs a registry slot in every census.
3. **Cover placement in `census_preempt`, or record that it cannot be** — three
   consecutive cycles have paid for a literal the pre-empt is clean across.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/scene_separability.py`, `eval/mppi_sandbox/tests/test_scene_separability.py`, `eval/mppi_sandbox/tests/test_guard_reflexivity.py`
- TSV row appended: pending
