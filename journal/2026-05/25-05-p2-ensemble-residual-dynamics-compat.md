# Ensemble Residual Dynamics MPPI Compatibility Analysis

- **Cycle**: 2026-05-25 05:00 KST
- **Branch**: `autoresearch/p2-ensemble-residual-dynamics-compat`
- **TODO**: `36ac5d39` [research] Evaluate ensemble residual dynamics compatibility with MPPI parallel rollouts
- **Phase**: P2
- **Status**: keep

## What I tried
- Created a standalone FLOPs estimation script (`learning/ensemble_flops_estimate.py`) that computes exact multiply-add counts for both ResidualDynamicsNet and MLPCFMVelocityField architectures
- Ran the script to compare single vs ensemble-of-3 for both model families under MPPI's 1000×20 rollout budget
- Wrote a comprehensive analysis doc (`docs/ensemble_residual_dynamics_analysis.md`) with architecture diagram and implementation plan

## What worked / what failed
- Clear quantitative answer: residual ensemble-3 at 584M FLOPs is 0.32× of a single ResNet-18 — trivially cheap
- Surprising finding: CFM velocity field ensemble is 78× ResNet-18 due to the 20-step Euler integration multiplier — this was not obvious from architecture specs alone
- The "ensemble the residual, not the CFM" recommendation is a concrete architectural decision that future P3 work can build on
- No PyTorch needed — pure arithmetic analysis, unblocked by the install bottleneck

## North-star delta
- +1 architectural decision locked: ensemble-3 residual is the uncertainty source, not ensemble CFM
- +1 P3 epistemic uncertainty channel pathway defined (per-sample variance → MPPI cost penalty)
- No movement on measurable metrics (still 0 numbers) — this is design-phase work

## Key learnings
- The Euler integration step count is a hidden multiplier that dramatically shifts the FLOPs balance — any model evaluated via multi-step ODE integration should be analyzed with this multiplier included
- Weight-stacked batching (vmap) can reduce wall-clock from K× to ~1.0-1.3× for small models — the ensemble "cost" is almost entirely in parameter diversity, not compute
- Energy regularization from PR #24 composes cleanly with ensembles: apply per-head, inherit stability in the mean

## Recommended next 1–3 priorities
1. **(user-blocked)** Install PyTorch → validate MLP CFM training convergence and energy regularizer stability
2. **(claude)** Implement `EnsembleResidualDynamics` wrapper (~60 LOC) once PyTorch is available — wraps K `ResidualDynamicsNet` heads with bootstrap resampling
3. **(claude)** Compare A2A warm-start mechanism with MPPI's shift-and-resample (new research feed entry, P2-relevant)

## Artifacts
- PR: #27 pending merge (autoresearch/p2-ensemble-residual-dynamics-compat)
- Files touched: learning/ensemble_flops_estimate.py, docs/ensemble_residual_dynamics_analysis.md, results/p2-ensemble-residual-dynamics-compat.tsv, RESULTS.md
- TSV row appended: yes
