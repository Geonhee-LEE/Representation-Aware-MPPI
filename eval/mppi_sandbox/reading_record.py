"""Persist a licensed reading, so the next one can be read against it.

D-072 went looking for the per-site ratios D-066..D-071 measured and found that
**nothing wrote them down**.  Six cycles emitted prose; the numbers survive only
where a headline happened to want them, and :func:`published_ratios.missing`
names the **16 of 33** licensed cells that did not make it — the source-frame
control on **11 of 11**.  So Q-078's no-new-run half came back not merely weak
but degenerate: two sites carry a gap and a control on both licensed trees, and
:data:`exclusion_scope.RANK_MIN_N` refuses n=2 because every pair of distinct
2-orderings correlates at exactly ±1.

The defect is plumbing, not measurement.  :func:`exclusion_scope.paired_reading`
and :func:`~exclusion_scope.replicated_reading` **already compute** the gap and
both frame controls for all seven sites; the loss happened between computing
them and writing the cycle up.  This module closes that seam: a reading in, one
JSON file out, and every downstream reading — :func:`exclusion_scope.
ratio_grades`, :func:`~exclusion_scope.ratio_ranking`, :func:`~exclusion_scope.
rank_agreement` — re-derivable from the file with no run and no retyping.

What this does *not* do
-----------------------

It does not recover the 16 dropped cells.  Those measurements are gone; their
runs are gone; the trees they were taken on are gone.  D-072's negative stands
exactly as written and this module is the forward fix, which is the honest
scope — it makes the *next* pair of readings comparable, and Q-078 becomes
answerable one licensed batch from now rather than retroactively.

The schema is derived, not typed
--------------------------------

D-047's lesson was a hand-typed copy of a registry that had grown underneath it.
So :data:`CELL_FIELDS` is read off :class:`exclusion_scope.FrameAttribution`
with :func:`dataclasses.fields` rather than spelled out: a field added to the
grader is a field the record carries and a field
:func:`test_record_carries_every_grader_field` demands, in the same commit,
without anyone remembering to.

Which denominator (Q-079)
-------------------------

Every ratio published to date divides the gap by the **exclusion frame alone**;
:class:`exclusion_scope.RatioGrade` divides by both frames summed.  Those are
different numbers over the same evidence, and D-072 filed Q-079 asking which is
right.  The record's answer is that this is the wrong shape of question: it
stores **both deltas per site**, so either denominator is derivable from the
file, and the manifest *declares* which one the cycle reported
(:data:`DENOM_BOTH` / :data:`DENOM_MEASURED`).  A reading does not have to pick;
it has to say.  That is CrowdSkill's "which output columns" field (feed
2026-08-05 00:00) doing real work rather than being adopted decoratively.

The seed field, honestly
------------------------

CrowdSkill's manifest asks for a random-seed schedule and this artifact class
has none — and that absence is not a shrug, it is the subject.  The only
documented way these counts move between two runs of one suite is an
address-based ``__repr__`` (:func:`predicate_inputs.drift`), and process
addresses are unseeded entropy nobody controls.  :attr:`Manifest.entropy` says
so in the file, next to the counts it explains.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, fields
from pathlib import Path

from eval.mppi_sandbox import claim_scope
from eval.mppi_sandbox import exclusion_scope as es
from eval.mppi_sandbox import predicate_inputs as pi
from eval.mppi_sandbox import predicate_vacuity as pv

REPO_ROOT = claim_scope.REPO_ROOT

#: Version of the on-disk shape.  Bumped when a field's *meaning* changes, not
#: when one is added — :data:`CELL_FIELDS` already makes additions visible.
SCHEMA = 1

#: The denominator :class:`exclusion_scope.RatioGrade` uses: both frames summed,
#: D-068's own noise budget.
DENOM_BOTH = "measured+source"
#: The denominator every published ratio actually used — the exclusion frame
#: alone.  Named so a record can say it was reported this way (Q-079).
DENOM_MEASURED = "measured"

#: Per-site fields, read off the grader rather than typed.  See the module
#: docstring: a hand-copied registry is D-047's exact defect.
CELL_FIELDS: tuple[str, ...] = tuple(f.name for f in fields(es.FrameAttribution))

#: The grader's *derived* per-site quantities — right now exactly ``gap``.
#:
#: These are not stored and must not be: ``gap`` is ``|reconstructed -
#: measured|``, so writing it down would create a second copy of a number that
#: can disagree with its own inputs.  But they are what a **reader** quotes, and
#: that gap between the two vocabularies is not hypothetical: the first version
#: of :func:`would_have_carried` compared against :data:`CELL_FIELDS` alone and
#: reported that the format covered **14** of the 16 dropped cells, because two
#: of them were published as ``gap`` and ``gap`` is a property.  A coverage
#: check keyed on storage names under-reports by exactly the quantities anyone
#: actually cites.  Derived, not typed, for :data:`CELL_FIELDS`' reason.
DERIVED_FIELDS: tuple[str, ...] = tuple(
    name for name, value in vars(es.FrameAttribution).items()
    if isinstance(value, property))

#: Everything a cell can answer for, stored or computed.
#:
#: The redundant-looking ``tuple(...)`` is load-bearing and was measured, not
#: guessed.  :func:`guard_reflexivity._is_set_valued` decides whether a module
#: constant is a *registry* by inspecting its **initializer form** — a
#: collection display or one of :data:`guard_reflexivity._SET_CALLS`.  Written
#: as the bare concatenation ``CELL_FIELDS + DERIVED_FIELDS`` this is a ``BinOp``
#: of two names, so the scan does not see a registry, and
#: :func:`would_have_carried` — an ``in``-shaped filter against it — **does not
#: enter the guard pool** (54, not 55).  Wrapping the identical value in
#: ``tuple`` puts it back.  Same guard, same registry, same sense, two
#: spellings, one visible: D-072's finding about the ``&`` operator, one level
#: down and in the worse direction, because the invisible spelling here is the
#: *ordinary* way a registry assembled from two other registries gets written.
#: Pinned by ``test_the_scan_is_blind_to_a_concatenated_registry``.
CARRIED_FIELDS: tuple[str, ...] = tuple(CELL_FIELDS + DERIVED_FIELDS)


@dataclass(frozen=True)
class Manifest:
    """The five things that have to be true of a reading for it to be re-read.

    Adapted from CrowdSkill's run-manifest contract (research feed, 2026-08-05
    00:00), one field at a time, with the mismatches stated rather than padded:

    ================================  ========================================
    CrowdSkill field                  here
    ================================  ========================================
    software version                  :attr:`tree` — the measured tree's hash
    geometry hash-or-source-ref       :attr:`tree` again; the tree *is* the
                                      subject, there is no separate scene
    random-seed schedule              :attr:`entropy` — **unseeded**, and that
                                      is the finding, not an omission
    parameter manifest                :attr:`k`, :attr:`hidden`,
                                      :attr:`population`
    declared output columns           :attr:`denominator`, :attr:`columns`
    ================================  ========================================

    :attr:`licensed` is carried too, because a record of an unlicensed batch is
    still worth keeping — D-069's guard exists to make "not all one tree" a
    reportable outcome rather than a silently-averaged one, and a file that
    dropped those readings would rebuild the selection bias by hand.
    """

    tree: str
    trees: tuple[str, ...]
    licensed: bool
    k: int
    hidden: tuple[str, ...]
    population: int
    denominator: str
    entropy: str
    columns: tuple[str, ...] = CELL_FIELDS

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"tree={self.tree[:12] or '?'} k={self.k} "
                f"licensed={self.licensed} n={self.population} "
                f"denominator={self.denominator}")


#: What :attr:`Manifest.entropy` says for a suite-census reading.  One string,
#: one place, so two records cannot disagree about the same fact.
UNSEEDED = ("unseeded: distinct-input fingerprints of address-repr sites are "
            "process addresses, which no seed controls (predicate_inputs.drift)")


@dataclass(frozen=True)
class Record:
    """One licensed reading, complete enough to re-grade without re-running."""

    manifest: Manifest
    cells: tuple[dict, ...]
    measured_bands: tuple[float, ...]
    source_bands: tuple[float, ...]

    @property
    def attributions(self) -> tuple[es.FrameAttribution, ...]:
        """The grader's own objects, rebuilt from the file."""
        return tuple(es.FrameAttribution(**{f: c[f] for f in CELL_FIELDS})
                     for c in self.cells)

    @property
    def grades(self) -> tuple[es.RatioGrade, ...]:
        return es.ratio_grades(self.attributions)

    @property
    def ranking(self) -> tuple[es.RatioGrade, ...]:
        return es.ratio_ranking(self.attributions)

    @property
    def sites(self) -> tuple[str, ...]:
        return tuple(c["site"] for c in self.cells)

    def ratios(self, denominator: str = DENOM_BOTH) -> dict[str, float]:
        """Per-site ratio under either denominator — Q-079 as a parameter.

        The record carries both deltas, so this is a *view*, not a second
        measurement.  A cycle that wants to compare its number against a
        published one divides the way the publication did and says so; a cycle
        that wants the conservative budget takes the default.
        """
        if denominator not in (DENOM_BOTH, DENOM_MEASURED):
            raise ValueError(f"unknown denominator: {denominator!r}")
        out = {}
        for c in self.cells:
            control = (c["measured_delta"] + c["source_delta"]
                       if denominator == DENOM_BOTH else c["measured_delta"])
            gap = abs(c["reconstructed"] - c["measured"])
            out[c["site"]] = float("inf") if control == 0 else gap / control
        return out

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return f"{self.manifest} sites={len(self.cells)}"


