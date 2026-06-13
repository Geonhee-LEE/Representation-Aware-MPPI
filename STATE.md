# Research State — auto-generated each cycle

_Last updated: 2026-06-12 01:00 KST · cycle p3-residual-rollout-epistemic-ref_

## North star distance

Still **0 measured numbers** — first quantitative baseline (`runs/cafe-001.json`)
remains unrun (Owner=user). Phase clock advanced to **P3** (risk/uncertainty fields)
on 2026-06-12. P2 build path (D-009 MLP-ensemble residual) is **one user-merge from
main** but has been merge-blocked for 9 days. This cycle de-risked the keystone
`EnsembleResidualDynamics` wrapper (concrete batched-rollout wiring spec) and produced
the first in-phase P3 artifact (variance→margin epistemic-channel design).

## Current bottleneck

**Human merge bandwidth on build-path code PRs — not analysis throughput.** The
gate-1 deadlock re-formed within 3 days of the last break because the *root fix*
(D-011 / PR #47) is itself stuck in the merge queue. Build-path PRs #44 (D-009
scaffold, keystone), #45 (training-data), #23 (dataset gen) need human merge — Curator
auto-merges only safe-surface docs, and the executor cannot merge to main. Until
#44/#45 land, every P2 code step is PR-dependency-blocked (feasibility filter), so the
executor is working the independent P3 design lane instead.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p3-residual-rollout-epistemic-ref` | 2026-06-12 01:00 | residual-in-rollout + variance→margin ref, **doc-only** | 0 (PR pending) |
| `autoresearch/p0-gate1-exclude-closed-pr-branches` | 2026-06-09 | D-011 root gate fix, **MERGEABLE** | ~3 (PR #47) |
| `autoresearch/p2-residual-dynamics-mlp-scaffold` | 2026-06-09 | D-009 scaffold (keystone) | ~9 (PR #44) |
| `autoresearch/p2-training-data-collection` | 2026-06-09 | replay buffer | ~9 (PR #45) |
| `autoresearch/p2-unicycle-dataset-generator` | 2026-06-09 | dataset gen | ~15 (PR #23) |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | 2026-06-09 | energy reg | ~15 (PR #24) |

_(PR #48 online-adaptation-comparison closed this cycle per D-010 — superseded by D-009, reopenable in 1 click for U2.)_

## Recent learnings (last 3 cycles)

- **(this cycle)** The K=3 ensemble batches *more easily* than a GP residual: matmul on
  the flattened `[M·T,d]` rollout batch, solver-free — the Stochastic-MPPI "residual
  must be a tensor op that batches with the sampler" constraint is satisfied for free.
- **(this cycle)** Gate-1 keeps re-forming because the root fix (#47) is stuck behind
  the same human-merge bottleneck it tries to fix; self-healing buys cycles but the
  user merging #44/#47 is the only durable fix.
- **(D-011/06-09)** Committing derived snapshot files (STATE/JOURNAL/RESULTS) on feature
  branches was the conflict surface that froze the queue; stripping them is the structural fix.

## Next claude-actionable (this cycle would pick from here)

1. **Spec the P3 epistemic-channel BEV rendering** (σ²→ego-frame grid) — feasible
   without the ensemble code (pure design/interface doc), continues the P3 lane started
   this cycle. Why-now: build lane stays merge-blocked; this is independent forward motion.
2. **Spec the margin-inflation cost-critic interface** (where `k·σ` enters the nav2_mppi
   collision/barrier term) — feasible doc/interface step, sets up Q-008's `k` knob. Why-now:
   pairs with #1, both de-risk P3 before any code merges.

_(Both are doc/interface steps — safe-surface, Curator-drainable, no PR-dependency.
The P2 code TODOs — EnsembleResidualDynamics wrapper, MPPI rollout integration — stay
infeasible until #44/#45 reach main.)_

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **Merge build-path PRs #44 (keystone) → #45 → #23, and #47 (D-011 root gate fix).**
   These need human review (touch `learning/`/`scripts/`), Curator won't auto-merge them.
   Until they land, the P2 code lane is fully blocked and gate-1 keeps re-forming. Run
   `bash scripts/aggregate_results.sh` on main afterward.
2. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` →
   `runs/cafe-001.json` (first quantitative baseline). Owner=user, 25+ days.
3. **`36bc5d39`** Install PyTorch (if claude-side install refused) — blocks ML
   training validation.

## Cycles to date

- 이번 주: 1 productive cycle (P3 design lane opened; gate-1 self-healed again).
- 프로젝트 통합: ~19 productive cycles.
