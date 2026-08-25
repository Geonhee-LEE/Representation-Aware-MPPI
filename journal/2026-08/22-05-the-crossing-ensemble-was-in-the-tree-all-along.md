# The crossing ensemble was in the tree all along

- **Cycle**: 2026-08-22 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c3c5d39` [sandbox] source-reach — `recorded_clearance.SOURCES` 를 tree 에서 유도한 ensemble 보유 module 과 대조
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Built `eval/mppi_sandbox/source_reach.py`: an **AST-only** scan of the package
  (no import, no execution) for module-level `UPPER_CASE` constants whose leaves
  hold float rows of width ≥ `recorded_clearance.MIN_SEEDS`, narrowed by a name
  vocabulary, graded against `recorded_clearance.SOURCES`.
- Graded only the under-reporting direction. `UNREGISTERED` (a site in a module
  **no** reader touches) convicts; `UNNAMED` (module registered, constant not
  named) and `UNSCANNED` (registered but function-assembled) are reported.
- Repaired the two census pins the addition moved, caught by `census_preempt`
  **before** the suite: guard pool 136 → 138, and `VOCABULARY` onto
  `unwatched_exemptions`.
- 19 tests in `tests/test_source_reach.py`; zero rollouts, every input already a
  constant in the tree.

## What worked / what failed

- **The registry is short by 15 modules, not by one.** `SOURCES` registers 3
  readers; the scan finds 23 vocabulary-matching ensemble sites, of which 21 are
  unaccounted and 15 sit in modules the registry has never heard of —
  `scene_transfer`, `scene_transplant`, `geometric_null`, `structural_null`,
  `tail_mean`, `excursion_seed_width`, `calibrated_ladder`, `floor_reach`.
- **The headline invalidates STATE's bottleneck for the third time.**
  `scene_transfer.OBSTACLE_CROSSING_ENSEMBLE` is **8 arms × 8 seeds** pinned to
  `OBSTACLE_CROSSING_SCENE = "cafe_obstacle_crossing_v0"` — the scene STATE
  calls "the only eligible scene genuinely unmeasured". `scene_transfer` also
  holds cut-in, head-on and convoy ensembles, i.e. a scene→ensemble map of four.
  STATE #2 `crossing-meas` is refunded before it was ever picked, which is the
  outcome the TODO body predicted in as many words.
- **`census_preempt` earned its 2 s.** It returned `DRIFT` on two of five
  censuses. Both would have been a red suite ~20 min later; this is D-312/D-313
  for the seventeenth time — the census of the census became a member of the
  census it audits.
- **What failed: I did not buy the suite.** `cycle_wallclock elapsed` read
  `SUITE_AFFORDABLE` with 0m38 of runway at 7m30, and by the time the two pin
  repairs were derived and verified it read `SUITE_UNAFFORDABLE` at 18m59. Per
  D-181 I cut scope rather than start a 22-min suite that ends 7 min past
  budget. The commit is therefore **stranded by design**, not by accident.
- `inert_surface staged` returned `STAGED_MOVED` — this cycle withdrew the
  exemptions on all five local-only pins (`STATE.md`, `JOURNAL.md`,
  `RESULTS.md`, `journal/`, `results/`). Next cycle pays D-044's tax on them
  unless it re-probes.

## North-star delta

- **No controller moved; zero rollouts.** The movement is that one of the two
  remaining "unmeasured eligible scene" claims is false, so 물체회피 coverage on
  the eligible set is better than the census says — again.
- A measurement that STATE ranked #2 and would have cost a rollout budget is
  refunded. That is the second refund in three cycles from the same defect.

## Key learnings

- **Deriving a set from readers does not make it derived from the tree.** D-413
  converted a literal to a derivation and the derivation was wrong one cycle
  later; this cycle's reading is the first taken from a source *neither side of
  `drift()` controls*. Comparing two sets finds disagreement, never a shared gap
  — breaking that needs a third reading, not a better second one.
- **The narrowing is where this instrument can go quietly wrong.** The bare
  structural test matches **82** constants; the vocabulary cuts it to 23. That
  filter is typed, so `vocabulary_gap()` grades it against the registry and
  `uncovered()` prints the 59 it dropped. Without both, this module would read
  clean for the same reason `drift()` did.
- **A guard's own `&` makes it a guard.** `vocabulary_gap` uses `set(...) &
  VOCABULARY` and entered `guard_reflexivity.guards()` on that operator alone —
  the D-116 shape again, one level up.
- The `cycle_wallclock elapsed` reading is only useful if taken **repeatedly**.
  I took it at 7m30 (affordable, 38 s of runway) and next at 18m59
  (unaffordable). The two pin repairs consumed the window and nothing told me
  while it was happening.

## Recommended next 1–3 priorities

1. **Clear the strand**: one suite, then push `76b4fee`. Phase 1 Step 0 will
   name it. Consider `push_preflight probe` first — `0559b8e9`'s green receipt
   does not cover this tree.
2. **Register `scene_transfer` as a reader** in `recorded_clearance.SOURCES`
   (four scenes, 8×8 each) and re-take the coverage count. This is the fix the
   census was built to demand, and it retires `crossing-meas` outright.
3. **Re-aim STATE's bottleneck** off `cafe_obstacle_crossing_v0` once (2) lands
   — and this time derive the sentence from `source_reach`, not from a set that
   has been wrong three times.

## Artifacts

- PR: #67 (open) — commit not yet pushed, suite unbought (D-181)
- Files touched: `eval/mppi_sandbox/source_reach.py`, `eval/mppi_sandbox/tests/test_source_reach.py`, `eval/mppi_sandbox/tests/test_guard_reflexivity.py`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
