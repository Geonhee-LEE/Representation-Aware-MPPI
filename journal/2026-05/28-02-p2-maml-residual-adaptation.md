# MAML-based residual dynamics adaptation analysis for P2 sim-to-real

- **Cycle**: 2026-05-28 02:00 KST
- **Branch**: `autoresearch/p2-maml-residual-adaptation`
- **TODO**: `36dc5d39` [research] Evaluate MAML-based residual adaptation as sim-to-real transfer strategy for P2 learned dynamics model
- **Phase**: P2
- **Status**: keep

## What I tried
- Evaluated MAML meta-learning (arxiv 2504.16369, Mei et al.) as adaptation strategy for our P2 residual dynamics model
- Mapped MAML's inner/outer loop structure onto our existing unicycle residual MLP (7→64→64→5)
- Analyzed composition with energy-based regularization (energy reg in both MAML loops preserves safety through adaptation)
- Analyzed composition with ensemble residual dynamics (shared meta-init, diverge at adaptation)
- Designed task distribution for synthetic meta-training data (`UnicycleTaskDistribution` varying τ_v, τ_ω, slip, noise)

## What worked / what failed
- MAML maps cleanly onto our stack: wraps existing MLP training, no architecture change needed
- Computational budget is negligible: 1-step adaptation on 20 samples < 1 ms, fits within 20 Hz MPPI budget
- Energy regularization composes with MAML (apply in both loops) — safety survives adaptation
- Identified that context-conditioned models (the main alternative) would require architecture changes — MAML is lower integration cost for P2
- Limitation: no empirical validation without PyTorch; this is a design-level analysis only

## North-star delta
- +1 design-level artifact defining our sim-to-real adaptation strategy for learned dynamics
- Completes the P2 "learned dynamics stack" design triad: energy regularization (stability) + ensemble (uncertainty) + MAML (adaptation)
- No runtime movement — still 0 measured numbers, still waiting on PyTorch + PR merges

## Key learnings
- The P2 learned dynamics integration is now well-specified at the design level: residual MLP + energy reg + ensemble + MAML. The bottleneck is purely execution (PyTorch install + PR merges), not design gaps.
- MAML's task distribution design (what dynamics parameters to vary) is at least as important as the algorithm itself. For unicycle, 5 parameters (τ_v, τ_ω, slip, v_noise, ω_noise) with broad uniform ranges should cover typical sim-to-real gaps.
- First-order MAML (FOMAML — dropping the Hessian term) is a viable simplification that trades a small adaptation quality loss for much simpler implementation (no second-order gradients).
- The three P2 analysis docs (energy reg, ensemble, MAML) should be read together — they form a coherent design specification for the learned dynamics module.

## Recommended next 1–3 priorities
1. **(user)** Install PyTorch in dev env — unblocks all ML execution (ensemble wrapper, MAML training, TCFM training)
2. **(user)** Merge open PR cluster (#22–27, #41) — 6 doc-only PRs carrying for 3+ days
3. **(claude)** Extend `gen_unicycle_dataset.py` with `--meta` flag for task-distributed data generation (prerequisite for MAML training, can be done without PyTorch)

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/41 (autoresearch/p2-maml-residual-adaptation)
- Files touched: docs/maml_residual_adaptation_analysis.md, results/p2-maml-residual-adaptation.tsv, RESULTS.md
- TSV row appended: yes
