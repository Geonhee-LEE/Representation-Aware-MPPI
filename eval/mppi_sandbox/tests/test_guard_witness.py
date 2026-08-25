"""Witnesses for D-059's 8 `NEVER_FIRED` candidates — the triage, executed.

The point of this file is that it *runs* the inputs.  D-059 triaged 3 of the 8
by reading them; this asserts all 8 by making them raise, which is the only
evidence that separates "untested" from D-058's "cannot fire".
"""

from __future__ import annotations

import subprocess

import pytest

from eval.mppi_sandbox import guard_vacuity as gv
from eval.mppi_sandbox import guard_witness as gw


@pytest.fixture(scope="module")
def results():
    return gw.attempts()


# --------------------------------------------------------------------------
# the headline: every candidate is reachable, by execution
# --------------------------------------------------------------------------

@pytest.mark.parametrize("witness", gw.WITNESSES, ids=lambda w: w.site)
def test_each_witness_makes_its_guard_raise(witness):
    """One test per site, so a regression names the guard rather than a count."""
    outcome = gw.attempt(witness)
    assert outcome.verdict == gw.SATISFIED, (
        f"{witness.site}: expected {witness.exception}, got {outcome.verdict} "
        f"({outcome.detail})")


def test_no_witness_failed(results):
    """`failed` is kept apart from `unwitnessed` and must stay empty.

    A misfiring witness says nothing about its guard.  Folding the two together
    would let a broken witness read as evidence of vacuity, which is D-050's
    "a probe that cannot separate two cases has measured neither".
    """
    assert gw.failed(results) == ()


def test_the_whole_candidate_set_is_answered(results):
    """8 candidates, 8 witnesses, 8 raises — D-059's set closed by execution."""
    assert len(gw.satisfiable(results)) == len(gw.WITNESSES) == 8


# --------------------------------------------------------------------------
# the grade, and the bound it carries
# --------------------------------------------------------------------------

def test_reachability_grades_partition_the_witnesses(results):
    """`DATA_REACHABLE` and `ARGUMENT_ONLY` cover every satisfiable site once.

    Asserted as a partition rather than as two counts: a third grade added
    without a home would otherwise vanish from both numbers, which is the
    omission D-045 through D-052 kept finding.
    """
    grades = gw.by_reachability(results)
    assert set(grades) == {gw.DATA_REACHABLE, gw.ARGUMENT_ONLY}
    covered = [site for sites in grades.values() for site in sites]
    assert sorted(covered) == sorted(gw.satisfiable(results))
    assert len(covered) == len(set(covered)), "a site graded twice"


def test_five_are_data_reachable_and_three_are_argument_only(results):
    """The number that answers Q-072, pinned so a re-grade is visible.

    Three guards can only be reached by a caller passing a value no producer in
    the package emits.  They are real argument validation and are *not* evidence
    that the suite is missing a case — saying so is the difference between this
    reading and "8 untested guards".
    """
    grades = gw.by_reachability(results)
    assert len(grades[gw.DATA_REACHABLE]) == 5
    assert len(grades[gw.ARGUMENT_ONLY]) == 3
    assert grades[gw.ARGUMENT_ONLY] == (
        "predicate_depth.measure",
        "repair_admissibility.Repair.margin_at_factor",
        "weight_units.batch_per_unit_spread",
    )


def test_every_witness_states_its_producer():
    """The grade is a judgement about the call graph and must show its working."""
    for witness in gw.WITNESSES:
        assert witness.producer.strip(), f"{witness.site} grades without a reason"
        if witness.reachability == gw.ARGUMENT_ONLY:
            assert witness.producer.startswith("none"), (
                f"{witness.site} is ARGUMENT_ONLY but names a producer")


# --------------------------------------------------------------------------
# the mirrors
# --------------------------------------------------------------------------

def _census(firings, excluded=()):
    return gv.Census(firings=tuple(firings), excluded=tuple(excluded), suite=())


def _all_clauses_as(verdict):
    return [gv.Firing(clause=c, verdict=verdict) for c in gv.guard_clauses()]


