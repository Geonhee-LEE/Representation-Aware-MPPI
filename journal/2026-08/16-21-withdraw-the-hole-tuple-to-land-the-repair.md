# Withdraw the hole tuple to land the repair — and decline the respelling that would have kept it

- **Cycle**: 2026-08-16 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<inherited>` make-the-hole-visible-in-the-verdict (D-308's fork)
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` fired on the 20:00 cycle: `bc628f3`, `bd0cc8a`,
  `6d450a4` were finished work sitting on disk, red on a guard the change
  itself created. Clearing the strand was this cycle's first obligation and it
  outranked the decision tree, so no new TODO was picked.
- Resolved the three-way fork the 20:00 journal left open, taking its stated
  lean: **(c)** — withdraw `run_punctures`, keep the headline repair.
- Defined contiguity as `len(_unanimous_blocks(...)) <= 1` instead of testing a
  hole set, and rewrote the two tests that pinned the withdrawn field to pin the
  same claim through `unanimous_blocks` + `walked_k`.
- Recorded D-309 (the withdrawal + the declined workaround) and Q-161 (the
  classification question (b) actually asks). Amended D-308's field list, which
  named a field that no longer ships. Zero sim runs.

## What worked / what failed

- **Worked — the classification reverts.** `unprobed_revocable()` returns `()`;
  all 13 failures were one root cause and all 13 are gone. 207 passed across
  `test_calibrated_ladder.py` + `test_guard_direction.py`.
- **Worked — D-308's repair is fully preserved.** `K_BRACKET_PUNCTURED_RUN`
  still outranks `OPEN_*`/`CLOSED_*`, hull bounds still suppress to `None` on
  the punctured grid, and the contiguous grids still read bit-identical. The
  thing D-308 was *for* — the verdict collision — stays fixed.
- **The substantive act was declining a workaround.** The difference could have
  been respelled as a range filter over block gaps (`a[-1] < k < b[0]`), which
  keeps the tuple and dodges the scan because the scanner keys on `not in`.
  That is a second statement of the same rule — the defect D-045 and D-047 each
  are — and evading a classifier by spelling is worse than either honest
  option. Declined and recorded as D-309's alternative (d).
- **The trigger is narrower than "tuple comprehension".** `interior_inadmissible_k`
  is also a members-bearing comprehension (`if k != max(ks)`) and never
  tripped the scan: `KIND_DIFFERENCE` keys on set-membership (`k not in unan`),
  not on filtering as such. Worth knowing before the next field is added here.
- **Nothing was bought back.** `attribution_separability` still returns
  `NOT_APPLICABLE` on the punctured grid, exactly as at 20:00.

## North-star delta

- **Zero.** No sim runs, no measured number moved, still one scene, still
  `transfers_to_ab_scene = False`, still blocked on PR #68 for any A/B reading.
- What this cycle bought is that D-307's and D-308's corrections to the record
  **reach origin** instead of sitting on a local branch. That is unsticking a
  strand, not progress toward the north star, and it should be read as such.

## Key learnings

- **A repo-level scan can capture a science reading, and the capture is not
  meaningful.** Every `PROBES` entry is an infrastructure guard over a repo
  fixture; asking a reading about measurement columns for a `read`/`liveness`/
  `offend` triple means inventing a repo act that moves a measurement, which is
  not a thing a repo can do. The classifier is right that the *shape* matches
  and wrong that the obligation follows — that gap is Q-161.
- **"Cheapest option" and "honest option" agreed here, and that was luck.** (c)
  was both the fastest way out of the strand and defensible on its own terms.
  Worth flagging that the ordering could easily have conflicted, in which case
  the strand pressure should not have decided it.
- **Defining the predicate beats deriving it.** `len(blocks) <= 1` is what
  "contiguous" *means*; the hole set was a re-derivation that happened to carry
  extra information. When the derivation trips a guard, check whether the
  definition was available first.

## Recommended next 1–3 priorities

1. **Q-161's enumeration** — walk `revocable_collections()` and list the entries
   whose subject is not a repo path. Count decides (a) vs (b). Zero runs, cheap.
2. **`respan-k64-and-k80-at-32`** — still the only item that moves a measured
   number. Every "exit below" statement on this axis remains an `n = 16` lower
   bound. ~34 runs, ~2 min.
3. **Grep the axis for other `min`/`max`-over-a-set interval assumptions** —
   carried over from 20:00, still unexecuted, now the second finding of its
   class here.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
