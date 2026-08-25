# SPDX-License-Identifier: BSD-3-Clause
"""`scorable_band.published_band` — the λ span guard's first non-fixture input.

D-147 shipped `certify_span` / `assert_span_certified` and left the gap its own
journal named: nothing called them. Every `ScorableBand` in the repo was built
by a test, so the guard had never been shown a band the project actually
publishes. This module supplies that band — D-133's eight-rung walk on
`cafe_head_on_v0` — and grades it.

Two things are being tested and they are separable. The first is the
**reconstruction**: the published record is a table of unsafe rates, and a rate
does not determine clearances, so the rebuild has to be checked against the
verdict column the walk recorded rather than trusted (D-139's rule — only a
cell whose answer is already written down can test the generator). The second
is the **certification** of the band that survives that check.
"""

from __future__ import annotations

import dataclasses

import pytest

from eval.mppi_sandbox import lam_window_index as lwi
from eval.mppi_sandbox.scorable_band import (
    BAND_SPLIT,
    PUBLISHED_ARMS,
    PUBLISHED_LADDER,
    PUBLISHED_LAM,
    PUBLISHED_SCENARIO,
    PUBLISHED_SEEDS,
    SPAN_CERTIFIED,
    UncertifiedSpan,
    UnreconstructedMagnitude,
    assert_span_certified,
    certify_span,
    published_band,
)


# --------------------------------------------------------------------------
# The reconstruction reproduces what the walk recorded.
# --------------------------------------------------------------------------

def test_every_rung_reproduces_its_recorded_verdict():
    """The falsifiable half. `PUBLISHED_LADDER` carries the verdict column D-133
    wrote down; the reconstruction has to re-derive it from the counts alone."""
    band = published_band()
    by_weight = {r.weight: r for r in band.rungs}
    for weight, _stock, _risk, _ess, recorded in PUBLISHED_LADDER:
        rung = by_weight[weight]
        if recorded is None:
            # The one rung the walk refused: it has no verdict to reproduce,
            # and the reconstruction must not invent one by grading it.
            assert not rung.graded, f"w={weight:g} was refused, not graded"
        else:
            assert rung.headroom.verdict == recorded, f"w={weight:g}"


def test_unsafe_rates_are_the_published_ones():
    """Counts in, rates out — the quantity the record actually pins."""
    band = published_band()
    by_weight = {r.weight: r for r in band.rungs}
    for weight, stock, risk, _ess, _recorded in PUBLISHED_LADDER:
        h = by_weight[weight].headroom
        assert h.a.unsafe_rate == pytest.approx(stock / PUBLISHED_SEEDS)
        assert h.b.unsafe_rate == pytest.approx(risk / PUBLISHED_SEEDS)


def test_band_reproduces_the_docstrings_structural_claims():
    """The module docstring makes four structural claims about this walk. All
    four are re-derived here, so a bad filler cannot quietly move one."""
    band = published_band()
    assert band.scenario == PUBLISHED_SCENARIO
    assert band.lam == PUBLISHED_LAM
    assert band.verdict == BAND_SPLIT           # "BAND_SPLIT rather than BAND_CLOSED"
    assert band.span == (75.0, 250.0)
    assert band.one_run_rungs == (250.0,)       # "bought by one seed"
    assert band.refused == ((30.0, "ess_out_of_band"),)


def test_the_refusal_at_30_is_one_sided_and_names_the_baseline():
    """D-132's asymmetry: the *baseline* left the ESS band, not the mechanism.
    Collapsing the flags to a conjunction would lose exactly this."""
    band = published_band()
    assert band.sole_refuser == "stock_mppi"
    assert band.refused_by_arm == (("stock_mppi", (30.0,)),)


def test_the_main_island_is_three_rungs_and_250_is_the_split():
    """'The band is three rungs wide, not one' is a claim about the contiguous
    island; `width_rungs` is 4 because of the detached one-run rung at 250. The
    two numbers are different claims and the test keeps them apart."""
    band = published_band()
    assert band.scorable == (75.0, 100.0, 150.0, 250.0)
    assert band.width_rungs == 4
    contiguous_island = tuple(w for w in band.scorable if w <= 150.0)
    assert len(contiguous_island) == 3
    assert not band.single_rung             # the D-131 state it replaced


# --------------------------------------------------------------------------
# Magnitudes are refused, not filled in.
# --------------------------------------------------------------------------

