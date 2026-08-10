"""The gate's green must name the population it was taken over.

Two things are being pinned here, and they pull in opposite directions:

* the guard **fires** on the shape that went unnoticed for 89 cycles — a green
  receipt whose skipped remainder is the part CI reports failing; and
* the guard **stays silent** on the shape that occurs every single cycle — a
  green receipt whose remainder is simply not known about.

A test suite that only pinned the first would license a guard that refuses every
push, which is D-042's muted-alarm defect and would be deleted within a day.
"""

from __future__ import annotations

import json
import re

import pytest

from eval.mppi_sandbox import ci_verdict as cv
from eval.mppi_sandbox import push_preflight as pp
from eval.mppi_sandbox import suite_coverage as sc

#: The counts CI run 31042602721 and the local gate actually produced on
#: 2026-08-06.  Kept as data so the tests below assert about a reading that
#: happened rather than one convenient for them.
LOCAL_FAST = {"passed": 1091, "skipped": 154}
CI_SLOW = {"failed": 12, "passed": 138, "skipped": 2, "deselected": 1068, "error": 2}


class TestEmptinessBeforeSuccess:
    """An empty reading leaves nothing out, and must not read as full coverage."""

    def test_no_counts_at_all_is_empty_not_full(self):
        assert sc.of({}).grade == sc.EMPTY

    def test_an_all_skipped_run_is_empty_not_partial(self):
        # push_preflight's own worked example: 400 collected, 400 skipped.
        assert sc.of({"skipped": 400}).grade == sc.EMPTY

    def test_fraction_of_an_empty_population_does_not_raise(self):
        assert sc.of({}).fraction == 0.0

    def test_empty_is_decided_first(self):
        assert sc.GRADES[0] == sc.EMPTY


class TestTheGradeSplitsTheRealReadings:
    def test_the_local_gate_is_partial(self):
        cov = sc.of(LOCAL_FAST)
        assert cov.grade == sc.PARTIAL
        assert cov.executed == 1091
        assert cov.uncovered == 154

    def test_the_local_gates_green_covered_seven_eighths_of_the_suite(self):
        # The headline: 1091/1091 reads as 100%; it was 87.6%.
        assert sc.of(LOCAL_FAST).fraction == pytest.approx(0.876, abs=0.005)

    def test_the_ci_slow_job_is_also_partial_in_the_other_direction(self):
        cov = sc.of(CI_SLOW)
        assert cov.grade == sc.PARTIAL
        assert cov.uncovered == 1070  # 2 skipped + 1068 deselected

    def test_a_full_run_grades_full(self):
        assert sc.of({"passed": 1246}).grade == sc.FULL

    def test_failures_still_count_as_executed(self):
        # A red run has covered its population; coverage and outcome are
        # orthogonal axes and conflating them would hide one behind the other.
        assert sc.of({"passed": 10, "failed": 2}).grade == sc.FULL


class TestTheTwoOutcomeListsPartitionTheVocabulary:
    """No outcome word may fall in neither list.

    ``executed`` and ``uncovered`` are computed by summing two hand-written
    tuples in two different modules.  A word in neither shrinks the population
    silently — the reading stays green and the denominator quietly drops — which
    is the same class of defect as the census scans that graded ``SUFFICIENT``
    off a population of zero.
    """

    def _vocabulary(self) -> set[str]:
        # The words parse_summary can actually emit, read off its own regex
        # rather than re-typed, so growing the regex grows this test.
        pattern = pp._SUMMARY_TOKEN.pattern
        group = re.search(r"\(([a-z|?s]+)\)\s*$", pattern.replace(r"\s+", " "))
        assert group, "could not read the outcome alternation out of the regex"
        words = set()
        for raw in group.group(1).split("|"):
            word = raw.replace("?", "")
            words.add(word.rstrip("s") if word.startswith("error") else word)
        return words

    def test_the_regex_alternation_is_readable(self):
        assert "passed" in self._vocabulary()

    def test_every_outcome_word_is_executed_or_uncovered(self):
        vocab = self._vocabulary() - {"warnings", "warning"}
        classified = set(pp.EXECUTED_OUTCOMES) | set(sc.UNCOVERED_OUTCOMES)
        assert vocab <= classified, f"unclassified outcome words: {vocab - classified}"

    def test_no_word_is_in_both(self):
        assert not set(pp.EXECUTED_OUTCOMES) & set(sc.UNCOVERED_OUTCOMES)


