"""Tests for :mod:`eval.mppi_sandbox.simd_attribution` (Q-091).

Two jobs.  The cheap one is the verdict algebra — every verdict reachable, the
degenerate censuses named before the successful ones.  The load-bearing one is
that the **published counts** are derived from the pinned census rather than
recalled, because the recollection has now been wrong twice.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import simd_attribution as sa


# --------------------------------------------------------------------------
# The census.  These are the numbers STATE / the journal / docs quote.
# --------------------------------------------------------------------------


def test_the_pinned_census_reproduces_the_runs_own_summary_line():
    """Run 31042602721 printed ``12 failed, ..., 2 errors``.  So must the rows."""
    counts = sa.census()
    assert counts["failed"] == 12
    assert counts["errors"] == 2
    assert counts["total"] == 14


def test_six_of_the_fourteen_are_timeouts_and_the_rest_carry_numbers():
    counts = sa.census()
    assert counts["timeouts"] == 6
    assert counts["attributable"] == 8
    assert counts["timeouts"] + counts["attributable"] == counts["total"]


def test_exclusion_scope_owns_eight_of_which_six_are_the_timeouts():
    """The cell both prior summaries got wrong.

    ``STATE.md`` said "2 in ``exclusion_scope``" among the 8 non-timeout
    failures — **correct**.  The 09:00 journal "corrected" it to "6 of 14, 4
    FAILED + 2 ERROR" — wrong on both the total and the split.  Measured from
    the run's summary block the file owns 8 rows: 6 FAILED + 2 ERROR, of which
    6 are timeouts, leaving exactly 2 attributable failures.
    """
    cell = sa.file_census()["eval/mppi_sandbox/tests/test_exclusion_scope.py"]
    assert cell["total"] == 8
    assert cell["timeouts"] == 6
    assert cell["attributable"] == 2


def test_every_timeout_lives_in_exclusion_scope():
    """D-096's fix is confined to one file; this pins that it stays true."""
    files = {f.file for f in sa.CI_FAILURES if f.cause == sa.TIMEOUT}
    assert files == {"eval/mppi_sandbox/tests/test_exclusion_scope.py"}


def test_every_attributable_row_carries_a_signature_to_match_against():
    """A ``DRIFT_CONSISTENT`` verdict is a textual match, so the text must exist.

    An attributable row with an empty signature would make every masked failure
    compare equal to nothing and grade ``DRIFT_SHAPED`` — a silent downgrade
    that looks like a finding.
    """
    for failure in sa.attributable():
        assert failure.signature.strip(), f"{failure.test_id} has no CI signature"


def test_timeout_rows_carry_no_signature():
    for failure in sa.CI_FAILURES:
        if failure.cause == sa.TIMEOUT:
            assert failure.signature == ""


def test_no_duplicate_rows():
    ids = [f.test_id for f in sa.CI_FAILURES]
    assert len(ids) == len(set(ids))


# --------------------------------------------------------------------------
# Position (D-104).  The field the first transcription dropped.
# --------------------------------------------------------------------------


def test_every_attributable_row_says_where_it_failed():
    """The contract that makes the next transcription not need luck.

    The original fourteen rows were copied out of ``short test summary info``,
    which elides both operands and carries no line number.  Nothing required
    otherwise, so nothing noticed for three cycles — until ``assert_reach`` asked
    a *where*-question, guessed the position from the printed operator shape,
    pinned 3 of 14, and missed the one site whose answer was already known.  The
    number had been in the job log the whole time, two lines below the text that
    was transcribed; recovering it needed a ``gh run view --log-failed`` against
    a log that expires.

    This assertion is what makes that unrepeatable: an under-transcribed census
    is red the moment it is written, not when someone eventually needs the field.
    """
    assert sa.unlocated() == (), "transcribed without a position — refetch the traceback footers"


def test_timeout_rows_carry_no_position_and_that_is_not_a_gap():
    """A test killed by the clock has no failing statement to point at.

    So ``located`` is a claim about the eight :data:`ASSERTION` rows only, and
    the six missing positions are a property of the failure mode rather than a
    deficiency of the transcription.  Asserted so that a future row cannot
    quietly acquire an invented line number.
    """
    for failure in sa.CI_FAILURES:
        if failure.cause == sa.TIMEOUT:
            assert failure.lineno == 0
            assert failure.statement == ""
            assert not failure.located


def test_located_accounts_for_exactly_the_attributable_rows():
    counts = sa.census()
    assert counts["located"] == counts["attributable"] == 8
    assert {f.test_id for f in sa.located()} == {f.test_id for f in sa.attributable()}


