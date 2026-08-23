# SPDX-License-Identifier: BSD-3-Clause
"""Q-188 aim reading: unit-level contracts, no integrations.

Same split as `test_avoidance_timing.py` — the 16-integration `measure_arm` is
exercised by the cycle that takes the reading; these tests pin the *scoring*,
where a silent error would move the verdict without moving the runtime.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import avoidance_aim as aa
from eval.mppi_sandbox import avoidance_timing as at


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


#: Reference path runs down the -y axis through the origin.
STRAIGHT = np.array([[0.0, 0.0, 0.0], [0.0, -5.0, 0.0]])


def _row(**kw) -> aa.SeedAim:
    base = dict(seed=0, index=0, t_s=0.0, clearance=0.0,
                on_path_clearance=0.0, deviation=0.0, peak_deviation=0.0)
    base.update(kw)
    return aa.SeedAim(**base)


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

def test_foot_points_agree_with_cross_track_series():
    """The two projections must not drift apart.

    `foot_points` re-derives what `cross_track_series` already computes and
    throws away. If either is edited alone the budget in `score_one_run` stops
    being a budget — `deviation` and `on_path_clearance` would be measured
    against different reference points.
    """
    t = _traj([0.4, -1.5, 0.0, 3.0], [-1.0, -2.0, -3.0, -9.0])
    foot = aa.foot_points(t, STRAIGHT)
    direct = np.linalg.norm(t[:, 1:3] - foot, axis=1)
    assert direct == pytest.approx(at.cross_track_series(t, STRAIGHT))


def test_foot_points_clamp_to_the_segment_like_the_distance_does():
    t = _traj([0.0], [-7.0])
    assert aa.foot_points(t, STRAIGHT)[0] == pytest.approx([0.0, -5.0])


def test_on_path_clearance_reads_the_hazard_where_it_actually_was():
    """The counterfactual moves the robot, never the obstacle.

    Robot at (1.5, -2) with the actor at (0, -2): the foot is (0, -2), i.e.
    the actor's own centre, so standing on the path would have meant a
    surface-to-surface clearance of -(r_ob + r_robot).
    """
    t = _traj([1.5], [-2.0])
    got = aa.on_path_clearance_at(t, STRAIGHT, [_Ob(0.0, -2.0, 0.3)], 0.2, 0)
    assert got == pytest.approx(-0.5)


def test_no_obstacles_gives_infinite_on_path_clearance():
    assert aa.on_path_clearance_at(_traj([0.0], [0.0]), STRAIGHT, [], 0.2, 0) \
        == float("inf")


# --------------------------------------------------------------------------
# the budget
# --------------------------------------------------------------------------

def test_score_one_run_reads_both_lengths_at_the_same_index():
    """`deviation` is taken at closest approach, not at the peak.

    The run swerves 1.0 m early and is back to 0.2 m off the path when it
    passes the actor. Reading the peak would credit the run with five times
    the excursion it actually had in hand at the moment that decided the
    clearance — the D-444 finding (the response is *early*) is exactly what
    makes those two numbers different.
    """
    t = _traj([1.0, 1.0, 0.2, 0.0], [-0.5, -1.0, -2.0, -3.0])
    row = aa.score_one_run(t, STRAIGHT, [_Ob(0.0, -2.0, 0.3)], 0.2, seed=7)
    assert row.index == 2
    assert row.deviation == pytest.approx(0.2)
    assert row.peak_deviation == pytest.approx(1.0)
    assert row.on_path_clearance == pytest.approx(-0.5)
    assert row.clearance == pytest.approx(-0.3)
    assert row.gain == pytest.approx(0.2)


def test_gain_never_exceeds_deviation():
    """The inequality the whole discriminator rests on.

    Moving `d` metres can increase a distance by at most `d`, so a run can
    never buy more clearance than it deviated. If this failed, `MAGNITUDE`
    would stop being a statement about what *any* aim could have done.
    """
    rng = np.random.default_rng(188)
    ob = _Ob(0.0, -2.0, 0.3)
    for _ in range(200):
        xs = rng.uniform(-2.0, 2.0, size=4)
        ys = np.linspace(-0.5, -3.5, 4)
        row = aa.score_one_run(_traj(xs, ys), STRAIGHT, [ob], 0.2, seed=0)
        assert row.gain <= row.deviation + 1e-9


def test_aim_efficiency_is_one_when_the_swerve_points_straight_away():
    t = _traj([0.0, 0.8], [-2.0, -2.0])
    row = aa.score_one_run(t[1:], STRAIGHT, [_Ob(0.0, -2.0, 0.3)], 0.2, seed=0)
    assert row.aim_efficiency == pytest.approx(1.0)


def test_aim_efficiency_is_nan_on_the_path_rather_than_dividing_by_zero():
    assert np.isnan(_row(deviation=0.0).aim_efficiency)


# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------

def test_a_seed_that_owed_nothing_is_its_own_bucket():
    """`SUFFICIENT` is reported, never dropped.

    Discarding the seeds the path already kept safe would bias the sample
    toward the hard ones and re-run the D-358 vacuity error inverted.
    """
    assert aa.classify(_row(on_path_clearance=0.5), 0.30) == "SUFFICIENT"


def test_too_small_to_have_cleared_at_any_aim_reads_magnitude():
    row = _row(on_path_clearance=0.0, deviation=0.05, clearance=0.05)
    assert aa.classify(row, 0.30) == "MAGNITUDE"


def test_big_enough_and_misdirected_reads_aim():
    row = _row(on_path_clearance=0.0, deviation=0.60, clearance=0.02)
    assert aa.classify(row, 0.30) == "AIM"


def test_big_enough_and_delivered_reads_cleared():
    row = _row(on_path_clearance=0.0, deviation=0.60, clearance=0.35)
    assert aa.classify(row, 0.30) == "CLEARED"


def test_the_boundary_deviation_equals_required_is_not_magnitude():
    """At `deviation == required` a perfect aim would exactly have cleared, so
    the failure is attributable to direction. The comparison is strict."""
    row = _row(on_path_clearance=0.0, deviation=0.30, clearance=0.10)
    assert aa.classify(row, 0.30) == "AIM"


def test_counts_reports_all_four_buckets_even_when_empty():
    assert set(aa.counts((), 0.30)) == {
        "SUFFICIENT", "MAGNITUDE", "AIM", "CLEARED"}
    assert sum(aa.counts((), 0.30).values()) == 0


# --------------------------------------------------------------------------
# verdict
# --------------------------------------------------------------------------

@pytest.mark.parametrize("bucket,head", [
    ({"SUFFICIENT": 16, "MAGNITUDE": 0, "AIM": 0, "CLEARED": 0}, "NO_DEFICIT"),
    ({"SUFFICIENT": 0, "MAGNITUDE": 12, "AIM": 4, "CLEARED": 0}, "MAGNITUDE"),
    ({"SUFFICIENT": 0, "MAGNITUDE": 4, "AIM": 12, "CLEARED": 0}, "AIM"),
    ({"SUFFICIENT": 0, "MAGNITUDE": 8, "AIM": 8, "CLEARED": 0}, "MIXED"),
])
def test_verdict_needs_a_two_to_one_majority(bucket, head):
    assert aa.verdict(bucket).split(":")[0] == head


def test_cleared_seeds_do_not_vote_in_the_verdict():
    """Only seeds that were owed something *and* missed it discriminate.

    A scene that cleared 15/16 and missed one on magnitude still reads
    `MAGNITUDE` — the verdict answers "when it fails, why", not "how often".
    """
    bucket = {"SUFFICIENT": 0, "MAGNITUDE": 1, "AIM": 0, "CLEARED": 15}
    assert aa.verdict(bucket).startswith("MAGNITUDE")


def test_verdicts_over_targets_covers_the_whole_ladder():
    rows = (_row(on_path_clearance=0.0, deviation=0.05, clearance=0.05),)
    got = aa.verdicts_over_targets(rows)
    assert set(got) == set(aa.TARGETS)
    # 0.10 target: required 0.10 > deviation 0.05 -> MAGNITUDE, and it only
    # gets more so as the target rises. The ladder is monotone here by
    # construction, which is what makes a *non*-monotone real reading news.
    assert all(v.startswith("MAGNITUDE") for v in got.values())


def test_the_scene_and_arms_are_the_ones_d444_read():
    """Q-188 is answered over D-444's runs, not a fresh sample."""
    assert aa.SCENE is at.SCENE
    assert aa.ARMS == at.ARMS == (0.0, 32.0)
    assert aa.SEEDS == at.SEEDS == tuple(range(16))
