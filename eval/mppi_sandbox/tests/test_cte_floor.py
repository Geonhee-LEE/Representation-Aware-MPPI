# SPDX-License-Identifier: BSD-3-Clause
"""Joint satisfiability of a scene's two lateral keys — the answer to Q-109.

D-121 measured that `cafe_head_on_v0` needs a **1.00 m** corridor to hold its
declared 0.40 m margin, and refused to call that a contradiction against the
scene's `cte_rms_max: 0.30`: a peak and an rms are different quantities, and
the comparison is only meaningful once the excursion is priced in the rms the
metric actually computes. These tests pin that price and the controls that
make it usable.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox.feasibility import (
    DEFAULT_ROBOT_RADIUS,
    _polyline_distance,
    declared_corridor,
    declared_cte_rms,
    declared_margin,
    min_cte_rms,
    required_corridor,
)
from eval.mppi_sandbox.obstacles import DEFAULT_RADIUS, CircleObstacle
from eval.mppi_sandbox.scenario import Scenario, load_scenario
from eval.path_tracking_metrics import cross_track_error

SCENARIOS = "eval/scenarios"

#: Surface-to-surface offset between two circle centres at zero clearance.
CONTACT = DEFAULT_RADIUS + DEFAULT_ROBOT_RADIUS


def _scene(name):
    return load_scenario(f"{SCENARIOS}/{name}.yaml")


# --------------------------------------------------------------------------
# The rms reader, and its separation from the corridor reader
# --------------------------------------------------------------------------

def test_the_two_lateral_readers_stay_distinct():
    """`cte_max` and `cte_rms_max` are read by name, never for each other.

    This is the same refusal `declared_corridor` documents, checked from the
    other side: head-on declares only the rms key, so one reader must see it
    and the other must not. Collapsing them would make Q-109 unaskable — the
    question exists precisely because the scene bounds the run and says
    nothing about any instant.
    """
    head_on = _scene("cafe_head_on_v0")
    assert declared_cte_rms(head_on) == 0.30
    assert declared_corridor(head_on) is None

    crossing = _scene("cafe_obstacle_crossing_v0")
    assert declared_corridor(crossing) == 1.0
    assert declared_cte_rms(crossing) == 0.40


# --------------------------------------------------------------------------
# Q-109's answer
# --------------------------------------------------------------------------

def test_head_on_two_keys_are_jointly_satisfiable():
    """The 1.00 m corridor costs far less rms than the scene's 0.30 budget.

    This is the answer: the excursion D-121 priced is a *transient*, and an
    rms bound charges it only for the samples it lasts. The floor lands near
    0.09, so the scene asks for nothing self-contradictory and its 8/8 unsafe
    verdict is not excused by an impossible declaration.
    """
    floor = min_cte_rms(_scene("cafe_head_on_v0"))

    assert floor.verdict == "COMPATIBLE"
    assert floor.is_jointly_satisfiable
    assert floor.min_cte_rms == pytest.approx(0.0865, abs=0.02)
    assert floor.min_cte_rms < floor.declared_cte_rms_max


def test_the_answer_survives_the_loitering_horizon():
    """The one knob that could have produced the answer for free.

    `cte_rms` averages over *samples*, so a schedule that dawdles on the path
    dilutes its own excursion — and the search is free to do that out to the
    timeout. The floor therefore falls as the horizon grows, which would make
    a bare `COMPATIBLE` a statement about `TIMEOUT_FACTOR` rather than about
    the scene. It is not: even at a horizon of exactly the expected duration,
    where no dilution is available at all, the floor stays under the declared
    bound with room to spare.
    """
    s = _scene("cafe_head_on_v0")
    floors = [min_cte_rms(s, timeout_factor=tf).min_cte_rms
              for tf in (1.0, 1.5, 2.0, 4.0)]

    assert floors == sorted(floors, reverse=True), "dilution is monotone"
    assert max(floors) == pytest.approx(0.1727, abs=0.02)
    assert max(floors) < declared_cte_rms(s)


def test_crossing_needs_no_excursion_at_all():
    """Cross-check against D-121: a 0.00 m corridor implies a 0.00 rms floor.

    The two screens share a grid but optimise different objectives, so their
    agreeing here is a real check — a non-zero floor on a scene that never has
    to leave the path would mean one of them is finding schedules the other
    cannot.
    """
    s = _scene("cafe_obstacle_crossing_v0")
    assert required_corridor(s) == 0.0
    assert min_cte_rms(s).min_cte_rms == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------------
# Comparability: the floor must be in the metric's units
# --------------------------------------------------------------------------

def test_offset_cost_matches_the_shipped_metric_on_a_curved_path():
    """The cost is polyline distance, not offset magnitude.

    They coincide on a straight reference — every shipped scene — and diverge
    on a curved one, where a point offset along the normal can sit nearer a
    different segment. `cte_rms` is built from the former, so pricing the
    latter would compare the floor against a bound measured differently.
    """
    path = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0],
                     [2.0, 2.0, np.pi / 2], [0.0, 2.0, np.pi]])
    pts = np.array([[2.4, 0.4], [1.0, 0.6], [2.6, 1.0], [0.5, 1.9]])

    traj = np.zeros((len(pts), 6))
    traj[:, 1:3] = pts
    assert _polyline_distance(pts, path) == pytest.approx(
        np.abs(cross_track_error(traj, path)), abs=1e-9)


# --------------------------------------------------------------------------
# Direction of the one-sidedness
# --------------------------------------------------------------------------

def test_truncating_the_search_can_only_raise_the_floor():
    """The one parameter that errs in the unsafe direction.

    Every other relaxation adds schedules and lowers the floor, keeping
    `INCOMPATIBLE` a proof. A lateral limit narrower than the excursion the
    margin needs removes schedules instead, and could manufacture a verdict
    the geometry does not support — which is why the default derives the limit
    from `required_corridor` rather than assuming a range.
    """
    s = _scene("cafe_head_on_v0")
    tight = min_cte_rms(s, lateral_limit=0.6).min_cte_rms
    derived = min_cte_rms(s).min_cte_rms

    assert required_corridor(s) > 0.6, "0.6 really does truncate the optimum"
    assert tight > derived


def test_margin_no_corridor_attains_short_circuits_optimistically():
    """`MARGIN_UNATTAINABLE` is not a joint-satisfiability failure.

    If no corridor up to the ceiling holds the margin, this screen has nothing
    to say about the *rms* keys — D-121 already owns that verdict. Reporting
    it as incompatible would double-count one defect as two and blame the rms
    bound for a margin problem.
    """
    s = Scenario(
        name="walled-in", start=np.array([0.0, 0.0, 0.0]),
        goal=np.array([4.0, 0.0, 0.0]),
        waypoints=np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0]]),
        target_speed=0.5, expected_duration=10.0,
        obstacles=[CircleObstacle(x=2.0, y=0.0)],
        acceptance={"min_distance_to_obstacle": 20.0, "cte_rms_max": 0.1},
    )
    floor = min_cte_rms(s)

    assert required_corridor(s) is None
    assert floor.verdict == "MARGIN_UNATTAINABLE"
    assert floor.is_jointly_satisfiable
    assert not np.isfinite(floor.min_cte_rms)


def test_scene_declaring_no_rms_bound_cannot_be_caught():
    """An absent key is not a bound of zero — the D-120 lesson, restated.

    A scene with no `cte_rms_max` places no whole-run lateral demand, so no
    excursion can violate one. The screen must report that it had nothing to
    check rather than grade the floor against a default.
    """
    s = Scenario(
        name="unbounded", start=np.array([0.0, 0.0, 0.0]),
        goal=np.array([4.0, 0.0, 0.0]),
        waypoints=np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0]]),
        target_speed=0.5, expected_duration=10.0,
        obstacles=[CircleObstacle(x=2.0, y=0.0)],
        acceptance={"min_distance_to_obstacle": 0.2},
    )
    floor = min_cte_rms(s)

    assert declared_cte_rms(s) is None
    assert floor.verdict == "NO_RMS_DECLARED"
    assert floor.is_jointly_satisfiable
    assert floor.min_cte_rms > 0.0, (
        "the excursion is still measured — only the comparison is missing")


def test_empty_scene_costs_nothing_to_track():
    """Negative control: nothing to avoid means the path itself is optimal."""
    s = _scene("cafe_straight_v0")
    assert not s.obstacles
    assert min_cte_rms(s).min_cte_rms == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------------
# What the answer does to D-120's attribution
# --------------------------------------------------------------------------

def test_no_shipped_obstacle_scene_declares_incompatible_keys():
    """The population result, so the head-on answer is not read as luck.

    D-121 moved 16 of D-120's 32 unsafe seeds from planner to scene
    declaration on the strength of an *unmeasured* incompatibility. None of
    the five obstacle-bearing scenes is actually incompatible, so that
    re-attribution does not survive: every scene's pair of lateral keys can be
    met at once, and the margin failures stay controller-side.
    """
    names = ["cafe_convoy_v0", "cafe_cut_in_v0", "cafe_freezing_v0",
             "cafe_head_on_v0", "cafe_obstacle_crossing_v0"]
    verdicts = {n: min_cte_rms(_scene(n)).verdict for n in names}

    assert not [n for n, v in verdicts.items() if v == "INCOMPATIBLE"]
    assert verdicts["cafe_head_on_v0"] == "COMPATIBLE"


def test_head_on_still_demands_a_corridor_the_scene_never_grants():
    """Compatible is not the same as declared, and the gap is the finding.

    Holding the margin needs a 1 m instantaneous sidestep. The scene permits
    it — no `cte_max` forbids anything — but never says so, and its only
    stated lateral number is 0.30, which reads like a much tighter box than
    the run is actually held to. That gap is a declaration defect a controller
    author cannot see, and it is what survives Q-109.
    """
    s = _scene("cafe_head_on_v0")

    assert declared_corridor(s) is None
    assert required_corridor(s) == pytest.approx(declared_margin(s) + CONTACT,
                                                 abs=0.02)
    assert required_corridor(s) > declared_cte_rms(s)
    assert min_cte_rms(s).min_cte_rms < declared_cte_rms(s)
