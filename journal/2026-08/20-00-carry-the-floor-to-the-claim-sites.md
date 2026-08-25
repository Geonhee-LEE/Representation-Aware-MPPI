# Carry the A-A floor to the sites that state the claim — and one endpoint survives

- **Cycle**: 2026-08-20 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — carry the floor to the sites that state the claim
- **Phase**: P5
- **Status**: keep

## What I tried

- Built `eval/mppi_sandbox/floor_reach.py`: a registry of the **six** cross-track
  endpoints this branch states (`excursion_tracking.SPREAD_SEPARATES` ×2,
  `excursion_seed_width.ROBUST_SEPARATION` ×2, `INTERSECTION` ×2), each joined to
  the `(column, scene)` whose `aa_calibration` floor bounds it. Zero rollouts —
  both operands were already pinned.
- Made the join **checkable rather than prose**: `carries_bound()` reads each
  claim-site module's source and reports whether it names its bound; `unjoined()`
  is the census and the CLI goes `rc=1` if it grows.
- Added the pointer comments to the two claim-site modules. Textual, not an
  import: `aa_calibration` already reads `excursion_seed_width.SEED_ENSEMBLE`, so
  a floor pin inside the sites would close a cycle.
- 13 tests in `tests/test_floor_reach.py`.

## What worked / what failed

- **Finding #1 — of six endpoints, exactly one clears its own max floor**
  (`SPREAD_SEPARATES[0]`, `2.14x`), and it is a min-vs-max claim's *minimum*
  whose paired maximum is `0.96x`. One endpoint clearing licenses nothing.
- **The two readings disagree, and this is the first place on the branch where
  they do.** `SITE_TALLY` is `(6, 3, 1)`: three endpoints clear the p95 floor,
  one clears the max. On `city_curved_v0` the floors are `0.0472` and `0.0760`
  (`1.61x` apart) and the `0.0730` endpoints sit *between* them — so the verdict
  there is a function of which floor you read. Both are reported; no claim rests
  on the p95 reading alone.
- **Finding #2 — D-370's surviving cross-track result does not survive.**
  `INTERSECTION[cafe_convoy_v0] = +0.0550`, reported as "barrable at seed width
  with a midpoint bar verified to cut all eight seeds", is **`0.82x`** of that
  scene's own max null floor. The bar-cuts-all-seeds verification is sound and
  asks a different question; only the floor bounds the claim.
- **I typed `SITE_TALLY` as `(6, 1, 1)` and the module's own drift check caught
  it** before the suite did — the p95 column was 3, not 1. The derived-pin
  discipline paid for itself inside the same cycle that introduced it.
- `census_preempt` 5/5 CLEAN. `inert_surface staged` returned `STAGED_MOVED`:
  the new test withdrew the exemptions on all five snapshot pins, which made
  D-315's receipt-last ordering mandatory rather than optional this cycle.

## North-star delta

- No metres. The movement is again in what the grading surface may **say**:
  every cross-track number on the branch is now joined in code to the floor that
  bounds it, and 5 of 6 are below it.
- 경로추종 is now measured-unreadable at eight seeds on *every* endpoint it
  states, not merely on the two D-371 checked. 물체회피 is untouched (5/5 above
  floor, D-372).
- The remaining lever is unchanged and is now the only one: `RESOLUTION_DEBT`
  = 512 rollouts for `8 arms × 32 seeds × 2 scenes`, buying a `2.10x` smaller floor.

## Key learnings

- **A pin derived from a function cannot be wrong for longer than one run.** The
  `(6, 1, 1)` slip was mine, was plausible, and was caught in 0.09 s. Every
  typed magnitude on this branch is a slip waiting for a suite to find it.
- **"Unjoined" was a structural fact, not a prose failure.** Before this cycle
  neither claim-site file mentioned `aa_calibration` anywhere in its source — a
  reader arriving at `ROBUST_SEPARATION` had no path to the finding that voids
  it. Five cycles of naming it in `STATE.md` did not change that; one
  `carries_bound()` census does.
- **The p95-vs-max choice has been free until now.** D-371 declared both
  readings and nothing turned on the difference. It does now, so future floor
  claims must name their reading.

## Recommended next 1–3 priorities

1. Spend the 512 rollouts (`RESOLUTION_DEBT`) on the binding pair — the only
   purchase that lowers the floor rather than widening a column already below it.
2. Extend `floor_reach.SITES` to the clearance column so the 5/5-above result is
   carried by the same census, not by D-372's prose.
3. Make `loop_reach.READING` integers derivable (Q-171) — the D-333 placement
   gap, still caught by eye.

## Artifacts

- PR: #67 (open, already queued — push adds +0 review surface)
- Files touched: `eval/mppi_sandbox/floor_reach.py`, `eval/mppi_sandbox/tests/test_floor_reach.py`, `eval/mppi_sandbox/excursion_tracking.py`, `eval/mppi_sandbox/excursion_seed_width.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
