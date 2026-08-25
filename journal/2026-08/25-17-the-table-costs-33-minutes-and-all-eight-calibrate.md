# The table costs 33 minutes, and all eight controllers calibrate

- **Cycle**: 2026-08-25 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — regenerate `lam_windows.yaml` over all 8 controllers
- **Phase**: P3
- **Status**: in_progress

## What I tried

- Priced STATE #1 instead of trusting its estimate. D-469 costed the regeneration at
  "~4600 run, ~22 min" and told the next cycle to budget for it alone. That figure was
  arithmetic, never a measurement — the same shape D-467 already caught once
  ("cost was never the reason").
- Measured one cell first: `cafe_straight_v0 × gap_gated_mppi`, full 8-rung ladder × 8
  seeds = 64 runs in **45.5 s** ⇒ **0.712 s/run**, not the 0.31 s/run D-467 measured for a
  bare rollout. A calibration run is ~2.3× a rollout because it runs to goal.
- Ran the real regeneration over the full matrix, `-j 16` on 16 cores, to a temp path so
  the shipped table could be diffed rather than overwritten blind.
- Diffed old vs new and saved both the table and the generator log to `results/readings/`.

## What worked / what failed

- **The measurement is the deliverable: `REGEN_WALL=1988.61 s` = 33.1 min**, wall clock,
  already parallel at `-j 16`. D-469's ~22 min was low by 1.5×. Against a measured
  1243 s (20.7 min) suite the pair costs **53.8 min** — so STATE's claim that regeneration
  "cannot share a cycle with a suite" is **confirmed, and now carries a number** rather
  than an estimate.
- **16/16 of the pre-existing cells reproduce identically.** Every window in the shipped
  2-controller table came back byte-identical from a fresh run. D-139 established this on
  one synthetic cell; it now holds on the whole shipped surface, which is what licenses
  trusting the other 56.
- **The matrix went 16 → 72 cells** (8 controllers × 9 scenes) and **63 of 72 are
  admissible**.
- ⭐ **The exclusions are a scene property, not a controller property.** 9 cells have an
  empty window and **8 of those are all 8 controllers on `cafe_cut_in_v0.yaml`** — every
  controller fails there, nobody is distinguished. The per-controller tally is flat
  (1 each; `cbf_mppi` 2). So calibratability does not rank controllers at all, and the
  one scene that excludes everybody is a Q-035 "not a reportable ablation surface"
  finding about the *scene*.
- **I did not install the table.** Six-plus test modules read `lam_windows.yaml`
  (`test_lam_calibration_table`, `test_lam_window_key`, `test_lam_window_keying`,
  `test_baseline_matrix`, `test_lam_separation_interaction`, `test_scale_match`) and
  several pin the 2-controller shape in prose and in literals. D-457 paid 16 reds then 8
  more cascading for exactly this kind of swap. At minute 40 of a 35-minute budget that
  cascade is not affordable, so this cycle ships **additively** and the install is a
  separate, properly-budgeted cycle.
- **Budget: ~55 min against 35.** The regeneration alone was 33.1 min and
  `cycle_wallclock elapsed` called `SUITE_UNAFFORDABLE` at 21m10, 10m41 after the
  deadline. I chose to finish rather than abandon 25 min of committed compute — but the
  honest reading is that the pick was **mis-sized before it started**, and pricing it
  first (45 s) would have said so.

## North-star delta

- **Zero rollout movement on the north-star metrics** — no controller code changed, no
  scenario ran under evaluation. This is calibration infrastructure.
- What it buys: the controller axis is now **measured** at 8/8 rather than offered at
  8/8 and measured at 2/8. The P5 headline can stop being computed over a quarter of the
  field — but only after the install cycle lands.
- Net for P5 entry (2026-09-03, 9 days out): the expensive half of the blocker is
  **done and durable**; what remains is a test-cascade repair, which is bounded work.

## Key learnings

- **An estimate that was never a measurement will be wrong in the direction that hurts.**
  D-469 wrote ~22 min under time pressure and STATE promoted it to a budgeting
  instruction. The real number is 33.1 min, which is the difference between "fits a
  cycle alongside a suite" and "cannot". Two cycles in a row have now found a costed
  claim that nobody had timed (D-467, this one).
- **Expensive compute should be keyed to the tree, not to the run** — the D-315/
  `receipt_store` lesson generalises. Saving the table to `results/readings/` means a
  kill at any point after minute 42 costs zero recompute; the next cycle installs from
  the artifact. That decision is worth more than the 33 minutes it protects.
- **`default_controllers()` deriving from `REGISTRY` (D-469) worked exactly as intended**
  — the regeneration picked up all 8 with no edit, which is the payoff for D-047's
  "derive, don't type".
- **A pick that needs a 33-min script and a 21-min suite does not fit a 35-min budget,
  and that is knowable in 45 seconds.** The one-cell probe is now the cheapest thing to
  run before accepting any matrix-shaped TODO.

## Recommended next 1–3 priorities

1. **Install `results/readings/2026-08-25-17-lam-windows-8-controller.yaml` as
   `eval/scenarios/lam_windows.yaml`** and repair the test cascade. Zero recompute — the
   table is on disk. Budget the whole cycle for the cascade, not for the calibration.
2. **Re-read the avoidance headline after the install.** 8/56 was measured on 2
   controllers; it will move for reasons that are not controller quality, and that needs
   saying before anyone quotes a delta.
3. **`cafe_cut_in_v0` excludes all 8 controllers** — decide whether it is a broken scene
   or a genuine Q-035 unreportable surface, before P5 counts it as a scene.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: results/readings/2026-08-25-17-lam-windows-8-controller.yaml, results/readings/2026-08-25-17-lam-regen.log, docs/decisions.md, journal/2026-08/25-17-*.md
- TSV row appended: yes
