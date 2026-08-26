"""The pre-empt is a set, and each member must be shown to bite.

D-317's cycle held a clean ``guards()`` reading and a red suite at the same
time.  So the property under test here is not "the pass runs" — it is that the
pass covers **more than one** census and that each member goes ``DRIFT`` when
its own census moves.  A member that cannot be made to bite contributes a clean
reading that means nothing, which is the defect being pre-empted, one level up.

Note on this file's own shape: it deliberately contains **no loop-body
population-claim assertion**.  Such an assertion would join
``loop_reach.targets()`` and require a ``READING`` entry — this file would then
have to move the very census it tests, in the same commit, which is a poor way
to learn whether the check works.  ``all(...)`` over a comprehension carries the
same claim without entering that population.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import replace
from types import SimpleNamespace
from pathlib import Path

import pytest

from eval.mppi_sandbox import census_preempt as cp


# --------------------------------------------------------------------------
# The set is a set
# --------------------------------------------------------------------------

def test_the_pass_covers_the_two_censuses_that_were_conflated():
    """`guards()` alone is what read clean while `loop_reach` went red.

    The regression this file exists to prevent is the pre-empt silently
    shrinking back to one member, which would look identical from the outside:
    a fast command, a clean line, a red suite.
    """
    names = {name for name, _ in cp.CENSUSES}
    assert {"guard_tally", "loop_reach_reading"} <= names
    assert len(cp.CENSUSES) >= 3


def test_every_registered_census_is_callable_and_self_naming():
    rows = {name: fn for name, fn in cp.CENSUSES}
    assert all(callable(fn) for fn in rows.values())
    got = {name: fn() for name, fn in rows.items()}
    assert all(reading.census == name for name, reading in got.items()), (
        "a Reading naming a census other than the one that produced it would "
        "misattribute a DRIFT to the wrong registry")


def test_the_omissions_are_named_rather_than_implied():
    """`uncovered()` is the module's work list, not its clearance.

    Mirrors `exemption_control.uncontrolled`: a typed set is honest only when
    the reader can see what it left out.
    """
    assert cp.uncovered() == cp.UNCOVERED
    assert len(cp.UNCOVERED) >= 3
    covered = {name for name, _ in cp.CENSUSES}
    assert all(name not in covered for name, _ in cp.UNCOVERED), (
        "a census cannot be both covered and declared uncovered")
    assert all(len(reason) > 40 for _, reason in cp.UNCOVERED), (
        "an omission with no stated reason is an oversight wearing a registry")


# --------------------------------------------------------------------------
# The guard pin is read, not copied
# --------------------------------------------------------------------------

def test_the_guard_pin_is_parsed_out_of_the_assertion():
    pinned = cp.pinned_guard_tally()
    assert isinstance(pinned, int) and pinned > 100


def test_this_module_does_not_restate_the_tally_it_reads():
    """D-047: one statement of the number, and it is not in this package's copy.

    A pre-empt carrying its own copy of the pin would need updating on the same
    cycles the pin does — i.e. it would fail in exactly the situation it exists
    to catch.

    Matched on a **digit boundary**, not as a bare substring (D-376). The
    substring form fired the moment the tally reached `130`, because the
    module's prose says "12:00 cost 1305 s" and `"130" in "1305"` — a
    restatement that is not one. The failure direction matters: it is a false
    alarm on an unrelated number, and the cheap way out (reword the prose until
    the digits stop colliding) leaves the collision waiting for the next tally.
    A digit-boundary match still catches the thing D-047 built this for — the
    tally written out as its own number — and stops catching decimals that
    merely contain it.
    """
    pinned = cp.pinned_guard_tally()
    source = (cp.PACKAGE / "census_preempt.py").read_text(encoding="utf-8")
    restated = re.search(rf"(?<!\d){pinned}(?!\d)", source)
    assert restated is None, (
        f"census_preempt.py restates the guard tally {pinned} at offset "
        f"{restated.start() if restated else -1}")


@pytest.mark.parametrize("body,want", [
    # the shape the suite actually uses: a fixture returning the population
    ("""
     @pytest.fixture
     def pool():
         return gr.guards()

     def test_x(pool):
         assert len(pool) == 42
     """, 42),
    # a local assignment
    ("""
     def test_x():
         pool = gr.guards()
         assert len(pool) == 43
     """, 43),
    # the direct form
    ("""
     def test_x():
         assert len(gr.guards()) == 44
     """, 44),
    # a len() over an unrelated population must not be mistaken for the pin
    ("""
     def test_x():
         other = some_other_call()
         assert len(other) == 45
     """, None),
])
def test_the_parser_recognises_the_binding_shapes(tmp_path, body, want):
    """The first draft handled two of these three and read `pin NOT FOUND`.

    That verdict was correct about the parser and wrong about the tree, which
    is the failure mode a fail-open default would have hidden: the fixture case
    is not an edge here, it is the only case in the file that matters.
    """
    (tmp_path / cp.GUARD_PIN_TEST).write_text(textwrap.dedent(body),
                                              encoding="utf-8")
    assert cp.pinned_guard_tally(tmp_path) == want


def test_a_missing_pin_file_fails_closed(tmp_path, monkeypatch):
    assert cp.pinned_guard_tally(tmp_path) is None
    monkeypatch.setattr(cp, "pinned_guard_tally", lambda *a, **k: None)
    reading = cp.guard_tally()
    assert reading.is_drift
    assert "NOT FOUND" in reading.detail, (
        "a parser that lost the pin must say so; a clean reading earned by "
        "reading nothing is the whole defect")


# --------------------------------------------------------------------------
# Tampers — one per census.  Each must bite.
# --------------------------------------------------------------------------

def test_guard_tally_bites_when_the_population_grows(monkeypatch):
    from eval.mppi_sandbox import guard_reflexivity as gr

    real = gr.guards()
    monkeypatch.setattr(gr, "guards", lambda *a, **k: real + (real[0],))
    reading = cp.guard_tally()
    assert reading.is_drift
    assert "+1" in reading.detail


def test_guard_tally_is_clean_on_the_tree_as_it_stands():
    """The live reading, which is also the check the executor runs.

    Kept green deliberately: this file's cycle added a guard
    (`census_preempt.loop_reach_reading`) and bumped the pin in the same commit,
    which is precisely the repair loop the module is for.
    """
    assert not cp.guard_tally().is_drift


def test_loop_reach_reading_bites_on_an_unrecorded_claim(monkeypatch):
    """The census that went red at 05:00 while `guards()` read clean."""
    from eval.mppi_sandbox import loop_reach as lr

    trimmed = dict(lr.READING)
    dropped = sorted(trimmed)[0]
    del trimmed[dropped]
    monkeypatch.setattr(lr, "READING", trimmed)
    reading = cp.loop_reach_reading()
    assert reading.is_drift
    assert "unrecorded" in reading.detail and dropped in reading.detail


def test_loop_reach_reading_bites_in_the_retired_direction_too(monkeypatch):
    """`READING`'s test demands equality, and equality fails both ways.

    A deleted test leaves a stale entry; reporting only the additions would
    hand back a clean line for a suite that is about to go red.
    """
    from eval.mppi_sandbox import loop_reach as lr

    monkeypatch.setattr(lr, "READING",
                        dict(lr.READING) | {"test_a_claim_since_deleted":
                                            (lr.SAMPLED, 2)})
    reading = cp.loop_reach_reading()
    assert reading.is_drift
    assert "retired" in reading.detail


def test_citation_sites_bites_on_an_unregistered_magnitude(monkeypatch):
    from eval.mppi_sandbox import citation_audit as ca

    monkeypatch.setattr(ca, "unregistered",
                        lambda *a, **k: [("2.0x", "docs/decisions.md", "D-999", 7)])
    reading = cp.citation_sites()
    assert reading.is_drift
    assert "docs/decisions.md:7" in reading.detail


# --------------------------------------------------------------------------
# 4. exemption_registry — the census D-330 paid 811 s for
# --------------------------------------------------------------------------

def test_exemption_registry_bites_on_an_entrant(monkeypatch):
    """D-330's accident, replayed: a constant enters the allow-list population.

    The real entrant was `clearance_census.REPRESENTATION_ARMS`, dragged in by
    a *cosmetic* membership test in a printer.  What matters for the tamper is
    only that an unwatched TYPED allow-list appears that the pin has never
    seen — the pre-empt cannot know why, and the 811 s suite did not either.
    """
    from eval.mppi_sandbox import guard_reflexivity as gr

    real = gr.unwatched_exemptions()
    monkeypatch.setattr(gr, "unwatched_exemptions",
                        lambda *a, **k: real + ("REPRESENTATION_ARMS",))
    reading = cp.exemption_registry()
    assert reading.is_drift
    assert "1 entered: REPRESENTATION_ARMS" in reading.detail
    assert "category" in reading.detail, (
        "the repair D-330 found was deleting the membership test, not bumping "
        "the pin — a DRIFT that does not say so invites the wrong fix")


def test_exemption_registry_bites_in_the_departure_direction_too(monkeypatch):
    """The pin is an equality, so a *removed* allow-list is a finding too.

    A watcher written for a previously-unwatched list moves it out of this
    population, which is a good change that still has to be recorded.
    """
    from eval.mppi_sandbox import guard_reflexivity as gr

    real = gr.unwatched_exemptions()
    monkeypatch.setattr(gr, "unwatched_exemptions", lambda *a, **k: real[1:])
    reading = cp.exemption_registry()
    assert reading.is_drift
    assert f"1 left: {real[0]}" in reading.detail


def test_exemption_registry_fails_closed_on_a_missing_pin(tmp_path, monkeypatch):
    """No parseable assertion ⇒ DRIFT, never a clean reading earned by nothing."""
    monkeypatch.setattr(cp, "TESTS", tmp_path)
    assert cp.pinned_unwatched_exemptions(tmp_path) is None
    assert cp.exemption_registry().is_drift


def test_scene_population_bites_on_an_added_scene(monkeypatch):
    """The tamper for the seventh entry — the direction that was measured.

    Not hypothetical: on 2026-08-24 a tenth yaml in `eval/scenarios/` failed
    two pinned assertions in 0.16 s while this pass read all-clean on six
    censuses and named no such omission in `uncovered()`.
    """
    real = cp.pinned_avoidance_capable()
    assert real is not None
    monkeypatch.setattr(cp, "pinned_avoidance_capable",
                        lambda *a, **k: real - {sorted(real)[0]})
    reading = cp.scene_population()
    assert reading.is_drift
    assert "entered" in reading.detail


def test_scene_population_bites_in_the_dropped_direction_too(monkeypatch):
    """A scene that silently leaves shrinks somebody's denominator."""
    real = cp.pinned_avoidance_capable()
    assert real is not None
    monkeypatch.setattr(cp, "pinned_avoidance_capable",
                        lambda *a, **k: real | {"a-scene-that-does-not-exist"})
    reading = cp.scene_population()
    assert reading.is_drift
    assert "left" in reading.detail


