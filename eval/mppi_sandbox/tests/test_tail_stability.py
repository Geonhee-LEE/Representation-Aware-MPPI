# SPDX-License-Identifier: BSD-3-Clause
"""The feed's cheap exit from STATE's fork, tested where it was supposed to bite."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import tail_stability as ts


def test_census_covers_both_binding_scenes():
    assert tuple(sorted(ts.CENSUS)) == tuple(sorted(ts.SCENES))
    for scene in ts.SCENES:
        assert len(ts.CENSUS[scene]) == 8, scene


def test_no_drift():
    assert ts.drift() == ()


def test_finding_1_every_arm_saturates_by_midpoint():
    """The paper's own test — 'is the running max still climbing?' — says no."""
    for scene in ts.SCENES:
        assert ts.saturated_by_midpoint(scene) == tuple(sorted(ts.CENSUS[scene])), scene


def test_finding_2_deciding_scene_spread_dwarfs_its_instability():
    """On the scene the 512 rollouts are priced for, the max is stable."""
    vs_median, vs_worst = ts.spread_over_instability(ts.DECIDING_SCENE)
    assert vs_median > 100.0, vs_median
    assert vs_worst > 50.0, vs_worst


def test_finding_3_instability_sits_on_the_unexcited_scene():
    """Relative instability is larger where nobody proposed to grade."""
    deciding = ts.spread_over_instability(ts.DECIDING_SCENE)[1]
    control = ts.spread_over_instability("city_curved_v0")[1]
    assert control < deciding, (control, deciding)
    assert ts.tail_limited() == ("city_curved_v0",)


def test_the_cheap_exit_is_closed():
    """The module's consequence for the bottleneck, as an assertion."""
    assert ts.seed_axis_disqualified() is False


def test_threshold_is_lenient_not_tuned():
    """A generous threshold that still clears the deciding scene is the honest fail.

    Guards against the finding being an artefact of a tight constant. The
    margin is stated at the strength it has: the deciding scene's *worst* arm
    clears a **5x stricter** bar (gap is `1.5%` of the spread) and its *median*
    arm clears a **16x** stricter one (`0.5%`). It does **not** clear 10x on the
    worst arm — recorded here rather than rounded away, since that is the real
    headroom and finding #2 should not be quoted above it.
    """
    scene = ts.DECIDING_SCENE
    median, worst = ts.split_half_gap(scene)
    assert worst <= 0.02 * ts.arm_spread(scene), worst
    assert median <= 0.006 * ts.arm_spread(scene), median


def test_arm_spread_matches_census_column():
    for scene in ts.SCENES:
        col = [mx for _n, mx, _r, _g in ts.CENSUS[scene].values()]
        assert ts.arm_spread(scene) == pytest.approx(max(col) - min(col), abs=1e-4)


def test_format_census_names_the_verdict():
    out = ts.format_census()
    assert "seed axis disqualified:  False" in out
    assert ts.DECIDING_SCENE in out
