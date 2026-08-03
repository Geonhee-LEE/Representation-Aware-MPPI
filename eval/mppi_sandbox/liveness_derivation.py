"""Can a probe's liveness act be *derived* rather than typed? — Q-068, STATE #1.

D-053 found that :mod:`guard_direction`'s reach is bounded by a hand-written
table of **2** :class:`guard_direction.Probe` entries, one layer below the table
:func:`guard_direction.unprobed_revocable` checks.  The obvious repair is to
stop typing the table: :func:`guard_reflexivity.acts_of` already enumerates the
git/filesystem operations each guard performs, with scope, derived from the
guard's own AST.  That is most of what a liveness act needs to know.

D-052 and D-053 both ended with the same instruction, so this module follows it
rather than shipping the repair: **measure the derivable fraction first.**

A liveness act is three things, not one
---------------------------------------

Reading the two hand-written acts back, each is a triple:

============================  ==========  ===========  ==========================
act                           scope       membership   subject
============================  ==========  ===========  ==========================
``_live_staged_declarations`` ``INDEX``   ``IN``       a member of
                                                       ``DECLARED_LOCAL_ONLY``
``_live_undeclared_drift``    ``WORKTREE`` ``OUT``     a tracked path *outside*
                                                       it (``CONTROL_PATH``)
============================  ==========  ===========  ==========================

``acts_of`` supplies exactly one of the three.  :class:`Act` carries
``tool``/``verb``/``scope``/``site``/``spelling``, and for a filesystem act the
spelling is the accessor name — ``read_text``, not the path it read.  So the
*subject* is structurally absent from the acts, and the membership sense is
absent too.  Both come from a different derivation, over
:class:`guard_reflexivity.Exemption`: a ``TYPED`` exemption names the registry
the subject must be inside (``AND``/``IN``) or outside (``SUB``/``NOT_IN``).

Three layers, and each one loses guards
----------------------------------------

:func:`derive` reports where each guard falls out, so the fraction is a census
with named exclusions rather than a ratio:

``NO_SCOPE``
    ``acts_of`` yields no mutable scope — nothing a fixture edit could move.
``NO_REGISTRY``
    No ``TYPED`` exemption, so no named set to draw a subject from.  A
    ``DERIVED`` exemption is an expression computed from the population itself;
    it names no constant a fixture can hold.
``NOT_PATHS``
    The registry resolves, but its members are not paths — claim ids, reading
    labels, precedence tokens.  Mutating a repository "at" ``SCOPED_CLAIMS`` is
    undefined, and scoring it derivable would be the D-050 defect of a probe
    that cannot tell a real reading from an impossible one.
``DERIVED``
    All three parts recovered.  This is the numerator, and it is **executed**
    (:func:`validate`) rather than asserted: the act runs in a scratch repo and
    the guard's reading must go non-empty, the same bar
    :func:`guard_direction.check_liveness` sets for the typed ones.

The precedence table, stated rather than hidden
-----------------------------------------------

A guard usually observes several scopes (``undeclared_drift`` reads ``COMMIT``,
``NAMESET`` and ``WORKTREE``), and only one of them is the cheapest window to
wake it through.  :data:`SCOPE_PRECEDENCE` picks.  That is a hand-written table,
and after D-045/D-047/D-049 it would be dishonest to call it anything else — but
it is a table over the **scope vocabulary** (4 tokens, fixed by
:mod:`guard_reflexivity`), not over the guard pool, so it does not grow when the
pool does.  :func:`unranked_scopes` is its mirror, over the scopes the pool
actually exhibits.
"""

from __future__ import annotations

import importlib
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from . import guard_direction as gd
from . import guard_reflexivity as gr
from . import probe_reach as pr

#: The subject must be **inside** the named registry for the guard to report it
#: (``AND``/``IN`` exemptions keep the intersection).
MEMBERSHIP_IN = "IN"
#: The subject must be **outside** it (``SUB``/``NOT_IN`` remove members).
MEMBERSHIP_OUT = "OUT"

ORIGIN_DERIVED = "DERIVED"
ORIGIN_NO_SCOPE = "NO_SCOPE"
ORIGIN_NO_REGISTRY = "NO_REGISTRY"
ORIGIN_NOT_PATHS = "NOT_PATHS"

