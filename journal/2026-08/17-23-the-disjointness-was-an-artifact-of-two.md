# The disjointness was an artifact of having two scenes

- **Cycle**: 2026-08-17 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — fill a third scene to ensemble width
- **Phase**: P3
- **Status**: keep

## What I tried

- Generalised `scene_transfer.retake_cut_in` → `retake_scene(scene)`: the loop
  was hard-wired to `CUT_IN_SCENE`, so a second column would have meant a
  hand-copied body. Every recorded column now comes from one function.
- Measured `cafe_head_on_v0` at full ensemble width (8 arms × 8 seeds) through
  that function. Chose it over `convoy` / `obstacle_crossing` because head-on is
  the geometry where yield-vs-freeze is sharpest — the axis the bottleneck asks
  about.
- Replaced the `_ensemble` `if` ladder with a `_COLUMNS` dict pinned equal to
  `MEASURED_SCENES` in both directions, so a scene can no longer be listed as
  measured but never dispatched.

## What worked / what failed

- **D-330's headline is falsified.** `cbf_mppi` wins `head_on` **8/8
  (+0.1781 m)** on top of its `freezing` **8/8 (+0.2282 m)**. The winner sets
  are *not* pairwise disjoint — one arm travels between two scenes. "No arm
  wins two scenes at once" was a statement about having measured exactly two.
- **`arms_that_generalise()` is still `()`** — `cbf_mppi` is blocked by exactly
  one scene, `cut_in` (2/8, −0.0213). The north-star clause is still unmet, but
  the failure mode changed shape: from "no arm travels" to "one arm travels and
  one scene blocks it".
- **`head_on` is a low-clearance scene for everything except `cbf_mppi`.**
  Baseline sits at 0.0009–0.0125 m; five arms beat it by margins of 0.001–0.02 m
  at 5–7/8. Those are wins by the letter of `wins` but they are two orders of
  magnitude smaller than `cbf_mppi`'s, and `social_mppi`'s 7/8 misses stability.
- **My own cost projection missed by 38 %** — 193.1 s measured against 267.3 s
  projected. Pinned, because it narrows D-330's explanation rather than
  repeating it (below).
- `geometric_mppi` stayed bit-identical to baseline on the third scene too, and
  `risk`/`frozen_risk` agreed on all 8 new seeds — 24/24 pairs now.

## North-star delta

- Coverage **2/5 → 3/5** hostable scenes at ensemble width.
- The "all environments" clause now has a **named obstruction** rather than a
  symmetric negative: `cbf_mppi` fails it only on `cut_in`. That is a
  strictly better-posed question than the one this cycle started with.
- No planner change; the arm that travels is the classical one (`cbf_mppi`),
  not a representation channel. Honest reading: the representation arms are
  still not the thing that generalises.

## Key learnings

- **A negative result over two members is a claim about the sample size.**
  D-330 measured disjointness and read it as a property of the arms; a third
  column moved it. The pinned test now asserts the *shared* arm by name, so the
  claim cannot be quietly weakened back to an always-satisfiable emptiness.
- **The accurate-estimate explanation was too broad.** D-330 credited "extrapolated
  from a measured column, not guessed". This cycle extrapolated from that same
  measured column across a *scene* boundary and ran 38 % long. The correction:
  the accuracy was **within-scene**, because scenes differ in episode length.
- **An unmeasured-scene negative case expires when that scene is measured.**
  `test_measured_scenes_have_columns_and_others_refuse` used `cafe_head_on_v0`
  as its `KeyError` case — exactly what this cycle measured. It now names an
  unmeasured scene and a second test pins that it is still both hostable and
  uncolumned, so the refusal cannot go vacuous unnoticed.

## Recommended next 1–3 priorities

1. **Ask what `cafe_cut_in_v0` does to `cbf_mppi`** — one arm, one blocking
   scene, both signs measured at full width. The best-posed the transfer
   question has been.
2. **Fill `cafe_convoy_v0` + `cafe_obstacle_crossing_v0`** (~6.5 min at the
   *measured* 193 s rate, not the projected one) — 3/5 → 5/5 closes coverage.
3. **Grade the `head_on` micro-wins for magnitude** — five arms clear the
   baseline by ~0.001–0.02 m. `wins` is sign-based; a scene this tight may need
   a magnitude floor or those rows are noise wearing a verdict.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/scene_transfer.py, eval/mppi_sandbox/tests/test_scene_transfer.py, eval/mppi_sandbox/tests/test_consumer_reach.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
