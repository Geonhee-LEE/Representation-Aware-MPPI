"""The geometric null arm and the attribution verdict it buys (STATE #1,
arxiv 2607.16591): is the clearance result the representation's, or geometry's?
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox import geometric_null as gn
from eval.mppi_sandbox.controllers import REGISTRY, make_controller
from eval.mppi_sandbox.controllers.geometric_mppi import (GeometricMPPI,
                                                          frozen_min_clearance)
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.scenario import load_scenario

CONVOY = "eval/scenarios/cafe_convoy_v0.yaml"


# --------------------------------------------------------------------------
# The controller: registry contract + the ablation invariant
# --------------------------------------------------------------------------

def test_geometric_mppi_is_in_the_registry():
    assert REGISTRY["geometric_mppi"] is GeometricMPPI


def test_w_geom_zero_is_byte_identical_to_stock():
    """The invariant every arm on this branch carries: the null's *off* state
    must be the baseline exactly, or a null-vs-stock reading is measuring the
    controller class rather than the term."""
    scen = load_scenario(CONVOY)
    stock = ab.run_arm(scen, "stock_mppi", seed=3)
    null_off = ab.run_arm(scen, "geometric_mppi", seed=3, w_geom=0.0)
    np.testing.assert_array_equal(stock.traj, null_off.traj)


def test_w_geom_nonzero_actually_moves_the_trajectory():
    """The positive control for the test above — an implementation that
    silently disabled the term would pass the invariant and nothing else.
    This is the `w_epist` inertness lesson (2026-08-02) applied up front."""
    scen = load_scenario(CONVOY)
    off = ab.run_arm(scen, "geometric_mppi", seed=3, w_geom=0.0)
    on = ab.run_arm(scen, "geometric_mppi", seed=3, w_geom=gn.NULL_W_GEOM)
    # The term changes the *duration* as well as the path, so the two arrays
    # need not even be the same length — shape inequality is a difference.
    assert (off.traj.shape != on.traj.shape
            or not np.allclose(off.traj, on.traj))


def test_geom_scale_must_be_positive():
    scen = load_scenario(CONVOY)
    with pytest.raises(ValueError, match="metres"):
        make_controller("geometric_mppi", scen, seed=0, w_geom=1.0,
                        geom_scale=0.0)


def test_geom_scale_defaults_to_the_barrier_decay_length():
    """The null gets no second free parameter to be tuned on."""
    scen = load_scenario(CONVOY)
    c = make_controller("geometric_mppi", scen, seed=0, w_geom=1.0)
    assert c.geom_scale == MPPIParams().obs_soft_scale


# --------------------------------------------------------------------------
# The "no motion model" property — this is what makes it the *min-lidar* null
# --------------------------------------------------------------------------

def _mover(vx: float) -> CircleObstacle:
    """An obstacle that closes on the origin at `vx` m/s along +x."""
    ts = np.arange(0.0, 11.0)
    schedule = np.stack([ts, vx * ts, np.zeros_like(ts)], axis=1)
    ob = CircleObstacle(x=0.0, y=0.0, radius=0.5, schedule=schedule)
    assert not np.allclose(ob.position(np.array([0.0]))[0],
                           ob.position(np.array([2.0]))[0]), \
        "this fixture is only meaningful if the obstacle actually moves"
    return ob


def test_clearance_is_frozen_across_the_rollout_horizon():
    """Two rollout steps at the *same* `t0` see the obstacle in one place —
    the horizon does not advance it. That is the whole difference from the
    DYNAMIC channel, which renders the predicted sweep forward."""
    ob = _mover(1.0)
    # One rollout, two horizon steps, at the identical point in space.
    traj_xy = np.array([[[3.0, 0.0], [3.0, 0.0]]])
    clear = frozen_min_clearance(traj_xy, [ob], t0=0.0, robot_radius=0.3)
    assert clear[0, 0] == pytest.approx(clear[0, 1])


def test_clearance_does_move_with_t0():
    """Frozen is not static: the *next control step* re-freezes at the new
    scan. An implementation that ignored `t0` entirely would pass the test
    above and be a different (and wrong) controller."""
    ob = _mover(1.0)
    traj_xy = np.array([[[3.0, 0.0]]])
    at0 = frozen_min_clearance(traj_xy, [ob], t0=0.0, robot_radius=0.3)[0, 0]
    at2 = frozen_min_clearance(traj_xy, [ob], t0=2.0, robot_radius=0.3)[0, 0]
    assert at2 < at0 - 1.0   # the obstacle closed 2 m of the gap


def test_clearance_reduces_by_min_not_by_sum():
    """A lidar returns the nearest return, and the sandbox's own soft barrier
    sums over obstacles independently. Reducing by `min` is what separates the
    two; a `sum` implementation would grow with obstacle count at fixed
    nearest distance."""
    near = CircleObstacle(x=1.0, y=0.0, radius=0.0)
    far = CircleObstacle(x=50.0, y=0.0, radius=0.0)
    traj_xy = np.array([[[0.0, 0.0]]])
    one = frozen_min_clearance(traj_xy, [near], t0=0.0, robot_radius=0.0)
    two = frozen_min_clearance(traj_xy, [near, far], t0=0.0, robot_radius=0.0)
    assert one[0, 0] == pytest.approx(two[0, 0])


def test_no_obstacles_leaves_the_term_silent():
    scen = load_scenario(CONVOY)
    c = make_controller("geometric_mppi", scen, seed=0, w_geom=1.0)
    c.obstacles = []
    traj = np.zeros((4, 3, 5))
    np.testing.assert_array_equal(c._extra_cost(traj, 0.0), np.zeros(4))


def test_deep_interpenetration_stays_finite():
    """The exponential is clipped so one rollout cannot cost `inf` — a
    non-finite cost makes the softmax unrankable rather than merely bad."""
    scen = load_scenario(CONVOY)
    c = make_controller("geometric_mppi", scen, seed=0, w_geom=1.0)
    ob = c.obstacles[0]
    at = np.asarray(ob.position(np.array([0.0])), dtype=float)[0]
    traj = np.zeros((1, 2, 5))
    traj[..., :2] = at                      # dead centre of the obstacle
    assert np.isfinite(c._extra_cost(traj, 0.0)).all()


# --------------------------------------------------------------------------
# The recorded walk
# --------------------------------------------------------------------------

def test_the_null_walk_is_paired_with_the_recorded_arms():
    """`versus_geometry` differences arm outcomes by seed index, so the three
    samples must be the same length or the pairing is not what it claims."""
    from eval.mppi_sandbox.scene_transplant import CONVOY_W75_CLEARANCES
    assert len(gn.NULL_CLEARANCES) == len(CONVOY_W75_CLEARANCES["stock_mppi"])
    assert len(gn.NULL_CLEARANCES) == len(CONVOY_W75_CLEARANCES["risk_mppi"])


def test_the_null_walk_was_admissible():
    """Both terms, and separately — an arm that did not drive and an arm
    sampled at a bad temperature are refused for different reasons."""
    assert gn.NULL_ADMISSIBILITY["all_reached"] is True
    assert gn.NULL_ADMISSIBILITY["ess_in_band"] is True


def test_the_null_walk_matches_the_recorded_rungs_operating_point():
    """A head-to-head against a *differently* calibrated arm would be a
    comparison of operating points wearing the mechanism's name."""
    from eval.mppi_sandbox import scene_transplant as st
    assert (gn.NULL_SCENARIO, gn.NULL_LAM, gn.NULL_WEIGHT, gn.NULL_MARGIN) == \
        (st.CONVOY_SCENARIO, st.CONVOY_LAM, st.CONVOY_WEIGHT, st.CONVOY_MARGIN)


