# SPDX-License-Identifier: BSD-3-Clause
"""`social_mppi` — the 2x2's winning cell as a registry name.

The controller introduces no cost term, so there is nothing here about
geometry: `test_predicted_geometry_critic.py` owns the field's shape and
`test_predicted_geometry_arm.py` owns its closed-loop audibility. What this
module pins is the only thing naming a cell can get wrong — **that the name and
the cell stay the same thing**:

- the arm must be byte-identical to the overrides it replaces, so the readings
  D-218/D-219/D-234/D-235 took on `(w_risk, w_ped) = (40, 50)` transfer to the
  name without being re-taken;
- its defaults must equal `three_arm`'s measured cell, read out of that module
  at run time rather than respelled here (D-237: prose that restates a
  population's members is a reader of it, and drifts from it silently);
- `three_arm.ARMS` must stay isolated at `w_risk = 0.0`, because mixing this
  arm's denomination into that dict is exactly the D-217/D-218 error.
"""

from __future__ import annotations

import numpy as np

from eval.mppi_sandbox import three_arm
from eval.mppi_sandbox.ab import simulate
from eval.mppi_sandbox.controllers import REGISTRY, make_controller
from eval.mppi_sandbox.controllers.social_mppi import SocialMPPI
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.scenario import load_scenario

CROSSING = three_arm.INTERACTION_SCENE
LAM = three_arm.LAM

#: The cell this arm is a name for, read from the module that measured it.
W_RISK = three_arm.W_RISK_ROWS[0]
W_PED = three_arm.W_PED_COLS[1]


def test_registry_exposes_the_arm():
    """A name the sweep harnesses can reach — the whole point of the module."""
    assert REGISTRY["social_mppi"] is SocialMPPI
    scen = load_scenario(CROSSING)
    assert isinstance(
        make_controller("social_mppi", scen, params=MPPIParams(lam=LAM)),
        SocialMPPI)


def test_defaults_are_the_measured_cell():
    """Defaults equal `three_arm`'s 2x2 cell, so the name cannot drift off it."""
    ctrl = make_controller("social_mppi", load_scenario(CROSSING),
                           params=MPPIParams(lam=LAM))
    assert (ctrl.w_risk, ctrl.predicted.w_ped) == (W_RISK, W_PED)


def test_arm_is_byte_identical_to_the_overrides_it_replaces():
    """Naming the cell must not become re-tuning it.

    If this ever fails, every number D-218/D-219/D-234/D-235 recorded on
    `(w_risk, w_ped) = (40, 50)` has stopped describing `social_mppi`, and the
    arm would be carrying borrowed evidence.
    """
    scen = load_scenario(CROSSING)
    params = MPPIParams(lam=LAM)
    named = simulate(scen, make_controller("social_mppi", scen, seed=0,
                                           params=params))
    overrides = simulate(scen, make_controller("risk_mppi", scen, seed=0,
                                               w_risk=W_RISK, w_ped=W_PED,
                                               params=params))
    assert np.array_equal(named, overrides)


def test_three_arm_stays_isolated_at_zero_risk():
    """`ARMS` answers "what does each knob buy *alone*" — in both directions.

    Asserted as one dict equality rather than a per-arm loop: the claim is
    about the whole population, and stating it that way leaves no iteration
    count that could be vacuous at zero arms.
    """
    got = {name: kwargs.get("w_risk", 0.0)
           for name, (_, kwargs) in three_arm.ARMS.items()}
    assert got == {name: 0.0 for name in three_arm.ARMS}


def test_the_paired_arm_is_deliberately_absent_from_arms():
    """Its `w_risk = 40` would mix the two denominations D-218 separated."""
    assert "social_mppi" not in {ctrl for ctrl, _ in three_arm.ARMS.values()}
