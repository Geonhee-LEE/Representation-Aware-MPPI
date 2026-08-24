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

    Comparing unparsed source found **one** mirror where D-048's population had
    three.  An undetected mirror promotes a sound guard into Q-063's answer set,
    so the bug inflated the finding rather than shrinking it — the rarer
    direction, and the reason it is pinned rather than trusted.  The count is 7
    since D-051 added :mod:`predicate_depth`, whose own checks contribute three
    mirrors; the historical statement is about D-048's population and stays as
    written.
    """
    found = gr.mirrors(pool)
    assert len(found) == 10
    by_source = {(a, b) for a, b in found
                 if _population_source(pool, a) in {_exemption_sources(pool, b)}}
    assert len(by_source) < len(found)


def _population_source(pool, qualname: str) -> str:
    return next(g.population for g in pool if g.qualname == qualname)


def _exemption_sources(pool, qualname: str) -> str:
    g = next(g for g in pool if g.qualname == qualname)
    return g.exemptions[0].expr


def test_mirrors_are_the_known_ten(pool):
    """Three at D-049, a fourth at D-050, three more at D-051, an eighth at D-101.

    ``guard_direction`` was written with ``unprobed_revocable`` /
    ``stale_probes`` as deliberate opposites — the population-vs-registry pair
    :mod:`tree_provenance` already had — and the mirror detector picked them up
    without being told, which is the cheapest available check that
    :func:`gr.mirrors` still means what D-048 said it means.

    D-051's three are the same shape a third time: ``predicate_depth`` derives
    its predicate population by glob and checks it against a typed adapter table
    in both directions, so ``unadapted_predicates`` mirrors the three functions
    that consume :func:`~eval.mppi_sandbox.predicate_depth.expr_predicates`.

    D-101's is the first pair whose second half was written **because** the
    first half entered the pool.  ``coverage`` started narrowing ``RESIDUE`` by
    membership in ``GRADED``, which left ``GRADED`` a typed allow-list with no
    enumerator; ``stale_grades`` is the enumerator owed for that, and it
    enumerates ``GRADED`` against ``RESIDUE`` — the opposite direction, so the
    detector pairs them without being told.  The pair is real rather than
    manufactured: one asks how much of the residue is graded, the other asks
    whether a grade has outlived its site, and neither answers the other's
    question.

    D-146's ``lam_window_key.attribution`` / ``table_shift_census`` is the
    tenth, and like the ninth it was **not** written to be found.  That cycle
    gave the census an ``arms`` scope so a controller column bought at one
    weight could not silently shrink a cross-weight denominator; the scope
    narrows the two tables' cell sets in the opposite sense from the way
    ``attribution`` narrows its contrast set, and the detector paired them
    without being told.  Two consecutive unintended pairs is the strongest
    evidence yet that :func:`gr.mirrors` is detecting a shape rather than a
    naming convention.

    D-107's ``inert_surface.entrants`` / ``departures`` is the ninth, and it is
    the cheapest evidence yet that the detector still means what D-048 said —
    because it was **not** written to be found.  The two exist because a stale
    pin's reader set has two deltas and the composition rule treats them
    asymmetrically (an entrant must be probed, a departure is monotone in the
    safe direction), so they narrow the same two sets in opposite senses without
    that ever being the intent.  It is also the pair STATE #1 has been asking
    for and not getting: ``cycle_artifacts.unsupported`` / ``disputed`` are a
    real mirror the detector misses, because they are spelled ``&`` and ``^``
    over the same two inputs rather than as a role swap.  These two got detected
    for their **spelling**, which is the same fact from the other side.
    """
    assert gr.mirrors(pool) == (
        ("candidate_scope.coverage", "candidate_scope.stale_grades"),
        ("citation_audit.missing_sites", "citation_audit.unregistered"),
        ("claim_scope.stale_coincidences", "claim_scope.unregistered_citations"),
        ("guard_direction.stale_probes", "guard_direction.unprobed_revocable"),
        ("inert_surface.departures", "inert_surface.entrants"),
        ("lam_window_key.attribution", "lam_window_key.table_shift_census"),
        ("local_only_audit.underived_declarations",
         "local_only_audit.unregistered_local_only"),
        ("predicate_depth.opaque_readings", "predicate_depth.unadapted_predicates"),
        ("predicate_depth.profiles", "predicate_depth.unadapted_predicates"),
        ("predicate_depth.stale_adapters", "predicate_depth.unadapted_predicates"),
    )


def test_q063_the_shape_occurs_twice_and_fails_once(pool):
    """Q-063 (b)'s answer, corrected by D-049 — and it is still a negative.

    D-048 read this as "of 23 guards, exactly one". Both halves were wrong and
    the conclusion was not. The **population** was short: admitting ``&`` as a
    filter (D-049) raises 23 → 28 and adds ``staged_declarations``, which is
    ``DIFFERENCE``-shaped and unmirrored, so the shape occurs **twice**. The
    **predicate** was short in the same place: :func:`revocable` asks whether a
    population is a difference, not whether the forbidden act *empties* it.
    Committing a snapshot file silences ``undeclared_drift`` — D-047's failure —
    and **fills** ``staged_declarations``, which is a guard working. So the count
    of *failures* is still one, and the lean ("a shape that exists once usually
    exists twice") is still rejected as a claim about failures.

    D-050 corrected the population a second time (28 → 30 for the same source)
    and the two-element answer survived both corrections: the guards the wider
    scan admits are all ``ENUMERATION``.
    """
    flagged = {g.qualname for g in gr.unmirrored_revocable(pool)}
    assert flagged == {
        "arrival_spread.separation_survives",
        # D-248's `arrival_spread.separation_survives` makes the count, and it
        # is the thirty-seventh consecutive cycle whose module entered the
        # registry it audits. Shape AND: `bool(comparisons) and all(...)`, the
        # non-vacuity clause conjoined with the reading itself -- so the two
        # operands are a population and a predicate over it, not two
        # populations. The module's actual conclusions are invisible for
        # D-079's familiar reason: `ArrivalComparison.verdict` branches on
        # numeric comparisons against a CI bound, and `censored` is a truth
        # test over two bools.
        "tree_provenance.undeclared_drift",
        "local_only_audit.staged_declarations",
        # D-105 adds two, and the membership grows without touching the claim.
        # `unsupported` is a difference an offender could collapse by emptying
        # `finding_grades()`; `report` by emptying `GRADES`.  Both are DERIVED,
        # so collapsing either takes the grader down with it — which is why the
        # count of *failures* is still one and the lean stays rejected.
        "cycle_artifacts.unsupported",
        "cycle_artifacts.report",
        # D-114 adds a fifth, and it is the first entrant that is a guard
        # **working**.  `unwatched_strandings` is `stranded - unsupported`, a
        # difference an offender could collapse by making every stranded cycle
        # lie — but the probe registered this cycle reads NAMES_OFFENCE on both
        # its subjects, so the shape is matched and the collapse is not the
        # observed mechanism.  Fourth member, third consecutive cycle to add
        # one, and the count of *failures* is still one.
        "cycle_artifacts.unwatched_strandings",
        # D-206's `carried_drift` adds a sixth, and it is the first whose
        # population is not an in-process registry at all: the difference is
        # `git diff --name-only base HEAD -- <carried>`, a subprocess call, and
        # the exemption is `NOT_IN entrants(candidate, src)` — the readers that
        # joined since the base probe, which by construction cannot have drifted
        # against it.  The shape is matched for the ordinary reason (a set
        # difference against a derived registry) and the count of *failures* is
        # still one, but the entrant is not yet a *reading*: it has no
        # `gd.PROBES` entry, so whether the forbidden act empties this
        # difference or fills it is unexecuted.  That is exactly the state
        # Q-065 was filed about, and it is recorded as outstanding here rather
        # than assumed benign — see Q-133.
        "inert_surface.carried_drift",
        # D-347's `scene_separability.format_tail_grade` adds a seventh, and it
        # is the first entrant that is not a guard at all: it is a **formatter**
        # (`reading == SCALAR`), and it entered on the strength of a dict
        # comprehension — `{o: worst_tail_extension(o) for o in
        # tail_extensions_by_observable()}` reads DIFFERENCE to `_is_set_valued`
        # because a comprehension over a call is the same syntax a set
        # difference wears. Nothing an offender does empties or fills it: the
        # population is recomputed from source on every call and the output is
        # a string nobody asserts on. So the count of *failures* is still one,
        # and the lean stays rejected — but for a new reason. The six prior
        # entrants were guards whose collapse was masked or working; this one
        # has no direction to execute because there is no reading to move.
        # That makes it the cleanest evidence yet for D-072's syntax result:
        # `revocable` is a claim about **spelling**, and a formatter written in
        # the spelling qualifies. Kept rather than exempted, per D-342's rule
        # that a formatter earns a test rather than a residue-list slot — an
        # exemption here would be a second statement of that rule.
        "scene_separability.format_tail_grade",
    }
    # D-248 adds `arrival_spread.separation_survives` as the seventh.
    # D-348's `scene_separability.format_tail_grade` is the eighth, and this pin
    # is the one that shows what an unaffordable file costs: the guard entered
    # when D-347 shipped, D-348 repaired the two `unmirrored_revocable` pins it
    # could see, and *this* count sat red through two further cycles because
    # nobody could pay 318s to run the file holding it (D-349).
    assert len(gr.revocable(pool)) == 8
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

    Four ``TYPED`` allow-lists have no module-level function enumerating them.
    All four are named in ``tests/``, so the finding is "no watcher in the
    layer this scan reads", not "unchecked" — the stronger claim would be
    false, and asserting the weaker one next to its own limit is the point.

    ``SELF_DEFINING`` (D-075) is the fourth, and it arrived one cycle after
    D-073's ``CARRIED_FIELDS`` did the same thing, for the same reason: naming
    an exclusion honestly turns it into a typed allow-list with no enumerator.
    Deliberately **not** fixed by writing a fifth watcher.  D-073 had to write
    one because ``CARRIED_FIELDS`` is a vocabulary that only a ``dir()`` over a
    round-tripped cell can confirm; ``SELF_DEFINING`` is different in kind —
    its single member is there because the value **equals its own band
    endpoint**, which is recomputable from the record on disk.  So the right
    repair is to derive the set rather than watch a typed copy of it, and that
    is Q-082 rather than a patch bolted onto this cycle's join.

    ``DECLARED_DEF_TIME`` (D-080) is the fifth, and it arrived *within one test
    run of being written* — the excuse list that answers Q-085 option (b) for
    ``guard_vacuity.EXCLUDED_TESTS`` is itself a typed allow-list with no
    module-level enumerator, so declaring one registry uncontrollable made
    another unwatched.  D-080 answered it the way D-079 asks rather than by
    writing a sixth watcher: the registry joined ``exemption_control.REGISTRIES``
    and got a tamper, so it is *controlled* even while it is unwatched.  The two
    are different properties and this pin only reports the second.

    ``RESOLVERS`` (D-275) is the sixth, and it repeats D-080's shape rather
    than adding one: `window_axis_reach` declared its resolver list instead of
    discovering it — deliberately, citing `lam_window_index.TABLES` — and a
    declared allow-list with no module-level enumerator is unwatched by
    construction.  The answer was D-080's too: the registry got a tamper in
    `exemption_control.TAMPERS` in the same repair, so it is **controlled**
    while unwatched.  Note that only one of D-275/D-276's declared lists
    arrives; `window_axis_migration.FORMS` is an enumeration of AST kinds that
    the module's own dispatch exhausts, so it has an enumerator and is watched.

    ``SITE_CLASSES`` and ``HULL_REPAIRED_BY`` (D-313) are the seventh and
    eighth, and they arrive together for one reason — D-312 built an instrument
    to audit extremum readings, and *"every instrument built to audit a
    population becomes a member of one"* is this package's most-reproduced
    finding.  They are **not** the same case as each other, and collapsing them
    would hide the more interesting half:

    * ``HULL_REPAIRED_BY`` is a genuine one-directional allow-list.
      :func:`extremum_reading.unrepaired_hulls` drops keys that appear in it
      and nothing puts them back — exactly the shape D-080 and D-275 describe.
      The answer is theirs unchanged: a control, not a ninth watcher, so
      *controlled* and *watched* stay distinct properties.
    * ``SITE_CLASSES`` is here because of a **limit in this scan, not a hole in
      that module**.  :func:`extremum_reading.sweep` computes the subtraction
      in *both* directions — ``found_keys - set(SITE_CLASSES)`` goes red as
      ``unregistered``, and ``set(SITE_CLASSES) - found_keys`` is reported as
      ``retired`` — against a population re-derived from the AST on every run.
      A list reconciled in both directions is not an exemption; the
      reconciliation **is** the watcher.  :func:`guard_reflexivity.exemption_watchers`
      cannot see it because it matches populations **by name**, and ``sweep``
      binds its re-derivation to a local called ``found``.  So the honest
      repair is to state the limit here rather than write a watcher that would
      only re-spell ``sweep`` under a name the matcher likes; whether
      ``exemption_watchers`` should match by *derivation* rather than by name
      is Q-090, not a patch bolted onto this cycle's strand-clearing.

    ``OBSERVABLES`` (D-338) is the ninth, and it is the first to arrive by a
    guard becoming **visible** rather than by a guard being written.  D-336's
    ``constant_at_every_index`` reached the same registry through
    ``_observables_of(t)``, so ``_provenance`` called it ``DERIVED`` and every
    ``TYPED`` screen — including this one — skipped it.  D-338 named the registry
    at the call site to clear
    :func:`predicate_depth.provenance_depth_exposure`, and the exemption became
    watchable; this entry is that screen reporting what it can now see.

    It is pinned here rather than repaired away, and the tension is worth stating
    because D-330's rule points the other way.  That rule says a *category*
    constant entering this population should be fixed by **deleting the
    membership test**, and ``observable in OBSERVABLES`` does look cosmetic: every
    caller draws its argument from ``OBSERVABLES`` already, so the test excludes
    nothing.  The reason it stays is that deleting it would not restore the prior
    state — it would drop ``constant_at_every_index`` out of the guard pool
    entirely (its other filter, ``_table_carries``, returns a bool and is not an
    exemption), trading a watched-but-unwatched-allow-list for a guard nothing
    scans at all.  Which of those two is the honest shape is **Q-165**, and it is
    a question about what a guard *is*, not a pin to bump under a clock.

    ``TTC_FAMILY`` (D-347) is the **second** member of the domain-declaration
    class D-340 opened, and the entrant that class was waiting on: D-340 found
    the class real with exactly one member (``OBSERVABLES``), so its rule was
    well-defined and untested, and said the next entrant would decide it.  Run
    D-340's own discriminant — *does any consumer supply the tested value from
    outside the registry?* — and the answer is no: the only two sites that test
    membership (``scene_separability.format_tail_grade`` and
    ``ttc_family_has_the_heavier_tail``) draw the tested name from
    ``_observables_of(table)``, i.e. from ``OBSERVABLES``/``CAUSAL_OBSERVABLES``
    themselves.  So it declares a category rather than excusing a case, the
    class now has two members drawn one cycle apart, and D-330's "delete the
    membership test" repair is declined here for a stated reason: the constant
    *is* the category, and deleting the test would re-type ``"min_ttc"`` and
    ``"ttc"`` at each call site, which is the exact duplication the constant was
    introduced to prevent.

    ``VOCABULARY`` (D-417) is the **third**, and it takes ``TTC_FAMILY``'s
    reasoning verbatim: it is the token set that *defines* what counts as a
    clearance-ensemble name in :mod:`source_reach`, so deleting the membership
    test would re-type ``"ENSEMBLE"``/``"CLEARANCE"`` at each call site. What
    makes it safe to leave unwatched here is that it is not unguarded — it is
    graded from the other side by :func:`source_reach.vocabulary_gap`, which
    fails if the vocabulary ever stops covering the registry it narrows. That
    is a weaker instrument than a tamper in ``exemption_control.REGISTRIES``,
    and promoting it there is the follow-up rather than a claim made here.
    """
    unwatched = gr.unwatched_exemptions(pool)
    assert set(unwatched) == {"DEGENERATE_READINGS", "SCOPED_CLAIMS",
                              "TEMPERATURE_RELEVANT", "SELF_DEFINING",
                              "DECLARED_DEF_TIME", "RESOLVERS",
                              "SITE_CLASSES", "HULL_REPAIRED_BY",
                              "OBSERVABLES", "TTC_FAMILY", "VOCABULARY"}
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


def test_and_shaped_guards_are_exactly_these_four(pool):
    """Pinned: a population correction is only worth its own exactness."""
    found = {g.qualname for g in pool
             if any(e.sense == gr.SENSE_AND for e in g.exemptions)}
    assert found == {
        "ab.ab_temperature",
        "guard_reflexivity.bite",
        "local_only_audit.staged_declarations",
        "exclusion_scope.rank_agreement",
        "simd_attribution.grade",
        # D-105: the intersection of the two dating keys.  The sixth `&`-shaped
        # guard, and the first whose two operands are *the same population read
        # two ways* rather than two populations — see Q-099.
        "cycle_artifacts.unsupported",
        # D-136: the seventh.  Isolating one factor means intersecting the cells
        # that share every *other* coordinate, so the `&` is the isolation
        # itself, not a correction applied to it — an empty intersection is
        # exactly the `NO_CONTRAST` the function refuses to call `FACTOR_INERT`.
        "lam_window_key.attribution",
        # D-146: the eighth.  A merge may only join tables that agree, so the
        # cells it emits are gated on the two headers' agreement and the two
        # cell sets' *dis*agreement — `&` over the cell keys is the refusal
        # (`DUPLICATE_CELL`), not a filter applied after one.
        "calibrate_lam.merge_tables",
        # D-174: the ninth.  Two null populations can only disagree about a
        # coefficient they both carry, so intersecting their `w_geom` keys *is*
        # the join — the frozen arm has no coefficient by construction and must
        # not be matched against a ladder rung.  Entering this registry is what
        # surfaced `LICENCE_NO_OVERLAP`: without it an empty intersection
        # returns "no disagreements" from a comparison that never ran.
        "admissibility_selection.licence_split",
        # D-289: the tenth, and the first from `calibrated_ladder` in four
        # consecutive entrants from that module.  Only seeds walked at *both*
        # interior rungs can carry a direction (D-019), so `set(at[lo_w]) &
        # set(at[hi_w])` **is** the pairing rather than a filter applied after
        # one — the same shape D-136 registered, arriving on the seed axis.  The
        # three prior entrants were all non-`&` and each said so; this one ends
        # that run, which is why the AND set moves for the first time since
        # D-174.
        "calibrated_ladder.census_ladder",
        # D-386: the eleventh.  A scene can only carry a *cross-column*
        # inference if both columns are pinned on it, so intersecting the two
        # harvest registries **is** the population — an empty intersection is
        # not "no scenes agree" but "no scene could have agreed or disagreed",
        # which is the distinction D-385 paid for one level down.  The result
        # is a population of one (`cafe_convoy_v0`), and the `&` is why that
        # number is legible at all: a scene-keyed union would have reported
        # five excited clearance cells as five candidate endpoints.
        "tail_mean.both_columns_scenes",
        # D-419: the twelfth, and it is here because D-417's note below was
        # **wrong about this set** — see the correction there.
        "source_reach.vocabulary_gap",
    }
    # D-412 entered the pool but **not** this set: `bottleneck_scope.scope`
    # exempts by `IN` over a derived name set, not by `&`, so the AND registry
    # is untouched and the red was the count alone.
    # D-417 enters **two**: `source_reach.vocabulary_gap` (a `&` over the
    # registry's own constant names — the AND shape D-049 admitted) and
    # `source_reach.format_grade`.  `format_grade` is a printer and does not
    # join the AND registry set above.
    #
    # **D-419 corrects the other half of this note.** D-417 also wrote that
    # `vocabulary_gap` does not join, on the reasoning that its `&` screens a
    # *name token* rather than exempting a population member.  That reasoning
    # describes what the `&` means; the set above is derived from what the `&`
    # **is**, and the deriving scan does not read intent.  The suite settled it
    # against the prose: `vocabulary_gap` was the sole extra item.  The lesson
    # is D-072's syntax result once more — a hand-written argument for why a
    # construct is *morally* not AND-shaped has no purchase on a census that
    # matches on shape, and the census is the thing that ships.  The census of the
    # census becomes a member of the census it audits — D-312/D-313 for the
    # seventeenth time, and this cycle paid 0.3 s for it instead of a suite.
    assert len(pool) == 140, (
        "**Back to 140, and the round trip is the entry.** D-463 overwrote "
        "`ci_verdict.py` with a same-named, disjoint module; `ci_verdict.read_run` "
        "left the pool and the tally read 139 — the first DEPARTURE this census "
        "had ever recorded, every prior move being an entrant, which is why the "
        "prose below reads as a running addition. D-465 restored the vocabulary "
        "and gave D-463's content its own name (`run_completeness`), so the "
        "departed member returned and the count is 140 again. Three things follow. "
        "(i) The tally is a *size*, not a composition (D-461 follow-up), so -1 "
        "and +1 are indistinguishable to it; both the departure and its reversal "
        "were identified by diffing the pool across commits, not by reading this "
        "number. (ii) The drift was authored by the very commit that was sitting "
        "unpushed — 2026-08-25 07:00 found it via `census_preempt` in ~2 s while "
        "clearing the strand, which is D-199/D-318's case made twice over: the "
        "guard fires before the push gate, and a stranded commit can carry a red "
        "that no one has met yet. (iii) `run_completeness` entered the package "
        "carrying four population-shaped functions and added **nothing** here — "
        "`failing_tests`, `failure_floor`, `unverdicted` and `ceiling_breaches` "
        "all narrow by equality against a verdict, D-079's invisible spelling, "
        "now for a sixth module. A rename that restores one guard and admits a "
        "whole new instrument for free is the sharpest available restatement of "
        "D-073's caveat: this number counts spellings, not instruments. "
        "D-048 judged 23; admitting `&` (D-049) gives 28; resolving set-valuedness "
        "one frame down (D-050) gives 30 for that same source, plus `guard_direction`'s "
        "own two checks = 32; D-051's `predicate_depth` adds six = 38; D-052's "
        "`exemption_masking` adds `masking_candidates` and `unscreened` = 40; "
        "D-053's `probe_reach` adds `reach_gap` = 41; D-054's `liveness_derivation` "
        "adds `mutable_scope` and `unranked_scopes` = 43; D-056's `act_gap` — the "
        "honest denominator `reach_gap` stood in for — makes 44. "
        "Seventh consecutive cycle whose module entered the registry it audits; the "
        "tally is kept as a running one because that recurrence is the finding. "
        "D-056's other new function, `misscored_probes`, did *not* enter, and the "
        "reason is worth the line: it restricts to a population whose answer is "
        "known (`r.guard in PROBES`) rather than exempting from one. That is what "
        "lets it be pinned empty — an exemption-shaped guard never can be. "
        "D-461's `d_enc_consumers.consumers` makes 140 — the Q-200 consumer "
        "census, whose own derived population is a guard, so it joined the "
        "registry it was written to audit. `census_preempt` returned this in "
        "~2 s before the suite; the same finding costs a 20-minute red run "
        "when it is discovered at the push gate instead (D-199/D-318). "
        "D-060's `guard_witness` adds `unwitnessed` and `stale_witnesses` = 46, "
        "the **ninth** consecutive cycle and the first to add a guard the "
        "`exemption_masking` screen cannot call: `unwitnessed`'s population is a "
        "coverage run, not a syntax-tree read, so it has no free default and "
        "screens UNRUNNABLE (see `test_no_pair_is_left_unscreened`). "
        "D-063's `exclusion_scope` adds `unresolved_subjects` and "
        "`corrected_candidates` = 48 — the **twelfth** consecutive cycle, and the "
        "recurrence is now itself the most-reproduced finding in this package: "
        "every instrument built to audit a population becomes a member of one. "
        "D-064's `predicate_vacuity.fold` makes 49 — the **thirteenth** consecutive "
        "cycle, and the first member that is not an auditor. The previous twelve "
        "exempt a population from the reading they then publish; `fold` *is* the "
        "exclusion — it applies `--ignore` as a set difference over recorded "
        "observations, which is the whole of D-064. So the recurrence is wider than "
        "'instruments audit themselves': the shape the detector keys on is a set "
        "difference against a named registry, and implementing an exclusion has it "
        "as surely as auditing one does. Whether that widens the finding or dilutes "
        "the detector is not settled here. "
        "D-065's `exclusion_scope` adds `surviving` and `voided_leaders` = 51 — the "
        "**fourteenth** consecutive cycle, and the first where the same cycle's other "
        "two new functions stayed out. `rerank` and `corrected_shift` take the "
        "population as an argument and rank it; `surviving` and `voided_leaders` "
        "difference it against `manufactured_candidates`. Both pairs implement one "
        "correction and only the differencing half is visible to the detector, which "
        "is the sharpest available restatement of D-056's `misscored_probes` note: "
        "the detector keys on *how* a population is narrowed, not on whether the "
        "narrowing is the kind that hides a finding. "
        "D-066's `predicate_inputs.fold_inputs` and `exclusion_scope.input_undercounts` "
        "make 53 — the **fifteenth** consecutive cycle, and it sharpens D-065's "
        "restatement once more rather than repeating it. Five of that cycle's seven "
        "new functions stayed out, and the one whose absence says the most is "
        "`corrected_inputs`: it *is* the correction D-066 exists to make — the "
        "exclusion applied per subject instead of per file — and the detector cannot "
        "see it, because it computes a **per-site fold** rather than differencing a "
        "population against a registry. `fold_inputs` enters for `pv.fold`'s exact "
        "reason (it applies `--ignore` as a set difference) and `input_undercounts` "
        "for the twelve auditors' reason. So the detector's blind spot is now "
        "characterised twice over: it misses a narrowing that is *parameterised* "
        "(D-065's `rerank`) and a narrowing that is *per-member* (this one), and "
        "catches only the narrowing that names a registry. Whether that is a finding "
        "about instruments or an artifact of the detector's shape is still not "
        "settled — but the question has now survived three cycles of evidence. "
        "D-072's `exclusion_scope.rank_agreement` makes 54 — the **sixteenth** "
        "consecutive cycle, and it settles the question above against the "
        "instruments and *for* the detector's shape. Two reasons, and the second "
        "is the sharper. First, it is the fourth `&`-shaped guard and the first "
        "whose intersection names **no registry on either side**: `set(a) & set(b)` "
        "over two readings' sites, both runtime data. So the three-cycle "
        "characterisation — 'catches only the narrowing that names a registry' — is "
        "false as stated; what the detector actually keys on is the `&` operator. "
        "Second, and this is the demonstration rather than the claim: the same "
        "cycle's `published_ratios.common_sites` performs the **identical** "
        "intersection over the identical kind of operand, spelled "
        "`set.intersection(*sets)`, and does **not** enter. One narrowing, two "
        "spellings, one of them visible. That is not a blind spot about *how* a "
        "population is narrowed (D-065) or about per-member folds (D-066) — it is "
        "the detector reading syntax where three cycles of commentary have been "
        "reading semantics into it. The recurrence is still real; the explanation "
        "offered for it since D-065 is not. "
        "D-073's `reading_record.would_have_carried` makes 55 — the **seventeenth** "
        "consecutive cycle, and it is D-072's syntax finding again at a level that "
        "costs something. The guard filters `in CARRIED_FIELDS`, an ordinary "
        "`IN`-shaped narrowing against a registry, and whether it is a guard at all "
        "turns on how the *constant* is written: `CELL_FIELDS + DERIVED_FIELDS` is a "
        "`BinOp` of two names, `_is_set_valued` says no, and the pool reads **54** "
        "with the guard sitting in plain sight. `tuple(CELL_FIELDS + DERIVED_FIELDS)` "
        "is the same value through a `_SET_CALLS` call and the pool reads 55. "
        "Measured both ways in-cycle, not argued — see "
        "`test_reading_record.test_the_scan_is_blind_to_a_concatenated_registry`. "
        "D-072's two spellings were `&` and `set.intersection`, one of which is "
        "unusual; these two are `A + B` and `tuple(A + B)`, and the invisible one is "
        "how a registry assembled from two other registries is *normally* written. "
        "So the detector's dependence on form is not a curiosity about exotic "
        "spellings — it is reachable by writing the idiomatic thing, which makes "
        "every 'exactly N' this pin has carried a count of the guards that happened "
        "to be spelled visibly. "
        "`reading_record.uncarried_fields` makes 56, and it is the *second-order* "
        "cost of that fix rather than another instance of the recurrence: making "
        "`CARRIED_FIELDS` visible as a registry immediately made it an **unwatched** "
        "one (`unwatched_exemptions` went from three to four), because a TYPED "
        "allow-list with no module-level enumerator is exactly D-047's state. So the "
        "watcher had to be written, and writing it added a guard, which is the "
        "package's own loop in miniature: every audit surfaced here costs a member. "
        "Its exempting set is *derived* — `dir()` over a cell that has actually been "
        "round-tripped — so `CARRIED_FIELDS` is watched by a measurement rather than "
        "by a copy of itself, which is the only version of this that closes D-045 "
        "instead of restating it. "
        "D-075's `magnitude_survival` makes **60** — the **eighteenth** consecutive "
        "cycle, and the largest single-cycle addition since D-051's six. Four at "
        "once, and the split among them is the finding rather than the count. "
        "`standings`, `unbanded` and `movements` all narrow against `banded` — a "
        "**local dict built two lines up**, not a module registry, not typed, not "
        "even module-scoped. `published` narrows against `SELF_DEFINING`, which is "
        "a module global. So D-072's syntax result holds at its strongest form yet: "
        "the detector keys on the `in` / `not in` operator and nothing else, and "
        "three of these four would be invisible to any characterisation that "
        "mentions registries at all. Note what this does to the recurrence's usual "
        "reading — 'every instrument built to audit a population becomes a member "
        "of one' has been the standing gloss since D-063, but a join that filters "
        "`if site in banded` is not auditing anything; it is skipping sites the "
        "band cannot grade. The shape is a guard; the intent is not. "
        "`SELF_DEFINING` also arrives **unwatched** (`unwatched_exemptions` three "
        "to four again), which is D-073's second-order cost repeating one cycle "
        "later for the same reason: naming an exclusion honestly makes it a typed "
        "allow-list with no enumerator. Not fixed here — see Q-082 — and the "
        "difference from D-073 is that this one *can* be derived away rather than "
        "watched, because the circular value is recomputable from the record. "
        "D-076's `readings`, `over_derivation` and `exemption_bite` make **63** — "
        "the **nineteenth** consecutive cycle, and the first where the additions "
        "come from a cycle that went looking for the *previous* cycle's addition. "
        "Q-082 asked whether to watch `SELF_DEFINING` or derive it; measuring both "
        "cost three new guards, which is a worse ratio than the fifth watcher it "
        "was trying to avoid. That is not an argument against the measurement — "
        "the measurement found the typed exemption removes **0 of 22** and the "
        "derivation manufactures **2 false positives** — but it does price the "
        "standing gloss one more time: the pool grows by auditing the pool, and "
        "declining to audit is the only move that does not grow it. D-077's `magnitude_census.uncovered` makes **64** --- the **twentieth** consecutive cycle, and the first in three where the addition costs nothing second-order. Both of its exemptions are `DERIVED` (`set(transcribed(cells))` and a comprehension over `novel(...)`), so `unwatched_exemptions` stays at four; D-073 and D-075 each pushed it three-to-four by naming an exclusion as a typed module global with no enumerator. Same recurrence, cheaper instance, and the reason is spelled in the guard: a narrowing computed by calling something is watched by whatever watches that something. Note also what did *not* enter --- `printing`, `novel`, `precision` and `census` are the module's other four population-shaped functions, and all four dedupe or count rather than difference, which is D-072's syntax result holding for a twentieth cycle without needing a new gloss. D-079's `exemption_control.uncontrolled` makes **65** --- the **twenty-first** consecutive cycle, and it is the cheapest instance yet on both axes. Only one of that module's three population-shaped functions entered: `uncontrolled` narrows `REGISTRIES` by `not in covered`, so the detector sees it; `inert` and `unreachable` narrow by **equality against a verdict string constant** (`== VERDICT_INERT`, `!= CALL_TIME`), and the detector does not. That is D-072's syntax result at its plainest --- the three functions are the same *kind* of thing (each publishes a residue of a declared population) and only the one spelled with a membership operator is visible, with no appeal to registries, per-member folds or parameterisation needed to explain the split. Second-order cost is again nil: `covered` is DERIVED from `TAMPERS`, so `unwatched_exemptions` stays at four, for D-077's reason exactly. D-080's `exemption_control.undeclared_unreachable` makes **66** --- the **twenty-second** consecutive cycle, and the first in four whose second-order cost is *not* nil: its exempting set `DECLARED_DEF_TIME` is a TYPED module global with no enumerator, so `unwatched_exemptions` went four-to-five within one test run of the registry being written, and `exemption_masking`'s screened pairs went 17-to-18. Declaring a registry uncontrollable is itself an exclusion, and the package charges for it at the same rate as any other. D-081 adds **nothing**, and that is this cycle's entry rather than an absence: `key_conflation`'s two population-shaped functions, `conflating` and `unprobed`, both narrow a probe set by **equality against a verdict string** (`== VERDICT_IDENTICAL`, `== VERDICT_VACUOUS`) --- D-079's exact invisible spelling, reproduced one cycle later in a module written without reference to it. So the twenty-two-cycle recurrence pauses here for a reason that has nothing to do with the instrument having stopped auditing populations: it audits one, publishes two residues of it, and the detector sees neither. Every 'exactly N' this pin has carried remains a count of the guards that happened to be spelled visibly (D-073), and this is the first cycle where the invisible spelling accounts for **all** of a module's guards rather than some of them. D-083's `inert_surface.readers` makes **67** --- the **twenty-third** consecutive cycle, and it is the first addition the package charged for *retroactively*: the guard entered at 13:00, the pin was never re-run, and the 14:00 cycle committed it and stacked another commit on top, so the count sat wrong through two cycles and was found by the 15:00 push gate rather than by the test. The addition itself is the cheap kind --- `readers` narrows `src.items()` by `rel not in direct`, a DERIVED exemption, so `unwatched_exemptions` is unmoved --- but the *interesting* member is the one that stayed out. `inert` is the function the whole module exists to publish, and it narrows by `verdict == VERDICT_INERT`: D-079's invisible spelling for a third consecutive cycle, in a third module written without reference to the previous two. The detector now has a two-cycle record of missing precisely the function each new instrument is built around, which is a sharper statement of D-073's caveat than any of the twenty-two visible additions were. D-087's `ci_verdict.read_run` makes **68** --- the **twenty-fourth** consecutive cycle, and the first whose visible member is neither an audit nor an exclusion. `read_run` narrows `_PRECEDENCE` by `if v in present`: that is the module's **primary computation**, an argmax picking the highest-ranked verdict actually observed, and it publishes the answer rather than a residue of anything. D-064 widened the recurrence from 'instruments audit themselves' to 'implementing an exclusion has the shape as surely as auditing one does'; this widens it again, because a *ranking* is neither. What the detector keys on is the membership operator (D-072), and a fold over an ordered registry is simply how one writes an argmax --- so the twenty-four-cycle streak is now better read as a fact about `in` than about instruments. The module's other three population-shaped functions are the counter-evidence, and they are D-079's invisible spelling for a **fourth** consecutive cycle: `failed_jobs`, `ceiling_breaches` and `ceiling_warnings` each publish a residue of the job population --- exactly the auditing shape the gloss describes --- and all three narrow by equality against a verdict (`== FAIL`, `.at_ceiling`), so the detector sees none of them. Four functions, one visible, and the visible one is the only one not doing what the recurrence claims. Second-order cost is nil: `present` is DERIVED from the readings, so `unwatched_exemptions` stays at five. D-089's `nested_suite_cost.unresolved_sites` makes **69** --- the **twenty-fifth** consecutive cycle, and it is D-079's split reproduced for a **fifth** time with the cleanest possible instrument. Three population-shaped functions; exactly one entered. `unresolved_sites` narrows by `s.key not in resolved`, so the detector sees it --- and it is the module's *least* important function, a residue carried only so an unread site never counts as a cleared one. The two that matter are invisible: `doomed_sites` narrows by `grade(...) == DOOMED` and `unreported` by `e.is_red`, both equality-against-a-verdict, and `doomed_sites` is the function the whole module exists to publish. That is now the **third** consecutive cycle (D-083, D-087, this one) in which the detector missed precisely the headline function of the new instrument while admitting its bookkeeping, and the pattern is no longer plausibly coincidence: an instrument's *conclusion* is naturally spelled as a verdict comparison, while its *caveats* are naturally spelled as set differences, so the detector systematically counts the caveats and misses the conclusions. Every 'exactly N' this pin has carried is a count of guards spelled visibly (D-073); it is now also, more specifically, a count weighted away from the functions the modules were written for. Second-order cost is nil: `resolved` is DERIVED from `suite_runners()`, so `unwatched_exemptions` stays at five. "
        "D-090's `nested_subject.spawners` and `nested_subject.subject_files` make **71** --- the **twenty-sixth** consecutive cycle, the first two-member addition since D-075's four, and the **fourth** consecutive instance of the headline-missed split (D-083, D-087, D-089, this one). Five population-shaped functions; the two that entered are both bookkeeping. `spawners` narrows by `name not in found` --- an accumulator in a fixed-point loop, i.e. the loop's own termination test --- and `subject_files` by `p.resolve() not in skip`, which is the `--ignore` list the census already pays for. The function the module exists to publish is `spawning`, and it narrows by `v == SPAWNS`: D-079's invisible spelling, unchanged, for a **sixth** module. So the prediction D-089 made one cycle earlier --- that conclusions get spelled as verdict comparisons and caveats as set differences, and the detector counts only the latter --- was written down before this module existed and held without adjustment. That is the first time the recurrence has been *predicted* rather than observed after the fact, which is a different epistemic status from the twenty-five instances behind it and the reason this entry is worth its length. Second-order cost is nil on the usual axis --- neither exempting set is a typed module global, so `unwatched_exemptions` stays at five --- but **not** nil on Q-069's: both land in `NO_REGISTRY` (10 -> 11 counts only `subject_files`, whose exempting set arrives through the *call signature* and so is unreachable by any module-scoped derivation; see `test_liveness_derivation`). "
        "D-091's `census_narrowing.contributions` makes **72** --- the **twenty-seventh** consecutive cycle, and the **fifth** consecutive headline-missed split, predicted for the **second** time running. `contributions` narrows by `if origin in drop`, which is bookkeeping: a per-origin tally of what the narrowing would remove. The function the module exists to publish is `compare`, and it narrows by `b.verdict != a.verdict` --- D-079's invisible spelling in its purest form, since a *verdict comparison* is now literally the operator, for a **seventh** module. D-089's rule (conclusions spelled as verdict comparisons, caveats as set membership) has now been written down in advance and held twice, so it has stopped being a retrospective gloss and become a usable predictor. Second-order cost is nil on both axes: `drop` is a `set()` over the function's own argument, so it is neither a typed module global (`unwatched_exemptions` stays at five) nor a new `NO_REGISTRY` member (11 -> 11, the first cycle in four to add nothing on Q-069's axis). "
        "D-098's `simd_attribution.grade` makes **73** --- the **twenty-eighth** consecutive cycle, and the **first in six** where the detector caught the module's *headline* function instead of its bookkeeping. The five-cycle streak (D-083, D-087, D-089, D-091 and the gloss written in advance for each) said conclusions are spelled as verdict comparisons and caveats as set membership, so the detector counts the caveats. `grade` is the conclusion --- it is the function that decides whether the census may be reported as an answer --- and it entered. But the split has not been refuted, it has moved *inside one function*: `grade` has four branches, and three of them are D-079's invisible spelling (`values == {UNREPRODUCED}`, `values <= drift`, and the `unmeasured(...)` truth test), while the fourth, `not (values & drift)`, is D-072's visible operator. The detector sees one quarter of the function it correctly admitted. So the twenty-eight-cycle recurrence is intact and the prediction rule survives with a caveat it did not have before: visibility is a property of *branches*, not of functions, and a headline function becomes visible as soon as any one of its cases happens to be spelled with a membership operator. What did **not** enter is the counter-evidence: `unmeasured` narrows `attributable(census)` by `f.test_id not in verdicts` --- a `not in`, the visible spelling --- and is absent, because its population is a call result and its exempting set a parameter rather than a named registry. Second-order cost is nil on both axes: the exemption is INLINE (`unwatched_exemptions` stays at five) and adds no `NO_REGISTRY` member (11 -> 11), the second consecutive cycle to cost nothing beyond the count itself. "
        "D-099's `drift_repair.routes` makes **74** --- the **twenty-ninth** consecutive cycle, and the headline-missed split is back and **predicted for the third time running**. `routes` narrows by `if verdict not in drift`, which is the loop filter: it decides which rows get priced, and publishes no conclusion. The function the module exists for is `price_widening` --- it is the one that returns which repair route is admissible --- and it is invisible, spelled as three shape comparisons (`a.shape == CATEGORICAL`, `== THRESHOLD`); `grade` is invisible too, narrowing by a truth test on `refused(...)`. So D-098's within-function caveat was the exception and D-089's across-function rule is the regularity: three of four population-shaped functions here are conclusions spelled as equality, and the one visible member is bookkeeping. One detail is sharper than the count. The single expression the detector sees in this module is `{sa.DRIFT_CONSISTENT, sa.DRIFT_SHAPED}` --- **the same two-element inline set** whose `&` made D-098's `grade` visible one cycle earlier, now spelled `not in`. Two consecutive modules, two different operators, one literal, and it is the only thing either module contributed to the pool. That is D-072's syntax result at its narrowest yet: what the pool has been counting for two cycles is not a kind of function but a particular set literal appearing in whatever position happens to be visible. Second-order cost is nil on both axes: the exemption is INLINE (`unwatched_exemptions` reads five, measured) and every other census pin in the same suite run held. D-101's `candidate_scope.coverage` and `candidate_scope.stale_grades` make **76** --- the **thirtieth** consecutive cycle, a two-member addition, and the first where one new member exists **only because the other one entered**. `coverage` became visible by accident of a repair: it used to read `len(GRADED), len(RESIDUE)` and now narrows `residue` by `if s in table`, because the table is a per-call parameter and the count has to be over the intersection. That single operator turned `GRADED` into a TYPED allow-list with no module-level enumerator, so `unwatched_exemptions` went five-to-six --- D-073's and D-080's second-order cost, third instance --- and the watcher owed for it, `stale_grades`, is itself population-shaped and enters the pool too. So the cost of one visible guard is measured here as **two** pool members, not one, and `unwatched_exemptions` is back to five only because the second was written in the same cycle. Everything this module was actually written for stayed invisible, which is D-089's across-function rule for a fourth prediction: `reading` reads `table.get(site, UNREAD)` with no membership at all, `of_grade` narrows by `g == kind`, `self_hiders` by `es.subject_of(f) == module`, and `self_entry_is_impossible` and `run_free_reading` by truth tests over those. Five conclusions, none visible; two pieces of bookkeeping, both visible, one of them conjured by the other. D-102's `assert_reach.classify` makes **77** --- the **thirty-first** consecutive cycle, and D-089's across-function rule holds for a **fifth** prediction written in advance. Exactly one member entered, and it is not the module's conclusion. `shielded` is the function `assert_reach` exists to publish --- it decides which assertions no run has evaluated --- and it narrows by `if ordinal <= at`, an **ordinal comparison**, which is a spelling the detector has not met before and does not see. `failing_ordinal`, `moved` and `unpinned` are invisible for D-079's familiar reason (equality against a recorded line, truth tests). What the detector caught is `classify`, a grader whose visible expression is `test.func.attr in (\"issubset\", \"issuperset\")` --- an inline tuple of two strings, in the one branch of the function that happens to use membership; the other four branches are `isinstance` and operator-type comparisons and are invisible, which is D-098's within-function caveat recurring. So the pool grew by one and the growth is again a fact about a spelling: this module contributed a two-element inline literal in membership position, for the **third** consecutive cycle that this is the only thing a new module contributes. Second-order cost is nil on both axes --- the exemption is INLINE, so `unwatched_exemptions` stays at five, and no `NO_REGISTRY` member is added. D-103's `loop_reach.report` makes **78** --- the **thirty-second** consecutive cycle, and it is the first member the package charged for *twice retroactively*: the guard entered when D-103 shipped, the pin was never re-run, the cycle never pushed, and this count sat wrong until D-104 ran the pin for an unrelated reason. `report` narrows by `if r[1] in UNEVALUATED` --- bookkeeping, a per-grade tally in the printed summary --- while the function `loop_reach` exists to publish is `run`, which grades by `hits == 0` / `hits == 1`, and `census`, which counts. So D-089's across-function rule holds for a **sixth** prediction written in advance: the conclusion is spelled as equality and is invisible, the caveat is spelled as membership and is counted. What is new is the second-order cost, and it is the most expensive instance yet **and** the first that was mispriced in the safe direction. `UNEVALUATED` shipped as `frozenset({NOT_RUN, EMPTY})` --- a TYPED allow-list with no module-level enumerator, so `unwatched_exemptions` went five-to-six within one test run of being written, D-073 / D-080 / D-101's cost for a **fourth** time, and this time it was left standing rather than paid in-cycle. D-104's repair is D-077's cheap one (derive rather than watch): `unevaluated_grades()` recomputes the set by calling `grade` on two zero-element probes, so it is watched by whatever watches the grader. But the *spelling* of that repair was measured rather than chosen, as D-073 measured its own: `UNEVALUATED = unevaluated_grades()` makes `_is_set_valued` say no and `report` **leaves the pool entirely**, so the pin reads 77-unchanged and D-103's cost reads as **nil** --- a repair that deletes the guard from the census instead of paying for it. Naming the derivation at the call site (`in unevaluated_grades()`) keeps the guard visible at 78 and reads DERIVED, because `_provenance` asks its question at the site (Q-067 / D-052 option b) and any module-level set constant reads TYPED however it was computed. Three spellings of one set, three different census readings, and only one of them is both counted and watched. That is D-073's syntax result at its most consequential: the previous instances made a guard visible or invisible, this one decides whether a *repair* is recorded as a payment or as a disappearance. D-104's own two new functions --- `simd_attribution.located` and `unlocated` --- add **nothing**, and the reason is D-079's invisible spelling for a seventh module: both narrow by a truth test on an attribute (`f.located`, `f.attributable and not f.located`). D-105's `cycle_artifacts.unsupported`, `cycle_artifacts.report` and `cycle_artifacts.tsv_rows` make **81** --- the **thirty-third** consecutive cycle, a two-member addition, and the first time D-089's across-function rule is broken **on purpose** rather than by accident of spelling. The rule (conclusions spelled as verdict comparisons and so invisible, caveats spelled as membership and so counted) held for six consecutive predictions. Here the module's headline function `unsupported` --- the one that publishes which cycles claimed a TSV row they never appended --- **entered**, and it entered because D-104 prescribed the spelling one cycle earlier: its repair for an unwatched typed allow-list is to derive the set and *name the derivation at the call site*, which puts `g in finding_grades()` inside the conclusion. So the visible operator is not a coincidence of how the author happened to write a filter; it is what following the previous cycle's accepted repair produces. D-089's rule is about the *natural* spelling of a conclusion, and D-104's repair is a rule that overrides the natural spelling --- the two are now in tension, and this is the first cycle where the tension is visible in the count. Everything else in the module is invisible for D-079's familiar reason: `grade_tsv` (the grader) branches on string equality, `published` and `unpublished` narrow by `is False` truth tests, and `assignment` and `census` count rather than difference. `report` enters as the usual bookkeeping member, a per-grade tally in the printed summary. `tsv_rows` enters as a third member once the two dating keys are separated (`if key == ...` narrowing over `KEYS`), and `unsupported` changes shape from IN to **AND** because it became the *intersection* of the two keys' flags --- the sixth `&`-shaped guard, and the first whose two operands are one population read two ways rather than two populations (Q-099). Second-order cost is nil on both axes: all three exemptions read DERIVED (`finding_grades()` is a call, `GRADES` and `KEYS` are watched), so `unwatched_exemptions` stays at five --- but only after the first cut shipped `FINDING_GRADES = frozenset({'UNSUPPORTED'})` as a typed module global and drove it five-to-six within one test run, D-073 / D-080 / D-101 / D-103's cost for a **fifth** time, paid in-cycle this time rather than left standing. D-106's `cycle_artifacts.unsupported_by` and `guard_direction.unprobeable_revocable` make **84** with `probe_reach.misscored_probes` --- the **thirty-fourth** consecutive cycle, a three-member addition, and the first in which two of the members exist only so another member can be probed. `unsupported_by` is `unsupported` with the second dating key's agreement suppressed --- the `read_unexempted` half the probe needs; `unprobeable_revocable` is the enumerator owed for the obligation's new exclusion, and it narrows `revocable(pool)` by `qualname in scalar`, so naming an exclusion is population-shaped for a second time after D-064 said so. `unsupported_by` is written as a call into `_flagged` rather than as a second copy of the grading, for the reason every `read_unexempted` in that module is written that way: a re-implementation is a second statement of the rule, which is what D-045 and D-047 each are. So the recurrence widens again. D-064 widened it from 'instruments audit themselves' to 'implementing an exclusion has the shape'; D-087 to a ranking; this adds a fourth kind --- the **apparatus for executing a guard is itself population-shaped**, because reading a population with one filter removed is still reading a population with a filter. Second-order cost is nil on both axes: the exemption is DERIVED (`_flagged` is a call), so `unwatched_exemptions` stays at five, and no mirror pair is created or destroyed. The third member is not a new function at all, and it is D-073's syntax result arriving with the sharpest possible provenance: `probe_reach.misscored_probes` has been in the package since D-056 and this pin's own text says, nine cycles' worth of prose above, that it *did not enter* --- because it restricted by `r.guard in gd.PROBES`, a cross-module attribute `_is_set_valued` does not resolve. Narrowing its population to the probes that share this fixture is one line, and the line binds a local (`covered = set(gd.shared_fixture_probes())`) --- which makes the same membership test visible and the guard enters. So a sentence written to explain a *permanent* absence was falsified by a spelling change that altered nothing about what the function computes, which is exactly what D-073 said every 'exactly N' here is worth. What did **not** enter is worth the same line as always --- `guard_reflexivity.scalar_readings` and `revocable_collections` narrow by `g.reading == READING_SCALAR` --- D-079's equality-against-a-verdict spelling for an eighth module, and the two functions this cycle was actually written around are again the invisible ones. `guard_direction.own_fixture_probes` and `shared_fixture_probes` are invisible for a different reason again: they narrow `PROBES.items()` by `p.build is not None`, an identity test. D-107's four `inert_surface` members make **88** --- the **thirty-fifth** consecutive cycle, and the largest single-module addition since D-051, but the count is less interesting than the split. Two are new functions: `entrants` and `departures`, which narrow the live reader set against the pin's recorded one in opposite senses. Those two are also the ninth **mirror**, and they are the strongest evidence yet that `mirrors` still means what D-048 said, because unlike D-101's pair they were not written to be one --- the composition rule simply treats the two deltas asymmetrically (an entrant must be probed, a departure is monotone in the safe direction) and the role swap falls out. Set that beside STATE #1's standing debt: `cycle_artifacts.unsupported` / `disputed` are a *real* mirror the detector misses because they are spelled `&` and `^` over the same two inputs instead of as a role swap. One pair detected for its spelling, one pair missed for its spelling, in the same pool --- D-072's syntax result stated from both sides at once. `reprobe` is the third and is ordinary bookkeeping (it partitions the readers into probed and carried). The **fourth is not a new function at all**, and it is D-106's `misscored_probes` phenomenon recurring one cycle later with no gap: `probe` has been in this package since D-095 and stayed out of the pool; adding a `tests` subset parameter and its guard clause (`set(tests) <= set(named.all)`) changed **nothing** about what the function computes and made the narrowing visible. Two consecutive cycles in which a pool member entered by spelling rather than by existing is no longer a curiosity about one function --- it is the running cost of a syntactic census, and the alternative (a census that reads intent) is the one thing D-072/D-073 established this package will not buy. Second-order cost is nil on both axes: every new exemption is a local bound in the function body, so `unwatched_exemptions` stays at five, and the one mirror created is recorded above rather than left to be discovered. D-112's `cycle_artifacts.stranded` and `unwatched_strandings` and D-113's `cycle_wallclock.graded` make **91** --- the **thirty-sixth** consecutive cycle, and the first time the pin went **three cycles unread**. That is the whole finding here and it is not about the number. D-112 and D-113 each shipped a module, each entered this registry, and neither ran this pin: both cycles died before their receipt and never pushed, so the count sat wrong from 08-07 03:00 until now while five other tests failed *because* of the same unpaid bill. The recurrence's usual second-order cost is nil, but a new one is visible and it is procedural rather than syntactic --- a census pin only prices an entrant if somebody runs it, and a cycle that cannot reach its own suite cannot be charged. `unwatched_strandings` is the substantive member: `stranded - unsupported`, spelled `if c.path not in lying`, and it is D-064's kind (implementing an exclusion has the shape) rather than the auditor kind, because the subtraction *is* what the guard publishes. `stranded` enters as the ordinary bookkeeping member --- it is one call into `unpublished` with the exemption declined, and the narrowing the detector sees is the one inside that call. `cycle_wallclock.graded` narrows by `if run.hour in by_hour`, the join filter, and D-089's across-function rule holds for a **seventh** prediction: the function `cycle_wallclock` exists to publish is `grade`, which decides PREMATURE / OVERRUN by threshold comparison against `MIN_OVERHEAD_SECONDS`, and it is invisible. Three consecutive cycles now where the module's conclusion is spelled as a numeric comparison and the visible member is its bookkeeping."
        "D-116's `cycle_wallclock.over_budget_grades` makes **92** --- the **thirty-eighth** consecutive cycle, and the first whose cost was bought **deliberately, with the trade known in advance**. D-115's `finding_grades` solves the same problem one cycle earlier and did *not* enter: it is a plain comprehension over two probe runs with no set difference, so the detector is blind to it. `over_budget_grades` is spelled `frozenset({epic}) - {brief}` instead, and the subtraction *is* the point --- it is what makes the derivation falsifiable, so an inverted comparison inside `budget_grade` flips the set rather than silently renaming its member; the test that catches that (`test_over_budget_grades_tracks_an_inverted_comparison`) exists only because of the spelling. So this entry prices something the previous thirty-seven did not isolate: **the syntax that makes a derivation testable is the same syntax the census detects**. D-072 established that the detector keys on the operator and nothing else; this adds that the operator is also where the falsifiability lives, which makes the recurrence a genuine trade rather than an accident of style. Second-order cost is nil --- the exemption is INLINE (a local name, not a typed global), so `unwatched_exemptions` stays at **five**."
        "D-136's `lam_window_key.attribution` makes **93** --- the **thirty-ninth** consecutive cycle, and the first entrant whose `&` is the *experimental design itself* rather than a correction applied to one. The seven `&`-shaped guards before it intersect a population with a caveat; this one intersects the two contrasted cells' arms (`set(a.arms) & set(b.arms)`), which is what isolating a factor **means** --- compare the cells that agree on every other coordinate, over the arms they have in common. So the operator the detector keys on and the operator the science needs are the same character, and D-116's finding (the syntax that makes a derivation testable is the syntax the census detects) recurs one level up: here it is the syntax that makes an *attribution* possible at all. The empty intersection is not a corner case but the module's `NO_CONTRAST` verdict, which is why `attribution` refuses to call it `FACTOR_INERT`. D-089's across-function rule holds for an **eighth** prediction --- `shift` and `grade`, the functions the module publishes, decide by equality against a recorded window and stay invisible --- but the caveat/conclusion split does not apply cleanly, because `attribution` is a conclusion that happens to be spelled as an intersection. Second-order cost is nil: the exemption is INLINE, so `unwatched_exemptions` stays at **five**. The procedural cost D-112 booked recurred instead, and worse: this member entered when D-136 shipped at 14:00, that cycle was killed before its receipt, and the pin --- along with `guard_direction`'s scalar count and two `loop_reach.READING` rows --- sat red on an unpushed branch for a full cycle. A census pin only prices an entrant if somebody runs it, for the second time in the same fortnight. "
        "D-145's `lam_window_key.seed_census` makes **94** --- the **fortieth** consecutive cycle, and the entrant is not `&`-shaped, so the AND set stays at seven. Its three exemptions are the two confounds the seed axis has to survive: `NOT_IN cells` names the registry cells at other weights instead of dropping them (the empty-denominator shape D-107/D-120/D-127 each booked), and the `IN`/`SUB` pair on `ladder` scopes the grade to the rungs both sources walked, because the generated tables walk eight rungs and the hand walks walked four. So this member exempts a population from a reading for the ordinary reason --- which is the recurrence itself, now boring: a function that compares two measurement sources cannot avoid declaring which pairs it declines to compare, and declaring that is what the detector keys on. The procedural cost D-112 booked did **not** recur: this pin was taken by the same cycle that moved it, off a receipt run ordered after the doc writes (D-043/D-044). "
        "D-146's `calibrate_lam.merge_tables` and the `arms` scope on "
        "`lam_window_key.table_shift_census` make **96** --- the **forty-first** "
        "consecutive cycle, and the first entrant that is `&`-shaped since D-136, "
        "so the AND set goes to eight. Both come from the same purchase: a "
        "controller column bought at one weight only. `merge_tables` intersects "
        "the two tables' cell keys to *refuse* (`DUPLICATE_CELL`), and the census "
        "scope narrows both cell sets to the columns that exist at both weights "
        "so the denominator cannot shrink silently. The recurrence holds with a "
        "sharper edge than usual: neither function was written as a guard --- one "
        "is a file-format join and the other is a parameter --- and both entered "
        "because *declining to compare* is the only honest way to state partial "
        "coverage. The tenth mirror arrived the same way, unintended (see "
        "`test_mirrors_are_the_known_ten`). "
        "D-174's `admissibility_selection.licence_split` makes **97** — and the "
        "run of consecutive cycles continues, with the cheapest possible "
        "second-order cost and one genuine finding bought. The `&` is a join "
        "over two populations' `w_geom` keys, so it is D-136's shape rather "
        "than a correction: a coefficient only one population carries cannot "
        "disagree with itself, and the frozen null has no coefficient at all by "
        "construction. What entering this registry actually bought is "
        "`LICENCE_NO_OVERLAP` — before it, an empty intersection returned "
        "`LICENCE_AGREED`, i.e. 'no disagreements' from a comparison that never "
        "ran, which is D-107's shape sitting inside the very screen written to "
        "catch a selected denominator. Note what stayed out: the module's other "
        "population-shaped functions (`_comparable`, `_coupling`, "
        "`_null_distribution`, `span_reading`) all fold or compare per member "
        "rather than differencing against a registry, which is D-072's syntax "
        "result holding once more. "
        "`receipt_cost.price` makes **98**, and the recurrence arrives from the "
        "least self-aware direction yet: the module audits *the suite's own "
        "wall clock*, not a population of guards, and its author (this cycle) "
        "did not notice it was writing a guard at all. The shape is "
        "`{m: s for m, s in grouped.items() if m not in keep_set}` — an "
        "`IN`/`NOT_IN` split of the measured modules into the candidate subset "
        "and its complement — so it is D-073's ordinary narrowing rather than "
        "D-072's `&`, and the nine-member `&` set above is untouched. What "
        "makes it worth a line is that the standing gloss since D-063 "
        "('every instrument built to audit a population becomes a member of "
        "one') keeps being read as a claim about *instruments*, and this entry "
        "is the cleanest counter-example to that reading yet: pricing a subset "
        "is a budgeting question about seconds, and it still lands here, "
        "because splitting a population in two is the syntax the detector "
        "keys on regardless of what the population is made of. D-072's result "
        "again, at the cheapest possible price. "
        "D-180's `receipt_cost.scope` makes **99** — the **thirty-seventh** "
        "consecutive cycle — and it is the first member whose entry was "
        "**predicted, priced, and used as a reason to defer** before it "
        "existed. D-177 declined to ship this function one cycle early on the "
        "stated ground that it 'enters the guard census as the 99th and breaks "
        "`len(pool) == 98`', and that the new value could only be learned by "
        "running this module (163.4s) *before* a full suite — impossible at "
        "`runs_affordable == 1`. Both halves of that prediction are now "
        "measured, and they split: the entry is exactly right (the narrowing "
        "is `c for c in changed if ... or c in exempt`, D-073's ordinary "
        "membership, and the `&` set above is untouched at nine), while the "
        "**price was wrong by roughly 650×**. The new value is `len(gr.guards())` "
        "— an AST scan over the package at **`real 0m0.248s`** — and the 163.4s "
        "is what it costs to *re-audit* the pool, which is a different object "
        "from reading its size. So a census pin that has been charged "
        "retroactively (D-103), charged twice (D-106), and left unread for "
        "three cycles (D-112) has now also been used as a **budget argument "
        "against shipping**, and that is the newest failure mode it has "
        "produced: not a wrong count, but two cycles of correct arithmetic "
        "over a misidentified quantity. Second-order cost is **nil on one axis "
        "and not the other, and this sentence is the second thing the run "
        "refuted**: it was first written as 'nil on both axes' on the reasoning "
        "that `set(meta)` is DERIVED from a call, so `unwatched_exemptions` "
        "stays at five — true, and measured. The other half was asserted "
        "without measuring, and `test_liveness_derivation` refused it: "
        "`NO_REGISTRY` went 16 -> **17**. The two axes are the same fact read "
        "in opposite directions — an exemption built inside the call is watched "
        "by whatever watches the call, and *for that very reason* no "
        "module-scoped registry names it — so 'DERIVED, therefore nil' is the "
        "inference that cannot be made, and D-073's cost is not one number but "
        "two that move apart. Worth one further line: the module's *other* new "
        "population-shaped function, `guard_meta_suite`, did **not** enter, "
        "and for D-079's now-familiar reason at one remove — it narrows by a "
        "truth test over a generator (`any('import' in line and ...)`) rather "
        "than by membership against a registry. The function that decides "
        "**what may be skipped** is invisible; the function that decides "
        "**whether skipping is allowed** is counted. "
        "D-206's `inert_surface.carried_drift` makes **100** — the "
        "**thirty-eighth** consecutive cycle — and the round number is worth "
        "one line for a reason that is not the number. Every one of the "
        "previous ninety-nine narrows a population held *in this process*: a "
        "registry, a dict of observations, a set of module names. This one's "
        "population is `git diff --name-only base HEAD -- <carried>`, a "
        "**subprocess**, and the detector reached it anyway — because the "
        "narrowing that precedes the call (`n for n in named.all if n not in "
        "new`) is the same membership-against-a-registry syntax D-073 keyed "
        "on, and it does not care that the difference is then handed to git. "
        "So D-072's syntax result extends past the process boundary, which is "
        "further than 'every instrument becomes a member of one' was ever "
        "argued to reach. "
        "The second-order cost is **not** nil this time, and unlike D-180 it "
        "is not a counter moving by one: entering `revocable_collections` "
        "creates a *probe obligation* (`gd.unprobed_revocable() == ()`), and "
        "there is no probe. The nine reds in `test_guard_direction` are that "
        "obligation, not a miscount, and they cannot be cleared by editing a "
        "number here — a probe is an executed before/after reading in a "
        "scratch repo, and designing one requires first answering what "
        "`carried_drift`'s *offence* is. That question is Q-133, and it is "
        "open. Recorded here so the next cycle picks up a specified "
        "deliverable rather than re-deriving the diagnosis: the census pin is "
        "correct at 100, and the direction of this member's blindness is "
        "unexecuted. "
        "Worth the same line D-180 earned: the module's other new function, "
        "`leaking_pins` (D-207), did **not** enter, and for D-079's reason — "
        "it narrows by a truth test over a call (`c for c in stale_pins(src) "
        "if inert(c, src)`) rather than by membership against a registry. The "
        "03:00 cycle's journal attributed these reds to `leaking_pins`; that "
        "was wrong, and the pool scan is what says so. "
        "D-214's `quoted_counts.audit` makes **101** — the **thirty-ninth** "
        "consecutive cycle — and it is the first entrant whose *population is "
        "prose*. Every one of the previous hundred narrows code, observations, "
        "or a git output; this one narrows the pass counts written in "
        "`journal/**/*.md`, and it enters through the identical syntax: "
        "`quote.value in population`, where `population` is "
        "`{r.counts.get('passed', 0) for r in archived(root)}`. So D-072's "
        "syntax result now has a reading it was never tested against — the "
        "detector does not care what the members *are*, only that a membership "
        "operator split them — and a module that reads no Python at all is the "
        "cleanest available demonstration that the standing gloss ('every "
        "instrument built to audit a population becomes a member of one') is "
        "about `in`, not about instruments. "
        "Second-order cost is nil on the `unwatched_exemptions` axis (the "
        "exemption is DERIVED from a call, D-077's reason) and **not** nil on "
        "Q-069's: `NO_REGISTRY` goes 18 -> **19**. That split is D-180's "
        "exactly, repeated rather than extended, and it is worth saying so "
        "plainly — the last four entrants each brought a distinct miss-reason "
        "and this one brings none. Note also the module's three other "
        "population-shaped functions: `quotes`, `archived` and `reach` all "
        "narrow by a truth test (`if instant is not None`, `if receipt is not "
        "None`) rather than by membership, so the detector sees none of them — "
        "D-079's invisible spelling, holding for a further module written "
        "without reference to it. "
        "`three_arm.is_interaction` makes **102** — the **fortieth** "
        "consecutive cycle — and it is the first entrant that exists *because "
        "the cycle removed an unwatched population one commit earlier*. The "
        "predicate first shipped as membership in a module-level "
        "`INTERACTION_VERDICTS = frozenset({SIGN_FLIP, CONDITIONAL})`, a typed "
        "allow-list with no enumerator, which drove `unwatched_exemptions` "
        "five-to-six inside one suite run — D-073 / D-080 / D-101 / D-103 / "
        "D-105's cost for a sixth time. The repair was D-104's second option "
        "(state the reading so the set need not exist): rule out the two "
        "*non*-interaction verdicts instead of naming the two interaction "
        "ones. The complement is spelled `v in (\"MAIN_EFFECT\", \"INERT\")` — "
        "an inline two-string tuple in membership position, D-102's exact "
        "shape — so paying the `unwatched_exemptions` bill **bought a pool "
        "entry**: three census reds cleared, one created, and the package's "
        "net position on the same predicate moved by one in each register. "
        "That is D-104's three-spellings-of-one-set arriving from the "
        "opposite direction — there the repair *deleted* a guard from the "
        "census and read as nil cost, here it *inserts* one — and it is the "
        "second time (after D-105) that an entrant is the module's headline "
        "conclusion rather than its bookkeeping, for the same reason both "
        "times: the prescribed repair overrides the natural spelling D-089's "
        "rule is about. "
        "Second-order cost is nil on both axes and **both were measured, not "
        "inferred** (D-180's lesson applied rather than restated): "
        "`unwatched_exemptions` reads five and `NO_REGISTRY` holds at 19. "
        "One correction belongs here, because the branch's 15:00 journal "
        "wrote the diagnosis down and it was wrong: it attributed these reds "
        "to `step_bought_with_freeze` wanting registration as an `&`-shaped "
        "guard. That function did **not** enter the pool at all, and the AND "
        "set above is untouched at nine — its `and` is a boolean operator "
        "joining two scalar comparisons (`> EPS_CLEARANCE`, `<` on "
        "`n_reached`), which is not the set intersection `SENSE_AND` reads. "
        "The module's other new functions are invisible for D-079's reason "
        "for a ninth module: `ped_step`, `interaction_verdict` and "
        "`verdict_ladder` narrow by threshold comparison or build a dict, and "
        "`risk_interaction_matrix` is a comprehension over the design grid. "
        "D-242's `acceptance_coverage.drift` makes **103**, and it entered while "
        "its own cycle was actively trying to stay out. The sweep's first draft "
        "hoisted `check_acceptance`'s rules table to a module constant precisely "
        "to satisfy D-047 --- read the registry, never copy it --- and that "
        "created two new TYPED allow-lists, putting the module into "
        "`unwatched_exemptions` instead (five to seven, plus a spurious `get` "
        "from a `.get()` call site). The repair removed the registry rather than "
        "pinning it: the graded set is now derived by *probing* the checker, so "
        "no second statement of the rules table exists to go short. `drift` still "
        "enters here, because it differences the survey against "
        "`UNGRADED_CENSUS`. That is the entry worth keeping --- D-047 compliance "
        "and detector-invisibility pull in opposite directions, and a guard whose "
        "job is to pin a census cannot avoid being one. Note also which repair "
        "did *not* work: adding functions that merely return the allow-lists left "
        "`unwatched_exemptions` unmoved, because a watcher must be a guard whose "
        "**population is** the list, not a function that hands it back --- three "
        "of this cycle's iterations went into learning that, at one 8.8-minute "
        "suite apiece for the two that were taken blind. "
        "D-251's `arrival_scope_census.drift` makes **104** --- and it is the "
        "second consecutive cycle whose single entrant is a census `drift`, "
        "written to the same shape for the same reason. Like D-242's it "
        "differences a survey against a module-level enumeration "
        "(`set(VERDICT_CENSUS)`, ENUMERATION / COLLECTION), and like D-242's it "
        "could not have been written any other way: pinning a per-scene verdict "
        "*is* reading a population. What is worth the line is which of this "
        "module's functions did **not** enter, because it is D-089's "
        "across-function rule holding for an **eighth** prediction. The function "
        "the module exists to publish is `ratio_ranks_contamination` --- it is "
        "the one that refutes Q-145's lean --- and it is invisible, spelled as a "
        "pairwise comparison over a sort (`all(a <= b for a, b in zip(...))`). "
        "`verdict` and `arrives` are invisible for the familiar reason (threshold "
        "and identity comparisons), and `scene_paths` narrows by catching an "
        "exception rather than by testing membership, which is a spelling the "
        "detector has not met and does not see --- notable because that "
        "try/except **is** this module's D-047 compliance, the loader-derived "
        "exclusion standing in for a hand-listed one. So a filter written "
        "specifically to satisfy the rule that drives entrants into this pool is "
        "itself uncounted. Second-order cost is nil on both axes: the exemption "
        "is PARAMETER-provenance (`rows`, a bound argument), so "
        "`unwatched_exemptions` stays at five, and no mirror pair is created. "
        "D-273's `window_axis_key.calibrated_axes` makes **107**, and it is the "
        "recurrence arriving from the one direction that had not produced it yet: "
        "not a module auditing a population, but a module **deriving a registry it "
        "refuses to type**. The guard is `n not in skip` over `ab.lam_ladder`'s "
        "signature parameters, and the `skip` set exists precisely so the axis "
        "list is read off the walk instead of hand-written — i.e. the exemption "
        "*is* this module's D-047 compliance, the same role D-251's try/except "
        "played, and this time the detector **does** see it. That pairing is worth "
        "the line: two consecutive entrants whose narrowing is a no-second-"
        "statement measure, one invisible (exception-shaped) and one visible "
        "(`not in`-shaped), which is D-072's syntax result holding at the level of "
        "*compliance mechanisms* rather than of auditors. Second-order cost is nil: "
        "the exemption is INLINE-provenance (a set literal built in-function, not a "
        "module global), so there is no typed allow-list to watch and "
        "`unwatched_exemptions` stays at five — the D-073/D-075 cost lands only "
        "when the exempting set is named at module scope. "
        "D-275's `window_axis_reach` adds `enforcing_functions` and `consumers`, "
        "and D-276's `window_axis_migration` adds `sites`, making **110** across "
        "two cycles repaired together --- the recurrence holds, and the joint "
        "repair is the only reason it is one entry instead of two. The pairing "
        "corrects the 06:00 journal, which booked all eight red pins to "
        "`window_axis_migration`: two of the three entrants are the *previous* "
        "cycle's module, whose own suite never ran to completion. What is new is "
        "the second-order cost, and it lands on the axis D-077 through D-079 kept "
        "finding nil. `sites` derives its population from a sibling registry "
        "(`window_axis_reach.RESOLVERS`) rather than typing a second list --- the "
        "reuse this package asks for --- and a *declared* registry read from "
        "another module has no enumerator, so `unwatched_exemptions` goes "
        "five-to-six and needed a tamper in the same repair. D-073, D-075 and "
        "D-080 each paid this by naming a new exclusion; this one pays it by "
        "**reusing** an old one, which is the first instance where the convention "
        "and the cost point the same way. "
        "D-286's `calibrated_ladder.ceiling_resolution` makes **112**, and it is "
        "the first entrant whose visible narrowing is the module's *conclusion* "
        "rather than its bookkeeping — D-089's across-function rule, which has "
        "now held for nine consecutive predictions, **fails here**. The shape is "
        "`set(usable_now) - set(usable_was)`, and that difference is not a "
        "correction applied to a reading: it **is** `region_is_artifact`, the "
        "thing the function was written to publish (did a 2.5x finer ladder find "
        "usable rungs the coarse one missed?). So this is D-064's kind — "
        "implementing an exclusion has the shape as surely as auditing one does "
        "— arriving for the first time on a *measurement* reader rather than on "
        "an instrument, which is the widest the standing gloss ('every instrument "
        "built to audit a population becomes a member of one') has been stretched "
        "past its own noun. The `SUB` sense goes to sixteen; the nine-member `&` "
        "set above is untouched, so `test_and_shaped_guards_are_exactly_these_four` "
        "needed no edit and the red was the count alone. Note what stayed out and "
        "why it sharpens D-072 rather than repeating it: the same function's "
        "`interior`, which decides the whole cliff/slope verdict, narrows by "
        "`pair[0] < p.weight < pair[1]` — a **chained ordinal comparison**, the "
        "spelling D-102 recorded as invisible — and `local_exponents` folds per "
        "consecutive pair. Both are more load-bearing than the difference that "
        "entered. Second-order cost is nil on both axes: the exemption is DERIVED "
        "from a local (`usable_was`), so `unwatched_exemptions` stays at five, and "
        "no `NO_REGISTRY` member is added. "
        "D-287's `calibrated_ladder.uniform_resolution_trend` makes **113** — the "
        "same module two cycles running, and the first entrant whose narrowing is "
        "the *withholding* rather than either the bookkeeping or the conclusion. "
        "The visible population is `probed` (`verdict != CROSSING_UNPROBED`), and "
        "the two exemptions on it are `comparable`'s `IN` against an inline "
        "verdict pair and `withheld`'s `NOT_IN comparable`, DERIVED from that "
        "local. What that difference computes is which temperature's gap is "
        "**excluded from `min_gap_refined`** — so it is D-064's kind again, one "
        "cycle after D-286 first stretched the gloss to a measurement reader, and "
        "this time the exclusion is not incidental to the finding but *is* the "
        "finding (`UNIFORM_TREND_WITHHELD` names exactly the set it removes). "
        "Read together the two cycles say something narrower than either alone: "
        "when a measurement reader's job is to decide what it may not compare, "
        "the census sees it, and D-089's across-function rule fails for the "
        "**second** consecutive prediction rather than the first. Note again what "
        "stayed out, because it is the same shape D-286 booked: `uniform` folds "
        "`len({interior[l] for l in lams}) == 1` — a set built and then compared "
        "by **equality**, D-079's invisible spelling — and it decides "
        "`resolution_uniform`, which is the reading the whole cycle was run to "
        "take. Two consecutive entrants from one module, and in both the "
        "load-bearing narrowing is invisible while a neighbouring one is counted. "
        "D-288's `calibrated_ladder.rise_attribution` makes **114** — the same module a **third** consecutive cycle, and the third consecutive confirmation of D-089's across-function rule. The one visible narrowing is the row filter (`if float(p.weight) in (lo, hi)`), which decides which measured rows are read and publishes nothing — bookkeeping, D-064's kind. Both narrowings that carry the finding are invisible, and they are invisible in the two spellings this census keeps rediscovering: `paired` folds `lo in d and hi in d` — the D-019 conjunction that decides which seeds may carry a direction at all, and the whole reason this cycle walked both rungs instead of the one the TODO named — while `rises`/`falls`, which *are* the verdict, narrow by `direction[s] == \'rise\'`, D-079's invisible equality on a string. So the module that entered three times running has never once entered on its conclusion. Second-order cost nil: the exemption is INLINE, `unwatched_exemptions` holds at five, and no `NO_REGISTRY` member is added. "
        "D-289's `calibrated_ladder.census_ladder` makes **115** — the same module a **fourth** consecutive cycle, and the first of the four that breaks the pattern the other three established. It is `&`-shaped, so the AND set moves for the first time since D-174 (nine members to ten), and the reason is that the pairing D-288 spelled `lo in d and hi in d` is spelled `set(at[lo_w]) & set(at[hi_w])` here: **the same D-019 conjunction, written in the sense this census can see**. Three cycles running, that narrowing was invisible and the census recorded it as invisible; the fourth wrote it as an intersection and it entered on exactly that. So D-089's across-function rule is not refuted — the load-bearing narrowing became visible because the *spelling* changed, not because the module changed what it narrows on. The conclusion itself (`rung_admits_band`, the `span[w] <= width` comparison that decides `CENSUS_RUNG_INADMISSIBLE`) is a magnitude test on a float and still publishes nothing this registry reads, so the module has now entered four times without once entering on its verdict. Second-order cost nil on both axes: the exemption is INLINE, `unwatched_exemptions` holds at five, and no `NO_REGISTRY` member is added. "
        "D-301's `calibrated_ladder.attribution_separability` makes **116** — the same module a **fifth** consecutive cycle, and the first entrant whose narrowing is a *typing* rather than an exclusion. The guard is `legs[e][\"attribution\"] in decided and legs[e][\"stable\"] and not legs[e][\"miss_is_one_seed_wide\"]` — three conjuncts, and the third is the finding: a leg with no genuine flips is only a survivor if the jackknife could *reach* it, and a `15/16` column's sole reachable deletion is the one that deletes the exit being measured. Note this is not the `&`-shape D-289 added — the AND set holds at ten — because the conjunction is over per-leg booleans, not over two populations; it narrows a set of two legs rather than intersecting two readings of one. So the module has now entered five times and still never on its verdict: `SEPARABILITY_STABLE`/`UNTESTABLE` is decided by `fragile`/`untestable` emptiness, which this registry does not read. Second-order cost nil: the exemption is INLINE, `unwatched_exemptions` holds at five, and no `NO_REGISTRY` member is added. "
        "Second-order cost is nil on both axes: one exemption is INLINE and the "
        "other DERIVED from a local, so `unwatched_exemptions` stays at five, and "
        "the guard is not `&`-shaped, so the nine-member AND set above is again "
        "untouched and the red was the count alone. "
        "D-312's `extremum_reading.scan_sites`, `unrepaired_hulls` and `sweep` make **119** — three at once, the largest single-cycle addition since D-076's three, and what it costs is the entry worth keeping. The AND set is untouched at ten (none of the three intersects two populations), and by the usual coda that would read as 'second-order cost nil'. It was not: two of the three route to masking (20 -> 22, against one-of-three or one-of-four for every prior cycle), both of the module's allow-lists arrive **unwatched**, `REGISTRIES` goes 11 -> 13 and the `NOT_PATHS` layer 4 -> 5. That is the auditor's version of the recurrence — an instrument that publishes what it lets through has typed exemptions *by construction*, so it cannot enter this pool cheaply the way a measurement reader can. "
        "The line the two repair cycles actually paid for, though, is not that one. D-312's tally repair went red on five files; D-313 fixed all five by **adding the two registry entries above**, and a census that grows is a census-moving event — so the repair re-fired the same lemma one frame out, on exactly the three pins that read `REGISTRIES`, `NOT_PATHS` and this running count. Two full suites, ~34 min of wall clock, for a recurrence this file has recorded twenty-odd times. The standing pre-empt is one line and sub-second — `[g.qualname for g in guards() if '<new module>' in g.qualname]` — and D-314 ran it **against the repair as well as against the module**, which is the half both prior cycles missed: the check has to be taken twice, because the fix is a member of the population too. "
        "D-318's `census_preempt.loop_reach_reading` makes **120**, and this one entered on the run of the very pass written to catch it: the pre-empt's first invocation reported `120 guards vs pin 119 (+1)`, one commit before any suite. Only one of the module's three checks entered — `loop_reach_reading` computes `want - recorded`, a set difference against a named registry, while `guard_tally` compares two integers and `citation_sites` forwards another module's list. That is the D-064 shape read from the other side: what the detector keys on is the *difference*, so a pass that reconciles three censuses joins the pool once rather than three times. "
        "D-333's `scene_transfer.blocking_scenes` makes **121**, and it is the first entrant admitted *by* the pre-empt rather than by a suite: `census_preempt` reported `121 guards vs pin 120 (+1)` at the stage, 2.4 s of checking against the 1002 s suite that would have carried the same red. That is the second consecutive cycle in which the pre-empt's own arrival (D-318, **120**) and its first real catch land one after the other, which is the shape worth recording — the instrument that watches this count entered it, and then immediately caught the next entrant. The guard itself narrows by `arm not in winners(s)`, a NOT-shaped exclusion, and is not `&`-shaped, so the AND set holds at ten. The sibling shipped in the same commit, `narrowest_block`, filters on `len(blocking_scenes(a)) == 1` and stayed out — D-079's invisible equality, one frame down on a derived count — so a cycle that added two functions to one module added one member here. Second-order cost was **not** nil, and the way it was learned is the entry's real content: the tally was repaired off the pre-empt and the cycle pushed on to the suite, which came back red on **two** further pins — the AND set and the deep-minus-shallow set — because the entrant had been written into the AND literal it does not belong to, and omitted from the deep-only literal it does. `census_preempt` was clean across both, correctly: it re-derives the *count*, and neither pin is a count. So the pre-empt bounds the cost of a tally drift to seconds and says nothing about **which** literals a new guard must be spelled into — the four censuses it names as covered are populations, not placements. That is the standing gap, and it is the one an entrant-adding cycle actually walks into. D-334 left the tally at **121** and the way it got there is the entry: the separability module first shipped `informative_separators` narrowing against `set(constant_observables())`, which made it entrant 122, and the pre-empt named it at the stage in ~2 s. The tally and the deep-only literal were both repaired up front — and the suite still came back red on **thirteen** further pins, because a `DIFFERENCE` entrant also owes a hand-written `guard_direction.PROBES` entry with a repo fixture and a permit/offend pair, which `unprobed_revocable` checks and no census re-derives. So the placement gap this prose has recorded twice is **wider than placement**: D-333 paid for two literals, D-334 discovered a third obligation behind them whose cost is a fixture, not a line. The repair was to make the narrowing predicate-shaped (`is_constant`) so it matches its three siblings in the same module, none of which were ever guards; the emptiness the probe would have watched is pinned as data instead (`INFORMATIVE_SEPARATION` whole-table equality, `constant_observables` exact membership). That is a legitimate shape choice and also an admission — the shape was chosen after the price was known, and it is recorded that way so a later cycle can disagree. What it should **not** be read as is a cheap escape hatch: it is available only because the population here is small enough to pin by value. the first time both of its drifting censuses fired on the same commit, which is the case its `UNCOVERED` line does not bound, since placement is still unwatched. "
        "D-349 left the tally at **124**, and the round trip is the entry. "
        "`TTC_FAMILY` arrived on `unwatched_exemptions` when D-347 named the two "
        "TTC columns once, so the subset rule owed a control, and the obvious "
        "target does not move — `ttc_family_has_the_heavier_tail` returns a "
        "`bool` invariant under shrinking the family (measured: the surviving "
        "`min(ttc)` still loses to `max(rest)`). A reader therefore had to exist "
        "for the tamper to read. Shipped set-shaped first "
        "(`tuple(o for o in tail_extensions_by_observable() if o in "
        "TTC_FAMILY)`) it was entrant **125**, and `census_preempt` named it at "
        "the stage in ~2 s — the third consecutive cycle the pre-empt has priced "
        "an entrant before a suite, and the first where the entrant was created "
        "by a repair the same cycle was making. But the tally was the cheap half "
        "of the bill: the set-shaped spelling grades `DIFFERENCE`/`COLLECTION`, "
        "so it is a **revocable collection** and owes a hand-written "
        "`guard_direction.PROBES` entry with a repo fixture and a permit/offend "
        "pair. That is exactly the obligation D-334 recorded as sitting *behind* "
        "the two literals it had already paid for, and it is the one no census "
        "re-derives — `census_preempt` read CLEAN on all five with the fixture "
        "unwritten, because placement is not a population. Repaired D-334's own "
        "way: `is_ttc_family` is predicate-shaped, matching the siblings in that "
        "module that were never guards, so it leaves the pool entirely (125 -> "
        "124) and the masking screen holds at 25 rather than 26. The shape was "
        "chosen after the price was known and is recorded that way so a later "
        "cycle can disagree. What it costs is D-104's objection: a repair that "
        "deletes the guard from the census reads as a disappearance rather than "
        "a payment — answered here only by the control itself, which shrinks the "
        "registry and watches a count move, so the registry is watched by "
        "something even though the watcher is not in this pool. "
        "D-363's `excursion_tracking.drift` makes **125**, and the entry is the "
        "one that did *not* stay. The pre-empt priced **two** entrants at the "
        "stage — `drift` and `main` — the fourth consecutive cycle it has done "
        "so before a suite (~2 s against 1324 s), and the tally was repaired to "
        "126 up front. The suite still came back red on **five** pins, every "
        "one of them naming `main` and none naming `drift`: `flagged`, "
        "`shaped`, the deep-minus-shallow set and `unprobeable_revocable`. That "
        "is D-333's placement gap arriving for the third time, and the third "
        "time it has cost a suite — `census_preempt` re-derives the *count* and "
        "read CLEAN on all five censuses with four shape literals wrong, "
        "correctly, because placement is not a population. What is new is "
        "*which* function drew it. `main` is a **printer**: it narrows by "
        "`scene in excited()` purely to put a `*` beside a row. The repair was "
        "to mark off `forced > 0.0` instead — the same predicate one frame "
        "down, D-079's invisible shape, and the very reason `excited()` itself "
        "never entered — so the printer leaves the pool (126 -> 125) and the "
        "four literals need no edit at all. Recorded as a shape choice made "
        "*after* the price was known, D-334's way, so a later cycle can "
        "disagree: the honest reading is that a display function had no "
        "business in this census, and the detector was right that it was "
        "spelled like a guard." " The cycle's four findings live in `excited`, `unexcited`, "
        "`under_forced`, `obstacle_free` and `high_level_low_spread` — five "
        "functions that each narrow the eight-scene population — and **none of "
        "them entered**. All five narrow by a comparison on a float "
        "(`r[0] > 0.0`, `rows[s][1] < rows[s][0]`, `... == float('inf')`), "
        "which is D-079's invisible-equality shape one frame out: a magnitude "
        "test, not a set difference. What did enter is `drift`, which "
        "differences the live join against `CENSUS`, and `main`, which prints "
        "it. So the module entered on its **bookkeeping** and stayed out on its "
        "**conclusions** — the exact inversion of D-288/D-289's four-cycle run, "
        "where the conclusion was invisible and the row filter was counted. "
        "Twenty-odd restatements in, the rule is stable and worth stating "
        "plainly: this pool measures the *spelling* of a narrowing, and a "
        "package whose findings are numeric comparisons will keep entering it "
        "through its `drift` functions no matter what it measures. Second-order "
        "cost nil: neither is `&`-shaped so the AND set holds at ten, both "
        "exemptions are INLINE, and no `NO_REGISTRY` member is added."
        " D-367 puts the count back to **126** with a single entrant, "
        "`pairing_precondition.against_baseline`, and it is worth the line "
        "because it is the *cleanest* instance of the rule the paragraph above "
        "just called stable. That module's four findings — `SIGN_VARIES`, the "
        "nine negative pairs, the `-0.7402` floor, the `sqrt(1 - rho) > 1` "
        "inflation — all live in `branch_wide_verdict` and in comparisons on a "
        "float, and **none of them entered**, exactly as predicted. What "
        "entered is the one function that narrows by **membership** rather than "
        "by magnitude: `BASELINE in (r.arm_a, r.arm_b)` is a set test on a "
        "population, so it is spelled like a guard whatever it is used for. "
        "The previous entrant, `excursion_tracking.main`, was a printer and was "
        "removed by re-spelling it; this one is not removable the same way, "
        "because the narrowing is the point — the baseline column *is* the "
        "population the deficit claim is made in, and a version that did not "
        "restrict to it would answer a different question. So the pool gains a "
        "member that is doing real work, which is the first time in three "
        "entrants that the honest repair is to admit it rather than to re-spell "
        "it. Second-order cost nil again: not `&`-shaped (AND set holds at "
        "ten), exemption is INLINE, no `NO_REGISTRY` member added."
        " D-368 makes it **128** with two entrants, `seed_debt.baseline_hurt` "
        "and `seed_debt.baseline_signs` — and they are the same shape D-367's "
        "single entrant was, from the same clause: both narrow by "
        "`BASELINE in (arm_a, arm_b)`. That is now the *third* module to enter "
        "this registry through its baseline restriction specifically, so the "
        "rule the two paragraphs above call stable has a sharper corollary: on "
        "this branch the membership test that keeps entering is always the one "
        "that isolates the comparison a deficit claim is made in. "
        "**D-371 makes it 129 and breaks that run** with one entrant, "
        "`aa_calibration.null_gaps`, whose `0 not in group` is a "
        "canonicalisation rather than an isolation: it drops complementary "
        "splits because `|mean(A) - mean(B)|` is symmetric, so the predicate "
        "ranges over the *index set* and not over which arms are compared. The "
        "corollary above therefore holds for three consecutive entrants and "
        "fails on the fourth, which is worth more than the streak was — it "
        "says the registry keys on narrowing per se, and the baseline-shaped "
        "run was a property of what those cycles happened to measure. "
        "D-368's own "
        "three findings behaved exactly as the rule predicts and **none "
        "entered** — the window intersection, the `1.96x` narrowing and the "
        "`17/26` sign tally are all magnitude comparisons on floats "
        "(`v > bar`, `rho < 0.0`, `hi - lo`), one frame out from D-079's "
        "invisible equality. Second-order cost nil for the third consecutive "
        "entrant cycle: neither is `&`-shaped (AND set holds at ten), both "
        "exemptions are INLINE, no `NO_REGISTRY` member added. "
        "**D-386 makes it 133** with three, and the third is the one worth the "
        "line. `free_screen_gap` (`scene not in harvested`) and "
        "`both_columns_scenes` (`&` of two harvest registries) enter on the "
        "usual shapes — the AND set moves for the second time since D-174. But "
        "`tail_mean.drift` enters *now*, having sat outside for two cycles: it "
        "was already an auditor, and its checks were `set(A) != set(B)` — "
        "inequality, which reports **that** two registries differ and never "
        "**which** members. D-386 added `set(both_columns_scenes()) - set(...)` "
        "and that one character moved it into the registry. So the entrant is "
        "not a new function but an old one that started naming its offenders, "
        "which is the sharpest statement yet of what this pool keys on: not "
        "auditing, not narrowing, but **set difference as the thing returned**. "
        "`degenerate_cells` stayed out on D-375's rule, narrowing by "
        "`n < MIN_DISTINCT_ARMS` — a magnitude comparison, the same frame that "
        "kept `tail_limited` out. "
        "**D-375 made it 130** with one entrant, `tail_stability.drift`, and "
        "the interesting half is which of that module's functions stayed out. "
        "`drift` enters on the plain auditor shape — `scene not in CENSUS`, "
        "`a not in saturated_by_midpoint(scene)`, one TYPED and one DERIVED set "
        "difference against a named registry. But `tail_limited`, the function "
        "carrying the module's actual **verdict**, does *not* enter: it narrows "
        "by `gap > FRACTION * spread`, a magnitude comparison on floats. So the "
        "cycle reproduces D-371's corollary from the other side — the registry "
        "keys on set difference per se, and a module can have its headline "
        "reading be invisible to this detector while its bookkeeping is not. "
        "That is the same one-frame-out blindness D-374's three findings showed, "
        "arriving now within a single module rather than across a cycle's "
        "output, which is the tighter statement of it. Second-order cost nil "
        "for the fourth consecutive entrant cycle: not `&`-shaped (AND set "
        "holds at ten), exemptions INLINE, no `NO_REGISTRY` member added. "
        "D-392's `aa_calibration.gradeable_column_verdict` makes **134**, and "
        "the pair it arrived in is the point. That cycle added two functions "
        "over the same finding — a cte_max tally counting a row whose arms do "
        "not separate — and only one entered. `gradeable_column_verdict` "
        "differences `CALIBRATED` against `degenerate_tally_rows()` and is "
        "admitted; `degenerate_tally_rows` itself *builds* that set by testing "
        "each member against `tail_mean.MIN_DISTINCT_ARMS`, a magnitude "
        "comparison, and stays out. So the detector saw the subtraction and not "
        "the criterion the subtraction is made by, which is D-072's syntax "
        "result yet again — but note the direction here is the reassuring one: "
        "the member it admitted is the one that publishes a narrowed reading, "
        "and the member it missed publishes nothing. Second-order cost nil for "
        "the fifth consecutive entrant cycle: not `&`-shaped (AND set holds at "
        "ten), exemptions INLINE, no `NO_REGISTRY` member added. "
        "D-404's `declared_suite.scope_of` makes **135**, and it is the "
        "registry-audits-itself shape at its purest: the guard subtracts "
        "the targets an invocation named from `DECLARED_SUITE`, and "
        "`DECLARED_SUITE` is the module's own single statement of the "
        "suite this very pool is derived by running. The detector admits "
        "it for the ordinary reason — a set difference publishing a "
        "narrowed reading (`missing`) — not for the reflexivity, which "
        "no criterion here can see. Sixth consecutive entrant cycle at "
        "nil second-order cost: not `&`-shaped (AND set holds at ten), "
        "exemptions INLINE, no `NO_REGISTRY` member added.")


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
    Committing a snapshot file silences ``undeclared_drift`` (D-047) and fires
    ``staged_declarations``.  Both match the shape; only the first is the
    failure.  So D-048's "one of 23" survives as a count of *failures* while
    being wrong as a count of *matches*.

    D-050 executed the direction and narrowed this further: the act does not
    *empty* ``undeclared_drift`` either.  Its exemption has already removed the
    offending path before the offence happens, so the reading is empty on both
    sides — see ``test_guard_direction.test_the_blind_guard_does_not_move_at_all``.
    The shape names a collapse that is real but **masked**, never observed.
    """
    shaped = {g.qualname for g in gr.unmirrored_revocable(pool)}
    assert shaped == {
        # D-248. Same entrant as the pin above, same reason.
        "arrival_spread.separation_survives",
        "tree_provenance.undeclared_drift",
        "local_only_audit.staged_declarations",
        # D-105 adds two, and unlike the pair above this is a **debt, not a
        # masked collapse**.  `cycle_artifacts.disputed` is the natural mirror
        # of `unsupported` — it reads the residue of the same two flag sets —
        # but it is spelled `^` where `unsupported` is spelled `&`, so
        # `mirrors()` does not pair them.  Either the detector learns the
        # symmetric-difference spelling (D-072's syntax result again) or the
        # module grows an explicit complement.  Recorded here rather than
        # papered over; it is the 22:00 cycle's top follow-up.
        "cycle_artifacts.unsupported",
        "cycle_artifacts.report",
        # D-114.  Same shape, and it sharpens the docstring's own limit: this
        # one is neither a masked collapse nor a spelling debt.  It matches
        # `revocable` and its executed direction is NAMES_OFFENCE — so the
        # shape's over-inclusiveness is now demonstrated by a working guard
        # rather than argued from `staged_declarations` alone.
        "cycle_artifacts.unwatched_strandings",
        # D-206 added the sixth, and for one cycle it was the first that was
        # **none of the three** states this pin had held — its direction was
        # *unexecuted*, because `carried_drift` had no `gd.PROBES` entry and so
        # no before/after reading existed.  D-209 closed that: the probe is
        # built (`build_carried_drift_repo`) and the executed direction is
        # NAMES_OFFENCE, so this is now the **second demonstrated working
        # guard** alongside `unwatched_strandings` — the shape over-includes
        # again, and again the reading rather than the shape is what says so.
        # What the probe does *not* yet execute is Q-133's rename case: a
        # carried reader deleted and reappearing under a new name leaves
        # `named.all` as a `departure` (unchecked) while its new name lands in
        # `entrants` (exempt), so moved content is invisible on both sides.
        # The `exempt=` seam this cycle added is what a probe for that would
        # drive; the subjects here are content moves, which the guard catches.
        "inert_surface.carried_drift",
        # D-347's `format_tail_grade` is the seventh, and it is the one entrant
        # this docstring's limit does **not** cover.  The docstring says the
        # shape names a collapse that may be masked (`undeclared_drift`) or
        # working (`staged_declarations`); this member has neither, because it
        # is a formatter and there is no reading to move in either direction.
        # It is `revocable` matching on spelling alone — see the pin in
        # `test_q063_the_shape_occurs_twice_and_fails_once` for the mechanism.
        "scene_separability.format_tail_grade",
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


# --------------------------------------------------------------------------
# D-050: set-valuedness was resolved one frame shallower than difference-ness
# --------------------------------------------------------------------------


def _shallow_pool(package=None):
    """The scan as D-049 shipped it: ``_is_set_valued`` not following calls."""
    original = gr._is_set_valued
    gr._is_set_valued = lambda expr, consts, imported, module_fns=None, depth=2: \
        original(expr, consts, imported, None, 0)
    try:
        return gr.guards(package=package)
    finally:
        gr._is_set_valued = original


def test_set_valuedness_follows_same_module_calls():
    """A guard that delegates its population to a helper is still a guard.

    D-050's finding, pinned as a regression.  ``_difference_kind`` has always
    resolved a same-module call one frame down; ``_is_set_valued`` did not, so
    the two predicates read *the same expression* at different depths.  The
    consequence was a deletion rather than a mis-ranking: rewriting
    ``staged_declarations`` as ``sorted(staged_changes(...) & REGISTRY)`` — the
    duplicate-removing refactor D-045 through D-049 kept prescribing — made its
    left operand a bare call, failed the ``BitAnd`` arm, and dropped the guard
    out of the guard registry entirely.
    """
    src = """
REGISTRY = ('a', 'b')

def _observe():
    return {'a', 'c'}

def offenders():
    return sorted(_observe() & set(REGISTRY))
"""
    tree = ast.parse(src)
    consts = gr._set_valued_constants(tree)
    module_fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    call = tree.body[-1].body[0].value.args[0].left
    assert isinstance(call, ast.Call)
    assert not gr._is_set_valued(call, consts, set(), None, 0), \
        "the shallow predicate is what D-049 shipped; keep it visible in the test"
    assert gr._is_set_valued(call, consts, set(), module_fns), \
        "D-050: a call whose returns are set-valued is a population"


def test_the_shallow_predicate_was_hiding_two_more_guards():
    """The population correction is not only about the refactored guard.

    Two guards were invisible at ``HEAD`` for reasons this cycle did not create.
    D-048 judged 23, D-049 corrected it to 28, and the true figure for that same
    source is 30 — the seventh of the last eight cycles whose scan was wrong
    about its own population, and again in the *under*-counting direction.

    D-051 adds three more, and they are the sharpest evidence the fix was load-
    bearing rather than cosmetic: half of :mod:`predicate_depth`'s own guards
    filter a population reached through a same-module call, so a module written
    **after** the fix would have been half-invisible **before** it.

    D-075 adds three, and they say the same thing about a module written
    eighteen cycles after the fix.  :mod:`magnitude_survival`'s ``standings``,
    ``unbanded`` and ``movements`` each filter against ``banded`` — the local
    name bound by a same-module ``bands(record, kind)`` call two lines up — and
    all three are invisible to the shallow scan for exactly D-051's reason.  Its
    fourth guard, ``published``, filters against the module global
    ``SELF_DEFINING`` and so appears in both scans; that 3-to-1 split is the
    cheapest available restatement of why the deep scan is not optional.
    """
    deep = {g.qualname for g in gr.guards()}
    shallow = {g.qualname for g in _shallow_pool()}
    assert deep - shallow == {
        "local_only_audit.derived_local_only",
        # D-105: `unsupported` filters against `finding_grades()` and `tsv_rows`
        # against `KEYS` reached through a same-module call, so the shallow scan
        # sees neither — D-051's reason, and the first time it applies to a
        # module's *headline* function.
        "cycle_artifacts.unsupported",
        "cycle_artifacts.tsv_rows",
        # D-106: the un-exempted half of `unsupported`, written so
        # `guard_direction` can read the same population through one key
        # instead of the intersection of two.  Deep-only for the same reason
        # its subject is — it filters against `_flagged(...)`, a same-module
        # call — so the probe apparatus lands on the *deep* side of D-051's
        # split too.
        "cycle_artifacts.unsupported_by",
        # D-107: `reprobe` builds `carried` by filtering `readers(...).all`
        # against `new`, itself bound from a same-module `entrants(...)` call —
        # D-051's reason for a fourth module.  Worth contrasting with its three
        # siblings, which are *not* here: `entrants` and `departures` narrow
        # against a set built inline from the pin, and `probe` against its own
        # parameter, so all three are visible to the shallow scan.  One module,
        # four entrants, and only the one that composes two same-module calls
        # lands on the deep side.
        "inert_surface.reprobe",
        "local_only_audit.staged_declarations",
        # D-461: `drift` filters the union of `consumers()` — a same-module
        # call — against the `CONSUMERS` pin, then filters `PROSE_OVERREACH`
        # against `prose_overreach()`, another one.  D-051's reason for a fifth
        # module.  Its siblings stay shallow-visible: `consumers` narrows
        # against the module global `D_ENC_DERIVED` and `code_consumers`
        # against its own inline literal, so one module contributes three
        # guard-shaped functions and only the one composing two same-module
        # calls lands deep.
        #
        # Worth the paragraph because of *how this was found*.
        # `census_preempt.guard_tally` caught the pool moving 139 -> 140 two
        # commits earlier and that repair was made — but the tally and this
        # deep/shallow **composition** are two different pins in two different
        # assertions, and fixing the one the preempt named left this one red
        # through a full 20-minute suite.  D-318's instruction to read the
        # `UNCOVERED` line gives no warning here: `guard_tally` *is* covered,
        # so the pass reads CLEAN while a second assertion over the same
        # population is already broken.  A census that grades a set's
        # cardinality does not thereby grade its membership.
        "d_enc_consumers.drift",
        "weight_units.closed_loop_per_unit_spread",
        "predicate_depth.disagreements",
        "predicate_depth.opaque_readings",
        "predicate_depth.profiles",
        "magnitude_survival.standings",
        "magnitude_survival.unbanded",
        "magnitude_survival.movements",
        # D-076 adds two, and one of them is a *migration* rather than an
        # arrival.  `readings` is new and filters against `banded` for D-051's
        # reason, like its three siblings.  `published` was the 3-to-1 split's
        # lone "1" — visible to both scans while it named `SELF_DEFINING`
        # inline — and moved here when D-076 routed its exemption through
        # `self_defining()`.  So the split is now 5-to-0, and the two scans
        # disagree about the *same* edit: `_provenance` still resolves it TYPED
        # (the call site passes `SELF_DEFINING` explicitly, D-052 (b)'s repair,
        # which is why `provenance_depth_exposure` is still empty), while the
        # shallow scan simply stops at the call and sees nothing.  One repair
        # fixed one scan; nothing in D-052 (b) ever claimed it would fix both.
        "magnitude_survival.published",
        "magnitude_survival.readings",
        # D-104 adds one, and it is a migration in the same direction as
        # `published` above.  `loop_reach.report` was visible to both scans
        # while it named the module constant `UNEVALUATED` inline; deriving
        # that constant (`in unevaluated_grades()`) is what makes its exemption
        # read DERIVED instead of TYPED, and the shallow scan stops at the call
        # and sees nothing.  So this entry is the price of D-103's unwatched
        # allow-list being paid rather than a new guard arriving — the same
        # trade `magnitude_survival.published` made when D-076 routed its
        # exemption through `self_defining()`.
        "loop_reach.report",
        # D-253 adds one, and it is D-051's reason for yet another module.
        # `reproduces` filters the published column against
        # `_cells_by_weight(cells)`, a same-module call, so the shallow scan
        # stops at the call and sees nothing.  Worth noting which member of
        # `headline_rescope` this is: not `regrade`, the function the module
        # exists to publish, which decides by equality against a verdict string
        # and is invisible for D-079's reason — but the *reproduction* check,
        # the caveat that licenses the re-read.  D-089's caveat/conclusion split
        # holds for a ninth prediction, in a module written without reference
        # to it.
        "headline_rescope.reproduces",
        # D-277 adds one, and it is D-051's reason for a further module — but
        # the *contrast* is what earns the comment.  `consumers` excludes the
        # resolvers' own definitions by filtering against `targets`, bound from
        # a same-module `resolvers()` call, so the shallow scan stops at the
        # call and sees nothing.  `window_axis_migration.sites` performs the
        # identical exclusion one module over and is **not** here: it filters
        # against `frozenset(RESOLVERS)`, a from-imported module global, which
        # both scans resolve.  Same exclusion, same author, same cycle; whether
        # it is deep-only turns entirely on whether the population arrived by
        # call or by name.  That is also precisely the split D-277's
        # `Tamper.bound_in` had to make explicit for the control over the same
        # registry, reached from the opposite direction — a registry read by
        # name is reachable to a tamper and visible to the shallow scan; one
        # reached through a call is neither.
        "window_axis_reach.consumers",
        # D-284: `ceiling_gap` reads `n_samples` off the ladder rows at one
        # temperature, filtering `points(rows)` — a population bound by a
        # same-module call, so the shallow scan stops at the call exactly as it
        # does for `window_axis_reach.consumers` above.  Worth noting which way
        # the split fell here: the *same* module's `ceiling_bracket` and
        # `ceiling_response` filter the same `points(rows)` and are **not**
        # guards at all, because neither carries an exemption — the population
        # correction is what makes a filter a guard, not the filtering.
        "calibrated_ladder.ceiling_gap",
        # D-333: `blocking_scenes` excludes the scenes an arm already wins by
        # filtering against `winners(s)`, a same-module call, so the shallow
        # scan stops at the call — D-051's reason once more.  The contrast is
        # inside the same commit: its sibling `narrowest_block` calls
        # `blocking_scenes(a)` just as indirectly and is **not** a guard at
        # all, because it narrows by `len(...) == 1` and carries no exemption.
        # Same module, same cycle, same call-bound population; what separates
        # them is the population correction, not the indirection — which is the
        # `calibrated_ladder.ceiling_gap` note above restated by a module
        # written without reference to it.
        "scene_transfer.blocking_scenes",
        # D-336 added `scene_separability.constant_at_every_index` here and
        # **D-338 withdrew it** — the only entry so far to leave this set, and
        # the migration runs opposite to `magnitude_survival.published` above.
        # `published` moved *in* when D-076 routed its exemption through a call;
        # `constant_at_every_index` moved *out* when D-338 stopped routing its
        # exemption through `_observables_of(t)` and named `OBSERVABLES` at the
        # call site. The reason it had to move is the cost D-052 (b) accepted in
        # writing: an exemption reached through a same-module call is admitted
        # by `_is_set_valued` and labelled `DERIVED` by `_provenance`, so it is
        # skipped by every `TYPED` screen — D-336's entry was this repo's first
        # live instance, and `provenance_depth_exposure` counted it. Naming the
        # registry fixes **both** scans at once, which is what makes this a
        # withdrawal rather than the one-scan repair `published` settled for.
    }
    assert not shallow - deep, "widening must not drop anything (D-038's lesson)"


def test_this_modules_own_completeness_checks_are_in_the_pool(pool):
    """The glob is reflexive: ``guard_direction``'s two checks are themselves guards."""
    names = {g.qualname for g in pool}
    assert "guard_direction.unprobed_revocable" in names
    assert "guard_direction.stale_probes" in names
