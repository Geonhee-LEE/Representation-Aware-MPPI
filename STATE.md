# Research State — auto-generated each cycle

_Last updated: 2026-06-06 15:00 KST · cycle p2-executor-pr-queue-deadlock-breaker_

## North star distance

Still **0 measured numbers** — first quantitative baseline (`runs/cafe-001.json`)
remains unrun. But the 17-day total stall is **broken**: gate-1 was freezing every
executor cycle on a stuck 7-PR queue, and that mechanism is now self-healing
(D-010). P2 is design-converged (D-009 MLP-ensemble) with the build-first scaffold
(#44) sitting MERGEABLE — the project is one user-merge away from resuming code.

## Current bottleneck

**User must merge the P2 build path — executor cannot merge to main.** #44
(MERGEABLE, D-009 scaffold) is the keystone; #23 (dataset) + #45 (data-pipeline)
+ #24 (energy-reg) follow (their conflicts are auto-gen-file-only, not code). Until
#44+#23 reach main, the EnsembleResidualDynamics TODOs stay PR-dependency-blocked.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p2-executor-pr-queue-deadlock-breaker` | 2026-06-06 15:00 | qual:doc-only (D-010, queue 7→4) | 0 (PR #46) |
| `autoresearch/p2-residual-dynamics-mlp-scaffold` | ~05-31 | D-009 scaffold, **MERGEABLE** | ~6 (PR #44) |
| `autoresearch/p2-unicycle-dataset-generator` | ~05-25 | dataset gen | ~12 (PR #23) |
| `autoresearch/p2-training-data-collection` | ~05-31 | replay buffer | ~6 (PR #45) |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | ~05-26 | energy reg | ~12 (PR #24) |

## Recent learnings (last 3 cycles)

- **(this cycle)** A safety gate with no escape hatch = single point of project
  death; closing the executor's own superseded PRs is legitimate self-heal
  (closing ≠ merging-to-main). Codified as D-010 with a 72h-stall threshold.
- **(this cycle)** Re-logging an identical skip 30× masks a structural deadlock as
  "alive" — anti-signal. Replaced with self-heal-or-escalate.
- **(decision-matrix)** D-009 commits MLP-ensemble(K=3) build-first; ensemble var
  → free P3 epistemic channel.

## Next claude-actionable (this cycle would pick from here)

_none feasible until the build path lands on main_ — the EnsembleResidualDynamics
wrapper + MPPI rollout integration both depend on #44/#23 reaching main
(PR-dependency-blocked per the feasibility filter). If still blocked next cycle and
gate-1 is clear, author an independent doc/infra step rather than branch-stacking.

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **Merge #44** (MERGEABLE, D-009 build-first residual scaffold) — the single
   keystone unblock for all P2 implementation TODOs.
2. **Merge/resolve #23 (dataset) + #45 (data-pipeline) + #24 (energy-reg)** —
   load-bearing; conflicts are auto-gen-file-only (STATE/JOURNAL/RESULTS).
3. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` →
   `runs/cafe-001.json` (first quantitative baseline). Owner=user, 25+ days.
4. **`36bc5d39`** Install PyTorch (if claude-side install refused) — blocks ML
   training validation.

## Cycles to date

- 이번 주: this cycle is the first productive executor cycle since 2026-05-31
  (22+ skip cycles/day during the 17-day stall).
- 프로젝트 통합: ~17 productive cycles.
