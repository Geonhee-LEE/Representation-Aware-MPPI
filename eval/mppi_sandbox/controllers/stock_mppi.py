# SPDX-License-Identifier: BSD-3-Clause
"""Pure-NumPy vanilla MPPI (Williams et al. 2017 information-theoretic form).

Sandbox baseline controller — the reference every representation-aware
variant is measured against. Deterministic: all sampling flows through a
seeded numpy Generator, so identical (scenario, seed) → identical run.

Cost = path-tracking (perpendicular distance^2 to reference polyline)
     + speed tracking (ramped down near goal so the robot stops)
     + obstacle soft barrier + hard collision penalty
     + terminal goal distance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..dynamics import Limits, step


@dataclass
class MPPIParams:
    horizon: int = 30
    samples: int = 256
    dt: float = 0.1
    lam: float = 0.1                       # softmax temperature
    sigma_v: float = 0.15
    sigma_w: float = 0.5
    w_path: float = 20.0
    w_speed: float = 2.0
    w_obs_soft: float = 10.0
    obs_soft_scale: float = 0.3            # [m] barrier decay length
    w_collision: float = 1.0e4
    w_terminal: float = 30.0
    w_omega: float = 0.5                   # rotation effort — no free pirouettes
    goal_slowdown_gain: float = 0.8        # v_ref = min(v*, gain·dist_to_goal)
    creep_speed: float = 0.08              # floor so the robot finishes the path


def _polyline_distance(pts: np.ndarray, path_xy: np.ndarray) -> np.ndarray:
    """Min perpendicular distance from each point (N,2) to polyline (M,2)."""
    a, b = path_xy[:-1], path_xy[1:]                     # (S,2)
    d = b - a
    len2 = np.maximum((d * d).sum(axis=1), 1e-12)        # (S,)
    ap = pts[:, None, :] - a[None]                       # (N,S,2)
    t = np.clip((ap * d[None]).sum(axis=2) / len2, 0.0, 1.0)
    proj = a[None] + t[..., None] * d[None]              # (N,S,2)
    return np.linalg.norm(pts[:, None, :] - proj, axis=2).min(axis=1)


class StockMPPI:
    def __init__(self, scenario, seed: int = 0,
                 params: MPPIParams | None = None,
                 limits: Limits | None = None,
                 robot_radius: float = 0.3):
        self.p = params or MPPIParams()
        self.limits = limits or Limits()
        self.rng = np.random.default_rng(seed)
        self.path_xy = scenario.waypoints[:, :2]
        self.goal_xy = scenario.goal[:2]
        self.target_speed = scenario.target_speed
        self.obstacles = scenario.obstacles
        self.robot_radius = robot_radius
        self.U = np.zeros((self.p.horizon, 2))           # warm-started plan
        self.U[:, 0] = scenario.target_speed

    def command(self, state: np.ndarray, t: float) -> np.ndarray:
        p, lim = self.p, self.limits
        noise = self.rng.normal(
            0.0, [p.sigma_v, p.sigma_w], size=(p.samples, p.horizon, 2))
        controls = self.U[None] + noise                  # (K,H,2)
        controls[..., 0] = np.clip(controls[..., 0], lim.v_min, lim.v_max)
        controls[..., 1] = np.clip(controls[..., 1], -lim.omega_max, lim.omega_max)

        # rollout: (K,5) advanced H steps with the shared plant model
        states = np.broadcast_to(state, (p.samples, 5)).copy()
        traj = np.empty((p.samples, p.horizon, 5))
        for h in range(p.horizon):
            states = step(states, controls[:, h], p.dt, lim)
            traj[:, h] = states

        cost = self._cost(traj, t)
        beta = cost.min()
        w = np.exp(-(cost - beta) / p.lam)
        w /= w.sum()

        self.U = self.U + np.einsum("k,khu->hu", w, noise)
        self.U[:, 0] = np.clip(self.U[:, 0], lim.v_min, lim.v_max)
        self.U[:, 1] = np.clip(self.U[:, 1], -lim.omega_max, lim.omega_max)

        u0 = self.U[0].copy()
        self.U[:-1] = self.U[1:]                          # receding-horizon shift
        return u0

    def _cost(self, traj: np.ndarray, t0: float) -> np.ndarray:
        p = self.p
        K, H, _ = traj.shape
        xy = traj[..., :2].reshape(K * H, 2)

        d_path = _polyline_distance(xy, self.path_xy).reshape(K, H)
        cost = p.w_path * (d_path ** 2).sum(axis=1)

        dist_goal = np.linalg.norm(traj[..., :2] - self.goal_xy, axis=2)  # (K,H)
        v_ref = np.minimum(self.target_speed,
                           np.maximum(p.goal_slowdown_gain * dist_goal,
                                      p.creep_speed))
        cost += p.w_speed * ((traj[..., 3] - v_ref) ** 2).sum(axis=1)
        cost += p.w_omega * (traj[..., 4] ** 2).sum(axis=1)

        if self.obstacles:
            times = t0 + p.dt * np.arange(1, H + 1)
            for ob in self.obstacles:
                pos = ob.position(times)                              # (H,2)
                clear = (np.linalg.norm(traj[..., :2] - pos[None], axis=2)
                         - ob.radius - self.robot_radius)             # (K,H)
                cost += p.w_obs_soft * np.exp(-clear / p.obs_soft_scale).sum(axis=1)
                cost += p.w_collision * (clear < 0.0).any(axis=1)

        cost += p.w_terminal * dist_goal[:, -1] ** 2
        return cost
