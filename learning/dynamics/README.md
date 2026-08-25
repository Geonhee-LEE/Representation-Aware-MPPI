# Learned Residual Dynamics (Phase 2)

Scaffold for the P2 learned dynamics model that MPPI rollout will query.

## Residual formulation (D-009)

```
s_{t+1} = f_nominal(s_t, a_t) + g_theta(s_t, a_t)
```

- `f_nominal` — hand-derived **differential-drive** kinematics, pure NumPy
  ([`nominal.py`](nominal.py)). Always importable; runs in the MPPI rollout.
- `g_theta` — learned **MLP-ensemble** residual correction, PyTorch
  ([`residual_model.py`](residual_model.py)). Ensemble disagreement gives an
  epistemic-uncertainty signal (reused as a P3 risk channel).

## Conventions

| symbol | meaning | dims |
|---|---|---|
| `s = [x, y, theta]` | SE(2) pose (theta in rad) | 3 |
| `a = [v, omega]` | body linear / angular velocity | 2 |
| network input `[s, a]` | concat | 5 |
| network output | next-state residual `[dx, dy, dtheta]` | 3 |

## Files

| file | contents | torch? |
|---|---|---|
| `nominal.py` | `NominalDiffDrive` (step / rollout), `wrap_angle` | no |
| `residual_model.py` | `ResidualDynamicsEnsemble` (mean + epistemic std) | yes |
| `test/test_nominal.py` | nominal-model unit tests | no |
| `test/test_residual_model.py` | ensemble unit tests (skips w/o torch) | optional |

## Running tests

```bash
pytest learning/dynamics/test/                 # full (needs torch for the ensemble)
pytest learning/dynamics/test/test_nominal.py  # torch-free subset
```

## Not yet built (P2 follow-ups)

1. **Training data pipeline** — collect `(s, a, s_next)` tuples from sim
   rollouts; the residual target is `s_next - f_nominal(s, a)`.
2. **Trainer** — fit the ensemble (per-member bootstrap / different seeds) with
   an NLL or MSE loss.
3. **MPPI rollout hook** — query `g_theta` per sampled trajectory and fold the
   epistemic std into the cost.
4. **Angle encoding** — feed `(sin theta, cos theta)` instead of raw `theta` to
   remove the wrap discontinuity at ±pi.
