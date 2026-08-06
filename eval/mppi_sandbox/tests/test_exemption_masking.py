"""STATE #1: screen every ``TYPED`` exemption for masking (D-052).

The tests are written so that each one states a fact that would have to change
for the module's conclusion to change, rather than pinning today's numbers.
"""

from __future__ import annotations

import ast
import textwrap

import pytest

from eval.mppi_sandbox import exemption_masking as em
from eval.mppi_sandbox import guard_reflexivity as gr
from eval.mppi_sandbox import git_surface
from eval.mppi_sandbox import tree_provenance as tp

#: The guard pool contains guards that read repository history, so its census is
#: a measurement *of this clone* and not only of the package.  On a clone that
#: cannot answer (CI's ``actions/checkout@v4`` produces one) those guards refuse,
#: and every count below shifts.  Split rather than skipped, for the reason
#: stated in ``test_local_only_audit``: a skip makes the CI half of the suite
#: assert nothing, which is this package's own recurring defect.
_DECIDABLE = git_surface.reading().decidable


def _surface_refused(screen_by_key, guard, constant):
    """The blind-clone claim: the pair graded UNRUNNABLE *because of the clone*.

    Asserting the verdict alone would be satisfied by a guard that is unrunnable
    for the unrelated reason ``_call`` already names (a required parameter with
    no default).  The note is what separates the two, so it is what is asserted.
    """
    screened = screen_by_key.get((guard, constant))
    assert screened is not None, f"{guard} ~ {constant} was not screened at all"
    assert screened.verdict == em.VERDICT_UNRUNNABLE, (
        f"{guard} graded {screened.verdict} on a clone that cannot answer "
        "history questions; expected a refusal"
    )
    assert "UndecidableSurface" in screened.note or any(
        v in screened.note for v in git_surface.VERDICTS
    ), f"unrunnable for an unnamed reason: {screened.note!r}"


# --------------------------------------------------------------------------
# population — derived, and the same population every other TYPED screen reads
# --------------------------------------------------------------------------


def test_population_is_exactly_the_typed_exemptions():
    """The screen may not disagree with the label it screens.

    ``bite``/``unwatched_exemptions``/``typed_exemptions`` all consume
    ``PROV_TYPED``; if this module derived its own idea of the population it
    could report a clean screen over a different set than the one at risk.
    """
    pool = gr.guards()
    expected = {(g.qualname, e.constant)
                for g in pool for e in g.typed_exemptions if e.constant}
    got = {r.key for r in em.routes(pool)}
    assert got == expected


def test_every_pair_has_a_suppression_route():
    """No pair may be unfalsifiable: a mask with no probe is undetectable."""
    assert em.unsuppressible() == ()


