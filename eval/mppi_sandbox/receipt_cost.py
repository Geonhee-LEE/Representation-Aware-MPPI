"""Price the suite against the cycle budget (STATE #1).

STATE's ``## Current bottleneck`` names a number and three remedies: the suite
costs **17m43 of a 35-min cycle budget**, and a *fast receipt subset*, a
*no-new-thrust-after-minute-N* rule, or *splitting grading out* would each fix
it.  It also says the three are "all real and all unpriced", and that is the
gap this module closes.  Unpriced is the operative word — the 12:00 cycle on
2026-08-10 reached EXECUTE with less than the suite's cost left, could not take
a receipt, and stranded; the 13:00 cycle spent itself entirely clearing that
strand.  Neither cycle was careless.  Both were spending against a budget
nobody had written down in the same units as the bill.

What this module is *not*
-------------------------

It is not a fast subset.  Choosing one is a decision with a cost — a receipt
taken over a subset is a weaker claim than one taken over the suite, and how
much weaker depends on which tests the subset drops.  Shipping the subset
before the price is the D-016 shape in reverse: a runnable slice that nobody
can say is the right slice.  So this module answers the question a subset
proposal has to survive — *what would it cost and what would it stop
watching* — and leaves the choosing to Q-126.

The truncation trap
-------------------

``pytest --durations=N`` prints the **slowest N** and silently omits the rest.
Summing what it printed therefore yields a number that is not the suite's cost
and is not labelled as such: it is a lower bound wearing a total's clothes.
The failure is quiet in the dangerous direction — a truncated report makes the
dropped tail look free, so a subset priced off it looks cheaper and safer than
it is, which is precisely backwards.

So :func:`price` refuses unless it can reconcile the report against an
independently known suite total: :data:`COMPLETE` when the reported durations
account for the run, :data:`TRUNCATED` when they do not.  A ``TRUNCATED``
report still yields *bounds* — the omitted tail has a known aggregate size even
when its per-test breakdown is gone — and those are returned as bounds rather
than as an estimate.  D-042's asymmetry: an instrument that can only clear a
proposal should not be trusted to clear one.

Nothing here simulates.  It parses text and does arithmetic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

#: The report accounts for the run: per-test detail exists for effectively all
#: of the wall clock, so a subset's price is a measurement.
COMPLETE = "COMPLETE"

#: The report omits a tail.  A subset's price is bracketed, not known: every
#: dropped-but-unreported test could be anywhere from free to the whole gap.
TRUNCATED = "TRUNCATED"

#: No durations lines at all.  Distinct from ``TRUNCATED`` — a report with no
#: rows is not a very truncated report, it is the absence of a measurement, and
#: collapsing the two would let an empty file price a subset at zero.
NO_DURATIONS = "NO_DURATIONS"

#: pytest's duration line: ``12.34s call     path/to/test_x.py::test_y``.
#: The phase is captured because ``setup``/``teardown`` rows for one test are
#: separate lines, and a per-test cost that ignores its own fixture setup would
#: under-price exactly the sim-bound tests this exists to find.
_DURATION_RE = re.compile(
    r"^\s*(?P<seconds>\d+(?:\.\d+)?)s\s+"
    r"(?P<phase>setup|call|teardown)\s+"
    r"(?P<nodeid>\S+)\s*$"
)

#: pytest's summary line, e.g. ``==== 2263 passed, 158 skipped in 1063.21s ====``
#: (optionally ``(0:17:43)``).  This is the independent total the reported rows
#: are reconciled against — independent because pytest measures it separately
#: from the per-test clocks, so agreement between them is evidence rather than
#: a tautology.
_SUMMARY_RE = re.compile(r"\bin\s+(?P<seconds>\d+(?:\.\d+)?)s\b")


@dataclass(frozen=True)
class Duration:
    """One ``(phase, test)`` timing row."""

    seconds: float
    phase: str
    nodeid: str

    @property
    def module(self) -> str:
        """The file part of the nodeid.

        Grouping is by module rather than by test because that is the
        granularity a subset can actually be expressed in — pytest selects
        files and directories cheaply, individual nodeids only via a growing
        literal list that goes stale the moment someone adds a test.
        """
        return self.nodeid.split("::", 1)[0]


def parse_durations(text: str) -> tuple[Duration, ...]:
    """Every duration row in *text*, in file order.

    Lines that are not duration rows are ignored rather than raising: the input
    is a whole pytest run's stdout, most of which is not this.
    """
    out: list[Duration] = []
    for line in text.splitlines():
        m = _DURATION_RE.match(line)
        if m:
            out.append(
                Duration(
                    seconds=float(m.group("seconds")),
                    phase=m.group("phase"),
                    nodeid=m.group("nodeid"),
                )
            )
    return tuple(out)


def parse_total(text: str) -> float | None:
    """Wall-clock seconds from pytest's summary line, or ``None`` if absent.

    ``None`` is not zero and is not an error — it means the reconciliation
    :func:`price` performs cannot be performed, which downgrades the verdict
    rather than failing it.
    """
    matches = _SUMMARY_RE.findall(text)
    return float(matches[-1]) if matches else None


def by_module(durations: tuple[Duration, ...]) -> dict[str, float]:
    """Total seconds per module, summed across all phases.

    Summed across phases deliberately: a sim-bound test that pays its cost in a
    session fixture would otherwise read as free at ``call`` time, which is the
    reading that would most mislead a subset proposal.
    """
    out: dict[str, float] = {}
    for d in durations:
        out[d.module] = out.get(d.module, 0.0) + d.seconds
    return out


@dataclass(frozen=True)
class Price:
    """What a candidate subset costs, and what it stops watching."""

    verdict: str
    #: Seconds the subset would spend.
    kept_seconds: float
    #: Seconds the subset would not spend — the saving, on reported rows only.
    dropped_seconds: float
    #: Wall clock the run actually took, if the summary line was present.
    total_seconds: float | None
    #: Reported seconds unaccounted for by any row — the truncated tail.  Zero
    #: when the report is complete.
    unreported_seconds: float
    kept_modules: tuple[str, ...] = ()
    dropped_modules: tuple[str, ...] = ()

    @property
    def kept_upper_bound(self) -> float:
        """Worst case for the subset: the whole unreported tail is inside it.

        The bound that matters.  A subset is proposed because it fits a budget,
        so the question it has to survive is not "what did the rows say" but
        "how bad can this be given what the rows did not say".
        """
        return self.kept_seconds + self.unreported_seconds

    @property
    def is_priced(self) -> bool:
        """Is ``kept_seconds`` a measurement rather than a lower bound?"""
        return self.verdict == COMPLETE

    def describe(self) -> str:
        if self.verdict == NO_DURATIONS:
            return (
                "NO_DURATIONS: no duration rows parsed — rerun with "
                "`--durations=0`; a subset cannot be priced off an empty report"
            )
        head = (
            f"{self.verdict}: subset costs {self.kept_seconds:.1f}s "
            f"({len(self.kept_modules)} modules), drops {self.dropped_seconds:.1f}s "
            f"({len(self.dropped_modules)} modules)"
        )
        if self.verdict == TRUNCATED:
            head += (
                f"; {self.unreported_seconds:.1f}s unreported, so the subset is "
                f"bounded by {self.kept_upper_bound:.1f}s, not priced at "
                f"{self.kept_seconds:.1f}s"
            )
        return head


def price(
    text: str,
    keep: tuple[str, ...],
    tolerance: float = 0.02,
) -> Price:
    """Price the subset consisting of modules in *keep*.

    *tolerance* is the fraction of the run's wall clock the reported rows may
    fail to account for while still grading :data:`COMPLETE`.  It is not zero
    because pytest's own collection and reporting overhead is real and is not
    attributable to any test — insisting on exact reconciliation would grade
    every honest complete report ``TRUNCATED``, and a check that is red on the
    good case is D-044's muted check.
    """
    durations = parse_durations(text)
    if not durations:
        return Price(
            verdict=NO_DURATIONS,
            kept_seconds=0.0,
            dropped_seconds=0.0,
            total_seconds=parse_total(text),
            unreported_seconds=0.0,
        )

    grouped = by_module(durations)
    keep_set = set(keep)
    kept = {m: s for m, s in grouped.items() if m in keep_set}
    dropped = {m: s for m, s in grouped.items() if m not in keep_set}

    total = parse_total(text)
    reported = sum(grouped.values())
    # Clamped at zero: rows can exceed the summary total (phases overlap under
    # xdist, and setup shared by many tests is billed to each), and a negative
    # "unreported tail" is not a thing a bound can be built from.
    unreported = max(0.0, (total - reported)) if total is not None else 0.0

    if total is None:
        verdict = TRUNCATED
    elif unreported <= tolerance * total:
        verdict = COMPLETE
    else:
        verdict = TRUNCATED

    return Price(
        verdict=verdict,
        kept_seconds=sum(kept.values()),
        dropped_seconds=sum(dropped.values()),
        total_seconds=total,
        unreported_seconds=unreported,
        kept_modules=tuple(sorted(kept)),
        dropped_modules=tuple(sorted(dropped)),
    )


@dataclass(frozen=True)
class Budget:
    """Cycle-budget arithmetic in the units the bill arrives in."""

    suite_seconds: float
    budget_seconds: float
    #: Seconds a cycle spends on everything that is not the suite.
    overhead_seconds: float

    @property
    def runs_affordable(self) -> int:
        """How many suite runs fit after overhead.  Floor, never rounded up."""
        spare = self.budget_seconds - self.overhead_seconds
        if self.suite_seconds <= 0:
            return 0
        return max(0, int(spare // self.suite_seconds))

    @property
    def latest_start_seconds(self) -> float:
        """Minute-of-cycle after which starting the suite strands the cycle.

        This is the number the 12:00 strand needed and did not have.  Negative
        means the suite cannot fit at all — reported as a negative rather than
        clamped to zero, because "you had -190s of slack" and "you had none"
        are different situations and only one of them is fixed by starting
        earlier.
        """
        return self.budget_seconds - self.suite_seconds

    def strands(self, started_at_seconds: float) -> bool:
        """Would a suite started at *started_at_seconds* overrun the budget?"""
        return started_at_seconds > self.latest_start_seconds


#: The module whose import marks a test as part of the guard meta-suite.
#: ``guard_reflexivity`` enumerates the guard pool, so a test that imports it
#: is a test *about the pool* rather than about the planner.
GUARD_POOL_MODULE = "guard_reflexivity"

#: The diff touches the guard meta-suite's subject, so the exemption is void
#: and the receipt must be taken over the full suite.
EXEMPTION_VOID = "EXEMPTION_VOID"

#: The diff leaves the guard sources and their meta-tests untouched, so the
#: 390s those modules cost is spent re-measuring something that cannot have
#: moved.  The receipt is taken over the suite minus that meta-suite.
EXEMPTION_ACTIVE = "EXEMPTION_ACTIVE"

#: No guard meta-suite could be derived — the scan found nothing importing
#: :data:`GUARD_POOL_MODULE`.  Distinct from ``EXEMPTION_ACTIVE`` with an empty
#: drop set, because "nothing to drop" and "the derivation broke" look
#: identical in the output and only one of them is safe to act on.  Fails
#: closed: the caller pays the full suite.
NO_META_SUITE = "NO_META_SUITE"


def guard_meta_suite(root: Path | None = None) -> tuple[str, ...]:
    """Test modules whose subject is the guard pool itself, repo-relative.

    **Derived, never typed** (D-047/D-073).  The membership rule is one line —
    *does this test module import the pool enumerator* — so a guard meta-test
    written next cycle joins the set by existing, and the exemption narrows
    itself without anyone remembering to widen a literal.  A hand-listed
    ``{"test_exemption_masking", ...}`` would be a second statement of a set
    that already states itself, which is the exact defect D-047 found in the
    push gate's hand-copied local-only grep.

    The rule is *import*, not *mention*, and the first cut got this wrong in a
    way worth recording: a bare substring scan swept up this function's own
    test module, whose only occurrence of the name is the string
    ``"test_guard_reflexivity"`` inside an assertion **about this derivation**.
    A membership rule that a module joins by describing it is not a
    derivation — it is self-reference — so the scan reads import statements.
    """
    base = (root or _repo_root()) / "eval" / "mppi_sandbox" / "tests"
    if not base.is_dir():
        return ()
    out: list[str] = []
    for path in sorted(base.glob("test_*.py")):
        try:
            text = path.read_text()
        except OSError:  # pragma: no cover - unreadable file
            continue
        if any(
            "import" in line and GUARD_POOL_MODULE in line
            for line in text.splitlines()
        ):
            out.append(f"eval/mppi_sandbox/tests/{path.name}")
    return tuple(out)


def _is_guard_source(rel: str) -> bool:
    """Is *rel* a guard **source** — a non-test module under the sandbox?

    This is D-177's stated trigger surface, ``eval/mppi_sandbox/*.py``.  The
    ``tests/`` subtree is excluded here and handled separately, because a test
    edit and a source edit void the exemption for different reasons and
    conflating them makes the reported reason wrong.
    """
    if not rel.endswith(".py"):
        return False
    parts = rel.split("/")
    return (
        len(parts) == 3
        and parts[0] == "eval"
        and parts[1] == "mppi_sandbox"
        and not parts[2].startswith("test_")
    )


@dataclass(frozen=True)
class Scope:
    """Which tests this cycle's receipt may be taken over, and why."""

    verdict: str
    #: Modules dropped from the receipt.  Empty whenever the exemption is void.
    dropped: tuple[str, ...]
    #: The changed paths that voided the exemption, empty if it holds.
    triggers: tuple[str, ...]

    @property
    def is_full(self) -> bool:
        """Must the receipt be taken over the whole suite?"""
        return self.verdict != EXEMPTION_ACTIVE

    def pytest_args(self, default: tuple[str, ...]) -> tuple[str, ...]:
        """The paths to hand pytest, given the cycle's *default* target list.

        Returns *default* unchanged when the exemption is void — the fast path
        is the special case and the full suite is the fallback, so a caller
        that ignores this object entirely still takes a valid receipt.
        """
        if self.is_full:
            return default
        kept = tuple(a for a in default if a not in self.dropped)
        return kept + tuple(f"--ignore={m}" for m in self.dropped)

    def describe(self) -> str:
        if self.verdict == EXEMPTION_VOID:
            head = f"{EXEMPTION_VOID}: full suite required"
            why = ", ".join(self.triggers[:4])
            more = f" (+{len(self.triggers) - 4} more)" if len(self.triggers) > 4 else ""
            return f"{head} — diff touches {why}{more}"
        if self.verdict == NO_META_SUITE:
            return f"{NO_META_SUITE}: full suite required — no meta-suite derived"
        return (
            f"{EXEMPTION_ACTIVE}: receipt over suite minus "
            f"{len(self.dropped)} guard meta-suite module(s)"
        )


