# Q-197 answered (a) — and the uncovered-literal list had a decoy in it

- **Cycle**: 2026-08-24 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 (decide Q-197) folded with #3 (cover the remaining pinned scene literals)
- **Phase**: P3 (calendar P5 — branch is 43 days unmerged, see D-140)
- **Status**: keep

## What I tried

- Took the side Q-197 asked for rather than measuring it again: **(a) — buy the
  scene move before P5 entry (2026-09-03)**. The previous cycle said explicitly
  that a further measuring cycle is avoidance.
- Went to place the 9th scene, and priced the authoring rather than the
  verification. D-455 re-priced (a) at **1 suite**; that prices the *checking*.
  The **authoring** is 23 glob consumers + a new `SCENE_SEED0` column (8 arms,
  needs actual rollouts) + a `lam_windows` row + a `threshold_vacuity` column.
  That is not one hourly cycle, and no census entry changes it.
- So bought the piece that makes it one: shipped **`scene_count_pins`**, the
  8th census in `census_preempt`, covering the scene-*count* literals that
  entry 7 (`scene_population`, D-455) does not reach.
- Registered the arm-count **decoys** beside it, with a tamper each.

## What worked / what failed

- The census is live and clean: `8 shipped scenes, 9 count pins agree (8 files,
  2 arm-count decoys excluded)`, ~0.05 s against a 1681 s suite.
- **D-455's uncovered-literal list was wrong in both directions.** Of its four
  literals, `len(col) == 8` is an **arm** count that must *not* move when a
  scene lands; the other three are joined by **six more** scene pins that were
  on nobody's list. A cycle working that list literally would have bumped one
  pin that should not move and missed six that must.
- The reason it was wrong is structural and worth stating once: **the shipped
  scene count and the controller arm count are both 8**, so `== 8` is ambiguous
  at the shape level. No grep and no AST signature separates them — only the
  quantity's meaning does. That is why this registry is hand-enumerated where
  entry 7's is derived, and why `test_scene_count_pin_sites_all_resolve` guards
  the concession.
- My own elapsed estimate ran ~4× long (I read myself at ~29 min when
  `cycle_wallclock elapsed` said 6m46). Same inflation D-154 measured on TSV
  stamps, now observed on the in-cycle clock. The tool was right; I was not.

## North-star delta

- No acceptance metric moved. No rollout, no controller line — cycle ~41
  without a measurement.
- Real movement is on the **price** of the north-star move, not the move: the
  ninth scene's blast radius is now 15 pins visible in 0.05 s instead of 9 of
  them arriving as separate red suites. Q-197(a)'s remaining cost is authoring,
  which is now the only thing left in it.

## Key learnings

- **"Priced at 1 suite" and "affordable in 1 cycle" are different claims**, and
  D-454/D-455 established only the first. Verification cost is what this branch
  has learned to measure; authoring cost is what actually bounds a cycle.
- **Two populations of the same size are indistinguishable to every tool this
  repo has.** The scene/arm collision at 8 is the first recorded instance. Any
  future census over a hand-enumerable population should record its decoys, not
  just its members — an omission and a deliberate exclusion look identical from
  outside.
- The in-cycle wall-clock reading is worth taking **more than twice**. Taking it
  once early (SUITE_AFFORDABLE) and trusting my own sense afterwards is how I
  nearly cut a deliverable that was comfortably inside budget.

## Recommended next 1–3 priorities

1. **Place `cafe_obstacle_contested_v0`** — the authoring cycle, now with the
   full 15-pin blast radius pre-visible. Budget it as authoring, not as a suite.
2. **`SCENE_SEED0` for the 9th scene needs 8 rollouts** — decide whether the new
   scene ships with a measured column or an explicitly empty one.
3. Q-183 — derive the candidate census population; now with a fifth data point
   and a second non-AST one.

## Artifacts
- PR: #67 (open, D-140 — continuing on an already-open PR, no new branch/PR)
- Files touched: `eval/mppi_sandbox/census_preempt.py`, `eval/mppi_sandbox/tests/test_census_preempt.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
