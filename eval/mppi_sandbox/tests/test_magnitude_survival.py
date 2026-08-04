"""Q-081's static half: every published magnitude against its own noise floor.

The tests that matter here are not the plumbing ones.  They are the three that
pin the *finding* --- that ``_pure``'s entire published series is inside its own
same-tree spread, that the survivors cluster on the narrow-band sites, and that
two of them survive by margins smaller than the band's own resolution --- because
a future cycle that re-runs the batch and gets a different band should be told
by a red test, not by nobody.
"""

from __future__ import annotations

import dataclasses

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


# --------------------------------------------------------------------------
# D-076 --- Q-082: watch the exemption, or derive it?
# --------------------------------------------------------------------------

def test_the_typed_exemption_has_never_removed_anything():
    """The test above passes *vacuously*, and this is the test that says so.

    ``PUBLISHED`` transcribes D-066/D-069/D-070/D-071.  It contains no D-074
    cell, so "no D-074 value survives the filter" is true because none was ever
    offered to it.  Pinned as two integers: a future cycle that transcribes
    D-074's 326 will flip this to ``(1, 23)`` and should have to say so.
    """
    assert ms.exemption_bite() == (0, 22)
    assert "D-074" not in {c.decision for c in published_ratios.PUBLISHED}


def test_value_equality_alone_over_derives_the_exemption(record):
    """Q-082's lean (b), refuted as stated --- and by how much.

    Without a key naming *which claim* the record was published as, the only
    available test is "does this magnitude equal one of the record's readings".
    Gaps here are small integers, so it fires on coincidences between different
    trees: 1 under the endpoint spelling Q-082 wrote, 2 under the stronger
    replicate spelling.  Both are false, neither is in ``SELF_DEFINING``, and
    each would silently shrink a survival denominator.
    """
    assert not ms.provenance(record)
    endpoint = ms.over_derivation(record, None, ms.SPELLING_ENDPOINT)
    replicate = ms.over_derivation(record, None, ms.SPELLING_REPLICATE)
    assert {(d, s) for d, s, _ in endpoint} == {
        ("D-069", "guard_reflexivity._shells_out_to_git_diff"),
    }
    assert {(d, s) for d, s, _ in replicate} == {
        ("D-069", "guard_reflexivity._shells_out_to_git_diff"),
        ("D-066", "guard_reflexivity._is_set_valued"),
    }
    # the endpoint spelling is a strict subset of the replicate one: band
    # extremes *are* replicate readings, so it cannot find anything the other
    # misses.  Choosing between the two spellings is choosing how wrong to be.
    assert set(endpoint) < set(replicate)


def test_ratios_do_not_collide_at_all(record):
    """Same mechanism, seen from the side where it does not bite.

    A ratio is a quotient of two counts and carries far more distinguishing
    digits than a gap of 9, so value-equality happens never here.  That is why
    the over-derivation is a *small-integer* defect and not a general one ---
    stated so a future cycle does not read "derivation over-derives" as a law.
    """
    for spelling in ms.SPELLINGS:
        assert ms.derived_self_defining(record, None, ms.KIND_RATIO,
                                        spelling) == ()


def test_a_provenanced_record_derives_the_exemption_exactly(record):
    """The repair: one manifest field turns the guess into a lookup.

    With ``published_as`` set, the decision key does the discriminating and the
    value key only confirms.  D-069's and D-066's coincidences drop out because
    they are not this record's claim.
    """
    provenanced = dataclasses.replace(
        record,
        manifest=dataclasses.replace(record.manifest, published_as="D-074"))
    assert ms.provenance(provenanced) == "D-074"
    assert ms.over_derivation(provenanced, None, ms.SPELLING_REPLICATE) == ()
    # and on the population as it stands, the derived exemption is *empty* ---
    # not because the derivation failed, but because the value it would exclude
    # is the one `PUBLISHED` never transcribed.  Same finding as
    # `exemption_bite`, reached from the other end.
    assert ms.self_defining(provenanced) == ()


def test_a_provenanced_record_would_catch_the_transcribed_number(record):
    """The exemption becomes load-bearing the moment 326 is transcribed.

    Constructed rather than waited for: append the D-074 cell ``PUBLISHED`` is
    missing and the derived exemption finds it with no typed triple involved.
    """
    provenanced = dataclasses.replace(
        record,
        manifest=dataclasses.replace(record.manifest, published_as="D-074"))
    cells = published_ratios.PUBLISHED + (
        dataclasses.replace(published_ratios.PUBLISHED[0],
                            decision="D-074", site="lam_dependence._pure",
                            gap=326),
    )
    assert ms.derived_self_defining(provenanced, cells, ms.KIND_GAP) == (
        ("D-074", "lam_dependence._pure", ms.KIND_GAP),
    )
    assert not [p for p in ms.published(cells, ms.KIND_GAP, provenanced)
                if p[0] == "D-074"]


def test_threading_the_record_changes_no_published_value(record):
    """Every D-075 count is bit-identical under the new signature.

    The whole point of the fallback: this record is unprovenanced, so
    ``published(record=...)`` must be the same tuple as ``published()``.  If
    this ever goes red, a D-075 magnitude moved for a plumbing reason.
    """
    assert not ms.provenance(record)
    for kind in ms.KINDS:
        assert ms.published(None, kind, record) == ms.published(None, kind)
    assert ms.self_defining(record) == ms.SELF_DEFINING
    assert ms.survival(record, None, ms.KIND_GAP).surviving == 8
    assert ms.survival(record, None, ms.KIND_RATIO).surviving == 4


def test_unprovenanced_records_still_load_from_disk(record):
    """D-076 is a default, not a schema bump.

    Every record on disk predates the field.  If ``read`` had used ``m[...]``
    the only banding reading this branch owns would have become unreadable.
    """
    assert record.manifest.published_as == ""
    assert "UNPROVENANCED" in ms.PROVENANCE_MISSING


def test_unknown_spelling_is_refused(record):
    with pytest.raises(ValueError, match="unknown spelling"):
        ms.readings(record, ms.KIND_GAP, "nope")


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