def scope(changed: tuple[str, ...], root: Path | None = None) -> Scope:
    """D-177's diff-conditional receipt scope.

    The guard meta-suite is *reflexive*: its subject is the guard pool, which
    moves only when a cycle edits the sandbox's own modules.  On a cycle that
    edits none of them, its 390s re-measures something that cannot have
    changed.  On a cycle that edits one, it is the only thing watching — so a
    **fixed** drop would blind the suite in precisely the cycle whose pins can
    break.  Hence conditional on the diff rather than chosen once.

    The exemption is void when the diff touches a guard source *or* one of the
    meta-tests themselves.  D-177's letter names only the sources; the tests
    are added here because the exemption's premise is "the claims about the
    pool have not moved", and editing an assertion moves them as surely as
    editing the code it reads.  Widening the void condition can only cost a
    full suite that was already the status quo.
    """
    meta = guard_meta_suite(root)
    if not meta:
        return Scope(verdict=NO_META_SUITE, dropped=(), triggers=())
    exempt = set(meta)
    triggers = tuple(
        c for c in changed if _is_guard_source(c) or c in exempt
    )
    if triggers:
        return Scope(verdict=EXEMPTION_VOID, dropped=(), triggers=triggers)
    return Scope(verdict=EXEMPTION_ACTIVE, dropped=meta, triggers=())


