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

import pytest

from eval.mppi_sandbox.scorable_band import (
    BAND_SPLIT,
    PUBLISHED_ARMS,
    PUBLISHED_LADDER,
    PUBLISHED_LAM,
    PUBLISHED_SCENARIO,
    PUBLISHED_SEEDS,
    SPAN_UNCALIBRATED,
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

def test_the_published_spans_last_uncalibrated_rung_is_its_weakest_one():
    """The guard's first real input, one rung from clean — and the rung that is
    left is the one that should have been left.

    D-148 read this at 2 of 4 certified, with 150 and 250 both unmeasured.
    D-149 bought `w = 150` (one scene, 2 arms, 8 rungs, ~4 min) and both head_on
    arms came back `[0.2, 0.4, 0.8]`, so λ = 0.8 is in-band and the rung
    certifies. What survives is `w = 250`, and the verdict stays
    `SPAN_UNCALIBRATED` rather than `SPAN_CERTIFIED` because of it — one
    unwitnessed rung is enough, which is the point of grading the span rather
    than averaging it.

    Still `SPAN_UNCALIBRATED` and not `SPAN_UNCERTIFIED`: nothing contradicts
    λ = 0.8 up there, nobody has looked (D-147's split).
    """
    cert = certify_span(published_band())
    assert cert.verdict == SPAN_UNCALIBRATED
    assert cert.certified == (75.0, 100.0, 150.0)
    assert cert.unmeasured == ((250.0, "NO_TABLE_AT_WEIGHT"),)
    assert not cert.ok
    # Nothing *refuses* the span — the gap is coverage, not contradiction.
    assert cert.refused == ()


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


def test_the_rung_that_makes_the_band_split_is_also_the_uncalibrated_one():
    """The sharp edge of the finding, and the reason it is worth a D-NNN.

    `w = 250` carries two independent weaknesses at once: its separation is a
    single run out of sixteen (sign *against* the mechanism), and it sits at a
    weight nobody calibrated. It is also the sole reason the band grades
    `BAND_SPLIT` instead of `BAND_CLOSED`. So the walk's one structural claim
    about the shape of the scorable set rests entirely on its weakest rung.
    """
    band = published_band()
    cert = certify_span(band)
    uncalibrated = {w for w, _ in cert.unmeasured}
    assert set(band.one_run_rungs) <= uncalibrated
    # And it is load-bearing: drop it and the band is a closed interval.
    without_250 = type(band)(tuple(r for r in band.rungs if r.weight != 250.0))
    assert without_250.verdict != BAND_SPLIT


def test_require_calibration_refuses_the_published_band():
    """The flag D-147 added for 'a site that walks calibrated weights only'.
    The published band is not such a site, and this is the test that says so."""
    with pytest.raises(UncertifiedSpan):
        assert_span_certified(published_band(), require_calibration=True)


def test_default_reports_rather_than_raising():
    """Unmeasured is not a refusal (D-147). Without the flag the band comes
    back graded, so the coverage gap is legible instead of fatal."""
    cert = assert_span_certified(published_band())
    assert cert.verdict == SPAN_UNCALIBRATED


def test_the_certified_rungs_are_a_strict_subset_of_the_scorable_ones():
    """Non-vacuity in both directions: the guard accepts something (75, 100 are
    real certifications, not an empty pass) and refuses something."""
    band = published_band()
    cert = certify_span(band)
    assert set(cert.certified) < set(band.scorable)
    assert cert.certified, "a certification that certified nothing would be vacuous"


def test_arms_are_the_names_the_calibration_tables_key_on():
    """D-144's basename bug one level over: certification couples on arm *name*,
    so a rebuild that renamed the arms would grade NO_CELL and look calibrated-
    adjacent while testing nothing."""
    band = published_band()
    assert PUBLISHED_ARMS == ("stock_mppi", "risk_mppi")
    for rung in band.rungs:
        assert (rung.headroom.a.arm, rung.headroom.b.arm) == PUBLISHED_ARMS
