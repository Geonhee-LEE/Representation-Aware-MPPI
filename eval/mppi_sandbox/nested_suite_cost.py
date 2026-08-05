"""The ceiling was never the bug: a nested suite run that outgrew its timeout.

Three cycles raised a CI ``timeout-minutes`` and read the next cancellation as
proof the number was still too small.  D-084 took ``fast`` 10 -> 30, D-085 took
``slow`` 60 -> 120, and STATE carried "redesign the split, do **not** raise 120
to 240" without a mechanism for *why* raising it would not work.  Here is the
mechanism, and it is an inequality between two numbers that live in different
files and were never compared:

===========================================  =========  ==========================
quantity                                     seconds    where it is declared
===========================================  =========  ==========================
the ``fast`` half's pytest step, on CI        **1396**   measured, run 30991167667
the timeout guarding a *nested* suite run     **900**    ``timeout: int = 900``
===========================================  =========  ==========================

Several instrument tests in the ``slow`` half observe the suite by **running it
in a subprocess** — :func:`predicate_vacuity.measure`,
:func:`predicate_inputs.measure`, and their ``measure_attributed`` siblings all
shell out to ``python -m pytest <DEFAULT_SUITE>`` and wait ``timeout`` seconds.
``DEFAULT_SUITE`` is the whole fast half.  So the nested run costs whatever the
fast half costs, and the moment the fast half crossed **900 s** every one of
those calls began timing out *by construction* — not flakily, not on a slow
runner, but arithmetically, on every run, forever.

That crossing is the event the three ceiling raises were reacting to, and none
of them touched it.  The ``slow`` job's log for run ``30987013397`` reads::

    08:04:49  ...test_the_controller_does_not_track_target_speed   PASSED [ 24%]
    08:26:34  ...test_the_exclusion_list_manufactured_...          FAILED [ 25%]
    08:41:34  ...test_the_reconstruction_agrees_with_a_measured_run FAILED [ 28%]
    08:56:34  ...test_both_published_rankings_were_taken_...        ERROR  [ 28%]
    09:19:08  ...test_the_input_fold_reproduces_a_measured_run...   ERROR  [ 29%]
    09:34:08  ...test_two_independent_flat_censuses_move_only_...   FAILED [ 31%]
    09:57:20  ##[error]The operation was canceled.

Three of those gaps are ``900.1``, ``900.4`` and ``900.5`` seconds — the timeout
to a tenth of a second.  Two more (``1305`` s and ``1354`` s) are a timeout
*plus* real work; :func:`_quanta` deliberately declines to call them two waits,
because 1354 is not 1800 and a stall detector that rounds in its own favour is
not a measurement.  Counting only the unambiguous three, the job spent **46% of
its accounted wall clock** waiting for timeouts it could not win, reached **31%**
of its tests, and was killed.  Raising the cap to 240 buys more timeouts, not
fewer.

Two things follow, and this module measures both.

**1. The cost is quadratic in suite size, so no ceiling is safe.**
:func:`grade` compares the two numbers above.  ``DOOMED`` is not a budget
opinion — it is the statement that *the wait is longer than the ceiling on the
work being waited for*, so the call cannot return.  Every instrument cycle adds
tests to the fast half, which lengthens every nested run, which is paid once per
nested call site; :func:`nested_call_sites` counts the multiplier.

**2. A cancelled job hides verdicts that already exist.**
This is the sixth instance of the shape :mod:`git_surface` tabulated and
:mod:`ci_verdict` extended, and it is the first where the hidden thing is
**already red**.  A job killed at its ceiling never prints a pytest summary, so
``gh`` reports ``cancelled`` and every reader in this package reads "no verdict".
But the ``-v`` stream had already published **five FAILED/ERROR results** before
the kill.  Nobody has seen them for twelve runs.  :func:`unreported` names them,
and :func:`read_log` refuses to grade a log it could not parse rather than
returning an empty tuple that reads like a clean bill — :mod:`exemption_masking`
learned that distinction one cycle ago (``UNPOPULATED``) and it applies here
unchanged: *no events parsed* is not *no failures found*.

This module is deliberately **pure**.  It parses text and reads source; it never
spawns a suite.  An instrument that diagnoses the cost of nested suite runs by
performing one would be the joke that writes itself, and
:func:`test_this_module_spawns_no_subprocess` pins that it does not.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence

PACKAGE = Path(__file__).resolve().parent

# --------------------------------------------------------------------------
# Measured constants.  Dated in place (D-078) rather than pinned: both move
# whenever the suite grows, and the *inequality* is the claim, not the values.
# --------------------------------------------------------------------------

#: The `fast` half's pytest step, on the CI runner.
#: `Run eval suite (fast half)` 08:57:31Z -> 09:20:47Z, run 30991167667,
#: head 08a1480, 2026-08-05.  This is what one nested suite call costs there.
CI_FAST_HALF_SECONDS = 1396

#: The timeout every nested suite call waits, from the `timeout: int = 900`
#: default shared by predicate_vacuity/predicate_inputs `measure`.
NESTED_TIMEOUT_SECONDS = 900

#: The `slow` job's declared ceiling after D-094's 120 -> 360 raise.
#: ⚠️ This is a **copy**.  The enforced ceiling is `timeout-minutes:` in
#: `.github/workflows/sandbox-ci.yml`, and `declared_ceiling.ceiling_seconds()`
#: reads it there.  Two statements of one number is D-047's defect class, so
#: `declared_ceiling.agreement()` grades this against the workflow and a test
#: pins `AGREES` — raise one without the other and the suite goes red naming
#: both values, instead of every `grade()` here silently reporting on a ceiling
#: CI does not apply.
SLOW_CEILING_SECONDS = 360 * 60

#: Verdicts for :func:`grade`.
AFFORDABLE = "AFFORDABLE"
MARGINAL = "MARGINAL"
DOOMED = "DOOMED"

#: Verdicts for :func:`read_log`.
WORK = "WORK"
STALL = "STALL"
UNPARSED = "UNPARSED"

#: A gap counts as a timeout if it lands within this fraction of the quantum.
#: The observed gaps are 900.0 / 900.4 / 900.4 s against a 900 s timeout, so
#: the tolerance exists for log-timestamp jitter, not for fitting.
STALL_TOLERANCE = 0.02

#: A log grades STALL when at least this fraction of its accounted wall clock
#: sits in timeout-shaped gaps.  The observed job is ~0.75; the threshold is
#: well below that and well above the zero a genuinely busy job produces.
STALL_SHARE = 0.30

_EVENT = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s+"
    r"(?P<nodeid>\S+::\S+)\s+"
    r"(?P<outcome>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b"
)

#: pytest's terminal summary.  Its presence is what makes a job's results
#: readable by anything other than this module.
_SUMMARY = re.compile(r"^\S*\s*=+ .*\b(passed|failed|error|no tests ran)\b.*=+", re.I)

_RED = frozenset({"FAILED", "ERROR"})


@dataclass(frozen=True)
class TestEvent:
    """One ``-v`` line: when pytest *finished* a test, and how it went."""

    at: datetime
    nodeid: str
    outcome: str

    @property
    def origin(self) -> str:
        """The file the test lives in."""
        return self.nodeid.split("::", 1)[0]

    @property
    def is_red(self) -> bool:
        return self.outcome in _RED


@dataclass(frozen=True)
class Gap:
    """The wall clock a single test consumed, and whether it looks like a wait."""

    event: TestEvent
    seconds: float
    quanta: int  #: how many whole timeouts this gap accounts for (0 if none)

    @property
    def is_stall(self) -> bool:
        return self.quanta > 0


@dataclass(frozen=True)
class LogReading:
    """What a job's log says about where its time went."""

    verdict: str
    events: tuple[TestEvent, ...]
    gaps: tuple[Gap, ...]
    reported: bool  #: did pytest print a summary anyone else could read?

    @property
    def stalled_seconds(self) -> float:
        return sum(g.seconds for g in self.gaps if g.is_stall)

    @property
    def accounted_seconds(self) -> float:
        return sum(g.seconds for g in self.gaps)

    @property
    def stall_share(self) -> float:
        total = self.accounted_seconds
        return 0.0 if total <= 0 else self.stalled_seconds / total