class TestTheRefusalNeedsBothHalves:
    """``UNCOVERED_RED`` is a conjunction, and each half is load-bearing."""

    def test_partial_plus_failing_remainder_refuses(self):
        assert sc.uncovered_is_red(LOCAL_FAST, cv.FAIL) is True

    def test_partial_with_an_unknown_remainder_does_not_refuse(self):
        # The everyday path.  If this ever returns True the gate blocks every
        # push and gets muted (D-042).
        assert sc.uncovered_is_red(LOCAL_FAST, None) is False

    def test_partial_with_a_passing_remainder_does_not_refuse(self):
        assert sc.uncovered_is_red(LOCAL_FAST, cv.PASS) is False

    def test_pending_and_unrun_remainders_do_not_refuse(self):
        for verdict in (cv.PENDING, cv.UNRUN, cv.UNREADABLE, cv.NO_JOBS):
            assert sc.uncovered_is_red(LOCAL_FAST, verdict) is False, verdict

    def test_full_coverage_cannot_be_uncovered_red(self):
        # Nothing was left out, so a failing "remainder" is not this receipt's
        # blind spot — it is a different tree's problem.
        assert sc.uncovered_is_red({"passed": 1246}, cv.FAIL) is False

    def test_an_empty_receipt_is_not_uncovered_red(self):
        # It is VACUOUS, which push_preflight decides earlier; grading it here
        # too would let the later verdict mask the more informative one.
        assert sc.uncovered_is_red({}, cv.FAIL) is False


class TestTheMetricStringCannotBeQuotedAsATotal:
    def test_a_partial_reading_carries_its_remainder(self):
        s = sc.describe_metric(LOCAL_FAST)
        assert "1091/1091" in s
        assert "+154 uncovered" in s

    def test_a_full_reading_is_bare(self):
        assert sc.describe_metric({"passed": 1246}) == "sandbox:pass=1246/1246"

    def test_an_empty_reading_says_so_rather_than_rendering_zero_of_zero(self):
        assert "EMPTY" in sc.describe_metric({})

    def test_the_partial_string_is_not_mistakable_for_a_full_one(self):
        assert sc.describe_metric(LOCAL_FAST) != sc.describe_metric(
            {"passed": 1091}
        )


