"""The exclusion list's own audit — that a candidate is not an ignore-list artifact.

The cheap tests pin the partition's semantics against hand-built readings, so
every rule is exercised both ways without paying for a suite run.  The one
`@pytest.mark.slow` test is the measurement itself: four runs of the fast half,
asserting the two sites the exclusion actually manufactured.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import exclusion_scope as es
from eval.mppi_sandbox import predicate_inputs as pi
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
# the price, and the one-run reconstruction (D-064)
# --------------------------------------------------------------------------

def test_price_counts_both_endpoint_runs_not_just_one():
    """`2 + len(excluded)`, derived — the docstring said `1 + …` and was wrong.

    `measure_exclusion_effect` takes a base reading *and* a fully-lifted one
    before the per-file loop starts.  Reading the loop is what settles it; the
    prose that stood here for a cycle had counted the endpoints as one.
    """
    assert es.price(()) == 2
    assert es.price((GW, PV)) == 4
    assert es.price() == 2 + len(pv.EXCLUDED_TESTS)


def _obs(site, true_calls=0, false_calls=0, other=()):
    return pv.Observation(site=site, true_calls=true_calls,
                          false_calls=false_calls, other_types=tuple(other))


@pytest.fixture
def record():
    """A per-origin record with the finding's exact shape.

    `suspect` is called `True` by everyone and `False` only by `test_guard_witness`
    — so hiding that file turns a two-sided predicate into a candidate, which is
    the move `manufactured_candidate` exists to name.  `owned` is only ever
    called by its own instrument.
    """
    return {
        "local_only_audit.suspect": {GW: _obs("local_only_audit.suspect", 0, 3),
                                     "other.py": _obs("local_only_audit.suspect", 7, 0)},
        "predicate_vacuity.owned": {PV: _obs("predicate_vacuity.owned", 2, 2)},
        "some_module.everywhere": {es.UNATTRIBUTABLE: _obs("some_module.everywhere", 1, 1)},
    }


@pytest.fixture
def population(record):
    def pred(site):
        module, qualname = site.split(".", 1)
        return pv.Predicate(module=module, qualname=qualname, kind="function",
                            lineno=1, admitted_by=pv.ADMIT_SHAPE, returns=(),
                            path=pv.PACKAGE / f"{module}.py")
    return [pred(s) for s in record]


def test_fold_drops_the_hidden_origins_and_sums_the_rest(record):
    assert pv.fold(record)["local_only_audit.suspect"].calls == 10
    hidden = pv.fold(record, [GW])["local_only_audit.suspect"]
    assert (hidden.true_calls, hidden.false_calls) == (7, 0)


def test_a_site_whose_every_caller_is_hidden_leaves_the_record(record):
    """Absent, not zero-count — so `classify` scores it `UNOBSERVED` as usual."""
    assert "predicate_vacuity.owned" not in pv.fold(record, [PV])


def test_reconstruct_reproduces_the_manufactured_candidate(record, population):
    """The finding's mechanism, on a record small enough to read by eye."""
    assert es.reconstruct(population, record, ())[
        "local_only_audit.suspect"] == pv.VERDICT_BOTH
    assert es.reconstruct(population, record, [GW])[
        "local_only_audit.suspect"] == pv.VERDICT_ALWAYS_TRUE


def test_effect_from_one_run_grades_the_same_way_as_six(record, population):
    """Same `Effect`, same grades — only the six measurements became six folds."""
    effect = es.effect_from_one_run(population, record, excluded=(GW, PV))

    assert es.manufactured_candidates(effect) == ("local_only_audit.suspect",)
    assert es.collateral(effect) == ("local_only_audit.suspect",)
    assert [m.site for m in effect.of(es.SELF_ENTRY)] == ["predicate_vacuity.owned"]


def test_unattributable_calls_survive_every_exclusion_and_are_reported(record, population):
    """A call no test file owns cannot be hidden, so it must not look hideable."""
    assert es.unattributable_calls(record) == (("some_module.everywhere", 2),)
    assert es.reconstruct(population, record, [GW, PV])[
        "some_module.everywhere"] == pv.VERDICT_BOTH


def test_origins_orders_by_call_count(record):
    assert es.origins(record, "local_only_audit.suspect") == (("other.py", 7), (GW, 3))
    assert es.origins(record, "never.called") == ()


def test_reconstruction_disagreements_names_both_readings(record, population):
    """The calibration's output has to say which side said what, or it is a bit."""
    assert es.reconstruction_disagreements(
        population, record, es.reconstruct(population, record, [GW]), [GW]) == ()
    assert es.reconstruction_disagreements(
        population, record, {"local_only_audit.suspect": pv.VERDICT_BOTH}, [GW])[0] == (
            "local_only_audit.suspect", pv.VERDICT_ALWAYS_TRUE, pv.VERDICT_BOTH)


