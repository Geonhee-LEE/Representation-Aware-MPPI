"""The structural null: `RiskMPPI` minus the motion model, same coefficient.

Two calibrated nulls failed in opposite directions (D-169/D-170 under-identify
the verdict, D-171 determines it), which indicts the *form* — a swap that buys
a coefficient must then answer "how loud", and both answers were bad. This arm
does not buy a coefficient. These tests hold it to that, mechanically, because
"there is no coefficient to calibrate" is exactly the kind of claim that is
true of a docstring and false of an object.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import structural_null as sn
from eval.mppi_sandbox.controllers import REGISTRY, make_controller
from eval.mppi_sandbox.controllers.frozen_risk_mppi import FrozenRiskMPPI
from eval.mppi_sandbox.controllers.risk_mppi import RiskMPPI
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.representations import (FrozenBevProducer,
                                               GTBevProducer, RiskChannel)
from eval.mppi_sandbox.scenario import load_scenario

CONVOY = "eval/scenarios/cafe_convoy_v0.yaml"

#: The walked rung's operating point, named rather than inherited from
#: `MPPIParams.lam = 0.1` — `default_lam_sites` charges a test that leaves the
#: temperature implicit, because such a test asserts about the shipped default
#: instead of about the rung (D-124/D-126).
#:
#: The constructor is repeated verbatim at all 20 call sites rather than
#: factored into a `params()` helper. That is not style: `_classify` requires a
#: **literal** `MPPIParams(...)` at the call site, so the helper spelling billed
#: `forwards` 23 → **43** while naming nothing — the census charges for the
#: indirection, not for the ignorance (D-072's syntax result, recorded again by
#: `test_default_lam_sites`'s own docstring). Inlining moves all 20 to
#: `decides`, which is also the honest category: every site here is a claim
#: about the walked rung's operating point.
LAM, W_OBS = 0.8, 75.0


@pytest.fixture(scope="module")
def convoy():
    return load_scenario(CONVOY)


def moving_obstacle() -> CircleObstacle:
    """One obstacle that actually goes somewhere.

    A *static* obstacle would make every assertion in this file pass for the
    wrong reason: with no motion, the swept render and the frozen one agree by
    construction and "prediction removed" would be indistinguishable from
    "prediction present". The schedule is what makes the ablation observable.
    """
    return CircleObstacle(x=2.0, y=0.0, radius=0.3,
                          schedule=np.array([[0.0, 2.0, 0.0],
                                             [4.0, 2.0, 3.0]]))


# ---------------------------------------------------------------- producer


def test_frozen_producer_renders_the_blob_at_t_and_not_along_the_sweep():
    """Pinned against a hand-computed blob, not against `GTBevProducer`.

    Comparing the two producers to each other would pass if both drifted the
    same way. The frozen DYNAMIC row has a closed form — one Gaussian at
    `ob.position(t)` with `sigma = blob_scale * radius`, undecayed — so it is
    checked against that instead.
    """
    ob = moving_obstacle()
    t = 1.0
    prod = FrozenBevProducer([ob], blob_scale=1.5)
    pos = np.asarray(ob.position(np.array([t])), dtype=float)[0]
    # Viewpoint chosen so the probes sit *lateral* to the line of sight rather
    # than behind the obstacle — otherwise the occlusion shadow, which is not
    # what this test is about, decides the answer.
    robot = pos - np.array([2.0, 0.0])
    bev = prod.render(robot, t)

    sig = 1.5 * ob.radius
    probes = pos + np.stack([np.array([0.0, d]) for d in
                             (0.0, 0.2, 0.4, 0.8)])
    got = bev.sample(RiskChannel.DYNAMIC, probes, unobserved_value=np.nan)
    want = np.exp(-0.5 * (np.linalg.norm(probes - pos, axis=1) / sig) ** 2)

    seen = ~np.isnan(got)
    assert seen.any(), "probes fell entirely in unobserved cells"
    # Grid quantisation (0.125 m cells) is the only source of error here.
    assert np.allclose(got[seen], want[seen], atol=0.15)


def test_frozen_producer_is_blind_to_where_the_obstacle_is_going():
    """The whole ablation, stated as a difference the sweep can see.

    Ahead of a moving obstacle, `GTBevProducer` paints predicted-sweep risk and
    the frozen producer paints (almost) none. If this ever ties, the "frozen"
    arm is rendering a prediction and every downstream reading is a comparison
    of an arm with itself.
    """
    ob = moving_obstacle()
    t = 0.0
    # Viewpoint lateral to the obstacle's travel, so the probe ahead of it is
    # in line of sight and the reading is about prediction, not occlusion.
    robot = np.array([0.0, 1.5])
    swept = GTBevProducer([ob], blob_scale=1.5).render(robot, t)
    frozen = FrozenBevProducer([ob], blob_scale=1.5).render(robot, t)

    # A point on the obstacle's future path, well clear of where it is now.
    ahead = np.array([[2.0, 1.5]])
    s = swept.sample(RiskChannel.DYNAMIC, ahead, unobserved_value=0.0)
    f = frozen.sample(RiskChannel.DYNAMIC, ahead, unobserved_value=0.0)
    assert s[0] > f[0] + 0.1, (s[0], f[0])


def test_frozen_producer_leaves_every_other_channel_alone():
    """STATIC / EPISTEMIC / TRAVERSABILITY are not part of the ablation."""
    obs = [moving_obstacle(), CircleObstacle(x=1.0, y=1.0, radius=0.3)]
    robot, t = np.array([0.0, 0.0]), 0.7
    swept = GTBevProducer(obs, blob_scale=1.5).render(robot, t)
    frozen = FrozenBevProducer(obs, blob_scale=1.5).render(robot, t)
    for ch in (RiskChannel.STATIC, RiskChannel.EPISTEMIC,
               RiskChannel.TRAVERSABILITY, RiskChannel.ALEATORIC):
        assert np.array_equal(swept.stack[ch], frozen.stack[ch]), ch
        assert np.array_equal(swept.mask[ch], frozen.mask[ch]), ch


def test_prediction_samples_is_not_a_constructor_knob():
    """A caller must not be able to restore prediction on a `Frozen*` object.

    Accepted-and-ignored rather than rejected, so kwargs transplanted from a
    `GTBevProducer` call site do not raise — but the value cannot take effect.
    """
    prod = FrozenBevProducer([moving_obstacle()], predict_samples=10)
    assert prod.n_pred == 1


# ------------------------------------------------------------- controller


def test_frozen_arm_is_registered_and_constructible(convoy):
    assert REGISTRY["frozen_risk_mppi"] is FrozenRiskMPPI
    ctrl = make_controller("frozen_risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    assert isinstance(ctrl.producer, FrozenBevProducer)
    assert isinstance(ctrl, RiskMPPI)   # consuming path is inherited verbatim


def test_frozen_arm_keeps_the_risk_arms_shipped_weight(convoy):
    """The point of the construction: `w_risk` is not re-chosen here."""
    risk = make_controller("risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    frozen = make_controller("frozen_risk_mppi", convoy, seed=0,
                             params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    assert frozen.w_risk == risk.w_risk == 40.0


def test_ablation_invariant_zero_weight_matches_stock(convoy):
    """Inherited from `RiskMPPI`, re-pinned here — a subclass can break it."""
    stock = make_controller("stock_mppi", convoy, seed=3, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    frozen = make_controller("frozen_risk_mppi", convoy, seed=3,
                             params=MPPIParams(lam=LAM, w_obs_soft=W_OBS), w_risk=0.0)
    state = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
    for t in (0.0, 0.5, 1.0):
        assert np.array_equal(stock.command(state, t), frozen.command(state, t))


def test_frozen_arm_is_no_louder_than_the_risk_arm(convoy):
    """The predicted cost of having no knob, asserted rather than assumed.

    `GTBevProducer`'s DYNAMIC row is a max over `predict_samples` blobs and the
    frozen one is a single member of that max, so at equal `w_risk` the frozen
    arm's extra cost is pointwise ≤ the risk arm's. That is why an ESS refusal
    on a walked rung would be `LOUDNESS_UNCALIBRATABLE` and not a bad
    coefficient choice — there is no coefficient, and the direction of the
    shortfall is structural.
    """
    risk = make_controller("risk_mppi", convoy, seed=1, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    frozen = make_controller("frozen_risk_mppi", convoy, seed=1,
                             params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    state = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
    t = 0.6
    for ctrl in (risk, frozen):
        ctrl.command(state, t)          # populates `_bev`
    traj = np.zeros((4, 3, 5))
    traj[..., :2] = np.array([[[0.5, 0.0], [1.0, 0.0], [1.5, 0.0]],
                              [[0.5, 0.3], [1.0, 0.5], [1.5, 0.8]],
                              [[0.2, 0.0], [0.4, 0.0], [0.6, 0.0]],
                              [[1.0, 1.0], [1.4, 1.2], [1.8, 1.4]]])
    c_risk = risk._extra_cost(traj, t)
    c_frozen = frozen._extra_cost(traj, t)
    assert np.all(c_frozen <= c_risk + 1e-9), (c_frozen, c_risk)


# ------------------------------------------------------------------ screen


def test_screen_passes_on_the_shipped_pair(convoy):
    """`STRUCTURAL_ABLATION` — the precondition D-170/D-171 could not meet."""
    risk = make_controller("risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    frozen = make_controller("frozen_risk_mppi", convoy, seed=0,
                             params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    s = sn.screen(risk, frozen)
    assert s.parity.verdict == "COEFFICIENTS_SHARED", s.parity.values
    assert s.prediction.verdict == "PREDICTION_REMOVED"
    assert s.verdict == "STRUCTURAL_ABLATION"
    assert s.well_posed


def test_screen_catches_a_calibrated_null_wearing_a_structural_label(convoy):
    """Turn one knob and the screen must stop calling it structural.

    This is the failure the module exists to prevent: a future cycle 'fixing'
    an ESS refusal by nudging `w_risk` would silently convert this arm into a
    third calibrated null, re-acquiring both prior failure modes.
    """
    risk = make_controller("risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    frozen = make_controller("frozen_risk_mppi", convoy, seed=0,
                             params=MPPIParams(lam=LAM, w_obs_soft=W_OBS), w_risk=25.0)
    s = sn.screen(risk, frozen)
    assert s.parity.verdict == "COEFFICIENTS_DIVERGED"
    assert "w_risk" in s.parity.diverged
    assert s.parity.values["w_risk"] == (40.0, 25.0)
    assert not s.well_posed


def test_screen_catches_a_temperature_difference(convoy):
    """λ is a calibration too — D-160 calibrates it per scene."""
    risk = make_controller("risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    frozen = make_controller("frozen_risk_mppi", convoy, seed=0,
                             params=MPPIParams(lam=1.6, w_obs_soft=W_OBS))
    s = sn.screen(risk, frozen)
    assert "p.lam" in s.parity.diverged


def test_parity_alone_is_not_the_screen(convoy):
    """An arm compared to itself has perfect parity and ablates nothing.

    The conjunction is the whole point: without this half, `screen` would
    certify a no-op as a structural ablation.
    """
    risk = make_controller("risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    twin = make_controller("risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    s = sn.screen(risk, twin)
    assert s.parity.verdict == "COEFFICIENTS_SHARED"
    assert s.prediction.verdict == "PREDICTION_PRESENT"
    assert not s.well_posed


def test_screen_catches_a_multivariate_producer_swap(convoy):
    """Removing prediction *and* shrinking the sensing range is two variables."""
    risk = make_controller("risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    frozen = make_controller(
        "frozen_risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS),
        producer=FrozenBevProducer(convoy.obstacles, sensing_range=2.0))
    s = sn.screen(risk, frozen)
    assert s.prediction.verdict == "PRODUCER_MULTIVARIATE"
    assert "r_sense" in s.prediction.other_diffs
    assert not s.well_posed


def test_screen_reports_no_producer_rather_than_guessing(convoy):
    """`StockMPPI` has no producer — that is a third state, not a False."""
    stock = make_controller("stock_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    risk = make_controller("risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    assert sn.prediction_parity(risk, stock).verdict == "NO_PRODUCER"


def test_parity_distinguishes_absent_from_zero(convoy):
    """`StockMPPI` has no `w_risk`; `RiskMPPI(w_risk=0)` has one set to zero.

    Collapsing these would let 'the term does not exist' pass a check that
    means 'the term is switched off', which is how an ablation invariant gets
    proved against the wrong object.
    """
    stock = make_controller("stock_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS))
    off = make_controller("risk_mppi", convoy, seed=0, params=MPPIParams(lam=LAM, w_obs_soft=W_OBS),
                          w_risk=0.0)
    reading = sn.coefficient_parity(stock, off)
    assert "w_risk" in reading.diverged
    assert reading.values["w_risk"] == (None, 0.0)
