"""Tests for :mod:`eval.mppi_sandbox.cycle_artifacts`.

The first test is the negative control, per D-102: the 2026-08-06 09:00 cycle
was found by hand by the 10:00 cycle, which wrote the finding into its journal,
so its answer is known independently of this instrument.  An instrument that
cannot reproduce the one case whose answer is already known has not been shown
to see anything at all.
"""

from __future__ import annotations

import os
import subprocess
import textwrap
import time
from datetime import timedelta
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


def _commit(cwd: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=str(cwd), check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", message],
        cwd=str(cwd), check=True, capture_output=True,
    )


@pytest.fixture
def scratch_repo(tmp_path: Path):
    """A repo whose journals were committed with each kind of ``Metric:`` line.

    Built rather than mocked because the fact under test is what ``git log
    --diff-filter=A`` answers, and a stubbed answer would test the stub.  The
    last commit **edits** ``pending.md`` while stating a real metric, which is
    the only way to show the grade follows the introducing commit.
    """
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(tmp_path),
                   check=True, capture_output=True)
    (tmp_path / "journal").mkdir()
    made = {}
    for name, metric in (
        ("pending.md", "Metric: sandbox:pass=pending"),
        ("silent.md", None),
        ("doc.md", "Metric: qual:doc-only"),
    ):
        path = _journal(tmp_path / "journal", name, "2026-08-09 18:00",
                        f"`{BRANCH}`", "yes")
        body = "[auto] a cycle\n\nTODO: x\nPhase: P5\n" + (metric or "") + "\n"
        _commit(tmp_path, body)
        made[name] = ca.parse(path, root=tmp_path)
    edited = tmp_path / "journal" / "pending.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\n- a later fix\n",
                      encoding="utf-8")
    _commit(tmp_path, "[auto] correct a predecessor\n\nMetric: sandbox:pass=2068/2068\n")
    return tmp_path, made


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
    assert not missing, (
        f"instrument stopped seeing hand-established cases: {missing}\n"
        + ca.divergence_digest(BRANCH, paths=KNOWN_UNSUPPORTED)
    )


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
    assert counts["HONOURED"] > counts["UNSUPPORTED"] * 5, ca.divergence_digest(BRANCH)
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


def _silent_repo(root: Path, published: int, total: int, claim: str = "no") -> str:
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
        _journal(root, name, f"2026-08-01 {10 + i:02d}:00", f"`{branch}`", claim)
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


def test_stranded_declines_the_exemption_and_names_the_whole_set(tmp_path):
    """``stranded`` is ``unpublished`` minus the positional exemption.

    Three cycles, one pushed: ``unpublished`` names ``c1`` and exempts ``c2``
    by position; ``stranded`` names both.  The gap between the two numbers is
    the fact the 07:00 and 08:00 cycles of 2026-08-07 each acted on.
    """
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=1, total=3)
    assert {c.path for c in ca.unpublished(branch, root=root)} == {
        "journal/2026-08/01-11-c1.md"
    }
    assert {c.path for c in ca.stranded(branch, root=root)} == {
        "journal/2026-08/01-11-c1.md",
        "journal/2026-08/01-12-c2.md",
    }


def test_stranded_is_empty_on_a_fully_pushed_branch(tmp_path):
    """The negative control, without which the assertion above passes for
    a function that returns every cycle unconditionally."""
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=3, total=3)
    assert ca.stranded(branch, root=root) == ()


def test_stranded_states_the_rule_once(tmp_path):
    """It delegates to ``unpublished`` rather than re-deriving the population.

    D-045/D-047: the copy nobody re-derives is the one that goes stale.  A
    stranding rule spelled twice would drift the moment ``published``'s
    unreadable-remote handling changed under one of them.
    """
    import inspect

    body = inspect.getsource(ca.stranded).split('"""')[-1]
    assert "unpublished(" in body
    assert "published(" not in body.replace("unpublished(", "")


def test_the_unwatched_set_is_what_the_push_gate_cannot_reach(tmp_path):
    """Stranded ∖ unsupported — in neither the gate's population nor anyone's.

    ``c1`` claims a TSV row it never appended, so the gate sees it.  ``c2``
    claims none, is equally stranded, and is invisible: that is the residue
    this function exists to name.
    """
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=1, total=3)
    (root / "results").mkdir(exist_ok=True)
    (root / "journal" / "2026-08" / "01-11-c1.md").write_text(
        (root / "journal" / "2026-08" / "01-11-c1.md")
        .read_text()
        .replace("TSV row appended: no", "TSV row appended: yes"),
        encoding="utf-8",
    )
    lying = {c.path for c in ca.unsupported(branch, root=root)}
    assert "journal/2026-08/01-11-c1.md" in lying
    assert {c.path for c in ca.unwatched_strandings(branch, root=root)} == {
        "journal/2026-08/01-12-c2.md"
    }


