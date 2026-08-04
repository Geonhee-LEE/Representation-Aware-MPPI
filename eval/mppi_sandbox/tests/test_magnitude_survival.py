"""Q-081's static half: every published magnitude against its own noise floor.

The tests that matter here are not the plumbing ones.  They are the three that
pin the *finding* --- that ``_pure``'s entire published series is inside its own
same-tree spread, that the survivors cluster on the narrow-band sites, and that
two of them survive by margins smaller than the band's own resolution --- because
a future cycle that re-runs the batch and gets a different band should be told
by a red test, not by nobody.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import magnitude_survival as ms
from eval.mppi_sandbox import published_ratios, reading_record


@pytest.fixture(scope="module")
def record():
    return ms.load()


# --------------------------------------------------------------------------
# plumbing
# --------------------------------------------------------------------------

def test_bands_come_from_the_records_own_spread(record):
    """One statistic, one spelling --- D-047's defect in miniature."""
    banded = ms.bands(record, ms.KIND_GAP)
    for site, lo, hi, spread in record.gap_spread:
        assert banded[site].lo == lo
        assert banded[site].hi == hi
        assert banded[site].spread == pytest.approx(spread)


def test_unknown_kind_is_refused(record):
    for call in (lambda: ms.bands(record, "nope"), lambda: ms.published(None, "nope")):
        with pytest.raises(ValueError, match="unknown kind"):
            call()


def test_ratio_spread_defaults_to_the_denominator_the_numbers_used(record):
    """Q-079: every published ratio divided by the exclusion frame alone.

    A band computed under ``measured+source`` would be a band for a quantity
    nobody published, so the default must not be inherited from ``ratios()``.
    """
    assert record.ratio_spread() == record.ratio_spread(reading_record.DENOM_MEASURED)
    both = record.ratio_spread(reading_record.DENOM_BOTH)
    assert both != record.ratio_spread()


def test_ratio_spread_drops_a_site_whose_control_is_zero_somewhere():
    """A spread over an infinity is not a number.  Pin the refusal, not a count."""
    rec = reading_record.Record(
        manifest=reading_record.Manifest(
            tree="t", trees=("t",), licensed=True, k=2, hidden=(), population=1,
            denominator=reading_record.DENOM_MEASURED,
            entropy=reading_record.UNSEEDED),
        cells=({"site": "s", "reconstructed": 10, "measured": 4,
                "measured_delta": 2, "source_delta": 1, "verdict": "X"},),
        measured_bands=(), source_bands=(),
        replicates=(
            ({"site": "s", "reconstructed": 10, "measured": 4,
              "measured_delta": 2, "source_delta": 1, "verdict": "X"},),
            ({"site": "s", "reconstructed": 10, "measured": 4,
              "measured_delta": 0, "source_delta": 1, "verdict": "X"},),
        ))
    assert rec.ratio_spread() == ()
    assert rec.gap_spread  # the gap band survives; only the ratio band drops


def test_the_self_defining_number_is_excluded():
    """D-074's ``_pure`` gap of 326 **is** that site's band ``hi``."""
    assert ("D-074", "lam_dependence._pure", ms.KIND_GAP) in ms.SELF_DEFINING
    assert not [p for p in ms.published(None, ms.KIND_GAP) if p[0] == "D-074"]


def test_license_is_a_tension_not_a_boolean():
    status = ms.license_status()
    assert "D-069" in status and "D-074" in status
    assert not isinstance(status, bool)


# --------------------------------------------------------------------------
# the finding
# --------------------------------------------------------------------------

def test_pure_publishes_four_gaps_and_none_of_the_movements_survive(record):
    """The most-cited site on the branch, and its whole series is noise.

    ``_pure``'s gap was written as 142 -> 196 -> 175 -> 214 across four
    decisions, each step read as the tree having moved.  The widest fold among
    them is 1.51x; the same instrument on an unchanged tree spans 1.74x.
    """
    moves = [m for m in ms.movements(record, None, ms.KIND_GAP)
             if m.site == "lam_dependence._pure"]
    assert len(moves) == 6, "four published gaps -> C(4,2) pairs"
    assert not [m for m in moves if m.survives]
    assert max(m.fold for m in moves) < moves[0].band.spread