def test_reading_a_magnitude_raises_rather_than_returning_a_filler():
    """The reconstruction has no clearances. The failure mode being blocked is
    a plausible number, not a missing one — with a below-margin filler
    `sub_margin` reads True for the whole band, which is a D-124 claim this
    walk never made."""
    band = published_band()
    h = band.rungs[0].headroom
    with pytest.raises(UnreconstructedMagnitude):
        _ = h.a.mean_clearance
    with pytest.raises(UnreconstructedMagnitude):
        _ = h.sub_margin


def test_the_refusal_is_an_attribute_error_so_probing_degrades_cleanly():
    """`hasattr` on an absent magnitude should read absent, not explode."""
    band = published_band()
    assert not hasattr(band.rungs[0].headroom.a, "mean_clearance")


def test_rates_survive_the_magnitude_refusal():
    """The refusal must not take the quantities the band is graded on with it —
    a guard that made the band ungradable would be its own kind of vacuity."""
    band = published_band()
    h = band.rungs[2].headroom          # w = 75
    assert h.a.unsafe_rate == pytest.approx(1.0)
    assert h.b.unsafe_rate == pytest.approx(11 / 16)
    assert h.verdict == "SEPARATED"


# --------------------------------------------------------------------------
# The certification. This is the finding.
# --------------------------------------------------------------------------

def test_the_published_span_is_fully_calibrated():
    """The band the project publishes now certifies at every rung that sets it.

    The arc, because the number alone does not carry it: D-148 built this
    object and got **2 of 4** with `w ∈ {150, 250}` unwitnessed on the λ axis;
    D-149 bought 150 and got 3 of 4; this cycle bought 250 and the verdict
    moves `SPAN_UNCALIBRATED → SPAN_CERTIFIED`. Every rung whose verdict
    contributes to `span` now has a table at its own weight saying λ = 0.8 is
    admissible there.

    `w = 250` could have retracted it, and more easily than 150 could: it is
    the detached one-run rung, and its stock arm *did* come back narrower —
    `[0.4, 0.8]` against `[0.2, 0.4, 0.8]` at every lower weight, the first
    head_on arm-cell to move at all across the four calibrated weights. 0.8
    survived the narrowing, so the rung certifies; had the window closed from
    the top instead of the bottom this would be a retraction of a rung D-133
    publishes.
    """
    cert = certify_span(published_band())
    assert cert.verdict == SPAN_CERTIFIED
    assert cert.certified == (75.0, 100.0, 150.0, 250.0)
    assert cert.unmeasured == ()
    assert cert.refused == ()
    assert cert.ok


def test_the_top_rungs_window_narrowed_without_dropping_the_operating_point():
    """Why the rung above certifies rather than being assumed to.

    The stock arm's admissible set shrinks at `w = 250` — 0.2 drops out — while
    the risk arm holds `[0.2, 0.4, 0.8]`. So `w = 250` is also the first weight
    where the two head_on arms disagree about the window at all, which is worth
    pinning: a certification reads as "λ = 0.8 is fine everywhere" and the
    honest statement is narrower than that.
    """
    stock = lwi.resolve("cafe_head_on_v0.yaml", "stock_mppi", 250.0)
    risk = lwi.resolve("cafe_head_on_v0.yaml", "risk_mppi", 250.0)
    assert stock.usable == (0.4, 0.8)          # 0.2 no longer admissible
    assert risk.usable == (0.2, 0.4, 0.8)      # unchanged from 150
    assert stock.usable != risk.usable, "the first head_on weight where arms differ"
    # The operating point is in both, which is the only reason the rung certifies.
    assert 0.8 in stock.usable and 0.8 in risk.usable


def test_the_certified_rung_was_bought_and_could_have_retracted_the_band():
    """`w = 150` is not certified by construction — it is certified by a
    measurement that was free to come back the other way.

    D-142 moved 6 of 14 arm-cells between `w = 10` and `w = 75`, so a head_on
    arm whose window had shifted off 0.8 at `w = 150` would have graded this
    rung `OFF_KEY`/`EMPTY_WINDOW` and turned the certification into a
    retraction of a rung D-133 published. It did not: both arms hold
    `[0.2, 0.4, 0.8]`, and the 8-seed table reproduces D-136's 16-seed hand
    walk exactly. This test pins the direction the result could have gone, so
    "certified" is not read as "assumed".
    """
    from eval.mppi_sandbox import lam_window_index as lwi
    # Unrolled rather than looped: two arms is not a population, and a
    # loop-body assert here would owe `loop_reach` a registration to prove it
    # ran at all. Both arms named outright cannot run zero times.
    stock = lwi.resolve("cafe_head_on_v0.yaml", "stock_mppi", 150.0)
    risk = lwi.resolve("cafe_head_on_v0.yaml", "risk_mppi", 150.0)
    assert stock.verdict == "ON_KEY" and risk.verdict == "ON_KEY"
    assert stock.usable == (0.2, 0.4, 0.8)
    assert risk.usable == (0.2, 0.4, 0.8)


