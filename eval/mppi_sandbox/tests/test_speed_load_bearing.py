"""`d_enc` is a function of the robot's speed, and the census flies the wrong one.

Every `*_v0.yaml` declares `target_speed_mps: 0.3` and every arm runs the
calibrated cruise `0.723` (D-024/D-025, re-measured in D-451). `obstacle_reach`
takes its nominal traversal speed from the declared value, so its whole census
describes a robot that is never simulated. These tests pin the size of that gap
rather than the repair — re-pointing `scene_reach` at the cruise would move
`CENSUS`, `UNBARRED_EXCITED`, the `0.5070` floor and `threshold_vacuity` in one
commit, which is Q-200 and a cycle of its own (D-458 is what that costs).
"""

from __future__ import annotations

import numpy as np

from eval.mppi_sandbox import obstacle_reach as ore
from eval.mppi_sandbox.scenario import load_scenario


def test_cruise_census_matches_the_yaml():
    assert ore.measure_at(ore.CRUISE_SPEED) == ore.CRUISE_CENSUS


def test_declared_speed_is_never_the_cruise():
    """The premise, and it is stronger than "they all declare 0.3".

    Four distinct declared speeds across nine scenes, none equal to the cruise.
    So `d_enc` is not a scene-comparable quantity either: the census flies a
    different robot in each row.
    """
    live = {p.stem: load_scenario(p).target_speed
            for p in sorted(ore.SCENARIO_DIR.glob("*_v0.yaml"))}
    assert live == ore.DECLARED_SPEEDS
    assert len(set(live.values())) == 4
    assert ore.CRUISE_SPEED not in set(live.values())


def test_the_two_obstacle_scenes_exchange_verdicts():
    """Finding #4 as an assertion, not a sentence.

    The scene the module calls `DISCRIMINATING` forces nothing at the speed the
    robot actually runs, and the scene `threshold_vacuity` grades `VACUOUS_PASS`
    is the one that forces more than the floor.
    """
    slow, fast = ore.measure(), ore.measure_at(ore.CRUISE_SPEED)
    graded, contested = ore.DISCRIMINATING_SCENE, "cafe_obstacle_contested_v0"

    assert slow[graded][1] >= 0.5070 and fast[graded][1] == 0.0
    assert slow[contested][1] == 0.0 and fast[contested][1] >= 0.5070
    assert ore.speed_inversions() == ore.SPEED_INVERTED
    assert set(ore.SPEED_INVERTED) == {graded, contested}


def test_contested_stages_all_five_actors_at_the_cruise():
    """The scene is authored correctly; only the instrument disagreed.

    Q-198 asked whether to move this scene's obstacle lane ~0.3 m toward the
    path. At the cruise every actor already passes within a centimetre of the
    nominal robot, so the move would have been a repair to a working scene.
    """
    scenario = load_scenario(
        ore.SCENARIO_DIR / "cafe_obstacle_contested_v0.yaml")
    t, xy = ore.nominal_traversal(scenario.waypoints, ore.CRUISE_SPEED)

    per_actor = [float(np.min(np.linalg.norm(ob.position(t) - xy, axis=1)))
                 for ob in scenario.obstacles]
    assert len(per_actor) == 5
    assert max(per_actor) < 0.011, per_actor


def test_crossing_meets_one_actor_at_the_cruise():
    """The D-451 counterpart: the graded scene's contest is thinner, not wider.

    At the declared speed it reads as the only excited scene. At the cruise four
    of its five actors are more than a metre away.
    """
    scenario = load_scenario(
        ore.SCENARIO_DIR / "cafe_obstacle_crossing_v0.yaml")
    t, xy = ore.nominal_traversal(scenario.waypoints, ore.CRUISE_SPEED)

    per_actor = sorted(float(np.min(np.linalg.norm(ob.position(t) - xy, axis=1)))
                       for ob in scenario.obstacles)
    assert len(per_actor) == 5
    assert per_actor[0] < 0.65
    assert min(per_actor[1:]) > 1.7


def test_drift_reports_the_cruise_census_too():
    """`drift()` is the module's own gate; the new pins must be inside it."""
    assert ore.drift() == []
