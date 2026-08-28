# The tracking record does not survive its own arrival gate — 3/4 → 2/3

- **Cycle**: 2026-08-29 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Re-derive `class_contract`'s tracking record with the unfinished cells dropped
- **Phase**: P5
- **Status**: keep

## What I tried

- Discharged a **strand** first (REVIEW Step 0, D-112): the 21:00 cycle's three
  commits were finished on disk and never reached `origin`. Pushed them; the
  receipt at `95d4c17` was already green (D-315 probe), so no suite was re-bought.
- Took STATE's bottleneck: D-487's `tracking_ranking_record` (`essps_mppi 3/4`)
  was computed over a column containing a run that never arrived.
- Implemented the gate **in `class_contract`**, not `axis_purchase` — the latter
  explicitly declined to re-derive the record on the grounds that the contract is
  `class_contract`'s to state and splitting it would put one claim in two modules.
- Cut cells by *absence* rather than by ranking them last, and checked the cut
  against **both** classes rather than only the one it was expected to move.

## What worked / what failed

- **The 3/4 does not survive: the honest figure is `essps_mppi` 2/3.** The
  forfeited scene is `cafe_obstacle_crossing_v0`, which was one of its three
  wins. Both halves of the fraction move — the arm is *ineligible* there, not
  beaten, so the denominator drops too.
- **The plurality nearly vanishes.** Ungated the ranking tally is 3-1; gated it
  is **2-1-1**, the forfeited win transferring to `social_mppi`. D-487's
  `NO_FRONTIER_SINGLETON` refusal is now a record argument as well as a
  frontier-width one.
- **The obstacle line survives the same cut** — `cbf_mppi` still wins all five
  outright once `essps_mppi` leaves the column. This was the direction I did not
  expect to move and is the reason it was checked.
- **A real design bug, caught by my own tamper tests.** The first cut computed
  the gated record over *gated* ranking scenes, so the denominator shrank twice
  — once for arrival and once because removing an arm dropped a column below the
  ranking bar. Two failing synthetic cases exposed it; the fix pools over the
  **ungated** ranking scenes and reports resolution loss separately
  (`gate_preserves_resolution`). Live, resolution is preserved (7→6, 6→5).
- `census_preempt` paid for itself again: `guard_tally` 155→158 and one
  unrecorded `loop_reach` row, caught in ~2 s at the stage rather than 13 min
  into a red suite. **Thirteenth consecutive cycle.**

## North-star delta

- **P5's 경로추종 reportable number got smaller and more honest** — the second
  consecutive cycle where buying a measurement *shrank* a claim rather than
  growing one (D-488 did the same to the 물체회피 line's unconditionality).
- No new controller / representation / dynamics code. This is a correctness pass
  over an existing claim, not new capability.

## Key learnings

- **A census bought for one purpose re-grades another.** `time_to_goal` was
  bought to score an axis; its first real use is as an *arrival gate* on a
  different axis's record. Cheap columns keep paying out sideways.
- **Coverage totality is a coincidence, and it already fails once.** The tracking
  gate is 4/4 only because that class's ranking scenes happen to equal the joint
  surface; the obstacle class owns a scene outside it and is **4/5**. Pinned as
  two separate fractions so no future cycle quotes one for both.
- **A guard can enter the pool by changing shape, not by being new.** `columns`
  joined `guard_reflexivity` because it grew a `gated` branch. A +3 tally with
  only two new `def`s is not an error — a name-diff between cycles cannot see
  this direction, which cost me a stash/diff round-trip to establish.
- **`gate_preserves_resolution` exists because the honest fix needed it.** Had I
  not separated the two causes, the record would have read 2/2 and looked
  *stronger* than the truth.

## Recommended next 1–3 priorities

1. **Decide whether `CLASS_AXIS` should instrument 경로추종 with all four
   `CLAUDE.md` clauses** — smoothness and `time_to_goal` columns both exist now,
   and D-488 deliberately left this open rather than smuggling it into one cycle.
2. **Widen `axis_purchase` to 8 seeds** (`WIDENING_UNBOUGHT = 224` rollouts, ~7
   min measured) — every finding on this branch, including this one, is seed 0.
3. **Close `census_preempt`'s guard-pin gap** — unchanged, and it fired again.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/class_contract.py, eval/mppi_sandbox/tests/test_class_contract.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, eval/mppi_sandbox/loop_reach.py, docs/decisions.md
- TSV row appended: yes
