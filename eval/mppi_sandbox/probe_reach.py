"""How many guards can the dynamic probe actually reach? — STATE #2, generalising D-052.

D-052's sharpest finding was not about any guard.  It was that
:mod:`exemption_masking`'s method — suppress the exemption, read again — was
applicable to **1 of 12** typed pairs, because the one guard D-050 probed
happens to accept ``declared=`` for an unrelated reason.  The instrument looked
general; its reach was a fact about the code it read, and nobody had asked.

This module asks the same question of the *other* dynamic probe.
:mod:`guard_direction` stands up a throwaway git repository per (guard, path),
commits the offence, and compares the readings.  It carries **2** entries in
:data:`guard_direction.PROBES`, and :func:`guard_direction.unprobed_revocable`
reports that table complete.  The question D-052 forces is whether **2** is a
designed bound or another coincidence.

It is a coincidence, and this module names the thing holding the place:

    **16** of the 40 guards take a repo root and are therefore addressable by a
    scratch repo at all.  Of those 16, the fixture
    :func:`guard_direction.build_scratch_repo` builds can carry **9** — the
    other **7 raise**, because the fixture contains the five declared local-only
    paths and one control file and nothing else, while those guards read
    ``docs/decisions.md`` or ``scripts/*.sh``.  The probe's reach is bounded by
    its **fixture**, not by its design, and the fixture is exactly large enough
    for the two guards that already have probes.

The mirror was checked against the wrong population
---------------------------------------------------

:func:`guard_direction.unprobed_revocable` compares :data:`PROBES` against
:func:`guard_reflexivity.revocable` — the ``DIFFERENCE``-shaped guards, of which
there are 2.  So it reads clean by construction.  Reachability and revocability
are different properties: revocability says a *before/after* verdict would be
interesting, reachability says one is *possible*.  A clearance over the smaller
of the two is D-045's shape — a registry checked against a population that
cannot contain its omissions.  :func:`reach_gap` is the mirror over the
population the probe can actually address.

Routed around, not merely reported (D-052's discipline)
--------------------------------------------------------

Reporting "7 guards raise" would leave the reach unmeasured, so
:func:`build_enriched_repo` adds the read surfaces those guards name — the
document scan and the writer scan — to the same scratch repo, and the reach is
re-measured.  The difference between the two numbers is the measured price of
the fixture coincidence, rather than an argument that one exists.

Verdicts, and why ``MUTE`` is split
------------------------------------

``READABLE``
    The guard runs in the fixture and reads **non-empty** — it is *loud at rest*.
    Until D-056 this verdict alone defined ``Reach.probeable``; see the retraction
    below.  The reading itself is still an honest measurement and is unchanged.
``MUTE_FIXTURE``
    Runs, reads empty in the fixture, **non-empty at the real root**.  The guard
    is alive and the fixture does not carry its subject.  Distinguished from:
``UNDECIDABLE``
    Reads empty in *both*.  Nothing here separates "the fixture is too small"
    from "this guard reads empty everywhere", and D-050's rule is that a probe
    which cannot tell those apart has not measured anything.  Named rather than
    folded into ``MUTE_FIXTURE``, for the reason D-052 kept ``VACUOUS`` out of
    ``INERT``.
``FIXTURE_ERROR``
    Raises.  Notably these guards raise rather than returning empty, which is
    :mod:`local_only_audit`'s own stated discipline working: an audit that
    degrades to "found nothing" would have scored ``UNDECIDABLE`` here and the
    fixture gap would have been invisible.
``NOT_A_READING``
    The return value is not a collection of names — ``report``-style guards
    returning ``str``.  A membership verdict over a string is undefined, so it
    is refused rather than measured by ``len()``.

Retraction — the probeability bar had the sign flipped (D-056)
---------------------------------------------------------------

``Reach.probeable`` was ``verdict == READABLE``: the guard is loud at rest.  It
claimed to answer *could a before/after probe score a verdict here*, and D-055's
correction one layer up — the bar is **membership**, subject absent before and
present after — says the opposite.  A guard silent at rest is the one a probe
wants; a guard already loud is the state that made D-055's third probe a false
positive, because the reading it scored was the fixture's and not the act's.

This is checkable without a new fixture, against ground truth nobody had
consulted: both entries in :data:`guard_direction.PROBES` are probeable **by
execution**.  Both score not-``READABLE``, in the base and enriched fixtures
alike.  So the bar was wrong on **2 of the 2** cases where the answer is known —
and this package's own test asserted them ``not probeable`` in the same breath
as a docstring calling them probeable, one line apart.

The measured consequences, all retractions of numbers this module published:

* :func:`unreachable` — the mirror whose job is to state what a reach number
  excluded — listed both working probes as unreachable.
* The reach denominator was **6 of 16**.  Against
  :attr:`Reach.act_addressable` it is **15 of 16**; only ``lam_dependence.report``
  is genuinely refused, and it returns a ``str``.
* So "readable, unprobed" = 6 was never the gap.  :func:`act_gap` = **13**, and
  D-055 had already measured the yield of the 6 at 0.

:attr:`Reach.reads_at_rest` keeps the old measurement under a name that says what
it is.  :func:`misscored_probes` is the ground-truth mirror, pinned empty.
"""

