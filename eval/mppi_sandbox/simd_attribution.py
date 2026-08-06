"""Is the ``slow`` job red because the code is wrong, or because the runner is
a different machine? (Q-091, STATE #1)

Every ``slow`` job log opens with a banner that already answers this, before any
measurement is taken::

    AVX512_SKX ABSENT; ... a closed-loop failure here is most likely dispatch
    drift, not a regression (D-033)

D-033 earned that sentence: five closed-loop verdicts were chased as a code
regression, the numpy pin was applied and honoured, the same five failed anyway,
and the actual variable turned out to be SIMD dispatch — *masking AVX-512 off on
the dev box reproduced the runner's number to all 17 digits.*

But the banner is printed **before** the run, and it fits every outcome.  An
explanation available in advance for any failure discriminates nothing, and
accepting it wholesale means the ``slow`` job can never be red for a real
reason.  D-033 was a finding about **five named tests**; the banner generalises
it to *any* closed-loop failure, and nobody has re-taken the reading since.

So this module takes the control D-033 assumed and never mechanised: run each
failure on the dev box **twice** — once native, once with AVX-512 masked — and
let the pair say which explanation the failure is entitled to.

The discriminator
-----------------

The masked dev box is the runner's dispatch (verified: masking leaves
``AVX2`` as the top extension, which is exactly what the runner reports).  So
for a failure CI observed:

======================  =============  =============================================
native / masked         verdict        reading
======================  =============  =============================================
pass / fail             DRIFT_*        AVX-512 is the variable.  ``DRIFT_CONSISTENT``
                                       if the masked failure reproduces CI's
                                       assertion text exactly, ``DRIFT_SHAPED`` if
                                       dispatch moves it but not to CI's number.
fail / fail             REAL           dispatch is not the variable; the assertion
                                       misses on both machines.  The banner does
                                       not cover this one.
pass / pass             UNREPRODUCED   neither dispatch reproduces CI.  Something
                                       else differs — data, ordering, environment.
fail / pass             INVERTED       the mask is not what CI is.  Refutes the
                                       premise rather than the finding.
======================  =============  =============================================

``DRIFT_CONSISTENT`` is deliberately the only verdict that requires a *textual*
match.  "The number moved when I changed dispatch" is weak — almost any float
does.  "The number moved to the one CI printed, to the last digit" is the claim
D-033 actually made, and it is the one worth inheriting.

Why the ERROR/timeout rows are excluded from attribution
--------------------------------------------------------

Six of the fourteen failures are ``subprocess.TimeoutExpired ... after 900
seconds`` and all six live in one file.  A timeout is not a number, so no
dispatch reading can attribute it — and D-096 has already fixed its cause (the
timeout was stated seven times in two values, none of which cleared the measured
suite cost).  They are kept in :data:`CI_FAILURES` because the census has to be
whole, and partitioned out by :func:`attributable` because grading them would
manufacture a verdict from an unrelated event.

A census correction this module exists to prevent
-------------------------------------------------

The 14 have now been summarised twice, and both summaries were wrong about the
same file:

* ``STATE.md`` (08:00) recorded ``2 in exclusion_scope`` among the 8 non-timeout
  failures;
* the 09:00 journal published this as a 🔴 correction — "``exclusion_scope`` owns
  **6 of 14** — 4 FAILED + 2 ERROR" — and used it to call the STATE census wrong.

Measured from the run's own ``short test summary info``: ``exclusion_scope`` owns
**8 of 14** — 6 FAILED + 2 ERROR — of which **6 are the timeouts**, leaving
exactly **2** non-timeout failures in that file.  STATE was right.  The
correction was the error, and it was the more confident of the two.  Hence
:data:`CI_FAILURES` is a pinned census with one row per failure and a test that
re-derives every published count from it, so the next summary is a query rather
than a recollection.

Refs: Q-091 · D-033 (the finding this re-takes) · D-097 (the failures live
outside the local gate's population) · D-096 (the six timeouts) · D-091 (a scan
with no subject test grades nothing) · D-076/D-081 (emptiness before success).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass

#: Attribution verdicts.  Ordered as :func:`attribute` decides them.
DRIFT_CONSISTENT = "DRIFT_CONSISTENT"
DRIFT_SHAPED = "DRIFT_SHAPED"
REAL = "REAL"
UNREPRODUCED = "UNREPRODUCED"
INVERTED = "INVERTED"

VERDICTS: tuple[str, ...] = (
    DRIFT_CONSISTENT,
    DRIFT_SHAPED,
    REAL,
    UNREPRODUCED,
    INVERTED,
)

#: Census grades.  ``VACUOUS`` and ``NO_SUBJECT`` are decided before any
#: "everything is attributed" reading, for the reason this package keeps
#: re-learning: a harness that observed nothing must not be able to report
#: success.  ``NO_SUBJECT`` is D-091's lesson specifically — a scan whose
#: subject never failed in *any* mode is measuring its own plumbing.
VACUOUS = "VACUOUS"
NO_SUBJECT = "NO_SUBJECT"
INCOMPLETE = "INCOMPLETE"
ALL_DRIFT = "ALL_DRIFT"
MIXED = "MIXED"
ALL_REAL = "ALL_REAL"

GRADES: tuple[str, ...] = (
    VACUOUS,
    NO_SUBJECT,
    INCOMPLETE,
    ALL_DRIFT,
    MIXED,
    ALL_REAL,
)

#: The numpy CPU features masked to reproduce the runner's dispatch.  Verified
#: on the dev box: with these disabled ``numpy.__config__`` reports ``AVX2`` as
#: its top extension and no ``AVX512*`` at all, which is what the runner's own
#: D-033 fingerprint step prints.
AVX512_MASK: tuple[str, ...] = (
    "AVX512F",
    "AVX512CD",
    "AVX512_SKX",
    "AVX512_CLX",
    "AVX512_CNL",
    "AVX512_ICL",
    "AVX512_KNL",
    "AVX512_KNM",
)

#: Cause words.  ``TIMEOUT`` rows carry no number, so they are not attributable.
TIMEOUT = "TIMEOUT"
ASSERTION = "ASSERTION"


@dataclass(frozen=True)
class CiFailure:
    """One row of the ``slow`` job's ``short test summary info``."""

    test_id: str
    outcome: str  # "FAILED" | "ERROR" -- as pytest printed it
    cause: str  # TIMEOUT | ASSERTION
    signature: str = ""  # CI's assertion text, for the textual match

    @property
    def file(self) -> str:
        return self.test_id.split("::", 1)[0]

    @property
    def attributable(self) -> bool:
        """A dispatch reading can only speak about a row that has a number."""
        return self.cause == ASSERTION