def test_the_statement_is_source_text_not_the_printed_signature():
    """Two fields from two parts of the log, and conflating them loses the point.

    ``signature`` is what pytest printed with the operands substituted in
    (``assert 1.0288845528582653 > 1.2``); ``statement`` is the source line as
    written (``assert swing > 1.2, (``).  The textual dispatch match in
    :func:`attribute` needs the former; pinning an ordinal against the tree needs
    the latter.  If a transcription ever pastes the same string into both, every
    row still "has a position" and :func:`assert_reach.moved` starts declaring
    drift on a tree that never moved.
    """
    for failure in sa.located():
        assert failure.statement != failure.signature
        assert failure.statement.lstrip().startswith("assert ")


def test_a_row_missing_either_half_of_the_position_is_not_located():
    """Both fields are required — a line with no text cannot be drift-checked."""
    assert not sa.CiFailure("t.py::t", "FAILED", sa.ASSERTION, "assert 1 == 2", 0, "assert x").located
    assert not sa.CiFailure("t.py::t", "FAILED", sa.ASSERTION, "assert 1 == 2", 12, "  ").located
    assert sa.CiFailure("t.py::t", "FAILED", sa.ASSERTION, "assert 1 == 2", 12, "assert x").located


def test_the_run_provenance_lives_with_the_census():
    """A line number is an index into a tree; the two travel together (D-043)."""
    assert sa.RUN_ID == "31042602721"
    assert len(sa.RUN_COMMIT) == 40


# --------------------------------------------------------------------------
# The verdict algebra.
# --------------------------------------------------------------------------


def _failure(signature: str = "assert 1 == 2") -> sa.CiFailure:
    return sa.CiFailure("t.py::t", "FAILED", sa.ASSERTION, signature)


def _reading(native: bool, masked: bool, sig: str = "") -> sa.LocalReading:
    return sa.LocalReading("t.py::t", native, masked, sig)


def test_pass_native_fail_masked_matching_text_is_drift_consistent():
    verdict = sa.attribute(_failure("assert 0.5 > 0.6"), _reading(True, False, "assert 0.5 > 0.6"))
    assert verdict == sa.DRIFT_CONSISTENT


def test_whitespace_is_not_part_of_the_claim():
    """pytest pads its ``E`` column; a match must survive that."""
    verdict = sa.attribute(
        _failure("assert 0.5 > 0.6"), _reading(True, False, "assert   0.5  >   0.6")
    )
    assert verdict == sa.DRIFT_CONSISTENT


def test_dispatch_moving_it_to_a_different_number_is_only_drift_shaped():
    """The weak claim must not be reported as the strong one.

    "It changed when I changed dispatch" is true of nearly any float.  D-033's
    claim was reproduction *to the digit*, and only that earns the banner.
    """
    verdict = sa.attribute(_failure("assert 0.5 > 0.6"), _reading(True, False, "assert 0.7 > 0.6"))
    assert verdict == sa.DRIFT_SHAPED


def test_ci_quoting_a_different_line_of_the_same_block_still_matches():
    """pytest prints a block; CI's summary quotes one line of it.

    The masked capture keeps the whole block, so the match is containment.
    Requiring equality would have graded a bit-exact reproduction
    ``DRIFT_SHAPED`` purely because the two captures started on different lines.
    """
    block = (
        "AssertionError: the shipped loud arm no longer ends up much closer "
        "assert 0.2896076533954799 < (0.12417971687770564 / 3)"
    )
    failure = _failure("assert 0.2896076533954799 < (0.12417971687770564 / 3)")
    assert sa.attribute(failure, _reading(True, False, block)) == sa.DRIFT_CONSISTENT


def test_an_empty_ci_signature_is_refused_rather_than_matching_everything():
    """The hazard containment introduces, closed where it would be produced.

    ``"" in anything`` is ``True``, so a row with no recorded CI text would earn
    the module's strongest verdict for having no evidence at all.
    """
    with pytest.raises(ValueError, match="no CI signature"):
        sa.attribute(_failure(""), _reading(True, False, "assert 1 > 2"))


def test_failing_under_both_dispatches_is_real():
    assert sa.attribute(_failure(), _reading(False, False)) == sa.REAL


def test_passing_under_both_dispatches_is_unreproduced():
    assert sa.attribute(_failure(), _reading(True, True)) == sa.UNREPRODUCED


def test_failing_native_but_passing_masked_is_inverted():
    assert sa.attribute(_failure(), _reading(False, True)) == sa.INVERTED


def test_every_verdict_is_reachable():
    """D-079's rule: a verdict with no witness is vocabulary, not a grade."""
    witnessed = {
        sa.attribute(_failure("assert 0.5 > 0.6"), _reading(True, False, "assert 0.5 > 0.6")),
        sa.attribute(_failure("assert 0.5 > 0.6"), _reading(True, False, "assert 9 > 0.6")),
        sa.attribute(_failure(), _reading(False, False)),
        sa.attribute(_failure(), _reading(True, True)),
        sa.attribute(_failure(), _reading(False, True)),
    }
    assert witnessed == set(sa.VERDICTS)


