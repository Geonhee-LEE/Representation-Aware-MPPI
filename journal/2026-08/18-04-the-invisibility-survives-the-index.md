# The invisibility survives the index — and gets worse

- **Cycle**: 2026-08-18 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-take the separability table at an early, causally-available index
- **Phase**: P3
- **Status**: keep

## What I tried

- Parametrised `scene_separability`'s five operators (`separates`,
  `separating_observables`, `is_constant`, `informative_separators`) on an
  optional `table`, so the identical rule can be applied to a different reading
  without a second copy of the analysis.
- Added two **causally available** index policies — `first_detection` (first
  index inside a 2.0 m clearance horizon) and `fixed_time` (nearest 1.0 s) —
  plus `_observables_at`, which differs from the hindsight reader in two ways
  that matter: the critical obstacle is the nearest one **at** the read index,
  and the derivatives are **backward** differences (`np.gradient` is centred and
  would read `k+1`).
- Re-took all 40 baseline rollouts once, emitting all three policies from the
  same trajectories (**77.5 s**), so policy-to-policy differences are differences
  of index and not of measurement.
- 11 new tests; `min_ttc` deliberately has no causal counterpart (an episode
  minimum is hindsight by construction) and is replaced by `ttc`.

## What worked / what failed

- **The negative survives.** `policies_that_separate_question_scene() == ()` —
  `cut_in` has no informative separator at either causal index. This was the one
  objection that could have overturned D-334, and it did not.
- **It survives *harder* than D-334's.** At the causal indices `cut_in`'s row is
  empty **before** the constant filter runs, so the causal negative does not
  depend on the zero-spread control at all. Cause: at the critical instant the
  nearest obstacle is a *static* one (`obstacle_speed = 0.0`, unique among five
  scenes); at first detection it is the moving one (`0.75`), which
  `cafe_obstacle_crossing_v0` also carries. D-334's separator was a parameter of
  an obstacle the switch would not have been looking at.
- **The policy control fired red and stays red.** `causal_policies_agree()` is
  **False** — the indices disagree about `freezing` (`ttc` separates at 1 s,
  nothing at first detection) and `head_on` (one separator vs two). So the table
  is index-dependent in general; only `cut_in`'s row is index-invariant. Pinned
  as two separate predicates so the narrow claim cannot be read as the broad one.
- **Free self-check landed**: the re-take's `critical` sub-table reproduced the
  pinned `OBSERVED` exactly, which is what licenses calling the refactor a
  widening rather than a re-measurement.
- ⭐ `census_preempt` caught **both** obligations at the stage (~2 s): 2
  unrecorded `loop_reach` rows and a `consumer_reach` UNREACHED on
  `causal_separation_table`. Pre-paying `extremum_reading.SITE_CLASSES` by hand
  — the `is_constant` keys re-spell to `tbl[...]` under the refactor — avoided a
  third. This is the axis that cost the last two cycles 67 m and 87 m.

## North-star delta

- **Negative, and it closes a door rather than opening one.** The "미관측 분포"
  clause is no closer: D-333's 5/5 coverage still presupposes an oracle, and this
  cycle removes the last cheap hope that a better *read index* would supply the
  switch. The remaining question is about the observable set itself.
- No change to any controller, cost, or measured clearance number.

## Key learnings

- **"Read it earlier" was the cheap objection, and it was answerable for free** —
  the same 40 rollouts carry every index, so the marginal cost of two more
  policies was ~1 s of post-processing on a 77.5 s measurement. Any future
  index-scoped caveat on this branch should be discharged the same way rather
  than deferred.
- **A hindsight index does not just move *when* you read — it moves *what* you
  read.** The obstacle-selection argmin was the larger of the two hindsight
  leaks, and it is the one that made D-334's constant look scene-unique.
- **Keep a control red when it is red.** The whole-table policy control fails,
  and narrowing it to `cut_in`'s row would have made it pass and erased the
  scope of every other row in the module.

## Recommended next 1–3 priorities

1. **Question the observable set, not the index.** The five were chosen before
   any of this was measured; the honest next move is to ask what a `cut_in`-
   specific channel would even look like (obstacle *lateral* velocity relative to
   the path, not speed) and whether it is constant-free.
2. **Prune the `risk`/`frozen_risk` duplicate** — 40/40 identical arm-seed pairs;
   the evidence is maximal and cannot improve.
3. **Merge pressure**: 6 open PRs, 37 days since the last merge.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/test_scene_separability.py, eval/mppi_sandbox/loop_reach.py, eval/mppi_sandbox/extremum_reading.py, docs/decisions.md
- TSV row appended: yes
