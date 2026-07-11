# SPDX-License-Identifier: BSD-3-Clause
"""RiskInflationCritic — epistemic k·σ margin inflation (D-013).

Sandbox implementation of docs/margin_inflation_cost_critic_interface.md:
the epistemic channel (RiskChannel.EPISTEMIC, idx 3) shrinks *effective*
clearance to obstacles by k·σ(x) — ignorance buys physical margin, and the
margin vanishes as σ → 0 (more data / better visibility).

Contract (D-013):
- standalone — never overloads the baseline obstacle term
- tighten-only: inflation ≥ 0 (never relaxes clearance)
- clamped: inflation ≤ delta_max
- k = 0.0 default → exact no-op → baseline reproduction (P5 ablation invariant)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..representations import RiskChannel


@dataclass
class RiskInflationCritic:
    k_margin_per_sigma: float = 0.0    # [m] margin per unit σ — 0 = no-op
    delta_max: float = 0.5             # [m] clamp on the added margin

    def margin(self, bev, pts: np.ndarray) -> np.ndarray:
        """(N,) tighten-only clearance shrink for world points (N, 2)."""
        if self.k_margin_per_sigma == 0.0 or bev is None:
            return np.zeros(len(pts))
        sigma = bev.sample(RiskChannel.EPISTEMIC, pts, unobserved_value=1.0)
        return np.clip(self.k_margin_per_sigma * sigma, 0.0, self.delta_max)
