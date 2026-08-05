"""D-080's defect generalised: scans that key a *qualified* entity by its bare
name — and whether the shipped tree can even show it.

D-080 found that :func:`exemption_control.references` matched reads by attribute
name and discarded the module, so ``predicate_vacuity.EXCLUDED_TESTS`` and
``guard_vacuity.EXCLUDED_TESTS`` each received the **union** of the other's
reads.  One published magnitude ("read in exactly one place") was wrong as a
result, and re-taking the count would never have caught it: the count was fresh,
the *key* was broken.  That is a defect class, not an incident, and this module
asks the two questions the class raises.

**1. Is the blind spot live?**  A bare-name key can only conflate if two
qualified entities in the package actually share a name.  :func:`shared_names`
is that population, and it is not theoretical: **15 of 280** module-level
constants are owned by two or more modules.  ``EXCLUDED_TESTS`` was one of
fifteen.

**2. Does a given scan conflate?**  Not inferred from syntax — *measured*.
:func:`probe` calls a scan with two same-named, different-module registries and
compares the readings.  This deliberately avoids an "is it qualified?" AST
heuristic, because the heuristic would be another name-keyed scan and would owe
this module its own audit.

The third verdict is the point of the file.  Two readings can be identical
because the scan conflates, or identical because **both are empty** — and an
empty pair proves nothing whatsoever.  D-075's ``"no D-074 value survives"``
passed for exactly that reason, and D-076 spent a cycle separating "removes
nothing" from "is not wired".  So :data:`VERDICT_VACUOUS` is reported
separately, and a probe that lands there is a probe that **has not run**:

* :data:`VERDICT_DISTINGUISHES` — the readings differ, so the scan is keyed.
* :data:`VERDICT_IDENTICAL` — the readings agree and are non-empty.  Conflation.
* :data:`VERDICT_VACUOUS` — both readings are empty.  No information, either way.

On the shipped tree :func:`unresolved_reads` grades ``VACUOUS``: it keys on the
bare name by construction (an unresolved read has no owner to key on), so its
"the resolved count is a lower bound" is a claim about a *name* rather than
about a *registry* — but the package currently contains **zero** unresolved
reads, so no probe over the shipped population can demonstrate it.  That is why
:func:`synthetic_control` exists: a two-module fixture built so the readings
*must* differ, which is where the bare-keyed scan is finally observable.  Per
D-078 and D-079 the control ships with its own controls — a no-op fixture that
must grade ``VACUOUS``, and a keyed scan over the same fixture that must grade
``DISTINGUISHES`` — because a control that cannot fail is D-075's defect one
layer up.

Refs: D-080 (the incident), D-079 (control your exemptions), D-078 (date the
quote), D-076 (bite vs wiring), D-075 (vacuous survival).
"""

from __future__ import annotations

import ast
import collections
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from . import exemption_control as ec

PACKAGE = Path(__file__).resolve().parent

#: Readings differ — the scan is keyed on the qualified entity.
VERDICT_DISTINGUISHES = "DISTINGUISHES"
#: Readings agree and are non-empty — the scan conflates the two entities.
VERDICT_IDENTICAL = "IDENTICAL"
#: Both readings are empty.  Identity here is not evidence of anything.
VERDICT_VACUOUS = "VACUOUS"


# ---------------------------------------------------------------------------
# Layer 1 — the population.  Can a bare-name key conflate anything at all?


def shared_names(package: Path | None = None) -> dict[str, tuple[str, ...]]:
    """Module-level constants whose bare name is owned by two or more modules.

    The denominator for every claim in this file.  An empty result would mean
    every bare-name key in the package is *latent* — wrong in principle, unable
    to bite in practice.  It is not empty.

    Restricted to ``UPPER_CASE`` module-level assignments: those are the
    registry-shaped names the package's scans are keyed on, and lowercasing the
    filter would fold in every local helper and drown the signal.
    """
    base = package or PACKAGE
    owners: dict[str, set[str]] = collections.defaultdict(set)
    for path in sorted(base.glob("*.py")):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:                                 # pragma: no cover
            continue
        for node in tree.body:
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    owners[target.id].add(path.stem)
    return {name: tuple(sorted(mods))
            for name, mods in sorted(owners.items()) if len(mods) > 1}


def constant_population(package: Path | None = None) -> int:
    """Every module-level ``UPPER_CASE`` constant — :func:`shared_names`' base.

    Published as a pair with the shared count, per D-078: a bare "15 names
    collide" is unreadable without the denominator it came from.
    """
    base = package or PACKAGE
    names: set[str] = set()
    for path in sorted(base.glob("*.py")):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:                                 # pragma: no cover
            continue
        for node in tree.body:
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    names.add(target.id)
    return len(names)