def test_scene_population_fails_closed_on_a_missing_pin(tmp_path, monkeypatch):
    """No parseable literal ⇒ DRIFT, never a clean reading earned by nothing."""
    monkeypatch.setattr(cp, "TESTS", tmp_path)
    assert cp.pinned_avoidance_capable(tmp_path) is None
    assert cp.scene_population().is_drift


def test_scene_count_pins_bites_when_the_matrix_widens(tmp_path, monkeypatch):
    """The tamper for the eighth entry — the Q-197 direction.

    A ninth scene lands in `eval/scenarios/` and the count pins still say 8.
    Simulated by shrinking the *pinned* side rather than writing a yaml, so the
    tamper cannot leave a stray scene behind for the rest of the suite.
    """
    pin = tmp_path / "test_scene_eligibility.py"
    pin.write_text("def test_three_of_eight_scenes_are_eligible():\n"
                   "    assert len(shipped.scenes) == 999\n", encoding="utf-8")
    monkeypatch.setattr(cp, "SCENE_COUNT_PINS", {
        "test_scene_eligibility.py": ("test_three_of_eight_scenes_are_eligible",)})
    reading = cp.scene_count_pins(tests=tmp_path)
    assert reading.is_drift
    assert "do not assert it" in reading.detail
    # the repair instruction must name the decoys, or a cycle repairs the
    # arm-count sites too — both populations are 8.
    assert "decoys" in reading.detail


