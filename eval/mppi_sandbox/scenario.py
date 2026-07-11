# SPDX-License-Identifier: BSD-3-Clause
"""Loader for eval/scenarios/*.yaml into sandbox-ready structures.

Only the physics-relevant keys are consumed (start / goal / reference_path /
target_speed_mps / expected_duration_s / dynamic_obstacles / acceptance).
Gazebo-only keys (launch:, world:) are ignored — the same yaml drives both
backends, which is the point (D-016).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from .obstacles import CircleObstacle


@dataclass
class Scenario:
    name: str
    start: np.ndarray          # (3,) x, y, yaw
    goal: np.ndarray           # (3,) x, y, yaw
    waypoints: np.ndarray      # (M, 3) x, y, yaw_target
    target_speed: float
    expected_duration: float
    obstacles: list[CircleObstacle] = field(default_factory=list)
    acceptance: dict = field(default_factory=dict)


def load_scenario(path: str | Path) -> Scenario:
    raw = yaml.safe_load(Path(path).read_text())
    start = raw["start"]
    goal = raw["goal"]
    return Scenario(
        name=raw.get("name", Path(path).stem),
        start=np.array([start["x"], start["y"], start["yaw"]], dtype=float),
        goal=np.array([goal["x"], goal["y"], goal["yaw"]], dtype=float),
        waypoints=np.array(raw["reference_path"]["waypoints"], dtype=float),
        target_speed=float(raw.get("target_speed_mps", 0.5)),
        expected_duration=float(raw.get("expected_duration_s", 30.0)),
        obstacles=[CircleObstacle.from_yaml(e)
                   for e in raw.get("dynamic_obstacles", [])],
        acceptance=raw.get("acceptance", {}) or {},
    )
