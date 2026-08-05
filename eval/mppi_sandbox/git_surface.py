"""Whether *this clone* can answer a question about repository history.

The cycle that wrote this had the fast CI job reach a real verdict for the first
time in two days — and the verdict was ``failure``, ten tests, on a tree the
local push gate had certified ``GREEN`` forty minutes earlier.  Neither reading
was wrong.  :mod:`push_preflight` measures a **worktree**; the authority measures
a **checkout**, and ``actions/checkout@v4`` produces a clone with one commit, no
``origin/main`` and no ``refs/remotes/origin/autoresearch/*`` at all.

Every failure was an instrument reading git and getting a confident answer out of
a clone that had nothing to say:

``local_only_audit.branch_committed``
    Folds ``git log origin/main..<branch>`` over the autoresearch refs.  With no
    refs the fold is over the empty set, so it returns ``frozenset()`` — and
    ``derived_local_only`` subtracts that from the overwrite scan and concludes
    that ``docs/decisions.md`` and ``docs/deliberations.md``, the two paths the
    module's own docstring holds up as the durable-record contrast case, are
    local-only.  The derivation did not fail.  It **inverted**, and reported the
    inversion in the same shape as an answer.

``local_only_audit.staged_changes``
    ``git diff origin/main...HEAD`` exits 128 on a ref that does not exist.  This
    one at least crashed, which is why it is the *less* dangerous of the two.

So the defect is not that git was unavailable.  It is that **absence of evidence
was returned in the vocabulary of evidence** — an empty fold is spelled exactly
like a fold that found nothing, and no caller can tell them apart.  That is the
same category error this package has now found in three unrelated places, and it
is worth naming as one:

============================  ======================  =========================
instrument                    silence was read as     the verdict that fixes it
============================  ======================  =========================
``push_preflight``            "didn't fail" = passed  ``VACUOUS``
``ci_verdict`` (STATE #1)     cancelled = ``FAIL``    ``UNRUN``
this module                   no refs = no commits    ``NO_REMOTE_BRANCHES``
============================  ======================  =========================

The fix is therefore not a ``try/except`` at each call site — that converts a
wrong answer into a skipped test, which is the vacuity failure one layer up, and
this package has caught itself doing exactly that twice (D-075, D-081).  The fix
is a **probe with its own verdict**, asserted positively on both surfaces: on the
dev box a test asserts the real derivation, and on CI the *same* test asserts
that the probe fired and named the right reason.  Neither surface can pass by
being quiet.

Why not just deepen the CI checkout
-----------------------------------

``fetch-depth: 0`` plus an explicit remote-ref fetch would make CI answer these
questions, and that is a real option — but it makes the instrument's correctness
a property of a YAML file three directories away, which is the sort of coupling
that goes stale silently.  It also would not help any *other* clone: a fresh
``git clone --depth 1`` on the user's machine has the same blindness.  The probe
is where the knowledge belongs, and it is cheap.  Deepening the checkout remains
worth doing on top; it changes this module's verdict from
``NO_REMOTE_BRANCHES`` to ``DECIDABLE`` and the tests then assert the stronger
branch automatically, with nothing to update here.

Fast half: three ``git`` subprocesses, no simulation.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .tree_provenance import REPO_ROOT

#: The clone holds every ref the derivations need.  Only on this verdict may a
#: caller read a history-derived population as a measurement.
DECIDABLE = "DECIDABLE"

#: ``refs/remotes/origin/autoresearch/*`` is empty.  A fold over the branches is
#: a fold over nothing, and — this is the whole point — returns the same value it
#: would return if the branches existed and committed nothing.
NO_REMOTE_BRANCHES = "NO_REMOTE_BRANCHES"

#: ``origin/main`` is not resolvable, so no ``origin/main..X`` range parses.
NO_MERGE_BASE = "NO_MERGE_BASE"

#: A shallow clone.  Refs may resolve while the history behind them is truncated,
#: so a ``--since``/``--until`` window silently reads a sub-window.  Kept
#: distinct from the two above because the failure is *partial*, which is harder
#: to see than an empty answer and not the same defect.
SHALLOW = "SHALLOW"

#: Not a git work tree at all (an unpacked tarball, a vendored copy).
NOT_A_REPO = "NOT_A_REPO"

#: Every verdict, in decreasing order of how much the clone can answer.  Ordered
#: so :func:`worst` can fold a set of readings without a second registry.
VERDICTS: tuple[str, ...] = (
    DECIDABLE,
    SHALLOW,
    NO_MERGE_BASE,
    NO_REMOTE_BRANCHES,
    NOT_A_REPO,
)

#: The ref namespace the branch-derived populations fold over.  Read here rather
#: than typed at each call site, so a change to the branch-naming convention is
#: one edit and the probe cannot drift away from the thing it certifies.
BRANCH_NAMESPACE = "refs/remotes/origin/autoresearch"

#: The ref every merge-base comparison is taken against.
MAIN_REF = "origin/main"


class UndecidableSurface(RuntimeError):
    """This clone cannot answer the question that was asked.

    Carries the :data:`VERDICTS` member as :attr:`verdict` so a caller — and a
    test — can assert *which* blindness applied rather than merely that
    something went wrong.  An exception whose only content is "it failed" would
    put this module back in the position it exists to fix.
    """

    def __init__(self, verdict: str, detail: str = "") -> None:
        self.verdict = verdict
        suffix = f": {detail}" if detail else ""
        super().__init__(f"{verdict}{suffix}")


@dataclass(frozen=True)
class SurfaceReading:
    """What this clone holds.  All four fields are measured, none inferred."""

    verdict: str
    #: ``origin/main`` resolves to a commit.
    has_main: bool
    #: How many ``autoresearch/*`` remote refs the clone holds.
    branch_refs: int
    #: ``core.bare``-independent shallowness, read from ``git rev-parse``.
    shallow: bool

    @property
    def decidable(self) -> bool:
        return self.verdict == DECIDABLE


def _git(*args: str, root: Path | None = None) -> tuple[int, str]:
    """Run git, returning ``(returncode, stdout)``.  Never raises on non-zero.

    Deliberately *not* ``check=True``.  Every caller in this module is asking a
    question whose negative answer is informative, so turning a non-zero exit
    into an exception here would throw away the reading.
    """
    try:
        out = subprocess.run(
            ("git", *args),
            cwd=str(root or REPO_ROOT),
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return 127, ""
    return out.returncode, out.stdout


def reading(root: Path | None = None) -> SurfaceReading:
    """Probe the clone.  Three subprocesses, no caching.

    Uncached on purpose: a clone gains refs mid-run (a ``git fetch`` in a
    fixture, a test that creates a branch), and a cached "no refs" reading would
    outlive the condition it described.  Three subprocesses is not a cost worth
    introducing a staleness class for.
    """
    code, _ = _git("rev-parse", "--git-dir", root=root)
    if code != 0:
        return SurfaceReading(NOT_A_REPO, False, 0, False)

    _, shallow_out = _git("rev-parse", "--is-shallow-repository", root=root)
    shallow = shallow_out.strip() == "true"

    main_code, _ = _git("rev-parse", "--verify", "--quiet", f"{MAIN_REF}^{{commit}}",
                        root=root)
    has_main = main_code == 0

    _, refs_out = _git("for-each-ref", "--format=%(refname)", BRANCH_NAMESPACE,
                       root=root)
    branch_refs = len([r for r in refs_out.split("\n") if r.strip()])

    if branch_refs == 0:
        verdict = NO_REMOTE_BRANCHES
    elif not has_main:
        verdict = NO_MERGE_BASE
    elif shallow:
        verdict = SHALLOW
    else:
        verdict = DECIDABLE
    return SurfaceReading(verdict, has_main, branch_refs, shallow)


def worst(*readings: SurfaceReading) -> str:
    """The least-capable verdict among several readings.

    Folds over :data:`VERDICTS` order rather than a second precedence table, so
    adding a verdict to the tuple orders it here with no further edit — the
    D-047 rule (one statement of a registry) applied to this module's own.
    """
    if not readings:
        return DECIDABLE
    return max((r.verdict for r in readings), key=VERDICTS.index)


def require_branches(root: Path | None = None) -> SurfaceReading:
    """Assert the clone can answer a *branch-fold* question, or raise.

    Raises on :data:`NO_REMOTE_BRANCHES` and :data:`NOT_A_REPO`.  It does **not**
    raise on :data:`NO_MERGE_BASE`: a fold that only needs the refs themselves is
    answerable without ``origin/main``, and refusing it would be the
    over-broad-guard mistake in the other direction.  :data:`SHALLOW` also passes
    — the refs are there and the fold is real, merely possibly truncated — but
    the reading carries the flag so a caller that cares can say so.
    """
    r = reading(root)
    if r.verdict in (NO_REMOTE_BRANCHES, NOT_A_REPO):
        raise UndecidableSurface(
            r.verdict,
            f"{BRANCH_NAMESPACE} holds {r.branch_refs} refs in {root or REPO_ROOT}",
        )
    return r


def require_main(root: Path | None = None) -> SurfaceReading:
    """Assert the clone can answer a question ranged against ``origin/main``."""
    r = reading(root)
    if not r.has_main:
        raise UndecidableSurface(
            NOT_A_REPO if r.verdict == NOT_A_REPO else NO_MERGE_BASE,
            f"{MAIN_REF} does not resolve in {root or REPO_ROOT}",
        )
    return r


def main() -> int:
    r = reading()
    print(f"verdict     : {r.verdict}")
    print(f"origin/main : {'yes' if r.has_main else 'NO'}")
    print(f"branch refs : {r.branch_refs} under {BRANCH_NAMESPACE}")
    print(f"shallow     : {'yes' if r.shallow else 'no'}")
    if not r.decidable:
        print("\nhistory-derived populations are NOT measurable in this clone;")
        print("local_only_audit will raise UndecidableSurface rather than invert.")
    return 0 if r.decidable else 1


if __name__ == "__main__":
    raise SystemExit(main())
