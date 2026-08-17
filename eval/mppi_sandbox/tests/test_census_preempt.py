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

import textwrap
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
    """
    pinned = cp.pinned_guard_tally()
    source = (cp.PACKAGE / "census_preempt.py").read_text(encoding="utf-8")
    assert str(pinned) not in source


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


def test_main_rejects_an_unknown_subcommand():
    assert cp.main(["wat"]) == 2


def test_the_whole_pass_is_cheaper_than_the_suite_it_pre_empts():
    """Under two seconds is the property that makes it run every cycle.

    Priced against the 788 s suite it stands in front of.  A pre-empt that
    needed the suite to answer would belong in the suite.
    """
    import time

    start = time.monotonic()
    rows = cp.readings()
    elapsed = time.monotonic() - start
    assert len(rows) == len(cp.CENSUSES)
    assert elapsed < 15.0, (
        f"pre-empt took {elapsed:.1f}s; budgeted well under the suite it "
        "replaces, with generous headroom for a cold cache on CI")
