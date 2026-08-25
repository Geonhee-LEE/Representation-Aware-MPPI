"""What six cycles of prose left behind — and what it cannot answer.

Two kinds of test here, and the split matters.  The *transcription* tests re-run
:func:`published_ratios.unverified` against the real repository, so a mistyped
digit in the table fails CI rather than propagating into a fifth cycle of
argument.  The *sufficiency* tests pin the finding: on the record as published,
Q-078's no-new-run rank correlation has n=2 (one-frame) and n=0 (both-frame)
against a floor of 3.

They are deliberately not written as "the answer is unanswerable, forever".  The
sufficiency tests read the floor and the table, so persisting a real per-site
artifact (STATE #3) flips them by adding data, which is the outcome they exist to
motivate.
"""

from __future__ import annotations

import dataclasses

import pytest

from eval.mppi_sandbox import exclusion_scope as es
from eval.mppi_sandbox import published_ratios as prs


# --------------------------------------------------------------------------
# the transcription, checked against the files it was copied from
# --------------------------------------------------------------------------

def test_every_transcribed_number_is_relocatable_in_its_named_source():
    """The only mechanisable half — digits present near the site they belong to."""
    assert prs.unverified() == ()


def test_the_check_is_not_vacuous_in_either_direction():
    """A wrong digit and a near-miss both fail; otherwise the pass means nothing."""
    real = prs.PUBLISHED[0]
    assert prs.unverified([dataclasses.replace(real, gap=9999)])
    assert prs.unverified([dataclasses.replace(real, gap=real.gap + 1)])


def test_a_cell_that_publishes_nothing_verifies_trivially_and_that_is_correct():
    """`None` is *absent from the record*, so there is no digit to locate."""
    blank = prs.Cell("D-070", "5eb5123d", "lam_dependence._pure", None, None,
                     None, prs.PUBLISHED[0].source, True)
    assert blank.numbers == () and prs.unverified([blank]) == ()
    assert not blank.one_frame and not blank.both_frames


def test_every_cell_names_one_of_the_seven_disagreeing_sites():
    assert {c.site for c in prs.PUBLISHED} <= set(prs.SITES)


# --------------------------------------------------------------------------
# what a ratio needs, and what the record carries
# --------------------------------------------------------------------------

def test_only_the_two_licensed_batches_can_supply_a_same_tree_ratio():
    """D-066/D-067/D-069 are `TRANSPORTED` under D-069's guard — gaps and
    controls from different trees are differences of four counts, not two."""
    assert prs.readings(prs.licensed()) == ("D-070", "D-071")
    assert all(c.tree for c in prs.licensed())


def test_the_source_frame_control_was_never_published_on_a_licensed_tree():
    """D-077 narrowed this from "on any tree", which was false.

    The old spelling asserted `all(c.source_delta is None for c in PUBLISHED)`
    and passed for six cycles — not because no cycle published a source-frame
    control, but because this record had not transcribed the one that did.
    D-068 published three, and `magnitude_census` found them by counting the
    population rather than by re-reading the prose.  The claim that actually
    does the work downstream is the licensed one, and it is unchanged: a ratio
    as `RatioGrade` defines it still has zero complete *licensed* cells, which
    is why `common_sites(both_frames=True)` is still empty.
    """
    assert all(c.source_delta is None for c in prs.licensed())
    assert prs.common_sites(both_frames=True) == ()
    published = [c for c in prs.PUBLISHED if c.source_delta is not None]
    assert [c.decision for c in published] == ["D-068"] * 3
    assert all(c.both_frames is False for c in published), (
        "D-068's gaps are D-066's 64-tree numbers; pairing them with a 69-tree "
        "control is the transport D-069 forbids, so gap stays None")


def test_the_two_licensed_readings_overlap_on_exactly_two_sites():
    assert prs.usable_sites("D-070", prs.licensed()) == (
        "guard_reflexivity._is_set_valued",
        "lam_dependence._is_pure_literal",
        "lam_dependence._is_structural",
        "lam_dependence._numeric",
        "lam_dependence._pure",
    )
    assert prs.usable_sites("D-071", prs.licensed()) == (
        "guard_reflexivity._is_set_valued",
        "lam_dependence._pure",
    )
    assert prs.common_sites() == ("guard_reflexivity._is_set_valued",
                                  "lam_dependence._pure")


def test_q078s_no_new_run_half_is_unanswerable_and_not_narrowly():
    """The finding.  n=2 is the degenerate size, not merely a small one."""
    one = prs.answerable(both_frames=False)
    assert (one.n, one.floor) == (2, es.RANK_MIN_N) and not one.enough
    assert prs.answerable(both_frames=True).n == 0


def test_the_two_common_sites_are_exactly_the_pair_d071_quoted():
    """D-071's "2.5x to 13x, reproduced on four trees" is an ordering of one pair.

    `_pure` at 214/87 and `_is_set_valued` at 13/1 are the two endpoints it
    named, and they are the whole of the licensed overlap — so the range and the
    ordering are the same two numbers, and a two-point ordering reproduces by
    construction.
    """
    cells = {c.site: c for c in prs.licensed() if c.decision == "D-071"}
    pure = cells["lam_dependence._pure"]
    setv = cells["guard_reflexivity._is_set_valued"]
    assert (pure.gap, pure.measured_delta) == (214, 87)
    assert (setv.gap, setv.measured_delta) == (13, 1)
    assert pure.gap / pure.measured_delta == pytest.approx(2.46, abs=0.01)
    assert setv.gap / setv.measured_delta == pytest.approx(13.0)
    assert set(prs.common_sites()) == {pure.site, setv.site}


def test_the_missing_cells_are_named_so_the_next_run_knows_what_to_keep():
    """Every one of these was computed by the reading and then dropped."""
    gaps = prs.missing()
    assert ("D-071", "lam_dependence._numeric", "gap") in gaps
    assert ("D-070", "guard_reflexivity._has_git_diff_literal",
            "measured_delta") in gaps
    # the source frame is missing for all 11 licensed cells, hence the bulk
    assert sum(1 for _, _, f in gaps if f == "source_delta") == len(prs.licensed())


def test_persisting_one_more_site_would_make_it_answerable():
    """The floor is a data threshold, not a verdict — this is how it clears."""
    extra = prs.PUBLISHED + (
        prs.Cell("D-071", "9338e10e", "lam_dependence._is_structural", 66, 2,
                 None, prs.PUBLISHED[0].source, True),)
    assert prs.answerable(extra).n == 3
    assert prs.answerable(extra).enough
