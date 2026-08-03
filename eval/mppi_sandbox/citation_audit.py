"""Find the citations nobody registered (STATE #1, Q-056 lean (b)).

:mod:`claim_scope` binds five dispatch-fragile claims to the prose that cites
them, and its tests hold that prose to the banked readings.  It has one
structural hole, which is the whole of Q-056: **the citation list is written by
hand**.  A claim is only policed at the sites someone remembered to type in.  A
citation nobody registered is exactly as silent as the drift D-036 found.

This module supplies the missing half — the *discovery* pass.  It scans the
repo's prose for the magnitudes of claims that have an instrument, attributes
each occurrence to the section or module that states it, and reports every site
that is not accounted for in a registry.  It does **not** decide what an
unaccounted site means; per Q-056's lean that stays a human/executor call.  The
tests fail on an *unregistered* site, not on a "wrong" one.

Two things this pass found that hand registration had missed:

1. ``claim_scope`` registers five sections citing ``2.0×``.  There are **six**.
   The sixth is ``D-036`` itself, the section that diagnoses the drift — a
   legitimate mention, but one the registry had no vocabulary for.  Hence
   :attr:`Site.role` ``diagnoses``.
2. The magnitudes are cited in **module docstrings** as well as in ``docs/``:
   ``weight_units`` opens with ``6.19×``, ``scale_match`` with ``2.11×``,
   ``horizon_audit`` with ``6.8×``.  ``claim_scope`` scans only ``docs/``, so
   code prose could drift from the instrument sitting in the same file.

The claims registered here differ in kind from ``claim_scope``'s.  Those five
have **two readings** because two machines disagree about them.  These four have
**one** — no second machine has measured them, and this module does not pretend
otherwise.  What it enforces is weaker and machine-independent: every site
stating a claim's magnitude is registered, and the defining site names an
instrument that could recompute it.  That is enough to make a *new* undeclared
citation go red, which is the failure mode that emitted no signal at all.

Known limit, stated rather than papered over: the scan keys on the ``N.NN×``
spelling.  A magnitude written bare in a table, or spelled to different
precision, is not found.  This bounds the pass to candidate generation — it can
prove a site *is* unregistered, never that none remain.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import claim_scope

REPO_ROOT = claim_scope.REPO_ROOT

#: Files whose prose is scanned.  ``docs/`` carries the decision record;
#: the sandbox modules carry the instruments *and* restate their own headline
#: numbers in module docstrings, which is a citation surface too.
SCANNED_DOCS: tuple[str, ...] = ("docs/decisions.md", "docs/deliberations.md")
SCANNED_MODULES: tuple[str, ...] = (
    "eval/mppi_sandbox/weight_units.py",
    "eval/mppi_sandbox/scale_match.py",
    "eval/mppi_sandbox/horizon_audit.py",
    "eval/mppi_sandbox/claim_scope.py",
    "eval/mppi_sandbox/dispatch_divergence.py",
)

#: Magnitudes are compared as floats; prose spells the same value several ways
#: (``2.0×`` / ``2.00×``).  Tight enough that ``6.19`` and ``6.8`` never merge.
MAGNITUDE_TOLERANCE = 1e-9

#: ``6.19×`` -- a decimal followed by a multiplication sign.  The negative
#: lookbehind keeps ``1.301`` out of ``11.301``; the lookahead keeps ``2.0x``
#: from matching inside an identifier.
_MAGNITUDE = re.compile(r"(?<![\d.])(\d+\.\d+)\s*[×x](?![\w])")


@dataclass(frozen=True)
class Site:
    """One place that states a claim's magnitude."""

    path: str
    #: ``"## D-028"`` for a markdown section; the module path for a docstring.
    anchor: str
    #: ``defines``   -- the section/module that measured it.
    #: ``restates``  -- a later section reusing it; the number must match.
    #: ``diagnoses`` -- prose *about* a drift, which necessarily quotes the
    #:                  wrong number alongside the right one.
    role: str
    #: why this site is allowed to state the number, in one line
    note: str = ""


@dataclass(frozen=True)
class MeasuredClaim:
    """A number with an instrument, and every site known to state it.

    Deliberately weaker than :class:`claim_scope.ScopedClaim`: no second
    reading, because no second machine has measured these.
    """

    claim: str
    magnitude: float
    #: ``module::function`` that could recompute it
    instrument: str
    sites: tuple[Site, ...] = field(default_factory=tuple)

    @property
    def defining(self) -> Site | None:
        for s in self.sites:
            if s.role == "defines":
                return s
        return None


#: Where the ``2.0×`` amplitude was actually measured.  ``claim_scope`` records
#: D-030 as an ``other-quantity`` *citation* of ``horizon_weight_swing``, which
#: is true but incomplete: D-030 is also the section that computed the number
#: (its Decision (4) table, ``w_voo`` 7.00 → 13.97 over ``H`` 15 → 34).  Both
#: facts at once are exactly D-036's conflation, so this module separates them.
_SWING_AMPLITUDE_ORIGIN = "## D-030"


