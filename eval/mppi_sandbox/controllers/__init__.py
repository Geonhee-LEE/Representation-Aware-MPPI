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
from .risk_mppi import RiskMPPI
from .stock_mppi import StockMPPI
from .visibility_gated_mppi import VisibilityGatedMPPI

REGISTRY = {
    "stock_mppi": StockMPPI,
    "risk_mppi": RiskMPPI,
    "cbf_mppi": CBFMPPI,
    "vg_mppi": VisibilityGatedMPPI,
}


def make_controller(name: str, scenario, seed: int = 0, **overrides):
    try:
        cls = REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"unknown controller '{name}' — available: {sorted(REGISTRY)}"
        ) from None
    return cls(scenario, seed=seed, **overrides)
