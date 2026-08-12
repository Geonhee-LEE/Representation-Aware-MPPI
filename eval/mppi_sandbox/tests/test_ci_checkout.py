"""The shipped workflow must hand the suite the corpus the suite reads."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from eval.mppi_sandbox import ci_checkout as cc


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "wf.yml"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


SHALLOW_WF = """
    jobs:
      fast:
        steps:
          - uses: actions/checkout@v4
          - run: python -m pytest eval/mppi_sandbox/tests/ -q
"""

FULL_WF = """
    jobs:
      fast:
        steps:
          - uses: actions/checkout@v4
            with:
              fetch-depth: 0
          - run: python -m pytest eval/mppi_sandbox/tests/ -q
"""


class TestTheShippedWorkflow:
    def test_every_suite_job_checks_out_full_history(self):
        assert cc.shallow_jobs() == [], (
            "a job runs the suite over a truncated commit graph; "
            "cycle_artifacts / tsv_timestamp / assert_reach read history as data"
        )

    def test_the_verdict_is_full_depth(self):
        assert cc.grade() == cc.FULL_DEPTH

    def test_the_reading_is_not_vacuous(self):
        """The screen must be looking at jobs, not at an empty mapping.

        Scoped to "at least one", not to a count, so adding a job cannot turn it
        red -- but a rename or restructure that drops every job out of the
        population fails here instead of passing as a clean bill.
        """
        depths = cc.checkout_depths()
        assert depths, "no suite-running job was found; the screen graded nothing"
        assert len(depths) >= 2, (
            f"expected both the fast and slow suite jobs, found {sorted(depths)}"
        )


class TestTheDefaultIsADepthNotAnAbsence:
    def test_a_job_with_no_fetch_depth_reports_depth_one(self, tmp_path):
        """The module's whole reason to exist: absent != unconstrained."""
        depths = cc.checkout_depths(_write(tmp_path, SHALLOW_WF))
        assert depths == {"fast": cc.CHECKOUT_DEFAULT_DEPTH}

    def test_that_job_grades_shallow(self, tmp_path):
        assert cc.grade(_write(tmp_path, SHALLOW_WF)) == cc.SHALLOW

    def test_an_explicit_zero_grades_full_depth(self, tmp_path):
        assert cc.grade(_write(tmp_path, FULL_WF)) == cc.FULL_DEPTH

    def test_the_two_workflows_differ_only_in_that_key(self, tmp_path):
        """Non-vacuity of the pair above: the fixtures are otherwise identical,
        so the verdict flip is attributable to `fetch-depth` and nothing else."""
        shallow = _write(tmp_path, SHALLOW_WF).read_text().replace(
            "- uses: actions/checkout@v4",
            "- uses: actions/checkout@v4\n    with:\n      fetch-depth: 0",
        )
        assert "fetch-depth" in shallow


class TestTheUnreadableCasesAreNotCleanBills:
    def test_a_missing_workflow_grades_unread(self, tmp_path):
        assert cc.grade(tmp_path / "nope.yml") == cc.UNREAD

    def test_malformed_yaml_grades_unread(self, tmp_path):
        assert cc.grade(_write(tmp_path, "jobs: [not, a, mapping]")) == cc.UNREAD

    def test_a_workflow_with_no_suite_job_is_not_full_depth(self, tmp_path):
        """A workflow with nothing to grade must not read as a pass."""
        wf = _write(tmp_path, """
            jobs:
              lint:
                steps:
                  - uses: actions/checkout@v4
                  - run: ruff check .
        """)
        assert cc.grade(wf) == cc.NO_SUITE_JOB

    def test_a_job_that_never_checks_out_is_absent_not_shallow(self, tmp_path):
        wf = _write(tmp_path, """
            jobs:
              fast:
                steps:
                  - run: python -m pytest eval/ -q
        """)
        assert cc.checkout_depths(wf) == {}


class TestTheJobPopulationIsDerivedNotTyped:
    def test_renaming_a_job_does_not_drop_it_from_the_population(self, tmp_path):
        wf = _write(tmp_path, SHALLOW_WF.replace("fast:", "renamed-job:"))
        assert cc.shallow_jobs(wf) == ["renamed-job"]

    def test_a_non_pytest_job_is_not_graded(self, tmp_path):
        wf = _write(tmp_path, SHALLOW_WF.replace(
            "python -m pytest eval/mppi_sandbox/tests/ -q", "echo hello"))
        assert cc.checkout_depths(wf) == {}


def test_report_names_the_shallow_job(tmp_path):
    text = cc.report(_write(tmp_path, SHALLOW_WF))
    assert "SHALLOW" in text
    assert "fast" in text
    assert "truncated corpus" in text


@pytest.mark.parametrize("verdict", [cc.SHALLOW, cc.UNREAD, cc.NO_SUITE_JOB])
def test_the_failing_verdicts_are_distinct_strings(verdict):
    assert verdict != cc.FULL_DEPTH
