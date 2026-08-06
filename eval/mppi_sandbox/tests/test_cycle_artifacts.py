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
    """Flagged by at least one key — 18:00 and 21:00 sit in `disputed`.

    Their rows were appended retroactively by the 22:00 cycle, so the
    ``records`` key reads them ``HONOURED``.  That is the key's known failure
    mode, not a refutation of the finding: `git show --stat` shows neither
    commit touching the TSV, which is evidence no dating rule can overturn.
    """
    found = {c.path for c in ca.unsupported(BRANCH) + ca.disputed(BRANCH)}
    missing = [p for p in KNOWN_UNSUPPORTED if p not in found]
    assert not missing, f"instrument stopped seeing hand-established cases: {missing}"


def test_the_two_keys_disagree_and_the_module_says_so():
    """Publishing either key alone would over-report; the residue is named."""
    assert ca.disputed(BRANCH), "the disagreement is real and must stay visible"
    confirmed = {c.path for c in ca.unsupported(BRANCH)}
    assert confirmed.isdisjoint({c.path for c in ca.disputed(BRANCH)})


def test_an_unknown_key_is_refused():
    import pytest as _pytest

    with _pytest.raises(ValueError):
        ca.tsv_rows(BRANCH, key="whenever")


def test_the_reading_is_not_everything():
    """A grader that flags every cycle reproduces the controls and is useless.

    The controls are all positives, so they cannot bound the false-positive
    rate; this is the check that the instrument discriminates at all.
    """
    counts = ca.census(BRANCH)
    assert counts["HONOURED"] > counts["UNSUPPORTED"] * 5
    assert counts["cycles"] == sum(counts[g] for g in ca.GRADES)
    assert counts["confirmed"] <= counts["UNSUPPORTED"]


# --------------------------------------------------------------------------
# the field the first cut got wrong
# --------------------------------------------------------------------------


def test_assignment_keys_on_the_commit_date_not_the_typed_timestamp():
    """D-093's row is stamped 04:05 and belongs to the 02:00 cycle.

    The first cut read the typed column and convicted 02:00 while crediting
    04:00 — one error in each direction from one transcribed field.
    """
    assigned = ca.assignment(BRANCH, key="records")
    two = "journal/2026-08/06-02-memo-keyed-on-identity.md"
    assert assigned[two] >= 1, "02:00 appended a row; the typed timestamp hides it"


def test_a_row_whose_sha_does_not_resolve_falls_back_and_is_counted():
    """The fallback must be visible, not silently mixed into the reading."""
    rows = ca.tsv_rows(BRANCH, key="records")
    assert sum(1 for _, dated in rows if not dated) >= 1
    assert ca.census(BRANCH)["tsv_rows"] > 0


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


def _silent_repo(root: Path, published: int, total: int) -> str:
    """A branch with *total* cycles of which the first *published* reached ``origin``.

    Built rather than observed, and that is the whole point of this fixture.
    The assertion it replaces named ``06-18`` in the **live** repository, which
    made it a reading of a transient state wearing an invariant's clothes: the
    2026-08-07 00:00 cycle pushed this branch, ``06-18`` became published, and
    the test went red having caught nothing — the finding was *discharged*, which
    is the outcome it existed to encourage.  D-095's shape, and the failure mode
    is the expensive direction: a test that a correct action turns red gets
    read as a regression by whoever meets it next.
    """
    import subprocess

    branch = "autoresearch/silent-probe"

    def git(*args: str, when: str | None = None) -> None:
        env = None
        if when is not None:
            import os

            env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
        subprocess.run(("git", *args), cwd=str(root), check=True,
                       capture_output=True, env=env)

    root.mkdir(parents=True, exist_ok=True)
    git("init", "-q", "-b", branch.split("/", 1)[1])
    git("config", "user.email", "probe@local")
    git("config", "user.name", "probe")
    (root / "journal" / "2026-08").mkdir(parents=True, exist_ok=True)

    for i in range(total):
        name = f"journal/2026-08/01-{10 + i:02d}-c{i}.md"
        _journal(root, name, f"2026-08-01 {10 + i:02d}:00", f"`{branch}`", "no")
        git("add", "-A")
        git("commit", "-qm", f"c{i}", when=f"2026-08-01T{10 + i:02d}:30:00+09:00")
        if i + 1 == published:
            git("update-ref", f"refs/remotes/origin/{branch}", "HEAD")
    return branch