# --------------------------------------------------------------------------
# the measurement — two runs, not six (D-064)
# --------------------------------------------------------------------------
#
# What stood here was two `@pytest.mark.slow` tests each calling
# `measure_exclusion_effect()`: 6 instrumented suite runs apiece at 4 min 57 s a
# run, so ~60 min for the pair.  That is why the attribution half of D-063 was
# asserted but never green.  Both now read one per-origin record — measured
# once, session-scoped — and a third test pays one more run to check that the
# reconstruction and a real run agree.

@pytest.fixture(scope="module")
def measured():
    """One attributed run with nothing hidden.  ~5 min, shared by the module."""
    pop, _ = pv._scan(pv.PACKAGE)
    return pop, pv.measure_attributed(pop, excluded=())


@pytest.mark.slow
def test_the_exclusion_list_manufactured_exactly_two_candidates(measured):
    """The headline, by execution — now from one run rather than six.

    Both sites are ones `test_guard_witness.py` calls while testing something
    else: it builds a repo whose push guard is a stale literal (so
    `guard_is_derived` returns `False`) and it shells out through
    `guard_reflexivity`.  Neither is a predicate that file is the instrument
    for, and both were ranked as one-sided candidates by D-061 and D-062.
    """
    pop, attributed = measured
    effect = es.effect_from_one_run(pop, attributed)

    assert set(es.manufactured_candidates(effect)) == {
        "local_only_audit.guard_is_derived",
        "guard_reflexivity._shells_out_to_git_diff",
    }
    # Subset, not equality: `collateral` also carries `UNOBSERVED → BOTH` moves,
    # where the excluded file was simply the predicate's only caller.  Those are
    # wrongly hidden too, and they cost nothing — no candidate came of them.
    assert set(es.manufactured_candidates(effect)) <= set(es.collateral(effect))


#: Which file's calls actually hid each headline site.  **Measured** (D-064),
#: and D-063 got one of the two wrong: it wrote both down as
#: `test_guard_witness.py` from a call-graph reading, having budgeted six suite
#: runs it could not afford.  The second entry is what the record says instead.
ATTRIBUTION = {
    "local_only_audit.guard_is_derived": (GW,),
    "guard_reflexivity._shells_out_to_git_diff": (PV,),
}


@pytest.mark.slow
def test_the_headline_sites_are_attributed_to_a_measured_file(measured):
    """The attribution half D-063 asserted but never ran.

    The grade survives — both are `COLLATERAL`, hidden by a file that is not
    their instrument.  The *attribution* does not: `_shells_out_to_git_diff` is
    hidden by `test_predicate_vacuity.py`, not by `test_guard_witness.py`.
    """
    pop, attributed = measured
    effect = es.effect_from_one_run(pop, attributed)
    by_site = {m.site: m for m in effect.masked}

    for site, expected in ATTRIBUTION.items():
        masked = by_site[site]
        assert masked.grade == es.COLLATERAL
        assert masked.attributed_to == expected, es.origins(attributed, site)


@pytest.mark.slow
def test_the_hidden_evidence_is_one_call_out_of_thousands(measured):
    """Why a call count could never have found this, and a call *graph* misread it.

    `test_guard_witness.py` calls `_shells_out_to_git_diff` 188 times and every
    one returns `False` — it is a heavy caller carrying no information, which is
    exactly what made it a plausible culprit to read off the call graph.  The
    verdict actually turns on a **single** `True`, and it comes from
    `test_predicate_vacuity.py`: D-062's own witness, written to show this
    predicate satisfiable, sitting in a file the census excludes.

    So the census hid the one piece of evidence that its top candidate was not
    vacuous, and it hid it under an exclusion whose stated purpose is to stop
    the instrument scoring its own subject.
    """
    pop, attributed = measured
    per_origin = attributed["guard_reflexivity._shells_out_to_git_diff"]

    assert per_origin[GW].true_calls == 0
    assert per_origin[GW].false_calls > 100
    assert sum(o.true_calls for o in per_origin.values()) == 1
    assert per_origin[PV].true_calls == 1