def parse_events(text: str) -> tuple[TestEvent, ...]:
    """Every ``-v`` test-completion line in a GitHub job log, in order."""
    out: list[TestEvent] = []
    for line in text.splitlines():
        m = _EVENT.match(line.strip())
        if m is None:
            continue
        stamp = m.group("ts").replace("Z", "+00:00")
        try:
            at = datetime.fromisoformat(stamp)
        except ValueError:  # pragma: no cover - defended, not expected
            continue
        out.append(TestEvent(at=at, nodeid=m.group("nodeid"),
                             outcome=m.group("outcome")))
    return tuple(out)


def gaps(events: Sequence[TestEvent],
         quantum: int = NESTED_TIMEOUT_SECONDS) -> tuple[Gap, ...]:
    """Attribute wall clock to each test as the gap since the previous one.

    The first event is dropped rather than measured against a job start time we
    may not have: install and collection sit in front of it, and charging those
    to the first test would manufacture a stall that is really setup.
    """
    out: list[Gap] = []
    for prev, cur in zip(events, events[1:]):
        seconds = (cur.at - prev.at).total_seconds()
        out.append(Gap(event=cur, seconds=seconds,
                       quanta=_quanta(seconds, quantum)))
    return tuple(out)


def _quanta(seconds: float, quantum: int) -> int:
    """How many whole ``quantum``-second waits this gap accounts for.

    A test that makes two nested calls waits two timeouts, so the match is
    against integer *multiples*, not the quantum alone.  The tolerance is
    per-multiple and tight: the 1354 s gap in the record above sits between one
    quantum and two and is graded **0**, not 1 and not 2.  That is the intended
    behaviour — it is a timeout plus 454 s of real work, and this function only
    claims gaps it can attribute unambiguously, leaving the mixed ones to
    understate the stall rather than inflate it.
    """
    if quantum <= 0 or seconds < quantum * (1 - STALL_TOLERANCE):
        return 0
    n = round(seconds / quantum)
    while n > 0 and abs(seconds - n * quantum) > quantum * STALL_TOLERANCE * n:
        n -= 1
    return n