def test_scene_count_pins_fails_closed_on_a_renamed_test(tmp_path, monkeypatch):
    """No such function ⇒ DRIFT, never a clean reading earned by nothing."""
    monkeypatch.setattr(cp, "SCENE_COUNT_PINS", {
        "test_scene_eligibility.py": ("test_that_was_renamed_away",)})
    reading = cp.scene_count_pins(tests=tmp_path)
    assert reading.is_drift
    assert "NOT FOUND" in reading.detail


def test_scene_count_pin_sites_all_resolve():
    """Every registered address exists — the registry is typed, so it can rot.

    This is the guard on the concession `scene_count_pins` makes: the sites are
    enumerated by hand because `== 8` cannot be told from the arm-count pins by
    shape. A hand-typed address list that silently stops resolving would hand
    back exactly the vacuous clean reading the module exists to prevent.
    """
    for fname, funcs in {**cp.SCENE_COUNT_PINS, **cp.SCENE_COUNT_DECOYS}.items():
        for func in funcs:
            assert cp._ints_compared_in(cp.TESTS / fname, func) is not None, \
                f"{fname}::{func} no longer resolves"


def test_the_decoys_do_not_assert_the_scene_count():
    """A decoy must never assert the derived scene count — that is what makes it
    a non-member rather than a stale pin.

    The direction of this test is inverted from how D-456 wrote it, and the
    inversion is D-457's finding. D-456 asserted the decoys *did* collide with
    the scene count, because when it was written both populations were 8 and the
    collision was the whole reason the registry existed. The ninth scene ended
    that: the arm count stayed 8 while the scene count moved to 9, so the
    collision test began failing on a registry that was entirely correct.

    "Currently indistinguishable by shape" is a property of one moment, so it
    cannot be the invariant. What holds across a scene addition is the thing the
    registry actually claims — a decoy tracks some *other* population, so it must
    not assert this one. That is true whether or not the two happen to be equal,
    and it is the assertion that would have caught a decoy wrongly bumped to 9.
    """
    derived = int(cp.scene_count_pins().detail.split()[0])
    for fname, funcs in cp.SCENE_COUNT_DECOYS.items():
        for func, reason in funcs.items():
            ints = cp._ints_compared_in(cp.TESTS / fname, func)
            assert ints is not None, f"{fname}::{func} no longer resolves"
            assert derived not in ints, (
                f"{fname}::{func} is registered as a decoy ({reason}) but now "
                f"asserts the scene count {derived} — either it was wrongly "
                "bumped by a scene-addition cycle, or it is a live pin that "
                "belongs in SCENE_COUNT_PINS")


