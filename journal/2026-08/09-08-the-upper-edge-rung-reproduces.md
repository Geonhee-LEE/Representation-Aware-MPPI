# The upper-edge rung reproduces — and two of four rungs are still unlooked-at

- **Cycle**: 2026-08-09 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — replicate `w = 150` on a disjoint seed block
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked the published band's `w = 150` rung on `cafe_head_on_v0` (λ = 0.8,
  margin 0.40 m) over **32 seeds** — D-133's block 0–15 *and* a fresh disjoint
  block 16–31, both arms, 64 runs, ~9 min. Same protocol as D-151's `w = 250`
  walk, unchanged, including re-walking the old block first as the entitlement
  check (D-139).
- Recorded the 64 clearances in `separation_reproduction.W150_CLEARANCES`;
  factored the two walks' block-splitting onto one `_reproduction` helper.
- Shipped `ReplicationCensus` + `published_census()`: coverage of the band's
  `SEPARATED` rungs by disjoint-block replication. 13 new tests (19 → 32).

## What worked / what failed

- 🟢 **The reference block reproduced D-133 exactly on both arms** — stock
  10/16 sub-margin, risk 1/16. Second walk in two cycles where the entitlement
  check passed, so the pipeline is not drifting.
- 🟢 **The rung reproduced.** Fresh block: stock **5/16**, risk **0/16** —
  `SEPARATED`, and in the direction the mechanism predicts. Pooled at n = 32:
  stock 15/32, risk 1/32, still `SEPARATED`. Verdict **`REPRODUCED`**, the
  first in the repo: the protocol had only ever returned a reversal, so this is
  the reading that shows it can come back either way rather than being a
  machine for overturning things.
- 🟡 **It confirms the sign, not the size.** The stock arm's sub-margin rate
  *halves* between blocks (10/16 → 5/16) while risk goes 1/16 → 0/16. The
  direction is stable and the magnitude is seed-dependent by ~2×, so a reader
  who takes the reference block's delta as the rung's effect size is reading
  more than replication bought. Pinned in its own test because the verdict
  deliberately says nothing about magnitude.
- 🟡 **The exact 10/16 agreement is luckier than it looks.** One of the ten
  sub-margin stock runs (seed 2) sits at **0.3993 m** — 0.7 mm under the
  margin. `REPRODUCED` survives either count, but the *exactness* that entitles
  the walk is one run from `9/16`. Recorded as a test rather than left for a
  future reader to rediscover.
- 🔴 **Two of the band's four separated rungs have still never been looked at
  twice.** That is what `ReplicationCensus` exists to say: `w = 75` and
  `w = 100` are `unreplicated`, and the two rungs that *were* replicated
  **disagree with each other** (`held (150,)`, `overturned (250,)`). Coverage
  is 2/4 with a 50% overturn rate on what has been checked — reported, never
  thresholded, the same discipline as `one_run_rungs`.
- 🟢 **The census made the older tests non-vacuous.** With only `w = 250` on
  record, a `verdict` hard-coded to `SIGN_REVERSED` passed every measurement
  test in the file. Two recorded walks that disagree kill that implementation.
- 🟢 No second suite: the `loop_reach` / `citation_audit` guards that cost
  D-148 and D-149 an extra 15 min were run as a targeted subset first, green.

## North-star delta

- The mechanism's **strongest** piece of evidence held up under the protocol
  that just overturned its weakest. `risk_mppi` is the safer arm at `w = 150`
  on 32 seeds, 1/32 vs 15/32 sub-margin, all 32 runs reaching goal.
- No new safety/tracking dynamics: headline stays `unsafe_rate` 0.0000 /
  `min_clearance` 0.3579 / `success_rate` 1.0000 over 5 cells / 40 seeds.
- Calibrated coverage unchanged (60 arm-cells, 5 weights). Bought seeds again,
  not weights — replication coverage 1/4 → **2/4** of the band's separated rungs.

## Key learnings

- **A replication programme needs a denominator, not a headline.** After one
  rung the honest summary was a sentence; after two it is a *rate*, and the
  rate (2/4 covered, 1/2 overturned) is a much less comfortable number than
  either individual result. The census should have existed at rung one.
- **`REPRODUCED` is the reading that validates the instrument.** A protocol
  that only ever overturns things is indistinguishable from a broken one. This
  cycle is the control.
- **Sign and size replicate independently** — worth carrying into P5's metric
  set, where effect sizes will be quoted and a 2× seed swing on the same rung
  would silently become a headline number.

## Recommended next 1–3 priorities

1. **Replicate `w = 100`** — the larger of the two unlooked-at rungs and an
   interior rung of the contiguous island, so a reversal there would break the
   island rather than trim it. Same protocol, ~64 runs, ~9 min, no new code.
2. **Fix `shift_census`'s absent-cell path (Q-121)** — unchanged for five
   cycles; needs `shift_census` promoted to a dataclass.
3. **Walk `gap_gated_mppi` at `w = 75`** — first weight contrast for D-146's
   column; widens `COMPARED_ARMS` to three. ~512 runs, ~6 min.

## Artifacts

- PR: #67 (open, continued per D-140)
- Files touched: `eval/mppi_sandbox/separation_reproduction.py`,
  `eval/mppi_sandbox/tests/test_separation_reproduction.py`,
  `docs/decisions.md`
- TSV row appended: yes
