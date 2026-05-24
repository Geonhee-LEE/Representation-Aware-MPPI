# Research State — auto-generated each cycle

_Last updated: 2026-05-25 05:00 KST · cycle p2-ensemble-residual-dynamics-compat_

## North star distance

Still **0 measured numbers**. P2 now has a complete model stack: MLP CFM velocity field, energy-based regularizer, and a quantitative ensemble feasibility analysis confirming the architecture for P3's epistemic uncertainty channel. All implementation artifacts await PyTorch install for training validation. Once training converges and ensemble wrapper is built, MPPI rollouts gain both a learned dynamics predictor and free uncertainty estimates.

## Current bottleneck

**PyTorch not installed — cannot validate MLP CFM training convergence or build ensemble wrapper (P2)**. Six prerequisite PRs (#12, #22–#27) also need merging to consolidate P2 design artifacts on main.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-ensemble-residual-dynamics-compat` | 2026-05-25 05:00 | qual:script-syntax-ok | 0 (PR #27 open) |
| `autoresearch/p2-mlp-cfm-velocity-field` | 2026-05-25 04:00 | qual:script-syntax-ok | 0 (PR #26 open) |
| `autoresearch/p2-flow-planner-nav2-mapping` | 2026-05-25 03:00 | qual:doc-only | 0 (PR #25 open) |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | 2026-05-25 02:00 | qual:script-syntax-ok | 0 (PR #24 open) |
| `autoresearch/p2-unicycle-dataset-generator` | 2026-05-25 01:00 | qual:script-syntax-ok | 0 (PR #23 open) |
| `autoresearch/p2-tcfm-evaluation` | 2026-05-25 00:00 | qual:doc-only | 0 (PR #22 open) |

## Recent learnings (last 3 cycles)

- Ensemble-3 residual MLP (584M FLOPs) fits comfortably in MPPI's 1000×20 rollout budget; CFM ensemble (140G) does not — ensemble the residual, not the CFM.
- MLP + FiLM (162 LOC) is dramatically simpler than TemporalUnet (~500+ LOC) — viable for rapid P2 iteration on 5D unicycle dynamics.
- Euler integration step count is a hidden FLOPs multiplier: any model evaluated via multi-step ODE integration must include this in budget analysis.

## Next claude-actionable (this cycle would pick from here)

1. **`36ac5d39…81df`** [research] Evaluate NRSeg noise-resilient BEV segmentation for Gazebo-trained models — P1 future work, Backlog. Owner=claude.
2. **(author if needed)** Compare A2A warm-start mechanism with MPPI's shift-and-resample — new research feed entry (2026-05-25), P2-relevant.

_Note: All high-priority P2 TODOs (MLP convergence, ensemble wrapper, TCFM training) require PyTorch install. Next executor cycle will pick NRSeg research TODO or author a new analysis task from the research feed._

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json` (first quantitative baseline). Owner=user. 14+ days.
2. **(implicit)** Install PyTorch in project venv — needed to run `learning/mlp_cfm_unicycle.py`, energy regularizer, and future ensemble wrapper.
3. **(implicit)** Merge PR cluster #12, #22–#27 — all doc/script-only, low-risk. Consolidates P2 design artifacts on main.

## Cycles to date

- 이번 주 (Mon 2026-05-19 시작): **6** (six consecutive P2 cycles)
- 프로젝트 통합: **15**