def test_unwitnessed_is_empty_over_the_real_candidate_keys():
    """Every witness key is a guard clause the AST scan actually reports.

    Uses the derived population with a synthetic verdict, so the mirror's
    semantics are checked without paying for a coverage run.  Marking all 38
    `NEVER_FIRED` is the worst case: anything the table is short of shows up.
    """
    everything = _census(_all_clauses_as(gv.VERDICT_NEVER_FIRED))
    missing = gw.unwitnessed(everything)
    witnessed = {w.site for w in gw.WITNESSES}
    assert not (witnessed & set(missing)), "a witnessed site reported unwitnessed"


def test_unwitnessed_reports_a_candidate_with_no_witness(tmp_path):
    """The mirror has teeth: an unknown candidate is named, not swallowed."""
    module = tmp_path / "invented.py"
    module.write_text(
        "def f(x):\n"
        "    if x:\n"
        "        raise ValueError('nobody wrote a witness for this')\n"
        "    return x\n",
        encoding="utf-8")
    clause, = gv.guard_clauses(tmp_path)
    cens = _census([gv.Firing(clause=clause, verdict=gv.VERDICT_NEVER_FIRED)])
    assert gw.unwitnessed(cens) == (clause.site,)


def test_unwitnessed_ignores_non_candidates(tmp_path):
    """Only `NEVER_FIRED` is the suspect set — `FIRES`/`UNREACHED` are not."""
    module = tmp_path / "invented.py"
    module.write_text(
        "def f(x):\n"
        "    if x:\n"
        "        raise ValueError('fires under the suite')\n"
        "    return x\n",
        encoding="utf-8")
    clause, = gv.guard_clauses(tmp_path)
    for verdict in (gv.VERDICT_FIRES, gv.VERDICT_UNREACHED):
        cens = _census([gv.Firing(clause=clause, verdict=verdict)])
        assert gw.unwitnessed(cens) == ()


def test_stale_witnesses_is_empty_at_head():
    """No witness names a site the scan lost — `stale_probes`' reason, one up."""
    everything = _census(_all_clauses_as(gv.VERDICT_FIRES))
    assert gw.stale_witnesses(everything) == ()


def test_stale_witnesses_flags_a_site_that_moved():
    """A witness for a deleted guard would keep `unwitnessed` quiet about it."""
    assert gw.stale_witnesses(_census([])) == tuple(
        sorted(w.site for w in gw.WITNESSES))


# --------------------------------------------------------------------------
# the census must not observe this file
# --------------------------------------------------------------------------

def test_this_file_is_excluded_from_the_census_suite():
    """Named in `EXCLUDED_TESTS`, and the name resolves to a file that exists.

    Without the exclusion these tests move all 8 candidates to `FIRES` and the
    census reads clean while no subject line changed — the instrument eating its
    own signal.
    """
    rel = "eval/mppi_sandbox/tests/test_guard_witness.py"
    assert rel in gv.EXCLUDED_TESTS
    assert (gv.PACKAGE.parent.parent / rel).is_file()


def test_measure_passes_the_exclusions_to_pytest(monkeypatch):
    """The wiring, not just the constant — `--ignore` really reaches the run.

    A registry that names an exclusion the command never applies is a stale
    literal, which is the D-047 shape this package has now hit twice.
    """
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        raise RuntimeError("stop before coverage reads anything")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError):
        gv.measure()
    for path in gv.EXCLUDED_TESTS:
        assert f"--ignore={path}" in seen["argv"]


@pytest.mark.slow
def test_witness_tests_would_otherwise_fire_the_guards():
    """The exclusion is load-bearing, shown by measuring both ways.

    Runs this file under coverage and checks the candidate guards' raise lines
    execute — i.e. that observing it really would flip `NEVER_FIRED` to `FIRES`.
    Slow because it is a real coverage subprocess (`test_calibration_member_
    fires_under_the_real_suite`'s precedent).
    """
    pytest.importorskip("coverage", reason="measure() shells out to coverage")
    executed = gv.measure(
        ("eval/mppi_sandbox/tests/test_guard_witness.py",), excluded=())
    cens = gv.census(suite=(), executed=executed)
    fired = {f.clause.site.rsplit(":", 1)[0]
             for f in cens.of(gv.VERDICT_FIRES)}
    witnessed = {w.site for w in gw.WITNESSES}
    assert witnessed <= fired, (
        f"witness tests did not fire: {sorted(witnessed - fired)}")
