# MLP-based CFM velocity field for unicycle dynamics

- **Cycle**: 2026-05-25 04:00 KST
- **Branch**: `autoresearch/p2-mlp-cfm-velocity-field`
- **TODO**: `36ac5d39` Evaluate MLP backbone (Flow Planner style) as lightweight alternative to TemporalUnet for short-horizon action CFM
- **Phase**: P2
- **Status**: keep

## What I tried
- Implemented MLP-based Conditional Flow Matching velocity field following Flow Planner's architecture pattern
- Used sinusoidal time embedding + FiLM (Feature-wise Linear Modulation) conditioning blocks
- Created inline synthetic unicycle trajectory generator (random start, random actions, unicycle kinematics with first-order velocity lag)
- Full training pipeline: OT-CFM loss, AdamW + cosine LR, validation MAE, Euler sampling, checkpoint save

## What worked / what failed
- Clean architecture: 3 classes (SinusoidalTimeEmbedding, FiLMBlock, MLPCFMVelocityField) + 4 functions
- Syntax validates cleanly via `ast.parse`
- Cannot verify training convergence this cycle — PyTorch not installed on system (user-blocked dependency)
- Self-contained design confirmed feasible: no import from `scripts/gen_unicycle_dataset.py` needed

## North-star delta
- +1 candidate dynamics model architecture for P2 (MLP alternative to TemporalUnet)
- 0 measured numbers yet — awaiting PyTorch install to run training
- Advances "learning dynamics → MPPI rollout" pipeline: once trained, this model's `sample_cfm()` output is the state-transition prediction MPPI rollouts need

## Key learnings
- MLP + FiLM is significantly simpler than TemporalUnet (162 LOC vs ~500+ for full TCFM) — good for rapid iteration
- Inline data generation removes the critical-path dependency on PR #23 merge
- OT-CFM (optimal transport) loss is cleaner than VP-SDE: just MSE between linear-interpolation velocity and predicted velocity
- Next training run will reveal if 128-dim hidden is sufficient for 5D→5D unicycle dynamics

## Recommended next 1–3 priorities
1. Install PyTorch in project venv → run `python3 learning/mlp_cfm_unicycle.py` → validate convergence (Owner=user)
2. Once convergence confirmed: compare MLP vs TemporalUnet on same data — decide primary P2 backbone
3. Wire `sample_cfm()` into MPPI rollout as dynamics model (P2 integration milestone)

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/26
- Files touched: learning/__init__.py, learning/mlp_cfm_unicycle.py, .gitignore
- TSV row appended: yes
