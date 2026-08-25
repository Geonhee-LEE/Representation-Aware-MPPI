# SPDX-License-Identifier: BSD-3-Clause
"""`comparison_headroom` — a verdict on whether an A/B could separate its arms.

The pins that matter are the two degenerate cases staying *apart* and the
`sub_margin` flag firing on the shape D-124 actually shipped. Everything here
is analytic — no sim — because the predicate is a function of clearances and a
margin, and pinning it against a sweep would make the test a weather report.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import comparison_headroom as ch

MARGIN = 0.40


def _arm(name: str, clearances) -> ch.ArmSafety:
    return ch.ArmSafety(arm=name, clearances=tuple(clearances), margin=MARGIN)


def _hr(a_clear, b_clear, *, weight: float = 10.0, lam: float = 0.8,
        scenario: str = "cafe_head_on_v0") -> ch.Headroom:
    return ch.Headroom(scenario=scenario, weight=weight, lam=lam,
                       a=_arm("stock_mppi", a_clear),
                       b=_arm("gap_gated_mppi", b_clear))


def test_both_arms_below_margin_is_unscorable():
    """D-124's shipped operating point: both arms unsafe on every seed."""
    hr = _hr([0.005, 0.006, 0.004], [0.009, 0.010, 0.008])
    assert hr.verdict == ch.NO_HEADROOM_UNSAFE
    assert not hr.scorable
    # And the delta is real — 1.7×-ish — which is exactly why the verdict has
    # to be taken from the boundary and not from the improvement.
    assert hr.b.mean_clearance > hr.a.mean_clearance


def test_both_arms_above_margin_is_also_unscorable_but_not_the_same_word():
    """The measured `w = 3000` case. Same experimental defect, opposite state
    of the system — merging the two names would print "we fixed it" and "we
    cannot touch it" identically."""
    hr = _hr([1.10, 1.12, 1.11], [1.11, 1.12, 1.12], weight=3000.0)
    assert hr.verdict == ch.NO_HEADROOM_SAFE
    assert not hr.scorable
    assert ch.NO_HEADROOM_SAFE != ch.NO_HEADROOM_UNSAFE


def test_straddling_margin_with_equal_rates_is_a_real_null():
    hr = _hr([0.10, 0.50, 0.60], [0.20, 0.55, 0.65])
    assert hr.verdict == ch.TIED
    assert hr.scorable, "a tie the experiment could have broken is scorable"


def test_differing_unsafe_rates_separate():
    hr = _hr([0.10, 0.20, 0.60], [0.50, 0.55, 0.65])
    assert hr.verdict == ch.SEPARATED
    assert hr.scorable
    assert hr.delta_unsafe == pytest.approx(-2 / 3), "signed b − a"


def test_sub_margin_flags_an_improvement_that_never_crosses_the_line():
    below = _hr([0.005, 0.006, 0.004], [0.009, 0.010, 0.008])
    assert below.sub_margin
    across = _hr([0.10, 0.50, 0.60], [0.20, 0.55, 0.65])
    assert not across.sub_margin


def test_margin_boundary_is_closed_below():
    """`near_miss.classify` grades `clearance < margin` unsafe, so a run *at*
    the margin is safe. Headroom reads the same boundary or the two disagree
    about the same ensemble."""
    hr = _hr([MARGIN, MARGIN], [MARGIN, MARGIN])
    assert hr.verdict == ch.NO_HEADROOM_SAFE


def test_mismatched_margins_refuse():
    a = ch.ArmSafety(arm="a", clearances=(0.1,), margin=0.40)
    b = ch.ArmSafety(arm="b", clearances=(0.1,), margin=0.30)
    with pytest.raises(ValueError, match="different margins"):
        ch.Headroom(scenario="s", weight=10.0, lam=0.8, a=a, b=b)


