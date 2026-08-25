# Two 8/8 scenes, opposite causes — Q-108 answered

- **Cycle**: 2026-08-07 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Answer Q-108 — is the declared margin geometrically reachable?
- **Phase**: P5
- **Status**: keep

## What I tried

- Built the en-route analogue of `goal_ball_clearance`: `path_clearance()`, a
  **bottleneck (maximin) DP** over the station × time grid — the best
  worst-instant clearance any admissible schedule can hold within a given
  lateral corridor.
- Added `required_corridor()`, which bisects for the narrowest corridor at
  which the scene's own declared margin becomes attainable. This is the
  number Q-108 actually wants: 4 of the 5 obstacle-bearing scenes declare no
  `cte_max`, so there is no corridor in the yaml to plug in.
- Added `declared_corridor()` (`cte_max`, `float | None`) beside
  `declared_margin` — and made it refuse to read `cte_rms_max`.
- Screened all 5 obstacle-bearing scenes; 12 tests in
  `tests/test_path_clearance.py`.

## What worked / what failed

- ✅ **Q-108 answers differently for the two scenes D-120 graded identically.**
  `cafe_head_on_v0` on the reference path is **-0.550 m** (interpenetration)
  and needs a **1.00 m** corridor; `cafe_obstacle_crossing_v0` is **+1.400 m**
  on-path and needs **0.00 m**. Same 8/8 unsafe verdict, opposite causes —
  branch (ii) scene geometry for head-on, branch (i) controller for crossing.
- ✅ **The head-on number is a closed form the DP recovers rather than
  assumes**: `ped_head_on` walks y = -5.5 → +0.5 and the robot must traverse
  y = 0 → -4, a strict subset, so no schedule avoids an instant of zero
  longitudinal separation and the margin is *entirely* lateral —
  `0.40 + 0.3 + 0.3 = 1.00` exactly. Pinned as an identity, not a literal.
- 🔴 **The lean I was handed does not work as stated.** Q-108 proposed
  extending `goal_ball_clearance` along the path. That screen maximises over
  arrival time, which is sound at the goal because the goal is where the
  robot must *end and stay*. En route the robot has a second freedom — which
  station it occupies when — and maximising over station and time
  independently screens **every** dynamic scene clean, because the pedestrian
  is always somewhere else at some time. The fix is to maximise over whole
  *schedules* (min over time inside, max over schedules outside), which is a
  different quantity and needs the DP.
- 🔴 **The default screen on head-on is vacuous, on purpose and visibly.**
  `path_clearance` defaults its corridor to the declared `cte_max`; head-on
  declares none, so the default returns `inf` and passes. Reading
  `cte_rms_max: 0.30` as a corridor instead would be the screen retiring a
  scene over a bound that constrains the *run* and not the *instant* — a
  transient excursion can leave the rms compliant. `required_corridor` exists
  because the honest default says nothing.
- 🟡 **The tension head-on leaves is not a contradiction and I will not call
  it one.** The scene declares no hard lateral bound, so a 1.00 m excursion
  is not forbidden — it is 3.3× the 0.30 m *rms* budget the scene does
  declare, and whether those two are jointly satisfiable is unmeasured
  (Q-109).
- 🟡 The time grid can miss the exact contact instant by half a step, so the
  on-path head-on bound reads -0.550 where the exact value is -0.600. Errs
  **optimistic**, which is the direction the screen is allowed to err in;
  pinned in both directions.

## North-star delta

- **The project's first quantitative safety target now has an owner, per
  scene.** `cafe_obstacle_crossing_v0`'s 0.30 m is a controller target with a
  proof that timing alone suffices. `cafe_head_on_v0`'s 0.40 m is not a
  controller target until the scene states a lateral budget that admits it.
- D-120's `unsafe_rate = 0.6667` headline is unchanged, but 16 of its 32
  unsafe seeds are now attributed to a scene declaration rather than to the
  planner.
- Costs no simulation: the whole 5-scene screen runs in **0.8 s**.

## Key learnings

- **A screen's soundness argument does not travel with its formula.**
  `goal_ball_clearance`'s max-over-time is sound only because the goal ball
  removes the schedule freedom. Copied one station earlier it becomes
  vacuous — and vacuous in the passing direction, which is the dangerous one.
- **Two scenes failing the same metric identically is not evidence they fail
  for the same reason**, and D-120 had no way to tell. The cheapest
  discriminator was geometric and needed no run.
- Screens that must never retire a passable scene should return `inf` when
  the input is absent, not a permissive default — the `inf` is legible as
  "this said nothing", a permissive number is not.

## Recommended next 1–3 priorities

1. **Declare a lateral budget for `cafe_head_on_v0` or restate its margin** —
   `cte_max ≥ 1.0` admits the 0.40 m margin; anything less makes it
   permanently red. Needs a human call on which the scene means (Q-109).
2. **Re-attribute the D-120 headline** — split `unsafe_rate` by whether the
   scene's margin is corridor-attainable, so the safety number the project
   quotes separates controller debt from declaration debt.
3. **Answer Q-107** (per-cell temperature aggregation) — still open from
   D-119 and it gates cross-controller deltas on `cafe_obstacle_crossing`,
   now the one scene proven to be a controller target.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic → #67)
- Files touched: eval/mppi_sandbox/feasibility.py, eval/mppi_sandbox/tests/test_path_clearance.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes
