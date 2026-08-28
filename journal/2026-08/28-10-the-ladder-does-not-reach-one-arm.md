# The ladder does not reach one arm

- **Cycle**: 2026-08-28 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — Probe the `essps_mppi` λ=0.1 pattern
- **Phase**: P5
- **Status**: keep

## What I tried

- STATE's bottleneck, five cycles old: `SHIPPED_LAM = 0.1` is admissible in
  exactly 8 of 72 cells, all `essps_mppi`, one per scene. The proposed cut was
  to read the 8 windows and classify `0.1` as **window-edge** (a calibration
  boundary effect) or **window-interior** (a property of the arm).
- Read the 8 cells out of `lam_windows.yaml` — no rollout, one `windows()` call.
- Followed the read into the controller and measured the mechanism directly.
- Shipped `lam_inertness.py` + 22 tests; repaired the 4 censuses it moved.

## What worked / what failed

- **Both offered options are refuted, and by the first read.** All 8 windows are
  the *entire* ladder (`0.05 … 6.4`, 8 of 8 rungs). There is no edge on the
  ladder, so `0.1` is neither at one nor inside one.
- **The mechanism is not a calibration fact.** `ESSPSMPPI._softmax_lam` solves
  the temperature per step (D-325) and reads `self.p.lam` only on a fallback its
  own docstring calls unreachable. Measured, same cost vector through the same
  method: `essps_mppi` returns **4.571501 at both `lam=0.05` and `lam=6.4`**;
  the other seven arms return the passed value verbatim. 128x of input, zero
  output movement — the arm does not read the axis being swept.
- **So "8 cells admit 0.1" is not a fact about `0.1`.** `0.05` has the identical
  support — the same 8 cells — and so does every rung. The 8 counts the scenes
  `essps_mppi` completes, and the missing 9th is `cafe_cut_in_v0`, which D-483
  proved geometrically uncompletable. The two derivations agree without being
  wired to each other.
- **It corrects a shipped table.** `operating_point.ladder_census` counts the 8
  inert cells at every rung, over-stating responsive support by exactly 8
  everywhere: its `0.2 -> 42 cells` is **34** responsive.
- **`census_preempt` earned its place again** — 4 drifts (`guard_tally` 145→147,
  3 unrecorded `loop_reach` rows, `lam_site_census` 106→107,
  `liveness_partition` 25→27) caught in ~2 s at the stage instead of ~10 min of
  red suite.

## North-star delta

- **A P5 baseline candidate is disqualified on measurement.** `essps_mppi` is
  the only arm admissible at the repo's shipped default, which reads as the safe
  baseline until you know why. Its temperature-robustness is an artifact of
  non-response, and D-325 already priced its real cost: perfect band compliance
  bought with **1.37x** the steps to the same endpoint. Time-to-goal is a
  north-star metric; band compliance is not.
- No planner movement and no new rollout — the plant's usable band still peaks
  at `0.4` and the correction shifts no conclusion about it. That is precisely
  why the defect survived five cycles.

## Key learnings

- **A swept parameter that reaches nothing produces a saturated window, and
  saturation reads exactly like robustness.** The failure mode is invisible to
  the calibration table by construction: the table records which rungs worked,
  and every rung "works" when the arm was never at any of them.
- **The census's conclusions were right while its numbers were inflated.** No
  test could go red, because nothing the number decided was wrong. Defects that
  change no decision are the ones that live longest.
- **Deriving an exemption by running the plant is better evidence and worse
  input.** The two new guards exempt against `inert_arms(scene)` — a measured
  set — and still score `NO_REGISTRY`. That grade tracks whether an exemption is
  *static*, not whether it is *principled*; Q-069's axis is misnamed.

## Recommended next 1–3 priorities

1. **Choose P5's baseline controller explicitly** — the decision P5 entry forces
   (6 days out) and which no cycle has taken. One arm is now disqualified on
   record, which narrows it rather than settling it.
2. **Q-209** — whether `calibrate_lam` should grade inert arms `LAM_INERT`
   rather than record a vacuous window. Leaning (b) but *after* P5 entry;
   the cheap mitigation is one comment line in `lam_windows.yaml`.
3. **Sweep the remaining consumers of the 72** (STATE #2, unmoved) — confirms
   nothing else quotes 72 as an admission gap, closing D-483 rather than
   leaving it half-applied.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/lam_inertness.py, eval/mppi_sandbox/tests/test_lam_inertness.py, eval/mppi_sandbox/loop_reach.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, eval/mppi_sandbox/tests/test_liveness_derivation.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: yes
