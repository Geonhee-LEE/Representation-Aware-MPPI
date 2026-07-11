# SPDX-License-Identifier: BSD-3-Clause
"""Differential-drive kinematics for the sandbox.

State  (5,): [x, y, yaw, v, omega]        (v, omega = realized body rates)
Control (2,): [v_cmd, omega_cmd]

Velocity tracks the command under acceleration limits (first-order,
rate-clipped) so MPPI smoothness costs and jerk metrics are non-trivial.
`step` accepts both a single state (5,) and a batch (K, 5) — the same
function is the sim plant and the MPPI rollout model (model = truth in v0;
P2 residual work will deliberately break that equality).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Limits:
    v_min: float = 0.0
    v_max: float = 0.8
    omega_max: float = 1.5
    accel_max: float = 1.0       # m/s^2
    alpha_max: float = 2.0       # rad/s^2


def step(state: np.ndarray, control: np.ndarray, dt: float,
         limits: Limits | None = None) -> np.ndarray:
    """Advance diff-drive state(s) by dt. Shapes: (5,)/(2,) or (K,5)/(K,2)."""
    lim = limits or Limits()
    s = np.atleast_2d(np.asarray(state, dtype=float))
    u = np.atleast_2d(np.asarray(control, dtype=float))

    v_cmd = np.clip(u[:, 0], lim.v_min, lim.v_max)
    w_cmd = np.clip(u[:, 1], -lim.omega_max, lim.omega_max)

    dv = np.clip(v_cmd - s[:, 3], -lim.accel_max * dt, lim.accel_max * dt)
    dw = np.clip(w_cmd - s[:, 4], -lim.alpha_max * dt, lim.alpha_max * dt)

    out = np.empty_like(s)
    out[:, 3] = s[:, 3] + dv
    out[:, 4] = s[:, 4] + dw
    out[:, 2] = s[:, 2] + out[:, 4] * dt
    out[:, 0] = s[:, 0] + out[:, 3] * np.cos(out[:, 2]) * dt
    out[:, 1] = s[:, 1] + out[:, 3] * np.sin(out[:, 2]) * dt

    return out[0] if np.asarray(state).ndim == 1 else out
