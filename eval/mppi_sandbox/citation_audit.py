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

1. ``claim_scope`` registers five sections citing ``2.0×``.  The scan finds
   **eight**: those five, ``D-036`` (the section that diagnoses the drift — a
   legitimate mention the registry had no vocabulary for, hence
   :attr:`Site.role` ``diagnoses``), and two module docstrings.
2. The magnitudes are cited in **module docstrings** as well as in ``docs/``:
   ``weight_units`` opens with ``6.19×``, ``scale_match`` with ``2.11×``,
   ``horizon_audit`` with ``6.8×``.  ``claim_scope`` scans only ``docs/``, so
   code prose could drift from the instrument sitting in the same file — and
   one had: ``horizon_audit``'s docstring carried the exact pairing D-036
   corrected in six ``docs/`` sections and stopped short of.

The claims registered here differ in kind from ``claim_scope``'s.  Those five
have **two readings** because two machines disagree about them.  These have
**one** — no second machine has measured them, and this module does not pretend
otherwise.  What it enforces is weaker and machine-independent: every site
stating a claim's magnitude is registered, and the defining site names an
instrument that could recompute it.  That is enough to make a *new* undeclared
citation go red, which is the failure mode that emitted no signal at all.

This file is itself in :data:`SCANNED_MODULES`.  A module that polices where
numbers are restated, while exempting the place it restates them, would be
reproducing the defect it was written for.

The ``N.NN×`` spelling was D-037's stated limit: a magnitude written bare in a
table is not found.  D-038 lifts it, and the lift is where the interesting part
is — see :data:`_BARE`, :data:`SIGNALS` and :func:`rank_unregistered`.  Three
things came out of widening that the plan for it did not predict:

1. **A widened pattern is not automatically a superset of the narrow one.**
   The obvious bare pattern ends ``(?![\\w.])`` to keep ``1.301`` out of
   ``11.301`` — and ASCII ``x`` is a word character, so it rejects ``2.320x``,
   a site the *narrow* pattern finds (``exposure``'s docstring spells the sign
   in ASCII).  Widening the spelling silently dropped a citation.  The
   multiplication sign has to be *consumed* as an optional suffix, not treated
   as a trailing disqualifier, and a test now asserts the superset relation
   over the real scan surface rather than over an example.
2. **The flood Q-057 was scoped around did not arrive.**  Across six claims
   the widening adds **5** distinct sites, not hundreds — the raw occurrence
   count looks far worse (2.0 goes 10 → 40) only because one section restates
   a number many times, and a *site* is what the registry tags.
3. **All 5 are false positives, and none of them is subtle.**  Every one
   carries a local token saying it is a different quantity: ``≥ 2.0 s`` (a
   duration), ``w_speed = 2.0`` (a weight literal), ``1.46 / K=256`` (a
   denominator), ``2.00 및 4.66`` (a ratio rung, spelled to a precision the
   claim never uses).  So the ranking that Q-057 wanted *before* widening is
   cheap to build and — for this repo — the honest verdict is that widening
   found **no** citation the ``×`` spelling was missing.  That is a negative
   result about the repo, not about the method: it is only knowable because
   the scan ran.

Consequently the widened pass is **advisory, not enforcing**.
:func:`unregistered` — the function whose emptiness the suite requires — still
reads the marked spelling only.  :func:`rank_unregistered` reports bare hits as
a ranked candidate list.  Promoting it to a gate would make the suite fail on
the sentence "``w_speed = 2.0``", which is not citation drift.

Surfaces deliberately *outside* the scan are declared in
:data:`EXCLUDED_SURFACES` with the reason, because D-037's finding was that a
registry fails by never looking at a surface.  An undeclared exclusion is
indistinguishable from an oversight; a declared one is a decision.

D-045 closes the loop that sentence leaves open.  Both file lists — the scanned
one and the excluded one — were *hand-maintained*, so the registry that polices
where numbers are restated was itself unpoliced at whichever file nobody
thought of.  Two changes:

1. :func:`scanned_modules` **globs** the package instead of naming its members,
   so a new module is in the surface the moment it exists.  This is Q-056's
   stated mechanism; D-044 met the same hole and dodged it by not spelling the
   magnitude, which works once and is not a mechanism.