def test_the_scene_pin_is_parsed_out_of_the_test_literal():
    """Read from the suite's own literal, never restated here (D-047)."""
    pinned = cp.pinned_avoidance_capable()
    assert pinned is not None
    from eval.mppi_sandbox.tests import test_avoidance_coverage as tac
    assert pinned == tac.AVOIDANCE_CAPABLE


def test_the_exemption_pin_is_parsed_out_of_the_assertion():
    """Read from the suite's own literal, never restated here (D-047)."""
    pinned = cp.pinned_unwatched_exemptions()
    assert pinned is not None
    from eval.mppi_sandbox import guard_reflexivity as gr
    assert pinned == set(gr.unwatched_exemptions())


def test_this_module_does_not_restate_the_allow_lists_it_reads():
    """The names must live in one place, and this file is not it.

    `pinned_guard_tally`'s discipline applied to a set instead of an integer:
    a second copy of the population living in the pre-empt would be one more
    thing to forget — the failure the module exists to remove, reintroduced at
    the level of the fix.
    """
    source = (Path(cp.__file__)).read_text(encoding="utf-8")
    for name in cp.pinned_unwatched_exemptions():
        assert f'"{name}"' not in source, (
            f"{name} is restated in census_preempt.py; parse it instead")


def test_exemption_registry_is_clean_on_the_tree_as_it_stands():
    assert not cp.exemption_registry().is_drift


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def test_report_states_its_scope_when_clean():
    rows = (cp.Reading("a", cp.CLEAN, "ok"), cp.Reading("b", cp.CLEAN, "ok"))
    text = cp.report(rows)
    assert "all clean" in text
    assert all(name in text for name, _ in cp.UNCOVERED), (
        "a clean pass must carry its own scope — the D-317 failure was a "
        "reading narrower than it looked")


def test_report_and_exit_code_carry_a_drift(monkeypatch):
    rows = (cp.Reading("a", cp.CLEAN, "ok"), cp.Reading("b", cp.DRIFT, "moved"))
    assert "1 of 2 censuses DRIFTED" in cp.report(rows)
    monkeypatch.setattr(cp, "readings", lambda: rows)
    assert cp.main([]) == 1
    monkeypatch.setattr(cp, "readings", lambda: rows[:1])
    assert cp.main(["report"]) == 0


