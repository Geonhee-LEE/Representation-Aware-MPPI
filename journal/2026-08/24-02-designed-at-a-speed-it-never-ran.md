# Q-191 answered by citation — and the scene loses three of its five actors

- **Cycle**: 2026-08-24 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE claude-actionable #1 — Q-191 declared vs realized `target_speed_mps`
- **Phase**: P3
- **Status**: keep

## What I tried

- Took Q-191's own prescribed action — grep `target_speed_mps` for consumers —
  and treated its stated decision rule ("zero refs in the sandbox path ⇒ (a)
  confirmed") as the thing under test rather than as the method.
- Cross-read `docs/decisions.md` for prior art before deriving anything, which
  is the step D-439 named as structurally missing from REVIEW.
- Priced the realized speed against the scene's own geometry comment, which
  derives its actor-contest timing arithmetically from `0.3 m/s`.

## What worked / what failed

- **Q-191 was already answered, 21 days before it was opened.** D-024
  (2026-08-03) resolved Q-045 with exactly option (a): `target_speed_mps` is a
  value the closed loop does not read. D-025 then replaced it as the screen's
  traversal driver. Q-191 is a re-derivation, not a new question.
- **Q-191's decision rule would have returned the wrong answer.** The grep
  returns **~8 modules**, not zero — `exposure`, `obstacle_reach`,
  `path_curvature`, `excursion_tracking`, `feasibility`. By the rule as written
  ("zero refs ⇒ (a)"), non-zero refs reject (a). But (a) is true. The refs are
  all *simulation-free screen* modules reading `scenario.target_speed` for an
  offline nominal traversal; none of them is the closed loop. The grep's
  population and the question's population are different populations —
  the D-317 / D-450 shape a third time.
- **Q-191's Lean argued from a coincidence to deny coincidence.** It read robot
  ≈ 0.75 against actor `speed: 0.75` as "too exact" and suspected a shared
  default. The robot's speed is `calibrated_cruise(0.8) = 0.723` — set by the
  `w_terminal / w_speed` ratio regime (D-025's `CRUISE_BY_VMAX`, measured on
  *this very scene* and pinned by `test_cruise_driven_nominal.py`). The actors'
  0.75 is declared per-actor in the yaml. Two unrelated mechanisms landing
  0.027 apart.
- **The new part, and it is not a bookkeeping point.** The yaml's geometry
  comment derives the actor contest from the declared speed: "robot descends
  x = 0 at 0.3 m/s, so it is at y = -2 around t = 6.7 and y = -4 around
  t = 13.3 … the corridor is contested for most of that window." At 0.723 m/s
  the robot is in the band `y ∈ [-2, -4]` during **t ∈ [2.77, 5.53]** and
  reaches the goal at t = 6.92 s. Actors in motion during transit:

  | speed | band transit | actors live |
  |---|---|---|
  | 0.300 declared | t ∈ [6.67, 13.33] | **5 / 5** |
  | 0.723 realized | t ∈ [2.77, 5.53] | **2 / 5** — `ped_cross_1`, `ped_cross_2` |

  `ped_cross_3` starts at t = 6.0, **0.47 s after the robot has already left
  the band**; `ped_cross_4` (t = 9.0) and `ped_cross_5` (t = 12.0) never
  overlap the transit at all. The staggered five-actor contest the scene was
  built to stage has never once been run.

## North-star delta

- **The scene named after obstacle avoidance stages 40 % of the avoidance it
  declares.** Every measurement on `cafe_obstacle_crossing_v0` on this branch —
  the four null sweeps, D-446's lever ladder, D-447's kinematic band — was
  taken against a 2-actor encounter described in the file as a 5-actor one.
  The measurements stand; their *scene description* does not.
- Zero sim, zero controller lines, zero new source. The table above is
  arithmetic over the yaml plus one in-tree calibrated constant.

## Key learnings

- **A question that names its own test can still name the wrong one.** Q-191
  was opened with a crisp, cheap, falsifiable action and that action decides a
  different question. Checking prior art cost less than running the test would
  have, and the test would have been actively misleading.
- **Re-derivation is now costing measurable cycles, not just tidiness.** D-439
  named the mechanism (REVIEW's read set excludes `decisions.md`); D-437 was
  the sixth copy of D-140; Q-191 is the same failure on the Q side. The
  recurrence is the finding.
- **Declared scene parameters that the loop ignores do not stay inert — they
  propagate into prose that later cycles reason from.** D-024 correctly stopped
  the number from driving *code*, and it kept driving the *comment*, which is
  what three cycles of scene-fairness argument (Q-190, D-447) were reading.

## Recommended next 1–3 priorities

1. **Decide the crossing scene's canonical speed** — Q-195. Either re-stage the
   actor schedules against 0.723 m/s so the five-actor contest actually
   happens, or restate the scene as a two-actor encounter. The former re-opens
   this branch's measurement history; the latter is honest and free.
2. **Mechanise the check**: a test asserting each scene's declared
   `target_speed_mps`-derived prose matches `calibrated_cruise(v_max)`, or
   that no scene comment derives timing from an unread field. Budget a whole
   cycle — it adds a lam site, which has gone red on five consecutive cycles.
3. **Q-194 remainder** — semantic half, price already measured (306 : 11).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: docs/decisions.md, docs/deliberations.md, journal/2026-08/24-02-designed-at-a-speed-it-never-ran.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
