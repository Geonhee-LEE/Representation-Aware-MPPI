# SPDX-License-Identifier: BSD-3-Clause
"""`scorable_band` — the width and edges of the region where an A/B can score.

The measured case these are modelled on is D-131/D-132: `cafe_head_on_v0` at
lam = 0.8, `risk_mppi` vs `stock_mppi`, walking `w_obs_soft`.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox.comparison_headroom import (
    ArmSafety,
    Headroom,
    NO_HEADROOM_SAFE,
    NO_HEADROOM_UNSAFE,
    SEPARATED,
)
from eval.mppi_sandbox.relief_interval import open_above, open_below
from eval.mppi_sandbox.scorable_band import (
    BAND_CLOSED,
    BAND_OPEN_ABOVE,
    BAND_OPEN_BELOW,
    BAND_OPEN_BOTH,
    BAND_SPLIT,
    BOUNDED,
    ESS_OUT_OF_BAND,
    ESS_UNMEASURED,
    NO_SCORABLE_RUNG,
    BandRung,
    ScorableBand,
    render,
)

MARGIN = 0.40
SCENE = "cafe_head_on_v0"
LAM = 0.8


def _headroom(weight, a_clear, b_clear, *, scenario=SCENE, lam=LAM):
    return Headroom(
        scenario=scenario,
        weight=weight,
        lam=lam,
        a=ArmSafety("stock_mppi", tuple(a_clear), MARGIN),
        b=ArmSafety("risk_mppi", tuple(b_clear), MARGIN),
    )


def _unsafe(weight, **kw):
    """Both arms below the margin everywhere — `NO_HEADROOM_UNSAFE`."""
    return _headroom(weight, (0.01,) * 4, (0.02,) * 4, **kw)


def _safe(weight, **kw):
    """Both arms above the margin everywhere — `NO_HEADROOM_SAFE`."""
    return _headroom(weight, (1.1,) * 4, (1.2,) * 4, **kw)


def _separated(weight, **kw):
    """Margin crossed, arms differ — the only verdict a claim can ride on."""
    return _headroom(weight, (0.01,) * 4, (0.01, 0.9, 0.9, 0.9), **kw)


def _rung(headroom, ess=True):
    return BandRung(headroom, ess_in_band=ess)


# --- the fixtures encode the verdicts the module is built on -----------------


def test_fixtures_produce_the_three_headroom_verdicts():
    assert _unsafe(30.0).verdict == NO_HEADROOM_UNSAFE
    assert _safe(300.0).verdict == NO_HEADROOM_SAFE
    assert _separated(100.0).verdict == SEPARATED


# --- a rung's own grading ----------------------------------------------------


def test_ess_out_of_band_rung_is_refused_not_scorable():
    """D-131: at w=30 both arms left the ESS band at a lam admissible at 10,
    100 and 300. A verdict taken there is about the softmax."""
    rung = BandRung(_separated(30.0), ess_in_band=False)
    assert rung.refusal == ESS_OUT_OF_BAND
    assert not rung.graded
    assert not rung.scorable
    # the underlying headroom is untouched — refusal is the experiment's
    # admissibility, not a claim the margin was not crossed
    assert rung.headroom.scorable


def test_unmeasured_ess_is_refused_rather_than_assumed_compliant():
    rung = BandRung(_separated(100.0), ess_in_band=None)
    assert rung.refusal == ESS_UNMEASURED
    assert not rung.scorable


def test_band_rung_has_no_default_ess_so_omission_cannot_read_as_pass():
    with pytest.raises(TypeError):
        BandRung(_separated(100.0))  # type: ignore[call-arg]


# --- the measured D-131 shape ------------------------------------------------


def test_single_scorable_rung_between_two_witnesses_is_a_closed_band():
    band = ScorableBand(
        (_rung(_unsafe(30.0)), _rung(_separated(100.0)), _rung(_safe(300.0)))
    )
    assert band.verdict == BAND_CLOSED
    assert band.scorable == (100.0,)
    assert band.width_rungs == 1
    assert band.single_rung
    assert band.span == (100.0, 100.0)
    # and the honest part: a closed band still only locates its edges to the
    # resolution of the ladder that found it
    assert band.edge_below == (30.0, 100.0)
    assert band.edge_above == (100.0, 300.0)
    assert band.verdict in BOUNDED


def test_densifying_turns_the_point_into_a_width_without_new_verdict_names():
    band = ScorableBand(
        tuple(
            _rung(h)
            for h in (
                _unsafe(30.0),
                _unsafe(75.0),
                _separated(100.0),
                _separated(150.0),
                _separated(200.0),
                _safe(300.0),
            )
        )
    )
    assert band.verdict == BAND_CLOSED
    assert band.width_rungs == 3
    assert not band.single_rung
    assert band.span == (100.0, 200.0)
    assert band.edge_below == (75.0, 100.0)
    assert band.edge_above == (200.0, 300.0)


# --- openness: a band that runs off the ladder --------------------------------


def test_band_touching_the_top_graded_rung_is_open_above():
    band = ScorableBand(
        (_rung(_unsafe(30.0)), _rung(_separated(100.0)), _rung(_separated(300.0)))
    )
    assert band.verdict == BAND_OPEN_ABOVE
    assert band.open_above and not band.open_below
    assert band.edge_above is None  # unwitnessed — not silently the ladder top
    assert band.edge_below == (30.0, 100.0)
    assert band.verdict not in BOUNDED


def test_band_touching_the_bottom_graded_rung_is_open_below():
    band = ScorableBand(
        (_rung(_separated(30.0)), _rung(_separated(100.0)), _rung(_safe(300.0)))
    )
    assert band.verdict == BAND_OPEN_BELOW
    assert band.open_below and not band.open_above
    assert band.edge_below is None


def test_every_graded_rung_scorable_is_open_both_ways():
    band = ScorableBand((_rung(_separated(100.0)), _rung(_separated(150.0))))
    assert band.verdict == BAND_OPEN_BOTH
    assert band.edge_below is None and band.edge_above is None
    assert band.span == (100.0, 150.0)  # a lower bound, and BOUNDED says so
    assert band.verdict not in BOUNDED


def test_openness_delegates_to_the_relief_interval_predicates():
    """One statement of `runs to the end of what was tested` (D-047)."""
    band = ScorableBand(
        (_rung(_unsafe(30.0)), _rung(_separated(100.0)), _rung(_separated(300.0)))
    )
    assert band.open_above is open_above(band.scorable, band.graded)
    assert band.open_below is open_below(band.scorable, band.graded)


def test_open_below_mirrors_open_above_on_the_same_inputs():
    assert open_below((30.0, 100.0), (30.0, 100.0, 300.0)) is True
    assert open_below((100.0,), (30.0, 100.0, 300.0)) is False
    assert open_below((), (30.0,)) is False
    assert open_below((30.0,), ()) is False


# --- non-contiguity: the D-127 two-islands shape, one axis over ---------------


def test_scorable_set_with_a_graded_hole_is_a_split_not_a_span():
    band = ScorableBand(
        tuple(
            _rung(h)
            for h in (
                _unsafe(30.0),
                _separated(100.0),
                _safe(150.0),
                _separated(200.0),
                _safe(300.0),
            )
        )
    )
    assert band.verdict == BAND_SPLIT
    assert not band.contiguous
    assert band.scorable == (100.0, 200.0)
    assert band.width_rungs == 2  # two rungs, not the three the span implies
    assert band.span == (100.0, 200.0)


def test_split_band_keeps_both_edge_brackets():
    band = ScorableBand(
        tuple(
            _rung(h)
            for h in (
                _unsafe(30.0),
                _separated(100.0),
                _safe(150.0),
                _separated(200.0),
                _safe(300.0),
            )
        )
    )
    assert band.edge_below == (30.0, 100.0)
    assert band.edge_above == (200.0, 300.0)
    assert band.verdict in BOUNDED


# --- refused rungs do not witness edges ---------------------------------------


def test_a_refused_rung_below_the_band_leaves_the_lower_edge_open():
    """Knowing nothing about a rung is not the same as knowing it fails."""
    band = ScorableBand(
        (
            BandRung(_unsafe(30.0), ess_in_band=False),
            _rung(_separated(100.0)),
            _rung(_safe(300.0)),
        )
    )
    assert band.graded == (100.0, 300.0)
    assert band.verdict == BAND_OPEN_BELOW
    assert band.edge_below is None
    assert band.refused == ((30.0, ESS_OUT_OF_BAND),)


def test_a_refused_rung_inside_the_span_is_a_hole_not_a_bridge():
    band = ScorableBand(
        (
            _rung(_separated(100.0)),
            BandRung(_safe(150.0), ess_in_band=None),
            _rung(_separated(200.0)),
            _rung(_safe(300.0)),
        )
    )
    assert band.contiguous  # among the graded rungs, yes
    assert band.interior_refused == (150.0,)  # but the interval has a hole
    assert band.verdict == BAND_OPEN_BELOW
    assert "interior holes" in str(band)


def test_interior_refused_is_empty_when_no_refusal_falls_inside():
    band = ScorableBand(
        (
            BandRung(_unsafe(30.0), ess_in_band=False),
            _rung(_separated(100.0)),
            _rung(_separated(200.0)),
        )
    )
    assert band.refused == ((30.0, ESS_OUT_OF_BAND),)
    assert band.interior_refused == ()


# --- degenerate ladders --------------------------------------------------------


def test_no_scorable_rung_reports_the_ladder_it_walked():
    band = ScorableBand((_rung(_unsafe(30.0)), _rung(_safe(300.0))))
    assert band.verdict == NO_SCORABLE_RUNG
    assert band.span is None
    assert band.width_rungs == 0
    assert not band.single_rung
    assert band.edge_below is None and band.edge_above is None
    assert band.tested == (30.0, 300.0)  # the finding is partly about this


def test_all_rungs_refused_is_no_scorable_rung_with_every_reason_named():
    band = ScorableBand(
        (
            BandRung(_separated(100.0), ess_in_band=False),
            BandRung(_separated(150.0), ess_in_band=None),
        )
    )
    assert band.verdict == NO_SCORABLE_RUNG
    assert band.graded == ()
    assert band.refused == ((100.0, ESS_OUT_OF_BAND), (150.0, ESS_UNMEASURED))


# --- construction guards --------------------------------------------------------


def test_empty_band_is_refused():
    with pytest.raises(ValueError, match="zero rungs"):
        ScorableBand(())


def test_rungs_are_sorted_by_weight_regardless_of_input_order():
    band = ScorableBand(
        (_rung(_safe(300.0)), _rung(_unsafe(30.0)), _rung(_separated(100.0)))
    )
    assert band.tested == (30.0, 100.0, 300.0)
    assert band.verdict == BAND_CLOSED


def test_mixed_scenes_are_refused():
    with pytest.raises(ValueError, match="one scene"):
        ScorableBand(
            (
                _rung(_separated(100.0)),
                _rung(_separated(150.0, scenario="cafe_convoy_v0")),
            )
        )


def test_mixed_temperatures_are_refused():
    """D-131: lam windows are not weight-invariant, so a walk that changes both
    axes at once cannot attribute the band to either."""
    with pytest.raises(ValueError, match="fixed temperature"):
        ScorableBand(
            (_rung(_separated(100.0)), _rung(_separated(150.0, lam=3.2)))
        )


def test_duplicate_rung_is_a_disagreement_not_a_band():
    with pytest.raises(ValueError, match="duplicate rung"):
        ScorableBand((_rung(_separated(100.0)), _rung(_safe(100.0))))


# --- a separation the survey cannot resolve --------------------------------------


def _one_run(weight):
    """Arms differ by exactly one run out of eight — D-132's `w = 250`."""
    return _headroom(weight, (0.9,) * 8, (0.01,) + (0.9,) * 7)


