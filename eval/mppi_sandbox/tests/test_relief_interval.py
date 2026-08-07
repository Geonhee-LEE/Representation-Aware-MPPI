# SPDX-License-Identifier: BSD-3-Clause
"""Q-111's survey: when one weight serves every scene, and when that is only
an artefact of how the question was arithmetic-ed."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import barrier_ceiling as bc
from eval.mppi_sandbox import relief_interval as ri
from eval.mppi_sandbox.scenario import load_scenario

#: Same convention as `test_barrier_ceiling`: every synthetic rung names the
#: temperature it belongs to rather than inheriting `MPPIParams.lam`'s shipped
#: 0.1, where the softmax is argmin-over-draws and no additive term is audible.
LAM = 0.8


def rung(value, unsafe, *, reached=True, band=True) -> bc.Rung:
    return bc.Rung(
        knob=bc.WEIGHT_KNOB, value=value, n=8, unsafe_rate=unsafe,
        mean_clearance=0.01, min_clearance=0.005, all_reached=reached,
        median_ess=64.0, ess_in_band=band,
    )


def result(scenario, baseline_unsafe, rungs) -> bc.SweepResult:
    base = rung(10.0, baseline_unsafe)
    return bc.SweepResult(
        scenario=scenario, knob=bc.WEIGHT_KNOB, lam=LAM, margin=0.30,
        baseline=base, rungs=tuple(rungs),
        verdict=bc.classify(base, rungs),
    )


def interval(scenario, *, needs, admissible, relieving, verdict):
    return ri.ReliefInterval(
        scenario=scenario, lam=LAM, baseline_value=10.0,
        baseline_unsafe=1.0 if needs else 0.0, needs_relief=needs,
        admissible=tuple(admissible), relieving=tuple(relieving),
        verdict=verdict,
    )


# --------------------------------------------------------------------------
# classify_scene — the two thresholds that must not be shared.
# --------------------------------------------------------------------------

def test_one_unsafe_seed_in_eight_still_needs_relief():
    """`needs_relief` is `> 0`, not `>= MIN_IMPROVEMENT`.

    The two bars answer different questions: MIN_IMPROVEMENT asks whether one
    rung distinguishes itself from another at n=8 (a resolution question),
    while `needs_relief` asks whether the scene has a safety problem at all.
    One unsafe seed in eight is 0.125 — a real problem — and reusing the
    resolution bar here would declare it clean.
    """
    scene = ri.classify_scene(result("a", 0.125, [rung(300.0, 0.0)]))
    assert scene.needs_relief and scene.resolvable
    assert scene.verdict == ri.RELIEF_FOUND


def test_a_gap_below_the_resolution_bar_is_not_the_knobs_failure():
    """A scene unsafe by less than MIN_IMPROVEMENT cannot be improved on by
    MIN_IMPROVEMENT, so *every* rung — including a perfect one — fails the
    relief test for arithmetic reasons. Calling that `UNRELIEVED` would blame
    the weight for the ensemble being too small, and would let such a scene
    veto a repin on a difference the survey cannot measure."""
    scene = ri.classify_scene(result("a", 0.05, [rung(300.0, 0.0)]))
    assert scene.needs_relief and not scene.resolvable
    assert scene.verdict == ri.SUBRESOLUTION
    # It votes with `admissible`: it may refuse a rung, not demand one.
    assert scene.permits == frozenset({300.0})


def test_a_subresolution_scene_does_not_make_the_survey_unrelievable():
    survey = ri.reconcile([
        ri.classify_scene(result("tiny", 0.05, [rung(300.0, 0.0)])),
        interval("needs", needs=True, admissible=[300.0], relieving=[300.0],
                 verdict=ri.RELIEF_FOUND),
    ])
    assert survey.verdict == ri.GLOBAL_REPIN
    assert survey.witness == 300.0
    assert survey.subresolution == ("tiny",)


def test_a_clean_baseline_needs_no_relief():
    scene = ri.classify_scene(result("convoy", 0.0, [rung(300.0, 0.0)]))
    assert not scene.needs_relief
    assert scene.verdict == ri.NO_RELIEF_NEEDED


def test_an_inadmissible_rung_never_relieves():
    """The rung that drops `unsafe_rate` by leaving the ESS band is
    `BOUGHT_INADMISSIBLY` upstream and must not appear as relief here."""
    scene = ri.classify_scene(
        result("a", 1.0, [rung(300.0, 0.0, band=False),
                          rung(1000.0, 0.0, reached=False)]))
    assert scene.relieving == ()
    assert scene.admissible == ()
    assert scene.verdict == ri.UNRELIEVED


def test_relief_must_clear_the_resolution_bar():
    """A rung improving by less than half a seed is not distinguishable from
    its neighbour at n=8, so it is not relief."""
    scene = ri.classify_scene(result("a", 1.0, [rung(300.0, 0.99)]))
    assert scene.relieving == ()
    assert scene.verdict == ri.UNRELIEVED


def test_threshold_is_cheapest_and_ceiling_is_largest_tolerated():
    scene = ri.classify_scene(
        result("a", 1.0, [rung(30.0, 1.0), rung(100.0, 0.0),
                          rung(300.0, 0.0), rung(1000.0, 0.0, band=False)]))
    assert scene.threshold == 100.0     # cheapest *relieving* rung
    assert scene.ceiling == 300.0       # largest *admissible* rung, relief or not
    assert scene.admissible == (30.0, 100.0, 300.0)


def test_threshold_and_ceiling_are_none_when_nothing_survives():
    scene = ri.classify_scene(result("a", 1.0, [rung(300.0, 0.0, band=False)]))
    assert scene.threshold is None and scene.ceiling is None


# --------------------------------------------------------------------------
# reconcile — a set intersection, and why it may not be an interval one.
# --------------------------------------------------------------------------

def test_a_shared_rung_is_a_witness():
    survey = ri.reconcile([
        interval("needs", needs=True, admissible=[100.0, 300.0],
                 relieving=[300.0], verdict=ri.RELIEF_FOUND),
        interval("clean", needs=False, admissible=[100.0, 300.0],
                 relieving=[], verdict=ri.NO_RELIEF_NEEDED),
    ])
    assert survey.verdict == ri.GLOBAL_REPIN
    assert survey.witness == 300.0


def test_the_witness_is_the_cheapest_serving_rung():
    survey = ri.reconcile([
        interval("needs", needs=True, admissible=[100.0, 300.0, 1000.0],
                 relieving=[100.0, 300.0, 1000.0], verdict=ri.RELIEF_FOUND),
        interval("clean", needs=False, admissible=[100.0, 300.0, 1000.0],
                 relieving=[], verdict=ri.NO_RELIEF_NEEDED),
    ])
    assert survey.witnesses == (100.0, 300.0, 1000.0)
    assert survey.witness == 100.0


def test_a_clean_scene_constrains_from_above():
    """This is D-125's convoy: it needs nothing and still gets a vote, because
    a repin runs on it too. Its admissible set is the ceiling on the repin."""
    survey = ri.reconcile([
        interval("needs", needs=True, admissible=[300.0],
                 relieving=[300.0], verdict=ri.RELIEF_FOUND),
        interval("clean", needs=False, admissible=[30.0, 100.0],
                 relieving=[], verdict=ri.NO_RELIEF_NEEDED),
    ])
    assert survey.verdict == ri.PER_SCENE_REQUIRED
    assert survey.witness is None


def test_intersection_is_over_sets_not_intervals():
    """The load-bearing test of this module.

    Scene `gappy` is admissible at 30 and 300 but **not** at 100 — nothing in
    this repo argues `all_reached AND ess_in_band` is monotone in the weight,
    so a mid-ladder hole is permitted. Under interval arithmetic its span is
    [30, 300], which intersects `clean`'s [100, 100] at 100 and would nominate
    a rung that is inadmissible on the very scene it came from. The set
    intersection is empty, which is the true answer.
    """
    survey = ri.reconcile([
        interval("gappy", needs=True, admissible=[30.0, 300.0],
                 relieving=[30.0, 300.0], verdict=ri.RELIEF_FOUND),
        interval("clean", needs=False, admissible=[100.0],
                 relieving=[], verdict=ri.NO_RELIEF_NEEDED),
    ])
    assert 100.0 not in survey.witnesses
    assert survey.verdict == ri.PER_SCENE_REQUIRED


def test_an_unrelievable_scene_outranks_an_empty_intersection():
    """`PER_SCENE_REQUIRED` says "no *shared* rung"; a per-scene policy fixes
    that. `UNRELIEVED` says a scene has no rung at all, which it does not."""
    survey = ri.reconcile([
        interval("hopeless", needs=True, admissible=[], relieving=[],
                 verdict=ri.UNRELIEVED),
        interval("fine", needs=False, admissible=[300.0], relieving=[],
                 verdict=ri.NO_RELIEF_NEEDED),
    ])
    assert survey.verdict == ri.UNRELIEVABLE
    assert survey.unrelieved == ("hopeless",)
    assert survey.witness is None


def test_a_scene_needing_relief_votes_with_relieving_not_admissible():
    """`permits` differs by `needs_relief`, and that asymmetry is the point:
    a rung that is merely tolerable does not fix a scene that is 8/8 unsafe."""
    needs = interval("needs", needs=True, admissible=[30.0, 300.0],
                     relieving=[300.0], verdict=ri.RELIEF_FOUND)
    clean = interval("clean", needs=False, admissible=[30.0, 300.0],
                     relieving=[], verdict=ri.NO_RELIEF_NEEDED)
    assert needs.permits == frozenset({300.0})
    assert clean.permits == frozenset({30.0, 300.0})


def test_an_empty_survey_is_not_a_global_repin():
    """Every scene refused ⇒ nothing was measured. The convenient reading of
    an empty intersection over an empty set is `all()` → True; refuse it."""
    survey = ri.reconcile([], {"a": ri.NO_DECLARED_MARGIN})
    assert survey.verdict != ri.GLOBAL_REPIN
    assert survey.witness is None


# --------------------------------------------------------------------------
# Refusals — named, not dropped.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("scene_file,expected", [
    ("cafe_freezing_v0.yaml", ri.NO_DECLARED_MARGIN),
    ("cafe_cut_in_v0.yaml", ri.NO_ADMISSIBLE_LAM),
    ("cafe_head_on_v0.yaml", None),
    ("cafe_obstacle_crossing_v0.yaml", None),
    ("cafe_convoy_v0.yaml", None),
])
def test_which_obstacle_scenes_can_be_swept(scene_file, expected):
    """Q-111's action line says "all five obstacle-bearing scenes"; two of
    them refuse, for two different pre-existing reasons. Pinned so a later
    scene edit that silently makes one sweepable shows up as a diff."""
    scen = load_scenario(f"eval/scenarios/{scene_file}")
    assert ri.sweepable(scen, scene_file) == expected


def test_refusals_survive_into_the_survey_and_its_report():
    survey = ri.reconcile(
        [interval("head_on", needs=True, admissible=[300.0],
                  relieving=[300.0], verdict=ri.RELIEF_FOUND)],
        {"cafe_freezing_v0.yaml": ri.NO_DECLARED_MARGIN},
    )
    assert survey.refused["cafe_freezing_v0.yaml"] == ri.NO_DECLARED_MARGIN
    assert "REFUSED" in str(survey) and "cafe_freezing_v0.yaml" in str(survey)


# --------------------------------------------------------------------------
# The ladder and the knob it moves.
# --------------------------------------------------------------------------

def test_ladder_is_geometric_and_brackets_the_shipped_weight():
    """The knob is a gain, so ladder density belongs in log space; and a
    ladder that does not start above the shipped weight cannot find a
    threshold above it."""
    ladder = ri.DEFAULT_LADDER
    ratios = [b / a for a, b in zip(ladder, ladder[1:])]
    assert all(r > 1.0 for r in ratios)
    assert min(ladder) > ri.shipped_weight()
    assert 300.0 in ladder          # D-125's relieving rung must be tested


def test_shipped_weight_is_read_not_restated():
    """One statement of the default (D-047) — it comes off `MPPIParams`."""
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
    assert ri.shipped_weight() == getattr(MPPIParams(), bc.WEIGHT_KNOB)
