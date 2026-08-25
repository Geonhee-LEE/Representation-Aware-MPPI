"""Can each never-fired guard be *made* to fire? — closing D-059's candidate set.

D-059 censused the package's 38 guard clauses and left **8** scored
``NEVER_FIRED``: the enclosing function ran, the ``raise`` did not.  That verdict
is a *necessary* condition for D-058's defect (a guard whose trigger cannot
occur) and nothing more — most untested argument checks sit there too.  D-059
hand-triaged 3 of the 8 and found 0 of D-058's shape.

Hand-triage is the thing this package keeps catching itself getting wrong.  Every
finding from D-045 to D-059 has the same skeleton: a claim about a population,
written down rather than executed, true of a smaller set than the one it names.
"I read the code and the trigger looks satisfiable" is exactly that claim.  So
this module replaces it with the only evidence that settles the question —
**an input that makes the guard raise**.

What a witness proves, and what it does not
--------------------------------------------

A witness is a nullary callable that invokes the guarded function and is expected
to raise the guard's exception.  If one exists, the trigger is satisfiable and
the guard is **untested, not vacuous** — the D-058 question is answered in the
negative for that site, by execution.  D-058's own guard admits no witness: no
scene makes ``shadow_batch`` raise, which is what made it vacuous rather than
merely quiet.  :func:`unwitnessed` is therefore the residual suspect set and the
real output of this module; the witnesses themselves are the working.

The bound: a witness proves satisfiability over the argument space, and the
argument space is larger than what callers actually supply.  ``measure("nope")``
raises, but every in-package caller of :func:`predicate_depth.measure` iterates
:data:`predicate_depth.ADAPTERS`, so no call the package makes can reach it.
Collapsing that into the same verdict as a guard whose trigger arrives in real
data would repeat D-050's error — a probe that cannot separate two cases has
measured neither.  Hence two grades:

``DATA_REACHABLE``
    Some producer *in this package* emits the triggering value.  ``cruise`` is
    NaN for a stalled arm (:attr:`horizon_audit.HorizonRow.stalled` exists for
    precisely that); ``n_reached=-1`` is the field's own default and historical
    probes carry it; the claims dict is ``json.load``-ed off disk.  These guards
    are load-bearing and simply unexercised — each is a test somebody owes.
``ARGUMENT_ONLY``
    The trigger requires a caller to pass a value no producer emits — an unknown
    knob string, an unregistered predicate name, a non-positive factor.  Ordinary
    argument validation.  D-059 called these "untested argument checks" by hand;
    the grade is that judgement with a criterion attached.

The grade is assigned per witness and is a **judgement about the call graph**,
not a measurement — :attr:`Witness.reachability` records which, and the docstring
of each witness states the producer it is claiming.  Nothing here derives the
grade automatically, and pretending otherwise would be the sixth hand-written
registry presented as a derivation.

Why the census must not see these tests
-----------------------------------------

The witnesses run inside ``eval/mppi_sandbox/tests/``, which is
:data:`guard_vacuity.DEFAULT_SUITE`.  Coverage does not care *why* a line ran, so
letting the census observe this module's own tests would move all 8 candidates
from ``NEVER_FIRED`` to ``FIRES`` and read as a clean bill — while not one line
of the subject code changed.  The instrument would have eaten its own signal.

:data:`guard_vacuity.EXCLUDED_TESTS` names this module's test file and
:func:`guard_vacuity.measure` passes ``--ignore`` for it, so ``NEVER_FIRED``
keeps meaning *the subject suite never fired it*.  The witness reading is a
second, separate measurement, and the two are only informative apart.
"""

from __future__ import annotations

import dataclasses
import json
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

#: The trigger arrives in values the package's own producers emit.
DATA_REACHABLE = "DATA_REACHABLE"
#: The trigger needs an argument no in-package producer emits.
ARGUMENT_ONLY = "ARGUMENT_ONLY"

