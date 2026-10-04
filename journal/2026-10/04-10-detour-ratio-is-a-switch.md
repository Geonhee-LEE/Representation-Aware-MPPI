# progress_detour_ratio is a switch on every shipped scene but figure8_v1

- **Cycle**: 2026-10-04 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3c4c5d39` pick a promotable `progress_detour_ratio` (figure8_v1 cte 0.144 at r1.5 vs 0.02 at r0)
- **Phase**: P6
- **Status**: keep

## What I tried
- Swept `w_progress=10` + knee+shape band 0.30, ratio {0, 1.2, 1.5, 2, 3} x {figure8_v1, curved, crossing, head_on} x seeds 0-15 (320 runs, 3m15).
- Computed each shipped path's length / chord (the gate's t=0 detour ratio).
- Pinned both in `test_detour_ratio_is_a_switch.py` (static, no rollouts, 10 tests).

## What worked / what failed
- figure8_v1: cte rises with ratio, .020 (r0) / .048 (r1.2) / .144 (r1.5), all 16/16. r2 and r3 are 0/16 because the gate opens mid-figure and the robot shortcuts.
- curved, crossing, head_on: r1.2, r1.5, r2 and r3 give **identical** results (curved cte .145, crossing 2/16, head_on T 9.6 s).
- Reason: every shipped scene has length/chord <= 1.129 (cafe 1.0, curved 1.129). So any ratio >= 1.13 opens the gate at t=0 and the attractor stays on throughout. Only figure8_v1 (9.38) has a ratio that sets anything.
- So curved's cte gain (.145 -> .030) is also the attractor being off, like crossing's 16/16 (D-512). No ratio keeps those gains and also fixes head_on.

## North-star delta
- No new pass. Answers the bottleneck: no ratio is promotable as a "tracking default". The r0 tracking gains and the r>0 head_on fix are mutually exclusive through this knob.
- If one is needed: r1.2 is the least-bad (figure8_v1 16/16 cte .048, head_on restored), but it is equal to band-only on every shipped scene.

## Key learnings
- A dial whose t=0 value is a scene property (length/chord) is a switch on any population where that property is clustered. Check the population's spread before sweeping the dial.
- The real lever is the attractor-off regime. Head_on's retreat under attractor-off is the thing to fix, not the gate. Hypothesis: `arclength_windowed` clips to the window's lower edge (s_robot - 0.5), so retreating more than 0.5 m costs no extra progress penalty.

## Recommended next 1-3 priorities
- Test the clip hypothesis: trace head_on seed 0 at r0 and price retreat beyond `back` (for example, unclipped lower bound or a linear penalty on s < s_robot - back).
- Make `completion_percent` monotone/windowed (figure8_v1 shortcut reads completion=1.0).

## Artifacts
- PR: none (branch continuation, per user branch-hygiene decision pending)
- Files touched: eval/mppi_sandbox/tests/test_detour_ratio_is_a_switch.py
- TSV row appended: yes