def test_no_pair_is_left_unscreened():
    """An empty candidate set is a clearance only if nothing was skipped.

    One pair is skipped, and the reason is structural rather than an oversight.
    :func:`_call` refuses to fabricate arguments and notes that "every guard in
    the derived population has defaults for all of its parameters" — which was
    true of all 44 guards when it was written and is a **coincidence**, not a
    property.  :func:`guard_witness.unwitnessed` is the first guard whose
    population is a *measurement* (a coverage run over the suite, ~5 min) rather
    than a read of the syntax tree or the filesystem, so it cannot carry a
    default without one of two lies: a cheap default that makes the guard read
    empty always — D-058's own defect, in the module built to hunt it — or a
    real one that charges every caller of ``unscreened()`` a full suite run.

    So the pair is named here rather than defaulted away, and ``UNRUNNABLE`` is
    doing exactly the job it was defined for.
    """
    if not _DECIDABLE:
        # The skipped set is a census over the pool, and on a clone that cannot
        # answer history questions the history-reading guards join it.  What is
        # asserted here is (a) the two structural skips are still present — they
        # have nothing to do with the clone — and (b) every *additional* skip
        # names a surface verdict rather than appearing for no stated reason.
        # An unexplained growth in the skipped set is exactly how an empty
        # candidate set becomes a false clearance, which is this test's subject.
        skipped = em.unscreened()
        assert any("guard_witness.unwitnessed" in u for u in skipped)
        assert any("magnitude_survival.over_derivation" in u for u in skipped)
        extra = [u for u in skipped
                 if "guard_witness.unwitnessed" not in u
                 and "magnitude_survival.over_derivation" not in u]
        for entry in extra:
            assert (
                "UndecidableSurface" in entry
                or em.VERDICT_UNPOPULATED in entry
                or any(v in entry for v in git_surface.VERDICTS)), (
                f"pair skipped for an unnamed reason on a blind clone: {entry!r}")
        return
    skipped = em.unscreened()
    assert set(skipped) >= {
        # D-088's two.  Both were `INERT` until this cycle, i.e. both were
        # counted as *results* by the very test whose subject is "an empty
        # candidate set is a clearance only if nothing was skipped".  The
        # clearance this test pinned for thirty-odd cycles was two pairs too
        # generous, and neither pair announced it, because a guard whose subject
        # is empty runs perfectly and returns nothing.
        "claim_scope.unregistered_citations ~ SCOPED_CLAIMS: UNPOPULATED "
        "guard read nothing at HEAD — suppression untested",
        "local_only_audit.staged_declarations ~ DECLARED_LOCAL_ONLY: "
        "UNPOPULATED guard read nothing at HEAD — suppression untested",
        "guard_witness.unwitnessed ~ WITNESSES: UNRUNNABLE call at HEAD: "
        "required parameter 'census'",
        # D-076's second, and it is the *ordinary* case the first was not.
        # `unwitnessed` cannot be defaulted because its population is a 5-minute
        # coverage run.  `over_derivation` cannot be defaulted for the dull
        # reason that it takes a `Record` — a file off disk, cheap, but not
        # something `_call` will fabricate.  So `UNRUNNABLE` is not a marker of
        # expensive guards; it is a marker of guards with a required argument,
        # and one instance was hiding that behind an interesting cause.
        "magnitude_survival.over_derivation ~ SELF_DEFINING: UNRUNNABLE call at "
        "HEAD: required parameter 'record'",
    }
    # `>=` rather than `==`, and the slack is bounded to exactly one pair for a
    # stated reason.  `undeclared_drift` reads the *worktree*, so it joins the
    # skipped set on any clean tree — including a decidable full clone with no
    # local edits, which this branch used to fail on.  Pinning the tuple exactly
    # would make this test assert a property of whoever's checkout is running
    # it, which is the defect D-088 removed from `test_screen_refinds_d050s_mask`
    # one section down; re-committing it here would be absurd.  What must not
    # slip is an entry with no stated reason, so that is what is checked.
    for entry in skipped:
        assert (em.VERDICT_UNPOPULATED in entry
                or em.VERDICT_UNRUNNABLE in entry
                or em.VERDICT_DEAD in entry), (
            f"pair skipped for an unnamed reason: {entry!r}")
    assert len(skipped) <= 5, (
        "at most the four above plus `undeclared_drift` on a clean tree; "
        f"got {len(skipped)}: {skipped!r}")


# --------------------------------------------------------------------------
# the finding: only one pair was probeable before this module existed
# --------------------------------------------------------------------------


def test_two_pairs_take_their_exemption_as_a_parameter():
    """D-050's probe was possible on exactly one guard, by coincidence — until D-101.

    ``undeclared_drift`` accepts ``declared=`` so :func:`tree_provenance.verify`
    can pass a stamp's own allow-list — not so anyone could audit it.  Every
    other typed exemption was a hard-wired module global, so the suppression
    method that found the only known mask was inapplicable to 11 of 12 pairs
    until this module routed around it.

    The docstring that stood here said: *"if this ever reads > 1, the extra guard
    became auditable by design and the module-global route is that much less
    load-bearing — worth knowing either way."*  It now reads 2, and the second
    one is the by-design case rather than another coincidence.
    ``candidate_scope.coverage`` takes ``graded=`` for exactly the audit reason:
    the rule it enforces ("an ungraded site reads ``UNREAD``") lost its whole
    live population when D-101 graded the residue, so the parameter is what lets
    the rule be exercised on a site that does not exist.  A guard whose
    exemption arrives by parameter is one a test can falsify without editing the
    module, which is the property this pin has been waiting to see acquired
    deliberately.
    """
    param = em.parameterised()
    assert param == ("candidate_scope.coverage ~ GRADED",
                     "tree_provenance.undeclared_drift ~ DECLARED_LOCAL_ONLY")


