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
    }
    assert len(gr.revocable(pool)) == 5
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

    """
    unwatched = gr.unwatched_exemptions(pool)
    assert set(unwatched) == {"DEGENERATE_READINGS", "SCOPED_CLAIMS",
                              "TEMPERATURE_RELEVANT", "SELF_DEFINING",
                              "DECLARED_DEF_TIME"}
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
    }
    assert len(pool) == 99, (
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
        "**whether skipping is allowed** is counted.")


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
    }
    assert not shallow - deep, "widening must not drop anything (D-038's lesson)"


def test_this_modules_own_completeness_checks_are_in_the_pool(pool):
    """The glob is reflexive: ``guard_direction``'s two checks are themselves guards."""
    names = {g.qualname for g in pool}
    assert "guard_direction.unprobed_revocable" in names
    assert "guard_direction.stale_probes" in names
