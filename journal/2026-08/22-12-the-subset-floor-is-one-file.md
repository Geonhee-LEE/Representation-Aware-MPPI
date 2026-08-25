# The subset floor is one file, and it is 7.2 minutes

- **Cycle**: 2026-08-22 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 `split-suite-or-split-cycle`
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE's top structural item — "mark the census tests so a repair cycle
  verifies in ~3 min instead of ~25" — and, before writing any marker, checked
  whether the instrument existed. It did: `census_subset` (Q-159's pricing
  instrument), and Q-159 was already **resolved → D-282** on 2026-08-15.
- D-282's verdict was taken against a full suite of **652 s**. `probe` reported
  this cycle's HEAD graded at **1437.81 s** — the suite has grown **2.2×** since
  the verdict, and the census registries have grown with it. So the verdict was
  re-priced rather than re-derived: one CLI run, zero new code.
- Ran `python3 -m eval.mppi_sandbox.census_subset` on clean CPU (it is a *timing*
  instrument, so contention would corrupt the only number it produces).

## What worked / what failed

- **The measurement**: `11 files in 11 shards: 433.5s (rc=0) against a full suite
  of 1438s [MEASURED] → SUBSET_MARGINAL`.
- **The verdict did not flip** — `SUBSET_MARGINAL` both times. D-282's answer (c)
  stands: the subset is a timing tool, `Price` is not a `Receipt`, and it cannot
  license a push. That half needed no re-measurement and did not get one.
- **The number underneath it moved a lot.** Saving was `652 − 243.5 = 408.5 s`
  (19% of a 35 min budget); it is now `1438 − 433.5 = 1004.5 s` — **16.7 min,
  48% of the budget**. D-282 called the remedy optional at 19%. At 48% the same
  arithmetic no longer reads as optional, even though the verdict word is
  unchanged.
- **STATE #1's target is refuted, not merely unmet.** `~3 min` was the goal;
  the subset is **7.2 min** and moving the wrong way — it grew **1.78×**
  (243.5 → 433.5 s) while the file count grew only 9 → 11.
- **The reason it cannot reach 3 min is structural, and this run is the first to
  show it plainly**: 11 files were placed in **11 shards**. Each census file
  already has a shard to itself, so the subset's wall clock *is* the slowest
  single census file. No further parallelism exists to buy. D-282 wrote this
  ("subset 의 하한은 가장 느린 file 하나") when the floor was invisible under a
  9-file/9-shard split; at 433.5 s it is the entire measurement.

## North-star delta

- **Zero rollouts, no controller moved — 40th consecutive cycle.** 경로추종 and
  물체회피 are untouched and should be read as untouched.
- One structural item on STATE's list is **removed by measurement rather than
  attempted**: subsetting cannot produce a 3-minute repair loop at any job count.
  That is worth more than a marker scheme that would have been built, measured,
  and found to bottom out at 7.2 min anyway.

## Key learnings

- **A resolved Q is not a settled number.** Q-159 → D-282 was correctly closed,
  but its verdict was a *ratio* against a full suite that has since doubled.
  Resolved questions whose answers are quotients should be re-priced when either
  operand moves 2×; nothing in this loop currently prompts that.
- **The `SUBSET_MARGINAL` word hid a 2.5× change in the quantity that matters.**
  `verdict()` thresholds on a fraction (`NEAR_FULL_FRACTION`) and an absolute
  (`CHEAP_SECONDS`); both were stable while the *saving* went 408 s → 1004 s.
  A verdict that is stable across a doubling is a verdict that is not tracking
  the decision it feeds.
- **Shard count equal to file count is the signal to stop optimising the split.**
  It is a cheap, readable end-of-road marker and it should be looked for before
  any future "split the suite" item is picked up.
- Checking whether the instrument already existed cost ~4 min of reading and
  saved the cycle from building a marker scheme on top of a module whose own
  docstring argues against exactly that (`suite_shard`'s preamble).

## Recommended next 1–3 priorities

1. **`slowest-census-file`** — identify which of the 11 census files is the
   433.5 s floor and why. That single file is now the whole subsetting story and
   possibly a large share of the 1438 s suite. Cheap: per-shard timings are
   already produced by `suite_shard`.
2. **`register-remaining-ensemble-modules`** — unchanged from STATE; `source_reach`
   still convicts ~14 modules. One batch, not one per cycle.
3. **`shadow-mask-two-channel-split`** — the first P3-substance item in six
   cycles; zero rollouts to spec.

## Artifacts

- PR: #67 (open, continued under D-140)
- Files touched: `journal/2026-08/22-12-the-subset-floor-is-one-file.md`, `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
