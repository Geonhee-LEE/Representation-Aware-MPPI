"""Q-065 (b): the direction of a guard's blindness, executed rather than inferred.

D-049 reported that :func:`gr.revocable` matches **twice** where the failure it
describes occurs **once**, and filed the direction question as Q-065.  Every
assertion here is a reading taken in a throwaway git repository, because the
whole point of the question is that the answer is not in the AST — a structural
test of a structural claim would be assuming the conclusion.

The sharp result is :func:`test_revocables_implied_mechanism_never_fires`:
across all ten (guard × declared path) readings, the collapse ``revocable``
models happens **zero** times.  It is not that the model is rare, it is that a
second sufficient cause — the exemption — always fires first.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import guard_direction as gd
from eval.mppi_sandbox import guard_reflexivity as gr
from eval.mppi_sandbox.tree_provenance import DECLARED_LOCAL_ONLY

WORKING = "local_only_audit.staged_declarations"
BLIND = "tree_provenance.undeclared_drift"


@pytest.fixture(scope="module")
def obs(tmp_path_factory):
    return gd.readings(tmp_path_factory.mktemp("directions"))


@pytest.fixture(scope="module")
def mechs(tmp_path_factory):
    return gd.mechanisms(tmp_path_factory.mktemp("mechanisms"))


# --------------------------------------------------------------------------
# the probe table's population is derived, even though the table is typed
# --------------------------------------------------------------------------


def test_every_revocable_guard_has_a_probe():
    """A ``DIFFERENCE`` guard nobody executed is the state Q-065 was filed about.

    The table in :data:`gd.PROBES` is hand-written — Q-065 (a)'s objection, which
    (b) does not escape — but its *completeness* is checked against the scan, so
    D-045's silent-omission mode is closed even though the entries are typed.
    """
    assert gd.unprobed_revocable() == ()


def test_no_stale_probes():
    """The mirror: an entry for a guard that changed shape would go unnoticed.

    This fired for real during D-050.  Extracting ``staged_changes`` out of
    ``staged_declarations`` dropped the guard out of the scan entirely, and this
    check is what said so.
    """
    assert gd.stale_probes() == ()


def test_the_probed_population_is_exactly_the_revocable_one():
    assert set(gd.PROBES) == {g.qualname for g in gr.revocable()}


# --------------------------------------------------------------------------
# liveness — so SILENT means blind, not dead
# --------------------------------------------------------------------------


@pytest.mark.parametrize("qualname", sorted(gd.PROBES))
def test_liveness_holds_for_every_probe(qualname, tmp_path):
    assert gd.check_liveness(qualname, tmp_path)


def test_liveness_refuses_an_act_that_changes_nothing(tmp_path):
    """The probe's own first self-catch, pinned.

    ``git add`` on a path identical to ``HEAD`` stages nothing, so the first
    draft's liveness act was a no-op and read empty.  An act that moves nothing
    measures nothing — D-048's "filter site with no population", one layer over.
    If this check is ever loosened, a dead guard scores ``SILENT`` and the
    finding becomes unfalsifiable.
    """
    probe = gd.PROBES[WORKING]
    noop = gd.Probe(read=probe.read, liveness=lambda root: None,
                    liveness_note="no-op", read_unexempted=probe.read_unexempted,
                    liveness_subject=probe.liveness_subject)
    original = gd.PROBES[WORKING]
    gd.PROBES[WORKING] = noop
    try:
        with pytest.raises(gd.ProbeError, match="did not put"):
            gd.check_liveness(WORKING, tmp_path)
    finally:
        gd.PROBES[WORKING] = original


def test_liveness_refuses_a_reading_the_act_did_not_produce(tmp_path):
    """The bar is membership, not non-emptiness — D-055's correction.

    An act that leaves a *non-empty* reading it had no part in used to pass.
    On the two probes here that never mattered, because the base fixture reads
    empty for both before their act; it mattered the moment
    :func:`liveness_derivation.validate` ran a third guard on a fixture that
    copies real surfaces in.  Simulated here rather than described: an act that
    perturbs the guard's population *without* touching the declared subject
    leaves a reading of 1 and must still be refused.
    """
    probe = gd.PROBES[WORKING]

    def acts_elsewhere(root):
        other = next(p for p in DECLARED_LOCAL_ONLY if p != probe.liveness_subject)
        (root / other).write_text("liveness edit\n", encoding="utf-8")
        gd._git(root, "add", other)

    loud = gd.Probe(read=probe.read, liveness=acts_elsewhere,
                    liveness_note="stages a path that is not the subject",
                    read_unexempted=probe.read_unexempted,
                    liveness_subject=probe.liveness_subject)
    original = gd.PROBES[WORKING]
    gd.PROBES[WORKING] = loud
    try:
        with pytest.raises(gd.ProbeError, match="did not put"):
            gd.check_liveness(WORKING, tmp_path)
    finally:
        gd.PROBES[WORKING] = original


# --------------------------------------------------------------------------
# the verdicts
# --------------------------------------------------------------------------


def test_readings_cover_every_guard_times_every_declared_path(obs):
    assert len(obs) == len(gd.PROBES) * len(DECLARED_LOCAL_ONLY)
    assert {d.path for d in obs} == set(DECLARED_LOCAL_ONLY)


def test_the_working_guard_names_its_own_offence(obs):
    """D-049's fix, re-read as a direction rather than as one hand-run case."""
    got = [d for d in obs if d.guard == WORKING]
    assert len(got) == len(DECLARED_LOCAL_ONLY)
    for d in got:
        assert d.verdict == gd.VERDICT_NAMES, d
        assert d.after == (d.path,), d


