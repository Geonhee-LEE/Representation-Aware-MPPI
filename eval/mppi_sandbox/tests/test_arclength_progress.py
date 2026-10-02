"""ArclengthProgressCritic (D-511): windowed, monotone progress on a figure-8.

The D-243 freeze price projects onto the nearest segment, so on city_figure8_v1
the shortcut from start to goal reads as ~15 m of progress. These tests pin
that aliasing, that the windowed projection removes it, and that the term is
inert at its default.
"""
import numpy as np

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.critics import (ArclengthProgressCritic,
                                       arclength_along, arclength_windowed)
from eval.mppi_sandbox.scenario import load_scenario

SCENE = "eval/scenarios/variants/city_figure8_v1.yaml"


def _path():
    return load_scenario(SCENE).waypoints[:, :2]


def test_nearest_projection_reads_the_shortcut_as_progress():
    path = _path()
    goal = path[-1:]
    assert arclength_along(goal, path)[0] > 15.0       # aliasing D-511 fixes


def test_windowed_projection_refuses_the_shortcut():
    path = _path()
    s = arclength_windowed(path[-1:], path, -0.5, 3.5)[0]
    assert s <= 3.5                                     # cannot claim the end


def test_robot_arclength_is_monotone_through_the_crossing():
    path = _path()
    c = ArclengthProgressCritic(path, w_progress=1.0)
    s_prev = 0.0
    # Walk the waypoints densely; s_robot must rise, never jump to the far lobe.
    for a, b in zip(path[:-1], path[1:]):
        for t in np.linspace(0.0, 1.0, 5):
            s = c.update(a + t * (b - a))
            assert s >= s_prev and s - s_prev < 0.6
            s_prev = s
    assert s_prev > 0.95 * c.length


def test_goal_gate_closed_until_near_the_end():
    c = ArclengthProgressCritic(_path(), w_progress=1.0, goal_gate=3.0)
    assert c.goal_gate() == 0.0
    c.s_robot = c.length - 2.0
    assert c.goal_gate() == 1.0


def test_inert_at_default():
    c = ArclengthProgressCritic(_path())
    assert c.goal_gate() == 1.0
    assert c.update(np.array([0.0, 0.0])) == 0.0
    assert not c.cost(np.zeros((4, 3, 5))).any()


def test_default_stock_mppi_command_is_unchanged_by_the_wiring():
    sc = load_scenario(SCENE)
    state = np.array([*sc.start, 0.0, 0.0])
    a = make_controller("stock_mppi", sc, seed=3).command(state, 0.0)
    b = make_controller("stock_mppi", sc, seed=3, w_progress=0.0).command(state, 0.0)
    np.testing.assert_array_equal(a, b)


def test_progress_term_drives_the_figure8_loop_and_passes():
    # Measured 2026-10-02 (D-511), city_figure8_v1 x seeds 0-3: stock 0/4
    # (heading rms 2.20-2.53, shortcut); w_progress=10 4/4 (cte_rms 0.020-0.022,
    # heading rms 0.10-0.14, 25.9-27.0 s); 30 4/4; 100 4/4; 300 0/1 (seed 0).
    from eval.mppi_sandbox.run import run_scenario
    r = run_scenario(SCENE, seed=0, w_progress=10.0)
    assert r["pass"] is True
    assert r["metrics"]["heading_err_rms"] < 0.2
    assert r["metrics"]["cte_rms"] < 0.05
