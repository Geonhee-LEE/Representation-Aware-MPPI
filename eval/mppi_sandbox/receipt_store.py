"""Keep a suite receipt past the cycle boundary that currently destroys it.

The bottleneck this exists to attack
------------------------------------

The suite costs ~1220 s of a 35-minute budget (``cycle_wallclock``'s measured
price).  A cycle therefore affords **one** run, and the push gate
(:mod:`push_preflight`) will not license a push without a green one.  That is
the right refusal.  The waste is what happens *next*: the receipt is written to
``/tmp/suite-receipt.json``, and the next cycle starts by deleting it — the
``record`` CLI unlinks ``--out`` before running, deliberately, so a crash cannot
leave a corpse that reads as evidence (D-082).

So a cycle that changes **nothing** a test can read — a repair cycle
republishing an unchanged head, the 16:00/18:00/20:00 strand repairs of
2026-08-11 — pays the full 1220 s to re-derive a number that was already
measured on exactly that tree.  Three cycles on 2026-08-11 did this, and each
had ~20 of its 35 minutes left over for actual work afterwards.

The receipt was never the scarce thing.  The *measurement* was, and it was being
thrown away while still valid.

The key is the tree, not the cycle
----------------------------------

A receipt is a claim about one tree.  :func:`push_preflight.check` already
decides validity by comparing ``worktree_fingerprint`` — so that fingerprint,
not the hour or the branch, is the only honest key.  Two cycles that produce
byte-identical trees are entitled to the same receipt; two that differ by one
tracked byte are not, and no naming scheme based on time can express that.

Hence :func:`path_for`: the file is named by the tree it describes.  Recall is a
lookup, never a search, and there is no "closest match" — the concept does not
exist here.

Why the store must stay untracked
---------------------------------

This is the constraint that decides the whole design, and getting it backwards
would make the store silently useless.

``worktree_fingerprint`` covers **tracked** files (``git ls-files``); untracked
paths land in the separate ``untracked_digest``, which :func:`push_preflight.check`
does not compare.  So:

* while the store is **untracked**, writing a receipt into it does not move the
  fingerprint, and the receipt stays valid for the tree it just measured;
* the moment the store were **committed**, every archive would change the
  tracked tree, so each receipt would invalidate itself the instant it landed
  and *every* recall would miss.  The store would cost disk and return nothing.

A tracked store is not merely suboptimal — it is a store that can never hit.
:data:`STORE_DIR` is therefore gitignored, and :func:`tracked_conflict` exists
to make the violation loud if some later cycle "helpfully" commits it.

Durability, honestly scoped
---------------------------

This buys durability across **cycle boundaries on one machine**, which is where
the loss actually happens.  It does not survive a fresh clone, and it is not
meant to: a receipt is evidence about a worktree, and a clone has a different
one.  ``/tmp`` on this host has survived 174 days of uptime, so the fragility
being fixed is the deliberate unlink, not tmpfs eviction.

What recall refuses
-------------------

:func:`recall` re-checks that the receipt inside the file carries the
fingerprint the filename claims.  A file named by a hash that does not contain
that hash has been renamed, hand-edited, or truncated mid-write, and the whole
value of the store is that its key is derived rather than asserted.  Every such
state collapses to ``None`` — no evidence — for :func:`push_preflight.load`'s
stated reason: distinguishing them would invite a branch that treats one of them
as evidence.

Refs: D-082 (a push is licensed by a receipt, not by memory), D-043/D-044 (a
count belongs to one tree), D-200/D-201 (``OBSERVED_SUITE_SECONDS`` wants more
than n=2 observations — this store accumulates them for free), D-162 (a guard
placed by hand is one a cycle forgets).
"""

from __future__ import annotations

from pathlib import Path

from . import push_preflight as pp
from . import tree_provenance as tp

#: Where receipts accumulate.  Repo-relative, and **untracked** — see the module
#: docstring: a committed store invalidates every receipt it holds.
#:
#: Not ``results/readings/``, which was this module's first choice and is
#: already a **tracked** directory holding a different artifact class
#: (``2026-08-05-04-ordering-control.json``, ordering-control measurement
#: cells).  Landing here would have been the quiet kind of wrong: the store
#: would have written and read without error while ``tracked_conflict`` was
#: non-empty from the first cycle, so it could never hit — and the
#: ``.gitignore`` entry would not have helped, since ignore rules do not apply
#: to already-tracked files.  ``tracked_conflict`` caught it on the first run.
STORE_DIR = Path("results") / "receipts"