def test_the_scope_clause_survives_a_drift(monkeypatch):
    """D-381: the ``Not covered:`` caveat must print on **both** verdicts.

    It stood on the clean branch alone, which put it in front of every reader
    except the one it was written for — a cycle looking at ``DRIFTED``, one
    edit away from touching a census, and entitled to know which four this
    pass never re-derived.  Same shape as D-380 one level out: the finding
    state was the side that lost information.
    """
    rows = (cp.Reading("a", cp.CLEAN, "ok"), cp.Reading("b", cp.DRIFT, "moved"))
    drifted, clean = cp.report(rows), cp.report(rows[:1])
    for name, _ in cp.UNCOVERED:
        assert name in drifted, (
            f"{name!r} named on the clean verdict but not the drifted one — "
            "a caveat a finding suppresses is absent when it is load-bearing")
        assert name in clean
    assert cp._scope_clause() in drifted and cp._scope_clause() in clean


def test_main_rejects_an_unknown_subcommand():
    assert cp.main(["wat"]) == 2


def test_the_whole_pass_is_cheaper_than_the_suite_it_pre_empts():
    """Cheap enough to run every cycle is the property; CPU time is the meter.

    Priced against the suite it stands in front of.  A pre-empt that needed
    the suite to answer would belong in the suite.

    **Measured in CPU time, not wall clock (D-438).**  A cycle runs this pass
    *alone*, but the suite runs it under 14-way sharding, so a wall-clock
    reading taken here prices CPU contention between shards -- a quantity the
    use case never sees.  That is not hypothetical: at wall clock this
    assertion went red at 15.1s against a 15.0 budget while the rest of the
    suite saturated the machine, on a tree where the pass costs 7.6s run on
    its own.  The work is single-threaded and in-process (unloaded wall and
    CPU agree to two decimals), so process_time measures the same quantity
    the budget is about and is immune to what the other shards are doing.
    """
    import time

    start = time.process_time()
    rows = cp.readings()
    cpu = time.process_time() - start
    assert len(rows) == len(cp.CENSUSES)
    # 15.0 -> **40.0** (D-441), and the bar is what moved this time because
    # D-438's premise was wrong. That cycle swapped wall clock for
    # `process_time` and asserted the result was "immune to what the other
    # shards are doing". It is not: `process_time` drops the *idle-wait*
    # component of contention but not the *memory/cache* component, and 14
    # shards saturating bandwidth make the same instructions burn more CPU
    # cycles. Measured on this tree: **7.71s wall / 7.63s CPU standalone**
    # against **15.08s CPU inside the suite** -- a 2x CPU inflation on code
    # that did not change. A threshold sitting at 2x standalone is therefore a
    # contention detector, and D-438's own argument ("fix what you measure,
    # not the bar") applies to itself one level down.
    #
    # 40.0 keeps the guard's actual purpose. That purpose was never "7.6s
    # specifically" -- it is that this pass stays *orders* below the 1470s
    # suite it pre-empts, so a cycle can afford to run it. 40s is still ~3% of
    # the suite and ~5x standalone, which catches the failure this guard
    # exists for (a pre-empt that grew suite-scale) while no longer firing on
    # a busy machine. The honest instrument would count instructions rather
    # than time; that is Q-186, not this cycle.
    # 40.0 -> **70.0** (D-480), and this time the bar moved because the *pass*
    # deliberately grew, which is the one reason D-438's "fix what you measure,
    # not the bar" does not apply. D-480 added two entries to close the
    # enumeration gap that cost D-478 and D-479 a red suite each. One is free
    # (`assert_reach_sites`, ~0.05s); the other is not: `liveness_partition`
    # costs **~13s standalone**, measured this cycle, and the cost is inside
    # `liveness_derivation.derive`'s per-guard registry resolution rather than
    # in the guard walk -- passing a pre-built pool moves it by ~0.4s, so there
    # is no cheap version of this entry to ship instead.
    #
    # Standalone went **7.6s -> ~21s**. At D-441's measured 2x contention
    # inflation that lands at ~42s, i.e. *through* the old bar, so 40.0 would
    # have gone red on a tree where nothing was wrong. 70.0 restores the same
    # margin the old bar had (~3.3x standalone) and keeps the guard's actual
    # purpose intact: it is still ~5% of the 1470s suite, so it still catches
    # the failure this guard exists for -- a pre-empt that grew suite-scale --
    # while the entry it now accommodates is 13s against the 745s red receipt
    # D-479 paid for not having it.
    assert cpu < 70.0, (
        f"pre-empt burned {cpu:.1f}s CPU; budgeted well under the suite it "
        "replaces, with generous headroom for contention and a cold CI cache")