#: The witness raised the exception the guard names.  Trigger is satisfiable.
SATISFIED = "SATISFIED"
#: Something raised, but not the guard's exception — the witness missed.
WRONG_EXCEPTION = "WRONG_EXCEPTION"
#: Nothing raised.  Either the witness is wrong or the guard really is vacuous.
NO_RAISE = "NO_RAISE"


@dataclass(frozen=True)
class Witness:
    """An input constructed to make one guard clause raise.

    ``module``/``function`` key into :func:`guard_vacuity.census`'s population by
    the same ``(module, function)`` pair :data:`guard_vacuity.CALIBRATION` uses,
    so a witness for a site the scan no longer reports is detectable
    (:func:`stale_witnesses`) rather than silently inert.
    """

    module: str
    function: str
    exception: str
    reachability: str
    #: Nullary; invoking it is expected to raise ``exception``.
    build: Callable[[], object]
    #: The producer whose output supplies the trigger, or why none does.
    producer: str

    @property
    def site(self) -> str:
        return f"{self.module}.{self.function}"

    @property
    def key(self) -> tuple[str, str]:
        return (self.module, self.function)


@dataclass(frozen=True)
class Attempt:
    """A witness plus what happened when it ran."""

    witness: Witness
    verdict: str
    #: ``repr`` of what was raised, or of the return value when nothing was.
    detail: str

    @property
    def satisfiable(self) -> bool:
        return self.verdict == SATISFIED

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return f"{self.verdict:<16} {self.witness.reachability:<15} {self.witness.site}"


# --------------------------------------------------------------------------
# the witnesses
# --------------------------------------------------------------------------

def _w_n_reached():
    """`n_reached=-1` is the dataclass default; every pre-Q-042 probe carries it."""
    from eval.mppi_sandbox import ab

    probe = ab.LamProbe(lam=1.0, median_ess=1.0, min_ess=1.0, max_ess=1.0,
                        n_in_band=0, n=1, all_reached=True)
    return ab._n_reached(probe)


def _w_readings():
    """`guard_reflexivity.scan` emits the pool; a new revocable guard lands in it.

    The guard's stated job is to refuse when a ``DIFFERENCE``-shaped guard has no
    entry in ``PROBES``.  The witness is that exact drift: an existing revocable
    guard under a name the typed table does not carry.  The raise precedes any
    use of ``workdir``, so the path need not exist.
    """
    from eval.mppi_sandbox import guard_direction as gd
    from eval.mppi_sandbox import guard_reflexivity as gr

    revocable = gr.revocable()
    if not revocable:  # pragma: no cover - defended, not expected
        raise AssertionError("no revocable guard to build an unprobed twin from")
    unprobed = dataclasses.replace(revocable[0], name=revocable[0].name + "_unprobed")
    return gd.readings(Path(tempfile.gettempdir()) / "guard-witness-unused",
                       pool=[unprobed])


def _w_cruise_ceiling():
    """`cruise_speed` returns NaN for an arm that never leaves the transient.

    `HorizonRow.stalled` is defined as `not isfinite(cruise)`, so the package
    states in its own types that this value occurs.
    """
    from eval.mppi_sandbox import horizon_audit as ha

    stalled = ha.HorizonRow(horizon=ha.SHIPPED_HORIZON, n_seeds=1,
                            median_steps=1.0, cruise=float("nan"),
                            mean_clearance=0.0, all_reached=True,
                            median_ess=1.0, truncated=False)
    return ha.cruise_ceiling([stalled])


def _w_unguarded_declarations():
    """`scripts/prompts/auto_research.md` is hand-edited, and was wrong once.

    D-047 is the record of that file's push guard being a stale literal; this
    module exists because of it.  A rewrite that drops both the derived call and
    the literal alternation is the case the guard names.
    """
    from eval.mppi_sandbox import local_only_audit as loa

    root = Path(tempfile.mkdtemp(prefix="guard-witness-"))
    guard = root / loa.GUARD_FILE
    guard.parent.mkdir(parents=True, exist_ok=True)
    guard.write_text("A prompt with neither a derived push guard nor a literal.\n",
                     encoding="utf-8")
    return loa.unguarded_declarations(root)


