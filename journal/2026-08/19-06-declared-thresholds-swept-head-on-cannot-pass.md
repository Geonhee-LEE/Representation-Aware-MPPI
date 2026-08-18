# The sweep found vacuity in the other direction — `head_on` declares a bar no arm can clear

- **Cycle**: 2026-08-19 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — sweep every scene's declared acceptance thresholds against attained clearance
- **Phase**: P5
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/threshold_vacuity.py`: for every shipped scene, read the
  declared `min_distance_to_obstacle` out of the yaml and grade it against the
  clearance range the arms actually attain, from tables already on disk
  (`scene_census.SCENE_SEED0`, `clearance_census.SHIPPED_ARM_CLEARANCE`).
  **Zero new rollouts** — the whole sweep is a `python3 -m` that returns in under a second.
- Five verdicts: `VACUOUS_PASS` (threshold ≤ attained floor), `VACUOUS_FAIL`
  (threshold > attained ceiling), `DISCRIMINATING`, `UNDECLARED`, `UNMEASURABLE`.
- Re-graded the two scenes with 8-seed columns on disk to check the seed-0
  reading is not an artifact of one seed.

## What worked / what failed

- **`cafe_head_on_v0` is `VACUOUS_FAIL`**: it declares `0.40` and the *best* arm in
  the registry attains `0.2003 m` (`cbf_mppi`); the other seven land in
  `0.0039`–`0.0146`. 8/8 arms fail the criterion on every run, and have since the
  scene landed. This is D-241/D-344/D-356's defect class **mirrored** — and the
  failing direction is the more dangerous one, because it reads as *the scene is
  hard* rather than as *the scene is broken*. It is the scene D-131 took this
  project's first scored mechanism claim on.
- **D-356's convoy verdict is population-scoped, and generalising it would have been
  wrong.** Over the full 8-arm registry `convoy`'s `0.30` **discriminates** —
  `essps_mppi` attains `0.2874` and fails it. It is vacuous only over the two arms
  D-356 measured (worst `0.3297`). Both readings are right about their own
  population; the tempting scene-level generalisation is false.
- **`cafe_freezing_v0` declares no clearance threshold at all** despite 2 obstacles —
  so there is no criterion to be vacuous. It is the scene this branch has the *most*
  clearance data for (the whole 8×8 ensemble) and the least clearance grading.
  That is `acceptance_coverage`'s blind spot one layer out: it asks whether a declared
  key is computed, and cannot see a key nobody declared.
- **My own instrument committed finding #2's error on the first run.** `widened()`
  compared a full-registry seed-0 grade against a *two-arm* 8-seed grade and reported
  `convoy` as "moved" — a population change attributed to the seeds. Fixed to restrict
  both sides to the same arms; the move disappeared and all three scenes read `unmoved`.
- `census_preempt` caught the unregistered loop-population row at the stage (~2 s)
  instead of 21 min into the suite — sixth consecutive cycle it has done so.

## North-star delta

- The acceptance matrix's **clearance** column is now swept end to end: of 8 scenes,
  3 are `UNMEASURABLE` (no obstacles), 1 `UNDECLARED`, 3 `DISCRIMINATING`, **1 vacuous**.
  So the bottleneck's worry — "how much of the pass/fail signal is structurally
  incapable of failing" — has a bounded answer for this key: **one scene**, and it
  fails-closed rather than passes-open.
- 물체회피 grading is *better characterised*, not yet better. No controller changed.
- The blind spot is named rather than closed: `UNSWEPT_KEYS` pins the **14** other
  declared acceptance keys this sweep does not cover, because no attained-range table
  exists for them on disk.

## Key learnings

- **Vacuity has two directions and this project had only ever looked for one.** Every
  prior finding (D-241, D-344, D-356) was a threshold nothing could *fail*. A threshold
  nothing can *pass* is equally ungraded and much better camouflaged — it produces a
  red column that looks like an honest hard scene.
- **A vacuity verdict is a statement about a population, not about a scene.** The same
  threshold on the same scene reads `VACUOUS_PASS` over one arm pair and
  `DISCRIMINATING` over the registry. Any future vacuity claim must name its arms.
- Checking `head_on`'s `0.40` against the attained ceiling costs one second and would
  have been available on the day the scene landed. The expensive part was never the
  measurement — it was not knowing to ask.

## Recommended next 1–3 priorities

1. **Decide what `cafe_head_on_v0`'s `0.40` should be** — it is either a real bar the
   arms must rise to (in which case the scene is correctly reporting total failure and
   the branch has an open safety debt) or a mis-set constant. The sweep cannot tell
   which; a human judgement on the scene's intent settles it.
2. **Extend the sweep to `cte_rms_max`** — the next-most-declared key (5 scenes) and
   the one carrying the 경로추종 half of the north star.
3. Widen `convoy` cross-track to 16 seeds (unchanged, still the weakest link in the
   branch headline at 5/8).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/threshold_vacuity.py, eval/mppi_sandbox/tests/test_threshold_vacuity.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md
- TSV row appended: pending
