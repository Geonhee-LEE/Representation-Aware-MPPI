# P2 residual-dynamics decision matrix — pick build-first architecture

- **Cycle**: 2026-05-31 00:00 KST
- **Branch**: `autoresearch/p2-residual-dynamics-decision-matrix`
- **TODO**: `370c5d39` P2 residual-dynamics architecture decision matrix
- **Phase**: P2
- **Status**: keep

## What I tried
- De-stuck two zombie `Doing` TODOs (issue #13/#14 sensor pipeline) that had sat
  Doing 16 days with empty Branch — they were perpetually firing gate-2 and
  silently stalling the executor. Moved Doing→Backlog, stripped `[stuck]`.
- Authored `docs/p2_residual_dynamics_decision.md`: 8-candidate × 8-axis matrix
  consolidating the fragmented P2 residual-dynamics research.
- Emitted D-009 (build-first = MLP-ensemble K=3, offline-frozen) + Q-007
  (analytic vs learned nominal) + docs index entry.

## What worked / what failed
- The matrix made the choice obvious once "MPPI batched-rollout fit" and
  "unicycle-bootstrap fit" were made explicit axes — ODE-based candidates
  (STRIDE-CFM, ICODE) self-eliminate for the *first* build despite strong papers.
- Ensemble variance → P3 epistemic channel is a genuinely free synergy no other
  candidate offers; it broke the near-tie with the energy-reg MLP (C8).
- gate-2 would have skipped this cycle on the zombie TODOs — the de-stuck step
  was the actual unlock, not the doc.

## North-star delta
- + 1 architecture decision committed: analysis→implementation is now unblocked
  for the first learned-representation→MPPI build (the C1 ensemble residual).
- Still **0 measured numbers** — pure design-convergence cycle, no sim run.

## Key learnings
- The real P2 bottleneck was convergence, not data: 5 open PRs were all *analysis*
  with no decision gate. A decision doc + ADR is higher-leverage than a 9th
  analysis right now.
- Perpetually-Doing zombie TODOs are themselves the silent-stall mechanism the
  gate caps were raised to avoid — executor should self-heal them, not skip.

## Recommended next 1–3 priorities
1. (claude, blocked on #23 merge) Implement `EnsembleResidualDynamics` wrapper
   (K=3 heads, bootstrap, var→epistemic) per D-009 — already a Notion TODO.
2. (claude) Once #23+wrapper on main, write the MPPI batched-rollout integration
   point swapping analytic dynamics for the ensemble forward.
3. (user) Drain the 6/6 PR queue (#23–27, #43) so executor unblocks.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/43
- Files touched: docs/p2_residual_dynamics_decision.md, docs/decisions.md, docs/deliberations.md, docs/README.md, results/p2-residual-dynamics-decision-matrix.tsv, RESULTS.md
- TSV row appended: yes