2. :func:`unaccounted_surfaces` enumerates ``git ls-files`` and requires every
   tracked file stating a registered magnitude to be *either* scanned *or*
   excluded-with-a-reason.  Nothing above it could ask this question: every
   check took the file list as given.

The second is where the finding was.  Four surfaces were neither scanned nor
declared, and the shape of the miss repeats D-044's exactly — the exclusion
list named **two** of D-011's **three** snapshot files, one cycle after D-011's
own local-only list was found naming three of five:

- ``JOURNAL.md`` (26 hits), the omitted third;
- ``results/*.tsv`` (10), named in ``RESULTS.md``'s own exclusion *reason*
  while absent from the list the reason belongs to;
- ``research/`` (2), written by a script, rotated rather than corrected;
- ``eval/requirements-ci.txt`` (1) — **not** an exclusion.  The CI pin's
  rationale comment cites D-030's ``2.0x`` swing against numpy 1.26.4 as the
  justification for pinning, which is a live restatement of a dispatch-fragile
  claim sitting in the file that decides what CI runs.  Registered, and now
  scanned via :data:`SCANNED_TEXT`.

That last one is the argument for the whole pass: it is a genuine citation, it
is not prose, and no amount of re-reading a list of docs would have produced
it.  The other three are excluded — but they are excluded *now on the record*,
which is the difference between a decision and an oversight.
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

#: The package whose module docstrings are scanned.  Enumerated by
#: :func:`scanned_modules` rather than typed out — see D-045.
SCANNED_PACKAGE = "eval/mppi_sandbox"

#: Live prose that is neither markdown nor a module docstring.  Whole-file,
#: anchored by path, because these have no section structure to attribute to.
#: ``requirements-ci.txt`` is here because its pin rationale *cites a claim*:
#: the comment block justifying the numpy pin restates D-030's ``2.0x`` swing,
#: which is the dispatch-fragile magnitude ``claim_scope`` exists to police.
#: Nobody would think to scan a requirements file, which is the point — it was
#: found by enumerating the surface, not by remembering it.
SCANNED_TEXT: tuple[str, ...] = ("eval/requirements-ci.txt",)


def scanned_modules(root: Path | None = None) -> tuple[str, ...]:
    """Every module in :data:`SCANNED_PACKAGE`, discovered rather than declared.

    This replaces a hand-written tuple, and the replacement is the whole of
    D-045's first half.  The tuple was Q-056's hole one level up: the registry
    polices where numbers are restated, so a registry that reads a
    *hand-maintained* file list is unpoliced exactly at the files nobody
    remembered to add.  D-044 demonstrated this with a freshly created module
    (``tree_provenance``) and resolved it by *not spelling* the magnitude —
    cheap once, and not a mechanism.

    A glob is a mechanism: a new module is in the surface the moment it exists,
    including one written by an executor who never read this file.
    """
    base = root or REPO_ROOT
    pkg = base / SCANNED_PACKAGE
    return tuple(sorted(
        f"{SCANNED_PACKAGE}/{p.name}" for p in pkg.glob("*.py")
    ))

#: Magnitudes are compared as floats; prose spells the same value several ways
#: (``2.0×`` / ``2.00×``).  Tight enough that ``6.19`` and ``6.8`` never merge.
MAGNITUDE_TOLERANCE = 1e-9

#: ``6.19×`` -- a decimal followed by a multiplication sign.  The negative
#: lookbehind keeps ``1.301`` out of ``11.301``; the lookahead keeps ``2.0x``
#: from matching inside an identifier.
_MAGNITUDE = re.compile(r"(?<![\d.])(\d+\.\d+)\s*[×x](?![\w])")

#: The same decimal with the multiplication sign made **optional** — every
#: statement of a magnitude, marked or bare.  A strict superset of
#: :data:`_MAGNITUDE` by construction, and asserted so over the real files.
#:
#: The sign is *consumed* rather than excluded, which is the whole subtlety:
#: ASCII ``x`` is a ``\w``, so the natural bare pattern ``(\d+\.\d+)(?![\w.])``
#: rejects ``2.320x`` — a site the narrow pattern matches.  ``(?!\.\d)`` keeps
#: version-shaped ``2.0.1`` out while still allowing a sentence to end ``2.0.``
_BARE = re.compile(r"(?<![\d.])(\d+\.\d+)(?!\.\d)\s*([×x])?(?![\w])")

#: Half-width of the prose window the ranking signals read around a hit.
CONTEXT_WIDTH = 48

#: Paths that state these magnitudes and are **not** scanned, each with the
#: reason.  Declared because D-037's finding was that a registry fails by
#: never looking at a surface — an exclusion nobody wrote down is
#: indistinguishable from having missed it.
EXCLUDED_SURFACES: tuple[tuple[str, str], ...] = (
    ("journal/", "dated per-cycle records. A journal entry correctly states "
                 "what was believed on its date; policing it would require "
                 "rewriting history to keep a present-tense claim true."),
    ("RESULTS.md", "generated from results/*.tsv by aggregate_results.sh, and "
                   "the TSV rows are append-only — neither is editable in "
                   "response to a drift finding."),
    ("STATE.md", "rewritten wholesale every cycle; it is a snapshot, not a "
                 "record, so a stale citation in it survives at most one hour."),
    # The three below were *unaccounted*, not excluded: neither scanned nor
    # declared, which is the state D-037 called indistinguishable from an
    # oversight -- because it is one.  Found by enumerating the surface
    # (:func:`unaccounted_surfaces`), not by re-reading this tuple.  Note the
    # shape: the list named two of D-011's three snapshot files and omitted the
    # third, one cycle after D-044 found D-011's own local-only list naming
    # three of five.  Two hand-maintained lists, two undercounts, same week.
    ("JOURNAL.md", "append-at-top digest of dated per-cycle entries -- the "
                   "same class as journal/, and excluded for the same reason: "
                   "an entry correctly states what was believed on its date. "
                   "It is also D-011 local-only, so a drift finding could not "
                   "be committed in response even if one were wanted."),
    ("results/", "append-only TSV rows (a soft limit: 'Never edit past "
                 "rows'). RESULTS.md's exclusion above already names these as "
                 "its source and gives the reason -- the reason was written "
                 "down while the surface it applies to was not."),
    ("research/", "written by scripts/researcher.sh, capped at 30 entries, "
                  "full-overwrite; D-044 registered it as local-only for the "
                  "same reason. Feed entries quote magnitudes from the papers "
                  "and from our own record while summarising them, and are "
                  "rotated out rather than corrected."),
    ("eval/mppi_sandbox/tests/", "test modules state magnitudes inside "
                                 "assertion failure messages, where the number "
                                 "is the *trigger* for re-deriving a claim "
                                 "rather than a restatement of it. A drifted "
                                 "number here fails its own test, which is the "
                                 "signal this registry exists to synthesise "
                                 "for prose -- so scanning them would duplicate "
                                 "a guard that already fires."),
)


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
        # ``other-quantity`` only.  This lift is about the ``2.0x`` *amplitude*,
        # and until D-046 every citation on this claim happened to be of that
        # kind -- the D-036 finding itself -- so "all of them" and "the ones
        # stating 2.0x" were the same tuple and the filter was invisible.
        # D-046's derived scan then registered eleven ``instrument`` citations,
        # which state 1.3008 / 1.029 and no amplitude at all; lifting those
        # here registered six sections as restating a magnitude they never
        # write, and two tests went red naming them.  The coincidence was load
        # bearing, which is the same shape as the defects D-044/D-045 found in
        # the lists they enumerated.
        for cit in swing.citations if cit.kind == "other-quantity"
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
            Site("eval/mppi_sandbox/barrier_ceiling.py",
                 "eval/mppi_sandbox/barrier_ceiling.py", "restates",
                 "D-125 cites it as the reason a barrier-weight sweep needs an "
                 "ESS filter: Q-049 asked whether the hazard was repo-wide and "
                 "this is the first sweep walking a weight far enough to say"),
            Site("docs/deliberations.md", "## Q-151", "restates",
                 "the 6.19x collapse is quoted as the *upper* bound of an "
                 "audibility window whose lower bound D-264 measured; the "
                 "trade-off's option (b) and the Lean each state it once"),
            Site("docs/decisions.md", "## D-037", "diagnoses",
                 "this cycle's audit; states the magnitude in order to report where it travels"),
            Site("docs/decisions.md", "## D-038", "diagnoses",
                 "Findings quote the two prose fragments that mis-fired the "
                 "ranking -- the colon-introduced result and the "
                 "slash-separated citation pair"),
            Site("eval/mppi_sandbox/citation_audit.py",
                 "eval/mppi_sandbox/citation_audit.py", "diagnoses",
                 "this module's own docstring, under its own scan"),
            Site("eval/mppi_sandbox/denominator_scope.py",
                 "eval/mppi_sandbox/denominator_scope.py", "restates",
                 "opening paragraph quotes the pair as the lam=1.6 reading "
                 "this module re-measures at the shipped temperature"),
            Site("docs/decisions.md", "## D-039", "restates",
                 "Context restates the pair in order to scope it to lam=1.6"),
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
            Site("docs/decisions.md", "## D-037", "diagnoses",
                 "this cycle's audit; states the magnitude in order to report where it travels"),
            Site("docs/decisions.md", "## D-038", "diagnoses",
                 "Findings quote the two prose fragments that mis-fired the "
                 "ranking -- the colon-introduced result and the "
                 "slash-separated citation pair"),
            Site("eval/mppi_sandbox/denominator_scope.py",
                 "eval/mppi_sandbox/denominator_scope.py", "restates",
                 "opening paragraph quotes the pair; section 1 reports where "
                 "this half of it goes at the shipped lam"),
            Site("docs/decisions.md", "## D-039", "restates",
                 "Context restates the pair in order to scope it to lam=1.6"),
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
            Site("docs/decisions.md", "## D-037", "diagnoses",
                 "this cycle's audit; states the magnitude in order to report where it travels"),
            Site("eval/mppi_sandbox/citation_audit.py",
                 "eval/mppi_sandbox/citation_audit.py", "diagnoses",
                 "this module's own docstring, under its own scan"),
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
            Site("docs/decisions.md", "## D-037", "diagnoses",
                 "this cycle's audit; states the magnitude in order to report where it travels"),
            Site("eval/mppi_sandbox/citation_audit.py",
                 "eval/mppi_sandbox/citation_audit.py", "diagnoses",
                 "this module's own docstring, under its own scan"),
        ),
    ),
    # Registered because the scan found it *clean* -- D-025 is the only docs/
    # section stating it.  STATE #1 named it a drift suspect and it is not one;
    # keeping it here is what makes that negative hold going forward rather
    # than being re-established by hand every time someone wonders.
    MeasuredClaim(
        claim="exposure_band_width_cruise",
        magnitude=2.320,
        instrument="exposure::exposure_band",
        sites=(
            Site("docs/decisions.md", "## D-025", "defines",
                 "Decision (2)/(3): band width under the calibrated cruise "
                 "driver, and the scene-independent lower bound"),
            Site("eval/mppi_sandbox/exposure.py", "eval/mppi_sandbox/exposure.py",
                 "restates", "module docstring states the narrowing"),
            Site("docs/decisions.md", "## D-037", "diagnoses",
                 "recorded as the honest negative of this cycle's audit"),
            Site("eval/mppi_sandbox/citation_audit.py",
                 "eval/mppi_sandbox/citation_audit.py", "diagnoses",
                 "D-038: this module's docstring quotes exposure's ASCII "
                 "'2.320x' as the example of the spelling the naive widened "
                 "pattern dropped. Caught live by the enforcing pass on the "
                 "cycle that wrote it -- the same self-scan property D-037 "
                 "added, firing on its own author for the second time"),
            Site("docs/decisions.md", "## D-038", "diagnoses",
                 "Findings (1) quotes exposure's ASCII '2.320x' as the site "
                 "the naive widened pattern lost"),
            Site("eval/mppi_sandbox/default_lam_sites.py",
                 "eval/mppi_sandbox/default_lam_sites.py", "diagnoses",
                 "D-041: cites the same '2.320x' as the precedent for its own "
                 "fail-open near-miss (a resolver that reads one import "
                 "spelling). Caught live by the enforcing pass on the cycle "
                 "that wrote it -- third consecutive self-catch"),
            Site("docs/deliberations.md", "## Q-057", "diagnoses",
                 "the resolution note carries the same example forward"),
            Site("docs/decisions.md", "## D-041", "diagnoses",
                 "Decision (5)(i) cites the same '2.320x' as the fail-open "
                 "precedent. Registered one cycle late, and the lateness is "
                 "the finding: D-041's journal recorded the guard green at "
                 "367 passed, then prepended this section and pushed. The "
                 "number was true of a tree that no longer existed at push "
                 "time -- see D-042"),
            Site("docs/decisions.md", "## D-043", "diagnoses",
                 "the section that *states* the write-ordering defect restates "
                 "the same magnitude while narrating it, and so reproduced the "
                 "defect one paragraph after describing it. Caught by D-043's "
                 "own new rule -- re-run the guard after the doc writes -- on "
                 "the first cycle that rule existed"),
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
            Site("docs/decisions.md", "## D-037", "diagnoses",
                 "this cycle's audit; states the magnitude in order to report where it travels"),
            Site("eval/mppi_sandbox/citation_audit.py",
                 "eval/mppi_sandbox/citation_audit.py", "diagnoses",
                 "this module's own docstring, under its own scan"),
            Site("eval/requirements-ci.txt", "eval/requirements-ci.txt", "restates",
                 "D-045: the CI pin's rationale comment states the swing as "
                 "'2.0x under 1.26.4' vs '1.029x under 2.5.1' -- the sharpest "
                 "statement of the numpy-dependence anywhere in the repo, and "
                 "the only citation of a dispatch-fragile claim living outside "
                 "docs/ and the sandbox package. Unregistered because no "
                 "registry looked at requirements files; found by enumerating "
                 "the tracked tree, not by widening a guess. 'restates' and "
                 "not 'diagnoses': it carries D-030's number forward as the "
                 "pin's justification, so if D-030 is ever rescoped the way "
                 "D-039 rescoped D-028, this is the site that silently keeps "
                 "the old reading -- attached to the file that decides what "
                 "CI runs"),
            Site("docs/decisions.md", "## D-046", "diagnoses",
                 "D-046: names the 2.0x amplitude while explaining that lifting "
                 "instrument-kind citations into its site list registered six "
                 "sections as restating a magnitude they never write"),
            Site("docs/decisions.md", "## D-045", "diagnoses",
                 "the section that adds requirements-ci.txt to the surface "
                 "quotes the citation it found in order to report it, and so "
                 "created a new site while describing one. Caught live by the "
                 "enforcing pass on the cycle that wrote it -- ninth "
                 "consecutive self-catch, and the first where the *reason* the "
                 "site existed was a widening of the scan surface rather than "
                 "a narration of someone else's drift"),
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

    for mod in scanned_modules(base):
        path = base / mod
        if not path.exists():
            continue
        n = _count(_module_docstring(path.read_text(encoding="utf-8")))
        if n:
            out.append((mod, mod, n))

    for txt in SCANNED_TEXT:
        path = base / txt
        if not path.exists():
            continue
        n = _count(path.read_text(encoding="utf-8"))
        if n:
            out.append((txt, txt, n))

    return out


# --------------------------------------------------------------------------
# D-038: the widened (bare-magnitude) pass, and the ranking Q-057 asked for
# before widening.  Advisory only -- see the module docstring.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Occurrence:
    """One statement of a magnitude, marked or bare, with its prose window."""

    path: str
    anchor: str
    #: as written -- ``2.0`` vs ``2.00`` is a signal, so the string is kept
    spelling: str
    #: whether a ``×``/``x`` follows; ``True`` ⇒ :data:`_MAGNITUDE` finds it too
    marked: bool
    before: str
    after: str

    @property
    def quote(self) -> str:
        return f"{self.before}[{self.spelling}]{self.after}".replace("\n", " ")


@dataclass(frozen=True)
class Signal:
    """A named, weighted piece of evidence about one occurrence.

    Weights are declared here rather than fitted.  The point is not calibrated
    probability — with 5 negatives and 34 positives in the whole repo there is
    nothing to fit — but an *ordering* whose reason is readable at each hit.
    """

    name: str
    weight: float
    why: str


#: Positive weight = looks like a citation of the claim.  Negative = looks like
#: a different quantity that happens to share the value.
SIGNALS: tuple[Signal, ...] = (
    Signal("multiplication_sign", +3.0,
           "written as a multiple (N.NN×) -- the spelling a ratio claim uses"),
    Signal("instrument_keyword", +1.0,
           "the claim's instrument or subject named in the same window"),
    Signal("unit_suffix", -3.0,
           "followed by a unit (s, m, %, ...) -- a dimensioned quantity, and "
           "these claims are all dimensionless ratios"),
    Signal("assignment", -3.0,
           "preceded by = or : -- a parameter literal, not a result"),
    Signal("denominator", -2.0,
           "followed by / or by 'of N' -- the numerator of some other ratio, "
           "or a count stated out of a population"),
    Signal("comparator", -1.0,
           "preceded by >=, <=, > or < -- a threshold being stated"),
    Signal("precision_mismatch", -1.0,
           "spelled to a precision the defining site never uses; a citation "
           "normally copies the number as published"),
)

_UNIT_AFTER = re.compile(r"^\s*(s\b|ms\b|m\b|m/s|%|초\b|배\b|Hz\b|z\b)")
#: ``=`` only, deliberately **not** ``:``.  The first draft accepted both and
#: fired on ``결과: **6.19×**`` — a colon followed by markdown emphasis is how
#: half this repo's prose introduces a result, so ``assignment`` was cancelling
#: ``multiplication_sign`` on four *genuine* citations and dropping them to 0.
#: A signal that fires on the positives is worse than no signal.
_ASSIGN_BEFORE = re.compile(r"=\s*[`*\"']*\s*$")
_COMPARATOR_BEFORE = re.compile(r"(>=|<=|[><≥≤])\s*[`*]*\s*$")
#: ``/`` **or** the prose spelling of the same relation.  D-045: widening the
#: scan surface pulled in ``speed_audit``'s docstring, which states D-024's
#: median-ESS fact as "1.46 of K = 256" where D-024 writes "1.46 / K=256".
#: Identical quantity, and the slash spelling was already a registered
#: ``denominator`` rejection — so the prose spelling scoring 0.0 with *no*
#: signal was the ranking getting the right answer for no reason, which is the
#: exact thing ``test_rejections_split_into_by_evidence_and_by_default``
#: exists to catch.  It caught it.  The alternative was to raise that test's
#: silent-bucket threshold, i.e. to weaken the check that found the gap.
#:
#: The leading ``[`*"']*`` is not cosmetic, and it was not predicted: D-045's
#: own prose writes the same ESS fact as ``**1.46** of K = 256`` — emphasis
#: closing *between* the number and the relation — where ``speed_audit`` writes
#: ``**1.46 of K = 256**`` with the bold spanning both.  The signal added
#: earlier in this very cycle could read the second and not the first, so the
#: re-run mandated by D-043 went red on the section describing the fix.  Same
#: tolerance ``_ASSIGN_BEFORE`` already carries, for the same reason: markdown
#: decoration is not evidence about what a number means.
_DENOM_AFTER = re.compile(r"^[`*\"']*\s*(/|of\s+[A-Za-z_]*\s*=?\s*\d)")

#: Score at or above which a bare hit is worth a human look.  Set so that the
#: marked spelling (+3) always clears it and an unmarked hit needs corroborating
#: keyword evidence *and* no disqualifier.
CANDIDATE_THRESHOLD = 1.0


def _iter_bodies(base: Path):
    """``(path, anchor, body)`` over the whole scan surface."""
    for doc in SCANNED_DOCS:
        path = base / doc
        if path.exists():
            for anchor, body in _md_sections(path.read_text(encoding="utf-8")):
                yield doc, anchor, body
    for mod in scanned_modules(base):
        path = base / mod
        if path.exists():
            yield mod, mod, _module_docstring(path.read_text(encoding="utf-8"))
    for txt in SCANNED_TEXT:
        path = base / txt
        if path.exists():
            yield txt, txt, path.read_text(encoding="utf-8")


def all_occurrences(magnitude: float, root: Path | None = None) -> list[Occurrence]:
    """Every statement of ``magnitude`` in the scan surface, marked or bare."""
    base = root or REPO_ROOT
    out: list[Occurrence] = []
    for path, anchor, body in _iter_bodies(base):
        for m in _BARE.finditer(body):
            if abs(float(m.group(1)) - magnitude) > MAGNITUDE_TOLERANCE:
                continue
            out.append(Occurrence(
                path=path, anchor=anchor, spelling=m.group(1),
                marked=m.group(2) is not None,
                before=body[max(0, m.start() - CONTEXT_WIDTH):m.start()],
                after=body[m.end():m.end() + CONTEXT_WIDTH]))
    return out


def canonical_spelling(mc: MeasuredClaim, root: Path | None = None) -> str | None:
    """How the defining site writes the number, or ``None`` if it does not.

    Derived from the prose rather than registered by hand: one more hand-typed
    field is one more thing that can disagree with the repo.
    """
    defining = mc.defining
    if defining is None:
        return None
    for occ in all_occurrences(mc.magnitude, root):
        if (occ.path, occ.anchor) == (defining.path, defining.anchor):
            return occ.spelling
    return None


def signals_for(occ: Occurrence, mc: MeasuredClaim,
                canonical: str | None = None) -> list[Signal]:
    """Which of :data:`SIGNALS` fire on this occurrence."""
    by_name = {s.name: s for s in SIGNALS}
    fired: list[Signal] = []
    if occ.marked:
        fired.append(by_name["multiplication_sign"])
    subject = mc.instrument.split("::")[0]
    if subject and subject in (occ.before + occ.after):
        fired.append(by_name["instrument_keyword"])
    # The disqualifiers all say "this is a different quantity that happens to
    # share the value", which is a statement about a *bare* number.  An
    # explicit × already says the number is a multiple, so they do not apply --
    # and firing them anyway is not hypothetical: ``6.19×/1.46×`` is a
    # slash-separated pair of citations, and reading its ``/`` as a ratio bar
    # scored a registered site as a false positive.
    if not occ.marked:
        if _UNIT_AFTER.match(occ.after):
            fired.append(by_name["unit_suffix"])
        if _ASSIGN_BEFORE.search(occ.before):
            fired.append(by_name["assignment"])
        if _DENOM_AFTER.match(occ.after):
            fired.append(by_name["denominator"])
        if _COMPARATOR_BEFORE.search(occ.before):
            fired.append(by_name["comparator"])
    if canonical is not None and occ.spelling != canonical:
        fired.append(by_name["precision_mismatch"])
    return fired


def rank_unregistered(root: Path | None = None) -> list[tuple[float, str, Occurrence, list[Signal]]]:
    """``(score, claim, occurrence, signals)`` for unregistered hits, best first.

    Advisory output.  A non-empty list is **not** a failure — see the module
    docstring; the enforcing check remains :func:`unregistered`, which reads
    the marked spelling only.
    """
    out = []
    for mc in MEASURED_CLAIMS:
        known = {(s.path, s.anchor) for s in mc.sites}
        canonical = canonical_spelling(mc, root)
        for occ in all_occurrences(mc.magnitude, root):
            if (occ.path, occ.anchor) in known:
                continue
            fired = signals_for(occ, mc, canonical)
            out.append((sum(s.weight for s in fired), mc.claim, occ, fired))
    return sorted(out, key=lambda r: -r[0])


def candidates(root: Path | None = None):
    """Unregistered hits scoring at or above :data:`CANDIDATE_THRESHOLD`."""
    return [r for r in rank_unregistered(root) if r[0] >= CANDIDATE_THRESHOLD]


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


# --------------------------------------------------------------------------
# D-045: the surface-completeness pass.  Everything above answers "is this
# site registered?"; nothing above answered "is this *file* even looked at?"
# --------------------------------------------------------------------------

class SurfaceEnumerationError(RuntimeError):
    """Raised when the tracked-file list cannot be obtained.

    Deliberately not a soft ``return []``.  This function's output is consumed
    by a test that passes when the list is empty, so an environment failure
    would read as "every surface is accounted for" — D-042's rule that an
    instrument which can only clear work must not be trusted to clear work.
    """


def tracked_files(root: Path | None = None) -> tuple[str, ...]:
    """Every git-tracked path, as the surface of files that could state a claim.

    Tracked-ness is the right filter and not merely a convenience: an untracked
    file cannot reach the pushed tree, so a citation in one is not part of the
    record.  This mirrors ``tree_provenance``'s split by destination.
    """
    import subprocess

    base = root or REPO_ROOT
    try:
        proc = subprocess.run(
            ["git", "-C", str(base), "ls-files", "-z"],
            capture_output=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover
        raise SurfaceEnumerationError(
            f"cannot enumerate tracked files under {base}: {exc}") from exc
    return tuple(sorted(
        p.decode("utf-8") for p in proc.stdout.split(b"\0") if p
    ))


def _accounted(path: str) -> str | None:
    """Which declaration covers ``path``, or ``None`` if nothing does."""
    if path in SCANNED_DOCS or path in SCANNED_TEXT:
        return "scanned"
    if path.startswith(f"{SCANNED_PACKAGE}/") and path.endswith(".py") \
            and "/" not in path[len(SCANNED_PACKAGE) + 1:]:
        return "scanned"
    for surface, _reason in EXCLUDED_SURFACES:
        if path == surface or (surface.endswith("/") and path.startswith(surface)):
            return "excluded"
    return None


def unaccounted_surfaces(root: Path | None = None) -> list[tuple[str, int]]:
    """``(path, hits)`` for tracked files that state a registered magnitude
    while being neither scanned nor declared-excluded.

    This is the invariant the hand-written file lists could not state.  D-037
    established that a registry fails by never *looking* at a surface, and
    declared its exclusions for that reason — but a declared-exclusion list is
    itself hand-maintained, so it fails the same way one level up, silently,
    at whichever surface nobody thought of.  Enumerating from `git ls-files`
    closes the loop: a file is scanned, or excluded with a reason, or this is
    non-empty and the suite is red.

    What it found on its first run, none of it by argument:
    ``JOURNAL.md`` (26 hits — the exclusion list named two of D-011's three
    snapshot files), ``results/*.tsv`` (10 — named in RESULTS.md's own
    exclusion *reason* but not in the list), ``research/feed.md`` (2), and
    ``eval/requirements-ci.txt`` (1), which is the one that mattered: a live,
    hand-edited citation of D-030's dispatch-fragile ``2.0x`` sitting in a
    requirements file, a surface no prose-registry would have thought to name.
    """
    base = root or REPO_ROOT
    mags = sorted({mc.magnitude for mc in MEASURED_CLAIMS})
    out: list[tuple[str, int]] = []
    for rel in tracked_files(base):
        if _accounted(rel) is not None:
            continue
        path = base / rel
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        n = sum(1 for m in _MAGNITUDE.finditer(body)
                if any(abs(float(m.group(1)) - g) <= MAGNITUDE_TOLERANCE
                       for g in mags))
        if n:
            out.append((rel, n))
    return sorted(out, key=lambda r: -r[1])


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

    ranked = rank_unregistered()
    rows += ["", f"-- widened (bare) pass: {len(ranked)} unregistered hit(s), "
                 f"{len(candidates())} at/above threshold {CANDIDATE_THRESHOLD} "
                 f"[advisory, not enforcing] --"]
    for score, claim, occ, fired in ranked:
        verdict = "CANDIDATE" if score >= CANDIDATE_THRESHOLD else "rejected "
        rows.append(f"  {score:>+5.1f} {verdict} {claim} @ {occ.anchor}")
        rows.append(f"          {occ.quote.strip()}")
        rows.append(f"          signals: "
                    + (", ".join(f"{s.name}{s.weight:+g}" for s in fired) or "none"))
    return "\n".join(rows)


if __name__ == "__main__":
    print(report())