def test_strand_report_marks_only_the_unwatched_rows():
    """The renderer takes populations and reads no repository."""
    a = ca.Cycle("journal/x.md", 0, "2026-08-07 03:00", "autoresearch/b", "no")
    b = ca.Cycle("journal/y.md", 1, "2026-08-07 06:00", "autoresearch/b", "yes")
    text = ca.strand_report((a, b), (a,))
    assert "journal/x.md" in text and "journal/y.md" in text
    assert text.count("← unwatched") == 1  # one marker, on a and not on b
    assert "1 of them are invisible" in text
    assert "← unwatched" in text.split("journal/x.md")[1].split("\n")[0]
    assert "← unwatched" not in text.split("journal/y.md")[1]


def test_strand_report_says_so_when_there_is_nothing():
    assert "no stranded cycles" in ca.strand_report((), ())


def _amend_after_publishing(root: Path) -> str:
    """The D-378 shape: every journal on origin, one commit of amendment ahead.

    Deliberately *not* ``_silent_repo(published=1)`` — that strands whole
    journal files, which the journal census already sees.  What it cannot see
    is a tree where the file set on origin is complete and a later commit only
    **modified** one of those files.  That is what 06:00 was carrying.
    """
    import subprocess

    branch = _silent_repo(root, published=3, total=3)
    target = root / "journal" / "2026-08" / "01-12-c2.md"
    target.write_text(target.read_text(encoding="utf-8") + "\n- amended\n",
                      encoding="utf-8")
    subprocess.run(("git", "add", "-A"), cwd=str(root), check=True,
                   capture_output=True)
    subprocess.run(("git", "commit", "-qm", "[auto] bookkeeping amendment"),
                   cwd=str(root), check=True, capture_output=True)
    return branch


def test_the_amendment_strand_is_invisible_to_the_journal_census(tmp_path):
    """D-378 reproduced: ``stranded`` is right and blind at the same time.

    This is the negative control the module's own docstring argues for — a case
    whose answer is known independently of anything here, because the 06:00
    cycle measured it by hand and ``push_preflight probe`` confirmed it from a
    third direction.  Both assertions matter: dropping the first would let a
    ``commit_strand`` that simply duplicated the journal census pass.
    """
    root = tmp_path / "repo"
    branch = _amend_after_publishing(root)
    assert ca.stranded(branch, root=root) == ()          # honest, and blind
    assert len(ca.commit_strand(branch, root=root)) == 1  # the half it misses


def test_commit_strand_is_empty_when_head_is_on_origin(tmp_path):
    """The negative control: without it, a function returning a constant
    non-empty tuple passes the assertion above."""
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=3, total=3)
    assert ca.commit_strand(branch, root=root) == ()


def test_commit_strand_counts_every_commit_ahead_not_just_the_last(tmp_path):
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=1, total=3)
    assert len(ca.commit_strand(branch, root=root)) == 2


def test_an_unreadable_origin_ref_is_unknown_not_clean(tmp_path):
    """``None``, never ``()``.

    A branch that has never been pushed has no ``origin/<branch>`` to diff
    against.  Reading that as "nothing ahead" would hand every fresh branch a
    clean bill of health on the one reading built to catch unpushed work —
    the same distinction :func:`published` draws for the journal half.
    """
    root = tmp_path / "repo"
    _silent_repo(root, published=3, total=3)
    assert ca.commit_strand("autoresearch/never-pushed", root=root) is None
    assert ca.commit_strand("", root=root) is None


def test_the_two_unknown_states_do_not_render_alike():
    """``None`` and ``()`` are different sentences, not different wordings."""
    unknown = ca.commit_strand_report(None)
    clean = ca.commit_strand_report(())
    assert "UNKNOWN" in unknown and "not read as clean" in unknown
    assert "none" in clean and "UNKNOWN" not in clean


def test_a_commit_strand_alone_raises_the_subcommand(monkeypatch, capsys):
    """The wiring, which is the whole finding of D-378.

    ``commit_strand`` existing but going unread would reproduce exactly the
    state Q-103 recorded for ``in_flight``: an instrument with no caller is
    indistinguishable from an instrument with no finding.  So this asserts the
    rc, not the function — with the journal census deliberately silent, so the
    non-zero can only have come from the commit half.
    """
    monkeypatch.setattr(ca, "stranded", lambda *a, **k: ())
    monkeypatch.setattr(ca, "unwatched_strandings", lambda *a, **k: ())
    monkeypatch.setattr(ca, "commit_strand", lambda *a, **k: ("deadbeef",))
    monkeypatch.setattr(ca, "commit_strand_report", lambda *a, **k: "  ahead")
    assert ca.main(["stranded", "autoresearch/probe"]) == 1
    capsys.readouterr()


