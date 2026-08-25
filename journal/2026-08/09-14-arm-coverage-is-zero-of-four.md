# Arm coverage is 0/4, not 1/4 — the census that counts rungs was reading blocks

- **Cycle**: 2026-08-09 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` A census over `censoring`, not just over rungs
- **Phase**: P3
- **Status**: keep

## What I tried

- Lifted censoring from `SeedBlock` (one block) to `Reproduction` (one rung):
  `censored` unions the pinned arms across **both** blocks, `censoring` counts
  distinct arms so an arm pinned at opposite boundaries in the two blocks is
  still one arm.
- Gave `ReplicationCensus` a second, independent verdict — `arm_verdict` over
  `two_sided` / `one_armed`, with `NO_REPLICATED_RUNG` / `NONE_TWO_SIDED` /
  `PARTIALLY_TWO_SIDED` / `FULLY_TWO_SIDED` — and put it in `__str__` so `4/4`
  cannot be quoted without the arm count beside it.
- 7 tests, including the reachability of all four arm verdicts and the
  independence of the two verdicts in both directions.

## What worked / what failed

- 🔴 **The number the slice was authored to report is wrong, and I found it by
  measuring instead of transcribing.** STATE and D-155 both say arm coverage is
  **1/4** with `w = 150` the one two-sided rung. That is a reading over
  *reference blocks*. `w = 150`'s reference block is free on both arms; its
  **replication** pins `risk_mppi` at 0/16. Over rungs the count is **0/4** —
  `NONE_TWO_SIDED`. Every rung the band rests on was walked twice and not one
  of those walks was a test of the pair.
- 🔴 **`w = 250` is worse than either block shows.** Its reference pins
  `stock_mppi` at a floor, its replication pins `risk_mppi` at one — *different*
  arms, same boundary. Each block alone is `ONE_ARM_CENSORED`; the rung is
  `BOTH_ARMS_CENSORED`. A max-over-blocks reading would have missed this, which
  is the concrete reason `censored` unions over arms rather than taking the
  worse block verdict.
- 🟢 **The union-vs-intersection choice is not a taste question here** — it is
  the whole delta between 1/4 and 0/4, so it is pinned in a test that computes
  both counts side by side rather than asserting the one I prefer.
- 🟢 The two verdicts are independent in *both* corners: the published band is
  `FULLY_REPLICATED` + `NONE_TWO_SIDED`, and a synthetic census reaches
  `PARTIALLY_REPLICATED` + `FULLY_TWO_SIDED`. So `arm_verdict` cannot be
  derived from `verdict` and is not a relabelling of it.
- 🟡 Reported, never thresholded, on the `one_run_rungs` discipline — no test
  asserts arm coverage is non-zero. Doing so would make today's honest 0/4 a
  permanent red (D-044's muted check).

## North-star delta

- No movement. Zero sim runs, no controller/representation/dynamics code; the
  headline (`unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate`
  1.0000 over 5 cells / 40 seeds) is untouched.
- What moved is the *strength of a claim already made*: the replication
  programme's headline result is weaker than it was recorded as being. That
  matters for P5, where these separations get quoted as evidence.

## Key learnings

- **A per-item field aggregated at the wrong level is a wrong population
  claim, not a missing one.** `SeedBlock.censoring` was correct at every call
  site; the error was that two cycles read it over reference blocks and wrote
  the answer down as a property of rungs. The census is what forces the level
  to be stated.
- **The dangerous aggregation is the one where the parts look reassuring.**
  Both of `w = 250`'s blocks read `ONE_ARM_CENSORED`; the rung is
  `BOTH_ARMS_CENSORED`. Same shape as D-149's empty-subset finding: the
  composition is more severe than either input, and nothing in the parts says so.
- **A slice authored to *report* a number should re-derive it.** The TODO said
  "so 4/4 cannot be quoted without 1/4 beside it". Had I implemented to that
  spec, the constant 1/4 would have shipped as a test fixture and the census
  would have certified the error it was built to prevent.

## Recommended next 1–3 priorities

1. **Price the ceiling** — three rungs are censored because `stock_mppi`
   cannot clear a 0.40 m margin anywhere. A margin sweep would say whether the
   band's separations survive at a margin both arms can straddle, which is the
   only route from `NONE_TWO_SIDED` to a two-sided test.
2. **Carry "unmeasured" in the strand verdict (D-156 follow-up)** — unchanged,
   one field + one test.
3. **Fix `shift_census`'s absent-cell path (Q-121)** — unchanged for ten
   cycles.

## Artifacts

- PR: #67 (open, continued under D-140)
- Files touched: `eval/mppi_sandbox/separation_reproduction.py`,
  `eval/mppi_sandbox/tests/test_separation_reproduction.py`,
  `docs/decisions.md`
- TSV row appended: yes
