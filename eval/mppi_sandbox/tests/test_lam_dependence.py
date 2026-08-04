# SPDX-License-Identifier: BSD-3-Clause
"""Q-061's static half: what the 52 shipped-``lam`` sites actually assert.

The interesting tests here are the three fail-opens, because all three were
live in this module's first draft and all three shrank the lower bound —
:func:`test_bare_equality_call_is_not_silent`,
:func:`test_local_banked_table_is_an_anchor`,
:func:`test_imported_banked_constant_is_an_anchor`.
"""

from __future__ import annotations

import ast

import pytest

from eval.mppi_sandbox import default_lam_sites as dls
from eval.mppi_sandbox import lam_dependence as ld


def _classify(src: str, banked: frozenset[str] = frozenset()) -> str:
    tree = ast.parse(src)
    tests = ld._asserts(tree)
    assert len(tests) == 1, f"fixture should hold exactly one assertion: {src!r}"
    return ld.classify_assertion(tests[0], banked)


# ------------------------------------------------------- the three fail-opens

def test_bare_equality_call_is_not_silent():
    """``assert_array_equal(a, b)`` is an assertion without the ``assert`` keyword.

    Reading only ``ast.Assert`` scored eight sites ``SILENT`` — including
    ``test_same_seed_identical_trajectory`` and
    ``test_all_knobs_zero_reproduces_stock_byte_for_byte``, the two Q-061 names
    as its motivating examples.  A false ``SILENT`` says *this site makes no
    claim*, which deletes the evidence rather than mis-grading it.
    """
    fn = ast.parse("def t():\n    np.testing.assert_array_equal(a, b)\n")
    found = ld._asserts(fn)
    assert len(found) == 1
    assert ld.classify_assertion(found[0]) == ld.IDENTITY


def test_local_banked_table_is_an_anchor():
    """A measurement checked against a table of literals is not an identity."""
    src = "TABLE = {0.3: 0.28, 0.6: 0.55}\ndef t(x):\n    assert m == pytest.approx(TABLE[x], rel=0.2)\n"
    tree = ast.parse(src)
    banked = ld._local_banked(tree)
    assert "TABLE" in banked
    body = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
    assert ld.classify_assertion(body[0], banked) == ld.ANCHORED
    # ...and without the banked set it reads as the wrong thing, which is the
    # whole point of resolving them.
    assert ld.classify_assertion(body[0], frozenset()) == ld.IDENTITY


def test_imported_banked_constant_is_an_anchor():
    """``exp.CRUISE_SPEED_MPS`` stops being a constant only if you stop looking.

    Live case: ``test_cruise_speed_constant_is_current`` compares a run against
    a number banked in :mod:`exposure`.  With only local names resolved it read
    ``IDENTITY``; it is D-040's defect verbatim.
    """
    judged = {(j.site.path, j.site.line): j for j in ld.judge()}
    site = judged[("eval/mppi_sandbox/tests/test_cruise_driven_nominal.py", 113)]
    assert site.kind == ld.ANCHORED


def test_every_fail_open_moved_the_bound_the_same_way():
    """All three misses understated the floor; none of them inflated it.

    Not a tautology about this code — a statement about the *bias* of the rule
    set, which is what D-041's post-mortem asked every instrument here to
    declare.  Under-resolution (fewer banked names, fewer assertion spellings)
    can only move sites *out* of ANCHORED, never into it.
    """
    full = ld.bracket()
    tree = ast.parse("A = 0.5\ndef t():\n    assert measured > A\n")
    body = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)][0]
    assert ld.classify_assertion(body, ld._local_banked(tree)) == ld.ANCHORED
    assert ld.classify_assertion(body, frozenset()) == ld.COMPARATIVE
    assert full.lower > 0


# ------------------------------------------------------ tolerances vs anchors

@pytest.mark.parametrize("kwarg", sorted(ld.TOLERANCE_KWARGS))
def test_tolerance_kwarg_is_not_an_anchor(kwarg):
    """Scoring tolerances as anchors would read every identity as ANCHORED.

    That is available, stable and 100 % by construction — the exact failure
    D-041 diagnosed in Q-060's counting plan, one level down.
    """
    assert _classify(f"assert np.allclose(a, b, {kwarg}=1e-9)") == ld.IDENTITY


def test_relative_bound_is_comparative_not_anchored():
    """``0.8 * shipped.mean_speed`` moves with whatever it is relative to.

    Getting this wrong inflates the *lower* bound, and unlike the fail-opens
    above that would be an unsound claim rather than a conservative one.
    """
    assert _classify("assert heavy < 0.8 * shipped.mean_speed") == ld.COMPARATIVE


def test_pure_literal_bound_is_anchored():
    assert _classify("assert dist_goal <= 0.3") == ld.ANCHORED
    assert _classify("assert clearance > 0.0") == ld.ANCHORED


