"""Can any *other* scene host the two-sided rung `cafe_head_on_v0` cannot?

The weight-carrying tests here are not the field checks. `test_exclusions_are_a
_set_not_a_first_match` pins the D-157 choice — a scene failing two screens
records both — by computing the two counts side by side rather than asserting
the preferred one, because that choice is the entire difference between "5
scenes excluded" and "6 exclusion reasons". `test_verdict_is_independent_of_the
_exclusion_set` keeps the displayed precedence from being mistaken for the
population reading, and `test_ineligible_scene_is_never_measured` blocks the
relabelling where a recorded-but-retired scene reads as coverage.
"""

import pytest

from eval.mppi_sandbox.scene_eligibility import (
    ELIGIBLE,
    FULLY_MEASURED,
    GOAL_BALL_BLOCKED,
    NO_DECLARED_MARGIN,
    NO_OBSTACLES,
    NO_SCENE_ELIGIBLE,
    NONE_MEASURED,
    PARTIALLY_MEASURED,
    RECORDED_SCENES,
    EligibilityCensus,
    SceneEligibility,
    census,
)
from eval.mppi_sandbox.scorable_band import PUBLISHED_SCENARIO


def _scene(name, *, obstacles=1, margin=0.30, clearance=1.0, exclusions=()):
    return SceneEligibility(scenario=name, n_obstacles=obstacles,
                            declared_margin=margin, best_goal_clearance=clearance,
                            exclusions=frozenset(exclusions))


@pytest.fixture(scope="module")
def shipped():
    return census()


# --- the measurement -------------------------------------------------------

def test_three_of_eight_scenes_are_eligible(shipped):
    """The successor question's denominator is 3, not the 8 STATE assumed."""
    assert len(shipped.scenes) == 8
    assert len(shipped.eligible) == 3
    assert {s.scenario for s in shipped.eligible} == {
        "cafe_convoy_v0", "cafe_head_on_v0", "cafe_obstacle_crossing_v0"}


def test_only_the_capped_scene_is_measured(shipped):
    """The one eligible scene with recorded clearances is the one already
    proved to cap out at 1/4 (D-158) — so every remaining route to a two-sided
    rung runs through a scene nobody has walked."""
    assert shipped.verdict == PARTIALLY_MEASURED
    assert [s.scenario for s in shipped.measured] == [PUBLISHED_SCENARIO]
    assert {s.scenario for s in shipped.unmeasured} == {
        "cafe_convoy_v0", "cafe_obstacle_crossing_v0"}


def test_each_exclusion_reason_convicts_its_scene(shipped):
    by_name = {s.scenario: s for s in shipped.scenes}
    assert NO_OBSTACLES in by_name["city_figure8_v0"].exclusions
    assert NO_DECLARED_MARGIN in by_name["cafe_freezing_v0"].exclusions
    assert by_name["cafe_freezing_v0"].n_obstacles == 2  # excluded despite obstacles
    assert GOAL_BALL_BLOCKED in by_name["cafe_cut_in_v0"].exclusions
    assert by_name["cafe_cut_in_v0"].best_goal_clearance < 0.0


# --- the choices that carry the weight -------------------------------------

def test_exclusions_are_a_set_not_a_first_match(shipped):
    """D-157: collapsing a multi-reason judgement to one reason is a *wrong*
    population claim, not a missing one.

    `cafe_straight_v0` fails two screens at once. Counting reasons and counting
    scenes must therefore give different totals — computed side by side here so
    the choice is pinned rather than assumed.
    """
    straight = {s.scenario: s for s in shipped.scenes}["cafe_straight_v0"]
    assert straight.exclusions == frozenset({NO_OBSTACLES, NO_DECLARED_MARGIN})

    scenes_excluded = len(shipped.excluded)
    reasons_recorded = sum(shipped.count(r) for r in
                           (NO_OBSTACLES, NO_DECLARED_MARGIN, GOAL_BALL_BLOCKED))
    assert scenes_excluded == 5
    # 3 obstacle-free scenes fail twice each (they also declare no margin),
    # `cafe_freezing_v0` once, `cafe_cut_in_v0` once → 8 reasons over 5 scenes.
    assert shipped.count(NO_OBSTACLES) == 3
    assert shipped.count(NO_DECLARED_MARGIN) == 4
    assert shipped.count(GOAL_BALL_BLOCKED) == 1
    assert reasons_recorded == 8
    assert reasons_recorded > scenes_excluded


