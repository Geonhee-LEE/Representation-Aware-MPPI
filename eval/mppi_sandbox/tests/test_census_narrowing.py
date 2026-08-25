"""Tests for :mod:`census_narrowing`.

The semantics are exercised on **synthetic** attributed records, not on a
nested suite run.  That is the point of the module: the counterfactual is a
fold, so everything except the one expensive run is pure and can be pinned
cheaply.  The negative control is load-bearing here — a comparison that can
only ever say ``PRESERVED`` would look identical to a correct one on this
package's real record, which is exactly D-090's two-zeroes problem.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import census_narrowing as cn
from eval.mppi_sandbox import nested_subject as ns
from eval.mppi_sandbox import predicate_vacuity as pv


def _pred(qualname: str, module: str = "m") -> pv.Predicate:
    return pv.Predicate(module=module, qualname=qualname, kind=pv.KIND_FUNCTION,
                        lineno=1, admitted_by=pv.ADMIT_ANNOTATION,
                        returns=("x > 0",), path=Path("m.py"))


def _obs(site: str, true_calls: int = 0, false_calls: int = 0,
         other: tuple[str, ...] = ()) -> pv.Observation:
    return pv.Observation(site=site, true_calls=true_calls,
                          false_calls=false_calls, other_types=other)


# --------------------------------------------------------------------------
# The negative control, first — the comparison must be able to say CHANGED
# --------------------------------------------------------------------------


def test_hiding_the_only_false_origin_moves_a_verdict_to_changed():
    """BOTH survives only while both origins are read."""
    pred = _pred("f")
    attributed = {"m.f": {"tests/a.py": _obs("m.f", true_calls=3),
                          "tests/b.py": _obs("m.f", false_calls=2)}}

    comp = cn.compare(attributed, hidden=["tests/b.py"], population=[pred])

    assert comp.verdict == cn.CHANGED
    assert not comp.admissible
    assert [str(m) for m in comp.moved] == [
        f"m.f: {pv.VERDICT_BOTH} -> {pv.VERDICT_ALWAYS_TRUE}"]
    assert comp.before[pv.VERDICT_BOTH] == 1
    assert comp.after[pv.VERDICT_ALWAYS_TRUE] == 1


def test_hiding_the_only_origin_at_all_moves_a_verdict_to_unobserved():
    pred = _pred("f")
    attributed = {"m.f": {"tests/a.py": _obs("m.f", true_calls=1,
                                             false_calls=1)}}

    comp = cn.compare(attributed, hidden=["tests/a.py"], population=[pred])

    assert comp.verdict == cn.CHANGED
    assert comp.moved[0].after == pv.VERDICT_UNOBSERVED


# --------------------------------------------------------------------------
# PRESERVED, and the two different things it can mean
# --------------------------------------------------------------------------


def test_preserved_when_the_hidden_origin_contributed_nothing():
    """D-090's mechanism, confirmed at the level of observations."""
    pred = _pred("f")
    attributed = {"m.f": {"tests/a.py": _obs("m.f", true_calls=1,
                                             false_calls=1)}}

    comp = cn.compare(attributed, hidden=["tests/spawner.py"],
                      population=[pred])

    assert comp.verdict == cn.PRESERVED
    assert comp.admissible
    assert comp.removed == 0
    assert comp.contributed == {}


def test_preserved_while_removing_real_observations_reports_the_removal():
    """A narrowing can be admissible and still not be free.

    The count is what separates "the hidden files were never contributing" from
    "they were contributing and it happened not to matter"; a single boolean
    would report both as the same fact.
    """
    pred = _pred("f")
    attributed = {"m.f": {"tests/a.py": _obs("m.f", true_calls=1,
                                             false_calls=1),
                          "tests/b.py": _obs("m.f", true_calls=4)}}

    comp = cn.compare(attributed, hidden=["tests/b.py"], population=[pred])

    assert comp.verdict == cn.PRESERVED
    assert comp.admissible
    assert comp.removed == 4
    assert comp.contributed == {"tests/b.py": 4}


def test_contributions_omits_hidden_files_the_record_never_mentions():
    attributed = {"m.f": {"tests/a.py": _obs("m.f", true_calls=1)}}

    assert cn.contributions(attributed, ["tests/b.py", "tests/c.py"]) == {}


# --------------------------------------------------------------------------
# VACUOUS — decided before equality, three ways
# --------------------------------------------------------------------------


def test_empty_record_is_vacuous_not_preserved():
    comp = cn.compare({}, hidden=["tests/a.py"], population=[_pred("f")])

    assert comp.verdict == cn.VACUOUS
    assert comp.vacuity == "no observations"
    assert not comp.admissible


def test_record_with_only_zero_call_slots_is_vacuous():
    attributed = {"m.f": {"tests/a.py": _obs("m.f")}}

    comp = cn.compare(attributed, hidden=["tests/a.py"], population=[_pred("f")])

    assert comp.verdict == cn.VACUOUS
    assert comp.vacuity == "no observations"