def collision_pairs(package: Path | None = None) -> tuple[tuple[str, str], ...]:
    """``(module, NAME)`` registries that share their bare name with another.

    The concrete probe inputs — every entity a bare-keyed scan could confuse for
    a sibling.  :func:`probe` consumes pairs drawn from here.
    """
    out: list[tuple[str, str]] = []
    for name, mods in shared_names(package).items():
        out.extend((mod, name) for mod in mods)
    return tuple(sorted(out))


# ---------------------------------------------------------------------------
# Layer 2 — differential probe.  Measured, not inferred from syntax.


@dataclass(frozen=True)
class Probe:
    """One scan, called with two same-named registries."""

    scan: str
    left: str
    right: str
    left_reading: str
    right_reading: str
    verdict: str


def _size(value: object) -> int | None:
    """Emptiness of a scan's reading, or ``None`` when it has no size.

    A scan returning a verdict *string* always answers something, so it has no
    empty reading and can never be vacuous — ``None`` says that rather than
    coercing the string to a number, which is how the first draft of this file
    printed ``binding`` as a 16-bit hash.
    """
    if isinstance(value, (tuple, list, set, frozenset, dict)):
        return len(value)
    if isinstance(value, str):
        return None
    raise TypeError(f"unsized reading: {type(value).__name__}")


def _shown(value: object, size: int | None) -> str:
    return str(value) if size is None else str(size)


def probe(scan: Callable[..., object],
          left: tuple[str, str],
          right: tuple[str, str],
          package: Path | None = None,
          name: str | None = None) -> Probe:
    """Call *scan* with two registries sharing a bare name; compare readings.

    ``VACUOUS`` when both readings are empty — see the module docstring.  The
    ordering matters: emptiness is checked **before** equality, because an empty
    pair is equal and reporting that as ``IDENTICAL`` is precisely the false
    positive this module exists to avoid.

    Equality is on the **values**, not on their sizes: two different read sets of
    the same length are different readings, and grading them ``IDENTICAL`` would
    invent a conflation that is not there.
    """
    lhs = scan(left, package) if package is not None else scan(left)
    rhs = scan(right, package) if package is not None else scan(right)
    l_size, r_size = _size(lhs), _size(rhs)
    if l_size == 0 and r_size == 0:
        verdict = VERDICT_VACUOUS
    elif lhs == rhs:
        verdict = VERDICT_IDENTICAL
    else:
        verdict = VERDICT_DISTINGUISHES
    return Probe(scan=name or getattr(scan, "__name__", repr(scan)),
                 left=f"{left[0]}.{left[1]}", right=f"{right[0]}.{right[1]}",
                 left_reading=_shown(lhs, l_size),
                 right_reading=_shown(rhs, r_size), verdict=verdict)


#: The name-keyed scans this package exposes over ``(module, NAME)`` registries.
#: :func:`ec.references` and :func:`ec.binding` were repaired by D-080;
#: :func:`ec.unresolved_reads` keys on the bare name by construction and is the
#: reason the synthetic layer exists.
SCANS: tuple[tuple[str, Callable[..., object]], ...] = (
    ("exemption_control.references", ec.references),
    ("exemption_control.unresolved_reads", ec.unresolved_reads),
    ("exemption_control.binding", ec.binding),
)

#: The one collision pair in the shipped tree whose members have *different*
#: read sets, so a keyed scan is obliged to separate them.  D-080's own case.
CANONICAL_PAIR = (("predicate_vacuity", "EXCLUDED_TESTS"),
                  ("guard_vacuity", "EXCLUDED_TESTS"))


def probes(package: Path | None = None) -> tuple[Probe, ...]:
    """Every scan in :data:`SCANS` probed against :data:`CANONICAL_PAIR`."""
    left, right = CANONICAL_PAIR
    return tuple(probe(fn, left, right, package=package, name=label)
                 for label, fn in SCANS)


def conflating(package: Path | None = None) -> tuple[str, ...]:
    """Scans measured to conflate — ``IDENTICAL`` on a pair that must differ."""
    return tuple(p.scan for p in probes(package)
                 if p.verdict == VERDICT_IDENTICAL)


def unprobed(package: Path | None = None) -> tuple[str, ...]:
    """Scans whose probe was ``VACUOUS`` — carried, not cleared.

    A vacuous probe is an *unrun* probe.  Reporting these separately is what
    stops a green suite from reading as "no scan conflates" when what it
    measured was "the tree could not tell".
    """
    return tuple(p.scan for p in probes(package)
                 if p.verdict == VERDICT_VACUOUS)


