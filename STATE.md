# Research State — auto-generated each cycle

_Last updated: 2026-05-28 02:00 KST · cycle p2-maml-residual-adaptation_

## North star distance

Still **0 measured numbers** — user sim run for `runs/cafe-001.json` unexecuted (18+ days), PyTorch not installed (blocks all ML execution). However, P2's learned dynamics design is now **fully specified**: residual MLP architecture + energy-based regularization (stability) + ensemble dynamics (uncertainty) + MAML meta-learning (sim-to-real adaptation). Six research PRs (#22–27, #41) carrying — awaiting user merge to land artifacts on main.

## Current bottleneck

**PyTorch not installed + 6 unmerged doc-only PRs block P2 execution.** Design phase is complete — the next progress requires either (a) PyTorch install to begin model training, or (b) PR merges to land P2 design artifacts on main and unblock dependent TODOs (TCFM training config depends on PR #23).

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-maml-residual-adaptation` | 2026-05-28 02:00 | qual:doc-only | 0 (PR #41 open) |
| `autoresearch/p2-unicycle-dataset-generator` | 2026-05-25 01:00 | qual:script-syntax-ok | 3 (PR #23 open) |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | 2026-05-25 02:00 | qual:doc-only | 3 (PR #24 open) |
| `autoresearch/p2-flow-planner-nav2-mapping` | 2026-05-25 03:00 | qual:doc-only | 3 (PR #25 open) |
| `autoresearch/p2-mlp-cfm-velocity-field` | 2026-05-25 04:00 | qual:doc-only | 3 (PR #26 open) |
| `autoresearch/p2-ensemble-residual-dynamics-compat` | 2026-05-25 05:00 | qual:doc-only | 3 (PR #27 open) |

## Recent learnings (last 3 cycles)

- **(this cycle)** MAML wraps the existing residual MLP training — no architecture change. Energy reg composes (apply in both inner+outer loops). Three P2 analysis docs (energy, ensemble, MAML) form a coherent design specification.
- **(p2-tcfm-evaluation)** TCFM and cfm_mppi are complementary — TCFM provides backbone, cfm_mppi provides MPPI integration. Option A (trajectory generator) is the simpler P2 prototype path.
- **(p0-state-template-split)** Structural STATE template fixes (claude-actionable vs user-blocked sections) prevent Owner-mismatch errors.

## Next claude-actionable (this cycle would pick from here)

1. **`(author new)`** Extend `gen_unicycle_dataset.py` with `--meta` flag for MAML task-distributed data generation — prerequisite for MAML training, implementable without PyTorch. Pure Python.
2. **`36cc5d39`** [research] Evaluate TC-MPPI time-correlated sampling as smoothness mechanism for nav2_mppi_controller — P1, P2, Backlog. Sampling-layer improvement complementary to learned dynamics.
3. **`(author new)`** Consolidate P2 learned dynamics design spec into single `docs/p2_learned_dynamics_spec.md` — synthesize energy reg + ensemble + MAML + TCFM analyses into unified architecture document.

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **`36bc5d39`** [setup] Install PyTorch in dev env — executor ML validation blocked (TCFM, ensemble dynamics, MLP backbone). Owner=user, P1.
2. **(implicit)** Merge PR cluster: #22 (TCFM eval), #23 (dataset gen), #24 (energy reg), #25 (flow planner), #26 (MLP CFM), #27 (ensemble), #41 (MAML) — all doc-only, low-risk.
3. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` → capture `runs/cafe-001.json`. Owner=user, 18+ days carrying.

## Cycles to date

- 이번 주 (Mon 2026-05-26 시작): **1**
- 프로젝트 통합: **11**
