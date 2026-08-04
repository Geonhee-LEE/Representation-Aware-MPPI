"""Q-074 (c): distinct inputs, not call counts, size a one-sided predicate.

Cheap tests pin the partition, the join with D-061's census, and the plugin's
assembly.  Anything that runs a real suite under the recorder is ``slow``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import predicate_inputs as pi
from eval.mppi_sandbox import predicate_vacuity as pv


def _pred(site: str) -> pv.Predicate:
    module, _, qualname = site.partition(".")
    return pv.Predicate(module=module, qualname=qualname,
                        kind=pv.KIND_FUNCTION, lineno=1,
                        admitted_by=pv.ADMIT_SHAPE, returns=("x > 0",),
                        path=Path("/nowhere.py"))


def _obs(site: str, calls: int, distinct: int, addr: bool = False,
         sample=()) -> pi.InputObservation:
    return pi.InputObservation(site=site, calls=calls, distinct=distinct,
                               address_reprs=addr, sample=tuple(sample))


# --------------------------------------------------------------------------
# The partition — pure, no suite run
# --------------------------------------------------------------------------


@pytest.mark.parametrize("calls, distinct, expected", [
    (5694, 1, pi.VERDICT_SINGLE_INPUT),
    (1, 1, pi.VERDICT_SINGLE_INPUT),
    (4, 4, pi.VERDICT_MANY_INPUTS),
    (0, 0, pi.VERDICT_UNOBSERVED),
])
def test_classify_splits_on_distinct_inputs_not_calls(calls, distinct, expected):
    obs = {"m.p": _obs("m.p", calls, distinct)} if calls else {}
    reading, = pi.classify([_pred("m.p")], obs)
    assert reading.verdict == expected


def test_the_split_is_degenerate_rather_than_chosen():
    """``distinct == 1`` is the boundary of the concept, not a threshold.

    D-020 shipped ``wilson_lower_at_least`` without justifying its constant and
    STATE has carried that debt ever since; D-061 declined to pick a floor on
    call counts for the same reason.  This pins that the same restraint holds
    here — two distinct inputs is already ``MANY_INPUTS``, so no number was
    picked, and grading above 1 stays open exactly as the call count did.
    """
    two, = pi.classify([_pred("m.p")], {"m.p": _obs("m.p", 2, 2)})
    assert two.verdict == pi.VERDICT_MANY_INPUTS


def test_an_uncalled_predicate_is_unobserved_not_single_input():
    """D-050's rule survives the change of statistic.

    A predicate nobody called has zero distinct inputs, and zero is not one.
    Merging them would report every dead helper in the package as recited.
    """
    reading, = pi.classify([_pred("m.never")], {})
    assert reading.verdict == pi.VERDICT_UNOBSERVED
    assert not reading.is_single


def test_an_address_repr_cannot_manufacture_a_single_input_reading():
    """Which way the fingerprint is wrong, pinned as a property of the verdicts.

    Identity-based reprs split equal values apart, so they can only push a site
    *out* of ``SINGLE_INPUT``.  A ``SINGLE_INPUT`` reading is therefore
    informative even when addresses were seen; a ``MANY_INPUTS`` one is not,
    because the count may be counting instances rather than questions.
    """
    single, = pi.classify([_pred("m.p")], {"m.p": _obs("m.p", 9, 1, addr=True)})
    many, = pi.classify([_pred("m.q")], {"m.q": _obs("m.q", 9, 9, addr=True)})
    clean, = pi.classify([_pred("m.r")], {"m.r": _obs("m.r", 9, 9)})

    assert single.is_single and single.informative
    assert many.verdict == pi.VERDICT_MANY_INPUTS and not many.informative
    assert clean.informative


# --------------------------------------------------------------------------
# The join — the claim this module makes about D-061's ordering
# --------------------------------------------------------------------------


def _joined(rows):
    """``(vacuity_census, input_census)`` over ``(site, verdict, T, F, calls, distinct)``."""
    preds = [_pred(site) for site, *_ in rows]
    vac = pv.Census(
        readings=pv.classify(preds, {
            site: pv.Observation(site=site, true_calls=t, false_calls=f)
            for site, _v, t, f, _c, _d in rows}),
        refused=(), suite=pv.DEFAULT_SUITE)
    inp = pi.InputCensus(
        readings=pi.classify(preds, {
            site: _obs(site, c, d) for site, _v, _t, _f, c, d in rows}),
        refused=(), suite=pv.DEFAULT_SUITE)
    return vac, inp


def test_recited_is_the_conjunction_one_sided_and_one_question():
    """Neither half alone is the finding.

    ``both_answers`` varies its answer, so its single input is uninteresting;
    ``well_probed`` is one-sided but was offered 40 distinct inputs, which is
    the case where the call count *was* evidence.  Only ``recited`` is both.
    """
    vac, inp = _joined([
        ("m.recited",     pv.VERDICT_ALWAYS_FALSE, 0, 5694, 5694, 1),
        ("m.well_probed", pv.VERDICT_ALWAYS_FALSE, 0, 40, 40, 40),
        ("m.both_answers", pv.VERDICT_BOTH, 3, 3, 6, 1),
    ])
    hits = pi.recited(vac, inp)
    assert [h.site for h in hits] == ["m.recited"]
    assert (hits[0].calls, hits[0].distinct) == (5694, 1)


def test_the_ordering_shift_is_the_falsifiable_form_of_the_claim():
    """D-061 led with the 5694-call site; by distinct inputs it ranks last.

    If the two orderings agreed, this instrument would have bought a bound and
    nothing else — so the disagreement is reported as a rank pair rather than
    asserted in prose.
    """
    vac, inp = _joined([
        ("m.loud",  pv.VERDICT_ALWAYS_FALSE, 0, 5694, 5694, 1),
        ("m.quiet", pv.VERDICT_ALWAYS_TRUE, 40, 0, 40, 40),
    ])
    assert [r.predicate.site for r in pv.by_evidence(vac.candidates)] == \
        ["m.loud", "m.quiet"]
    assert [r.predicate.site for r in pi.by_input_diversity(vac.candidates, inp)] == \
        ["m.quiet", "m.loud"]
    assert pi.ordering_shift(vac, inp) == (("m.loud", 0, 1), ("m.quiet", 1, 0))


def test_agreeing_orderings_report_no_shift():
    """The negative result has to be expressible, or the instrument only ever confirms."""
    vac, inp = _joined([
        ("m.a", pv.VERDICT_ALWAYS_FALSE, 0, 90, 90, 30),
        ("m.b", pv.VERDICT_ALWAYS_FALSE, 0, 10, 10, 5),
    ])
    assert pi.ordering_shift(vac, inp) == ()


def test_a_site_missing_from_the_input_census_is_not_reported_as_recited():
    """The join must not turn an absent measurement into a positive finding."""
    vac, _ = _joined([("m.p", pv.VERDICT_ALWAYS_FALSE, 0, 12, 12, 1)])
    empty = pi.InputCensus(readings=(), refused=(), suite=pv.DEFAULT_SUITE)
    assert pi.recited(vac, empty) == ()


# --------------------------------------------------------------------------
# The generated plugin — assembled, not restated
# --------------------------------------------------------------------------


def test_the_plugin_reuses_d061_install_machinery_verbatim():
    """One statement of how a site gets reached, shared by both censuses.

    If the install half were copied instead, the two censuses could drift into
    describing different populations while both reporting the same suite.
    """
    src = pi.plugin_source()
    assert pv._PLUGIN_PRELUDE in src
    assert pv._PLUGIN_INSTALL in src
    assert pv._PLUGIN_RECORD_VALUES not in src


def test_the_plugin_registers_exactly_one_dump():
    """``atexit`` is LIFO — a second registration would clobber the first's file."""
    src = pi.plugin_source()
    assert src.count("atexit.register(_dump)") == 1
    assert src.count("def _dump()") == 1
    assert pv._PLUGIN.count("atexit.register(_dump)") == 1


