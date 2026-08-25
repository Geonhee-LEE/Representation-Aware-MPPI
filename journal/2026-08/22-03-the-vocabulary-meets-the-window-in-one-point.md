# The declared vocabulary meets the window in exactly one point

- **Cycle**: 2026-08-22 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `freeze-margin` Decide whether `cafe_freezing_v0` declares a `min_distance_to_obstacle`
- **Phase**: P3
- **Status**: keep

## What I tried

- Picked STATE's #1 actionable. Before writing anything, checked whether the tree
  already answered it — `declaration_gap` does most of the work: the seed-robust
  discriminating window for this scene is `(0.3359, 0.7713)`, derived from the
  8×8 ensemble, and it **deliberately proposes no value** ("the bar's value is
  scene intent and stays user-blocked").
- Took that refusal as correct and asked the narrower question it leaves open:
  the branch has already declared margins on four other scenes, so the choice is
  not over the reals. **How many values already in the vocabulary are interior?**
- Shipped `margin_vocabulary` (+13 tests): derives the vocabulary from the
  scenario yamls via `threshold_vacuity.declared_thresholds()`, grades each value
  against `declaration_gap.common_window()`, and pins the intersection count.
- Did **not** edit `cafe_freezing_v0.yaml`. The value is user-blocked by
  `declaration_gap`'s own scope statement and nothing this cycle found overturns
  that.

## What worked / what failed

- **The answer is one.** Vocabulary is `{0.30, 0.40}`. `0.30` (declared by 3 of
  the 4 declaring scenes) is a `FLOOR` — all 64 ensemble cells clear it and it
  straddles **zero** arms, so adopting it would flip the scene to eligible *and*
  grade it 64/64 green, a bar reporting avoidance skill it never tested. `0.40`
  (`cafe_head_on_v0` only) is `INTERIOR` — cuts 45/64 cells, separates 4/8 arm
  rows all-seeds, straddles 3 arms' own per-seed ranges.
- So `freeze-margin` is **forced up to precedent**: adopt an existing branch
  value and exactly one discriminates; or invent one outside the vocabulary and
  own that explicitly. That is a much smaller ask than STATE has been carrying.
- The near-miss worth recording: my first instinct was to sweep candidate margins
  and recommend one. That would have re-litigated a scope boundary
  `declaration_gap` had already drawn correctly. Reading the module's own
  "what this does not claim" section before building is what stopped it.
- Cost zero rollouts — every operand was a recorded constant or a yaml on disk.

## North-star delta

- **No metric moved**; no controller or rollout was touched. Honest zero on the
  measured picture: still `3/8 eligible, 1/3 measured`.
- What moved is the *cost* of the next measurement: a user decision that read as
  open-ended ("pick a clearance bar") is now a binary with a named default and a
  named reason to reject the obvious-looking alternative.
- Guards against a specific false green: had someone adopted `0.30` by analogy
  with the three scenes that use it, the census would have reported
  `cafe_freezing_v0` measured-and-passing on evidence that separates nothing.

## Key learnings

- **A scope refusal is a boundary, not a wall.** `declaration_gap` refused to
  propose a value and was right to. The productive move was to find the question
  strictly inside that refusal — precedent rather than optimality — instead of
  either overturning it or treating the item as blocked.
- **Derive the vocabulary too (D-413, again).** A typed `frozenset({0.30, 0.40})`
  would be correct today and would stop being the vocabulary the moment a fifth
  scene declares a third value. The graded claim here is a *count* of the
  intersection, so it must move when the population does — hence a
  `monkeypatch` test that adds a scene and asserts the verdict flips to
  `AMBIGUOUS`.
- **`0.30` being the branch's majority value is not evidence about this scene.**
  Three scenes declare it; it is vacuous on the only scene with an 8-seed
  ensemble to check it against. Popularity of a constant says nothing about its
  discriminating power on a scene with a different geometry.

## Recommended next 1–3 priorities

1. **`freeze-margin` handoff** — surface the forced choice to the user (adopt
   `0.40` by precedent, or invent). One yaml line once answered; `Owner=user`.
2. **`convoy-meas`** — record per-seed clearance for `cafe_convoy_v0` (5
   obstacles, margin 0.30): genuinely unmeasured, and the larger open cell.
3. **`floor-reach-recheck`** — D-374's `5.44x` window/null-floor ratio is the
   number that licenses declaring a bar here at all; re-read it before any
   declaration lands.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/margin_vocabulary.py, eval/mppi_sandbox/tests/test_margin_vocabulary.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
