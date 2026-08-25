"""The TSV ``timestamp`` column is typed, not read — measure it, then stop writing it.

Every cycle appends one row to ``results/<slug>.tsv``::

    timestamp                   commit    metric              status  description
    2026-08-05T08:35:00+09:00   9d2ef1a   sandbox:pass=1608   keep    ...

Four of those five fields are records of something.  The first is a **claim
about a clock**, and the constitution asks the executor to type it by hand.

Why a hand-typed clock reading goes wrong in one direction
----------------------------------------------------------

A cycle does not know what time it finished.  It knows what hour it *started*
in — cron names that — and it estimates the elapsed minutes.  Measured on this
branch, that estimate runs about **3× long**: the 2026-08-09 07:00 and 08:00
cycles self-reported "~85 min" and "~82 min" against wrapper-recorded **28m01**
and **28m38**.  Start hour plus an inflated estimate lands *ahead* of the real
clock, so the error has a sign, and the sign is what makes it detectable.

:mod:`cycle_artifacts` already refutes this column as a dating key — its
docstring says so in as many words ("a cycle that overruns types the hour it
finished in") and routes around it with a ``commit`` ∩ ``git blame``
intersection.  What was never asked is **how far it has drifted**, and routing
around a bad field while leaving the writer producing more of it is the cheap
half: every other consumer of ``results/*.tsv`` — ``aggregate_results.sh``,
``RESULTS.md``, a human reading the table — still gets the typed number.

The reading, and why it is a proof rather than a correlation
-------------------------------------------------------------

A row is written and *then* committed.  So the stamp must be **at or before**
the commit that introduced that line; a stamp after it would be a clock reading
taken after the commit that contains it, which is not a thing a clock can do.
``git blame`` supplies the introducing commit, and the comparison is a deduction
with no threshold in it.

Over all 34 ``results/*.tsv`` files, 183 rows, at the time of writing:

===============================  =====
dated by blame                   183
stamp at-or-before its commit    143
**stamp after its commit**       **40**
worst overshoot                  **+128 min**
===============================  =====

The honest 143 behave exactly as the mechanism predicts they should: median lag
**1.2 min** — write the row, commit it a minute later.  That distribution is
the control.  Without it, "40 rows are late" could as easily have been a bug in
the blame key as a bug in the column.

A second, independent signature agrees
---------------------------------------

A clock read with ``date +%H:%M:%S`` lands on ``seconds == 00`` with p = 1/60.
Across the same 183 rows it happens **63** times against a chance expectation of
**3.0**, and **36 of the 40** impossible rows are among them.  Two signatures
that agree on the same rows make this a *mechanism* rather than a coincidence.

It is nevertheless **reported and never thresholded** — the same discipline
``scorable_band.one_run_rungs`` follows.  :attr:`TimestampAudit.verdict` keys on
the overshoot alone, because that one is a deduction: no defensible constant
separates "suspiciously round" from "round".  Publishing a number and grading on
it are different acts, and only the second one needs a threshold nobody can
justify.

The audit reports and the gate refuses, and they cover disjoint rows (D-044)
----------------------------------------------------------------------------

The 40 bad rows **cannot be repaired**.  The constitution's soft limits make
``results/*.tsv`` append-only in as many words ("Never edit past rows"), and
rewriting them would also destroy the blame key that convicts them — D-102's
lesson, that a repair deletes its own evidence, arriving here a third time.

So a gate over the committed population would be red on every cycle forever,
and D-044 says exactly what happens to such a check: it gets muted.  The split
is therefore by *reparability*, not by severity:

:func:`audit`
    The whole committed population.  A reading.  Always ``rc=0``.  Nobody can
    clear it and nobody is asked to.

:func:`check`
    Only the rows this cycle is about to add — uncommitted, still in the working
    tree, still editable.  ``rc=1`` if one is stamped in the future.

The gate's test is ``stamp > now``, not ``stamp > commit``, because at write
time there is no commit yet.  It is strictly weaker — it catches the inflated
estimate only once the inflation exceeds the row's own age — and it has a
**false-positive rate of exactly zero** for an honest clock read, which is what
lets it fail closed without becoming the thing everyone passes with ``--force``.

Where the gate is placed is load-bearing, and it is the weak point
------------------------------------------------------------------

:func:`check`'s population is *uncommitted* rows, and the constitution's cycle
order is ``TSV → commit → push``.  So by the time the push chain runs, the row
is already committed and the gate reads ``NO_PENDING_ROW`` — **vacuous by
placement**.  It has to run in the window between the append and
``git add results/``, which is why it is wired there in
``scripts/prompts/auto_research.md`` rather than into the ``&&`` chain beside
:mod:`push_preflight`, where every other check on this branch lives.

That is a placement a future cycle can quietly get wrong, so the design does not
rest on it: :attr:`TimestampAudit.post_epoch_impossible` sees the row one cycle
later whether or not the gate ever ran.  A guard whose only evidence of working
is that somebody called it in the right place is a guard with no evidence.

The half :mod:`cycle_artifacts` skipped
----------------------------------------

Detecting a typed stamp is still worse than not typing one.  :func:`row` and
``python3 -m eval.mppi_sandbox.tsv_timestamp row --append`` build the line with
the clock, so the executor stops transcribing the field it keeps getting wrong.
The gate exists for the cycle that writes the row by hand anyway.
"""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))