def test_the_plugin_compiles_and_carries_its_parameters():
    src = pi.plugin_source(sample=7, repr_limit=42)
    compile(src, "<plugin>", "exec")
    assert "_SAMPLE = 7" in src and "_REPR_LIMIT = 42" in src
    assert "__SAMPLE__" not in src and "__REPR_LIMIT__" not in src


def test_splitting_the_plugin_left_d061_byte_identical():
    """The seam is internal — D-061's reading must not depend on this refactor."""
    assert pv._PLUGIN == (pv._PLUGIN_PRELUDE + pv._PLUGIN_RECORD_VALUES
                          + pv._PLUGIN_INSTALL + pv._PLUGIN_DUMP)


def test_this_modules_own_tests_are_excluded_from_the_census():
    """D-060's lesson, paid upfront for the second time.

    These tests call this module's predicates with inputs chosen to be diverse,
    and diversity is what it measures.  A census watching them would score its
    own predicates ``MANY_INPUTS`` for free.
    """
    assert "eval/mppi_sandbox/tests/test_predicate_inputs.py" in pv.EXCLUDED_TESTS


# --------------------------------------------------------------------------
# Calibration — constructed, because the historical registry is still 0
# --------------------------------------------------------------------------


def test_the_calibration_set_contains_the_shape_the_history_could_not_supply():
    """D-057's shape: many calls, one argument.

    D-061's calibration set was 0 because the one historical instance lives in
    a test.  The constructed set does not have that problem — ``recited_bar``
    is that shape by construction.
    """
    assert pi.CALIBRATION_EXPECTED["subject.recited_bar"] == \
        (pi.VERDICT_SINGLE_INPUT, 1)


def test_miscalibrated_fails_on_an_absent_member_not_just_a_wrong_one():
    """An empty mirror asserts nothing and reads as a clean bill (D-046)."""
    empty = pi.InputCensus(readings=(), refused=(), suite=("tests/",))
    assert len(pi.miscalibrated(empty)) == len(pi.CALIBRATION_EXPECTED)