# --------------------------------------------------------------------------
# The verdict
# --------------------------------------------------------------------------

def test_the_recorded_mechanism_rung_is_still_the_populations_largest():
    """The rung was chosen because D-166 ranks it `A = 1.0000`. If that ever
    stops being true the choice needs re-arguing, so it is pinned here."""
    assert gn.mechanism_versus_stock().superiority == pytest.approx(1.0)


def test_geometry_alone_very_nearly_reproduces_the_mechanism_separation():
    """The measured headline: geometry alone reaches `A = 0.9868` against
    stock where the representation reaches `1.0000`."""
    assert gn.versus_stock().superiority == pytest.approx(0.9868, abs=5e-4)


def test_shipped_verdict_is_representation_adds():
    a = gn.attribution()
    assert a.admissible
    assert a.verdict == gn.REPRESENTATION_ADDS


def test_the_residual_the_representation_owns_is_a_quarter_of_the_effect():
    """`REPRESENTATION_ADDS` on its own reads as a win for the branch's
    premise. The share is what makes it a qualified one, so it is pinned at
    the same place as the verdict rather than left to the prose."""
    assert gn.attribution().residual_share == pytest.approx(0.772, abs=2e-3)


def test_the_head_to_head_edge_is_real_and_not_a_boundary_call():
    """The verdict turns on the head-to-head CI excluding zero. If it merely
    grazed zero the reading would be an artefact of the bootstrap seed, so
    both ends are pinned."""
    lo, hi = gn.versus_geometry().bootstrap_ci()
    assert lo > 0.0
    assert (lo, hi) == pytest.approx((0.0161, 0.0505), abs=5e-4)


def test_the_residual_does_not_survive_one_coefficient_rung_up():
    """The refused louder null: `EQUIVALENT` at eps = 0.05 m with a CI that
    contains zero. Pinned because "the residual is 23%" and "the residual is
    stable" are different claims and the module only measures the first."""
    loud = gn.louder_versus_geometry()
    lo, hi = loud.bootstrap_ci()
    assert lo < 0.0 < hi
    assert loud.equivalence(gn.Attribution().eps) == "EQUIVALENT"


