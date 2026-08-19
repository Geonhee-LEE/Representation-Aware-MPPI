# The A-A floor is a property of the column, and one scene proves it

- **Cycle**: 2026-08-19 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c1c5d39` cafe_head_on_v0 을 A-A floor 로 calibrate — bar 선언 전에, rollout 0회
- **Phase**: P3
- **Status**: keep

## What I tried

- Picked STATE next-action #1: calibrate `cafe_head_on_v0` against its own A-A
  null floor before the user declares its clearance bar. D-371 left it
  `UNCALIBRATED`, and `STATE.md` held the declaration one cycle for that reason.
- Found the pick was **under-scoped**: D-371 reached for
  `clearance_census.SEED_ENSEMBLE` (one scene) and never for
  `scene_transfer._COLUMNS` beside it, which holds **five** scenes of 8 arms ×
  8 seeds. So calibrating head_on and calibrating four more cost the same
  arithmetic. Widened `CALIBRATED` from 3 cells to 7. **Zero rollouts.**
- Re-keyed the module from `scene` to `(column, scene)`. This was forced, not
  cosmetic: `cafe_convoy_v0` now carries both columns, so the old scene-keyed
  `_ensemble()` would have silently returned its `cte_max` row to a caller
  asking for clearance.
- Fixed two stale `loop_reach.READING` counts (`24 → 56`, `3 → 7`) that the
  widening invalidated.

## What worked / what failed

- **head_on clears, and the hold is discharged**: `0.1781` real gap against a
  `0.0393` p95 floor = **`4.53x`**, above the adversarial max (`0.0433`) too.
  D-368's interval `(0.0043, 0.1044)` cuts a difference this harness can
  resolve — user-blocked #2 is licensed.
- **All five clearance scenes clear, `2.44x`–`6.28x`; both `cte_max` scenes fail
  by both readings.** The two populations do not overlap: worst clearance row
  beats best `cte_max` row by more than 2×.
- **D-371's finding #3 does not survive the widening.** It read the split as
  per-scene ("the obstacle-free scene is the worse one") — the only reading
  available from one row per column. `cafe_convoy_v0` is now calibrated in
  *both* columns, holding scene, arms, operating point and seeds fixed: it
  clears by `5.14x` in clearance and fails at `0.96x` in `cte_max`, **on the
  same eight runs**. The axis is the column.
- `census_preempt` read CLEAN on all 5 censuses while two `READING` integers
  were stale — the D-333 placement gap, third occurrence. Caught by reading the
  comment, not by a tool.
- **Process failure, mine**: I launched the suite via `nohup ... &` inside a
  Bash call and it did not survive; the receipt was empty and ~1 min was lost.
  Worse, launching it there at all inverted D-315's receipt-last order. Recovered
  by doing every REPORT write first and taking the receipt after.

## North-star delta

- **경로추종 unchanged and still ungradeable** — this cycle adds no cross-track
  resolution. `RESOLUTION_DEBT` (512 rollouts) is untouched.
- **물체회피 (clearance) strengthened from one scene to five.** The column that
  actually grades is now demonstrated above its own harness noise on every scene
  it has been measured on, not just on `cafe_freezing_v0`.
- **One user-blocked declaration unblocked** (`cafe_head_on_v0`), on evidence
  rather than on the absence of counter-evidence.

## Key learnings

- **A calibration's scope is set by which registry it reads, not by what it
  costs.** D-371 priced further scenes at 384 rollouts; four of them were free
  and sitting in a dict one import away. The "cheapest action is to read what
  the branch already measured" pattern is now four cycles running.
- **One scene in two columns beats five scenes in one.** The controlled
  comparison did the work that widening alone could not — it is the only row
  that can separate a column effect from a scene effect.
- **A tool reading CLEAN bounds only its own census.** `census_preempt` names
  what it does not cover and it was right to; the stale integers were inside
  that named gap.

## Recommended next 1–3 priorities

1. **Tell the user user-blocked #2 is licensed** — the head_on bar declaration
   was held pending exactly this and can now proceed.
2. **Carry the floor to the sites that state the claim** (`SPREAD_SEPARATES`,
   `SEED_SCOPE`, `excursion_seed_width.VERDICT`) — fifth consecutive cycle to
   name this gap without building it.
3. **Make `READING` integers derivable** so the D-333 placement gap stops being
   caught by eye (Q-171 already open on this).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/aa_calibration.py`,
  `eval/mppi_sandbox/tests/test_aa_calibration.py`,
  `eval/mppi_sandbox/loop_reach.py`
- TSV row appended: pending
