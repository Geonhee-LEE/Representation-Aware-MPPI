# Research State — auto-generated each cycle

_Last updated: 2026-06-06 16:00 KST · cycle p0-gate1-exclude-closed-pr-branches_

## North star distance

Still **0 measured numbers** — first quantitative baseline (`runs/cafe-001.json`)
remains unrun. The 17-day total stall stays broken: the gate-1 self-heal (D-010,
PR #46) plus this cycle's gate-1 **measurement** fix (PR #47) together make the
PR-queue gate both escapable and accurately counted. P2 is design-converged
(D-009 MLP-ensemble); the build path (#44, MERGEABLE) is one user-merge from
resuming code.

## Current bottleneck

**User must merge the in-flight PRs — executor cannot merge to main.** Two
adjacent infra PRs first: #46 (deadlock-breaker/D-010) then #47 (gate-1 count
fix) — merge #46 first, they edit the same gate-1 region. Then the P2 build path
#44 (D-009 scaffold) + #23 (dataset) + #45 (data-pipeline) + #24 (energy-reg).
Until #44+#23 reach main, the EnsembleResidualDynamics TODOs stay
PR-dependency-blocked.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| `autoresearch/p0-gate1-exclude-closed-pr-branches` | 2026-06-06 16:00 | qual:script-syntax-ok (queue count 8→5 fix) | 0 (PR #47) |
| `autoresearch/p2-executor-pr-queue-deadlock-breaker` | 2026-06-06 15:00 | D-010 self-heal clause | 0 (PR #46) |
| `autoresearch/p2-residual-dynamics-mlp-scaffold` | ~05-31 | D-009 scaffold, **MERGEABLE** | ~6 (PR #44) |
| `autoresearch/p2-unicycle-dataset-generator` | ~05-25 | dataset gen | ~12 (PR #23) |
| `autoresearch/p2-training-data-collection` | ~05-31 | replay buffer | ~6 (PR #45) |
| `autoresearch/p2-energy-based-residual-dynamics-reg` | ~05-26 | energy reg | ~12 (PR #24) |

## Recent learnings (last 3 cycles)

- **(this cycle)** A self-heal and the metric it acts on must agree: D-010 *closed*
  PRs to drain the queue, but the gate still *counted* them ("no merged PR"), so
  the heal was cosmetic until the count was fixed too (PR #47).
- **(deadlock-breaker)** A safety gate with no escape hatch = single point of
  project death; closing the executor's own superseded PRs is legitimate self-heal
  (closing ≠ merging-to-main). Codified as D-010 with a 72h-stall threshold.
- **(decision-matrix)** D-009 commits MLP-ensemble(K=3) build-first; ensemble var
  → free P3 epistemic channel.

## Next claude-actionable (this cycle would pick from here)

_none feasible until the build path lands on main_ — EnsembleResidualDynamics
wrapper + MPPI rollout integration both depend on #44/#23 reaching main
(PR-dependency-blocked per the feasibility filter). Note the queue is now at the
cap (6 open PRs incl. #47), so next cycle gate-1 will correctly skip until a merge
drains it. If gate-1 is clear next cycle and the build path is still blocked,
author another independent doc/infra or `[research]` design step — do NOT
branch-stack. Phase-0 candidate: SVGD task-dependent parameter-uncertainty
shaping (feed 2604.01034) composes with the D-009 ensemble for P2 rollout
robustness — a doc-only design analysis is feasible while PR-blocked.

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **Merge #46 then #47** (adjacent gate-1 infra edits; #46 first) — restores the
   PR-queue gate to escapable + correctly-counted.
2. **Merge #44** (MERGEABLE, D-009 build-first residual scaffold) — the single
   keystone unblock for all P2 implementation TODOs.
3. **Merge/resolve #23 (dataset) + #45 (data-pipeline) + #24 (energy-reg)** —
   load-bearing; conflicts are auto-gen-file-only (STATE/JOURNAL/RESULTS).
4. **`358c5d39`** Run `cafe_straight_v0` sim with `include_run_metrics:=true` →
   `runs/cafe-001.json` (first quantitative baseline). Owner=user, 25+ days.
5. **`36bc5d39`** Install PyTorch (if claude-side install refused) — blocks ML
   training validation.

## Cycles to date

- 이번 주: 2nd productive executor cycle since the 17-day stall broke (15:00
  deadlock-breaker, 16:00 this gate-count fix).
- 프로젝트 통합: ~18 productive cycles.
