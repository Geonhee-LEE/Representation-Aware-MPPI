# Research Feed

Auto-populated by `scripts/researcher.sh` (4-hourly cron). Newest first, cap 30
entries. Per-cycle archive lives under `research/YYYY-MM/<seq>.md`. Format and
conventions: see [`research/README.md`](README.md).

---

## 2026-05-26 14:00 — Socially Aware Crowd Nav via Online Uncertainty-Driven Risk Adaptation

- **Source**: https://arxiv.org/abs/2506.14305
- **Type**: arxiv
- **Why relevant**: Dual-level uncertainty (epistemic EU + aleatoric AU) per waypoint + minimum-risk filter for online crowd nav. **온라인 risk 적응** 이 우리 P3/P4 risk channel 의 가중치를 fixed 가 아니라 시점/맥락별로 조정하는 메커니즘 단서. 우리 north-star "모든 환경" — 환경별 자동 가중치 조정 = 일반화.
- **Suggested TODO**: dual-level EU/AU filter formula 추출 → 우리 risk channel critic 가중치 schedule 후보.

## 2026-05-26 14:00 — Disentangling Uncertainty for Safe Social Navigation (IROS 2025, DRL)

- **Source**: https://arxiv.org/abs/2409.10655
- **Type**: arxiv
- **Why relevant**: aleatoric + epistemic + predictive uncertainty 분리하여 DRL policy distribution 에 통합. P3 의 5 channel 중 "epistemic" vs "aleatoric" 채널 정확한 분리 기준이 우리는 still 가설 — 본 논문이 분리 정의 + 측정 + 행동 결정 사용 방법 정립.
- **Suggested TODO**: § "Disentanglement methodology" 직접 우리 P3 risk_field.md spec 에 인용.

## 2026-05-26 14:00 — DyObAv-MPCnWTA: Deep prediction + MPC for warehouse dynamic obstacles

- **Source**: https://github.com/Woodenonez/DyObAv-MPCnWTA-Warehouse
- **Type**: github
- **Why relevant**: 동적 obstacle multimodal motion prediction + MPC collision-free trajectory generation. Warehouse 시나리오 — 우리 cafe 와 city 사이 중간 난이도. 코드 직접 비교/차용 candidate.
- **Suggested TODO**: clone + run, 우리 jackal_cafe 보행자 시나리오와 비교 가능한지 평가.

## 2026-05-26 08:00 — Embedded Robust MPPI with Sensitivity Tubes + GPU Acceleration
- **Source**: https://ieeexplore.ieee.org/document/11127520/
- **Type**: arxiv
- **Why relevant**: Robustifies MPPI against parameter uncertainty by incorporating closed-loop state sensitivity into the controller formulation — sensitivity tubes bound the effect of model mismatch on rollout trajectories. Includes embedded GPU-parallel implementation validated on aerial robot obstacle avoidance. P2-relevant: as we integrate learned dynamics models (which inherently have model mismatch), sensitivity tubes offer a principled robustness mechanism without leaving the MPPI sampling framework.
- **Suggested TODO**: evaluate sensitivity tube formulation as robustness wrapper when integrating residual dynamics model in P2 MPPI rollout.

## 2026-05-26 04:03 — TRAIL: Implicit Neural Representation of Terrain Traversability (Jia, Li, How 2026)
- **Source**: https://arxiv.org/abs/2511.18183
- **Type**: arxiv
- **Why relevant**: Learns implicit neural representation (INR) of terrain as a continuous, queryable field — enables gradient-based trajectory optimization that adapts path geometry + speed profile based on traversability. From MIT (How group). Directly aligned with representation-aware thesis: learned spatial representation feeding into planning replaces discrete grid-based maps. P3-relevant as INR provides a differentiable terrain representation for risk/uncertainty channels.
- **Suggested TODO**: study TRAIL's INR architecture as reference for continuous terrain representation feeding MPPI cost evaluation.

