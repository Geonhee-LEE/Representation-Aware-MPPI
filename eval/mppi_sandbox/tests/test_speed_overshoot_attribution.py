# SPDX-License-Identifier: BSD-3-Clause
"""Q-045: what makes the closed loop depart from `target_speed_mps`? (D-024)

D-022 reported "the controller does not track `target_speed_mps`" and D-023
had to declare a timing band because of it. Q-045 offered three candidate
defects: (a) the scenario setting, (b) the cost weights, (c) a missing
speed-tracking term. These tests settle all three on measured input, and pin
the two things a later cycle would otherwise get wrong: that the **overshoot
ratio is an artifact of the declaration** (a), and that the obvious closed-form
predictor for the cruise speed is **refuted** (b's mechanism).

Cost discipline: every simulating test shares `_response` through a
module-level cache, so each (weights, target, v_max) cell is paid for once.
"""

from __future__ import annotations

import copy
from functools import lru_cache

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams, StockMPPI
from eval.mppi_sandbox.scenario import load_scenario
from eval.mppi_sandbox.speed_audit import (
    D_RAMP_M,
    T_TRANSIENT_S,
    TARGET_SPEED_INERTNESS,
    analytic_cruise_speed,
    cruise_speed,
    overshoot_ratio,
    speed_response,
)

SCENE = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
SEEDS = range(3)


@lru_cache(maxsize=None)
def _scen(target_speed: float | None = None):
    s = load_scenario(SCENE)
    if target_speed is not None:
        s = copy.copy(s)
        s.target_speed = target_speed
    return s


@lru_cache(maxsize=None)
def _response(w_terminal: float = 30.0, w_speed: float = 2.0,
              target_speed: float | None = None, v_max: float | None = None):
    return speed_response(
        _scen(target_speed), seeds=SEEDS, v_max=v_max,
        params=MPPIParams(w_terminal=w_terminal, w_speed=w_speed))


# --------------------------------------------------------------- Q-045 (c)

def test_speed_tracking_term_exists_in_the_shipped_objective():
    """(c) is false by inspection — the term has always been there."""
    assert "w_speed" in StockMPPI._cost.__code__.co_names
    assert MPPIParams().w_speed > 0.0


def test_speed_term_is_live_not_merely_present():
    """Presence is not enough: raising `w_speed` alone must move the loop.

    Guards the weaker reading of (c) — "there is a term but it does nothing".
    D-021 found exactly that failure mode for `w_epist` (per-sample spread
    exactly 0, so any weight is a softmax no-op), so it has to be excluded here
    rather than assumed.
    """
    shipped = _response()
    heavy = _response(w_speed=60.0)
    assert heavy.all_reached and shipped.all_reached
    assert heavy.mean_speed < 0.8 * shipped.mean_speed


# --------------------------------------------------------------- Q-045 (a)

@pytest.mark.parametrize("target", sorted(TARGET_SPEED_INERTNESS))
def test_declared_target_speed_is_nearly_inert(target):
    """(a) is false: a 4x sweep of the declaration moves realized speed ~3%.

    The declared target reaches the controller only through the warm start
    `U[:, 0]` and the `v_ref` cap, and neither survives the first few updates.
    Tolerance is loose (20%) because the claim is *inertness*, and a loose
    bound that still excludes proportionality is the honest way to state it:
    tracking would require the realized speed to move 4x across this sweep.
    """
    measured = _response(target_speed=target).mean_speed
    assert measured == pytest.approx(TARGET_SPEED_INERTNESS[target], rel=0.20)


def test_realized_speed_does_not_scale_with_the_declaration():
    """The sharp form: 4x in, < 1.25x out."""
    speeds = [_response(target_speed=t).mean_speed
              for t in sorted(TARGET_SPEED_INERTNESS)]
    assert max(speeds) / min(speeds) < 1.25, speeds


