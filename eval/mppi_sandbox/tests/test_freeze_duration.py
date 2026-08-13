# SPDX-License-Identifier: BSD-3-Clause
"""`freeze_duration` — the scene's own acceptance key, now computed.

The regression these pin is not arithmetic. `cafe_freezing_v0` declared
`freeze_duration_max: 2.0` and ranked it **second** in
`success_metric_priority`, and `check_acceptance` mapped the unknown key to the
string `"skipped"`, which `run_scenario`'s `isinstance(v, bool)` filter drops
from `pass`. The freezing scene was not testing for freezing.
`test_freezing_scene_actually_asks_about_freezing` is the one that would have
caught it, and it is written to fail if the key is ever dropped again.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.freeze_price import (
    FREEZING_SCENE,
    STALL_SPEED_MPS,
    freeze_duration,
    stalled_mask,
)
from eval.mppi_sandbox.run import check_acceptance
from eval.mppi_sandbox.scenario import load_scenario

DT = 0.1
STRAIGHT = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]])


def _traj(speeds: list[float], *, dt: float = DT) -> np.ndarray:
    """(T,6) trajectory advancing along +x at the given per-step speeds."""
    t = np.arange(len(speeds) + 1) * dt
    x = np.concatenate([[0.0], np.cumsum(np.array(speeds) * dt)])
    rows = np.zeros((len(t), 6))
    rows[:, 0] = t
    rows[:, 1] = x
    rows[:, 4] = np.concatenate([[0.0], speeds])
    return rows


def test_steady_motion_never_stalls():
    """A run that always beats the creep floor has no freeze at all."""
    assert freeze_duration(_traj([0.5] * 40), STRAIGHT) == 0.0


def test_longest_contiguous_stall_is_the_reading():
    """Two stalls → the *longest* is reported, not the total and not the first."""
    speeds = [0.5] * 5 + [0.0] * 8 + [0.5] * 5 + [0.0] * 20 + [0.5] * 5
    got = freeze_duration(_traj(speeds), STRAIGHT)
    assert got == pytest.approx(20 * DT, abs=1e-9)


def test_progress_is_along_path_not_ground_speed():
    """Motion perpendicular to the path is a stall, however fast it is.

    The yaml says "stopped *without progress*". A robot swerving sideways
    around a pedestrian has ground speed and no progress, and pricing that as
    motion is exactly how a freeze metric gets talked out of firing.
    """
    rows = np.zeros((31, 6))
    rows[:, 0] = np.arange(31) * DT
    rows[:, 2] = np.arange(31) * 0.5 * DT          # +y only; path runs along +x
    rows[:, 4] = 0.5                                # ground speed is healthy
    assert freeze_duration(rows, STRAIGHT) == pytest.approx(30 * DT, abs=1e-9)


def test_stall_threshold_is_the_shipped_creep_floor():
    """The threshold is borrowed, not invented — keep the two tied.

    `STALL_SPEED_MPS` means "slower than the controller's own definition of
    still-making-progress". If someone retunes `creep_speed`, this fails and
    forces the decision to be made once rather than drifting.
    """
    assert STALL_SPEED_MPS == MPPIParams().creep_speed


def test_threshold_is_a_strict_floor():
    """Just under the floor stalls; just over it does not."""
    assert stalled_mask(_traj([STALL_SPEED_MPS * 0.9] * 10), STRAIGHT).all()
    assert not stalled_mask(_traj([STALL_SPEED_MPS * 1.1] * 10), STRAIGHT).any()


def test_degenerate_trajectories_do_not_raise():
    """No step taken ⇒ no step stalled. Empty is not a freeze."""
    assert freeze_duration(np.zeros((1, 6)), STRAIGHT) == 0.0
    assert stalled_mask(np.zeros((0, 6)), STRAIGHT).size == 0


def test_freezing_scene_actually_asks_about_freezing():
    """The scene's second-priority criterion must reach `pass`, not "skipped".

    This is the defect's own test. Before this cycle the assertion below read
    `"skipped"` — a string, which `run_scenario` filters out of `pass` — so
    `cafe_freezing_v0` could stall indefinitely and still be green.
    """
    acc = load_scenario(FREEZING_SCENE).acceptance
    assert acc["freeze_duration_max"] == 2.0, "scene stopped declaring the key"

    # Wide enough for *every* rule the scene declares, not just this one: the
    # scene also declares `time_to_goal_max`, and each rule indexes its metric
    # directly (a missing metric is a loud KeyError, deliberately — see D-247).
    checks = check_acceptance(acc, {"freeze_duration": 5.0, "cte_rms": 0.0,
                                    "cte_max": 0.0, "heading_err_rms": 0.0,
                                    "completion_final": 1.0, "goal_reached": 1,
                                    "time_to_goal": 7.4},
                              clearance=1.0)
    assert checks["freeze_duration_max"] is False, "a 5 s stall must fail a 2 s limit"
    assert isinstance(checks["freeze_duration_max"], bool), \
        "a str verdict is dropped from `pass` — the original defect"

    checks_ok = check_acceptance(acc, {"freeze_duration": 0.4, "cte_rms": 0.0,
                                       "cte_max": 0.0, "heading_err_rms": 0.0,
                                       "completion_final": 1.0,
                                       "goal_reached": 1,
                                       "time_to_goal": 7.4},
                                 clearance=1.0)
    assert checks_ok["freeze_duration_max"] is True


# --- the arrival-scoped truncation (D-250) ----------------------------------

def test_freeze_duration_before_truncates_at_arrival():
    """Same function, different rows — the property the split rests on."""
    import numpy as np

    from eval.mppi_sandbox.freeze_price import (freeze_duration,
                                                freeze_duration_before)

    # Drives 0..2 s at 1 m/s along x, then sits still from 2 s to 12 s.
    t_drive = np.arange(0.0, 2.0, 0.1)
    t_park = np.arange(2.0, 12.0, 0.1)
    path = np.array([[0.0, 0.0], [2.0, 0.0]])
    rows = [[t, t * 1.0, 0.0, 0.0, 1.0, 0.0] for t in t_drive]
    rows += [[t, 2.0, 0.0, 0.0, 0.0, 0.0] for t in t_park]
    traj = np.array(rows, dtype=float)

    whole = freeze_duration(traj, path)
    assert whole > 9.0, "the parked tail is the whole-trajectory reading"

    before = freeze_duration_before(traj, path, arrival=2.0)
    assert before < 0.5, "nothing stalled while it was still driving"

    # No arrival ⇒ the two coincide by construction.
    assert freeze_duration_before(traj, path, arrival=None) == whole
