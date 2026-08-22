# Registering `scene_transfer` empties the unmeasured set — no scene was ever walked

- **Cycle**: 2026-08-22 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE-derived `register-scene-transfer` (D-417's demanded follow-up)
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Wrote `recorded_clearance._from_scene_transfer`, the fourth reader, and
  registered it in `SOURCES`. D-417 found 15 ensemble-bearing modules the
  registry had never heard of and explicitly called registration "the follow-up
  this census *requires*, not a substitute for it"; nobody had written it.
- Added `scene_transfer.columns()` as the public read of `_COLUMNS`, and
  registered *that* rather than the constant.
- Repaired the 11 pins the registration moved, across three test modules.

## What worked / what failed

- **Coverage went `2/3 → 3/3 FULLY_MEASURED`.** `cafe_obstacle_crossing_v0` —
  the scene STATE has called "the only eligible scene genuinely unmeasured" for
  four cycles — carries an **8 arms × 8 seeds** column that has been sitting in
  `scene_transfer` the whole time. **`unmeasured` is now empty, and not one
  rollout was run to empty it.** Second refunded measurement in three cycles.
- **Registering `_COLUMNS` directly would have turned `vocabulary_gap()` red**,
  and that is the guard working. `source_reach` requires every constant-backed
  registered source to carry a `VOCABULARY` token; `_COLUMNS` carries none, so
  the registry would have fallen outside the vocabulary that audits it. Going
  through `columns()` puts the reader in `published_census()`'s `UNSCANNED`
  class — the honest label for an aggregator over five named constants.
- **A free catch before the suite**: my first draft spelled the scene into
  `source` (`scene_transfer._COLUMNS['cafe_...']`), which would have made one
  reader look like five and failed `len({e.source}) == len(SOURCES)`. Caught by
  reading the pin, not by running it.
- **The suite was not bought and this cycle is stranded.** `elapsed` said
  `SUITE_AFFORDABLE` with a 6m39 deadline; the 11-pin repair ran to ~26 min.
  Three attempts to run the coupled modules each hit the timeout — those are
  the sim-heavy ones, which is precisely STATE #2's complaint.

## North-star delta

- **Zero rollouts, no controller moved — 38th consecutive cycle.** Honest
  reading: this is verification-surface work again.
- What it *does* buy is the retirement of a false bottleneck. Three cycles were
  scoped off "go measure the unmeasured scene". There is no such scene, and now
  no test says there is.

## Key learnings

- **The same coverage set has now been wrong three times in three cycles**
  (D-413 literal → D-416 missing reader → D-417/this missing *module*), and
  every fix has been "widen the registry". The pattern is not that the registry
  keeps being unlucky; it is that **a census over readers can only ever be as
  wide as its reader list**, and nothing grades that list except `source_reach`,
  which still reports `UNREGISTERED` on ~14 more modules.
- **Registering a source is not free — it moved 11 pins.** Most encoded the
  *old* finding as fact ("the registry is currently short", "only the capped
  scene is measured"). A test that only records a bug leaves nothing watching
  the fix, so they were re-aimed at the new reading rather than deleted.
- `test_none_and_fully_measured_are_distinct_from_partial` had already been
  silently re-pointed once (convoy → crossing) and was about to lose its
  meaning a second time. It now uses a **synthetic** scene name: there is no
  real unwalked eligible scene left to borrow.
- **D-419's rule held and I followed it.** `census_preempt` read `CLEAN 5/5`
  with a non-empty `UNCOVERED`, so the "I verified it, therefore it is
  complete" bet was not available — and with no strand outstanding, D-112 gave
  no reason to override D-181. Cut scope instead of buying a suite at minute 26.

## Recommended next 1–3 priorities

1. **`buy-one-suite-and-push`** — 1 commit stranded, no diagnosis left. The
   three repaired modules are green (43 tests); what is unverified is the
   sim-heavy coupled set (`test_seed_debt`, `test_key_discrimination`,
   `test_guard_reflexivity`, `test_three_arm`).
2. **`split-suite-or-split-cycle`** (STATE #2) — this cycle is the third in a
   row where a ~25 min suite against a 35 min budget is the binding constraint.
   It is now the top structural blocker, ahead of any P3 substance.
3. **`register-remaining-ensemble-modules`** — `source_reach` still convicts
   ~14 modules. Do them as one batch, not one per cycle.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/recorded_clearance.py, eval/mppi_sandbox/scene_transfer.py, eval/mppi_sandbox/tests/test_recorded_clearance.py, eval/mppi_sandbox/tests/test_source_reach.py, eval/mppi_sandbox/tests/test_scene_eligibility.py
- TSV row appended: yes
