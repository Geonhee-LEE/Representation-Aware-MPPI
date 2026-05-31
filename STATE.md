# Research State — auto-generated each cycle

_Last updated: 2026-05-31 23:00 KST · cycle p2-training-data-collection_

## North star distance

P2 in progress. The residual-dynamics track now has both halves of the pre-training stack: an MLP-ensemble scaffold (`learning/dynamics/`, on the unmerged `p2-residual-dynamics-mlp-scaffold` branch, PR #44) and a training-data collection path (`data_pipeline/`, this cycle, PR #45). No MPPI integration, no trained model yet. Classical MPPI baseline still the only thing running in sim; learned-representation track is data-ready but neither trained nor wired into rollout.

## Current bottleneck

**Merge throughput, not new code.** Eight P2 PRs are open and unmerged (#23, #24, #25, #26, #27, #43, #44, #45). The residual model (#44) and its data pipeline (#45) live on separate branches; trainer/eval work (`delta = next_state - nominal(s,a)`, fit `ResidualEnsemble`, MSE eval) needs both on `main` together. Until the queue drains, every high-value follow-up is PR-dependency-infeasible and the executor will skip or stall. The PR-queue safety gate (≥6) is now tripped — next cycles should hold until the user merges.

## Open experiments

| branch | last update | last description | days open |
|---|---|---|---|
| autoresearch/p2-training-data-collection | 2026-05-31 23:00 | replay buffer + synthetic-plant scripted rollouts (300-tuple smoke); PR #45 | 0 |
| autoresearch/p2-residual-dynamics-mlp-scaffold | 2026-05-31 21:00 | MLP-ensemble residual scaffold + nominal diff-drive; PR #44 | 0 |
| autoresearch/p2-residual-dynamics-decision-matrix | 2026-05-31 00:00 | D-009 ADR; PR #43 | ~1 |
| autoresearch/p2-unicycle-dataset-generator | ~05-25 | unicycle dataset gen; PR #23 | ~6 |
| autoresearch/p2-ensemble-residual-dynamics-compat | ~05-27 | ensemble compat; PR #27 | ~4 |

## Recent learnings (last 3 cycles)

- Data collection only needs ground-truth transitions; computing the residual target is the trainer's job — this decoupling let the data pipeline land off `main` despite the model scaffold being unmerged.
- A synthetic plant with explicit unmodeled terms (drag/slip/drift) gives a *known* residual, usable later as a sanity oracle for the trained model.
- The binding constraint has shifted from "produce P2 artifacts" to "merge them" — the executor can keep generating off-main thrusts but they pile into an unreviewed queue.

## Next claude-actionable (this cycle would pick from here)

_Thin — most P2 follow-ups are PR-dependency-blocked until the queue drains._

1. **p2-data-pipeline-tests** Add a pytest for `data_pipeline` (buffer round-trip, dim-validation, non-zero residual gap) — feasible off main now, hardens the schema contract before trainer work. — why now: needs only this cycle's code.
2. **p2-collect-cli-doc** Document the tuple schema + collection recipe in `docs/` and cross-link `learning/` ↔ `data_pipeline/` — doc-only, feasible off main.

## Next user-blocked (waiting on user action — surfaces in Telegram queue, not for PLAN)

1. **drain-p2-pr-queue** Merge/close the 8 open P2 PRs (#23–27, #43–45) — the PR-queue gate (≥6) is tripped, so the executor is now rate-limited to skips. This is the single highest-leverage action. — why now: unblocks trainer + numeric eval and restarts executor throughput.
2. **install-pytorch** Install PyTorch in the dev/executor env — torch absent, so ensemble training-smoke + torch unit tests are skipped.
3. **run-cafe-baseline-sim** Run `cafe_straight_v0` with `include_run_metrics:=true` → first quantitative baseline `runs/cafe-001.json` (Owner=user, 20+ days open).

## Cycles to date

- This week (from 2026-05-25): multiple P2 cycles (TCFM, MAML, decision-matrix, scaffold, this).
- Project total: ~18 (per JOURNAL history + in-flight stack).
