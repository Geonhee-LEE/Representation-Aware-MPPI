"""The record has to be sufficient, not merely present.

A serialiser is easy to write and easy to write *lossily*, and a lossy one is
worse than prose because it looks authoritative.  So the load-bearing test here
is not "the file round-trips" — it is that the grades computed from the file are
:func:`operator.eq` to the grades computed from the live reading, over a
synthetic reading built to exercise every verdict the grader can issue.
"""

from __future__ import annotations

import json

import pytest

from eval.mppi_sandbox import exclusion_scope as es
from eval.mppi_sandbox import predicate_inputs as pi
from eval.mppi_sandbox import published_ratios as pr
from eval.mppi_sandbox import reading_record as rr


def _drift(site: str, first: int, second: int, calls: int = 1000) -> pi.Drift:
    return pi.Drift(site=site, first=first, second=second, calls_first=calls,
                    calls_second=calls, address_reprs=True)


def _spread(site: str, counts: tuple[int, ...]) -> pi.Spread:
    return pi.Spread(site=site, counts=counts,
                     calls=(1000,) * len(counts), address_reprs=True)


@pytest.fixture
def licensed() -> es.LicensedReading:
    """A k=2 reading covering FOLD / DRIFT_UNDER / DRIFT_COVERS."""
    disagreements = (("a._pure", 9600, 9814),      # gap 214
                     ("a._set", 9600, 9613),       # gap 13
                     ("a._wide", 9600, 9602))      # gap 2
    measured = (_drift("a._pure", 9600, 9687),     # moved 87
                _drift("a._set", 9600, 9601),      # moved 1
                _drift("a._wide", 9600, 9610))     # moved 10 >= gap 2
    source = (_drift("a._pure", 9600, 9600),
              _drift("a._set", 9600, 9600),
              _drift("a._wide", 9600, 9600))
    trees = ("t0",) * 4
    return es.LicensedReading(
        trees=trees, disagreements=disagreements, measured_drifts=measured,
        source_drifts=source,
        attributions=es.attribute_two_frame(disagreements, measured, source,
                                            trees=trees))


@pytest.fixture
def replicated() -> es.ReplicatedReading:
    """The same three sites at k=3, on a *different* tree."""
    disagreements = (("a._pure", 9600, 9775),
                     ("a._set", 9600, 9615),
                     ("a._wide", 9600, 9603))
    measured = (_spread("a._pure", (9600, 9613, 9600)),
                _spread("a._set", (9600, 9602, 9601)),
                _spread("a._wide", (9600, 9640, 9610)))
    source = (_spread("a._pure", (9600, 9600, 9600)),
              _spread("a._set", (9600, 9600, 9600)),
              _spread("a._wide", (9600, 9600, 9600)))
    trees = ("t1",) * 6
    # Three gap readings off the same batch.  Replicate 1 swaps the top two
    # sites' ratios (_set overtakes _pure) so the ordering control has something
    # to disagree about; replicate 2 repeats replicate 0's ordering.  Controls
    # are shared, so the only thing moving is the gap — which is the point.
    replicate_disagreements = (
        disagreements,
        (("a._pure", 9600, 9750), ("a._set", 9600, 9660),
         ("a._wide", 9600, 9605)),
        (("a._pure", 9600, 9790), ("a._set", 9600, 9610),
         ("a._wide", 9600, 9604)),
    )
    return es.ReplicatedReading(
        k=3, trees=trees, disagreements=disagreements,
        measured_spreads=measured, source_spreads=source,
        measured_bands=(0.005, 0.001, 0.004), source_bands=(0.0, 0.0, 0.0),
        attributions=es.attribute_two_frame(disagreements, measured, source,
                                            trees=trees),
        pair_attributions=es.attribute_two_frame(disagreements, measured,
                                                 source, trees=trees),
        replicate_disagreements=replicate_disagreements)


# --------------------------------------------------------------------------
# Sufficiency — the property the module exists for
# --------------------------------------------------------------------------