# --------------------------------------------------------------------------
# 5. consumer_reach residue — the census that was in neither list
# --------------------------------------------------------------------------

def _ghost(qualname: str):
    """A stand-in row; the census reads only `definition.qualname`."""
    return SimpleNamespace(definition=SimpleNamespace(qualname=qualname))


def test_consumer_reach_residue_bites_on_a_new_dead_definition(monkeypatch):
    """The ordinary joining move: ship a definition and wire its caller later.

    This is the census the branch paid two red receipts for, and the one named
    in neither `CENSUSES` nor `UNCOVERED` — so a reader who followed D-318 and
    read the `Not covered:` line was still not told it was absent.
    """
    from eval.mppi_sandbox import consumer_reach as cr

    real = list(cr.findings())
    monkeypatch.setattr(cr, "findings",
                        lambda *a, **k: real + [_ghost("ghost.Ghost.make")])
    reading = cp.consumer_reach_residue()
    assert reading.is_drift
    assert "findings +1: ghost.Ghost.make" in reading.detail
    assert "LIVE" in reading.detail, (
        "a residue DRIFT must name the clearable direction — wiring a caller "
        "flips the verdict; editing the pin is the other one (D-044)")


def test_consumer_reach_residue_bites_in_the_departure_direction_too(
        monkeypatch):
    """Wiring a caller removes a name, which is good and still recorded."""
    from eval.mppi_sandbox import consumer_reach as cr

    real = list(cr.findings())
    assert real, "the pinned residue is non-empty; the tamper needs a victim"
    monkeypatch.setattr(cr, "findings", lambda *a, **k: real[1:])
    reading = cp.consumer_reach_residue()
    assert reading.is_drift
    assert f"findings -1: {real[0].definition.qualname}" in reading.detail


def test_consumer_reach_residue_reads_the_two_populations_separately(
        monkeypatch):
    """`module_findings` must not answer for `findings`.

    Suffix matching would let one pin cover both, and a move in either would
    then go unread — the narrower-than-it-looks failure, reproduced inside the
    fix for it.
    """
    from eval.mppi_sandbox import consumer_reach as cr

    real = list(cr.module_findings())
    monkeypatch.setattr(cr, "module_findings",
                        lambda *a, **k: real + [_ghost("ghost.mod")])
    reading = cp.consumer_reach_residue()
    assert reading.is_drift
    assert "module_findings +1: ghost.mod" in reading.detail
    assert cp.pinned_reach_residue("findings") != cp.pinned_reach_residue(
        "module_findings"), "two distinct literals, two distinct pins"


def test_consumer_reach_residue_fails_closed_on_a_missing_pin(
        tmp_path, monkeypatch):
    """No parseable assertion ⇒ DRIFT, never a reading earned by reading nothing."""
    monkeypatch.setattr(cp, "TESTS", tmp_path)
    assert cp.pinned_reach_residue("findings", tmp_path) is None
    assert cp.consumer_reach_residue().is_drift


def test_the_residue_pins_are_parsed_out_of_the_assertions():
    """Read from the suite's own literals, never restated here (D-047)."""
    for kind in cp.REACH_KINDS:
        pinned = cp.pinned_reach_residue(kind)
        assert pinned is not None and pinned


# --------------------------------------------------------------------------
# 6. lam_site_census — the third census to arrive from neither list
# --------------------------------------------------------------------------

def test_lam_site_census_bites_when_a_site_enters(monkeypatch):
    """The ordinary joining move for a *measuring* cycle: run a sweep.

    D-428, D-430 and D-433 each moved `forwards` by exactly one, so this is the
    signature of the work the roadmap is currently made of — and D-433's move
    left the pin red, its push gate refused, and the commit stranded overnight
    while the pre-empt read CLEAN.
    """
    from eval.mppi_sandbox import default_lam_sites as dls

    real = dls.census()
    monkeypatch.setattr(
        dls, "census",
        lambda *a, **k: replace(real, forwards=real.forwards + 1))
    reading = cp.lam_site_census()
    assert reading.is_drift
    assert f"forwards {real.forwards}→{real.forwards + 1}" in reading.detail
    assert "total" in reading.detail, (
        "a lam DRIFT must name the separately pinned total too — bumping the "
        "triple alone leaves the other assertion red thirteen minutes later")


