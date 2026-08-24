# SPDX-License-Identifier: BSD-3-Clause
"""The obstacle excitation channel — D-361 finding #1's unmeasured half."""

from __future__ import annotations

import math

import numpy as np
import pytest

from eval.mppi_sandbox import cte_peak_vacuity, obstacle_reach, path_curvature


def test_census_matches_the_yaml():
    """`CENSUS` is re-derivable; an edit to any scene's obstacles goes red."""
    assert obstacle_reach.drift() == []


def test_obstacle_free_scenes_are_exactly_the_three():
    assert obstacle_reach.obstacle_free() == obstacle_reach.OBSTACLE_FREE_SCENES
    assert len(obstacle_reach.OBSTACLE_FREE_SCENES) == 3


def test_finding_1_the_channel_separates_the_cross_track_partition():
    """Among `cte_max` declarers, "has an obstacle" and "grades" coincide.

    This is the statement `path_curvature` could not make: its channel put the
    graded scene at ratio `0.0`, the *bottom* of its own ordering.
    """
    bars = obstacle_reach.declared_bars()
    assert len(bars) == 5
    live = obstacle_reach.measure()
    excited = {k for k in bars if live[k][1] > 0.0}
    assert excited == {obstacle_reach.DISCRIMINATING_SCENE}
    # the other four are not weakly excited — they are exactly zero
    for key in bars:
        if key != obstacle_reach.DISCRIMINATING_SCENE:
            assert live[key][1] == 0.0

    # ...but "not excited" stopped being one mechanism when the 9th scene
    # landed. Until `cafe_obstacle_contested_v0`, every unexcited declarer was
    # unexcited because it carried *no obstacle* (`d_enc` infinite), which is
    # what let finding #1 read "has an obstacle" and "grades" as coinciding.
    # Contested_v0 declares a bar, carries 5 obstacles, and still forces
    # exactly 0.0 — its nearest encounter is 1.0849 m, an order of magnitude
    # outside the corridor. So the partition survives in its *verdict* and
    # splits in its *mechanism*, and only the second is a property of the yaml.
    unexcited = [k for k in bars if k != obstacle_reach.DISCRIMINATING_SCENE]
    obstacle_free = [k for k in unexcited if not math.isfinite(live[k][0])]
    distant = [k for k in unexcited if math.isfinite(live[k][0])]
    assert sorted(obstacle_free) == list(obstacle_reach.OBSTACLE_FREE_SCENES)
    assert distant == ["cafe_obstacle_contested_v0"]
    assert live[distant[0]][0] > 10 * live[obstacle_reach.DISCRIMINATING_SCENE][0]


def test_the_graded_scene_is_straight_and_excited():
    """D-361's finding #1, now with both channels measured on the same cell."""
    scene = obstacle_reach.DISCRIMINATING_SCENE
    assert scene in path_curvature.STRAIGHT_SCENES          # no curvature
    assert obstacle_reach.measure()[scene][1] > 0.5         # but an obstacle
    assert path_curvature.CENSUS[scene][2] == 0.0           # curvature ratio 0


def test_finding_2_two_scenes_force_more_excursion_with_no_bar():
    """`cut_in` and `head_on` out-force the graded scene and declare no bar."""
    assert obstacle_reach.unbarred_excited() == obstacle_reach.UNBARRED_EXCITED
    live = obstacle_reach.measure()
    graded = live[obstacle_reach.DISCRIMINATING_SCENE][1]
    bars = obstacle_reach.declared_bars()
    for key in obstacle_reach.UNBARRED_EXCITED:
        assert key not in bars
        assert live[key][1] >= graded


def test_finding_3_the_ratio_is_sub_unity_where_it_grades():
    """0.5070 against a 1.0 bar, and the cell grades anyway."""
    scene = obstacle_reach.DISCRIMINATING_SCENE
    forced = obstacle_reach.measure()[scene][1]
    ratio = forced / obstacle_reach.declared_bars()[scene]
    assert 0.0 < ratio < 1.0
    # and it is *not* below path_curvature's line by accident — that channel
    # reads exactly 0 here, so a curvature threshold cannot explain this cell.
    assert ratio > path_curvature.CENSUS[scene][2]


def test_the_encounter_reading_disagrees_with_the_time_blind_one():
    """`freezing`'s actors have swept past before the robot arrives.

    Scope note in the module docstring, asserted so a future refactor to the
    cheaper time-blind measurement cannot pass silently.
    """
    d_enc, forced, d_static = obstacle_reach.measure()["cafe_freezing_v0"]
    assert d_static < 0.6 <= d_enc      # time-blind says close, encounter says clear
    assert forced == 0.0


def test_nominal_traversal_runs_the_polyline_at_target_speed():
    wps = np.array([[0.0, 0.0, 0.0], [0.0, -4.0, 0.0]])
    t, xy = obstacle_reach.nominal_traversal(wps, speed=0.5)
    assert t[0] == 0.0
    assert xy[0] == pytest.approx([0.0, 0.0])
    assert xy[-1] == pytest.approx([0.0, -4.0])
    assert t[-1] == pytest.approx(4.0 / 0.5, abs=obstacle_reach.NOMINAL_DT)


def test_scene_reach_is_insensitive_to_the_time_step():
    """4 dp stability, so `NOMINAL_DT` is a resolution choice and not a result."""
    from pathlib import Path

    from eval.mppi_sandbox.scenario import load_scenario

    sc = load_scenario(
        obstacle_reach.SCENARIO_DIR / f"{obstacle_reach.DISCRIMINATING_SCENE}.yaml")
    assert Path(obstacle_reach.SCENARIO_DIR).is_dir()
    coarse = obstacle_reach.scene_reach(sc)
    obstacle_reach.NOMINAL_DT  # documented default used by scene_reach
    t, xy = obstacle_reach.nominal_traversal(sc.waypoints, sc.target_speed, dt=0.005)
    fine = min(float(np.min(np.linalg.norm(ob.position(t) - xy, axis=1)))
               for ob in sc.obstacles)
    assert coarse[0] == pytest.approx(fine, abs=1e-3)


def test_population_is_the_same_eight_scenes_the_cte_sweep_graded():
    # The two populations were the same eight scenes until the 9th landed, and
    # they came apart for a reason worth keeping: `obstacle_reach` reads static
    # yaml (free, so it picked the scene up the moment the file existed) while
    # `cte_peak_vacuity` is keyed on a measured seed-0 column (8 arms of
    # rollout, unbought). The gap is exactly the unharvested set, and asserting
    # *that* keeps the drift loud — a tenth scene, or a dropped column, still
    # fails here — without pretending a measurement was taken.
    from eval.mppi_sandbox import scene_census as sc

    static_pop = set(obstacle_reach.measure())
    measured_pop = set(cte_peak_vacuity.CENSUS)
    assert static_pop - measured_pop == set(sc.UNHARVESTED_SCENES)
    assert not measured_pop - static_pop