STATUSES: tuple[str, ...] = ("keep", "discard", "crash", "in_progress")
"""The constitution's ``status`` domain for a TSV row."""

HEADER: tuple[str, ...] = ("timestamp", "commit", "metric", "status", "description")

_ENV = {"LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin:/usr/local/bin"}

_SHA_RE = re.compile(r"[0-9a-f]{40}")

CHANCE_ROUND_SECOND = 1.0 / 60.0
"""P(a clock reading lands on ``seconds == 00``).  Reported, never thresholded."""

EPOCH = datetime(2026, 8, 9, 11, 0, tzinfo=KST)
"""When :func:`row` landed — the first moment a cycle could stop typing the field.

:attr:`TimestampAudit.verdict` is ``TYPED`` **forever**: the 40 offending rows
are append-only and no future good behaviour can empty that set.  So the verdict
alone cannot answer the question the next cycle actually has — *did we just add a
41st?* — and a reading that cannot change is one nobody re-reads.

:attr:`TimestampAudit.post_epoch_impossible` is the part that can move.  It is
**reported, not gated**, for the same reason the legacy rows are: by the time a
bad row is committed it is unrepairable too, so a test asserting it empty would
convert the first regression into a permanent red (D-044 again).  What it buys
is that the regression is *visible* — and it is the backstop for :func:`check`
being bypassed, which is a live risk, see below.
"""


def _root(root: Path | None = None) -> Path:
    return Path(root) if root is not None else Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Row:
    """One TSV row, with the two times that ought to agree.

    ``stamp`` is what the row claims; ``committed_at`` is when git says the line
    entered the tree.  ``committed_at is None`` means git cannot date the line —
    it is uncommitted — which is not a defect, it is the state every row is in
    for the few minutes between the append and the commit.
    """

    path: str
    lineno: int
    stamp: datetime
    committed_at: datetime | None

    @property
    def dated(self) -> bool:
        """Can git date this line?  Uncommitted rows cannot be audited."""
        return self.committed_at is not None

    @property
    def overshoot_min(self) -> float | None:
        """Minutes the stamp runs *past* its introducing commit; ``None`` if undated.

        Positive is the impossible direction.  Negative is the ordinary one and
        its magnitude is the write→commit lag, which is how the honest
        population is characterised rather than merely assumed.
        """
        if self.committed_at is None:
            return None
        return (self.stamp - self.committed_at).total_seconds() / 60.0

    @property
    def impossible(self) -> bool:
        """A clock reading taken after the commit that contains it."""
        over = self.overshoot_min
        return over is not None and over > 0

    @property
    def round_second(self) -> bool:
        """The typed signature: ``seconds == 00``.  Evidence, not proof."""
        return self.stamp.second == 0