@pytest.mark.slow
def test_self_entries_are_the_majority_and_are_left_alone(measured):
    """The exclusion list is not wrong, only wrongly scoped.

    Asserted so that a future widening of `EXCLUDED_TESTS` that starts hiding
    other modules' predicates shows up here rather than in a candidate list.
    """
    pop, attributed = measured
    effect = es.effect_from_one_run(pop, attributed)
    self_entries = effect.of(es.SELF_ENTRY)

    assert len(self_entries) > len(effect.of(es.COLLATERAL))
    for masked in self_entries:
        assert not masked.manufactured_candidate, (
            f"{masked.site} is a self-entry whose verdict the exclusion inverted")


@pytest.mark.slow
def test_the_reconstruction_agrees_with_a_measured_run(measured):
    """The calibration — one extra run, and the reason the cheap reading is usable.

    `effect_from_one_run` assumes that hiding a test file changes nothing about
    what the surviving files observe.  Here that assumption is checked against
    the one exclusion set anybody cares about: the reconstructed verdicts under
    `EXCLUDED_TESTS` against a run that actually passed `--ignore`.

    A pass is joint evidence for two things — that the per-origin recorder
    tallies the same values as the flat one, and that the counterfactual holds —
    and cannot separate them.  It is `n = 1` exclusion set over
    `len(population)` predicates, which is what it claims and no more.
    """
    pop, attributed = measured
    obs = pv.measure(pop, excluded=pv.EXCLUDED_TESTS)
    real = {r.predicate.site: r.verdict for r in pv.classify(pop, obs)}

    assert es.reconstruction_disagreements(pop, attributed, real) == ()


# --------------------------------------------------------------------------
# re-taking the published rankings over the surviving population (D-065)
# --------------------------------------------------------------------------
#
# D-061 ordered the candidates by call count and D-062 re-ordered them by
# distinct inputs; D-063/D-064 then established that two members of the set both
# rankings were taken over were manufactured by `EXCLUDED_TESTS`.  Rank is
# positional, so neither published ordering is a claim about the set that
# survives — these tests pin the re-taking, including the case where the
# published disagreement turns out to have been the artifact's doing.


def _ranked(rows):
    """`(census, effect, inputs)` from `(site, true, false, distinct, hidden_by)`.

    `hidden_by` names an origin to attribute the site's `False` calls to, which
    is how a row is made into an exclusion artifact; `None` attributes every
    call to a file no exclusion names.
    """
    record, obs = {}, {}
    for site, true_calls, false_calls, distinct, hidden_by in rows:
        per = {"other.py": _obs(site, true_calls, 0)}
        if false_calls:
            per[hidden_by or "other.py"] = _obs(site, 0, false_calls)
        record[site] = per
        obs[site] = pi.InputObservation(site=site, calls=true_calls + false_calls,
                                        distinct=distinct)

    def pred(site):
        module, qualname = site.split(".", 1)
        return pv.Predicate(module=module, qualname=qualname,
                            kind=pv.KIND_FUNCTION, lineno=1,
                            admitted_by=pv.ADMIT_SHAPE, returns=(),
                            path=pv.PACKAGE / f"{module}.py")

    population = [pred(s) for s in record]
    effect = es.effect_from_one_run(population, record, excluded=(GW,))
    census = pv.Census(readings=pv.classify(population, pv.fold(record, [GW])),
                       refused=(), suite=pv.DEFAULT_SUITE)
    inputs = pi.InputCensus(readings=pi.classify(population, obs), refused=(),
                            suite=pv.DEFAULT_SUITE)
    return census, effect, inputs


#: `suspect` is two-sided until `test_guard_witness.py` is hidden, so it is an
#: artifact; `loud` and `quiet` are one-sided whatever the exclusion does.
CONTAMINATED = [("local_only_audit.suspect", 7, 3, 1, GW),
                ("alpha.loud", 5, 0, 1, None),
                ("beta.quiet", 3, 0, 3, None)]


def test_the_artifact_is_in_the_published_set_and_out_of_the_surviving_one():
    census, effect, _ = _ranked(CONTAMINATED)

    assert [r.predicate.site for r in census.candidates] == [
        "local_only_audit.suspect", "alpha.loud", "beta.quiet"]
    assert es.manufactured_candidates(effect) == ("local_only_audit.suspect",)
    assert [r.predicate.site for r in es.surviving(census, effect)] == [
        "alpha.loud", "beta.quiet"]


def test_surviving_returns_readings_not_sites_so_the_rankings_can_be_re_taken():
    """The reason this is not just `corrected_candidates` — both orderings need
    the observation, and a site string does not carry one."""
    census, effect, _ = _ranked(CONTAMINATED)
    alive = es.surviving(census, effect)

    assert tuple(r.predicate.site for r in alive) == \
        es.corrected_candidates(census, effect)
    assert all(isinstance(r, pv.Reading) and r.observation for r in alive)


