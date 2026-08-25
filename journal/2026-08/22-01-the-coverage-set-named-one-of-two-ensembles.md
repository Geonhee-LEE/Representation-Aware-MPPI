# The coverage set named one of two ensembles

- **Cycle**: 2026-08-22 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `scene-elig` Derive `RECORDED_SCENES` instead of typing it
- **Phase**: P3
- **Status**: keep

## What I tried

- PLAN's candidate was STATE's #1, `convoy-meas` — go record per-seed clearance
  on `cafe_convoy_v0`, one of the two "eligible and unmeasured" scenes that are
  the whole of the current bottleneck. Before buying rollouts I asked where the
  word *unmeasured* comes from, and it comes from
  `scene_eligibility.RECORDED_SCENES` — a **one-element typed literal**.
- Derived the same set from source instead: `eval/mppi_sandbox/recorded_clearance.py`
  walks the modules that actually own per-seed clearance ensembles and reports
  what they say they are pinned to.
- Wired `RECORDED_SCENES` to the derivation, updated the pin test, added
  `test_recorded_clearance.py` (11 tests) and two tests in
  `test_scene_eligibility.py` that reproduce the shipped drift.

## What worked / what failed

- The literal was **wrong, and had been for its whole life**. The tree holds two
  per-seed clearance ensembles, not one: `separation_reproduction` (32 seeds,
  2 arms, `cafe_head_on_v0`) and `clearance_census.SEED_ENSEMBLE` (**8 seeds ×
  8 arms, `cafe_freezing_v0`**). The literal named only the first.
- Its comment cited D-047 and imported `PUBLISHED_SCENARIO` rather than spelling
  it — so the **spelling** could not drift. The **membership** was never guarded,
  and membership is the half that moved. D-047 one level up.
- The bug is currently **inert**, and that is the hazard rather than the
  reassurance: `measured` is `eligible and scenario in RECORDED_SCENES`, and
  `cafe_freezing_v0` is excluded under `NO_DECLARED_MARGIN`. Every printed count
  is right *by accident*. `scene_eligibility` prints byte-identical output before
  and after this change.
- The masking is not stable. STATE's own actionable **#3 `freeze-margin`** — a
  one-line yaml edit declaring `min_distance_to_obstacle` on `cafe_freezing_v0`
  — flips that scene eligible, and the very next census would call it
  **unmeasured** with an 8×8 ensemble already on disk. Two of STATE's three
  claude-actionables were on a collision course with each other.
- Derivation cost: **0.077 s**. No simulation; every input is already a constant.

## North-star delta

- **No metric moved** — `3/8 eligible, 1/3 measured` is unchanged, deliberately.
- What moved is the *trustworthiness of the denominator*: the coverage count is
  now read off the ensembles rather than off a sentence, so the bottleneck's
  "2 unmeasured eligible scenes" is a derived claim for the first time.
- One future cycle of wasted rollouts on `cafe_freezing_v0` avoided, conditional
  on `freeze-margin` landing.

## Key learnings

- **D-047 has a second half nobody had read.** Importing a name stops *spelling*
  drift; it does nothing about *membership* drift. `frozenset({IMPORTED_NAME})`
  looks derived and is typed. Every hand-typed set in this package with an
  imported member is suspect on the same grounds.
- **An inert bug in a census is worse than a live one**, because nothing goes red
  and the reading looks confirmed. D-107's empty-population lesson, applied to a
  set that is non-empty but short.
- **Screen the bottleneck's own vocabulary before spending on it.** D-412 checked
  STATE's bottleneck against the census; this cycle checked the census against
  the tree. Same move, one layer down, same result — the expensive plan was
  aimed at a word rather than a measurement.

## Recommended next 1–3 priorities

1. `freeze-margin` is now **cheaper and safer** — the census will read it
   correctly the moment it lands. Do it next.
2. Audit the other hand-typed sets in the package for the same shape
   (`frozenset({...})` / tuple literals whose members are imported names).
3. `convoy-meas` / `crossing-meas` stand: both are genuinely unmeasured under the
   derived set too.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/recorded_clearance.py`, `eval/mppi_sandbox/scene_eligibility.py`, `eval/mppi_sandbox/tests/test_recorded_clearance.py`, `eval/mppi_sandbox/tests/test_scene_eligibility.py`
- TSV row appended: yes
