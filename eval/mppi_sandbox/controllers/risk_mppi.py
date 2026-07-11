# SPDX-License-Identifier: BSD-3-Clause
"""Representation-aware MPPI — StockMPPI consuming the D-012 BEV stack.

Two consumption paths, matching the project's critic routing decisions:

1. DYNAMIC channel (idx 1) → additive risk cost (`w_risk`): rollout points
   are charged for entering the *anticipated sweep* of scripted obstacles
   (Gaussian blobs along predicted positions). This is what makes the
   controller yield early / give a wide berth instead of grazing — vanilla
   MPPI only reacts to where the obstacle is at each rollout instant.

2. EPISTEMIC channel (idx 3) → RiskInflationCritic (D-013): clearance to
   every obstacle shrinks by clip(k·σ, 0, Δ_max) — ignorance (occlusion
   shadows, beyond sensing range) buys physical margin. tighten-only,
   k = 0 default → byte-identical to stock_mppi (ablation invariant).

The BEV is rendered once per control step (ego-centered window); rollout
points that leave the window sample the pessimistic prior.
"""

from __future__ import annotations

import numpy as np

from ..critics import RiskInflationCritic
from ..dynamics import Limits
from ..representations import GTBevProducer, RiskChannel
from .stock_mppi import MPPIParams, StockMPPI


class RiskMPPI(StockMPPI):
    def __init__(self, scenario, seed: int = 0,
                 params: MPPIParams | None = None,
                 limits: Limits | None = None,
                 robot_radius: float = 0.3,
                 w_risk: float = 40.0,
                 k_margin_per_sigma: float = 0.0,
                 delta_max: float = 0.5,
                 blob_scale: float = 1.5,
                 producer: GTBevProducer | None = None):
        super().__init__(scenario, seed=seed, params=params, limits=limits,
                         robot_radius=robot_radius)
        self.w_risk = w_risk
        self.critic = RiskInflationCritic(k_margin_per_sigma, delta_max)
        self.producer = producer or GTBevProducer(scenario.obstacles,
                                                  blob_scale=blob_scale)
        self._bev = None

    def command(self, state: np.ndarray, t: float) -> np.ndarray:
        active = self.w_risk != 0.0 or self.critic.k_margin_per_sigma != 0.0
        self._bev = (self.producer.render(state[:2], t)
                     if (active and self.obstacles) else None)
        return super().command(state, t)

    def _extra_margin(self, xy_flat: np.ndarray, t0: float) -> np.ndarray:
        if self._bev is None:
            return np.zeros(len(xy_flat))
        return self.critic.margin(self._bev, xy_flat)

    def _extra_cost(self, traj: np.ndarray, t0: float) -> np.ndarray:
        K = traj.shape[0]
        if self._bev is None or self.w_risk == 0.0:
            return np.zeros(K)
        xy = traj[..., :2].reshape(-1, 2)
        risk = self._bev.sample(RiskChannel.DYNAMIC, xy, unobserved_value=0.0)
        return self.w_risk * risk.reshape(K, -1).sum(axis=1)
