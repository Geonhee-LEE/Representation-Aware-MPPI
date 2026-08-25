# Five of eight cross-track bars cannot fail — and the clearance winner is the one that fails them

- **Cycle**: 2026-08-19 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — sweep `cte_rms_max` as D-357 swept `min_distance_to_obstacle`
- **Phase**: P5
- **Status**: keep

## What I tried

- Bought the attained-range table D-357 declined to buy: **64 closed-loop rollouts**
  (8 scenes × 8 arms, seed 0, ~40 s wall clock on 14 workers) harvesting `cte_rms`
  off the same runs that produce `min_clearance`. That absence was exactly what
  `threshold_vacuity.UNSWEPT_KEYS` recorded, and it was the whole reason the
  경로추종 column had never been graded.
- Shipped `eval/mppi_sandbox/cte_vacuity.py`: the same five-verdict sweep, with the
  comparison **inverted**, plus `CTE_SEED0` / `CENSUS` / `CLEARANCE_TENSION` pins
  and 11 tests.
- Corrected `threshold_vacuity`'s docstring claim that no `cte_rms_max` table exists
  on disk — true when written, false as of this commit.

## What worked / what failed

- **5 of 8 scenes are `VACUOUS_PASS`** — the whole eight-arm registry passes by
  more than an order of magnitude. `cafe_straight_v0` declares `0.20` against a
  worst arm of `0.0088` (**23×**); `city_figure8_v0` `0.50` vs `0.0250`;
  `freezing` `0.50` vs `0.0231`; `convoy` `0.50` vs `0.0706`; `city_curved_v0`
  `0.50` vs `0.1303`. The clearance column had **one** vacuous scene; this one has five.
- **The dangerous direction inverted, and D-357's ranking of the two was
  parochial.** A clearance bar is a floor, a cross-track bar is a ceiling, so the
  verdicts swap sides: every defect here is `VACUOUS_PASS`, none is `VACUOUS_FAIL`.
  D-357 called `VACUOUS_FAIL` the more dangerous *of the two directions it could
  see* because it reads as "the scene is hard." A vacuous **pass** column reads as
  "경로추종 is solved everywhere" — and 5/8 green cells were never able to say
  anything else.
- **The clearance winner is the cross-track loser.** On the three discriminating
  scenes the failing arms are `cbf_mppi` (head_on + obstacle_crossing),
  `social_mppi` (head_on), `essps_mppi` (cut_in). `cbf_mppi` is
  `clearance_census`'s *only* genuine winner (+0.228 m over `stock_mppi`, 8/8
  seeds). The one arm measured buying 물체회피 is the one failing 경로추종 twice —
  and the north star demands both at once. No single-column sweep could see this.
- **My first boundary test was wrong and the module was right**: I asserted a
  single-arm population one hair over the bar grades `DISCRIMINATING`; `lo == hi`
  there, so it is `VACUOUS_FAIL`. Fixed the test, kept both boundaries asserted.
- `census_preempt` caught the unregistered `loop_reach` row at the stage (~2 s)
  instead of ~21 min into the suite — **seventh** consecutive cycle it has done so.

## North-star delta

- The acceptance matrix's **경로추종** column is now swept end to end, and it is in
  worse shape than the 물체회피 one: **5 vacuous vs 1**, 3 discriminating, 0
  undeclared, 0 unmeasurable. The bottleneck's question — how much of the pass/fail
  signal is structurally incapable of failing — now has a bounded answer for *both*
  headline keys, and the answer is that **6 of 16 cells grade nothing**.
- Still characterisation, not performance: no controller changed. But the tension
  finding is the first *measured* statement on this branch that the two halves of
  the north star trade against each other rather than being independently winnable.
- The seed-0 reading can only **over**-report vacuity (more seeds only widen `hi`,
  which moves scenes toward `DISCRIMINATING`), so "five" is an upper bound.
  `WIDENING_UNBOUGHT = 448` prices the check I declined.

## Key learnings

- D-357's "the failing direction is the dangerous one" was a claim about a
  one-column population and does not survive the second column. Ranking defect
  directions before both signs of the criterion are in hand is premature.
- The cheap-because-on-disk framing has a cost: D-357 was affordable *because* it
  reused pinned tables, and that same affordability is what left the larger defect
  unmeasured for as long as it went unmeasured. 64 rollouts was ~40 s.
- `cte_max` is now the cheapest remaining column — declared by 4 scenes, and its
  rollouts are already pinned in `CTE_SEED0`. It needs no new sim time at all.

## Recommended next 1–3 priorities

1. Sweep `cte_max` (peak, not rms) from the already-pinned `CTE_SEED0` rollouts — zero new rollouts.
2. Decide the 5 vacuous `cte_rms_max` bars: tighten toward attained ranges, or record why a 20× margin is intended. Same judgement class as `head_on`'s `0.40`, so it likely belongs with the user.
3. Re-take the tension finding over 8 seeds — is `cbf_mppi`'s cross-track failure robust, or a seed-0 artifact?

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/cte_vacuity.py, eval/mppi_sandbox/tests/test_cte_vacuity.py, eval/mppi_sandbox/threshold_vacuity.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md
- TSV row appended: pending
