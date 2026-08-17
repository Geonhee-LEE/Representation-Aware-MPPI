# SPDX-License-Identifier: BSD-3-Clause
"""Q-162: `cut_in` separates — and so does every other scene, which is the point.

The tests split into three groups on purpose:

* the **operator** tests drive :func:`scene_separability.separates` off a
  synthetic table, so they say what the no-overlap rule means and keep saying
  it when a re-take moves the measured numbers;
* the **measurement** pins hold the recorded verdict, including the control
  row that is the actual answer to Q-162;
* the **provenance** pins hold the two properties that make the measurement
  mean what it claims — baseline-only rollouts, and a registry that matches
  the recorded keys in both directions.
"""


from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import scene_separability as sep
from eval.mppi_sandbox.clearance_census import BASELINE, SEEDS
from eval.mppi_sandbox.scene_transfer import MEASURED_SCENES

# --------------------------------------------------------------------------
# the operator
# --------------------------------------------------------------------------


def _table(values: dict[str, tuple[float, ...]]) -> dict:
    """A synthetic `OBSERVED` carrying one observable over the five scenes."""
    return {scene: {"probe": values[scene]} for scene in MEASURED_SCENES}


def test_separation_needs_a_gap_on_one_side_or_the_other(monkeypatch):
    """Above the rest and below the rest both count; overlapping does not."""
    below = dict.fromkeys(MEASURED_SCENES, (5.0, 6.0))
    below[sep.QUESTION_SCENE] = (0.0, 1.0)
    monkeypatch.setattr(sep, "OBSERVED", _table(below))
    assert sep.separates(sep.QUESTION_SCENE, "probe")

    above = dict.fromkeys(MEASURED_SCENES, (0.0, 1.0))
    above[sep.QUESTION_SCENE] = (5.0, 6.0)
    monkeypatch.setattr(sep, "OBSERVED", _table(above))
    assert sep.separates(sep.QUESTION_SCENE, "probe")


def test_a_single_overlapping_seed_defeats_separation(monkeypatch):
    """The rule is strict — one seed inside the other range is enough.

    This is the direction that matters for a *switch*: a threshold that eight
    seeds straddle is a threshold that mis-fires, so a rule tolerant of one
    crossing would be reporting a switch that does not exist.
    """
    values = dict.fromkeys(MEASURED_SCENES, (5.0, 6.0))
    values[sep.QUESTION_SCENE] = (0.0, 5.5)      # 5.5 sits inside [5, 6]
    monkeypatch.setattr(sep, "OBSERVED", _table(values))
    assert not sep.separates(sep.QUESTION_SCENE, "probe")


def test_an_infinite_value_never_separates(monkeypatch):
    """`min_ttc` is `inf` when nothing ever closes; that is absence, not signal.

    Without this branch an all-`inf` scene would read as separated from any
    finite one, and a switch keyed on it would be keyed on "no obstacle is
    approaching" — which is exactly the case where the choice of arm does not
    matter. The negative case is drawn from the **coded** branch rather than
    from a measured pair, so no re-take can retire it.
    """
    values = dict.fromkeys(MEASURED_SCENES, (5.0, 6.0))
    values[sep.QUESTION_SCENE] = (float("inf"), float("inf"))
    monkeypatch.setattr(sep, "OBSERVED", _table(values))
    assert not sep.separates(sep.QUESTION_SCENE, "probe")


# --------------------------------------------------------------------------
# the measurement
# --------------------------------------------------------------------------


def test_observed_covers_every_measured_scene_at_ensemble_width():
    """Every hostable scene, every observable, all `SEEDS` seeds — a census.

    The claim under test ("`cut_in` is separable, and so is everything else")
    is a statement about the *whole* measured set, so a table missing a scene
    or short a seed would make the control row weaker without making any
    assertion fail.
    """
    assert tuple(sep.OBSERVED) == MEASURED_SCENES
    for scene in MEASURED_SCENES:
        assert tuple(sep.OBSERVED[scene]) == sep.OBSERVABLES
        for observable in sep.OBSERVABLES:
            assert len(sep.OBSERVED[scene][observable]) == SEEDS


def test_the_question_scene_separates():
    """Q-162's literal question, answered yes — and this is the weaker half."""
    assert sep.separating_observables(sep.QUESTION_SCENE) == ("obstacle_speed",)


