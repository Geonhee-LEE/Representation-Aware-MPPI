# SPDX-License-Identifier: BSD-3-Clause
"""How many call sites run at the shipped ``lam`` — and why Q-060 could not count them.

D-040 measured that :data:`operating_point.SHIPPED_LAM` = ``0.1`` is admissible
in **0 of 24** calibrated cells while sitting on every cell's ladder.  Q-060
asked what to do about the default and priced its option (c) — *make ``lam`` a
required argument* — as "호출부 전부를 건드린다", touching every call site.  The
stated method for the count was: grep ``make_controller`` / ``MPPIParams()`` for
calls passing no temperature.

**That method is void, and void in a way that returns a number.**
``make_controller`` has no ``lam`` parameter.  Neither does ``StockMPPI``,
``RiskMPPI`` or ``CBFMPPI``.  The temperature reaches a controller only as a
field of the ``params`` object::

    make_controller("risk_mppi", scene, seed=0, params=MPPIParams(lam=1.6))
                                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^

So "call sites of ``make_controller`` passing no ``lam``" is **32 of 32** — 100 %
by construction, not by measurement.  The count is available, it is stable, and
it says nothing.  This is the third consecutive cycle in which a pre-committed
counting plan named the wrong thing to count: D-037's was the *surface*, D-038's
the *unit*, D-040's the *statistic*.  Here it is the **route** — the site that
constructs a controller is not the site that decides its temperature.

What is countable is where a temperature is *decided*, which is a three-way
partition, not the binary Q-060 assumed:

``DECIDES``
    a concrete ``lam`` is chosen here — ``params=MPPIParams(lam=...)``, or a
    ``lam=`` kwarg on a carrier that takes one (:mod:`scale_match`'s
    ``exchange_rate``).
``DEFAULTS``
    no ``params`` reaches the constructor and no ``**kwargs`` could carry one,
    so ``StockMPPI.__init__``'s ``params or MPPIParams()`` fires and the
    controller runs at ``SHIPPED_LAM`` — out of band on every calibrated cell.
``FORWARDS``
    ``params=<opaque>`` or a ``**splat`` — the choice belongs to *this* site's
    caller, so the site itself decides nothing and makes its enclosing function
    a carrier in turn (:func:`carriers` takes the fixpoint).

Over that partition (:func:`census`):

    DECIDES 31   DEFAULTS 54   FORWARDS 19   (104 sites)

D-041 read ``DECIDES 30 … (103)``; the pool grows as the package audits itself
(D-058 added one), so this line is a running tally and
``test_census_counts_are_pinned`` is what keeps it from going stale.  The
*conclusions* below are stated against the partition, not the totals, and none
of them has moved.

Three things follow, and only the first was asked for.

1. **Q-060 (c) costs 54 sites, not the whole census.**  The 19 ``FORWARDS``
   need no edit at all — they already delegate — and the ``DECIDES`` already
   comply.  The option Q-060 leaned away from as invasive is about **half** the
   size it was priced at, and the half that remains is almost entirely test
   code.
2. **The default is not a fallback here, it is the majority.**  ``DEFAULTS``
   outnumbers ``DECIDES``, so the modal temperature in this repo is the one rung
   that no cell admits.  D-040 found the one *registered claim* in that
   position (``exposure_band_hi``); the unregistered population is larger than
   the registered one by an order of magnitude.
3. **Only 2 of the 54 are inert** (:func:`census` counts them): a site that
   constructs a controller and never simulates weights nothing, so ``lam``
   cannot reach a number.  Both are ``raises`` tests.  The inert count is
   reported rather than netted out, because "52 sites actually weight at an
   inadmissible temperature" is the load-bearing number and it should not be
   reachable only by subtraction.

**The resolver's own near-miss is pinned by test.**  The first draft resolved
only ``from ..ab import seed_sweep``-style bare names and missed
``from eval.mppi_sandbox import ab`` + ``ab.seed_sweep(...)``.  Both spellings
are live in this repo, and the miss was silent and fail-open: the census read
**66** sites instead of 103, understating ``DEFAULTS`` by 24.  Same direction as
D-037's regex-vs-``ast`` bug and D-038's ``2.320x``.  A scan that resolves one
import spelling is not a subset of the truth, it is a different question, so
:func:`sites` is asserted to find both.

**Carrier identity is qualified**, ``(module, name)``, for a reason the first
draft also demonstrated: keying on the bare function name made every ``main``,
``__init__`` and ``measure`` in the tree a carrier once any one of them
forwarded, inflating the census to 136 sites — 33 of them in ``eval/run_metrics.py``
and ``eval/tests/``, which construct no controller at all.

Nothing here simulates.  Every number is a read of the repo's own syntax tree,
so this suite is true on every machine — the same property that lets
:mod:`claim_scope` and :mod:`operating_point` police claims that are not.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The only tree scanned.  Complete, not merely conventional: no ``.py`` file
#: outside ``eval/`` names any of :data:`CARRIER_SEEDS`, and a test asserts it
#: rather than leaving the exclusion undeclared (D-038's corollary — an
#: undeclared exclusion is indistinguishable from an oversight).
SCAN_ROOT = "eval"

_CONTROLLERS = "eval.mppi_sandbox.controllers"

#: Qualified ``(module, name)`` of everything that constructs a controller
#: directly.  Qualified because bare names collide: see the module docstring.
CARRIER_SEEDS: frozenset[tuple[str, str]] = frozenset({
    (_CONTROLLERS, "make_controller"),
    (f"{_CONTROLLERS}.stock_mppi", "StockMPPI"),
    (f"{_CONTROLLERS}.risk_mppi", "RiskMPPI"),
    (f"{_CONTROLLERS}.cbf_mppi", "CBFMPPI"),
})

#: The kwarg carrying the temperature object, and the dataclass field inside it.
PARAMS_KWARG = "params"
LAM_FIELD = "lam"

#: Seed names that step a controller.  A function calling one of these
#: simulates; so does a function calling *such* a function, which is why
#: :func:`_simulating` takes a fixpoint rather than matching this set directly.
#: Matching it directly was the first draft's bug and it failed in the
#: dangerous direction: the eight ``test_shadow_cost_seed_robustness`` sites
#: reach ``ab.seed_sweep`` through local helpers (``_sweeps`` / ``_arms_at``)
#: and were scored inert, shrinking the weighting population 44 -> 52 by
#: silence.  A false ``True`` here costs nothing; a false ``False`` deletes
#: evidence for the finding.
_SIMULATING_SEEDS = frozenset({
    "simulate", "command", "run_arm", "seed_sweep", "run_scenario",
    "speed_response", "lam_ladder",
})

DECIDES, DEFAULTS, FORWARDS = "DECIDES", "DEFAULTS", "FORWARDS"
KINDS: tuple[str, ...] = (DECIDES, DEFAULTS, FORWARDS)


@dataclass(frozen=True)
class Site:
    """One call that puts a temperature into a controller, or declines to."""

    path: str          # repo-relative
    line: int
    kind: str          # one of KINDS
    evidence: str      # the source text the classification turned on
    function: str      # enclosing def, or "<module>"
    simulates: bool    # whether the enclosing def ever steps a controller

    @property
    def at_shipped_lam(self) -> bool:
        """Runs at ``MPPIParams().lam`` — the rung no calibrated cell admits."""
        return self.kind == DEFAULTS


def _modname(path: Path) -> str:
    return f"{SCAN_ROOT}." + ".".join(
        path.relative_to(REPO_ROOT / SCAN_ROOT).with_suffix("").parts)


def _absolute(modname: str, node: ast.ImportFrom) -> str:
    """Resolve a possibly-relative ``from`` import against the importing module."""
    if not node.level:
        return node.module or ""
    base = modname.rsplit(".", node.level)[0]
    return f"{base}.{node.module}" if node.module else base


def _import_maps(tree: ast.AST, modname: str) -> tuple[dict, dict]:
    """``(bare name -> (module, attr), module alias -> module)``.

    Two maps because two spellings reach the same function: ``from ab import
    seed_sweep`` binds a bare name, ``from eval.mppi_sandbox import ab`` binds a
    *module* that is then dotted into.  Resolving only the first is the
    fail-open the module docstring describes.
    """
    names: dict[str, tuple[str, str]] = {}
    alias: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = _absolute(modname, node)
            for a in node.names:
                local = a.asname or a.name
                names[local] = (module, a.name)
                alias[local] = f"{module}.{a.name}"   # if a.name is a submodule
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    alias[a.asname] = a.name
                else:
                    alias[a.name.split(".")[0]] = a.name.split(".")[0]
    for node in ast.walk(tree):                        # locally defined wins last
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.setdefault(node.name, (modname, node.name))
    return names, alias


def _target(call: ast.Call, names: dict, alias: dict) -> tuple[str, str] | None:
    func = call.func
    if isinstance(func, ast.Name):
        return names.get(func.id)
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        module = alias.get(func.value.id)
        return (module, func.attr) if module else None
    return None


def _enclosing(tree: ast.AST, node: ast.Call) -> ast.FunctionDef | None:
    best = None
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if fn.lineno <= node.lineno <= (fn.end_lineno or fn.lineno):
                if best is None or fn.lineno > best.lineno:
                    best = fn
    return best


def _classify(call: ast.Call, src: str) -> tuple[str, str]:
    """Three-way, on the syntax alone.  Order matters: an explicit ``lam=``
    beats everything, a ``params=`` object beats a ``**splat``, and only the
    total absence of both routes is a real default."""
    kwargs = {k.arg for k in call.keywords if k.arg}
    splat = any(k.arg is None for k in call.keywords)
    if LAM_FIELD in kwargs:
        return DECIDES, f"{LAM_FIELD}="
    params = next((k.value for k in call.keywords if k.arg == PARAMS_KWARG), None)
    if params is not None:
        text = ast.get_source_segment(src, params) or "?"
        is_literal_params = (isinstance(params, ast.Call)
                             and getattr(params.func, "id", None) == "MPPIParams")
        if not is_literal_params:
            return FORWARDS, text            # a name / `params or MPPIParams()`
        if any(k.arg == LAM_FIELD for k in params.keywords):
            return DECIDES, text
        if any(k.arg is None for k in params.keywords):
            return FORWARDS, text            # MPPIParams(**opaque)
        return DEFAULTS, text                # MPPIParams(horizon=...) -- no lam
    return (FORWARDS, "**splat") if splat else (DEFAULTS, "(no params)")


def _sources(root: Path | None = None) -> dict[Path, tuple[str, ast.AST, str]]:
    base = (root or REPO_ROOT) / SCAN_ROOT
    out = {}
    for path in sorted(base.rglob("*.py")):
        src = path.read_text(encoding="utf-8")
        out[path] = (src, ast.parse(src), _modname(path))
    return out


def _calls(tree: ast.AST, fn: ast.FunctionDef, names: dict, alias: dict,
           modname: str) -> set[tuple[str, str]]:
    """Qualified targets called inside ``fn``, plus bare seed names it uses."""
    out: set[tuple[str, str]] = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        bare = (func.id if isinstance(func, ast.Name)
                else func.attr if isinstance(func, ast.Attribute) else None)
        if bare in _SIMULATING_SEEDS:
            out.add(("<seed>", bare))
        target = _target(node, names, alias)
        if target is not None:
            out.add(target)
    return out


def _simulating(sources: dict) -> set[tuple[str, str]]:
    """Qualified functions that step a controller, transitively.

    Seeded by :data:`_SIMULATING_SEEDS` and closed under "calls a simulating
    function", so a test that reaches ``seed_sweep`` through two local helpers
    is scored the same as one that calls it directly.
    """
    graph: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for _, (src, tree, modname) in sources.items():
        names, alias = _import_maps(tree, modname)
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                graph[(modname, fn.name)] = _calls(tree, fn, names, alias, modname)
    live = {("<seed>", n) for n in _SIMULATING_SEEDS}
    for _ in range(len(graph) + 1):
        grew = False
        for node, callees in graph.items():
            if node not in live and (callees & live):
                live.add(node)
                grew = True
        if not grew:
            break
    return live


def _scan(root: Path | None = None) -> tuple[list[Site], set[tuple[str, str]]]:
    sources = _sources(root)
    live = _simulating(sources)
    carriers = set(CARRIER_SEEDS)
    sites: list[Site] = []
    for _ in range(len(sources) + 1):          # fixpoint; bounded, never a while
        sites, grew = [], False
        for path, (src, tree, modname) in sources.items():
            names, alias = _import_maps(tree, modname)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if _target(node, names, alias) not in carriers:
                    continue
                fn = _enclosing(tree, node)
                kind, evidence = _classify(node, src)
                sites.append(Site(
                    path=str(path.relative_to(root or REPO_ROOT)),
                    line=node.lineno,
                    kind=kind,
                    evidence=evidence,
                    function=fn.name if fn else "<module>",
                    simulates=(modname, fn.name) in live if fn else True,
                ))
                if kind == FORWARDS and fn is not None:
                    if (modname, fn.name) not in carriers:
                        carriers.add((modname, fn.name))
                        grew = True
        if not grew:
            break
    return sites, carriers


def sites(root: Path | None = None) -> tuple[Site, ...]:
    """Every temperature-decision site in the scan root, classified."""
    return tuple(_scan(root)[0])


def carriers(root: Path | None = None) -> frozenset[tuple[str, str]]:
    """The fixpoint: seeds plus every function that forwards into one."""
    return frozenset(_scan(root)[1])


@dataclass(frozen=True)
class Census:
    decides: int
    defaults: int
    forwards: int
    inert_defaults: int          # DEFAULTS sites that never step a controller

    @property
    def total(self) -> int:
        return self.decides + self.defaults + self.forwards

    @property
    def weighting_at_shipped(self) -> int:
        """DEFAULTS that actually run — the load-bearing number, not a residual."""
        return self.defaults - self.inert_defaults

    @property
    def migration_cost(self) -> int:
        """Sites Q-060 (c) would have to edit to make ``lam`` required.

        ``FORWARDS`` sites delegate and ``DECIDES`` sites already comply, so the
        cost is exactly the defaults — the number Q-060 priced as *all* of them.
        """
        return self.defaults


def census(root: Path | None = None) -> Census:
    found = sites(root)
    return Census(
        decides=sum(1 for s in found if s.kind == DECIDES),
        defaults=sum(1 for s in found if s.kind == DEFAULTS),
        forwards=sum(1 for s in found if s.kind == FORWARDS),
        inert_defaults=sum(1 for s in found
                           if s.kind == DEFAULTS and not s.simulates),
    )


def report(root: Path | None = None) -> str:
    from .operating_point import SHIPPED_LAM

    c = census(root)
    rows = [
        f"temperature-decision sites under {SCAN_ROOT}/ : {c.total}",
        f"  DECIDES  {c.decides:>3d}   an explicit lam reaches the controller",
        f"  DEFAULTS {c.defaults:>3d}   runs at MPPIParams().lam = {SHIPPED_LAM:g}",
        f"  FORWARDS {c.forwards:>3d}   defers to the caller; decides nothing",
        "",
        f"of the {c.defaults} defaults, {c.inert_defaults} never step a "
        f"controller (temperature inert)",
        f"=> {c.weighting_at_shipped} sites weight at a rung no calibrated cell admits",
        "",
        f"Q-060 (c) migration cost: {c.migration_cost} sites "
        f"(not {c.total} -- forwards and decides need no edit)",
        "",
        f"{'kind':<9} {'site':<52} {'evidence'}",
    ]
    for s in sorted(sites(root), key=lambda s: (s.kind, s.path, s.line)):
        rows.append(f"{s.kind:<9} {s.path + ':' + str(s.line):<52} {s.evidence[:40]}")
    return "\n".join(rows)


if __name__ == "__main__":
    print(report())
