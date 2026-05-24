# Research State — auto-generated each cycle

_Last updated: 2026-05-25 04:00 KST · cycle p2-mlp-cfm-velocity-field_

## North star distance

Still **0 measured numbers**. P2 now has a complete model implementation (MLP CFM velocity field) ready for training, but PyTorch is not installed in the project environment. Once PyTorch is available and training converges, this model's `sample_cfm()` becomes the dynamics predictor that MPPI rollouts consume — closing the gap from "no learned dynamics" to "trained dynamics model ready for integration."

## Current bottleneck

**PyTorch not installed — cannot validate MLP CFM training convergence (P2)**. Five prerequisite PRs (#12, #22–#26) also need merging to consolidate the P2 design artifacts on main.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-mlp-cfm-velocity-field` | 2026-05-25 04:00 | qual:script-syntax-ok | 0 (PR #26 open) |
| `autoresearch/p2-flow-planner-nav2-mapping` | 2026-05-25 03:00 | qual:doc-only | 0 (PR #25 open) |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | 2026-05-25 02:00 | qual:script-syntax-ok | 0 (PR #24 open) |
| `autoresearch/p2-unicycle-dataset-generator` | 2026-05-25 01:00 | qual:script-syntax-ok | 0 (PR #23 open) |
| `autoresearch/p2-tcfm-evaluation` | 2026-05-25 00:00 | qual:doc-only | 0 (PR #22 open) |

## Recent learnings (last 3 cycles)

- MLP + FiLM (162 LOC) is dramatically simpler than TemporalUnet (~500+ LOC) — viable for rapid P2 iteration on 5D unicycle dynamics.
- Inline synthetic data generation decouples model development from the PR merge queue (PR #23 no longer on critical path for training experiments).
- OT-CFM loss (MSE on linear-interpolation velocity) is implementation-trivial compared to VP-SDE — good default for our scale.

## Next claude-actionable (this cycle would pick from here)

1. **`36ac5d39…81df`** [research] Evaluate NRSeg noise-resilient BEV segmentation for Gazebo-trained models — P1 future work, Backlog. Owner=claude.
2. **(author if needed)** Ensemble residual dynamics compatibility check with MPPI parallel rollouts — from research/feed.md, P2-relevant.

_Note: All high-priority P2 TODOs (TCFM TemporalUnet training, MLP convergence validation) are now user-blocked on PyTorch install. Next executor cycle will likely pick the NRSeg research TODO or author a new analysis task._

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json` (first quantitative baseline). Owner=user. 14+ days.
2. **(implicit)** Install PyTorch in project venv — needed to run `learning/mlp_cfm_unicycle.py` and validate convergence.
3. **(implicit)** Merge PR cluster #12, #22–#26 — all doc/script-only, low-risk. Consolidates P2 design artifacts on main.

## Cycles to date

- 이번 주 (Mon 2026-05-19 시작): **5** (five consecutive P2 cycles)
- 프로젝트 통합: **14**
