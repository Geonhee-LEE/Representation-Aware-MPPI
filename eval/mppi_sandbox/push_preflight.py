"""Refuse to push a tree nobody ran the suite on (STATE #1, the D-043 sibling).

D-043 and D-044 police **when** a count is taken: stamp before measuring, verify
after the doc writes, re-run if the tree moved.  Both rules assume a count
*exists*.  A cycle that dies before Phase 4 takes none at all, and then the
mechanism is silent — there is nothing to verify against, so nothing goes red.

That is not hypothetical.  On 2026-08-05 it happened **three times in one day**:

* 07:00 crashed after commit; the 08:00 cycle found D-077 committed, unpushed,
  and its journal claiming ``TSV row appended: yes``.
* 10:00 crashed after commit; the 11:00 cycle pushed ``1f69128`` and *then*
  discovered it was **red** — three census pins D-080's own prose had named and
  never re-pinned.  PR #67 was red for an hour because a push went out ahead of
  a measurement.
* 11:00 crashed after commit; ``903d148`` — the commit that *repairs* those
  three failures — sat unpushed, so the "red → green" outcome recorded in
  ``STATE.md`` was a true statement about a tree that origin had never seen.

The third one is the argument for mechanising rather than writing the rule down
again: the cycle that diagnosed the defect, and wrote the diagnosis into the
decision log, then committed that diagnosis and failed to ship it, by the same
defect, within the hour.

So this module makes "green before push" *checkable* the way
:mod:`tree_provenance` made "fresh before publish" checkable.  A push is
licensed by an artifact — a :class:`Receipt` — not by an executor's memory that
it ran something.

Two trees, and neither check licenses a push alone
--------------------------------------------------

:mod:`tree_provenance` already splits the surface by destination: the
**worktree** is what the tests read, the ``HEAD`` tree is what ``git push``
ships, and D-011 *requires* the two to differ on the declared local-only files.
A receipt is therefore a claim about the worktree, and a push ships something
else.  Composing them is the whole content of :func:`check`:

* the receipt must match the worktree **now** (else the run describes a tree
  that no longer exists — D-043's defect, at push time), **and**
* worktree-vs-``HEAD`` drift must be confined to the declared set (else the
  green claim is about an artifact that is not the one going out).

Either alone is satisfiable while the other fails, and either alone would have
cleared a bad push.  The verdict names which one fired.

Fail closed, and say which way it failed
----------------------------------------

Every unknown grades as a refusal, because the failure this module exists to
stop *is* the absence of information:

* :data:`NO_RECEIPT` — no run was recorded.  The three crashes above.
* :data:`STALE` — the tree moved since the run.
* :data:`VACUOUS` — the run reports success having collected **nothing**.
* :data:`RED` — the run failed.
* :data:`UNDECLARED` — the measured tree is not the shipped tree.
* :data:`GREEN` — the only verdict that licenses a push.

:data:`VACUOUS` is here for the reason D-081 put it in :mod:`key_conflation` and
D-076 spent a cycle on: a green reading and an empty reading are not the same
reading.  ``pytest`` exits ``5`` on "no tests collected", a mistyped path
collects zero, and an unparseable summary tells us nothing — all three would
otherwise present as "did not fail".  D-075's ``"no D-074 value survives"``
passed vacuously for exactly this shape.  So emptiness is decided **before**
success, and an unreadable summary is emptiness rather than a shrug.

The receipt is *recorded*, not typed
------------------------------------

:func:`record` shells out to the suite and writes what it observed.  There is no
supported path that produces a receipt from a human-supplied count, because a
number an executor can type is a number an executor can type from memory — which
is the class of defect D-043, D-078 and D-081 each caught a fresh instance of.

The CI on the PR remains the only authority for the pushed tree.  This is a
local gate on a local claim; it stops a *known-unmeasured* push, not a
green-here-red-there one.

Refs: D-043 (bind a count to its tree), D-044 (the count has one valid moment),
D-011 (the local-only three), D-075/D-076/D-081 (vacuous survival), D-042 (a
check whose default is alarm gets muted).
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import inert_surface as ins
from . import suite_coverage as sc
from . import tree_provenance as tp

#: Verdicts.  Spelled as module constants rather than an enum to match the rest
#: of the package, and compared by identity nowhere — :func:`check` returns the
#: string and callers compare by equality.
NO_RECEIPT = "NO_RECEIPT"
STALE = "STALE"
VACUOUS = "VACUOUS"
RED = "RED"
#: The receipt is green over a *part* of the suite, and the part it left out is
#: known to be failing.  Distinct from :data:`RED` — this run did not fail; it
#: declined to ask the question that is failing.  See :mod:`suite_coverage`.
UNCOVERED_RED = "UNCOVERED_RED"
UNDECLARED = "UNDECLARED"
GREEN = "GREEN"

#: Every verdict, in the order :func:`check` decides them.  Ordering is part of
#: the contract: a receipt can be simultaneously stale *and* red, and the
#: earlier entry is the more informative diagnosis of *why the push is unsafe*.
#: Pinned as data so a test can assert the decision procedure is exhaustive
#: rather than re-deriving the list from the branches.
#:
#: :data:`UNCOVERED_RED` sits after :data:`RED` because a run that failed is
#: better described by its own failure than by what it skipped, and before
#: :data:`UNDECLARED` because a wrong *population* invalidates the reading
#: itself, whereas a wrong *tree* invalidates only its destination.
VERDICTS: tuple[str, ...] = (
    NO_RECEIPT,
    STALE,
    VACUOUS,
    RED,
    UNCOVERED_RED,
    UNDECLARED,
    GREEN,
)

#: pytest outcome words that mean "a test body actually executed".  ``skipped``
#: and ``deselected`` are deliberately **excluded**: a run that collected 400
#: tests and skipped all 400 asserted nothing, and grading it ``GREEN`` is
#: precisely the vacuous-survival defect this module refuses to reproduce.
EXECUTED_OUTCOMES: tuple[str, ...] = (
    "passed",
    "failed",
    "error",
    "errors",
    "xpassed",
    "xfailed",
)

#: Outcome words that mean the suite is not green.
FAILING_OUTCOMES: tuple[str, ...] = ("failed", "error", "errors")

_SUMMARY_TOKEN = re.compile(
    r"(\d+)\s+(passed|failed|errors?|skipped|xfailed|xpassed|deselected|warnings?)"
)


def parse_summary(text: str) -> dict[str, int]:
    """Outcome counts from ``pytest`` terminal output.

    Reads the **last** line carrying summary tokens, because ``-q`` prints a
    progress line, then the short summary, then the counts; earlier lines can
    contain the same words inside a failure's traceback.

    Returns ``{}`` when nothing parses.  That is not "clean" — :func:`check`
    grades an unparseable summary :data:`VACUOUS`, since a run whose outcome
    could not be read is a run whose outcome is unknown, and unknown fails
    closed here.
    """
    best: dict[str, int] = {}
    for line in text.splitlines():
        found = _SUMMARY_TOKEN.findall(line)
        if not found:
            continue
        counts: dict[str, int] = {}
        for n, word in found:
            counts[word.rstrip("s") if word.startswith("error") else word] = int(n)
        best = counts
    return best


@dataclass(frozen=True)
class Receipt:
    """A suite run, bound to the tree it read.

    ``worktree_fingerprint`` is the binding.  ``head`` is recorded for the
    message only: a receipt whose ``head`` matches but whose worktree does not is
    still stale, so the fingerprint is what :func:`check` compares.
    """

    head: str
    worktree_fingerprint: str
    committed_fingerprint: str
    returncode: int
    counts: dict[str, int]
    command: tuple[str, ...] = ()
    #: Per-path digests of the tree the run read.  The fingerprint is enough to
    #: *detect* staleness; this is what lets :func:`check` say **which** paths
    #: moved, which is the precondition for asking whether any of them could
    #: have moved a test.  Absent (older receipts) means the question cannot be
    #: asked, and an unanswerable question grades ``STALE``.
    worktree: dict[str, str] = field(default_factory=dict)

    @property
    def executed(self) -> int:
        """Tests whose body ran.  Zero means the run asserted nothing."""
        return sum(self.counts.get(word, 0) for word in EXECUTED_OUTCOMES)

    @property
    def failures(self) -> int:
        return sum(self.counts.get(word, 0) for word in FAILING_OUTCOMES)

    def to_json(self) -> str:
        return json.dumps(
            {
                "head": self.head,
                "worktree_fingerprint": self.worktree_fingerprint,
                "committed_fingerprint": self.committed_fingerprint,
                "returncode": self.returncode,
                "counts": self.counts,
                "command": list(self.command),
                "worktree": self.worktree,
            },
            indent=2,
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, blob: str) -> "Receipt":
        d = json.loads(blob)
        return cls(
            head=d["head"],
            worktree_fingerprint=d["worktree_fingerprint"],
            committed_fingerprint=d["committed_fingerprint"],
            returncode=int(d["returncode"]),
            counts={k: int(v) for k, v in d.get("counts", {}).items()},
            command=tuple(d.get("command", ())),
            worktree=dict(d.get("worktree", {})),
        )


@dataclass(frozen=True)
class Verdict:
    """A verdict plus the evidence for it, so a refusal names its own cause."""

    verdict: str
    detail: str
    receipt: Receipt | None = None
    drift: tp.Drift | None = None

    @property
    def ok(self) -> bool:
        return self.verdict == GREEN

    def describe(self) -> str:
        return f"{self.verdict}: {self.detail}"


def record(
    command: tuple[str, ...],
    root: Path | None = None,
    timeout: int = 1800,
) -> tuple[Receipt, str]:
    """Run *command*, then stamp the tree it read, and return both.

    The stamp is taken **after** the run rather than before, so the receipt
    describes the tree as it stood when the last assertion executed.  If the run
    itself mutated a tracked file, :func:`check` sees the post-run tree and a
    later edit still grades :data:`STALE` — the direction that fails closed.
    """
    proc = subprocess.run(
        command,
        cwd=str(root or tp.REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = proc.stdout + proc.stderr
    st = tp.stamp(root)
    receipt = Receipt(
        head=st.head,
        worktree_fingerprint=st.worktree_fingerprint,
        committed_fingerprint=st.committed_fingerprint,
        returncode=proc.returncode,
        counts=parse_summary(output),
        command=tuple(command),
        worktree=dict(st.worktree),
    )
    return receipt, output


def load(path: Path) -> Receipt | None:
    """Read a receipt, or ``None`` if there is not one to read.

    Every unreadable state collapses to ``None`` on purpose: a missing file, a
    truncated write from a crashed cycle, and a receipt from an older schema are
    the same thing to a caller — no evidence — and distinguishing them would
    invite a branch that treats one of them as evidence.
    """
    try:
        return Receipt.from_json(path.read_text())
    except (OSError, ValueError, KeyError):
        return None


def check(
    receipt_path: Path,
    root: Path | None = None,
    declared: dict[str, str] | None = None,
    uncovered_verdict: str | None = None,
) -> Verdict:
    """Is it safe to push the tree in hand?  :data:`GREEN` alone means yes.

    Decides in :data:`VERDICTS` order.  The two composed conditions — receipt
    matches the worktree, worktree-vs-``HEAD`` drift is declared — are checked
    at opposite ends so that the *unshipped-tree* verdict is only reached once
    the measurement itself is known good; reporting :data:`UNDECLARED` for a red
    run would name the less important of two problems.

    *uncovered_verdict* is a :mod:`ci_verdict` verdict for the CI job that runs
    whatever this receipt skipped, or ``None`` when unknown.  It is a parameter
    rather than a fetch because this gate runs before every push and must not
    need the network; :mod:`suite_coverage` explains why ``None`` does not fail
    closed here when it does everywhere else in this module.
    """
    receipt = load(receipt_path)
    if receipt is None:
        return Verdict(
            NO_RECEIPT,
            f"no readable suite receipt at {receipt_path} — nothing has been "
            "measured for this tree",
        )

    st = tp.stamp(root)
    ignored: tuple[str, ...] = ()
    if st.worktree_fingerprint != receipt.worktree_fingerprint:
        prior = receipt.worktree or _receipt_worktree(receipt_path)
        if not prior:
            return Verdict(
                STALE,
                "the tree moved after the suite ran, and the receipt carries no "
                "per-path digests — which paths moved cannot be asked, so the "
                "move cannot be shown harmless",
                receipt=receipt,
            )
        drift = tp._diff(prior, st.worktree)
        material, ignored = ins.filter_drift(drift)
        if material:
            return Verdict(
                STALE,
                "the tree moved after the suite ran on a path that a test can "
                f"read ({material.describe()})"
                + (f"; ignored inert: {', '.join(ignored)}" if ignored else ""),
                receipt=receipt,
                drift=material,
            )

    if receipt.executed == 0:
        return Verdict(
            VACUOUS,
            f"the run executed no tests (counts={receipt.counts or 'unparseable'}) "
            "— 'did not fail' is not 'passed'",
            receipt=receipt,
        )

    if receipt.returncode != 0 or receipt.failures:
        return Verdict(
            RED,
            f"the suite failed (rc={receipt.returncode}, "
            f"failures={receipt.failures}, counts={receipt.counts})",
            receipt=receipt,
        )

    if sc.uncovered_is_red(receipt.counts, uncovered_verdict):
        return Verdict(
            UNCOVERED_RED,
            "the receipt is green over part of the suite and the rest is known "
            f"red: {sc.of(receipt.counts).describe()} — the uncovered tests are "
            "the ones failing, so this green is not evidence about them",
            receipt=receipt,
        )

    undeclared = tp.undeclared_drift(st, root, declared)
    if undeclared:
        return Verdict(
            UNDECLARED,
            "the measured tree is not the tree being pushed: "
            + undeclared.describe(),
            receipt=receipt,
            drift=undeclared,
        )

    return Verdict(
        GREEN,
        f"{sc.of(receipt.counts).describe()}, none failed, "
        + (
            f"tree moved only on measured-inert paths ({', '.join(ignored)})"
            if ignored
            else "tree unchanged since"
        )
        + f" (head={receipt.head[:8]})",
        receipt=receipt,
    )


def _receipt_worktree(receipt_path: Path) -> dict[str, str]:
    """Per-path digests a receipt may carry alongside its fingerprint.

    :func:`record` stores only the fingerprint, which is enough to *detect*
    staleness but not to name the files.  A caller that wants named paths can
    write a ``worktree`` map into the receipt JSON; absent one, :func:`check`
    still reports :data:`STALE`, just without the path list.  Detection does not
    depend on the optional field — the fingerprint comparison is the test.
    """
    try:
        return json.loads(receipt_path.read_text()).get("worktree", {}) or {}
    except (OSError, ValueError):
        return {}


def _main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.push_preflight",
        description="Refuse to push a tree nobody ran the suite on (STATE #1).",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_rec = sub.add_parser("record", help="run the suite and write a receipt")
    p_rec.add_argument("--out", type=Path, required=True)
    p_rec.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="args after `--` are passed to pytest",
    )

    p_chk = sub.add_parser("check", help="exit 0 only if the push is licensed")
    p_chk.add_argument("receipt", type=Path)
    p_chk.add_argument(
        "--uncovered-verdict",
        default=None,
        help=(
            "ci_verdict verdict (PASS/FAIL/...) for the CI job running the half "
            "this receipt skips. Omitted means unknown, which does not refuse — "
            "the local suite always skips the slow half, so a default refusal "
            "would block every push (D-042)."
        ),
    )

    args = ap.parse_args(argv)

    if args.cmd == "record":
        # Unlink first, and this is the crash case rather than housekeeping.
        # `--out` is a fixed path (`/tmp/suite-receipt.json` in the cycle
        # order), `record` takes minutes, and the failure this module was built
        # for is a cycle that dies *during* it.  Leave the old file in place and
        # the corpse of the previous run is what `check` reads: well-formed,
        # green, and about a suite nobody ran today.  NO_RECEIPT is the verdict
        # D-082 specified for a crash, and it is only reachable if the crash
        # leaves nothing behind.
        args.out.unlink(missing_ok=True)
        extra = [a for a in args.pytest_args if a != "--"]
        cmd = ("python3", "-m", "pytest", *extra)
        receipt, output = record(tuple(cmd))
        args.out.write_text(receipt.to_json())
        tail = output.strip().splitlines()[-1:] or ["(no output)"]
        print(f"receipt written: {args.out} — rc={receipt.returncode} {tail[0]}")
        return 0 if receipt.returncode == 0 else 1

    verdict = check(args.receipt, uncovered_verdict=args.uncovered_verdict)
    print(verdict.describe())
    if not verdict.ok:
        print("=> push refused: a push is licensed by a green receipt, not by memory.")
    return 0 if verdict.ok else 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())