@pytest.mark.parametrize("margin", [None, 0.0, -1.0])
def test_unscorable_margin_refuses(margin):
    """A scene with no declared margin is excluded by name, not graded — the
    same rule `near_miss.score` enforces one layer down."""
    a = ch.ArmSafety(arm="a", clearances=(0.1,), margin=margin)
    b = ch.ArmSafety(arm="b", clearances=(0.1,), margin=margin)
    with pytest.raises(ValueError, match="not scorable"):
        ch.Headroom(scenario="s", weight=10.0, lam=0.8, a=a, b=b)


class TestShift:
    """`shift` is what retro-actively grades a published claim."""

    def test_measured_head_on_rescore_is_still_unscorable(self):
        """The cycle's actual finding: 10 → 3000 swaps one degenerate verdict
        for the other, so re-running above the relief threshold did **not**
        rescue D-124's comparison."""
        before = _hr([0.005, 0.006], [0.009, 0.010], weight=10.0)
        after = _hr([1.10, 1.12], [1.11, 1.12], weight=3000.0)
        assert before.verdict == ch.NO_HEADROOM_UNSAFE
        assert after.verdict == ch.NO_HEADROOM_SAFE
        assert ch.shift(before, after) == ch.STILL_UNSCORABLE

    def test_bought_headroom(self):
        before = _hr([0.005, 0.006], [0.009, 0.010], weight=10.0)
        after = _hr([0.10, 0.50], [0.55, 0.65], weight=100.0)
        assert ch.shift(before, after) == ch.BOUGHT_HEADROOM

    def test_lost_headroom(self):
        before = _hr([0.10, 0.50], [0.55, 0.65], weight=100.0)
        after = _hr([1.10, 1.12], [1.11, 1.12], weight=3000.0)
        assert ch.shift(before, after) == ch.LOST_HEADROOM

    def test_scorable_throughout(self):
        before = _hr([0.10, 0.50], [0.55, 0.65], weight=100.0)
        after = _hr([0.20, 0.50], [0.55, 0.65], weight=300.0)
        assert ch.shift(before, after) == ch.SCORABLE_THROUGHOUT

    def test_risk_channel_separates_only_below_the_relief_threshold(self):
        """The cycle's positive finding, pinned as the shape it has: the one
        rung where the risk channel's A/B is a test (`w = 100`) sits *below*
        the relief threshold (300), above which both arms pass and the
        comparison goes dead again."""
        at_100 = ch.Headroom(
            scenario="cafe_head_on_v0", weight=100.0, lam=0.8,
            a=_arm("stock_mppi", [0.10] * 8),
            b=_arm("risk_mppi", [0.10, 0.10] + [0.50] * 6))
        at_300 = ch.Headroom(
            scenario="cafe_head_on_v0", weight=300.0, lam=0.8,
            a=_arm("stock_mppi", [0.49] * 8),
            b=_arm("risk_mppi", [0.62] * 8))
        assert at_100.verdict == ch.SEPARATED
        assert at_100.delta_unsafe == pytest.approx(-0.75), "risk safer by 0.75"
        assert at_300.verdict == ch.NO_HEADROOM_SAFE
        assert ch.shift(at_100, at_300) == ch.LOST_HEADROOM

    def test_shift_across_scenes_refuses(self):
        before = _hr([0.005], [0.009], scenario="cafe_head_on_v0")
        after = _hr([0.10], [0.55], scenario="cafe_convoy_v0")
        with pytest.raises(ValueError, match="across scenes"):
            ch.shift(before, after)


def test_render_is_one_line_per_operating_point():
    rows = [_hr([0.005], [0.009], weight=10.0),
            _hr([1.10], [1.11], weight=3000.0)]
    out = ch.render(rows)
    assert len(out.splitlines()) == 2
    assert "NO_HEADROOM_UNSAFE" in out and "NO_HEADROOM_SAFE" in out
    assert "SUB_MARGIN" in out, "the sub-margin caveat travels with the row"
