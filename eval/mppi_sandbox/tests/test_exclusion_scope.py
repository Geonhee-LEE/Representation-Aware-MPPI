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


# --------------------------------------------------------------------------
# the same audit on the input census — D-065's declared bound, bought (D-066)
# --------------------------------------------------------------------------

LOA = "eval/mppi_sandbox/tests/test_local_only_audit.py"


def _islice(calls: int, *digests: str) -> pi.InputSlice:
    return pi.InputSlice(calls=calls, digests=frozenset(digests))


def _ipred(site: str) -> pv.Predicate:
    module, qualname = site.split(".", 1)
    return pv.Predicate(module=module, qualname=qualname, kind=pv.KIND_FUNCTION,
                        lineno=1, admitted_by=pv.ADMIT_SHAPE, returns=(),
                        path=pv.PACKAGE / f"{module}.py")


def test_scoped_exclusion_keeps_a_sites_own_instrument_hidden():
    """`SELF_ENTRY` was always the correct half — the correction is not a lift."""
    assert es.scoped_exclusion("guard_witness.Attempt.satisfiable", [GW]) == (GW,)


def test_scoped_exclusion_restores_every_file_that_is_not_the_instrument():
    """The thesis, computable: per-subject where the list was written per-file."""
    assert es.scoped_exclusion("local_only_audit.guard_is_derived", [GW, PV]) == ()


def test_an_undercount_is_graded_collateral_when_its_source_is_a_mere_caller():
    """The finding's shape on the input side: `test_guard_witness.py` asks
    `local_only_audit.guard_is_derived` a question no other file asks, and it is
    not that predicate's instrument."""
    attributed = {"local_only_audit.guard_is_derived": {
        "other.py": _islice(4, "d1"), GW: _islice(2, "d2")}}
    pop = [_ipred("local_only_audit.guard_is_derived")]

    under, = es.input_undercounts(pop, attributed, excluded=(GW,))
    assert (under.excluded_distinct, under.lifted_distinct, under.hidden) == (1, 2, 1)
    assert under.attributed_to == (GW,)
    assert under.grade == es.COLLATERAL


def test_an_undercount_is_graded_self_entry_when_the_instrument_is_the_source():
    """Hiding this one is the contamination control doing its job, so it is a
    correctly-hidden question rather than a measurement error."""
    attributed = {"guard_witness.satisfiable": {
        "other.py": _islice(4, "d1"), GW: _islice(2, "d2")}}
    pop = [_ipred("guard_witness.satisfiable")]

    under, = es.input_undercounts(pop, attributed, excluded=(GW,))
    assert under.grade == es.SELF_ENTRY


def test_a_file_asking_a_question_someone_else_also_asked_is_not_attributed():
    """Attribution is "lifting this file alone raises the count", computed from
    the digest sets — a duplicated question raises nothing, so it is no source."""
    attributed = {"m.p": {"other.py": _islice(4, "d1"), GW: _islice(2, "d1")}}

    assert es.input_undercounts([_ipred("m.p")], attributed, excluded=(GW,)) == ()


def test_manufactured_singles_names_the_direction_that_costs_something():
    """`distinct == 1` is Q-074 (c)'s whole finding shape.  A site the ignore
    list pushed there would have been promoted to a witness on the strength of
    the exclusion rather than of the suite."""
    attributed = {"m.recited": {"other.py": _islice(50, "d1"), GW: _islice(2, "d2")},
                  "m.varied": {"other.py": _islice(9, "d1", "d2"), GW: _islice(2, "d3")}}
    pop = [_ipred("m.recited"), _ipred("m.varied")]

    under = es.input_undercounts(pop, attributed, excluded=(GW,))
    assert es.manufactured_singles(under) == ("m.recited",)
    assert es.collateral_undercounts(under) == ("m.recited", "m.varied")


def test_no_undercount_is_unattributable_because_a_union_has_sources():
    """The structural difference from the value side, asserted rather than
    assumed: a verdict is a fold of a sum and can need two lifts at once, but
    every element of a union came from at least one member."""
    attributed = {"m.p": {"other.py": _islice(4, "d1"), GW: _islice(2, "d2"),
                          PV: _islice(2, "d3")}}

    under = es.input_undercounts([_ipred("m.p")], attributed, excluded=(GW, PV))
    assert es.unattributed_undercounts(under) == ()
    assert under[0].attributed_to == (GW, PV)
    assert under[0].grade == es.COLLATERAL


def test_corrected_inputs_is_neither_the_shipped_reading_nor_the_lifted_one():
    """The three readings differ at the site the exclusion was written for.

    Shipped hides all files everywhere (1 — under-counted), lifted hides none
    (3 — the instrument inflates its own subject), per-subject hides only
    `test_guard_witness.py` from `guard_witness` (2).
    """
    attributed = {"guard_witness.satisfiable": {
        "other.py": _islice(4, "d1"), GW: _islice(2, "d2"), PV: _islice(2, "d3")}}
    pop = [_ipred("guard_witness.satisfiable")]

    shipped = pi.fold_inputs(attributed, (GW, PV))["guard_witness.satisfiable"]
    lifted = pi.fold_inputs(attributed, ())["guard_witness.satisfiable"]
    corrected = es.corrected_inputs(pop, attributed, excluded=(GW, PV))

    assert (shipped.distinct, lifted.distinct) == (1, 3)
    assert corrected.readings[0].observation.distinct == 2


