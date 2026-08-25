# SPDX-License-Identifier: BSD-3-Clause
"""Q-187 timing reading: unit-level contracts, no integrations.

The expensive part (`measure_arm`, 16 integrations per arm) is exercised by
the cycle that took the reading and is not re-run here — these tests pin the
*scoring*, which is where a silent error would change the verdict without
changing the runtime.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import avoidance_timing as at


class _Ob:
    """Stationary circle; matches the `position(t)` protocol `ab` uses."""

    def __init__(self, x: float, y: float, radius: float) -> None:
        self._xy, self.radius = np.array([x, y], dtype=float), radius

    def position(self, t: np.ndarray) -> np.ndarray:
        return np.repeat(self._xy[None, :], np.asarray(t).size, axis=0)


def _traj(xs, ys, dt: float = 0.1) -> np.ndarray:
    """(T, 6) log with column 0 = time, 1:3 = xy — `ab`'s layout."""
    n = len(xs)
    out = np.zeros((n, 6))
    out[:, 0] = np.arange(n) * dt
    out[:, 1], out[:, 2] = xs, ys
    return out


STRAIGHT = np.array([[0.0, 0.0, 0.0], [0.0, -5.0, 0.0]])


def test_cross_track_is_zero_on_the_reference_and_grows_off_it():
    t = _traj([0.0, 0.5, 1.0], [-1.0, -1.0, -1.0])
    xte = at.cross_track_series(t, STRAIGHT)
    assert xte[0] == pytest.approx(0.0, abs=1e-9)
    assert xte[1] == pytest.approx(0.5)
    assert xte[2] == pytest.approx(1.0)


def test_cross_track_clamps_to_the_segment_rather_than_its_infinite_line():
    """A point past the polyline's end is scored to the endpoint.

    Without the clamp an overshooting run would read a *smaller* cross-track
    than it has, which on this scene would understate deviation exactly where
    the encounter ends.
    """
    t = _traj([0.0], [-7.0])
    assert at.cross_track_series(t, STRAIGHT)[0] == pytest.approx(2.0)


def test_closest_approach_index_finds_the_minimum_and_breaks_ties_early():
    assert at.closest_approach_index(np.array([3.0, 1.0, 2.0])) == 1
    assert at.closest_approach_index(np.array([1.0, 1.0, 2.0])) == 0


def test_first_deviation_index_is_none_when_the_path_was_held():
    xte = np.array([0.01, 0.02, 0.03])
    assert at.first_deviation_index(xte, 0.2) is None
    assert at.first_deviation_index(xte, 0.015) == 1


def test_clearance_series_matches_the_scalar_it_generalises():
    """The series' minimum must equal `obstacles.min_clearance` exactly.

    The series is a second derivation of the same quantity (module docstring
    says so); if the two ever disagree, the argmin indexes a curve nothing
    else in the repo believes in.
    """
    from eval.mppi_sandbox.obstacles import min_clearance

    t = _traj([0.0, 0.3, 0.6, 0.9], [-1.0, -1.5, -2.0, -2.5])
    obs = [_Ob(0.5, -2.0, 0.2), _Ob(-1.0, -1.0, 0.3)]
    series = at.clearance_series(t, obs, robot_radius=0.25)
    assert float(series.min()) == pytest.approx(min_clearance(t, obs, 0.25))


def test_no_obstacles_gives_an_infinite_series_not_an_empty_one():
    """Shape is load-bearing: `argmin` over an empty array raises."""
    series = at.clearance_series(_traj([0.0, 0.0], [0.0, -1.0]), [], 0.25)
    assert series.shape == (2,) and np.isinf(series).all()


def test_a_seed_that_never_deviates_is_flagged_not_silently_scored():
    """`lead_s` must be NaN, and `anticipatory` False — never 0.0.

    A 0.0 lead would be indistinguishable from a genuine simultaneous
    deviation, which is the misread the third bucket exists to prevent.
    """
    row = at.time_one_run(_traj([0.0] * 5, np.linspace(0, -2, 5)), STRAIGHT,
                          [_Ob(1.0, -1.0, 0.2)], 0.25, seed=3, threshold=0.5)
    assert row.deviated is False
    assert np.isnan(row.lead_s)
    assert row.anticipatory is False


def test_lead_time_sign_encodes_the_ordering():
    """Deviate at t=0.1, hazard passed at t=0.4 -> positive lead."""
    xs = [0.0, 0.9, 0.9, 0.9, 0.9]
    ys = [0.0, -0.4, -0.8, -1.2, -1.6]
    row = at.time_one_run(_traj(xs, ys), STRAIGHT, [_Ob(0.9, -1.2, 0.1)],
                          0.25, seed=0, threshold=0.5)
    assert row.deviated and row.lead_s > 0.0 and row.anticipatory


def test_sign_counts_partitions_every_row_exactly_once():
    rows = (
        at.SeedTiming(0, 0.2, True, 1.0, 3.0, 0.1),    # anticipatory
        at.SeedTiming(1, 0.2, True, -1.0, 3.0, 0.1),   # reactive
        at.SeedTiming(2, 0.2, True, 0.0, 3.0, 0.1),    # reactive (not strict >0)
        at.SeedTiming(3, 0.2, False, float("nan"), 3.0, 0.1),
    )
    counts = at.sign_counts(rows)
    assert counts == {"anticipatory": 1, "reactive": 2, "never_deviated": 1}
    assert sum(counts.values()) == len(rows)


@pytest.mark.parametrize("counts,head", [
    ({"anticipatory": 16, "reactive": 0, "never_deviated": 0}, "ANTICIPATORY"),
    ({"anticipatory": 0, "reactive": 16, "never_deviated": 0}, "REACTIVE"),
    ({"anticipatory": 8, "reactive": 8, "never_deviated": 0}, "MIXED"),
    ({"anticipatory": 0, "reactive": 0, "never_deviated": 16}, "NO_DEVIATION"),
])
def test_verdict_refuses_to_round_a_split_toward_either_branch(counts, head):
    assert at.verdict(counts).startswith(head)


def test_measure_arm_refuses_a_truncated_run():
    """D-443's precondition, re-pinned here because this module re-states it.

    A stalled seed has no meaningful closest-approach index — the encounter it
    would index may never have occurred — so the reading must not be defined
    over it.
    """
    class _Stub:
        seed, reached_goal = 7, False

    import eval.mppi_sandbox.ab as ab_mod

    real = ab_mod.seed_sweep
    ab_mod.seed_sweep = lambda *a, **k: [_Stub()]
    try:
        with pytest.raises(RuntimeError, match="did not reach goal"):
            at.measure_arm(object(), 0.0, seeds=(7,))
    finally:
        ab_mod.seed_sweep = real