class TestTheGateSpeaksTheVerdict:
    """End-to-end through ``push_preflight.check`` on a real receipt file."""

    def _receipt(self, tmp_path, counts):
        import subprocess

        from eval.mppi_sandbox import tree_provenance as tp

        st = tp.stamp()
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        r = pp.Receipt(
            head=head,
            worktree_fingerprint=st.worktree_fingerprint,
            committed_fingerprint=st.committed_fingerprint,
            returncode=0,
            counts=counts,
            command=("python3", "-m", "pytest", "-q"),
            worktree=dict(st.worktree),
        )
        path = tmp_path / "receipt.json"
        path.write_text(r.to_json())
        return path

    def _check(self, tmp_path, counts, **kw):
        """``check`` with the *tree* and *population* axes neutralised.

        Both are ambient — they read the repository these tests happen to run
        in, not their arguments — and this class grades neither.  The tree axis
        is neutralised by declaring whatever drifts (below); the population axis
        by passing ``frontier=()`` (D-109), which otherwise grades
        ``UNSUPPORTED_CLAIM`` on **every** cycle: D-044 orders the journal
        written at 4a and the TSV row appended after the suite runs at 4a-ter, so
        mid-cycle the in-flight journal's claim is unmet by construction.  These
        three tests went red on 2026-08-07 for that reason and no other.

        Neither neutralisation weakens a guard: the tree axis keeps
        ``test_an_uncommitted_edit_still_reaches_undeclared`` below, and the
        population axis is proven end-to-end in ``test_push_claim_gate.py``,
        every test of which drives a scratch repo through an explicit ``root``.

        ``check`` grades population and tree-vs-``HEAD`` drift in one pass, and
        these tests are about the first.  Run inside a cycle that has edited a
        tracked file and not yet committed it — which is every cycle, including
        the one that wrote this file — the tree axis reaches ``UNDECLARED``
        first and the coverage assertion below never runs.  A test that only
        passes on a clean worktree is a test that reports on the worktree.

        So: declare whatever is currently drifting.  ``check``'s other verdicts
        keep their own tests; nothing here weakens them.
        """
        from eval.mppi_sandbox import tree_provenance as tp

        drift = tp.undeclared_drift()
        declared = {
            p: "neutralised by test fixture"
            for p in (*drift.changed, *drift.added, *drift.removed)
        }
        declared.update({p: "declared local-only" for p in tp.DECLARED_LOCAL_ONLY})
        kw.setdefault("frontier", ())
        return pp.check(self._receipt(tmp_path, counts), declared=declared, **kw)

    def test_a_known_red_remainder_refuses_the_push(self, tmp_path):
        v = self._check(tmp_path, LOCAL_FAST, uncovered_verdict=cv.FAIL)
        assert v.verdict == pp.UNCOVERED_RED
        assert not v.ok
        assert "154" in v.detail

    def test_the_same_receipt_passes_when_the_remainder_is_unknown(self, tmp_path):
        # The negative control for the guard as a whole: today's ordinary cycle
        # must still be able to push.
        v = self._check(tmp_path, LOCAL_FAST)
        assert v.verdict == pp.GREEN, v.describe()

    def test_even_that_green_names_what_it_did_not_cover(self, tmp_path):
        v = self._check(tmp_path, LOCAL_FAST)
        assert "154 uncovered" in v.detail

    def test_a_red_receipt_is_still_reported_as_red_not_uncovered(self, tmp_path):
        v = self._check(tmp_path, dict(LOCAL_FAST, failed=1), uncovered_verdict=cv.FAIL)
        assert v.verdict == pp.RED

    def test_a_vacuous_receipt_is_still_vacuous(self, tmp_path):
        v = self._check(tmp_path, {"skipped": 9}, uncovered_verdict=cv.FAIL)
        assert v.verdict == pp.VACUOUS

    def test_the_fixture_does_not_disable_the_tree_axis_for_real_callers(self, tmp_path):
        # The neutralisation above is fixture-local. Without it, an uncommitted
        # tracked edit must still reach UNDECLARED — otherwise these tests would
        # be quietly asserting that check() stopped grading the tree at all.
        from eval.mppi_sandbox import tree_provenance as tp

        if not tp.undeclared_drift().changed:
            pytest.skip("worktree is clean; nothing to be undeclared about")
        v = pp.check(self._receipt(tmp_path, LOCAL_FAST))
        assert v.verdict == pp.UNDECLARED


class TestTheVerdictOrderIsPinned:
    def test_uncovered_red_sits_between_red_and_undeclared(self):
        order = list(pp.VERDICTS)
        assert order.index(pp.RED) < order.index(pp.UNCOVERED_RED)
        assert order.index(pp.UNCOVERED_RED) < order.index(pp.UNDECLARED)

    def test_green_is_last(self):
        assert pp.VERDICTS[-1] == pp.GREEN

    def test_every_verdict_constant_appears_in_the_tuple(self):
        constants = {
            v
            for name, v in vars(pp).items()
            if name.isupper() and isinstance(v, str) and v == name
        }
        assert constants == set(pp.VERDICTS)