def test_round_trip_reproduces_every_grade_exactly(licensed, tmp_path):
    """Not "the file parses" — the *downstream readings* are identical."""
    live = es.ratio_grades(licensed.attributions)
    rr.write(rr.to_record(licensed), tmp_path / "r.json")
    assert rr.read(tmp_path / "r.json").grades == live


def test_round_trip_reproduces_the_ranking(licensed, tmp_path):
    rr.write(rr.to_record(licensed), tmp_path / "r.json")
    loaded = rr.read(tmp_path / "r.json")
    assert loaded.ranking == es.ratio_ranking(licensed.attributions)


def test_record_carries_every_grader_field(licensed, tmp_path):
    """The derived-schema guarantee, asserted against the live dataclass.

    If :class:`exclusion_scope.FrameAttribution` grows a field, this fails
    unless the record grew it too — which it does automatically, because
    :data:`reading_record.CELL_FIELDS` is read off the dataclass.  The test is
    here to catch the *other* direction: someone replacing the derivation with a
    literal.
    """
    from dataclasses import fields
    want = {f.name for f in fields(es.FrameAttribution)}
    payload = json.loads(rr.write(rr.to_record(licensed),
                                  tmp_path / "r.json").read_text())
    for cell in payload["cells"]:
        assert want <= set(cell)


def test_a_cell_missing_a_grader_field_is_refused(licensed, tmp_path):
    """A partial parse must be an error, not a quietly degraded reading."""
    path = rr.write(rr.to_record(licensed), tmp_path / "r.json")
    payload = json.loads(path.read_text())
    del payload["cells"][0]["source_delta"]
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="missing grader fields"):
        rr.read(path)


def test_unknown_schema_is_refused(licensed, tmp_path):
    path = rr.write(rr.to_record(licensed), tmp_path / "r.json")
    payload = json.loads(path.read_text())
    payload["schema"] = SCHEMA_FROM_THE_FUTURE = rr.SCHEMA + 1
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="unsupported record schema"):
        rr.read(path)
    assert SCHEMA_FROM_THE_FUTURE != rr.SCHEMA


# --------------------------------------------------------------------------
# Q-078 — the reading the record makes possible
# --------------------------------------------------------------------------


def test_agreement_between_two_records_needs_no_prose(licensed, replicated,
                                                      tmp_path):
    """Two files in, one rho out — the whole point of the cycle."""
    rr.write(rr.to_record(licensed), tmp_path / "a.json")
    rr.write(rr.to_record(replicated), tmp_path / "b.json")
    got = rr.agreement(rr.read(tmp_path / "a.json"),
                       rr.read(tmp_path / "b.json"))
    assert got.n == 3 >= es.RANK_MIN_N
    assert got.reportable


def test_agreement_over_two_sites_is_still_refused(licensed, tmp_path):
    """The record does not launder D-072's negative — n=2 stays unreportable."""
    small = rr.Record(manifest=rr.to_record(licensed).manifest,
                      cells=rr.to_record(licensed).cells[:2],
                      measured_bands=(0.0,), source_bands=(0.0,))
    rr.write(small, tmp_path / "a.json")
    assert rr.agreement(rr.read(tmp_path / "a.json"), small).rho is None


def test_same_tree_and_unlicensed_readings_are_flagged_incomparable(licensed,
                                                                    replicated):
    a = rr.to_record(licensed)
    assert rr.comparable(a, rr.to_record(replicated)) == ()
    assert any("same" in why or "tree" in why for why in rr.comparable(a, a))


def test_declared_denominator_mismatch_is_flagged(licensed):
    a = rr.to_record(licensed, denominator=rr.DENOM_BOTH)
    b = rr.to_record(licensed, denominator=rr.DENOM_MEASURED)
    assert any("denominators differ" in why for why in rr.comparable(a, b))


# --------------------------------------------------------------------------
# Q-079 — both denominators, from one file
# --------------------------------------------------------------------------


def test_both_denominators_are_derivable_from_one_record(licensed):
    """The record does not have to pick; it has to declare."""
    record = rr.to_record(licensed)
    both = record.ratios(rr.DENOM_BOTH)
    measured_only = record.ratios(rr.DENOM_MEASURED)
    # source frame is stationary in this fixture, so the two agree here...
    assert both == measured_only
    # ...and the parameter is still real: RatioGrade's control sums the frames.
    assert record.grades[0].control == (record.cells[0]["measured_delta"]
                                        + record.cells[0]["source_delta"])