def _bands(reading) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Both frames' bands, whichever reading shape produced them.

    :class:`exclusion_scope.ReplicatedReading` already lists its C(k,2) bands;
    :class:`~exclusion_scope.LicensedReading` holds the pair itself, so its band
    is computed here and lands as a one-element list.  Same field either way —
    the *distribution* of the band is what D-071 found to be 7.7× wide, and a
    record that stored a scalar for k=2 and a list for k>2 would make that
    comparison a typing exercise.
    """
    replicated = getattr(reading, "measured_bands", None)
    if replicated is not None:
        return tuple(replicated), tuple(reading.source_bands)
    return ((pi.drift_band(reading.measured_drifts),),
            (pi.drift_band(reading.source_drifts),))


def to_record(reading,
              denominator: str = DENOM_BOTH,
              hidden: Sequence[str] = pv.EXCLUDED_TESTS,
              population: int | None = None) -> Record:
    """Serialise a :class:`~exclusion_scope.LicensedReading` or replicate of one.

    ``population`` defaults to the number of sites the reading graded, which is
    the disagreeing set and *not* the predicate population — so a caller that
    knows the real one should pass it.  Defaulting to the smaller number rather
    than guessing the larger keeps the record from asserting a count nobody
    took.
    """
    measured_bands, source_bands = _bands(reading)
    trees = tuple(reading.trees)
    return Record(
        manifest=Manifest(
            tree=trees[0] if reading.licensed and trees else "",
            trees=trees,
            licensed=reading.licensed,
            k=getattr(reading, "k", 2),
            hidden=tuple(hidden),
            population=len(reading.attributions) if population is None
            else population,
            denominator=denominator,
            entropy=UNSEEDED,
        ),
        cells=tuple({f: getattr(a, f) for f in CELL_FIELDS}
                    for a in reading.attributions),
        measured_bands=measured_bands,
        source_bands=source_bands,
    )


def write(record: Record, path: Path) -> Path:
    """Write ``record`` as JSON.  Sorted keys, so two records diff line by line."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": SCHEMA,
        "manifest": {f.name: getattr(record.manifest, f.name)
                     for f in fields(Manifest)},
        "cells": [dict(c) for c in record.cells],
        "measured_bands": list(record.measured_bands),
        "source_bands": list(record.source_bands),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def read(path: Path) -> Record:
    """Load a record written by :func:`write`.

    Refuses an unknown ``schema`` outright rather than best-efforting it: the
    whole value of the file is that the number in it means what the reader
    thinks it means, and a silent partial parse is how a transcription defect
    comes back wearing JSON.
    """
    payload = json.loads(Path(path).read_text())
    if payload.get("schema") != SCHEMA:
        raise ValueError(f"unsupported record schema: {payload.get('schema')!r}")
    m = payload["manifest"]
    missing_fields = [f for f in CELL_FIELDS
                      for c in payload["cells"] if f not in c]
    if missing_fields:
        raise ValueError(f"record is missing grader fields: "
                         f"{sorted(set(missing_fields))}")
    return Record(
        manifest=Manifest(
            tree=m["tree"], trees=tuple(m["trees"]), licensed=m["licensed"],
            k=m["k"], hidden=tuple(m["hidden"]), population=m["population"],
            denominator=m["denominator"], entropy=m["entropy"],
            columns=tuple(m["columns"]),
        ),
        cells=tuple(payload["cells"]),
        measured_bands=tuple(payload["measured_bands"]),
        source_bands=tuple(payload["source_bands"]),
    )


