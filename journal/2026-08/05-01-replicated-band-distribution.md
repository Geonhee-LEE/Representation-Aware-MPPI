# Q-077 bought: k=3 per frame, and the zero threshold turns out to be unreachable rather than strict

- **Cycle**: 2026-08-05 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — replace the zero-movement threshold with a band estimated from k pairs per frame
- **Phase**: P4 (instrument lane; the branch is P3)
- **Status**: keep

## What I tried

- Generalised D-070's four-run batch to **k runs per frame**: `predicate_inputs.Spread`
  / `spread` / `fold_spread` / `spread_band`, and `exclusion_scope.replicated_reading`
  (2k concurrent runs, every one `_stamped` on both sides).
- Took Q-077's **(a)-side** branch deliberately: hold `FOLD_IMPLICATED` at *exactly
  zero movement* and make it **harder to meet** (stationary across k runs, not 2)
  rather than widening the threshold to a band. Widening needs a constant, and an
  unjustified constant is the defect this package already carries four of.
- Added `ReplicatedReading.fragile` — `(site, verdict at k=2, verdict at k)` wherever
  replication moved a grade. That is Q-077's coin-flip **priced** instead of argued.
- Ran it: **k=3, 6 concurrent runs, 435 s**, tree `9338e10e…`, licensed.

## What worked / what failed

- ✅ **Licensed on the first try**: all 12 stamps agree, `work_repeated` True in the
  exclusion frame. The batch is 50 % bigger than D-070's and still held one tree.
- 🔴 **`fragile` is empty — and it is empty for the wrong reason.** No verdict moved
  between k=2 and k=3 because **nothing was stationary at k=2 either**: all 7 sites
  grade `DRIFT_UNDERSHOOTS` in both readings. The knife-edge existed; this batch
  never put a foot on it.
- 🔴 **The real finding is that the threshold is now unreachable, not strict.** At
  k=3 no site repeats exactly in *either* frame, so `FOLD_IMPLICATED` cannot be
  earned at all. Making a zero threshold harder to meet does not make it more
  informative — past some k it makes the grade dead. That kills my own chosen
  branch of Q-077 as cleanly as the band branch was killed by needing a constant.
- 🔴 **The band is not a property of the measurement — it is a property of which
  pair you drew.** Three pairs of the *same* exclusion frame, same tree, same batch:
  **0.519 % / 0.068 % / 0.487 %**, a **7.7×** range. Source frame: 0.356 % / 0.259 %
  / 0.098 %, **3.7×**. D-070 reported a single 0.106 % and D-066 charged its
  reconstruction 0.487 % — that reconstruction band sits *inside* the range a pure
  control pair produces.
- 🔴 **Fourth tree, fourth magnitude set.** `_pure` 142 → 196 → 175 → **214**;
  `_has_git_diff_literal` 95 → 29 → 30 → **65**; `_is_set_valued` 12 → 20 → 15 → **13**.
- ⚠️ The controls grew with them: `_pure` exclusion frame moved **87** (was 13),
  `_numeric` **47** (was 5). Still undershooting every gap, but the noise budget is
  ~6× D-070's and the "13× undershoot" argument from last cycle does not survive at
  this batch.
- ⚠️ **Eighteenth self-entry**: predicate population 71 → **74**.

## North-star delta

- **No avoidance or tracking number moved — thirty-ninth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4, unchanged.
- What moved: the band every reading since D-066 has been quoted against is now known
  to have a **7.7× spread within one frame on one tree**, so five cycles of magnitude
  arguments were conducted against a number with an unstated error bar of that size.
- What moved against the story: this cycle spent 435 s of compute to retire *both*
  branches of Q-077 and put nothing in their place.

## Key learnings

- **A threshold that gets harder to meet with more evidence is not a stricter test —
  it is a test that stops firing.** The intuition "replication strengthens a zero"
  is right about the *claim* and wrong about the *grade*: P(exact repeat) falls with
  k, so the grade converges to never-issued regardless of whether the fold is guilty.
- **One pair is not one sample of the band, it is one sample of a 7.7×-wide
  distribution.** Q-077's lean — "estimate the band from a batch, then pick a
  threshold" — is now measurably unbuyable at k=3: the estimate's own spread is
  larger than the differences the threshold would adjudicate.
- **`fragile` being empty is a null with a mechanism, and reporting the mechanism is
  the whole value.** "No verdict changed" would have read as robustness; "no verdict
  changed because no verdict was reachable" is the opposite.
- What would change my mind: a grade defined on the *gap-to-control ratio* rather
  than on stationarity — every site here undershoots, but by ratios spanning 2.5×
  (`_pure`: 214 vs 87) to 13× (`_is_set_valued`: 13 vs 1), and that ordering has
  now reproduced on four trees while the magnitudes have not.

## Recommended next 1–3 priorities

1. **Replace stationarity with a ratio statistic.** Grade `gap / max(frame movement)`
   and report the distribution, not a class — the one quantity that reproduced across
   four trees when nothing else did.
2. **Persist the disagreeing set + per-tree magnitudes as `results/*.json`.** Fifth
   cycle in a row whose headline is a set the record cannot check.
3. **Explain why the observed-site count sits at 50** while the population went
   64 → 70 → 71 → **74**.

## Artifacts

- PR: #67 (existing; 66th consecutive cycle, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/predicate_inputs.py`,
  `eval/mppi_sandbox/exclusion_scope.py`,
  `eval/mppi_sandbox/tests/test_exclusion_scope.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