## 2026-05-26 04:03 — CFU-MPPI: Map-Conditioned Trajectory Sampler for MPPI (Cao, Moorthy, Poyrazoglu, Isler 2025)
- **Source**: https://arxiv.org/abs/2510.16905
- **Type**: arxiv
- **Why relevant**: Generates MPPI control distributions conditioned on local map (C-free space), replacing environment-independent sampling. Better success rate with smaller sampling budget in cluttered environments. Core alignment with representation-aware MPPI thesis — the sampler itself becomes representation-aware, not just the cost function. Complementary to representation-aware critics.
- **Suggested TODO**: evaluate map-conditioned sampling as complementary approach to representation-aware cost critics in nav2_mppi_controller.

## 2026-05-26 04:03 — MPPI-DK: Accelerating MPPI via Learned Linear Koopman Dynamics (Hao, Fang, Lu, Mou 2026)
- **Source**: https://arxiv.org/abs/2603.05385
- **Type**: arxiv
- **Why relevant**: Replaces nonlinear dynamics in MPPI rollout with learned linear deep Koopman operator — faster rollout while preserving control quality. P2-relevant: as learned dynamics models grow with BEV channels, Koopman linearization could maintain real-time performance. Different angle from Koopman+CBF paper (2603.21070) already in feed — this one targets computational efficiency, not safety.
- **Suggested TODO**: evaluate Koopman linearization as computational efficiency strategy when MPPI dynamics model complexity grows in P2.

## 2026-05-26 00:04 — MPPI as Preconditioned Gradient Descent (Fazlyab, Sharifi, Wang 2026)
- **Source**: https://arxiv.org/abs/2603.24489
- **Type**: arxiv
- **Why relevant**: Proves MPPI update = unit-step preconditioned gradient descent with fixed-covariance Gaussians. Provides convergence guarantees based on covariance properties of the sampling distribution. As we modify MPPI's input representation (multi-channel BEV, P1/P3), understanding how covariance affects convergence is foundational — gives theoretical backing for tuning sampling distribution as representation dimensionality grows.
- **Suggested TODO**: study convergence conditions; assess if representation-augmented MPPI cost landscape satisfies descent guarantees.

## 2026-05-26 00:04 — MPPI-PID: Gain-Space MPPI for Path Following (Kato, Oishi, Ito 2026)
- **Source**: https://arxiv.org/abs/2603.29499
- **Type**: arxiv
- **Why relevant**: Reformulates MPPI to optimize PID gains instead of raw control sequences — lower-dimensional optimization space + smoother control inputs + comparable performance with fewer samples. Tested on mini forklift. Path following quality is a north-star metric; gain-space optimization is an alternative to direct control-sequence sampling when input dimensionality grows with BEV channels.
- **Suggested TODO**: evaluate gain-space optimization approach as alternative to direct control-sequence sampling in nav2_mppi_controller.

## 2026-05-26 00:04 — Koopman-Based Linear MPC + CBF for Safe Navigation (Liu et al. 2026)
- **Source**: https://arxiv.org/abs/2603.21070
- **Type**: arxiv
- **Why relevant**: Lifts nonlinear dynamics AND CBF into linear Koopman space, converting safety-constrained nonlinear MPC into a QP. Demonstrated on robot navigation task. Connects P2 (learned dynamics) + safety (CBF-MPPI thread): Koopman-linearized dynamics make safety filtering computationally tractable. Alternative path to safe_control's direct CBF-QP approach.
- **Suggested TODO**: compare Koopman-linearized CBF-MPC vs direct CBF-QP (safe_control) on computation time and constraint satisfaction.

## 2026-05-26 00:04 — Deep Probabilistic Traversability + Test-Time Adaptation (Nature Sci. Rep. 2026)
- **Source**: https://www.nature.com/articles/s41598-026-40109-1
- **Type**: arxiv
- **Why relevant**: Learning-based traversability estimation with probabilistic uncertainty quantification and test-time adaptation for OOD environments. P3-relevant: probabilistic traversability output with uncertainty naturally maps to risk/uncertainty field channels (epistemic from OOD terrain, aleatoric from terrain variance). Test-time adaptation addresses sim-to-real gap.
- **Suggested TODO**: review uncertainty decomposition methodology; evaluate if test-time adaptation transfers to Gazebo→real-world pipeline.

