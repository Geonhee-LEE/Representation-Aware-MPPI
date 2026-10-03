# w_progress's obstacle-scene effect is its goal gate (yield), not the progress reward

- **Cycle**: 2026-10-03 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` cross-scene check of `w_progress=10` on the 9 shipped scenes
- **Phase**: P6
- **Status**: keep

## What I tried
- The killed 10:00 cycle left a raw-stock n=16 run (/tmp/d512.json). I re-ran it on the knee+shape band (0.30) used by D-504..D-508: 9 scenes x seeds 0-15, band vs band + `w_progress=10`, judged by each yaml's acceptance.
- Diagnosed the head_on regression by tracing seed 0.
- Added an inert `progress_detour_ratio` knob that reopens the goal gate when the remaining path is <= ratio x the straight-line goal distance. Measured ratio 1.5 on 10 scenes (9 + city_figure8_v1) at n=16.

## What worked / what failed
- band + w10: crossing **6/16 -> 16/16** (T 9.7 -> 17.8 s); convoy, freezing, contested, straight and curved 16/16 in both arms, with cte equal or better (curved 0.141 -> 0.030); cut_in 0/16 in both (goal ball blocked).
- **Regression**: head_on T 9.9 -> **42.1 s** (cte 0.31 -> 0.63). The gate keeps the attractor off for the whole 4 m path, so the robot backs up behind its start (y=+1.4) and parks behind the stopped pedestrian.
- ratio 1.5: head_on back to 9.6 s and figure8_v1 16/16 (cte 0.144). But crossing falls to **2/16**, so the crossing gain came from the attractor being off. That is a yield, not progress.
- Pinned by `test_progress_goal_gate_is_the_yield.py` (gate unit tests + head_on seed 0 closed loop).

## North-star delta
- w_progress cannot be promoted as is: +32 s on head_on.
- The crossing heading fix now has two mechanisms (D-507 scoped heading, attractor-off yield). Both cost about +5-8 s of yield time.

## Key learnings
- A cost term with a gate can win through the gate rather than through the term. Ablate the gate separately before crediting the term.
- On short paths (<= goal_gate + 1 m) the D-511 gate is a global "no attractor" switch.

## Recommended next 1-3 priorities
- Promote `w_progress=10, progress_detour_ratio=1.5` as the tracking default candidate: identical on cafe scenes, improves curved/figure8 tracking. Needs a measured cut_in/convoy n=16 diff (done here: no regression).
- User policy call on yield time (crossing): D-507 scoped heading vs w/o.

## Artifacts
- PR: none (branch continuation, per user branch-hygiene decision pending)
- Files touched: critics/arclength_progress.py, controllers/stock_mppi.py, tests/test_progress_goal_gate_is_the_yield.py, tests/test_default_lam_sites.py
- TSV row appended: yes
