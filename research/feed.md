# Research Feed

Auto-populated by `scripts/researcher.sh` (4-hourly cron). Newest first, cap 30
entries. Per-cycle archive lives under `research/YYYY-MM/<seq>.md`. Format and
conventions: see [`research/README.md`](README.md).

---

## 2026-05-24 22:40 — TCFM: Trajectory Conditional Flow Matching (100× faster than diffusion)

- **Source**: https://github.com/CORE-Robotics-Lab/TCFM · paper https://arxiv.org/abs/2403.10809
- **Type**: arxiv + github
- **Why relevant**: Direct competitor / complement to cfm_mppi (Mizuta & Leung). Claims 100× speed-up over diffusion + 35% higher predictive accuracy + 142% better planning. Sean Ye / Matthew Gombolay (Georgia Tech CORE). Reduces our P2 (learning dynamics) integration cost — TCFM API can be wrapped as the "generator" half of our future CFM-MPPI port.
- **Suggested TODO**: clone TCFM repo, run its unicycle eval, compare velocity-field architecture vs cfm_mppi's transformer.

## 2026-05-24 22:40 — Flow Planner: hierarchical CFM (waypoint + action)

- **Source**: https://github.com/frankcholula/flow_planner
- **Type**: github
- **Why relevant**: Splits CFM planning into long-horizon Waypoint Planner + short-horizon Action Planner. Natural fit for our Nav2 global/local planner split — global = waypoint flow, local = MPPI refines per-segment.
- **Suggested TODO**: skim repo architecture, write 1-paragraph mapping to our Nav2 stack in `docs/cfm_mppi_analysis.md` (issue #17 follow-up).

## 2026-05-24 22:40 — PA-MPPI: Perception-Aware MPPI for unknown environments

- **Source**: https://arxiv.org/abs/2509.14978
- **Type**: arxiv
- **Why relevant**: Quadrotor focus but the **perception-aware** angle (cost over future field-of-view coverage, not just collision) is directly transferable to our ground robot with limited camera FoV (forward-facing only). Hints at how to do partial-observability-aware MPPI when LiDAR/camera don't see behind walls.
- **Suggested TODO**: extract their perception cost formulation, add as candidate critic to our nav2_mppi_params Phase-3 experiment.

## 2026-05-24 22:40 — Biased-MPPI: ancillary controller fusion for sampling

- **Source**: https://www.semanticscholar.org/paper/1e0e10cbb19ab216896032b2e861919f1135d696
- **Type**: arxiv
- **Why relevant**: Informs sampling-based MPC by fusing **ancillary controllers** (e.g., Pure Pursuit baseline) into the noise distribution. Our roadmap already files Pure-Pursuit baseline (TODO #2 in north-star backlog) — Biased-MPPI's framework is the principled way to fuse those baselines as MPPI initial samples instead of running them in parallel.
- **Suggested TODO**: read paper, add note to MPPI critic-weight ablation TODO (#?) about fusing Pure-Pursuit as `ancillary_init` sample bank.

## 2026-05-24 22:40 — IANN-MPPI: interaction-aware NN-enhanced MPPI

- **Source**: (search-only — full citation in next cycle)
- **Type**: arxiv
- **Why relevant**: Predicts how surrounding agents may react to each control sequence sampled by MPPI. P4-relevant: dynamic obstacle prediction module that's MPPI-aware, not constant-velocity. Replaces our current planned constant-velocity placeholder with a learned interaction model.
- **Suggested TODO**: capture in P4 TODO list as "interaction-aware predictor option" (parallel track to SFM port).

## 2026-05-24 22:40 — Trajectory Planning with MPC under Prediction Uncertainty

- **Source**: https://arxiv.org/abs/2504.19193
- **Type**: arxiv
- **Why relevant**: Aleatoric uncertainty propagation through MPC trajectory cost. Direct input for our P3 risk/uncertainty channel work — provides a baseline formulation we can compare our channelized representation against.
- **Suggested TODO**: cite in our P3 risk_field.md spec when written.

---

## 2026-05-01 00:00 — bootstrap

- **Source**: (none — feed initialized)
- **Type**: blog
- **Why relevant**: Placeholder so future cycles can dedup against a non-empty file. Researcher's first real run replaces this entry's slot.
- **Suggested TODO**: none