#: The complete census of CI run ``31042602721`` — the first ``slow`` job ever
#: allowed to finish (162.7 min against the 360 min cap D-094 raised).  Its
#: summary line: ``12 failed, 138 passed, 2 skipped, 1068 deselected, 2 errors``.
#:
#: Transcribed from the run's ``short test summary info`` block, one row per
#: line of it.  Counts published anywhere else are derived from this tuple by
#: :func:`census`, never re-counted by hand.
CI_FAILURES: tuple[CiFailure, ...] = (
    CiFailure(
        "eval/mppi_sandbox/tests/test_ab_temperature_protocol.py"
        "::test_protocol_moves_the_effect_size_but_not_its_sign",
        "FAILED",
        ASSERTION,
        "assert 0.036210379360192974 > (1.25 * 0.03433654744256881)",
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_denominator_scope.py"
        "::TestD028sMechanismIsTemperatureConditional"
        "::test_the_shipped_loud_arm_is_healthier_yet_understated_more",
        "FAILED",
        ASSERTION,
        "assert 0.2896076533954799 < (0.12417971687770564 / 3)",
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_exclusion_scope.py"
        "::test_the_exclusion_list_manufactured_exactly_two_candidates",
        "FAILED",
        ASSERTION,
        "assert {'exclusion_s...d.stationary'} == {'guard_refle...d_is_derived'}",
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_exclusion_scope.py"
        "::test_self_entries_are_the_majority_and_are_left_alone",
        "FAILED",
        ASSERTION,
        "assert not True",
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_exclusion_scope.py"
        "::test_the_reconstruction_agrees_with_a_measured_run",
        "FAILED",
        TIMEOUT,
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_exclusion_scope.py"
        "::test_two_independent_flat_censuses_move_only_where_addresses_do",
        "FAILED",
        TIMEOUT,
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_exclusion_scope.py"
        "::test_the_four_run_batch_single_tree_licenses",
        "FAILED",
        TIMEOUT,
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_exclusion_scope.py"
        "::test_the_six_run_batch_prices_the_zero_movement_threshold",
        "FAILED",
        TIMEOUT,
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_exposure_timing_band.py"
        "::TestTheBandConstantIsMeasured"
        "::test_reportable_scenes_land_inside_the_declared_band",
        "FAILED",
        ASSERTION,
        "assert 2.185714285714286 == 2.038 ± 0.05",
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_hazard_exposure.py"
        "::test_refutation_reproduces_from_simulation",
        "FAILED",
        ASSERTION,
        "assert set() == {0.4}",
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_horizon_audit.py"
        "::TestScaleMatchedWeightIsHorizonDependent"
        "::test_the_prescribed_weight_moves_with_the_horizon",
        "FAILED",
        ASSERTION,
        "assert 1.0288845528582653 > 1.2",
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_scale_match.py"
        "::TestThePrescriptionLandsWhereItSaysItWill"
        "::test_the_prescribed_weight_achieves_the_requested_ratio",
        "FAILED",
        ASSERTION,
        "assert 0.17901180719252627 == 0.25 ± 0.0625",
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_exclusion_scope.py"
        "::test_both_published_rankings_were_taken_over_a_population_with_artifacts",
        "ERROR",
        TIMEOUT,
    ),
    CiFailure(
        "eval/mppi_sandbox/tests/test_exclusion_scope.py"
        "::test_the_input_fold_reproduces_a_measured_run_under_the_same_exclusion",
        "ERROR",
        TIMEOUT,
    ),
)


