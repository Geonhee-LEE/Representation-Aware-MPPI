# Pin the ungated heading-price collision on cut_in as a test

- **Cycle**: 2026-09-27 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략
- **Phase**: P6 (TODO tagged P5)
- **Status**: in_progress

## What I tried
- Discharged the 09-27 10:00 strand first (D-112): `push_preflight record` on `e32cd59` gave 4537 passed / 0 failed (1447 s), pushed `18ed26a..e32cd59`.
- While the suite ran, measured cut_in (knee+shape band, w_heading_near=64) on seeds 0-7, ungated vs v_gate 0.45, from a `/tmp` script so the receipt tree did not move.
- Added `eval/mppi_sandbox/tests/test_heading_near_gate_is_safety.py`: seeds 0/3/5, asserting ungated min clearance < 0 and gated ≥ the 0.30 m band.

## What worked / what failed
- Seeds 0-7 ungated: 4/8 collide (0: -0.56, 1: -0.23, 3: -0.50, 5: -0.46 m). Gated 0.45: 0/8 negative, 7/8 at the band, seed 1 at 0.10 m (D-505's parked-creep fail, same as baseline).
- Pinned seeds 0/3/5 (seed 1 excluded because its gated arm is the known creep fail). 6 integrations, narrow run 2/2 green in 21 s.
- The test commit is a deliberate strand: a second suite does not fit after the strand-discharge suite.

## North-star delta
- No controller change. D-505's safety constraint (`w_heading_near` never ships without `heading_near_v_gate`) is now executable: any future default that drops the gate goes red.

## Key learnings
- The first two claude-actionable items after a strand keep costing a full suite each; putting the measurement in `/tmp` during the discharge suite is the only way to make a cycle yield both a push and new work.

## Recommended next 1–3 priorities
1. Discharge this cycle's strand (test commit + report).
2. head_on fails heading on 16/16 under both arms. Check whether D-499's near-obstacle localization holds there.
3. User policy call: accept ~5 s of yielding for heading fails 19→1/32 (gate always on).

## Artifacts
- PR: none (PR #67 closed by user 09-21). Test + report commit is a deliberate strand.
- Files touched: eval/mppi_sandbox/tests/test_heading_near_gate_is_safety.py, eval/mppi_sandbox/tests/test_default_lam_sites.py (forwards 45→46, total 251→252), journal/2026-09/27-20-pin-ungated-heading-collision-on-cut-in.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