def test_corrected_inputs_scores_a_site_with_no_surviving_caller_unobserved():
    attributed = {"guard_witness.only_self": {GW: _islice(2, "d1")}}
    corrected = es.corrected_inputs([_ipred("guard_witness.only_self")],
                                    attributed, excluded=(GW,))

    assert corrected.readings[0].verdict == pi.VERDICT_UNOBSERVED


def test_input_reconstruction_disagreement_reports_both_answers():
    """The calibration this side needs and the value side does not: the slices
    store an 8-byte digest per fingerprint, so a collision would deflate a
    reconstructed count the flat recorder got right."""
    attributed = {"m.p": {"other.py": _islice(4, "d1", "d2")}}
    agreeing = {"m.p": pi.InputObservation(site="m.p", calls=4, distinct=2)}
    disagreeing = {"m.p": pi.InputObservation(site="m.p", calls=4, distinct=3)}

    assert es.input_reconstruction_disagreements(attributed, agreeing, ()) == ()
    assert es.input_reconstruction_disagreements(attributed, disagreeing, ()) == \
        (("m.p", 2, 3),)


@pytest.fixture(scope="module")
def attributed_inputs():
    """One per-origin argument-recorder run with nothing hidden.  ~5 min.

    The run D-065 named and did not buy.  It replaces nothing: the flat
    `input_census` above stays, because it is the thing this fold has to be
    calibrated against.
    """
    pop, _ = pv._scan(pv.PACKAGE)
    return pop, pi.measure_attributed(pop, excluded=())


@pytest.mark.slow
def test_the_input_fold_reproduces_a_measured_run_under_the_same_exclusion(
        attributed_inputs, input_census):
    """The calibration, and it is not optional.

    Every count below is a *counterfactual* over one run: it assumes removing a
    file does not change what the surviving files ask, and it assumes an 8-byte
    digest does not merge two questions.  Both assumptions push counts down.
    This compares the reconstructed shipped reading against a measured one, site
    by site, and D-064's rule applies unchanged — non-empty and the fold is not
    a substitute for the runs.
    """
    _, attributed = attributed_inputs
    measured_obs = {r.predicate.site: r.observation
                    for r in input_census.readings if r.observation is not None}

    assert es.input_reconstruction_disagreements(
        attributed, measured_obs, pv.EXCLUDED_TESTS) == ()


@pytest.mark.slow
def test_the_exclusion_list_undercounts_distinct_inputs_and_names_by_how_much(
        attributed_inputs):
    """D-065's declared bound, bought — the reading itself.

    Two claims, and only the second is a finding.  The first is structural: a
    distinct count folds a union, so every under-count has at least one
    attributing file and `UNATTRIBUTED` cannot occur.  The second is the reading
    D-065 could not afford: which survivors' questions came only from an
    excluded file, and whether any of them was pushed to `SINGLE_INPUT` — the
    verdict Q-074 (c) promotes to a witness.
    """
    pop, attributed = attributed_inputs
    under = es.input_undercounts(pop, attributed)

    assert es.unattributed_undercounts(under) == (), (
        "a union's every element has a source; non-empty means the digest sets "
        "and the folded counts disagree and nothing above this can be trusted")
    for u in under:
        assert u.hidden > 0 and u.attributed_to
        assert u.grade in (es.SELF_ENTRY, es.COLLATERAL)


@pytest.mark.slow
def test_the_survivors_rankings_are_re_taken_on_per_subject_input_counts(
        measured, attributed_inputs):
    """D-065's re-take, on counts the exclusion list no longer deflates.

    D-065 re-took both orderings over the surviving population and found
    `corrected_shift` empty — but it read every survivor's distinct count under
    the whole ignore list, which is the bound it wrote into its own docstring.
    This re-takes the same reading with each site folded under its own
    `scoped_exclusion`: its instrument still hidden, every other excluded file's
    questions restored.  Whatever it returns is a statement about the ordering
    D-062 published, taken on the population D-065 corrected and the counts this
    cycle corrected.
    """
    pop, attributed_values = measured
    _, attributed = attributed_inputs
    effect = es.effect_from_one_run(pop, attributed_values)
    census = pv.Census(
        readings=pv.classify(pop, pv.fold(attributed_values, pv.EXCLUDED_TESTS)),
        refused=(), suite=pv.DEFAULT_SUITE)
    corrected = es.corrected_inputs(pop, attributed)

    alive = es.surviving(census, effect)
    moves = es.rerank(census, effect, corrected)
    assert len(moves) == len(alive)
    assert all(m.site in {r.predicate.site for r in alive} for m in moves)
