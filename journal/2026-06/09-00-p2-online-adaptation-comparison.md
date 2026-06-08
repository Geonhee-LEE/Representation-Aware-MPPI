# P2 online-adaptation comparison + zombie-Doing self-heal

- **Cycle**: 2026-06-09 00:00 KST
- **Branch**: `autoresearch/p2-online-adaptation-comparison`
- **TODO**: `374c5d39` [research] compare online-adaptation mechanisms for P2 learned-dynamics rollout fidelity
- **Phase**: P2
- **Status**: keep

## What I tried
- Self-healed 2 zombie `Doing` TODOs (`371c5d39` training-data pipeline, `36ac5d39` ensemble wrapper) → `Today`; both PR-dependency-blocked since 06-03, firing gate-2 and driving a 9-day silent stall (STATE last 05-31).
- Wrote `docs/online_adaptation_comparison.md`: 4-way table (function-encoder+RLS vs low-rank 2nd-order vs MAML vs plain ensemble) over inference cost / data need / gradient-free / MPPI integration / our-platform evidence.
- Logged the open trade-off as Q-008 in `docs/deliberations.md`.

## What worked / what failed
- Self-heal cleared gate-2 structurally (Doing→Today) so the executor could make a feasible move instead of skipping into a 10th stalled day — same play as the 05-31 cycle's issue #13/#14 de-stuck.
- Picked the one bottleneck-adjacent item that is *feasible* (doc-only, no PyTorch, no unmerged-PR dependency) while every P2-impl TODO stays blocked on #44/#23.
- Did **not** unblock the actual bottleneck (PR merges are user-owned) — only advanced the design question that sits behind it.

## North-star delta
- + 1 design decision-input toward "모든 환경 / 미관측 분포" generalization: a recommended online-adaptation lever (function-encoder+RLS, Jackal-validated) for when the frozen ensemble meets OOD.
- Still **0 measured numbers** — no movement on the quantitative-baseline gap.

## Key learnings
- The recommendation is empirically gated, not committed: the online layer is premature until the frozen ensemble exists AND measured OOD rollout drift exceeds MPPI cost sensitivity. Encoded that as the sequencing note so a future cycle doesn't wire RLS preemptively.
- Two PR-blocked TODOs left in `Doing` will silently re-arm gate-2 every cycle — the durable fix is to keep PR-dependency items in `Today` (feasibility filter skips them) not `Doing`.

## Recommended next 1–3 priorities
1. **(user)** Drain PR queue — merge #44 (scaffold) + #23 (dataset) so P2 impl TODOs become feasible. This is the true bottleneck.
2. **(claude, feasible now)** Extend `gen_unicycle_dataset.py` with `--meta` task distribution (`36dc5d39`) — doc/script work, no PR dependency, unblocks both MAML and OOD-probe data.
3. **(claude, after #44/#23 land)** Implement EnsembleResidualDynamics wrapper (`36ac5d39`) + training-data pipeline (`371c5d39`) — now back in Today, auto-feasible on merge.

## Artifacts
- PR: #48 (autoresearch/p2-online-adaptation-comparison)
- Files touched: docs/online_adaptation_comparison.md, docs/deliberations.md, results/p2-online-adaptation-comparison.tsv, RESULTS.md
- TSV row appended: yes
