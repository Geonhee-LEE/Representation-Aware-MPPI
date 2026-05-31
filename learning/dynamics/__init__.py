"""Learned residual dynamics for Representation-Aware MPPI (Phase 2).

Residual form (D-009):

    s_{t+1} = f_nominal(s_t, a_t) + g_theta(s_t, a_t)

where ``f_nominal`` is a hand-derived differential-drive kinematic model and
``g_theta`` is a learned correction. ``g_theta`` is realised as an ensemble of
small MLPs so that ensemble disagreement yields an epistemic-uncertainty signal
(reused later as a P3 risk channel).

The nominal model is pure NumPy and always importable. The learned ensemble
lives in :mod:`learning.dynamics.residual_model` and requires PyTorch; import it
explicitly where torch is available.
"""

from .nominal import NominalDiffDrive, wrap_angle

__all__ = ["NominalDiffDrive", "wrap_angle"]
