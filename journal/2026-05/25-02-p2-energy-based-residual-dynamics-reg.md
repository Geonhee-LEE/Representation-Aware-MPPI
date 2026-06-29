# Energy-based regularizer for residual dynamics

- **Cycle**: 2026-05-25 02:00 KST
- **Branch**: `autoresearch/p2-energy-based-residual-dynamics-reg`
- **TODO**: `36ac5d39` [research] Review energy-based regularization for residual dynamics in neural MPC (arxiv 2604.14678)
- **Phase**: P2
- **Status**: keep

## What I tried
- Analyzed energy-based regularization approach from arxiv 2604.14678 for applicability to our differential-drive residual dynamics
- Wrote analysis doc covering hinge-loss formulation, energy function choices (kinetic vs quadratic-goal vs learned Lyapunov), and integration path for P2
- Implemented PyTorch prototype: `UnicycleNominalDynamics` (matching dataset generator's kinematic model), `ResidualDynamicsNet` (zero-init output), `EnergyRegularizer` with configurable energy function
- Included `EnergyRegularizedTrainer` with combined MSE + energy loss, and a 64-step rollout stability check in the demo

## What worked / what failed
- Syntax validates cleanly; prototype is self-contained and importable
- Could not run the demo (PyTorch not installed on the CI/dev machine) — deferred to local verification
- The analysis identified three open questions about TCFM interaction that need ablation when training begins
- Created the `learning/` package — first ML module in the repo, establishes the pattern for future code

## North-star delta
- No direct metric movement — this is a training infrastructure component, not an end-to-end evaluation
- Removes a future blocker: when TCFM training starts, the stability guarantee is ready to plug in
- Contributes to "representation quality" half of the core hypothesis by ensuring learned dynamics don't degrade planner behavior

## Key learnings
- Kinetic energy V = 0.5(v² + ω²) is the simplest energy function for unicycle; it prevents velocity blow-up (the most dangerous MPPI failure mode) without requiring a goal state at training time
- Zero-initializing the residual MLP output layer is a critical safety measure — the model starts equivalent to the nominal, and the energy regularizer keeps it close during training
- The hinge formulation (max(0, ΔE)) is preferable to L2 on energy difference because it allows energy-reducing corrections (the residual should be able to model dissipative effects like friction)

## Recommended next 1–3 priorities
1. **Adapt TCFM TemporalUnet for 2D unicycle + train** — blocked on PR #23 merge; once merged, this is the natural next step that consumes both the dataset generator and this regularizer
2. **[research] Map Flow Planner hierarchical CFM onto Nav2 split** — completes the P2 design landscape (existing TODO, Status=Today)
3. **Install PyTorch in project venv** — needed to actually run the demo and future training; Owner=user

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/24
- Files touched: learning/__init__.py, learning/energy_regularizer.py, docs/energy_regularization_analysis.md
- TSV row appended: yes
