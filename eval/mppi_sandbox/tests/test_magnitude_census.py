"""Q-083: `PUBLISHED` is a sample, and the verdict survives every spelling.

The finding this file pins is not the count.  It is that the count is
*unstable* --- 19 magnitude-printing decisions under the permissive spelling, 8
under the strict one --- and the **verdict is not**.  Under all four spellings
`PUBLISHED`'s five transcribed decisions leave uncovered decisions carrying
novel magnitudes, so D-075's denominator of 23 is a number over an unknown
population no matter which spelling a future cycle prefers.

That matters because D-076 was defeated by exactly this shape in reverse: it
measured two spellings of a derivation, found they disagreed, and had to stop
because the answer depended on the choice.  Here the choice is real and the
answer does not depend on it, which is the only reason the cycle gets to
conclude anything.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import magnitude_census as mc
from eval.mppi_sandbox import published_ratios as prs

# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

DOC = """intro prose, no decision yet

## D-002 — older
`lam_dependence._pure` gap 40 here.

## D-010 — newer
`_pure` again at 40, and `_is_structural` **7** on the same line.
"""


def test_sections_are_returned_oldest_first_regardless_of_file_order():
    """The document is written newest-first; `novel` needs the other order.

    Sorting on the parsed number rather than reversing the file is what keeps a
    manually mis-ordered entry from silently inverting a novelty verdict.
    """
    got = mc.sections(DOC)
    assert [s.decision for s in got] == ["D-002", "D-010"]
    assert [s.number for s in got] == [2, 10]
    assert "intro prose" not in "".join(s.body for s in got)


def test_the_real_document_parses_to_the_number_of_decisions_it_claims():
    doc = mc.sections((mc.REPO_ROOT / mc.DECISIONS_DOC).read_text(encoding="utf-8"))
    assert len(doc) == len({s.decision for s in doc}), "no duplicate D-NNN"
    assert [s.number for s in doc] == sorted(s.number for s in doc)
    assert doc[0].decision == "D-001"


def test_site_names_are_derived_from_published_ratios_not_retyped():
    """D-047: a site added to the record is censused in the same commit."""
    assert set(mc.SHORT_NAMES) == {s.split(".")[-1] for s in prs.SITES}


# --------------------------------------------------------------------------
# the two failure modes a scan of this shape has
# --------------------------------------------------------------------------

def test_a_shared_suffix_does_not_conflate_two_sites():
    """`_pure` is a suffix of `_is_pure_literal`; a substring test would merge them."""
    doc = mc.sections("## D-001 — x\n`_is_pure_literal` is 5.\n")
    assert {m.site for m in mc.scan(doc)} == {"_is_pure_literal"}


def test_a_module_qualified_name_is_marked_qualified_and_a_bare_one_is_not():
    doc = mc.sections("## D-001 — x\n`lam_dependence._pure` 40\n\n"
                      "## D-002 — y\n`_pure` 41\n")
    by_decision = {m.decision: m for m in mc.scan(doc)}
    assert by_decision["D-001"].qualified is True
    assert by_decision["D-002"].qualified is False


def test_crosstalk_fires_only_on_digits_behind_a_second_site_name():
    """Prose here routinely puts two sites and four numbers on one line."""
    doc = mc.sections("## D-001 — x\n`_pure` **40** and `_is_structural` **7**\n")
    scanned = mc.scan(doc)
    pure_40 = next(m for m in scanned if m.site == "_pure" and m.value == 40)
    pure_7 = next(m for m in scanned if m.site == "_pure" and m.value == 7)
    struct_7 = next(m for m in scanned if m.site == "_is_structural")
    assert pure_40.crosstalk is False, "nothing between the anchor and its own digit"
    assert pure_7.crosstalk is True, "`_is_structural` sits between them"
    assert struct_7.crosstalk is False and struct_7.value == 7


def test_the_window_stops_where_published_ratios_stops_reading():
    """A magnitude this census finds is one `unverified` could re-locate."""
    assert mc.WINDOW_LINES == 1
    doc = mc.sections("## D-001 — x\n`_pure`\n40\n41\n")
    values = {m.value for m in mc.scan(doc)}
    assert values == {40}, "the line after the anchor is in, the one after that is out"


# --------------------------------------------------------------------------
# novelty — the discriminator that separates a reading from a re-quote
# --------------------------------------------------------------------------

def test_novel_keeps_the_earliest_decision_to_print_a_site_value_pair():
    got = mc.novel(mc.scan(mc.sections(DOC)))
    pairs = {(m.decision, m.site, m.value) for m in got}
    assert ("D-002", "_pure", 40) in pairs
    assert ("D-010", "_pure", 40) not in pairs, "D-010 re-quotes D-002's 40"
    assert ("D-010", "_is_structural", 7) in pairs


def test_novelty_is_a_lower_bound_and_the_docstring_says_so():
    """It cannot separate a new reading that collides with an old value.

    D-076 measured how often small integers collide across unrelated trees, so
    this limit is quantified elsewhere rather than merely conceded here.
    """
    doc = mc.sections("## D-001 — x\n`_pure` 12\n\n## D-002 — y\n`_pure` 12\n")
    assert len(mc.novel(mc.scan(doc))) == 1


# --------------------------------------------------------------------------
# Q-083's answer
# --------------------------------------------------------------------------

SPELLINGS = {
    "permissive": lambda m: True,
    "qualified": lambda m: m.qualified,
    "no-crosstalk": lambda m: not m.crosstalk,
    "clean": lambda m: m.clean,
}


def test_published_is_a_sample_not_a_census():
    """The headline.  Five decisions transcribed out of nineteen that print.

    Five and not four because D-077 acted on its own shopping list in-cycle:
    D-068 was a candidate when the census first ran and is covered now.  The
    verdict did not move, which is the honest reading — clearing one of
    thirteen candidates does not turn a sample into a census.

    Nineteen, not eighteen: these are the counts **after** the D-077 entry was
    written to `docs/decisions.md`, per D-043/D-044 — the distinction D-077's
    own prose got wrong and D-078 repaired.

    D-077 pinned `decisions == 77` here and predicted that writing D-078 would
    break it, on the reasoning that a stale pin is a stale measurement.  D-078
    kept the forcing function and dropped the breakage: the *total* is read
    as-of the newest entry, so it tracks the document, while the counts the
    verdict actually rests on stay hard-pinned.  Cycle N+1 no longer has to
    re-type a number to stay green, which is what made the stale triple
    survivable in the first place.
    """
    doc = mc.sections((mc.REPO_ROOT / mc.DECISIONS_DOC).read_text(encoding="utf-8"))
    got = mc.census()
    assert got.decisions == len(doc)
    # D-105 made 20 / 14: its prose prints the 6-of-99 reading, the 78->80
    # census move and the 9->6 first-cut correction, so it is a
    # magnitude-printing decision by the same test as the other nineteen.
    # D-110 makes 21 / 15, and the way that bill arrived is the point: the
    # cycle that wrote D-110 published "second-order census cost nil: 106
    # tests unmoved" and never ran the suite (its own commit trailer reads
    # `Metric: sandbox:pass=pending-4a-ter`), so the entry sat in the pool
    # unpaid until a cycle that did run one picked it up.  Fifth instance of
    # an unmeasured "census nil" on this branch -- the claim is only available
    # to a cycle that took a reading.
    # D-339 makes 22 / 16, and it is the *cheapest* possible instance of this
    # bill: D-338's own entry prints the 3606/3609 and 3604/3609 suite counts
    # and the 122-guard tally, so writing it moved this census by one.  Worth
    # separating from the four OBSERVABLES failures it shipped alongside --
    # Q-165 attributed all four to `OBSERVABLES` entering `TYPED`, and these
    # two are not that.  They would have moved if D-338 had written no code at
    # all, because the mover is the REPORT-phase doc write D-043 mandates.
    # D-376 makes 23 / 17, and it is the same bill again with a sharper label:
    # the entry that moved this census is the one where a cycle wrote down that
    # its own suite came back red, quoting the pass/fail/error split.  The
    # mover is the REPORT-phase doc write D-043 mandates, so a cycle is charged
    # for the act of recording a measurement honestly.  Worth naming, because
    # the incentive runs the wrong way: the cheapest entry to write is the one
    # that quotes no numbers.  Paid here rather than avoided, which is the only
    # answer that keeps D-043 and this census pointing the same direction.
    assert got.printing == 23
    assert got.transcribed == 5
    assert got.uncovered_candidates == 17
    assert got.is_census is False


def test_the_verdict_survives_every_spelling_even_though_the_count_does_not():
    """The reason this cycle gets to conclude anything.

    The permissive spelling over-counts — D-050/D-051 discuss `_is_set_valued`
    as a *predicate under construction* and the nearby integers are D-numbers
    and cycle counts, not magnitudes of anything.  The strict spelling
    under-counts — it drops D-070 and D-071, the two licensed readings the whole
    record is built out of, because this branch's prose spells sites bare.
    Neither is the right filter.  Both say SAMPLE.
    """
    scanned = mc.scan()
    verdicts = {}
    for name, keep in SPELLINGS.items():
        subset = [m for m in scanned if keep(m)]
        unc = mc.uncovered(subset)
        verdicts[name] = (len(mc.printing(subset)),
                          sum(1 for u in unc if u.candidate))
    # -> 23 (D-376): same shape a second time. The permissive spelling picks up
    # the new entry, the strict one does not, so the gap widened by exactly the
    # one entry and the verdict is unmoved -- which is this test's whole claim.
    assert verdicts["permissive"][0] == 23 and verdicts["clean"][0] == 8
    assert all(candidates > 0 for _, candidates in verdicts.values()), verdicts
    assert all(printing > mc.census().transcribed
               for printing, _ in verdicts.values()), verdicts


def test_the_census_counts_its_own_decision_entry():
    """The self-entry, and this time it is unavoidable rather than sloppy.

    D-045..D-076 kept entering the *predicate* populations they audit, and every
    one of those was an implementation choice that could in principle have been
    made differently.  This one cannot: a census of the decision log, published
    as a decision, counts itself.  D-077 prints site-adjacent magnitudes (it
    quotes D-068's 40 / 41 / 28 to explain what was transcribed), so it lands in
    `printing`, and `PUBLISHED` does not transcribe it, so it lands in
    `uncovered` as a candidate.

    Pinned rather than suppressed.  Exempting the current decision would be a
    typed exemption of exactly the kind D-076 found removing nothing, and the
    honest number is the one that includes the observer.
    """
    unc = {u.decision: u for u in mc.uncovered()}
    assert "D-077" in unc and unc["D-077"].candidate
    assert "D-077" not in mc.transcribed()


def test_the_strict_spelling_drops_both_licensed_readings():
    """Named explicitly so nobody adopts `clean` as the filter."""
    clean = [m for m in mc.scan() if m.clean]
    assert set(mc.printing(clean)).isdisjoint(prs.readings(prs.licensed()))


def test_d067_is_an_uncovered_candidate_under_every_spelling():
    """The one with the strongest remaining claim to being a missing reading.

    D-068 was the other, and it is gone from this list because D-077 acted on
    it: it published three source-frame controls, `PUBLISHED` carried none, and
    the record carries them now.  That is the census paying for itself once —
    the list is a shopping list, not a scoreboard.
    """
    scanned = mc.scan()
    for name, keep in SPELLINGS.items():
        subset = [m for m in scanned if keep(m)]
        candidates = {u.decision for u in mc.uncovered(subset) if u.candidate}
        assert "D-067" in candidates, name
        assert "D-068" not in candidates, name


def test_the_census_found_d068_by_counting_not_by_re_reading_the_prose():
    """What the transcription of D-068 actually bought, stated as a pin.

    Nothing licensed moved — `common_sites(both_frames=True)` is still empty and
    every D-075 count is bit-identical.  What moved is that the record now
    carries a source-frame control at all, so the sentence
    `published_ratios` used to open with is no longer false.
    """
    published = [c for c in prs.PUBLISHED if c.source_delta is not None]
    assert {(c.site.split(".")[-1], c.source_delta) for c in published} == {
        ("_pure", 40), ("_is_structural", 41), ("_has_git_diff_literal", 28)}
    assert prs.unverified() == (), "each one re-locates in docs/decisions.md"
    assert prs.common_sites(both_frames=True) == ()


def test_a_decision_that_only_re_quotes_is_not_a_candidate():
    """D-075 prints seven site-adjacent integers and takes no reading."""
    by_decision = {u.decision: u for u in mc.uncovered()}
    assert by_decision["D-075"].total == 7
    assert by_decision["D-075"].novel == 0
    assert by_decision["D-075"].candidate is False


def test_transcribed_decisions_are_excluded_from_the_shopping_list():
    covered = set(mc.transcribed())
    assert covered == {"D-066", "D-068", "D-069", "D-070", "D-071"}
    assert covered.isdisjoint({u.decision for u in mc.uncovered()})


# --------------------------------------------------------------------------
# the scan's own error rate, as integers rather than as a caveat
# --------------------------------------------------------------------------

def test_precision_is_reported_and_is_low():
    """D-076's cheapest finding, asked of a scanner instead of a filter."""
    got = mc.precision()
    assert got.total > 0
    assert got.clean <= got.qualified <= got.total
    assert got.clean <= got.total - got.crosstalk
    assert got.clean_fraction < 0.25, (
        "if this ever rises, the prose started qualifying site names and the "
        "strict spelling may have become usable — re-read the census")


def test_the_bulk_of_the_imprecision_is_bare_spelling_not_crosstalk():
    """Which one dominates decides what a future fix would have to change.

    Crosstalk is a property of the scan and could be narrowed.  Bare spelling is
    a property of the *document*, so the strict spelling cannot be rescued
    without rewriting six cycles of prose.
    """
    got = mc.precision()
    assert got.total - got.qualified > got.crosstalk


# --------------------------------------------------------------------------
# D-078: the quoted verdict is indexed by its own entry, and checked
# --------------------------------------------------------------------------

def test_as_of_rewinds_the_document_side_only():
    """The census restricted to the entries that existed at a given decision."""
    doc = mc.sections((mc.REPO_ROOT / mc.DECISIONS_DOC).read_text(encoding="utf-8"))
    newest, previous = doc[-1].decision, doc[-2].decision
    now = mc.census()
    at_77 = mc.as_of(newest)
    at_76 = mc.as_of(previous)
    assert at_77 == now, "as-of the newest entry is today's reading"
    assert at_76.decisions == at_77.decisions - 1
    assert at_76.printing <= at_77.printing
    # transcribed is a code registry with no history here; as_of says so by
    # holding it constant rather than pretending to rewind it.
    assert at_76.transcribed == at_77.transcribed


def test_as_of_reproduces_the_numbers_d077_actually_printed():
    """The diagnosis behind D-078, as an equality rather than a story.

    D-077's prose carried ``18 printing / 12 uncovered`` over 76 decisions while
    its own test pinned 19/13 over 77.  Both were measurements of the census;
    they differ by exactly one write --- D-077's own entry.  That the stale
    triple is *precisely* ``as_of("D-076")`` is what rules out a typo and rules
    in the write-ordering defect D-043 exists for.
    """
    stale = mc.as_of("D-076")
    assert (stale.printing, stale.uncovered_candidates, stale.decisions) == (18, 12, 76)


def test_as_of_rejects_a_decision_that_does_not_exist():
    with pytest.raises(KeyError):
        mc.as_of("D-999")


def test_every_quoted_census_verdict_agrees_with_its_own_as_of_reading():
    """The guard D-077 needed and did not have.

    A census verdict written in the canonical spelling is re-checkable forever,
    because it is indexed by the entry that states it.  This is the assertion
    that would have gone red on D-077 as pushed.
    """
    assert mc.drifted() == (), (
        "a decision entry quotes a census verdict that disagrees with the "
        "document as it stood at that entry: " + repr(mc.drifted()))


def test_the_canonical_spelling_is_actually_used_somewhere():
    """A guard over an empty population is the exact defect D-076 found.

    ``drifted() == ()`` passes vacuously if no entry uses the spelling, so the
    bite is asserted separately --- D-076's 0-of-22 lesson applied to this
    cycle's own guard on the cycle that writes it.
    """
    quotes = mc.quoted()
    assert len(quotes) >= 1
    assert any(q.decision == "D-077" for q in quotes)


def test_a_drifted_quote_is_detected():
    """Fail the guard on purpose: the negative control for the test above."""
    doc = mc.sections((mc.REPO_ROOT / mc.DECISIONS_DOC).read_text(encoding="utf-8"))
    tampered = tuple(
        mc.Section(s.decision, s.number,
                   s.body.replace("19 printing / 5 transcribed / 13 uncovered (77 decisions)",
                                  "18 printing / 5 transcribed / 12 uncovered (76 decisions)"))
        if s.decision == "D-077" else s
        for s in doc
    )
    bad = mc.drifted(doc=tampered)
    assert len(bad) == 1
    quote, measured = bad[0]
    assert quote.decision == "D-077"
    assert quote.printing == 18 and measured.printing == 19
