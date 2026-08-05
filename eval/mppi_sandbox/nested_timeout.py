"""The nested-suite timeout was stated seven times, in two different values.

D-094 raised the *job* ceiling and made it derived: the requirement is the
measured collapsed floor times a headroom factor, and the declared value is read
from the workflow, where it is enforced.  The first completed ``slow`` run since
that raise (``31042602721``, ``d6b60c8``, 162.7 min against a 360 min cap,
**+55% headroom**) confirms the raise worked — the job was not killed.  It also
published, for the first time in twelve-plus runs, *why the job is red*:

    12 failed, 138 passed, 2 skipped, 1068 deselected, 2 errors in 9752.82s

and **6 of those 14 are one sentence**::

    subprocess.TimeoutExpired: Command '[... -m pytest <DEFAULT_SUITE> ...]'
    timed out after 900 seconds

That is D-089's finding, now measured on a run that *completed* rather than
inferred from a run that was killed before it could report.  The arithmetic is
no longer an estimate: the ``fast`` job's pytest step on the same commit ran
**1032 s and passed** (20:07:57 -> 20:25:09), and the nested spawns invoke the
same selection — ``DEFAULT_SUITE`` with no ``--slow``, i.e. the fast half minus
four ``--ignore`` s.  1032 s of suite inside a 900 s timeout does not fail
flakily or on an unlucky runner.  It fails **by construction, on every run**.

D-094 fixed the ceiling that *kills the job*.  This fixes the timeout that
*makes the job red once it is allowed to finish* — the two were always separate
numbers, and repairing the first is what made the second legible.

**The defect class is D-047's, one layer down, and worse.**  D-047 was a
hand-typed copy of a registry that had grown; D-094 found the job ceiling stated
three times.  Here the timeout was stated **seven** times and there was *no*
single site where it was enforced — every spawn enforced its own copy:

===========================================  ========  ================
site                                         seconds   form
===========================================  ========  ================
``predicate_vacuity.measure``                     900  parameter default
``predicate_inputs.measure``                      900  parameter default
``guard_vacuity._coverage_of`` (call site)        900  **hard-coded**
``nested_suite_cost.NESTED_TIMEOUT_SECONDS``      900  audit copy
``predicate_vacuity.measure_attributed``         1800  parameter default
``predicate_inputs.measure_attributed``          1800  parameter default
``census_narrowing.measure``                     1800  parameter default
===========================================  ========  ================

The three 1800s are the tell.  Somebody already hit this wall on the attributed
censuses and doubled *those calls*, leaving the other four at a value the same
reasoning condemns — **and 1800 s does not clear the requirement either** (2792 s;
see :func:`required_seconds`), so the raise that was made was both partial in
scope and short in size.  A local fix to a global constant reads, in the diff,
exactly like a considered choice, and nothing in the package recorded that the
numbers had diverged, because nothing had ever counted them.

So this module **measures the population** (:func:`declared_timeouts`, an AST
scan) rather than restating it — a hand-typed list of the sites would reproduce
the bug it exists to find.  ⚠️ **And I wrote this table before running the scan,
with six rows and the wrong membership**: ``census_narrowing`` was missing and
``inert_surface`` was in it.  The count in the heading above is the measured one;
the first draft's was a guess that happened to look authoritative because it was
formatted as a table.

The scan must see the ``guard_vacuity`` row specifically.  D-091 showed that
``nested_suite_cost.suite_runners()`` — a *signature* scan requiring an integer
``timeout`` default — cannot, because that call hard-codes ``timeout=900`` at the
call site; it read **5** where the truth was 6, and 5 x 1396 s fits a 7200 s
ceiling while 6 x 1396 s does not.  One missing name inverted that verdict.  So
:func:`declared_timeouts` matches on the **spawn**, not the signature, and
:func:`agreement` is graded against the measured population.

**A subject test is not optional, and leaving it out is a unit error rather than
a near-miss.**  The first run of this scan returned **12 stating sites at five
values** and dutifully graded a 60 s ``gh`` API call and two 300 s *scratch*
suites (two synthetic files, not ``DEFAULT_SUITE``) ``INSUFFICIENT`` against a
full-suite figure.  That is D-091's own first-draft failure — it graded
``_measure_scratch`` ``DOOMED`` against the full-suite 1396 s — reproduced one
cycle later by someone who had just read the sentence describing it.  Hence
:data:`FULL_SUITE` / :data:`NARROW` / :data:`NOT_PYTEST`, and
:attr:`Declaration.gradable`; the honest population is **7 of 17 matched**.

**Absence is not agreement.**  A scan that finds nothing must not read
``AGREES`` — that is this package's most-repeated defect (``UNRUN``,
``UNPOPULATED``, ``UNCOLLECTED``, ``UNIDENTIFIED``, ``UNREAD``, ``CAP_UNVERIFIED``,
and D-095's ``PROBED == {}``, where a complete and tested module was inoperative
because its registry had never been filled).  :data:`UNDECLARED` is the seventh
name for it, and :func:`agreement` returns it on an empty population.

**The requirement is derived, and it is bounded above.**  ``required_seconds``
is the measured suite cost times :data:`declared_ceiling.HEADROOM_FACTOR` — the
same rule D-094 applied, not a fresh guess.  But raising this number is not free:
every runner class pays it inside one job, so ``classes x required`` is spent
against the job ceiling D-094 just declared.  :func:`fits_ceiling` does that
division, and :data:`EXCEEDS_CEILING` is the verdict when the derived timeout
cannot be afforded — at which point the remaining moves are the ones D-094 named
(co-install the recorders, or cut the census subject), not a bigger number.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from . import declared_ceiling as dc

PACKAGE = Path(__file__).resolve().parent

#: Every observed cost of one full nested suite run, in seconds, with provenance.
#: Both are readings of the *same* selection (``DEFAULT_SUITE``, no ``--slow``)
#: from steps that **completed and passed**, so each is a runtime and not a lower
#: bound — they differ because runners and commits differ, not because one is
#: wrong.
OBSERVED_SUITE_SECONDS: tuple[tuple[int, str], ...] = (
    (1396, "D-089, run 30991167667 job 'pytest (fast)' pytest step"),
    (1032, "run 31042602721 job 'pytest (fast)' step 20:07:57->20:25:09Z"),
)


def measured_suite_seconds() -> int:
    """The cost the requirement is derived from: the **worst** observation.

    Not the latest, and not the mean.  The failure this number exists to prevent
    is asymmetric: a timeout below the suite's cost kills every nested run *by
    construction* (six red tests on run 31042602721), while one above it costs
    nothing at all unless something is already hanging.  Deriving from the most
    recent reading would have picked 1032 s here and re-armed the same trap on
    any runner as slow as the one D-089 measured.

    This is also why the observations are kept as a list rather than collapsed
    to a single constant when a newer one arrives: a replaced number cannot be
    compared against the one it replaced.
    """
    return max(s for s, _ in OBSERVED_SUITE_SECONDS)

# Verdicts.
AGREES = "AGREES"
DIVERGES = "DIVERGES"
UNDECLARED = "UNDECLARED"

# Subjects.  The requirement derived here is about **one full nested suite run**,
# so it may only be applied to sites whose spawn actually runs one.  A scan that
# skips this step grades a 60 s ``gh`` call and a 300 s two-file scratch suite
# ``INSUFFICIENT`` against a full-suite figure — which is not a finding, it is a
# unit error, and it is the false positive D-091's first draft shipped and caught.
FULL_SUITE = "FULL_SUITE"
NARROW = "NARROW"
NOT_PYTEST = "NOT_PYTEST"

SUFFICIENT = "SUFFICIENT"
INSUFFICIENT = "INSUFFICIENT"

FITS = "FITS"
EXCEEDS_CEILING = "EXCEEDS_CEILING"
CEILING_UNREAD = "CEILING_UNREAD"


@dataclass(frozen=True)
class Declaration:
    """One statement of the nested-suite timeout, and how it is spelled."""

    module: str
    lineno: int
    seconds: int | None
    #: ``"default"`` (a parameter default), ``"call"`` (hard-coded at the spawn),
    #: or ``"constant"`` (a module-level name).  Kept because the three are
    #: found by different scans, and the *call* form is the one D-091's
    #: signature scan structurally could not see.
    form: str
    #: ``True`` when the spawn's timeout is a *name* rather than a literal, i.e.
    #: it is threaded from a caller and this site states nothing of its own.
    forwarded: bool = False
    #: What this site actually runs — see :data:`FULL_SUITE`.  Only ``FULL_SUITE``
    #: rows may be graded against :func:`required_seconds`.
    subject: str = FULL_SUITE

    @property
    def gradable(self) -> bool:
        return self.subject == FULL_SUITE and not self.forwarded and self.seconds is not None

    def describe(self) -> str:
        secs = "forwarded" if self.forwarded else f"{self.seconds}s"
        return f"{self.module}:{self.lineno} {secs} ({self.form}, {self.subject})"


def _literal(node: ast.AST) -> int | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, int) else None


def declared_timeouts(package: Path | None = None) -> tuple[Declaration, ...]:
    """Every site that states a nested-suite timeout, **measured** by AST scan.

    Two shapes are collected, because the package uses both and a scan that
    knows only one under-counts in the direction that reads clean (D-091):

    * a ``timeout=<int>`` keyword on a spawn call — the *enforcing* site, which
      a signature scan cannot see;
    * a ``timeout: int = <n>`` parameter default on a function that (transitively
      or directly) reaches such a spawn — the *declaring* site.

    Sites that forward a name (``timeout=timeout``) are returned with
    ``forwarded=True`` and no seconds: they enforce whatever they are handed and
    state nothing, so counting them as a declaration would inflate agreement.
    """
    root = package or PACKAGE
    out: list[Declaration] = []
    for path in sorted(root.glob("*.py")):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover - the package parses
            continue
        mod = path.stem
        for node in ast.walk(tree):
            # (a) hard-coded / forwarded timeout on a spawn call.
            if isinstance(node, ast.Call):
                # No spawn-name vocabulary here.  A first draft filtered the
                # callee against {"run", "check_output", "check_call", "Popen"}
                # first; that check is **redundant** with the subject test below,
                # which already answers NOT_PYTEST for anything whose argv does
                # not contain "pytest" — and nothing that is not a spawn takes a
                # `timeout=` beside a pytest argv.  Measured both ways in-cycle:
                # identical readings (see the test).  Deleting it is also what
                # keeps this scan out of the guard census, but that is the
                # consequence and not the reason; a redundant narrowing that
                # costs a probe, a registry entry and a tamper is worth removing
                # on its own terms.
                subject = _call_subject(node)
                for kw in node.keywords:
                    if kw.arg != "timeout":
                        continue
                    lit = _literal(kw.value)
                    out.append(Declaration(mod, kw.value.lineno, lit, "call",
                                           forwarded=lit is None, subject=subject))
            # (b) parameter default on a function that spawns a suite.
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                subject = _def_subject(node)
                if subject == NOT_PYTEST:
                    continue
                args = node.args
                defaults = args.defaults
                named = args.args[len(args.args) - len(defaults):] if defaults else []
                pairs = list(zip(named, defaults)) + [
                    (a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is not None
                ]
                for arg, default in pairs:
                    if arg.arg == "timeout" and (lit := _literal(default)) is not None:
                        out.append(Declaration(mod, default.lineno, lit, "default",
                                               subject=subject))
    return tuple(out)


def _names_full_suite(dump: str) -> bool:
    """Does this AST dump reference the whole-suite selection?

    Either by the constant's name, or by splatting a ``suite`` parameter — the
    ``guard_vacuity`` form, whose default *is* ``DEFAULT_SUITE`` and which a
    scan looking only for the constant would miss (D-091's shape).
    """
    return ("DEFAULT_SUITE" in dump or "FULL_SUITE" in dump
            or "Starred(value=Name(id='suite'" in dump)


def _call_subject(node: ast.Call) -> str:
    """What does this spawn run?  Read off its argv, not its name."""
    dump = ast.dump(ast.Tuple(elts=list(node.args), ctx=ast.Load()))
    if "'pytest'" not in dump:
        return NOT_PYTEST
    return FULL_SUITE if _names_full_suite(dump) else NARROW


def _def_subject(node: ast.AST) -> str:
    """A function's subject is the default of its own ``suite`` parameter.

    ``NOT_PYTEST`` when the body never mentions pytest at all, so a ``timeout``
    default on an unrelated helper is dropped rather than graded.
    """
    body = ast.dump(node)
    if "pytest" not in body and "suite" not in body:
        return NOT_PYTEST
    args = node.args
    defaults = args.defaults
    named = args.args[len(args.args) - len(defaults):] if defaults else []
    for arg, default in zip(named, defaults):
        if arg.arg == "suite":
            return FULL_SUITE if _names_full_suite(ast.dump(default)) else NARROW
    return FULL_SUITE if _names_full_suite(body) else NARROW


def constant_declarations(package: Path | None = None) -> tuple[Declaration, ...]:
    """Module-level names that restate the timeout, e.g. the audit copy.

    Separate from :func:`declared_timeouts` because a constant enforces nothing
    by itself; it is a *claim about* the enforced value, and D-094's
    :func:`declared_ceiling.agreement` exists for exactly that relationship.
    """
    root = package or PACKAGE
    out: list[Declaration] = []
    for path in sorted(root.glob("*.py")):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover
            continue
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and "NESTED_TIMEOUT" in target.id:
                    if (lit := _literal(node.value)) is not None:
                        out.append(Declaration(path.stem, node.lineno, lit, "constant"))
    return tuple(out)


def gradable(package: Path | None = None) -> tuple[Declaration, ...]:
    """The sites this module is entitled to speak about: full-suite, literal."""
    decls = declared_timeouts(package) + constant_declarations(package)
    return tuple(d for d in decls if d.gradable)


def stated_values(package: Path | None = None) -> tuple[int, ...]:
    """The distinct seconds stated **for a full-suite run**, ascending.

    Empty ⇒ nothing found, which :func:`agreement` reads as :data:`UNDECLARED`
    and never as agreement.
    """
    return tuple(sorted({d.seconds for d in gradable(package)}))


def agreement(package: Path | None = None) -> str:
    """Do all stated timeouts agree?

    :data:`UNDECLARED` on an empty population — an unread scan is not a clean
    bill, and this package has shipped that mistake often enough to name it
    seven times now.
    """
    values = stated_values(package)
    if not values:
        return UNDECLARED
    return AGREES if len(values) == 1 else DIVERGES


def required_seconds(measured: int | None = None) -> int:
    """Measured cost of one nested run x the headroom factor.  Derived, not chosen.

    Reuses :data:`declared_ceiling.HEADROOM_FACTOR` rather than restating it,
    because a second copy of the factor would be this module's own defect class.
    """
    return int(round((measured_suite_seconds() if measured is None else measured)
                     * dc.HEADROOM_FACTOR))


def grade(declared: int, measured: int | None = None) -> str:
    """Is ``declared`` above the derived requirement?"""
    return SUFFICIENT if declared >= required_seconds(measured) else INSUFFICIENT


def fits_ceiling(classes: int,
                 declared: int | None = None,
                 ceiling_s: int | None = None) -> str:
    """Can ``classes`` runner classes each afford ``declared`` inside the job?

    The timeout is not a free variable either: raising it multiplies straight
    into the job ceiling D-094 declared.  ``CEILING_UNREAD`` when the workflow
    cannot be read, so a conditional never prints in the shape of a measurement
    (D-094's ``CAP_UNVERIFIED``, same rule).
    """
    ceiling = ceiling_s if ceiling_s is not None else dc.ceiling_seconds()
    if not ceiling:
        return CEILING_UNREAD
    want = required_seconds() if declared is None else declared
    return FITS if classes * want <= ceiling else EXCEEDS_CEILING


def report(package: Path | None = None) -> str:
    """One-screen summary: the population, the spread, and the requirement."""
    decls = declared_timeouts(package) + constant_declarations(package)
    grade_me = gradable(package)
    lines = [f"nested-suite timeout: {len(grade_me)} full-suite sites "
             f"of {len(decls)} matched — {agreement(package)}"]
    lines += [f"  - {d.describe()}" for d in sorted(decls, key=lambda d: (d.subject, d.module))]
    req = required_seconds()
    worst = measured_suite_seconds()
    lines.append(f"worst observed {worst}s x {dc.HEADROOM_FACTOR} = {req}s required")
    lines += [f"    observed {s}s  [{why}]" for s, why in OBSERVED_SUITE_SECONDS]
    for v in stated_values(package):
        lines.append(f"  stated {v}s: {grade(v)}")
    return "\n".join(lines)
