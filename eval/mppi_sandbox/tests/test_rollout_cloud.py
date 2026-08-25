# SPDX-License-Identifier: BSD-3-Clause
"""Q-149 — the cancelling root read on a planner-shaped candidate set."""

import numpy as np
import pytest

from eval.mppi_sandbox import cancelling_stability as cs
from eval.mppi_sandbox import epistemic_sign as es
from eval.mppi_sandbox import rollout_cloud as rc


# --- the new path is the old quantity ------------------------------------

def test_scene_reproduces_blind_corner():
    """`scene()` must be a re-use of `blind_corner`'s geometry, not a fork."""
    _, bev_ref, robot_ref, points_ref, _ = es.blind_corner(radius=0.5, stride=13)
    _, bev, robot = rc.scene(0.5)
    assert np.array_equal(bev.stack, bev_ref.stack)
    assert np.array_equal(bev.origin, bev_ref.origin)
    assert np.array_equal(robot, robot_ref)
    assert np.array_equal(rc.grid_points(bev, 13), points_ref)


@pytest.mark.parametrize("radius,stride", [(0.3, 7), (0.5, 13), (1.0, 31)])
def test_root_on_grid_equals_root_at(radius, stride):
    """`root_on` on the grid set is `cancelling_stability.root_at` verbatim.

    This equality is what makes the module a re-read of D-257's number rather
    than a new number wearing its name (D-047).
    """
    producer, bev, robot = rc.scene(radius)
    got = rc.root_on(producer, bev, robot, rc.grid_points(bev, stride))
    assert got == pytest.approx(cs.root_at(radius, stride), rel=1e-12)


def test_grid_k_matches_the_grid_it_describes():
    _, bev, _ = rc.scene(0.5)
    for stride in (3, 13, 31):
        assert rc.grid_k(bev, stride) == len(rc.grid_points(bev, stride))


# --- the candidate sets are what they claim to be -------------------------

def test_uniform_points_fill_the_window():
    _, bev, _ = rc.scene(0.5)
    pts = rc.uniform_points(bev, 4000, seed=0)
    n = bev.stack.shape[1]
    span = n * bev.resolution
    assert len(pts) == 4000
    assert (pts >= bev.origin).all() and (pts <= bev.origin + span).all()
    # covers the window rather than a corner of it
    assert (pts.min(axis=0) < bev.origin + 0.05 * span).all()
    assert (pts.max(axis=0) > bev.origin + 0.95 * span).all()


def test_rollout_points_are_robot_anchored_and_forward_biased():
    """The cloud must be planner-shaped: it starts at the robot and fans ahead.

    This is the property that makes the ROLLOUT band worth reading at all — a
    cloud that filled the window uniformly would just be `uniform` with extra
    steps, and the displacement below would carry no planner meaning.
    """
    _, bev, _ = rc.scene(0.5)
    pts = rc.rollout_points(bev, 900, seed=0)
    assert len(pts) == 900
    d = np.linalg.norm(pts, axis=1)
    assert d.min() < 0.2                      # anchored at the robot
    assert pts[:, 0].mean() > 3 * abs(pts[:, 1].mean())   # forward-biased
    # and it does NOT cover the window the grid covers
    n = bev.stack.shape[1]
    span = n * bev.resolution
    assert pts[:, 0].min() > bev.origin[0] + 0.25 * span


def test_rollout_points_obey_the_sandbox_speed_limit():
    """Consecutive points within one rollout are inside `Limits().v_max·dt`."""
    _, bev, _ = rc.scene(0.5)
    pts = rc.rollout_points(bev, rc.ROLLOUT_H * 4, seed=3)
    per = pts.reshape(4, rc.ROLLOUT_H, 2)
    hops = np.linalg.norm(np.diff(per, axis=1), axis=2)
    from eval.mppi_sandbox.dynamics import Limits
    assert hops.max() <= Limits().v_max * rc.ROLLOUT_DT + 1e-9


def test_clouds_are_seed_deterministic_and_seed_sensitive():
    _, bev, _ = rc.scene(0.5)
    for maker in (rc.uniform_points, rc.rollout_points):
        assert np.array_equal(maker(bev, 200, 4), maker(bev, 200, 4))
        assert not np.array_equal(maker(bev, 200, 4), maker(bev, 200, 5))


# --- the band ------------------------------------------------------------

def test_band_needs_a_real_ensemble_to_be_a_band():
    band = rc.band_on(rc.UNIFORM, 0.5, 200, ensemble=(0, 1, 2))
    assert len(band.roots) == 3
    assert band.lo <= band.mean <= band.hi
    assert band.width == band.hi - band.lo
    assert band.contains(band.mean)


def test_band_on_rejects_an_unknown_support():
    with pytest.raises(ValueError, match="unknown support"):
        rc.band_on("LATTICE", 0.5, 200)


def test_grid_band_ignores_k_and_summarises_its_own_ensemble():
    """For GRID the stride sets K, so a passed-in `k` must not be believed.

    And no single K describes the stride ensemble — it spans ~10x — so the field
    holds the median, which is a summary rather than the band's parameter.
    """
    _, bev, _ = rc.scene(0.5)
    band = rc.band_on(rc.GRID, 0.5, k=999_999, ensemble=(11, 13, 17))
    assert band.k == int(np.median([rc.grid_k(bev, s) for s in (11, 13, 17)]))
    assert rc.grid_k(bev, 3) > 9 * rc.grid_k(bev, 31)   # the ~10x K span