def test_a_moving_source_frame_separates_the_two_denominators(licensed):
    record = rr.to_record(licensed)
    cells = tuple({**c, "source_delta": 100} for c in record.cells)
    moved = rr.Record(manifest=record.manifest, cells=cells,
                      measured_bands=record.measured_bands,
                      source_bands=record.source_bands)
    assert moved.ratios(rr.DENOM_BOTH) != moved.ratios(rr.DENOM_MEASURED)


def test_unknown_denominator_is_refused(licensed):
    with pytest.raises(ValueError, match="unknown denominator"):
        rr.to_record(licensed).ratios("gap/anything")


# --------------------------------------------------------------------------
# Manifest — what the file has to say about itself
# --------------------------------------------------------------------------


def test_manifest_carries_the_tree_and_k(licensed, replicated):
    assert rr.to_record(licensed).manifest.k == 2
    assert rr.to_record(replicated).manifest.k == 3
    assert rr.to_record(licensed).manifest.tree == "t0"


def test_an_unlicensed_reading_records_the_empty_tree_and_keeps_its_frames():
    """A batch that moved is still worth a file — with its verdict intact."""
    disagreements = (("a._pure", 9600, 9814),)
    drifts = (_drift("a._pure", 9600, 9600),)
    trees = ("t0", "t0", "t1", "t1")
    reading = es.LicensedReading(
        trees=trees, disagreements=disagreements, measured_drifts=drifts,
        source_drifts=drifts,
        attributions=es.attribute_two_frame(disagreements, drifts, drifts,
                                            trees=trees))
    record = rr.to_record(reading)
    assert record.manifest.licensed is False
    assert record.manifest.tree == ""
    assert record.manifest.trees == trees
    assert record.cells[0]["verdict"] == es.ATTR_TRANSPORTED


def test_the_seed_field_says_unseeded_rather_than_omitting_itself(licensed):
    assert "unseeded" in rr.to_record(licensed).manifest.entropy


def test_bands_are_a_list_at_k2_as_well_as_k3(licensed, replicated):
    """One field shape, so the band's own spread stays comparable across k."""
    assert len(rr.to_record(licensed).measured_bands) == 1
    assert len(rr.to_record(replicated).measured_bands) == 3


# --------------------------------------------------------------------------
# What the format does and does not repair
# --------------------------------------------------------------------------


def test_the_format_would_have_carried_every_dropped_cell():
    missing = pr.missing()
    assert missing, "published_ratios should still name the dropped cells"
    assert rr.would_have_carried(missing) == missing


def test_coverage_keyed_on_stored_fields_alone_under_reports():
    """The bug this cycle wrote and then measured, pinned so it stays measured.

    ``gap`` is a property, not a stored field, and two of the sixteen dropped
    cells were published as ``gap``.  A coverage check over
    :data:`reading_record.CELL_FIELDS` therefore reports 14/16 while the format
    can in fact answer for all sixteen.  Pinned rather than deleted because the
    same shape recurs wherever a record stores primitives and prose quotes
    derivations.
    """
    missing = pr.missing()
    stored_only = tuple(m for m in missing if m[2] in rr.CELL_FIELDS)
    assert len(stored_only) < len(missing)
    assert {m[2] for m in missing} - set(rr.CELL_FIELDS) == {"gap"}
    assert "gap" in rr.DERIVED_FIELDS


# --------------------------------------------------------------------------
# The scan's own blind spot, found by writing an ordinary constant
# --------------------------------------------------------------------------


_CONCATENATED = '''
A = tuple(("x",))
B = tuple(("y",))
BOTH = A + B


def narrows(items):
    return tuple(i for i in items if i in BOTH)
'''

_WRAPPED = _CONCATENATED.replace("BOTH = A + B", "BOTH = tuple(A + B)")