def read_log(text: str,
             quantum: int = NESTED_TIMEOUT_SECONDS) -> LogReading:
    """Grade a job log: was the time *work*, or was it *waiting*?

    ``UNPARSED`` is the load-bearing verdict.  A log this module cannot read
    yields no events, and an empty event tuple would otherwise flow into
    :func:`unreported` as "no failures" and into :attr:`stall_share` as 0.0 —
    both of which read exactly like a healthy job.  Emptiness is decided
    **before** health, for :mod:`exemption_masking`'s reason.
    """
    events = parse_events(text)
    reported = any(_SUMMARY.match(line.strip()) for line in text.splitlines())
    if not events:
        return LogReading(UNPARSED, (), (), reported)
    measured = gaps(events, quantum)
    reading = LogReading(WORK, events, measured, reported)
    if reading.stall_share >= STALL_SHARE:
        return LogReading(STALL, events, measured, reported)
    return reading


def unreported(reading: LogReading) -> tuple[TestEvent, ...]:
    """Red results that no reader of the job's *conclusion* can see.

    A job killed at its ceiling prints no pytest summary, so ``gh`` publishes
    ``cancelled`` and :mod:`ci_verdict` grades ``UNRUN`` — correctly, since the
    job did not finish.  Both are silent about failures the ``-v`` stream had
    already published.  Those are these.

    Empty when the job *did* report: the failures are then visible through the
    ordinary channel and this function has nothing to add.
    """
    if reading.verdict == UNPARSED or reading.reported:
        return ()
    return tuple(e for e in reading.events if e.is_red)


def grade(suite_seconds: int = CI_FAST_HALF_SECONDS,
          timeout_seconds: int = NESTED_TIMEOUT_SECONDS) -> str:
    """Can a nested suite run finish inside the timeout that guards it?

    ``DOOMED`` says the guarded work is *longer than its own guard*, so the call
    times out on every run of every job on every runner — a property of the two
    numbers, not of the machine.  This is the verdict the CI ceiling raises kept
    missing, because a ``cancelled`` job looks identical whichever side of this
    inequality it is on.
    """
    if timeout_seconds <= 0:
        return DOOMED
    ratio = suite_seconds / timeout_seconds
    if ratio >= 1.0:
        return DOOMED
    if ratio >= 1.0 - STALL_SHARE:
        return MARGINAL
    return AFFORDABLE


#: What suite a call site actually runs — the subject its timeout is a bet on.
FULL_SUITE = "FULL_SUITE"
SCRATCH = "SCRATCH"
UNKNOWN_SUBJECT = "UNKNOWN_SUBJECT"


@dataclass(frozen=True)
class CallSite:
    """A place that runs a suite in a subprocess, what it runs, what it waits.

    ``subject`` is not decoration.  The first draft of this scan graded
    ``_measure_scratch`` (``timeout=300``, and it runs a **two-file synthetic
    suite**) ``DOOMED`` against the 1396 s full-suite duration — comparing a
    timeout to the cost of work that site does not do.  A timeout is only
    doomed relative to the suite it actually waits on, so the subject is
    measured before the arithmetic is allowed to run.
    """

    module: str
    function: str
    timeout: int | None  #: None when the default is not an integer literal
    subject: str

    @property
    def key(self) -> tuple[str, str]:
        """Module-qualified, per D-080: a bare function name is not an owner."""
        return (self.module, self.function)


