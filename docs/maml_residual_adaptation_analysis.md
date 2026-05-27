# MAML-Based Residual Dynamics Adaptation for MPPI

_Phase P2 research evaluation · 2026-05-28_

**Source**: [arXiv 2504.16369](https://arxiv.org/abs/2504.16369) (Mei, Zhou, Yu, Srivastava, Tan — April 2025)
**Title**: Fast Online Adaptive Neural MPC via Meta-Learning
**Core claim**: MAML meta-training enables few-shot online adaptation of residual
dynamics within MPC, bridging sim-to-real without full retraining.

---

## Problem statement

When a residual dynamics model `f_res(x, u)` is trained in simulation and
deployed to a real (or unseen) environment, the model-reality gap causes
trajectory divergence during MPC/MPPI rollouts. Standard remedies:

| Approach | Adaptation speed | Data need | Drawback |
|---|---|---|---|
| Domain randomization | None (train-time) | Large domain set | Conservative, worst-case |
| Fine-tuning | Slow (many gradient steps) | 100s of transitions | Catastrophic forgetting |
| System identification | Manual | Physics parameters | Limited to parametric gap |
| **MAML meta-learning** | **Fast (1–5 steps)** | **5–20 transitions** | Meta-training cost |

MAML addresses the critical P2 question: once we train our residual dynamics
(on synthetic unicycle data from `scripts/gen_unicycle_dataset.py`), how do we
adapt it when the real robot behaves differently?

---

## MAML for residual dynamics — algorithm structure

### Meta-training (offline, in simulation)

The key insight: train the residual model's **initial weights** θ₀ such that
a few gradient steps on new-environment data produce a good model for that
environment. This is Model-Agnostic Meta-Learning (Finn et al., ICML 2017)
applied to dynamics.

```
Meta-training loop:
  for each task τᵢ ~ p(τ)          # τ = different dynamics parameters
    D_support, D_query = sample from τᵢ

    # Inner loop: adapt
    θ'ᵢ = θ - α · ∇_θ L(f_θ, D_support)      # 1-5 gradient steps

    # Outer loop: meta-update
    θ ← θ - β · ∇_θ Σᵢ L(f_θ'ᵢ, D_query)    # update initial weights
```

**Task distribution p(τ)**: For our unicycle, this means varying:
- Wheel radius, track width (geometric)
- Velocity lag time constants τ_v, τ_ω (actuator response)
- Friction coefficients (terrain)
- Mass, inertia (payload changes)
- Sensor noise characteristics

Each task is a different parameterization of the unicycle dynamics. The
meta-learner sees many such parameterizations and learns initial weights
that are maximally adaptable.

### Online adaptation (at deployment)

```
On new environment:
  Collect D_online = {(xₜ, uₜ, x_{t+1})}  # 5-20 real transitions
  θ_adapted = θ₀ - α · ∇_θ L(f_θ₀, D_online)  # 1-5 gradient steps
  Use f_θ_adapted in MPPI rollout for the rest of the episode
```

The adaptation is fast enough to run between MPPI control cycles (or every
N cycles). With a 2-layer MLP residual (our architecture: 7→64→64→5), a
single gradient step on 20 samples takes <1 ms on CPU.

---

## How this maps to our P2 stack

### Current residual dynamics architecture

From the energy-based regularization analysis and ensemble dynamics analysis:

```
  state_t = [x, y, θ, v, ω]       (5-dim)
  action_t = [v_cmd, ω_cmd]       (2-dim)
  input = [state_t, action_t]     (7-dim)

  ┌───────────────────┐
  │  f_nom (unicycle)  │ → x_nominal
  └───────────────────┘
  ┌───────────────────┐
  │  f_res (MLP 7→64→64→5) │ → Δx_residual
  └───────────────────┘

  x_{t+1} = f_nom(x_t, u_t) + f_res(x_t, u_t; θ)
```

### MAML integration plan

```
                     META-TRAINING (offline)
  ┌─────────────────────────────────────────────────┐
  │  p(τ): unicycle parameter distribution          │
  │  ┌──────┐  ┌──────┐  ┌──────┐                  │
  │  │ τ₁   │  │ τ₂   │  │ τ₃   │  ...  (50–200    │
  │  │τ_v=.2│  │τ_v=.3│  │τ_v=.1│       tasks)     │
  │  │μ=0.5 │  │μ=0.8 │  │μ=0.3 │                  │
  │  └──────┘  └──────┘  └──────┘                  │
  │        ↓ support + query sets per task          │
  │  MAML outer loop → θ₀ (meta-initialized)        │
  └─────────────────────────────────────────────────┘
                          │
                          ▼
                     DEPLOYMENT (online)
  ┌─────────────────────────────────────────────────┐
  │  Real robot or new sim environment              │
  │  1. Run MPPI with f_nom only for K steps        │
  │  2. Collect D_online = {(x, u, x')} from K      │
  │     transitions                                  │
  │  3. θ_adapted = MAML_adapt(θ₀, D_online)        │
  │  4. Switch MPPI to f_nom + f_res(θ_adapted)     │
  │  5. (Optional) Re-adapt every M steps           │
  └─────────────────────────────────────────────────┘
```

### Task distribution for synthetic data

Our `scripts/gen_unicycle_dataset.py` currently generates trajectories with
fixed dynamics parameters. For MAML meta-training, we need a **task
distribution** version:

```python
class UnicycleTaskDistribution:
    def sample_task(self):
        return {
            'tau_v': uniform(0.05, 0.5),    # velocity lag [s]
            'tau_omega': uniform(0.03, 0.3), # angular velocity lag [s]
            'v_noise_std': uniform(0, 0.1),  # process noise
            'omega_noise_std': uniform(0, 0.05),
            'wheel_slip': uniform(0, 0.15),  # multiplicative slip
        }
```

Each task generates a (support, query) split: ~10 transitions each.
Meta-training needs 50–200 tasks to converge (per Finn et al. guidance
for low-dim systems).

---

## Comparison with alternative adaptation strategies

| Strategy | Adaptation data | Gradient steps | Catastrophic forgetting | Stability guarantee |
|---|---|---|---|---|
| **MAML (this)** | 5–20 transitions | 1–5 | Low (adapts from meta-init) | Via energy reg (composable) |
| Fine-tuning | 100+ transitions | 50+ | High | None inherent |
| Domain randomization | 0 (train-time) | 0 | N/A | Conservative by design |
| Context-conditioned | 20–50 transitions | 0 (forward pass) | None | Depends on conditioning |
| Online system ID | 10–50 | Analytical | N/A | Parametric model limits |

### Context-conditioned alternative

An alternative to MAML is a context-conditioned model that takes recent
transitions as input and infers the dynamics in a single forward pass (no
gradient computation at deployment). Architecture:

```
  f_res(x, u, context; θ)    where context = encode(D_online)
```

Pros: no gradient at deployment (faster, no autograd needed in C++).
Cons: requires more training data, harder to integrate with existing
MLP architecture, less sample-efficient online.

For P2 prototyping, **MAML is preferred** because:
1. Our residual MLP is already defined — MAML wraps the training loop,
   doesn't change the model.
2. 1-step adaptation on 20 samples is fast enough for our 20 Hz MPPI.
3. Composes with energy regularization (apply reg in both inner + outer loops).

---

## Interaction with existing P2 components

### Energy-based regularization (arxiv 2604.14678)

Energy regularization applies to MAML in both loops:

```
Inner loop:
  L_inner = L_data(D_support) + λ · L_energy(D_support)
  θ' = θ - α · ∇_θ L_inner

Outer loop:
  L_outer = L_data(D_query, θ') + λ · L_energy(D_query, θ')
  θ ← θ - β · ∇_θ L_outer
```

This ensures adapted weights never produce energy-injecting residuals,
even for unseen environments. The energy regularizer is a safety net that
survives adaptation.

### Ensemble residual dynamics (doi:10.3390/s26010340)

MAML + ensemble has two options:

1. **MAML per head**: Each ensemble member has its own meta-initialized θ₀ᵏ,
   adapted independently. Epistemic uncertainty = variance across adapted heads.
   Cost: K × adaptation cost.

2. **Shared MAML, diverge at adaptation**: Single meta-initialization θ₀,
   adapt K times with different bootstrap subsets of D_online.
   Cost: K × adaptation cost, but K=3 is cheap for our 5K-param MLP.

Option 2 is simpler and preserves the ensemble's uncertainty semantics:
disagreement after adaptation reflects genuine environment ambiguity, not
just initialization difference.

### TCFM / CFM trajectory generation

MAML applies to the **residual dynamics model only**, not the CFM trajectory
generator. The CFM generates trajectory proposals that MPPI evaluates using
`f_nom + f_res`. When `f_res` adapts via MAML, the MPPI cost landscape
changes, and CFM proposals are implicitly re-ranked — no change to the CFM
model itself.

---

## Implementation roadmap

### Phase 1: Meta-training data infrastructure (~30 min, claude)

Extend `scripts/gen_unicycle_dataset.py` with a `--meta` flag that generates
task-distributed data:
- Output format: `.npz` with `tasks/` prefix, each task having `support_states`,
  `support_actions`, `query_states`, `query_actions`
- 100 tasks × 20 transitions × 2 (support + query) = 4000 total transitions

### Phase 2: MAML training loop (~60 min, claude, needs PyTorch)

Implement `learning/maml_residual.py`:
- `MAMLResidualTrainer(model, inner_lr, outer_lr, inner_steps, energy_reg)`
- Inner loop: 1–5 gradient steps on support set
- Outer loop: standard Adam on query-set loss evaluated at adapted weights
- Use `torch.func.grad` or `higher` library for differentiating through
  the inner loop

### Phase 3: Online adaptation interface (~30 min, claude, needs PyTorch)

Implement `learning/online_adapter.py`:
- `OnlineAdapter(meta_model, buffer_size=20, adapt_every=10)`
- Collects real transitions in a FIFO buffer
- Triggers adaptation when buffer is full
- Thread-safe for integration with ROS2 control loop

### Phase 4: MPPI integration (~60 min, needs sim verification)

Wire adapted dynamics into the MPPI rollout:
- Replace `f_nom` call with `f_nom + f_res_adapted`
- Re-adapt every M control cycles (M=50 at 20 Hz = every 2.5 s)
- Log adaptation loss for diagnostics

---

## Computational budget analysis

| Operation | FLOPs | Wall time (CPU) | Frequency |
|---|---|---|---|
| MAML 1-step adapt (20 samples) | ~40K | <1 ms | Every 50 ctrl cycles |
| Residual forward (1000×20 MPPI) | 195M | ~5 ms | Every ctrl cycle |
| Ensemble-3 residual forward | 584M | ~15 ms | Every ctrl cycle |
| Energy reg check (per training step) | ~20K | <0.1 ms | Training only |

MAML adaptation fits comfortably in the MPPI budget. The 1-step adaptation
every 2.5 seconds adds negligible overhead.

---

## Key design decisions for our project

1. **Start with 1-step MAML** — simplest, cheapest. Multi-step MAML
   (Antoniou et al., 2018) can be added later if 1-step is insufficient.

2. **Task distribution matters more than algorithm details.** The range
   of dynamics parameters in `UnicycleTaskDistribution` determines what
   environments MAML can adapt to. Start broad, narrow based on real gaps.

3. **Energy regularization in both loops.** This is the composability
   advantage — safety survives adaptation.

4. **Evaluate MAML vs. fine-tuning first.** Before committing to the MAML
   training complexity, run a quick experiment: can 1–5 gradient steps of
   plain fine-tuning (from a pre-trained model) match MAML? If yes for
   our low-dim system, the simpler approach wins.

5. **Defer context-conditioned models.** These require architecture changes
   and more training data. MAML wraps our existing MLP — lower integration
   cost for P2.

---

## Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MAML overfits to task distribution | Medium | Model fails on OOD envs | Broad task distribution + domain randomization fallback |
| Second-order gradients expensive | Low (small model) | Training slow | First-order MAML (FOMAML) as fallback — drops Hessian |
| Adapted model destabilizes MPPI | Low | Unsafe trajectories | Energy regularizer + rollout divergence detector |
| PyTorch `higher` lib compatibility | Medium | Training loop blocked | Manual gradient computation as fallback |

---

## Conclusion

MAML-based meta-learning is the best-fit adaptation strategy for our P2
residual dynamics model because:

1. **Minimal architecture change** — wraps the existing MLP training loop
2. **Composes with energy regularization** — safety survives adaptation
3. **Composes with ensemble** — option 2 (shared init, diverge at adapt)
   preserves uncertainty semantics
4. **Computationally cheap** — 1-step adapt on 20 samples < 1 ms
5. **Addresses the core sim-to-real gap** — the single biggest risk when
   deploying learned dynamics from synthetic data

**Recommended next step**: Extend `gen_unicycle_dataset.py` with `--meta`
task-distributed mode, then implement `learning/maml_residual.py` once
PyTorch is available.