def _blame_times(path: Path, root: Path) -> dict[int, datetime]:
    """Line number → commit time of the commit that **added** that line.

    Uncommitted lines blame to the all-zero sha and are reported as absent,
    which is what routes them to :func:`check` instead of :func:`audit`.
    """
    proc = subprocess.run(
        ["git", "blame", "--line-porcelain", "--", str(path)],
        cwd=str(root), capture_output=True, text=True,
        env={**_ENV, "TZ": "Asia/Seoul"},
    )
    if proc.returncode != 0:
        return {}
    out: dict[int, datetime] = {}
    lineno: int | None = None
    uncommitted = False
    for line in proc.stdout.splitlines():
        head = line.split(" ")
        if len(head) >= 3 and _SHA_RE.fullmatch(head[0]):
            lineno = int(head[2]) if head[2].isdigit() else None
            uncommitted = head[0] == "0" * 40
        elif line.startswith("committer-time ") and lineno is not None and not uncommitted:
            epoch = int(line.split(" ", 1)[1])
            out[lineno] = datetime.fromtimestamp(epoch, tz=KST)
    return out


def tsv_files(root: Path | None = None) -> tuple[Path, ...]:
    return tuple(sorted((_root(root) / "results").glob("*.tsv")))


def rows(root: Path | None = None) -> tuple[Row, ...]:
    """Every parseable row of every ``results/*.tsv``, paired with its blame time.

    Rows whose ``timestamp`` field does not parse are skipped rather than
    counted as findings: this module measures a column that is being written
    wrongly, and a field that is not a timestamp at all is a different defect
    with a different fix.
    """
    base = _root(root)
    out: list[Row] = []
    for path in tsv_files(base):
        blame = _blame_times(path, base)
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            fields = line.split("\t")
            if len(fields) < len(HEADER) or fields[0] == HEADER[0]:
                continue
            try:
                stamp = datetime.fromisoformat(fields[0].strip())
            except ValueError:
                continue
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=KST)
            out.append(Row(
                path=str(path.relative_to(base)),
                lineno=i,
                stamp=stamp,
                committed_at=blame.get(i),
            ))
    return tuple(out)


