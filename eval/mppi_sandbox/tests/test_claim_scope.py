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


def test_instrument_tagged_citations_state_the_calibrated_reading():
    """Currently vacuous -- every citation in the repo turned out to be an
    ``other-quantity`` one, which is itself the finding.  Kept so the first
    citation that *does* claim to be the instrument's own gets checked."""
    for sc in cs.SCOPED_CLAIMS:
        for cit in sc.citations:
            if cit.kind != "instrument":
                continue
            rel = abs(cit.states - sc.reading_calibrated) / sc.reading_calibrated
            assert rel <= cs.CITATION_TOLERANCE, (
                f"{cit.doc} {cit.anchor} states {cit.states} for {sc.claim}, "
                f"instrument reads {sc.reading_calibrated}")


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
