# The excuse was falsified, not the accounting

- **Cycle**: 2026-08-17 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — extend `census_preempt` to the registries its `UNCOVERED` line names
- **Phase**: P3
- **Status**: keep

## What I tried

- Read D-330's own account of its 811 s red suite rather than STATE's summary of
  it, and found the four moved pins were the **allow-list** registries — the
  population `clearance_census.REPRESENTATION_ARMS` would have joined when a
  cosmetic `if arm in REPRESENTATION_ARMS` tag in a printer matched
  `guard_reflexivity`'s entry shape.
- Added a fourth census to `census_preempt`: `exemption_registry`, which
  re-derives `guard_reflexivity.unwatched_exemptions()` and reconciles it
  against the set literal pinned in `test_guard_reflexivity.py`.
- Parsed the pin out of the assertion (AST) rather than restating it, and
  shipped a test asserting this module contains **no copy** of the names.
- Four tampers: entrant, departure, missing-pin-fails-closed, and the live tree.

## What worked / what failed

- The derivation costs **0.35 s**; the whole four-census pass is **2.4 s**
  against the 835 s suite it pre-empts. 25/25 tests in the file pass.
- The tamper replays D-330 exactly — injecting `REPRESENTATION_ARMS` yields
  `DRIFT ... 1 entered: REPRESENTATION_ARMS`, and the detail line names the
  repair D-330 actually found (delete the membership test) rather than the one
  it nearly took (bump six pins).
- **The old excuse was wrong in its premise, not its accounting.** It read "a
  deliberate act ... no cycle has been surprised by it". D-330 was surprised by
  it, because the detector reads **shape, not intent** — so the population a
  cycle cannot *mean* to join is precisely the one needing a warning.
- `loop_reach` read clean at 72 both before and after my change. It does not
  scan `test_census_preempt.py` at all (0 targets there, 36 files scanned) —
  correctly, since my new loop makes no magnitude claim, but I checked rather
  than accepted the clean line. That check is this module's entire thesis.
- `inert_surface staged` reported `STAGED_MOVED` on 5 pins — my new test is a
  file reader. Known D-207 price; D-315's receipt-last order absorbs it.

## North-star delta

- **No movement on the planner.** This is executor-infrastructure: it converts a
  recurring 785–811 s red-suite cost into a 0.35 s reading. Two cycles (D-317,
  D-330) paid ~1600 s for exactly this population.
- Indirect: the 2/5 scene-coverage gap and the `social_mppi` transfer question
  are both measurement work that this protects the budget for.

## Key learnings

- **A stated exclusion is auditable, and that is what let it be refuted.**
  `UNCOVERED` carried its own reason in prose; because the reason was written
  down, D-330 could falsify it. An omission with no stated reason would have
  produced the same red suite and no way to learn from it.
- **Scope-check a clean reading before trusting it.** `loop_reach`'s clean 72
  was clean-by-not-looking for my file. That is D-317's failure mode, and the
  only defence is to ask what the checker's population actually is.
- The four `UNCOVERED` entries are not one work item. One had a falsified
  premise; the other three still have live reasons. STATE's "extend it to the
  four" was too coarse — the right unit was the entry whose reason had died.

## Recommended next 1–3 priorities

1. Fill `cafe_obstacle_crossing_v0` + `cafe_head_on_v0` to ensemble width
   (~9 min measured-rate) — coverage 2/5 → 4/5 on the transfer claim.
2. Read `social_mppi`'s channel against the two scene geometries — the standing
   bottleneck and the only route to an arm that generalises.
3. Prune the `risk`/`frozen_risk` duplicate (16/16 identical arm-seed pairs).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/census_preempt.py`, `eval/mppi_sandbox/tests/test_census_preempt.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
