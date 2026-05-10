# Mirror include_run_metrics flag onto the outdoor launch

- **Cycle**: 2026-05-07 09:00 KST
- **Branch**: `autoresearch/p1-outdoor-launch-include-run-metrics`
- **TODO**: `<new-cycle-5>` [north-star] Apply include_run_metrics flag to jackal_outdoor_sim.launch.py
- **Phase**: P1
- **Status**: keep

## What I tried
- Mirrored cycle 4's cafe-launch wiring onto `jackal_outdoor_sim.launch.py`: imported `ExecuteProcess`, added 5 launch args (`include_run_metrics`, `run_id`, `target_speed`, `run_metrics_output_dir`, `run_metrics_pythonpath`), and a default-off `ExecuteProcess` spawning `python3 -m eval.run_metrics`.
- Added `eval/tests/test_launch_outdoor_include_run_metrics.py` (sibling to the cafe test that's still in-flight on PR #7) — 6 contract tests on the outdoor LD.
- Bookkeeping: opened **PR #7** for the prior cycle's cafe-launch branch (it had been pushed but not turned into a PR).

## What worked / what failed
- colcon build clean; `pytest eval/` → 32 pass (6 outdoor + 26 prior).
- First refactor attempt put both cafe + outdoor tests in a single shared-base file. **Failed**: cafe launch on main lacks the new args (PR #7 unmerged), so the cafe assertions failed with `'run_id' not found`. Caught by smoke test, not in production.
- Pivoted to a sibling test file → both PRs (cafe = #7, outdoor = #8) now conflict-free regardless of merge order.

## North-star delta
- **+ outdoor scenarios unblocked** for first quantitative numbers. After PR #7 + #8 both merge, `city_curved_v0`, `city_figure8_v0`, and the cafe-via-outdoor variant from `eval/scenarios/*.yaml` all use the same single-command JSON-capture recipe.
- Still 0 measured numbers in the repo — that gates on the user's first `ros2 launch`.

## Key learnings
- **Co-evolving same-file PRs need separate test paths.** When two unmerged branches both touch the same module's tests, even a "clean refactor to share a base class" creates a conflict gradient. Sibling files with intentional duplication are cheaper than a merge dance.
- **Always sanity-check what's actually on `main` vs what's on the in-flight branch.** The cafe test file existed in my mental model only because I'd just read it on the cafe branch — checking it out on a fresh `main`-based branch surfaced the truth.
- The previous cycle's executor pushed the cafe branch but didn't open the PR. Worth tightening the EXECUTE phase spec to make `gh pr create` explicit (currently "push the branch (never `main`)" is the last verb).

## Recommended next 1–3 priorities
1. **(user)** Merge PR #7 (cafe-launch flag) → run `cafe_straight_v0` with `include_run_metrics:=true` → first `runs/cafe-001.json`. Same as STATE's prior #1.
2. **(user)** Merge PR #8 (this PR, outdoor-launch flag) → unlock outdoor scenarios.
3. **(claude)** Add `gh pr create` step explicit to `scripts/prompts/auto_research.md` EXECUTE phase, so future cycles never push-without-PR.

## Artifacts
- PR: #8 (this), #7 (housekeeping for prior cycle)
- Files touched: `src/representation_aware_mppi_bringup/launch/jackal_outdoor_sim.launch.py`, `eval/tests/test_launch_outdoor_include_run_metrics.py`, `results/p1-outdoor-launch-include-run-metrics.tsv`
- TSV row appended: yes (`qual:tests-32pass`, status=`keep`)
