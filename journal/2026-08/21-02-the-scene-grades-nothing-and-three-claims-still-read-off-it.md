# The scene grades nothing, and three claims still read off it

- **Cycle**: 2026-08-21 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c2c5d39` city_curved_v0 을 구조적으로 ungradeable 로 기록하고 거기 걸린 claim 감사
- **Phase**: P3
- **Status**: keep

## What I tried

- Turned D-392's per-cell readings into a **scene-level** pin.
  `ungradeable_scenes()` derives from `full_screen()` — `screen()`'s two
  columns plus the TVaR ensembles and `cte_max` at the operating point, which
  `screen()` never saw — and returns a scene only when *every* held column is
  degenerate.
- Wrote the audit half as `scene_scoped_claims()`: read this module's own
  source, resolve the scene's aliases through the symbols its ensembles are
  pinned under, classify each claim `RETIRED` vs `LOAD_BEARING`.
- Cleared the strand from 01:00 (2 commits that never reached origin).

## What worked / what failed

- **The scene-level statement did not exist and three cell-level ones did.**
  `second_verdict` says it of the TVaR column, `aligned_second_verdict` of
  `cte_max` at the operating point, `degenerate_tally_rows` of the tally row.
  None of the three forbids buying a *fourth* cell on this scene, which is
  exactly what 01:00 did for 57.3 s. `ungradeable_scenes()` is the first thing
  that does, and it costs 0 rollouts.
- **The audit found 3 of 5 scoped claims still returning a statistic over a
  population of two** — `second_ratio`, `second_baseline_ratio`,
  `aligned_second_is_gradeable`. `report()` prints the first two beside
  `cafe_convoy_v0`'s and `cafe_head_on_v0`'s numbers with nothing marking the
  difference. That is the concrete residue the TODO was written to surface.
- **Two detector bugs, both of which fail silently toward "clean".** First
  pass missed `second_ratio` entirely (it names `TVAR_ENSEMBLE_SECOND`, never
  `SECOND_SCENE`) and scored `full_screen`/`format_census`/`drift` as scoped.
  Fixing aliases-by-identity plus "drop anything naming another scene" then
  returned **`{}`** — because `SCENE` is a substring of `SECOND_SCENE` and
  `TVAR_ENSEMBLE` of `TVAR_ENSEMBLE_SECOND`, so every `second_*` claim scored
  as an enumerator. An empty audit reads exactly like a clean one; the test now
  asserts non-emptiness and names the four enumerators that must stay out.
- `census_preempt` was clean this cycle (134/134) — first time in seven. The
  entrants are derived helpers, not typed censuses, so there was no tally to
  move.

## North-star delta

- **Zero planner movement, 25 cycles.** No controller, scenario or cost term
  changed.
- Not a subtraction, for the first time in six cycles — but not a result
  either. What was added is a **stop**: a derived pin that makes the next
  cycle's "buy a cell on `city_curved_v0`" impossible to write by accident.
- The `1/3 → 1/2` denominator move from 01:00 is now reachable from the scene
  side as well as the row side.

## Key learnings

- Three correct statements about three cells do not add up to the statement
  about the scene, and the missing one is the only one with **prohibitive**
  force. Per-cell verdicts describe; a scene-level pin forbids.
- A census that filters can fail toward empty, and empty is indistinguishable
  from clean at a glance. Both of this cycle's bugs pointed that way. Any
  filtering census needs a non-emptiness assertion before it needs anything
  else.
- Symbol-name substring containment is a live hazard in this module
  specifically — `SCENE`/`SECOND_SCENE`/`THIRD_SCENE`, `TVAR_ENSEMBLE`/
  `_SECOND`/`_THIRD` are all prefixes of one another. Whole-symbol matching,
  not `in`.

## Recommended next 1–3 priorities

1. **Mark the 3 load-bearing claims at their print site** — `report()` prints
   `second_ratio` and `second_baseline_ratio` unmarked next to gradeable
   scenes. 0 rollouts; the audit already names them.
2. **Run `ungradeable_scenes()` against the 6 unharvested scenarios** before
   any of them is bought — the predicate is scene-general and the screen is
   free wherever a pin exists.
3. **Branch-scope decision (user)** — 25 cycles, zero planner change.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tail_mean.py, eval/mppi_sandbox/tests/test_tail_mean.py, docs/decisions.md
- TSV row appended: yes
