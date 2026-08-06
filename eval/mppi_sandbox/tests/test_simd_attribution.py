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