def test_geometry_literal_is_structural_not_anchored():
    assert _classify("assert len(traj) == 3") == ld.STRUCTURAL
    assert _classify("assert ctrl.command(x, 0.0).shape == (2,)") == ld.STRUCTURAL


def test_non_numeric_comparison_is_opaque():
    """``result["collision"] is False`` is a physical claim this cannot read.

    It lands in the unresolved band rather than in either bound — the honest
    place for a claim the syntax does not expose.
    """
    assert _classify('assert result["collision"] is False') == ld.OPAQUE


# --------------------------------------------------- reachability & precedence

def test_helper_sites_inherit_their_callers_assertions():
    """Sixteen of the 52 sit in helpers that assert nothing themselves.

    Scoring reachability without the caller edge is D-041's ``simulates`` bug
    at one level of remove: the run is made here, the claim is made there.
    """
    judged = {(j.site.path, j.site.line): j for j in ld.judge()}
    helper = judged[("eval/mppi_sandbox/tests/test_speed_overshoot_attribution.py", 53)]
    assert helper.site.function == "_response"
    assert helper.n_assertions > 0
    assert helper.kind != ld.SILENT


def test_site_takes_the_strongest_class_it_reaches():
    judged = [j for j in ld.judge() if ld.IDENTITY in j.reached and len(j.reached) > 1]
    assert judged, "fixture assumption: some site reaches identity plus something"
    for j in judged:
        assert ld.PRECEDENCE.index(j.kind) <= ld.PRECEDENCE.index(ld.IDENTITY)


def test_precedence_ranks_every_class_exactly_once():
    assert len(set(ld.PRECEDENCE)) == len(ld.PRECEDENCE)
    assert set(ld.TEMPERATURE_RELEVANT) <= set(ld.PRECEDENCE)


# ------------------------------------------------------------- the bracket

def test_population_is_exactly_d041s_census():
    """This module re-partitions D-041's population; it must not resize it."""
    assert ld.bracket().total == dls.census().weighting_at_shipped


def test_identity_is_not_subtracted_from_the_bill():
    """The one subtraction that would make the number smaller is refused.

    "These two runs agree at ``lam = 0.1``" is evidence about that rung, not a
    proof of a contract.  Discharging it is what Q-061 (c)'s instrument is for,
    so ``unresolved`` has to still contain the identities.
    """
    b = ld.bracket()
    assert b.upper == b.total
    assert b.unresolved == b.total - b.lower
    assert b.unresolved >= b.counts.get(ld.IDENTITY, 0)


def test_bill_floor_survives_granting_the_whole_conjecture():
    """Even if every IDENTITY is temperature-symmetric, the bill stays large.

    This is the finding: Q-061's premise is true but small.  The population is
    dominated by anchored physical claims, so subtracting the contract tests
    does not turn the re-run into a cheap job.
    """
    b = ld.bracket()
    granted = b.total - b.counts.get(ld.IDENTITY, 0)
    assert granted > b.total // 2
    assert b.lower <= granted


def test_two_rung_cost_is_double_the_site_count():
    """Q-061's lean says one admissible rung cannot decide it (a pass may be luck)."""
    b = ld.bracket()
    assert b.simulations_at_two_rungs == (b.lower * 2, b.upper * 2)


def test_two_sites_are_not_tests_and_neither_bills_a_sim():
    """``run.py``'s CLI ships the default; it makes no claim to re-measure.

    It belongs to Q-060 (the disposition of the default), not to Q-061 (which
    banked claims move).  Reporting it inside the 52 without saying so would
    let a reader price it into the sim bill.

    D-060 adds a second, and it is a **false site**:
    ``guard_witness._w_batch_per_unit_spread`` calls a simulating function
    without naming a ``lam``, so the static detector scores it ``DEFAULTS``.  It
    provably never simulates — the call exists to make ``batch_per_unit_spread``
    raise ``KeyError`` on an unknown knob, and that raise precedes every use of
    ``scenario``, which ``test_guard_witness`` asserts by execution.  So the
    site's sim bill is **zero** and neither entry here is a re-measurement:
    ``run.py`` because it makes no claim, this one because it makes no run.

    That a call which cannot reach the simulator still counts as a site is a
    real bound on ``_all_sites``, filed as Q-073 rather than papered over — the
    detector is syntactic and reachability is not.
    """
    non_test = [j for j in ld.judge() if "/tests/" not in j.site.path]
    assert sorted(j.site.path for j in non_test) == [
        "eval/mppi_sandbox/guard_witness.py",
        "eval/mppi_sandbox/run.py",
    ]
    assert {j.kind for j in non_test} == {ld.SILENT}


def test_report_states_both_bounds():
    text = ld.report()
    assert "lower bound" in text and "upper bound" in text
    assert str(ld.bracket().lower) in text
