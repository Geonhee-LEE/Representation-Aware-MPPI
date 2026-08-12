# The off-family step had no scene to stand on — and off-family the interaction mirrors

- **Cycle**: 2026-08-12 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #3 — a scene outside the `cafe_*` family (in-branch on PR #67 per D-140; gate 1 is 6/6)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's #3 ("a scene outside the `cafe_*` family — the next capability
  step") and found **it was not runnable as stated**: `scene_eligibility`
  already convicts both shipped off-family scenes, `city_curved_v0` and
  `city_figure8_v0`, of `NO_OBSTACLES`. Confirmed by running city_curved
  through the sandbox — `min_obstacle_clearance: Infinity`.
- Authored `eval/scenarios/variants/city_crossing_v0.yaml`: straight 12 m
  traverse of small_city's SW road, four pedestrians crossing perpendicular,
  each timed to be on the centreline as the robot arrives. env_class **B**
  against crossing's D, 0.6 m/s against 0.3, margin **0.30** chosen to match
  convoy/crossing so a cross-family reading is gradeable.
- Placed it in `variants/`, not the matrix, and pinned that placement by test.
- Walked the full `w_risk` × `w_ped` 2×2 on it at λ=0.8, 6 paired seeds — the
  same protocol D-219 used on the three cafe scenes.

## What worked / what failed

- 🟢 **The scene is eligible and contested.** 4 obstacles, margin 0.30, goal
  clearance 3.31 m, and the baseline's worst-case clearance is **0.0025 m** —
  so it avoids *both* censoring directions: city_curved's empty population and
  convoy's `BOTH_ARMS_CENSORED` floor where everything clears.
- 🟢 **Off-family, the interaction mirrors.** Cafe family (D-219): `w_ped`
  helps **with** the risk term (+0.3756 / +0.1968 / +0.0806) and is flat-to-
  negative alone. Here it is the other way round — **+0.0128 alone, −0.0001
  with** `w_risk=40`. The verdict token `SIGN_FLIP` reproduces; the *direction*
  does not.
- 🔴 **`is_interaction` is `False` off-family** — the ladder reads
  `SIGN_FLIP / CONDITIONAL / CONDITIONAL / INERT` across ε ∈ {1e-6, 1e-3, 1e-2,
  5e-2}, collapsing to INERT at 5 cm. D-219's threshold-robust conjunction,
  the claim that walk actually licensed, **does not survive leaving the cafe
  family.**
- 🔴 **The scene as tuned is too hard, and this caps what the reading
  licenses.** All four cells sit at median clearance 0.018–0.032 m against a
  0.30 m margin — every configuration is deep in violation, so the comparison
  is between four failing arms. That is head_on's censoring direction, and the
  0.0128 m step is small enough to be scene noise. Stated rather than buried.
- 🟢 5 new tests, all green. Zero pinned populations moved: `variants/` is
  outside the census glob, verified by the census still reading 8 scenes.

## North-star delta

- **First off-family scene in the repo that can host a clearance comparison at
  all** — the matrix went from 3 eligible scenes (all `cafe_*`) to 3 + 1
  off-family variant. The north-star gap STATE has named for weeks ("every
  measured scene is in the `cafe_*` family") is now one scene smaller.
- **A capability claim narrowed, honestly.** D-219 booked `is_interaction` on
  three scenes; that conjunction now has a measured counterexample. Knowing
  the claim is cafe-family-bounded is worth more than a fourth confirmation.
- No controller or representation changed — the planner is exactly as good as
  it was at 17:00. This bought a *measurement surface*, not capability.

## Key learnings

- **"Run it on another scene" can be blocked by the scene, and the screen that
  says so already existed.** `scene_eligibility` has convicted the city scenes
  of `NO_OBSTACLES` since D-159, and STATE still ranked the off-family walk as
  a next action for several cycles. The gap was not knowledge, it was that
  nobody ran the screen against the plan.
- **A verdict token reproducing is not the finding reproducing.** `SIGN_FLIP`
  is true on all four scenes now, and on the fourth it means the opposite. A
  cross-scene census that tallied verdict strings would have read 4/4 and
  called it generalization.
- **Family and difficulty got confounded and I could not separate them.** This
  scene is off-family *and* harder than any cafe scene. The mirror could be
  either. Naming that is cheaper than the walk that would resolve it.

## Recommended next 1–3 priorities

1. **Retune `city_crossing_v0` to an uncensored operating point** — stagger the
   four pedestrians so the corridor is contested but survivable, target a
   baseline worst-case near 0.30 rather than 0.0025, and re-walk the 2×2. This
   is what separates "off-family" from "too hard".
2. **Q-133's remaining rename direction** — unexecuted for six cycles, and the
   fixture work is now specified (`git mv` + content edit in
   `build_carried_drift_repo`).
3. **PR queue** — 6/6, no merge in 31 days. Nothing here is reachable by the
   executor.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/scenarios/variants/city_crossing_v0.yaml, eval/mppi_sandbox/tests/test_city_crossing_scene.py, docs/decisions.md, docs/deliberations.md, journal/2026-08/12-18-the-off-family-step-had-no-scene-to-stand-on.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
