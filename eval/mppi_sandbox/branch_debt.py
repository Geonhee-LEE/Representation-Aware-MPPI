"""How large is the diff this branch is asking a human to review?

STATE.md of 2026-08-17 11:00 named the bottleneck precisely and then mis-measured
it by a factor of fifty.  It said PR #67 was "sixteen commits spanning a cost
critic, a verification surface, and a ``K`` axis", and proposed a scoping call on
that basis: does the branch close, and does the ``K`` work continue on a fresh
one?  The measurement is **840 commits, 656 files, +155,753 lines**, accumulated
since 2026-07-12 — the same day the last merge landed.

Both numbers were available to the same shell.  The prose one was carried
forward, cycle over cycle, by a chain of cycles that each read the previous
STATE and each had no cheap way to check it.  That is the failure this module
removes: a branch's review debt is a **reading**, not a remembered adjective.

Why the threshold is not a number this module chooses
-----------------------------------------------------

The obvious grade — "is this diff too big" — needs a line, and any line this
module invents is a line the next cycle can argue with.  So it does not invent
one.  It derives the comparison from the repository's own history: main is
squash-merged, so every commit on ``main`` *is* a diff that a human actually
reviewed and accepted.  The largest of them is the largest review this project
has ever been known to absorb.

The comparison is a **componentwise envelope, not one commit**, and the
distinction is worth keeping: measured 2026-08-17 the widest merge was 41 files
(``4220969``, the CBF-QP port) and the largest was +9,543 lines (``4ec669e``,
the Stage-1 RDSim port) — two different reviews.  So the envelope is generous by
construction; nothing has to have been reviewed at *both* extremes at once for
the branch to have to clear both.  The current branch is 16x that file count and
16x those insertions, which makes the claim structural rather than aesthetic —
not "this diff feels large" but *no diff of this size has ever been reviewed in
this repository, on either axis, even granting the most favourable pairing* —
and it re-derives itself as history grows, so it cannot go stale the way a
constant would.

``UNDECIDABLE`` is a verdict, not an exception
----------------------------------------------

:mod:`git_surface` recorded the shape of the bug this module is most likely to
grow: an instrument that reads git, gets nothing, and returns the nothing in the
vocabulary of a measurement.  ``actions/checkout@v4`` produces a clone with one
commit and no ``origin/main``; on that clone ``git rev-list main..HEAD`` is not
"zero commits of debt", it is *no answer*.  Every entry point here returns
:data:`UNDECIDABLE` when the base is unreachable, and the tests assert that
branch positively so CI cannot pass by being quiet.

Usage::

    python3 -m eval.mppi_sandbox.branch_debt report
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

#: The clone cannot see the base, so no debt statement is available.
UNDECIDABLE = "UNDECIDABLE"
#: The branch is no larger than a diff this repository has already merged.
WITHIN_PRECEDENT = "WITHIN_PRECEDENT"
#: The branch is larger than every diff this repository has ever merged.
BEYOND_PRECEDENT = "BEYOND_PRECEDENT"

#: How far back to walk ``main`` when deriving the precedent.  The repository has
#: 59 first-parent commits as of 2026-08-17; the cap bounds the walk's cost on a
#: repository that keeps growing, and is reported so a reader can tell a capped
#: walk from an exhaustive one.
PRECEDENT_WALK = 80


def _git(*args: str) -> str | None:
    """Run ``git`` and return stripped stdout, or ``None`` if it could not answer."""
    try:
        out = subprocess.run(
            ("git", *args),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def parse_shortstat(line: str) -> tuple[int, int]:
    """``(files, insertions)`` from a ``git diff --shortstat`` line.

    Split out so a caller measuring a *scoped* diff (``queue_debt``, which
    restricts the comparison to the paths a branch actually touched) reuses this
    parser instead of growing a second one that drifts from it.
    """
    files = insertions = 0
    for chunk in line.split(","):
        chunk = chunk.strip()
        head_token = chunk.split(" ", 1)[0]
        if not head_token.isdigit():
            continue
        if "file" in chunk:
            files = int(head_token)
        elif "insertion" in chunk:
            insertions = int(head_token)
    return files, insertions


def _shortstat(base: str, head: str) -> tuple[int, int] | None:
    """``(files, insertions)`` for ``base..head``, or ``None`` if undecidable."""
    line = _git("diff", "--shortstat", base, head)
    if line is None:
        return None
    return parse_shortstat(line)


@dataclass(frozen=True)
class Debt:
    """The review debt of one branch against one base."""

    verdict: str
    commits: int
    files: int
    insertions: int
    #: Componentwise envelope of every merge: the widest and the largest diff
    #: this repository has accepted, which need not be the same commit.
    precedent_files: int
    precedent_insertions: int
    #: How many merged commits the precedent was derived from.  ``0`` alongside a
    #: non-``UNDECIDABLE`` verdict would itself be a vacuity, so tests pin it.
    precedent_n: int

    @property
    def files_ratio(self) -> float:
        """Branch file count as a multiple of the precedent.  ``0.0`` if undecidable."""
        if self.precedent_files <= 0:
            return 0.0
        return self.files / self.precedent_files

    @property
    def insertions_ratio(self) -> float:
        """Branch insertions as a multiple of the precedent.  ``0.0`` if undecidable."""
        if self.precedent_insertions <= 0:
            return 0.0
        return self.insertions / self.precedent_insertions


def precedent(base: str = "main", walk: int = PRECEDENT_WALK) -> tuple[int, int, int]:
    """Componentwise envelope ``(files, insertions, n)`` ever merged into ``base``.

    ``main`` is squash-merged, so each first-parent commit is one accepted
    review.  The two maxima are taken independently and so may come from
    different commits — deliberately, since that makes the envelope the most
    favourable comparison available to the branch being graded.  Returns
    ``(0, 0, 0)`` when the clone cannot walk the base — the caller turns that
    into :data:`UNDECIDABLE` rather than into a zero.
    """
    listing = _git("rev-list", "--first-parent", f"--max-count={walk}", base)
    if not listing:
        return 0, 0, 0
    best_files = best_insertions = 0
    seen = 0
    for sha in listing.splitlines():
        sha = sha.strip()
        if not sha:
            continue
        measured = _shortstat(f"{sha}^", sha)
        if measured is None:
            # The root commit has no parent; it is not a review anyone did.
            continue
        seen += 1
        files, insertions = measured
        best_files = max(best_files, files)
        best_insertions = max(best_insertions, insertions)
    return best_files, best_insertions, seen


def grade(
    files: int,
    insertions: int,
    precedent_files: int,
    precedent_insertions: int,
    precedent_n: int,
) -> str:
    """Grade a measured diff against a measured envelope.

    Kept free of git so the boundary is testable without a repository.  An empty
    walk (``precedent_n == 0``) is :data:`UNDECIDABLE` and never
    ``WITHIN_PRECEDENT``: "no merge was large enough to exceed" and "no merge was
    looked at" are the two readings :mod:`git_surface` exists to keep apart, and
    the second one wearing the first one's verdict is the whole bug.
    """
    if precedent_n <= 0:
        return UNDECIDABLE
    if files > precedent_files or insertions > precedent_insertions:
        return BEYOND_PRECEDENT
    return WITHIN_PRECEDENT


def debt(base: str = "main", head: str = "HEAD") -> Debt:
    """Measure ``head``'s review debt against ``base``.

    The verdict is :data:`UNDECIDABLE` unless *every* input was measurable: the
    merge base, the diff, the commit count, and a non-empty precedent walk.  A
    partial reading published as a whole one is the failure
    :mod:`git_surface` names.
    """
    empty = Debt(UNDECIDABLE, 0, 0, 0, 0, 0, 0)

    fork = _git("merge-base", base, head)
    if not fork:
        return empty

    counted = _git("rev-list", "--count", f"{fork}..{head}")
    if counted is None or not counted.isdigit():
        return empty

    measured = _shortstat(fork, head)
    if measured is None:
        return empty
    files, insertions = measured

    best_files, best_insertions, seen = precedent(base)
    if seen == 0:
        return empty

    return Debt(
        verdict=grade(files, insertions, best_files, best_insertions, seen),
        commits=int(counted),
        files=files,
        insertions=insertions,
        precedent_files=best_files,
        precedent_insertions=best_insertions,
        precedent_n=seen,
    )


def report(base: str = "main", head: str = "HEAD") -> str:
    """One line a cycle can paste into STATE.md instead of an adjective."""
    d = debt(base, head)
    if d.verdict == UNDECIDABLE:
        return (
            "branch_debt — UNDECIDABLE: this clone cannot see "
            f"`{base}`, so no review-debt statement is available "
            "(shallow checkout, or the base ref is absent)."
        )
    return (
        f"branch_debt — {d.verdict}: {d.commits} commits, {d.files} files, "
        f"+{d.insertions} lines against `{base}`.  Largest diff ever merged "
        f"here: {d.precedent_files} files, +{d.precedent_insertions} "
        f"(over {d.precedent_n} merged commits) — "
        f"{d.files_ratio:.0f}x the files, {d.insertions_ratio:.0f}x the insertions."
    )


if __name__ == "__main__":  # pragma: no cover - CLI shim
    import sys

    print(report())
    sys.exit(0)