@dataclass(frozen=True)
class TimestampAudit:
    """The committed population.  A reading — see the module docstring on D-044.

    ``NO_ROW`` is named because every other field of this object reads
    identically to a clean population when there is nothing to read: ``dated``
    is 0, ``impossible`` is ``()``, ``worst_overshoot_min`` is ``None``.  A
    caller distinguishing "the column is fine" from "there was no column"
    cannot do it from any other field — the sixth-plus instance of the D-107
    shape on this branch.
    """

    all_rows: tuple[Row, ...]

    @property
    def dated(self) -> tuple[Row, ...]:
        """Rows git can date.  The audit's denominator."""
        return tuple(r for r in self.all_rows if r.dated)

    @property
    def undated(self) -> tuple[Row, ...]:
        """Uncommitted rows — :func:`check`'s population, not this one's."""
        return tuple(r for r in self.all_rows if not r.dated)

    @property
    def impossible(self) -> tuple[Row, ...]:
        return tuple(r for r in self.dated if r.impossible)

    @property
    def honest_lag_min(self) -> tuple[float, ...]:
        """Write→commit lag of the non-impossible rows, in minutes, positive.

        The control distribution.  A test that only ever looked at the 40 bad
        rows could not tell a broken column from a broken blame key; a median
        near one minute says the key is sound and the column is not.
        """
        return tuple(-r.overshoot_min for r in self.dated if not r.impossible)

    @property
    def worst_overshoot_min(self) -> float | None:
        over = [r.overshoot_min for r in self.impossible]
        return max(over) if over else None

    @property
    def round_seconds(self) -> tuple[Row, ...]:
        """The corroborating signature.  Reported, never thresholded."""
        return tuple(r for r in self.all_rows if r.round_second)

    @property
    def expected_round_seconds(self) -> float:
        return len(self.all_rows) * CHANCE_ROUND_SECOND

    @property
    def corroborated(self) -> tuple[Row, ...]:
        """Impossible *and* round-second — where the two signatures agree."""
        return tuple(r for r in self.impossible if r.round_second)

    @property
    def post_epoch_impossible(self) -> tuple[Row, ...]:
        """Impossible rows committed after :data:`EPOCH` — the part that can move.

        The legacy 40 are frozen, so the verdict is ``TYPED`` for good; this is
        the field that answers "did a cycle regress?".  Empty is the claim the
        writer is supposed to make true.  Reported, not gated — see :data:`EPOCH`.
        """
        return tuple(r for r in self.impossible if r.committed_at >= EPOCH)

    @property
    def legacy_impossible(self) -> tuple[Row, ...]:
        """The unrepairable population this module was written to measure."""
        return tuple(r for r in self.impossible if r.committed_at < EPOCH)

    @property
    def verdict(self) -> str:
        """``NO_ROW`` | ``CLOCK_READ`` | ``TYPED``.

        Keys on :attr:`impossible` alone.  The round-second excess is far larger
        evidence in the informal sense, and it is deliberately not in the
        verdict: grading on it needs a cutoff between "suspiciously round" and
        "round" that nobody can defend, while an overshoot is a deduction.
        """
        if not self.all_rows:
            return "NO_ROW"
        return "TYPED" if self.impossible else "CLOCK_READ"


def audit(root: Path | None = None) -> TimestampAudit:
    return TimestampAudit(all_rows=rows(root))


@dataclass(frozen=True)
class PendingCheck:
    """The gate.  Scoped to rows that are still editable, which is why it can fail closed.

    ``NO_PENDING_ROW`` is named for the same reason ``NO_ROW`` is: a cycle that
    appended nothing and a cycle that appended a good row are indistinguishable
    from :attr:`future` alone, and only one of them has discharged the
    constitution's "append a row" step.
    """

    pending: tuple[Row, ...]
    now: datetime

    @property
    def future(self) -> tuple[Row, ...]:
        """Rows claiming a clock reading that has not happened yet."""
        return tuple(r for r in self.pending if r.stamp > self.now)

    @property
    def verdict(self) -> str:
        """``NO_PENDING_ROW`` | ``STAMP_READ`` | ``STAMP_AHEAD``."""
        if not self.pending:
            return "NO_PENDING_ROW"
        return "STAMP_AHEAD" if self.future else "STAMP_READ"


def check(root: Path | None = None, *, now: datetime | None = None) -> PendingCheck:
    """Grade only the uncommitted rows — the ones a cycle can still fix."""
    return PendingCheck(
        pending=tuple(r for r in rows(root) if not r.dated),
        now=now or datetime.now(tz=KST),
    )


def row(commit: str, metric: str, status: str, description: str,
        *, now: datetime | None = None) -> str:
    """Build a TSV row whose ``timestamp`` is **read**, not typed.

    This is the half :mod:`cycle_artifacts` skipped.  ``now`` is injectable so
    the tests can pin the format without pinning the clock, and defaults to the
    real one so a caller cannot accidentally supply an estimate.
    """
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}; expected one of {STATUSES}")
    stamp = (now or datetime.now(tz=KST)).replace(microsecond=0)
    fields = (stamp.isoformat(), commit, metric, status, description.replace("\t", " "))
    return "\t".join(fields)


