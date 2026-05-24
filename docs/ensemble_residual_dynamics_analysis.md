# Ensemble Residual Dynamics: MPPI Parallel Rollout Compatibility

_Analysis for TODO `36ac5d39` — based on doi:10.3390/s26010340_

## Question

Does an ensemble-of-K residual dynamics MLP fit inside MPPI's parallel
rollout budget (1000 samples × 20 horizon steps = 20,000 forward calls per
control cycle at 50 Hz)?

## Architecture under test

Two model families from the P2 learning stack:

| Model | Params | FLOPs/call | Purpose |
|---|---|---|---|
| `ResidualDynamicsNet` (64-hidden, 2-layer) | 4,997 | 9.7K | Direct step correction on nominal unicycle |
| `MLPCFMVelocityField` (128-hidden, FiLM) | 59,013 | 117K | Flow-matching velocity field (needs 20 Euler steps) |

## FLOPs per control cycle (N=1000, H=20)

| Config | Residual | CFM (×20 Euler) |
|---|---|---|
| Single model | 195M | 46.8G |
| Ensemble-3 (serial) | 584M | 140G |
| Ensemble-3 (batched, `vmap`) | ~195-250M wall | ~47-61G wall |

Reference: one ResNet-18 forward = 1.8G FLOPs.

## Verdict

**Residual dynamics ensemble: ✅ fully compatible.** At 584M serial FLOPs
(0.32× of a single ResNet-18 forward), an ensemble-of-3 is negligible even
without GPU batching. With weight-stacked `vmap`, wall-clock overhead is
~1.0–1.3× vs single model.

**CFM velocity field ensemble: ⚠️ heavy.** The 20-step Euler integration
multiplier pushes ensemble-3 to 140G FLOPs — 78× a ResNet-18 forward. Even
with GPU batching this may not fit a 50 Hz budget. Single CFM + residual
ensemble is the pragmatic split.

## Memory footprint (fp32)

| Component | Single | Ensemble-3 |
|---|---|---|
| Residual weights | 19.5 KB | 58.6 KB |
| CFM weights | 230.5 KB | 691.6 KB |
| Activations (batch=1000) | 19.5 KB | 58.6 KB |

Memory is not a constraint for either model at this scale.

## Recommended architecture for P2→P3

```
                       ┌──────────────────────┐
  state_t, action_t ──▶│ Nominal Unicycle f(·) │──▶ x_nominal
                       └──────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
   ┌─────────────┐     ┌─────────────┐      ┌─────────────┐
   │ Residual #1 │     │ Residual #2 │      │ Residual #3 │
   └──────┬──────┘     └──────┬──────┘      └──────┬──────┘
          │                   │                     │
          └─────────┬─────────┴─────────────────────┘
                    ▼
            mean(δ₁, δ₂, δ₃) → x_combined = x_nominal + mean_δ
            var(δ₁, δ₂, δ₃)  → σ²_epistemic  ─── feeds P3 risk channel
```

1. **Ensemble the residual, not the CFM.** The residual MLP is 12× smaller and
   runs once per step (no Euler loop). Ensembling adds <3× serial FLOPs — well
   under budget.

2. **Epistemic uncertainty for free.** Per-sample variance across K residual
   heads estimates model disagreement. This directly feeds P3's epistemic
   uncertainty channel without a separate uncertainty model.

3. **Feature-driven activation gate** (from the paper). Only apply the ensemble
   residual when disagreement exceeds a threshold — when the ensemble agrees,
   fall back to single-head for speed. This makes the effective overhead < 3× in
   practice (most state-space regions are well-covered by training data).

4. **Energy regularization stacks.** The `EnergyRegularizer` from PR #24 applies
   per-head: each residual is independently energy-bounded, so the ensemble mean
   inherits stability.

## Implementation plan

When PyTorch is available:

1. Wrap `ResidualDynamicsNet` in `EnsembleResidualDynamics(K=3)` — store K
   independent `nn.Module` instances, forward returns `(mean_delta, var_delta)`.
2. Add `activation_gate(var_delta, threshold)` — binary mask per sample.
3. Train each head on bootstrap-resampled subsets of the same dataset (standard
   ensemble diversity technique).
4. Pipe `var_delta` into MPPI cost as `+ lambda_epistemic * var_delta.sum(-1)` —
   samples that land in high-disagreement regions get penalized.

Estimated LOC: ~60 (ensemble wrapper) + ~20 (MPPI cost integration).

## Relation to other P2 work

| Artifact | How it connects |
|---|---|
| `learning/mlp_cfm_unicycle.py` (PR #26) | CFM stays single-model; ensemble insight says "don't ensemble this" |
| `learning/energy_regularizer.py` (PR #24) | Energy reg applies per-head, ensuring ensemble stability |
| `scripts/gen_unicycle_dataset.py` (PR #23) | Dataset generator produces training data for ensemble heads |
| `docs/cfm_mppi_analysis.md` (PR #25) | CFM architectural context; ensemble analysis complements it |

## Source

- Paper: [Ensemble Residual Dynamics for MPC Path Tracking](https://doi.org/10.3390/s26010340)
- Key insight: feature-driven activation gate + ensemble uncertainty
- FLOPs script: `learning/ensemble_flops_estimate.py` (this branch)
