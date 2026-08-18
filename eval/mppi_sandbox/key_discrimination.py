"""A key is not validated by how *few* things it matches.

Three cycles running, this package has proposed a marker as the key for a
verdict, measured it before writing to it (D-186), and rejected it — each time
on a number that was reported as *narrowness*:

* D-193: ``# pragma: no cover`` hits **48** of 744, and **43** grade ``LIVE``.
* D-196: "call syntax with an argument in the decision log" hits **25** of 599,
  "most of them ``LIVE``".

Both rejections were right and both were *described* wrong.  The stated reason
was that the key is too wide; the operative reason, in both cases, was that the
things it caught were **the same kind of thing** the residue member is not.  A
key that hits 48 names of which 5 are non-``LIVE`` and a key that hits 6 names of
which 5 are non-``LIVE`` are worlds apart, and counting hits cannot tell them
apart.  So the discipline that got written down ("measure the key before keying
on it") records the cheaper half of what those cycles actually did, and a fourth
cycle following it to the letter can still ship D-193's defect.

Two results that must not be reported as one
--------------------------------------------

:func:`narrowing` answers *how much smaller is the matched set*.
:func:`discrimination` answers *did the composition of the matched set move*.
They are separate readings because only the second one licenses a verdict:

* the narrow key matches fewer names **and** its non-``LIVE`` fraction rises ⇒
  it is selecting for the property the verdict is about, and the residue member
  it catches is caught *because* of that property;
* the narrow key matches fewer names and the composition is **unchanged** ⇒ it
  is a smaller sample of the same population.  It picks the residue member out
  only by the coincidence that the others have callers — which is D-193's defect
  exactly, arriving with a better hit count.

The second is the reading on today's tree, and it is why no ``OPERATOR_INVOKED``
verdict ships with this module.  ``reprobe`` stays ``UNREACHED``.

On the threshold
----------------

:data:`SEPARATION_MARGIN` is a judgement, not a measurement, and a reading that
turned on where it sits would be worth little.  This one does not: the measured
composition delta for the narrow key was **-1.4 points** against a margin of
**25** when this module was written.  When a future key lands near the line,
that is the signal to measure a second axis — not to move the line.

**Which end moved?  D-342.**  The delta has since read -1.4, +9.7, +15.2 and
+20.1 points, and each cycle read the move as a new name entering the narrow
key.  Measured across D-341, that reading is wrong: the narrow composition was
``hits=16, live=11`` on both sides of the change, the same sixteen names, while
the delta rose past a rung.  The wide *control* had gone ``60/53`` to ``63/56``
— three ordinary reachable functions, landing in the wide key and nowhere near
the narrow one, dropping the control's non-``LIVE`` fraction and lifting the
difference by exactly that much.

So :attr:`Reading.discrimination` is a difference of two fractions and **either
end moves it**, which makes it the wrong thing to hand-pin a bound onto: any
cycle that adds a called function anywhere in this package can push it through
a threshold without touching the key under test.  The narrow composition is the
stable axis and the one the verdict is about; the difference is still the
reading, but it is compared against :data:`SEPARATION_MARGIN` alone, never
against a tighter literal that will be squeezed again.  Both readings — a
number that moved and a key that did not — are true at once, and reporting only
the first is the same conflation :func:`narrowing` and :func:`discrimination`
were split to prevent, one level up.

:data:`VACUOUS` exists for the same reason it exists in :mod:`census_narrowing`
and three modules before it: a key matching nothing reads as "no ``LIVE`` hits",
which is a perfect discrimination score and means the key was never tested.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from . import consumer_reach as cr
from .citation_audit import SCANNED_DOCS

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Verdicts.  ``SEPARATES`` is the only one that licenses keying on it.
SEPARATES = "SEPARATES"
NARROWED_NOT_SEPARATED = "NARROWED_NOT_SEPARATED"
VACUOUS = "VACUOUS"

#: Points of non-``LIVE`` fraction the narrow key must gain over the wide one.
#: See the module docstring: the reading it was written for clears or misses it
#: by a margin large enough that the exact value is not load-bearing.
SEPARATION_MARGIN = 0.25

#: Fewer hits than this and the composition is not a reading, it is an anecdote.
MIN_HITS = 3

#: How far after a call site a recorded return value may sit and still be read
#: as that call's result.  Prose in the decision log puts the verdict in the
#: same clause ("``reprobe('STATE.md')`` ... -> ``INERT_COMPOSED`` gen-1").
RETURN_WINDOW = 160

#: A backticked SCREAMING_SNAKE token: this package's spelling of a verdict, and
#: so of a *recorded return value*.  Four characters minimum keeps ``CI`` and
#: ``PR`` out.
_RETURN_TOKEN = re.compile(r"`([A-Z][A-Z0-9_]{3,})`")


@dataclass(frozen=True)
class Composition:
    """What a key matched, graded by the verdict the key is meant to predict."""

    hits: int
    live: int

    @property
    def non_live_fraction(self) -> float:
        return (self.hits - self.live) / self.hits if self.hits else 0.0


@dataclass(frozen=True)
class Reading:
    """A wide key, a narrow key, and whether narrowing bought anything."""

    wide: Composition
    narrow: Composition
    wide_names: tuple[str, ...]
    narrow_names: tuple[str, ...]
    verdict: str

    @property
    def narrowing(self) -> float:
        """How many times smaller the narrow key's matched set is."""
        return self.wide.hits / self.narrow.hits if self.narrow.hits else 0.0

    @property
    def discrimination(self) -> float:
        """Points of non-``LIVE`` fraction gained by narrowing.  The reading."""
        return self.narrow.non_live_fraction - self.wide.non_live_fraction