def test_the_scene_level_control_does_not_by_itself_sink_the_question():
    """**The control that did *not* fire, pinned so nobody re-reads it as if it had.**

    If every scene separated, `cut_in` separating would be a restatement of
    "the five scenarios are five different files". Only three of five do, so
    `separation_is_distinctive` is True and the scene-level reading gives
    Q-162's option (A) qualified support. That support is withdrawn one control
    later, by the zero-spread test below — and the withdrawal is the finding.
    Recording the intermediate verdict is what keeps the two from being
    conflated by a later cycle reading only the headline.

    Pinned as an equality on the full table rather than as a count, so an
    observable that stops separating some scene shows up as a changed row
    instead of silently holding the total at three.
    """
    assert sep.separation_table() == sep.SEPARATION
    assert sep.scenes_that_separate() == ("cafe_freezing_v0", "cafe_cut_in_v0",
                                          "cafe_head_on_v0")
    assert sep.separation_is_distinctive()


def test_the_question_scenes_only_separator_is_a_scenario_constant():
    """**The verdict.** `obstacle_speed` never moves across eight seeds.

    `cut_in`'s single separation is carried by this one observable, whose
    within-scene spread is exactly zero in all five scenes — one value per
    scene, copied from the yaml through a rollout-shaped function. A switch
    keyed on it is a switch keyed on the scene label, which is Q-162's option
    (C). (`head_on`'s `min_ttc` is a genuine reading and is *not* covered by
    this test; that is the next one's job.)

    Pinned as an equality on the constant set, not as a property of
    `obstacle_speed` alone: a future observable that also fails to move is the
    same mistake, and this goes red when one is added.
    """
    assert sep.constant_observables() == ("obstacle_speed",)
    for scene in MEASURED_SCENES:
        values = sep.OBSERVED[scene]["obstacle_speed"]
        assert len(set(values)) == 1, scene


def test_the_question_scene_is_not_informatively_separable():
    """Strip the constant and `cut_in` separates on **nothing**.

    The scene D-333 named as the switch's decision point is the scene these
    plan-time observables cannot see. The one informative separation in the
    whole matrix belongs to `head_on` — a different scene, and one the switch
    does not need, since `cbf_mppi` already wins it.
    """
    assert sep.informative_separators(sep.QUESTION_SCENE) == ()
    assert not sep.question_scene_is_informatively_separable()
    assert sep.scenes_that_separate_informatively() == ("cafe_head_on_v0",)
    assert {s: sep.informative_separators(s) for s in MEASURED_SCENES} \
        == sep.INFORMATIVE_SEPARATION


def test_no_observable_separates_the_question_scene_alone():
    """The sharper form: not one of the five observables is `cut_in`-specific.

    `separation_is_distinctive` asks whether *some* scene fails to separate.
    This asks the dual — whether some **observable** separates `cut_in` and
    nothing else — because that observable, if it existed, would be the channel
    Q-162 is looking for even though the scene-level count is uninformative.
    """
    for observable in sep.OBSERVABLES:
        separated = [s for s in MEASURED_SCENES if sep.separates(s, observable)]
        assert separated != [sep.QUESTION_SCENE], observable


# --------------------------------------------------------------------------
# provenance
# --------------------------------------------------------------------------


def test_the_rollouts_are_the_baseline_arms():
    """A switch runs before an arm is chosen, so the observables must not read one.

    Checked against the source rather than by running the 40 rollouts: the
    property is "this module names exactly one arm, and it is the baseline",
    which is a statement about the code, not about a measurement.
    """
    source = Path(sep.__file__).read_text()
    assert "make_controller(BASELINE" in source
    assert BASELINE == "stock_mppi"
    for arm in ("cbf_mppi", "social_mppi"):
        assert f'"{arm}"' not in source, arm


def test_the_observable_registry_and_the_recorded_keys_pin_each_other():
    """Bidirectional, per `scene_transfer`'s `MEASURED_SCENES` precedent.

    One direction alone lets a new observable be measured and never graded, or
    graded and never measured; the pair makes either a red test.
    """
    for scene in MEASURED_SCENES:
        assert set(sep.OBSERVED[scene]) == set(sep.OBSERVABLES)
    assert set(sep.SEPARATION) == set(MEASURED_SCENES)
    for scene, observables in sep.SEPARATION.items():
        assert set(observables) <= set(sep.OBSERVABLES), scene