LIVENESS_LIVE = "LIVE"
LIVENESS_DEAD = "DEAD"
LIVENESS_ERROR = "ERROR"
#: The reading is non-empty and the act did not put it there — the fixture was
#: already loud.  Scored apart from ``DEAD`` because the two are different
#: facts: ``DEAD`` says the act moved nothing *and there was nothing*, ``INERT``
#: says the act moved nothing *and a non-emptiness bar could not tell*.
LIVENESS_INERT = "INERT"

#: Cheapest-first: which window to wake a multi-scope guard through.  An index
#: edit is visible to a ``COMMIT``-scoped reader only after a commit, so the
#: narrower scope is the one to mutate.  Over the vocabulary, not the pool.
SCOPE_PRECEDENCE = (
    gr.SCOPE_INDEX,
    gr.SCOPE_WORKTREE,
    gr.SCOPE_NAMESET,
    gr.SCOPE_COMMIT,
)

#: Exemption senses that keep the intersection vs. remove members.
_SENSE_MEMBERSHIP = {
    gr.SENSE_AND: MEMBERSHIP_IN,
    gr.SENSE_IN: MEMBERSHIP_IN,
    gr.SENSE_SUB: MEMBERSHIP_OUT,
    gr.SENSE_NOT_IN: MEMBERSHIP_OUT,
}


class DerivationError(RuntimeError):
    """A derivation could not be performed as described."""


# --------------------------------------------------------------------------
# the three parts
# --------------------------------------------------------------------------


def mutable_scope(qualname: str) -> str | None:
    """The scope a fixture edit should target to wake this guard.

    ``None`` when the guard performs no act in a rankable scope — ``UNKNOWN``
    acts are not a window, they are an unread dispatcher (D-048's shape).
    """
    scopes = {a.scope for a in gr.acts_of(qualname)}
    for scope in SCOPE_PRECEDENCE:
        if scope in scopes:
            return scope
    return None


def unranked_scopes(pool: Iterable[gr.Guard] | None = None) -> tuple[str, ...]:
    """Scopes the pool exhibits that :data:`SCOPE_PRECEDENCE` does not rank.

    The mirror the precedence table needs.  ``UNKNOWN`` is excluded by name: it
    is guard_reflexivity's own "no scope decided", not a window someone forgot
    to rank, and folding it in would make this mirror permanently non-empty and
    therefore permanently ignored.
    """
    guards = tuple(pool if pool is not None else gr.guards())
    seen = {a.scope for g in guards for a in gr.acts_of(g.qualname)}
    return tuple(sorted(seen - set(SCOPE_PRECEDENCE) - {gr.SCOPE_UNKNOWN}))


def _registry_of(guard: gr.Guard) -> tuple[str, str] | None:
    """``(constant name, membership)`` from the guard's first TYPED exemption."""
    for ex in guard.typed_exemptions:
        membership = _SENSE_MEMBERSHIP.get(ex.sense)
        if ex.constant and membership:
            return ex.constant, membership
    return None


def resolve_registry(guard: gr.Guard, name: str) -> tuple[str, ...] | None:
    """Members of a named constant, or ``None`` if it does not resolve."""
    try:
        module = importlib.import_module(f"{__package__}.{guard.module}")
        value = getattr(module, name)
    except (ImportError, AttributeError):
        return None
    try:
        return tuple(sorted(str(x) for x in value))
    except TypeError:
        return None


def path_members(members: Iterable[str], root: Path | None = None) -> tuple[str, ...]:
    """Registry members that name a path that exists under ``root``.

    Existence, not spelling.  A ``"/"``-contains test would accept
    ``"calibrated/other"`` and reject ``"TODO.md"``, and the question this
    answers is whether a fixture can *hold* the subject — which is a fact about
    the filesystem, so it is asked of the filesystem.
    """
    base = (root or pr._repo_root()).resolve()
    return tuple(m for m in members if (base / m).exists())


# --------------------------------------------------------------------------
# the recipe
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Recipe:
    """A liveness act assembled from the guard's own code, or the reason not."""

    guard: str
    origin: str
    scope: str = ""
    membership: str = ""
    registry: str = ""
    subject: str = ""
    note: str = ""

    @property
    def derived(self) -> bool:
        return self.origin == ORIGIN_DERIVED

    def act(self, root: Path) -> None:
        """Perform the mutation in a scratch repo built by :mod:`guard_direction`."""
        if not self.derived:
            raise DerivationError(f"{self.guard}: {self.origin} — no act to perform")
        target = root / self.subject
        target.parent.mkdir(parents=True, exist_ok=True)
        # A ``git add`` of a file identical to HEAD stages nothing — the no-op
        # act that guard_direction's own first draft shipped.  Write first,
        # always, and write something the base fixture did not.
        target.write_text("derived liveness edit\n", encoding="utf-8")
        if self.scope == gr.SCOPE_WORKTREE:
            return
        subprocess.run(("git", "-C", str(root), "add", self.subject),
                       check=True, capture_output=True)
        if self.scope in (gr.SCOPE_NAMESET, gr.SCOPE_COMMIT):
            subprocess.run(("git", "-C", str(root), "commit", "-qm",
                            f"derived liveness: {self.subject}"),
                           check=True, capture_output=True)


