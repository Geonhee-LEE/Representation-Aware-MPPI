# cut_in clearance fail is the baseline creep mode, and the speed gate is a safety requirement

- **Cycle**: 2026-09-27 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` [sandbox] knee+shape 아래 heading_err_rms_max 공략
- **Phase**: P6 (TODO tagged P5)
- **Status**: in_progress

## What I tried
- Discharged the 09-26 20:00 strand first (D-112): `push_preflight record` gave 4537 passed / 0 failed in 1015 s, and I pushed `101383e..18ed26a`. `stranded` is clean.
- While the suite ran I localized the cut_in clearance fail (`/tmp` scripts only, so the tree stayed on the receipt). knee+shape, paired seeds 0–31, three arms: w=0, ungated w=64, and w=64 + v_gate 0.45. For each seed I recorded min clearance, when it happens, the positions, and the closing speed split between robot and obstacle.

## What worked / what failed
- Every cut_in run ends parked at the 0.30 m barrier band around the pedestrian, which stops at (0, -3.8), inside the goal ball (0/32 goals in every arm). The fails all happen in this parked phase. Obstacle closing speed is 0.00 in every fail, so this is a static near-contact, not the cut-in manoeuvre.
- **The gated arm is no worse than baseline at n=32**: w=0 fails 1/32 (seed 30, 0.11 m) and w=64+0.45 fails 1/32 (seed 1, 0.10 m). The "0→1" in D-504 was n=16 noise.
- Seed-1 mechanism: the robot sits in the band at v≈0 (clr 0.23), then pivots about 2.9 rad with 0.1–0.3 m/s forward creep. That swings it to 0.10 m before the barrier pushes it back out. Its |v| stays below the 0.45 gate the whole time, so the heading price is off. It is the baseline's low-speed creep mode, not the gated price.
- **Ungated w=64 collides**: 12/32 seeds have negative clearance (−0.23 to −0.58 m). The ungated heading price pushes fast rollouts to align with the path heading, and on cut_in that heading points straight into the parked pedestrian. The speed gate is what prevents this, so it is a safety requirement, not only a time-to-goal fix.

## North-star delta
- No controller change. The cut_in objection to a default change (D-504 (c)) is withdrawn: w=64+0.45 matches baseline clearance at n=32. What still blocks a default is the policy call on ~5 s of yielding.
- New constraint: `w_heading_near` must never ship without `heading_near_v_gate`. The ungated form is a collision regression on a blocked goal line.

## Key learnings
- n=16 single-fail differences need n=32 plus the baseline arm before they count. Both arms had exactly one fail at n=32.
- A path-aligned heading price is dangerous whenever the reference path runs through an obstacle, for example a blocked goal ball. Gating by speed (or by clearance) is load-bearing.

## Recommended next 1–3 priorities
1. Pin the ungated-collision finding as a test: cut_in, w=64 with v_gate=0 vs 0.45 on a couple of known seeds (e.g. 0 and 14), asserting that gated clearance ≥ 0.
2. head_on fails heading on 16/16 under both arms. Check whether D-499's near-obstacle localization holds there.
3. User policy call: accept ~5 s of yielding in exchange for heading fails 19→1/32? If yes, promote w=64+0.45 as a default, gate always on.

## Artifacts
- PR: none (PR #67 closed by user 09-21). Report commit is a deliberate strand if no second suite fits.
- Files touched: docs/decisions.md, journal/2026-09/27-10-cut-in-clearance-fail-is-baseline-creep-and-the-gate-is-safety.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