def test_the_mandated_carry_is_not_read_as_a_strand(tmp_path):
    """D-380, and the case that produced it — measured, not hypothetical.

    The fixture is the exact D-378 shape: every journal on origin, one later
    bookkeeping-only commit ahead.  D-379 correctly saw a commit there; the
    open question this settles is what that commit *is*.  Both assertions
    matter — the first is what D-379 bought and must not regress, the second
    is what it left collapsed.
    """
    root = tmp_path / "repo"
    branch = _amend_after_publishing(root)
    ahead = ca.commit_strand(branch, root=root)
    assert len(ahead) == 1                                  # D-379 still holds
    assert ca.strand_kind(ahead, root=root) == ca.CARRY     # D-380 adds this


def test_a_carry_that_outlived_its_ride_is_a_strand(tmp_path):
    """The age bound, which is what keeps the exemption from being a hole.

    D-378 promises the carry is picked up by the *next* cycle.  If that never
    happened the commit is unpushed work again, and an exemption with no
    expiry would hand it a clean bill forever — the precise shape of the bug
    D-380 exists to remove, re-introduced one level down.  ``now`` is injected
    rather than slept for.
    """
    import time

    root = tmp_path / "repo"
    branch = _amend_after_publishing(root)
    ahead = ca.commit_strand(branch, root=root)
    aged = int(time.time()) + (ca.CARRY_MAX_AGE_MIN + 1) * 60
    assert ca.strand_kind(ahead, root=root, now=aged) == ca.STRAND


def test_a_commit_touching_work_is_a_strand_whatever_its_message(tmp_path):
    """The surface bound.  A carry is defined by what it *touches*, not by
    what its commit message calls itself — otherwise the exemption is
    claimable by writing the right subject line."""
    import subprocess

    root = tmp_path / "repo"
    branch = _silent_repo(root, published=3, total=3)
    (root / "eval").mkdir(exist_ok=True)
    (root / "eval" / "thing.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(("git", "add", "-A"), cwd=str(root), check=True,
                   capture_output=True)
    subprocess.run(("git", "commit", "-qm", "[auto] D-378 bookkeeping"),
                   cwd=str(root), check=True, capture_output=True)
    ahead = ca.commit_strand(branch, root=root)
    assert ca.strand_kind(ahead, root=root) == ca.STRAND


def test_two_commits_ahead_are_a_strand_even_if_both_are_bookkeeping(tmp_path):
    """Rule 1 is the one that catches the failure the other two cannot: a
    cycle that rode the carry, committed its own bookkeeping and then died
    before pushing leaves two innocent-looking commits and no work at all."""
    import subprocess

    root = tmp_path / "repo"
    branch = _amend_after_publishing(root)
    target = root / "journal" / "2026-08" / "01-12-c2.md"
    target.write_text(target.read_text(encoding="utf-8") + "\n- again\n",
                      encoding="utf-8")
    subprocess.run(("git", "add", "-A"), cwd=str(root), check=True,
                   capture_output=True)
    subprocess.run(("git", "commit", "-qm", "[auto] more bookkeeping"),
                   cwd=str(root), check=True, capture_output=True)
    ahead = ca.commit_strand(branch, root=root)
    assert len(ahead) == 2
    assert ca.strand_kind(ahead, root=root) == ca.STRAND


def test_the_carry_does_not_raise_the_subcommand(monkeypatch, capsys):
    """The wiring half — the finding is the rc, so the rc is what is asserted.

    Mirrors ``test_a_commit_strand_alone_raises_the_subcommand``: the journal
    census is silenced so the verdict can only have come from the commit half.
    """
    monkeypatch.setattr(ca, "stranded", lambda *a, **k: ())
    monkeypatch.setattr(ca, "unwatched_strandings", lambda *a, **k: ())
    monkeypatch.setattr(ca, "commit_strand", lambda *a, **k: ("deadbeef",))
    monkeypatch.setattr(ca, "strand_kind", lambda *a, **k: ca.CARRY)
    monkeypatch.setattr(ca, "commit_strand_report", lambda *a, **k: "  carry")
    assert ca.main(["stranded", "autoresearch/probe"]) == 0
    capsys.readouterr()


def test_the_carry_and_the_strand_do_not_render_alike(tmp_path):
    """A verdict the caller cannot act on differently is a verdict that does
    not exist.  The carry block must forbid the push the strand block
    demands."""
    root = tmp_path / "repo"
    branch = _amend_after_publishing(root)
    ahead = ca.commit_strand(branch, root=root)
    carry = ca.commit_strand_report(ahead, root=root)
    import time
    aged = int(time.time()) + (ca.CARRY_MAX_AGE_MIN + 1) * 60
    strand = ca.commit_strand_report(ahead, root=root, now=aged)
    assert "do NOT push it alone" in carry and "none owed" in carry
    assert "repair: push this branch" in strand
    assert "do NOT push it alone" not in strand


