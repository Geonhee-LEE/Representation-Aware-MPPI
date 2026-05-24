# Research State — auto-generated each cycle

_Last updated: 2026-05-25 02:00 KST · cycle p2-energy-based-residual-dynamics-reg_

## North star distance

Still **0 measured numbers** — user sim run for `runs/cafe-001.json` remains unexecuted (14+ days). P2 now has three executable artifacts: TCFM architecture evaluation (PR #22), synthetic trajectory dataset generator (PR #23), and energy-based regularizer prototype (PR #24). The training pipeline is architecturally complete on the claude side — nominal dynamics + residual MLP + stability guarantee + training loop — but all three PRs await merge to main.

## Current bottleneck

**No trained TCFM model yet (P2)**. Three prerequisite PRs (#22, #23, #24) need merging. Once PR #23 (dataset generator) lands on main, the TCFM TemporalUnet training TODO becomes feasible with the energy regularizer from PR #24 ready to plug in.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-energy-based-residual-dynamics-reg` | 2026-05-25 02:00 | qual:script-syntax-ok | 0 (PR #24 open) |
| `autoresearch/p2-unicycle-dataset-generator` | 2026-05-25 01:00 | qual:script-syntax-ok | 0 (PR #23 open) |
| `autoresearch/p2-tcfm-evaluation` | 2026-05-25 00:00 | qual:doc-only | 0 (PR #22 open) |
| `autoresearch/p0-state-template-split-next-priorities` | 2026-05-10 18:08 | qual:doc-only | 15 (PR #12 open) |

## Recent learnings (last 3 cycles)

- Kinetic energy V = 0.5(v² + ω²) is the simplest goal-free energy function for unicycle stability; hinge formulation allows energy-reducing corrections (friction modeling) while preventing blow-up.
- dt=0.1s with 64-step horizon (6.4s) provides reasonable trajectory variety for TCFM training; first-order velocity lag produces smooth acceleration profiles.
- TCFM and cfm_mppi are complementary: TCFM provides the velocity-field backbone + training pipeline, cfm_mppi provides the MPPI integration pattern. Option A (trajectory generator) is the simpler P2 prototype path.

## Next claude-actionable (this cycle would pick from here)

1. **`36ac5d39…81a7`** Adapt TCFM TemporalUnet config for 2D unicycle (5-dim state, 2-dim action) + train on synthetic dataset — first learned dynamics model for P2. Blocked until PR #23 merges to main.
2. **`36ac5d39…81ec`** [research] Map Flow Planner hierarchical CFM onto Nav2 global/local split — completes P2 design landscape. Owner=claude, P2, Today. No PR dependency.
3. **`36ac5d39…81df`** [research] Evaluate NRSeg noise-resilient BEV segmentation for Gazebo-trained models — P1 future work. Owner=claude, P1, Backlog.

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json` (first quantitative baseline). Owner=user, NeedsUserTest=true. 14+ days carrying.
2. **(implicit)** Merge PR #12 + PR #22 + PR #23 + PR #24 — doc/script-only, low-risk. Unblocks TCFM training TODO.
3. **(implicit)** Install PyTorch in project venv — needed to run `learning/` modules and future training.

## Cycles to date

- 이번 주 (Mon 2026-05-19 시작): **3** (three consecutive P2 cycles)
- 프로젝트 통합: **12**
