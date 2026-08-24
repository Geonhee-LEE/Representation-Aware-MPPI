# Four of the five flagged sites were decoys — and the census that flagged them was reading its own list

- **Cycle**: 2026-08-24 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — place `cafe_obstacle_contested_v0` (the authoring cycle D-456 scoped)
- **Phase**: P3
- **Status**: in_progress (receipt RED — 16 failures; committed `6bc6369`, unpushed)

## What I tried

- Resumed a **strand the strand-check cannot see**: the 15:00 run graded `KILLED`
  and left the whole authoring deliverable *uncommitted* on disk — the 122-line
  `cafe_obstacle_contested_v0.yaml`, a **measured** `SCENE_SEED0` column (8 real
  rollouts), and 6 of the 15 pin sites already bumped. `cycle_artifacts
  stranded` reads `journal/` against `origin` and 15:00 never wrote a journal,
  so it reported "no stranded cycles" over a tree holding a cycle's work.
- Ran `census_preempt` as D-456 intended: `scene_count_pins` named **5**
  remaining stale pin sites, with the standing warning not to touch the two
  registered arm-count decoys.
- Checked each of the 5 against ground truth before bumping it, instead of
  working the list literally.
- Registered the newly-found decoys with the **mechanism** that makes each one a
  non-member, and inverted the decoy reflexivity test whose premise the ninth
  scene had just falsified.

## What worked / what failed

- **The census's work list was wrong in the over-flagging direction: 4 of 5.**
  Only `test_arrival_scope_census.py::test_every_shipped_scene_is_swept` was a
  live pin (`assert len(rows) == 8`, red on this tree). The other four hold an
  `8` that tracks a *different* population and must not move.
- **The three new decoy mechanisms are each distinct from the arm-count
  collision D-456 registered** — that entry had exactly one mechanism and
  assumed it was the class:
  - `test_cte_peak_vacuity.py` — `8 * 8 * 7` is a **historical cost constant**,
    the matrix width at the moment D-358 *declined* a widening. A record of a
    purchase not made; a scene addition leaves it true.
  - `test_lam_window_regeneration.py` — the population is `lam_windows.yaml` /
    `variants/lam_windows_w10.yaml`, neither of which globs `eval/scenarios/`.
    The new scene inherits no lam window **by its own declaration**, so that
    table did not move.
  - `test_scene_eligibility.py::test_exclusions_are_a_set_not_a_first_match` —
    the `8` counts *exclusion reasons* over the *excluded* scenes. Contested_v0
    is eligible (5 obstacles + declared 0.30 m margin), so it adds neither a
    scene nor a reason. **This one is scene-dependent**: it is a decoy for this
    entrant and would be a live pin for an obstacle-free one.
- **`test_exposure_timing_band.py` was the trap in the other direction.** A
  targeted pytest run reported it *passing*, which would have licensed dropping
  it as a fifth decoy — it passed only because it is **slow-gated and was
  skipped**. `_scenario_paths()` does glob `eval/scenarios/*.yaml`, so both its
  assertions (`5` obstacle scenes, `8` paths) are live and would have gone red
  in the full suite. A cheap local run and the graded suite disagreed, and the
  cheap one read clean.