def test_an_unknown_commit_strand_is_not_a_finding(monkeypatch, capsys):
    """rc=1 must stay *clearable* — it is a gate, not an advisory (D-044).

    ``None`` means git could not answer, and no push clears that, so raising on
    it would put an unclearable finding in REVIEW's ``&&`` chain.  Reported in
    the text, absent from the verdict.
    """
    monkeypatch.setattr(ca, "stranded", lambda *a, **k: ())
    monkeypatch.setattr(ca, "unwatched_strandings", lambda *a, **k: ())
    monkeypatch.setattr(ca, "commit_strand", lambda *a, **k: None)
    assert ca.main(["stranded", "autoresearch/probe"]) == 0
    assert "UNKNOWN" in capsys.readouterr().out


def test_the_stranded_subcommand_exits_non_zero_on_a_finding(capsys):
    """REVIEW runs this under ``&&``; a finding a caller must parse is a
    finding callers stop taking."""
    assert ca.main(["stranded", "autoresearch/does-not-exist-anywhere"]) == 0
    capsys.readouterr()


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


# --------------------------------------------------------------------------
# D-156 — the strand's second cost: the tree was never graded
# --------------------------------------------------------------------------

#: The control for :func:`ca.measurement`, established by hand before the
#: function existed.  The 18:00 cycle on 2026-08-09 stranded at ``156f9f9``,
#: stamped ``Metric: sandbox:pass=pending``; the 19:00 cycle that cleared it
#: pushed ``bd9f20d``, stamped ``sandbox:pass=2068/2068``.  Both answers were
#: written into 19:00's journal and are true independently of this instrument.
UNGRADED_STRAND = "journal/2026-08/09-18-the-last-scene-cannot-be-walked.md"
GRADED_STRAND = "journal/2026-08/09-19-the-fourth-strand-and-the-scar-the-repair-cannot-reach.md"


def _cycle_at(path: str) -> ca.Cycle:
    cycle = ca.parse(Path(ca.REPO_ROOT) / path)
    assert cycle is not None, f"{path} is not a cycle report"
    return cycle


def test_the_known_ungraded_strand_is_reproduced():
    """The hand-established case: 18:00 committed a tree no suite ever read."""
    assert ca.measurement(_cycle_at(UNGRADED_STRAND)) == "PENDING"


def test_the_cycle_that_cleared_it_reads_graded():
    """The other half of the control — without it "PENDING" could be constant."""
    assert ca.measurement(_cycle_at(GRADED_STRAND)) == ca.GRADED


def test_a_journal_git_has_never_seen_is_uncommitted(tmp_path):
    """Not the same finding as PENDING: this one needs a commit, not a suite."""
    path = _journal(tmp_path, "x.md", "2026-08-09 20:00", f"`{BRANCH}`", "yes")
    cycle = ca.parse(path, root=tmp_path)
    assert cycle is not None and ca.measurement(cycle, root=tmp_path) == "UNCOMMITTED"


def test_a_commit_with_no_metric_line_reads_unstated(scratch_repo):
    """A cycle that stated no grade is distinguishable from one that owed one."""
    repo, cycles = scratch_repo
    assert ca.measurement(cycles["silent.md"], root=repo) == "UNSTATED"


def test_a_qual_metric_counts_as_graded(scratch_repo):
    """``qual:doc-only`` is a stated verification surface, not a missing one.

    The predicate is "did the cycle grade its tree", not "did it run pytest" —
    reading a doc-only cycle as ungraded would put a finding on every cycle
    that correctly had no suite to run.
    """
    repo, cycles = scratch_repo
    assert ca.measurement(cycles["doc.md"], root=repo) == ca.GRADED


def test_the_grade_belongs_to_the_cycle_that_wrote_the_file(scratch_repo):
    """A later commit editing an old journal must not relabel it.

    ``--diff-filter=A``'s reason.  The 09:00 correction on 2026-08-09 was
    exactly this shape: one cycle amending a predecessor's journal.  Keying on
    the newest touching commit would have credited the predecessor with the
    corrector's grade.
    """
    repo, cycles = scratch_repo
    assert ca.measurement(cycles["pending.md"], root=repo) == "PENDING", (
        "the graded commit that edited this file later must not overwrite its grade"
    )


def test_every_verdict_is_in_the_enum(scratch_repo):
    """The vocabulary is the constant, not four string literals in a renderer."""
    repo, cycles = scratch_repo
    seen = {ca.measurement(c, root=repo) for c in cycles.values()}
    assert seen <= set(ca.MEASUREMENTS)
    assert len(seen) >= 3, "a vocabulary exercised by one value is not a vocabulary"


def test_strand_report_carries_the_ungraded_verdict():
    """D-156's ask: the reading REVIEW takes must say the tree was unmeasured."""
    a = ca.Cycle(path="a.md", minute=1, stamp="2026-08-09 18:00",
                 branch=BRANCH, tsv_claim="yes")
    text = ca.strand_report((a,), (), {"a.md": "PENDING"})
    assert "ungraded (PENDING)" in text
    assert "budget a suite run" in text


