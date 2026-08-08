# SPDX-License-Identifier: BSD-3-Clause
"""`scorable_band.certify_span` — the λ guard applied to a published span.

D-144 built the enforcing consumer for one `Headroom`; D-145/D-146 cleared the
two calibration refusals standing against the project's published rows. The gap
left is that a *band* still takes λ as a free argument: `ScorableBand` walks the
weight axis at a fixed temperature and nothing checks that temperature was
admissible at the rungs whose verdicts set the span.

The thing this module has to get right is the one D-144 got wrong on its first
cut and Q-120 named in general. Only three weights carry a calibration table, so
a certification that demanded one per rung would refuse essentially every band —
and a guard that refuses everything reads as maximal strictness while checking
nothing. So both directions are pinned here, and the *middle* case is pinned
separately: a band nobody measured must be distinguishable from a band a
measurement contradicts, because only the second is a defect.

Analytic. Clearances exist only to make legal `Headroom`s — a certification is a
function of `(scenario, controller, weight, λ)` and the tables, not of the runs.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import lam_window_index as lwi
from eval.mppi_sandbox.comparison_headroom import UNCERTIFIED, ArmSafety, Headroom
from eval.mppi_sandbox.scorable_band import (
    SPAN_CERTIFIED,
    SPAN_REFUSING,
    SPAN_UNCALIBRATED,
    SPAN_UNCERTIFIED,
    SPAN_UNMEASURED,
    BandRung,
    ScorableBand,
    UncertifiedSpan,
    assert_span_certified,
    certify_span,
)

MARGIN = 0.40
HEADON = "cafe_head_on_v0"
CROSSING = "cafe_obstacle_crossing_v0"

#: The weights that carry a calibration table (D-141 / D-142 / D-145).
CALIBRATED = (10.0, 75.0, 100.0)

#: D-132's operating point: admissible on both head_on arms at `w = 10`.
GOOD_LAM = 0.8

INDEX = lwi.build_index()


def _separated(weight: float, lam: float, scenario: str = HEADON) -> Headroom:
    """Margin crossed, arms differ — `SEPARATED`, so the rung is scorable."""
    return Headroom(
        scenario=scenario, weight=weight, lam=lam,
        a=ArmSafety("stock_mppi", (0.01,) * 4, MARGIN),
        b=ArmSafety("risk_mppi", (0.01, 0.9, 0.9, 0.9), MARGIN),
    )


def _band(weights, lam=GOOD_LAM, scenario=HEADON) -> ScorableBand:
    return ScorableBand(
        rungs=tuple(
            BandRung(_separated(w, lam, scenario), ess_in_band=True) for w in weights
        )
    )


# --------------------------------------------------------------------------
# It accepts, it refuses, and the middle case is neither.
# --------------------------------------------------------------------------

def test_a_band_walked_entirely_at_calibrated_weights_certifies():
    """Every scorable rung at a weight with a table, λ inside both windows.

    If this refused there would be no band the guard could ever pass, which is
    the accept-nothing vacuity rather than strictness.
    """
    cert = certify_span(_band(CALIBRATED), INDEX)
    assert cert.verdict == SPAN_CERTIFIED
    assert cert.ok
    assert cert.certified == CALIBRATED
    assert cert.refused == ()
    assert cert.unmeasured == ()


def test_a_band_at_a_refused_temperature_is_uncertified():
    """λ = 3.2 at `w = 10` on head_on: both arms record `[0.2, 0.4, 0.8]`
    (D-141), so the tables speak at these weights and say 3.2 is out.

    This is the case the guard exists for — a span published at a temperature
    the scene does not admit.
    """
    cert = certify_span(_band(CALIBRATED, lam=3.2), INDEX)
    assert cert.verdict == SPAN_UNCERTIFIED
    assert not cert.ok
    assert [w for w, _ in cert.refused] == list(CALIBRATED)


def test_an_uncalibrated_weight_is_not_a_refusal():
    """`w = 250` carries no table, so nothing was measured there.

    The band is unwitnessed on the λ axis at that rung, not contradicted — and
    the distinction is the whole reason this does not collapse into a guard
    that refuses every band (only three weights are calibrated today).
    """
    cert = certify_span(_band((10.0, 250.0)), INDEX)
    assert cert.verdict == SPAN_UNCALIBRATED
    assert not cert.ok
    assert cert.certified == (10.0,)
    assert [w for w, _ in cert.unmeasured] == [250.0]
    assert cert.refused == ()


# --------------------------------------------------------------------------
# What raises, and what only reports.
# --------------------------------------------------------------------------

def test_assert_raises_on_a_contradicted_span_and_returns_on_a_good_one():
    assert assert_span_certified(_band(CALIBRATED), INDEX).ok
    with pytest.raises(UncertifiedSpan):
        assert_span_certified(_band(CALIBRATED, lam=3.2), INDEX)


def test_assert_does_not_raise_on_an_uncalibrated_span_by_default():
    """A missing measurement is a purchase order, not a failure.

    Raising here would make the guard fire on the overwhelming majority of
    bands — including every honest one whose ladder simply runs past `w = 100`
    — and a check that cannot be cleared by doing the work is one that gets
    muted (D-044).
    """
    cert = assert_span_certified(_band((10.0, 250.0)), INDEX)
    assert cert.verdict == SPAN_UNCALIBRATED


def test_require_calibration_promotes_the_coverage_gap_to_a_failure():
    """The escape hatch for a call site that genuinely walks calibrated
    weights only. Off by default; the flag is the record of which sites those
    are."""
    with pytest.raises(UncertifiedSpan):
        assert_span_certified(_band((10.0, 250.0)), INDEX, require_calibration=True)
    assert assert_span_certified(
        _band(CALIBRATED), INDEX, require_calibration=True
    ).ok


# --------------------------------------------------------------------------
# Denominators and scope.
# --------------------------------------------------------------------------

def test_a_band_with_no_scorable_rung_cannot_be_certified():
    """`NO_SCORABLE_RUNG` publishes no operating point, so certifying it would
    pass on an empty denominator — the shape D-107 / D-120 / D-127 each booked
    one axis over."""
    band = ScorableBand(
        rungs=(BandRung(_separated(10.0, GOOD_LAM), ess_in_band=False),)
    )
    assert band.scorable == ()
    with pytest.raises(ValueError, match="nothing.*to certify"):
        certify_span(band, INDEX)


def test_only_the_scorable_rungs_are_certified():
    """A refused rung bounds the band from outside and carries no claim.

    Demanding a calibrated operating point for it would count coverage the
    headline never rests on — and, the other way, would let an ESS-refused rung
    at an uncalibrated weight drag an otherwise certified span down.
    """
    band = ScorableBand(rungs=(
        BandRung(_separated(10.0, GOOD_LAM), ess_in_band=True),
        BandRung(_separated(250.0, GOOD_LAM), ess_in_band=False),
    ))
    cert = certify_span(band, INDEX)
    assert [w for w, _ in cert.certs] == [10.0]
    assert cert.verdict == SPAN_CERTIFIED


# --------------------------------------------------------------------------
# The partition has exactly one statement of itself.
# --------------------------------------------------------------------------

def test_the_two_refusal_classes_partition_the_uncertified_verdicts():
    """A refusal added to `comparison_headroom.UNCERTIFIED` must land in one
    class or the other, and this fails the day one lands in neither.

    Written as a partition rather than as two hand-typed lists for D-047's
    reason: the copy that drifts is the one nothing checks.
    """
    assert SPAN_UNMEASURED | SPAN_REFUSING == frozenset(UNCERTIFIED)
    assert SPAN_UNMEASURED & SPAN_REFUSING == frozenset()
    assert SPAN_UNMEASURED and SPAN_REFUSING, "an empty class grades nothing"