def test_lam_site_census_bites_in_the_departure_direction_too(monkeypatch):
    """Deleting a call site is a move, and equality fails in both directions."""
    from eval.mppi_sandbox import default_lam_sites as dls

    real = dls.census()
    monkeypatch.setattr(
        dls, "census",
        lambda *a, **k: replace(real, decides=real.decides - 1))
    reading = cp.lam_site_census()
    assert reading.is_drift
    assert f"decides {real.decides}→{real.decides - 1}" in reading.detail


def test_lam_site_census_reads_the_three_counts_by_name(monkeypatch):
    """Keyed on attribute name, not tuple position.

    A reordered assertion must be read correctly rather than silently
    transposing two counts — a transposition that happened to be compensating
    would read CLEAN, which is the narrower-than-it-looks failure this whole
    module exists to remove.
    """
    from eval.mppi_sandbox import default_lam_sites as dls

    pinned = cp.pinned_lam_triple()
    real = dls.census()
    assert pinned is not None
    assert set(pinned) == set(cp.LAM_KINDS)
    assert all(pinned[k] == getattr(real, k) for k in cp.LAM_KINDS)


def test_lam_site_census_fails_closed_on_a_missing_pin(tmp_path, monkeypatch):
    """No parseable assertion ⇒ DRIFT, never a reading earned by reading nothing."""
    monkeypatch.setattr(cp, "TESTS", tmp_path)
    assert cp.pinned_lam_triple(tmp_path) is None
    assert cp.lam_site_census().is_drift


def test_the_lam_pin_is_parsed_out_of_the_assertion():
    """Read from the suite's own literal, never restated here (D-047).

    Checked over the **AST** rather than the text.  A substring test is what
    this assertion was first written as, and it fails on its own subject
    matter: `"43"` occurs inside `D-433`, the decision whose strand is the
    reason this census exists.  Prose that *narrates* a magnitude is not a
    second statement of it — a second `int` literal in the derivation is, and
    that is the thing D-047 forbids.
    """
    import ast as _ast

    pinned = cp.pinned_lam_triple()
    assert pinned is not None
    tree = _ast.parse(Path(cp.__file__).read_text(encoding="utf-8"))
    literals = {n.value for n in _ast.walk(tree)
                if isinstance(n, _ast.Constant) and isinstance(n.value, int)
                and not isinstance(n.value, bool)}
    assert not (literals & set(pinned.values())), (
        "the triple must have exactly one statement of itself, and it is the "
        "assertion in the suite — not a second copy living in the pre-empt"
    )


def test_lam_site_census_is_clean_on_the_tree_as_it_stands():
    """The entry is live, not merely present."""
    reading = cp.lam_site_census()
    assert not reading.is_drift, reading.detail
    assert "pin matches" in reading.detail


# --------------------------------------------------------------------------
# 9-10. the two censuses that were in *neither* list (D-480)
# --------------------------------------------------------------------------
# D-478 and D-479 each spent a red suite on a census `census_preempt` did not
# re-derive *and* did not name in `UNCOVERED`.  Two misses in two cycles made
# it a pattern rather than an accident: the `Not covered:` clause D-318 told
# readers to read was, for these two populations, silent -- so a clean pass
# over-stated its own scope in exactly the way D-317 diagnosed one level down.


def test_assert_reach_sites_bites_when_a_shielded_assertion_moves(monkeypatch):
    """The D-478 shape: an edit shifts a shielded site's line number.

    Nothing in `assert_reach` need change for this to fire -- inserting a line
    anywhere above either site is enough, which is why the line pin is the
    tighter of the two derivations this entry runs.
    """
    from eval.mppi_sandbox import assert_reach as ar

    real = ar.shielded()
    assert real, "the fixture needs a live shielded population"
    moved = tuple(
        SimpleNamespace(assertion=SimpleNamespace(lineno=r.assertion.lineno + 1))
        for r in real)
    monkeypatch.setattr(ar, "shielded", lambda *a, **k: moved)
    reading = cp.assert_reach_sites()
    assert reading.is_drift
    assert "not among the pinned" in reading.detail


