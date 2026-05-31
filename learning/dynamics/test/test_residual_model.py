"""Unit tests for the PyTorch MLP-ensemble residual model.

Skips cleanly when torch is not installed, so the torch-free portion of the
suite (``test_nominal.py``) still runs in minimal environments.
"""

import os
import sys

import pytest

torch = pytest.importorskip("torch")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from learning.dynamics.residual_model import (  # noqa: E402
    INPUT_DIM,
    OUTPUT_DIM,
    ResidualDynamicsEnsemble,
)


def test_forward_shapes():
    ens = ResidualDynamicsEnsemble(num_models=4, hidden=16, depth=2)
    state = torch.zeros(8, 3)
    action = torch.zeros(8, 2)
    mean, std = ens(state, action)
    assert mean.shape == (8, OUTPUT_DIM)
    assert std.shape == (8, OUTPUT_DIM)


def test_uncertainty_nonnegative():
    ens = ResidualDynamicsEnsemble(num_models=5, hidden=16, depth=2)
    state = torch.randn(16, 3)
    action = torch.randn(16, 2)
    _, std = ens(state, action)
    assert torch.all(std >= 0.0)


def test_distinct_members_disagree():
    # Randomly initialised members should not all be identical -> nonzero std.
    ens = ResidualDynamicsEnsemble(num_models=5, hidden=16, depth=2)
    _, std = ens(torch.randn(32, 3), torch.randn(32, 2))
    assert std.mean().item() > 0.0


def test_all_member_residuals_shape():
    ens = ResidualDynamicsEnsemble(num_models=3, hidden=16, depth=2)
    out = ens.all_member_residuals(torch.zeros(5, 3), torch.zeros(5, 2))
    assert out.shape == (3, 5, OUTPUT_DIM)


def test_input_dim_constant():
    assert INPUT_DIM == 5


def test_rejects_singleton_ensemble():
    with pytest.raises(ValueError):
        ResidualDynamicsEnsemble(num_models=1)


def test_dim_validation():
    ens = ResidualDynamicsEnsemble(num_models=2, hidden=8, depth=1)
    with pytest.raises(ValueError):
        ens(torch.zeros(4, 2), torch.zeros(4, 2))  # bad state dim