def _repo_root() -> Path:
    from pathlib import Path as _P

    return _P(__file__).resolve().parents[2]


#: The base :func:`changed_paths` diffs against when no receipt licenses a
#: nearer one.  ``main`` is the conservative answer — it asks the same question
#: CI asks — and it is what every failure mode below falls back to.
DEFAULT_BASE = "main"

#: A full receipt was found and its commit is the base.  The only verdict that
#: moves the base off :data:`DEFAULT_BASE`.
BASE_RECEIPT = "BASE_RECEIPT"

#: No receipt on disk, or it would not parse.  The receipt lives in ``/tmp`` and
#: does not survive a reboot, so this is the ordinary case on a cold machine —
#: not an error, just no licence to narrow.
BASE_NO_RECEIPT = "NO_RECEIPT"

#: The last receipt was itself taken over a *narrowed* suite, so it never ran
#: the guard meta-suite and cannot certify that the pool's claims still hold.
#: Using its commit as the base would let the exemption bootstrap itself off a
#: run that skipped the very tests the exemption is trading away.
BASE_SCOPED_RECEIPT = "SCOPED_RECEIPT"

#: The receipt names a commit this repo cannot resolve (a receipt carried over
#: from another worktree, or a commit since garbage-collected).  Fails closed:
#: an unresolvable base would make ``git diff`` error and the union come back
#: empty, which reads exactly like "nothing changed".
BASE_UNKNOWN_COMMIT = "UNKNOWN_COMMIT"


