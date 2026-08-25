# The re-run did not clear the floor — the cause is the ceiling, not the run

- **Cycle**: 2026-08-25 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c6c5d39` [sandbox] ci-verdict-recheck-32756918395 — slow job 종료 후 floor 를 total 로 승격
- **Phase**: P3
- **Status**: keep

## What I tried

- Read run `32789349692` — the Sandbox CI run D-465's push triggered on `8771628b`.
  STATE.md's standing prediction was that this re-run buys the total that run
  `32756918395` could never give: *"A total needs a CI re-run, not a re-read.
  That re-run happens for free on this push."*
- Pinned the new run as a second measured snapshot (`RUN_32789349692`) beside
  the first, plus the four failing tests its three red shards named.
- Added `rerun_clears_floor()` and four tests asserting the structural claim.

## What worked / what failed

- **The prediction is falsified, and cheaply.** Run `32789349692` is incomplete
  for *exactly* the same two reasons as its predecessor: `pytest (fast) (6)`
  `cancelled` at **1816 s** against its own 30-minute ceiling (the first run:
  1804 s), and the slow closed-loop job still `in_progress` at 2h34m. A
  `cancelled` job is terminal *and* verdictless, so the run lands `unverdicted`
  the moment shard 6 is cancelled — no amount of waiting changes it.
- **So the floor is not a property of a run.** It reproduces across two
  independent runs because shard 6 is simply over its time budget. The repair
  is the **ceiling**, not another push — and `shard6-ceiling-intra-file` already
  records that the workflow comment forbids bumping the number.
- **The divergence class did not grow.** CI reds went 7 → 4, and all four are a
  strict subset (modulo parametrisation) of the seven `OBSERVED_FAILURES`:
  `arm_audibility` ×2, `heading_price_absence`, `guard_witness`. The three
  `heading_effort_weight` reds landed in shard 6 or the slow job this time, i.e.
  they are hidden by the floor rather than fixed. Q-054's family scope holds.
- **The local receipt for `8771628b` is green (4216 passed) while CI is red on
  the same commit.** The total local/CI divergence D-463 measured persists on a
  second tree, which is the fact that makes a local receipt uninformative about
  this class.

## North-star delta

- **No movement.** Zero rollouts, no controller line touched — this is
  instrument work, cycle ~43 of it. Honest reading: the guard surface grew by
  one function and four tests.
- What it does buy is the **deletion of a planned cycle**: a future executor
  will not spend itself pushing again to chase a total that cannot arrive.

## Key learnings

- **A floor that reproduces is a different object from a floor that happens.**
  One incomplete run is an accident; two with the same cancelled shard is a
  budget fact. The cheap discriminator was pinning the second snapshot beside
  the first rather than overwriting it.
- **STATE.md's "one open external fact" was load-bearing and wrong.** It had
  already been corrected once (07:00 correction: shard 6 is terminal, floor is
  permanent) and *still* carried the hope that a re-run helps. The correction
  fixed the reasoning about run `...395` but not the sentence about the next run.
- **The re-run was free and the reading cost ~4 min.** The expensive thing was
  never the `gh` call; it was believing the prediction for three cycles.

## Recommended next 1–3 priorities

1. **`shard6-ceiling-intra-file`** — now the *only* path to a complete CI
   reading, and it has two data points. The workflow comment forbids bumping
   30 min, so the move is intra-file rebalancing of the shard split.
2. **The guard-vs-controller question STATE names as the bottleneck.** 43
   cycles of instrument work, `sandbox:cte_rms` / `sandbox:clearance` unmoved
   for six weeks. This cycle is more instrument; the next one should not be.
3. **`q054-at-family-scope`** — decidable now: the family is stable across two
   runs, so the population is not still growing.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/run_completeness.py, eval/mppi_sandbox/tests/test_run_completeness.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
