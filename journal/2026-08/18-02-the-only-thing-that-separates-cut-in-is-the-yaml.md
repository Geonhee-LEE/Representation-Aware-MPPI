# The only thing that separates `cut_in` is the yaml

- **Cycle**: 2026-08-18 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — measure whether `cut_in` is separable by plan-time observables (Q-162)
- **Phase**: P3
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/scene_separability.py`: five plan-time observables
  (`lateralness`, `closing_speed`, `bearing_rate`, `obstacle_speed`, `min_ttc`)
  read off **baseline** (`stock_mppi`) rollouts at the critical-clearance
  instant, over all 5 hostable scenes × 8 seeds = 40 rollouts, **76.2 s**.
- Measured **separability**, not a classifier — Q-162 explicitly said five
  scenes cannot justify fitting one. `separates(scene, obs)` is the strict
  no-overlap test: a scene's 8 seeds entirely outside the other 32's range.
- Ran the control on **all five** scenes rather than only on `cut_in`, then a
  second control on the observables themselves.

## What worked / what failed

- **`cut_in` separates — on `obstacle_speed` alone, and that observable has
  zero within-scene spread.** It takes one value per scene across all eight
  seeds (`1.25 / 0.0 / 1.0 / 0.8333 / 0.75`): a scenario parameter read through
  a rollout-shaped function, not a measurement. Separating on it is reading the
  scene label. That is Q-162's option **(C)**.
- **Strip the constant and `cut_in` separates on nothing.** The only informative
  separation in the whole matrix is `min_ttc` on `cafe_head_on_v0` — a different
  scene, and one the switch does not need since `cbf_mppi` already wins it.
- **The scene-level control did *not* fire, and I had predicted it would.** I
  wrote the docstring expecting all five scenes to separate (making the yes
  vacuous). Measured: **3/5** — only *extremal* scenes separate, because the
  test is against the pooled range, not the value set. `separation_is_distinctive()`
  is therefore **True**. Had I stopped at that control I would have reported
  qualified support for option (A). The zero-spread control is what overturned it.
- The prediction was caught by the test I had already written against the
  constant, not by re-reading — third cycle running where a pin caught a typed
  claim.
- `census_preempt` fired at the stage on **both** its drifting censuses at once
  (guard tally 121→122, three unrecorded `loop_reach` rows), ~2 s against a
  ~840 s suite. First time both fired on one commit.

## North-star delta

- **A negative, and it downgrades the previous cycle's headline.** D-333's "5/5
  hostable coverage" holds as measured but is now explicitly **conditioned on an
  oracle**: the `cbf`/`social` union covers the set only if something tells the
  planner which scene it is in, and on this evidence that something is the
  scenario file. The north star's unseen-distribution clause is untouched by it.
- No movement on the core hypothesis. The one informative plan-time reading in
  the matrix belongs to the scene that did not need it.

## Key learnings

- **A separator with zero seed spread is not a measurement.** This is the
  reusable bar: any future observable must move across seeds of the *same*
  scene before its separation counts. Without it, "plan-time observable" and
  "scenario constant" are indistinguishable at the API surface — both are
  functions of the rollout's inputs.
- **Two controls can disagree, and the weaker one fires first.** The scene-level
  null (run the test on every scene) is the obvious control and it *passed* the
  question through. The verdict came from a control on the observable axis that
  I only added after seeing the numbers. Recording the intermediate verdict in
  a test (`test_the_scene_level_control_does_not_by_itself_sink_the_question`)
  is how the two stay unconflated.
- **Placement, not count, was again the second-order cost — but it was paid up
  front this time.** D-333 discovered its deep-only literal via an 824 s red;
  its own note said the pre-empt cannot see placement. Reading that note before
  the suite cost one grep.

## Recommended next 1–3 priorities

1. **Ask what `min_ttc` on `head_on` means for the switch** — it is the one
   informative separation and it is on the wrong scene. Is there a `cut_in`
   observable at a *non-critical* index (the current reading is hindsight-
   scoped, an upper bound), or is the scene genuinely invisible?
2. **Extend `census_preempt` to placement-vs-population** — the axis D-333
   named and this cycle paid a grep to cover by hand. Both literals are
   derivable from `guards()`.
3. **Prune the `risk`/`frozen_risk` duplicate** — 40/40 identical, unchanged.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/test_scene_separability.py, eval/mppi_sandbox/loop_reach.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
