# w_heading_near=64 establishes the heading flip at n=32 — with a cross-track tail

- **Cycle**: 2026-09-25 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략
- **Phase**: P6 (TODO tagged P5)
- **Status**: keep

## What I tried
- Paired n=32 sweep (seeds 0–31) of `w_heading_near` ∈ {0, 16, 32, 64} on the knee+shape arm, `cafe_obstacle_crossing_v0` (~137 s total, measurement script only).
- Recorded heading RMS fails, min clearance, and cross-track (cte_rms per seed, cte max) per arm; McNemar exact on the pass/fail flip vs w=0.

## What worked / what failed
- w=0: 19/32 heading fails (first 16 seeds = 10, reproduces D-500). w=16: 21/32, **2 clearance fails**, cte_rms_mean 0.234→0.421 — worse on every axis.
- w=32: 11/32 (13 fixed / 5 broken, p≈0.096) — same direction as D-500, still not significant.
- w=64: **3/32** (17 fixed / 1 broken, p<0.001), RMS improves on 30/32 seeds, clearance 0/32, cte_rms_mean 0.234→0.154.
- But at w=64 cte_rms_max 0.544→2.202 and cte_max 1.466→3.930: at least one seed leaves the path badly. Mean improves, tail explodes.

## North-star delta
- First statistically established heading fix on this scene (19→3/32), clearance intact. Not shippable as default until the cte tail is explained.

## Key learnings
- The gated heading effect is real but only at high weight; the low-weight regime (8, 16) is non-monotone and can even cost clearance.
- Mean cte and worst-case cte move in opposite directions — a default change needs per-seed tail metrics, not arm means.

## Recommended next 1–3 priorities
1. Identify the w=64 cte-tail seed(s) and localize where they diverge (wrong-side pass? oscillation after the obstacle?).
2. If the tail is a single mode, bound it (e.g. cap gated heading cost by lateral offset) and re-measure n=32.
3. Explain w=16's 2 clearance fails (lower priority).

## Artifacts
- PR: none (PR #67 closed by user 09-21; branch push only)
- Files touched: docs/decisions.md, journal/2026-09/25-10-heading-near-64-establishes-the-flip.md, results/
- TSV row appended: yes
