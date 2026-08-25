# The unanimous set was the censored set — same tuple, opposite reading

- **Cycle**: 2026-08-17 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-74f4` [sandbox] Carry saturation with every thresholded reading
- **Phase**: P5
- **Status**: keep

## What I tried

- Carried D-317's censoring caveat from the module that discovered it
  (`membership_dethresholded_in_k`) to the two functions callers actually read a
  `K` verdict from: `ensemble_scaling_in_k` and `k_axis_bracket`, both of which
  published `membership_by_k` / `n_in_band` bare.
- Added `count_saturated_at_k` + `count_is_censored_above_at` to both, forwarded
  (not re-derived) into the bracket so the two cannot disagree about which
  columns are blind.
- Three tests including the D-317-style negative control: the flag must be able
  to come back **empty**, derived from the measured saturated set rather than
  hardcoded (D-047).
- **Ended the ninth deferral off the `K` axis.** Zero sim runs.

## What worked / what failed

- **The finding is that the field already existed under a different name.**
  `ensemble_scaling_in_k` computes `unanimous_k` as `tuple(k for k in ks if
  per_k[k]["n_in_band"] == need)` — which is *exactly* the saturation predicate.
  The payload has published the censored columns since D-292, under a name that
  reads as an **achievement** ("these columns are unanimous") when the identical
  fact read as a measurement property says **the count is blind there**. So this
  was never a missing measurement; it was a missing reading of one. Both
  spellings now ship, with `saturation_equals_unanimity` measured rather than
  asserted.
- **Sharper on the bracket: the run `k_axis_bracket` brackets *is* the censored
  region.** `unan` and the saturated set are the same predicate, so every bound
  the payload reports — `run_bounds_open_intervals`, `unanimous_blocks`, both
  neighbours — is an edge of the region where the count has stopped moving. That
  does not invalidate the bracket (an edge of the blind region is precisely what
  a membership bracket *can* honestly locate), but it does mean the payload must
  refuse to say anything about the run's **interior**, which is where D-317
  measured the axis peaking. `interior_search_statistic` now names the
  replacement by name, because the bottleneck being fixed is a reader habit and
  a habit is not corrected by a field you must know to look up.
- Verified the new fields reproduce D-317's numbers exactly: `(96, 128, 160)` at
  `n=16`, `(96, 160)` at `n=32`.
- ⭐ **`census_preempt` paid on its first standing run.** Wired into Phase 3 by
  the 08:00 cycle; this is the first cycle where the *constitution*, not an
  author's memory, ran it. It went `DRIFT` in ~2 s: two of my three new tests
  were population claims absent from `loop_reach.READING` — the 05:00 failure
  mode, which cost 785 s of red suite that time. Repaired with the D-305 scoping
  before any suite started. Its `UNCOVERED` line was worth reading too.
- ⚠️ **`pkill -f` matched its own shell — third reproduction.** The pattern
  `eval.mppi_sandbox.loop_reach report` appeared *in the pkill argument itself*,
  so the compound command killed its parent (rc=144). D-313 and D-316 each hit
  this class; I hit it having read both this cycle. Cost ~1 min.

## North-star delta

- **No movement toward the north star**, and this is the honest reading: still
  one scene, one rung, one temperature, zero sim runs,
  `transfers_to_ab_scene = False`, every A/B reading blocked on PR #68.
- What moved is the *validity* of the `K`-axis claims already on the branch: any
  future bracket search now finds the censoring caveat attached to the number it
  would drive off, instead of in a sibling module it would have to know to
  consult.

## Key learnings

- **A caveat is delivered where the number is published, not where it is
  discovered.** D-317 measured the censoring correctly and completely, and it
  was worth nothing to a caller reading `k_axis_bracket`. This is the same shape
  as 08:00's lesson about modules vs. text: the finding is not standing until it
  is at the site.
- **Check whether the field you are adding is already there under an
  encouraging name.** The cheapest version of this cycle was a rename plus two
  measured identities, not new machinery. The defect was epistemic, not missing
  data.
- **The pre-empt's value is now measured twice and both times it was the same
  defect class** (unregistered population claim from a new test). Two seconds
  against 785; the wiring is the part that made it happen unprompted.

## Recommended next 1–3 priorities

1. **Make the bracket refuse an interior claim structurally**, not just by
   naming the right statistic — a caller can still read `run_bounds` and infer
   an interior. A `K_BRACKET_INTERIOR_UNREADABLE` verdict or an interior-facing
   field that returns `None` would be the D-308 treatment applied one level in.
2. **Decide whether this branch closes** (`3bec5d39-9c22`, carried) — PR #67 now
   carries thirteen commits spanning a cost critic, a verification surface, and
   a `K` axis. That is one unreviewable diff.
3. **`aggregate_results.sh` above the receipt** (`3bec5d39-81d1`, carried).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67 open)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py,
  eval/mppi_sandbox/loop_reach.py,
  eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md
- TSV row appended: pending
