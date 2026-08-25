# SPDX-License-Identifier: BSD-3-Clause
"""Is D-256's cancelling root a property of the critics, or of one scene cell?"""

import numpy as np
import pytest

from eval.mppi_sandbox import cancelling_stability as cs
from eval.mppi_sandbox.epistemic_sign import (
    SHADOW_TAU,
    blind_corner,
    cancelling_ratio,
)


@pytest.fixture(scope="module")
def bands():
    """The full radius x stride sweep — ~0.13 s, paid once for the module."""
    return cs.sweep()


def _band(radius, roots):
    """A synthetic band, for testing the verdict logic without a BEV build."""
    return cs.RootBand(radius, tuple(roots), (3, 5))


# --- why the "ratio" reads only one arm -------------------------------------

def test_the_epistemic_channel_is_exactly_binary():
    """The premise under `REPEL_SPLIT_UNIT`: sigma takes two values, not a range.

    If this ever becomes continuous (a soft/blurred shadow), the repel arm stops
    contributing a constant and every claim below has to be re-derived.
    """
    for radius in (0.3, 0.5, 1.0):
        _, _, _, _, sigma = blind_corner(radius=radius)
        assert set(np.unique(sigma)) == {0.0, 1.0}
        assert 0.0 < SHADOW_TAU < 1.0     # the tau splits *on* the two values


@pytest.mark.parametrize("radius", [0.3, 0.5, 0.8, 1.25])
@pytest.mark.parametrize("stride", [3, 13, 31])
def test_repel_split_is_the_same_constant_at_every_geometry(radius, stride):
    """`REPEL_SPLIT_UNIT` is structural, so it is measured, not asserted.

    This is what makes `cancelling_ratio` a reading of the *attract* arm alone:
    the denominator is 1.0 everywhere, so the root is `-v1` verbatim.
    """
    assert cs.repel_split_unit(radius, stride) == pytest.approx(
        cs.REPEL_SPLIT_UNIT, abs=1e-12)


def test_root_at_agrees_with_the_shipped_cancelling_ratio():
    """Two names for one number — pinned equal rather than left to drift (D-047).

    `root_at` recomputes instead of delegating (one geometry build per cell,
    not two); this is the test that keeps the optimisation honest.
    """
    for radius, stride in ((0.5, 13), (0.3, 7), (1.0, 23)):
        assert cs.root_at(radius, stride) == pytest.approx(
            cancelling_ratio(radius=radius, stride=stride), rel=1e-12)


# --- the band is the unit of the reading ------------------------------------

def test_a_single_stride_is_refused_as_a_band():
    """The conflation the module exists to prevent, enforced at the door."""
    with pytest.raises(ValueError, match="sample, not a band"):
        cs.band_at(0.5, strides=(13,))


def test_band_brackets_its_own_samples(bands):
    for b in bands:
        assert b.lo <= b.mean <= b.hi
        assert b.width >= 0.0
        assert all(b.contains(r) for r in b.roots)


def test_sampling_alone_moves_the_root_by_a_fifth_or_more(bands):
    """Stride changes no physical quantity, so this width is pure instrument.

    Every band is at least 18% of its own mean wide. That is the noise floor
    any single-stride radius trend has to clear.
    """
    assert all(b.relative_width > 0.15 for b in bands)


# --- what the sweep does and does not establish -----------------------------

def test_geometry_genuinely_moves_the_root(bands):
    """The finding that survives: r=0.3 and r=1.0 cannot be reconciled.

    Their bands are disjoint, so no choice of stride makes a small-disc scene
    read like a large-disc one. The root is *not* a constant of the critics.
    """
    assert cs.geometry_moves_the_root(bands) is True
    small = next(b for b in bands if b.radius == 0.3)
    large = next(b for b in bands if b.radius == 1.0)
    assert cs.separation(small, large) == cs.SEPARATED
    assert small.hi < large.lo


def test_most_adjacent_radius_pairs_are_not_separated(bands):
    """The counter-finding: the single-stride trend is mostly unestablished.

    Read at stride=13 alone the roots march 0.2462 -> 0.5106 and look like a
    clean monotone law. Over the stride ensemble, 5 of the 6 adjacent steps
    have overlapping bands — the trend is real end-to-end and not resolvable
    step-by-step.
    """
    conf = cs.confounded_neighbours(bands)
    assert len(conf) >= 4
    assert len(conf) < len(bands) - 1      # not *every* pair — 0.3->0.4 separates


