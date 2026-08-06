"""Tests for :mod:`eval.mppi_sandbox.cycle_artifacts`.

The first test is the negative control, per D-102: the 2026-08-06 09:00 cycle
was found by hand by the 10:00 cycle, which wrote the finding into its journal,
so its answer is known independently of this instrument.  An instrument that
cannot reproduce the one case whose answer is already known has not been shown
to see anything at all.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from eval.mppi_sandbox import cycle_artifacts as ca

BRANCH = "autoresearch/p3-epistemic-shadow-cost-critic"

#: The three cases established by hand before this module existed.  Named as
#: paths rather than counts so a test failure says *which* one stopped being
#: reproduced.
KNOWN_UNSUPPORTED = (
    "journal/2026-08/06-09-green-over-a-partial-population.md",
    "journal/2026-08/06-18-loop-reach-population-vacuity.md",
    "journal/2026-08/06-21-the-position-was-a-field-not-a-table.md",
)


def _journal(tmp_path: Path, name: str, stamp: str, branch: str, claim: str) -> Path:
    path = tmp_path / name
    path.write_text(
        textwrap.dedent(
            f"""\
            # A cycle

            - **Cycle**: {stamp} KST
            - **Branch**: {branch}
            - **Status**: in_progress

            ## Artifacts

            - PR: #67
            - TSV row appended: {claim}
            """
        ),
        encoding="utf-8",
    )
    return path


# --------------------------------------------------------------------------
# the control
# --------------------------------------------------------------------------


def test_the_control_case_is_reproduced():
    """09:00 claimed a row and appended none — established by the 10:00 cycle."""
    found = {c.path for c in ca.unsupported(BRANCH)}
    assert KNOWN_UNSUPPORTED[0] in found


def test_all_three_hand_established_cases_are_reproduced():
    found = {c.path for c in ca.unsupported(BRANCH)}
    missing = [p for p in KNOWN_UNSUPPORTED if p not in found]
    assert not missing, f"instrument stopped seeing hand-established cases: {missing}"


def test_the_reading_is_not_everything():
    """A grader that flags every cycle reproduces the controls and is useless.

    The controls are all positives, so they cannot bound the false-positive
    rate; this is the check that the instrument discriminates at all.
    """
    counts = ca.census(BRANCH)
    assert counts["HONOURED"] > counts["UNSUPPORTED"] * 5
    assert counts["cycles"] == sum(counts[g] for g in ca.GRADES)


# --------------------------------------------------------------------------
# the field the first cut got wrong
# --------------------------------------------------------------------------


def test_assignment_keys_on_the_commit_date_not_the_typed_timestamp():
    """D-093's row is stamped 04:05 and belongs to the 02:00 cycle.

    The first cut read the typed column and convicted 02:00 while crediting
    04:00 — one error in each direction from one transcribed field.
    """
    assigned = ca.assignment(BRANCH)
    two = "journal/2026-08/06-02-memo-keyed-on-identity.md"
    assert assigned[two] >= 1, "02:00 appended a row; the typed timestamp hides it"


def test_a_row_whose_sha_does_not_resolve_falls_back_and_is_counted():
    """The fallback must be visible, not silently mixed into the reading."""
    counts = ca.census(BRANCH)
    assert counts["undated_rows"] >= 1
    assert counts["undated_rows"] < counts["tsv_rows"]


def test_commit_minute_refuses_a_non_sha():
    assert ca._commit_minute("pending") is None
    assert ca._commit_minute("") is None


# --------------------------------------------------------------------------
# grading, and the asymmetry between the two directions
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "claim,rows,expected",
    [
        ("yes", 1, "HONOURED"),
        ("yes", 0, "UNSUPPORTED"),
        ("no", 0, "CONSISTENT_NO"),
        ("no", 1, "UNDERCLAIMED"),
        ("", 0, "UNPARSED"),
        ("maybe", 0, "UNPARSED"),
    ],
)
def test_grade_table(claim, rows, expected):
    cycle = ca.Cycle(path="x.md", minute=0, stamp="s", branch=BRANCH, tsv_claim=claim)
    assert ca.grade_tsv(cycle, rows) == expected


def test_only_the_over_claiming_direction_is_a_finding():
    assert ca.finding_grades() == {"UNSUPPORTED"}
    assert "UNDERCLAIMED" not in ca.finding_grades()


def test_the_finding_set_is_derived_from_the_grader_not_typed():
    """Change what an over-claim grades to, and the finding set follows.

    A typed copy would keep saying ``UNSUPPORTED`` after the grader stopped
    producing it — D-047's defect class, and the exact shape the census
    charged this module for on its first cut.
    """
    import inspect

    source = inspect.getsource(ca.finding_grades)
    assert "UNSUPPORTED" not in source, "the set must be computed, not spelled"
    assert "grade_tsv" in source


def test_every_grade_is_in_the_enum():
    """A grade the enum does not name would be invisible to census and report."""
    for claim in ("yes", "no", "", "maybe"):
        for rows in (0, 1):
            cycle = ca.Cycle("x.md", 0, "s", BRANCH, claim)
            assert ca.grade_tsv(cycle, rows) in ca.GRADES


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------


def test_a_file_with_no_cycle_stamp_is_not_a_silent_cycle(tmp_path):
    """``journal/README.md`` is not a cycle report and must not be graded."""
    path = tmp_path / "README.md"
    path.write_text("# Journal\n\nConventions live here.\n", encoding="utf-8")
    assert ca.parse(path) is None


def test_a_skip_cycle_names_no_branch(tmp_path):
    path = _journal(
        tmp_path, "a.md", "2026-08-06 03:00", "none (gate 1 fired)", "no"
    )
    cycle = ca.parse(path)
    assert cycle is not None and cycle.branch == ""


def test_skip_cycles_are_counted_not_dropped():
    """An exclusion nobody can count is an unstated filter."""
    assert ca.census(BRANCH)["no_branch"] >= 1
    assert all(not c.branch for c in ca.skipped_cycles())


def test_branch_is_read_through_trailing_prose(tmp_path):
    path = _journal(
        tmp_path,
        "a.md",
        "2026-08-06 03:00",
        f"`{BRANCH}` (PR #67, already in queue)",
        "yes",
    )
    cycle = ca.parse(path)
    assert cycle is not None and cycle.branch == BRANCH


def test_cycles_are_ordered_oldest_first():
    ordered = ca.cycles(BRANCH)
    assert [c.minute for c in ordered] == sorted(c.minute for c in ordered)


# --------------------------------------------------------------------------
# the second claim: did the cycle leave the machine?
# --------------------------------------------------------------------------


def test_the_newest_cycle_is_exempt_and_the_exemption_is_derived():
    """A cycle in flight has a journal and no push; that is not a finding."""
    ordered = ca.cycles(BRANCH)
    newest = ordered[-1]
    assert newest.path not in {c.path for c in ca.unpublished(BRANCH)}


def test_the_exemption_is_positional_not_a_named_list():
    """No path literal may appear in the exemption logic.

    A named exemption is a registry, and a registry maintained by memory is
    short at whichever element nobody remembered (D-046).
    """
    import inspect

    source = inspect.getsource(ca.unpublished)
    assert "journal/" not in source
    assert "ordered[:-1]" in source


def test_a_second_silent_cycle_makes_the_first_one_red():
    """18:00 went red only once 21:00 also failed to push — one cycle of latency."""
    silent = {c.path for c in ca.unpublished(BRANCH)}
    assert "journal/2026-08/06-18-loop-reach-population-vacuity.md" in silent


def test_an_unreadable_remote_yields_no_finding():
    """Not knowing is not the same as knowing there is nothing."""
    cycle = ca.Cycle("x.md", 0, "s", "autoresearch/does-not-exist-anywhere", "yes")
    assert ca.published(cycle) is None
    assert ca.unpublished("autoresearch/does-not-exist-anywhere") == ()


def test_a_skip_cycle_has_no_published_answer(tmp_path):
    path = _journal(tmp_path, "a.md", "2026-08-06 03:00", "none", "no")
    cycle = ca.parse(path)
    assert cycle is not None and ca.published(cycle) is None


# --------------------------------------------------------------------------
# emptiness before success — the rule this branch applies everywhere
# --------------------------------------------------------------------------


def test_the_reading_is_not_vacuous():
    """Every assertion above is worthless if the corpus is empty."""
    counts = ca.census(BRANCH)
    assert counts["cycles"] >= 90
    assert counts["tsv_rows"] >= 90


def test_report_names_every_finding_it_counted():
    text = ca.report(BRANCH)
    for cycle in ca.unsupported(BRANCH):
        assert cycle.path in text
    assert f"unsupported claims: {len(ca.unsupported(BRANCH))}" in text


def test_an_unknown_subcommand_is_refused():
    assert ca.main([]) == 2
    assert ca.main(["census"]) == 2
