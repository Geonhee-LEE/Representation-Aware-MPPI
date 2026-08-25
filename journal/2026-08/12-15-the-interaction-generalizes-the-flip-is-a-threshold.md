# The interaction generalizes; the sign flip is a threshold

- **Cycle**: 2026-08-12 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — walk the full `w_risk` × `w_ped` 2×2 on all three eligible scenes
- **Phase**: P5 (calendar) · work is P3-line
- **Status**: in_progress (measurement complete; push refused on a red suite)

## What I tried

- Promoted `risk_interaction()` from one scene to all three eligible scenes
  (`risk_interaction_matrix`), 6 paired seeds, `lam = 0.8` — D-218 measured the
  2×2 on `cafe_obstacle_crossing_v0` only and booked "PGIF is an interaction,
  not a main effect" from it. One scene cannot separate a property of the term
  from a property of the scene, which is precisely the error D-218 caught D-217
  making one denomination up.
- Added a verdict vocabulary for a 2×2 (`interaction_verdict`): `SIGN_FLIP` /
  `CONDITIONAL` / `MAIN_EFFECT` / `INERT`, with `BOUGHT_WITH_FREEZE` checked
  **first** so a frozen cell cannot report clearance.
- Re-read every verdict at four thresholds (`verdict_ladder`) instead of
  trusting the module's float-noise `EPS_CLEARANCE`.

## What worked / what failed

- 🟢 **All three scenes read `SIGN_FLIP`, and completion held 6/6 in all 24
  cells** — so no cell's clearance was bought by freezing and every number is
  readable. `w_ped` step per row (worst-case clearance, m):

  | scene | `w_risk = 40` | `w_risk = 0` |
  |---|---|---|
  | `cafe_obstacle_crossing_v0` | **+0.3756** | −0.0192 |
  | `cafe_convoy_v0` | **+0.1968** | −0.0055 |
  | `cafe_head_on_v0` | **+0.0806** | −0.0002 |

  D-218's crossing-scene numbers reproduced exactly (+0.3756 vs +0.3755 —
  rounding), so this is an extension, not a re-measurement.
- 🔴 **The verdict was partly naming the threshold, not the measurement.**
  `EPS_CLEARANCE = 1e-6` is a float-noise guard, so a **−0.0002 m** step — a
  fifth of a millimetre — counts as "the term harms alone". Re-read at 5 cm all
  three scenes are `CONDITIONAL` instead: the term is *silent* alone, not
  harmful. Had I reported the ladder's top rung only, the headline would have
  been "the flip generalizes to all three scenes" and it would have been an
  artifact of the guard constant.
- 🟢 What **does** survive every threshold is that no scene reads `MAIN_EFFECT`
  or `INERT`. `is_interaction()` pins that conjunction, and it is the claim the
  walk actually licenses.

- 🔴 **The cycle does not push: the suite is red at 2 failed / 2633 passed and
  the gate refuses.** Both failures are the census family — adding functions to
  this package enters the registries the package audits, for the *n*-th
  consecutive cycle. The first suite reported **5**; removing a module-level
  allow-list (`INTERACTION_VERDICTS`, an unwatched population) cleared three of
  them honestly, since the predicate reads the same as the complement of
  `MAIN_EFFECT`/`INERT`. The remaining two want `step_bought_with_freeze`'s
  `and`-shaped guard registered in two pinned tallies.
- 🔴 **I stopped rather than pin those two by hand.** The tallies encode a
  running count derived across ~20 prior decisions, and I am past the suite
  deadline (`SUITE_UNAFFORDABLE` at 30m), so any edit would ship unverified —
  which is the "fix the numbers until green" move this branch's 10:00 journal
  explicitly forbade. Diagnosis is recorded instead; the fix is one suite away.

## North-star delta

- **The branch's most recent capability claim is now a 3-scene result rather
  than a 1-scene one.** "PGIF's predicted-geometry field needs the BEV risk
  term" holds on every eligible scene, at every threshold tested.
- **D-218's stronger half is now bounded.** "The risk term alone *costs*
  worst-case clearance" is real on the crossing scene (~2 cm) and is
  sub-millimetre on the other two — it is a crossing-scene property, not a term
  property.
- Zero freezing tax across 24 cells at these densities, extending D-218's
  36-of-36 completion reading.

## Key learnings

- **A verdict that reads one threshold reports the threshold.** The 2×2 grader
  inherited `EPS_CLEARANCE` because it lived in the module; nothing about that
  constant makes it a *physical* scale, and the difference between "harms
  alone" and "silent alone" turned entirely on it. Any future verdict of this
  shape should ship its ladder, not its point reading.
- **Generalizing a claim can strengthen and weaken it at once.** The scene axis
  confirmed the interaction and refuted the flip's physical reading in the same
  table. Reporting only the confirmation would have been the D-217 error again,
  one level up.
- The measurement was ~4 min of compute for three scenes; the reason it had not
  been done is that `risk_interaction()` took a `scene` argument nobody looped
  over. Cheap generalizations sit behind existing parameters more often than
  behind new code.

## Recommended next 1–3 priorities

1. **Register `three_arm.step_bought_with_freeze` in the two `&`-shaped guard
   tallies and push this branch** — the work is committed and verified
   (`tree_provenance verify` clean at `57c35f7`); only the census pins are
   outstanding. This is the whole of next cycle's first move.
2. **Scale-match the arms, or state that the head-to-head cannot rank them.**
   `w_epist = 200` / `w_geom = 40` / `w_ped = 50` enter different summands with
   different units; `geometric`'s clean sweep may be a volume setting.
3. **Re-read the `geometric` null's three-scene win through the same eps
   ladder** — it is the arm that won everywhere and the only one no test covers.
4. Fix `inert_surface`'s `STAGED_MOVED` message to name what it measured
   (carried, unchanged, third cycle).

## Artifacts

- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, #67)
- Files touched: `eval/mppi_sandbox/three_arm.py`,
  `eval/mppi_sandbox/tests/test_three_arm.py`, `docs/decisions.md`
- TSV row appended: yes (2 rows — the measurement, then an in_progress corrective)