def test_attributing_a_timeout_row_raises_rather_than_inventing_a_verdict():
    timeout_row = sa.CiFailure("t.py::t", "FAILED", sa.TIMEOUT)
    with pytest.raises(ValueError, match="no number"):
        sa.attribute(timeout_row, _reading(True, False))


def test_a_reading_for_a_different_test_is_refused():
    with pytest.raises(ValueError, match="reading is for"):
        sa.attribute(_failure(), sa.LocalReading("other.py::x", True, False))


# --------------------------------------------------------------------------
# Census grades — the degenerate ones first.
# --------------------------------------------------------------------------


#: A two-row census so the grade tests state their own population instead of
#: inheriting the real one — otherwise every mapping below is INCOMPLETE and
#: the grades under test are unreachable.
PAIR: tuple[sa.CiFailure, ...] = (
    sa.CiFailure("a", "FAILED", sa.ASSERTION, "assert a"),
    sa.CiFailure("b", "FAILED", sa.ASSERTION, "assert b"),
)


def test_an_empty_census_is_vacuous_not_explained():
    assert sa.grade({}, PAIR) == sa.VACUOUS


def test_a_census_that_reproduced_nothing_is_no_subject():
    """The D-091 shape: a scan whose subject never fired grades its plumbing.

    All-``UNREPRODUCED`` means not one CI failure was reproduced under either
    dispatch — the ids drifted, ``--slow`` was dropped, the selection was empty.
    Without this verdict that state reads as "nothing is wrong here".
    """
    assert sa.grade({"a": sa.UNREPRODUCED, "b": sa.UNREPRODUCED}, PAIR) == sa.NO_SUBJECT


def test_all_drift_requires_every_row_to_be_a_drift_verdict():
    assert sa.grade({"a": sa.DRIFT_CONSISTENT, "b": sa.DRIFT_SHAPED}, PAIR) == sa.ALL_DRIFT


def test_one_real_failure_is_enough_to_deny_the_banner_its_blanket():
    """The banner claims dispatch explains *any* closed-loop failure here."""
    assert sa.grade({"a": sa.DRIFT_CONSISTENT, "b": sa.REAL}, PAIR) == sa.MIXED


def test_no_drift_anywhere_is_all_real():
    assert sa.grade({"a": sa.REAL, "b": sa.REAL}, PAIR) == sa.ALL_REAL


def test_unreproduced_mixed_with_real_does_not_read_as_no_subject():
    """``NO_SUBJECT`` is about observing nothing, not about one quiet row."""
    assert sa.grade({"a": sa.UNREPRODUCED, "b": sa.REAL}, PAIR) == sa.ALL_REAL


def test_a_verdict_over_part_of_the_population_is_incomplete():
    """D-097's lesson, one module over: a subset verdict is not a total one.

    Reporting ``ALL_DRIFT`` from a half-read census would be the banner's own
    error — an explanation generalised past its evidence — committed by the
    instrument built to catch it.
    """
    assert sa.grade({"a": sa.DRIFT_CONSISTENT}, PAIR) == sa.INCOMPLETE
    assert sa.unmeasured({"a": sa.DRIFT_CONSISTENT}, PAIR) == ("b",)


def test_incomplete_does_not_mask_the_two_degenerate_grades():
    """A partial census that observed nothing is still VACUOUS/NO_SUBJECT.

    Ordering matters: ``INCOMPLETE`` is a statement about coverage and the other
    two are statements about content, and a reading with no content must not be
    downgraded to a merely-partial one.
    """
    assert sa.grade({}, PAIR) == sa.VACUOUS
    assert sa.grade({"a": sa.UNREPRODUCED}, PAIR) == sa.NO_SUBJECT


def test_every_grade_is_reachable():
    witnessed = {
        sa.grade({}, PAIR),
        sa.grade({"a": sa.UNREPRODUCED}, PAIR),
        sa.grade({"a": sa.DRIFT_CONSISTENT}, PAIR),
        sa.grade({"a": sa.DRIFT_CONSISTENT, "b": sa.DRIFT_SHAPED}, PAIR),
        sa.grade({"a": sa.DRIFT_CONSISTENT, "b": sa.REAL}, PAIR),
        sa.grade({"a": sa.REAL, "b": sa.REAL}, PAIR),
    }
    assert witnessed == set(sa.GRADES)


# --------------------------------------------------------------------------
# measured_magnitude — why the tolerance is not part of the match.
# --------------------------------------------------------------------------