def test_module_global_route_covers_the_rest():
    by_route: dict[str, int] = {}
    for r in em.routes():
        by_route[r.route] = by_route.get(r.route, 0) + 1
    assert by_route.get(em.ROUTE_UNREACHABLE, 0) == 0
    # 12 through D-053; D-054's `liveness_derivation.unranked_scopes` subtracts
    # the module global `SCOPE_PRECEDENCE`, so it routes module-global too.
    # D-060's `guard_witness.unwitnessed ~ WITNESSES` makes 14 — it *routes*
    # module-global fine; what it cannot do is be **called**, which is a
    # different layer and is pinned by `test_no_pair_is_left_unscreened`.
    # D-073's `reading_record.would_have_carried ~ CARRIED_FIELDS` makes 15. Its
    # sibling `uncarried_fields` does not route here: its exempting set is DERIVED
    # (a `dir()` over a round-tripped cell), and this screen is TYPED-pairs only.
    # D-075's `magnitude_survival.published ~ SELF_DEFINING` makes 16. Only one
    # of that cycle's four new guards routes here, and the other three say why:
    # `standings` / `unbanded` / `movements` filter against `banded`, a **local**
    # dict from a same-module call, so there is no module global to reach and no
    # TYPED pair to screen. Four guards, one screenable — the screen's population
    # tracks module-scoped registries, not guards.
    # D-076's `magnitude_survival.exemption_bite ~ SELF_DEFINING` makes 17. Its
    # two siblings again say why only one arrived: `readings` filters against
    # `banded` (local, D-051's shape), and `over_derivation` *does* route here
    # but cannot be called — it is the second `UNRUNNABLE` and is counted by
    # `test_no_pair_is_left_unscreened` instead. Three guards, one screened, one
    # screenable-but-uncallable, one out of scope.
    # D-080's `exemption_control.undeclared_unreachable ~ DECLARED_DEF_TIME`
    # makes 18. Its own module supplies the contrast: `uncontrolled` narrows
    # `REGISTRIES` by `not in covered`, where `covered` is DERIVED from
    # `TAMPERS`, so it is a guard (D-079) but not a TYPED pair and does not
    # route here. The registry that *does* route is the excuse list D-080 wrote
    # to hold `guard_vacuity.EXCLUDED_TESTS` — so the cycle that declared one
    # uncontrollable registry created a screenable pair for another, which is
    # the second-order cost D-073 and D-075 each paid and D-077/D-079 avoided.
    # D-101's `candidate_scope.coverage ~ GRADED` makes 19, and it is the first
    # addition on the PARAMETER route since D-050's coincidence — see
    # `test_two_pairs_take_their_exemption_as_a_parameter` for why that one is
    # deliberate. Its sibling `stale_grades` does not route here: its exempting
    # set is `set(residue)`, DERIVED from a parameter, and this screen is
    # TYPED-pairs only. Same one-of-two split D-075 through D-080 kept paying,
    # with the twist that here the unscreened sibling exists *because* the
    # screened one entered.
    assert by_route[em.ROUTE_MODULE_GLOBAL] + by_route[em.ROUTE_PARAMETER] == 19


# --------------------------------------------------------------------------
# the screen re-finds the only positive result it generalises from
# --------------------------------------------------------------------------


def test_screen_refinds_d050s_mask():
    """A screen that cannot re-find D-050's mask is not a screen.

    This is the test the first draft failed twice — once because the parameter
    route was missed (so the pair was probed through the wrong namespace) and
    once because ``Drift`` is a dataclass and collapsed to a one-element reading
    on both sides of the suppression.

    D-088 rewrote it a third time, and the old version is the finding.  It
    branched on ``_DECIDABLE`` — whether the clone can answer *history* questions
    — while its own comment correctly said ``undeclared_drift`` "needs no
    remote".  What decides this pair's verdict is whether a **declared path is
    drifting in the worktree**, a different axis entirely.  The two co-vary on CI
    (a fresh checkout is both blind and clean) and that coincidence is the whole
    reason the wrong gate looked right — D-046's shape, holding a gate's place
    this time.  When the axes came apart CI graded ``INERT``, which the old gate
    did not admit, and the failure read as a bug in the clone rather than in the
    vocabulary.

    Branching on the *right* environment variable would still have been wrong,
    because it makes the assertion conditional on a tree nobody controls: this
    repo's own dev checkout re-finds the mask only because ``STATE.md`` happens
    to be dirty at the moment the suite runs.  So D-050's condition is
    **constructed** — a stamp in which a declared path differs — and the screen
    must re-find the mask on any tree, including a pristine one.
    """
    declared = next(iter(tp.DECLARED_LOCAL_ONLY))
    route = next(r for r in em.routes()
                 if r.key == ("tree_provenance.undeclared_drift",
                              "DECLARED_LOCAL_ONLY"))
    real_stamp = tp.stamp
    try:
        # D-050's exact shape: the offence is a declared path diverging, and the
        # exemption removes it from the population before the guard can report.
        tp.stamp = lambda *a, **k: tp.Stamp(
            head="synthetic", worktree_fingerprint="w",
            committed_fingerprint="c", untracked_digest="", n_tracked=1,
            n_untracked=0,
            committed={declared: "before"}, worktree={declared: "after"})
        drift = em.screen_one(route)
    finally:
        tp.stamp = real_stamp

    assert drift.verdict == em.VERDICT_CANDIDATE
    assert drift.revealed > 0


