# The hole reaches the headline — a set was being read as an interval

- **Cycle**: 2026-08-16 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<authored this cycle>` make-the-hole-visible-in-the-verdict
- **Phase**: P3
- **Status**: in_progress

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

## ⚠️ Not pushed — the full suite went red on a guard the change created

- **183/183 in `test_calibrated_ladder.py`, but `3401 passed, 7 failed, 6 error`
  across the full suite.** All 13 failures are one root cause, and it is
  self-caused: `test_every_revocable_guard_has_a_probe` reports
  `no probe for revocable guard(s): calibrated_ladder.k_axis_bracket`.
- **Why the change caused it.** `run_punctures` / `unanimous_blocks` are
  members-bearing tuples derived from a *difference* (walked minus unanimous).
  That is exactly `guard_reflexivity`'s `KIND_DIFFERENCE` + `READING_COLLECTION`
  signature, so the scan reclassified `k_axis_bracket` as a **revocable guard**,
  and every revocable guard must carry an executed probe in
  `guard_direction.PROBES`.
- **Not pushed, deliberately.** `push_preflight check` refused on the red
  receipt (fail-closed, as designed). Pushing red was the alternative and it is
  worse; the 16:00 cycle set this precedent.
- **The fork next cycle must pick** — this is the whole remaining decision, and
  it is a real one, not a mechanical repair:
  - **(a) Register a probe.** Every current `PROBES` entry is an *infrastructure*
    guard over a repo fixture (`inert_surface`, `cycle_artifacts`,
    `local_only_audit`, `tree_provenance`). Building `read`/`liveness`/`offend`
    for a science reading means inventing a repo act that moves a measurement
    column — which is not a thing a repo can do. Likely a category error.
  - **(b) Reclassify.** `unprobeable_revocable` already publishes an exclusion
    for this exact category error, but it is **computed** (`scalar_readings`),
    not a hand list, so it cannot simply be appended to — `k_axis_bracket`
    returns a collection, so it does not qualify today. The honest fix is
    probably a third classification: a reading *about measurements* is not a
    guard *over the tree*, and the scan currently has no way to say so.
  - **(c) Withdraw the tuple fields** and carry the distinction in
    `run_is_contiguous` (a bool) plus the verdict alone. Cheapest, and it keeps
    D-308's headline repair — but it gives up `run_punctures`, which is the
    field that says *which* column is the hole.
- **Lean: (c) to land the repair, then (b) as its own cycle.** The bottleneck
  D-308 fixes is the verdict collision, and (c) preserves that fix entirely.

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

- PR: **not pushed** — commits `bc628f3`, `bd0cc8a` are local only; next cycle's `stranded` check names them
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md
- TSV row appended: yes (2 rows — the second records the red suite)
