"""Unit tests for the pure-NumPy nominal diff-drive model (torch-free)."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from learning.dynamics.nominal import NominalDiffDrive, wrap_angle  # noqa: E402


def test_wrap_angle_range():
    angles = np.array([0.0, np.pi, -np.pi, 3.0 * np.pi, -3.0 * np.pi, 10.0])
    wrapped = wrap_angle(angles)
    assert np.all(wrapped > -np.pi - 1e-9)
    assert np.all(wrapped <= np.pi + 1e-9)


def test_straight_line_motion():
    m = NominalDiffDrive(dt=0.5)
    nxt = m.step([0.0, 0.0, 0.0], [2.0, 0.0])  # v=2, omega=0, dt=0.5 -> +1 in x
    assert np.allclose(nxt, [1.0, 0.0, 0.0])


def test_pure_rotation_keeps_position():
    m = NominalDiffDrive(dt=0.1)
    nxt = m.step([1.0, 2.0, 0.0], [0.0, 1.0])
    assert np.allclose(nxt[:2], [1.0, 2.0])
    assert np.isclose(nxt[2], 0.1)


def test_batched_matches_single():
    m = NominalDiffDrive(dt=0.2)
    states = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, np.pi / 2]])
    actions = np.array([[1.0, 0.0], [1.0, 0.5]])
    batched = m.step(states, actions)
    singles = np.stack([m.step(states[i], actions[i]) for i in range(2)])
    assert np.allclose(batched, singles)


def test_rollout_shape_and_consistency():
    m = NominalDiffDrive(dt=0.1)
    actions = np.tile([1.0, 0.0], (10, 1))
    traj = m.rollout([0.0, 0.0, 0.0], actions)
    assert traj.shape == (10, 3)
    # Straight line at v=1, dt=0.1 for 10 steps -> x advances by 1.0 total.
    assert np.isclose(traj[-1, 0], 1.0)
    assert np.allclose(traj[:, 1], 0.0)


def test_dim_validation():
    m = NominalDiffDrive(dt=0.1)
    with pytest.raises(ValueError):
        m.step([0.0, 0.0], [1.0, 0.0])  # bad state dim
    with pytest.raises(ValueError):
        m.step([0.0, 0.0, 0.0], [1.0])  # bad action dim


def test_dt_must_be_positive():
    with pytest.raises(ValueError):
        NominalDiffDrive(dt=0.0)