def test_a_graded_strand_gets_no_budget_line():
    """Only a push is owed when the tree was measured — say so by staying quiet."""
    a = ca.Cycle(path="a.md", minute=1, stamp="2026-08-09 18:00",
                 branch=BRANCH, tsv_claim="yes")
    text = ca.strand_report((a,), (), {"a.md": ca.GRADED})
    assert "ungraded" not in text and "budget a suite run" not in text


def test_the_renderer_invents_no_grade_it_was_not_given():
    """No measurements supplied ⇒ the old wording, not a fabricated ``GRADED``."""
    a = ca.Cycle(path="a.md", minute=1, stamp="2026-08-09 18:00",
                 branch=BRANCH, tsv_claim="yes")
    assert "ungraded" not in ca.strand_report((a,), ())


def test_the_census_publishes_the_ungraded_count():
    """A count with no reader is the shape this module exists to refuse."""
    counts = ca.census(BRANCH)
    assert counts["stranded_ungraded"] <= counts["stranded"]
    assert f"of which never graded: {counts['stranded_ungraded']}" in ca.report(BRANCH)


# --------------------------------------------------------------------------
# claim_support: the same fact, read while it is still repairable
# --------------------------------------------------------------------------


def _claim_repo(root: Path, claim: str, row: str | None, *, commit_row: bool) -> None:
    """A one-cycle repo, optionally carrying a TSV row, optionally committed.

    ``commit_row`` is the axis under test rather than a detail: the reading has
    to give the same answer on both sides of ``git add``, which is exactly the
    property :mod:`tsv_timestamp`'s ``check`` does not have.
    """
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(root),
                   check=True, capture_output=True)
    (root / "journal").mkdir()
    _journal(root / "journal", "c.md", "2026-08-09 18:00", f"`{BRANCH}`", claim)
    _commit(root, "[auto] a cycle\n\nMetric: sandbox:pass=1/1\n")
    if row is None:
        return
    (root / "results").mkdir()
    tsv = ca.tsv_path(BRANCH, root=root)
    tsv.write_text(f"{row}\tdeadbee\tqual:doc-only\tin_progress\ta row\n",
                   encoding="utf-8")
    if commit_row:
        _commit(root, "[auto] tsv row\n")


def test_the_claim_is_unsupported_while_the_cycle_can_still_fix_it(tmp_path):
    """The 09:00/11:00/18:00 signature, reproduced before the push instead of after.

    The push gate already consumes this population and is not at fault — those
    three cycles never reached it.  Read at the write site, the same tree is red.
    """
    _claim_repo(tmp_path, "yes", None, commit_row=False)
    assert ca.claim_support(BRANCH, root=tmp_path) == "UNSUPPORTED"
    assert ca.claim_support(BRANCH, root=tmp_path) in ca.finding_grades()


def test_an_uncommitted_row_already_supports_the_claim(tmp_path):
    """4a runs before ``git add``; a reading that needed the commit would be useless."""
    _claim_repo(tmp_path, "yes", "2026-08-09T18:07:00", commit_row=False)
    assert ca.claim_support(BRANCH, root=tmp_path) == "HONOURED"


def test_the_reading_does_not_go_vacuous_once_the_row_is_committed(tmp_path):
    """Why this one may live in the push gate's ``&&`` chain and ``tsv_timestamp
    check`` may not: that guard grades only *uncommitted* rows, so ``git add``
    silences it and the constitution has to place it by hand.  Same tree, both
    sides of the commit, same answer."""
    _claim_repo(tmp_path, "yes", "2026-08-09T18:07:00", commit_row=True)
    assert ca.claim_support(BRANCH, root=tmp_path) == "HONOURED"


def test_pending_states_nothing_and_is_therefore_not_a_finding(tmp_path):
    """The write-site repair: a cycle that dies before the append leaves no scar.

    Deliberately *not* graded as an over-claim.  Making the honest direction
    expensive is how a guard teaches cycles to write ``yes`` and hope.
    """
    _claim_repo(tmp_path, ca.PENDING_CLAIM, None, commit_row=False)
    grade = ca.claim_support(BRANCH, root=tmp_path)
    assert grade == "UNPARSED" and grade not in ca.finding_grades()


def test_the_line_is_emitted_from_the_row_count_not_from_intent(tmp_path):
    """D-154's move applied to the claim: the word comes from counting, not predicting."""
    _claim_repo(tmp_path, ca.PENDING_CLAIM, None, commit_row=False)
    assert ca.claim_line(BRANCH, root=tmp_path) == "- TSV row appended: no"
    (tmp_path / "results").mkdir()
    ca.tsv_path(BRANCH, root=tmp_path).write_text(
        "2026-08-09T18:07:00\tdeadbee\tqual:doc-only\tin_progress\ta row\n",
        encoding="utf-8",
    )
    assert ca.claim_line(BRANCH, root=tmp_path) == "- TSV row appended: yes"


