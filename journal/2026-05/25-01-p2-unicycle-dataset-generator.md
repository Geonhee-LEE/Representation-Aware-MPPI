# Synthetic unicycle trajectory dataset generator for P2 TCFM bootstrap

- **Cycle**: 2026-05-25 01:00 KST
- **Branch**: `autoresearch/p2-unicycle-dataset-generator`
- **TODO**: `36ac5d39` Create synthetic unicycle trajectory dataset generator
- **Phase**: P2
- **Status**: keep

## What I tried
- Created `scripts/gen_unicycle_dataset.py`: a self-contained Python script that generates synthetic differential-drive robot trajectories
- Used unicycle kinematics (x'=v*cos(θ), y'=v*sin(θ), θ'=ω) with first-order velocity lag (tau_v=0.2, tau_omega=0.1) for realism
- Proportional goal-tracking controller with heading-dependent speed reduction + Gaussian process noise on commands
- Output format: TCFM-compatible `.npz` with raw + min-max normalized arrays, normalization bounds, and metadata

## What worked / what failed
- Script generates valid trajectories with 33% goal-reached rate on 100-traj test (6.4s horizon @ 10Hz)
- Normalization correctly maps to [-1, 1] range across all state and action dimensions
- Trajectories show meaningful goal-directed behavior: avg distance-to-goal decreases from 5.6m to 4.6m
- No failures — straightforward numerical script with no external dependencies beyond numpy

## North-star delta
- First executable P2 artifact: training data pipeline now exists, removing the "no data" bottleneck for TCFM training
- Zero ROS2/sim dependency means this is immediately usable for offline ML experiments
- Still no measured navigation numbers (user sim run blocked 14+ days), but the path from data → TCFM training → MPPI integration is now unblocked

## Key learnings
- dt=0.1s (10Hz) with 64-step horizon (6.4s) provides a reasonable balance of goal-reaching and trajectory variety for a ±3m arena
- First-order velocity lag (tau_v=0.2s, tau_omega=0.1s) produces smooth, physically plausible acceleration profiles without adding complexity
- The `.npz` format with both raw and normalized arrays preserves denormalization capability at inference — critical for mapping TCFM output back to physical coordinates

## Recommended next 1-3 priorities
1. Adapt TCFM's TemporalUnet config for 2D unicycle (5-dim state, 2-dim action) and train on the generated dataset — first learned dynamics model
2. [research] Review energy-based regularization for residual dynamics (arxiv 2604.14678) — stability guarantee for P2 learned dynamics
3. [research] Map Flow Planner hierarchical CFM onto Nav2 global/local split — completes P2 design landscape

## Artifacts
- PR: #23 (autoresearch/p2-unicycle-dataset-generator)
- Files touched: scripts/gen_unicycle_dataset.py, .gitignore
- TSV row appended: yes