def test_record_attributing_everything_to_nobody_is_vacuous():
    """No choice of hidden files can change this fold."""
    attributed = {"m.f": {cn.UNATTRIBUTED: _obs("m.f", true_calls=2,
                                                false_calls=2)}}

    comp = cn.compare(attributed, hidden=["tests/a.py"], population=[_pred("f")])

    assert comp.verdict == cn.VACUOUS
    assert comp.vacuity == "no attributed origins"
    assert not comp.admissible


def test_empty_population_is_vacuous():
    attributed = {"m.f": {"tests/a.py": _obs("m.f", true_calls=1)}}

    comp = cn.compare(attributed, hidden=["tests/a.py"], population=[])

    assert comp.verdict == cn.VACUOUS
    assert comp.vacuity == "no population"


def test_vacuity_outranks_a_moved_verdict():
    """Emptiness is decided first, so a fold over nothing never reads CHANGED."""
    comp = cn.compare({}, hidden=["tests/a.py"], population=[_pred("f")])

    assert comp.verdict == cn.VACUOUS
    assert comp.moved == ()


# --------------------------------------------------------------------------
# The hidden set is the one D-090 named, in a spelling that can match
# --------------------------------------------------------------------------


def test_hidden_origins_emits_both_absolute_and_repo_relative_spellings():
    hidden = cn.hidden_origins()
    spawning = ns.spawning()

    assert spawning, "D-090's population is empty — the bound has gone away"
    assert len(hidden) == 2 * len(spawning)
    for path in spawning:
        assert str(path) in hidden
        assert path.name in {Path(h).name for h in hidden}


def test_hidden_origins_relative_spellings_are_repo_relative_posix():
    relative = [h for h in cn.hidden_origins() if not h.startswith("/")]

    assert relative
    for h in relative:
        assert h.startswith("eval/"), h
        assert "\\" not in h


def test_hidden_origins_never_names_a_file_the_census_already_ignores():
    """The two exemptions have different reasons and must not be conflated.

    ``EXCLUDED_TESTS`` hides files that would let the census observe *itself*
    (D-060); this narrowing hides files whose observations never arrive (D-090).
    A file in both would make the second population look larger than the saving
    it can deliver.
    """
    already = {Path(p).name for p in pv.EXCLUDED_TESTS}
    named = {Path(h).name for h in cn.hidden_origins()}

    assert not (already & named)


# --------------------------------------------------------------------------
# Reflexivity, per D-083 — this module is inside its own subject
# --------------------------------------------------------------------------


def test_this_test_file_is_not_in_the_hidden_set():
    """And that is a claim about the module, checked rather than assumed.

    The first draft asserted the opposite — that this file spawns and therefore
    hides itself, copying ``test_nested_subject``'s reflexive position — and it
    failed.  It failed because it is **wrong**: every test above works on
    synthetic records, so nothing here shells out, and the file is graded
    ``IN_PROCESS``.  That is the better position of the two.  ``test_nested_
    subject`` sits inside the population it narrows away, so the evidence for
    the narrowing is partly evidence the narrowing would delete; this file does
    not, so it keeps contributing observations after the narrowing lands.
    """
    assert Path(__file__).name not in {Path(h).name for h in cn.hidden_origins()}
    assert ns.classify(Path(__file__).read_text(encoding="utf-8")) == ns.IN_PROCESS


def test_measure_is_the_only_function_here_that_runs_a_suite():
    """Everything else is pure, which is what makes one run enough.

    Read off this module's AST rather than off ``ns.spawners()``: that set is
    keyed on **bare names** (``key_conflation``'s defect class, accepted there
    with its consequence stated), and ``measure`` is a name three modules own,
    so asking it whether *this* ``measure`` spawns gets an answer that would be
    the same if this one were pure.
    """
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(cn))
    spawning_funcs = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                and c.func.attr == "measure_attributed"
                for c in ast.walk(node))
    }

    assert spawning_funcs == {"measure"}


@pytest.mark.parametrize("verdict", [cn.PRESERVED, cn.CHANGED, cn.VACUOUS])
def test_every_verdict_is_reachable(verdict):
    """Exhaustiveness, per D-081: a verdict no test reaches is not shipped."""
    pred = _pred("f")
    cases = {
        cn.PRESERVED: ({"m.f": {"tests/a.py": _obs("m.f", 1, 1)}},
                       ["tests/z.py"]),
        cn.CHANGED: ({"m.f": {"tests/a.py": _obs("m.f", 1, 1)}},
                     ["tests/a.py"]),
        cn.VACUOUS: ({}, ["tests/a.py"]),
    }
    attributed, hidden = cases[verdict]

    assert cn.compare(attributed, hidden, [pred]).verdict == verdict
