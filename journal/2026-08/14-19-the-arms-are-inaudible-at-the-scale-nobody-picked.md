# The arms are inaudible at the scale nobody picked

- **Cycle**: 2026-08-14 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `arm-scale-audibility` (STATE #1)
- **Phase**: P3
- **Status**: keep

## What I tried

- D-263 froze Q-148's four arms and named `ARM_SCALE = 1.0` as the one input
  with no measurement behind it. This cycle measured it: are the epistemic
  channels loud enough to be heard beside the obstacle and path terms already
  in `_cost`, or is every arm the control?
- Found the instrument already shipped — `weight_units.measure` prices any
  additive coefficient in units of the cost it competes against, and
  `w_epist` / `w_voo` are both already in its `ADDITIVE_WEIGHTS`. So
  `arm_audibility` supplies the arm, the verdict vocabulary and the inversion,
  and re-derives no spread (D-047).
- Graded all three active arms on `cafe_obstacle_crossing_v0`, and swept
  `w_epist` across every scene this branch can run.

## What worked / what failed

- **The A/B is vacuous at `ARM_SCALE = 1.0`** — `ab_is_vacuous` returns `True`.
  No active arm has a channel the softmax can hear:

  | arm | channel | ratio | verdict | arm scale needed |
  |---|---|---|---|---|
  | `REPEL_ONLY` | `w_epist` | `0` | `SILENT` | — |
  | `ATTRACT_ONLY` | `w_voo` | `0.01842` | `FAINT` | `5.428` |
  | `BOTH_ON` | `w_voo` | `0.009843` | `FAINT` | `10.16` |

  Against `w_path` at `1.98`–`2.20` on the same runs, the attract channel is
  about two orders of magnitude down.
- **The two failures are different in kind, and only one is a scale problem.**
  `FAINT` is rescalable — the spread is linear in the weight, so the inversion
  is exact arithmetic, not a search. `SILENT` is not: `w_epist`'s spread is
  exactly `0.0` on *every* scene here (`obstacle_crossing`, `freezing`,
  `straight`, `head_on`, `cut_in`), at both `1.0` and `0.2918`. The shadow
  critic prices a shadow and none of these scenes casts one — D-021's reading,
  reproduced from a new direction.
- **A name I wrote was wrong and the mixed cell caught it.** I first called the
  inversion `required_scale`. It returns a *channel weight*, and on `BOTH_ON`
  that channel holds only a `0.7082` share of the scale — so the same number
  means `7.195` as a weight and `10.16` as a scale. Renamed to
  `required_weight` with `required_arm_scale(channel, arm)` doing the
  conversion off the arm. This is the third time the branch has caught one
  quantity wearing two names.

## North-star delta

- No closed-loop movement; this is still a cost-field reading. But it removes
  a live way for the next closed-loop cycle to waste itself: run the A/B as
  frozen and all four arms return the control, with the null misreadable as
  "the epistemic channel does not help."
- One unmeasured parameter of D-263's table is now measured on the scenes
  available, with the number that would fix it (`5.428` / `10.16`) rather than
  a direction.

## Key learnings

- **A frozen config is not a runnable config until every term in it has been
  priced against the terms it joins.** Six decisions argued the ratio to four
  decimals; the ratio decides the sign and the scale decides whether the sign
  is ever heard. D-256's `w ∈ {1,10,200}` invariance is exactly what made this
  easy to skip — it reads like the scale does not matter, and its scope is the
  cost field's sign, not the planner's cost landscape.
- **`SILENT` and `FAINT` must not share a return value.** Both are "inaudible",
  but one is repaired by a number and the other by a scene. Collapsing them
  would have produced a huge finite `required_scale` for `w_epist` and sent a
  future cycle to turn a knob that cannot work.
- The `SILENT` reading is scene-scoped and does **not** transfer to the A/B
  scene: `cafe_blind_corner_v0` is the one scene with an occluder and it is on
  unmerged PR #68, so it is quoted, never imported. `scene_caveat()` carries
  `recheck_on_merge: True` as data.

## Recommended next 1–3 priorities

1. **`arm-scale-pick`** — decide `ARM_SCALE` against a declared audibility bar
   rather than inheriting `1.0`. The measurement now exists; the pick is a
   decision like D-261's ratio was, and `10.16` is the mixed cell's floor.
2. **`voo-audibility-across-scenes`** — the `FAINT` ratio varies `0.0184`,
   `0.0229`, `0.0233` across three scenes. If the required scale is
   scene-stable, one scale serves the A/B; if not, the pick is per-scene and
   D-260's non-transfer bites again.
3. **PR #68 merge** (user) — still the only route to grading `w_epist` on a
   scene that casts a shadow.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/arm_audibility.py`, `eval/mppi_sandbox/tests/test_arm_audibility.py`
- TSV row appended: pending