def test_the_split_rung_keeps_its_one_run_weakness_after_calibration():
    """D-148 found `w = 250` carrying two independent weaknesses at once — a
    separation bought by a single run in sixteen (sign *against* the
    mechanism), and no calibration at its weight — while being the sole reason
    the band grades `BAND_SPLIT`. This cycle retired the second one only.

    That is the point of the test surviving rather than being deleted: the
    coincidence is broken, and what is left is the weakness calibration cannot
    touch. A λ table says the temperature was admissible at that weight; it says
    nothing about whether one unsafe run out of sixteen is a separation. The
    band's only *structural* claim still rests on that rung, and now rests on it
    for exactly one reason instead of two.
    """
    band = published_band()
    cert = certify_span(band)
    # The rung is no longer uncalibrated…
    assert {w for w, _ in cert.unmeasured} == set()
    assert 250.0 in cert.certified
    # …and is still the one-run rung, and still the one that splits the band.
    assert band.one_run_rungs == (250.0,)
    without_250 = type(band)(tuple(r for r in band.rungs if r.weight != 250.0))
    assert without_250.verdict != BAND_SPLIT


def test_require_calibration_now_accepts_the_published_band():
    """The flag D-147 added for "a site that walks calibrated weights only".

    D-147 argued the flag had to be *off* by default because a default-on
    version would refuse nearly every band, and D-148 duly found the project's
    own published band failing it. It now passes — the first band in the repo
    to clear the strict form — which is what the flag was for and is the whole
    point of having bought the four tables.
    """
    cert = assert_span_certified(published_band(), require_calibration=True)
    assert cert.ok and cert.verdict == SPAN_CERTIFIED


def test_the_strict_flag_still_refuses_a_band_that_runs_past_the_tables():
    """…and the flag is not vacuous now that the published band clears it.

    The refusal witness has to live somewhere other than the object under
    certification, or buying the last table would have quietly turned
    `require_calibration=True` into an assertion that passes for every input.
    D-145 booked this shape ("a refusal test should name the gap, not the
    weight"); the gap here is the complement of the index's domain, so the
    probe rung is derived from it rather than named.
    """
    band = published_band()
    probe = lwi.build_index().uncalibrated_probe
    # Template off a *scorable* rung: `certify_span` only grades those, so
    # cloning the unscorable top rung would build a band that passes for the
    # wrong reason and leave this test green with nothing in it.
    template = next(r for r in band.rungs if r.scorable)
    past_the_tables = type(band)(band.rungs + (dataclasses.replace(
        template, headroom=dataclasses.replace(template.headroom, weight=probe)),))
    assert past_the_tables.rungs[-1].scorable
    with pytest.raises(UncertifiedSpan):
        assert_span_certified(past_the_tables, require_calibration=True)


def test_default_reports_rather_than_raising():
    """Unmeasured is not a refusal (D-147). Without the flag the band comes
    back graded rather than throwing — now graded clean, where D-148/D-149 read
    it as a legible coverage gap."""
    cert = assert_span_certified(published_band())
    assert cert.verdict == SPAN_CERTIFIED


def test_every_scorable_rung_is_certified_and_the_denominator_is_real():
    """Non-vacuity in both directions, restated for a band that now certifies
    completely.

    `certified == scorable` is the strongest reading this object can produce,
    so the guard against it is the *denominator*: an empty `scorable` would
    also satisfy set equality, and that is the empty-denominator pass D-107 /
    D-120 / D-127 each booked. Both sides are asserted non-empty.
    """
    band = published_band()
    cert = certify_span(band)
    assert band.scorable, "a band publishing nothing certifies vacuously"
    assert cert.certified, "a certification that certified nothing would be vacuous"
    assert set(cert.certified) == set(band.scorable)


def test_arms_are_the_names_the_calibration_tables_key_on():
    """D-144's basename bug one level over: certification couples on arm *name*,
    so a rebuild that renamed the arms would grade NO_CELL and look calibrated-
    adjacent while testing nothing."""
    band = published_band()
    assert PUBLISHED_ARMS == ("stock_mppi", "risk_mppi")
    for rung in band.rungs:
        assert (rung.headroom.a.arm, rung.headroom.b.arm) == PUBLISHED_ARMS
