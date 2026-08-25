"""Re-run the push gate with ``git push`` itself as the caller.

The failure this exists to make impossible
------------------------------------------

The constitution's push line is a chain, and the chain *is* the gate (D-082)::

    push_preflight check receipt.json && cycle_artifacts claim && git push ...

Its whole safety property is that ``check``'s exit code reaches the ``&&``.  On
2026-08-12 16:00 a cycle wanted the refusal to be readable in a long log and
wrote ``push_preflight check ... | tail -4 && ... && git push``.  A pipeline's
exit status is the status of its **last** command, so the chain saw ``tail``'s
``0``.  The gate printed ``STALE ... push refused`` and the push ran in the same
command, and the tree that landed on ``origin`` was never licensed.

Nothing was disabled and no rule was argued with.  Four characters added for
legibility replaced the exit code, and the gate went on printing exactly what it
was built to print while being read by nobody.  That is the specific shape of
the hole: **the gate's authority lived entirely in a number that the caller
composes**, and shell composition is not something a callee can police.

Why the fix is a hook rather than a stricter gate
-------------------------------------------------

The obvious repairs are the ones that do not work here:

* ``set -o pipefail`` in the constitution's snippet — correct, and it fixes the
  snippet.  It does not fix the *next* invocation, because a cycle composes its
  own shell commands ad hoc and the snippet is a suggestion in a prompt.
* Have ``check`` detect that its stdout is a pipe and refuse.  Under cron the
  executor's stdout is *always* a pipe, so this is red on every honest run —
  D-044's muted-check failure mode, bought at full price.
* Detect the pipe by inspecting the parent process.  Both sides of ``a | b`` are
  children of the same shell; there is nothing in ``/proc`` that distinguishes
  "my exit code is being read" from "my exit code is being discarded".

The property that actually fails is not "was the gate run" — the gate *was* run,
and it said no.  It is "**did the refusal reach the push**".  So the check has
to be made by something the pusher cannot compose around, and ``git`` already
offers exactly one such position: a ``pre-push`` hook runs as ``git push``'s own
callee, after the caller's shell has finished having opinions.  Piping the
outer command does not reach it, because by then the pipeline is over and
``git`` is the one calling.

The hook re-runs :func:`push_preflight.check` — the same function, on the same
tree, reaching the same verdict.  This is deliberate: the gate was never wrong,
so a *second, different* check would be new surface to get wrong.  The receipt
is recalled from :mod:`receipt_store` by the gate's own tree-match rule (see
:func:`licence_path`), so the hook needs no argument and cannot be pointed at a
friendlier file.

Honest scope: ``--no-verify`` still bypasses this
-------------------------------------------------

``git push --no-verify`` skips ``pre-push`` entirely, and this module makes no
attempt to detect that.  Stating the limit precisely is the point:

* the failure being repaired was a cycle that **believed it was gated** while
  the gate's answer was discarded by an unrelated formatting change;
* ``--no-verify`` is a cycle **saying out loud** that it is pushing ungated.  It
  appears verbatim in the command, in the journal, and in the cron log.

The first is invisible and was survivable for a whole cycle.  The second is a
decision with a name on it.  This hook converts the first into the second, and
that is the entire claim — not that pushing unlicensed became impossible, but
that it stopped being something a cycle can do by accident while reading its
own logs more comfortably.

The wiring is not automatic either
----------------------------------

``git`` only consults ``scripts/githooks`` once ``core.hooksPath`` points there,
and that is repository-local config which no commit can carry — a fresh clone
has the hook file and not the wiring.  So :func:`wiring` reports the state and
:func:`install` sets it, and ``status`` fails closed (rc=1) when unwired, so the
answer is a reading rather than an assumption.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import inert_surface as ins
from . import push_preflight as pp
from . import receipt_store as rs
from . import tree_provenance as tp

#: Only pushes that move a ref under this prefix are this hook's business.  The
#: executor is the sole author of these branches (constitution, "Push the
#: branch"), so the guarded population is exactly the population the push gate
#: was written for.  A human pushing ``main`` or a topic branch is not gated by
#: an instrument built to police the executor's own suite discipline.
GUARDED_PREFIX = "refs/heads/autoresearch/"

#: Where the hook script lives in the tree, relative to the repository root.
HOOKS_DIR = Path("scripts") / "githooks"

HOOK_NAME = "pre-push"

#: A deleted ref arrives with an all-zero local sha and ships no tree, so there
#: is nothing for a suite to have measured.
_DELETION_SHA_CHARS = "0"

ALLOW = "ALLOW"
REFUSE = "REFUSE"


@dataclass(frozen=True)
class Decision:
    """The hook's answer, carrying the reason it reached it."""

    outcome: str
    detail: str
    refs: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.outcome == ALLOW


