"""The counterfactual D-090 deferred costs one nested run, not two.

D-090 bounded the population: **20 of 59** collected files (19 of 58 when it was
published, before its own test file existed) do their work through a spawned
Python, and the recorder is installed on the nested pytest with a ``-p`` flag
that crosses no process boundary — so those files pay full wall clock and return
observations the recorder cannot receive.  It then declined to apply the
narrowing, for a reason it stated plainly: narrowing changes census readings,
the before/after comparison "did not fit this cycle's budget", and shipping a
semantic change with no evidence the verdicts survive is the worse trade.

**The budget objection assumed two nested runs.**  The package already holds a
shape that needs one.  :func:`predicate_vacuity.measure_attributed` tallies per
*originating test file*, and :func:`predicate_vacuity.fold` reconstructs the
reading "as if these origins had been ``--ignore``-d".  Full and narrowed
censuses therefore come out of a **single** run, and the comparison D-090
deferred is affordable.  That is this module's whole reason to exist: not a new
measurement, a cheaper arrangement of one that was already available.

What the comparison is *for* is a hazard D-090's static bound does not close.
:func:`nested_subject.classify` grades a file ``SPAWNS`` if it **contains** a
spawn — not that all of its work happens in the child.  A ``SPAWNS`` file may
still call subject predicates in-process, in its assertions or its fixtures, and
those calls are observations the census *does* receive.  So the narrowing is not
free by construction.  It is admissible only if the verdicts survive it, and
whether they survive is a measurement, not an argument.

Two results that must not be reported as one
--------------------------------------------

:func:`compare` answers *did any verdict move*.  :func:`contributions` answers
*was anything actually removed*.  They are separate functions because they carry
different epistemic weight and folding them into a single "safe" flag is the
conflation this package keeps re-finding:

* hidden origins contributed **0** observations ⇒ the narrowing is free, and
  D-090's mechanism is confirmed at the level of observations rather than of
  syntax;
* hidden origins contributed **>0** and the verdicts still match ⇒ the narrowing
  removed real evidence that happened not to be decisive.  Still admissible,
  but it is a claim about *this* population on *this* tree, and it can stop
  being true when a test is added.

:data:`VACUOUS` exists for the reason it has existed three times before (D-075's
vacuous survival, D-081's overwritten fixture, D-088's unpopulated reading, and
D-090's two-zeroes probe).  A comparison over an empty record preserves every
verdict trivially, and a record where **nothing** is attributed to any origin
cannot show that hiding an origin does anything at all — in both cases
``PRESERVED`` would be a statement about a no-op wearing the words of a result.
Emptiness is decided *before* equality, never after.

What this module does not claim
-------------------------------

A share of seconds.  Same bound D-090 published under: per-file wall clock on
the CI runner is in no artifact this module can read, and a local timing is a
reading of a different machine running a different suite half.  Q-090 still
carries the timing question, and it is not answered by anything here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from . import nested_subject as ns
from . import predicate_vacuity as pv

PACKAGE = Path(__file__).resolve().parent

#: Verdicts for :func:`compare`.
PRESERVED = "PRESERVED"
CHANGED = "CHANGED"
VACUOUS = "VACUOUS"

#: The origin the recorder uses for calls made outside any test file's
#: collection or execution.  An observation carrying it is attributed to no
#: file, so hiding files can never remove it — which is why a record made
#: entirely of these grades :data:`VACUOUS`.
UNATTRIBUTED = ""


@dataclass(frozen=True)
class Move:
    """One predicate whose verdict did not survive the narrowing."""

    site: str
    before: str
    after: str

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return f"{self.site}: {self.before} -> {self.after}"


@dataclass(frozen=True)
class Comparison:
    """Full census vs narrowed census, taken from one attributed run."""

    verdict: str
    moved: tuple[Move, ...]
    #: Verdict tallies, before and after, keyed by verdict string.
    before: Mapping[str, int]
    after: Mapping[str, int]
    #: Origins the narrowing hid, and how many observations each contributed.
    contributed: Mapping[str, int]
    #: Why a :data:`VACUOUS` reading was vacuous.  Empty when it was not.
    vacuity: str = ""

    @property
    def admissible(self) -> bool:
        """May the narrowing be applied on the evidence of this comparison?

        ``VACUOUS`` is deliberately **not** admissible.  A comparison that
        proves nothing is not a comparison that proves the narrowing safe, and
        the difference between those two is where D-075 lost a cycle.
        """
        return self.verdict == PRESERVED

    @property
    def removed(self) -> int:
        """Observations the narrowing actually took away."""
        return sum(self.contributed.values())

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        head = f"{self.verdict}"
        if self.vacuity:
            head += f" ({self.vacuity})"
        return (f"{head}; {len(self.moved)} verdict(s) moved; "
                f"{self.removed} observation(s) removed from "
                f"{len(self.contributed)} hidden origin(s)")


def hidden_origins(suite: Sequence[str] = pv.DEFAULT_SUITE,
                   root: Path | None = None,
                   excluded: Sequence[str] = pv.EXCLUDED_TESTS,
                   ) -> tuple[str, ...]:
    """The narrowing D-090 proposed, spelled the way origins are spelled.

    :func:`nested_subject.spawning` returns absolute paths; the recorder
    attributes to whatever pytest calls the file.  Both spellings are emitted
    so a match is not lost to a path-shape mismatch — the failure mode would be
    "nothing was hidden", i.e. a ``PRESERVED`` that is really a no-op, which is
    the exact reading :data:`VACUOUS` exists to refuse.
    """
    root = (root or PACKAGE.parent.parent).resolve()
    out: set[str] = set()
    for path in ns.spawning(suite, root, excluded):
        out.add(str(path))
        try:
            out.add(path.resolve().relative_to(root).as_posix())
        except ValueError:  # pragma: no cover - path outside the repo
            pass
    return tuple(sorted(out))


def contributions(attributed: Mapping[str, Mapping[str, pv.Observation]],
                  hidden: Sequence[str],
                  ) -> dict[str, int]:
    """Per hidden origin, how many observations it originated.

    Only origins the record actually mentions appear.  A hidden file absent
    from the record contributed nothing *and is not evidence the record is
    healthy*, so it is not listed as a zero — that would let a comparison over a
    record naming no origins at all display a tidy column of zeroes.
    """
    drop = set(hidden)
    out: dict[str, int] = {}
    for per in attributed.values():
        for origin, obs in per.items():
            if origin in drop:
                out[origin] = out.get(origin, 0) + obs.calls
    return dict(sorted(out.items()))


def _attributed_origins(
        attributed: Mapping[str, Mapping[str, pv.Observation]]) -> set[str]:
    return {origin
            for per in attributed.values()
            for origin, obs in per.items()
            if origin != UNATTRIBUTED and obs.calls}


def _tally(readings: Iterable[pv.Reading]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in readings:
        out[r.verdict] = out.get(r.verdict, 0) + 1
    return dict(sorted(out.items()))


def compare(attributed: Mapping[str, Mapping[str, pv.Observation]],
            hidden: Sequence[str],
            population: Sequence[pv.Predicate],
            ) -> Comparison:
    """Grade the narrowing from one attributed record.

    ``before`` folds the record whole; ``after`` folds it with ``hidden``
    dropped.  Both go through :func:`predicate_vacuity.classify`, so the
    comparison is between two things the census would itself have said, not
    between two summaries of it.
    """
    contributed = contributions(attributed, hidden)
    vacuity = _vacuity(attributed, population)
    before = pv.classify(population, pv.fold(attributed))
    after = pv.classify(population, pv.fold(attributed, hidden=hidden))
    moved = tuple(Move(site=b.predicate.site, before=b.verdict, after=a.verdict)
                  for b, a in zip(before, after) if b.verdict != a.verdict)
    if vacuity:
        verdict = VACUOUS
    elif moved:
        verdict = CHANGED
    else:
        verdict = PRESERVED
    return Comparison(verdict=verdict, moved=moved, before=_tally(before),
                      after=_tally(after), contributed=contributed,
                      vacuity=vacuity)


def _vacuity(attributed: Mapping[str, Mapping[str, pv.Observation]],
             population: Sequence[pv.Predicate]) -> str:
    """Why this comparison could prove nothing, or ``""`` if it could.

    Three ways, checked before any verdict is compared:

    ``no observations``
        the run recorded nothing, so every verdict is ``UNOBSERVED`` on both
        sides and they match for the reason a blank page matches itself;
    ``no attributed origins``
        every observation carries :data:`UNATTRIBUTED`, so no choice of hidden
        files can change the fold — the attribution machinery said nothing and
        a match is a statement about it, not about the narrowing;
    ``no population``
        nothing was classified, so there were no verdicts to preserve.
    """
    if not population:
        return "no population"
    if not any(obs.calls for per in attributed.values() for obs in per.values()):
        return "no observations"
    if not _attributed_origins(attributed):
        return "no attributed origins"
    return ""


def measure(suite: Sequence[str] = pv.DEFAULT_SUITE,
            root: Path | None = None,
            timeout: int = 1800,
            ) -> Comparison:
    """One nested run, both censuses.  The expensive entry point.

    ``excluded`` is not a parameter: :func:`predicate_vacuity.measure_attributed`
    is called with nothing hidden on purpose, because the reconstruction is what
    makes one run enough.  Passing an exclusion to the run would throw away the
    counterfactual and leave this module needing the second run it exists to
    avoid.
    """
    root = root or PACKAGE.parent.parent
    population, _refused = pv._scan(PACKAGE)
    attributed = pv.measure_attributed(population, suite=suite, root=root,
                                       timeout=timeout)
    hidden = hidden_origins(suite, root)
    return compare(attributed, hidden, population)


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI
    comp = measure()
    print(comp)
    print(f"  before: {comp.before}")
    print(f"  after:  {comp.after}")
    for origin, calls in comp.contributed.items():
        print(f"  contributed {calls:>5}  {origin}")
    for move in comp.moved:
        print(f"  MOVED {move}")
    return 0 if comp.admissible else 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
