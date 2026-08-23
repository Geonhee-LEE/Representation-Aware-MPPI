# SPDX-License-Identifier: BSD-3-Clause
"""Q-189 budget partition: unit-level contracts, no integrations.

Same split as `test_avoidance_aim.py` — the 16-integration `measure_arm` is
exercised by the cycle that takes the reading; these tests pin the *scoring*,
where a silent error would move the verdict without moving the runtime.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import avoidance_budget as ab_
from eval.mppi_sandbox import avoidance_aim as aa


class _Ob:
    """Stationary circle; matches the `position(t)` protocol `ab` uses."""

    def __init__(self, x: float, y: float, radius: float) -> None:
        self._xy, self.radius = np.array([x, y], dtype=float), radius

    def position(self, t: np.ndarray) -> np.ndarray:
        return np.repeat(self._xy[None, :], np.asarray(t).size, axis=0)


def _traj(xs, ys, dt: float = 0.1) -> np.ndarray:
    n = len(xs)
    out = np.zeros((n, 6))
    out[:, 0] = np.arange(n) * dt
    out[:, 1], out[:, 2] = xs, ys
    return out


#: Reference path runs along +x through the origin.
STRAIGHT = np.array([[0.0, 0.0, 0.0], [5.0, 0.0, 0.0]])


def _row(**kw) -> ab_.SeedBudget:
    base = dict(seed=0, index=0, t_s=0.0, deviation=1.0, away=1.0, slide=0.0,
                bearing_tangent_frac=0.0, tangent_frac=0.0, gain=1.0)
    base.update(kw)
    return ab_.SeedBudget(**base)


# --------------------------------------------------------------------------
# The partition identity
# --------------------------------------------------------------------------

def test_away_and_slide_partition_the_deviation_exactly():
    """`away**2 + slide**2 == deviation**2` — the excursion is fully accounted.

    This is the claim the module makes about where the metres went, so it is
    pinned as an identity rather than spot-checked on one geometry.
    """
    # Hazard off to the side at (2, 1); robot displaced from its foot at (2, 0).
    traj = _traj([2.0], [0.4])
    row = ab_.score_one_run(traj, STRAIGHT, [_Ob(2.0, 1.0, 0.2)], 0.1, seed=0)
    assert row.away ** 2 + row.slide ** 2 == pytest.approx(row.deviation ** 2)
    assert row.slide >= 0.0


def test_hazard_dead_ahead_puts_the_whole_excursion_into_slide():
    """Bearing along the tangent -> a path-normal excursion buys nothing.

    This is Q-189's TIMING branch in its purest form: the hazard sits on the
    path ahead, the robot's only available displacement is path-normal, and it
    is therefore orthogonal to the bearing. `away` ~ 0 at *any* deviation.
    """
    haz = _Ob(4.0, 0.0, 0.2)
    small = ab_.score_one_run(_traj([2.0], [0.1]), STRAIGHT, [haz], 0.1, seed=0)
    large = ab_.score_one_run(_traj([2.0], [0.8]), STRAIGHT, [haz], 0.1, seed=1)
    # Bearing from foot (2,0) to hazard (4,0) is exactly the path tangent.
    assert small.bearing_tangent_frac == pytest.approx(1.0)
    assert large.bearing_tangent_frac == pytest.approx(1.0)
    # 8x the excursion, and both land essentially entirely in slide.
    assert large.deviation == pytest.approx(8 * small.deviation)
    assert abs(small.away) < 1e-9 and abs(large.away) < 1e-9
    assert large.slide == pytest.approx(large.deviation)
    # The gain that survives is purely second-order: sliding `d` across a
    # bearing of length R buys sqrt(R**2 + d**2) - R, not d. That is D-445's
    # saturation reproduced from geometry alone, with no controller in the
    # loop — and it is why 8x the excursion does not buy 8x the clearance.
    R = 2.0
    assert large.gain == pytest.approx(np.hypot(R, large.deviation) - R)
    assert small.gain == pytest.approx(np.hypot(R, small.deviation) - R)
    # 8x the deviation buys 55x less than 8x the gain would have been.
    assert large.gain / small.gain > 8.0        # quadratic, so it does grow...
    assert large.gain < 0.25 * large.deviation  # ...but stays a fifth of the spend


def test_hazard_abeam_converts_the_excursion_into_clearance():
    """Bearing along the normal -> the excursion is spent on `away`.

    The contrast case to the test above: same displacement, hazard moved from
    'ahead' to 'abeam', and now the identical excursion buys clearance. This is
    what makes `bearing_tangent_frac` a discriminator rather than a constant.
    """
    # Hazard abeam at (2, 2); robot swerves to (2, -0.5), i.e. directly away.
    row = ab_.score_one_run(_traj([2.0], [-0.5]), STRAIGHT, [_Ob(2.0, 2.0, 0.2)],
                            0.1, seed=0)
    assert row.bearing_tangent_frac == pytest.approx(0.0, abs=1e-9)
    assert row.away == pytest.approx(row.deviation)
    assert row.slide == pytest.approx(0.0, abs=1e-9)
    assert row.gain == pytest.approx(row.deviation, rel=1e-9)


def test_away_is_signed_when_the_excursion_closes_on_the_hazard():
    """Swerving *toward* the hazard is a negative `away`, not a positive one.

    An unsigned projection would report a wrong-way excursion as if it had
    bought clearance, which is exactly the error `aim_efficiency`'s sign
    convention exists to avoid (D-445).
    """
    row = ab_.score_one_run(_traj([2.0], [0.5]), STRAIGHT, [_Ob(2.0, 2.0, 0.2)],
                            0.1, seed=0)
    assert row.away < 0.0
    assert row.gain < 0.0


def test_tangent_frac_of_the_deviation_is_degenerate():
    """The literal Q-189 framing is vacuous — pinned, so nobody re-derives it.

    `foot_points` returns the *nearest* point on the polyline, so the deviation
    vector is orthogonal to its segment by construction. The module says so in
    prose; this is the measurement behind the prose.
    """
    for y in (0.05, 0.3, 0.9):
        row = ab_.score_one_run(_traj([2.0], [y]), STRAIGHT, [_Ob(2.0, 2.0, 0.2)],
                                0.1, seed=0)
        assert row.tangent_frac == pytest.approx(0.0, abs=1e-9)


def test_gain_matches_the_linearisation_when_the_hazard_is_far():
    """`gain ~ -d . u` is the identity the module's reasoning rests on.

    It is exact only in the limit of a far hazard, so the test states the
    regime rather than asserting the approximation everywhere.
    """
    row = ab_.score_one_run(_traj([2.0], [-0.2]), STRAIGHT, [_Ob(2.0, 50.0, 0.2)],
                            0.1, seed=0)
    assert row.gain == pytest.approx(row.away, rel=1e-3)


# --------------------------------------------------------------------------
# Index and hazard selection agree with the reading this one extends
# --------------------------------------------------------------------------

def test_index_agrees_with_the_aim_reading():
    """Both readings must describe the same instant or they are incomparable.

    D-445's numbers and this partition are quoted side by side in the journal,
    so a drift in the closest-approach index would silently make the comparison
    a statement about two different moments.
    """
    xs = np.linspace(0.0, 4.0, 41)
    ys = np.full_like(xs, 0.3)
    traj, obs = _traj(xs, ys), [_Ob(2.0, 1.0, 0.2)]
    mine = ab_.score_one_run(traj, STRAIGHT, obs, 0.1, seed=0)
    theirs = aa.score_one_run(traj, STRAIGHT, obs, 0.1, seed=0)
    assert mine.index == theirs.index
    assert mine.deviation == pytest.approx(theirs.deviation)


def test_gain_agrees_with_the_aim_reading():
    """`gain` is recomputed here from centres; `avoidance_aim` builds it from
    surface clearances. Radii cancel, so the two must agree — and if they ever
    stop agreeing, one of the two hazard selections has drifted."""
    xs = np.linspace(0.0, 4.0, 41)
    traj = _traj(xs, np.full_like(xs, 0.3))
    obs = [_Ob(2.0, 1.2, 0.25)]
    mine = ab_.score_one_run(traj, STRAIGHT, obs, 0.15, seed=0)
    theirs = aa.score_one_run(traj, STRAIGHT, obs, 0.15, seed=0)
    assert mine.gain == pytest.approx(theirs.gain)


def test_no_hazard_is_an_error_not_an_infinity():
    """`avoidance_aim` returns inf for a hazard-free run because a clearance is
    still defined there. A *partition of the bearing* is not, so this refuses
    rather than inventing a direction."""
    with pytest.raises(ValueError):
        ab_.score_one_run(_traj([1.0], [0.1]), STRAIGHT, [], 0.1, seed=0)


# --------------------------------------------------------------------------
# Verdict layer
# --------------------------------------------------------------------------

def test_lever_reads_timing_when_bearings_are_tangential():
    rows = tuple(_row(seed=i, bearing_tangent_frac=0.95) for i in range(6))
    assert ab_.lever(rows, 0.707).startswith("TIMING")


def test_lever_reads_prediction_when_bearings_are_normal():
    rows = tuple(_row(seed=i, bearing_tangent_frac=0.1) for i in range(6))
    assert ab_.lever(rows, 0.707).startswith("PREDICTION")


def test_lever_reads_mixed_without_a_majority():
    rows = tuple(_row(seed=i, bearing_tangent_frac=(0.95 if i % 2 else 0.1))
                 for i in range(6))
    assert ab_.lever(rows, 0.707).startswith("MIXED")


def test_seeds_that_never_left_the_path_do_not_vote():
    """A controller that never swerved has no excursion to partition.

    Letting `deviation == 0` rows vote would let them carry whatever
    `bearing_tangent_frac` their geometry happened to have into a claim about
    where a swerve went.
    """
    rows = tuple(_row(seed=i, deviation=0.0, bearing_tangent_frac=0.95)
                 for i in range(6))
    assert ab_.lever(rows, 0.707).startswith("NO_EXCURSION")


def test_lever_over_bands_reports_every_rung():
    rows = tuple(_row(seed=i, bearing_tangent_frac=0.8) for i in range(6))
    got = ab_.lever_over_bands(rows)
    assert set(got) == set(ab_.BANDS)
    # 0.8 sits above two rungs and below the third: the call is *expected* to
    # move, and seeing it move is the point of sweeping.
    assert got[0.50].startswith("TIMING") and got[0.85].startswith("PREDICTION")


def test_shares_on_empty_input_is_nan_not_an_exception():
    got = ab_.shares(())
    assert set(got) >= {"deviation", "away", "slide", "gain"}
    assert all(np.isnan(v) for v in got.values())


def test_shares_averages_the_population():
    rows = (_row(seed=0, away=1.0, slide=0.0), _row(seed=1, away=0.0, slide=1.0))
    got = ab_.shares(rows)
    assert got["away"] == pytest.approx(0.5)
    assert got["slide"] == pytest.approx(0.5)