def guarded_refs(stdin_text: str) -> tuple[str, ...]:
    """The ``autoresearch/*`` refs this push would move.

    ``git`` feeds ``pre-push`` one line per ref, ``<local-ref> <local-sha>
    <remote-ref> <remote-sha>``.  The **remote** ref is what decides membership:
    it is the name that will exist on ``origin``, which is what the queue and
    the review bandwidth are counted in.  A local branch pushed under a
    different remote name is judged by where it lands.
    """
    found: list[str] = []
    for line in stdin_text.splitlines():
        fields = line.split()
        if len(fields) != 4:
            continue
        _local_ref, local_sha, remote_ref, _remote_sha = fields
        if not local_sha.strip(_DELETION_SHA_CHARS):
            continue
        if remote_ref.startswith(GUARDED_PREFIX):
            found.append(remote_ref)
    return tuple(found)


def licence_path(root: Path | None = None) -> Path:
    """Which archived receipt to hand the gate for the tree in hand.

    The exact-fingerprint entry first, and if there is none, the store is
    searched for a receipt whose tree differs from this one **only on paths
    :mod:`inert_surface` has measured to be unreadable by the suite** — the
    admission :func:`push_preflight.tree_match` already grants, asked here with
    the same implementation so recall and gate cannot disagree.

    Why the search has to exist (D-237)
    -----------------------------------

    The first version of this function was one line — ``path_for(current
    fingerprint)`` — and it made the pin mechanism inert at the only gate that
    blocks a push.  The protocol *mandates* writes after the receipt: the 4b
    digest, the 4c snapshot, the TSV row — exactly the population
    :data:`inert_surface.POST_RECEIPT_WRITES` is built from, spelled there and
    deliberately not respelled here (a literal path in this docstring makes this
    module a *reader* of it and withdraws the pin, which is how the first draft
    of this paragraph cost the 4b one).  Every one of those writes moves the
    worktree fingerprint, so by the time ``git push`` runs the hook, the key has
    always changed and the archived receipt can never be found.  The 2026-08-13
    12:00 cycle held four freshly re-taken pins, watched ``check`` go **GREEN**
    on the drift they exempt, and was then refused by this hook with
    ``NO_RECEIPT`` — and paid a second 513 s suite to archive a receipt under
    the pushed tree's own fingerprint.  The pins bought nothing at the one place
    they were supposed to pay off.

    What the search does *not* weaken
    ---------------------------------

    Still no argument: the caller passes nothing and cannot aim this at a
    friendlier file.  Every candidate is admitted by :func:`tree_match`, which
    is the gate's own test, and :func:`push_preflight.check` then judges the
    winner on all of its other conditions — green, non-vacuous, covered,
    declared, no unsupported claim.  A receipt this search returns is one the
    gate would have accepted had the exact key survived; it cannot manufacture a
    pass ``check`` would refuse, because ``check`` still runs.

    Fails closed: with no admissible receipt the *exact* path is returned, so
    the verdict stays ``NO_RECEIPT`` on the tree nobody measured.
    """
    st = tp.stamp(root)
    exact = rs.path_for(st.worktree_fingerprint, root)
    if exact.exists():
        return exact
    for path in _admissible(st, root):
        return path
    return exact


