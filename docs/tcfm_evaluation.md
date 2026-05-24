# TCFM Evaluation — Trajectory Conditional Flow Matching

_Phase P2 research evaluation · 2026-05-25_

**Source**: [CORE-Robotics-Lab/TCFM](https://github.com/CORE-Robotics-Lab/TCFM) · [arXiv 2403.10809](https://arxiv.org/abs/2403.10809)
**Authors**: Sean Ye, Matthew Gombolay (Georgia Tech CORE Lab)
**Claims**: 100× faster than diffusion, 35% higher predictive accuracy, 142% better planning score

---

## Architecture Overview

TCFM replaces diffusion's iterative denoising with a single ODE solve over a
learned velocity field. The core pipeline:

1. **Backbone model** learns a velocity field `v(x, t, cond)` mapping noise→trajectory
2. **Training**: Conditional Flow Matching loss (via `torchcfm.ConditionalFlowMatcher`)
   regresses the velocity field against optimal-transport interpolation paths
3. **Inference**: `torchdiffeq.odeint` integrates the ODE from `t=0` (Gaussian noise)
   to `t=1` (predicted trajectory) using Euler method with ~100 steps

### Backbone Options

| Model | Type | Key Properties |
|---|---|---|
| `TemporalUnet` | 1D Conv U-Net | Residual blocks + sinusoidal time MLP; `[B, horizon, transition_dim]` input as 1D conv over time; dim_mults (1,2,4,8) |
| `TransformerForDiffusion` | Encoder-Decoder Transformer | 12-layer, 12-head, 768-dim; time as conditioning token; cross-attention between trajectory and observation embeddings |

### CFM Sampling (`p_sample_loop_cfm`)

```python
traj = torchdiffeq.odeint(
    lambda t, x: model.forward(t, x, global_cond=global_cond),
    torch.randn(shape),                             # start: noise
    torch.linspace(0, 1, n_timesteps + 1),           # ODE time span
    atol=1e-4, rtol=1e-4, method="euler",
)
return traj[-1]  # final trajectory at t=1
```

Diffusion requires ~1000 iterative denoising steps; CFM solves a single ODE in
~100 Euler steps (or fewer — the code has a commented 2-step variant). This
explains the 100× speed claim.

### Conditioning

`global_cond` is a dictionary of tensors (class labels, detection features, etc.)
injected via FiLM conditioning or cross-attention. In the aircraft domain, this
conditions on past trajectory observations. For our use case, this would carry
robot state + goal + representation features from the BEV/risk channels.

---

## Comparison: TCFM vs cfm_mppi (Mizuta & Leung)

| Aspect | TCFM | cfm_mppi |
|---|---|---|
| **Goal** | Trajectory forecasting (predict future given past) | MPPI sample generation (replace Gaussian noise with learned distribution) |
| **Backbone** | TemporalUnet or Transformer | Transformer-based |
| **CFM library** | `torchcfm` + `torchdiffeq` | Custom CFM implementation |
| **Output** | Full trajectory `[horizon × state_dim]` | Control sequence `[horizon × action_dim]` |
| **MPPI integration** | None — standalone predictor | Direct: generates candidate rollouts for MPPI cost evaluation |
| **Speed** | ~100 Euler steps at inference | Not benchmarked vs diffusion |
| **Conditioning** | Global features (dict of tensors) | Current state + goal |
| **Domain** | Aircraft, prisoner pursuit | Mobile robot navigation |

**Key insight**: TCFM and cfm_mppi are complementary, not competing:
- cfm_mppi defines the *integration pattern* (CFM → MPPI cost eval → weighted selection)
- TCFM contributes the *velocity-field backbone + training pipeline*
- A hybrid uses TCFM's TemporalUnet backbone within cfm_mppi's MPPI integration

---

## Relevance to Our P2 (Learning Dynamics → MPPI Rollout Integration)

### What TCFM gives us

1. **Mature training pipeline**: Dataset loaders, normalization, training loop, and
   config system — reduces boilerplate for our unicycle trajectory dataset
2. **Two proven backbone architectures**: TemporalUnet (fast, good for short horizons)
   and Transformer (better for long-range dependencies, higher capacity)
3. **Speed**: Single-step ODE inference is compatible with MPPI's real-time requirement
   (~50-100 Hz control loop). Diffusion's 1000-step denoising is not.
4. **Conditioning mechanism**: `global_cond` dict maps cleanly to our representation
   channels (BEV features, risk fields, goal embedding)

### What TCFM lacks for our use case

1. **No unicycle/diff-drive dynamics**: All configs target aircraft or pursuit-evasion.
   We need to create our own dataset from simulation runs.
2. **No MPPI integration**: TCFM is a standalone forecaster. The cfm_mppi integration
   pattern (generate K samples → evaluate cost → weight) must be built separately.
3. **No dynamics-model mode**: TCFM predicts trajectories directly; our P2 needs a
   *dynamics model* `f(state, action) → next_state` for MPPI rollout. Two options:
   - (A) Use TCFM as a *trajectory generator* (replace MPPI's forward rollout entirely)
   - (B) Train TCFM in *residual dynamics* mode (predict `Δstate` given `state + action`)
4. **No online adaptation**: Pre-trained only. For P3 (uncertainty estimation), we'd
   need to add epistemic uncertainty (e.g., ensemble or MC dropout).

### Recommended integration path

```
Option A — Trajectory Generator (simpler, P2 scope):
  TCFM generates K candidate trajectories conditioned on (robot_state, goal, BEV)
  → MPPI cost evaluates each → weighted selection → first action executed

Option B — Learned Dynamics (deeper, P2-P3 scope):
  MPPI forward rollout uses TCFM as f(s,a)→s' instead of analytical model
  → requires action-conditioned training (state+action input, next_state output)
  → more faithful to MPPI framework but needs paired (s,a,s') data
```

**Recommendation**: Start with Option A. It's faster to prototype (TCFM already
outputs trajectories), validates the speed claim in our domain, and produces the
first end-to-end "learned representation → MPPI" demo. Option B is Phase P3
follow-up work once we have a working pipeline.

---

## Dataset Requirements for Our Domain

To train TCFM on our robot trajectories:

| Field | Value |
|---|---|
| Format | Per-trajectory folder with `.npz` arrays |
| Features | `x.npz`, `y.npz`, `theta.npz`, `v.npz`, `omega.npz` |
| Conditioning | `goal_x.npz`, `goal_y.npz` (or BEV features as global_cond) |
| Normalization | Min-max per feature, map to [-1, 1] |
| Source | Gazebo sim runs (cafe + small_city scenarios) |
| Min trajectories | ~500-1000 for TemporalUnet; ~5000+ for Transformer |

This depends on the user completing sim runs (TODO `358c5d39`). In the meantime,
synthetic unicycle trajectories (RK4 integration of diff-drive kinematics with
random goals) can bootstrap training.

---

## Next Steps

1. **[P2, claude]** Create synthetic unicycle trajectory dataset generator
   (`scripts/gen_unicycle_dataset.py`) using diff-drive kinematics + random goals
2. **[P2, claude]** Adapt TCFM's TemporalUnet config for 2D unicycle
   (5-dim state: x, y, θ, v, ω; 2-dim action: v_cmd, ω_cmd)
3. **[P2, user]** Run cafe/city sim scenarios to collect real trajectory data
   (blocked on TODO `358c5d39`)
4. **[P2, claude]** Implement Option A integration: TCFM trajectory generator →
   MPPI cost evaluation → action selection (Nav2 plugin or standalone Python)
