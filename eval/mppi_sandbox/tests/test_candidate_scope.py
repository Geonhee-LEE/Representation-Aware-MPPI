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


class TestTheRunFreeBound:
    """What the exclusion list settles on its own — and what it cannot."""

    def test_the_bound_settled_nothing_about_the_residue(self):
        """The price tag on the measurement: every residue site's module has a
        test in `EXCLUDED_TESTS`, so `SELF_ENTRY` was reachable for all four and
        the cheap route discriminates nothing."""
        assert cs.RUN_FREE_DISCHARGED == ()
        assert set(cs.run_free_reading().values()) == {cs.INDETERMINATE}

    def test_it_refutes_self_entry_when_no_self_hider_exists(self):
        """Non-vacuous the only way that matters: a site whose module has no
        excluded test *is* settled, with no run."""
        foreign = ("eval/mppi_sandbox/tests/test_guard_witness.py",)
        site = "predicate_inputs.Drift.stationary"
        assert cs.self_hiders(site, foreign) == ()
        assert cs.self_entry_is_impossible(site, foreign)
        assert cs.run_free_reading((site,), foreign) == {site: es.COLLATERAL}

    def test_it_never_answers_self_entry(self):
        """One-sided by construction: confirming needs to know *which* file did
        the hiding, and that is measured.  Asserted over the live list and over
        a list containing nothing but self-hiders."""
        only_self = ("eval/mppi_sandbox/tests/test_predicate_inputs.py",)
        for excluded in (tuple(pv.EXCLUDED_TESTS), only_self):
            answers = set(cs.run_free_reading(cs.RESIDUE, excluded).values())
            assert es.SELF_ENTRY not in answers

    def test_the_headline_pair_is_collateral_with_no_run_at_all(self):
        """The asymmetry the refuted assertion was hiding: the half carrying the
        finding is settled by construction, the half nobody measured is not."""
        assert cs.HEADLINE_FORCED == cs.HEADLINE
        forced = cs.run_free_reading(cs.HEADLINE)
        assert set(forced.values()) == {es.COLLATERAL}
        assert all(cs.reading()[s] == forced[s] for s in cs.HEADLINE)

    def test_indeterminate_is_neither_a_grade_nor_unread(self):
        assert cs.INDETERMINATE not in (es.SELF_ENTRY, es.COLLATERAL,
                                        es.UNATTRIBUTED, cs.UNREAD)

    def test_the_bound_derives_the_module_the_way_grade_does(self):
        """If the two disagreed about what "own module" means, the bound could
        refute a `SELF_ENTRY` that `grade` then hands out."""
        for site in cs.observed():
            for hider in cs.self_hiders(site):
                assert es.grade(site, (hider,)) == es.SELF_ENTRY


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


class TestTheUnreadRuleOutlivesTheSitesItCovered:
    """D-098's error, refused by construction — and the rule kept non-vacuous.

    The rule "an ungraded site reads `UNREAD`, never a default" covered three
    sites until this cycle graded them, and now covers none.  A rule whose only
    witness is the live population stops being tested the moment the population
    moves, which is how two of this branch's own tests went green over an empty
    dict (06-06).  So it is exercised on a site that does not exist.
    """

    def test_coverage_is_four_of_four(self):
        assert cs.coverage() == (4, 4)
        assert set(cs.GRADED) == set(cs.RESIDUE)

    def test_a_site_with_no_grade_still_reads_unread(self):
        """The rule, on a hypothetical seventh member — the only witness left."""
        seventh = "some_module.SomeClass.some_predicate"
        reading = cs.reading(graded=cs.GRADED, residue=cs.RESIDUE + (seventh,))
        assert reading[seventh] == cs.UNREAD
        assert cs.coverage(residue=cs.RESIDUE + (seventh,)) == (4, 5)

    def test_dropping_a_grade_reopens_the_site_rather_than_defaulting_it(self):
        """Negative control on the table itself: remove an entry and the site
        must go back to `UNREAD`, not inherit its neighbours' grade."""
        thinned = {k: v for k, v in cs.GRADED.items()
                   if k != "predicate_inputs.Spread.stationary"}
        reading = cs.reading(graded=thinned)
        assert reading["predicate_inputs.Spread.stationary"] == cs.UNREAD
        assert cs.coverage(graded=thinned) == (3, 4)

    def test_unread_is_not_an_exclusion_scope_grade(self):
        """A fact about the reading must not be spellable as a fact about the
        site — that conflation is how an absence gets read as a clean."""
        assert cs.UNREAD not in (es.SELF_ENTRY, es.COLLATERAL, es.UNATTRIBUTED)

    def test_graded_is_two_of_each_kind(self):
        assert cs.GRADED == {
            "exclusion_scope.RankAgreement.reportable": es.SELF_ENTRY,
            "exclusion_scope.ReplicatedReading.licensed": es.SELF_ENTRY,
            "predicate_inputs.Drift.stationary": es.COLLATERAL,
            "predicate_inputs.Spread.stationary": es.COLLATERAL,
        }

    @pytest.mark.parametrize("site", cs.RESIDUE)
    def test_no_residue_site_is_silently_defaulted(self, site):
        assert cs.reading()[site] in (es.SELF_ENTRY, es.COLLATERAL,
                                      es.UNATTRIBUTED, cs.UNREAD)


