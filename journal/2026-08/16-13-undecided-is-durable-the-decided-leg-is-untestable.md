# `UNDECIDED` is durable; the one decided leg is untestable

- **Cycle**: 2026-08-16 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39` separability-of-position-and-spread
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's #1 science item: D-299/D-300 attribute a window's exits by lending a
  column one of the run's two factors, but **both factors come off the same
  16-seed ensemble**, so `UNDECIDED` had two live explanations the instrument
  could not separate — the quantities genuinely fail to separate there, or the
  ensemble is too small for the answer to mean anything.
- `attribution_separability(window=...)`: leave-one-seed-out on the exit
  columns already on disk, recomputing both substitutions on the remaining 15
  and re-reading the attribution. All 16 deletions, both axes, **zero sim
  runs**.
- Ran it on both windows — the `K` axis (`SAME_EDGE_UNDECIDED`, one decided
  leg left at `K = 176 → spread`) and the `lam` axis
  (`LAM_WINDOW_UNDECIDED`, `("neither", "both")`).

## What worked / what failed

- **The plain jackknife was confounded, and finding that was the cycle.** An
  exit column is an exit *because* a seed sits outside the band, so deleting
  that seed deletes the phenomenon: the remaining 15 are in band, both
  substitutions cure trivially, and the attribution reads `both` regardless of
  what the two quantities were doing. Raw, the axes produced **exactly one**
  flip — `K = 176` losing seed `0`, the `7.53` that misses the `8.8` floor and
  is simultaneously the `min` that `lower_spread` is computed from. Scored raw,
  the last decided leg on either axis looked one seed deep.
- **Split by whether the deleted seed was in band, nothing flips anywhere.**
  Zero genuine flips on four legs across two axes. Which deletions are legal
  turned out to be the whole reading, not a refinement of it.
- **`lam` → `SEPARABILITY_STABLE`.** `neither` at `0.9` and `both` at `1.15`
  are what all 16 subsets return. D-300's `UNDECIDED` there is **structure**,
  not a sample-size artifact — which answers STATE's question in the direction
  that costs more seeds nothing.
- **`K` → `SEPARABILITY_UNTESTABLE`, a verdict I had to add.** `K = 176` is a
  `15/16` column, so the only deletion that could move its `spread`
  attribution is the confounded one. Calling that `STABLE` would have claimed
  a test that never ran; `K = 80` is the contrast — **two** out-of-band seeds
  (`0` and `11`), so no single deletion removes its miss and its `neither` is
  genuinely probed.
- **The suite went red on two pins this cycle caused itself**, both mechanical
  and both found only by the full run: `attribution_separability` entered the
  guard registry as the **116th** member (`calibrated_ladder`'s fifth
  consecutive cycle, and the first entrant whose narrowing is a *typing* rather
  than an exclusion — the third conjunct is the `miss_is_one_seed_wide` reach
  test), and the new `lam` test is a population-claim loop owing a
  `loop_reach.READING` row (`SAMPLED, 2`, measured with `run(paths=...)` scoped
  to the ladder file, not typed from the leg count). Cost: a second full suite.
- One field over-claimed on the first pass: `decided_legs_stable` counted the
  untestable leg as a survivor (it has no genuine flips because no genuine
  deletion can reach it). Now requires the jackknife to have had purchase.

## North-star delta

- **No robot-facing number moved.** No obstacle, clearance, near-miss or CTE
  reading; still one scene (`cafe_freezing_v0`), still
  `transfers_to_ab_scene = False`, still blocked on PR #68 for any A/B
  reading. Zero new sim runs.
- What moved is that a standing ambiguity is now **closed in one direction and
  correctly labelled unclosed in the other**: `lam`'s `UNDECIDED` is durable,
  `K`'s decided leg is unprobeable at `n = 16`. Both were "we don't know"
  before.
- The instrument is now honest about a confound that would have silently
  inverted its headline — the one raw flip pointed the wrong way.

## Key learnings

- **A jackknife on an exit column deletes the exit.** Order-statistic
  coordinates plus membership-defined columns means the seed that makes a
  column interesting is the seed the resample removes. Any future resampling
  test on these ladders has to type its deletions before reading them.
- **"Not falsified" and "not testable" are different grades and the code has
  to carry both.** Three cycles in a row now (D-298 verdict, D-300 cure test,
  this) the finding was that a predicate was reading something other than
  what its name claimed.
- **The `lam` window's failure to separate will not yield to more seeds.**
  D-300 said what would decide it — a column above the run missing by more
  than one factor's worth, or a below-column narrow enough to be admissible.
  This cycle rules out the cheap alternative of just running more seeds there.
- The `K` leg *is* a seed-count question, and specifically an `n = 32` one: at
  32 a column missing by one seed at 16 either keeps missing widely enough to
  survive a deletion, or stops being an exit.

## Recommended next 1–3 priorities

1. **Re-run `K = 176` at `n = 32`** — the only thing that can decide the
   untestable leg. Costs 32 runs (~2 min at the measured rate), and it is the
   first item in weeks whose answer is not already on disk.
2. **Perturb the run reference too** — this cycle held it fixed and declared
   so. It is a median across three columns' medians, expected robust, but
   expected is not measured.
3. Unchanged: answer Q-160 / retire the five self-blocked `inert_surface`
   pins (eighth cycle of the same `STAGED_MOVED`).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py
- TSV row appended: yes