def test_masking_class_is_bounded_at_one_by_measurement():
    """STATE #1's answer.

    ``bite`` alone is weak — it fires on every exemption that is doing its job.
    Intersecting with revocability (D-048: only a ``DIFFERENCE`` population can
    be collapsed by the offence) leaves exactly D-050's own pair.  Q-063 bounded
    this class at one structurally; this bounds it at one by measurement over
    all typed pairs, which is the stronger statement.
    """
    masks = em.masking_candidates()
    if not _DECIDABLE:
        # The bound is a census over the pool, and the pool is smaller here.
        # What survives is the direction: no pair outside D-050's may qualify.
        assert set(masks) <= {
            "tree_provenance.undeclared_drift ~ DECLARED_LOCAL_ONLY (+5)"}
        return
    assert masks == ("tree_provenance.undeclared_drift ~ DECLARED_LOCAL_ONLY (+5)",)


def test_bite_alone_is_weaker_than_the_intersection():
    """The reason the intersection exists, pinned as an inequality.

    If these ever become equal, either every biting exemption became revocable
    or the revocability filter stopped filtering — both are findings.
    """
    scored = em.screen()
    assert len(em.candidates(scored)) > len(em.masking_candidates(scored))


def test_the_other_difference_guard_screens_diverges_not_masking():
    """``staged_declarations`` is revocable but does **not** bite.

    The mechanism was always stated correctly: it narrows *down to* the registry
    (``changed & DECLARED_LOCAL_ONLY``) rather than subtracting it, so
    suppression **empties** its population instead of growing it.  Same registry,
    same module, opposite sense — which is why the intersection is not just "the
    DIFFERENCE guards".

    D-088 found that this test, and the ``masking_candidates`` docstring quoting
    it, pinned that mechanism to ``INERT`` — the one verdict it cannot produce.
    Emptying a population *is* ``DIVERGES``, the verdict this module defined for
    "changed without growing ... named so it cannot be silently counted as one".
    ``INERT`` (0→0) is what the pair reads when the index is empty, which is
    precisely when the described narrowing never happens.  Nothing caught it
    because a git index is empty in every ordinary run, so the number the prose
    quoted had never once been produced by the process the prose described.

    So the mechanism is asserted where it is observable: stage a declared path
    and read the pair.  The test now fails if suppression ever *grows* this
    guard, which is the fact the masking bound actually needs.
    """
    scored = {(s.guard, s.constant): s for s in em.screen()}
    key = ("local_only_audit.staged_declarations", "DECLARED_LOCAL_ONLY")
    if not _DECIDABLE:
        _surface_refused(scored, *key)
        return

    staged = scored[key]
    if not staged.head_size:
        # The ordinary state: nothing staged, so the guard read nothing and the
        # exemption was never exercised.  That is now sayable.
        assert staged.verdict == em.VERDICT_UNPOPULATED

    # The mechanism itself, measured rather than asserted from the syntax: give
    # the guard a subject and suppression must shrink it to nothing.
    route = next(r for r in em.routes() if r.key == key)
    from eval.mppi_sandbox import local_only_audit
    declared = next(iter(local_only_audit.DECLARED_LOCAL_ONLY))
    real_staged_changes = local_only_audit.staged_changes
    try:
        # A synthetic subject, so the reading does not depend on the real index
        # — the test asserts the guard's shape, not the state of this checkout.
        local_only_audit.staged_changes = lambda *a, **k: {declared}
        populated = em.screen_one(route)
    finally:
        local_only_audit.staged_changes = real_staged_changes

    assert populated.head_size == 1
    assert populated.suppressed_size == 0
    assert populated.verdict == em.VERDICT_DIVERGES
    assert populated.verdict != em.VERDICT_CANDIDATE, (
        "narrowing down to the registry must never read as a bite")