def agreement(first: Record, second: Record) -> es.RankAgreement:
    """Q-078, computed from two files instead of from six cycles of prose.

    Nothing here is new statistics — it is :func:`exclusion_scope.rank_agreement`
    with its inputs supplied by the record rather than retyped.  That is the
    entire point: the reason D-072 could not answer Q-078 was never the
    statistic, it was that ``first`` and ``second`` did not exist on disk.
    """
    return es.rank_agreement(first.grades, second.grades)


def comparable(first: Record, second: Record) -> tuple[str, ...]:
    """Why two records may not be rank-correlated, or ``()`` if they may.

    Read *before* :func:`agreement`, because a rho over incomparable readings is
    a number that looks fine.  Three ways it goes wrong, all of which happened
    at least once in D-066..D-071:

    - either reading is unlicensed (its own frames disagree on the tree),
    - both readings are of the **same** tree, so the correlation measures
      nothing about reproduction,
    - the declared denominators differ, so the two rankings order different
      quantities.
    """
    out = []
    if not first.manifest.licensed:
        out.append("first reading is unlicensed")
    if not second.manifest.licensed:
        out.append("second reading is unlicensed")
    if (first.manifest.licensed and second.manifest.licensed
            and first.manifest.tree == second.manifest.tree):
        out.append(f"both readings are of tree {first.manifest.tree[:12]}")
    if first.manifest.denominator != second.manifest.denominator:
        out.append(f"denominators differ: {first.manifest.denominator} vs "
                   f"{second.manifest.denominator}")
    return tuple(out)


