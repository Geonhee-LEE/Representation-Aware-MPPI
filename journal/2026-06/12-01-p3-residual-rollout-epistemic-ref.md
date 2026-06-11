# P3 residual-in-rollout + variance→safety implementation reference

- **Cycle**: 2026-06-12 01:00 KST
- **Branch**: `autoresearch/p3-residual-rollout-epistemic-ref`
- **TODO**: `37cc5d39` [research] Extract Stochastic-MPPI batched-GP-residual-in-rollout + variance→chance-constraint as wiring reference for D-009 EnsembleResidualDynamics + P3 epistemic channel
- **Phase**: P3
- **Status**: keep

## What I tried
- Cleared a re-formed gate-1 deadlock first: queue was at 6, last merge 2026-06-08 (>72h stall). Closed superseded PR #48 (online-adaptation comparison, deferred to U2 by D-009) per the D-010 deadlock-breaker → queue 6→5, branch deleted but PR reopenable.
- Authored `docs/residual_in_rollout_reference.md`: extracted the Stochastic-MPPI mechanism on two axes — (1) residual evaluated *inside* the batched MPPI rollout, (2) posterior variance → tightened chance-constraint — and mapped each onto the D-009 K=3 MLP-ensemble + the P3 epistemic channel.
- Added Q-008 (epistemic-margin gain `k`) to `docs/deliberations.md`; indexed the doc in `docs/README.md`.

## What worked / what failed
- The K=3 ensemble is *strictly easier* to batch than the reference's GP: residual is `K` matmuls on the flattened `[M·T, d]` batch nav2_mppi already materializes — solver-free, no GPyTorch. The "residual must be a tensor op that batches with the sampler" constraint is satisfied for free.
- Concrete wrapper signature pinned: `residual(s,a) -> (mu, var)`, compose `s_next = f_nom + mu`, thread `var` out for the cost layer — ready to apply the moment #44 lands.
- Variance routing: margin-inflation (constraint geometry) is the principled path; additive `λσ²` is the baseline the reference deliberately avoids. The gain `k` has no target until P5 has a near-miss metric → logged as Q-008, not hand-picked.

## North-star delta
- No measured numbers yet (unchanged). But the keystone `EnsembleResidualDynamics` wrapper is de-risked: its hardest open question (batched-rollout integration shape) now has a concrete spec, so it's mechanical once #44 merges.
- First in-phase P3 artifact: variance→margin epistemic-channel design, render-ready as a BEV channel.

## Key learnings
- The recurring gate-1 deadlock re-formed within 3 days of the last break — the root fix (D-011 / PR #47) is itself stuck in the merge queue, so the executor keeps having to self-heal. The *true* bottleneck is human merge bandwidth on build-path code PRs, not analysis throughput.
- When the build lane is merge-blocked, the phase clock (now P3) opens an independent forward lane — design groundwork that de-risks the blocked code is higher-value than yet another P2 analysis.

## Recommended next 1–3 priorities
- **User: merge the P2 build-path PRs** (#44 keystone, then #45, #23) — every P2 code step is PR-dependency-blocked until they reach main. #47 (D-011 root gate fix) too, to stop the deadlock recurring.
- Next executor cycle (if still merge-blocked + gate-1 clear): another independent P3 step — e.g. spec the epistemic-channel BEV rendering (σ²→ego-grid) or the margin-inflation cost-critic interface, both feasible without the ensemble code.
- When #44 lands: implement `EnsembleResidualDynamics` per this doc's wiring recommendation.

## Artifacts
- PR: pending merge (autoresearch/p3-residual-rollout-epistemic-ref)
- Files touched: docs/residual_in_rollout_reference.md, docs/deliberations.md, docs/README.md, results/p3-residual-rollout-epistemic-ref.tsv
- TSV row appended: yes