# --------------------------------------------------------------------------
# instrument liveness — D-050's lesson applied to this module
# --------------------------------------------------------------------------


def test_suppression_is_restored_after_every_screen():
    """The probe patches module globals; it must leave none of them patched."""
    from eval.mppi_sandbox import local_only_audit, tree_provenance
    before = tuple(tree_provenance.DECLARED_LOCAL_ONLY)
    em.screen()
    assert tuple(tree_provenance.DECLARED_LOCAL_ONLY) == before
    if not _DECIDABLE:
        # Restoration is the claim; the readback needs a decidable clone.
        with pytest.raises(git_surface.UndecidableSurface):
            local_only_audit.unregistered_local_only()
        return
    assert local_only_audit.unregistered_local_only() == []


def test_dataclass_readings_are_flattened_not_collapsed():
    """``_reading`` must see inside a dataclass or growth is invisible."""
    from eval.mppi_sandbox.tree_provenance import Drift
    small = em._reading(Drift(changed=("a",)))
    big = em._reading(Drift(changed=("a",), added=("b", "c")))
    assert len(small) == 1 and len(big) == 3
    assert set(small) < set(big)


def test_empty_registry_is_vacuous_not_inert():
    """An empty allow-list cannot be suppressed, and must not read as clean."""
    from eval.mppi_sandbox import claim_scope
    original = claim_scope.COINCIDENTAL
    route = next(r for r in em.routes()
                 if r.key == ("claim_scope.unregistered_citations", "COINCIDENTAL"))
    try:
        claim_scope.COINCIDENTAL = ()
        assert em.screen_one(route).verdict == em.VERDICT_VACUOUS
    finally:
        claim_scope.COINCIDENTAL = original


def test_empty_reading_is_unpopulated_not_inert():
    """D-088: ``VACUOUS``'s sibling, and the reason it had to exist.

    ``test_empty_registry_is_vacuous_not_inert`` (above) pins the first
    emptiness — nothing to suppress.  This pins the second — nothing to suppress
    it *from*.  The two are the same argument and only one was ever made, so for
    three cycles a guard that read nothing was reported as an exemption that
    removes nothing.
    """
    from eval.mppi_sandbox import claim_scope
    route = next(r for r in em.routes()
                 if r.key == ("claim_scope.unregistered_citations", "COINCIDENTAL"))
    original = claim_scope.unregistered_citations
    try:
        # Registry stays non-empty, so VACUOUS cannot fire and INERT is the only
        # thing the old vocabulary could have said.
        claim_scope.unregistered_citations = lambda *a, **k: ()
        screened = em.screen_one(route)
    finally:
        claim_scope.unregistered_citations = original
    assert screened.registry_size > 0, "VACUOUS would make this test vacuous"
    assert screened.verdict == em.VERDICT_UNPOPULATED
    assert screened.verdict != em.VERDICT_INERT


def test_inert_never_covers_an_empty_reading():
    """The invariant that makes ``INERT`` mean something.

    ``INERT`` is a claim about the exemption: it removes nothing *from a
    population that exists*.  If it is ever allowed to cover a 0→0 pair it also
    covers "there was no population", and the two are indistinguishable in the
    report — which is what D-088 found, in three of the module's own pairs at
    once.  Stated as an invariant rather than a count so it holds on any tree.
    """
    for screened in em.screen():
        if screened.verdict == em.VERDICT_INERT:
            assert screened.head_size > 0, (
                f"{screened.guard} ~ {screened.constant} graded INERT on an "
                "empty reading; that is UNPOPULATED")