def test_naming_the_cycle_beats_inferring_it_from_position(tmp_path):
    """D-110's repair a second time — ``newest`` is only the running cycle after 4a."""
    _claim_repo(tmp_path, "yes", None, commit_row=False)
    assert ca.claim_support(BRANCH, root=tmp_path,
                            cycle_path="journal/c.md") == "UNSUPPORTED"
    assert ca.claim_support(BRANCH, root=tmp_path,
                            cycle_path="journal/absent.md") == ca.NO_CYCLE


def test_no_journal_is_not_a_clean_bill(tmp_path):
    """D-107: an empty population must not read as a pass."""
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(tmp_path),
                   check=True, capture_output=True)
    grade = ca.claim_support(BRANCH, root=tmp_path)
    assert grade == ca.NO_CYCLE and grade not in ca.finding_grades()


def test_the_cli_exits_non_zero_only_on_the_over_claim(tmp_path, capsys, monkeypatch):
    """The gate contract: ``&&`` in the push line means rc is the whole interface.

    The in-flight hour is stated rather than inherited (D-202).  This test used
    to read whatever hour the *test runner's* own cycle was in, which was
    harmless only while nothing consulted it -- and would now make the rc depend
    on what time of day the suite ran.
    """
    monkeypatch.setattr(ca, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(ca, "JOURNAL_DIR", tmp_path / "journal")
    monkeypatch.setattr(ca, "inflight_hour", lambda **kw: CLAIM_HOUR)
    _claim_repo(tmp_path, "yes", None, commit_row=False)
    assert ca.main(["claim", BRANCH]) == 1
    assert "UNSUPPORTED" in capsys.readouterr().out


# --- D-202: the reading has to know *whose* claim it is grading -------------
#
# `_claim_rows`'s fallback to `ordered[-1]` is correct exactly when 4a has
# already run.  The 2026-08-11 20:00 cycle called `claim` before writing its
# own 4a, so the newest journal was 19:00's -- and the CLI announced it as "the
# in-flight cycle's".  Both directions are pinned: the misattribution must go
# rc=2, and the correctly-attributed reading must keep grading exactly as it did.

CLAIM_HOUR = "2026-08-09T18"
"""The hour `_claim_repo`'s single journal is stamped in."""


def test_a_newer_hour_than_the_newest_journal_means_this_cycle_has_no_4a(tmp_path):
    """The 20:00 signature: running at 19:xx+, newest journal is 18:00's."""
    _claim_repo(tmp_path, "yes", None, commit_row=False)
    assert ca.identification(BRANCH, root=tmp_path,
                             hour="2026-08-09T19") == ca.NO_INFLIGHT_JOURNAL
    assert ca.claim_support(BRANCH, root=tmp_path,
                            hour="2026-08-09T19") == ca.NO_INFLIGHT_JOURNAL


def test_the_matching_hour_grades_exactly_as_before(tmp_path):
    """The guard must not change the verdict on the reading it was added to protect."""
    _claim_repo(tmp_path, "yes", None, commit_row=False)
    assert ca.identification(BRANCH, root=tmp_path, hour=CLAIM_HOUR) == ca.IDENTIFIED
    assert ca.claim_support(BRANCH, root=tmp_path, hour=CLAIM_HOUR) == "UNSUPPORTED"
    assert ca.claim_line(BRANCH, root=tmp_path,
                         hour=CLAIM_HOUR) == "- TSV row appended: no"


def test_the_refusal_cannot_be_pasted(tmp_path):
    """The failure mode was a *paste*, so the refusal must not be a valid line.

    A warning printed next to a usable ``yes`` would have been read the same way
    the old output was: the operator copies the line, not the caveat above it.
    """
    _claim_repo(tmp_path, "yes", "2026-08-09T18:07:00", commit_row=False)
    line = ca.claim_line(BRANCH, root=tmp_path, hour="2026-08-09T19")
    assert line == ca.REFUSED_LINE
    assert "TSV row appended" not in line


def test_an_unreadable_inflight_hour_fails_open(tmp_path):
    """No run in flight is not evidence of the defect -- manual runs must work."""
    _claim_repo(tmp_path, "yes", None, commit_row=False)
    assert ca.identification(BRANCH, root=tmp_path) == ca.INFLIGHT_UNKNOWN
    assert ca.claim_support(BRANCH, root=tmp_path) == "UNSUPPORTED"


def test_naming_the_cycle_outright_beats_the_hour(tmp_path):
    """``cycle_path`` is D-110's repair; the new guard must not override it."""
    _claim_repo(tmp_path, "yes", None, commit_row=False)
    assert ca.identification(BRANCH, root=tmp_path, cycle_path="journal/c.md",
                             hour="2026-08-09T23") == ca.IDENTIFIED
    assert ca.claim_support(BRANCH, root=tmp_path, cycle_path="journal/c.md",
                            hour="2026-08-09T23") == "UNSUPPORTED"


def test_the_misattribution_is_not_the_over_claim_finding(tmp_path):
    """rc=2 vs rc=1: one is cleared by writing 4a, the other cannot be cleared.

    Folding it into :func:`finding_grades` would make the push gate refuse for a
    reason the cycle can fix in ten seconds, and would put a clearable caveat in
    the same bucket as a permanent scar -- D-199's split, which exists because a
    check that cannot be cleared is one that gets muted (D-044).
    """
    assert ca.NO_INFLIGHT_JOURNAL not in ca.finding_grades()
    assert ca.IDENTIFIED not in ca.finding_grades()
    assert ca.INFLIGHT_UNKNOWN not in ca.finding_grades()


def test_the_cli_exits_two_when_asked_before_4a(tmp_path, capsys, monkeypatch):
    """rc=2 is the "you asked too early" channel, and it names the other cycle."""
    monkeypatch.setattr(ca, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(ca, "JOURNAL_DIR", tmp_path / "journal")
    monkeypatch.setattr(ca, "inflight_hour", lambda **kw: "2026-08-09T19")
    _claim_repo(tmp_path, "yes", None, commit_row=False)
    assert ca.main(["claim", BRANCH]) == 2
    out = capsys.readouterr().out
    assert "NO_INFLIGHT_JOURNAL" in out
    assert "journal/c.md" in out and "previous cycle" in out
    assert "- TSV row appended: yes" not in out


def test_the_hour_key_matches_the_wrapper_spelling():
    """``Run.hour`` is ``started[:13]``; the journal stamp has a space, not a T."""
    from eval.mppi_sandbox import cycle_wallclock as cw

    run = cw.Run(started="2026-08-11T21:00:01+09:00", ended="", rc=None)
    assert ca._hour_key("2026-08-11 21:00") == run.hour


# --------------------------------------------------------------------------
# D-230: the grades a red run saw, carried by the failure that saw them
# --------------------------------------------------------------------------


def test_the_digest_names_every_cycle_carrying_a_finding(tmp_path):
    """Unrestricted, the listing is the population that moved between CI and here."""
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=3, total=3, claim="yes")
    text = ca.divergence_digest(branch, root=root)
    for i in range(3):
        assert f"journal/2026-08/01-{10 + i:02d}-c{i}.md" in text
    assert text.count("UNSUPPORTED   ") == 3


def test_the_digest_restricted_to_paths_says_nothing_about_the_others(tmp_path):
    """The controls' assertion is about three cycles; it must not dump 221."""
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=3, total=3, claim="yes")
    only = ("journal/2026-08/01-11-c1.md",)
    text = ca.divergence_digest(branch, root=root, paths=only)
    assert only[0] in text
    assert "01-10-c0.md" not in text
    assert "01-12-c2.md" not in text


