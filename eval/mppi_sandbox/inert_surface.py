"""Which tracked paths can a write move a test outcome through?  (STATE #2)

D-082 shipped the push gate one cycle ago and it works: no receipt, no push.
But :func:`push_preflight.check` compares a **whole-tree fingerprint**, and
D-044 fixed a cycle order that writes *after* the receipt is taken —

    4a journal → 4a-bis docs → commit → **record** → 4b ``JOURNAL.md``
    → 4c ``STATE.md`` → TSV ``results/*.tsv`` → commit → push

— so by the time the push line runs, three tracked files have moved and the
receipt grades :data:`~push_preflight.STALE`.  Every cycle.  The 12:00 cycle
paid for it in the only currency available: a **second full suite run** at the
end, on a 15-minute execute budget.  Two rules that are each correct alone and
contradict when composed.

D-044's own table already contains the resolution and states it as an
assertion:

    | 4b ``JOURNAL.md``, 4c ``STATE.md`` | no — read by no test | after the re-run |
    | TSV ``results/*.tsv``              | no — read by no test (checked) | last write |

"(checked)" is doing load-bearing work there and nobody re-checks it.  An
exemption whose basis was measured once, by hand, and never again is D-079's
decoration: the day a test starts reading ``results/*.tsv``, the exemption
silently becomes a hole and the gate that exists to catch unmeasured pushes
starts clearing them.

So this module does not *type* the inert set.  It **derives** one and makes the
derivation falsifiable.

The derivation was finally *run* on 2026-08-06 and all four grade
:data:`INERT` — see :data:`PROBED`.  Worth stating plainly that D-044's
hand-check was **right**, because for the two cycles this module existed
unpopulated the tax was paid anyway: an instrument that has not been read
grades nothing, and :func:`inert` answers ``False`` to every question it is
asked until a probe is transcribed into it.

Two layers, and the static one is deliberately an over-approximation
--------------------------------------------------------------------

**Static** — :func:`readers` asks which test files could reach a path *at all*.
Mention-in-the-test-file is not a necessary condition (a test can iterate
:data:`tree_provenance.DECLARED_LOCAL_ONLY` and open every entry without ever
spelling ``STATE.md``), so the scan is transitive one hop: a test counts as a
reader if it mentions the path, **or** if it imports a package module that
does.  Over-approximating is the safe direction — a path this layer calls
unreachable is unreachable, and a path it calls reachable may still be inert.

**Dynamic** — :func:`probe` settles it the only way it can be settled: change
the file's bytes, re-run the tests the static layer named, compare outcomes.
This is D-081's differential probe, and it is here for the same reason: the
question "does a test read this file?" is about behaviour, and a scan over
syntax answers a different question that merely correlates.

The probe runs over the *named subset*, not the suite, which is what makes it
affordable — seconds instead of the eight minutes a full run costs.  That is
sound precisely because the static layer over-approximates: a test outside the
named set has no path to the file, so re-running it would be re-running a
control that cannot move.

``NO_READER`` is not ``INERT``, and an empty probe is neither
------------------------------------------------------------

Three separate states, kept separate because collapsing any pair reproduces a
defect this package has already paid for:

* :data:`NO_READER` — the static layer found nothing that could reach it.  A
  claim about the *scan*, resting on the one-hop bound; honest, and weaker than
  a measurement.
* :data:`INERT` — probed, and the suite subset did not move.  A measurement.
* :data:`CONTENT_READ` — probed, and something moved.  The exemption is void.
* :data:`VACUOUS` — the probe ran **no tests**, so it observed nothing.  Grading
  that ``INERT`` is exactly D-075's vacuous survival and D-081's empty-pair
  ``IDENTICAL``: emptiness is decided *before* success, here as everywhere else
  in this package.

Refs: D-082 (a push is licensed by a receipt), D-044 (the count has one valid
moment; the surface table), D-043 (bind a count to its tree), D-079 (an
exemption without a control is decoration), D-081 (measure the scan, do not
infer it from syntax), D-076 (a typed set is admissible when a control proves
it still holds).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import tree_provenance as tp

#: Static verdicts.
NO_READER = "NO_READER"
HAS_READER = "HAS_READER"

#: Probe verdicts.
INERT = "INERT"
CONTENT_READ = "CONTENT_READ"
VACUOUS = "VACUOUS"

#: A verdict assembled from a pinned reading plus a probe of what entered since.
#: Weaker than :data:`INERT` and deliberately spelled differently — see
#: :func:`compose`.
INERT_COMPOSED = "INERT_COMPOSED"

#: How many compositions a pin may carry before a full probe is required again.
#:
#: Composition buys affordability at the cost of one un-re-measured premise (the
#: carried readers are inert *on the tree the base probe ran on*).  Left
#: uncapped, each generation would inherit the last one's debt and the pin would
#: decay exactly the way the four original pins decayed — silently, and in the
#: direction that reads clean.  Generations 0..2 are acceptable; the third
#: composition is refused, which forces the ~8-minute full probe back on the
#: schedule instead of leaving it to a cycle that notices.
COMPOSITION_CAP = 3

#: The write surfaces the Phase-4 cycle order touches *after* the receipt is
#: recorded, each with the write that moves it.  This is the population the
#: module exists to grade — not a general-purpose inert-file registry.
#:
#: ``results/`` is a **prefix**: the TSV path is per-branch, so pinning the
#: literal name would exempt one branch's file and silently re-admit the next.
POST_RECEIPT_WRITES: dict[str, str] = {
    "STATE.md": "D-044 4c: full-overwrite snapshot, written after the re-run",
    "JOURNAL.md": "D-044 4b: append-at-top digest, written after the re-run",
    "RESULTS.md": "regenerated by scripts/aggregate_results.sh before push",
    "results/": "D-044: the TSV row, last write before push",
}

#: Repo-relative prefixes whose ``*.py`` files are scanned for mentions.  Kept
#: narrow on purpose: a mention inside a file no test can import is not a path
#: to the file, and widening this to the whole repo would import ``scripts/``
#: shell wrappers that no pytest run executes.
SCAN_ROOTS: tuple[str, ...] = ("eval/",)

#: The package prefix an ``import`` of a scanned module is spelled with.
_PKG = "eval/mppi_sandbox/"


@dataclass(frozen=True)
class Readers:
    """Test files that could reach a path, split by how they reach it."""

    direct: tuple[str, ...] = ()
    via: tuple[str, ...] = ()
    modules: tuple[str, ...] = ()

    @property
    def all(self) -> tuple[str, ...]:
        return tuple(sorted({*self.direct, *self.via}))

    def __bool__(self) -> bool:
        return bool(self.all)

    def describe(self) -> str:
        if not self:
            return "no reader"
        bits = [f"direct: {len(self.direct)}", f"via: {len(self.via)}"]
        if self.modules:
            bits.append(f"through {', '.join(self.modules)}")
        return "; ".join(bits)


def _python_sources(root: Path | None = None) -> dict[str, str]:
    """Tracked ``*.py`` text under :data:`SCAN_ROOTS`, keyed by repo path.

    Reads from the **worktree**, not from ``HEAD``: the surface a probe would
    execute is the one on disk, and a scan of the committed tree would grade a
    file the run never sees.
    """
    base = root or tp.REPO_ROOT
    out: dict[str, str] = {}
    for rel in tp.tracked_paths(root):
        if not rel.endswith(".py") or not rel.startswith(SCAN_ROOTS):
            continue
        try:
            out[rel] = (base / rel).read_text(errors="replace")
        except OSError:
            continue
    return out


def _is_test(rel: str) -> bool:
    return Path(rel).name.startswith("test_")


def mentions(candidate: str, sources: dict[str, str] | None = None) -> tuple[str, ...]:
    """Scanned files whose source text contains *candidate*.

    Matched as a substring of the **repo-relative path**, not the basename.
    Keying on the basename is the defect D-081 named a class: ``run.py`` is a
    name three modules own, and a scan that matched it would attribute reads
    across unrelated files.  A trailing-slash candidate matches by prefix, so
    ``results/`` covers every per-branch TSV.
    """
    src = _python_sources() if sources is None else sources
    return tuple(sorted(rel for rel, text in src.items() if candidate in text))


def _module_name(rel: str) -> str:
    """Importable dotted suffix for a scanned package module."""
    return Path(rel).stem


def readers(candidate: str, sources: dict[str, str] | None = None) -> Readers:
    """Test files that could read *candidate*, one hop through the package.

    ``direct`` spells the path itself.  ``via`` imports a package module that
    spells it — the case a direct scan misses, and the reason the scan is
    transitive: a test that walks :data:`tree_provenance.DECLARED_LOCAL_ONLY`
    and opens each entry reads ``STATE.md`` without containing the string.

    One hop, not fixpoint, and this is a stated bound rather than a claim of
    completeness: two hops would pull in most of the package through
    ``tree_provenance`` and the resulting set would be the suite, which is the
    thing the probe cannot afford to run.  The dynamic layer is what closes the
    gap — a path this function under-reports grades ``CONTENT_READ`` on any
    honest probe, because the probe compares outcomes rather than imports.
    """
    src = _python_sources() if sources is None else sources
    named = mentions(candidate, src)
    direct = tuple(r for r in named if _is_test(r))
    carriers = tuple(r for r in named if not _is_test(r) and r.startswith(_PKG))
    wanted = {_module_name(r) for r in carriers}
    via = tuple(
        sorted(
            rel
            for rel, text in src.items()
            if _is_test(rel)
            and rel not in direct
            and any(_imports(text, mod) for mod in wanted)
        )
    )
    return Readers(direct=direct, via=via, modules=tuple(sorted(wanted)))


def _imports(text: str, module: str) -> bool:
    """Does *text* import the package module *module*?

    Three spellings, because the package uses all three: ``from . import X``,
    ``from ..mppi_sandbox import X`` and a dotted ``mppi_sandbox.X`` reference.
    Substring-matched with the delimiters attached so ``ab`` does not match
    ``tab``.
    """
    return any(
        token in text
        for token in (
            f"import {module}\n",
            f"import {module} ",
            f"import {module},",
            f"mppi_sandbox.{module}",
            f" {module}.",
        )
    )


def classify(candidate: str, sources: dict[str, str] | None = None) -> str:
    """:data:`NO_READER` or :data:`HAS_READER` — the static layer's verdict."""
    return HAS_READER if readers(candidate, sources) else NO_READER