def test_the_scan_is_blind_to_a_concatenated_registry(tmp_path):
    """One registry, two spellings, one visible — measured, not argued.

    :func:`guard_reflexivity._is_set_valued` decides registry-hood from the
    constant's **initializer form**.  ``A + B`` is a ``BinOp`` of two names, so a
    filter against it is not a guard as far as the scan is concerned;
    ``tuple(A + B)`` is a :data:`guard_reflexivity._SET_CALLS` call over the same
    value and is.  D-072 found the same shape at the ``&`` operator and read it
    as a fact about operators; it is a fact about **forms**, and this is the
    second instance in two cycles.

    Worse than the ``&`` case in one respect: concatenating two derived
    registries is how a registry composed of other registries is normally
    written, so the blind spot sits on the idiomatic spelling rather than an
    unusual one.  :data:`reading_record.CARRIED_FIELDS` carries the ``tuple(...)``
    wrapper for exactly this reason.
    """
    from eval.mppi_sandbox import guard_reflexivity as gr
    def scan(src: str) -> set[str]:
        path = tmp_path / f"m{abs(hash(src))}.py"
        path.write_text(src)
        return {g.name for g in gr._guards_in(path)}

    assert scan(_CONCATENATED) == set()
    assert scan(_WRAPPED) == {"narrows"}


def test_making_the_registry_visible_required_giving_it_a_watcher():
    """The second-order cost, pinned because it is the interesting half.

    A visible registry that nothing enumerates is an *unwatched allow-list* —
    D-047's exact state — so the fix for the blind spot immediately created the
    hole :func:`guard_reflexivity.unwatched_exemptions` reports, and
    :func:`reading_record.uncarried_fields` had to be written to close it.  The
    watcher's exempting set is ``DERIVED`` on purpose: a registry watched by a
    second copy of itself is what D-045 found short.
    """
    from eval.mppi_sandbox import guard_reflexivity as gr
    pool = gr.guards()
    assert gr.exemption_watchers(pool)["CARRIED_FIELDS"] == (
        "reading_record.uncarried_fields",)
    assert "CARRIED_FIELDS" not in gr.unwatched_exemptions(pool)
    assert rr.uncarried_fields() == ()


def test_the_watcher_bites_if_a_carried_field_stops_round_tripping():
    """An empty watcher is a clearance only if it could have been non-empty."""
    original = rr.CARRIED_FIELDS
    try:
        rr.CARRIED_FIELDS = original + ("a_field_no_cell_supplies",)
        assert rr.uncarried_fields() == ("a_field_no_cell_supplies",)
    finally:
        rr.CARRIED_FIELDS = original


def test_this_modules_registry_is_visible_to_the_scan():
    """The consequence: :func:`reading_record.would_have_carried` is in the pool.

    A guard that filters against a registry and is invisible to the registry of
    guards is D-047's defect verbatim.  Fixing the spelling rather than
    documenting the miss is the only version of this that is not the same bug.
    """
    from eval.mppi_sandbox import guard_reflexivity as gr
    names = {g.qualname for g in gr.guards()}
    assert "reading_record.would_have_carried" in names


def test_but_it_recovers_none_of_them():
    """The honest counterpart, pinned so the happy number is never quoted alone."""
    assert rr.unrecoverable(pr.missing()) == pr.missing()
    assert len(rr.unrecoverable(pr.missing())) == len(pr.missing())


# --------------------------------------------------------------------------
# The ordering's own control (SCHEMA 2)
# --------------------------------------------------------------------------


def test_every_replicate_gives_a_gap_not_just_the_first(replicated):
    """k replicates were spent entirely on the denominator until now.

    ``replicated_reading`` paired ``(A1, M1)`` for the gap and used the other
    2(k-1) runs only to widen the frames' bands, so the numerator stayed at n=1
    while the control got replicated.  Every pair is a gap by the same pairing
    D-070 fixed; this asserts they all arrive.
    """
    per = replicated.replicate_attributions
    assert len(per) == replicated.k
    assert tuple(a.site for a in per[0]) == tuple(a.site for a in per[1])
    assert per[0] != per[1]