#: Characters of the fingerprint used in the filename.  Long enough that a
#: collision is not a practical concern, short enough that the directory stays
#: readable when an operator lists it.  The full fingerprint is re-verified from
#: the file's contents on recall, so this prefix is an index, never the proof.
KEY_CHARS = 16


def store_dir(root: Path | None = None) -> Path:
    return (root or tp.REPO_ROOT) / STORE_DIR


def path_for(fingerprint: str, root: Path | None = None) -> Path:
    """The one path a receipt for *fingerprint* may occupy."""
    return store_dir(root) / f"{fingerprint[:KEY_CHARS]}.json"


def archive(receipt: pp.Receipt, root: Path | None = None) -> Path:
    """Persist *receipt* under its own tree fingerprint and return the path.

    Overwrites an existing entry for the same fingerprint.  That is the correct
    resolution rather than a conflict: both receipts describe the same tree, so
    the newer one is at worst equally true, and refusing here would leave the
    stale one in place — the direction that keeps the *older* evidence.
    """
    path = path_for(receipt.worktree_fingerprint, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(receipt.to_json())
    return path


def recall(fingerprint: str, root: Path | None = None) -> pp.Receipt | None:
    """The archived receipt for *fingerprint*, or ``None`` if there is no proof.

    ``None`` covers absent, unreadable, and **misfiled** — a receipt whose own
    ``worktree_fingerprint`` is not the one the filename claims.  The last case
    is the one worth spelling out: the store's guarantee is that its key is
    *derived from* the contents, so a file that breaks that link is not a weaker
    receipt, it is not a receipt.
    """
    receipt = pp.load(path_for(fingerprint, root))
    if receipt is None:
        return None
    if receipt.worktree_fingerprint != fingerprint:
        return None
    return receipt


def recall_current(root: Path | None = None) -> pp.Receipt | None:
    """The archived receipt for the tree as it stands right now, if any.

    This is the call a cycle makes to find out whether it can skip the suite.
    Note what it does *not* do: it never decides the push.  It hands back
    evidence, and :func:`push_preflight.check` remains the sole judge — a
    hit here is only as good as that gate says it is.
    """
    return recall(tp.stamp(root).worktree_fingerprint, root)


def tracked_conflict(root: Path | None = None) -> tuple[str, ...]:
    """Store paths that git tracks — always empty, or the store is broken.

    Exists because the failure is silent: a committed store still writes, still
    reads, and simply never hits, so the symptom is "the cache does nothing"
    rather than an error.  Naming the condition lets a test assert it instead of
    a future cycle rediscovering it.
    """
    prefix = STORE_DIR.as_posix() + "/"
    return tuple(p for p in tp.tracked_paths(root) if p.startswith(prefix))


def entries(root: Path | None = None) -> tuple[Path, ...]:
    d = store_dir(root)
    return tuple(sorted(d.glob("*.json"))) if d.is_dir() else ()


def _main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.receipt_store",
        description="Keep a suite receipt past the cycle boundary (STATE #1).",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_arc = sub.add_parser("archive", help="copy a receipt into the store")
    p_arc.add_argument("receipt", type=Path)

    sub.add_parser("recall", help="report the archived receipt for this tree")
    sub.add_parser("list", help="list archived receipts")

    args = ap.parse_args(argv)

    if args.cmd == "archive":
        receipt = pp.load(args.receipt)
        if receipt is None:
            print(f"receipt_store — nothing readable at {args.receipt}; not archived.")
            return 1
        path = archive(receipt)
        print(
            f"receipt_store — archived {receipt.worktree_fingerprint[:KEY_CHARS]} "
            f"→ {path} (rc={receipt.returncode}, executed={receipt.executed})"
        )
        return 0

    if args.cmd == "list":
        found = entries()
        if not found:
            print("receipt_store — store is empty.")
            return 0
        print(f"receipt_store — {len(found)} archived receipt(s):")
        for path in found:
            receipt = pp.load(path)
            if receipt is None:
                print(f"  {path.name}  (unreadable)")
                continue
            secs = receipt.duration_seconds
            price = f"{secs:.0f}s" if secs is not None else "unpriced"
            print(
                f"  {path.name}  rc={receipt.returncode} "
                f"executed={receipt.executed} {price}"
            )
        return 0

    receipt = recall_current()
    if receipt is None:
        print(
            "receipt_store — MISS: no archived receipt for this tree. "
            "The suite has to run."
        )
        return 1
    secs = receipt.duration_seconds
    price = f", {secs:.0f}s when it ran" if secs is not None else ""
    print(
        f"receipt_store — HIT: this tree was measured "
        f"(rc={receipt.returncode}, executed={receipt.executed}{price}). "
        "`push_preflight check` still decides the push."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())
