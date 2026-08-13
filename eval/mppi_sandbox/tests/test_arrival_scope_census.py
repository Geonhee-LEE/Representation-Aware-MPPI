# SPDX-License-Identifier: BSD-3-Clause
"""`arrival_scope_census` — the blast radius of an arrival-scoped `freeze_duration`."""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import arrival_scope_census as asc
from eval.mppi_sandbox.freeze_price import freeze_duration, freeze_duration_before
from eval.mppi_sandbox.run import load_scenario


@pytest.fixture(scope="module")
def rows():
    return asc.sweep()


# ---------------------------------------------------------------- the census

def test_census_holds(rows):
    """Every shipped scene is pinned, and measures the verdict it is pinned at."""
    assert asc.drift(rows) == []


def test_every_shipped_scene_is_swept(rows):
    """The sweep covers the scene set, not a subset someone typed."""
    assert {r.scene for r in rows} == set(asc.VERDICT_CENSUS)
    assert len(rows) == 8


def test_lam_windows_is_not_a_scene():
    """The variant table in the scenario dir is excluded by the loader, not by name.

    D-047: a hand-listed exclusion drifts from what it mirrors. `scene_paths`
    filters on "does `load_scenario` accept it", so the next non-scene yaml is
    handled without anyone remembering this module exists.
    """
    names = {p.stem for p in asc.scene_paths()}
    assert "lam_windows" not in names
    assert (asc.SCENARIO_DIR / "lam_windows.yaml").exists()


# ------------------------------------------- the finding: freezing is not special

def test_contamination_is_not_confined_to_the_freezing_scene(rows):
    """STATE's bottleneck question, answered: every arriving scene is bitten.

    `cafe_freezing_v0` is special only in that it *declares*
    `freeze_duration_max` — the defect is in the metric, and the single
    declaration is all that has been containing it.
    """
    contaminated = {r.scene for r in rows
                    if r.verdict == asc.VERDICT_CONTAMINATED}
    assert "cafe_freezing_v0" in contaminated
    assert contaminated - {"cafe_freezing_v0"}, "freezing scene is not alone"
    arriving = {r.scene for r in rows if r.arrives}
    assert contaminated == arriving, "every arriving scene is contaminated"


def test_post_arrival_share_is_never_small_on_an_arriving_scene(rows):
    """No arriving scene sits near the threshold — the census is not a knife edge."""
    shares = [r.post_arrival_share for r in rows if r.arrives]
    assert shares and all(s > 0.2 for s in shares)
    assert max(shares) == pytest.approx(1.0)


# --------------------------------------------------------- Q-145's lean, refuted

def test_duration_ratio_does_not_rank_contamination(rows):
    """Q-145 lean (b) refuted **by its own sweep**, not by argument.

    The cheap precondition census — flag scenes where `duration_s >>
    time_to_goal` — cannot stand in for the scope reading: the lowest-ratio
    arriving scene carries more contamination than most higher-ratio ones.
    """
    assert asc.ratio_ranks_contamination(rows) is False


def test_lowest_ratio_scene_is_contaminated(rows):
    """The concrete counterexample, pinned so a re-measure has to re-refute it.

    `city_curved_v0` has the smallest `duration_s / time_to_goal` of any
    arriving scene and would be cleared first by any ratio threshold — yet a
    majority of its whole-trajectory reading is post-arrival.
    """
    arriving = [r for r in rows if r.arrives]
    lowest = min(arriving, key=lambda r: r.duration_ratio)
    assert lowest.duration_ratio < 1.1
    assert lowest.verdict == asc.VERDICT_CONTAMINATED
    assert lowest.post_arrival_share > 0.5


def test_a_ratio_threshold_clearing_it_also_clears_a_fully_contaminated_scene(rows):
    """Why the ratio fails is structural: the orders genuinely cross.

    Any threshold permissive enough to clear the lowest-ratio scene also clears
    at least one scene whose whole-trajectory reading is *entirely*
    post-arrival — so no tuning of Q-145's threshold recovers the census.
    """
    arriving = [r for r in rows if r.arrives]
    lowest = min(arriving, key=lambda r: r.duration_ratio)
    also_cleared = [r for r in arriving
                    if r.duration_ratio <= lowest.duration_ratio * 1.2
                    and r.post_arrival_share == pytest.approx(1.0)]
    assert also_cleared, "the ratio and share orders cross"


# -------------------------------------------- arrival that is not a measurement

def test_figure8_arrives_at_time_zero_because_its_start_is_its_goal(rows):
    """The closed loop: arrival-scoping there is vacuous, not corrective.

    `time_to_goal` is the first timestep inside both tolerances and the
    figure-8's start pose *is* its goal pose, so it fires before the robot
    moves. The arrival-scoped reading over an empty window is 0.0 for any
    controller on any seed — swapping 29.6 s of unusable number for 0.0 s of
    unusable number is not a fix.
    """
    scenario = load_scenario(asc.SCENARIO_DIR / "city_figure8_v0.yaml")
    start = np.asarray(scenario.start, dtype=float)
    goal = np.asarray(scenario.goal, dtype=float)
    assert np.hypot(*(goal[:2] - start[:2])) < float(
        scenario.acceptance.get("goal_xy_tol", 0.2))

    row = next(r for r in rows if r.scene == "city_figure8_v0")
    assert row.arrival_s == pytest.approx(0.0)
    assert row.arrives is False
    assert row.before == pytest.approx(0.0)
    assert row.whole > 1.0
    assert row.verdict == asc.VERDICT_ARRIVAL_UNUSABLE


