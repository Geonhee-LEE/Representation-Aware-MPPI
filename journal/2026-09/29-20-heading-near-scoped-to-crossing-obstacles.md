# Heading price scoped to path-crossing obstacles

- **Cycle**: 2026-09-29 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략
- **Phase**: P6
- **Status**: keep

## What I tried
- New inert knob `heading_near_max_cos` in `StockMPPI`. A moving obstacle drops out of the `w_heading_near` gate wherever |cos(its heading - path tangent)| exceeds the knob. Static obstacles still count.
- Measured at knee+shape band, w=64, v_gate 0.45, max_cos 0.5: crossing n=32, head_on n=16, cut_in n=32 (/tmp script, ~20 s per 144 runs on 16 procs).
- Pinned the result in `test_heading_near_crossing_scope.py` (seed 3, 4 integrations). Bumped the lam census forwards 47→48 and total 253→254.

## What worked / what failed
- crossing: scoped arm is **identical per seed** to the gated arm. Heading fails go 19→1/32 and clearance fails stay 0/32.
- head_on: scoped arm is **identical per seed** to w=0 (median rms 0.416 vs gated 0.544), so D-506's regression is gone.
- cut_in: clearance fails are 1/32 on all three arms. Heading fails are 32/32 on every arm (the pedestrian parks in the goal ball).
- My first test version called a `_run` helper, which the lam census counted as 4 `defaults` sites and which broke the majority-margin pin. I inlined `ab.run_arm(..., params=p)` in the fixture, so it now counts as 1 `forwards` site.

## North-star delta
- On these three scenes the heading term no longer trades one scene against another: crossing gets the full gain and head_on/cut_in are unchanged. The one remaining blocker to a default is the ~5 s time-to-goal from yielding on crossing (a policy call).

## Key learnings
- Classifying the obstacle's motion relative to the path separates "yield to a crosser" from "sidestep an oncoming walker". A scalar weight cannot make that separation.
- The lam census counts `helper(...)` calls without explicit params as `defaults`. Forward `params=` at the `run_arm` call instead.

## Recommended next 1–3 priorities
- User policy call on the time-to-goal cost (+5 s on crossing); the rest of the evidence for promoting `w_heading_near=64, v_gate=0.45, max_cos=0.5` is in.
- Cross-scene n=16 sweep of the scoped arm over the other 6 scenes before any default flip.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/controllers/stock_mppi.py, eval/mppi_sandbox/tests/test_heading_near_crossing_scope.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, docs/decisions.md
- TSV row appended: yes
