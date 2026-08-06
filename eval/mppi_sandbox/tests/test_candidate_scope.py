"""Q-092's residue, and the orthogonality that explains it.

Every test here is fast: the point of the module under test is that the reading
was already on CI and the mechanism is constructible, so neither needs the
nested-suite fixture that made the original two rows look unreadable.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import candidate_scope as cs
from eval.mppi_sandbox import exclusion_scope as es
from eval.mppi_sandbox import predicate_vacuity as pv


class TestTheMechanism:
    """`grade` and `manufactured_candidate` read disjoint fields."""

    def test_a_self_entry_can_be_a_manufactured_candidate(self):
        witness = cs.orthogonality_witness()
        assert witness.grade == es.SELF_ENTRY
        assert witness.manufactured_candidate

    def test_the_witness_needs_no_measurement_to_be_a_self_entry(self):
        """`grade` derives it from the file stem, so the conjunction is
        reachable by construction — not an accident of one population."""
        site = "exclusion_scope.RankAgreement.reportable"
        own_test = "eval/mppi_sandbox/tests/test_exclusion_scope.py"
        assert es.grade(site, (own_test,)) == es.SELF_ENTRY

    def test_the_two_properties_read_disjoint_fields(self):
        """The structural claim behind "orthogonal": moving the direction does
        not move the grade, and moving the hider does not move the direction."""
        base = cs.orthogonality_witness()

        flipped_direction = es.Masked(
            site=base.site,
            excluded_verdict=pv.VERDICT_UNOBSERVED,
            lifted_verdict=base.lifted_verdict,
            attributed_to=base.attributed_to,
            grade=base.grade,
        )
        assert flipped_direction.grade == base.grade
        assert not flipped_direction.manufactured_candidate

        foreign = "eval/mppi_sandbox/tests/test_guard_witness.py"
        flipped_hider = es.Masked(
            site=base.site,
            excluded_verdict=base.excluded_verdict,
            lifted_verdict=base.lifted_verdict,
            attributed_to=(foreign,),
            grade=es.grade(base.site, (foreign,)),
        )
        assert flipped_hider.grade == es.COLLATERAL
        assert flipped_hider.manufactured_candidate == base.manufactured_candidate


class TestTheReadingIsPinnedNotRecalled:
    def test_observed_is_the_headline_pair_plus_the_residue(self):
        assert cs.observed() == tuple(sorted(cs.HEADLINE + cs.RESIDUE))
        assert len(cs.observed()) == 6

    def test_the_headline_pair_survived_the_move(self):
        """The literal was not wrong about its own members — only about being
        an equality over the union."""
        assert set(cs.HEADLINE) <= set(cs.observed())

    def test_the_residue_is_disjoint_from_the_headline(self):
        assert not set(cs.RESIDUE) & set(cs.HEADLINE)

    def test_provenance_names_a_ci_job_not_a_local_run(self):
        assert cs.PROVENANCE["run"] and cs.PROVENANCE["job"]
        assert "slow" in cs.PROVENANCE["workflow"]


class TestItDoesNotGeneraliseThreeUnreadSites:
    """D-098's error, refused by construction."""

    def test_coverage_is_one_of_four(self):
        assert cs.coverage() == (1, 4)

    def test_every_ungraded_residue_site_reads_unread(self):
        reading = cs.reading()
        ungraded = [s for s in cs.RESIDUE if s not in cs.GRADED]
        assert len(ungraded) == 3
        assert all(reading[s] == cs.UNREAD for s in ungraded)

    def test_unread_is_not_an_exclusion_scope_grade(self):
        """A fact about the reading must not be spellable as a fact about the
        site — that conflation is how an absence gets read as a clean."""
        assert cs.UNREAD not in (es.SELF_ENTRY, es.COLLATERAL, es.UNATTRIBUTED)

    def test_graded_is_exactly_what_the_log_states(self):
        assert cs.GRADED == {
            "exclusion_scope.RankAgreement.reportable": es.SELF_ENTRY,
        }

    @pytest.mark.parametrize("site", cs.RESIDUE)
    def test_no_residue_site_is_silently_defaulted(self, site):
        assert cs.reading()[site] in (es.SELF_ENTRY, es.COLLATERAL,
                                      es.UNATTRIBUTED, cs.UNREAD)


class TestTheVerdict:
    def test_q092_is_real_not_machine(self):
        v = cs.verdict()
        assert v.real

    def test_the_two_rows_are_one_finding(self):
        v = cs.verdict()
        assert v.findings == 1
        assert v.shared_site in cs.RESIDUE

    def test_the_verdict_carries_its_own_coverage(self):
        """So no caller can quote the verdict without the 1/4 attached."""
        v = cs.verdict()
        assert (v.graded, v.total) == cs.coverage()
        assert f"{v.graded}/{v.total}" in str(v)

    def test_the_shared_site_is_the_one_site_the_log_grades(self):
        assert cs.verdict().shared_site in cs.GRADED