def _sites_from_claim_scope() -> tuple[Site, ...]:
    """Lift ``claim_scope``'s hand-registered ``2.0×`` citations into sites.

    Imported rather than re-typed: two registries stating the same citation
    list independently is one more surface for them to disagree on.

    The origin section becomes ``defines`` and the rest ``restates`` — the
    shape of the drift D-036 found, made structural: one section measured an
    amplitude, four others carried it to a claim it does not measure.
    """
    swing = next(c for c in claim_scope.SCOPED_CLAIMS
                 if c.claim == "horizon_weight_swing")
    return tuple(
        Site(path=cit.doc, anchor=cit.anchor,
             role="defines" if cit.anchor == _SWING_AMPLITUDE_ORIGIN else "restates",
             note=f"claim_scope citation ({cit.kind}): {cit.quantity}")
        for cit in swing.citations
    )


MEASURED_CLAIMS: tuple[MeasuredClaim, ...] = (
    MeasuredClaim(
        claim="w_voo_over_baseline_spread",
        magnitude=6.19,
        instrument="weight_units::measure",
        sites=(
            Site("docs/decisions.md", "## D-027", "defines",
                 "Decision (3) measured w_voo=200 at 6.19x this scene's median "
                 "per-step baseline total-cost spread"),
            Site("docs/decisions.md", "## D-028", "restates",
                 "Context attributes the measurement to D-027; Decision (2) "
                 "reuses it as the numerator of the 6.19-vs-1.46 pair"),
            Site("docs/deliberations.md", "## Q-049", "restates",
                 "the question D-028 answers; quotes it in Question, Lean, and "
                 "the resolution note"),
            Site("eval/mppi_sandbox/weight_units.py", "eval/mppi_sandbox/weight_units.py",
                 "restates", "module docstring opens on the headline number"),
            Site("eval/mppi_sandbox/scale_match.py", "eval/mppi_sandbox/scale_match.py",
                 "restates", "docstring cites it as the motivating disguised-"
                 "temperature result; found by the scan, not by hand"),
        ),
    ),
    MeasuredClaim(
        claim="w_voo_over_own_arm_spread",
        magnitude=1.46,
        instrument="weight_units::measure",
        sites=(
            Site("docs/decisions.md", "## D-028", "defines",
                 "Decision (2) measured the same weight against its own arm -- "
                 "the denominator half of the pair, and D-028's actual result"),
            Site("docs/deliberations.md", "## Q-049", "restates",
                 "resolution note carries the pair forward"),
        ),
    ),
    MeasuredClaim(
        claim="scale_matched_weight_lam_swing",
        magnitude=2.11,
        instrument="scale_match::exchange_rate",
        sites=(
            Site("docs/decisions.md", "## D-029", "defines",
                 "Decision (4): the scale-matched weight inherits the "
                 "denominator's swing over lam 0.1->3.2 (5.43 -> 3.41)"),
            Site("docs/decisions.md", "## D-030", "restates",
                 "Decision (4) compares the horizon amplitude against it as a "
                 "same-order-of-magnitude reference"),
            Site("eval/mppi_sandbox/scale_match.py", "eval/mppi_sandbox/scale_match.py",
                 "restates", "module docstring states it end-to-end"),
            Site("eval/mppi_sandbox/horizon_audit.py", "eval/mppi_sandbox/horizon_audit.py",
                 "restates", "docstring uses it as the same-order reference, "
                 "mirroring D-030's restatement"),
        ),
    ),
    MeasuredClaim(
        claim="horizon_cruise_cliff",
        magnitude=6.8,
        instrument="horizon_audit::cruise_ceiling",
        sites=(
            Site("docs/decisions.md", "## D-030", "defines",
                 "Decision (1): cruise 0.772 at H=34 -> 0.1135 at H=35, one rung"),
            Site("docs/decisions.md", "## D-036", "restates",
                 "Alternatives (d) rests on this cliff standing independently "
                 "of the rescoped claim -- the reason retract was overkill"),
            Site("eval/mppi_sandbox/horizon_audit.py", "eval/mppi_sandbox/horizon_audit.py",
                 "restates", "module docstring states the collapse"),
        ),
    ),
    # The dispatch-fragile claim whose citations claim_scope owns.  Registered
    # here only so the *scan* can confirm that hand list is complete -- and it
    # was not: D-036 is a sixth site.
    MeasuredClaim(
        claim="horizon_weight_swing_cited",
        magnitude=2.0,
        instrument="dispatch_divergence::_horizon_weight_swing",
        sites=_sites_from_claim_scope() + (
            Site("docs/decisions.md", "## D-036", "diagnoses",
                 "the section that found the drift; states the wrong number in "
                 "order to correct it, beside the instrument's 1.3008"),
            Site("eval/mppi_sandbox/claim_scope.py", "eval/mppi_sandbox/claim_scope.py",
                 "diagnoses", "module docstring narrates the same correction"),
            Site("eval/mppi_sandbox/horizon_audit.py", "eval/mppi_sandbox/horizon_audit.py",
                 "restates", "the drift itself, in code: D-036 stamped six "
                 "docs/ sections and missed this one. Repaired in the same "
                 "cycle the scan found it -- now states w(34)/w(30)=1.3008 "
                 "and the oracle beside the 2.0x span"),
        ),
    ),
)