def test_a_one_run_separation_is_scorable_and_named_as_such():
    rung = _rung(_one_run(250.0))
    assert rung.scorable  # SEPARATED by the letter of the definition
    assert rung.separation_runs == 1


def test_separation_runs_counts_runs_not_rates():
    h = _headroom(100.0, (0.01,) * 8, (0.01,) * 3 + (0.9,) * 5)
    assert _rung(h).separation_runs == 5


def test_separation_runs_is_none_for_unequal_seed_counts():
    h = _headroom(100.0, (0.01,) * 8, (0.01,) * 2 + (0.9,) * 2)
    assert _rung(h).separation_runs is None


def test_a_split_bought_by_one_run_says_so():
    """The measured D-132 shape: three real rungs, then an isolated singleton
    at the top whose whole separation is one seed and points the other way."""
    band = ScorableBand(
        tuple(
            _rung(h)
            for h in (
                _unsafe(55.0),
                _separated(75.0),
                _separated(100.0),
                _safe(200.0),
                _one_run(250.0),
                _safe(300.0),
            )
        )
    )
    assert band.verdict == BAND_SPLIT
    assert band.scorable == (75.0, 100.0, 250.0)
    assert band.one_run_rungs == (250.0,)
    assert "one-run separations: 250" in str(band)


