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
    """An empty candidate set is a clearance only if nothing was skipped."""
    assert em.unscreened() == ()


# --------------------------------------------------------------------------
# the finding: only one pair was probeable before this module existed
# --------------------------------------------------------------------------


def test_only_one_pair_takes_its_exemption_as_a_parameter():
    """D-050's probe was possible on exactly one guard, by coincidence.

    ``undeclared_drift`` accepts ``declared=`` so :func:`tree_provenance.verify`
    can pass a stamp's own allow-list — not so anyone could audit it.  Every
    other typed exemption is a hard-wired module global, so the suppression
    method that found the only known mask was inapplicable to 11 of 12 pairs
    until this module routed around it.

    If this ever reads > 1, the extra guard became auditable by design and the
    module-global route is that much less load-bearing — worth knowing either way.
    """
    param = em.parameterised()
    assert param == ("tree_provenance.undeclared_drift ~ DECLARED_LOCAL_ONLY",)


def test_module_global_route_covers_the_rest():
    by_route: dict[str, int] = {}
    for r in em.routes():
        by_route[r.route] = by_route.get(r.route, 0) + 1
    assert by_route.get(em.ROUTE_UNREACHABLE, 0) == 0
    assert by_route[em.ROUTE_MODULE_GLOBAL] + by_route[em.ROUTE_PARAMETER] == 12


# --------------------------------------------------------------------------
# the screen re-finds the only positive result it generalises from
# --------------------------------------------------------------------------


def test_screen_refinds_d050s_mask():
    """A screen that cannot re-find D-050's mask is not a screen.

    This is the test the first draft failed twice — once because the parameter
    route was missed (so the pair was probed through the wrong namespace) and
    once because ``Drift`` is a dataclass and collapsed to a one-element reading
    on both sides of the suppression.
    """
    scored = {(s.guard, s.constant): s for s in em.screen()}
    drift = scored[("tree_provenance.undeclared_drift", "DECLARED_LOCAL_ONLY")]
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
    assert masks == ("tree_provenance.undeclared_drift ~ DECLARED_LOCAL_ONLY (+5)",)


def test_bite_alone_is_weaker_than_the_intersection():
    """The reason the intersection exists, pinned as an inequality.

    If these ever become equal, either every biting exemption became revocable
    or the revocability filter stopped filtering — both are findings.
    """
    scored = em.screen()
    assert len(em.candidates(scored)) > len(em.masking_candidates(scored))


def test_the_other_difference_guard_screens_inert_not_masking():
    """``staged_declarations`` is revocable but does **not** bite.

    It narrows *down to* the registry (``changed & DECLARED_LOCAL_ONLY``) rather
    than subtracting it, so suppression empties its population instead of
    growing it.  Same registry, same module, opposite sense — which is why the
    intersection is not just "the DIFFERENCE guards".
    """
    scored = {(s.guard, s.constant): s for s in em.screen()}
    staged = scored[("local_only_audit.staged_declarations", "DECLARED_LOCAL_ONLY")]
    assert staged.verdict == em.VERDICT_INERT


# --------------------------------------------------------------------------
# instrument liveness — D-050's lesson applied to this module
# --------------------------------------------------------------------------


def test_suppression_is_restored_after_every_screen():
    """The probe patches module globals; it must leave none of them patched."""
    from eval.mppi_sandbox import local_only_audit, tree_provenance
    before = tuple(tree_provenance.DECLARED_LOCAL_ONLY)
    em.screen()
    assert tuple(tree_provenance.DECLARED_LOCAL_ONLY) == before
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