def test_gap_survival_is_a_minority_and_clusters_on_the_narrow_bands(record):
    s = ms.survival(record, None, ms.KIND_GAP)
    assert (s.surviving, s.total) == (8, 23)
    assert (s.sites_surviving, s.sites_total) == (3, 6)
    assert s.unbanded == 0
    survivors = {m.site for m in ms.movements(record, None, ms.KIND_GAP)
                 if m.survives}
    widest = {site for site, _, _, spread in record.gap_spread if spread >= 2.2}
    # every surviving site has a band at or below 2.19x; the wide-band sites
    # (_shells 4.50x, _numeric 2.59x, _is_pure_literal 2.23x) supply none.
    assert not survivors & widest


def test_three_gap_survivors_are_inside_the_bands_own_resolution(record):
    """Survival by 1-5% of a fold estimated from k=3 is not a margin.

    Named rather than silently counted in the 8: if the batch is re-run these
    are the three that will change side, and the finding should say so before it
    happens.  The margins are 1.009x (``_is_structural`` 84 vs 73), 1.023x
    (``_has_git_diff_literal`` 65 vs 29) and 1.047x (``_is_set_valued`` 15 vs
    20) --- so the defensible reading of the gap result is **5 of 23**, not 8,
    and this test exists so the 8 is never quoted without the 5.
    """
    marginal = [m for m in ms.movements(record, None, ms.KIND_GAP)
                if m.survives and m.fold / m.band.spread < 1.06]
    assert len(marginal) == 3
    assert {m.site for m in marginal} == {
        "lam_dependence._is_structural",
        "guard_reflexivity._has_git_diff_literal",
        "guard_reflexivity._is_set_valued",
    }
    # every marginal survivor is a pair that includes D-069 --- the one reading
    # of the four whose gaps were published with no control at all.
    assert all("D-069" in (m.earlier[0], m.later[0]) for m in marginal)


def test_the_ratio_is_the_sturdier_published_quantity(record):
    """First control on this branch to *support* a prior claim rather than retire it.

    D-071 kept the ratio over stationarity.  4 of 5 ratio movements clear their
    band, against 8 of 23 for the gap.
    """
    ratio = ms.survival(record, None, ms.KIND_RATIO)
    gap = ms.survival(record, None, ms.KIND_GAP)
    assert (ratio.surviving, ratio.total) == (4, 5)
    assert ratio.rate > gap.rate


def test_half_the_surviving_ratio_movements_rest_on_a_control_of_one_or_two(record):
    """The 80% is not what it looks like, and the module has to say so."""
    weak = {(d, s) for d, s, _ in ms.fragile()}
    survivors = [m for m in ms.movements(record, None, ms.KIND_RATIO) if m.survives]
    resting = [m for m in survivors
               if (m.earlier[0], m.site) in weak or (m.later[0], m.site) in weak]
    assert len(resting) == 2
    assert {m.site for m in resting} == {
        "lam_dependence._is_structural",
        "guard_reflexivity._is_set_valued",
    }
    # the two that do not rest on a tiny control are both _pure's --- the site
    # whose *gap* movements all failed.  Same site, opposite verdict, because
    # the two quantities are not the same claim.
    sturdy = [m for m in survivors if m not in resting]
    assert {m.site for m in sturdy} == {"lam_dependence._pure"}


def test_every_banded_site_is_one_the_published_record_actually_names(record):
    """No band is graded against a site published_ratios never transcribed."""
    banded = set(ms.bands(record, ms.KIND_GAP))
    assert banded <= set(published_ratios.SITES)
