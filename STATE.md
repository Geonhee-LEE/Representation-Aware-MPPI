# Research State — auto-generated each cycle

_Last updated: 2026-05-25 03:00 KST · cycle p2-flow-planner-nav2-mapping_

## North star distance

Still **0 measured numbers** — user sim run for `runs/cafe-001.json` remains unexecuted (14+ days). P2 design landscape is now complete: TCFM architecture (PR #22), synthetic dataset generator (PR #23), energy-based regularizer (PR #24), and Flow Planner Nav2 mapping (PR #25). Four PRs await merge; once #23 lands, TCFM training becomes feasible.

## Current bottleneck

**No trained TCFM model yet (P2)**. Four prerequisite PRs (#22–#25) need merging. PR #23 (dataset generator) is the critical-path dependency for the training TODO.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-flow-planner-nav2-mapping` | 2026-05-25 03:00 | qual:doc-only | 0 (PR #25 open) |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | 2026-05-25 02:00 | qual:script-syntax-ok | 0 (PR #24 open) |
| `autoresearch/p2-unicycle-dataset-generator` | 2026-05-25 01:00 | qual:script-syntax-ok | 0 (PR #23 open) |
| `autoresearch/p2-tcfm-evaluation` | 2026-05-25 00:00 | qual:doc-only | 0 (PR #22 open) |
| `autoresearch/p0-state-template-split-next-priorities` | 2026-05-10 18:08 | qual:doc-only | 15 (PR #12 open) |

## Recent learnings (last 3 cycles)

- Flow Planner's `StatefulHierarchicalPlanner` is structurally identical to Nav2's global/local split — confirms "local-only CFM" is the right integration depth for our project.
- The local planner conditioning on `(current_state, subgoal)` is a confirmed cross-project pattern (Flow Planner + cfm_mppi) — this is exactly how TCFM should interface with MPPI.
- MLP backbone with sinusoidal time + FiLM conditioning may be a lighter alternative to TemporalUnet for short-horizon 2D unicycle action generation.

## Next claude-actionable (this cycle would pick from here)

1. **`36ac5d39…81a7`** Adapt TCFM TemporalUnet config for 2D unicycle (5-dim state, 2-dim action) + train on synthetic dataset — first learned dynamics model for P2. Blocked until PR #23 merges to main.
2. **(new candidate)** Evaluate MLP backbone (Flow Planner style) as lightweight TCFM alternative — could prototype without PR merge dependency if using inline synthetic data.
3. **`36ac5d39…81df`** [research] Evaluate NRSeg noise-resilient BEV segmentation for Gazebo-trained models — P1 future work. Owner=claude, P1, Backlog.

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json` (first quantitative baseline). Owner=user, NeedsUserTest=true. 14+ days carrying.
2. **(implicit)** Merge PR #12 + PR #22 + PR #23 + PR #24 + PR #25 — doc/script-only, low-risk. Unblocks TCFM training TODO.
3. **(implicit)** Install PyTorch in project venv — needed to run `learning/` modules and future training.

## Cycles to date

- 이번 주 (Mon 2026-05-19 시작): **4** (four consecutive P2 cycles — TCFM eval, dataset gen, energy reg, Flow Planner mapping)
- 프로젝트 통합: **13**