def nested_call_sites(root: Path | None = None) -> tuple[CallSite, ...]:
    """Every ``subprocess.run`` of ``pytest`` in the package, with its timeout.

    This is the multiplier in "cost = sites x suite duration".  Measured from
    source rather than listed, so a new instrument that shells out to the suite
    joins the count without anyone remembering to add it — the registry-drift
    failure this package has now paid for several times over.
    """
    root = root or PACKAGE
    out: list[CallSite] = []
    for path in sorted(root.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):  # pragma: no cover - defended
            continue
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            defaults = _int_defaults(func)
            for call in ast.walk(func):
                if not _is_pytest_subprocess(call):
                    continue
                out.append(CallSite(module=path.stem, function=func.name,
                                    timeout=_timeout_of(call, defaults),
                                    subject=_subject_of(call, func)))
    return tuple(out)


def _subject_of(call: ast.Call,
                func: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Does this site run the *whole* suite, or a scratch one it built?

    ``FULL_SUITE`` when the command splats a name that reaches the enclosing
    signature's ``suite`` parameter or ``DEFAULT_SUITE``; ``SCRATCH`` when the
    paths are literals the caller wrote.  Anything else is ``UNKNOWN_SUBJECT``
    and is carried as unmeasured rather than assumed cheap.
    """
    names = {n.id for arg in call.args for n in ast.walk(arg)
             if isinstance(n, ast.Name)}
    attrs = {n.attr for arg in call.args for n in ast.walk(arg)
             if isinstance(n, ast.Attribute)}
    params = {a.arg for a in func.args.posonlyargs + func.args.args
              + func.args.kwonlyargs}
    if "DEFAULT_SUITE" in names | attrs:
        return FULL_SUITE
    if "suite" in names & params:
        return FULL_SUITE
    literals = [c.value for arg in call.args for c in ast.walk(arg)
                if isinstance(c, ast.Constant) and isinstance(c.value, str)]
    if any(v.endswith(".py") or v.endswith("/") for v in literals):
        return SCRATCH
    return UNKNOWN_SUBJECT


def _int_defaults(func: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, int]:
    """Keyword/positional parameter names bound to integer literal defaults."""
    args = func.args
    out: dict[str, int] = {}
    positional = args.posonlyargs + args.args
    for name, default in zip(positional[len(positional) - len(args.defaults):],
                             args.defaults):
        if isinstance(default, ast.Constant) and isinstance(default.value, int):
            out[name.arg] = default.value
    for name, default in zip(args.kwonlyargs, args.kw_defaults):
        if isinstance(default, ast.Constant) and isinstance(default.value, int):
            out[name.arg] = default.value
    return out


def _is_pytest_subprocess(node: ast.AST) -> bool:
    """A ``subprocess.run([... "-m", "pytest" ...])`` call."""
    if not isinstance(node, ast.Call):
        return False
    fn = node.func
    if not (isinstance(fn, ast.Attribute) and fn.attr == "run"
            and isinstance(fn.value, ast.Name) and fn.value.id == "subprocess"):
        return False
    return any(isinstance(c, ast.Constant) and c.value == "pytest"
               for arg in node.args for c in ast.walk(arg))


def _timeout_of(call: ast.Call, defaults: dict[str, int]) -> int | None:
    """The ``timeout=`` a call waits: a literal, or the parameter it forwards."""
    for kw in call.keywords:
        if kw.arg != "timeout":
            continue
        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int):
            return kw.value.value
        if isinstance(kw.value, ast.Name):
            return defaults.get(kw.value.id)
        return None
    return None


def suite_runners(root: Path | None = None) -> tuple[CallSite, ...]:
    """Public entry points that run the **full** suite, with what they wait.

    The subprocess call itself is often not where the number lives:
    ``predicate_vacuity._run_recorder`` takes ``timeout`` as a bare parameter
    and the 900 is declared one frame up, on ``measure``.  A scan that only
    reads call sites therefore reports the two real offenders as *unresolved*
    and the answer looks like it is missing.  So this reads the **signature**
    instead — a function that defaults ``suite`` to ``DEFAULT_SUITE`` and
    declares an integer ``timeout`` default is, by construction, a full-suite
    run with a declared wait, whichever frame ultimately spawns it.
    """
    root = root or PACKAGE
    out: list[CallSite] = []
    for path in sorted(root.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):  # pragma: no cover - defended
            continue
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            defaults = _int_defaults(func)
            if "timeout" not in defaults or not _defaults_to_full_suite(func):
                continue
            out.append(CallSite(module=path.stem, function=func.name,
                                timeout=defaults["timeout"], subject=FULL_SUITE))
    return tuple(out)


def _defaults_to_full_suite(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Does this signature declare ``suite`` defaulting to ``DEFAULT_SUITE``?"""
    args = func.args
    positional = args.posonlyargs + args.args
    pairs = list(zip(positional[len(positional) - len(args.defaults):],
                     args.defaults))
    pairs += [(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults)
              if d is not None]
    for arg, default in pairs:
        if arg.arg != "suite":
            continue
        for node in ast.walk(default):
            if isinstance(node, ast.Name) and node.id == "DEFAULT_SUITE":
                return True
            if isinstance(node, ast.Attribute) and node.attr == "DEFAULT_SUITE":
                return True
    return False


def doomed_sites(suite_seconds: int = CI_FAST_HALF_SECONDS,
                 root: Path | None = None) -> tuple[CallSite, ...]:
    """Full-suite waits that cannot outlast the suite they wait on.

    Restricted to ``FULL_SUITE`` subjects: ``suite_seconds`` is a measurement of
    the full suite, so comparing it to a site that runs a scratch suite would be
    a category error dressed as arithmetic.  Sites with an unresolved timeout
    are **not** here either — they are unmeasured, not cleared, and
    :func:`unresolved_sites` carries them so a site this scan could not read
    never counts as one it read and approved.
    """
    candidates = suite_runners(root) + tuple(
        s for s in nested_call_sites(root) if s.subject == FULL_SUITE)
    seen: dict[tuple[str, str], CallSite] = {}
    for site in candidates:
        if site.timeout is not None and site.key not in seen:
            seen[site.key] = site
    return tuple(s for s in seen.values()
                 if grade(suite_seconds, s.timeout or 0) == DOOMED)


def unresolved_sites(root: Path | None = None) -> tuple[CallSite, ...]:
    """Full-suite call sites whose timeout this scan could not resolve.

    A site here is resolved by :func:`suite_runners` if its declaring function
    carries the default; what survives is genuinely unread.
    """
    resolved = {s.key for s in suite_runners(root)}
    return tuple(s for s in nested_call_sites(root)
                 if s.timeout is None and s.subject == FULL_SUITE
                 and s.key not in resolved)


def budget(suite_seconds: int = CI_FAST_HALF_SECONDS,
           ceiling_seconds: int = SLOW_CEILING_SECONDS,
           root: Path | None = None) -> float:
    """Seconds the doomed waits burn per job, against the job's ceiling.

    One wait per doomed site is the **floor**, not the estimate: the ``slow``
    half holds many tests and each may reach a doomed site more than once, so
    the real burn is a multiple of this.  The measured job spent 46% of its
    accounted clock in unambiguous stalls against a floor of 38%.  Understating
    is on purpose — the argument only needs the floor to be untenable already.
    """
    if ceiling_seconds <= 0:
        return float("inf")
    burn = sum(s.timeout or 0 for s in doomed_sites(suite_seconds, root))
    return burn / ceiling_seconds


def _main(argv: Sequence[str] | None = None) -> int:
    import argparse
    import sys

    p = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.nested_suite_cost",
        description="Why the slow job is killed: nested suite > its timeout.")
    p.add_argument("--log", type=Path, default=None,
                   help="a GitHub job log to attribute")
    p.add_argument("--suite-seconds", type=int, default=CI_FAST_HALF_SECONDS)
    args = p.parse_args(argv)

    verdict = grade(args.suite_seconds)
    print(f"nested suite {args.suite_seconds}s vs timeout "
          f"{NESTED_TIMEOUT_SECONDS}s: {verdict}")
    for site in nested_call_sites():
        mark = "DOOMED" if (site.timeout is not None
                            and grade(args.suite_seconds, site.timeout) == DOOMED
                            ) else "ok"
        print(f"  {site.module}.{site.function}: timeout={site.timeout} [{mark}]")
    print(f"  burn = {budget(args.suite_seconds):.0%} of the slow ceiling")

    if args.log is not None:
        reading = read_log(args.log.read_text(encoding="utf-8"))
        print(f"log: {reading.verdict} "
              f"({reading.stall_share:.0%} of {reading.accounted_seconds:.0f}s "
              f"in timeout-shaped gaps, reported={reading.reported})")
        for e in unreported(reading):
            print(f"  HIDDEN {e.outcome}: {e.nodeid}")
    return 0 if verdict != DOOMED else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