def derive(guard: gr.Guard, root: Path | None = None) -> Recipe:
    """Assemble a liveness act for one guard, or name the layer that failed."""
    scope = mutable_scope(guard.qualname)
    if scope is None:
        return Recipe(guard.qualname, ORIGIN_NO_SCOPE,
                      note="no act in a rankable scope")
    found = _registry_of(guard)
    if found is None:
        return Recipe(guard.qualname, ORIGIN_NO_REGISTRY, scope=scope,
                      note="no TYPED exemption naming a constant")
    name, membership = found
    members = resolve_registry(guard, name)
    if members is None:
        return Recipe(guard.qualname, ORIGIN_NO_REGISTRY, scope=scope,
                      membership=membership, registry=name,
                      note=f"{name} does not resolve to a collection")
    paths = path_members(members, root)
    if not paths:
        return Recipe(guard.qualname, ORIGIN_NOT_PATHS, scope=scope,
                      membership=membership, registry=name,
                      note=f"{name}: {len(members)} members, 0 name a path")
    # ``IN`` wants a registry member; ``OUT`` wants the complement, and the
    # fixture ships exactly one witness for that — the control file whose whole
    # purpose is to be tracked and undeclared.
    subject = paths[0] if membership == MEMBERSHIP_IN else gd.CONTROL_PATH
    return Recipe(guard.qualname, ORIGIN_DERIVED, scope=scope,
                  membership=membership, registry=name, subject=subject,
                  note=f"{'member of' if membership == MEMBERSHIP_IN else 'outside'} "
                       f"{name}, {len(paths)}/{len(members)} members are paths")


def recipes(pool: Iterable[gr.Guard] | None = None,
            root: Path | None = None) -> tuple[Recipe, ...]:
    """A recipe (or a named failure) for every root-addressable guard."""
    return tuple(derive(g, root) for g in pr.root_addressable(pool))


def census(scored: Iterable[Recipe]) -> dict[str, int]:
    """How many guards fell out at each layer.  The denominator, stated."""
    out = {ORIGIN_DERIVED: 0, ORIGIN_NO_SCOPE: 0,
           ORIGIN_NO_REGISTRY: 0, ORIGIN_NOT_PATHS: 0}
    for r in scored:
        out[r.origin] = out.get(r.origin, 0) + 1
    return out


# --------------------------------------------------------------------------
# executing it — a derived act is a claim until it wakes the guard
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Liveness:
    """What the derived act did when it was actually run.

    Both sides are recorded, because the verdict is a *difference* and a
    one-sided reading cannot express one.  See :func:`validate` for why that is
    not a refinement but the correction of a wrong answer.
    """

    guard: str
    outcome: str
    reading: int = 0
    before: int = 0
    note: str = ""

    @property
    def live(self) -> bool:
        return self.outcome == LIVENESS_LIVE

    @property
    def moved(self) -> bool:
        """Did the reading change at all across the act?"""
        return self.reading != self.before


