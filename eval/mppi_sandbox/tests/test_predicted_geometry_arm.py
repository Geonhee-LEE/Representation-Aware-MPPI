# SPDX-License-Identifier: BSD-3-Clause
"""`RiskMPPI(w_ped=...)` as a runnable arm — the closed-loop half of the port.

`test_predicted_geometry_critic.py` pins the cost term's geometry in isolation.
These two pin the properties that only exist once it is wired into a
controller, and they are the two that D-021 taught this branch to check *before*
spending a comparison on an arm:

- the zero-weight arm must be **bit-identical** to the arm without it, or every
  ablation denominated against it is measuring the wiring;
- the weighted arm must actually **move the trajectory** on a scene with
  pedestrians. `ShadowCostCritic` shipped and was later measured signal-free at
  the shipped horizon (D-021): byte-identical trajectories at `w_epist = 200`.
  Discovering that costs one run here and cost that critic several cycles.
"""

from __future__ import annotations

import numpy as np

from eval.mppi_sandbox.ab import simulate
from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.scenario import load_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"


def _run(w_ped: float, seed: int = 0) -> np.ndarray:
    scen = load_scenario(CROSSING)
    ctrl = make_controller("risk_mppi", scen, seed=seed, w_ped=w_ped)
    return simulate(scen, ctrl)


def test_zero_weight_reproduces_the_unweighted_arm_exactly():
    """The ablation invariant: w_ped = 0.0 is a no-op, not a small perturbation."""
    scen = load_scenario(CROSSING)
    without = simulate(scen, make_controller("risk_mppi", scen, seed=0))
    with_zero = _run(w_ped=0.0, seed=0)
    assert np.array_equal(without, with_zero)


def test_weighted_arm_is_not_inert_on_a_pedestrian_scene():
    """D-021's lesson applied before the arm is spent on a comparison.

    A cost term that never varies across rollouts cancels exactly in the
    softmax and executes a byte-identical trajectory at any weight. On a scene
    whose pedestrians cross the path, the anisotropic field must be audible.
    """
    baseline = _run(w_ped=0.0, seed=0)
    weighted = _run(w_ped=50.0, seed=0)
    assert not np.array_equal(baseline, weighted), (
        "w_ped = 50 executed a byte-identical trajectory — the term is inert "
        "on this scene, exactly as ShadowCostCritic was (D-021)"
    )
