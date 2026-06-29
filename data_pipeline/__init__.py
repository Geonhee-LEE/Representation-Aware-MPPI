"""Training-data collection pipeline for the residual dynamics model.

Produces ``(state, action, next_state, dt)`` tuples that the residual
learner (``learning.residual.ResidualEnsemble``) consumes. The trainer
computes its target as ``delta = next_state - nominal_step(state, action)``,
so this pipeline only needs to emit *ground-truth* transitions — it stays
intentionally decoupled from the nominal/residual model code.

Conventions match ``learning.nominal`` / ``learning.residual``:
    state  s = [x, y, theta, v, omega]   (5,)
    action a = [v_cmd, omega_cmd]         (2,)
"""

from .replay_buffer import ReplayBuffer, STATE_DIM, ACTION_DIM

__all__ = ["ReplayBuffer", "STATE_DIM", "ACTION_DIM"]