def validate(recipe: Recipe, workdir: Path, guard: gr.Guard,
             enriched: bool = True) -> Liveness:
    """Run the derived act in a scratch repo and read the guard **both sides**.

    The bar is that the act **puts its own subject** into the reading: the
    subject is absent before and present after.  Two weaker bars were shipped
    before this one and both score a guard live that the act never touched:

    ``non-empty after``
        :func:`guard_direction.check_liveness`'s bar, inherited here.  It cannot
        separate *the act woke the guard* from *the fixture was already loud*,
        and the difference is not hypothetical — the enriched fixture copies the
        real ``docs/`` in, so ``unregistered_local_only`` reads
        ``{docs/decisions.md, docs/deliberations.md}`` **before any act runs**.
        Under the old bar it scored ``LIVE``; its reading did not move by a
        single element and never named ``eval/control.txt``.  That false
        positive was the whole measured yield of the derivation.
    ``the reading moved``
        Better, and still wrong in the same direction: any incidental churn in a
        copied surface satisfies it.  Membership is the test for the same reason
        :class:`guard_direction.Direction` gives one layer up — a cardinality
        test cannot say *which* element moved, and here the only element that
        licenses the verdict is the one the act was built to produce.
    """
    repo = workdir / recipe.guard.replace(".", "_")
    try:
        if enriched:
            pr.build_enriched_repo(repo)
        else:
            gd.build_scratch_repo(repo)
        before = pr.read_at(guard, repo)
        recipe.act(repo)
        reading = pr.read_at(guard, repo)
    except Exception as exc:  # noqa: BLE001 - any failure is a failure to wake it
        return Liveness(recipe.guard, LIVENESS_ERROR,
                        note=f"{type(exc).__name__}: {str(exc)[:100]}")
    if reading is None or before is None:
        return Liveness(recipe.guard, LIVENESS_ERROR,
                        note="return value is not a collection of names")
    where = (f"{recipe.scope}/{recipe.membership} act on {recipe.subject}")
    if recipe.subject in reading and recipe.subject not in before:
        return Liveness(recipe.guard, LIVENESS_LIVE, len(reading), len(before))
    if reading:
        return Liveness(recipe.guard, LIVENESS_INERT, len(reading), len(before),
                        note=f"{where} left a reading of {len(reading)} that does "
                             f"not name it (was {len(before)}, "
                             f"{'moved' if reading != before else 'unmoved'})")
    return Liveness(recipe.guard, LIVENESS_DEAD, 0, len(before),
                    note=f"{where} left the reading empty")


def validated(pool: Iterable[gr.Guard] | None = None, *,
              workdir: Path, root: Path | None = None) -> tuple[Liveness, ...]:
    """Every derived recipe, executed."""
    guards = {g.qualname: g for g in pr.root_addressable(pool)}
    return tuple(validate(r, workdir, guards[r.guard])
                 for r in recipes(pool, root) if r.derived)


def unwoken(scored: Iterable[Liveness]) -> tuple[str, ...]:
    """Derived acts that did **not** wake their guard.

    Non-empty is the honest reading of "derivable": the three parts were
    recovered and the act still measured nothing, so the derivation is
    incomplete in a way the census alone cannot show.
    """
    return tuple(sorted(f"{l.guard}: {l.outcome} {l.note}".strip()
                        for l in scored if not l.live))


def agrees_with_typed(root: Path | None = None) -> dict[str, dict[str, str]]:
    """Derived ``(scope, membership)`` next to the two hand-written acts.

    The ground truth for this whole module has **n = 2**, which is the same
    smallness D-053 found in the probe table.  Stating the pair explicitly keeps
    the agreement from reading as a validation over the pool.
    """
    typed = {
        "local_only_audit.staged_declarations": (gr.SCOPE_INDEX, MEMBERSHIP_IN),
        "tree_provenance.undeclared_drift": (gr.SCOPE_WORKTREE, MEMBERSHIP_OUT),
    }
    by_name = {r.guard: r for r in recipes(root=root)}
    out: dict[str, dict[str, str]] = {}
    for name, (scope, membership) in typed.items():
        r = by_name.get(name)
        out[name] = {
            "typed": f"{scope}/{membership}",
            "derived": f"{r.scope}/{r.membership}" if r else "MISSING",
            "agrees": str(bool(r and r.scope == scope and r.membership == membership)),
        }
    return out


def report(pool: Iterable[gr.Guard] | None = None) -> str:  # pragma: no cover - CLI
    import tempfile

    scored = recipes(pool)
    counts = census(scored)
    lines = [f"root-addressable: {len(scored)}"]
    for key, n in counts.items():
        lines.append(f"  {key:14s} {n}")
    for r in scored:
        lines.append(f"    {r.origin:12s} {r.guard:42s} "
                     f"{r.scope}/{r.membership} {r.subject} — {r.note}")
    lines.append(f"typed probes: {len(gd.PROBES)}")
    for name, row in agrees_with_typed().items():
        lines.append(f"  {name}: typed={row['typed']} derived={row['derived']} "
                     f"agrees={row['agrees']}")
    lines.append(f"unranked scopes: {unranked_scopes(pool)}")
    with tempfile.TemporaryDirectory() as td:
        live = validated(pool, workdir=Path(td))
    lines.append(f"executed: {len(live)} live={sum(l.live for l in live)}")
    for name in unwoken(live):
        lines.append(f"  {name}")
    return "\n".join(lines)


def main() -> int:  # pragma: no cover - CLI
    print(report())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
