# SPDX-License-Identifier: BSD-3-Clause
"""ShadowCostCritic — additive epistemic shadow-entry cost (Q-017 answer (a)).

The complement to RiskInflationCritic (D-013). Where the k·σ margin *shrinks
clearance to a known obstacle* — and was measured closed-loop inert in
occlusion geometry (Q-017: the min-clearance point is always visible, σ = 0,
and rollouts reach the shadow only after the swerve commits) — this critic
charges each rollout point an **additive** cost proportional to the epistemic
σ it traverses:

    cost_k = w_epist · Σ_h σ(x_kh)          [EPISTEMIC channel, idx 3]

The mechanism is fundamentally different from margin inflation:

- Margin inflation is *obstacle-relative*: it only bites where a known
  obstacle's clearance term is already active, so a shadow with no modelled
  obstacle behind it is free. That is exactly the horizon-visibility race
  Q-017 diagnosed.
- Additive shadow cost is *field-absolute*: driving through an occlusion
  shadow (or beyond sensing range) is priced whether or not a known obstacle
  sits there, so the plan is biased toward staying in observed (σ = 0) space —
  which is what "avoid the blind corner" actually requires.

Contract (mirrors D-013 so P5 ablation attribution holds):
- standalone — never overloads the baseline obstacle term
- add-only: cost ≥ 0 (σ ∈ [0, 1], w_epist ≥ 0)
- w_epist = 0.0 default → exact no-op → baseline reproduction (ablation invariant)
- unobserved (out-of-grid) points sample the pessimistic prior σ = 1.0 (D-012)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..representations import RiskChannel


@dataclass
class ShadowCostCritic:
    w_epist: float = 0.0    # additive cost per unit σ per rollout point — 0 = no-op

    def cost(self, bev, xy_flat: np.ndarray, K: int) -> np.ndarray:
        """(K,) additive per-rollout shadow-entry cost.

        `xy_flat` is the (K·H, 2) stack of rollout world points (row-major
        over rollouts then horizon), `K` the rollout count.
        """
        if self.w_epist == 0.0 or bev is None:
            return np.zeros(K)
        sigma = bev.sample(RiskChannel.EPISTEMIC, xy_flat, unobserved_value=1.0)
        return self.w_epist * sigma.reshape(K, -1).sum(axis=1)