# --- rendering -----------------------------------------------------------------


def test_str_names_the_edges_and_the_rung_count():
    band = ScorableBand(
        (_rung(_unsafe(30.0)), _rung(_separated(100.0)), _rung(_safe(300.0)))
    )
    text = str(band)
    assert BAND_CLOSED in text
    assert "1 rung(s) of 3 graded" in text
    assert "lower edge in (30, 100]" in text
    assert "upper edge in [100, 300)" in text


def test_render_is_one_line_per_band():
    a = ScorableBand((_rung(_unsafe(30.0)), _rung(_separated(100.0))))
    b = ScorableBand((_rung(_separated(100.0)), _rung(_safe(300.0))))
    assert render((a, b)).splitlines() == [str(a), str(b)]


# --- which arm left the band (D-133) --------------------------------------------


def _attributed(headroom, *, stock, risk):
    """A rung carrying the per-arm ESS flags as well as their conjunction."""
    conj = None if stock is None or risk is None else (stock and risk)
    return BandRung(
        headroom,
        ess_in_band=conj,
        ess_arms=(("stock_mppi", stock), ("risk_mppi", risk)),
    )


def test_attribution_is_optional_and_absent_by_default():
    """The conjunction is all the grading needs, so a caller that only has it
    must stay legal — attribution buys the *reading* of a refusal, not the
    refusal."""
    rung = BandRung(_separated(100.0), ess_in_band=False)
    assert rung.ess_arms == ()
    assert rung.out_of_band_arms == ()
    assert rung.refusal == ESS_OUT_OF_BAND


