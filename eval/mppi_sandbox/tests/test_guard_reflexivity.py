"""Q-063 (b): does a guard's clean reading survive the failure it was built for?

Each verdict here is pinned rather than asserted loosely, because the answer is
a **negative** — the D-047 shape is found exactly once, in D-047's own guard —
and a negative from a scan is only worth what the scan's own correctness is
worth.  Four of the last five cycles had a first-draft scan that under-counted
its own population, always in the direction that deletes evidence.
"""

from __future__ import annotations

import ast

import pytest

from eval.mppi_sandbox import guard_reflexivity as gr


@pytest.fixture(scope="module")
def pool():
    return gr.guards()


def test_guard_population_is_globbed_not_typed(pool):
    """D-045's lesson: the registry of registries must not be hand-written."""
    modules = {m.stem for m in gr.package_modules()}
    assert "tree_provenance" in modules and "citation_audit" in modules
    assert len(modules) >= 20
    assert {g.module for g in pool} <= modules


def test_scan_finds_the_known_guards(pool):
    """The guards three consecutive decisions were written about are all in."""
    names = {g.qualname for g in pool}
    for known in (
        "tree_provenance.undeclared_drift",
        "tree_provenance.stale_declarations",
        "local_only_audit.unregistered_local_only",
        "local_only_audit.underived_declarations",
        "claim_scope.unregistered_citations",
        "claim_scope.stale_coincidences",
        "citation_audit.unregistered",
    ):
        assert known in names, known


def test_membership_dispatch_is_not_a_guard(pool):
    """``if key in ('a', 'b')`` with nothing iterated filters no population.

    The first draft admitted six of these — ``run.main``,
    ``dispatch_divergence.dispatch_fingerprint``, ``horizon_audit.cruise_ceiling``
    among them — and each one carried a fake ``pop=None``.  A guard with no
    population cannot have an exemption that removes anything from it.
    """
    names = {g.qualname for g in pool}
    for not_a_guard in ("run.main", "dispatch_divergence.dispatch_fingerprint",
                        "horizon_audit.cruise_ceiling"):
        assert not_a_guard not in names, not_a_guard
    assert all(g.population_key for g in pool)


def test_inline_displays_are_not_registries(pool):
    """A collection written at the filter site has no second statement to go short.

    Tagged, not dropped: the distinction between ``INLINE`` and ``TYPED`` is
    exactly the distinction between a literal and a registry, and every one of
    D-045/D-046/D-047 turned on a registry's second statement.
    """
    inline = [e for g in pool for e in g.exemptions if e.provenance == gr.PROV_INLINE]
    assert inline, "the INLINE tag must be reachable or it is untested vocabulary"
    assert all(e.constant is None for e in inline)
    typed = [e for g in pool for e in g.typed_exemptions]
    assert all(e.constant and e.constant.isupper() for e in typed)


def test_core_name_sees_through_spelling():
    """Mirror detection compares expressions nobody spells the same way."""
    def key(src: str) -> str:
        return gr.core_name(ast.parse(src, mode="eval").body)

    assert key("sorted(set(derived_local_only(root)))") == "derived_local_only"
    assert key("{dc.key for dc in derived_citations(root)}") == "derived_citations"
    assert key("((c, d, a) for c, d, a, _ in COINCIDENTAL)") == "COINCIDENTAL"
    assert key("DECLARED_LOCAL_ONLY") == "DECLARED_LOCAL_ONLY"


def test_string_comparison_would_have_missed_two_of_three_mirrors(pool):
    """Pins the first draft's error so no later cycle re-introduces it.

    Comparing unparsed source found **one** mirror where there are three.  An
    undetected mirror promotes a sound guard into Q-063's answer set, so the
    bug inflated the finding rather than shrinking it — the rarer direction,
    and the reason it is pinned rather than trusted.
    """
    found = gr.mirrors(pool)
    assert len(found) == 3
    by_source = {(a, b) for a, b in found
                 if _population_source(pool, a) in {_exemption_sources(pool, b)}}
    assert len(by_source) < len(found)


def _population_source(pool, qualname: str) -> str:
    return next(g.population for g in pool if g.qualname == qualname)


def _exemption_sources(pool, qualname: str) -> str:
    g = next(g for g in pool if g.qualname == qualname)
    return g.exemptions[0].expr


def test_mirrors_are_the_known_three(pool):
    assert gr.mirrors(pool) == (
        ("citation_audit.missing_sites", "citation_audit.unregistered"),
        ("claim_scope.stale_coincidences", "claim_scope.unregistered_citations"),
        ("local_only_audit.underived_declarations",
         "local_only_audit.unregistered_local_only"),
    )