def test_assert_reach_sites_bites_when_the_corpus_moves(monkeypatch):
    """The other direction: the recorded run's commit no longer matches.

    `moved()` is self-reconciling -- `()` is its clean value -- so this half
    needs no pin parsed, and it is checked ahead of the line pin because a
    moved corpus makes the line numbers meaningless rather than merely wrong.
    """
    from eval.mppi_sandbox import assert_reach as ar

    monkeypatch.setattr(ar, "moved", lambda: ("eval/mppi_sandbox/foo.py",))
    reading = cp.assert_reach_sites()
    assert reading.is_drift
    assert "moved since the recorded run" in reading.detail


def test_assert_reach_sites_fails_closed_on_a_renamed_pin(monkeypatch):
    """A pin the parser cannot find is a finding, not a pass.

    `pinned_guard_tally`'s reasoning: failing open would hand back a clean
    reading earned by reading nothing, which is the defect this module exists
    to remove.
    """
    monkeypatch.setattr(cp, "SHIELDED_PIN_FUNC", "test_that_does_not_exist")
    reading = cp.assert_reach_sites()
    assert reading.is_drift
    assert "pin NOT FOUND" in reading.detail


def test_liveness_partition_bites_when_a_guard_enters(monkeypatch):
    """The D-479 shape, exactly: `NO_REGISTRY` moves and the tally does not.

    This is the miss that makes the pair a pattern.  A cycle that writes one
    small set-valued function joins *both* the guard tally and this partition;
    `guard_tally` reports the first and is silent about the second, and the two
    cannot stand in for each other because they count the same objects under
    different partitions.
    """
    from eval.mppi_sandbox import liveness_derivation as ld

    pinned = cp.pinned_origin_partition()
    real = {getattr(ld, name): n for name, n in pinned.items()}
    bumped = dict(real)
    bumped[ld.ORIGIN_NO_REGISTRY] += 1
    # `recipes` is stubbed too, not just `census`: the derivation costs ~13s and
    # this test is about the *reconciliation*, not about re-deriving the pool.
    monkeypatch.setattr(ld, "recipes", lambda *a, **k: ())
    monkeypatch.setattr(ld, "census", lambda *a, **k: bumped)
    reading = cp.liveness_partition()
    assert reading.is_drift
    assert "ORIGIN_NO_REGISTRY" in reading.detail
    assert "entered or changed origin" in reading.detail


def test_liveness_partition_bites_on_an_unwatched_origin_class(monkeypatch):
    """The third direction, and the one no count comparison reaches.

    A new *origin* -- not a new guard -- leaves every pinned count correct and
    still means the partition no longer partitions.  Checked as a set
    difference rather than a sum so it is caught by the census that owns it
    instead of by whichever pinned count happens to fall short.
    """
    from eval.mppi_sandbox import liveness_derivation as ld

    pinned = cp.pinned_origin_partition()
    real = {getattr(ld, name): n for name, n in pinned.items()}
    monkeypatch.setattr(ld, "recipes", lambda *a, **k: ())
    monkeypatch.setattr(ld, "census",
                        lambda *a, **k: {**real, "ORIGIN_INVENTED": 0})
    reading = cp.liveness_partition()
    assert reading.is_drift
    assert "absent from" in reading.detail


def test_liveness_partition_fails_closed_on_a_missing_pin(tmp_path, monkeypatch):
    """Same failing-closed rule as every other entry here."""
    from eval.mppi_sandbox import liveness_derivation as ld

    monkeypatch.setattr(ld, "recipes", lambda *a, **k: ())
    monkeypatch.setattr(ld, "census", lambda *a, **k: {})
    monkeypatch.setattr(cp, "TESTS", tmp_path)
    reading = cp.liveness_partition()
    assert reading.is_drift
    assert "pin NOT FOUND" in reading.detail


def test_the_origin_partition_is_parsed_out_of_the_assertion():
    """One statement of the partition, and it is the suite's -- not a copy.

    D-047: keyed on the constant's *attribute name*, so a reordered or
    re-spelled literal is read correctly rather than silently transposed, and
    the counts themselves live only in the test that asserts them.
    """
    pinned = cp.pinned_origin_partition()
    assert pinned is not None
    assert all(name.startswith(cp.LIVENESS_ORIGIN_PREFIX) for name in pinned)
    assert "ORIGIN_NO_REGISTRY" in pinned


def test_both_new_entries_are_clean_on_the_tree_as_it_stands():
    """The entries are live, not merely present."""
    for reading in (cp.assert_reach_sites(), cp.liveness_partition()):
        assert not reading.is_drift, reading.detail