def population(root: Path | None = None) -> dict[str, str]:
    """Every public module-level function name, mapped to its reach verdict.

    The population is :func:`consumer_reach.module_functions`' — population B —
    because that is the population the verdict under test would be issued
    *into*.  A key measured against any other set answers a question nobody
    asked.
    """
    out: dict[str, str] = {}
    for reach in cr.module_reaches(root):
        out[reach.definition.name] = reach.verdict
    return out


def scanned_prose(root: Path | None = None) -> str:
    """The decision-log surface a key is matched against."""
    base = root or REPO_ROOT
    bodies = []
    for doc in SCANNED_DOCS:
        path = base / doc
        if path.exists():
            bodies.append(path.read_text(encoding="utf-8"))
    return "\n".join(bodies)


def _call_sites(name: str, prose: str) -> list[re.Match[str]]:
    """Backticked call syntax for ``name`` carrying a non-empty argument."""
    pattern = re.compile(r"`[^`\n]*\b" + re.escape(name) + r"\(\s*[^)\s][^`\n]*`")
    return list(pattern.finditer(prose))


def called_with_argument(name: str, prose: str) -> bool:
    """D-196's **wide** key: the log shows the function being called."""
    return bool(_call_sites(name, prose))


def called_with_recorded_return(name: str, prose: str) -> bool:
    """The **narrow** key: a call site whose returned verdict is written down.

    This is the key D-196 deferred as "the right one and unmeasured".  It is
    strictly stronger evidence than the wide key — not "somebody wrote the name
    with parentheses" but "it ran, with this argument, and here is what came
    back".  Being stronger evidence and being a *discriminating* key are
    different properties, and this module exists because only the first was
    obvious.
    """
    for match in _call_sites(name, prose):
        if _RETURN_TOKEN.search(prose[match.end():match.end() + RETURN_WINDOW]):
            return True
    return False


def _compose(names: Sequence[str], verdicts: dict[str, str]) -> Composition:
    return Composition(hits=len(names),
                       live=sum(1 for n in names if verdicts.get(n) == "LIVE"))


def measure(wide: Callable[[str, str], bool] = called_with_argument,
            narrow: Callable[[str, str], bool] = called_with_recorded_return,
            root: Path | None = None) -> Reading:
    """Grade ``narrow`` as a candidate key, using ``wide`` as its control.

    The control is not decoration.  "9 of 10 hits are ``LIVE``" sounds damning
    until the wide key reads 32 of 35 — at which point the narrow key has not
    made the situation worse *or better*, and that is the finding.
    """
    verdicts = population(root)
    prose = scanned_prose(root)
    names = sorted(verdicts)

    wide_names = tuple(n for n in names if wide(n, prose))
    narrow_names = tuple(n for n in names if narrow(n, prose))

    wide_comp = _compose(wide_names, verdicts)
    narrow_comp = _compose(narrow_names, verdicts)

    if narrow_comp.hits < MIN_HITS or wide_comp.hits < MIN_HITS:
        verdict = VACUOUS
    elif (narrow_comp.non_live_fraction
          - wide_comp.non_live_fraction) >= SEPARATION_MARGIN:
        verdict = SEPARATES
    else:
        verdict = NARROWED_NOT_SEPARATED

    return Reading(wide=wide_comp, narrow=narrow_comp, wide_names=wide_names,
                   narrow_names=narrow_names, verdict=verdict)


def report(root: Path | None = None) -> str:
    """One screen: both numbers, labelled so they cannot be read as one."""
    r = measure(root=root)
    lines = [
        f"key_discrimination — {r.verdict}",
        "",
        f"  wide    {r.wide.hits:3d} hits  {r.wide.live:3d} LIVE  "
        f"non-LIVE {r.wide.non_live_fraction:6.1%}",
        f"  narrow  {r.narrow.hits:3d} hits  {r.narrow.live:3d} LIVE  "
        f"non-LIVE {r.narrow.non_live_fraction:6.1%}",
        "",
        f"  narrowing        {r.narrowing:.1f}x  (how much smaller)",
        f"  discrimination  {r.discrimination:+.1%}  (whether it selects; "
        f"margin {SEPARATION_MARGIN:.0%})",
        "",
        f"  narrow hits: {', '.join(r.narrow_names) or '-'}",
    ]
    if r.verdict == NARROWED_NOT_SEPARATED:
        lines += ["", "  A smaller sample of the same population. Any residue "
                      "member it catches is",
                  "  caught by the coincidence that the others have callers "
                      "(D-193, D-196)."]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI
    print(report())
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
