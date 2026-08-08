# The field only the reader knew

- **Cycle**: 2026-08-08 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-key `lam_windows.yaml` by weight (Q-116 (a))
- **Phase**: P5
- **Status**: keep

## What I tried

- Gave `calibrate_lam` the write half of a contract that had only ever had a
  read half: `--w-obs-soft` walks every ladder at a chosen obstacle weight and
  `to_yaml` emits the `calibration_weight:` key that `lam_window_key._rows` has
  been reading since D-134.
- Threaded the weight down the one path that could not carry it:
  `ab.lam_ladder` owns the `params=` slot (`MPPIParams(lam=...)`), so
  `w_obs_soft` was unreachable through `arm_kwargs` — the mechanical reason the
  table was measurable at exactly one weight.
- Carried the weight **on** `SceneCalibration` rather than beside it, so
  `to_yaml` reads it off the cells; added the two refusals that keeps honest
  (`to_yaml` on mixed-weight cells, `refine` merging rungs from another weight).
- Left the shipped `lam_windows.yaml` **unkeyed**, with a test that fails if
  anyone stamps it by hand.

## What worked / what failed

- 🟢 **The round trip had never been tested, and that is the finding.** `_rows`
  read `calibration_weight:`; nothing wrote one; the only table either side ever
  saw was the shipped one that has no such key. Had the writer emitted
  `calibrated_at:`, every lookup would still have graded `UNKEYED` and no test
  would have failed. Twelve new tests, and the load-bearing three are
  write→read: `ON_KEY` at the written weight, `OFF_KEY` at any other,
  `measured_at` preserved across the refusal.
- 🟢 **`ON_KEY` is now reachable at all.** Before this cycle every call graded
  `UNKEYED` and no sequence of actions could change that — the guard's own
  docstring named `calibrate_lam` as the missing writer and the writer did not
  exist. D-044 already booked what happens to a check nobody can clear.
- 🔴 **But nothing is keyed yet, and the headline must not overstate it.** The
  shipped table still grades `UNKEYED` for every caller. Keying it means
  *re-running* ~500 closed-loop runs, not editing a header; a 2-seed shortcut is
  exactly what D-134 caught reading risk/crossing as `{0.4, 0.8}` where 16 seeds
  give `{0.8}`. This cycle shipped the means, not the measurement.
- 🟢 Two provenance comments went stale the moment the flag landed and were
  fixed in the same commit: `CALIBRATION_WEIGHT`'s justification ("`calibrate_lam`
  … overrides nothing else") had become false, and the module docstring's "the
  table stays as generated" needed the D-138 amendment.
- 🟢 12 new tests pass in 0.06 s, 58 adjacent lam tests unchanged. No sim: the
  threading claim is about plumbing and is asserted on the `MPPIParams` handed
  to `seed_sweep`, which is the whole of what it means.

## North-star delta

- No new dynamics measured — the headline stands where D-136 left it
  (`unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000, 5 cells
  / 40 seeds, audited population 6 not 8).
- Movement is in what a *future* measurement can claim: the project's λ windows
  can now be recorded against the weight they were measured at, so a ladder walk
  at `w = 150` stops silently borrowing a window measured at `w = 10`. D-134
  showed that borrowing is not hypothetical — crossing/risk moves `[1.6, 3.2]`
  → `{0.8}` across that gap.

## Key learnings

- **A field with a reader and no writer is not a half-built feature, it is an
  untested contract.** Both sides can be self-consistent, documented, and
  covered by tests, and still never have agreed on a spelling. The cheap test is
  the round trip, and it is worth writing the day the reader lands rather than
  the day the writer does.
- **A parameter that cannot be passed is a measurement that cannot be taken.**
  `lam_windows.yaml` looked like a table someone had chosen not to re-key; it was
  a table nobody *could* re-key, because the one function that builds the params
  object owned the slot. The scope of a result was set by a keyword-argument
  collision.
- **Shipping a guard obliges shipping the means to satisfy it** (D-044/D-129,
  third sighting). Q-116 chose (b) guard-first deliberately and said (a) was
  what made it schedulable; the debt came due one cycle later than the guard.

## Recommended next 1–3 priorities

1. **Regenerate one scene's row at `w = 100` and `w = 150`** via
   `calibrate_lam --w-obs-soft --out eval/scenarios/variants/` — head_on, whose
   window D-135 already re-measured by hand, so the generated table can be
   checked against a known answer before any consumer trusts it.
2. **Give `SEPARATED` a resolution floor (Q-115)** — still open; every rung of
   D-136's ladder graded `SEPARATED` including λ = 1.6 where both arms are out of
   band.
3. **A third scene in the registry** at `w = 100` *or* `w = 150`, never a fresh
   weight, so it adds a contrast rather than only a census row.

## Artifacts
- PR: #67 (already open — no new review bandwidth; gate 1 at cap)
- Files touched: `eval/mppi_sandbox/ab.py`, `eval/mppi_sandbox/calibrate_lam.py`, `eval/mppi_sandbox/lam_window_key.py`, `eval/mppi_sandbox/tests/test_lam_window_keying.py`, `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