def test_the_digest_carries_the_census_whether_or_not_rows_are_listed(tmp_path):
    """A clean population still reports its counts — the digest never invents rows.

    The honest direction has to stay cheap to emit (D-162's rule, applied to a
    diagnostic): if a green population produced an empty string, the digest
    would only ever be seen attached to bad news and nobody could calibrate it.
    """
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=3, total=3)  # claims "no" — no findings
    text = ca.divergence_digest(branch, root=root)
    assert "census: " in text
    assert "CONSISTENT_NO=3" in text
    assert "c0.md" not in text


def test_both_live_assertions_still_carry_the_digest():
    """Pinned by reading this file, not by remembering to keep it wired.

    The two assertions are the only place the CI-only grades are observable
    (D-230).  Dropping the message would leave them true statements that throw
    away the one reading nothing local can reproduce, and a bare ``assert 183 >
    38 * 5`` is exactly what that regression looks like.
    """
    src = Path(__file__).read_text(encoding="utf-8")
    for anchor in (
        "instrument stopped seeing hand-established cases",
        'counts["HONOURED"] > counts["UNSUPPORTED"] * 5',
    ):
        assert anchor in src, f"assertion moved: {anchor}"
        after = src.split(anchor, 1)[1][:220]
        assert "divergence_digest" in after, f"digest dropped from: {anchor}"


# --------------------------------------------------------------------------
# D-231 — the blame clock names its zone
# --------------------------------------------------------------------------


