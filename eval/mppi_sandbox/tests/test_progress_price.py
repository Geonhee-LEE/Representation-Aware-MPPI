# SPDX-License-Identifier: BSD-3-Clause
"""`ProgressPriceCritic` — the freeze, priced (D-243).

Three classes of pin, in descending order of what they protect:

1. **The ablation invariant.** `w_freeze = 0` must leave every arm
   byte-identical to the run recorded before this term existed. Every other
   critic in this package holds the same invariant and it is the reason a
   default-on regression cannot hide inside a shipped number.
2. **The shared threshold.** The cost term and the acceptance key it exists to
   move must define "stalled" with one constant. A future edit to
   `freeze_price.STALL_SPEED_MPS` has to move the price with the metric.
3. **The arithmetic**, including the direction nobody tests: a rollout that
   makes progress pays *exactly* zero, not merely little.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.critics import ProgressPriceCritic, arclength_along
from eval.mppi_sandbox.freeze_price import (
    FREEZING_SCENE,
    STALL_SPEED_MPS,
    freeze_duration,
)
from eval.mppi_sandbox.run import ROBOT_RADIUS, simulate
from eval.mppi_sandbox.scenario import load_scenario
from eval.path_tracking_metrics import completion_percent

DT = 0.1
STRAIGHT = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]])

#: The temperature every simulated claim below was measured at. Named rather
#: than inherited from `MPPIParams.lam` because these tests assert on
#: *trajectory* magnitudes — a freeze duration and a byte-identity — and a site
#: that leaves the rung implicit is asserting about a temperature it never
#: chose (`test_default_lam_sites`' `defaults` column, D-124's pattern). The
#: value is the shipped default, which is what D-243's sweep was run at.
LAM = 0.1


def _rollouts(speeds_per_k: list[list[float]], x0: float = 0.0) -> np.ndarray:
    """(K,H,5) rollouts advancing along +x from `x0` at the given speeds."""
    K, H = len(speeds_per_k), len(speeds_per_k[0])
    traj = np.zeros((K, H, 5))
    for k, speeds in enumerate(speeds_per_k):
        traj[k, :, 0] = x0 + np.cumsum(np.array(speeds) * DT)
    return traj


# --------------------------------------------------------------- arclength


def test_arclength_matches_the_looping_reference():
    """The vectorised projection must agree with `completion_percent`.

    That function is the one `freeze_duration` measures through, so a
    disagreement here is the price and the metric reading different geometry.
    """
    path = np.array([[0.0, 0.0, 0.0], [3.0, 0.0, 0.0], [3.0, 4.0, 0.0]])
    pts = np.array([[0.0, 0.0], [1.5, 0.2], [3.0, 0.0], [3.1, 2.0], [3.0, 4.0]])

    rows = np.zeros((len(pts), 6))
    rows[:, 1:3] = pts
    expected = completion_percent(rows, path) * 7.0        # 3 + 4 total length

    assert arclength_along(pts, path[:, :2]) == pytest.approx(expected, abs=1e-9)


def test_arclength_is_clamped_to_the_polyline_ends():
    """A point past the end projects onto the end, not beyond it."""
    got = arclength_along(np.array([[20.0, 0.0], [-5.0, 0.0]]), STRAIGHT[:, :2])
    assert got[0] == pytest.approx(10.0)
    assert got[1] == pytest.approx(0.0)


# ------------------------------------------------------- ablation invariant


def test_zero_weight_costs_exactly_zero():
    """Not 'small' — zero. The ablation invariant is exact or it is nothing."""
    traj = _rollouts([[0.0] * 10, [0.5] * 10])
    cost = ProgressPriceCritic(0.0).cost(traj, STRAIGHT[:, :2], DT)
    assert cost.shape == (2,)
    assert np.array_equal(cost, np.zeros(2))


def test_default_weight_is_off():
    assert ProgressPriceCritic().w_freeze == 0.0


def test_shipped_arms_are_byte_identical_with_the_term_defaulted_off():
    """The invariant that matters: no shipped arm's commands moved.

    Compares against the term physically absent (`progress` replaced by a
    zero-returning stub), not against `w_freeze = 0`, so this fails if the
    default ever flips as well as if the arithmetic leaks.
    """
    scen = load_scenario(FREEZING_SCENE)
    for arm in ("stock_mppi", "risk_mppi", "social_mppi"):
        live = make_controller(arm, scen, seed=0, robot_radius=ROBOT_RADIUS,
                               params=MPPIParams(lam=LAM))
        stub = make_controller(arm, scen, seed=0, robot_radius=ROBOT_RADIUS,
                               params=MPPIParams(lam=LAM))
        stub.progress.cost = lambda *a, **k: np.zeros(stub.p.samples)
        assert np.array_equal(simulate(scen, live), simulate(scen, stub)), \
            f"{arm} moved with the freeze price defaulted off"


# ------------------------------------------------------- shared threshold


def test_stall_threshold_is_the_metrics_own_constant():
    """One definition of 'stalled', shared by the price and the acceptance key.

    `freeze_duration` grades against `STALL_SPEED_MPS`; a critic that charged a
    different threshold would be optimising a quantity the scene does not
    grade. `freeze_price` in turn pins that constant to `StockMPPI.creep_speed`,
    so this is the second link of a chain, not a free constant.
    """
    assert ProgressPriceCritic(1.0).stall_speed == STALL_SPEED_MPS


# --------------------------------------------------------------- arithmetic


def test_progress_at_the_threshold_is_free():
    """The hinge is one-sided: a healthy rollout pays nothing at all."""
    at_threshold = _rollouts([[STALL_SPEED_MPS] * 10])
    faster = _rollouts([[0.6] * 10])
    critic = ProgressPriceCritic(1.0e4)
    assert critic.cost(at_threshold, STRAIGHT[:, :2], DT) == pytest.approx(0.0)
    assert critic.cost(faster, STRAIGHT[:, :2], DT) == pytest.approx(0.0)


def test_a_stopped_rollout_pays_the_full_deficit():
    """Fully stopped ⇒ the deficit is the whole threshold step, each step, squared."""
    traj = _rollouts([[0.0] * 10])
    got = ProgressPriceCritic(3.0).cost(traj, STRAIGHT[:, :2], DT)
    expected = 3.0 * 9 * (STALL_SPEED_MPS * DT) ** 2      # 9 diffs, no start_xy
    assert got == pytest.approx(expected)


def test_the_start_position_adds_the_first_step():
    """Without `start_xy` the term cannot see a plan that stops immediately."""
    traj = _rollouts([[0.0] * 10])
    critic = ProgressPriceCritic(3.0)
    without = critic.cost(traj, STRAIGHT[:, :2], DT)
    with_start = critic.cost(traj, STRAIGHT[:, :2], DT, np.array([0.0, 0.0]))
    assert with_start == pytest.approx(without * 10.0 / 9.0)


def test_reversing_costs_more_than_standing_still():
    """Backing up is worse than a stall and the deficit is not clipped."""
    critic = ProgressPriceCritic(1.0)
    stopped = critic.cost(_rollouts([[0.0] * 10], x0=5.0), STRAIGHT[:, :2], DT)
    reversing = critic.cost(_rollouts([[-0.3] * 10], x0=5.0), STRAIGHT[:, :2], DT)
    assert reversing[0] > stopped[0]


def test_reversing_off_the_start_of_the_path_reads_as_a_stall():
    """A known edge of measuring progress as *projected* arclength.

    Arclength is clamped to the polyline, so a rollout reversing past the path's
    start has nowhere further to go and prices identically to one standing still
    there. Pinned rather than fixed: the metric this term is graded against
    (`freeze_duration`, via `completion_percent`) clamps the same way, so
    un-clamping the price alone would make it optimise a quantity the scene does
    not grade — the one thing this critic is built not to do.
    """
    critic = ProgressPriceCritic(1.0)
    stopped = critic.cost(_rollouts([[0.0] * 10]), STRAIGHT[:, :2], DT)
    reversing = critic.cost(_rollouts([[-0.3] * 10]), STRAIGHT[:, :2], DT)
    assert reversing[0] == pytest.approx(stopped[0])


def test_cost_is_monotone_in_the_weight():
    traj = _rollouts([[0.0] * 10])
    path = STRAIGHT[:, :2]
    costs = [ProgressPriceCritic(w).cost(traj, path, DT)[0]
             for w in (1.0, 10.0, 100.0)]
    assert costs[0] < costs[1] < costs[2]


# ------------------------------------------------- the measured claim (D-243)


@pytest.mark.parametrize("seed", (0, 1, 2))
def test_the_priced_arm_clears_the_scenes_own_limit(seed):
    """The cycle's claim, re-measured: `social_mppi` at `w_freeze = 1e4` stops
    exceeding `cafe_freezing_v0`'s declared 2.0 s limit, on every seed it was
    measured on — where the same arm at `w_freeze = 0` exceeded on 2 of 3.

    This is the deliverable's grade, so it is pinned rather than left in a
    journal paragraph. It is also the slowest test here (~1 s/seed); the
    baseline half is not re-simulated because `test_freeze_duration.py` already
    covers the metric, and this test's subject is the price.
    """
    scen = load_scenario(FREEZING_SCENE)
    ctrl = make_controller("social_mppi", scen, seed=seed,
                           robot_radius=ROBOT_RADIUS, w_freeze=1.0e4,
                           params=MPPIParams(lam=LAM))
    traj = simulate(scen, ctrl)

    limit = scen.acceptance["freeze_duration_max"]
    assert freeze_duration(traj, scen.waypoints) <= limit
    assert completion_percent(traj, scen.waypoints)[-1] >= 0.99, \
        "the price must not buy freeze by failing to arrive"
