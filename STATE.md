# Research State — auto-generated each cycle

_Last updated: 2026-05-25 01:00 KST · cycle p2-unicycle-dataset-generator_

## North star distance

Still **0 measured numbers** — user sim run for `runs/cafe-001.json` remains unexecuted (14+ days). However, P2 now has its first executable artifact: a synthetic trajectory dataset generator that removes the "no training data" blocker. The path from data generation → TCFM training → MPPI integration is fully unblocked on the claude side. Two consecutive P2 cycles (TCFM evaluation + dataset generator) have broken the 15-day drought.

## Current bottleneck

**No trained TCFM model yet (P2)**. The dataset generator exists; next step is adapting TCFM's TemporalUnet config for 2D unicycle (5-dim state, 2-dim action) and running a training experiment on the synthetic data.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-unicycle-dataset-generator` | 2026-05-25 01:00 | qual:script-syntax-ok | 0 (PR #23 open) |
| `autoresearch/p2-tcfm-evaluation` | 2026-05-25 00:00 | qual:doc-only | 0 (PR #22 open) |
| `autoresearch/p0-state-template-split-next-priorities` | 2026-05-10 18:08 | qual:doc-only | 15 (PR #12 open) |

## Recent learnings (last 3 cycles)

- **(this cycle)** dt=0.1s (10Hz) with 64-step horizon (6.4s) provides reasonable trajectory variety for TCFM training; first-order velocity lag produces smooth acceleration profiles without complexity.
- **(prev cycle)** TCFM and cfm_mppi are complementary — TCFM provides the velocity-field backbone + training pipeline, cfm_mppi provides the MPPI integration pattern. Option A (trajectory generator) is the simpler P2 prototype path.
- **(prev cycle)** CFM's speed advantage is architecturally simple: single ODE solve (~100 Euler steps) replaces diffusion's ~1000 denoising steps, making real-time MPPI feasible.

## Next claude-actionable (this cycle would pick from here)

1. **`(author new)`** Adapt TCFM TemporalUnet config for 2D unicycle (5-dim state, 2-dim action) + train on synthetic dataset — first learned dynamics model for P2.
2. **`36ac5d39…8166`** [research] Review energy-based regularization for residual dynamics in neural MPC (arxiv 2604.14678) — stability guarantee for P2 learned dynamics. Owner=claude, P2, Backlog.
3. **`36ac5d39…81ec`** [research] Map Flow Planner hierarchical CFM onto Nav2 global/local split — completes P2 design landscape. Owner=claude, P2, Today.

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json` (first quantitative baseline). Owner=user, NeedsUserTest=true, P0. 14+ days carrying.
2. **(implicit)** Merge PR #12 (STATE template split) + PR #22 (TCFM evaluation) + PR #23 (dataset generator) — doc/script-only, low-risk.

## Cycles to date

- 이번 주 (Mon 2026-05-19 시작): **2** (consecutive P2 cycles after 15-day drought)
- 프로젝트 통합: **11**
