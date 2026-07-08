# P4 Dynamic Obstacles Kick-off Spec

- **Cycle**: 2026-07-09 00:05 KST
- **Branch**: `autoresearch/p4-dynamic-obstacles-kickoff`
- **TODO**: `P4-kickoff` P4 dynamic obstacles kick-off doc spec
- **Phase**: P4
- **Status**: keep

## What I tried

- Wrote `docs/p4_dynamic_obstacles_kickoff.md` (193 lines) scoping the full P4 phase
- Mapped D1→D4 stage progression with week-level timing against D-stage framework in `dynamic_obstacles_uncertainty_track.md`
- Incorporated 3 research feed signals: iCrowdNav I²Former (pedestrian intent predictor), NavIsaacLab (crowd-gen taxonomy), DUCCT-MPPI (dual-uncertainty localization+prediction arm)
- Defined dynamic risk channel architecture (tracker → prediction model → BEV grid → MPPI critic) with three prediction model candidates ranked by complexity

## What worked / what failed

- Doc lane worked cleanly — no P2 dependency, no build needed, clean commit+push+PR in ~5 min
- Research feed synthesis was productive: I²Former (D4), NavIsaacLab taxonomy (P5 evaluation substrate), DUCCT-MPPI UT arm (defer to P5), DRA-MPPI MC (D3 ablation candidate) — all clear placement
- Notion MCP denied again (27th cumulative) — TODO seeds live only in the kickoff doc until MCP grant

## North-star delta

- **+1 spec doc**: P4 scope now explicitly documented before the phase starts (day -1)
- **+6 TODO seeds**: P4-T01 through P4-T06 defined with dependencies, priority, owner
- **0 code change**: pure doc; no direct north-star movement, but removes ambiguity about what P4 means

## Key learnings

- D4 (reactive pedestrians) needs I²Former **only as a module** — the RL policy is not borrowed; this boundary keeps the classical-planner thesis intact
- DUCCT-MPPI UT localization arm is a P5 addition, not P4 — P4 focuses on DRA-MPPI MC prediction arm first; UT arm complexity (Gaussian AMCL approximation) needs its own cycle
- NavIsaacLab crowd-gen methodology is borrowable without adopting Isaac Lab; the cross-scale taxonomy (5/10/20 actor density) directly maps to `per-pedestrian-density` metric in `dynamic_obstacles_uncertainty_track.md` §6
- HuNav ROS2 is the recommended reactive pedestrian plugin for D3/D4 over PedSim (Jazzy compat better)

## Recommended next 1–3 priorities

1. **Gazebo dynamic scenario YAML v1** (5/10/20 actor density, scripted, P4-T02) — no P2 dep, doc+config only, can run next cycle
2. **HuNav ROS2 install test in Jazzy** (P4-T05) — study + apt/source install test, no P2 dep
3. **Create Notion `[research]` TODOs** (HOLO-MPPI/DUCCT-MPPI/iCrowdNav/condition-aware-residual) once MCP grant arrives — next cycle if MCP allowed

## Artifacts

- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/64
- Files touched: `docs/p4_dynamic_obstacles_kickoff.md`, `results/p4-dynamic-obstacles-kickoff.tsv`
- TSV row appended: yes
