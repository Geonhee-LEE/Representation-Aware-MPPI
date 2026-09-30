# Scoped heading price: no regression on the other 6 scenes

- **Cycle**: 2026-09-30 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략
- **Phase**: P6
- **Status**: keep

## What I tried
- Ran a paired n=16 check (seeds 0–15, knee+shape band) of w=0 against the scoped arm (w_heading_near 64, v_gate 0.45, max_cos 0.5) on the 6 scenes D-507 had not covered: convoy, freezing, contested, straight, city_curved, city_figure8.
- Scored each run against that scene's own yaml `acceptance` block (goal, min clearance, cte_rms/cte_max/heading limits where declared). I also compared per-seed trajectories between the two arms. This was a /tmp script: 192 runs in 2m12 on 16 procs. No code changed.

## What worked / what failed
- convoy, freezing, contested: both arms pass 16/16 and min clearance stays at 0.30. The scoped arm does fire on these scenes (its trajectories differ from w=0), and heading rms improves on 11/16, 11/16 and 8/16 seeds. Mean arrival steps move 161.5→159.8, 138.6→137.3 and 170.8→174.2, so crossing's ~5 s yield cost does not carry over.
- straight, city_curved, city_figure8: these scenes have no obstacles, so the gate never opens and the scoped arm matches w=0 bit for bit on every seed.
- figure8 is 0/16 on both arms (heading 16, goal 7). That is a baseline defect and has nothing to do with this knob.

## North-star delta
- All 9 scenes now have evidence for the scoped arm. The only regression anywhere is the crossing time-to-goal (+5 s, D-504). On the obstacle scenes it gains heading at little or no time cost, and it adds no clearance fails.

## Key learnings
- The yield cost is specific to crossing. Convoy and freezing also have pedestrians moving across the path, yet arrival time did not go up there. So the +5 s is a property of crossing's geometry (the crosser lands in the robot's first 3 m), not of the knob.
- city_figure8's 0/16 heading fails with median rms ~2.06 look like a metric or path-projection artifact on a self-intersecting path. That is worth a separate look.

## Recommended next 1–3 priorities
- User policy call: promote `w_heading_near=64, v_gate=0.45, max_cos=0.5` to default given +5 s on crossing only.
- Diagnose city_figure8 0/16 (heading rms ~2.06 on both arms): check whether it is a controller failure or a heading-metric projection artifact at the crossing point of the path.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: docs/decisions.md, journal/2026-09/30-10-scoped-heading-near-cross-scene-no-regression.md, results/
- TSV row appended: yes
