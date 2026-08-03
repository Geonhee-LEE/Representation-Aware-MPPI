"""Q-068: how much of a probe's liveness act is derivable from the guard's code?

The headline numbers are pinned rather than described, because the whole point
of the exercise is the *fraction*, and a fraction that drifts silently is the
D-048 defect this package keeps re-finding.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import guard_direction as gd
from eval.mppi_sandbox import guard_reflexivity as gr
from eval.mppi_sandbox import liveness_derivation as ld
from eval.mppi_sandbox import probe_reach as pr


@pytest.fixture(scope="module")
def scored() -> tuple[ld.Recipe, ...]:
    return ld.recipes()


@pytest.fixture(scope="module")
def executed(tmp_path_factory) -> tuple[ld.Liveness, ...]:
    return ld.validated(workdir=tmp_path_factory.mktemp("liveness"))


# --------------------------------------------------------------------------
# the census is a partition of the addressable population
# --------------------------------------------------------------------------


def test_census_partitions_the_root_addressable_pool(scored):
    """Every addressable guard is scored exactly once, at exactly one layer.

    Pinned as a partition for D-052's reason: a layer rule that stops matching
    must not be able to quietly shrink the population the fraction is over.
    """
    counts = ld.census(scored)
    assert sum(counts.values()) == len(scored) == len(pr.root_addressable())
    assert {r.guard for r in scored} == {g.qualname for g in pr.root_addressable()}


def test_derivable_fraction_is_four_of_sixteen(scored):
    """The measurement Q-068 asked for, before any repair is shipped."""
    counts = ld.census(scored)
    assert counts == {
        ld.ORIGIN_DERIVED: 4,
        ld.ORIGIN_NO_SCOPE: 0,
        ld.ORIGIN_NO_REGISTRY: 9,
        ld.ORIGIN_NOT_PATHS: 3,
    }


def test_scope_is_the_layer_that_loses_nobody(scored):
    """``acts_of`` — the thing Q-068 proposed deriving from — never fails.

    Zero ``NO_SCOPE`` is the finding, not a vacuous pass: the part of the act
    that ``acts_of`` supplies is recoverable for **all 16**, and the fraction
    falls to 4 entirely at the two layers ``acts_of`` says nothing about.
    """
    assert all(r.scope for r in scored)
    assert ld.census(scored)[ld.ORIGIN_NO_SCOPE] == 0


# --------------------------------------------------------------------------
# the precedence table, and its mirror
# --------------------------------------------------------------------------


def test_precedence_ranks_every_scope_the_pool_exhibits():
    """:data:`SCOPE_PRECEDENCE` is a table; this is the population it is short on."""
    assert ld.unranked_scopes() == ()


def test_precedence_covers_the_guard_reflexivity_vocabulary():
    """It ranks the scope vocabulary itself, so pool growth cannot outgrow it."""
    vocabulary = {gr.SCOPE_INDEX, gr.SCOPE_WORKTREE, gr.SCOPE_NAMESET,
                  gr.SCOPE_COMMIT, gr.SCOPE_UNKNOWN}
    assert set(ld.SCOPE_PRECEDENCE) == vocabulary - {gr.SCOPE_UNKNOWN}


# --------------------------------------------------------------------------
# agreement with the hand-written acts — n = 2, and it says so
# --------------------------------------------------------------------------


def test_derivation_reproduces_both_typed_acts():
    """Both existing probes are re-derived exactly, scope and membership.

    This is the evidence that the derivation is not merely plausible — and the
    ground truth for it has **n = 2**, the same smallness D-053 found in the
    table being replaced.  :func:`test_derivation_beats_the_typed_table_by_one`
    is the honest counterweight.
    """
    rows = ld.agrees_with_typed()
    assert set(rows) == set(gd.PROBES)
    assert all(row["agrees"] == "True" for row in rows.values())
    assert rows["local_only_audit.staged_declarations"]["derived"] == "INDEX/IN"
    assert rows["tree_provenance.undeclared_drift"]["derived"] == "WORKTREE/OUT"


# --------------------------------------------------------------------------
# executed, not asserted
# --------------------------------------------------------------------------


def test_two_derived_acts_do_not_wake_their_guard(executed):
    """``DERIVED`` is a census verdict; **two** of four survive execution.

    Two different failures, and they are worth keeping apart:

    ``pre_epoch_commits`` — ``DEAD``
        Recovers all three parts and still reads empty.  Its population is
        bounded by ``--until=<epoch>`` over ``origin/main..<ref>`` — a
        *temporal and topological* precondition that lives in neither
        :func:`guard_reflexivity.acts_of` (which gives the window) nor
        :class:`guard_reflexivity.Exemption` (which gives the registry).  A
        fourth part of a liveness act exists and nothing in either registry
        names it.
    ``unregistered_local_only`` — ``INERT``
        Recovers all three parts, and the act moves the reading by nothing at
        all.  It scored ``LIVE`` under the previous non-emptiness bar purely
        because the enriched fixture copies ``docs/`` in, so the guard already
        named ``docs/decisions.md`` and ``docs/deliberations.md`` before
        anything ran.  See :func:`ld.validate`.
    """
    assert len(executed) == 4
    assert sum(l.live for l in executed) == 2
    outcomes = {l.guard: l.outcome for l in executed}
    assert outcomes["local_only_audit.pre_epoch_commits"] == ld.LIVENESS_DEAD
    assert outcomes["local_only_audit.unregistered_local_only"] == ld.LIVENESS_INERT
    assert len(ld.unwoken(executed)) == 2


def test_the_inert_act_did_not_move_the_reading_by_one_element(executed):
    """The INERT verdict is a *stationary* reading, not a near-miss.

    Worth pinning separately from the outcome token: an act that moved the
    population but named the wrong element would also score ``INERT``, and that
    would be a different (and much smaller) defect than the one measured.  Here
    the before and after readings are the same size and the act's subject is in
    neither, so the derivation contributed nothing the fixture did not already
    supply.
    """
    inert = next(l for l in executed
                 if l.guard == "local_only_audit.unregistered_local_only")
    assert inert.before == inert.reading == 2
    assert not inert.moved
    assert "does not name it" in inert.note


def test_the_dead_act_is_not_a_precedence_mistake(tmp_path):
    """It reads empty through **every** scope, so the table did not pick wrong.

    Worth separating: a ``DEAD`` verdict on a multi-scope guard is exactly what
    a wrong :data:`SCOPE_PRECEDENCE` entry would look like, and attributing it
    to the missing fourth part without checking would be D-032's misdiagnosis.
    """
    import dataclasses

    name = "local_only_audit.pre_epoch_commits"
    guard = {g.qualname: g for g in pr.root_addressable()}[name]
    base = next(r for r in ld.recipes() if r.guard == name)
    for scope in ld.SCOPE_PRECEDENCE:
        alt = dataclasses.replace(base, scope=scope)
        assert not ld.validate(alt, tmp_path / scope, guard).live


def test_the_derivation_yields_nothing_over_the_typed_table(executed):
    """Net yield over the hand-written table: **zero**, once the bar is right.

    The number has now been read three ways, each smaller than the last, and the
    shrinkage is the finding rather than an embarrassment:

    ===========================  =====  =========================================
    reading                      yield  what it was actually measuring
    ===========================  =====  =========================================
    D-053 ``reach_gap``          6      guards the fixture can *read*
    D-054 executed, non-empty    1      …that also read non-empty afterwards
    this, executed, membership   0      …whose reading the act actually produced
    ===========================  =====  =========================================

    The guards that survive are exactly the two somebody wrote by hand.  Q-068's
    proposal — derive the probe table instead of typing it — is answered in the
    negative on the population it was proposed over, and answered by execution
    rather than by argument.
    """
    live = {l.guard for l in executed if l.live}
    assert live == set(gd.PROBES)
    assert live - set(gd.PROBES) == set()


# --------------------------------------------------------------------------
# the parts, individually
# --------------------------------------------------------------------------


def test_path_members_asks_the_filesystem_not_the_spelling():
    """A ``"/"``-contains test would accept a claim id and reject ``TODO.md``."""
    assert ld.path_members(("TODO.md", "STATE.md")) == ("TODO.md", "STATE.md")
    assert ld.path_members(("calibrated/other", "no/such/file.txt")) == ()


def test_not_paths_layer_names_a_real_registry(scored):
    """``NOT_PATHS`` guards resolve their constant — they just aren't paths."""
    rows = [r for r in scored if r.origin == ld.ORIGIN_NOT_PATHS]
    assert {r.registry for r in rows} == {
        "DEGENERATE_READINGS", "SCOPED_CLAIMS", "TEMPERATURE_RELEVANT"}
    assert all("0 name a path" in r.note for r in rows)


def test_underivable_recipes_refuse_to_act(scored):
    """No silent no-op act: a non-derived recipe raises rather than doing nothing."""
    dud = next(r for r in scored if not r.derived)
    with pytest.raises(ld.DerivationError):
        dud.act(Path("/tmp/does-not-matter"))
