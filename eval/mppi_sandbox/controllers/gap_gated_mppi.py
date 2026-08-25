# SPDX-License-Identifier: BSD-3-Clause
"""StockMPPI with the two-sided-gap barrier gate switched on.

Exists as a registry name so the gate can be swept by the existing harnesses
(`ab.seed_sweep`, `baseline_matrix`, `near_miss.score_runs`) without teaching
any of them a new keyword. The mechanism lives in `..gap_gate`; the cost-term
wiring lives in `StockMPPI._cost` behind `gap_gate_strength`. This module is
the *arm*, not the mechanism.

Target of record: `cafe_obstacle_crossing_v0`, whose required corridor D-121
measured at **0.00 m** — the robot can hold the declared 0.30 m margin without
ever leaving the reference path, so its 8/8 unsafe rate (D-120) is controller
debt with no geometric excuse. That is the scene where a barrier peaking inside
the gap is the suspected mechanism, and D-123 fixed the yardstick: judge it
against `stock_mppi` **at the same temperature** (λ = 0.8), never against the
other arm, whose published delta on this scene inverts at a matched rung.
"""

from __future__ import annotations

from .stock_mppi import StockMPPI


class GapGatedMPPI(StockMPPI):
    """`StockMPPI` with `gap_gate_strength = 1.0` (the paper's full gate)."""

    def __init__(self, scenario, seed: int = 0, *,
                 gap_gate_strength: float = 1.0, **kwargs):
        super().__init__(scenario, seed=seed,
                         gap_gate_strength=gap_gate_strength, **kwargs)