def test_miscalibrated_checks_the_distinct_count_not_only_the_verdict():
    """A recorder that fingerprinted nothing would pass a verdict-only mirror.

    Every call would collapse to one fingerprint, every called site would read
    ``SINGLE_INPUT``, and three of the four expected verdicts would still be
    right.  Pinning the count is what makes the mirror able to see that.
    """
    preds = [_pred(site) for site in pi.CALIBRATION_EXPECTED]
    collapsed = pi.InputCensus(
        readings=pi.classify(preds, {
            "subject.recited_bar": _obs("subject.recited_bar", 50, 1),
            "subject.varied_bar": _obs("subject.varied_bar", 4, 1),
            "subject.no_arguments": _obs("subject.no_arguments", 50, 1),
        }),
        refused=(), suite=("tests/",))
    problems = pi.miscalibrated(collapsed)
    assert any("varied_bar" in p for p in problems)


@pytest.mark.slow
def test_calibration_census_returns_all_four_verdicts(tmp_path):
    """The witness, run through the shipped subprocess path (D-060's move)."""
    cens = pi.calibration_census(tmp_path)
    assert pi.miscalibrated(cens) == ()


# --------------------------------------------------------------------------
# the per-origin recorder (D-066) — the run that buys D-065's declared bound
# --------------------------------------------------------------------------

def _slice(calls: int, *digests: str, addr: bool = False,
           sample: tuple[str, ...] = ()) -> pi.InputSlice:
    return pi.InputSlice(calls=calls, digests=frozenset(digests),
                         address_reprs=addr, sample=sample)


def test_the_flat_recorder_reassembles_byte_identical_from_its_three_halves():
    """The seam is a split, not a rewrite — same claim D-064 made on the value side.

    If this fails, the per-origin recorder was bought by changing what the
    shipped census measures, and every count D-061 through D-065 published
    would be describing a different instrument than the one that took them.
    """
    assert pi._PLUGIN_RECORD_INPUTS == (pi._PLUGIN_FINGERPRINT_INPUTS
                                        + pi._PLUGIN_TALLY_INPUTS
                                        + pi._PLUGIN_WRAP_INPUTS)


def test_both_recorders_share_the_fingerprint_and_the_wrap():
    """The two censuses must agree on what *one question* is, or the fold is not
    comparable to the run it reconstructs."""
    attributed = pi.plugin_source_attributed()
    flat = pi.plugin_source()
    for half in (pi._PLUGIN_FINGERPRINT_INPUTS, pi._PLUGIN_WRAP_INPUTS):
        rendered = (half.replace("__SAMPLE__", str(pi._SAMPLE))
                    .replace("__REPR_LIMIT__", str(pi.REPR_LIMIT)))
        assert rendered in flat and rendered in attributed


def test_both_recorders_are_valid_python():
    for src in (pi.plugin_source(), pi.plugin_source_attributed()):
        compile(src, "<plugin>", "exec")


def test_fold_unions_distinct_inputs_rather_than_adding_them():
    """The whole reason a slice carries a set: two files asking the same
    question asked one question between them, and no pair of counts says so."""
    attributed = {"m.p": {"a.py": _slice(3, "d1"), "b.py": _slice(4, "d1")}}

    folded = pi.fold_inputs(attributed)["m.p"]
    assert (folded.calls, folded.distinct) == (7, 1)


def test_fold_counts_a_question_only_one_file_asked():
    attributed = {"m.p": {"a.py": _slice(3, "d1"), "b.py": _slice(4, "d1", "d2")}}

    assert pi.fold_inputs(attributed)["m.p"].distinct == 2
    assert pi.fold_inputs(attributed, ["b.py"])["m.p"].distinct == 1


def test_fold_omits_a_site_every_surviving_file_is_silent_about():
    """`classify` scores an absent site `UNOBSERVED`, so dropping it here is how
    a predicate whose sole caller was hidden reads as unobserved rather than as
    single-input — the difference between no evidence and thin evidence."""
    attributed = {"m.p": {"a.py": _slice(3, "d1")}}

    assert pi.fold_inputs(attributed, ["a.py"]) == {}
    readings = pi.classify([_pred("m.p")], pi.fold_inputs(attributed, ["a.py"]))
    assert readings[0].verdict == pi.VERDICT_UNOBSERVED


def test_fold_ors_the_address_flag_and_keeps_a_bounded_sample():
    attributed = {"m.p": {"a.py": _slice(1, "d1", sample=("(1,)",)),
                          "b.py": _slice(1, "d2", addr=True,
                                         sample=("(<X at 0x1>,)",))}}

    folded = pi.fold_inputs(attributed)["m.p"]
    assert folded.address_reprs
    assert len(folded.sample) <= pi._SAMPLE
    assert pi.fold_inputs(attributed, ["b.py"])["m.p"].address_reprs is False
