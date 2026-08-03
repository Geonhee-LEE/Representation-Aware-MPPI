"""Q-063 (b): does a guard's clean reading survive the failure it was built for?

Each verdict here is pinned rather than asserted loosely, because the answer is
a **negative** — the D-047 *failure* is found exactly once — and a negative from
a scan is only worth what the scan's own correctness is worth.  D-049 is the
demonstration: D-048 scanned for ``-``/``in``/``not in``, missed the ``&``
spelling, and so judged 23 guards without ``staged_declarations`` — the guard
D-047 had shipped one cycle earlier.  Five of the last six cycles had a
first-draft scan wrong about its own population.

The file therefore also carries Q-064's half (:func:`gr.watched_operations`
onward): what each guard *does*, not what it filters.
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


def test_q063_the_shape_occurs_twice_and_fails_once(pool):
    """Q-063 (b)'s answer, corrected by D-049 — and it is still a negative.

    D-048 read this as "of 23 guards, exactly one". Both halves were wrong and
    the conclusion was not. The **population** was short: admitting ``&`` as a
    filter (D-049) raises 23 → 28 and adds ``staged_declarations``, which is
    ``DIFFERENCE``-shaped and unmirrored, so the shape occurs **twice**. The
    **predicate** was short in the same place: :func:`revocable` asks whether a
    population is a difference, not whether the forbidden act *empties* it.
    Committing a snapshot file empties ``undeclared_drift`` — the guard goes
    quiet, which is D-047's failure — and **fills** ``staged_declarations``,
    which is a guard working. So the count of *failures* is still one, and the
    lean ("a shape that exists once usually exists twice") is still rejected as
    a claim about failures.
    """
    flagged = {g.qualname for g in gr.unmirrored_revocable(pool)}
    assert flagged == {
        "tree_provenance.undeclared_drift",
        "local_only_audit.staged_declarations",
    }
    assert len(gr.revocable(pool)) == 2
    assert len(pool) > 20, "a two-element answer needs a population to be small in"


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


# --------------------------------------------------------------------------
# Q-064 (b): the acts, not the sets
# --------------------------------------------------------------------------


def test_the_and_sense_recovers_the_guard_d047_shipped(pool):
    """D-048's scan could not see the guard written one cycle before it.

    ``staged_declarations`` narrows an observation *down to* the registry
    (``changed & set(DECLARED_LOCAL_ONLY)``) instead of removing the registry
    from a population.  D-048 read ``-``, ``in`` and ``not in``, so the guard
    D-047 shipped to close D-011's hole was absent from the 23 it judged.
    """
    names = {g.qualname for g in pool}
    assert "local_only_audit.staged_declarations" in names


def test_and_shaped_guards_are_exactly_these_three(pool):
    """Pinned: a population correction is only worth its own exactness."""
    found = {g.qualname for g in pool
             if any(e.sense == gr.SENSE_AND for e in g.exemptions)}
    assert found == {
        "ab.ab_temperature",
        "guard_reflexivity.bite",
        "local_only_audit.staged_declarations",
    }
    assert len(pool) == 28, "D-048 judged 23; admitting `&` adds 3"


def test_every_scope_is_now_observed(pool):
    """Derived on both sides — the vocabulary is fixed, the reached set is not.

    This is Q-064's answer: of the four states a change can reach, the suite
    looked through three.  The gap was the *index* — the exact verb D-048
    concluded nobody watched, arrived at here from the acts in the code rather
    than from reading three guards by hand — and D-049 closed it by giving
    ``staged_declarations`` the ``--cached`` read its name always claimed.

    Kept as an equality rather than deleted: an empty result is a clearance
    only while something re-derives it, and this is the whole of that argument.
    """
    assert gr.unobserved_scopes(pool) == ()
    reached = {a.scope for acts in gr.watched_operations(pool).values() for a in acts}
    assert gr.SCOPE_INDEX in reached


def test_no_guard_name_claims_a_scope_it_does_not_observe(pool):
    """The name is the fourth statement of a registry, and nothing checked it.

    ``staged_declarations`` was the one hit: named for the index, reading only
    commits.  The predicate stays after the fix for the same reason as above.
    """
    assert gr.misnamed_scopes(pool) == ()
    assert gr.nominal_scope("staged_declarations") == gr.SCOPE_INDEX
    observed = {a.scope for a in gr.acts_of("local_only_audit.staged_declarations")}
    assert gr.SCOPE_INDEX in observed


def test_declared_local_only_is_watched_through_three_windows(pool):
    """D-048 counted watchers; this counts windows.  Here they do not collapse."""
    cover = gr.scope_coverage(pool)["DECLARED_LOCAL_ONLY"]
    assert set(cover["scopes"]) == {gr.SCOPE_COMMIT, gr.SCOPE_NAMESET, gr.SCOPE_WORKTREE}
    assert gr.SCOPE_INDEX not in cover["scopes"]


def test_git_wrapper_dispatch_is_not_an_act():
    """``subprocess.run(("git", *args))`` names no subcommand, so it has no scope.

    Counting it gave every git-touching guard a phantom ``UNKNOWN`` act —
    D-048's "filter site with no population" one layer down.
    """
    acts = gr.acts_of("tree_provenance.stale_declarations")
    assert acts, "the guard does shell out to git"
    assert all(a.verb != "*" for a in acts)
    assert all(a.scope != gr.SCOPE_UNKNOWN for a in acts)


@pytest.mark.parametrize("args,scope", [
    (("diff", "--name-only", "--cached"), gr.SCOPE_INDEX),
    (("diff", "--name-only", "origin/main...HEAD"), gr.SCOPE_COMMIT),
    (("diff", "--name-only", "HEAD"), gr.SCOPE_WORKTREE),
    (("ls-files", "-z"), gr.SCOPE_NAMESET),
    (("ls-files", "--others", "--exclude-standard"), gr.SCOPE_WORKTREE),
    (("ls-tree", "-r", "HEAD"), gr.SCOPE_COMMIT),
    (("log", "--name-only"), gr.SCOPE_COMMIT),
    ((), gr.SCOPE_UNKNOWN),
])
def test_scope_comes_from_the_invocation_literals(args, scope):
    assert gr._git_scope(args) == scope


def test_starred_local_list_is_resolved():
    """``args = ["log", ...]`` then ``_git(*args)`` — missing this drops a COMMIT act."""
    acts = gr.acts_of("local_only_audit.pre_epoch_commits")
    assert any(a.verb == "log" and a.scope == gr.SCOPE_COMMIT for a in acts)


def test_unknown_name_token_claims_nothing():
    """The name vocabulary fails by under-detecting, never by mis-attributing."""
    assert gr.nominal_scope("unregistered_local_only") is None
    assert gr.nominal_scope("staged_declarations") == gr.SCOPE_INDEX


def test_revocable_tests_shape_not_direction(pool):
    """The honest limit on D-048's headline, and on this cycle's correction.

    ``revocable`` asks whether a population is a *difference*; it does not ask
    whether the forbidden act **empties** that difference or **fills** it.
    Committing a snapshot file empties ``undeclared_drift`` (the guard goes
    quiet — D-047) and fills ``staged_declarations`` (the guard fires).  Both
    match the shape; only the first is the failure.  So D-048's "one of 23"
    survives as a count of *failures* while being wrong as a count of *matches*.
    """
    shaped = {g.qualname for g in gr.unmirrored_revocable(pool)}
    assert shaped == {
        "tree_provenance.undeclared_drift",
        "local_only_audit.staged_declarations",
    }


def test_the_index_read_is_real_not_inferred(tmp_path):
    """Stage a declared local-only path; the guard named for it must fire.

    Structural findings are worth what the structure claim is worth, so both
    the defect and its fix are executed rather than argued.  Deleting the
    middle assertion silently restores D-047's blind spot.
    """
    import subprocess

    from eval.mppi_sandbox import local_only_audit as loa

    def git(*args):
        subprocess.run(("git", "-C", str(tmp_path), *args), check=True,
                       capture_output=True)

    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@t"); git("config", "user.name", "t")
    (tmp_path / "STATE.md").write_text("base\n")
    (tmp_path / "keep.txt").write_text("x\n")
    git("add", "-A"); git("commit", "-qm", "base")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    git("checkout", "-q", "-b", "autoresearch/x")

    (tmp_path / "STATE.md").write_text("violating edit\n")
    assert loa.staged_declarations(root=tmp_path) == [], \
        "an unstaged local edit is exactly what D-011 requires — not a violation"

    git("add", "STATE.md")
    assert loa.staged_declarations(root=tmp_path) == ["STATE.md"], \
        "D-049: as shipped by D-047 this returned [] and printed 'none committed'"

    git("commit", "-qm", "violation")
    assert loa.staged_declarations(root=tmp_path) == ["STATE.md"], \
        "the act D-047 did observe still fires"
