"""Nominal differential-drive kinematic model (pure NumPy).

This is ``f_nominal`` in the residual decomposition
``s_{t+1} = f_nominal(s_t, a_t) + g_theta(s_t, a_t)`` (D-009). It is deliberately
dependency-light (NumPy only) so it can run inside the MPPI rollout and be unit
tested without PyTorch.

State / action conventions (shared across the whole P2 dynamics stack):

- state  ``s = [x, y, theta]``  — SE(2) pose, ``theta`` in radians.
- action ``a = [v, omega]``     — body-frame linear / angular velocity.

Both batched (``(B, 3)`` / ``(B, 2)``) and single-sample (``(3,)`` / ``(2,)``)
inputs are accepted; the output matches the input rank.
"""

from __future__ import annotations

import numpy as np

STATE_DIM = 3
ACTION_DIM = 2


def wrap_angle(theta):
    """Wrap angle(s) to ``(-pi, pi]``."""
    return (np.asarray(theta) + np.pi) % (2.0 * np.pi) - np.pi


class NominalDiffDrive:
    """Discrete-time unicycle / differential-drive forward model.

    Integration is explicit Euler on the unicycle kinematics::

        x'     = x + v * cos(theta) * dt
        y'     = y + v * sin(theta) * dt
        theta' = wrap(theta + omega * dt)

    Euler (rather than exact arc integration) is intentional: it keeps the
    nominal model simple and pushes the curvature/slip error into the learned
    residual ``g_theta``, which is exactly what P2 is meant to capture.
    """

    def __init__(self, dt: float = 0.1):
        if dt <= 0.0:
            raise ValueError(f"dt must be positive, got {dt}")
        self.dt = float(dt)

    def step(self, state, action):
        """Advance one timestep. Returns next state, same rank as ``state``."""
        s = np.asarray(state, dtype=float)
        a = np.asarray(action, dtype=float)
        single = s.ndim == 1
        s = np.atleast_2d(s)
        a = np.atleast_2d(a)
        if s.shape[-1] != STATE_DIM:
            raise ValueError(f"state last dim must be {STATE_DIM}, got {s.shape}")
        if a.shape[-1] != ACTION_DIM:
            raise ValueError(f"action last dim must be {ACTION_DIM}, got {a.shape}")
        if s.shape[0] != a.shape[0]:
            raise ValueError(f"batch mismatch: state {s.shape[0]} vs action {a.shape[0]}")

        x, y, theta = s[:, 0], s[:, 1], s[:, 2]
        v, omega = a[:, 0], a[:, 1]

        nxt = np.empty_like(s)
        nxt[:, 0] = x + v * np.cos(theta) * self.dt
        nxt[:, 1] = y + v * np.sin(theta) * self.dt
        nxt[:, 2] = wrap_angle(theta + omega * self.dt)

        return nxt[0] if single else nxt

    def rollout(self, state, actions):
        """Roll a sequence of actions ``(T, 2)`` from a single ``state`` ``(3,)``.

        Returns the ``(T, 3)`` trajectory of resulting states (excluding the
        initial state), matching the MPPI per-sample rollout shape.
        """
        s = np.asarray(state, dtype=float)
        acts = np.asarray(actions, dtype=float)
        if s.ndim != 1 or acts.ndim != 2:
            raise ValueError("rollout expects state (3,) and actions (T, 2)")
        traj = np.empty((acts.shape[0], STATE_DIM))
        cur = s
        for t in range(acts.shape[0]):
            cur = self.step(cur, acts[t])
            traj[t] = cur
        return traj