def test_verdict_is_independent_of_the_exclusion_set():
    """`verdict` is a display precedence pick; it must not be readable as the
    population fact. Two scenes with different exclusion sets share a verdict."""
    one = _scene("a", exclusions=(NO_OBSTACLES,))
    both = _scene("b", exclusions=(NO_OBSTACLES, NO_DECLARED_MARGIN))
    assert one.verdict == both.verdict == NO_OBSTACLES
    assert one.exclusions != both.exclusions


def test_precedence_orders_the_displayed_reason():
    assert _scene("x", exclusions=(NO_DECLARED_MARGIN, GOAL_BALL_BLOCKED)).verdict \
        == NO_DECLARED_MARGIN
    assert _scene("y", exclusions=(GOAL_BALL_BLOCKED,)).verdict == GOAL_BALL_BLOCKED
    assert _scene("z").verdict == ELIGIBLE


def test_ineligible_scene_is_never_measured():
    """A retired scene with recorded data is not coverage. Without this,
    `measured` would relabel an excluded scene as an available result."""
    retired = _scene(PUBLISHED_SCENARIO, obstacles=0,
                     exclusions=(NO_OBSTACLES,))
    assert retired.scenario in RECORDED_SCENES
    assert not retired.measured


# --- the margin is a scene constant, not a band one ------------------------

def test_eligible_scenes_do_not_share_one_margin(shipped):
    """`Headroom` grades one margin, so a cross-scene overlap reading cannot
    quote `PUBLISHED_MARGIN` — the eligible scenes declare two."""
    assert shipped.declared_margins == (0.30, 0.40)
    assert not shipped.margin_is_shared


def test_margin_is_shared_when_it_actually_is():
    same = EligibilityCensus(scenes=(_scene("a", margin=0.30),
                                     _scene("b", margin=0.30)))
    assert same.declared_margins == (0.30,)
    assert same.margin_is_shared


# --- vacuity ---------------------------------------------------------------

def test_no_eligible_scene_is_named_not_inferred():
    """Every other field of an all-excluded census reads identical to a fully
    measured one (empty tuples, empty margins), which is the sixth-plus
    instance of D-107's shape — so the verdict names the case."""
    empty = EligibilityCensus(scenes=(_scene("a", obstacles=0,
                                             exclusions=(NO_OBSTACLES,)),))
    assert empty.verdict == NO_SCENE_ELIGIBLE
    assert empty.measured == () and empty.unmeasured == ()
    assert empty.declared_margins == ()
    assert empty.margin_is_shared            # vacuously — hence the verdict


def test_none_and_fully_measured_are_distinct_from_partial():
    unwalked = EligibilityCensus(scenes=(_scene("cafe_convoy_v0"),))
    assert unwalked.verdict == NONE_MEASURED

    walked = EligibilityCensus(scenes=(_scene(PUBLISHED_SCENARIO, margin=0.40),))
    assert walked.verdict == FULLY_MEASURED

    assert EligibilityCensus(
        scenes=(_scene(PUBLISHED_SCENARIO, margin=0.40),
                _scene("cafe_convoy_v0"))).verdict == PARTIALLY_MEASURED


def test_recorded_scenes_tracks_the_published_scenario():
    """Spelled once (D-047): the recorded-clearance scene name is imported from
    `scorable_band`, so the two cannot drift."""
    assert RECORDED_SCENES == frozenset({PUBLISHED_SCENARIO})


def test_render_names_the_margin_split(shipped):
    text = str(shipped)
    assert "3/8 eligible" in text and "1/3 measured" in text
    assert "distinct margins" in text
