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
from eval.mppi_sandbox.recorded_clearance import recorded_scenes
from eval.mppi_sandbox.scorable_band import PUBLISHED_SCENARIO


def _scene(name, *, obstacles=1, margin=0.30, clearance=1.0, exclusions=()):
    return SceneEligibility(scenario=name, n_obstacles=obstacles,
                            declared_margin=margin, best_goal_clearance=clearance,
                            exclusions=frozenset(exclusions))


@pytest.fixture(scope="module")
def shipped():
    return census()


# --- the measurement -------------------------------------------------------

def test_four_of_nine_scenes_are_eligible(shipped):
    """The successor question's denominator is 4, not the 9 STATE assumed.

    Was `three_of_eight` until D-457 landed `cafe_obstacle_contested_v0`, which
    carries obstacles and a declared margin and so enters eligible on arrival.
    """
    assert len(shipped.scenes) == 9
    assert len(shipped.eligible) == 4
    assert {s.scenario for s in shipped.eligible} == {
        "cafe_convoy_v0", "cafe_head_on_v0", "cafe_obstacle_contested_v0",
        "cafe_obstacle_crossing_v0"}


def test_landing_an_eligible_scene_reopens_the_measured_gap(shipped):
    """D-457 spends the sentence this census produced, in the useful direction.

    It read FULLY_MEASURED for three cycles: `cafe_convoy_v0` left the unwalked
    set when the census learned `scene_census.PAIRED_ENSEMBLE` (D-416), and
    `cafe_obstacle_crossing_v0` left it when `scene_transfer` was registered
    (D-417's follow-up) — both times by *registering a reader*, never by
    walking a scene. `cafe_obstacle_contested_v0` is the first entrant that
    moves it the other way, and it does so honestly: the scene ships a seed-0
    column (`scene_census.SCENE_SEED0`) but no `MIN_SEEDS`-deep ensemble, and
    `measured` is defined on ensemble depth, not on the existence of numbers.

    So PARTIALLY_MEASURED here is not a regression to repair. It is the census
    reporting a real gap that landing a scene created, which is the entire
    reason the gap is worth having a census for.
    """
    assert shipped.verdict == PARTIALLY_MEASURED
    assert {s.scenario for s in shipped.measured} == {
        PUBLISHED_SCENARIO, "cafe_convoy_v0", "cafe_obstacle_crossing_v0"}
    assert {s.scenario for s in shipped.unmeasured} == {
        "cafe_obstacle_contested_v0"}


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
    # A name no module records, rather than a real scene. Both real candidates
    # this test has used — `cafe_convoy_v0`, then `cafe_obstacle_crossing_v0` —
    # turned out to be measured all along, one per cycle, each time silently
    # converting this into a test of `FULLY_MEASURED`. There is no longer any
    # genuinely unwalked eligible scene to borrow, so the synthetic name is
    # what keeps the `NONE_MEASURED` branch actually exercised.
    unwalked = EligibilityCensus(scenes=(_scene("scene_no_reader_records_v0"),))
    assert unwalked.verdict == NONE_MEASURED

    walked = EligibilityCensus(scenes=(_scene(PUBLISHED_SCENARIO, margin=0.40),))
    assert walked.verdict == FULLY_MEASURED

    assert EligibilityCensus(
        scenes=(_scene(PUBLISHED_SCENARIO, margin=0.40),
                _scene("scene_no_reader_records_v0"))).verdict == PARTIALLY_MEASURED


def test_recorded_scenes_is_derived_not_typed():
    """The old pin asserted `RECORDED_SCENES == {PUBLISHED_SCENARIO}` and passed
    for the module's whole life while the set was **wrong**: it never named
    `clearance_census`'s 8x8 ensemble on `cafe_freezing_v0`. Importing the name
    guarded the spelling (D-047) and left the membership unguarded. This asserts
    the derivation instead, so a new ensemble anywhere in the tree moves the set
    rather than aging the literal."""
    assert RECORDED_SCENES == recorded_scenes()
    assert PUBLISHED_SCENARIO in RECORDED_SCENES
    # The member the literal missed. Named explicitly because its absence cost
    # nothing today and would have cost a whole cycle the moment the scene
    # declared a margin.
    assert "cafe_freezing_v0" in RECORDED_SCENES


def test_the_omission_was_masked_by_an_exclusion_not_by_being_harmless():
    """Why the bug was invisible, asserted rather than narrated: with the old
    literal the census printed the same counts, because `measured` requires
    `eligible` and `cafe_freezing_v0` is excluded. Grant it a margin and the two
    sets disagree — which is the failure a one-line yaml edit would have bought."""
    typed = frozenset({PUBLISHED_SCENARIO})
    excluded = _scene("cafe_freezing_v0", exclusions=(NO_DECLARED_MARGIN,))
    assert not excluded.measured  # same answer under either set

    eligible = _scene("cafe_freezing_v0", margin=0.30)
    assert eligible.measured                       # derived set: already walked
    assert eligible.scenario not in typed          # typed set: "go measure it"


def test_render_names_the_margin_split(shipped):
    text = str(shipped)
    assert "4/9 eligible" in text and "3/4 measured" in text
    assert "distinct margins" in text
