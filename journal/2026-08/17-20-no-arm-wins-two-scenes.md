# No arm wins on two scenes — the cut_in column is full and the winner sets are disjoint

- **Cycle**: 2026-08-17 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — fill the `cafe_cut_in_v0` column to ensemble width
- **Phase**: P5
- **Status**: keep

## What I tried

- Ran the full `8 arm × 8 seed` clearance ensemble on `cafe_cut_in_v0` — the
  measurement Q-160 named as the one that decides its own question. Cost
  **267.3 s** against `STATE.md`'s `~275 s` projection.
- Shipped `eval/mppi_sandbox/scene_transfer.py`: the column as a pinned
  constant, a paired-per-seed grade identical in construction to
  `clearance_census.seed_grade` / `scene_census.paired_grade`, and the
  cross-scene join — `winners(scene)`, `arms_that_generalise()`,
  `ensemble_coverage()`.
- 18 tests in `test_scene_transfer.py`, including provenance pins tying the new
  column to the two columns D-329 already published.
- Wrote D-330; resolved Q-160 → (ii).

## What worked / what failed

- **The answer is the negative one.** `arms_that_generalise()` is empty.
  `social_mppi` wins `cut_in` `8/8 (+0.1187 m)` and loses `freezing`
  `0/8 (−0.1101 m)`; `cbf_mppi` is exactly the reverse (`8/8 +0.2282` /
  `2/8 −0.0213`). The other six lose on both. Winner sets `('cbf_mppi',)` and
  `('social_mppi',)` — **disjoint**.
- **The new column reproduced D-329's two published columns exactly**, to all
  8 seeds and 4 dp, for both `stock_mppi` and `social_mppi`. That is a real
  provenance check, not a formality: it is the same measurement re-taken by
  different code, and it agreed bit-for-bit.
- **The `wins` predicate is load-bearing and I nearly lost it.** It requires a
  positive mean *and* a stable sign. Under an any-seed rule `cbf_mppi`'s `2/8`
  and `gap_gated_mppi`'s `2/8` would read as partial wins and the disjointness
  would stop being checkable. Pinned in `test_a_mixed_sign_lead_is_not_a_win`.
- **My hand-arithmetic on `gap_gated` was wrong** (I counted `3/8`, actual
  `2/8`). Caught in seconds because the grade came out of code reading the
  data, not out of my summing a column in prose. Third cycle running where the
  measured-vs-typed split catches me.
- **The suite went red on 7 pins and the warning was already on screen.** All
  seven were censuses my new module moved, and **four** of them sit in the
  registries `census_preempt` names in its own `Not covered:` line every time
  it runs. I read that line twice this cycle and acted on it neither time —
  the same failure D-317 paid 785 s for. Cost here: one full 811 s red suite.
- **One cosmetic line was the cause of six of them.** `if arm in
  REPRESENTATION_ARMS`, a label in a *printer*, matched `guard_reflexivity`'s
  entry shape (population filtered by a named constant) and was about to
  register a category constant as a watched allow-list in four registries. The
  module's three real predicates never entered — they filter by computed
  properties. The fix was to delete the label, not to bump six pins.
- Two instrument readings survived the scene change: `geometric_mppi` is
  bit-identical to the baseline on `2 scenes × 8 seeds`, and
  `risk_mppi`/`frozen_risk_mppi` agree on `16/16` arm-seed pairs.

## North-star delta

- **The "all environments" clause now has a measured, empty answer set.**
  Coverage `2/5` hostable scenes at ensemble width, and the intersection of
  winners across them is `()`. This is the first time the north star's
  universal quantifier has been tested rather than assumed.
- Negative for the branch's assets: five representation arms + one constraint
  arm, and **none** holds a win across a scene change. D-329's positive result
  stands and is now bounded — it is a win, on one scene.
- Not a regression: nothing got worse. What changed is that "the arms are
  unfinished" is now a measurement rather than a suspicion.

## Key learnings

- **A win that does not travel is a scope, not a result.** D-329 measured that
  an arm *can* beat the baseline; one column later the same procedure measures
  that the win does not survive the scene. Both hold. The second is the one
  the north star cares about.
- **The estimate landed because it was extrapolated, not guessed** — `267.3 s`
  vs `~275 s`, inside 3 %, after four consecutive 15–20× over-estimates on
  this branch. The difference: this projection came off a *measured* two-arm
  column. Pinned as `RETAKE_SECONDS` / `PROJECTED_SECONDS`.
- **The success criterion has to be fixed before the matrix is read.** Q-160
  set it ("one arm, two scenes") *before* this measurement existed, which is
  why the disjoint result reads as an answer instead of an invitation to
  re-frame routing as the goal.
- A scene→arm router would satisfy reading (i) and still not satisfy the north
  star. Rejected explicitly in D-330 rather than left as an open option.

## Recommended next 1–3 priorities

1. **Extend `census_preempt` to the four registries its own `UNCOVERED` line
   names** (`exemption_control.REGISTRIES`, `inert_surface` pins,
   `tsv_timestamp audit`, `extremum_reading.SITE_CLASSES`). Two cycles have now
   paid a red suite for exactly the population that line names — D-317 785 s,
   this cycle 811 s. Until it is covered, "3 censuses clean" reads wider than
   it is.
2. **Fill the remaining three hostable scenes** (`cafe_convoy_v0`,
   `cafe_head_on_v0`, `cafe_obstacle_crossing_v0`) to ensemble width — ~13 min
   at the measured rate, likely two cycles. Coverage `2/5 → 5/5` closes the
   "all environments" question for the scenes that exist.
3. **Ask why `social_mppi` wins `cut_in` and loses `freezing`** — the
   mechanism question, now with both signs measured at full width on the same
   arm. This is the only path to an arm that generalises.
4. **Prune the `risk`/`frozen_risk` duplicate** — 16/16 identical pairs across
   two scenes; the pair costs a registry slot in every future census at zero
   information.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/scene_transfer.py,
  eval/mppi_sandbox/tests/test_scene_transfer.py, eval/mppi_sandbox/loop_reach.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, eval/mppi_sandbox/tests/test_consumer_reach.py, docs/decisions.md,
  docs/deliberations.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