def test_attribution_does_not_change_grading():
    plain = BandRung(_separated(30.0), ess_in_band=False)
    named = _attributed(_separated(30.0), stock=False, risk=True)
    assert named.refusal == plain.refusal
    assert named.graded == plain.graded
    assert named.scorable == plain.scorable
    assert named.out_of_band_arms == ("stock_mppi",)


def test_per_arm_flags_must_conjoin_to_the_declared_ess_in_band():
    """Two statements of one fact that disagree is a defect to surface, not a
    rung to grade — the duplicate-rung check one level up, same argument."""
    with pytest.raises(ValueError, match="disagreement to resolve"):
        BandRung(
            _separated(100.0),
            ess_in_band=True,
            ess_arms=(("stock_mppi", False), ("risk_mppi", True)),
        )


def test_an_unmeasured_arm_makes_the_conjunction_unmeasured_not_false():
    """`None and True` is falsy in Python and would silently downgrade an
    unmeasured rung to a failed one, which are different refusals."""
    rung = _attributed(_separated(100.0), stock=None, risk=True)
    assert rung.ess_in_band is None
    assert rung.refusal == ESS_UNMEASURED
    assert rung.out_of_band_arms == ()


def test_attribution_to_an_arm_that_did_not_run_is_rejected():
    with pytest.raises(ValueError, match="did not run"):
        BandRung(
            _separated(100.0),
            ess_in_band=False,
            ess_arms=(("stock_mppi", False), ("vg_mppi", True)),
        )


def test_one_sided_refusal_names_the_arm_responsible():
    """`cafe_obstacle_crossing_v0` calibrates its arms to disjoint lam windows,
    so a band with no scorable rung there may be bounding the shared operating
    point rather than the mechanism. The two readings print identically without
    this."""
    band = ScorableBand(
        (
            _attributed(_unsafe(30.0), stock=False, risk=True),
            _attributed(_separated(100.0), stock=False, risk=True),
            _attributed(_safe(300.0), stock=True, risk=True),
        )
    )
    assert band.verdict == NO_SCORABLE_RUNG
    assert band.refused_by_arm == (("stock_mppi", (30.0, 100.0)),)
    assert band.sole_refuser == "stock_mppi"


def test_a_two_sided_refusal_has_no_single_owner_to_name():
    band = ScorableBand(
        (
            _attributed(_unsafe(30.0), stock=False, risk=True),
            _attributed(_separated(100.0), stock=True, risk=False),
        )
    )
    assert band.sole_refuser is None
    assert band.refused_by_arm == (
        ("risk_mppi", (100.0,)),
        ("stock_mppi", (30.0,)),
    )


def test_unattributed_refusals_do_not_fabricate_a_sole_refuser():
    """Nobody said who, which is not the same as nobody being out of band."""
    band = ScorableBand(
        (
            BandRung(_unsafe(30.0), ess_in_band=False),
            BandRung(_separated(100.0), ess_in_band=True),
        )
    )
    assert band.refused_by_arm == ()
    assert band.sole_refuser is None