- **The ninth scene retired the decoy registry's original invariant.**
  `test_the_arm_count_decoys_are_not_scene_pins` asserted the decoys *do*
  collide with the current scene count — true only while both populations were
  8. At 9 it began failing on a registry that was entirely correct, and its own
  docstring had predicted exactly this ("if the two ever differ … the entry's
  disambiguation note should say so").
- Zero sim, zero controller lines this cycle; the 8 rollouts in the shipped
  `SCENE_SEED0` column were measured by the 15:00 run, not by this one.

## The suite refuted half of this

Everything above is what I believed when `census_preempt` returned **8 of 8
CLEAN**. The full receipt suite then came back **RED: 16 failed, 4165 passed**,
and **not one failure was on either scene census's list**:

| module | failures |
|---|---|
| `test_obstacle_reach.py` | 3 |
| `test_scene_transfer.py` | 3 |
| `test_threshold_vacuity.py` | 2 |
| `test_margin_vocabulary.py` | 2 |
| `test_goal_revisit_screen.py` | 2 |
| `test_tail_mean.py`, `test_quoted_counts.py`, `test_lam_calibration_table.py`, `test_cte_vacuity.py` | 1 each |

- **The sharpest case is `test_threshold_vacuity.py`, which is *registered as a
  decoy*.** The red functions are not the registered one — they are two *other*
  functions in the same file (`test_census_matches_the_scenarios_on_disk`,
  `test_every_shipped_scene_is_graded`). The registry is keyed file → function,
  so marking one function a decoy quietly removed **the file's other functions
  from the population**. And `test_obstacle_reach.py::test_population_is_the_
  same_eight_scenes_the_cte_sweep_graded` says "the same eight scenes" in its
  own name.
- **So D-455's "23 glob consumers" was right and D-456's 15 pins were a subset
  of it.** Entries 7 and 8 claimed the blast radius was "fully visible in
  0.05 s"; that was true *only of their own list*. This is the fifth recurrence
  of D-317/D-344/D-433/D-455 — an uncovered population reads exactly like a
  covered one — and this time it happened one level up, inside the tool built to
  prevent it, **while it returned CLEAN**.
- The push gate refused, correctly. `6bc6369` is committed and **unpushed**.

## North-star delta

- **Corrected: the 9th scene is placed but NOT graded.** It is the first
  obstacle-bearing scene added
  since the matrix froze at 8, and the first that stages the 5-actor contest
  `cafe_obstacle_crossing_v0` advertises and never ran (D-451: 2 of 5).
  Avoidance-capable set 5 → 6. This is direct movement on the "다중" obstacle
  class, which STATE has listed as untested for ~40 cycles.
- **A measured finding is already in the tree**: every arm's clearance is an
  order of magnitude larger on contested_v0 (0.43–0.73 m) than on its sibling
  (0.005–0.33 m) — the contested band is not threadable at cruise, so the arms
  yield instead, and the discriminating axis moves off clearance onto **time**
  (166 → 1001 steps, a 6× spread at near-identical completion). The pair is a
  controlled comparison: identical path, lanes, actor speed, acceptance block.
- P5 entry is **2026-09-03, ten days out**, and the matrix it will grade is now
  9 wide with the contest represented.

## Key learnings

- **A census returning CLEAN is a statement about its population, not about the
  tree.** This is the finding that outranks everything else here: 8 of 8 clean
  and 16 red on the same commit. The cheap pre-empt is still worth its 2 s — it
  caught 2 real pins — but "clean" must be read as "the pins I know of agree",
  and D-318's `UNCOVERED` line does not help when the omission is *inside* a
  census that thinks it is complete.
- **A file-keyed decoy registry silently excludes the file's other functions.**
  Marking `test_threshold_vacuity.py::test_head_on_...` a decoy is what kept two
  live scene pins in that same file off every list. The registry's granularity
  and its population's granularity have to match.
- **A census that fixes under-listing can over-list, and the second error is
  not cheaper.** D-456 was built because D-455's hand list missed 6 pins; its
  first live use flagged 4 sites that must not move. Working *either* list
  literally corrupts the tree — the under-list leaves reds, the over-list
  *creates* them on assertions that were correct before the cycle started.
- **"Same size" is a property of a moment, not an invariant.** Every decoy
  mechanism here is "an 8 that isn't the scene count", and the registry's job
  survives the counts diverging only if it records *why* each entry is a
  non-member. Hence the reason string, and the inverted test: a decoy must never
  assert the derived count — true whether or not the two happen to be equal.
- **A skipped test reads exactly like a passing one.** This is the D-400 /
  D-394 shape (a narrow population reads cleaner than a wide one) arriving in
  the cheapest possible place: `-q` output. Over that 9-module subset,
  `1 failed, 153 passed, 9 skipped` (subset, not the suite) was one line above
  the answer and the answer was in the *skipped* count.
- **One decoy's status depends on the entrant, not the site.** The
  eligibility-complement pin is the first registry entry that cannot be
  classified once and left alone; the next scene addition has to re-read it.

## Recommended next 1–3 priorities

1. **Turn the 16 reds green — this is the whole next cycle.** The work list is
   now empirical rather than typed: 9 modules, named above, none of which any
   census enumerated. Treat this as the real remaining price of Q-197(a), the
   one D-456 never costed.
2. **Re-key the scene census population off the 23 glob consumers D-455
   measured, not off a hand list** (Q-183, now with the strongest possible
   evidence). Sub-requirement discovered here: the decoy registry must be keyed
   per *function*, since one file holds both a decoy and two live pins.
3. **Re-sweep `lam_windows.yaml` for the 9th scene** — the gap the scene
   declares in its own notes; blocks it from any swept A/B. Deferred behind (1).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/scenarios/cafe_obstacle_contested_v0.yaml, eval/mppi_sandbox/census_preempt.py, eval/mppi_sandbox/scene_census.py, eval/mppi_sandbox/path_curvature.py, eval/mppi_sandbox/arrival_scope_census.py, eval/mppi_sandbox/tests/{test_census_preempt,test_arrival_scope_census,test_exposure_timing_band,test_avoidance_coverage,test_scene_eligibility,test_city_crossing_scene,test_epistemic_reach_screen,test_path_curvature}.py, docs/decisions.md
- TSV row appended: yes