def attributable(census: tuple[CiFailure, ...] = CI_FAILURES) -> tuple[CiFailure, ...]:
    """The rows a dispatch reading is entitled to speak about."""
    return tuple(f for f in census if f.attributable)


def census(rows: tuple[CiFailure, ...] = CI_FAILURES) -> dict[str, int]:
    """Every published count, derived from the pinned rows.

    The point of this function is that the numbers in STATE, the journal and
    ``docs/`` become a query against :data:`CI_FAILURES` instead of a count
    somebody took by eye — which has now been done twice and been wrong twice,
    the second time as a confident correction of the first.
    """
    per_file: dict[str, int] = {}
    for row in rows:
        per_file[row.file] = per_file.get(row.file, 0) + 1
    return {
        "total": len(rows),
        "failed": sum(1 for r in rows if r.outcome == "FAILED"),
        "errors": sum(1 for r in rows if r.outcome == "ERROR"),
        "timeouts": sum(1 for r in rows if r.cause == TIMEOUT),
        "attributable": len(attributable(rows)),
        "files": len(per_file),
    }


def file_census(rows: tuple[CiFailure, ...] = CI_FAILURES) -> dict[str, dict[str, int]]:
    """Per-file breakdown: how many rows, and how many of them are timeouts.

    ``exclusion_scope`` is the row this exists for — 8 total, 6 of them
    timeouts, 2 real assertions — the split both prior summaries got wrong.
    """
    out: dict[str, dict[str, int]] = {}
    for row in rows:
        cell = out.setdefault(row.file, {"total": 0, "timeouts": 0, "attributable": 0})
        cell["total"] += 1
        if row.cause == TIMEOUT:
            cell["timeouts"] += 1
        else:
            cell["attributable"] += 1
    return out


@dataclass(frozen=True)
class LocalReading:
    """One test run on the dev box under both dispatches."""

    test_id: str
    native_passed: bool
    masked_passed: bool
    masked_signature: str = ""

    @property
    def dispatch_moved_it(self) -> bool:
        return self.native_passed != self.masked_passed


def _normalise(text: str) -> str:
    """Collapse whitespace so pytest's column padding is not part of the claim."""
    return re.sub(r"\s+", " ", text).strip()


def attribute(failure: CiFailure, reading: LocalReading) -> str:
    """Grade one CI failure against its two-dispatch dev-box reading.

    Raises on a timeout row rather than returning a verdict: a dispatch reading
    about a row with no number is a category error, and returning something
    plausible for it is how a census acquires manufactured entries.
    """
    if not failure.attributable:
        raise ValueError(
            f"{failure.test_id} failed by {failure.cause}, which carries no "
            "number for a dispatch reading to attribute"
        )
    if failure.test_id != reading.test_id:
        raise ValueError(f"reading is for {reading.test_id}, not {failure.test_id}")
    if not failure.signature.strip():
        # Containment makes the empty string match every block, so a row with no
        # recorded CI text would grade DRIFT_CONSISTENT unconditionally -- the
        # strongest verdict in this module, awarded for having no evidence.
        # Exactly the absence-read-as-clean shape this branch has now hit nine
        # times, so it is refused at the point where it would be produced rather
        # than only pinned in the census data.
        raise ValueError(
            f"{failure.test_id} is attributable but carries no CI signature; "
            "a textual match against nothing is not a match"
        )

    if reading.native_passed and not reading.masked_passed:
        # Containment, not equality.  pytest prints an assertion as a block --
        # the ``AssertionError`` message, then the rewritten comparison, then
        # the ``+ where`` expansion -- and which of those lines CI's summary
        # quoted depends on whether the assert carried a message.  Requiring
        # equality would grade a bit-exact reproduction DRIFT_SHAPED whenever
        # the two captures started on different lines of the same block, which
        # is a downgrade that reads like a finding.  The digits still have to
        # be there, so this stays D-033's claim and not a weaker one.
        same = _normalise(failure.signature) in _normalise(reading.masked_signature)
        return DRIFT_CONSISTENT if same else DRIFT_SHAPED
    if not reading.native_passed and not reading.masked_passed:
        return REAL
    if reading.native_passed and reading.masked_passed:
        return UNREPRODUCED
    return INVERTED


