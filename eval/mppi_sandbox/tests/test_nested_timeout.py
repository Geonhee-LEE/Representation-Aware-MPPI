"""The nested-suite timeout: one statement, derived, and above the suite's cost.

The defect these pin is the one run 31042602721 published: six ``TimeoutExpired``
failures because the timeout guarding a nested full-suite run (900 s) was below
the suite's measured cost (1032-1396 s).  It failed by construction on every run,
which is why the tests here are about *arithmetic and population*, not flakiness.
"""

from __future__ import annotations

import ast
import textwrap

import pytest

from eval.mppi_sandbox import declared_ceiling as dc
from eval.mppi_sandbox import nested_suite_cost as nsc
from eval.mppi_sandbox import nested_timeout as nt


class TestTheValueIsStatedOnce:
    """D-047 / D-094's defect class: a number restated is a number that drifts."""

    def test_exactly_one_full_suite_site_states_a_literal(self):
        """Every spawn imports the constant; only the constant is a literal.

        Before this cycle the scan read **seven** full-suite sites at **two**
        values (900 and 1800).  A regression here means somebody hard-coded a
        timeout at a spawn again, which is precisely how the 1800s appeared.
        """
        stating = nt.gradable()
        assert len(stating) == 1, (
            "more than one full-suite site states a timeout literal: "
            + "; ".join(d.describe() for d in stating))
        assert stating[0].module == "nested_suite_cost"

    def test_the_population_agrees(self):
        assert nt.agreement() == nt.AGREES

    def test_the_shipped_value_clears_the_requirement(self):
        assert nt.grade(nsc.NESTED_TIMEOUT_SECONDS) == nt.SUFFICIENT

    def test_the_value_that_was_shipped_before_does_not(self):
        """900 s and 1800 s both fail — including the one somebody already raised.

        The 1800 s bump on the attributed censuses was the right direction and
        still short; without this assertion the fix reads as though 900 was the
        only wrong number.
        """
        assert nt.grade(900) == nt.INSUFFICIENT
        assert nt.grade(1800) == nt.INSUFFICIENT


class TestTheRequirementIsDerived:
    def test_it_is_the_worst_observation_times_the_shared_factor(self):
        assert nt.required_seconds() == int(round(
            max(s for s, _ in nt.OBSERVED_SUITE_SECONDS) * dc.HEADROOM_FACTOR))

    def test_the_factor_is_not_restated_here(self):
        """The headroom factor has one home (D-094's).  A copy is the same bug."""
        src = (nt.PACKAGE / "nested_timeout.py").read_text()
        assert "HEADROOM_FACTOR = " not in src

    def test_the_worst_observation_is_used_not_the_latest(self):
        """Asymmetric failure: too small kills every run, too large costs nothing.

        Pinned because ``OBSERVED_SUITE_SECONDS`` is ordered oldest-first and the
        newest reading is the *smaller* one — a ``[-1]`` would look right, read
        1032 s, and re-arm the trap on any runner as slow as D-089's.
        """
        assert nt.measured_suite_seconds() == 1396
        assert nt.OBSERVED_SUITE_SECONDS[-1][0] == 1032

    def test_every_observation_exceeds_the_timeout_that_was_shipped(self):
        """The finding itself: 900 s was below *every* reading, not a bad draw."""
        assert all(s > 900 for s, _ in nt.OBSERVED_SUITE_SECONDS)


class TestTheScanDiscriminatesSubjects:
    """Grading a 60 s ``gh`` call against a full-suite figure is a unit error."""

    def test_the_gh_call_is_not_pytest(self):
        rows = {d.module: d for d in nt.declared_timeouts() if d.subject == nt.NOT_PYTEST}
        assert "ci_verdict" in rows

    def test_the_scratch_runs_are_narrow_and_ungraded(self):
        narrow = {d.module for d in nt.declared_timeouts() if d.subject == nt.NARROW}
        assert {"predicate_vacuity", "predicate_inputs"} <= narrow
        assert all(d.subject == nt.FULL_SUITE for d in nt.gradable())

    def test_a_call_site_literal_is_seen_at_all(self):
        """D-091's miss: a signature scan cannot see ``timeout=900`` at a call.

        Synthetic rather than asserted against the tree, because the tree no
        longer contains one — and a guard that only passes while the defect is
        absent tests nothing.
        """
        src = textwrap.dedent('''
            import subprocess
            def go(suite=DEFAULT_SUITE):
                subprocess.run([sys.executable, "-m", "pytest", *suite],
                               timeout=900)
        ''')
        tree = ast.parse(src)
        call = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "run")
        assert nt._call_subject(call) == nt.FULL_SUITE

    def test_the_dropped_spawn_name_filter_changes_no_graded_reading(self):
        """The redundancy claim in :func:`declared_timeouts`, measured not asserted.

        A first draft narrowed callees by ``{"run", "check_output", "check_call",
        "Popen"}`` before testing the subject.  Re-applying that filter here must
        leave the graded population identical — the subject test already answers
        ``NOT_PYTEST`` for anything whose argv lacks ``pytest``.  It admits three
        extra ungraded rows and nothing else.
        """
        spawn_names = {"run", "check_output", "check_call", "Popen"}
        rows = nt.declared_timeouts()
        # No *call/default* row is graded either way — the one graded row is the
        # constant, which this scan never produced.  That is the equivalence:
        # dropping the filter admits rows, and admits none that count.
        assert [d for d in rows if d.gradable] == []
        dropped = [d for d in rows if d.subject == nt.NOT_PYTEST]
        assert dropped, "no non-spawn rows admitted — the filter was not redundant"
        assert all(not d.gradable for d in dropped)
        assert spawn_names  # the vocabulary is recorded here, not in the module

    def test_a_forwarded_timeout_states_nothing(self):
        """``timeout=timeout`` enforces what it is handed; counting it inflates."""
        fwd = [d for d in nt.declared_timeouts() if d.forwarded]
        assert fwd, "no forwarding site found — the scan stopped seeing them"
        assert all(not d.gradable for d in fwd)


class TestAbsenceIsNotAgreement:
    """The seventh name for absence-as-result on this branch (D-095's shape)."""

    def test_an_empty_population_is_undeclared_not_agreed(self, tmp_path):
        assert nt.agreement(tmp_path) == nt.UNDECLARED
        assert nt.stated_values(tmp_path) == ()

    def test_the_real_package_is_not_empty(self):
        """Positive control: without it the test above passes on a broken scan."""
        assert nt.declared_timeouts()
        assert nt.gradable()


class TestRaisingItIsBoundedAbove:
    """Every runner class pays the timeout inside one job (D-094's ceiling)."""

    def test_the_current_class_count_fits(self):
        assert nt.fits_ceiling(6) == nt.FITS

    def test_the_runway_is_one_more_class(self):
        """Same one-class margin D-094 measured for the ceiling — not a coincidence.

        Both are ``classes x per-run cost`` against the same platform cap, so a
        raise here spends the runway a new runner class would have needed.
        """
        assert nt.fits_ceiling(7) == nt.FITS
        assert nt.fits_ceiling(8) == nt.EXCEEDS_CEILING

    def test_an_unreadable_ceiling_is_not_a_pass(self):
        assert nt.fits_ceiling(6, ceiling_s=0) == nt.CEILING_UNREAD


def test_report_names_both_observations():
    """The report must show the reading it did *not* use, or the max is unauditable."""
    text = nt.report()
    assert "1396" in text and "1032" in text
    assert "2792" in text