def test_the_blind_guard_is_silent_on_every_declared_path(obs):
    """D-047's defect, and it is not path-specific — all five, not just STATE.md."""
    got = [d for d in obs if d.guard == BLIND]
    assert len(got) == len(DECLARED_LOCAL_ONLY)
    for d in got:
        assert d.verdict == gd.VERDICT_SILENT, d
        assert d.before == () and d.after == (), d


def test_fails_quietly_is_exactly_the_blind_guard(tmp_path):
    quiet = gd.fails_quietly(tmp_path)
    assert {d.guard for d in quiet} == {BLIND}
    assert len(quiet) == len(DECLARED_LOCAL_ONLY)


# --------------------------------------------------------------------------
# D-050's headline
# --------------------------------------------------------------------------


def test_revocables_implied_mechanism_never_fires(obs):
    """``revocable`` models a collapse that is observed **zero** times.

    Q-065 asked whether direction is recoverable from the shape.  It is worse
    than "no": the mechanism the shape names is not merely un-signed, it is
    **unreachable**.  Deleting this assertion restores the reading that made
    D-049 describe the failure as the population being emptied by the act.
    """
    assert [d for d in obs if d.quieter] == []


def test_the_blind_guard_does_not_move_at_all(obs):
    """Not quieter — *unchanged*.  The exemption emptied it before the offence."""
    assert all(not d.moved for d in obs if d.guard == BLIND)
    assert all(d.moved for d in obs if d.guard == WORKING)


def test_the_collapse_is_masked_by_the_exemption(mechs):
    """Both causes are sufficient, so the one in the AST is never the observed one."""
    blind = [m for m in mechs if m.guard == BLIND]
    assert len(blind) == len(DECLARED_LOCAL_ONLY)
    for m in blind:
        assert m.blinded_by_exemption, m
        assert m.blinded_by_collapse, m
        assert m.masked, m


def test_the_working_guard_is_blinded_by_neither_cause(mechs):
    for m in (m for m in mechs if m.guard == WORKING):
        assert not m.blinded_by_exemption, m
        assert not m.blinded_by_collapse, m
        assert not m.masked, m


def test_suppressing_the_exemption_reveals_the_offence(mechs):
    """The control that makes ``blinded_by_exemption`` mean something.

    With the allow-list empty the offending path *is* in the population before
    the offence — so the guard's silence is the exemption's doing and not an
    artifact of the scratch repo having nothing to see.
    """
    for m in (m for m in mechs if m.guard == BLIND):
        assert m.path in m.raw_before, m
        assert m.raw_after == (), m