def append(branch: str, commit: str, metric: str, status: str, description: str,
           *, root: Path | None = None, now: datetime | None = None) -> Path:
    """Append a clock-read row to ``results/<slug>.tsv``, writing the header if new."""
    path = _root(root) / "results" / f"{branch.split('/')[-1]}.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    line = row(commit, metric, status, description, now=now)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    with path.open("a", encoding="utf-8") as fh:
        if not existing:
            fh.write("\t".join(HEADER) + "\n")
        elif not existing.endswith("\n"):
            fh.write("\n")
        fh.write(line + "\n")
    return path


def report(root: Path | None = None) -> str:  # pragma: no cover - display only
    a = audit(root)
    lines = [
        f"tsv_timestamp — {a.verdict}  "
        f"({len(a.all_rows)} rows in {len(tsv_files(root))} file(s), "
        f"{len(a.dated)} dated, {len(a.undated)} uncommitted)",
    ]
    if a.impossible:
        lag = sorted(a.honest_lag_min)
        median = lag[len(lag) // 2] if lag else float("nan")
        lines.append(
            f"  impossible (stamp after its own commit): {len(a.impossible)}/{len(a.dated)}"
            f"  worst +{a.worst_overshoot_min:.0f} min"
        )
        lines.append(
            f"  control — honest write->commit lag: median {median:.1f} min "
            f"over {len(lag)} rows"
        )
    lines.append(
        f"  seconds==00: {len(a.round_seconds)} vs {a.expected_round_seconds:.1f} by chance"
        f"  ({len(a.corroborated)} of the impossible rows agree)  [reported, not graded]"
    )
    for r in a.impossible[:5]:
        lines.append(f"    {r.path}:{r.lineno}  {r.stamp.isoformat()}  +{r.overshoot_min:.0f} min")
    if len(a.impossible) > 5:
        lines.append(f"    ... and {len(a.impossible) - 5} more")
    lines.append(
        f"  legacy (pre-{EPOCH.date()}): {len(a.legacy_impossible)}  "
        f"post-epoch regressions: {len(a.post_epoch_impossible)}"
    )
    lines.append("  => append-only (soft limits): these are unrepairable and NOT gated.")
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    import argparse

    ap = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.tsv_timestamp",
        description="Measure the hand-typed TSV timestamp column; refuse a future-stamped new row.",
    )
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("audit", help="reading over the committed population (always rc=0)")
    sub.add_parser("check", help="gate: rc=1 if an uncommitted row is stamped ahead of now")
    p_row = sub.add_parser("row", help="build a clock-read TSV row")
    p_row.add_argument("--commit", required=True)
    p_row.add_argument("--metric", required=True)
    p_row.add_argument("--status", required=True, choices=STATUSES)
    p_row.add_argument("--description", required=True)
    p_row.add_argument("--append", metavar="BRANCH",
                       help="append to results/<slug>.tsv instead of printing")
    args = ap.parse_args(argv)

    if args.cmd == "row":
        if args.append:
            path = append(args.append, args.commit, args.metric, args.status,
                          args.description)
            print(f"appended to {path}")
        else:
            print(row(args.commit, args.metric, args.status, args.description))
        return 0

    if args.cmd == "check":
        c = check()
        if c.verdict == "NO_PENDING_ROW":
            print("tsv_timestamp — NO_PENDING_ROW: no uncommitted TSV row to grade.")
            return 0
        if c.verdict == "STAMP_READ":
            print(f"OK: {len(c.pending)} uncommitted row(s), none stamped ahead of now.")
            return 0
        for r in c.future:
            ahead = (r.stamp - c.now).total_seconds() / 60.0
            print(f"ERROR: {r.path}:{r.lineno} stamped {r.stamp.isoformat()} "
                  f"— {ahead:.0f} min in the future")
        print("=> the stamp was typed, not read. Rebuild it with: "
              "python3 -m eval.mppi_sandbox.tsv_timestamp row --commit ... --append <branch>")
        return 1

    print(report())
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())
