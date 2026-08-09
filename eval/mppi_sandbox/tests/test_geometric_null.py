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

#: The walked rung's own operating point, named at every construction site
#: rather than inherited from `MPPIParams.lam = 0.1`. `default_lam_sites`
#: charged the first draft of this file eight `DEFAULTS` and four
#: `inert_defaults` for leaving it implicit, which is the census doing exactly
#: what D-124 / D-126 record it doing: a test that does not name the
#: temperature is asserting about the shipped default, not about the rung.
LAM, W_OBS = 0.8, 75.0


def synthetic_rung(stock, geom, risk, **kw) -> gn.NullRung:
    """A rung whose three arms are stated rather than measured.

    Four of this file's verdicts have **no shipped witness** (D-107's rule:
    prove the unreachable branch synthetically or it is untested). Before the
    census landed they were proved by monkeypatching module constants, which
    stopped working the moment a rung became a record — and that is the better
    outcome: a verdict built from a stated `NullRung` cannot silently disagree
    with the one the shipped rung takes, because it goes through the same
    method.
    """
    fields = dict(
        scenario="synthetic", lam=LAM, weight=W_OBS, margin=0.30, w_geom=1.0,
        clearances=tuple(geom), all_reached=True, ess_in_band=True,
        recorded={"stock_mppi": tuple(stock), "risk_mppi": tuple(risk)})
    fields.update(kw)
    return gn.NullRung(**fields)


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
    stock = ab.run_arm(scen, "stock_mppi", seed=3, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    null_off = ab.run_arm(scen, "geometric_mppi", seed=3, w_geom=0.0,
                          params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    np.testing.assert_array_equal(stock.traj, null_off.traj)


def test_w_geom_nonzero_actually_moves_the_trajectory():
    """The positive control for the test above — an implementation that
    silently disabled the term would pass the invariant and nothing else.
    This is the `w_epist` inertness lesson (2026-08-02) applied up front."""
    scen = load_scenario(CONVOY)
    off = ab.run_arm(scen, "geometric_mppi", seed=3, w_geom=0.0,
                     params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    on = ab.run_arm(scen, "geometric_mppi", seed=3, w_geom=gn.NULL_W_GEOM,
                    params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    # The term changes the *duration* as well as the path, so the two arrays
    # need not even be the same length — shape inequality is a difference.
    assert (off.traj.shape != on.traj.shape
            or not np.allclose(off.traj, on.traj))


def test_geom_scale_must_be_positive():
    scen = load_scenario(CONVOY)
    with pytest.raises(ValueError, match="metres"):
        make_controller("geometric_mppi", scen, seed=0, w_geom=1.0,
                        geom_scale=0.0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))


def test_geom_scale_defaults_to_the_barrier_decay_length():
    """The null gets no second free parameter to be tuned on."""
    scen = load_scenario(CONVOY)
    c = make_controller("geometric_mppi", scen, seed=0, w_geom=1.0,
                        params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
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
    c = make_controller("geometric_mppi", scen, seed=0, w_geom=1.0,
                        params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    c.obstacles = []
    traj = np.zeros((4, 3, 5))
    np.testing.assert_array_equal(c._extra_cost(traj, 0.0), np.zeros(4))


def test_deep_interpenetration_stays_finite():
    """The exponential is clipped so one rollout cannot cost `inf` — a
    non-finite cost makes the softmax unrankable rather than merely bad."""
    scen = load_scenario(CONVOY)
    c = make_controller("geometric_mppi", scen, seed=0, w_geom=1.0,
                        params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
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


def test_geometry_suffices_is_reachable():
    """No shipped witness — the head-to-head separates — so it is proved
    synthetically alongside the other unwitnessed verdicts."""
    stock = tuple(float(i) for i in range(8))
    both = tuple(v + 5.0 for v in stock)
    rung = synthetic_rung(stock, both, both)
    assert rung.attribution().verdict == gn.GEOMETRY_SUFFICES


def test_residual_share_refuses_a_zero_denominator():
    """A rung where the mechanism has no gain has no share of one to
    attribute — the empty-denominator guard, in its arithmetic form."""
    flat = tuple(float(i) for i in range(8))
    rung = synthetic_rung(flat, tuple(v + 1.0 for v in flat), flat)
    with pytest.raises(ZeroDivisionError, match="no gain"):
        _ = rung.attribution().residual_share


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


def test_representation_adds_and_geometry_wins_are_both_reachable():
    """Neither verdict has a shipped witness either, and they are the two the
    branch's premise turns on — a mis-wired sign would otherwise be invisible
    until a scene finally separated."""
    stock = tuple(float(i) for i in range(8))
    weak = tuple(v + 0.1 for v in stock)
    strong = tuple(v + 5.0 for v in stock)

    assert (synthetic_rung(stock, weak, strong).attribution().verdict
            == gn.REPRESENTATION_ADDS)
    assert (synthetic_rung(stock, strong, weak).attribution().verdict
            == gn.GEOMETRY_WINS)


# --------------------------------------------------------------------------
# The census: coverage before verdict, and scene/rung confounding
# --------------------------------------------------------------------------

def test_census_denominator_is_the_walked_rung_population():
    """Coverage is reported against `margin_free`'s six walked rungs, read
    rather than hard-coded — so walking a seventh rung there lowers this
    census's coverage instead of leaving it silently flattering."""
    from eval.mppi_sandbox import margin_free as mf

    assert gn.census().population == len(mf.census().rungs)


def test_census_counts_only_admissible_rungs():
    """An inadmissible walk is not a rung the census has covered. Same rule
    `Attribution` applies one level down (`NULL_INADMISSIBLE`), applied to the
    denominator so an inadmissible walk cannot inflate coverage."""
    good = synthetic_rung((1.0, 2.0), (1.5, 2.5), (2.0, 3.0))
    bad = synthetic_rung((1.0, 2.0), (1.5, 2.5), (2.0, 3.0),
                         ess_in_band=False)
    c = gn.NullCensus(rungs=(good, bad))
    assert c.graded == (good,)
    assert c.coverage[0] == 1


def test_a_single_rung_census_refuses_to_generalise():
    """One rung cannot say whether its reading travels — the state D-167
    shipped in, named rather than reported as a positive result.

    The shipped census left that state in the *other* direction at D-170 (0
    rungs, not 2), so the rule is pinned synthetically. It is a statement about
    the verdict logic and should not have been resting on the coverage the
    branch happened to have that week."""
    one = synthetic_rung(tuple(float(i) for i in range(8)),
                         tuple(float(i) + 0.1 for i in range(8)),
                         tuple(float(i) + 5.0 for i in range(8)))
    c = gn.NullCensus(rungs=(one,))
    assert c.coverage[0] == 1
    assert c.verdict == gn.SINGLE_RUNG
    assert c.separates_scene_from_rung is False


def test_disagreeing_rungs_from_different_scenes_stay_confounded():
    """Two rungs, two scenes, opposite verdicts: "rung property" and "scene
    property" are the same statement about that data, so the census says so
    instead of picking one. This is exactly STATE's open question and the
    census must not answer it from a design that cannot."""
    stock = tuple(float(i) for i in range(8))
    weak = tuple(v + 0.1 for v in stock)
    strong = tuple(v + 5.0 for v in stock)
    adds = synthetic_rung(stock, weak, strong, scenario="scene_a")
    suffices = synthetic_rung(stock, strong, strong, scenario="scene_b")
    c = gn.NullCensus(rungs=(adds, suffices))

    assert set(c.verdicts.values()) == {gn.REPRESENTATION_ADDS,
                                        gn.GEOMETRY_SUFFICES}
    assert c.verdict == gn.SCENE_CONFOUNDED_WITH_RUNG


def test_two_rungs_of_one_scene_separate_scene_from_rung():
    """The same disagreement becomes attributable the moment one scene
    contributes both rungs — the property that says when STATE's question is
    answerable at all."""
    stock = tuple(float(i) for i in range(8))
    weak = tuple(v + 0.1 for v in stock)
    strong = tuple(v + 5.0 for v in stock)
    import dataclasses as dc
    adds = synthetic_rung(stock, weak, strong)
    suffices = dc.replace(synthetic_rung(stock, strong, strong), weight=100.0)
    c = gn.NullCensus(rungs=(adds, suffices))

    assert c.separates_scene_from_rung is True
    assert c.verdict == gn.RESIDUAL_RUNG_DEPENDENT


def test_agreeing_rungs_read_residual_holds():
    stock = tuple(float(i) for i in range(8))
    weak = tuple(v + 0.1 for v in stock)
    strong = tuple(v + 5.0 for v in stock)
    import dataclasses as dc
    a = synthetic_rung(stock, weak, strong)
    b = dc.replace(a, weight=100.0)
    assert gn.NullCensus(rungs=(a, b)).verdict == gn.RESIDUAL_HOLDS


def test_an_empty_census_is_not_a_tie():
    """D-107's shape one more time: no graded rung is an empty denominator,
    not agreement."""
    bad = synthetic_rung((1.0, 2.0), (1.5, 2.5), (2.0, 3.0),
                         all_reached=False)
    assert gn.NullCensus(rungs=(bad,)).verdict == gn.NO_GRADED_RUNG
    assert gn.NullCensus(rungs=()).verdict == gn.NO_GRADED_RUNG


def test_shares_are_reported_per_rung_and_never_averaged():
    """A mean over rungs measured at different `w_geom` on different scenes is
    not a quantity — the API only offers the per-rung mapping."""
    assert not hasattr(gn.NullCensus(rungs=()), "mean_share")
    shares = gn.census().shares
    assert len(shares) == len(gn.census().graded)
    assert all(isinstance(v, float) for v in shares.values())


# --------------------------------------------------------------------------
# Was the coefficient the null was walked at ever pinned?
# --------------------------------------------------------------------------

def test_an_unrecorded_ladder_is_not_a_flat_one():
    """Three states, not two: D-167's rung carries no `w_geom` ladder, and
    "the criterion could not pin it" must not be read off "nobody wrote it
    down"."""
    r = synthetic_rung((1.0,), (2.0,), (3.0,))
    assert r.ess_response is None
    assert r.coefficient_identification == "UNRECORDED"


def test_a_flat_ladder_does_not_identify_the_coefficient():
    """Every candidate matching the target equally well is the criterion
    failing, not succeeding — and it looks identical to success in the picked
    number alone."""
    flat = synthetic_rung((1.0,), (2.0,), (3.0,),
                          ess_ladder={1.0: 115.8, 2.0: 115.9, 8.0: 115.6},
                          ess_target=115.9)
    assert flat.ess_response < gn.FLAT_ESS_RESPONSE
    assert flat.coefficient_identification == "FLAT"


def test_a_responsive_ladder_identifies_it():
    steep = synthetic_rung((1.0,), (2.0,), (3.0,),
                           ess_ladder={2.5: 86.0, 40.0: 12.4},
                           ess_target=105.0)
    assert steep.coefficient_identification == "IDENTIFIED"


def test_only_a_mechanism_win_on_a_flat_rung_is_exposed():
    """The controller's residual asymmetry, as a countable list: a null that
    loses on an unpinned coefficient may merely be quiet, while a null that
    ties or wins is not exposed to that objection at all."""
    stock = tuple(float(i) for i in range(8))
    weak = tuple(v + 0.1 for v in stock)
    strong = tuple(v + 5.0 for v in stock)
    ladder = {1.0: 115.8, 8.0: 115.6}

    exposed = synthetic_rung(stock, weak, strong, scenario="flat_win",
                             ess_ladder=ladder, ess_target=115.9)
    not_exposed = synthetic_rung(stock, strong, strong, scenario="flat_tie",
                                 ess_ladder=ladder, ess_target=115.9)
    pinned_win = synthetic_rung(stock, weak, strong, scenario="pinned_win",
                                ess_ladder={2.5: 86.0, 40.0: 12.4},
                                ess_target=105.0)

    c = gn.NullCensus(rungs=(exposed, not_exposed, pinned_win))
    assert c.exposed_to_quiet_null == (f"flat_win@{W_OBS:g}",)


# --------------------------------------------------------------------------
# The second rung: walked, refused, and pointing the other way
# --------------------------------------------------------------------------

def test_the_head_on_walk_is_paired_with_the_recorded_arms():
    from eval.mppi_sandbox.separation_reproduction import W75_CLEARANCES

    r = gn.HEADON_W75_NULL
    assert len(r.clearances) == len(W75_CLEARANCES["stock_mppi"]) == 32
    assert r.recorded is W75_CLEARANCES


def test_the_head_on_walk_is_refused_on_one_seed():
    """31/32 in band is a refusal, not a rounding error: `assert_ess_in_band`
    is all-seeds and every walk on this branch is held to it."""
    r = gn.HEADON_W75_NULL
    assert r.all_reached is True
    assert r.ess_in_band is False
    assert r.admissible is False
    assert r.attribution().verdict == gn.NULL_INADMISSIBLE


def test_the_refused_rung_is_listed_but_not_graded():
    """It stays in `null_rungs` so the refusal is visible, and out of `graded`
    so it cannot move a verdict — a walk dropped from the list entirely is a
    walk nobody can see was refused."""
    c = gn.census()
    assert gn.HEADON_W75_NULL in c.rungs
    assert gn.HEADON_W75_NULL not in c.graded
    # D-170: convoy joined it in `rungs`-but-not-`graded`, so the census's
    # denominator is now empty. The invariant under test is unchanged — every
    # walk stays visible, no refused walk votes — and it is *more* load-bearing
    # at 0/6 than it was at 1/6, since the list is now the only place either
    # walk can be seen at all.
    assert len(c.rungs) == 2
    assert c.coverage == (0, c.population)
    assert c.verdict == gn.NO_GRADED_RUNG


def test_the_refused_rungs_numbers_disagree_with_the_graded_one():
    """Recorded because it is the reason this rung was worth walking and the
    reason it must not be quoted as a result. Convoy says geometry reproduces
    77% of the gain; head_on's refused walk says 5% — the opposite direction.
    Both cannot be the residual, and neither is settled while one of the two
    is inadmissible on ESS *and* taken at an unpinned coefficient.

    D-170 closed this the other way round from how it was expected to close:
    not by settling which number is the residual but by refusing both rungs,
    so the disagreement is now between two figures that the census quotes
    neither of. Kept, with the reading it is now evidence for."""
    graded = gn.CONVOY_W75_NULL.attribution().residual_share
    refused = gn.HEADON_W75_NULL.attribution().residual_share
    assert graded > 0.7
    assert refused < 0.1
    assert gn.HEADON_W75_NULL.coefficient_identification == "FLAT"
    # ...and neither is a reading any more: both rungs are ungraded, for two
    # *different* reasons — head_on's criterion never responded, convoy's did.
    assert gn.CONVOY_W75_NULL.coefficient_identification == "IDENTIFIED"
    assert gn.census().graded == ()


def test_the_flat_ladder_is_what_the_pick_came_off():
    """The pick is the ESS-closest rung of a ladder that barely moves — every
    candidate 'matches', so the coefficient is the ladder's spacing rather
    than a measurement.

    The bound was 1% when the ladder topped out at `w_geom = 8`. D-169
    extended it 20× to 160 and the span went to 1.70%, so the number here is
    the re-measured one — **tightened in meaning, not loosened**: the old
    reading was consistent with "the ladder was too short", and this one is
    not.
    """
    r = gn.HEADON_W75_NULL
    assert r.w_geom in r.ess_ladder
    assert max(r.ess_ladder) == 160.0
    assert r.ess_response < 0.02
    assert r.coefficient_identification == "FLAT"


def test_the_refusal_is_the_quiet_direction():
    """Seed 25 ran at ESS 134.15 against a band topping out at 128.0 — above,
    not below. Pinned because the direction is what decides whether the
    head_on numbers are evidence: a null refused for being too *quiet* is the
    exact case the controller's residual asymmetry says cannot be read as the
    mechanism winning."""
    lo, hi = ab.ess_band(256)
    assert (lo, hi) == (12.8, 128.0)
    assert 134.15 > hi
    assert gn.HEADON_W75_NULL.ess_in_band is False


# --------------------------------------------------------------------------
# D-169: extending the ladder answered STATE's question in the third way
# --------------------------------------------------------------------------


def test_extending_the_ladder_20x_does_not_wake_the_sampler():
    """STATE predicted two outcomes and both assumed the null was too *quiet*:
    extend `w_geom` until median ESS responds, then re-walk. Extended 20× past
    the old top rung it still does not respond, so neither predicted branch is
    the one that happened."""
    r = gn.HEADON_W75_NULL
    assert set(r.ess_ladder) >= {10.0, 20.0, 40.0, 80.0, 160.0}
    assert r.ess_response < gn.FLAT_ESS_RESPONSE / 5


def test_ess_and_behaviour_are_decoupled_by_two_orders_of_magnitude():
    """The finding. The sampler's ESS is blind to a coefficient that moves
    achieved clearance by more than the mechanism's entire gain over stock, so
    "matched on ESS" and "matched in loudness" are not the same predicate on
    this scene."""
    r = gn.HEADON_W75_NULL
    assert r.ess_response < 0.02
    assert r.behavioural_response > 1.0
    assert r.behavioural_response / r.ess_response > 50


def test_the_ladder_reaches_opposite_verdicts():
    """Not merely 'more than one' — the two verdicts that contradict each
    other. `REPRESENTATION_ADDS` says the representation buys something
    geometry does not; `GEOMETRY_WINS` says geometry beats it. Both are
    reachable on one rung by moving a coefficient the ESS criterion cannot
    distinguish, which is why the rung carries no reading."""
    verdicts = gn.HEADON_W75_NULL.ladder_verdicts
    assert gn.REPRESENTATION_ADDS in verdicts.values()
    assert gn.GEOMETRY_WINS in verdicts.values()
    assert gn.HEADON_W75_NULL.verdict_identification == gn.VERDICT_UNIDENTIFIED


def test_the_ladder_rungs_are_not_refusable_on_the_walks_grounds():
    """Every ladder rung had 16/16 reach and 16/16 in band, so the spread of
    verdicts above cannot be waved off as inadmissible runs — the objection
    that retired the 32-seed `w_geom = 2.0` walk does not reach these."""
    for w, (reached, in_band) in gn.HEADON_W75_LADDER_ADMISSIBILITY.items():
        assert w in gn.HEADON_W75_CLEARANCE_LADDER
        assert (reached, in_band) == (16, 16)
    assert set(gn.HEADON_W75_LADDER_ADMISSIBILITY) == set(
        gn.HEADON_W75_CLEARANCE_LADDER)


def test_ladder_verdicts_read_against_the_ladders_own_seeds():
    """The ladder is 16 seeds and the recorded arms are 32. Both are
    seed-ordered from 0, so the comparison must use the shared prefix; reading
    16 null clearances against 32 recorded ones compares two different seed
    sets and the pairing `residual_share` depends on is gone."""
    r = gn.HEADON_W75_NULL
    stock, risk = r._ladder_arms()
    assert len(stock) == len(risk) == 16
    assert stock == r.recorded["stock_mppi"][:16]
    assert len(r.recorded["stock_mppi"]) == 32


def test_unidentified_refuses_a_rung_that_would_otherwise_grade():
    """The new `admissible` clause is reachable on its own. Every existing
    refused rung also fails an older clause, so without this witness the third
    clause could be deleted with the suite still green."""
    import dataclasses as dc

    base = gn.HEADON_W75_NULL
    probe = dc.replace(base, ess_in_band=True, all_reached=True)
    assert probe.verdict_identification == gn.VERDICT_UNIDENTIFIED
    assert probe.admissible is False
    # ...and it is the *only* thing refusing it.
    assert dc.replace(probe, clearance_ladder=None).admissible is True


def test_unrecorded_ladder_does_not_refuse():
    """`UNRECORDED` is not a failure — a rule that refused it would turn
    "nobody measured" into "measured bad".

    Convoy carried this state until D-170 measured it. The rule is now pinned
    on a synthetic rung instead of on convoy, because a witness that only
    exists while some real rung stays unmeasured is a witness that disappears
    the moment the project does its job."""
    r = synthetic_rung((1.0,), (2.0,), (3.0,))
    assert r.clearance_ladder is None
    assert r.verdict_identification == "UNRECORDED"
    assert r.behavioural_response is None
    assert r.admissible is True


# --------------------------------------------------------------------------
# D-170: the census's one graded rung, asked the question that dissolved
# head_on's — on the scene where the ESS criterion demonstrably works
# --------------------------------------------------------------------------


def test_convoys_ess_criterion_actually_responds():
    """The precondition that makes this rung's refusal interesting. D-169's
    escape hatch for head_on was that the sampler is *blind* to `w_geom` there
    (1.7% response), so the criterion never had a chance. On convoy it has one:
    86.6% response, `IDENTIFIED`, 50× head_on's."""
    r = gn.CONVOY_W75_NULL
    assert r.coefficient_identification == "IDENTIFIED"
    assert r.ess_response > 8 * gn.FLAT_ESS_RESPONSE
    assert r.ess_response > 40 * gn.HEADON_W75_NULL.ess_response


def test_a_working_ess_criterion_still_does_not_identify_the_verdict():
    """The finding, and it is strictly stronger than D-169's.

    head_on could be dismissed as one scene where the instrument is broken.
    Here the instrument works — the ladder moves ESS by 86.6% of the target —
    and the verdict *still* flips across it, `REPRESENTATION_ADDS` at
    `w_geom ∈ {1, 2.5}` and `GEOMETRY_SUFFICES` from 5 up. So "ESS-matching
    identifies a coefficient" and "ESS-matching identifies a verdict" are
    different properties, and convoy has the first without the second."""
    r = gn.CONVOY_W75_NULL
    verdicts = r.ladder_verdicts
    assert gn.REPRESENTATION_ADDS in verdicts.values()
    assert gn.GEOMETRY_SUFFICES in verdicts.values()
    assert r.verdict_identification == gn.VERDICT_UNIDENTIFIED
    assert r.admissible is False


def test_the_refusal_does_not_rest_on_rungs_the_criterion_would_reject():
    """The obvious objection, pre-empted by measurement rather than by prose.

    `w_geom = 40` runs at median ESS 14.03 against a 96.36 target with 8/16 in
    band; counting its verdict would be answering an objection nobody made.
    Restricted to rungs that are ladder-admissible **and** match the target at
    least as well as the shipped 2.5, the disagreement survives — because the
    rung that flips it, `w_geom = 5`, is 16/16 in band and a *better* ESS match
    than the coefficient whose verdict got published."""
    r = gn.CONVOY_W75_NULL
    matched = r.matched_ladder
    assert set(matched) == {1.0, 2.5, 5.0}
    assert 40.0 not in matched and 20.0 not in matched
    assert r.matched_verdict_identification == gn.VERDICT_UNIDENTIFIED
    assert matched[5.0] == gn.GEOMETRY_SUFFICES


def test_the_calibration_did_not_pick_its_own_criterions_optimum():
    """A defect independent of the verdict spread, and invisible from the
    shipped `w_geom` alone: two coefficients match the ESS target strictly
    better than the 2.5 the reading was taken at, and the best of them says
    the opposite thing."""
    r = gn.CONVOY_W75_NULL
    assert r.better_matched == (1.0, 5.0)
    shipped = abs(r.ess_ladder[r.w_geom] - r.ess_target)
    best = min(abs(r.ess_ladder[w] - r.ess_target) for w in r.better_matched)
    assert best < shipped / 5
    assert r.ladder_verdicts[5.0] != r.ladder_verdicts[r.w_geom]


def test_the_ladder_reconciles_with_both_recorded_walks():
    """Two of the six rungs are cross-checks, not new data: the ladder's 2.5
    is the first 16 seeds of the 32-seed walk and its 5.0 is the first 16 of
    the refused `LOUDER_NULL`. Exact agreement is what makes this ladder and
    those walks one measurement rather than two that happen to point the same
    way."""
    lad = gn.CONVOY_W75_CLEARANCE_LADDER
    assert lad[2.5] == gn.NULL_CLEARANCES[:16]
    assert lad[5.0] == tuple(gn.LOUDER_NULL["clearances"])[:16]


def test_the_census_is_now_empty_and_says_so():
    """The consequence, and the reason this cycle is a retraction rather than
    a confirmation. Both walked rungs are refused, so the attribution census
    has an **empty denominator** — `NO_GRADED_RUNG`, not a tie, not a null
    result about the mechanism (D-107's shape). D-167's `residual_share =
    0.7725` is no longer a reading the census will quote."""
    c = gn.census()
    assert c.coverage == (0, 6)
    assert c.verdict == gn.NO_GRADED_RUNG
    assert set(c.verdict_unidentified) == {"cafe_convoy_v0.yaml@75",
                                           "cafe_head_on_v0.yaml@75"}
    assert c.graded == ()
    assert c.shares == {} and c.verdicts == {}


def test_matched_ladder_can_acquit_a_rung_the_full_ladder_refuses():
    """The restricted predicate has to be able to say `IDENTIFIED` where the
    unrestricted one does not, or it is not a distinction — it is the same
    refusal spelled twice. Synthetic, because no shipped rung is acquitted by
    it (D-107's rule: prove the branch is reachable rather than assume it)."""
    import dataclasses as dc

    r = gn.CONVOY_W75_NULL
    # Keep only the two rungs that agree inside the matched set, and push the
    # disagreeing one out of it by making its ESS match strictly worse.
    ess = dict(r.ess_ladder)
    ess[5.0] = 10.0
    probe = dc.replace(r, ess_ladder=ess)
    assert set(probe.matched_ladder) == {1.0, 2.5}
    assert probe.matched_verdict_identification == "IDENTIFIED"
    assert probe.verdict_identification == gn.VERDICT_UNIDENTIFIED


def test_ladder_admissibility_covers_the_recorded_ladder():
    """The admissibility table and the clearance table must name the same
    rungs, or `matched_ladder`'s filter silently defaults a missing rung to
    admissible — the permissive direction."""
    assert set(gn.CONVOY_W75_LADDER_ADMISSIBILITY) == set(
        gn.CONVOY_W75_CLEARANCE_LADDER)
    assert all(reached == 16
               for reached, _ in gn.CONVOY_W75_LADDER_ADMISSIBILITY.values())
    # Unlike head_on's, this ladder loses seeds as it climbs — the same
    # sampler response `coefficient_identification` reads, seen in the band.
    assert gn.CONVOY_W75_LADDER_ADMISSIBILITY[40.0][1] == 8
    assert all(n == 16 for _, n in
               gn.HEADON_W75_LADDER_ADMISSIBILITY.values())


def test_census_names_the_unidentified_rung_and_keeps_it_ungraded():
    """Coverage before verdict, D-168's rule, with the new refusal visible.
    An ungraded rung that the census does not *name* is a walk nobody can see
    was refused."""
    c = gn.census()
    assert "cafe_head_on_v0.yaml@75" in c.verdict_unidentified
    assert gn.HEADON_W75_NULL not in c.graded
    assert c.coverage == (0, 6)
    assert c.verdict == gn.NO_GRADED_RUNG


def test_unidentified_is_stronger_than_quiet_null_exposure():
    """The two are different readings of the same worry and the census reports
    both. `exposed_to_quiet_null` lists graded rungs where a flat ladder
    leaves a win *open* to the objection; `verdict_unidentified` lists rungs
    where the ladder was walked and the objection is realised. Convoy sits in
    neither: it is graded and its ladder was never asked."""
    c = gn.census()
    assert c.exposed_to_quiet_null == ()
    assert c.verdict_unidentified != ()
    assert set(c.verdict_unidentified) & set(c.exposed_to_quiet_null) == set()
