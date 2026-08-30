"""Bind a pass count to the tree it was measured on (D-043, STATE #1).

D-043 found that ``d060636``'s reported ``367 passed`` was a true statement
about a tree that **no longer existed at push time**: the cycle ran the guard,
*then* prepended its ``D-041`` section, and that prose restated one of the
banked magnitudes — creating exactly the unregistered citation site
:mod:`citation_audit` is built to catch.  The number was not fabricated.  It was
measured, correctly, against an artifact nobody shipped.

The magnitude is deliberately *not* spelled here.  When this module was written
:mod:`citation_audit`'s scan surface was a hand-written tuple, so a new module
restating a claim was unpoliced until someone remembered to add it — Q-056's
hole, demonstrated by this file rather than argued.  Not creating the site was
the cheap resolution, and it stays as written.  D-045 supplied the mechanism the
next cycle: :func:`citation_audit.scanned_modules` now globs the package, so
this file has been inside the scan since then whether or not anyone typed it in.

The rule D-043 states is "re-run the fast half *after* the doc writes".  A rule
phrased that way is a thing an executor has to remember, and thirty cycles of
"committed by hand for the thirtieth cycle running" is the base rate for how
well this project remembers procedural rules.  So this module makes the rule
*checkable* instead: stamp the tree before measuring, verify after writing, and
the discrepancy names its own paths.

Two fingerprints, not one
-------------------------

The naive instrument — hash the worktree, compare before/after — goes red every
single cycle, because D-011 *requires* the worktree to drift: ``STATE.md`` /
``JOURNAL.md`` / ``RESULTS.md`` are written every cycle and deliberately never
committed on an ``autoresearch/*`` branch.  An always-red check is ignored
within a week, and D-042's asymmetry lesson applies in this direction too: a
check whose default is alarm launders into a check with no default at all.

So the surface is split by *destination* rather than by directory:

``worktree_digests``
    what the tests actually read — tracked paths as they sit on disk, local-only
    edits included.  A pass count is a property of **this**.

``committed_digests``
    the ``HEAD`` tree — what ``git push`` ships.  A PR's CI runs against
    **this**.

D-043's defect is the two silently disagreeing on a file that carries a claim.
:func:`undeclared_drift` is the check: worktree-vs-``HEAD`` may differ, but only
on paths that are *declared* local-only.  Anything else is a number measured
against something unshipped.

What running it found
---------------------

D-011 declares **three** local-only files.  The worktree diverges by **five**:
``TODO.md`` (rewritten by ``scripts/mirror_todos.sh``) and ``research/feed.md``
(rewritten by the 4-hourly Researcher) are also full-overwrite artifacts that no
branch commits, and neither is named anywhere in the 🚫 rule they obey.  They
were not exempted; they were unnoticed.  That is the same shape as the citation
sites of D-036 — the registry policed what someone remembered to type in — and
it means the "3 snapshot files" figure quoted in the Phase 3 push rule has been
an undercount for as long as both scripts have existed.

:data:`DECLARED_LOCAL_ONLY` therefore carries five entries and a reason per
entry, and :func:`undeclared_drift` reports the rest.  The list is a
*declaration*, in D-038's sense: an excluded surface that is written down is
auditable, and one that is implicit is just a hole.

Fail-open, deliberately named
-----------------------------

Untracked files are **not** in either fingerprint, because they are not in the
pushed tree — folding them in would make every stray ``.last_result`` a false
mismatch.  But an untracked file can still change a test outcome (a stray
module on the import path), in which case the measurement is not reproducible
from the commit at all, which is a *different* failure than D-043's.  So their
identities are hashed into :attr:`Stamp.untracked_digest` and surfaced as a
separate condition rather than silently dropped.  Per D-042: an instrument that
can only clear work should not be trusted to clear work, so the thing it cannot
see gets a field instead of a shrug.

This module is fast-half only: it hashes files and shells out to ``git``.
Nothing simulates.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Repo root, resolved from this file rather than the cwd: the executor runs from
# the project root but pytest may not, and a provenance check that depends on
# where it was invoked from is not a provenance check.
REPO_ROOT = Path(__file__).resolve().parents[2]

#: Tracked paths a branch is *expected* to differ from ``HEAD`` on, with the
#: reason each is exempt.  D-011 named the first three; the last two were found
#: by :func:`undeclared_drift` on the tree that first ran it (see module
#: docstring).  Anything not in here that drifts is D-043's defect.
DECLARED_LOCAL_ONLY: dict[str, str] = {
    "STATE.md": "D-011: full-overwrite snapshot, rewritten every cycle, never committed on a branch",
    "JOURNAL.md": "D-011: append-at-top digest, never committed on a branch",
    "RESULTS.md": "D-011: regenerated by scripts/aggregate_results.sh, never staged",
    "TODO.md": "rewritten by scripts/mirror_todos.sh; same full-overwrite class as the D-011 three",
    "research/feed.md": "rewritten by the 4-hourly scripts/researcher.sh; capped at 30 entries",
}

#: Sentinel digest for a path git tracks that is absent from disk.  A deleted
#: tracked file has to be distinguishable from an empty one, or a deletion reads
#: as "unchanged" against a zero-byte file.
MISSING = "absent"

LOOP_PROMPT = REPO_ROOT / "scripts" / "prompts" / "auto_research.md"

#: How a ``declared`` invocation is spelled.  Built from ``__name__`` rather
#: than typed, so a module rename breaks the pin loudly instead of leaving it
#: matching a string nothing runs (D-047, and cf. `bottleneck_scope.INVOCATION`).
DECLARED_INVOCATION = f"python3 -m {__name__} declared"

#: The REVIEW heading whose body must contain the call.  Scoping matters here in
#: a way it did not for `bottleneck_scope`: that module is invoked from exactly
#: one loop step, so a whole-file substring test was already a real pin.  This
#: module is invoked from three (Phase 3 `stamp`, Phase 4a-ter `verify` /
#: `declared`), so an unscoped `DECLARED_INVOCATION in text` would report
#: `True` off the 4a-ter block and pass **vacuously** — green whether or not
#: REVIEW ever gained the reading.  The section slice is what makes it a pin.
REVIEW_HEADING = "## Phase 1 — REVIEW"


def review_section(prompt_path: str | Path | None = None) -> str:
    """The body of the loop prompt's Phase 1 REVIEW section.

    Returns ``""`` — not an exception — when the prompt or the heading is
    missing, because "no prompt", "no REVIEW section" and "REVIEW section that
    does not call" are one finding for the only reader that matters: a cycle
    that will not take the reading either way.
    """
    path = Path(prompt_path) if prompt_path is not None else LOOP_PROMPT
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    start = text.find(REVIEW_HEADING)
    if start < 0:
        return ""
    body = text[start + len(REVIEW_HEADING):]
    end = body.find("\n## Phase ")
    return body if end < 0 else body[:end]


def wired_into_review(prompt_path: str | Path | None = None) -> bool:
    """Does Phase 1 REVIEW actually invoke ``declared``?

    D-494 is the worked example: 15 files of doc drift that belonged to no
    cycle made `push_preflight` refuse `UNDECLARED` on every push, and two
    consecutive cycles each discovered it only *after* spending a suite.  The
    reading costs one command and is the only one that catches an unpublishable
    tree before that spend.
    """
    return DECLARED_INVOCATION in review_section(prompt_path)


def _git(*args: str, root: Path | None = None) -> str:
    """Run ``git`` in *root* and return stripped stdout.

    Raises :class:`subprocess.CalledProcessError` rather than returning a
    default — a provenance instrument that silently degrades to "no git here"
    would report a clean tree for an unknown one.
    """
    out = subprocess.run(
        ("git", *args),
        cwd=str(root or REPO_ROOT),
        capture_output=True,
        check=True,
        text=True,
    )
    return out.stdout.strip()


def _digest_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def tracked_paths(root: Path | None = None) -> tuple[str, ...]:
    """Repo-relative paths git tracks at the index, sorted.

    ``-z`` because this repo already contains a filename with an embedded quote
    (``2026-07-17"`` — a shell-quoting bug's leftover), and newline-splitting
    ``git ls-files`` output is only correct until someone's ``date`` call is
    misquoted.
    """
    raw = _git("ls-files", "-z", root=root)
    return tuple(sorted(p for p in raw.split("\0") if p))


def worktree_digests(root: Path | None = None) -> dict[str, str]:
    """Content digest per tracked path, **as it sits on disk**.

    This is the surface a test run reads, so it is the surface a pass count is a
    property of.
    """
    base = root or REPO_ROOT
    out: dict[str, str] = {}
    for rel in tracked_paths(root):
        path = base / rel
        try:
            out[rel] = _digest_bytes(path.read_bytes())
        except (FileNotFoundError, NotADirectoryError, IsADirectoryError):
            out[rel] = MISSING
    return out


def committed_digests(ref: str = "HEAD", root: Path | None = None) -> dict[str, str]:
    """Content digest per path in *ref*'s tree — what ``git push`` ships.

    Digests are recomputed from blob contents with the same hash as
    :func:`worktree_digests` rather than reusing git's own blob sha, because
    git's sha is taken over a ``blob <len>\\0`` header and would never compare
    equal to a bare content hash.  Two hashes that cannot be compared are worse
    than one, since the mismatch looks like a finding.
    """
    listing = _git("ls-tree", "-r", "-z", "--full-tree", ref, root=root)
    out: dict[str, str] = {}
    for entry in listing.split("\0"):
        if not entry:
            continue
        meta, _, rel = entry.partition("\t")
        parts = meta.split()
        if len(parts) < 3 or parts[1] != "blob":
            # Submodule (commit) or malformed line: nothing to hash.
            continue
        blob = subprocess.run(
            ("git", "cat-file", "blob", parts[2]),
            cwd=str(root or REPO_ROOT),
            capture_output=True,
            check=True,
        ).stdout
        out[rel] = _digest_bytes(blob)
    return out


def untracked_paths(root: Path | None = None) -> tuple[str, ...]:
    """Untracked, non-ignored paths — outside both fingerprints, still reported."""
    raw = _git("ls-files", "--others", "--exclude-standard", "-z", root=root)
    return tuple(sorted(p for p in raw.split("\0") if p))


def _fingerprint(digests: dict[str, str]) -> str:
    """One hash over the whole (path, digest) map.

    Sorted, NUL-delimited, and the path is hashed alongside its content so a
    rename is a change.  A fingerprint over contents alone would call a moved
    file an unmoved one.
    """
    h = hashlib.sha256()
    for rel in sorted(digests):
        h.update(rel.encode())
        h.update(b"\0")
        h.update(digests[rel].encode())
        h.update(b"\0")
    return h.hexdigest()


@dataclass(frozen=True)
class Stamp:
    """A tree's identity at one instant, precise enough to diff against later."""

    head: str
    worktree_fingerprint: str
    committed_fingerprint: str
    untracked_digest: str
    n_tracked: int
    n_untracked: int
    #: Per-path detail, so a later mismatch can *name* the files rather than
    #: only asserting that something moved.  The whole point of D-043 is that
    #: "something changed" was already known; which file carried the claim was
    #: not.
    worktree: dict[str, str] = field(default_factory=dict, repr=False)
    committed: dict[str, str] = field(default_factory=dict, repr=False)
    untracked: tuple[str, ...] = field(default=(), repr=False)

    def to_json(self) -> str:
        return json.dumps(
            {
                "head": self.head,
                "worktree_fingerprint": self.worktree_fingerprint,
                "committed_fingerprint": self.committed_fingerprint,
                "untracked_digest": self.untracked_digest,
                "n_tracked": self.n_tracked,
                "n_untracked": self.n_untracked,
                "worktree": self.worktree,
                "committed": self.committed,
                "untracked": list(self.untracked),
            },
            indent=2,
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, blob: str) -> "Stamp":
        d = json.loads(blob)
        return cls(
            head=d["head"],
            worktree_fingerprint=d["worktree_fingerprint"],
            committed_fingerprint=d["committed_fingerprint"],
            untracked_digest=d["untracked_digest"],
            n_tracked=d["n_tracked"],
            n_untracked=d["n_untracked"],
            worktree=d.get("worktree", {}),
            committed=d.get("committed", {}),
            untracked=tuple(d.get("untracked", ())),
        )


def stamp(root: Path | None = None, ref: str = "HEAD") -> Stamp:
    """Capture the tree's identity now.  Call before measuring, and after."""
    wt = worktree_digests(root)
    ct = committed_digests(ref, root)
    un = untracked_paths(root)
    return Stamp(
        head=_git("rev-parse", ref, root=root),
        worktree_fingerprint=_fingerprint(wt),
        committed_fingerprint=_fingerprint(ct),
        untracked_digest=_fingerprint({p: "" for p in un}),
        n_tracked=len(wt),
        n_untracked=len(un),
        worktree=wt,
        committed=ct,
        untracked=un,
    )


@dataclass(frozen=True)
class Drift:
    """What moved between two states, named path by path."""

    changed: tuple[str, ...] = ()
    added: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(sorted({*self.changed, *self.added, *self.removed}))

    def __bool__(self) -> bool:
        return bool(self.changed or self.added or self.removed)

    def describe(self) -> str:
        if not self:
            return "no drift"
        bits = []
        for label, group in (
            ("changed", self.changed),
            ("added", self.added),
            ("removed", self.removed),
        ):
            if group:
                bits.append(f"{label}: {', '.join(group)}")
        return "; ".join(bits)


def _diff(before: dict[str, str], after: dict[str, str]) -> Drift:
    return Drift(
        changed=tuple(
            sorted(k for k in before.keys() & after.keys() if before[k] != after[k])
        ),
        added=tuple(sorted(after.keys() - before.keys())),
        removed=tuple(sorted(before.keys() - after.keys())),
    )


def verify(prior: Stamp, root: Path | None = None, ref: str = "HEAD") -> Drift:
    """Is the tree a measurement was taken on still the tree in hand?

    This is D-043's direct rule, mechanised.  A non-empty result means any pass
    count recorded against *prior* describes a tree that no longer exists — the
    count is not wrong, it is about something else.  Local-only files are **not**
    exempt here: a doc write is exactly what D-043 caught, and the guard reads
    ``docs/``.
    """
    return _diff(prior.worktree, worktree_digests(root))


def undeclared_drift(
    current: Stamp | None = None,
    root: Path | None = None,
    declared: dict[str, str] | None = None,
) -> Drift:
    """Worktree-vs-``HEAD`` drift on paths that are **not** declared local-only.

    Empty means the tree the tests read and the tree the PR ships differ only by
    files whose divergence is written down.  Non-empty means a pass count is
    being reported for one artifact and pushed as another.
    """
    st = current or stamp(root)
    allow = DECLARED_LOCAL_ONLY if declared is None else declared
    raw = _diff(st.committed, st.worktree)
    return Drift(
        changed=tuple(p for p in raw.changed if p not in allow),
        added=tuple(p for p in raw.added if p not in allow),
        removed=tuple(p for p in raw.removed if p not in allow),
    )


def stale_declarations(root: Path | None = None) -> tuple[str, ...]:
    """Declared local-only paths that git does not track.

    The mirror of :func:`undeclared_drift`: an exemption for a file that no
    longer exists is an exemption nobody will notice went dead, and it would
    silently re-admit the path it was written to cover if the name came back
    under a different meaning.
    """
    tracked = set(tracked_paths(root))
    return tuple(sorted(p for p in DECLARED_LOCAL_ONLY if p not in tracked))


def _main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.tree_provenance",
        description="Bind a measurement to the tree it was taken on (D-043).",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_stamp = sub.add_parser("stamp", help="write a tree stamp as JSON to stdout")
    p_stamp.add_argument("--out", type=Path, default=None)
    p_verify = sub.add_parser(
        "verify", help="compare a prior stamp against the tree now (D-043's rule)"
    )
    p_verify.add_argument("stamp", type=Path)
    sub.add_parser(
        "declared", help="report worktree-vs-HEAD drift outside the declared set"
    )
    args = ap.parse_args(argv)

    if args.cmd == "stamp":
        blob = stamp().to_json()
        if args.out:
            args.out.write_text(blob)
            print(f"stamp written: {args.out}")
        else:
            print(blob)
        return 0

    if args.cmd == "verify":
        prior = Stamp.from_json(args.stamp.read_text())
        drift = verify(prior)
        if not drift:
            print(f"OK: tree unchanged since stamp (head={prior.head[:8]})")
            return 0
        print(f"DRIFT since stamp (head={prior.head[:8]}): {drift.describe()}")
        print(
            "=> any pass count recorded against this stamp is a statement about a "
            "tree that no longer exists (D-043)."
        )
        return 1

    stale = stale_declarations()
    drift = undeclared_drift()
    for path, why in sorted(DECLARED_LOCAL_ONLY.items()):
        print(f"declared local-only: {path} — {why}")
    if stale:
        print(f"STALE declarations (not tracked): {', '.join(stale)}")
    if not drift:
        print("OK: worktree differs from HEAD only on declared local-only paths")
        return 0 if not stale else 1
    print(f"UNDECLARED worktree-vs-HEAD drift: {drift.describe()}")
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())
