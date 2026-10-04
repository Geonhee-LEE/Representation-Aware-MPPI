"""D-514: head_on's attractor-off regression is a cheap retreat, priced away.

D-512 found that `w_progress=10` with the goal gate closed makes head_on back up
behind its start (T 9.9 -> 42.1 s). Cause: the progress reward is symmetric, so
a rollout that ends 1 m behind `s_robot` costs only `w_progress * 1 m`, and that
is cheaper than the barrier cost of the oncoming pedestrian. `retreat_gain`
charges backward rollouts `retreat_gain` x the forward rate.

Knee+shape band 0.30, seeds 0-15, each scene's yaml acceptance, measured
2026-10-04 20:00:

    scene              w10                  w10 + retreat_gain 100
    head_on            0/16  T 42.1 s       0/16  T 12.3 s  (fast 16/16)
    crossing           16/16 T 17.8 s       16/16 T 17.8 s
    curved             16/16 cte .030       16/16 cte .030
    city_figure8_v1    16/16 T 25.0 s       16/16 T 25.0 s
    convoy / freezing / contested / straight: 16/16, identical

Gain ladder on head_on (T median, runs with T < 20 s): k=1 40.4 s 6/16,
k=10 13.9 s 12/16, k=100 12.3 s 16/16. head_on still fails on
min_distance_to_obstacle, same as with the attractor on (w0).

Extending the first segment backward, so points behind the start read negative
arclength, was also tried: 42.1 -> 40.4 s. The window clip at `s_robot - back`
was not the cause. The retreat price was.

Cost: 2 integrations.
"""
import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.critics import ArclengthProgressCritic
from eval.mppi_sandbox.scenario import load_scenario

HEAD_ON = "eval/scenarios/cafe_head_on_v0.yaml"
BAND = 0.30
PATH = np.array([[0.0, 0.0], [0.0, -4.0]])


def _rollouts(end_y):
    traj = np.zeros((len(end_y), 3, 2))
    traj[:, -1, 1] = end_y
    return traj


def test_retreat_gain_is_inert_at_default():
    c = ArclengthProgressCritic(PATH, w_progress=10.0)
    assert c.retreat_gain == 1.0
    c.s_robot = 1.0
    np.testing.assert_allclose(c.cost(_rollouts([-1.5, -0.6])), [-5.0, 4.0])


def test_retreat_gain_scales_only_backward_rollouts():
    c = ArclengthProgressCritic(PATH, w_progress=10.0, retreat_gain=100.0)
    c.s_robot = 1.0
    np.testing.assert_allclose(c.cost(_rollouts([-1.5, -1.0, -0.6])),
                               [-5.0, 0.0, 400.0])


@pytest.fixture(scope="module")
def head_on():
    sc = load_scenario(HEAD_ON)
    p = MPPIParams(collision_margin=BAND, obs_barrier_band=BAND)
    out = {}
    for key, k in (("k1", 1.0), ("k100", 100.0)):
        r = ab.run_arm(sc, "stock_mppi", 1, params=p, w_progress=10.0,
                       progress_retreat_gain=k)
        out[key] = (r.traj, sc.goal)
    return out


def _ttg(traj, goal, tol=0.2):
    d = np.hypot(traj[:, 1] - goal[0], traj[:, 2] - goal[1])
    hit = np.flatnonzero(d <= tol)
    return float(traj[hit[0], 0]) if hit.size else float("inf")


def test_retreat_price_removes_the_head_on_retreat(head_on):
    t1, t100 = _ttg(*head_on["k1"]), _ttg(*head_on["k100"])
    assert t1 > 35.0                                        # seed 1: 43.4 s
    assert head_on["k1"][0][:, 2].max() > 1.0               # behind its start
    assert t100 < 20.0
    assert head_on["k100"][0][:, 2].max() < 0.5
