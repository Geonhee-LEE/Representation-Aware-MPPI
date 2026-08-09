# The last rung reproduces — the census closes at 4/4, and full coverage is not agreement

- **Cycle**: 2026-08-09 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — replicate `w = 75` on a disjoint seed block
- **Phase**: P3
- **Status**: keep

## What I tried

- **Cleared the 11:00 strand first** (D-112). `cycle_artifacts stranded` named
  `09-11-the-typed-timestamp-stops-at-the-writer.md`: commit `95f5248` was on
  disk and `origin` had not moved past `26c5227`. Its TSV row was also missing
  — the journal claimed `TSV row appended: yes` and no row on any `results/*`
  file names that commit.
- Walked the published band's `w = 75` rung on `cafe_head_on_v0` (λ = 0.8,
  margin 0.40 m) over **32 seeds** — D-133's block 0–15 re-walked as the
  entitlement check (D-139) plus the fresh disjoint block 16–31, both arms,
  **64 runs**, all reaching goal.
- Recorded `W75_CLEARANCES`, added `w75_reproduction()`, and put the rung into
  `published_census()`. Coverage 3/4 → **4/4**.
- 4 new tests (44 in the file, from 40), including the census flip and a
  magnitude-ordering test the verdict deliberately does not gate.

## What worked / what failed

- 🟢 **The reference block reproduced D-133 exactly** — stock 16/16
  sub-margin, risk **11/16**. Fourth walk in four cycles where the entitlement
  check passed. This one is the strictest of the four: `w = 75` is the only
  rung whose published risk count is neither a boundary nor next to one, so a
  drifted pipeline would have had to land on exactly 11 by luck rather than by
  being pinned at 0 or 16. The other three rungs' checks could not say that.
- 🟢 **The rung reproduced and the island survived intact.** Fresh block: stock
  16/16, risk **8/16** — `SEPARATED`, same direction, and the separation
  *grew* (11/16 → 8/16). Pooled n = 32: stock 32/32, risk 19/32. The
  contiguous separated island `{75, 100, 150}` now has all three rungs walked
  twice and none of them moved.
- 🔴 **`FULLY_REPLICATED` is a statement about the denominator, and it reads
  like a result.** The census now says every separated rung has a second block
  — while `w = 250` is still `overturned`. "The band is fully replicated" and
  "the band replicated" are one word apart and mean different things, and the
  verdict is the field a reader quotes. Pinned `held (75, 100, 150)` /
  `overturned (250,)` as separate assertions in the census test and said so in
  the class docstring; the fields were already separate, but nothing had ever
  *stated* that the verdict must not be collapsed into them, because until this
  cycle the verdict was `PARTIALLY_REPLICATED` and nobody could misread it.
- 🔴 **Three of the four rungs are one-armed tests.** `w = 75` joins `w = 100`
  at `ONE_ARM_CENSORED` with stock at `CEILING` — and it is the *deepest*
  ceiling of the three: the best stock run anywhere in its 32 is **0.3176 m**
  against a 0.40 m margin, versus 0.3705 m at `w = 100`. So the census's 4/4
  covers exactly **one** rung (`w = 150`) where both arms were free to move.
  Coverage of rungs is not coverage of arms, and the two now differ 4/4 vs 1/4.
- 🟡 **The closed census is also the band's weakest rung.** Pooled
  `separation_runs`: `w = 75` **13**, `w = 150` 14, `w = 100` 24. The rung that
  completes the coverage contributes the thinnest separation in the island.
  Reported in its own test, never thresholded — same discipline as
  `one_run_rungs`.

## North-star delta

- **The mechanism's evidence base is now closed at the rung level**: all four
  `SEPARATED` rungs of the published band have a disjoint second block, three
  held, one overturned. That is the strongest form of the safety claim this
  branch has ever been able to state, and it is still one-armed on 3 of 4.
- Headline unchanged — no new controller/representation code, so `unsafe_rate`
  0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000 stand where D-136
  left them.

## Key learnings

- **A verdict that changes meaning when its denominator fills is a verdict that
  needs a docstring before it flips, not after.** `PARTIALLY_REPLICATED` was
  self-describing; `FULLY_REPLICATED` is not, and the moment it became
  reachable was the moment it became misreadable.
- **The entitlement check has a strength, and it is the published count's
  distance from a boundary.** Three of these four checks could have passed a
  drifted pipeline that saturates; only `w = 75`'s could not. Worth knowing
  before trusting the run of four.
- **Coverage closed on one axis exposes the next axis.** Rung coverage is 4/4
  and arm coverage is 1/4. The census answers the question it was built for and
  the censoring field now carries the open risk alone.

## Recommended next 1–3 priorities

1. **A census over `censoring`, not just over rungs** — 3 of 4 replicated rungs
   are one-armed, and nothing aggregates that. `ReplicationCensus` reports
   `held`/`overturned` but is blind to whether a held rung was a two-sided
   test. Smallest useful slice: a `two_sided` property + its own reading.
2. **Fix `shift_census`'s absent-cell path (Q-121)** — unchanged for nine
   cycles; needs `shift_census` promoted to a dataclass so `absent` sits
   outside the grade map.
3. **Audit the TSV `commit` / `status` columns** — D-154 scoped itself to
   `timestamp`; row 1 of this branch's TSV carries a `pending` sentinel in
   `commit`, and this cycle found a *missing* row, which is a fifth-column
   failure the timestamp audit cannot see.

## Artifacts

- PR: #67 (existing — continued under D-140, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/separation_reproduction.py`,
  `eval/mppi_sandbox/tests/test_separation_reproduction.py`,
  `docs/decisions.md`
- TSV row appended: yes (2 rows — the 11:00 strand's missing row + this cycle's)