def test_the_question_scene_is_the_one_the_complement_result_named():
    """`QUESTION_SCENE` is `cbf_mppi`'s only block — not a scene chosen here.

    D-333's complement result is what makes Q-162 a question at all; if a later
    cycle's measurement moved the blocking scene, this module would be asking
    about the wrong one and every row above would be answering a dead question.
    """
    from eval.mppi_sandbox.scene_transfer import blocking_scenes
    assert blocking_scenes("cbf_mppi") == (sep.QUESTION_SCENE,)


@pytest.mark.parametrize("scene", MEASURED_SCENES)
def test_separating_observables_is_ordered_by_the_registry(scene):
    """Registry order, not dict-iteration order — the table is read by humans."""
    got = sep.separating_observables(scene)
    assert list(got) == [o for o in sep.OBSERVABLES if o in got]


# --------------------------------------------------------------------------
# the causal indices (D-335)
# --------------------------------------------------------------------------
#
# D-334 read every observable at the episode's minimum-clearance instant, which
# a planner cannot know in advance, and said so: the reading was an *upper
# bound* on what a switch could see. These pins hold the follow-through — the
# same rule applied to the same 40 rollouts at two indices a switch could
# actually reach.


def test_cut_in_has_no_informative_separator_at_any_measured_index():
    """**The D-335 verdict.** The invisibility is not an artefact of reading late.

    This is the reading D-334 could not make. Had `cut_in` separated at a
    causal index, D-334's negative would have been an artefact of the hindsight
    instant and the switch would still have been on the table; it does not, at
    either causal policy, so the negative survives the one objection that could
    have overturned it.
    """
    assert sep.policies_that_separate_question_scene() == ()
    for policy in sep.INDEX_POLICIES[1:]:
        assert not sep.question_scene_is_causally_separable(policy), policy


def test_cut_in_fails_at_the_causal_indices_before_the_constant_filter_runs():
    """Empty even *un*filtered — a strictly stronger failure than D-334's.

    At the critical index `cut_in` did separate, on a constant, and the verdict
    needed :func:`constant_observables` to strike it out. At both causal
    indices there is nothing to strike out: the raw row is already empty. So
    the causal negative does not depend on the zero-spread control at all, and
    would stand even if that control were wrong.
    """
    assert sep.separating_observables(sep.QUESTION_SCENE) != ()      # D-334, filtered later
    for policy in sep.INDEX_POLICIES[1:]:
        raw = sep.causal_separation_table(policy)
        assert raw[sep.QUESTION_SCENE] == (), (policy, raw)
        # ...and the un-filtered table is not empty everywhere, so the empty row
        # above is a reading about `cut_in` rather than a broken table.
        assert any(raw[s] for s in MEASURED_SCENES), policy


def test_the_constant_stops_singling_out_cut_in_once_the_index_is_causal():
    """Why the raw row empties: the constant is read off a *different obstacle*.

    At the critical instant `cut_in`'s nearest obstacle is a static one, so
    `obstacle_speed` reads `0.0` and is unique among the five scenes. At first
    detection the nearest obstacle is the moving one, `0.75` — which
    `cafe_obstacle_crossing_v0` also carries, so the constant no longer
    separates anything. D-334 called its separator a scenario parameter; this
    is the sharper statement, that it was a parameter of an obstacle the switch
    would not even have been looking at.
    """
    assert sep.OBSERVED[sep.QUESTION_SCENE]["obstacle_speed"] == (0.0,) * SEEDS
    for policy in sep.INDEX_POLICIES[1:]:
        table = sep.CAUSAL_OBSERVED[policy]
        assert table[sep.QUESTION_SCENE]["obstacle_speed"] == (0.75,) * SEEDS
        assert (table["cafe_obstacle_crossing_v0"]["obstacle_speed"]
                == table[sep.QUESTION_SCENE]["obstacle_speed"])
        assert sep.is_constant("obstacle_speed", table), policy


def test_the_policies_disagree_away_from_the_question_scene():
    """The control fires, **and it fires red** — the table is index-dependent.

    `freezing` separates on `ttc` at a fixed 1 s and on nothing at first
    detection; `head_on` picks up `lateralness` at one index and not the other.
    Pinned as a disagreement rather than quietly narrowed to `cut_in`'s row,
    because the honest scope of every other row in this module is "at this
    index" and a green whole-table control would erase that.
    """
    assert not sep.causal_policies_agree()
    first = sep.causal_informative_table("first_detection")
    fixed = sep.causal_informative_table("fixed_time")
    assert first["cafe_freezing_v0"] == ()
    assert fixed["cafe_freezing_v0"] == ("ttc",)
    assert first["cafe_head_on_v0"] == ("closing_speed",)
    assert fixed["cafe_head_on_v0"] == ("lateralness", "closing_speed")