@dataclass(frozen=True)
class Probe:
    """A differential read of one path: mutate, re-run the named subset, compare."""

    candidate: str
    verdict: str
    before: dict[str, int] = field(default_factory=dict)
    after: dict[str, int] = field(default_factory=dict)
    tests: tuple[str, ...] = ()
    #: Reader files whose inertness is **inherited from the base pin**, not
    #: re-measured by this probe.  Empty for a full probe.  Named rather than
    #: counted, per D-038: an exclusion stated is auditable, one implied is a
    #: hole — and this is the exact premise a composed verdict rests on.
    carried: tuple[str, ...] = ()

    def describe(self) -> str:
        tail = f"; carried {len(self.carried)} from the pin" if self.carried else ""
        return (
            f"{self.candidate}: {self.verdict} "
            f"({len(self.tests)} test files; {self.before} -> {self.after}){tail}"
        )


def _run(tests: tuple[str, ...], root: Path | None = None) -> dict[str, int]:
    from . import push_preflight as pp

    proc = subprocess.run(
        ("python3", "-m", "pytest", *tests, "-q", "--no-header", "-p", "no:cacheprovider"),
        cwd=str(root or tp.REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=900,
    )
    return pp.parse_summary(proc.stdout + proc.stderr)


def probe(
    candidate: str,
    root: Path | None = None,
    sources: dict[str, str] | None = None,
    tests: tuple[str, ...] | None = None,
) -> Probe:
    """Change the bytes, re-run the readers, and see whether anything moved.

    The mutation is an **appended comment line**, not a truncation: these are
    all append-structured text artifacts, and appending is the write the cycle
    order actually performs.  Probing with a destructive edit would answer a
    question no cycle asks.

    The original bytes are restored in a ``finally``, and a directory candidate
    probes its newest member — a prefix has no content of its own to move.

    *tests* restricts the re-run to a caller-chosen subset of the named readers.
    :func:`reprobe` uses it to run only what entered since a pin; passing a set
    that is not a subset of the readers is a caller error, not a narrower
    reading, so it is refused rather than silently intersected.
    """
    base = root or tp.REPO_ROOT
    named = readers(candidate, sources)
    if not named:
        return Probe(candidate, VACUOUS, tests=())
    if tests is not None and not set(tests) <= set(named.all):
        raise ValueError(
            f"{candidate}: probe subset is not a subset of its readers: "
            f"{sorted(set(tests) - set(named.all))}"
        )

    target = _probe_target(candidate, base)
    if target is None:
        return Probe(candidate, VACUOUS, tests=named.all)

    tests = named.all if tests is None else tuple(tests)
    if not tests:
        return Probe(candidate, VACUOUS, tests=())
    before = _run(tests, root)
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n<!-- inert_surface probe -->\n")
        after = _run(tests, root)
    finally:
        target.write_bytes(original)

    if not before or not after:
        verdict = VACUOUS
    elif before == after:
        verdict = INERT
    else:
        verdict = CONTENT_READ
    return Probe(candidate, verdict, before=before, after=after, tests=tests)


def entrants(candidate: str, sources: dict[str, str] | None = None) -> tuple[str, ...]:
    """Reader files that entered the set since the pin was taken.

    ``()`` when there is no pin — an unpinned candidate has no base to compose
    onto, so "nothing entered" would be the wrong reading of the wrong question.
    """
    pin = PROBED.get(candidate)
    if pin is None:
        return ()
    was = set(pin.readers_key.split("|")) if pin.readers_key else set()
    return tuple(sorted(set(readers(candidate, sources).all) - was))


def departures(candidate: str, sources: dict[str, str] | None = None) -> tuple[str, ...]:
    """Reader files that left the set since the pin was taken.

    Reported but not probed, and that asymmetry is the composition rule: a
    departure can only shrink the set a verdict quantifies over, and movement is
    a disjunction over members, so losing one cannot introduce movement.  An
    entrant can.
    """
    pin = PROBED.get(candidate)
    if pin is None:
        return ()
    was = set(pin.readers_key.split("|")) if pin.readers_key else set()
    return tuple(sorted(was - set(readers(candidate, sources).all)))


def compose(base: str, entrant: str, saw_entrants: bool) -> str:
    """Verdict for the whole reader set, from the pin's and the entrants' halves.

    Sound because a probe verdict is a **disjunction over the set it ran on** —
    "did any named test move" — so for disjoint halves

        moved(pinned ∪ entered) = moved(pinned) ∨ moved(entered)

    and departures are monotone in the safe direction (see :func:`departures`).
    The point of the split is cost: the four original pins took ~34 min between
    them and were stale within a day, which is not a schedule anybody keeps.
    Re-running only what entered costs seconds and keeps the same disjunction.

    What it does **not** buy: the pinned half was measured on the pin's tree, and
    a reader file that kept its name while changing content is not re-measured
    here.  :func:`readers_key` is a set of names, so that drift is invisible to
    the premise check.  Hence the distinct verdict and :data:`COMPOSITION_CAP` —
    the weakening is priced, bounded and spelled, not absorbed into
    :data:`INERT`.
    """
    if base not in (INERT, INERT_COMPOSED):
        return CONTENT_READ if base == CONTENT_READ else VACUOUS
    if not saw_entrants:
        # Nothing entered: the pin's own reading still covers the whole set, so
        # composition adds nothing and must not launder a weaker verdict into a
        # stronger one.
        return base
    if entrant == CONTENT_READ:
        return CONTENT_READ
    if entrant != INERT:
        # A vacuous entrant probe observed nothing.  Grading that INERT is the
        # emptiness-before-success rule this package applies everywhere else.
        return VACUOUS
    return INERT_COMPOSED


def reprobe(
    candidate: str,
    root: Path | None = None,
    sources: dict[str, str] | None = None,
) -> Probe:
    """Re-take a stale pin by probing **only what entered** since it was taken.

    Returns a :class:`Probe` whose ``tests`` are the entrants actually run and
    whose ``carried`` names the readers inherited from the pin.  Falls back to
    the full :func:`probe` when there is no pin to compose onto, or when the pin
    has already carried :data:`COMPOSITION_CAP` generations.
    """
    pin = PROBED.get(candidate)
    if pin is None or pin.generation >= COMPOSITION_CAP - 1:
        return probe(candidate, root, sources)

    new = entrants(candidate, sources)
    carried = tuple(n for n in readers(candidate, sources).all if n not in new)
    if not new:
        return Probe(candidate, compose(pin.verdict, VACUOUS, False), carried=carried)

    part = probe(candidate, root, sources, tests=new)
    return Probe(
        candidate,
        compose(pin.verdict, part.verdict, True),
        before=part.before,
        after=part.after,
        tests=new,
        carried=carried,
    )


def _probe_target(candidate: str, base: Path) -> Path | None:
    """The concrete file a candidate names — newest member for a prefix."""
    if not candidate.endswith("/"):
        path = base / candidate
        return path if path.is_file() else None
    directory = base / candidate.rstrip("/")
    members = sorted(
        (p for p in directory.glob("*") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
    )
    return members[-1] if members else None


def readers_key(candidate: str, sources: dict[str, str] | None = None) -> str:
    """A stable name for *which* files could reach *candidate*, not how many.

    This is the premise a pinned probe verdict rests on.  The probe re-ran a
    named subset and observed nothing move; that finding is about **those
    files**, so it survives exactly as long as the set does.  Counting would not
    do — a test file removed and another added leaves the count alone.
    """
    return "|".join(readers(candidate, sources).all)


@dataclass(frozen=True)
class Pin:
    """A recorded probe verdict plus the premise it was taken under."""

    verdict: str
    readers_key: str
    taken: str
    note: str = ""
    #: Reader files this verdict inherited rather than re-measured, for a
    #: :data:`INERT_COMPOSED` pin.  Empty for a full probe.
    carried: tuple[str, ...] = ()
    #: Compositions carried since the last full probe.  ``0`` is a full probe.
    #: :func:`inert` refuses at :data:`COMPOSITION_CAP`.
    generation: int = 0


#: Directory the transcribed reader sets below live in.
_TESTS = "eval/mppi_sandbox/tests/"


def _key(*names: str) -> str:
    """A :func:`readers_key` spelled as its member basenames.

    The keys this transcribes are ~900-character ``|``-joined path lists, and a
    pin is only useful if a reviewer can see *which* file entered or left the
    set.  One name per line diffs; one long string does not.  Sorted here
    because :attr:`Readers.all` is sorted — the key is a set, and a
    transcription that got the order wrong should still compare equal, while a
    transcription that got a *name* wrong must not.
    """
    return "|".join(sorted(_TESTS + n for n in names))


#: Probe verdicts recorded on a named tree, keyed by candidate.
#:
#: These are **measurements**, produced by ``python3 -m
#: eval.mppi_sandbox.inert_surface probe`` and transcribed — not judgements.  A
#: candidate absent from here is not exempt, which is the direction that fails
#: closed: the gate refuses, a cycle pays for one extra run, and nobody ships an
#: unmeasured tree.
#:
#: The static layer grades all four :data:`HAS_READER`, so D-044's "read by no
#: test (checked)" is **false as a static claim** — every one of them is named,
#: directly or one hop away, by some test.  That is why the pin exists at all:
#: reachability is not readership, and only the differential probe can tell the
#: two apart.
#:
#: Taken 2026-08-06 06:00 KST on ``d6b60c8``, all four :data:`INERT` — so
#: D-044's "(checked)" is true after all, and is now a **measurement** rather
#: than a hand-check nobody re-ran.  Until this dict was filled the module was
#: complete and inoperative: :func:`inert` is ``False`` for every unpinned
#: candidate, so :func:`filter_drift` ignored nothing, every receipt graded
#: :data:`~push_preflight.STALE` on the 4b/4c/TSV writes, and each cycle bought
#: the gate's assent with a second full suite run.  The instrument existed; the
#: reading it grades had never been taken.
#:
#: The four probes cost ~34 min of wall clock between them and this dict is
#: what that buys — per candidate, one mutate/restore pair over its **named
#: reader subset** (10–14 test files), not over the suite.
#: All four went stale **within one day** of being taken — see :func:`entrants`.
#: Nothing left any reader set; eight test files entered across the four, and a
#: pin whose only re-take costs ~8.5 min of wall clock is a pin that stays
#: stale.  That is not a hypothetical: between 2026-08-06 06:00 and 08-07 01:00
#: every one of these read :data:`~push_preflight.STALE`, :func:`filter_drift`
#: ignored nothing, and each cycle bought the gate's assent with a second full
#: suite run — D-095's ``PROBED == {}`` reached a second time, by attrition
#: rather than by never being filled.  Hence :func:`reprobe` and the
#: :data:`INERT_COMPOSED` generation counter: the four below were re-taken over
#: their **entrants only**, ~3.5 min for all four instead of ~34.
PROBED: dict[str, Pin] = {
    "STATE.md": Pin(
        verdict=INERT_COMPOSED,
        readers_key=_key(
            "test_assert_reach.py",
            "test_ci_verdict.py",
            "test_citation_audit.py",
            "test_claim_scope.py",
            "test_drift_repair.py",
            "test_exemption_masking.py",
            "test_git_surface.py",
            "test_guard_direction.py",
            "test_guard_reflexivity.py",
            "test_inert_surface.py",
            "test_liveness_derivation.py",
            "test_local_only_audit.py",
            "test_predicate_inputs.py",
            "test_probe_reach.py",
            "test_push_claim_gate.py",
            "test_push_preflight.py",
            "test_simd_attribution.py",
            "test_suite_coverage.py",
            "test_tree_provenance.py",
        ),
        taken="2026-08-07 06:00 KST · f8e090a (entrants); base 08-06 06:00 · d6b60c8",
        note=(
            "gen-2: 1 entrant (test_push_claim_gate.py) re-run, 11 passed "
            "unmoved; 18 carried.  Cost 0.9 s — the D-107 estimate of ~3.5 min "
            "for all four was priced off an entrant set of 8 files, and this "
            "re-take had 1."
        ),
        carried=("14 files pinned INERT on d6b60c8",),
        generation=2,
    ),
    "JOURNAL.md": Pin(
        verdict=INERT_COMPOSED,
        readers_key=_key(
            "test_citation_audit.py",
            "test_claim_scope.py",
            "test_exemption_masking.py",
            "test_guard_direction.py",
            "test_inert_surface.py",
            "test_local_only_audit.py",
            "test_predicate_inputs.py",
            "test_probe_reach.py",
            "test_push_claim_gate.py",
            "test_push_preflight.py",
            "test_suite_coverage.py",
            "test_tree_provenance.py",
        ),
        taken="2026-08-07 06:00 KST · f8e090a (entrants); base 08-06 06:00 · d6b60c8",
        note=(
            "gen-2: 1 entrant (test_push_claim_gate.py) re-run, 11 passed "
            "unmoved; 11 carried."
        ),
        carried=("10 files pinned INERT on d6b60c8",),
        generation=2,
    ),
    "RESULTS.md": Pin(
        verdict=INERT_COMPOSED,
        readers_key=_key(
            "test_citation_audit.py",
            "test_claim_scope.py",
            "test_exemption_masking.py",
            "test_git_surface.py",
            "test_guard_direction.py",
            "test_guard_reflexivity.py",
            "test_inert_surface.py",
            "test_local_only_audit.py",
            "test_predicate_inputs.py",
            "test_probe_reach.py",
            "test_push_claim_gate.py",
            "test_push_preflight.py",
            "test_suite_coverage.py",
            "test_tree_provenance.py",
        ),
        taken="2026-08-07 06:00 KST · f8e090a (entrants); base 08-06 06:00 · d6b60c8",
        note=(
            "gen-2: 1 entrant (test_push_claim_gate.py) re-run, 11 passed "
            "unmoved; 13 carried."
        ),
        carried=("12 files pinned INERT on d6b60c8",),
        generation=2,
    ),
    "results/": Pin(
        verdict=INERT_COMPOSED,
        readers_key=_key(
            "test_citation_audit.py",
            "test_claim_scope.py",
            "test_cycle_artifacts.py",
            "test_dispatch_divergence.py",
            "test_drift_repair.py",
            "test_exemption_control.py",
            "test_exemption_masking.py",
            "test_git_surface.py",
            "test_guard_direction.py",
            "test_guard_reflexivity.py",
            "test_inert_surface.py",
            "test_liveness_derivation.py",
            "test_magnitude_survival.py",
            "test_operating_point.py",
            "test_probe_reach.py",
            "test_push_claim_gate.py",
            "test_push_preflight.py",
            "test_repair_admissibility.py",
        ),
        taken="2026-08-07 06:00 KST · f8e090a (entrants); base 08-06 06:00 · d6b60c8",
        note=(
            "gen-2: 2 entrants (test_push_claim_gate.py, "
            "test_push_preflight.py) re-run, 43 passed unmoved; 16 carried.  "
            "This is the "
            "candidate STATE #3 named: cycle_artifacts (D-105) genuinely reads "
            "results/*.tsv, so D-044's 'read by no test (checked)' is false as "
            "a static claim — and the probe says the read does not move an "
            "outcome, so the exemption survives on a measurement rather than on "
            "the hand-check that was already false."
        ),
        carried=("11 files pinned INERT on d6b60c8",),
        generation=2,
    ),
}


def stale_pins(sources: dict[str, str] | None = None) -> tuple[str, ...]:
    """Pinned candidates whose reader set has moved since the probe.

    The control D-079 asks for, and the reason the pin is not decoration: the
    day a test starts reading one of these paths, its reader key changes, this
    function names it, a test goes red, and :func:`inert` withdraws the
    exemption on the **next push** — not on the next audit.
    """
    src = _python_sources() if sources is None else sources
    return tuple(
        sorted(c for c, pin in PROBED.items() if readers_key(c, src) != pin.readers_key)
    )


def inert(candidate: str, sources: dict[str, str] | None = None) -> bool:
    """May a write to *candidate* be ignored when grading a receipt stale?

    Two conditions, and the composition is the content:

    * a recorded probe graded it :data:`INERT` — a measurement, not a claim;
    * the reader set that probe ran over is **still the reader set** — the
      premise re-derived at call time, cheaply, from the tree in hand.

    Either alone clears a bad exemption.  A pin without the premise check is
    D-076's typed set going quietly out of date; the premise check without a
    pin is the static layer, which grades every one of these ``HAS_READER`` and
    would exempt nothing.
    """
    pin = PROBED.get(candidate)
    if pin is None or pin.verdict not in (INERT, INERT_COMPOSED):
        return False
    if pin.generation >= COMPOSITION_CAP:
        # A pin that has carried its budget of un-re-measured generations is
        # withdrawn here rather than at the next audit, for the reason every
        # withdrawal in this module happens here: the gate is where the cost of
        # being wrong is paid.
        return False
    return readers_key(candidate, sources) == pin.readers_key


def filter_drift(
    drift: tp.Drift,
    sources: dict[str, str] | None = None,
    population: dict[str, str] | None = None,
) -> tuple[tp.Drift, tuple[str, ...]]:
    """Split *drift* into what invalidates a receipt and what provably cannot.

    Returns ``(material, ignored)``.  A path is ignored when it is covered by
    :data:`POST_RECEIPT_WRITES` **and** :func:`inert` currently holds for the
    covering entry — never on membership alone.  A drifted path outside the
    population is material by default, because the gate's whole purpose is that
    an unrecognised change is a reason to stop.
    """
    pop = POST_RECEIPT_WRITES if population is None else population
    src = _python_sources() if sources is None else sources
    exempt = {c for c in pop if inert(c, src)}

    def _ignorable(path: str) -> bool:
        return any(
            path == c or (c.endswith("/") and path.startswith(c)) for c in exempt
        )

    ignored = tuple(sorted(p for p in drift.paths if _ignorable(p)))
    # Both halves sorted, for the same reason: this pair is what a refusal
    # prints, and a gate whose message reorders with the caller's argument
    # order is a gate whose output cannot be diffed between two cycles.
    # `ignored` was sorted from the first draft and `material` was not, which
    # is the whole of the D-085 ordering failure.
    material = tp.Drift(
        changed=tuple(sorted(p for p in drift.changed if not _ignorable(p))),
        added=tuple(sorted(p for p in drift.added if not _ignorable(p))),
        removed=tuple(sorted(p for p in drift.removed if not _ignorable(p))),
    )
    return material, ignored


def survey(sources: dict[str, str] | None = None) -> dict[str, Readers]:
    """Static reader set per :data:`POST_RECEIPT_WRITES` entry."""
    src = _python_sources() if sources is None else sources
    return {c: readers(c, src) for c in POST_RECEIPT_WRITES}


def _main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.inert_surface",
        description="Which post-receipt writes can move a test outcome? (STATE #2)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("survey", help="static reader set per candidate")
    p_probe = sub.add_parser("probe", help="mutate and re-run the named readers")
    p_probe.add_argument("candidate", nargs="?", default=None)

    args = ap.parse_args(argv)
    src = _python_sources()

    if args.cmd == "survey":
        for cand, r in survey(src).items():
            print(f"{cand:<14} {classify(cand, src):<11} {r.describe()}")
        return 0

    cands = [args.candidate] if args.candidate else list(POST_RECEIPT_WRITES)
    worst = 0
    for cand in cands:
        p = probe(cand, sources=src)
        print(p.describe())
        if p.verdict == CONTENT_READ:
            worst = 1
    return worst


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())