from __future__ import annotations

import importlib
import inspect
import shutil
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import guard_direction as gd
from . import guard_reflexivity as gr

#: The guard takes ``root: Path | None`` — a scratch **git repository** can be
#: handed to it, which is the substrate :mod:`guard_direction` builds.
SUBSTRATE_REPO_ROOT = "REPO_ROOT"
#: Takes ``package``/``module`` — addressable, but by a scratch *source tree*,
#: which is a different fixture than the one the probe has.
SUBSTRATE_PACKAGE_SOURCE = "PACKAGE_SOURCE"
#: Takes an already-scanned pool or an already-scored result.  Addressable only
#: through whatever produced that argument; no fixture reaches it directly.
SUBSTRATE_SCANNED_POOL = "SCANNED_POOL"
#: Takes scenarios, metrics, weights — nothing a filesystem fixture varies.
SUBSTRATE_DOMAIN = "DOMAIN"

VERDICT_READABLE = "READABLE"
VERDICT_MUTE_FIXTURE = "MUTE_FIXTURE"
VERDICT_UNDECIDABLE = "UNDECIDABLE"
VERDICT_FIXTURE_ERROR = "FIXTURE_ERROR"
VERDICT_NOT_A_READING = "NOT_A_READING"

#: Parameter names that point a guard at a repository root.
ROOT_PARAMS = ("root",)
#: Parameter names that point a guard at a source tree to scan.
SOURCE_PARAMS = ("package", "module")
#: Parameter names that hand a guard a population somebody else already built.
POOL_PARAMS = ("pool", "screened", "scored")

#: Surfaces the fixture must carry for the document- and writer-scanning guards.
#: Derived from the exceptions the base fixture raises, not from a wish list —
#: see :func:`build_enriched_repo`.
READ_SURFACES = ("docs", "scripts")


class ReachError(RuntimeError):
    """The reach measurement could not be performed as described."""


# --------------------------------------------------------------------------
# substrate — derived from the signature, not typed
# --------------------------------------------------------------------------


def _callable_of(guard: gr.Guard) -> Callable[..., Any]:
    try:
        module = importlib.import_module(f"{__package__}.{guard.module}")
        return getattr(module, guard.name)
    except (ImportError, AttributeError) as exc:  # pragma: no cover - defensive
        raise ReachError(f"{guard.qualname}: not importable: {exc}") from exc


def substrate_of(guard: gr.Guard) -> str:
    """Which fixture, if any, could point this guard somewhere else.

    Read off :func:`inspect.signature` rather than a table, because a table is
    the thing D-045 keeps catching.  The order matters: a guard taking both
    ``pool`` and ``package`` (``misnamed_scopes``) is scored by the *strongest*
    handle a fixture has on it, which is the source tree.
    """
    params = inspect.signature(_callable_of(guard)).parameters
    if any(p in params for p in ROOT_PARAMS):
        return SUBSTRATE_REPO_ROOT
    if any(p in params for p in SOURCE_PARAMS):
        return SUBSTRATE_PACKAGE_SOURCE
    if any(p in params for p in POOL_PARAMS):
        return SUBSTRATE_SCANNED_POOL
    return SUBSTRATE_DOMAIN