def test_the_magnitude_is_the_long_literal_not_the_threshold():
    assert (
        sa.measured_magnitude("assert 0.036210379360192974 > (1.25 * 0.03433654744256881)")
        == "0.036210379360192974"
    )


def test_a_tolerance_rendered_differently_does_not_defeat_the_match():
    """CI printed ``± 0.0625``; this box printed ``± 6.2e-02`` for the same run.

    That difference is pytest's formatting, not the machine's arithmetic.  A
    rule that compared whole lines would grade a digit-for-digit reproduction
    ``DRIFT_SHAPED`` on it.
    """
    ci = _failure("assert 0.17901180719252627 == 0.25 ± 0.0625")
    local = _reading(True, False, "assert 0.17901180719252627 == 0.25 ± 6.2e-02")
    assert sa.attribute(ci, local) == sa.DRIFT_CONSISTENT


def test_an_assertion_with_no_float_falls_back_to_whole_signature_matching():
    assert sa.measured_magnitude("assert set() == {0.4}") == ""
    ci = _failure("assert set() == {0.4}")
    assert sa.attribute(ci, _reading(True, False, "E assert set() == {0.4}")) == (
        sa.DRIFT_CONSISTENT
    )


def test_a_genuinely_different_magnitude_is_still_only_drift_shaped():
    ci = _failure("assert 0.17901180719252627 == 0.25 ± 0.0625")
    local = _reading(True, False, "assert 0.19999999999999998 == 0.25 ± 0.0625")
    assert sa.attribute(ci, local) == sa.DRIFT_SHAPED


# --------------------------------------------------------------------------
# The measured finding (2026-08-06).
# --------------------------------------------------------------------------


def test_every_readable_closed_loop_failure_passes_native_and_fails_masked():
    """Q-091's answer, as data.

    Six of the eight attributable rows are readable on the dev box, and every
    one of them flips with dispatch alone.  This is the control D-033's banner
    assumed for four months without anyone taking it.
    """
    assert len(sa.MEASURED_2026_08_06) == 6
    for reading in sa.MEASURED_2026_08_06:
        assert reading.native_passed, reading.test_id
        assert not reading.masked_passed, reading.test_id
        assert reading.dispatch_moved_it


def test_the_measured_census_is_all_drift_and_none_real():
    verdicts = sa.verdicts()
    assert set(verdicts.values()) <= {sa.DRIFT_CONSISTENT, sa.DRIFT_SHAPED}
    assert sa.REAL not in verdicts.values()


def test_three_rows_reproduce_cis_number_to_the_digit():
    verdicts = sa.verdicts()
    consistent = [k for k, v in verdicts.items() if v == sa.DRIFT_CONSISTENT]
    assert len(consistent) == 3


def test_the_finding_is_graded_incomplete_not_all_drift():
    """The two unread rows are what stops this being a claim about all eight.

    Every row that *was* read is drift, and the temptation is to report that as
    the answer.  ``INCOMPLETE`` is the module refusing to let its own result
    generalise past its evidence — which is the exact error the banner makes.
    """
    assert sa.grade(sa.verdicts()) == sa.INCOMPLETE


def test_the_two_unread_rows_are_the_exclusion_scope_pair():
    unread = sa.unmeasured(sa.verdicts())
    assert len(unread) == 2
    assert all("test_exclusion_scope.py" in t for t in unread)


# --------------------------------------------------------------------------
# The mask itself.
# --------------------------------------------------------------------------


def test_the_mask_actually_removes_avx512_from_numpys_dispatch():
    """The premise the whole module rests on, checked rather than assumed.

    If the dev box has no AVX-512 to begin with, the masked and native legs are
    the same machine and every verdict is meaningless — so skip rather than
    report.  This is the positive control D-075/D-081/D-088 were each missing.
    """
    import os
    import subprocess
    import sys

    probe = (
        "import numpy;"
        "print(','.join(numpy.__config__.show(mode='dicts')"
        "['SIMD Extensions']['found']))"
    )
    native = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True
    ).stdout
    if "AVX512" not in native:
        pytest.skip("dev box has no AVX-512; the two legs would be the same machine")

    env = dict(os.environ, NPY_DISABLE_CPU_FEATURES=" ".join(sa.AVX512_MASK))
    masked = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, env=env
    ).stdout
    # Absence of "AVX512" is also what a *crashed* probe prints, so require
    # positive evidence that numpy ran and reported a feature list before
    # reading the absence as the mask working.  Same shape as the empty-signature
    # refusal in attribute(): nothing must never be the strongest reading.
    assert "AVX2" in masked, f"masked probe produced no feature list: {masked!r}"
    assert "AVX512" not in masked, f"mask did not take effect: {masked}"
