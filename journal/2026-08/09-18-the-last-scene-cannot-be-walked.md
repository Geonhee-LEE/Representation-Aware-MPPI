# The last eligible scene cannot be walked — and only convoy's margin is mis-declared

- **Cycle**: 2026-08-09 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — walk `cafe_obstacle_crossing_v0`, both arms, at margin 0.30
- **Phase**: P5
- **Status**: keep

## What I tried

- Ran `scene_transplant`'s screen on `cafe_obstacle_crossing_v0` **before** the
  planned 64-run walk, as STATE instructed. The screen refused the walk: **0 of
  4** rungs transplant, so the cycle spent zero simulation runs.
- Split the refusal, because crossing's is not convoy's: added
  `NO_ADMISSIBLE_LAM` for an arm whose admissible λ window is **empty**, beside
  the existing `LAM_NOT_ADMISSIBLE` for a non-empty window that merely excludes
  the reference λ.
- Answered STATE's standing hypothesis instead — *are the declared margins the
  instrument at fault?* — with `margin_placement`, a pure-computation census
  over the 5 rungs this repo has actually walked.

## What worked / what failed

- **Crossing is unwalkable at the band's protocol, 0/4.** At `w = 75` the stock
  arm is calibrated at λ = 4.5255 while `risk_mppi` has **no admissible λ at
  all**; at `w = 100` both arms are empty; `w ∈ {150, 250}` have no cell. The
  walkable-scene population is **2, not 3** — D-159's denominator narrows once
  more, and this time it is closed by calibration, not by any controller.
- **The screen was worth more than the walk.** STATE budgeted ~64 runs; the
  answer cost none and is stronger than a measurement would have been — a run
  at λ = 0.8 here would have produced a number `assert_ess_in_band` refuses.
- **STATE's margin hypothesis is half wrong, and the wrong half is the band's.**
  It predicted that no scene's declared margin sits inside its own clearance
  distribution. True of convoy (0.30 m against [0.8914, 1.2066], every run
  clearing by ≥ 0.59 m → `MISPLACED`). **False of head_on**: 0.40 m is interior
  to both arms at `w ∈ {150, 250}` and interior to the risk arm at all four
  rungs. The acceptance yaml is the finding for *one* scene, not for the census.
- **The two answers disagree because they are asked at different scopes.** The
  2/5 "well placed" rungs are interior when the 32 seeds are **pooled** and
  censored in **every** 16-seed block — block-scope coverage is **0/5**. Pooling
  manufactures an interior range that neither half has, and that gap is exactly
  D-157's 2/4-vs-0/4 delta seen from the margin side.
- **`NO_ADMISSIBLE_LAM` sits ahead of `LAM_NOT_ADMISSIBLE` in the same branch**,
  so it could have silently re-graded D-160's published 1/4. A regression test
  pins convoy's screen at `PARTIAL_TRANSPLANT` 1/4; it did not move.

## North-star delta

- No movement on the headline: no controller or representation code, no sim
  runs. `unsafe_rate` **0.0000** / `min_clearance` **0.3579** / `success_rate`
  **1.0000** unchanged.
- The successor question's population is now fully enumerated and **closed**:
  of 8 matrix scenes, 3 eligible, 2 walkable, 0 two-sided. Every route from the
  published band to a second scene at the band's own λ is accounted for.
- One diagnosis retired: "the declared margins are the instrument" is now a
  convoy-local fact rather than the census-wide explanation STATE carried.

## Key learnings

- **Screen the population before measuring the property** — third cycle running
  (D-159 scenes, D-160 rungs, D-161 the last scene's rungs), and the third time
  the screen was cheaper than the measurement and changed what it could mean.
  This is now the default first move, not a precaution.
- **An empty window and a wrong-valued window are different refusals.** One can
  be bought back by giving up a shared constant; the other offers nothing to
  give up. A `blocked` count that merges them loses the recoverable half.
- **Interiority is scope-dependent and the flattering scope is the pooled one.**
  Any future "is this margin well declared" reading must state whether it pools
  the blocks, because the honest answer (0/5) and the flattering one (2/5) come
  from the same clearances.
- The band's `w ∈ {75, 100}` censoring is a **ceiling on the stock arm**
  (`BELOW_ALL`), not a mis-declared margin — so D-158's "the effect is large"
  reading survives contact with the margin question.

## Recommended next 1–3 priorities

1. **Ask what a two-sided rung would require, given the census is closed.**
   Every recorded rung is block-censored; the options are a scene whose margin
   is interior per block, more seeds per block, or an operating point between
   the band's rungs. Pure computation from the existing 5 walks can price which.
2. **Re-calibrate `cafe_obstacle_crossing_v0` at a weight where an arm has a
   non-empty window** — the only route that reopens the third scene, and the
   screen already names `w ∈ {150, 250}` as unmeasured rather than empty.
3. **Carry "unmeasured" in the strand verdict (D-156 follow-up)** — deferred a
   fifth cycle; one field, one test.

## Artifacts

- PR: [#67](https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/67) (open, continued per D-140)
- Files touched: `eval/mppi_sandbox/scene_transplant.py`, `eval/mppi_sandbox/margin_placement.py`, `eval/mppi_sandbox/tests/test_scene_transplant.py`, `eval/mppi_sandbox/tests/test_margin_placement.py`
- TSV row appended: yes
