# The undeclared clearance bar is the cheaper repair — and the only one checked against seeds

- **Cycle**: 2026-08-19 16:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c1c5d39` cafe_freezing_v0 의 UNDECLARED clearance key 도 같은 placement gap 인가?
- **Phase**: P5
- **Status**: keep

## What I tried

- Took STATE #2 rather than STATE #1. The 8-seed widening (#1) needs 256 rollouts
  *plus* a code extension to `excursion_tracking.measure()`, and
  `cycle_wallclock elapsed` gave 7m23 to reach the suite deadline — not feasible.
  #2 is zero-rollout: `cafe_freezing_v0` is `clearance_census.PEAK_SCENE`, so its
  harvest is already the full 8×8 `SEED_ENSEMBLE`.
- New `eval/mppi_sandbox/declaration_gap.py` + 16 tests: per-seed attained range
  across arms, the intersection of those ranges, and the ranking against
  `spread_generality.CENSUS`.

## What worked / what failed

- **The scene is a `DECLARATION_GAP`, not an ungradeable one.** Seed-0 arm spread
  is `0.4537 m` — `1.29x` the widest *graded* clearance scene (`cafe_cut_in_v0`,
  `0.3512`) and `2.31x` D-365's vacuous `cafe_head_on_v0` (`0.1964`). Nothing here
  fails for lack of dispersion.
- **The seed-robust window is `(0.3359, 0.7713)`, width `0.4354 m`.** Any bar
  strictly inside it cuts the arm population on **all eight** seeds — checked
  directly per seed, not inferred from the interval arithmetic.
- **The ordering STATE carried is inverted.** `head_on` needs a constant *moved*
  into a `0.1964 m` interval read off **one** seed; `freezing` needs one *added*,
  the interval is `2.2x` wider, and it is verified on eight. STATE ranked the
  harder repair first.
- **Bonus, and it is the first payment on the standing seed debt.** Per-seed
  spread runs `0.4390`–`0.4989`: a `0.0599 m` swing, **13.2 %** of the statistic's
  own value, and the *narrowest* seed still out-spreads every scene in
  `spread_generality.CENSUS`. Arm spread is not a seed-noise artefact — on this
  scene. `SEED_SCOPE` stays pinned: it is about four other scenes.
- `inert_surface staged` returned `STAGED_MOVED` (5 pins) — the known D-207 price
  for adding a test file, paid rather than re-probed (`reprobe` is self-blocked,
  Q-091).

## North-star delta

- 물체회피 column: the branch's most-measured scene moves from "no criterion" to
  "criterion absent, and here is the eight-seed-verified interval it may be drawn
  from". The value stays scene intent (user-blocked) — the *interval* did not.
- Zero rollouts. No new controller behaviour; this is grading-surface work.

## Key learnings

- **The scene with the most data was the one with no grading at all.** Worth a
  standing check: where a branch has spent its rollouts and where it has spent
  its criteria are different questions, and they had fully diverged here.
- **"Same class as D-365" was the wrong frame, and asking it was still right.**
  The TODO asked whether this is the same placement failure; it is the same
  *repairable* family but a strictly easier member, and only the arithmetic
  showed the ordering.
- **A single 8-seed ensemble bought a partial answer to a question scoped at
  four scenes.** The seed-stability of spread was assumed unanswerable without
  256 rollouts; one scene's existing harvest answers it for that scene at zero cost.

## Recommended next 1–3 priorities

1. **STATE #1 unchanged and now better motivated** — 8 seeds on the four excited
   scenes. This cycle shows the spread statistic *survives* seeds on the one scene
   that can say so; the other four are still seed-0.
2. **Declare `min_distance_to_obstacle` on `cafe_freezing_v0`** — user-blocked
   (value is scene intent), but the interval is now measured and seed-verified.
   Cheaper than STATE's current user-blocked #1.
3. **Check whether `cafe_head_on_v0`'s `0.1964` interval survives seeds** before
   the move is made — its target range is seed-0 only, so a repair could land
   outside what the other seven attain.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/declaration_gap.py, eval/mppi_sandbox/tests/test_declaration_gap.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
