"""The push gate reads the journal's claims, and reads only the ones it ships.

:mod:`cycle_artifacts` has graded unsupported ``TSV row appended: yes`` claims
since D-105.  On 2026-08-07 the 01:00 cycle produced one, was graded
``UNSUPPORTED rows=0`` correctly and on time, and the finding sat unread for an
hour — the process that would have run the suite was the process that had died.
Wiring the reading into :func:`push_preflight.check` moves it to the one place
every cycle must pass through.

The scope is the part that needed measuring, not arguing.  Refusing on
:func:`cycle_artifacts.unsupported` outright refuses **on arrival**: this branch
carries four confirmed claims and all four are already on ``origin``.  So the
gate reads the *frontier* — claims not yet published — and the two tests that
matter here are the pair that separates those populations:
:func:`test_refuses_an_unpublished_unsupported_claim` and
:func:`test_clears_when_the_same_offence_is_already_published`.  One offence,
one bit of difference, opposite verdicts.  Without the second, the first is
equally consistent with a gate that refuses everything — which is the failure
D-075/D-076/D-081 each shipped a version of, and which here would have been
*guaranteed* by the obvious wiring.

The third test is the one that makes the refusal honest: appending the row
clears it.  That is not a hypothetical repair — it is exactly what the 02:00
cycle did by hand an hour after the fact, and under this gate it is what would
have licensed the push at the time.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import cycle_artifacts as ca
from eval.mppi_sandbox import guard_direction as gd
from eval.mppi_sandbox import push_preflight as pp
from eval.mppi_sandbox import tree_provenance as tp


@pytest.fixture
def cycles_repo(tmp_path: Path) -> Path:
    """The probe fixture: four dated cycles on ``autoresearch/probe``, no rows.

    Reused rather than rebuilt.  Its dates are pinned through ``git commit
    --date``, which is what lets :mod:`cycle_artifacts`' two keys disagree at
    all; a fixture written here from scratch would collapse them onto one
    minute and could not construct the case the module is about.
    """
    root = tmp_path / "repo"
    gd.build_cycle_artifacts_repo(root)
    # The builder checks out ``probe``, not ``autoresearch/probe``: its own
    # consumer passes the branch in explicitly and never asks git.  The gate
    # *derives* the branch from ``HEAD``, so the checkout name has to match what
    # the journals declare — see ``test_a_name_mismatch_grades_nothing``.
    gd._git(root, "branch", "-M", gd.CA_BRANCH)
    return root


def _receipt(root: Path, name: str = "receipt.json") -> Path:
    """A green receipt describing *root* exactly as it stands right now."""
    st = tp.stamp(root)
    path = root / name
    path.write_text(
        pp.Receipt(
            head=st.head,
            worktree_fingerprint=st.worktree_fingerprint,
            committed_fingerprint=st.committed_fingerprint,
            returncode=0,
            counts={"passed": 9, "skipped": 1},
            command=("python3", "-m", "pytest", "-q"),
        ).to_json()
    )
    return path


def _publish(root: Path) -> None:
    """Point ``origin/<branch>`` at ``HEAD`` — the branch is now on the remote."""
    gd._git(root, "update-ref", f"refs/remotes/origin/{gd.CA_BRANCH}", "HEAD")


def _append_row(root: Path) -> None:
    """Discharge the claim the way a cycle actually discharges it."""
    sha = gd._git(root, "rev-parse", "--short", "HEAD").strip()
    tsv = root / "results" / "probe.tsv"
    with tsv.open("a", encoding="utf-8") as fh:
        fh.write(f"2026-08-01T11:30:00+09:00\t{sha}\tqual:doc-only\tkeep\trow\n")
    gd._git(root, "add", "results/probe.tsv")
    gd._git(root, "commit", "-qm", "TSV row", when="2026-08-01T11:30:00+09:00")


# --- the discriminating pair -------------------------------------------------


def test_refuses_an_unpublished_unsupported_claim(cycles_repo: Path):
    gd._ca_offend(cycles_repo, gd.CA_PLAIN)
    v = pp.check(_receipt(cycles_repo), root=cycles_repo, declared={})
    assert v.verdict == pp.UNSUPPORTED_CLAIM, v.describe()
    assert not v.ok
    assert gd.CA_PLAIN in v.detail, "a refusal must name the claim it refuses"


def test_clears_when_the_same_offence_is_already_published(cycles_repo: Path):
    """The scope rule, executed.

    Identical offence, identical tree; the only difference is that
    ``origin/<branch>`` already carries the journal.  A published claim is not
    repairable by the cycle now pushing, and refusing on it would make the gate
    uncrossable — which, measured on the real branch, is what an unscoped gate
    would have been from its first commit (4 confirmed, 4 published).
    """
    gd._ca_offend(cycles_repo, gd.CA_PLAIN)
    _publish(cycles_repo)
    v = pp.check(_receipt(cycles_repo), root=cycles_repo, declared={})
    assert v.verdict == pp.GREEN, v.describe()


# --- the refusal is repairable, and the repair is the one that was performed --


def test_appending_the_row_clears_the_refusal(cycles_repo: Path):
    gd._ca_offend(cycles_repo, gd.CA_PLAIN)
    assert (
        pp.check(_receipt(cycles_repo, "before.json"), root=cycles_repo,
                 declared={}).verdict
        == pp.UNSUPPORTED_CLAIM
    )
    _append_row(cycles_repo)
    v = pp.check(_receipt(cycles_repo, "after.json"), root=cycles_repo, declared={})
    assert v.verdict == pp.GREEN, v.describe()


# --- the honest cycle is not taxed -------------------------------------------


def test_an_honest_branch_reaches_green(cycles_repo: Path):
    """No offence: every journal claims ``no`` and there is no row to want.

    Without this the three tests above cannot distinguish "reads the claims"
    from "refuses whenever a journal exists".
    """
    v = pp.check(_receipt(cycles_repo), root=cycles_repo, declared={})
    assert v.verdict == pp.GREEN, v.describe()


def test_masked_offence_is_not_refused(cycles_repo: Path):
    """The gate inherits the two-key intersection rather than restating it.

    ``CA_MASKED`` claims a row and one key reads it honoured, so
    :func:`cycle_artifacts.unsupported` publishes nothing — and the gate must
    publish nothing either.  This is the test that would fail if the frontier
    filter had been written as its own grading pass: a second statement of the
    rule is free to be stricter than the first, and D-045/D-047 are both what
    happens when it drifts.
    """
    gd._ca_offend(cycles_repo, gd.CA_MASKED)
    assert ca.unsupported(gd.CA_BRANCH, root=cycles_repo) == ()
    v = pp.check(_receipt(cycles_repo), root=cycles_repo, declared={})
    assert v.verdict == pp.GREEN, v.describe()


# --- the population is inherited, not recomputed ------------------------------


def test_frontier_is_a_subset_of_the_graded_population(cycles_repo: Path):
    gd._ca_offend(cycles_repo, gd.CA_PLAIN)
    flagged = {c.path for c in ca.unsupported(gd.CA_BRANCH, root=cycles_repo)}
    frontier = {c.path for c in pp._unsupported_frontier(cycles_repo)}
    assert frontier <= flagged
    assert frontier, "the fixture must reach a non-empty frontier or this is vacuous"


def test_a_name_mismatch_grades_nothing(cycles_repo: Path):
    """The gate's reach is bounded by the checked-out branch **name**.

    The journals declare ``autoresearch/probe``; check out anything else and
    :func:`cycle_artifacts.cycles` returns nothing, so the gate is silent on an
    offence that is plainly there.  Pinned rather than fixed: the alternative is
    to grade journals whose declared branch is not the one being pushed, which
    would make every push from ``main`` answer for every branch's claims.  It is
    a fail-*open* edge, and an undocumented one is the kind this branch has
    spent six cycles paying for.
    """
    gd._ca_offend(cycles_repo, gd.CA_PLAIN)
    assert pp._unsupported_frontier(cycles_repo), "the offence is visible by name"
    gd._git(cycles_repo, "checkout", "-q", "-b", "some/other-name")
    assert pp._unsupported_frontier(cycles_repo) == ()


def test_a_branch_with_no_journals_is_silent(tmp_path: Path):
    """``main``, CI checkouts, detached HEAD — nothing to grade, nothing to say.

    The gate must not become a reason a non-cycle push cannot happen.
    """
    root = tmp_path / "plain"
    root.mkdir()
    gd._git(root, "init", "-q", "-b", "main")
    gd._git(root, "config", "user.email", "t@t")
    gd._git(root, "config", "user.name", "t")
    (root / "code.py").write_text("VALUE = 1\n")
    gd._git(root, "add", "-A")
    gd._git(root, "commit", "-qm", "init")
    assert pp._unsupported_frontier(root) == ()