def test_never_arriving_scene_is_an_identity_not_a_clean_bill(rows):
    """`cafe_cut_in_v0` never arrives, so the scopes coincide by construction.

    Its zero disagreement must not read as CLEAN — that is the absence of a
    reading, and `freeze_duration_before` documents the identity.
    """
    row = next(r for r in rows if r.scene == "cafe_cut_in_v0")
    assert row.arrival_s is None
    assert row.whole == pytest.approx(row.before)
    assert row.whole > 0.0
    assert row.verdict == asc.VERDICT_ARRIVAL_UNUSABLE
    assert row.post_arrival_share is None
    assert row.duration_ratio is None


def test_arrival_unusable_is_disjoint_from_clean(rows):
    """The third category exists precisely so no one reads 0 % as healthy."""
    unusable = {r.scene for r in rows
                if r.verdict == asc.VERDICT_ARRIVAL_UNUSABLE}
    clean = {r.scene for r in rows if r.verdict == asc.VERDICT_CLEAN}
    assert unusable == {"cafe_cut_in_v0", "city_figure8_v0"}
    assert not (unusable & clean)


# ------------------------------------------------------------------- mechanics

def test_both_scopes_come_off_one_trajectory():
    """D-250's method: one run, two readings — never two runs.

    Two runs would differ by the controller's own noise as well as by the
    scope, and the difference has to be attributable to the scope alone.
    """
    row = asc.measure(asc.SCENARIO_DIR / "cafe_freezing_v0.yaml")
    again = asc.measure(asc.SCENARIO_DIR / "cafe_freezing_v0.yaml")
    assert row == again, "measurement is deterministic at the census seed"
    assert row.before <= row.whole, "the truncation cannot lengthen the stall"


def test_before_never_exceeds_whole_on_any_scene(rows):
    """The scoping is a restriction, so this holds for every scene by construction."""
    for r in rows:
        assert r.before <= r.whole + 1e-12, r.scene


def test_measure_agrees_with_freeze_price_directly():
    """The census reads the shipped definitions, not a re-implementation."""
    path = asc.SCENARIO_DIR / "cafe_straight_v0.yaml"
    row = asc.measure(path)
    scenario = load_scenario(path)

    from eval.mppi_sandbox.run import ROBOT_RADIUS, make_controller, simulate
    from eval.path_tracking_metrics import Goal, time_to_goal

    ctrl = make_controller(asc.CENSUS_ARM, scenario, seed=asc.CENSUS_SEED,
                           robot_radius=ROBOT_RADIUS)
    traj = simulate(scenario, ctrl)
    acc = scenario.acceptance
    arrival = time_to_goal(traj, Goal(*scenario.goal),
                           xy_tol=float(acc.get("goal_xy_tol", 0.2)),
                           yaw_tol=float(acc.get("goal_yaw_tol", 0.3)))

    assert row.arrival_s == pytest.approx(arrival)
    assert row.whole == pytest.approx(freeze_duration(traj, scenario.waypoints))
    assert row.before == pytest.approx(
        freeze_duration_before(traj, scenario.waypoints, arrival))


def test_arrival_eps_admits_only_a_zero_arrival():
    """The epsilon separates "began at the goal" from "got there fast".

    One simulation step at the shipped `dt = 0.1` is 0.1 s, which must read as
    a genuine arrival; only t=0 is the degenerate case.
    """
    assert asc.ARRIVAL_EPS_S < 0.1
    fast = asc.SceneScope(scene="x", duration_s=10.0, arrival_s=0.1,
                          whole=1.0, before=0.5)
    assert fast.arrives is True
    zero = asc.SceneScope(scene="x", duration_s=10.0, arrival_s=0.0,
                          whole=1.0, before=0.0)
    assert zero.arrives is False


def test_share_is_none_when_there_is_no_freeze_to_apportion():
    """A share off `whole == 0` would be an arithmetic artifact, not a reading."""
    row = asc.SceneScope(scene="x", duration_s=10.0, arrival_s=5.0,
                         whole=0.0, before=0.0)
    assert row.post_arrival_share is None
    assert row.verdict == asc.VERDICT_CLEAN


def test_drift_reports_unpinned_and_disagreeing_scenes():
    """Both directions of the census guard fire."""
    unpinned = asc.SceneScope(scene="brand_new_v0", duration_s=10.0,
                              arrival_s=5.0, whole=1.0, before=0.0)
    assert any("unpinned" in d for d in asc.drift([unpinned]))

    flipped = asc.SceneScope(scene="cafe_freezing_v0", duration_s=10.0,
                             arrival_s=5.0, whole=1.0, before=1.0)
    found = asc.drift([flipped])
    assert any("census CONTAMINATED vs measured CLEAN" in d for d in found)
    assert any("pinned but not measured" in d for d in found)