def uncarried_fields() -> tuple[str, ...]:
    """Entries of :data:`CARRIED_FIELDS` a round-tripped cell cannot answer for.

    The watcher :func:`guard_reflexivity.unwatched_exemptions` asked for, and it
    is a real one rather than a decoration.  Making :data:`CARRIED_FIELDS` a
    visible registry immediately made it an **unwatched** allow-list — a TYPED
    set that filters a guard's population while no module-level function
    enumerates it, which is exactly the state D-047's defect lived in.

    What it catches: a name in :data:`CARRIED_FIELDS` that survives neither as a
    stored key nor as a property of the rebuilt object.  That happens the moment
    :class:`exclusion_scope.FrameAttribution` grows a field the record does not
    round-trip (an ``init=False`` field, say), and it would otherwise show up as
    :func:`would_have_carried` quietly over-reporting its own coverage.

    The exempting set is **derived, not typed**: it is read off a cell that has
    actually been through the round trip (``dict`` out, ``FrameAttribution``
    back in), so it is a second observation of the same thing rather than a
    second copy of the list.  A registry watched by a copy of itself is D-045's
    defect; a registry watched by a measurement is the thing that catches it.

    The probe is built from :data:`CELL_FIELDS` rather than typed out, so this
    does not become the hand-copied registry two levels down.
    """
    rebuilt = es.FrameAttribution(**{f: 0 for f in CELL_FIELDS})
    answerable = {name for name in dir(rebuilt) if not name.startswith("_")}
    return tuple(f for f in CARRIED_FIELDS if f not in answerable)


