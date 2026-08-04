"""The exclusion list's own audit — that a candidate is not an ignore-list artifact.

The cheap tests pin the partition's semantics against hand-built readings, so
every rule is exercised both ways without paying for a suite run.  The one
`@pytest.mark.slow` test is the measurement itself: four runs of the fast half,
asserting the two sites the exclusion actually manufactured.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import exclusion_scope as es
from eval.mppi_sandbox import predicate_vacuity as pv

GW = "eval/mppi_sandbox/tests/test_guard_witness.py"
PV = "eval/mppi_sandbox/tests/test_predicate_vacuity.py"


# --------------------------------------------------------------------------
# the subject convention, and the mirror that makes it falsifiable
# --------------------------------------------------------------------------

def test_subject_is_derived_from_the_stem_both_ways():
    assert es.subject_of(GW) == "guard_witness"
    assert es.subject_of("eval/mppi_sandbox/tests/conftest.py") == "conftest"


def test_every_exclusion_names_a_real_module():
    """`SELF_ENTRY` must be decided against a module, not against a string.

    Non-empty means a module was renamed and the grading below is guessing —
    the failure mode a hand-written convention has and a derivation does not.
    """
    assert es.unresolved_subjects() == ()


# --------------------------------------------------------------------------
# the grade — both answers, plus the refusal
# --------------------------------------------------------------------------

def test_grade_is_self_entry_when_the_file_is_the_sites_instrument():
    assert es.grade("guard_witness.Attempt.satisfiable", [GW]) == es.SELF_ENTRY


def test_grade_is_collateral_when_the_file_is_merely_a_caller():
    """The finding's shape: `test_guard_witness.py` is not `local_only_audit`'s test."""
    assert es.grade("local_only_audit.guard_is_derived", [GW]) == es.COLLATERAL


def test_grade_refuses_rather_than_guesses_with_no_attribution():
    """A move no single lift reproduced is reported, not folded into a grade.

    D-050's rule: a probe that cannot separate two cases has measured neither.
    """
    assert es.grade("anything.at_all", []) == es.UNATTRIBUTED


def test_a_site_hidden_by_two_files_is_collateral_unless_both_are_its_test():
    """`all`, not `any` — one non-instrument attributor is enough to grade it."""
    assert es.grade("predicate_vacuity.Reading.is_candidate", [PV]) == es.SELF_ENTRY
    assert es.grade("predicate_vacuity.Reading.is_candidate",
                    [PV, GW]) == es.COLLATERAL


# --------------------------------------------------------------------------
# classify — pure, so the semantics cost nothing to pin
# --------------------------------------------------------------------------

@pytest.fixture
def effect():
    """Three readings covering every grade and both move directions."""
    excluded = {
        "local_only_audit.guard_is_derived": pv.VERDICT_ALWAYS_TRUE,
        "guard_witness.Attempt.satisfiable": pv.VERDICT_UNOBSERVED,
        "some_module.interacts": pv.VERDICT_ALWAYS_FALSE,
        "some_module.unmoved": pv.VERDICT_BOTH,
    }
    lifted = {
        "local_only_audit.guard_is_derived": pv.VERDICT_BOTH,
        "guard_witness.Attempt.satisfiable": pv.VERDICT_ALWAYS_TRUE,
        "some_module.interacts": pv.VERDICT_BOTH,
        "some_module.unmoved": pv.VERDICT_BOTH,
    }
    per_file = {
        GW: {"local_only_audit.guard_is_derived": pv.VERDICT_BOTH,
             "guard_witness.Attempt.satisfiable": pv.VERDICT_ALWAYS_TRUE},
        PV: {},
    }
    return es.Effect(masked=es.classify(excluded, lifted, per_file),
                     excluded=excluded, lifted=lifted, excluded_tests=(GW, PV))


def test_only_moved_predicates_enter_the_masked_set(effect):
    assert "some_module.unmoved" not in {m.site for m in effect.masked}
    assert len(effect.masked) == 3


def test_grades_partition_the_masked_set(effect):
    """A fourth grade added without a home would otherwise vanish from the counts."""
    graded = sum(len(effect.of(g))
                 for g in (es.SELF_ENTRY, es.COLLATERAL, es.UNATTRIBUTED))
    assert graded == len(effect.masked)


def test_an_unreproduced_move_is_unattributed_not_collateral(effect):
    """`some_module.interacts` moves only when both files are lifted at once."""
    assert es.collateral(effect) == ("local_only_audit.guard_is_derived",)
    assert [m.site for m in effect.of(es.UNATTRIBUTED)] == ["some_module.interacts"]


# --------------------------------------------------------------------------
# the direction that costs something
# --------------------------------------------------------------------------

def test_manufactured_candidate_needs_a_two_sided_predicate_underneath(effect):
    """`BOTH → one-sided` invents a suspect; `UNOBSERVED → one-sided` does not.

    The second only means the excluded file was the predicate's sole caller,
    which is a statement about the suite and not about the exclusion.
    """
    by_site = {m.site: m for m in effect.masked}
    assert by_site["local_only_audit.guard_is_derived"].manufactured_candidate
    assert not by_site["guard_witness.Attempt.satisfiable"].manufactured_candidate


def test_manufactured_candidates_include_the_unattributed_move(effect):
    """Grade and direction are independent readings and must not be conflated.

    `some_module.interacts` is `UNATTRIBUTED` — this module cannot say which
    file hid it — and still `ALWAYS_FALSE → BOTH`, so it is still a suspect the
    exclusion invented.  Filtering manufactured candidates by grade would drop
    it and report the correction as smaller than it is.
    """
    assert es.manufactured_candidates(effect) == (
        "local_only_audit.guard_is_derived", "some_module.interacts")


def test_corrected_candidates_drops_the_artifacts_and_keeps_the_rest(effect):
    """A hand-built census, so the correction is pinned without a suite run."""
    def reading(site, verdict):
        module, qualname = site.split(".", 1)
        pred = pv.Predicate(module=module, qualname=qualname, kind="function",
                            lineno=1, admitted_by=pv.ADMIT_SHAPE, returns=(),
                            path=pv.PACKAGE / f"{module}.py")
        return pv.Reading(predicate=pred, verdict=verdict, observation=None)

    census = pv.Census(
        readings=(reading("local_only_audit.guard_is_derived", pv.VERDICT_ALWAYS_TRUE),
                  reading("real.suspect", pv.VERDICT_ALWAYS_FALSE),
                  reading("some.other", pv.VERDICT_BOTH)),
        refused=(), suite=pv.DEFAULT_SUITE)

    assert len(census.candidates) == 2
    assert es.corrected_candidates(census, effect) == ("real.suspect",)


# --------------------------------------------------------------------------
# the measurement
# --------------------------------------------------------------------------

@pytest.mark.slow
def test_the_exclusion_list_manufactured_exactly_two_candidates():
    """Four runs of the fast half — the headline, by execution.

    Both sites are ones `test_guard_witness.py` calls while testing something
    else: it builds a repo whose push guard is a stale literal (so
    `guard_is_derived` returns `False`) and it shells out through
    `guard_reflexivity`.  Neither is a predicate that file is the instrument
    for, and both were ranked as one-sided candidates by D-061 and D-062.
    """
    effect = es.measure_exclusion_effect()

    assert set(es.manufactured_candidates(effect)) == {
        "local_only_audit.guard_is_derived",
        "guard_reflexivity._shells_out_to_git_diff",
    }
    # Subset, not equality: `collateral` also carries `UNOBSERVED → BOTH` moves,
    # where the excluded file was simply the predicate's only caller.  Those are
    # wrongly hidden too, and they cost nothing — no candidate came of them.
    assert set(es.manufactured_candidates(effect)) <= set(es.collateral(effect))


@pytest.mark.slow
def test_self_entries_are_the_majority_and_are_left_alone():
    """The exclusion list is not wrong, only wrongly scoped.

    Asserted so that a future widening of `EXCLUDED_TESTS` that starts hiding
    other modules' predicates shows up here rather than in a candidate list.
    """
    effect = es.measure_exclusion_effect()
    self_entries = effect.of(es.SELF_ENTRY)

    assert len(self_entries) > len(effect.of(es.COLLATERAL))
    for masked in self_entries:
        assert not masked.manufactured_candidate, (
            f"{masked.site} is a self-entry whose verdict the exclusion inverted")