def test_q063_the_shape_occurs_exactly_once(pool):
    """Q-063 (b)'s answer, and it is a negative.

    The lean was that "a shape that exists once usually exists twice".  It does
    not here: of 23 guards, exactly one has a population that the offending act
    can collapse, and it is the guard D-047 was written about.  Every other
    guard enumerates its population from a listing — ``git ls-files``, a
    document scan, a module's own members — and an enumerated population still
    contains the offender after the offence.
    """
    flagged = gr.unmirrored_revocable(pool)
    assert [g.qualname for g in flagged] == ["tree_provenance.undeclared_drift"]
    assert len(gr.revocable(pool)) == 1
    assert len(pool) > 20, "a one-element answer needs a population to be small in"


def test_revocability_is_about_the_population_not_the_name(pool):
    """``stale_declarations`` shares the allow-list and is *not* revocable.

    Both live in ``tree_provenance`` and both read ``DECLARED_LOCAL_ONLY``, so a
    name- or module-based rule would flag both or neither.  The separating fact
    is structural: one watches a difference between two observations, the other
    enumerates a list.
    """
    drift = next(g for g in pool if g.name == "undeclared_drift")
    stale = next(g for g in pool if g.name == "stale_declarations")
    assert drift.population_kind == gr.KIND_DIFFERENCE
    assert stale.population_kind == gr.KIND_ENUMERATION
    assert drift.typed_exemptions[0].constant == "DECLARED_LOCAL_ONLY"


def test_the_allow_list_that_was_watched_twice_and_still_blind(pool):
    """D-047's second half: coverage by existence is not coverage by act.

    ``DECLARED_LOCAL_ONLY`` has the *most* watchers of any allow-list in the
    package — and both of them read clean through the entire ~30 cycles in
    which ``TODO.md`` and ``research/feed.md`` were committable.  So this
    assertion is deliberately not phrased as a clearance.
    """
    watchers = gr.exemption_watchers(pool)
    assert set(watchers["DECLARED_LOCAL_ONLY"]) == {
        "local_only_audit.underived_declarations",
        "tree_provenance.stale_declarations",
    }
    assert "local_only_audit.staged_declarations" not in watchers["DECLARED_LOCAL_ONLY"]


def test_unwatched_allow_lists_are_module_layer_only(pool):
    """STATE #2's half, stated at the scope the scan actually has.

    Three ``TYPED`` allow-lists have no module-level function enumerating them.
    All three are named in ``tests/``, so the finding is "no watcher in the
    layer this scan reads", not "unchecked" — the stronger claim would be
    false, and asserting the weaker one next to its own limit is the point.
    """
    unwatched = gr.unwatched_exemptions(pool)
    assert set(unwatched) == {"DEGENERATE_READINGS", "SCOPED_CLAIMS",
                              "TEMPERATURE_RELEVANT"}
    mentions = gr.test_layer_mentions()
    for key in unwatched:
        assert mentions[key], f"{key} unwatched at both layers"


def test_bite_verdicts_cover_the_four_states():
    assert gr.bite("g", [1, 2, 3], [2]).verdict == "BITES"
    assert gr.bite("g", [1, 2, 3], [9]).verdict == "INERT"
    assert gr.bite("g", [1, 2], [1, 2]).verdict == "TOTAL"
    assert gr.bite("g", [], [1]).verdict == "VACUOUS"


def test_inert_exemption_is_the_d046_shape():
    """An exemption removing nothing is the state in which a bug is invisible.

    D-046's ``_sites_from_claim_scope`` lacked a ``kind`` filter and nothing
    revealed it, because every citation on that claim happened to be
    ``other-quantity``: the filter's place was held by a coincidence.  ``INERT``
    is that state, named.
    """
    scored = gr.bite("claim_scope.unregistered_citations", ["a", "b"], [],
                     exemption_name="COINCIDENTAL")
    assert scored.verdict == "INERT"
    assert scored.overlap == 0


def test_unbitten_is_the_mirror_of_bite(pool):
    """An unscored pair is indistinguishable from a pair that scored clean."""
    assert gr.unbitten([], pool), "nothing scored ⇒ every TYPED pair must be named"
    every = [gr.bite(g.qualname, [], [], e.constant or e.key)
             for g in pool for e in g.typed_exemptions]
    assert gr.unbitten(every, pool) == ()


def test_report_names_its_own_findings(pool):
    text = gr.report()
    assert "tree_provenance.undeclared_drift" in text
    assert "DECLARED_LOCAL_ONLY" in text
    assert "(nobody)" in text
