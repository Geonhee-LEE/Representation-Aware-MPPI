# SPDX-License-Identifier: BSD-3-Clause
"""Controller plug-in registry.

A controller is any object with:

    command(state: (5,) ndarray, t: float) -> (2,) ndarray  [v_cmd, omega_cmd]

constructed via make_controller(name, scenario, seed=..., **overrides).
Adding a controller = one module + one REGISTRY line + pytest passing the
scenario contract in tests/ — that is the whole integration surface.
"""

from __future__ import annotations

from .cbf_mppi import CBFMPPI
from .frozen_risk_mppi import FrozenRiskMPPI
from .gap_gated_mppi import GapGatedMPPI
from .geometric_mppi import GeometricMPPI
from .risk_mppi import RiskMPPI
from .social_mppi import SocialMPPI
from .stock_mppi import StockMPPI

REGISTRY = {
    "stock_mppi": StockMPPI,
    "risk_mppi": RiskMPPI,
    "cbf_mppi": CBFMPPI,
    "gap_gated_mppi": GapGatedMPPI,
    "geometric_mppi": GeometricMPPI,
    "frozen_risk_mppi": FrozenRiskMPPI,
    "social_mppi": SocialMPPI,
}


def make_controller(name: str, scenario, seed: int = 0, **overrides):
    try:
        cls = REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"unknown controller '{name}' — available: {sorted(REGISTRY)}"
        ) from None
    return cls(scenario, seed=seed, **overrides)