def _md_sections(text: str):
    """``(anchor, body)`` per ``## `` section; anchor is the heading's D/Q id."""
    heads = list(re.finditer(r"^## .*$", text, flags=re.M))
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        anchor = h.group(0).split("—")[0].strip()
        yield anchor, text[h.start():end]


def _module_docstring(text: str) -> str:
    """Module docstring, or ``""`` when absent or unparseable.

    Parsed rather than pattern-matched: every module in the scan surface opens
    with an SPDX comment, so the docstring is not at offset 0, and a regex
    anchored at the top of the file silently returned nothing for all three --
    reporting the registered sites as *stale* instead of as found.  A discovery
    pass that fails open is worse than none, so this uses the real parser.
    """
    try:
        return ast.get_docstring(ast.parse(text)) or ""
    except SyntaxError:
        return ""


def occurrences(magnitude: float, root: Path | None = None) -> list[tuple[str, str, int]]:
    """Every ``(path, anchor, count)`` stating ``magnitude`` in the scan surface."""
    base = root or REPO_ROOT
    out: list[tuple[str, str, int]] = []

    def _count(body: str) -> int:
        return sum(1 for m in _MAGNITUDE.finditer(body)
                   if abs(float(m.group(1)) - magnitude) <= MAGNITUDE_TOLERANCE)

    for doc in SCANNED_DOCS:
        path = base / doc
        if not path.exists():
            continue
        for anchor, body in _md_sections(path.read_text(encoding="utf-8")):
            n = _count(body)
            if n:
                out.append((doc, anchor, n))

    for mod in SCANNED_MODULES:
        path = base / mod
        if not path.exists():
            continue
        n = _count(_module_docstring(path.read_text(encoding="utf-8")))
        if n:
            out.append((mod, mod, n))

    return out


def unregistered(root: Path | None = None) -> list[tuple[str, str, str, int]]:
    """``(claim, path, anchor, count)`` for sites no registry accounts for.

    This is the Q-056 output: candidates for a human to tag, not verdicts.
    """
    out = []
    for mc in MEASURED_CLAIMS:
        known = {(s.path, s.anchor) for s in mc.sites}
        for path, anchor, n in occurrences(mc.magnitude, root):
            if (path, anchor) not in known:
                out.append((mc.claim, path, anchor, n))
    return out


def undefined(root: Path | None = None) -> list[str]:
    """Claims whose registry names no defining site -- an unsourced number."""
    return [mc.claim for mc in MEASURED_CLAIMS if mc.defining is None]


def missing_sites(root: Path | None = None) -> list[tuple[str, str, str]]:
    """Registered ``(claim, path, anchor)`` the scan no longer finds.

    A site that stops stating the number is not automatically wrong -- prose
    gets rewritten -- but it means the registry is describing a repo that no
    longer exists, which is how ``claim_scope``'s stale-anchor failure starts.
    """
    out = []
    for mc in MEASURED_CLAIMS:
        found = {(p, a) for p, a, _ in occurrences(mc.magnitude, root)}
        for s in mc.sites:
            if (s.path, s.anchor) not in found:
                out.append((mc.claim, s.path, s.anchor))
    return out


def report() -> str:
    rows = [f"{'claim':<32} {'mag':>7} {'instrument':<44} {'sites':>5}"]
    for mc in MEASURED_CLAIMS:
        rows.append(f"{mc.claim:<32} {mc.magnitude:>7.4g} {mc.instrument:<44} "
                    f"{len(mc.sites):>5}")
    rows.append("")
    for mc in MEASURED_CLAIMS:
        for path, anchor, n in occurrences(mc.magnitude):
            role = next((s.role for s in mc.sites
                         if (s.path, s.anchor) == (path, anchor)), "UNREGISTERED")
            where = anchor if anchor.startswith("##") else "(module docstring)"
            rows.append(f"  {mc.magnitude:>7.4g}x {role:<13} {path} {where} x{n}")
    unreg, stale = unregistered(), missing_sites()
    rows += ["", f"unregistered sites: {len(unreg)}"
                 + ("" if not unreg else " -> " + ", ".join(
                     f"{c}@{a}" for c, _, a, _ in unreg)),
             f"stale registered sites: {len(stale)}"
             + ("" if not stale else " -> " + ", ".join(
                 f"{c}@{a}" for c, _, a in stale))]
    return "\n".join(rows)


if __name__ == "__main__":
    print(report())
