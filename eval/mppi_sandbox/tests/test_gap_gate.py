# SPDX-License-Identifier: BSD-3-Clause
"""Two-sided-gap barrier gate (MorphoCopter-MPC borrow) — see ..gap_gate."""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox.controllers import REGISTRY, make_controller
from eval.mppi_sandbox.gap_gate import gate_factor, two_sided_mu
from eval.mppi_sandbox.scenario import load_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"


# ---------------------------------------------------------------- mu

def test_single_obstacle_is_one_sided_so_mu_is_one():
    """N < 2 has no passage to be inside of — barrier must pass through."""
    delta = np.array([[[1.0, 0.0]]])          # (1,1,2)
    clear = np.array([[0.5]])                 # (1,1)
    assert two_sided_mu(delta, clear) == pytest.approx(1.0)


def test_mu_is_zero_on_a_true_centreline():
    """Opposed *and* equidistant — the one configuration the gate is for."""
    delta = np.array([[1.0, 0.0], [-1.0, 0.0]])   # (2,2)
    clear = np.array([0.4, 0.4])
    assert two_sided_mu(delta, clear) == pytest.approx(0.0)


def test_mu_is_one_when_both_obstacles_lie_the_same_way():
    delta = np.array([[1.0, 0.0], [2.0, 0.0]])
    clear = np.array([0.4, 1.2])
    assert two_sided_mu(delta, clear) == pytest.approx(1.0)


def test_off_centre_in_an_opposed_gap_restores_the_barrier():
    """The load-bearing safety property, and the reason mu carries an
    imbalance term the paper's does not.

    A pure opposite-sidedness test reads mu = 0 here — the obstacles straddle
    the robot — and would switch the soft barrier fully off while the robot is
    pressed against one wall. `max(alignment, imbalance)` refuses that.
    """
    delta = np.array([[0.05, 0.0], [-3.0, 0.0]])   # hugging the near one
    clear = np.array([0.02, 2.60])
    mu = two_sided_mu(delta, clear)
    assert mu > 0.9, f"mu={mu} would gate the barrier off next to a wall"
    assert gate_factor(mu, 1.0) > 0.9


def test_mu_uses_the_two_nearest_not_the_whole_list():
    """A third wall far away is not part of the gap being threaded."""
    delta = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 9.0]])
    clear = np.array([0.4, 0.4, 8.7])
    assert two_sided_mu(delta, clear) == pytest.approx(0.0)


def test_mu_is_bounded_on_random_configurations():
    rng = np.random.default_rng(0)
    delta = rng.normal(size=(200, 4, 2))
    clear = np.abs(rng.normal(size=(200, 4)))
    mu = two_sided_mu(delta, clear)
    assert mu.shape == (200,)
    assert np.all((mu >= 0.0) & (mu <= 1.0))


def test_mu_survives_interpenetration_without_dividing_by_zero():
    delta = np.array([[0.1, 0.0], [-0.1, 0.0]])
    clear = np.array([-0.2, -0.2])            # both surfaces breached
    mu = two_sided_mu(delta, clear)
    assert np.isfinite(mu) and 0.0 <= mu <= 1.0


# ------------------------------------------------------------ gate factor

def test_strength_zero_is_the_identity_factor():
    """The ablation invariant, at the scalar level."""
    mu = np.linspace(0.0, 1.0, 11)
    assert np.allclose(gate_factor(mu, 0.0), 1.0)


def test_full_strength_matches_the_paper_endpoints():
    assert gate_factor(0.0, 1.0) == pytest.approx(0.0)
    assert gate_factor(1.0, 1.0) == pytest.approx(1.0)


def test_factor_is_monotone_and_never_amplifies():
    mu = np.linspace(0.0, 1.0, 101)
    g = gate_factor(mu, 1.0)
    assert np.all(np.diff(g) >= -1e-12)
    assert np.all((g >= 0.0) & (g <= 1.0)), "a gate may only reduce repulsion"


# ------------------------------------------------------------- controller

def test_gap_gated_mppi_is_registered():
    assert "gap_gated_mppi" in REGISTRY


def test_strength_zero_is_byte_identical_to_stock():
    """Ablation invariant at the controller level: the gated branch is not
    taken at s = 0, so every run recorded before the gate existed still holds.
    """
    scen = load_scenario(CROSSING)
    a = make_controller("stock_mppi", scen, seed=3)
    b = make_controller("gap_gated_mppi", scen, seed=3, gap_gate_strength=0.0)
    state = np.array([0.0, -2.0, -1.5708, 0.3, 0.0])
    for t in (0.0, 0.5, 1.0):
        assert np.array_equal(a.command(state, t), b.command(state, t))


def test_gate_actually_changes_the_command_when_on():
    """Guard against shipping an inert knob (cf. the Q-017 inertness episode):
    the gate must be audible somewhere on its target scene."""
    scen = load_scenario(CROSSING)
    a = make_controller("stock_mppi", scen, seed=3)
    b = make_controller("gap_gated_mppi", scen, seed=3)
    state = np.array([0.0, -2.4, -1.5708, 0.3, 0.0])
    moved = any(not np.array_equal(a.command(state, t), b.command(state, t))
                for t in (0.0, 1.0, 2.0, 3.0, 4.0))
    assert moved, "gap_gate_strength=1.0 left every command bit-identical"


def test_gate_never_suppresses_the_hard_collision_term():
    """Caveat (3) of the borrow: the gate can zero the soft barrier, so safety
    inside the gap rests wholly on `w_collision`. Assert it is still charged
    at mu = 0 — an interpenetrating rollout must stay expensive.
    """
    scen = load_scenario(CROSSING)
    ctrl = make_controller("gap_gated_mppi", scen, seed=0)
    p = ctrl.p
    # One rollout, one step, parked exactly between two opposed obstacles and
    # inside both of them.
    obs = ctrl.obstacles[:2]
    assert len(obs) == 2
    traj = np.zeros((1, p.horizon, 5))
    mid = 0.5 * (obs[0].position(np.zeros(1))[0] + obs[1].position(np.zeros(1))[0])
    traj[..., :2] = mid
    cost = ctrl._cost(traj, 0.0)
    assert cost[0] >= p.w_collision, (
        f"cost {cost[0]} < w_collision {p.w_collision} — the gate leaked into "
        "the hard term")