def test_a_second_silent_cycle_makes_the_first_one_red(tmp_path):
    """One cycle of latency: the newest is exempt, the one before it is not.

    Four cycles, the first two pushed.  ``c2`` is silent and no longer newest,
    so it is the finding; ``c3`` is in flight and exempt by position.  This is
    the rule the live-repo assertion was standing in for, and unlike that
    assertion it cannot be discharged by anybody pushing anything.
    """
    branch = _silent_repo(tmp_path / "repo", published=2, total=4)
    silent = {c.path for c in ca.unpublished(branch, root=tmp_path / "repo")}
    assert silent == {"journal/2026-08/01-12-c2.md"}


def test_one_silent_cycle_alone_is_not_yet_a_finding(tmp_path):
    """The negative control the replaced assertion never had.

    With only the newest cycle unpushed there is nothing to report — that is a
    cycle in flight.  Without this case the test above passes for a module that
    flags every unpushed journal it meets, which is a materially different and
    much noisier instrument.
    """
    branch = _silent_repo(tmp_path / "repo", published=3, total=4)
    assert ca.unpublished(branch, root=tmp_path / "repo") == ()


def test_the_positional_exemption_hides_a_dead_predecessor(tmp_path):
    """D-110: the exempt slot is occupied by the *previous* cycle during REVIEW.

    The premise behind ``ordered[:-1]`` is "newest == in flight", and it holds
    only once the running cycle has written its journal at 4a.  Before that
    write the newest journal on disk belongs to the cycle that just ended — so a
    predecessor that committed and died before pushing sits in the exempt slot
    and grades clean.  Three cycles, one pushed: ``c2`` is genuinely stranded and
    ``unpublished`` names only ``c1``.

    This is the live 2026-08-07 06:00 incident, reproduced in a scratch repo
    rather than asserted against the working tree — the whole point of D-095's
    fixture, since the live reading is discharged the moment anybody pushes.
    """
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=1, total=3)
    silent = {c.path for c in ca.unpublished(branch, root=root)}
    assert silent == {"journal/2026-08/01-11-c1.md"}
    # c2 is stranded and invisible — the defect, stated as an assertion.
    newest = ca.cycles(branch, root=root)[-1]
    assert newest.path == "journal/2026-08/01-12-c2.md"
    assert ca.published(newest, root=root) is False
    assert newest.path not in silent


def test_naming_the_in_flight_cycle_grades_the_predecessor(tmp_path):
    """The repair: state what is in flight instead of inferring it from order.

    The 07:00 cycle knows its own journal is not written yet, so *no* cycle on
    disk is in flight.  Saying so surfaces both stranded cycles.
    """
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=1, total=3)
    silent = {c.path for c in ca.unpublished(branch, root=root, in_flight=None)}
    assert silent == {
        "journal/2026-08/01-11-c1.md",
        "journal/2026-08/01-12-c2.md",
    }


def test_naming_a_cycle_exempts_that_one_and_only_that_one(tmp_path):
    """``in_flight=<path>`` is an exemption of one, not a positional offset."""
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=1, total=3)
    silent = {
        c.path
        for c in ca.unpublished(
            branch, root=root, in_flight="journal/2026-08/01-11-c1.md"
        )
    }
    assert silent == {"journal/2026-08/01-12-c2.md"}


def test_frontier_stranded_reports_what_the_exemption_drops(tmp_path):
    """The exempt observation is published rather than discarded (D-038)."""
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=1, total=3)
    stranded = ca.frontier_stranded(branch, root=root)
    assert stranded is not None
    assert stranded.path == "journal/2026-08/01-12-c2.md"
    assert ca.census(branch, root=root)["frontier_stranded"] == 1


def test_frontier_stranded_is_quiet_when_the_newest_cycle_pushed(tmp_path):
    """The negative control: a fully-pushed branch reports nothing.

    Without this, the assertion above passes for a function that returns the
    newest cycle unconditionally — a materially different instrument that is
    always red.
    """
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=3, total=3)
    assert ca.frontier_stranded(branch, root=root) is None
    assert ca.census(branch, root=root)["frontier_stranded"] == 0


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