## 2026-05-25 22:00 — DPCBF: Dynamic Parabolic CBF for nonholonomic robots (Park/Kim/Panagou, ICRA 2026)

- **Source**: https://arxiv.org/abs/2510.01402 · project https://www.taekyung.me/dpcbf · video https://youtu.be/57qgoe7YJao
- **Type**: arxiv + implementation (safe_control)
- **Why relevant**: Solves the **infeasibility failure mode** of standard collision-cone / velocity-obstacle CBFs by adapting the safe-set parabola's vertex + curvature dynamically based on distance AND relative-velocity magnitude. Demonstrated navigating up to **100 dynamic obstacles** in dense scenarios where C3BF gives up. Author is `safe_control` maintainer — implementation already verified on our machine via `eval/safe_control_harness/run_dpcbf.sh` (Tracking finished, kinematic bicycle + dynamic obstacles). Direct path to P4 reactive-pedestrian stress test.
- **Suggested TODO**: 3-stage — (A) `eval/safe_control_harness/` sweep over obstacle count + speed, (B) integration spec for nav2_mppi critic, (C) C++ port follow-up. Filed as issue #33.

## 2026-05-25 20:03 — DualGuard MPPI: HJ Reachability + MPPI dual safety filtering
- **Source**: https://arxiv.org/abs/2502.01924
- **Type**: arxiv
- **Why relevant**: Two-stage safety filtering inside MPPI: (1) HJ reachability filters each sampled perturbation to produce provably safe rollouts, (2) safety filter on the selected control sequence before application. Achieves strict safety without sacrificing performance — more effective exploration with the same sample count. Directly applicable to our safety-aware MPPI work (CBF-MPPI thread) with a principled alternative to CBF constraints. RA-L 2026.
- **Suggested TODO**: compare DualGuard's HJ reachability filtering vs CBF-MPPI constraints in safe_control benchmark; evaluate integration path for nav2_mppi_controller.

## 2026-05-25 20:03 — Probabilistic Pedestrian Intent → Risk-Optimal Trajectories in Shared Spaces
- **Source**: https://www.mdpi.com/2079-8954/14/4/434
- **Type**: arxiv
- **Why relevant**: Prediction-driven planning framework with two modules: Social-STGCNN predicts pedestrian trajectories as probability distributions, then a risk-optimal planner generates trajectories that minimize collision risk. The *intent*-level prediction (beyond raw trajectory) adds anticipatory capability. P4-relevant: maps to our dynamic risk channel architecture where pedestrian predictions feed MPPI cost.
- **Suggested TODO**: study intent-to-risk pipeline as input architecture for P4 dynamic risk channel; compare with DRA-MPPI's Monte Carlo approach.

## 2026-05-25 14:00 — safe_control: CBF-QP / MPC-CBF / gatekeeper benchmark library (Taekyung Kim)

- **Source**: https://github.com/tkkim-robot/safe_control (264⭐, updated 5/23)
- **Type**: github
- **Why relevant**: Production-grade Python safety-critical control playground — CBF-QP, MPC-CBF, optimal-decay CBF, gatekeeper, C3BF/DPCBF for dynamic obstacles. Supports si/di/unicycle/bicycle/quadrotor/VTOL dynamics + RGB-D sensing sim + dynamic envs + multi-agent. **Could replace or augment our Gazebo-only sim playground for fast controller iteration before full sim**. License unstated → fork carefully.
- **Suggested TODO**: clone, run `examples/test_tracking.py --model du` (DynamicUnicycle2D), evaluate as offline test harness alongside our `eval/path_tracking_metrics.py`.

## 2026-05-25 14:00 — DR-MPC: Dynamics-Regularized MPC (RL+MPC residual for human avoidance + path tracking)

