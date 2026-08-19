# SPDX-License-Identifier: BSD-3-Clause
"""Path curvature vs sampler reach — the measurement D-360 left as `CURVATURE_UNMEASURED`.

The load-bearing assertion is again a **negative**, and it points the opposite
way from the hypothesis that motivated the module. D-360 finding #2 borrowed
Nav2 #5925's mechanism — cross-track failure is excited by path curvature, so a
straight scene cannot fail a cross-track bar — and offered it as the surviving
explanation for five vacuous cells. Measured, the suite's **only** scene whose
cross-track bar grades has a reference path with **no curvature at all**.
`test_the_graded_scene_is_straight` is that finding; if a future scenario edit
gives `cafe_obstacle_crossing_v0` a bend, it goes red, which is the honest
signal that the refutation no longer rests on what it rested on.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from eval.mppi_sandbox import path_curvature as pc


def test_no_drift_from_census():
    """Every pinned radius, reach and ratio still derives from the yaml."""
    assert pc.drift() == []


def test_module_cli_is_green():
    assert pc.main() == 0


def test_the_graded_scene_is_straight():
    """Finding #1 — curvature is not what makes a cross-track bar gradeable.

    `cafe_obstacle_crossing_v0` is the sole `DISCRIMINATING` scene on both the
    RMS bar (D-358) and the peak bar (D-360), and its authored path is exactly
    collinear. So the graded cell is bought by obstacle avoidance, not by path
    geometry.
    """
    assert pc.DISCRIMINATING_SCENE in pc.straight_scenes()
    r_min, _, ratio = pc.measure()[pc.DISCRIMINATING_SCENE]
    assert not np.isfinite(r_min)
    assert ratio == 0.0


def test_six_of_eight_scenes_have_no_curvature():
    """The straight set is a supermajority, and it is derived, not typed."""
    live = pc.measure()
    assert len(live) == 8
    assert pc.straight_scenes() == pc.STRAIGHT_SCENES
    assert len(pc.STRAIGHT_SCENES) == 6


def test_curvature_orders_the_vacuous_three_as_headroom_did():
    """Finding #2 — D-360's ordering survives, but only among vacuous scenes.

    Peak headroom ranked the three vacuous declaring scenes
    `curved (2.18x) < figure8 (9.25x) < straight (23.26x)`; nearer to grading
    first. The excitation ratio must rank them the same way, reversed (a higher
    ratio means nearer to grading).
    """
    live = pc.measure()
    curved = live["city_curved_v0"][2]
    figure8 = live["city_figure8_v0"][2]
    straight = live["cafe_straight_v0"][2]
    assert curved > figure8 > straight
    assert straight == 0.0


def test_no_scene_reaches_the_excitation_ratio():
    """Finding #3 — every scene is below 1.0, so "add a curved scene" is under-specified."""
    assert pc.unreached() == tuple(sorted(pc.measure()))
    assert max(r for _, _, r in pc.measure().values()) < pc.EXCITATION_RATIO_THRESHOLD


def test_min_curvature_radius_on_known_geometry():
    """A unit circle's inscribed polygon has circumradius 1 at every vertex."""
    ang = np.linspace(0.0, 2.0 * math.pi, 13)
    circle = np.stack([np.cos(ang), np.sin(ang), np.zeros_like(ang)], axis=1)
    assert pc.min_curvature_radius(circle) == pytest.approx(1.0, abs=1e-9)


def test_min_curvature_radius_is_inf_on_a_line():
    line = np.array([[0.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, -2.0, 0.0]])
    assert pc.min_curvature_radius(line) == float("inf")


def test_repeated_waypoint_is_not_a_hairpin():
    """A coincident point is a discretisation accident, not a zero radius."""
    dup = np.array([[0.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, -1.0, 0.0],
                    [0.0, -2.0, 0.0]])
    assert pc.min_curvature_radius(dup) == float("inf")


def test_reach_uses_the_default_horizon():
    assert pc.reach(0.5) == pytest.approx(1.5)
    assert pc.REACH_USES_DEFAULT_HORIZON == ("horizon", 30, "dt", 0.1)


def test_excitation_ratio_maps_a_straight_path_to_zero():
    assert pc.excitation_ratio(float("inf"), 1.5) == 0.0
    assert pc.excitation_ratio(3.0, 1.5) == pytest.approx(0.5)
