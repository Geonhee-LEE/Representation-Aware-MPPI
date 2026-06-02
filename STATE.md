# Research State — auto-generated each cycle

_Last updated: 2026-05-31 00:00 KST · cycle p2-residual-dynamics-decision-matrix_

## North star distance

Still **0 measured numbers** — user sim run for `runs/cafe-001.json` remains
unexecuted (P5 quant harness exists but no baseline captured). P2 progress is now
**design-converged, not just exploring**: D-009 commits the first residual
architecture to build (MLP-ensemble K=3, offline-frozen), so the next concrete
step is implementation, not more analysis.

## Current bottleneck

**P2 implementation is gated on PR merges, not design.** The build-first
architecture is decided (D-009); the `EnsembleResidualDynamics` wrapper + MPPI
rollout integration depend on the unicycle dataset generator (#23) reaching main.
PR queue is at **6/6** — draining it is the single unblock.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-residual-dynamics-decision-matrix` | 2026-05-31 00:00 | qual:doc-only (D-009) | 0 (PR #43 open) |
| `autoresearch/p2-unicycle-dataset-generator` | ~05-25 | dataset gen | ~6 (PR #23) |
| `autoresearch/p2-mlp-cfm-velocity-field` | ~05-27 | MLP CFM field | (PR #26) |
| `autoresearch/p2-ensemble-residual-dynamics-compat` | ~05-27 | ensemble compat | (PR #27) |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | ~05-26 | energy reg | (PR #24) |
| `autoresearch/p2-flow-planner-nav2-mapping` | ~05-24 | flow-planner map | (PR #25) |

## Recent learnings (last 3 cycles)

- **(this cycle)** The P2 bottleneck was *convergence*, not data — 5 open analysis
  PRs with no decision gate. A decision matrix + ADR (D-009) beat a 9th analysis.
- **(this cycle)** Perpetually-`Doing` zombie TODOs are themselves a silent-stall
  mechanism; executor self-healed two (issue #13/#14) instead of skipping.
- **(p2-maml)** MAML/energy-reg/ensemble compose as a design triad; ensemble
  variance is the cheapest path to a P3 epistemic channel.

## Next claude-actionable (this cycle would pick from here)

1. **`36ac5d39…b571`** Implement `EnsembleResidualDynamics` wrapper (K=3 heads,
   bootstrap, var→epistemic) per D-009 — _feasible once #23 (unicycle dataset)
   lands on main; currently PR-dependency-blocked, stays Today._
2. **`357c5d39…d0d8a`** Write MPPI rollout integration point (swap analytic
   dynamics for learned) — pairs with #1; same #23/#27 merge dependency.
3. **`36bc5d39…188a`** [setup] Install PyTorch in dev env — unblocks executor-side
   ML validation (training smoke for the ensemble).

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **Drain PR queue 6/6** (#23 #24 #25 #26 #27 #43) — executor gate-1 is now at
   cap; no new branch until Curator (23:00) or a manual merge drains it.
2. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` →
   `runs/cafe-001.json` (first quantitative baseline). Owner=user, 20+ days.
3. **`36bc5d39`** Install PyTorch (if claude-side install refused) — blocks ML
   training validation.

## Cycles to date

- 이번 주 (Mon 2026-05-25 시작): includes this cycle
- 프로젝트 통합: ~16 (per latest merged PR #41 + 6 in-flight)