def test_a_clean_tree_reports_its_unprobed_pairs():
    """The false-clearance case, end to end, on a synthetic clean tree.

    The failure this forbids is specific: **zero candidates and zero skips** on
    a checkout where the ``DIFFERENCE`` guards — the entire population a second
    mask could come from — were never probed at all.  That is what CI read.
    """
    route = next(r for r in em.routes()
                 if r.key == ("tree_provenance.undeclared_drift",
                              "DECLARED_LOCAL_ONLY"))
    real_stamp = tp.stamp
    try:
        # A pristine checkout: committed and worktree agree, so the guard reads
        # nothing.  Patched at the *stamp*, not at the guard, so the guard under
        # test is the real one — this is what CI's `actions/checkout@v4` hands it.
        tp.stamp = lambda *a, **k: tp.Stamp(
            head="synthetic", worktree_fingerprint="w",
            committed_fingerprint="w", untracked_digest="", n_tracked=1,
            n_untracked=0,
            committed={"eval/mppi_sandbox/run.py": "same"},
            worktree={"eval/mppi_sandbox/run.py": "same"})
        screened = em.screen_one(route)
    finally:
        tp.stamp = real_stamp
    assert screened.verdict == em.VERDICT_UNPOPULATED
    # and it must be *reported*, not merely named — an unprobed pair that does
    # not reach `unscreened` is exactly as invisible as one graded INERT.
    assert em.unscreened([screened]) != ()
    assert em.candidates([screened]) == ()


def test_unrunnable_guard_is_reported_not_guessed():
    """A required parameter is refused rather than fabricated."""
    def needs_an_argument(x):  # pragma: no cover - never called
        return x
    with pytest.raises(TypeError):
        em._call(needs_an_argument)


# --------------------------------------------------------------------------
# the route predicate's third spelling — the one the first draft missed
# --------------------------------------------------------------------------


@pytest.mark.parametrize("body,expected", [
    # signature default — the spelling the first draft did find
    ("def g(allow=REGISTRY):\n    return allow", "allow"),
    # the None-default idiom this package actually uses: the assignment target
    # is a *local*, not the parameter, which is what hid `undeclared_drift`
    ("def g(declared=None):\n"
     "    allow = REGISTRY if declared is None else declared\n"
     "    return allow", "declared"),
    # rebinding the parameter itself
    ("def g(declared=None):\n"
     "    declared = declared or REGISTRY\n"
     "    return declared", "declared"),
    # no route: the registry is read straight out of the module namespace
    ("def g():\n    return REGISTRY", None),
])
def test_substitution_spellings(body, expected):
    fn = ast.parse(textwrap.dedent(body)).body[0]
    assert em._substitutes_for(fn, "REGISTRY") == expected


def test_ifexp_route_does_not_fire_without_a_parameter():
    """A conditional between two constants is not a suppression route."""
    fn = ast.parse("def g():\n    allow = REGISTRY if FLAG else OTHER\n"
                   "    return allow").body[0]
    assert em._substitutes_for(fn, "REGISTRY") is None


# --------------------------------------------------------------------------
# Q-067 → D-052: (b), and the obligation that comes with it
# --------------------------------------------------------------------------


def test_provenance_exposure_is_still_zero_and_still_derived():
    """(b) is only tenable while the exposure is empty — so re-derive it."""
    from eval.mppi_sandbox import predicate_depth
    assert predicate_depth.provenance_depth_exposure() == ()


def test_decision_b_names_its_repair_in_the_code():
    """D-052 (b) required stating what to do when the exposure goes positive.

    Q-067 rejected option (c) ("do nothing, it is zero") precisely because a
    zero with no attached action is indistinguishable from an unnoticed one.
    """
    from eval.mppi_sandbox import predicate_depth
    doc = predicate_depth.provenance_depth_exposure.__doc__ or ""
    assert "name the helper's registry at the call site" in doc
    assert "Q-067" in doc and "D-052" in doc
    prov_doc = gr._provenance.__doc__ or ""
    assert "syntactic" in prov_doc.lower()
    assert "exemption_masking" in prov_doc


def test_masking_screen_population_is_what_the_exposure_threatens():
    """Why the exposure got *larger* this cycle rather than staying priced.

    Every pair this module screens is a ``TYPED`` one, so an exemption that
    slips to ``DERIVED`` leaves the masking screen's population silently.
    """
    pool = gr.guards()
    typed = sum(len(g.typed_exemptions) for g in pool)
    assert len(em.routes(pool)) == typed