class TestTheFindingIsFourNotTwo:
    """What grading the residue changed about the answer."""

    def test_collateral_is_the_headline_pair_plus_both_predicate_inputs_sites(self):
        assert cs.of_grade(es.COLLATERAL) == tuple(sorted(
            cs.HEADLINE + ("predicate_inputs.Drift.stationary",
                           "predicate_inputs.Spread.stationary")))

    def test_the_two_self_entries_are_the_exclusion_scope_ones(self):
        assert cs.of_grade(es.SELF_ENTRY) == (
            "exclusion_scope.RankAgreement.reportable",
            "exclusion_scope.ReplicatedReading.licensed")

    def test_the_partition_covers_every_observed_site(self):
        parts = sum((cs.of_grade(g) for g in
                     (es.SELF_ENTRY, es.COLLATERAL, es.UNATTRIBUTED)), ())
        assert tuple(sorted(parts)) == cs.observed()

    def test_a_foreign_file_is_the_sole_hider_of_one_predicate_inputs_site(self):
        """The widening the self-entry assertion exists to catch, having
        happened: `test_exclusion_scope.py` is not `predicate_inputs`'
        instrument, and for `Spread.stationary` nothing else hid it."""
        hiders = cs.ATTRIBUTED["predicate_inputs.Spread.stationary"]
        assert hiders == ("eval/mppi_sandbox/tests/test_exclusion_scope.py",)
        assert es.grade("predicate_inputs.Spread.stationary", hiders) == \
            es.COLLATERAL

    def test_one_self_hider_does_not_make_a_site_a_self_entry(self):
        """`Drift.stationary` is hidden by its own instrument *and* a foreign
        one.  `grade` is `every`, not `some` — the weaker reading would have
        filed it as bookkeeping."""
        hiders = cs.ATTRIBUTED["predicate_inputs.Drift.stationary"]
        assert len(hiders) == 2
        assert cs.self_hiders("predicate_inputs.Drift.stationary") != ()
        assert es.grade("predicate_inputs.Drift.stationary", hiders) == \
            es.COLLATERAL

    def test_every_grade_names_the_reading_it_came_from(self):
        """Three of the four were taken on this box, not on CI.  D-086 forbids
        letting one module-level provenance imply the stronger reading for all
        of them."""
        assert set(cs.SOURCE) == set(cs.GRADED)
        assert set(cs.SOURCE.values()) <= set(cs.SOURCES)
        assert cs.SOURCES[cs.SOURCE[
            "exclusion_scope.RankAgreement.reportable"]]["kind"] == "ci"
        local = [s for s, k in cs.SOURCE.items()
                 if cs.SOURCES[k]["kind"] == "local"]
        assert len(local) == 3

    def test_the_local_source_says_why_a_local_reading_is_admissible(self):
        """A local reading needs an argument, not a habit."""
        entry = cs.SOURCES["local:04c445f7"]
        assert entry["why_admissible"]
        assert entry["call"].startswith("exclusion_scope.effect_from_one_run")


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

    def test_the_shared_site_is_graded_and_is_the_harmless_kind(self):
        """The site both CI rows name is a `SELF_ENTRY` — so the row that made
        this branch red is the bookkeeping half, and the half worth acting on
        (`of_grade(COLLATERAL)`) was never named by either failure."""
        shared = cs.verdict().shared_site
        assert cs.GRADED[shared] == es.SELF_ENTRY
        assert shared not in cs.of_grade(es.COLLATERAL)