def unmeasured(
    verdicts: dict[str, str], census: tuple[CiFailure, ...] = CI_FAILURES
) -> tuple[str, ...]:
    """Attributable rows with no dispatch reading.

    Not every attributable row is *readable* on the dev box.  Two of them —
    both in ``test_exclusion_scope.py`` — spawn a full nested pytest run of
    their own, so a single invocation costs more than the whole cycle budget
    and returns before reaching its assertion.  A row like that has no verdict,
    and the distinction between "explained" and "never asked" is the entire
    point of this module.
    """
    return tuple(f.test_id for f in attributable(census) if f.test_id not in verdicts)


def grade(
    verdicts: dict[str, str], census: tuple[CiFailure, ...] = CI_FAILURES
) -> str:
    """Grade the census as a whole.

    The degenerate grades come first, and for three different reasons.

    ``VACUOUS`` — an empty mapping observed nothing, so it cannot report that
    everything is explained.

    ``NO_SUBJECT`` — a mapping in which *no* row failed under either dispatch
    means the harness never reproduced a single CI failure: the ids drifted,
    ``--slow`` was dropped, the selection was empty.  That state is
    indistinguishable from "all clean" unless it is named.  D-091 shipped
    exactly that bug — a scan with no subject graded a 60 s ``gh`` call against
    a full-suite figure and looked authoritative.

    ``INCOMPLETE`` — some attributable row was never read.  This is D-097's
    finding one module over: a verdict taken over part of a population must not
    be quoted as one about the whole.  ``ALL_DRIFT`` from a subset would be the
    banner's own error (an explanation generalised past its evidence) committed
    by the instrument built to catch it.
    """
    if not verdicts:
        return VACUOUS
    values = set(verdicts.values())
    if values == {UNREPRODUCED}:
        return NO_SUBJECT
    if unmeasured(verdicts, census):
        return INCOMPLETE
    drift = {DRIFT_CONSISTENT, DRIFT_SHAPED}
    if values <= drift:
        return ALL_DRIFT
    if not (values & drift):
        return ALL_REAL
    return MIXED


def measure(
    failures: tuple[CiFailure, ...] | None = None,
    timeout: int = 900,
) -> dict[str, LocalReading]:
    """Run each attributable failure natively and with AVX-512 masked.

    Expensive — these are ``slow``-marked closed-loop tests.  Callers in the
    test suite use pinned readings; this is the function that takes a fresh one.
    """
    subjects = attributable() if failures is None else failures
    out: dict[str, LocalReading] = {}
    for failure in subjects:
        results: dict[str, tuple[bool, str]] = {}
        for mode in ("native", "masked"):
            env = dict(os.environ)
            if mode == "masked":
                env["NPY_DISABLE_CPU_FEATURES"] = " ".join(AVX512_MASK)
            else:
                env.pop("NPY_DISABLE_CPU_FEATURES", None)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--slow",
                    failure.test_id,
                    "-q",
                    "-p",
                    "no:cacheprovider",
                ],
                capture_output=True,
                text=True,
                env=env,
                timeout=timeout,
            )
            # Keep the whole ``E`` block, not its first line.  :func:`attribute`
            # matches CI's quoted signature by containment, and which line of
            # the block CI quoted is not something this end can predict.
            block = " ".join(
                line[1:].strip()
                for line in proc.stdout.splitlines()
                if line.startswith("E ")
            )
            results[mode] = (proc.returncode == 0, block)
        out[failure.test_id] = LocalReading(
            test_id=failure.test_id,
            native_passed=results["native"][0],
            masked_passed=results["masked"][0],
            masked_signature=results["masked"][1],
        )
    return out
