# The scene was not the defect, and neither was the figure-eight

- **Cycle**: 2026-08-03 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Triage `city_figure8_v0`'s 0.016 m/s cruise (Q-047)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE item **#1**, the head-of-list technical item D-025 promoted: is
  `city_figure8_v0`'s 0.016 m/s cruise a third scene defect (Q-037's class) or
  a real controller failure on a self-intersecting reference?
- Ran the **two-directional controlled intervention** (D-018 discipline) rather
  than inspecting the scene: open figure-8's closure, and independently *close*
  a healthy scene's goal onto its start.
- Followed with a **2×2 over the two goal-distance terms** (`goal_slowdown_gain`
  ramp × `w_terminal`) to rank which one binds, plus a healthy-scene control.
- Shipped the resulting precondition as a static screen in `feasibility.py` —
  the module Q-037 created for exactly this move — with 11 tests.

## What worked / what failed

- **Both of Q-047's options are wrong, and the second one dies cleanly.**
  `city_curved_v0` has no self-intersection and cruises a healthy 0.739 m/s,
  4/4, 21.3 s. Change **only** `goal := start` and it collapses: cruise `NaN`
  (a stall by `cruise_speed`'s own definition), 2/4, 100 s timeout. So a
  self-intersecting reference is **not necessary** to produce the failure.
- **And the first dies too.** Opening figure-8's closure recovers cruise 15×
  (0.0164 → 0.2538) but the run still times out at 240 s having driven **13.1 m
  of a 30.6 m reference**. Repairing the scene is necessary and *not
  sufficient*, so "defective scene" does not describe it either.
- **The mechanism is the terminal cost, not the speed ramp — and I had the
  ranking backwards until the 2×2 ran.** Dropping the ramp alone moves driven
  arclength the *wrong way* on both scenes (13.11 → 11.78, 5.04 → 4.72).
  Dropping `w_terminal` moves it 13.11 → **73.23**. `w_terminal = 30.0` against
  `w_speed = 2.0` predicts exactly that ordering.
- **So the sentence is "the robot was told it has already arrived", not "told
  to go slowly".** At the crossing point — which *is* the goal — the terminal
  term sits at its global minimum, so every rollout that leaves is penalised.
  The loop parks on its own goal with half the path unvisited.
- **The completion guard was measuring the start.** `ab.reached_goal` reads the
  last sample only; when `d(start, goal) ≤ goal_xy_tol` a run that never moves
  satisfies it. That is why 03:00 read "3/4 reached" at 0.016 m/s.
- **Control held.** Removing both terms from the *healthy* scene still finishes
  4/4 at cruise 0.567 — the removal does not repair scenes by breaking the
  measurement.

## North-star delta

- **First genuine capability finding in ten cycles, though not the one Q-047
  proposed.** Not "MPPI fails on figure-eights" but: **the shipped objective
  assumes a monotone approach to the goal, and any reference that revisits its
  goal neighbourhood is outside its contract.** That is a real, general
  limitation of the planner on the path to "all environments" — loops, patrol
  routes, and return-to-start missions are all outside it.
- **The reportable matrix does not shrink.** Q-047's scene-defect branch would
  have cut it 4 → 3; it is refuted, so 4 stands.
- No tracking metric improved. The screen costs milliseconds and no rollout.

## Key learnings

- **A dichotomy offered by the previous cycle is a hypothesis, not a partition.**
  Q-047 posed "scene defect or controller failure" and the answer was a third
  thing that neither phrase covers. Both options were refuted by *one*
  intervention each — cheap, because the refutations were designed before the
  runs.
- **Reproducing a failure on a scene that lacks the suspected feature is worth
  more than any amount of inspecting the scene that has it.** B1 — inducing the
  stall on a non-self-intersecting scene — did all the work.
- **Rank your mechanism's terms before writing the mechanism down.** I had the
  ramp as the cause from code reading; the 2×2 showed it is nearly inert and
  the terminal term is 30:2 dominant. The 2×2 cost one run and changed the
  finding's whole sentence.
- **A guard that reads one sample can be satisfied by the initial state.** The
  same defect class as D-023/D-024: a statistic validated on the population it
  was not defined over.

## Recommended next 1–3 priorities

1. **Q-048 — repair the contract, not the scene**: drive `v_ref` and the
   terminal term off *remaining arclength* rather than Euclidean `d_goal`, and
   make `reached_goal` require completion as well as proximity. Belongs on the
   re-baseline branch (#11) — it moves every shipped number.
2. **Try the alternate-perspective cost construction** (feed 2404.07781) — now
   the longest-deferred candidate, **fourth** cycle raised and not picked.
3. **Re-run the audible/deaf partition through `reach_on_trajectory`** using
   `speed_audit.calibrated_cruise` for the fan warm start.

## Artifacts

- PR: #67 (already in the queue — this cycle adds no review bandwidth)
- Files touched: `eval/mppi_sandbox/feasibility.py`,
  `eval/mppi_sandbox/tests/test_goal_revisit_screen.py`, `docs/decisions.md`
  (D-026), `docs/deliberations.md` (Q-048), `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
