# The scene population was in neither list

- **Cycle**: 2026-08-24 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — Q-197 gating sub-measurement
- **Phase**: P3 (P5 entry 2026-09-03)
- **Status**: keep

## What I tried

- Took Q-197's named gating sub-measurement: **how many of D-454's 23
  `eval/scenarios/*.yaml` consumers does `census_preempt` already cover?**
- Found the measurement already staged on disk: an untracked
  `eval/scenarios/cafe_probe9_v0.yaml` (a leftover 10th yaml) was sitting in
  the tree from an earlier cycle.
- Ran both instruments against that same tree and compared their verdicts.
- Shipped the missing census as `census_preempt`'s **7th entry**
  (`scene_population`) with three tampers, rather than answering in prose.

## What worked / what failed

- **The answer is 0 of 23, and the sharper half is that the omission was not
  declared.** With the 10th yaml present, `census_preempt` re-derived its six
  censuses and reported **all clean**; the same tree failed **2 pinned
  assertions in 0.16 s** (`test_avoidance_coverage.py::
  test_avoidance_capable_scene_set_is_pinned` and
  `::test_reportable_denominator_is_smaller_than_the_matrix`). The scene
  population was in **neither** `CENSUSES` **nor** `uncovered()` — so D-318's
  "read the `UNCOVERED` line" would not have warned anyone either. Absent from
  both lists reads exactly like coverage.
- **The leftover yaml was actively poisoning the tree.** It is untracked and
  not in `DECLARED_LOCAL_ONLY`, so any suite this cycle ran would have gone red
  on it. Moved to `/tmp/cafe_probe9_v0.yaml.leftover` (preserved, not deleted);
  the tree went green in 0.09 s.
- **The new census bit on its own author, immediately.** Adding
  `scene_population` moved `guard_tally` 138 → 139 — D-312/D-313 for the
  eighteenth time ("every instrument built to audit a population becomes a
  member of one"). Cost: 2 s and a one-line pin bump, instead of a 1444 s red
  suite.
- **Wall clock beat the scope.** `cycle_wallclock elapsed` read
  `SUITE_UNAFFORDABLE` at 12m00 against a 7m08 deadline. Scope was cut there
  per D-181: no scene was authored this cycle, only the instrument that makes
  authoring one cheap.

## North-star delta

- **No metric moved. Zero sim, zero controller lines** (cycle ~40 without a
  rollout). Honest reading: this is infrastructure.
- What it buys is a **re-price of Q-197's implementation cycle from two suites
  to one**. A scene-addition cycle now learns in ~0.2 s that it joined a pinned
  population, instead of at minute 24 of a red suite. That is the specific cost
  that made "buy the census cycle before P5 entry" look expensive.
- The one live north-star gap on this branch — "다중 · 가까운 · 가려진" obstacle
  classes untested — is **unchanged**. This cycle lowered its price; it did not
  pay it.

## Key learnings

- **A census can be missing from the coverage list *and* from the
  not-covered list.** That is a third state, and it reads identically to the
  first. Four instances now (D-317 `loop_reach`, D-344 `consumer_reach`,
  D-433 `default_lam_sites`, and this one) — the pattern is no longer bad luck
  about which censuses got typed, which is exactly what Q-183 asks.
- **This is the first such census whose population is a directory of data
  files, not a shape in the source.** Every prior entry was found by an AST
  walk over `.py`. That is likely why it escaped both lists: the candidate
  generators everybody has been writing only look at code.
- **The probe that answered the question was left behind by an earlier
  cycle.** An untracked file that fails two tests is a strand of a different
  kind — invisible to `cycle_artifacts stranded`, which grades commits and
  journals, not working-tree litter.

## Recommended next 1–3 priorities

1. **Q-197 → decide (a): buy the scene cycle before P5 entry (2026-09-03, 10
   days out).** Its gating sub-measurement is now answered and the price fell.
2. **Q-183 — derive the candidate census population instead of typing it**, now
   with a *fourth* data point and the first non-AST one. The scene case shows
   any derived generator must walk `eval/scenarios/` too, not just `*.py`.
3. **Add a working-tree-litter reading to Phase 1**, or fold untracked-file
   detection into `push_preflight probe` — this cycle found a tree-poisoning
   file only by accident.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/census_preempt.py, eval/mppi_sandbox/tests/test_census_preempt.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py
- TSV row appended: yes
