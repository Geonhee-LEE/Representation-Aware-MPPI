# The 13 entrants were legitimate; the un-run census check is what stranded them

- **Cycle**: 2026-08-22 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `strand-repair` D-112 stranding gate (outranks the decision tree)
- **Phase**: P5
- **Status**: keep

## What I tried

- Phase 1's `cycle_artifacts stranded` fired rc=1: `bb3ddbc` (D-427, the barrier-shape
  knob) was one commit ahead of `origin` with a finished journal on disk, and the
  18:00 cycle that followed it graded `NO_JOURNAL` — it produced nothing at all.
- The receipt probe explained why the strand could not simply be pushed: the receipt
  for `bb3ddbcc` was **red**, 3 failures, all in `test_default_lam_sites.py`. The push
  gate refuses a red receipt, so the strand was not a forgotten `git push` — it was a
  branch that could not legally push.
- Re-derived the census and repaired all four pins to the measured values:
  `(decides, defaults, forwards)` `(106, 72, 40) → (106, 85, 41)`, `total 218 → 232`,
  `inert_defaults 4 → 17`, margin `34 → 21`, plus the 13 new names in the inert
  allowlist (with duplicates — a function that constructs twice is two sites).

## What worked / what failed

- **The entrants were legitimate and the pins were still right to fire.** All 13 new
  sites construct `MPPIParams(obs_barrier_band=...)` to interrogate the *cost
  function*; `lam` is applied to that function's output in the softmax, so no
  temperature is reachable from what they exercise. They are the `_cost_at` shape
  (D-411), not a compliance regression. "Legitimate" and "announced" are different
  properties and only the pin supplies the second.
- **`weighting_at_shipped` did not move — 68 before, 68 after.** `defaults` rose by 13
  and the load-bearing number, sites that actually weight at an inadmissible
  temperature, is unchanged. This is the first cycle where the gap between `defaults`
  and the sim bill did the entire work, and it is why re-pinning is the honest repair
  here rather than something to argue away.
- **The margin gave back nine cycles of widening in one commit** (34 → 21; largest
  prior move: 3). D-383's "every new census this branch writes lands in `decides`" was
  a claim about the *kind of module* recent cycles happened to write, not a property
  the census enforces — a cost-function test file has no rung to spell.
- **What failed is exactly one line.** `census_preempt` costs ~2s, sits in the commit
  block for this reason, and was not run by the 17:00 cycle. It reads `rc=1` here on
  both sides of the stage, so it was available the whole time. Cost of skipping it:
  two dead cycles (18:00 produced no journal) and a 24-minute suite re-run.

## North-star delta

- **No movement toward avoidance/tracking** — this is repair, not measurement. D-427's
  actual finding (knee+shape 3/5 vs knee 1/5) is unchanged and is what reaches `main`.
- **It unblocks the finding**, which was the real cost: the complementarity result had
  been sitting undelivered on disk for two cycles.

## Key learnings

- The stranding gate and the receipt probe answer different questions and this cycle
  needed both. `stranded` said "this work never reached origin"; the probe said "and
  it cannot, because it is red". Either alone would have produced the wrong repair —
  a bare `git push` would have been refused, and a green probe would have hidden the
  strand's cause.
- A red branch does not announce itself between cycles. 18:00 sat on the same red tree
  and left no journal, so the only signal that anything was wrong was a gate one cycle
  later. The checks that cost seconds are the only ones that fire at the moment the
  damage is cheap.
- The census margin is not a compliance score. Two of its last three moves were
  downward and both were honest; reading it as "compliance falling" would invite
  exactly the wrong repair — naming a rung in a test whose subject is the default.

## Recommended next 1–3 priorities

1. **16-seed ensemble for the knee+shape arm.** D-427's 1/5 → 3/5 is Fisher p ≈ 0.52
   at n=5; per-seed `cte_rms` improves on 4 of 5 (−38 %). The direction deserves power.
2. **Re-pin `test_buying_the_clearance_check_is_not_free` off seed 0.** Flagged by
   D-426, re-confirmed by D-427: seed 0 is the one seed that worsens, and it is the
   seed the test pins. Still open.
3. **`cafe_cut_in_v0` scene defect (D-426 defect 2)** still blocks any transfer claim
   beyond the single scene.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_default_lam_sites.py, docs/decisions.md
- TSV row appended: yes