def _commit_at(cwd: Path, message: str, when: str) -> None:
    """Commit with both author and committer time pinned to ``when``."""
    subprocess.run(["git", "add", "-A"], cwd=str(cwd), check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", message],
        cwd=str(cwd), check=True, capture_output=True,
        env={**os.environ, "GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when},
    )


@pytest.fixture
def dated_row_repo(tmp_path: Path):
    """A repo with one TSV row committed at a known instant.

    The instant is chosen so UTC and KST disagree about **which hour it is**:
    12:30Z is 21:30 the same day in Seoul.  A reader that takes the ambient zone
    therefore reports a different hour on a GitHub runner than on the developer's
    machine, and this fixture is the smallest thing that can tell them apart.
    """
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(tmp_path),
                   check=True, capture_output=True)
    (tmp_path / "results").mkdir()
    tsv = tmp_path / "results" / "p3-zone.tsv"
    tsv.write_text(
        "timestamp\tcommit\tmetric\tstatus\tdescription\n"
        "2026-08-06T21:30:00+09:00\tdeadbee\tqual:doc-only\tin_progress\ta row\n",
        encoding="utf-8",
    )
    _commit_at(tmp_path, "[auto] append a row", "2026-08-06T12:30:00+00:00")
    return tmp_path


def test_blame_dating_names_kst_rather_than_the_ambient_zone(dated_row_repo):
    """D-231 — the whole of the CI/local census divergence, in one row.

    ``git blame --line-porcelain`` reports ``committer-time`` as a **raw
    epoch**, so the ``TZ=Asia/Seoul`` pinned on the subprocess never reaches it:
    that variable steers git's own date *formatting*, and this field is not
    formatted.  The conversion happens in Python, and for four cycles it happened
    through ``time.localtime`` — KST here, **UTC on the runner**.  Every row
    landed nine hours early in CI and was reassigned to whichever cycle then
    preceded it, which is why CI graded this branch 186/37 while every local
    reading of a byte-identical tree graded it 206/17 on the same 233 cycles and
    230 rows.  D-230 excluded timezone by testing :func:`_commit_minute`, which
    *is* pinned; the unpinned twin was never the one measured.
    """
    expected = ca._minutes("2026-08-06", "21", "30")
    zones = ("Asia/Seoul", "UTC", "America/New_York")
    seen = {}
    saved = os.environ.get("TZ")
    try:
        for zone in zones:
            os.environ["TZ"] = zone
            time.tzset()
            seen[zone] = ca.tsv_rows("autoresearch/p3-zone", root=dated_row_repo)
    finally:
        if saved is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = saved
        time.tzset()

    # Asserted as one total equality rather than a per-zone loop: dict equality
    # pins the key set and the values together, so there is no iteration count
    # for the claim to be vacuous at.  A loop here would be the exact shape
    # `loop_reach` exists to measure the reach of (2026-08-06 18:00) — and the
    # cheapest answer to "did the body run?" is an assertion that has no body.
    assert seen == {z: ((expected, True),) for z in zones}


def test_the_blame_readers_share_one_statement_of_the_zone(dated_row_repo):
    """Two modules parse this same field; only one of them was ever right.

    :func:`tsv_timestamp._blame_times` has always converted with an explicit
    ``KST``.  ``cycle_artifacts`` respelled the conversion and got it wrong, and
    the two agreed on the developer's machine for as long as the machine was in
    Seoul — D-047's shape, where a second statement of one fact drifts silently.
    Pinning the *identity* of the constant is what stops a future edit from
    reintroducing a local copy that starts out equal.
    """
    from eval.mppi_sandbox import tsv_timestamp as tt

    assert ca._KST is tt.KST
    assert ca._KST.utcoffset(None) == timedelta(hours=9)


def test_discharge_push_is_recognised_only_when_the_strand_graded_honest(tmp_path):
    """Q-169: rc=2 on a strand-discharge push is ``&&``'s side effect, not the gate's intent.

    ``_silent_repo`` leaves ``01-12-c2`` stranded and honest — exactly the
    2026-08-19 08:00 shape, where the push carried a finished previous cycle and
    ``claim`` had no 4a to grade.  Making ``01-12-c2`` over-claim a TSV row it
    never appended moves it out of ``unwatched_strandings`` and the exemption
    must vanish with it: an over-claiming strand is the rc=1 case first.
    """
    root = tmp_path / "repo"
    branch = _silent_repo(root, published=1, total=3)
    newest = "journal/2026-08/01-12-c2.md"
    off_hour = "2026-08-01T13"

    assert ca.identification(branch, root=root, hour=off_hour) == ca.NO_INFLIGHT_JOURNAL
    found = ca.discharge_push(branch, root=root, hour=off_hour)
    assert found is not None and found.path == newest

    # In flight: the newest journal *is* this cycle's 4a, so there is a real
    # claim to grade and no discharge to exempt.
    assert ca.discharge_push(branch, root=root, hour="2026-08-01T12") is None

    # Over-claiming strand: still stranded, no longer honest, no exemption.
    p = root / newest
    p.write_text(
        p.read_text(encoding="utf-8").replace(
            "TSV row appended: no", "TSV row appended: yes"
        ),
        encoding="utf-8",
    )
    assert newest in {c.path for c in ca.unsupported(branch, root=root)}
    assert ca.discharge_push(branch, root=root, hour=off_hour) is None
