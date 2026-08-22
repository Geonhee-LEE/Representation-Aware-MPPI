# The n=16 ensemble: knee+shape clears the gate without buying a detour

- **Cycle**: 2026-08-22 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — 16-seed ensemble, knee+shape arm, reporting the mode split
- **Phase**: P5
- **Status**: in_progress

## What I tried

- **Cleared the strand first (D-112).** `cycle_artifacts stranded` named `bbdac64`
  (D-429) as finished work that never reached origin; the 20:00 cycle had been
  refused by `push_preflight` (`SCOPED: 0/3 declared targets named`) and ran out of
  budget. This cycle's push carries both commits.
- Took STATE #1, which D-429 had already attached a caveat to: widen the knee/shape
  matrix from 5 seeds to 16 **and** report the mode split per arm, so the ensemble's
  power is not spent on a mode-mixture estimand.
- Measured 4 arms × 16 seeds (64 runs, ~40 s) before writing anything, then pinned
  the result in `test_knee_shape_ensemble.py` (6 tests, 34 s).

## What worked / what failed

- **D-427's headline shrinks and does not survive as a marginal effect.** 1/5 → 3/5
  reads as **3/16 → 6/16** at n=16, and Fisher on knee-vs-knee+shape gives
  **p ~ 0.43**. What *is* significant is the pair against base (0/16 vs 6/16,
  **p ~ 0.018**). The honest claim is "knee+shape beats doing nothing", not "shape
  beats knee". The test pins that non-significance on purpose: a future widening
  that crosses 0.05 makes it fail, and that failure is the promote signal.
- **Mode is not a property of a seed.** Detour seeds under `knee` are {0,5,7,11};
  under `knee+shape` they are {2,3,5,6,12,15} — overlap **{5}**, one seed. The shape
  knob does not convert squeeze seeds into detour seeds, it reshuffles them in both
  directions. D-429's `test_seed_zero_is_in_the_smaller_mode` is a knee-arm statement.
- **⭐ The two arms pass by different mechanisms — the real find.** Under `knee`,
  passing seeds {0,5,7} ⊆ detour seeds: you buy clearance with a wide berth, exactly
  D-426's 1:1 trade. Under `knee+shape`, 4 of the 6 passing seeds are **squeeze-mode**
  — they hold the path *and* clear the gate. Compact support makes clearance
  affordable without a detour, and that, not the 6/16, is why the knob is worth keeping.
- **The residual is entirely tracking.** Under the pair, `min_distance_to_obstacle` is
  green **16/16**; every remaining failure is `heading_err_rms_max` (10) or cte (6).

## North-star delta

- First time the two halves of the north star have **separated on this scene**: object
  avoidance is met by knee+shape on 16/16 seeds, and what remains is a heading-smoothness
  problem. The next controller question is a tracking question, not an avoidance one.
- Escapes the 1:1 avoidance↔tracking trade D-426 priced — at least on a majority of the
  passing seeds, and with a named mechanism (compact support) rather than a count.
- Honest deflation: the 3/5 number this branch has been quoting for three cycles was
  optimistic by ~22 points, and the shape knob's marginal contribution is still unproven.

## Key learnings

- Widening an ensemble is as likely to **deflate** a headline as confirm it, and the
  deflation is the cheap part — the value came from the *split* D-429 forced us to report
  alongside the mean, not from the extra seeds.
- Pinning a **non**-result (p > 0.05) is a usable test: it makes the claim's own weakness
  a thing that fails loudly when it stops being true, instead of a caveat that rots in prose.
- "Seed N is a detour seed" was a category error that survived two cycles. The fix was to
  ask the same question of a second arm — cross-arm comparison, not more seeds, exposed it.

## Recommended next 1–3 priorities

1. **Attack `heading_err_rms_max` under knee+shape** — it is now the single dominant
   failing check (10/16) and the only thing between this scene and a green matrix.
2. **Why do 4 of 6 passing seeds squeeze?** Isolate what distinguishes a squeeze-passer
   from a squeeze-failer under the pair; that predicate is the next knob's specification.
3. Widen to n=32 only if (1) and (2) stall — the marginal-effect p is the least
   valuable open number on the branch right now.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_knee_shape_ensemble.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
