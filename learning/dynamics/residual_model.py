"""Learned residual dynamics: probabilistic MLP-ensemble (PyTorch).

This is ``g_theta`` in ``s_{t+1} = f_nominal(s_t, a_t) + g_theta(s_t, a_t)``
(D-009). It is an ensemble of small MLPs; the spread across ensemble members is
used as an epistemic-uncertainty estimate (reused as a P3 risk channel).

Requires PyTorch. Importing this module without torch raises ``ImportError`` at
import time — keep the import local to call sites that have torch available. The
nominal model (:mod:`learning.dynamics.nominal`) stays torch-free on purpose.

Network I/O:

- input  : ``[x, y, theta, v, omega]`` → 5 dims. ``theta`` is fed raw in this
  build-first scaffold; switching to ``(sin theta, cos theta)`` to remove the
  wrap discontinuity is a tracked follow-up.
- output : residual on the next state ``[dx, dy, dtheta]`` → 3 dims.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .nominal import ACTION_DIM, STATE_DIM

INPUT_DIM = STATE_DIM + ACTION_DIM  # 5
OUTPUT_DIM = STATE_DIM             # 3


class _ResidualMLP(nn.Module):
    """A single ensemble member: MLP from [s, a] to a state residual."""

    def __init__(self, hidden: int = 64, depth: int = 2):
        super().__init__()
        layers: list[nn.Module] = []
        last = INPUT_DIM
        for _ in range(depth):
            layers += [nn.Linear(last, hidden), nn.SiLU()]
            last = hidden
        layers.append(nn.Linear(last, OUTPUT_DIM))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ResidualDynamicsEnsemble(nn.Module):
    """Ensemble of residual MLPs with disagreement-based uncertainty.

    Parameters
    ----------
    num_models : ensemble size N (>= 2 so disagreement is defined).
    hidden, depth : per-member MLP width / number of hidden layers.
    """

    def __init__(self, num_models: int = 5, hidden: int = 64, depth: int = 2):
        super().__init__()
        if num_models < 2:
            raise ValueError(f"need >= 2 ensemble members, got {num_models}")
        self.num_models = num_models
        self.members = nn.ModuleList(
            [_ResidualMLP(hidden=hidden, depth=depth) for _ in range(num_models)]
        )

    def _pack(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        if state.shape[-1] != STATE_DIM or action.shape[-1] != ACTION_DIM:
            raise ValueError(
                f"expected state[...,{STATE_DIM}] action[...,{ACTION_DIM}], "
                f"got {tuple(state.shape)} {tuple(action.shape)}"
            )
        return torch.cat([state, action], dim=-1)

    def forward(self, state: torch.Tensor, action: torch.Tensor):
        """Return ``(mean_residual, epistemic_std)``.

        - ``mean_residual`` : ``(B, 3)`` ensemble-mean state correction.
        - ``epistemic_std``  : ``(B, 3)`` per-dim std across members (disagreement).
        """
        x = self._pack(state, action)
        preds = torch.stack([m(x) for m in self.members], dim=0)  # (N, B, 3)
        return preds.mean(dim=0), preds.std(dim=0)

    def all_member_residuals(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """Stacked per-member residuals ``(N, B, 3)`` (for particle-style rollout)."""
        x = self._pack(state, action)
        return torch.stack([m(x) for m in self.members], dim=0)