def substrates(pool: Iterable[gr.Guard] | None = None) -> dict[str, tuple[str, ...]]:
    """Every guard, partitioned by substrate.

    Pinned as a **partition** in the tests — the union must equal the guard pool
    exactly — so a substrate rule that stops matching cannot quietly shrink the
    population this module reports over.  D-052's equality pin, same reason.
    """
    guards = tuple(pool if pool is not None else gr.guards())
    out: dict[str, list[str]] = {}
    for g in guards:
        out.setdefault(substrate_of(g), []).append(g.qualname)
    return {k: tuple(sorted(v)) for k, v in sorted(out.items())}


def root_addressable(pool: Iterable[gr.Guard] | None = None) -> tuple[gr.Guard, ...]:
    """Guards a scratch git repository can be handed to at all."""
    guards = tuple(pool if pool is not None else gr.guards())
    return tuple(g for g in guards if substrate_of(g) == SUBSTRATE_REPO_ROOT)


# --------------------------------------------------------------------------
# reading a guard uniformly
# --------------------------------------------------------------------------


def normalise(value: Any) -> frozenset[str] | None:
    """A guard's return value as a set of names, or ``None`` if it is not one.

    ``None`` is the ``NOT_A_READING`` case and is deliberately not an empty set:
    ``len("")`` and ``len(())`` are both 0 and mean entirely different things,
    and folding them would report a ``report()``-style guard as ``UNDECIDABLE``
    — a measurement where none was possible.
    """
    if value is None or isinstance(value, (str, bytes, int, float, bool)):
        return None
    for attr in ("changed", "added", "removed"):  # tree_provenance.Drift
        if hasattr(value, attr):
            return frozenset(
                str(x) for a in ("changed", "added", "removed")
                for x in getattr(value, a, ())
            )
    if isinstance(value, dict):
        return frozenset(str(k) for k in value)
    try:
        return frozenset(str(x) for x in value)
    except TypeError:
        return None


def read_at(guard: gr.Guard, root: Path) -> frozenset[str] | None:
    """Call the guard against ``root`` and normalise what comes back."""
    return normalise(_callable_of(guard)(root=root))


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------


