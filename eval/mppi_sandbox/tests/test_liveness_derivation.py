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
from eval.mppi_sandbox import git_surface
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
    """The measurement Q-068 asked for, before any repair is shipped.

    ``NO_REGISTRY`` 9 -> 10 (D-089): ``nested_suite_cost.unresolved_sites``
    narrows against ``resolved``, a set built from ``suite_runners()`` inside
    the function — derivable, but not a module-level registry, so it lands in
    the same bucket as the other nine. Q-069's split (which layer actually
    blocks each of these) is still unanswered and this makes the tenth case.

    ``NO_REGISTRY`` 10 -> 11 (D-090): ``nested_subject.subject_files`` narrows
    against ``skip``, a set built from the ``excluded`` **parameter** inside the
    function. Same bucket, and it sharpens Q-069 rather than merely enlarging
    it: the previous ten are derivable-in-principle from something module-level,
    while this one's exempting set arrives through the call signature, so no
    module-scoped derivation could reach it at all. The other new member,
    ``nested_subject.spawners``, narrows against its own accumulator and lands
    here too — but that one is genuinely derivable, which is why the bucket
    gaining two members moves the count by one axis and the *question* by
    another.
    ``NO_REGISTRY`` 11 -> 13 and the population 16 -> **22** (D-106).  The jump
    is not two new functions; it is :mod:`cycle_artifacts` becoming *addressable*
    at all.  :func:`probe_reach.root_addressable` selects guards a scratch-repo
    fixture can point at, and until this cycle that module resolved its journal
    and results directories from ``__file__`` — so six of its guards were
    unreachable for a reason that had nothing to do with what they filter.
    Threading a ``root`` through, which the probe needed anyway, admitted all
    six.  The derivable numerator is **unchanged at 4**: none of the six carries
    a ``TYPED`` registry, so the fraction went 4/16 to 4/22 without Q-068's
    answer moving at all.

    ``NO_REGISTRY`` 13 -> **15**, population 22 -> **24** (D-107), and one of the
    two entrants is the D-106 phenomenon again: :func:`inert_surface.reprobe` is
    genuinely new, but :func:`inert_surface.probe` is **not** — it gained a
    ``tests`` subset parameter and one guard clause, which changed nothing about
    what it computes and everything about whether the scan can see it narrowing.
    Second instance in two cycles of a pool member entering by **spelling**, and
    it is worth stating plainly that this is the price of a syntactic census
    (D-072/D-073) rather than a defect in it: the alternative reads intent.  The
    numerator is again **unchanged at 4** — neither entrant carries a ``TYPED``
    registry, both narrow against a set built inside the call.

    ``NO_REGISTRY`` 15 -> **16**, population 24 -> **25** (D-114).  The entrant
    is :func:`cycle_artifacts.unwatched_strandings`, and it is the D-106
    phenomenon a third time in the same module: the function is not new — D-112
    shipped it — it became *addressable* only once a probe existed to point a
    fixture at it, which is what this cycle registered.  The numerator is
    **unchanged at 4** for the fourth consecutive cycle: its exempting set is
    ``{c.path for c in unsupported(...)}``, a set comprehension built inside the
    call, so no module-scoped derivation could reach it.  Four cycles of the
    denominator moving and the numerator standing still is now the substantive
    reading of Q-068, and it is a stronger negative than the original 4/16.

    ``NO_REGISTRY`` 16 -> **17**, population 25 -> **26** (D-180).  The entrant
    is :func:`receipt_cost.scope`, and it arrived as a **refutation of its own
    cycle's prose**: the D-180 entry and the census pin both claimed "second-order
    cost is nil on both axes", reasoning that ``set(meta)`` is DERIVED from a call
    and so leaves ``unwatched_exemptions`` at five.  That half was right.  The
    other axis was asserted without being measured, and the suite refused it —
    the very property that makes the exemption *watched* (it is built inside the
    call, from ``guard_meta_suite()``) is what makes it **unreachable by any
    module-scoped derivation**, so it lands here.  D-073's cost and Q-068's
    numerator are the same fact read from two directions: an exemption computed
    at call time is watched by whatever watches the call, and for exactly that
    reason no registry names it.  The numerator is **unchanged at 4** for the
    fifth consecutive cycle.

    ``NO_REGISTRY`` 17 -> **18**, population 26 -> **27** (D-209).  The entrant
    is :func:`inert_surface.carried_drift`, the fourth consecutive hand-written
    entrant the derivation cannot reach — but it misses for a **third distinct
    reason**, which is the part worth pinning.  D-106/D-114 missed by
    *addressability* and D-107/D-180 by *spelling*; this one is addressable and
    unremarkably spelled, and still unreachable because its offence is a
    **content move under an unchanged name**.  Its key is a set of names, so the
    act vocabulary the derivation is written over has no token for "the bytes
    moved, the name did not" — there is nothing here for a module-scoped
    derivation to *find*, rather than something it merely cannot see.  The
    numerator is **unchanged at 4** for the sixth consecutive cycle, and three
    distinct miss-reasons standing behind one flat numerator is now the
    substance of Q-068's negative: 4/27 is not one obstacle repeated 23 times.

    ``NO_REGISTRY`` 18 -> **19**, population 27 -> **28** (D-214).  The entrant
    is :func:`quoted_counts.audit`, and unlike the last four it contributes **no
    new miss-reason** — which is why it is recorded in one paragraph rather than
    five.  Its exemption is ``{receipt.counts.get('passed', 0) for receipt in
    archived(root)}``: ``DERIVED``, keyed on a call, built at call time.  That is
    exactly D-180's mechanism, and the honest reading is that the third reason
    has now recurred rather than that a fourth has appeared.

    What *is* new is the subject.  Every prior entrant audits code; this one
    audits **prose** — journal-quoted pass counts — and it lands in the same
    bucket for the same reason, which says the recurrence is a property of how
    exemptions are *written* on this branch and not of what they are written
    about.  The numerator is **unchanged at 4** for the seventh consecutive
    cycle.

    ``NO_REGISTRY`` 19 -> **21** and ``NOT_PATHS`` 3 -> **4**, population 28 ->
    **31** (D-275/D-276).  Three entrants in one repair, from **two** cycles'
    modules — and the split is worth keeping, because the 06:00 journal booked
    all eight red pins to `window_axis_migration` and only one of these is
    that module's.  `window_axis_reach.enforcing_functions` and
    `window_axis_reach.consumers` (D-275) miss for the standard reason, no
    TYPED exemption naming a constant.  `window_axis_migration.sites` (D-276)
    is the ``NOT_PATHS`` entrant: its key is ``RESOLVERS``, whose three members
    are ``(module, attribute)`` pairs, so 0 of 3 name a path.

    The entrants say something the earlier five do not.  Each was written to
    **derive** its population from a sibling registry rather than type a second
    list — `sites` reads `window_axis_reach.RESOLVERS`, exactly the reuse this
    repo's conventions ask for — and that reuse is what lands it here: a
    derivation keyed on a registry of dotted names has nothing path-shaped to
    find.  The miss is a cost of the convention, not a lapse from it, which is
    why the repair is a count bump and not a fix.  The numerator is
    **unchanged at 4** for the eighth consecutive cycle.

    ``NO_REGISTRY`` 25 -> **27** (D-484): `lam_inertness.rung_support` and
    `lam_inertness.report`, entering as a pair — and they are the first entrants
    whose exemption set is **DERIVED rather than typed**.  Both narrow their
    population against ``inert_arms(scene)``, which is not a registry of dotted
    names but a *measurement*: eight controllers constructed and asked what
    temperature they return.  That is the shape this docstring has spent eleven
    cycles asking for, and it still scores ``NO_REGISTRY`` — because the scan
    looks for a resolvable registry, and a set produced by running the plant
    resolves to nothing at import time.  So the eleventh consecutive unmoved
    numerator is not another imitation of an underivable convention (D-479's
    reading, one entry down); it is the opposite case, a guard that took the
    *harder* and more honest route to its exemption and was scored identically.
    The lesson sharpens Q-069 rather than repeating it: ``NO_REGISTRY`` is not
    measuring whether a guard's exemption is principled, it is measuring whether
    the exemption is **static**, and those two properties are not the same axis.
    A derived exemption is strictly better evidence and strictly worse input.

    ``NO_REGISTRY`` 24 -> **25** (D-479): `baseline_matrix.scene_admission_gap`,
    the scene-axis counterpart written when D-477 closed the controller axis.
    It scores ``SCOPED_CLAIMS: 5 members, 0 name a path`` — the same shape its
    sibling `admission_gap` carries, which is the point worth recording. The two
    guards are *deliberately* perpendicular grains on one table, written a
    fortnight apart by different cycles, and the derivation scan cannot tell
    them apart at all: both narrow a set built inside the function against a
    population reached through a call. So the tenth consecutive unmoved
    numerator is not ten independent unlucky guards — here it is one guard
    **and its own intentional twin**, and the twin inherited the underivability
    without anyone choosing it. That is Q-069's re-reading (below) getting its
    cleanest instance: the convention propagates through imitation, which is how
    a codebase produces underivable guards by default.

    Found the expensive way, and the way is the finding. `census_preempt` was
    run twice at the stage and returned all-clean both times, because this
    census is in **neither** its eight covered censuses nor its ``UNCOVERED``
    line — the same enumeration gap D-478 hit with `assert_reach` one cycle
    earlier, now the second instance. A 745 s suite went red on this one line.

    ``NO_REGISTRY`` 22 -> **24** (D-473), and it is the first entry that moves
    this bucket by **two from one module**.  Both `lam_rollout.reaching_names`
    and `lam_rollout.compare` narrow against `ROLLOUT_PRIMITIVES`, which is a
    module-level literal and therefore *looks* like the TYPED registry this
    bucket exists to distinguish from — but the guards reach it through
    `qualified_primitives()`, a function, so no module-scoped derivation
    lands on it and the pair falls here.  That is the D-106 phenomenon for
    the fifth time and the sharpest instance yet: the registry is one hop
    away and the hop is what disqualifies it.  Q-068's fraction is unmoved at
    4 derivable; the denominator grows again, which is the negative reading
    D-114 called stronger than the original 4/16.

    ``NO_REGISTRY`` 21 -> 22 and ``NOT_PATHS`` 4 -> 5 (D-313): D-312's
    `extremum_reading` lands two guards in the addressable pool, and they split
    across *different* layers, which is the only interesting thing about them.
    ``scan_sites`` narrows an AST walk against no registry at all, so it joins
    the twenty-one.  ``sweep`` does have a module-level registry —
    ``SITE_CLASSES`` — but its keys are ``(module, function, expression)``
    tuples whose first element is a bare filename string, so a path-shaped
    derivation has nothing to match, exactly the convention cost the paragraph
    above describes.  ``unrepaired_hulls``, the third guard of that cycle, is
    not addressable at root and so is not in this partition at all.

    The numerator is **unchanged at 4** for the ninth consecutive cycle, and
    the denominator has now grown by 12 since Q-068 asked the question.  That
    ratio is itself the answer accumulating: nine cycles of new guards, none of
    them derivable, is no longer plausibly a run of bad luck about individual
    guards.  Q-069 should be re-read as asking why the *convention* produces
    underivable guards by default rather than which layer blocks each one.
    """
    counts = ld.census(scored)
    assert counts == {
        ld.ORIGIN_DERIVED: 4,
        ld.ORIGIN_NO_SCOPE: 2,
        ld.ORIGIN_NO_REGISTRY: 27,
        ld.ORIGIN_NOT_PATHS: 5,
    }