@dataclass(frozen=True)
class Base:
    """Which commit the exemption's diff is taken from, and on whose authority.

    :attr:`ref` is always usable — every refusal below resolves to
    :data:`DEFAULT_BASE` rather than to ``None``, so a caller that ignores the
    verdict entirely still gets the conservative behaviour that stood before
    this function existed.
    """

    verdict: str
    ref: str
    detail: str = ""

    @property
    def is_receipt(self) -> bool:
        return self.verdict == BASE_RECEIPT

    def describe(self) -> str:
        if self.is_receipt:
            return f"{BASE_RECEIPT}: diffing against {self.ref[:8]} — {self.detail}"
        return f"{self.verdict}: base falls back to {self.ref} — {self.detail}"


def _receipt_is_full(command: tuple[str, ...]) -> bool:
    """Did the run behind this receipt cover the guard meta-suite?

    Read off :func:`Scope.pytest_args`' own narrowing mechanism — the
    ``--ignore=`` flags it emits — rather than off a flag someone remembers to
    set.  If that mechanism ever changes shape, this returns ``False`` and the
    base stays ``main``, which is the direction that costs a full suite instead
    of skipping one.
    """
    return not any(str(a).startswith("--ignore=") for a in command)


def exemption_base(
    receipt_path: Path | None = None, root: Path | None = None
) -> Base:
    """Q-129's base: the commit the last **full** receipt was taken on.

    The exemption in :func:`scope` claims that the guard pool's subject has not
    moved *since it was last measured whole*.  Read against ``main`` that claim
    is asked over the branch's entire life, so on a long-lived branch — this one
    has been open 11 days and carries 94 trigger paths — every cycle answers
    ``EXEMPTION_VOID`` and the exemption is inert from the cycle it shipped.
    ``main`` is not wrong, it is answering a different question: *what does this
    PR change*, which is CI's question, not the receipt's.

    Q-129 costed this at a ``push_preflight`` change — "that commit is recorded
    nowhere; the receipt must be taught to carry a tree hash".  It already
    carries it: :attr:`push_preflight.Receipt.head` has been written by
    :func:`push_preflight.record` since the receipt existed, because
    :func:`tree_provenance.stamp` returns it and every field of the stamp was
    kept.  So the work here is a *read*, and no new field is written — the same
    shape D-182 found one cycle earlier, where a quantity the instrument needed
    turned out to be measured already and merely dropped.

    Three refusals, all resolving to :data:`DEFAULT_BASE`, because each one
    means the receipt cannot license a narrower question and the conservative
    base is never unsafe — only expensive.
    """
    from pathlib import Path as _P

    from . import cycle_wallclock as cw
    from . import push_preflight as pp

    base_dir = _P(str(root or _repo_root()))
    # The default path is imported from the one module that already states it
    # (D-047): two spellings of ``/tmp/suite-receipt.json`` is two places for it
    # to drift, and this one would drift silently — a wrong path reads exactly
    # like a missing receipt, i.e. the fallback, i.e. nothing goes red.
    path = receipt_path if receipt_path is not None else cw.DEFAULT_RECEIPT
    receipt = pp.load(_P(str(path)))
    if receipt is None:
        return Base(BASE_NO_RECEIPT, DEFAULT_BASE, f"no readable receipt at {path}")
    if not _receipt_is_full(receipt.command):
        return Base(
            BASE_SCOPED_RECEIPT,
            DEFAULT_BASE,
            "last receipt was narrowed, so it never ran the meta-suite",
        )
    if not _commit_exists(receipt.head, base_dir):
        return Base(
            BASE_UNKNOWN_COMMIT,
            DEFAULT_BASE,
            f"receipt names {receipt.head[:8]}, unresolvable here",
        )
    return Base(BASE_RECEIPT, receipt.head, "last full receipt")


