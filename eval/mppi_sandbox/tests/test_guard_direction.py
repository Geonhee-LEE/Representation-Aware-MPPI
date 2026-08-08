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
CLAIMS = "cycle_artifacts.unsupported"


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


def test_the_probed_population_is_exactly_the_revocable_collections():
    assert set(gd.PROBES) == {g.qualname for g in gr.revocable_collections()}


def test_the_obligation_is_narrower_than_the_census_and_says_so():
    """The exclusion is one guard, it is named, and it is derived.

    ``revocable`` is a reading of the census pool, which counts visible
    *spellings* (D-072/D-073) — so it contains ``cycle_artifacts.report``, a
    renderer whose printed tallies come from a difference.  The probe obligation
    inherited that population and therefore demanded an executed "does the
    reading name the offence" of a function that returns a string.  There is no
    honest way to satisfy it: the only reading a renderer has is its text, and
    recovering a population by parsing text is a second statement of the rule —
    D-045's and D-047's shape exactly.
    """
    assert gd.unprobeable_revocable() == ("cycle_artifacts.report",)
    excluded = set(gd.unprobeable_revocable())
    assert excluded.isdisjoint(gd.PROBES)
    assert excluded | {g.qualname for g in gr.revocable_collections()} \
        == {g.qualname for g in gr.revocable()}


def test_the_exclusion_is_not_special_cased_to_the_guard_it_drops():
    """A predicate justified only by the member it removes is a special case.

    Eight of the pool's guards have a scalar reading and only one of them is
    revocable, so the rule was not reverse-engineered from
    ``cycle_artifacts.report`` — it has seven other instances that this
    obligation never reached anyway.

    8 -> **10** (D-114), and neither entrant is a new rule: D-112 split
    ``cycle_artifacts.strand_report`` out of the query so the *rendering* could
    be tested without a scratch repo, and D-113 added ``cycle_wallclock.main``.
    Both are renderers returning one string, which is what ``scalar_readings``
    selects for.  The margin the assertion is really about — instances outside
    the guard the exclusion drops — widens from seven to nine, so the
    special-case worry it was written against gets further away, not closer.

    10 -> **11** (D-136): ``lam_window_key.attribution`` grades one factor and
    returns one verdict, so it is the same renderer shape as the other ten and
    joins for the same reason.  The margin widens to ten.

    11 -> **12** (D-146): ``calibrate_lam.merge_tables`` returns the merged
    table as one string, which is the same renderer shape again — it joins for
    the spelling, not for being a guard, which is exactly the point this pin
    keeps making.  The margin widens to eleven.
    """
    scalar = {g.qualname for g in gr.scalar_readings()}
    assert len(scalar) == 12, sorted(scalar)
    assert "cycle_artifacts.report" in scalar
    assert scalar - {g.qualname for g in gr.revocable()}, \
        "the rule must have instances outside the one guard it excludes here"


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


def test_readings_cover_every_guard_times_its_own_subjects(obs):
    """The subject space is the guard's, not the module's.

    This asserted ``len(PROBES) * len(DECLARED_LOCAL_ONLY)`` while every probed
    guard enforced D-011, and two guards enforcing one rule cannot tell "the
    paths this rule covers" from "the paths every rule covers".  The third guard
    is about journal files; under the old loop it would have been handed
    ``STATE.md`` and scored blind to an offence that is not its.
    """
    assert len(obs) == sum(len(p.subjects) for p in gd.PROBES.values())
    for qualname, probe in gd.PROBES.items():
        assert {d.path for d in obs if d.guard == qualname} == set(probe.subjects)
    assert set(gd.PROBES[WORKING].subjects) == set(DECLARED_LOCAL_ONLY)


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


def test_fails_quietly_is_the_blind_guard_plus_the_intersections_known_cost(tmp_path):
    """Two guards go quiet now, and the second one was **predicted in prose**.

    D-105 argued that ``unsupported``'s intersection of two dating keys can be
    silenced by a row appended retroactively — the ``records`` key credits the
    silent cycle with a row it did not write, the keys disagree, and the
    intersection publishes nothing.  That argument is now a reading taken in a
    scratch repository with the two dates pinned apart, which is the difference
    between a caveat and a measurement.
    """
    quiet = gd.fails_quietly(tmp_path)
    assert {d.guard for d in quiet} == {BLIND, CLAIMS}
    assert len([d for d in quiet if d.guard == BLIND]) == len(DECLARED_LOCAL_ONLY)
    assert [d.path for d in quiet if d.guard == CLAIMS] == [gd.CA_MASKED]


def test_the_claims_guard_names_the_offence_both_keys_agree_on(obs):
    """The other half: when neither key is fooled, the guard is loud."""
    got = [d for d in obs if d.guard == CLAIMS and d.path == gd.CA_PLAIN]
    assert len(got) == 1
    assert got[0].verdict == gd.VERDICT_NAMES
    assert got[0].before == () and got[0].after == (gd.CA_PLAIN,)


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


def test_a_third_blindness_mechanism_the_two_flags_cannot_express(mechs):
    """The exemption can also remove an offence it did **not** precede.

    ``blinded_by_exemption`` reads ``raw_before`` — was the subject already in
    the population before the act — and that is the right moment only when the
    permitted state carries the subject, which an unstaged edit does and a
    journal that has not yet lied does not.  So on ``cycle_artifacts.unsupported``
    both existing flags read ``no`` while the guard is demonstrably silent, and
    the reading that says why is the one taken *after*: the offence enters the
    single-key population and the second key's agreement removes it.
    """
    masked = [m for m in mechs if m.guard == CLAIMS and m.path == gd.CA_MASKED]
    assert len(masked) == 1
    m = masked[0]
    assert m.exempted_away, m
    assert not m.blinded_by_exemption and not m.blinded_by_collapse, m
    assert m.path in m.raw_after and m.path not in m.exempt_after, m

    plain = [m for m in mechs if m.guard == CLAIMS and m.path == gd.CA_PLAIN]
    assert plain and not plain[0].exempted_away, plain


def test_exempted_away_is_disjoint_from_the_masked_collapse(mechs):
    """The three mechanisms are distinguishable, not three names for one reading."""
    assert not any(m.exempted_away and m.masked for m in mechs)
    assert sum(m.exempted_away for m in mechs) == 1
    assert sum(m.masked for m in mechs) == len(DECLARED_LOCAL_ONLY)


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