def build_enriched_repo(root: Path, source: Path | None = None) -> tuple[str, ...]:
    """:func:`guard_direction.build_scratch_repo` plus the surfaces it omits.

    The base fixture holds the five declared local-only paths and one control
    file — everything the two existing probes read and nothing else.  The
    document-scanning and writer-scanning guards raise on it.  This copies the
    real repository's :data:`READ_SURFACES` in and commits them, so the same
    before/after machinery can address those guards too.

    Returns the surfaces actually copied, so a missing one is a reported fact
    rather than a silently smaller fixture.
    """
    gd.build_scratch_repo(root)
    src = (source or _repo_root()).resolve()
    copied: list[str] = []
    for rel in READ_SURFACES:
        origin = src / rel
        if not origin.is_dir():
            continue
        shutil.copytree(origin, root / rel, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        copied.append(rel)
    if not copied:
        raise ReachError(f"no read surfaces found under {src} — fixture would be "
                         "identical to the base one and the comparison meaningless")
    subprocess.run(("git", "-C", str(root), "add", "-A"),
                   check=True, capture_output=True)
    subprocess.run(("git", "-C", str(root), "commit", "-qm", "read surfaces"),
                   check=True, capture_output=True)
    return tuple(copied)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------
# the measurement
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Reach:
    """One guard's readability in one fixture, next to its reading at HEAD."""

    guard: str
    verdict: str
    fixture_size: int | None = None
    real_size: int | None = None
    note: str = ""

    @property
    def reads_at_rest(self) -> bool:
        """Is the guard's reading non-empty **before any act** — is it loud?

        This is exactly what :func:`measure` computes, and it was called
        ``probeable`` for three cycles.  It is not probeability: it is the
        fixture's loudness at rest, and D-056 measured the two to disagree on
        every case where the answer is known.  See :func:`misscored_probes`.
        """
        return self.verdict == VERDICT_READABLE

    @property
    def act_addressable(self) -> bool:
        """Could a hand-written before/after act score a verdict on this guard?

        The honest precondition, and it is far weaker than
        :attr:`reads_at_rest`: the guard must *run* in the fixture and *return a
        reading*.  Silence at rest disqualifies nothing — under D-055's
        membership bar it is the state a probe **wants**, because a subject
        absent before and present after is the cleanest verdict available.
        Only :data:`VERDICT_FIXTURE_ERROR` (it raised) and
        :data:`VERDICT_NOT_A_READING` (no set to take membership in) are refused.
        """
        return self.verdict not in (VERDICT_FIXTURE_ERROR, VERDICT_NOT_A_READING)


def measure(guard: gr.Guard, fixture: Path, real: Path | None = None) -> Reach:
    """Read one guard in the fixture and at the real root, and score the pair."""
    real_root = (real or _repo_root()).resolve()
    try:
        here = read_at(guard, fixture)
    except Exception as exc:  # noqa: BLE001 - any failure is a fixture failure
        return Reach(guard.qualname, VERDICT_FIXTURE_ERROR,
                     note=f"{type(exc).__name__}: {str(exc)[:100]}")
    if here is None:
        return Reach(guard.qualname, VERDICT_NOT_A_READING,
                     note="return value is not a collection of names")
    try:
        there = read_at(guard, real_root)
    except Exception as exc:  # noqa: BLE001
        there = None
        real_note = f"real root raised {type(exc).__name__}"
    else:
        real_note = ""
    real_size = None if there is None else len(there)
    if here:
        return Reach(guard.qualname, VERDICT_READABLE, len(here), real_size, real_note)
    if real_size:
        return Reach(guard.qualname, VERDICT_MUTE_FIXTURE, 0, real_size,
                     real_note or "alive at HEAD, empty in the fixture")
    return Reach(guard.qualname, VERDICT_UNDECIDABLE, 0, real_size,
                 real_note or "empty in both — cannot separate small fixture "
                              "from a guard that never reads")


def reach(pool: Iterable[gr.Guard] | None = None, *, fixture: Path,
          real: Path | None = None) -> tuple[Reach, ...]:
    """Every root-addressable guard, measured in one fixture."""
    return tuple(measure(g, fixture, real) for g in root_addressable(pool))


def reach_gap(scored: Iterable[Reach]) -> tuple[str, ...]:
    """Guards the fixture can carry that :data:`guard_direction.PROBES` omits.

    The mirror :func:`guard_direction.unprobed_revocable` should have been.  It
    compares the probe table against ``revocable()`` — 2 guards — so it cannot
    report an omission outside that shape, and every guard here is outside it.
    Non-empty is not a defect on its own: a guard may be readable and
    uninteresting to a before/after probe.  It is the honest denominator for the
    claim "the probe table is complete", which was being made over 2.
    """
    have = set(gd.PROBES)
    return tuple(sorted(r.guard for r in scored
                        if r.reads_at_rest and r.guard not in have))


def act_gap(scored: Iterable[Reach]) -> tuple[str, ...]:
    """The honest denominator :func:`reach_gap` was standing in for.

    Guards an act *could* be written for, minus the two that have one.
    :func:`reach_gap` answers a narrower question — loud at rest and unprobed —
    and D-055 took the one member of it that was ever tested and measured its
    yield at **0**, because loudness at rest is what made that verdict a false
    positive.  Selecting on it is therefore not a weak proxy for probeability
    but an adverse one, and this is the population the claim "the probe table is
    complete" is actually made over.
    """
    have = set(gd.PROBES)
    return tuple(sorted(r.guard for r in scored
                        if r.act_addressable and r.guard not in have))


def misscored_probes(scored: Iterable[Reach]) -> tuple[str, ...]:
    """Registered probes this module's own bar refuses — must be empty (D-056).

    The ground truth nobody consulted: every entry in :data:`guard_direction.PROBES`
    is probeable **by execution** — it has a liveness act, it runs each cycle, and
    D-055 re-confirmed both under the stricter membership bar.  So any predicate
    claiming to decide probeability must score all of them probeable, and that is
    checkable without a single new fixture.

    Under the old ``probeable = READABLE`` bar this returned **both** entries: both
    registered probes read empty at rest, in the base and enriched fixtures alike.
    A 2-of-2 false-negative rate on the only population where the answer is known
    — and the package's own test asserted the two ``not probeable`` in the same
    breath as a docstring calling them probeable.  Against
    :attr:`Reach.act_addressable` it is empty, which is the whole claim.

    D-106 narrows the population from :data:`guard_direction.PROBES` to the
    probes that use *this module's* fixture.  "Every entry has a liveness act
    that runs each cycle" is still true of all of them; what stopped being true
    is that the act runs **here**.  A probe that constructs its own repository
    is unreachable in the shared scratch one for a reason that says nothing
    about whether it is probeable, and scoring it refused would make this
    module's own ground truth wrong in the direction it was written to catch.
    The excluded set is named by :func:`guard_direction.own_fixture_probes`,
    derived from the table rather than typed beside it.
    """
    covered = set(gd.shared_fixture_probes())
    return tuple(sorted(r.guard for r in scored
                        if r.guard in covered and not r.act_addressable))


def fixture_gap(base: Iterable[Reach], enriched: Iterable[Reach]) -> tuple[str, ...]:
    """Guards the base fixture cannot carry but the enriched one can.

    The measured price of the coincidence: each of these is a guard whose
    absence from the probe's reach is a property of what
    :func:`guard_direction.build_scratch_repo` happens to write, not of the
    guard or of the probe.
    """
    before = {r.guard: r for r in base}
    return tuple(sorted(r.guard for r in enriched
                        if r.verdict != VERDICT_FIXTURE_ERROR
                        and before.get(r.guard) is not None
                        and before[r.guard].verdict == VERDICT_FIXTURE_ERROR))


def unreachable(scored: Iterable[Reach]) -> tuple[str, ...]:
    """Root-addressable guards **no act** in this fixture could score.

    The clearance-blocking mirror, fifth-and-something registry in this package
    to get one: a reach number is a measurement only if what it excluded is
    stated next to it.  Which made it worse that the exclusion was drawn on
    :attr:`Reach.reads_at_rest` and so listed both registered probes as
    unreachable — the mirror stating what was excluded was excluding the two
    guards that demonstrably work.  Drawn on :attr:`Reach.act_addressable` it
    keeps only the genuine refusals: raised, or returned no set.
    """
    return tuple(sorted(f"{r.guard}: {r.verdict} {r.note}".strip()
                        for r in scored if not r.act_addressable))


def report(pool: Iterable[gr.Guard] | None = None) -> str:  # pragma: no cover - CLI shape
    import tempfile

    guards = tuple(pool if pool is not None else gr.guards())
    parts = substrates(guards)
    lines = [f"guards: {len(guards)}"]
    for name, members in parts.items():
        lines.append(f"  {name:16s} {len(members)}")
    with tempfile.TemporaryDirectory() as td:
        base_root = Path(td) / "base"
        gd.build_scratch_repo(base_root)
        base = reach(guards, fixture=base_root)
        rich_root = Path(td) / "rich"
        copied = build_enriched_repo(rich_root)
        rich = reach(guards, fixture=rich_root)
    lines.append(f"root-addressable: {len(base)}")
    lines.append(f"  base fixture     loud={sum(r.reads_at_rest for r in base)} "
                 f"act-addressable={sum(r.act_addressable for r in base)} "
                 f"errors={sum(r.verdict == VERDICT_FIXTURE_ERROR for r in base)}")
    lines.append(f"  enriched {copied} loud={sum(r.reads_at_rest for r in rich)} "
                 f"act-addressable={sum(r.act_addressable for r in rich)} "
                 f"errors={sum(r.verdict == VERDICT_FIXTURE_ERROR for r in rich)}")
    for r in rich:
        lines.append(f"    {r.verdict:15s} {r.guard} "
                     f"fixture={r.fixture_size} real={r.real_size} {r.note}")
    lines.append(f"probes registered: {len(gd.PROBES)}")
    lines.append(f"misscored probes (must be 0): {len(misscored_probes(rich))}")
    for name in misscored_probes(rich):
        lines.append(f"  {name}")
    lines.append(f"reach gap (loud at rest, unprobed): {len(reach_gap(rich))}")
    for name in reach_gap(rich):
        lines.append(f"  {name}")
    lines.append(f"act gap (act-addressable, unprobed): {len(act_gap(rich))}")
    for name in act_gap(rich):
        lines.append(f"  {name}")
    gap = fixture_gap(base, rich)
    lines.append(f"fixture gap (base error -> enriched runnable): {len(gap)}")
    for name in gap:
        lines.append(f"  {name}")
    lines.append(f"unreachable: {len(unreachable(rich))}")
    for name in unreachable(rich):
        lines.append(f"  {name}")
    return "\n".join(lines)


def main() -> int:  # pragma: no cover - CLI
    print(report())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