class TestTheGuardHasALiveSubject:
    """Does the population this guard exists to describe actually exist?

    D-091's defect, twice reproduced on this branch: a scan graded against a
    subject that was not in its input.  If the local suite ever stops having a
    slow half, every test above still passes on hand-written counts while the
    guard describes nothing.  So: measure the real split, cheaply.
    """

    def test_the_local_suite_really_does_leave_a_slow_half_unrun(self):
        import subprocess

        proc = subprocess.run(
            [
                "python3",
                "-m",
                "pytest",
                "eval/mppi_sandbox/tests/",
                "eval/tests/test_path_tracking_metrics.py",
                "eval/tests/test_run_metrics.py",
                "-q",
                "--collect-only",
                "-p",
                "no:cacheprovider",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        m = re.search(r"(\d+) slow test\(s\) not run", proc.stdout)
        assert m, f"conftest no longer reports a slow remainder:\n{proc.stdout[-800:]}"
        assert int(m.group(1)) > 0

    def test_the_constitutions_command_is_the_one_that_skips_them(self):
        # The gate is only interesting if the command the cycle actually runs is
        # the partial one.  Pinned against the workflow, where the split lives.
        from pathlib import Path

        wf = Path(".github/workflows/sandbox-ci.yml").read_text()
        assert "--slow -m slow" in wf, "the slow job no longer selects the slow half"
        fast = [
            ln
            for ln in wf.splitlines()
            if "python -m pytest" in ln and "--slow" not in ln
        ]
        assert fast, "no fast pytest invocation found; the two halves may have merged"


def test_module_docstring_numbers_match_the_pinned_readings():
    """The prose quotes 1092/1246 and 154; keep it from drifting off the data."""
    doc = sc.__doc__ or ""
    assert "154" in doc
    assert "1246" in doc
    assert json.dumps(LOCAL_FAST)  # the readings above are the ones cited


class TestCIWatchesWhatTheGuardsRead:
    """The safety net under D-177's fast receipt has to cover the guards' data.

    D-177 exempts the guard meta-suite from the local receipt when the diff
    leaves ``eval/mppi_sandbox/*.py`` alone, and pays for that with "the full
    set still runs in CI".  Q-127 found the hole: some guards read ``docs/`` as
    *data* — ``citation_audit.SCANNED_DOCS`` is exactly two files under it — so
    a docs-only diff can turn the meta-suite red, and CI's ``paths`` filter did
    not name ``docs/``.  The exemption's second term was empty for precisely
    the diff shape the REPORT phase produces every cycle (D-044 makes writing
    ``docs/decisions.md`` near-mandatory).

    The requirement is *derived* from the registry here rather than re-typed as
    a literal ``docs/**``.  That is D-047's rule: the thirty-cycle-old grep in
    the constitution matched three of five declared paths because somebody had
    hand-copied a list that later grew, and the two it missed were files the
    rule forbade committing and nothing stopped from being committed.  If
    ``SCANNED_DOCS`` gains a third file outside the filter, this goes red.
    """

    WORKFLOW = ".github/workflows/sandbox-ci.yml"

    @staticmethod
    def _path_filters(text: str) -> list[tuple[str, ...]]:
        """Every inline ``paths: [...]`` list in the workflow, in file order."""
        out = []
        for m in re.finditer(r"^\s*paths:\s*\[([^\]]*)\]\s*$", text, re.M):
            out.append(tuple(p.strip().strip("'\"") for p in m.group(1).split(",")))
        return out

    @staticmethod
    def _matches(glob: str, path: str) -> bool:
        """GitHub path-glob semantics: ``**`` spans ``/``, ``*`` does not."""
        rx, i = "", 0
        while i < len(glob):
            if glob.startswith("**", i):
                rx, i = rx + ".*", i + 2
            elif glob[i] == "*":
                rx, i = rx + "[^/]*", i + 1
            else:
                rx, i = rx + re.escape(glob[i]), i + 1
        return re.fullmatch(rx, path) is not None

    def test_both_triggers_still_carry_an_inline_path_filter(self):
        # If the file is reshaped to block-style lists the parser above would
        # silently find nothing and every assertion below would pass vacuously.
        from pathlib import Path

        filters = self._path_filters(Path(self.WORKFLOW).read_text())
        assert len(filters) == 2, (
            "expected a paths: filter on both push and pull_request; "
            f"parsed {len(filters)}. If the workflow moved to block-style "
            "lists, teach _path_filters about it — do not delete this test."
        )

    def test_every_scanned_doc_is_covered_by_both_triggers(self):
        from pathlib import Path

        from eval.mppi_sandbox import citation_audit as ca

        assert ca.SCANNED_DOCS, "the registry is empty; nothing would be asserted"
        filters = self._path_filters(Path(self.WORKFLOW).read_text())
        for globs in filters:
            for doc in ca.SCANNED_DOCS:
                assert any(self._matches(g, doc) for g in globs), (
                    f"{doc} is read by citation_audit but no glob in {globs} "
                    "triggers CI on it — Q-127's hole, reopened."
                )

    def test_the_matcher_distinguishes_single_and_double_star(self):
        # The assertion above is only worth anything if the matcher is not a
        # blanket yes.  `docs/*` must NOT cover a nested file; `docs/**` must.
        assert self._matches("docs/**", "docs/decisions.md")
        assert self._matches("docs/**", "docs/adr/nested/x.md")
        assert self._matches("docs/*", "docs/decisions.md")
        assert not self._matches("docs/*", "docs/adr/nested/x.md")
        assert not self._matches("eval/**", "docs/decisions.md")
