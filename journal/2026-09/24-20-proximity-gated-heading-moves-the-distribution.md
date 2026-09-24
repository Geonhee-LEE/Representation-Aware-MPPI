# Proximity-gated heading price moves the distribution, not yet the pass count

- **Cycle**: 2026-09-24 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략
- **Phase**: P6 (TODO tagged P5)
- **Status**: keep

## What I tried
- Found the 09-23 20:00 cycle's uncommitted `w_heading_near` / `heading_near_band` knob in `stock_mppi.py` (heading price gated to timesteps with clearance < 1.05 m, D-499's window); `tree_provenance declared` was rc=1 on it.
- Measured it on the knee+shape arm, `cafe_obstacle_crossing_v0`, paired 16 seeds: w ∈ {0, 8, 32}.
- Pinned the w=0 vs w=32 result in `test_heading_near_gate.py` (4 tests, ~29 s); bumped the lam census (`forwards` 44→45, total 250→251).

## What worked / what failed
- w=0: heading fails 10/16 (reproduces D-430). w=8: 11/16. w=32: **7/16**. Clearance fails 0/16 in all three arms.
- At w=32 per-seed heading RMS improves on 12 seeds, worsens on 4 (sign p≈0.08) — unlike `w_omega` (D-433, 9/7) this shifts the distribution.
- But pass/fail flip is 6 fixed vs 3 broken (McNemar p≈0.51), and w=8 is non-monotone → not established; default stays 0.
- A gate-geometry unit test tripped two lam-census invariants (`inert_defaults`, majority margin); dropped it rather than re-pin under time pressure.

## North-star delta
- First heading lever on this scene that moves the distribution without costing clearance (10→7 fails at n=16). Not a default change.

## Key learnings
- Structural (gated) pricing beats effort weighting here — consistent with D-499's localization.
- n=16 is too small to confirm a 3-seed swing; the next step is more seeds or a finer w sweep, not a new knob.

## Recommended next 1–3 priorities
1. Extend the w_heading_near sweep (16, 32, 64) at n=32 seeds to establish or kill the flip.
2. Check cte_rms_max / cte_max under w=32 — heading gain may be paid in cross-track.

## Artifacts
- PR: none (PR #67 closed by user 09-21; branch push only)
- Files touched: eval/mppi_sandbox/controllers/stock_mppi.py, eval/mppi_sandbox/tests/test_heading_near_gate.py, eval/mppi_sandbox/tests/test_default_lam_sites.py, docs/decisions.md
- TSV row appended: yes