def test_the_louder_null_is_refused_and_the_verdict_never_reads_it():
    """It is recorded data, not a graded arm — its ESS failed on 32 seeds."""
    assert gn.LOUDER_NULL["ess_in_band"] is False
    assert gn.LOUDER_NULL["clearances"] != gn.NULL_CLEARANCES
    # The verdict is a function of the admissible walk alone: perturbing the
    # refused one must not move it.
    before = gn.attribution().verdict
    saved = dict(gn.LOUDER_NULL)
    try:
        gn.LOUDER_NULL["clearances"] = tuple(
            v + 10.0 for v in saved["clearances"])
        assert gn.attribution().verdict == before
    finally:
        gn.LOUDER_NULL.update(saved)


def test_the_equal_coefficient_swap_has_no_shared_admissible_temperature():
    """The refusal that forced the calibration. Stated as a recomputation off
    `LAM_LADDER` rather than as a constant, so an edit to the ladder cannot
    leave the claim behind."""
    assert gn.shared_admissible_lams() == ()
    # And the reason: the two populations' admissible columns do not meet.
    assert gn.LAM_LADDER[0.8]["geometric_mppi"] < 8
    assert gn.LAM_LADDER[0.8]["stock_mppi"] == 8
    assert gn.LAM_LADDER[0.8]["risk_mppi"] == 8
    assert gn.LAM_LADDER[1.6]["geometric_mppi"] == 7    # the null's own best


def test_shared_admissible_lams_is_reachable():
    """Its shipped reading is empty, so the non-empty branch has no witness —
    D-107's shape, proved synthetically."""
    saved = dict(gn.LAM_LADDER)
    try:
        gn.LAM_LADDER[0.8] = {"stock_mppi": 8, "risk_mppi": 8,
                              "geometric_mppi": 8}
        assert gn.shared_admissible_lams() == (0.8,)
    finally:
        gn.LAM_LADDER.clear()
        gn.LAM_LADDER.update(saved)


def test_geometry_suffices_is_reachable(monkeypatch):
    """No shipped witness — the head-to-head separates — so it is proved
    synthetically alongside the other unwitnessed verdicts."""
    stock = tuple(float(i) for i in range(8))
    both = tuple(v + 5.0 for v in stock)
    monkeypatch.setattr(gn, "NULL_CLEARANCES", both)
    monkeypatch.setattr(gn, "CONVOY_W75_CLEARANCES",
                        {"stock_mppi": stock, "risk_mppi": both})
    assert gn.Attribution().verdict == gn.GEOMETRY_SUFFICES


def test_residual_share_refuses_a_zero_denominator():
    """A rung where the mechanism has no gain has no share of one to
    attribute — the empty-denominator guard, in its arithmetic form."""
    flat = tuple(float(i) for i in range(8))
    a = gn.Attribution()
    import unittest.mock as mock
    with mock.patch.object(gn, "CONVOY_W75_CLEARANCES",
                           {"stock_mppi": flat, "risk_mppi": flat}):
        with pytest.raises(ZeroDivisionError, match="no gain"):
            _ = a.residual_share


def test_an_inadmissible_walk_refuses_rather_than_ties():
    """The empty-denominator guard: `NULL_INADMISSIBLE` and `GEOMETRY_SUFFICES`
    must not print the same, because "indistinguishable" and "one arm's runs
    do not count" are opposite epistemic states."""
    assert gn.Attribution(admissible=False).verdict == gn.NULL_INADMISSIBLE


def test_both_inert_is_reachable():
    """No shipped witness — this rung separates — so it is proved
    synthetically, D-107's shape."""
    a = gn.Attribution(inert_effect=0.999)
    assert a.verdict == gn.BOTH_INERT


def test_representation_adds_and_geometry_wins_are_both_reachable(monkeypatch):
    """Neither verdict has a shipped witness either, and they are the two the
    branch's premise turns on — a mis-wired sign would otherwise be invisible
    until a scene finally separated."""
    stock = tuple(float(i) for i in range(8))
    weak = tuple(v + 0.1 for v in stock)
    strong = tuple(v + 5.0 for v in stock)

    monkeypatch.setattr(gn, "NULL_CLEARANCES", weak)
    monkeypatch.setattr(
        gn, "CONVOY_W75_CLEARANCES",
        {"stock_mppi": stock, "risk_mppi": strong})
    assert gn.Attribution().verdict == gn.REPRESENTATION_ADDS

    monkeypatch.setattr(gn, "NULL_CLEARANCES", strong)
    monkeypatch.setattr(
        gn, "CONVOY_W75_CLEARANCES",
        {"stock_mppi": stock, "risk_mppi": weak})
    assert gn.Attribution().verdict == gn.GEOMETRY_WINS