def _w_measure():
    """No in-package caller can reach this: all of them iterate `ADAPTERS`.

    `depth_profile`, `profiles` and `opaque_readings` each key from
    :data:`predicate_depth.ADAPTERS` itself, so the lookup cannot miss.  The
    witness is an external caller passing an unregistered name.
    """
    from eval.mppi_sandbox import predicate_depth as pd

    return pd.measure("guard_witness.no_such_predicate")


def _w_margin_at_factor():
    """No in-package caller at all — `factor` is supplied by tests and the CLI."""
    from eval.mppi_sandbox import repair_admissibility as ra

    return ra.Repair(claim="witness", kind="band", verdict="witness",
                     widen_factor=2.0).margin_at_factor(0.0)


def _w_price():
    """`main` feeds `price_all` two `json.load`-ed claim files.

    A two-sided claim (`lo` and `hi` both present) whose `excursion` key is
    absent is a malformed-but-parseable file, which is what the guard refuses.
    """
    from eval.mppi_sandbox import repair_admissibility as ra

    two_sided_without_excursion = json.loads('{"lo": 0.0, "hi": 1.0}')
    return ra.price({"value": 1.0}, two_sided_without_excursion, "witness")


def _w_batch_per_unit_spread():
    """No in-package caller; every test passes a literal from the knob tables.

    The raise precedes every use of `scenario` and `weights`, so neither needs
    to be real for the witness to reach it.
    """
    from eval.mppi_sandbox import weight_units as wu

    return wu.batch_per_unit_spread(None, "guard_witness.no_such_knob", ())


#: One entry per :data:`guard_vacuity` ``NEVER_FIRED`` candidate.  Hand-written
#: and *presented as* hand-written: a witness is an argued input, and there is no
#: honest way to derive one.  :func:`unwitnessed` is the mirror that reports what
#: this table is short of, which is the part that must not be hand-written.
WITNESSES: tuple[Witness, ...] = (
    Witness("ab", "_n_reached", "ValueError", DATA_REACHABLE, _w_n_reached,
            producer="LamProbe.n_reached default (-1), carried by every pre-Q-042 probe"),
    Witness("guard_direction", "readings", "ProbeError", DATA_REACHABLE, _w_readings,
            producer="guard_reflexivity.scan — a new revocable guard with no PROBES entry"),
    Witness("horizon_audit", "cruise_ceiling", "ValueError", DATA_REACHABLE,
            _w_cruise_ceiling,
            producer="cruise_speed returns NaN for a stalled arm (HorizonRow.stalled)"),
    Witness("local_only_audit", "unguarded_declarations", "WriterSurfaceError",
            DATA_REACHABLE, _w_unguarded_declarations,
            producer="scripts/prompts/auto_research.md, hand-edited (D-047 is the precedent)"),
    Witness("predicate_depth", "measure", "ProbeError", ARGUMENT_ONLY, _w_measure,
            producer="none — every in-package caller keys from ADAPTERS"),
    Witness("repair_admissibility", "Repair.margin_at_factor", "ValueError",
            ARGUMENT_ONLY, _w_margin_at_factor,
            producer="none — no in-package caller"),
    Witness("repair_admissibility", "price", "ValueError", DATA_REACHABLE, _w_price,
            producer="main() → price_all over two json.load-ed claim files"),
    Witness("weight_units", "batch_per_unit_spread", "KeyError", ARGUMENT_ONLY,
            _w_batch_per_unit_spread,
            producer="none — no in-package caller; tests pass knob-table literals"),
)


# --------------------------------------------------------------------------
# running them
# --------------------------------------------------------------------------