def _commit_exists(sha: str, root: Path) -> bool:
    import subprocess

    if not sha:
        return False
    try:
        res = subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        return False
    return res.returncode == 0


def changed_paths(root: Path | None = None, base: str | None = None) -> tuple[str, ...]:
    """Every path this branch touches relative to *base*, plus the worktree.

    Three reads unioned, because a cycle's diff is spread across all three at
    the moment the scope question is asked: committed-since-base, staged, and
    unstaged.  Reading only the committed half would call the exemption active
    on a cycle whose guard edit is sitting uncommitted — the false green this
    function exists to refuse.

    *base* defaults to :data:`DEFAULT_BASE`; :func:`exemption_base` is what
    supplies a nearer one.  The three-dot form is kept for a receipt base too:
    the receipt's commit is normally an ancestor of ``HEAD``, where two-dot and
    three-dot agree, and where they disagree (a rebase moved it off the branch)
    three-dot diffs from the merge-base and so reports a *wider* change set —
    more triggers, more full suites, which is the direction that fails closed.
    """
    import subprocess

    root_dir = str(root or _repo_root())
    ref = base or DEFAULT_BASE
    out: set[str] = set()
    for cmd in (
        ["git", "diff", "--name-only", f"{ref}...HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--name-only", "--cached"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        try:
            res = subprocess.run(
                cmd, cwd=root_dir, capture_output=True, text=True, timeout=60
            )
        except (OSError, subprocess.SubprocessError):  # pragma: no cover
            continue
        if res.returncode == 0:
            out.update(line for line in res.stdout.splitlines() if line.strip())
    return tuple(sorted(out))


def _main(argv: list[str] | None = None) -> int:
    """Price a candidate subset off a kept run log.

    A CLI rather than an import-and-call, because the input is now a file that
    ``push_preflight record`` leaves behind by default (:func:`push_preflight.log_path`)
    and the whole point of keeping it is that reading it costs nothing.  The
    exit code follows the verdict: non-zero on :data:`TRUNCATED` and
    :data:`NO_DURATIONS`, since both mean *this output cannot price a subset*
    and the caller should not proceed as though a number came back.  The bound
    is still printed — a refusal that withholds what it does know is one people
    route around.
    """
    import argparse
    from pathlib import Path

    ap = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.receipt_cost",
        description="Price a candidate fast-receipt subset against a run log.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_pr = sub.add_parser("price", help="price a subset off a pytest run log")
    p_pr.add_argument("log", type=Path, help="terminal output of a --durations=0 run")
    p_pr.add_argument(
        "--keep",
        action="append",
        default=[],
        help="module path to keep in the subset (repeatable)",
    )
    p_pr.add_argument("--tolerance", type=float, default=0.02)

    p_mod = sub.add_parser("modules", help="list modules by cost, most expensive first")
    p_mod.add_argument("log", type=Path)
    p_mod.add_argument("--top", type=int, default=0, help="0 = all")

    p_sc = sub.add_parser("scope", help="D-177 diff-conditional receipt scope")
    p_sc.add_argument(
        "--path",
        action="append",
        default=None,
        help="treat these as the diff instead of reading git (repeatable)",
    )

    args = ap.parse_args(argv)

    if args.cmd == "scope":
        if args.path:
            changed = tuple(args.path)
        else:
            b = exemption_base()
            print(b.describe())
            changed = changed_paths(base=b.ref)
        s = scope(changed)
        print(s.describe())
        for m in s.dropped:
            print(f"  drop {m}")
        # rc mirrors the verdict rather than success: 0 only when the receipt
        # may be narrowed, so a caller can gate on it without parsing prose.
        return 0 if not s.is_full else 1
    try:
        text = args.log.read_text()
    except OSError as exc:
        print(f"cannot read {args.log}: {exc}")
        return 2

    if args.cmd == "modules":
        grouped = by_module(parse_durations(text))
        total = parse_total(text)
        rows = sorted(grouped.items(), key=lambda kv: -kv[1])
        if args.top:
            rows = rows[: args.top]
        for mod, secs in rows:
            share = f" ({secs / total:6.2%})" if total else ""
            print(f"{secs:9.2f}s{share}  {mod}")
        reported = sum(grouped.values())
        print(
            f"-- {len(grouped)} modules, {reported:.1f}s reported"
            + (f", {total:.1f}s wall clock" if total is not None else ", no total")
        )
        return 0

    p = price(text, tuple(args.keep), tolerance=args.tolerance)
    print(p.describe())
    if p.total_seconds is not None:
        print(f"   wall clock {p.total_seconds:.1f}s, reported rows account for "
              f"{p.total_seconds - p.unreported_seconds:.1f}s")
    return 0 if p.is_priced else 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())
