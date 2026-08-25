# The scene named after an obstacle did not have one — and giving it one split the temperature window by controller

- **Cycle**: 2026-08-02 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE item #1 — give the 4 obstacle-free scenes sandbox `dynamic_obstacles`
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE item #1, the head-of-line technical item 17:00 left: 4 of the 8
  sandbox scenes carry no `dynamic_obstacles`, so "avoidance across the
  scenario matrix" was a claim about half of it. Started with
  `cafe_obstacle_crossing_v0`, whose 5 hazards existed only in
  `cafe3_jazzy.sdf.xacro` — a Gazebo world file the NumPy sandbox never loads.
- Gave it 5 scripted actors sweeping the `y ∈ [-2, -4]` walking band on
  staggered schedules, two counter-flow, plus the `goal_reached` / `collision`
  / `min_distance_to_obstacle` acceptance keys it never had. Screened the
  result against 17:00's goal-ball precondition **before** running anything.
- Generalised the guard rather than the fix: `feasibility.py` gains
  `is_avoidance_measurable` and `vacuous_acceptance_checks`, and
  `test_avoidance_coverage.py` pins the avoidance denominator as strict set
  equalities.
- Re-measured the scene's `lam` window, since changing a scene's obstacle set
  invalidates the row 16:00 recorded for it.

## What worked / what failed

- **The scene is now genuinely hazardous.** At the shipped `lam = 0.1` it
  closes to **0.0097 m** of an actor — clears `collision: 0`, fails
  `min_distance_to_obstacle: 0.30`. The temperature degeneracy this branch has
  characterised through ESS statistics finally has a *clearance* number on it.
- **The measured window moved, and moved differently per controller.**
  Same scene, only intervention = adding obstacles:

  | controller | window (empty scene) | window (5 actors) |
  |---|---|---|
  | `stock_mppi` | `[0.2, 0.4]` | `[0.4, 0.8]` |
  | `risk_mppi`  | `[0.2, 0.4]` | `[1.6, 3.2]` |

  They **overlapped completely before and are disjoint after**. Both the
  independent ladder and the calibrator agree cell-for-cell.
- **Scope of that, stated honestly: 1 of the 7 calibratable scenes.** The full
  regenerated table has `stock ∩ risk` non-empty on the other six, and
  `cafe_convoy_v0` carries the same *five* obstacles without the effect — so
  obstacle count alone does not explain it, and the likelier factor is that the
  crossing actors are staggered and counter-flowing where the convoy moves in
  formation. One scene is enough to invalidate a single-`lam` A/B *there*; it
  is not yet evidence the practice is broadly wrong.
- **Regeneration doubled as the determinism check the generator never had.**
  The new table differs from 16:00's in exactly 4 lines — both cells of the
  scene I changed. Everything else, including the ~7×-cost `city_figure8_v0`,
  reproduces byte-identically.
- **The calibration table could not be regenerated at all.** `--scenarios`
  defaults to `eval/scenarios/*.yaml`, which matches the generator's own
  output. 16:00's run worked only because the file did not exist yet; every
  re-run since died with `KeyError: 'start'` in a worker. The header has said
  "do not hand-edit; re-run it instead" the whole time.
- Suite **149 → 154 passed + 1 xfailed**; the 5 new coverage tests cost
  **0.08 s** (they simulate nothing). No existing test broke.

## North-star delta

- **First movement on the avoidance clause in six cycles.** Scenes that can
  contribute an avoidance number: **4 → 5**; scenes that can contribute a
  *completed-run* one (excluding `cafe_cut_in_v0`'s occupied goal ball):
  **3 → 4**. Still half the matrix, but the count is now checked rather than
  assumed.
- A near-miss is measurable in the sandbox for the first time on this scene:
  0.0097 m at the shipped defaults is a concrete safety number, not a proxy.
- No tracking metric improved. This buys measurement *reach*, not capability.

## Key learnings

- **Per-scene calibration is not sufficient; per-*arm* may be required.** Q-036
  asked whether a cross-scene aggregate survives per-scene calibration. There
  is now a scene where even that is not enough: the two controllers' windows
  are disjoint, so an A/B between them has no shared admissible temperature,
  while every A/B this branch has run reports both arms at one `lam`. On the
  present evidence (1 of 7 scenes) this is a demonstrated failure case rather
  than a general refutation — which is exactly why it needs answering before
  the re-baseline picks a convention, not after.
- **The controlled intervention confirms the cost-magnitude mechanism.** 15:00
  inferred that admissible `lam` tracks the magnitude of the scene's cost
  landscape, from cross-scene correlation. Here the scene is fixed and only the
  obstacle set changes: adding hazards raised both windows, and raised
  `risk_mppi`'s 8× against `stock_mppi`'s 2× — the arm with the extra cost term
  moves further. That is the mechanism, not a correlate, and it is why
  Watson & Peters' *solve-for-the-temperature* framing (feed 16:00, STATE #12)
  is the right shape.
- **A generated artifact whose regeneration is untested is a hand-edited
  artifact.** The defect was invisible for exactly as long as nobody needed to
  re-run the generator. Same family as 17:00's unsatisfiable acceptance block
  and this cycle's vacuous `collision: 0`: a declared property nothing
  exercises.
- **Vacuous-pass defects are worse than impossible-pass ones.** Q-037's scene
  could never pass; a scene asserting `collision: 0` with nothing to hit can
  never fail. The first depresses reported numbers, the second inflates them.

## Recommended next 1–3 priorities

1. **Decide whether a single-`lam` A/B is admissible at all** (new **Q-039**).
   `cafe_obstacle_crossing_v0` now has disjoint per-controller windows, so
   #67/#68/#69's A/Bs need either per-arm temperatures or an explicit statement
   that the comparison is at a shared, non-admissible one.
2. **Give the remaining 3 obstacle-free scenes obstacles** — `cafe_straight_v0`
   is deliberately clean (it is the tracking baseline), so the real targets are
   `city_curved_v0` and `city_figure8_v0`. Same recipe, screen first.
3. **Re-measure `city_curved_v0`'s `lam = 3.2` hole** (old STATE #3) — now that
   the generator can actually be re-run.

## Artifacts

- PR: #67 (open, already in the review queue — no new review bandwidth)
- Files touched: `eval/scenarios/cafe_obstacle_crossing_v0.yaml`,
  `eval/mppi_sandbox/feasibility.py`, `eval/mppi_sandbox/calibrate_lam.py`,
  `eval/mppi_sandbox/tests/test_avoidance_coverage.py`,
  `eval/mppi_sandbox/tests/test_lam_calibration_table.py`,
  `eval/mppi_sandbox/tests/test_mppi_update_consistency.py`,
  `eval/scenarios/lam_windows.yaml`
- TSV row appended: yes