def test_overshoot_ratio_is_an_artifact_of_the_declaration():
    """The same controller on the same scene *undershoots* at target = 0.6.

    This is what voids "the loop overshoots `target_speed_mps` by 1.8x" as a
    controller property: the ratio straddles 1.0 under a change to a yaml field
    the loop does not read. D-022's observation stands; its attribution does
    not.
    """
    fast_decl = overshoot_ratio(_response(target_speed=0.60), _scen(0.60))
    slow_decl = overshoot_ratio(_response(target_speed=0.15), _scen(0.15))
    assert fast_decl < 1.0 < slow_decl
    assert slow_decl / fast_decl > 3.0


# --------------------------------------------------------------- Q-045 (b)

def test_terminal_weight_is_the_cause():
    """Removing the terminal term collapses the speed — the kill direction."""
    shipped = _response()
    killed = _response(w_terminal=0.0)
    assert killed.all_reached
    assert killed.mean_speed < 0.5 * shipped.mean_speed


def test_both_directions_reduce_the_departure():
    """D-018 discipline: a cause has to be demonstrated from both sides.

    Lowering `w_terminal` and raising `w_speed` are different interventions on
    the same ratio; if only one moved the loop, the other term would be a
    bystander and the mechanism claim would be unsupported.
    """
    shipped = _response().mean_speed
    assert _response(w_terminal=0.0).mean_speed < shipped
    assert _response(w_speed=60.0).mean_speed < shipped


def test_neither_intervention_buys_the_speed_back_by_stalling():
    """A slower arm that never finishes is not evidence about speed control."""
    for cell in (_response(w_terminal=0.0), _response(w_speed=60.0)):
        assert cell.all_reached
        assert not np.isnan(cell.cruise_speed)


# ------------------------------------------------- the refuted closed form

def test_analytic_stationary_point_is_refuted():
    """Pin the disagreement so the closed form is not re-derived and believed.

    Measured cruise sits well above the one-segment optimum near the goal. The
    controller runs at ESS ~ 1.5 of K = 256, where the update is
    argmin-over-draws rather than a step toward any stationary point.
    """
    scen = _scen()
    runs = ab.seed_sweep(scen, "stock_mppi", SEEDS)
    traj = runs[0].traj
    d_goal = np.linalg.norm(traj[:, ab.COL_XY] - scen.goal[:2], axis=1)
    live = (traj[:, 0] >= T_TRANSIENT_S) & (d_goal >= D_RAMP_M) & (d_goal < 2.0)
    assert live.sum() >= 3

    measured = float(np.median(traj[live, ab.COL_V]))
    predicted = analytic_cruise_speed(float(d_goal[live].mean()),
                                      scen.target_speed)
    assert measured > 1.3 * predicted, (measured, predicted)


def test_ess_explains_why_the_closed_form_fails():
    """The premise the closed form needs — that MPPI optimises its cost."""
    r = _response()
    assert r.median_ess < 5.0, r.median_ess


# ------------------------------------------------------ the right statistic

def test_cruise_speed_excludes_both_end_regimes():
    """`mean_speed` averages transient + cruise + goal ramp; cruise does not."""
    scen = _scen()
    traj = ab.run_arm(scen, "stock_mppi", 0).traj
    assert cruise_speed(traj, scen) > ab.mean_speed(traj)


def test_cruise_speed_is_nan_for_a_stalled_run():
    """A stalled arm has no cruise speed and must not be credited with one."""
    scen = _scen()
    traj = ab.run_arm(scen, "stock_mppi", 0).traj
    assert np.isnan(cruise_speed(traj, scen, t_transient=1e9))


def test_v_max_binds_below_the_weight_ratio():
    """The operative ceiling is `min(v_max, f(w_terminal / w_speed))`.

    Q-045's option set named neither. At `v_max = 0.4` the limit binds (cruise
    tracks it); at 0.8 the ratio does. `target_speed_mps = 0.3` is below both
    and is not the ceiling in either regime.
    """
    tight = _response(v_max=0.4)
    loose = _response()
    assert tight.cruise_speed <= 0.4 + 1e-9
    assert tight.cruise_speed > 0.7 * 0.4
    assert loose.cruise_speed > 0.5
    assert loose.cruise_speed > _scen().target_speed
