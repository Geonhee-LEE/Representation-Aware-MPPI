# The hole reaches the headline — a set was being read as an interval

- **Cycle**: 2026-08-16 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<authored this cycle>` make-the-hole-visible-in-the-verdict
- **Phase**: P3
- **Status**: keep

## What I tried

- Repaired the predicate STATE named as the bottleneck: `k_axis_bracket`
  returned the same verdict **and** the same `run_bounds_open_intervals` for a
  contiguous unanimous run and a punctured one (D-307 pinned the collision).
- Located the mechanism rather than patching the symptom: the bounds were built
  from `min(unan)`/`max(unan)` — the **convex hull** of the unanimous columns,
  which is blind to whether anything measured sits inside it.
- Added `K_BRACKET_PUNCTURED_RUN`, a `_unanimous_blocks` helper, and three
  payload fields (`run_is_contiguous`, `run_punctures`, `unanimous_blocks`);
  suppressed the hull bounds to `None` when the set is not an interval.
- Zero sim runs. Updated D-307's paragraph-(3) pin — it asserted the collision,
  which is now the thing that must not happen — and added a D-308 test.

## What worked / what failed

- **Worked — the headline now separates the two grids.** The `n = 32` grid
  returns `K_BRACKET_PUNCTURED_RUN` with bounds `None`; the `SUB16` grid still
  returns `K_BRACKET_OPEN_BELOW` with its bounds intact.
- **Worked — contiguous readings are bit-identical.** The default grid still
  returns `K_BRACKET_CLOSED_SAME_EDGE` with unchanged bounds, so D-296…D-306's
  contiguous-grid quotes are untouched. 183/183 in the file, no other test moved.
- **The adjacency definition was the one real design choice.** Punctures are
  computed over the **walked** axis, not over `K`: a column nobody measured is
  absence of evidence, and a hull-based test would have called a sparse grid
  punctured. Pinned with a sparse-grid case that must read contiguous.
- **Failed to buy anything back.** `attribution_separability` still returns
  `NOT_APPLICABLE` on the punctured grid. The repair makes the shortfall
  legible; it does not remove it.

## North-star delta

- **No movement in any robot-facing number.** Zero runs, one scene, still
  `transfers_to_ab_scene = False`, still blocked on PR #68 for any A/B reading.
- What moved is the reporting surface: the verdict field that five decisions
  quoted as evidence of a run can no longer be quoted that way when there isn't
  one. That is a correction to the record, not progress toward the north star.

## Key learnings

- **A field can be right and still be unreadable.** `interior_inadmissible_k`
  carried the distinction correctly the whole time; the bug was that no headline
  consulted it. D-307 saw the same shape one level down (D-304's confound). The
  recurring failure is not missing data — it is a payload field the summary
  never reads, and the fix is always to move the fact up, not to measure again.
- **`min`/`max` over a set is a silent interval assumption.** It is the same
  defect class in both places it has now appeared on this axis. Worth grepping
  for the pattern before it produces a third finding.
- **Ordering the verdicts is the substantive part.** `PUNCTURED` had to outrank
  `OPEN_BELOW` / `CLOSED_*`, because those answer *how a run ends* and presuppose
  there is one. A verdict that answers the second question while the first is
  unanswered is what produced the collision.

## Recommended next 1–3 priorities

1. **`respan-k64-and-k80-at-32`** — the two columns below the run. Every "exit
   below" statement on this axis is still an `n = 16` lower bound, and D-307
   showed the ensemble does not move columns alike. ~34 runs, ~2 min.
2. **Grep the axis for other `min`/`max`-over-a-set interval assumptions** —
   this is now the second finding of that class here. Zero runs.
3. **`3bec5d39-…-f353` third-ensemble-for-the-marginal-span** — `K = 128` at
   `n = 48`; the interior exit carries more weight now that it is named as one.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md
- TSV row appended: pending
