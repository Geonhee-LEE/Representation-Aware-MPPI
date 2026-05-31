"""Append-only replay buffer for residual-dynamics training data.

Stores transitions ``(state, action, next_state, dt)`` and serializes to a
compressed ``.npz`` file. Kept dependency-light (numpy only) so data
collection can run anywhere — including headless CI — without torch.

The on-disk schema is the contract between *this* pipeline and the future
residual trainer, so it is versioned via ``SCHEMA_VERSION``. A trainer can
load the arrays and compute its supervision target as::

    feature = concat(state, action)                  # (N, 7)
    target  = next_state - nominal_step(state, act)  # (N, 5)
"""

from __future__ import annotations

import numpy as np

STATE_DIM = 5   # [x, y, theta, v, omega]
ACTION_DIM = 2  # [v_cmd, omega_cmd]
SCHEMA_VERSION = 1


class ReplayBuffer:
    """In-memory transition store with ``.npz`` (de)serialization."""

    def __init__(self):
        self._states = []
        self._actions = []
        self._next_states = []
        self._dts = []

    def __len__(self) -> int:
        return len(self._states)

    def add(self, state, action, next_state, dt: float) -> None:
        """Append one transition, validating dimensions."""
        s = np.asarray(state, dtype=np.float64).reshape(-1)
        a = np.asarray(action, dtype=np.float64).reshape(-1)
        ns = np.asarray(next_state, dtype=np.float64).reshape(-1)
        if s.shape[0] != STATE_DIM:
            raise ValueError(f"state must be {STATE_DIM}-dim, got {s.shape[0]}")
        if a.shape[0] != ACTION_DIM:
            raise ValueError(f"action must be {ACTION_DIM}-dim, got {a.shape[0]}")
        if ns.shape[0] != STATE_DIM:
            raise ValueError(f"next_state must be {STATE_DIM}-dim, got {ns.shape[0]}")
        self._states.append(s)
        self._actions.append(a)
        self._next_states.append(ns)
        self._dts.append(float(dt))

    def add_rollout(self, states, actions, next_states, dt: float) -> None:
        """Append a full trajectory of equal-length transition arrays."""
        if not (len(states) == len(actions) == len(next_states)):
            raise ValueError("states/actions/next_states length mismatch")
        for s, a, ns in zip(states, actions, next_states):
            self.add(s, a, ns, dt)

    def as_arrays(self):
        """Return ``(states, actions, next_states, dts)`` stacked arrays."""
        if len(self) == 0:
            return (
                np.empty((0, STATE_DIM)),
                np.empty((0, ACTION_DIM)),
                np.empty((0, STATE_DIM)),
                np.empty((0,)),
            )
        return (
            np.stack(self._states),
            np.stack(self._actions),
            np.stack(self._next_states),
            np.asarray(self._dts),
        )

    def stats(self) -> dict:
        """Summary stats useful for a sanity check after collection."""
        states, actions, next_states, _ = self.as_arrays()
        if len(self) == 0:
            return {"n": 0}
        delta = next_states - states
        return {
            "n": len(self),
            "state_mean": states.mean(axis=0).round(4).tolist(),
            "action_mean": actions.mean(axis=0).round(4).tolist(),
            "step_delta_abs_mean": np.abs(delta).mean(axis=0).round(4).tolist(),
        }

    def save(self, path: str) -> None:
        """Serialize to a compressed ``.npz`` at ``path``."""
        states, actions, next_states, dts = self.as_arrays()
        np.savez_compressed(
            path,
            schema_version=np.asarray(SCHEMA_VERSION),
            states=states,
            actions=actions,
            next_states=next_states,
            dts=dts,
        )

    @classmethod
    def load(cls, path: str) -> "ReplayBuffer":
        """Load a buffer previously written by :meth:`save`."""
        data = np.load(path)
        version = int(data["schema_version"])
        if version != SCHEMA_VERSION:
            raise ValueError(
                f"schema version {version} != expected {SCHEMA_VERSION}"
            )
        buf = cls()
        buf.add_rollout(
            data["states"], data["actions"], data["next_states"],
            dt=float(data["dts"][0]) if len(data["dts"]) else 0.0,
        )
        # add_rollout uses a single dt; restore the true per-step dts.
        buf._dts = list(np.asarray(data["dts"], dtype=np.float64))
        return buf