def test_separation_accepts_a_cloud_band():
    """`CloudBand` is passed to `cancelling_stability.separation` by duck-type.

    Cross-module duck-typing is a contract nobody declared; this declares it.
    """
    a = rc.CloudBand(rc.UNIFORM, 0.5, 10, (0.1, 0.2), (0, 1))
    b = rc.CloudBand(rc.ROLLOUT, 0.5, 10, (0.3, 0.4), (0, 1))
    c = rc.CloudBand(rc.ROLLOUT, 0.5, 10, (0.15, 0.4), (0, 1))
    assert cs.separation(a, b) == cs.SEPARATED
    assert cs.separation(a, c) == cs.CONFOUNDED


# --- the two findings ----------------------------------------------------

@pytest.fixture(scope="module")
def bands():
    return rc.compare(radius=0.5, stride=13)


def test_clouds_are_matched_to_the_grid_count(bands):
    """Matched K is exact, not approximate — the comparison depends on it."""
    _, bev, _ = rc.scene(0.5)
    k = rc.grid_k(bev, 13)
    assert bands[rc.UNIFORM].k == k == bands[rc.ROLLOUT].k


def test_the_grid_width_is_sampling_not_alignment(bands):
    """Finding 1: the matched-K random cloud is *wider*, not narrower.

    So D-257's stride spread was not lattice alignment. A regular lattice is the
    lower-variance estimator of a ray aggregate at fixed K, which makes D-257's
    band a lower bound on what a K-point reading costs.
    """
    verdict, ratio = rc.width_attribution(bands)
    assert verdict == "LATTICE_TIGHTER"
    assert ratio > 1.5
    assert bands[rc.UNIFORM].width > bands[rc.GRID].width


def test_the_planner_support_moves_the_root(bands):
    """Finding 2 (the load-bearing one): ROLLOUT and GRID bands are disjoint.

    D-256's `0.3587` and D-257's whole radius sweep are readings on a support no
    planner scores. On a planner-shaped cloud the attract arm needs materially
    more weight to cancel the sum, so Q-148's both-arms-on cell sits somewhere
    else than the grid reading placed it.
    """
    assert rc.support_moves_the_root(bands) == cs.SEPARATED
    assert bands[rc.ROLLOUT].lo > bands[rc.GRID].hi      # and in this direction
    assert bands[rc.ROLLOUT].mean > 1.5 * bands[rc.GRID].mean


def test_the_grid_band_still_contains_the_published_number(bands):
    """D-256's `0.3587` is not wrong *for the grid* — it is wrong about scope."""
    assert bands[rc.GRID].contains(0.3587)
    assert not bands[rc.ROLLOUT].contains(0.3587)


def test_displacement_is_a_majority_not_a_law():
    """Across D-257's own radii the displacement holds at most, not all, cells.

    Measured, not asserted into existence: `SEPARATED` at 4 radii, `CONFOUNDED`
    at 2, and `UNPOSED` at the largest. The honest claim is therefore "the
    support usually moves the root", not "the support moves the root" — quoting
    the r=0.5 cell as a property is the same over-reach D-257 caught D-256 in.
    """
    sweep = rc.displacement_sweep()
    verdicts = [v for _, v in sweep]
    assert len(sweep) == 7
    assert verdicts.count(cs.SEPARATED) == 4
    assert verdicts.count(cs.CONFOUNDED) == 2
    assert verdicts.count(rc.UNPOSED) == 1
    # never in the other direction: where they separate, ROLLOUT is always above
    for radius, verdict in sweep:
        if verdict == cs.SEPARATED:
            b = rc.compare(radius, 13)
            assert b[rc.ROLLOUT].lo > b[rc.GRID].hi


def test_the_largest_radius_is_unposed_on_the_planner_support():
    """At r=1.25 the rollout cloud never reaches a shadowed point.

    The grid reports a finite root at that radius anyway, because it samples the
    region behind the disc that no forward rollout of this horizon can enter.
    One support has no question; the other has an answer. That is the sharpest
    form of the displacement finding and it must not read as a crash.
    """
    assert dict(rc.displacement_sweep())[1.25] == rc.UNPOSED
    with pytest.raises(ValueError, match="does not pose the question"):
        rc.band_on(rc.ROLLOUT, 1.25, rc.matched_k(1.25, 13), ensemble=(0, 1))
    # the grid, on the same scene, answers
    assert cs.band_at(1.25).width >= 0.0


def test_the_summed_sign_is_still_repel_at_unit_weight(bands):
    """At 1:1 the sum stays REPEL on the planner support — the *margin* shrank.

    The root moving from ~0.35 to ~0.75 does not flip Q-148's both-on cell; it
    moves it from 2.8x of headroom down to ~1.3x, which is why the cell stops
    being a disguised re-run of the repel arm and starts being informative.
    """
    assert bands[rc.ROLLOUT].hi < 1.0
    assert 1.0 / bands[rc.ROLLOUT].mean < 1.0 / bands[rc.GRID].mean


def test_format_compare_reports_both_findings(bands):
    text = rc.format_compare(bands)
    assert "LATTICE_TIGHTER" in text
    assert cs.SEPARATED in text
    for name in (rc.GRID, rc.UNIFORM, rc.ROLLOUT):
        assert name in text