def test_the_apparent_turnover_at_the_largest_radius_is_inside_the_noise(bands):
    """r=1.25 reads below r=1.0 at stride=13; the ensemble declines to rank them.

    Reporting that dip as a real turnover is exactly the overclaim this module
    is built to catch.
    """
    one = next(b for b in bands if b.radius == 1.0)
    biggest = next(b for b in bands if b.radius == 1.25)
    assert biggest.mean < one.mean                     # the dip is there...
    assert cs.separation(one, biggest) == cs.CONFOUNDED  # ...and not established


# --- verdict logic, on synthetic bands --------------------------------------

def test_disjoint_bands_separate_and_overlapping_ones_do_not():
    a, b = _band(0.3, [0.10, 0.20]), _band(1.0, [0.40, 0.50])
    assert cs.separation(a, b) == cs.SEPARATED
    assert cs.separation(b, a) == cs.SEPARATED          # symmetric
    c = _band(0.5, [0.15, 0.45])
    assert cs.separation(a, c) == cs.CONFOUNDED
    assert cs.separation(c, a) == cs.CONFOUNDED


def test_bands_that_merely_touch_are_confounded():
    """The boundary resolves toward refusal, not toward a claim."""
    a, b = _band(0.3, [0.10, 0.20]), _band(1.0, [0.20, 0.30])
    assert cs.separation(a, b) == cs.CONFOUNDED


def test_overlap_never_licenses_an_equality_claim():
    """`CONFOUNDED` is "cannot tell", and there is no verdict spelled `SAME`.

    Pinned as an API fact: a future caller cannot read sameness out of this
    module, because the module never offers the word.
    """
    assert not hasattr(cs, "SAME")
    assert {cs.SEPARATED, cs.CONFOUNDED} == {"SEPARATED", "CONFOUNDED"}


def test_identical_bands_yield_no_geometry_movement():
    same = [_band(r, [0.30, 0.40]) for r in (0.3, 0.5, 1.0)]
    assert cs.geometry_moves_the_root(same) is False
    assert cs.confounded_neighbours(same) == [(0.3, 0.5), (0.5, 1.0)]


def test_well_separated_bands_have_no_confounded_neighbours():
    clean = [_band(0.3, [0.10, 0.11]), _band(0.5, [0.30, 0.31]),
             _band(1.0, [0.50, 0.51])]
    assert cs.confounded_neighbours(clean) == []
    assert cs.geometry_moves_the_root(clean) is True


# --- grading the quoted number ----------------------------------------------

def test_d256s_quoted_root_is_a_valid_sample_with_no_supported_precision(bands):
    """D-256's `0.3587 : 1` — inside its band, and pinned to zero decimals.

    So the number is not wrong; the four digits are. The band at radius=0.5 is
    ~0.12 wide, which does not pin even the first decimal place.
    """
    at_half = next(b for b in bands if b.radius == 0.5)
    verdict, digits = cs.grade_single(0.3587, at_half)
    assert verdict == cs.IN_BAND
    assert digits == 0.0


def test_a_value_outside_its_band_is_named_as_such():
    b = _band(0.5, [0.30, 0.40])
    assert cs.grade_single(0.90, b)[0] == cs.OUT_OF_BAND
    assert cs.grade_single(0.35, b)[0] == cs.IN_BAND


def test_supported_decimals_tracks_the_band_width():
    assert cs.grade_single(0.35, _band(0.5, [0.345, 0.355]))[1] == 2.0   # w=0.01
    assert cs.grade_single(0.35, _band(0.5, [0.3495, 0.3505]))[1] == 3.0  # w=1e-3
    # A zero-width band is the only case that pins every digit; it cannot arise
    # from a real sweep (see the >15% width test) but the arithmetic must not
    # divide by it.
    assert cs.grade_single(0.35, _band(0.5, [0.35, 0.35]))[1] == float("inf")


def test_format_sweep_reports_both_the_finding_and_the_refusal(bands):
    text = cs.format_sweep(bands)
    assert "geometry_moves_the_root=True" in text
    assert "confounded adjacent pairs" in text
    assert "0.30" in text and "1.25" in text
