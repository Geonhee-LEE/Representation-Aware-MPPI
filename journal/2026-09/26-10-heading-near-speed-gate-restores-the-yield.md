# A speed gate on w_heading_near keeps the heading fix and restores the yield

- **Cycle**: 2026-09-26 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략
- **Phase**: P6 (TODO tagged P5)
- **Status**: in_progress

## What I tried
- Discharged the 09-25 20:00 strand first (D-112): full suite through `push_preflight record` came back 4535 passed / 0 failed in 1034 s, and I pushed `3be5be2..9222167`.
- While that suite ran, I prototyped a speed gate for the gated heading price. It was a monkeypatch in `/tmp`, so the tree stayed on the receipt. I swept v_gate ∈ {0.10…1.00} at w=64 over paired seeds 0–31. The prototype reproduces D-501's seed-27 figures exactly (cte_max 3.930).
- I shipped it as `MPPIParams.heading_near_v_gate` (default 0.0, inert) and extended `test_heading_near_gate.py` in its existing fixture site, so the lam census stays at 108/98/45.

## What worked / what failed
- v_gate 0.30–0.55 is a plateau: heading fails **1/32** (0.35: 3/32), clearance fails 0/32, cte_max 0.99 / 0.83 / 0.27 m (w=0: 1.47). Seed 27 is back to cte_max ≤ 0.11 m. At 0.70 heading fails go back up to 9/32, and 1.00 reproduces w=0 exactly (sanity).
- The pinned point is 0.45. On the first 16 seeds it fixes 10 and breaks 1 (McNemar p≈0.012). New tests: 6/6 in 56 s. Lam census tests: 42/42. `census_preempt`: all 12 clean.
- Cost: mean time-to-goal goes 18.9 → 24.2 s and mean speed 0.305 → 0.210 m/s, slightly slower than ungated w=64 (23.2 s). I think rollouts slow down to escape the price, but that mechanism is not verified.
- **Not pushed**: `cycle_wallclock` read SUITE_UNAFFORDABLE at 17m55, before the code commit. `3b014c5` plus this report are a deliberate strand. `inert_surface staged` reported STAGED_MOVED (5 pins), which is a price, not a failure.

## North-star delta
- On the crossing scene the knee+shape arm now has an inert config with 1/32 heading fails, 0/32 clearance fails, and a cte_max below baseline. The last named tail mode is removed. That config pays ~28% in time-to-goal, so it is not a default yet.

## Key learnings
- Gating a cost on state (clearance) was not enough. The gate also needs to know *what manoeuvre* the robot is in, and speed is a cheap proxy for "yielding".
- The gate can be escaped: any cost that switches off below a speed teaches the planner to slow down. Always measure time-to-goal next to a gated price.

## Recommended next 1–3 priorities
1. Discharge this strand (suite + record + push).
2. Split the time-to-goal cost. Where along the path is the extra ~5 s spent: near the obstacles (slowing to escape the price) or elsewhere? If it is near the obstacles, a smooth ramp in |v| instead of a step may recover it.
3. Re-run the full scenario matrix with w=64 + v_gate=0.45 to check whether other scenes regress, before any default change.

## Artifacts
- PR: none (PR #67 closed by user 09-21). Strand `3b014c5` + report commit, not pushed this cycle.
- Files touched: eval/mppi_sandbox/controllers/stock_mppi.py, eval/mppi_sandbox/tests/test_heading_near_gate.py, docs/decisions.md, journal/2026-09/26-10-heading-near-speed-gate-restores-the-yield.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