def test_scope_is_no_longer_the_layer_that_loses_nobody(scored):
    """The zero was a property of the pool, not of ``acts_of`` (D-106).

    This asserted ``NO_SCOPE == 0`` and read it as the finding: the part of the
    act :func:`gr.acts_of` supplies is recoverable for **all 16**, and the
    fraction falls to 4 entirely at the two layers ``acts_of`` says nothing
    about.  Every one of those 16 performed a git or filesystem operation
    somewhere in its own body, which is not a fact about the derivation — it is
    a fact about which guards a fixture could reach before
    :mod:`cycle_artifacts` took a ``root``.

    The two that now fall out are ``unsupported`` and ``unsupported_by``, whose
    bodies contain no act at all: they call two frames down to something that
    does.  So the honest statement is narrower than the old one and is kept as a
    *named* exclusion rather than a repaired zero — widening ``acts_of`` to
    follow calls is Q-067/D-052's rejected direction, and the cost of not
    widening it is exactly this: a purely-computational guard has no act to
    wake it through, and no depth limit is why.
    """
    lost = tuple(sorted(r.guard for r in scored if not r.scope))
    assert lost == ("cycle_artifacts.unsupported", "cycle_artifacts.unsupported_by")
    assert ld.census(scored)[ld.ORIGIN_NO_SCOPE] == len(lost)
    assert all(r.scope for r in scored if r.guard not in lost)


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

    D-106 adds a third typed probe the derivation reaches for and comes back
    empty-handed, so ``agrees_with_typed`` is now a strict subset of the table.
    The comparison it publishes is unchanged on the two it can make; what the
    third one shows is that the ground truth stayed at **n = 2** while the table
    went to three, which is the direction that makes the negative stronger
    rather than staler.

    D-114 adds a fourth for the same reason and with the same result.
    ``cycle_artifacts.unwatched_strandings`` was hand-probed this cycle; its
    offence is *writing a journal and not pushing it*, which is a commit the
    derivation has no act for, so it falls out at ``NO_SCOPE`` beside
    ``unsupported``.  Ground truth is still **n = 2** against a table of four.
    Two cycles ago the table beat the derivation by one; it now beats it by two,
    and the derivation has not reached a new guard since it was proposed.
    """
    rows = ld.agrees_with_typed()
    assert set(rows) < set(gd.PROBES)
    assert set(gd.PROBES) - set(rows) == {
        "cycle_artifacts.unsupported",
        "cycle_artifacts.unwatched_strandings",
        # D-209's `carried_drift` is the **fourth** consecutive hand-written
        # entrant the derivation cannot reach, and it misses for a third
        # distinct reason: its offence is neither a path-scoped edit nor a bare
        # commit but a *content move under an unchanged name*, which the act
        # vocabulary has no token for at all.  Ground truth stays n = 2 while
        # the table goes to 5 — the gap the proposal promised to close is now
        # widening once per cycle.
        "inert_surface.carried_drift",
    }
    assert all(row["agrees"] == "True" for row in rows.values())
    assert rows["local_only_audit.staged_declarations"]["derived"] == "INDEX/IN"
    assert rows["tree_provenance.undeclared_drift"]["derived"] == "WORKTREE/OUT"


# --------------------------------------------------------------------------
# executed, not asserted
# --------------------------------------------------------------------------


def test_two_derived_acts_do_not_wake_their_guard(executed):
    """``DERIVED`` is a census verdict; **two** of four survive execution.

    Two different failures, and they are worth keeping apart:

    ``pre_epoch_commits`` — ``ERROR`` (was ``DEAD``, and the change is a finding)
        D-086's correction.  This read ``DEAD`` — "recovers all three parts and
        still reads empty" — and the emptiness was attributed to a fourth,
        unregistered part of a liveness act: a *temporal and topological*
        precondition (``--until=<epoch>`` over ``origin/main..<ref>``) named by
        neither :func:`guard_reflexivity.acts_of` nor
        :class:`guard_reflexivity.Exemption`.

        That attribution was wrong, and wrong in the direction D-086 is about.
        **The fixture is a synthetic repo with no ``origin/main`` and no
        autoresearch refs** — the same blindness as a CI checkout.  The guard
        was not reading empty because the act failed to wake it; it was reading
        empty because the clone could not be asked.  Now that
        :mod:`git_surface` refuses instead of folding over nothing, the outcome
        is ``ERROR`` carrying the surface verdict, which is the true statement.

        The precondition observation may still be right — but it was never
        *measured* here, and this fixture cannot measure it.  Re-deriving it
        needs a fixture with both ref halves, which is recorded as follow-up
        rather than asserted now.
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
    assert outcomes["local_only_audit.pre_epoch_commits"] == ld.LIVENESS_ERROR
    # ...and the error must name the surface, not merely be an error. Without
    # this the assertion above is satisfied by any exception at all, which is
    # how "the guard reads empty" survived four cycles as a claim about the
    # guard when it was a claim about the fixture.
    surfaced = next(l for l in executed
                    if l.guard == "local_only_audit.pre_epoch_commits")
    assert "UndecidableSurface" in str(surfaced.note) or any(
        v in str(surfaced.note) for v in git_surface.VERDICTS), (
        f"pre_epoch_commits errored for an unnamed reason: {surfaced.note!r}")
    # ...and the second one too. D-086 found BOTH of the two "surviving" acts
    # were readings of the fixture rather than of their guards: this one scored
    # INERT ("the act moves the reading by nothing at all") on the same
    # history-blind repo, and the guard it calls folds over the same absent
    # refs. Neither guard was executable here; one read empty and one read
    # stationary, and both were the empty fold wearing two different verdicts.
    assert outcomes["local_only_audit.unregistered_local_only"] == ld.LIVENESS_ERROR
    stationary = next(l for l in executed
                      if l.guard == "local_only_audit.unregistered_local_only")
    assert "UndecidableSurface" in str(stationary.note) or any(
        v in str(stationary.note) for v in git_surface.VERDICTS), (
        f"unregistered_local_only errored for an unnamed reason: "
        f"{stationary.note!r}")
    # unwoken() counts acts that did not wake their guard. An act that could not
    # be run did not wake it either, so the count is unchanged — but it now
    # means "unexecutable here", not "executed and inert", which is exactly the
    # distinction this cycle exists to keep.
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
    # D-086: this claim is RETRACTED as unmeasured, not refuted. The readings it
    # compared (before == reading == 2) came from a fixture with no origin/main
    # and no autoresearch refs, so `derived_local_only`'s fold ran over nothing
    # and returned a population that was an artifact of the clone. A stationary
    # reading between two invalid readings says nothing about the act.
    #
    # What is asserted instead is that the guard now REFUSES, which is the only
    # honest statement this fixture supports. Re-deriving the original claim
    # needs a fixture holding both ref halves — recorded as follow-up rather
    # than quietly deleted, per D-042: an instrument that can only clear work
    # must name what it could not look at.
    assert inert.outcome == ld.LIVENESS_ERROR
    assert not inert.moved, "a refused call must not be recorded as movement"
    assert inert.before == inert.reading == 0, (
        "a guard that raised has no reading; a non-zero one here means the "
        "refusal was caught somewhere that substituted a default"
    )


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

    The guards that survive are exactly the ones somebody wrote by hand.  Q-068's
    proposal — derive the probe table instead of typing it — is answered in the
    negative on the population it was proposed over, and answered by execution
    rather than by argument.

    D-106 makes the statement stronger by making the typed table *bigger* than
    the derived one.  ``cycle_artifacts.unsupported`` was probed by hand this
    cycle and the derivation cannot reach it — it falls out at ``NO_SCOPE``,
    having no act of its own — so the yield is not merely zero, it is zero while
    the hand-written table grew.  A derivation that stands still while the thing
    it was proposed to replace grows is answered twice.

    D-114 makes it three times, and the gap is now two rather than one.
    ``unwatched_strandings`` is unreachable for the same structural reason as
    ``unsupported`` — its act is a commit, not a path-scoped edit — so the
    derived set stayed at 2 while the table went to 4.  The proposal was "derive
    the probes instead of hand-writing them"; three consecutive hand-written
    entrants that the derivation cannot reach is the measured answer.
    """
    live = {l.guard for l in executed if l.live}
    assert live - set(gd.PROBES) == set(), "the derivation may not exceed the table"
    assert live < set(gd.PROBES), "…and this cycle it is a strict subset"
    assert set(gd.PROBES) - live == {
        "cycle_artifacts.unsupported",
        "cycle_artifacts.unwatched_strandings",
        # D-209.  Fourth unreachable entrant; see the note in
        # `test_derivation_reproduces_both_typed_acts`.  The derived set has
        # been 2 for four consecutive cycles while the table went 2 → 5.
        "inert_surface.carried_drift",
    }


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
        "DEGENERATE_READINGS", "SCOPED_CLAIMS", "TEMPERATURE_RELEVANT",
        "RESOLVERS",
        # D-313: `extremum_reading.SITE_CLASSES`, the fifth.  Its 34 members are
        # AST node-class names, so it resolves and names no path for the same
        # reason the other four do.  Its sibling `HULL_REPAIRED_BY` does *not*
        # appear here — it lands one layer up in `NO_REGISTRY` — which is why
        # this layer is pinned by name rather than by count: a two-entry repair
        # split across two layers, and only naming them shows that.
        "SITE_CLASSES"}
    assert all("0 name a path" in r.note for r in rows)


def test_underivable_recipes_refuse_to_act(scored):
    """No silent no-op act: a non-derived recipe raises rather than doing nothing."""
    dud = next(r for r in scored if not r.derived)
    with pytest.raises(ld.DerivationError):
        dud.act(Path("/tmp/does-not-matter"))
