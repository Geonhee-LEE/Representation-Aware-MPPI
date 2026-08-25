"""The prose must agree with the banked readings (D-036).

Fast tests only: everything here is arithmetic on transcribed constants plus
string search over files in the repo.  Nothing simulates, so nothing is
dispatch-fragile -- which is the property that lets this suite police claims
that *are*.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import claim_scope as cs
from eval.mppi_sandbox import dispatch_divergence as dd
from eval.mppi_sandbox import repair_admissibility as ra


def test_registry_covers_exactly_the_divergent_set():
    """A sixth flipping claim must be scoped, not silently uncovered."""
    assert {sc.claim for sc in cs.SCOPED_CLAIMS} == set(dd.CLAIMS)


def test_every_claim_names_an_oracle_and_an_instrument():
    """D-035's finding: choosing a machine relocates a constant, so the machine
    has to be written down next to it or the constant means nothing."""
    for sc in cs.SCOPED_CLAIMS:
        assert sc.oracle, sc.claim
        module, _, func = sc.instrument.partition("::")
        assert module == "dispatch_divergence", sc.claim
        assert hasattr(dd, func), f"{sc.claim}: no instrument {func}"


def test_transcribed_readings_match_the_banked_measurement_registry():
    """The instrument named must be the one that produced the reading.

    Guards the transcription, not the value -- if a future edit repoints a
    claim at a different statistic, the reading it carries is stale.
    """
    for sc in cs.SCOPED_CLAIMS:
        _, _, func = sc.instrument.partition("::")
        assert dd.CLAIMS[sc.claim] is getattr(dd, func), sc.claim


@pytest.mark.parametrize(
    "claim,expected",
    [("horizon_weight_swing", 0.1444), ("ab_protocol_overstatement", 0.2183)],
)
def test_retained_of_assertion_reproduces_the_D035_bill(claim, expected):
    """Same arithmetic as ``repair_admissibility``, reached a second way."""
    sc = next(s for s in cs.SCOPED_CLAIMS if s.claim == claim)
    assert sc.retained_of_assertion == pytest.approx(expected, abs=5e-4)

    priced = ra._threshold_repair(claim, sc.asserted_lo, sc.reading_other)
    assert priced.effect_retained == pytest.approx(sc.retained_of_assertion)


@pytest.mark.parametrize(
    "claim,expected", [("horizon_weight_swing", 0.096), ("ab_protocol_overstatement", 0.078)]
)
def test_a_reading_keeps_less_than_its_assertion(claim, expected):
    """The number readers meet survives worse than the number D-035 priced.

    A test that cleared its threshold by a margin has an effect *larger* than
    the one asserted, so the same absolute collapse eats a bigger fraction of
    it.  Reporting only ``retained_of_assertion`` flatters the record.
    """
    sc = next(s for s in cs.SCOPED_CLAIMS if s.claim == claim)
    assert sc.retained_of_reading == pytest.approx(expected, abs=5e-3)
    assert sc.retained_of_reading < sc.retained_of_assertion


def test_every_cited_section_exists():
    for sc in cs.SCOPED_CLAIMS:
        for cit in sc.citations:
            assert cs.section(cit.doc, cit.anchor).strip(), f"{cit.doc} {cit.anchor}"


def test_every_cited_section_carries_the_oracle_stamp():
    """STATE #3, overdue four cycles: a reader must not meet one of these
    numbers without meeting the machine it is conditional on."""
    missing = cs.unstamped()
    assert not missing, "unstamped: " + ", ".join(
        f"{c.anchor}@{c.doc} ({claim})" for claim, c in missing)


def test_other_quantity_citations_also_state_the_instrument_reading():
    """The entanglement D-036 names: ``D-030``'s ``2.0x`` is ``w(34)/w(15)``,
    while the assertion that flips is ``w(34)/w(30) = 1.3008``.  Comparing the
    first against the second machine's reading of the second overstates the
    collapse.  A section may keep its own number -- it may not keep it alone."""
    missing = cs.undisambiguated()
    assert not missing, "no instrument reading beside the cited number: " + ", ".join(
        f"{c.anchor}@{c.doc} (cites {c.states:g}x for {claim})" for claim, c in missing)


def test_instrument_tagged_citations_state_that_arm_s_reading():
    """Vacuous until D-046 -- every *hand-registered* citation turned out to be
    an ``other-quantity`` one, which was itself the finding.  The derived scan
    then found eleven ``instrument`` citations, so this now bites.

    Checked against the arm the citation names, not always the calibrated one:
    ``D-035``'s repaired thresholds and ``D-045``'s ``1.029x`` state the *AVX2*
    reading, and they are correct to do so.
    """
    checked = 0
    for sc in cs.SCOPED_CLAIMS:
        for cit in sc.citations:
            if cit.kind != "instrument":
                continue
            assert cit.arm in {"calibrated", "other"}, cit.arm
            expected = cit.reading_of(sc)
            rel = abs(cit.states - expected) / abs(expected)
            assert rel <= cs.CITATION_TOLERANCE, (
                f"{cit.doc} {cit.anchor} states {cit.states} for {sc.claim} "
                f"({cit.arm}); instrument reads {expected}")
            checked += 1
    assert checked, "no instrument-tagged citation left -- the guard went vacuous"


def test_other_quantity_citations_declare_what_they_measure():
    for sc in cs.SCOPED_CLAIMS:
        for cit in sc.citations:
            if cit.kind == "other-quantity":
                assert cit.quantity.strip(), f"{cit.doc} {cit.anchor}"
            assert cit.kind in {"instrument", "other-quantity"}, cit.kind


def test_stale_anchor_is_an_error_not_an_empty_section():
    with pytest.raises(LookupError):
        cs.section("docs/decisions.md", "## D-999")


def test_retained_of_citation_is_the_smallest_of_the_three():
    """Ordering that makes the retraction notice worth writing: the number the
    docs propagate survives worse than the reading, which survives worse than
    the assertion."""
    sc = next(s for s in cs.SCOPED_CLAIMS if s.claim == "horizon_weight_swing")
    cited = sc.retained_of_citation(2.0)
    assert cited == pytest.approx(0.0289, abs=5e-4)
    assert cited < sc.retained_of_reading < sc.retained_of_assertion


# --------------------------------------------------------------------------
# Registry completeness (D-046).  Everything above trusts SCOPED_CLAIMS to name
# every citation; these derive the population instead and diff against it.
# --------------------------------------------------------------------------


def test_claim_set_is_derived_from_the_module_not_the_hand_written_dict():
    """``dd.CLAIMS`` is hand-typed too, so agreeing with it proves little.

    A ``_foo() -> Claim`` that nobody added to ``CLAIMS`` would be invisible to
    both registries at once; this walks the module's own members.
    """
    assert set(cs.instrumented_claims()) == set(dd.CLAIMS), (
        "dispatch_divergence defines a Claim function that CLAIMS omits")
    assert set(cs.instrumented_claims()) == {sc.claim for sc in cs.SCOPED_CLAIMS}


def test_no_docs_section_states_a_reading_without_being_registered():
    """The D-046 invariant: derived population minus hand-typed list is empty.

    Non-empty means a section states a dispatch-fragile reading while sitting
    outside every guard built on this registry -- unstamped and
    undisambiguated, because nothing knows it is a citation.  Its first run
    found 11 such sites across 7 sections, 9 of them unstamped, including
    ``D-034`` -- the excursion table that tabulates *every* contested reading.
    """
    missing = cs.unregistered_citations()
    assert not missing, "unregistered citation sites: " + ", ".join(
        f"{d.anchor}@{d.doc} states {d.spelling} ({d.claim}/{d.reading})"
        for d in missing)


def test_declared_coincidences_are_still_found_by_the_scan():
    """A rejection for a match that has been edited away would silently
    re-admit the section if the number came back meaning something else."""
    stale = cs.stale_coincidences()
    assert not stale, f"COINCIDENTAL entries the scan no longer finds: {stale}"


def test_every_coincidence_declares_a_reason():
    for claim, doc, anchor, reason in cs.COINCIDENTAL:
        assert reason.strip(), f"{anchor}@{doc} ({claim})"
        assert any(sc.claim == claim for sc in cs.SCOPED_CLAIMS), claim


def test_unscannable_readings_are_declared_rather_than_silently_skipped():
    """D-042: an instrument that can only clear work must not be trusted to.

    ``hazard_shared_rungs`` reads 1.0/0.0, which render as bare ``1`` and ``0``
    and occur in every section.  Excluding them is correct; excluding them
    *silently* would make "no unregistered citations" read as a statement about
    a claim that was never scanned.
    """
    unscannable = cs.unscannable_readings()
    assert unscannable, "the degenerate-reading declaration went empty unnoticed"
    assert {c for c, _, _ in unscannable} == {"hazard_shared_rungs"}
    for _, _, value in unscannable:
        assert value in cs.DEGENERATE_READINGS


def test_matcher_does_not_find_a_reading_inside_a_longer_number():
    """``D-038``'s own bug, in this module's matcher: ``1.301`` is not in
    ``11.301``.  That section quotes the pair verbatim while explaining it."""
    swing = next(s for s in cs.SCOPED_CLAIMS if s.claim == "horizon_weight_swing")
    assert not cs._renders(swing.reading_calibrated, "값은 11.301 이었다")
    assert cs._renders(swing.reading_calibrated, "값은 1.301 이었다")


def test_matcher_finds_a_reading_written_to_more_digits_than_the_registry():
    """The direction that matters more: a section stating the reading *more*
    precisely is still stating it.  A right-boundary substring rule hid
    ``D-034``'s ``0.251146`` from a registry banking ``0.2511``."""
    sm = next(s for s in cs.SCOPED_CLAIMS if s.claim == "scale_match_achieved_ratio")
    assert cs._renders(sm.reading_calibrated, "| 0.251146 |")
    assert cs._renders(sm.reading_calibrated, "| 0.2511 |")
    assert not cs._renders(sm.reading_calibrated, "| 0.2612 |")


def test_derived_citations_covers_the_docs_citation_audit_scans():
    """Two registries naming the doc surface independently is one more surface
    for them to disagree on; asserted rather than imported (circular)."""
    from eval.mppi_sandbox import citation_audit as ca

    assert set(cs.CITED_DOCS) == set(ca.SCANNED_DOCS)