def test_removing_an_artifact_renumbers_every_rank_below_it():
    """The claim: a published rank is not transportable to a subset.

    The survivors' *relative* order is untouched — both keys are per-site — and
    that is exactly why the finding has to be stated in ranks.  `loud` was the
    second-loudest candidate and is now the loudest; the sentence "the leading
    candidate is X" changes truth value without any measurement changing.
    """
    census, effect, inputs = _ranked(CONTAMINATED)
    moves = {r.site: r for r in es.rerank(census, effect, inputs)}

    assert moves["alpha.loud"].published == (1, 2)
    assert moves["alpha.loud"].corrected == (0, 1)
    assert moves["beta.quiet"].published == (2, 0)
    assert moves["beta.quiet"].corrected == (1, 0)
    assert moves["alpha.loud"].moved and moves["beta.quiet"].moved


def test_a_candidate_set_with_no_artifacts_reranks_to_itself():
    """The negative result has to be expressible, or the instrument only confirms."""
    census, effect, inputs = _ranked([("alpha.loud", 5, 0, 1, None),
                                      ("beta.quiet", 3, 0, 3, None)])

    assert es.manufactured_candidates(effect) == ()
    assert not any(r.moved for r in es.rerank(census, effect, inputs))
    assert es.voided_leaders(census, effect, inputs) == ()


def test_voided_leaders_names_an_artifact_that_headlined_an_ordering():
    """An artifact anywhere costs a renumbering; one at rank 0 costs the sentence."""
    census, effect, inputs = _ranked(CONTAMINATED)

    assert [r.predicate.site for r in pv.by_evidence(census.candidates)][0] == \
        "local_only_audit.suspect"
    assert es.voided_leaders(census, effect, inputs) == ("local_only_audit.suspect",)


def test_the_published_disagreement_can_be_entirely_the_artifacts_doing():
    """D-062's falsifiable half, re-taken — and here it does not survive.

    `loud` and `quiet` agree on both orderings, so the only reason the published
    `ordering_shift` was non-empty is a site that should not have been in the
    set.  This is the shape that would void the finding rather than renumber it,
    which is why `corrected_shift` exists as a separate reading.
    """
    census, effect, inputs = _ranked([("local_only_audit.suspect", 7, 3, 2, GW),
                                      ("alpha.loud", 5, 0, 3, None),
                                      ("beta.quiet", 3, 0, 1, None)])

    assert pi.ordering_shift(census, inputs) != ()
    assert es.corrected_shift(census, effect, inputs) == ()


def test_the_published_disagreement_can_also_survive_the_correction():
    """The other answer, so a pass of the test above is evidence and not a wiring bug."""
    census, effect, inputs = _ranked(CONTAMINATED)

    assert es.corrected_shift(census, effect, inputs) == \
        (("alpha.loud", 0, 1), ("beta.quiet", 1, 0))


@pytest.fixture(scope="module")
def input_census():
    """One argument-recorder run under `EXCLUDED_TESTS`.  ~5 min.

    A second run rather than a fold of the first: D-064's per-origin trick
    reconstructs *verdicts*, and a distinct-input count is not reconstructible
    from a value tally.  Taken under the exclusion on purpose — it has to
    reproduce the census D-062 published its ordering over.
    """
    return pi.census()


@pytest.mark.slow
def test_both_published_rankings_were_taken_over_a_population_with_artifacts(
        measured, input_census):
    """D-061's and D-062's orderings, re-taken over the set that survived.

    The correction removes members from the *population*; it re-reads nothing.
    Every surviving site keeps the call count and the distinct-input count it
    was measured with — so whatever this reports is a statement about ranks,
    which is what both decisions led with.

    **Bound**: the surviving sites' input counts are still read under
    `EXCLUDED_TESTS`, so a survivor whose questions were themselves asked only
    by an excluded file is still under-counted here.  Fixing that is a third
    run with the list lifted, and it is not this test.
    """
    pop, attributed = measured
    effect = es.effect_from_one_run(pop, attributed)
    census = pv.Census(
        readings=pv.classify(pop, pv.fold(attributed, pv.EXCLUDED_TESTS)),
        refused=(), suite=pv.DEFAULT_SUITE)

    alive = es.surviving(census, effect)
    assert len(alive) == len(census.candidates) - 2, (
        "the two manufactured candidates should be exactly what drops out")

    moves = es.rerank(census, effect, input_census)
    assert len(moves) == len(alive)
    assert any(m.moved for m in moves), (
        "removing two members of a ranked set must renumber something")