def would_have_carried(missing: Sequence[tuple[str, str, str]] | None = None
                       ) -> tuple[tuple[str, str, str], ...]:
    """Which of :func:`published_ratios.missing`'s cells this format carries.

    A record built by :func:`to_record` has no optional fields — every cell gets
    every entry of :data:`CELL_FIELDS` because the grader computed them all — so
    the answer is "all of the ones the format can answer for", and the residue
    (if any) is a quantity the prose reported that the record cannot supply.

    Keyed on :data:`CARRIED_FIELDS`, **not** :data:`CELL_FIELDS`, for the reason
    written there: two of the sixteen dropped cells were published as ``gap``,
    which the record derives rather than stores, and a check that missed them
    would have understated its own coverage while looking rigorous.

    This is a claim about the **format**, and the distinction matters enough to
    be in the name: it does not recover a single dropped number.  It says that a
    cycle running this code cannot drop one.

    ``missing`` defaults to the live :func:`published_ratios.missing` rather than
    being required.  Not sugar: :func:`exemption_masking.unscreened` grades a
    guard ``UNRUNNABLE`` when it cannot be called at HEAD without fabricated
    arguments, and a guard nothing can call is a guard nothing screens for an
    inert exemption — D-058's defect, one module over.
    """
    if missing is None:
        from eval.mppi_sandbox import published_ratios as pr
        missing = pr.missing()
    return tuple(m for m in missing if m[2] in CARRIED_FIELDS)


def unrecoverable(missing: Sequence[tuple[str, str, str]] | None = None
                  ) -> tuple[tuple[str, str, str], ...]:
    """The counterpart, and the one that should be quoted next to it.

    Every cell :func:`published_ratios.missing` names is gone: its run is gone,
    its tree is gone, and no format adopted today brings it back.  So this is
    the whole input, unfiltered — stated as a function rather than as a sentence
    so that a future cycle reading :func:`would_have_carried`'s happy number has
    the other one in the same namespace.
    """
    if missing is None:
        from eval.mppi_sandbox import published_ratios as pr
        missing = pr.missing()
    return tuple(missing)


def take_and_record(path: Path, k: int = 3, root: Path | None = None,
                    denominator: str = DENOM_BOTH) -> Record:  # pragma: no cover
    """Buy a licensed batch and write it down — the hook STATE #2 asks for.

    Not exercised by the fast suite: it is 2k concurrent five-minute suite runs.
    The next cycle that buys a batch calls this instead of
    :func:`exclusion_scope.replicated_reading` directly, and the batch it was
    going to run anyway becomes the first record on disk.
    """
    package = (root / "eval" / "mppi_sandbox") if root is not None else pv.PACKAGE
    population, _ = pv._scan(package)
    reading = es.replicated_reading(k=k, population=population, root=root)
    record = to_record(reading, denominator=denominator,
                       population=len(population))
    write(record, path)
    return record


def report(record: Record) -> str:  # pragma: no cover - reporting
    lines = [str(record), f"  entropy: {record.manifest.entropy}", ""]
    lines += [f"  {g}" for g in record.ranking]
    lines += ["", f"  measured bands: {record.measured_bands}",
              f"  source bands:   {record.source_bands}"]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - CLI
    import sys
    print(report(read(Path(sys.argv[1]))))