def test_the_question_scene_row_is_the_one_thing_all_three_indices_agree_on():
    """The narrow claim the verdict rests on, pinned apart from the broad one.

    Separated from :func:`causal_policies_agree` on purpose: that one is False
    and this one is True, and a reader who conflates them concludes either that
    the index never matters (it does) or that `cut_in`'s row is as shaky as the
    rest (it is not).
    """
    assert sep.policies_agree_on_question_scene()
    assert not sep.causal_policies_agree()


def test_the_causal_readers_never_look_past_the_read_index():
    """Causality as a property of the operator, not of the recorded numbers.

    Drives `_observables_at` off a synthetic trajectory whose future is
    *poisoned* — every quantity after the read index is garbage. A centred
    `np.gradient`, which is what the critical reader uses, would pull `k + 1`
    into the closing speed and the bearing rate and this would blow up; the
    backward difference cannot see it. This is the test that would have caught
    a re-index that forgot to change the derivative.
    """
    import numpy as np

    class _Ob:
        radius = 0.1

        def position(self, t):
            t = np.atleast_1d(t)
            xs = np.where(t <= 1.0, 5.0 - t, 1e9)      # poisoned after t = 1
            return np.stack([xs, np.zeros_like(xs)], axis=-1).squeeze()

        def velocity(self, t):
            return np.array([-1.0, 0.0])

    t = np.linspace(0.0, 2.0, 21)
    traj = np.zeros((t.size, 6))
    traj[:, 0] = t
    k = int(np.argmin(np.abs(t - 1.0)))
    got = sep._observables_at(traj, [_Ob()], 0.1, k)
    assert all(np.isfinite(v) for v in got.values()), got
    assert got["closing_speed"] == pytest.approx(1.0, abs=1e-6)


def test_every_causal_policy_is_recorded_and_every_recorded_policy_is_causal():
    """Bidirectional, per the `OBSERVABLES`/`OBSERVED` pin above.

    `critical` is deliberately absent from `CAUSAL_OBSERVED` — its table *is*
    `OBSERVED`, and a second copy could drift from the first.
    """
    assert set(sep.CAUSAL_OBSERVED) == set(sep.INDEX_POLICIES[1:])
    assert "critical" not in sep.CAUSAL_OBSERVED
    for policy, table in sep.CAUSAL_OBSERVED.items():
        assert set(table) == set(MEASURED_SCENES), policy
        for scene, row in table.items():
            assert set(row) == set(sep.CAUSAL_OBSERVABLES), (policy, scene)
            for observable, values in row.items():
                assert len(values) == SEEDS, (policy, scene, observable)


def test_the_causal_registry_swaps_exactly_the_hindsight_column():
    """`min_ttc` has no causal counterpart; `ttc` replaces it, and only it.

    An episode-wide minimum needs the episode to have finished. Pinned as a
    set difference so a later cycle that adds an observable to one registry and
    not the other goes red rather than producing two tables that silently
    cannot be compared.
    """
    assert set(sep.OBSERVABLES) - set(sep.CAUSAL_OBSERVABLES) == {"min_ttc"}
    assert set(sep.CAUSAL_OBSERVABLES) - set(sep.OBSERVABLES) == {"ttc"}


def test_the_table_argument_leaves_the_hindsight_reading_untouched():
    """The refactor is a widening, not a re-measurement.

    Every operator grew an optional `table`; the default path must still be the
    D-334 reading, byte for byte. The re-take also confirmed this at the source
    — its `critical` sub-table reproduced `OBSERVED` exactly — but that costs
    40 rollouts and this costs nothing.
    """
    assert sep.separation_table() == sep.SEPARATION
    assert {s: sep.informative_separators(s) for s in MEASURED_SCENES} \
        == sep.INFORMATIVE_SEPARATION
    for scene in MEASURED_SCENES:
        assert (sep.separating_observables(scene, None)
                == sep.separating_observables(scene, sep.OBSERVED))
