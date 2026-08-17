# SPDX-License-Identifier: BSD-3-Clause
"""The clearance census covers the registry and agrees with D-326's pair."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import clearance_census as cc
from eval.mppi_sandbox.controllers import REGISTRY
from eval.mppi_sandbox.essps import PER_ITERATION_ARMS
from eval.mppi_sandbox.scenario import load_scenario


@pytest.fixture(scope="module")
def scene():
    return load_scenario(cc.SCENE_PATH)


def test_census_covers_every_registry_arm():
    """No arm is silently outside the population.

    A census whose population is smaller than it looks reads exactly like a
    clean one (D-107/D-317), and this one's whole claim is "no arm on this
    branch bought clearance" — which is false the moment an arm is missing.
    """
    assert set(cc.SHIPPED_ARM_CLEARANCE) == set(REGISTRY)


def test_representation_arms_are_registry_arms_minus_the_named_exclusions():
    """`REPRESENTATION_ARMS` excludes exactly the baseline, `cbf_mppi` and
    `geometric_mppi` — the arms that are not representation work — and the
    exclusion is stated here rather than left to the reader to infer."""
    excluded = set(REGISTRY) - set(cc.REPRESENTATION_ARMS)
    assert excluded == {cc.BASELINE, "cbf_mppi", "geometric_mppi"}


def test_epistemic_split_is_derived_not_typed(scene):
    """The hand-written kwarg census matches what the constructors do.

    This is the guard that lets a future cycle add a `REGISTRY` line without
    reading this module: if the new arm lands on the wrong side of the split,
    `retake` would run it at an operating point the census does not describe.
    """
    derived = {n for n in REGISTRY if cc.takes_epistemic_kwargs(n, scene)}
    assert derived == set(cc.EPISTEMIC_ARMS)


def test_shared_rows_agree_with_d326():
    """`essps_mppi` / `risk_mppi` clearance matches `PER_ITERATION_ARMS`.

    The two constants were measured by separate scripts at the same operating
    point; pinning them equal is what makes this census a re-take of D-326's
    pair rather than an unrelated pair of numbers that happen to sit nearby.
    """
    for arm in ("essps_mppi", "risk_mppi"):
        assert cc.SHIPPED_ARM_CLEARANCE[arm][0] == PER_ITERATION_ARMS[arm][7]


def test_no_representation_arm_out_clears_plain_mppi():
    """The bottleneck's answer, as an assertion.

    Stated in the direction that can go stale: if a later cycle ships a
    representation arm that *does* beat plain MPPI, this test goes red and the
    module's headline paragraph has to be rewritten — which is the point.
    """
    v = cc.grade()
    assert v.any_representation_buys_clearance is False
    assert v.representation_gain < 0.0
    assert v.best_representation == "gap_gated_mppi"


def test_best_overall_is_a_constraint_method_not_a_representation():
    """`cbf_mppi` wins the census and is excluded from the representation set,
    so the headline cannot be read as a representation win."""
    v = cc.grade()
    assert v.best_overall == "cbf_mppi"
    assert v.best_overall not in cc.REPRESENTATION_ARMS
    assert v.best_overall_clearance > v.baseline


def test_the_gaps_are_larger_than_the_one_d326_declined_to_claim():
    """D-326 would not call `0.0128 m` a regression. The gaps here are an order
    of magnitude larger, which is the whole reason the sign is claimable."""
    d326_unclaimable = abs(PER_ITERATION_ARMS["essps_mppi"][7]
                           - PER_ITERATION_ARMS["risk_mppi"][7])
    v = cc.grade()
    worst = min(cc.SHIPPED_ARM_CLEARANCE[n][0] for n in cc.REPRESENTATION_ARMS)
    assert abs(v.baseline - worst) > 10 * d326_unclaimable


def test_format_grade_names_the_confound():
    text = cc.format_grade()
    assert "baseline" in text
    assert "any_representation_buys_clearance = False" in text
    assert len(text.splitlines()) == len(REGISTRY) + 7


def test_geometric_arm_is_indistinguishable_from_the_baseline():
    """`geometric_mppi` reproduces `stock_mppi` to every recorded digit.

    Pinned rather than mentioned: three identical numbers (clearance,
    completion, steps) is the signature of a channel that is **inert** at this
    operating point, not of two controllers that happen to agree. If a later
    cycle makes the geometric channel bite, this goes red and the census's
    reading of it as "not representation work" has to be revisited.
    """
    assert (cc.SHIPPED_ARM_CLEARANCE["geometric_mppi"]
            == cc.SHIPPED_ARM_CLEARANCE[cc.BASELINE])