- **Source**: https://github.com/James-R-Han/DR-MPC · paper https://arxiv.org/abs/2410.10646 (36⭐, updated 5/21)
- **Type**: github + arxiv
- **Why relevant**: SAC RL learns **residual on top of MPC nominal** for path-tracking + human-avoidance simultaneously. Uses U Toronto's `pysteam` (SE(3) optimization). Modularized: `environment/{path_tracking, human_avoidance, HA_and_PT}` — direct mirror of our north-star formulation (avoidance + tracking together). Includes OOD pipeline + comparison across DRL/ResidualDRL/DR-MPC baselines.
- **Suggested TODO**: study DR-MPC's residual learning architecture; the `ResidualDRL` baseline they include is exactly our P2 (learning dynamics in MPPI rollout) integration template.

## 2026-05-25 14:00 — SCOPE: Stochastic Cartographic Occupancy Prediction Engine (89× faster)

- **Source**: https://arxiv.org/abs/2407.00144 (Xie & Dames, v2 2025-06)
- **Type**: arxiv
- **Why relevant**: Stochastic prediction of future occupancy under robot + dynamic obstacle + static geometry. Real-time optimized: **89× faster inference + 8× less memory** than SOTA. Generates *range of possible futures* (not single point estimate). Direct architectural reference for our P3 (risk/uncertainty channel) — SCOPE's stochastic output naturally feeds aleatoric+epistemic split.
- **Suggested TODO**: extract SCOPE's prediction tensor format; spec how it would feed our P3 BEV risk channel as a stochastic input.

## 2026-05-25 14:00 — Reference lineage doc — 4 papers as integrated R&D track