# ---------------------------------------------------------------------------
# Layer 3 — synthetic control.  Where a vacuous probe becomes observable.

#: Two modules that each define ``REG`` and read it two ways: resolvably (a bare
#: ``REG`` load, which owns its own module) and unresolvably (``self.REG``, whose
#: base is not a module alias).  **Both** read sets are built to differ — ``a``
#: has 2 of each, ``b`` has 1 — so the same fixture drives the bare-keyed scan
#: and its wrong-direction control.
#:
#: The first draft carried only the ``self.REG`` reads.  That made
#: :func:`ec.references` read ``0`` on both modules and grade ``VACUOUS``, so the
#: control D-079 requires proved nothing: with no scan able to separate ``a``
#: from ``b``, the bare scan's ``IDENTICAL`` was as consistent with a broken
#: fixture as with a broken scan.
_FIXTURE: dict[str, str] = {
    "a.py": (
        "REG = ('x',)\n"
        "def resolvable_one():\n"
        "    return REG\n"
        "def resolvable_two():\n"
        "    return REG\n"
        "class T:\n"
        "    def one(self):\n"
        "        return self.REG\n"
        "    def two(self):\n"
        "        return self.REG\n"
    ),
    "b.py": (
        "REG = ('y',)\n"
        "def resolvable_only():\n"
        "    return REG\n"
        "class U:\n"
        "    def only(self):\n"
        "        return self.REG\n"
    ),
}

#: A fixture with the same two registries and **no** unresolved reads, so a
#: probe over it must grade ``VACUOUS``.  Without this, ``VACUOUS`` would be a
#: verdict the control can never produce, and its appearance on the real tree
#: would be unfalsifiable.
_FIXTURE_NOOP: dict[str, str] = {
    "a.py": "REG = ('x',)\n",
    "b.py": "REG = ('y',)\n",
}


def _write(files: dict[str, str], root: Path) -> Path:
    for name, body in files.items():
        (root / name).write_text(body)
    return root


def synthetic_control() -> tuple[Probe, Probe, Probe]:
    """The bare-keyed scan, a keyed scan, and a no-op — over synthetic source.

    Returns ``(bare, keyed, noop)``:

    * **bare** — :func:`ec.unresolved_reads` over :data:`_FIXTURE`, where ``a``
      has two unattributable reads and ``b`` has one.  A keyed scan would report
      2 and 1; this reports the union — the same value twice — so ``IDENTICAL``.
      This is the observation the shipped tree cannot make.
    * **keyed** — :func:`ec.references` over the same fixture, where ``a`` has
      two resolvable reads and ``b`` has one, so it must grade
      ``DISTINGUISHES``.  It is the wrong-direction control D-079 requires: if
      nothing could separate ``a`` from ``b`` here, the bare result would be an
      artefact of the fixture rather than of the scan.
    * **noop** — the bare scan over :data:`_FIXTURE_NOOP`, which has nothing to
      find and must grade ``VACUOUS``.
    """
    left, right = ("a", "REG"), ("b", "REG")
    with tempfile.TemporaryDirectory() as live, \
            tempfile.TemporaryDirectory() as inert:
        live_root = _write(_FIXTURE, Path(live))
        inert_root = _write(_FIXTURE_NOOP, Path(inert))
        bare = probe(ec.unresolved_reads, left, right, package=live_root,
                     name="unresolved_reads@fixture")
        keyed = probe(ec.references, left, right, package=live_root,
                      name="references@fixture")
        noop = probe(ec.unresolved_reads, left, right, package=inert_root,
                     name="unresolved_reads@noop")
    return bare, keyed, noop


def report(package: Path | None = None) -> str:
    shared = shared_names(package)
    lines = [
        f"shared bare names : {len(shared)} of {constant_population(package)} "
        f"module-level constants",
        f"collision pairs   : {len(collision_pairs(package))}",
        "",
        "scan                                    left  right  verdict",
    ]
    for p in probes(package):
        lines.append(f"{p.scan:<40}{p.left_reading:<11}{p.right_reading:<11}"
                     f"{p.verdict}")
    lines.append("")
    lines.append("synthetic control (fixture: a has 2 unresolved, b has 1)")
    for p in synthetic_control():
        lines.append(f"{p.scan:<40}{p.left_reading:<11}{p.right_reading:<11}"
                     f"{p.verdict}")
    if conflating(package):
        lines.append(f"conflating on shipped tree: {', '.join(conflating(package))}")
    if unprobed(package):
        lines.append(f"unprobed (vacuous): {', '.join(unprobed(package))}")
    return "\n".join(lines)


if __name__ == "__main__":                                  # pragma: no cover
    print(report())
