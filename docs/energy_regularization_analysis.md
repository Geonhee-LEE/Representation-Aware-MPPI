# Energy-Based Regularization for Residual Dynamics in MPPI

Reference: arxiv 2604.14678 (April 2026)

## Problem

When learning a residual dynamics model f_res to augment the nominal
unicycle model f_nom, nothing prevents the residual from injecting
spurious energy. During MPPI rollouts the error compounds over the
horizon (64 steps at dt=0.1 s → 6.4 s), so even a small per-step
energy injection causes trajectory divergence and unsafe cost
evaluations.

## Core idea

Add a **hinge-loss energy regularizer** to the training objective:

    L_total = L_data + λ · L_energy

    L_data  = (1/N) Σ ‖f_nom(xᵢ,uᵢ) + f_res(xᵢ,uᵢ) − x_{i+1}‖²

    L_energy = (1/N) Σ max(0, V(x_nom + Δ) − V(x_nom))

where V is a scalar energy function (kinetic, quadratic-goal, or
learned Lyapunov). The hinge loss activates only when the residual
**increases** system energy relative to the nominal prediction — it
does not penalize energy-neutral or energy-reducing corrections.

## Energy function choices for differential drive

| V(x)                          | Pros                      | Cons                       |
|-------------------------------|---------------------------|----------------------------|
| 0.5(v² + ω²)                 | Simple, no goal required  | Ignores position drift     |
| ‖pos − goal‖² + α(v² + ω²)  | Full-state, goal-aware    | Needs goal at train time   |
| Learned Lyapunov V_θ(x)      | Adapts to true basin      | Extra model to train       |

For the P2 prototype we use **kinetic energy** V = 0.5(v² + ω²) — it
is goal-free (works for the synthetic dataset which has random goals)
and directly prevents velocity blow-up, the most dangerous failure mode
during MPPI rollouts.

## How it applies to our stack

```
                 ┌──────────────┐
  (x, u) ───────┤  f_nom       ├──── x_nom
                 │  (unicycle)  │         │
                 └──────────────┘         │
                 ┌──────────────┐         ▼
  (x, u) ───────┤  f_res (MLP) ├──── x_nom + Δ ──── MPPI rollout cost
                 │  θ learned   │     ▲
                 └──────────────┘     │
                                 L_energy guards
                                 this addition
```

1. **Nominal**: `UnicycleNominalDynamics` — first-order velocity lag
   (tau_v=0.2, tau_omega=0.1) matching the TCFM dataset generator's
   kinematic model.
2. **Residual**: 2-layer MLP (7→64→64→5), output-layer zero-init so
   residual starts near zero (safe from epoch 0).
3. **Training**: MSE data loss + λ=0.1–1.0 energy regularizer. The
   paper reports 23% positional accuracy improvement over analytical
   MPC alone.

## Design decisions for P2

- **λ schedule**: Start λ=0.5 (strong regularization) for the first
  50% of epochs, decay to λ=0.1 to let the residual fit fine details.
- **Rollout-aware variant** (future): Apply the energy check over a
  K-step rollout instead of single-step. This catches slow energy drift
  that single-step hinge misses. Defer to P3 when we have real sim
  data.
- **Integration point**: The regularizer is a standalone PyTorch module
  (`learning/energy_regularizer.py`) that plugs into any training loop.
  The TCFM TemporalUnet trainer (next TODO) imports it as:
  ```python
  from learning.energy_regularizer import EnergyRegularizer
  L_energy = regularizer.compute(nominal_next, combined_next)
  ```

## Open questions

1. How does λ interact with TCFM's flow-matching loss? The ODE loss
   already regularizes trajectory smoothness; energy regularization may
   be redundant or complementary. Needs ablation.
2. Should V be defined in state-space or in the TCFM latent space? If
   the TemporalUnet transforms states before predicting, latent-space
   energy might be more meaningful.
3. The paper uses quadrotor dynamics — how much of the 23% gain
   transfers to the simpler unicycle domain? Likely less, since the
   unicycle has fewer unstable modes.

## Prototype

See `learning/energy_regularizer.py` — runnable demo with synthetic
data, validates that the regularizer keeps residual magnitude bounded
while achieving good prediction accuracy.