- **Source**: docs/cfm_mppi_integration_spec.md (#18) + new docs/reference_lineage.md
- **Type**: meta
- **Why relevant**: 4 references (cfm_mppi / DR-MPC / SCOPE / safe_control) form a coherent ecosystem mapping onto our P2-P4 work. safe_control = controller playground; DR-MPC = RL+MPC residual blueprint; SCOPE = stochastic prediction; cfm_mppi = generative trajectory prior. Worth a single doc tying them.
- **Suggested TODO**: write `docs/reference_lineage.md` showing how each maps to a Phase, with adopt/inspire/skip decisions.

---

## 2026-05-25 12:02 — DRA-MPPI: Dynamic Risk-Aware MPPI for Mobile Robots in Crowds
- **Source**: https://arxiv.org/abs/2506.21205
- **Type**: arxiv
- **Why relevant**: Incorporates non-Gaussian stochastic human trajectory predictions into MPPI via efficient Monte Carlo collision probability approximation. Solves the freezing robot problem while improving safety among pedestrians. P4-relevant: directly applicable architecture for our dynamic risk channel — collision probability as MPPI cost vs. hard constraint rejection of risky samples.
- **Suggested TODO**: study DRA-MPPI's Monte Carlo collision probability integration for P4 dynamic obstacle avoidance.

## 2026-05-25 12:02 — Step-MPPI: Single-Step MPPI via Learned Sampling Distribution
- **Source**: https://arxiv.org/abs/2604.01539
- **Type**: arxiv
- **Why relevant**: Replaces hand-tuned MPPI sampling covariance with a neural network trained self-supervised on MPC cost + entropy regularization, enabling single-step lookahead with multi-step foresight. As our MPPI input dimensionality grows with BEV channels (P1/P3), learned proposal distributions could dramatically reduce sample count needed for convergence.
- **Suggested TODO**: evaluate Step-MPPI's learned distribution approach as alternative to manual covariance tuning in nav2_mppi_controller.

## 2026-05-25 08:00 — mppi_numba: GPU MPPI with Probabilistic Traversability
- **Source**: https://github.com/mit-acl/mppi_numba
- **Type**: github
- **Why relevant**: GPU-accelerated MPPI implementation with a probabilistic traversability model that plans risk-aware trajectories using CVaR (Conditional Value at Risk). Seminal reference for our P3 risk/uncertainty field — demonstrates how location-dependent parameter distributions in a 3D tensor can feed directly into MPPI rollout cost evaluation.
- **Suggested TODO**: study mppi_numba's traversability tensor structure as reference architecture for our P3 risk field channels.

## 2026-05-25 08:00 — SocialNav-Map: Dynamic Mapping with Human Trajectory Prediction
- **Source**: https://arxiv.org/abs/2511.12232
- **Type**: arxiv
- **Why relevant**: Zero-shot social navigation via dynamic occupancy mapping that integrates predicted human trajectories. Reduces human collision rates by 10%+ without environment-specific training. P4-relevant: the "predict human paths → update dynamic map → planner avoids" pipeline maps directly to our architecture where BEV dynamic channels feed MPPI cost.
- **Suggested TODO**: evaluate SocialNav-Map's prediction-to-map pipeline as input architecture for our P4 dynamic risk channel.

## 2026-05-25 04:02 — Gauss-Newton Accelerated MPPI Control
- **Source**: https://arxiv.org/abs/2512.04579
- **Type**: arxiv
- **Why relevant**: Incorporates 2nd-order Generalized Gauss-Newton optimization into MPPI via Jacobian reconstruction, substantially improving scalability to high-dimensional systems. Directly relevant as we scale MPPI input from 2D costmap to multi-channel BEV (P1/P3) — higher-dim representation needs efficient sampling.
- **Suggested TODO**: evaluate GN-MPPI's Jacobian reconstruction applicability when MPPI input dimensionality grows with BEV channels.

## 2026-05-25 04:02 — Action-to-Action Flow Matching (single-step inference)
- **Source**: https://arxiv.org/abs/2602.07322
- **Type**: arxiv
- **Why relevant**: Shifts flow matching initialization from random noise to previous action (warm-start), enabling single-step inference. Directly parallels MPPI's receding-horizon warm-start paradigm. If we adopt CFM for trajectory proposals (cfm_mppi thread), A2A's warm-start could reduce inference from multi-step to single-step at control frequency.
- **Suggested TODO**: compare A2A warm-start mechanism with MPPI's shift-and-resample for potential hybrid approach.

## 2026-05-25 04:02 — Halton-Sampling MPPI for Smooth Ground Vehicle Trajectories
- **Source**: https://www.mdpi.com/2504-446X/10/2/96
- **Type**: arxiv
- **Why relevant**: Replaces Gaussian noise with low-discrepancy Halton sequences for better spatial coverage, adds Ornstein-Uhlenbeck process for temporal correlation between successive control perturbations. Produces smoother trajectories for ground vehicles. Direct sampling improvement for our MPPI — better coverage with fewer samples means faster convergence.
- **Suggested TODO**: prototype Halton sequence noise injection in nav2_mppi_controller's noise generator, compare sample efficiency vs Gaussian baseline.

## 2026-05-25 00:00 — Energy-based Regularization for Residual Dynamics in Neural MPC
- **Source**: https://arxiv.org/abs/2604.14678
- **Type**: arxiv
- **Why relevant**: Proposes energy-based regularization loss for training residual dynamics models in MPC. 23% positional accuracy improvement over analytical MPC. Directly applicable to P2 (learning dynamics integration) — regularization technique prevents learned residual from destabilizing the system. Code available.
- **Suggested TODO**: review energy-based loss formulation, evaluate if applicable to our differential-drive residual dynamics model.

## 2026-05-25 00:00 — Ensemble Residual Dynamics for MPC Path Tracking
- **Source**: https://doi.org/10.3390/s26010340
- **Type**: arxiv
- **Why relevant**: Ensemble learning-based residual dynamics refinement for MPC with feature-driven activation — selectively applies residual correction only when nonlinear behaviors arise. P2-relevant: our residual dynamics model could benefit from ensemble uncertainty + selective activation gate.
- **Suggested TODO**: check if ensemble approach is compatible with MPPI's parallel rollout architecture.

## 2026-05-25 00:00 — NRSeg: Noise-Resilient BEV Segmentation via World Models
- **Source**: https://arxiv.org/abs/2507.04002
- **Type**: arxiv
- **Why relevant**: Uses synthetic data from driving world models to augment BEV segmentation training, with noise-resilient learning (13.8% mIoU gain). P1-relevant: if we generate BEV training data from Gazebo sim, their noise-handling techniques (PGCM metric, BiDPP prediction) could improve our multi-channel BEV quality.
- **Suggested TODO**: evaluate PGCM metric applicability when training BEV model on Gazebo-generated data.

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

---