def test_the_replicates_share_one_denominator(replicated):
    """Same controls under every numerator, or the ranking compares two scores."""
    per = replicated.replicate_attributions
    for attributions in per[1:]:
        assert ([(a.measured_delta, a.source_delta) for a in attributions]
                == [(a.measured_delta, a.source_delta) for a in per[0]])


def test_the_ordering_control_is_c_k_2_agreements_on_one_tree(replicated):
    """D-071's (c) finally has the control it was published without.

    Three replicates give three pairs; the fixture makes replicate 1 swap the
    top two sites and replicate 2 restore them, so the agreements are not all
    +1 and the statistic is demonstrably reading the data.
    """
    control = replicated.ordering_control
    assert len(control) == 3
    assert all(a.n == 3 for a in control)
    assert [round(a.rho, 3) for a in control] == [0.5, 1.0, 0.5]


def test_an_ordering_that_disagrees_with_itself_is_visible(replicated):
    """The falsification path, stated as a test rather than as a hope.

    A cross-tree rho only means something against this number.  If a same-tree
    batch cannot reproduce its own ordering, no cross-tree reading of it is
    evidence of structure — so the control has to be able to come back low, and
    this pins that it can.
    """
    assert any(a.rho < 1.0 for a in replicated.ordering_control)


def test_the_ordering_control_survives_the_round_trip(replicated, tmp_path):
    """The reason SCHEMA went to 2: off disk, no re-run, same answer."""
    rr.write(rr.to_record(replicated), tmp_path / "r.json")
    loaded = rr.read(tmp_path / "r.json")
    assert loaded.ordering_control == replicated.ordering_control


def test_replicate_cells_are_checked_for_grader_fields_too(replicated, tmp_path):
    """A partial parse in the replicates is refused exactly like one in ``cells``.

    Otherwise the schema bump would have created a second, unguarded copy of the
    surface the original check exists to protect.
    """
    path = tmp_path / "r.json"
    rr.write(rr.to_record(replicated), path)
    payload = json.loads(path.read_text())
    payload["replicates"][1][0].pop("source_delta")
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="missing grader fields"):
        rr.read(path)


def test_a_two_run_reading_reports_no_ordering_control(licensed, tmp_path):
    """Absent, not zero — a k=2 reading has one gap and cannot answer this.

    :class:`exclusion_scope.LicensedReading` has no replicates to give, and the
    empty tuple says so.  Reporting 0 (or 1) here would be the record asserting
    a measurement nobody took, which is the defect the whole module exists
    against.
    """
    rr.write(rr.to_record(licensed), tmp_path / "r.json")
    assert rr.read(tmp_path / "r.json").ordering_control == ()


def test_schema_1_files_are_refused_rather_than_read_without_replicates(
        replicated, tmp_path):
    """``cells`` narrowed in meaning from "the reading" to "replicate 0".

    That is why this is a bump and not an addition: a SCHEMA 1 file parsed under
    SCHEMA 2 would silently report an empty ordering control for a reading that
    may well have had replicates, which reads as "measured and found nothing".
    """
    path = tmp_path / "r.json"
    rr.write(rr.to_record(replicated), path)
    payload = json.loads(path.read_text())
    payload["schema"] = 1
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="unsupported record schema"):
        rr.read(path)


def test_gap_spread_prices_the_premise_under_d069(replicated):
    """A magnitude's movement with the tree held fixed, per site.

    D-069 read cross-tree magnitude ratios of 0.31–1.67 as evidence that
    transport voids a magnitude.  The premise is that a magnitude holds still
    when nothing is edited; this reports whether it does.
    """
    spread = replicated.replicate_attributions and rr.to_record(
        replicated).gap_spread
    assert [s[0] for s in spread] == sorted(
        [s[0] for s in spread], key=lambda site:
        -next(r[3] for r in spread if r[0] == site))
    assert all(lo <= hi and ratio == hi / lo
               for _, lo, hi, ratio in spread)


def test_gap_spread_is_empty_without_replicates(licensed):
    """No replicates, no control — absent rather than 1.0."""
    assert rr.to_record(licensed).gap_spread == ()
