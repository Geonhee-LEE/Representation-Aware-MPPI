"""Synthetic 'true plant' for generating residual-learning data offline.

Until sim/rosbag rollout logging is wired, we need *some* ground-truth
transitions so the residual trainer has something to fit. This module
models a diff-drive robot with **deliberately unmodeled effects** that the
nominal model (``learning.nominal.nominal_step``) does not capture:

  * velocity-dependent longitudinal drag (slows the robot more at speed),
  * heading-rate slip (achieved omega lags command beyond the nominal lag),
  * a small constant lateral drift (miscalibrated wheelbase).

The gap between this plant and the nominal model *is* the residual the
ensemble learns. Keeping the plant here (not in ``learning/``) keeps the
data pipeline self-contained and decoupled from the model code.

NOTE: this is a stand-in for real sim data, not a validated robot model.
Replace ``true_plant_step`` with sim/rosbag logging once available.
"""

from __future__ import annotations

import numpy as np


def true_plant_step(state, action, dt: float = 0.1, tau: float = 0.3,
                    drag: float = 0.12, slip: float = 0.08,
                    lateral_drift: float = 0.01):
    """One step of the synthetic 'true' diff-drive plant.

    Args mirror ``learning.nominal.nominal_step`` plus unmodeled-effect
    gains. Returns ``np.ndarray`` next state ``[x, y, theta, v, omega]``.
    """
    x, y, theta, v, omega = (float(c) for c in state)
    v_cmd, omega_cmd = (float(c) for c in action)

    # Velocity tracking with extra drag (unmodeled vs nominal first-order lag).
    v_next = v + (dt / tau) * (v_cmd - v) - drag * v * dt
    omega_next = omega + (dt / tau) * (omega_cmd - omega) - slip * omega * dt

    # Pose integration with a small lateral drift in the body frame.
    x_next = x + (v * np.cos(theta) - lateral_drift * np.sin(theta)) * dt
    y_next = y + (v * np.sin(theta) + lateral_drift * np.cos(theta)) * dt
    theta_next = theta + omega * dt
    theta_next = (theta_next + np.pi) % (2 * np.pi) - np.pi

    return np.array([x_next, y_next, theta_next, v_next, omega_next])
