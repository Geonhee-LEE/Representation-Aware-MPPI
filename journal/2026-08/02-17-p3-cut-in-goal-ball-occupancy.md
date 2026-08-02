# Q-037 answered: `cafe_cut_in_v0` is a scene defect, not a capability gap

- **Cycle**: 2026-08-02 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (PR #67, already in queue)
- **TODO**: STATE item #1 — diagnose `cafe_cut_in_v0`'s non-completion
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the top STATE claude-actionable: 16:00 measured `cafe_cut_in_v0` as
  uncalibratable for **both** controllers at a per-seed ESS spread of 1.00×,
  filed Q-037, and explicitly deferred the cause.
- Hypothesised the failure was terminal geometry rather than control, and
  checked it statically before running anything.
- Shipped the check as a **precondition module** (`feasibility.py`) rather than
  a fix to the one scene, then screened all 8 shipped scenarios.
- Cross-checked the static verdict against 16:00's ~500-run empirical ladder.

## What worked / what failed

- ✅ **The cause is arithmetic, and needs no simulation.** `ped_cut_in`'s
  terminal waypoint `(0, -3.8)` is held forever from `t = 5.0`; the goal is
  `(0, -4.0)` with `goal_xy_tol = 0.2`; summed radii are `0.3 + 0.3 = 0.6`.
  Best clearance attainable *anywhere the run is allowed to stop* is **−0.2 m**.
- ✅ **The scene's own acceptance block is self-contradictory.** It demands
  `goal_reached: 1` **and** `collision: 0`. Being at the goal *implies*
  interpenetration, so the two hard checks cannot both hold. That is what makes
  it a scene defect and not a controller result — Q-037 answered.
- ✅ **Static screen and the 500-run ladder agree exactly.** Both partition the
  matrix to `{cafe_cut_in_v0}`. Pinned as a strict set equality, not a subset
  with a vacuous-pass escape hatch (my first cut had one).
- ✅ **Only failure of 8, and not marginal** — the next-worst scene clears by
  **1.87 m**. The criterion is nowhere near its decision boundary.
- ✅ **Free in CI**: suite **142 → 149 passed**, **132.5 s → 132.5 s**. Seven
  tests at zero runtime because the screen simulates nothing — the opposite of
  the wide-ladder cost that forced 16:00's script/test split.
- 🔴 **Screening surfaced a second, larger gap I did not chase**: 4 of the 8
  scenes (`cafe_straight`, `cafe_obstacle_crossing`, `city_curved`,
  `city_figure8`) carry **zero** `dynamic_obstacles` in the sandbox —
  including one *named* `obstacle_crossing`, which relies on Gazebo cafe3
  actors that the NumPy sandbox never loads. Avoidance is measurable on 4
  scenes, not 8.
- ⏸️ **Did not fix the scene.** Q-032's lean (no baseline-changing edit
  mid-queue) applies directly: editing `cafe_cut_in_v0.yaml` invalidates the
  table 16:00 just committed. Verified the fix instead so the re-baseline
  branch can apply it cold — appending `{t: 9.0, x: 1.2, y: -4.6}` (the ped
  departs laterally instead of parking on the goal) lifts best clearance to
  **+0.94 m**, clearing even the declared `min_distance_to_obstacle: 0.30`.

## North-star delta

- **No new closed-loop capability — fifth consecutive measurement-validity
  cycle.** Honest: no avoidance or tracking number improved.
- What moved is the **denominator**. 16:00 established the 8-scene matrix is
  really 7; this cycle proves *why* in closed form and makes the exclusion
  reproducible in milliseconds instead of ~500 runs. Q-036's "the denominator
  is wrong" now has a mechanical screen behind it.
- The avoidance clause of the north star gets a **worse but truer** reading:
  obstacle avoidance is currently measurable on **4** sandbox scenes, not 8.

## Key learnings

- **A negative measurement should be re-derived statically before it is
  explained dynamically.** 16:00 spent ~500 closed-loop runs to learn "never
  completes"; the cause was two waypoints and a sum of radii. When the
  empirical and the static account agree, the static one is the one to ship —
  it is the cheap screen for scenes nobody has run yet.
- **Preconditions should be optimistic on purpose.** The screen maximises over
  the goal ball and over arrival time, so it can only ever *prove*
  infeasibility. An asymmetric check may retire a scene by mistake; this one
  structurally cannot.
- **A scenario's acceptance block can be unsatisfiable, and nothing was
  checking.** The matrix has carried a scene whose two hard checks exclude each
  other since it was written. That is a validation gap wider than this scene.
- **The screen paid for itself immediately by finding a bigger defect** than
  the one it was written for — half the matrix has no sandbox obstacles.

## Recommended next 1–3 priorities

1. **Give the 4 obstacle-free scenes sandbox `dynamic_obstacles`** — starting
   with `cafe_obstacle_crossing_v0`, whose name promises an obstacle it does
   not have. Until then no cross-scene avoidance aggregate means anything.
2. **Validate acceptance blocks at scenario load** — reject mutually
   unsatisfiable check pairs (`goal_reached` + `collision` under a proven goal
   occupancy) the way `target_speed_mps > v_max` should be rejected.
3. **Apply the verified `cafe_cut_in_v0` fix on the re-baseline branch**
   (`{t: 9.0, x: 1.2, y: -4.6}`, → +0.94 m) and re-run that one scene's
   calibration row.

## Artifacts

- PR: #67 (already open — no new review bandwidth consumed)
- Files touched: `eval/mppi_sandbox/feasibility.py`,
  `eval/mppi_sandbox/tests/test_scenario_feasibility.py`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes (`sandbox:pass=149/149`, keep)
- Commit: `b634320`