def attempt(witness: Witness) -> Attempt:
    """Run one witness and score what came back.

    Matches on the exception's **class name** rather than on an imported type:
    the guard clause's exception is discovered from the AST by
    :mod:`guard_vacuity`, which yields a name and never a class, and keying both
    sides the same way is what lets :func:`unwitnessed` compare them at all.
    """
    try:
        value = witness.build()
    except BaseException as exc:  # noqa: BLE001 - scoring, not handling
        name = type(exc).__name__
        if name == witness.exception:
            return Attempt(witness, SATISFIED, f"{name}: {exc}")
        return Attempt(witness, WRONG_EXCEPTION, f"{name}: {exc}")
    return Attempt(witness, NO_RAISE, repr(value))


def attempts(witnesses: Iterable[Witness] = WITNESSES) -> tuple[Attempt, ...]:
    return tuple(attempt(w) for w in witnesses)


def satisfiable(results: Iterable[Attempt]) -> tuple[str, ...]:
    """Sites proved reachable by execution — untested, not vacuous."""
    return tuple(sorted(a.witness.site for a in results if a.satisfiable))


def failed(results: Iterable[Attempt]) -> tuple[Attempt, ...]:
    """Witnesses that did not do what they claim — the table's own bugs.

    Kept apart from :func:`unwitnessed`: a witness that misfires says nothing
    about the guard, only about the witness, and folding the two together would
    let a broken witness read as evidence of vacuity.
    """
    return tuple(a for a in results if not a.satisfiable)


def by_reachability(results: Iterable[Attempt]) -> dict[str, tuple[str, ...]]:
    """The satisfiable sites split by whether real data can reach them."""
    out: dict[str, list[str]] = {DATA_REACHABLE: [], ARGUMENT_ONLY: []}
    for a in results:
        if a.satisfiable:
            out[a.witness.reachability].append(a.witness.site)
    return {k: tuple(sorted(v)) for k, v in out.items()}


def unwitnessed(census) -> tuple[str, ...]:
    """``NEVER_FIRED`` candidates with no witness — **the residual suspect set**.

    This is the output that matters.  Everything else in this module is the
    working; a site that survives here is one nobody could construct an input
    for, which is D-058's shape and the only thing the census was ever looking
    for.  Empty means the candidate set is closed, not that the package is
    clean — closure is a statement about the 8, and the docstring's
    ``ARGUMENT_ONLY`` bound still applies to 3 of them.
    """
    have = {w.key for w in WITNESSES}
    return tuple(sorted(f.clause.site for f in census.candidates
                        if (f.clause.module, f.clause.function) not in have))


def stale_witnesses(census) -> tuple[str, ...]:
    """Witnesses naming a site the census no longer reports as a guard clause.

    :func:`guard_direction.stale_probes`' reason, one layer over: an entry for a
    guard that moved or was deleted is an entry nobody will notice went dead,
    and it would keep :func:`unwitnessed` quiet about a real candidate that
    happens to share its key.
    """
    live = {(f.clause.module, f.clause.function) for f in census.firings}
    return tuple(sorted(w.site for w in WITNESSES if w.key not in live))


def report(census=None) -> str:  # pragma: no cover - reporting sugar
    from eval.mppi_sandbox import guard_vacuity as gv

    results = attempts()
    grades = by_reachability(results)
    lines = [
        f"{len(WITNESSES)} witnesses: {len(satisfiable(results))} SATISFIED, "
        f"{len(failed(results))} failed",
        f"  DATA_REACHABLE  {len(grades[DATA_REACHABLE])}",
        f"  ARGUMENT_ONLY   {len(grades[ARGUMENT_ONLY])}",
        "",
    ]
    lines.extend(f"  {a}" for a in results)
    if census is None:
        census = gv.census()
    lines += ["", f"  unwitnessed candidates: {unwitnessed(census) or '()'}",
              f"  stale witnesses:        {stale_witnesses(census) or '()'}"]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - CLI
    print(report())
