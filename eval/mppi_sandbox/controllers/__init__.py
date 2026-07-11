# SPDX-License-Identifier: BSD-3-Clause
"""Controller plug-in registry.

A controller is any object with:

    command(state: (5,) ndarray, t: float) -> (2,) ndarray  [v_cmd, omega_cmd]

constructed via make_controller(name, scenario, seed=..., **overrides).
Adding a controller = one module + one REGISTRY line + pytest passing the
scenario contract in tests/ — that is the whole integration surface.
"""

from __future__ import annotations

from .stock_mppi import StockMPPI

REGISTRY = {
    "stock_mppi": StockMPPI,
}


def make_controller(name: str, scenario, seed: int = 0, **overrides):
    try:
        cls = REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"unknown controller '{name}' — available: {sorted(REGISTRY)}"
        ) from None
    return cls(scenario, seed=seed, **overrides)
