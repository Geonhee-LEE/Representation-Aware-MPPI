# Research State — auto-generated each cycle

_Last updated: 2026-06-09 00:00 KST · cycle p2-online-adaptation-comparison_

## North star distance

Still **0 measured numbers** — `runs/cafe-001.json` baseline remains uncaptured
(user-blocked sim). P2 design is well-converged: build-first architecture decided
(D-009 MLP-ensemble K=3, offline-frozen) AND the next layer scoped (online adaptation,
Q-008 leans function-encoder+RLS). But **nothing P2 has reached main** — the entire
implementation track is stalled behind unmerged PRs.

## Current bottleneck

**P2 implementation is fully PR-merge-blocked, and the executor was silently stalled
for ~9 days behind it.** Every P2-impl TODO (ensemble wrapper, training pipeline,
rollout integration) depends on PR #44 (scaffold) + #23 (unicycle dataset) landing on
main. Those merges are user-owned. Until they land, the executor can only advance
*design* (done: D-009 arch, Q-008 online layer), not *code*. Draining the PR queue is
the single unblock.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-online-adaptation-comparison` | 2026-06-09 00:00 | qual:doc-only (Q-008) | 0 (PR #48 open) |
| `autoresearch/p2-residual-dynamics-mlp-scaffold` | ~05-31 | nominal + MLP-ensemble scaffold | ~9 (PR #44) |
| `autoresearch/p2-training-data-collection` | ~06 | replay buffer + scripted rollouts | (PR #45) |
| `autoresearch/p0-gate1-exclude-closed-pr-branches` | ~06 | gate-1 count fix | (PR #47) |
| `autoresearch/p2-unicycle-dataset-generator` | ~05-25 | dataset gen | ~15 (PR #23) |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | ~05-26 | energy reg | ~14 (PR #24) |

## Recent learnings (last 3 cycles)

- **(this cycle)** PR-blocked TODOs left in `Doing` silently re-arm gate-2 every cycle
  → a 9-day stall. Durable fix: PR-dependency items live in `Today` (feasibility filter
  skips them), never `Doing`. Self-healed 2 zombies this cycle.
- **(this cycle)** Online adaptation is empirically gated, not committed — wire RLS only
  after measured OOD rollout drift exceeds MPPI cost sensitivity, never preemptively.
- **(p2-decision-matrix)** A decision gate (D-009) beat a 9th isolated analysis; the
  ensemble's variance is the cheapest path to a P3 epistemic channel.

## Next claude-actionable (this cycle would pick from here)

1. **`36dc5d39…4402`** Extend `gen_unicycle_dataset.py` with `--meta` task distribution
   — feasible NOW (script/doc, no PR dependency), unblocks MAML + OOD-probe data.
2. **`36ac5d39…b571`** Implement EnsembleResidualDynamics wrapper (K=3) — back in Today;
   _PR-dependency-blocked on #44/#23, auto-feasible once they land. Skip until then._
3. **`371c5d39…3c48`** Residual-dynamics training-data pipeline (s,a,s_next → residual
   target) — back in Today; _same #44/#23 dependency, skip until merged._

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **Drain PR queue** (#23 #24 #44 #45 #47 #48) — executor gate-1 at 5/6; merging #44+#23
   unblocks the entire P2 implementation track. Highest leverage.
2. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` →
   `runs/cafe-001.json` (first quantitative baseline). Owner=user, ~17 days open.
3. **`36bc5d39`** Install PyTorch in dev env — blocks executor-side ML training validation.

## Cycles to date

- 이번 주 (Mon 2026-06-08 시작): this cycle
- 프로젝트 통합: ~19 (per merged PR #41 + journal history + 6 in-flight)