def _admissible(st, root: Path | None = None):
    """Store entries whose measured tree :func:`tree_match` accepts for *st*.

    Newest first: when several receipts are admissible they are all licences for
    this tree, and the most recent is the one whose measurement is closest to
    what is about to be pushed.  Ordering is fully determined (mtime, then path)
    so two runs of the hook on one tree reach the same receipt.

    Two costs are hoisted out of the loop, both measured rather than guessed:
    the tree is stamped **once** by the caller and passed in (0.44 s), and the
    pins' premise check is taken once (0.09 s — :func:`inert` re-derives each
    pin's reader set from the tree).  Per receipt what remains is a JSON parse
    and a dict diff.  That is the whole reason this is not written as ``check``
    over every entry: ``check`` re-stamps the worktree, re-checks the pins and
    re-scans the journal frontier per call, which over the 67 receipts on disk
    on 2026-08-13 was ~7 s inside a ``pre-push`` hook, for a question that is
    the same 67 times.  As written the same full miss measures **0.57 s**; a hit
    stops at the first admissible entry and pays one parse.
    """
    exempt = ins.exempt_candidates()
    entries = sorted(
        rs.entries(root),
        key=lambda p: (-p.stat().st_mtime, p.name),
    )
    for path in entries:
        receipt = pp.load(path)
        if receipt is None:
            continue
        if pp.tree_match(receipt, st, path, exempt=exempt).ok:
            yield path


def decide(
    stdin_text: str,
    receipt_path: Path | None = None,
    root: Path | None = None,
    checker=None,
) -> Decision:
    """Should this push proceed?

    *checker* defaults to :func:`push_preflight.check` and exists so the
    decision can be tested without manufacturing a green suite run; it is the
    same function the constitution's chain calls.
    """
    refs = guarded_refs(stdin_text)
    if not refs:
        return Decision(
            ALLOW,
            "no autoresearch ref moves in this push — outside the population "
            "this hook gates",
        )
    if receipt_path is None:
        receipt_path = licence_path(root)
    check = checker if checker is not None else pp.check
    verdict = check(receipt_path, root=root)
    if verdict.ok:
        return Decision(
            ALLOW,
            f"push gate re-run at push time: {verdict.verdict} — {verdict.detail}",
            refs,
        )
    return Decision(
        REFUSE,
        f"push gate re-run at push time: {verdict.verdict} — {verdict.detail}",
        refs,
    )


def wiring(root: Path | None = None) -> str:
    """The repository-local ``core.hooksPath``, or an empty string if unset."""
    base = Path(root) if root is not None else Path.cwd()
    proc = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=str(base),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def wired(root: Path | None = None) -> bool:
    """Is ``git`` actually consulting :data:`HOOKS_DIR`?"""
    return wiring(root) == str(HOOKS_DIR)


def install(root: Path | None = None) -> str:
    """Point ``core.hooksPath`` at :data:`HOOKS_DIR` for this clone."""
    base = Path(root) if root is not None else Path.cwd()
    subprocess.run(
        ["git", "config", "core.hooksPath", str(HOOKS_DIR)],
        cwd=str(base),
        capture_output=True,
        text=True,
        check=True,
    )
    return wiring(root)


def _main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "status"

    if cmd == "hook":
        decision = decide(sys.stdin.read())
        print(f"push_licence — {decision.outcome}: {decision.detail}")
        if not decision.ok:
            print(
                "  the gate refused at push time.  Fix the tree and re-measure "
                "with `push_preflight record`; pushing anyway needs an explicit "
                "`git push --no-verify`, which is a decision with a name on it.",
                file=sys.stderr,
            )
            return 1
        return 0

    if cmd == "install":
        print(f"push_licence — core.hooksPath = {install()}")
        return 0

    if cmd == "status":
        path = wiring()
        if wired():
            print(f"push_licence — hook wired: core.hooksPath = {path}")
            return 0
        shown = path if path else "(unset)"
        print(
            f"push_licence — hook NOT wired: core.hooksPath = {shown}; "
            f"expected {HOOKS_DIR}.  Run `python3 -m "
            "eval.mppi_sandbox.push_licence install`."
        )
        return 1

    print(f"push_licence — unknown command {cmd!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
