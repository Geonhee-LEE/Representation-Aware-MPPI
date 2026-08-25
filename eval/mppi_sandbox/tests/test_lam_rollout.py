"""Pins for :mod:`eval.mppi_sandbox.lam_rollout` (Q-203).

Every assertion here is AST/regex work — no scenario is loaded and no rollout is
run, which is the point: the module that says *which tests are slow* must not
itself be one, or it cannot be run in the cheap lane where the answer is needed.
"""

from __future__ import annotations

import inspect

import pytest

from eval.mppi_sandbox import ab, lam_rollout as lr


def test_primitives_still_resolve_to_functions_in_ab():
    """The declared literal is pinned to the registry it copies (D-047).

    ``ROLLOUT_PRIMITIVES`` is hand-written because "spends wall clock" is not a
    property the source declares.  A rename in :mod:`ab` would otherwise empty
    the derived set silently, and an empty derived set reads exactly like "no
    test rolls out" — the clean-looking wrong answer.
    """
    for name in lr.ROLLOUT_PRIMITIVES:
        assert hasattr(ab, name), f"{name} no longer exists in ab"
        assert inspect.isfunction(getattr(ab, name)), f"ab.{name} is not a function"


def test_derived_set_is_non_empty_and_names_lam_tests():
    """Non-emptiness is the failure mode that matters; see the module docstring."""
    tests = lr.derived_rollout_tests()
    assert tests, "derived rollout set is empty — the walk found nothing"
    assert all("::test_" in nodeid for nodeid in tests)
    assert any("lam" in nodeid for nodeid in tests), (
        "no lam test reaches a rollout, which contradicts three cycles of timeouts"
    )


def test_reaching_closure_contains_the_primitives_and_their_callers():
    reaching = lr.reaching_names()
    assert lr.qualified_primitives() <= reaching
    # `lam_ladder` calls `seed_sweep`, so the fixpoint must have walked at least
    # one hop beyond the seeds rather than returning them unchanged.
    assert len(reaching) > len(lr.ROLLOUT_PRIMITIVES)


def test_qualification_keeps_the_derived_set_a_minority_of_the_suite():
    """The bare-name graph welded 57% of the suite into one component (D-473).

    This is the pin that says the qualified graph is still *discriminating*.  A
    derived set that grows back toward the whole suite is not a marker plan, and
    it would fail silently — every lam test would be "slow" and the cascade would
    be exactly as unenumerable as before.
    """
    derived = len(lr.derived_rollout_tests())
    assert 0 < derived < 500, f"derived set is {derived}; qualification regressed"


def test_parse_durations_reads_call_phase_only():
    text = (
        "============ slowest 40 durations ============\n"
        "60.12s call     eval/mppi_sandbox/tests/test_a.py::test_slow\n"
        "10.00s setup    eval/mppi_sandbox/tests/test_a.py::test_fixture_heavy\n"
        " 0.01s call     eval/mppi_sandbox/tests/test_a.py::test_fast\n"
    )
    parsed = lr.parse_durations(text)
    assert parsed == {
        "eval/mppi_sandbox/tests/test_a.py::test_slow": 60.12,
        "eval/mppi_sandbox/tests/test_a.py::test_fast": 0.01,
    }


def test_parse_durations_keeps_the_max_across_shards():
    """Fourteen concatenated pytest streams can name the same id twice."""
    text = (
        "1.00s call     t.py::test_x\n"
        "===== shard 2/14 =====\n"
        "9.00s call     t.py::test_x\n"
    )
    assert lr.parse_durations(text) == {"t.py::test_x": 9.00}


def test_measured_threshold_filters():
    text = "9.00s call     t.py::test_slow\n0.10s call     t.py::test_fast\n"
    assert lr.measured_rollout_tests(text, threshold=1.0) == ("t.py::test_slow",)
    assert lr.measured_rollout_tests(text, threshold=100.0) == ()


def test_compare_partitions_are_disjoint_and_debracket_parametrisation():
    derived = lr.derived_rollout_tests()
    assert derived, "precondition: the walk found something to compare against"
    # Feed a log naming the first derived test *with* a parametrisation suffix
    # plus one id the walk cannot know about.
    text = (
        f"5.00s call     {derived[0]}[case-3]\n"
        "5.00s call     nowhere/test_ghost.py::test_ghost\n"
    )
    cmp = lr.compare(text, threshold=1.0)
    assert derived[0] in cmp.both, "parametrised id failed to match its base name"
    assert "nowhere/test_ghost.py::test_ghost" in cmp.measured_only
    assert not (set(cmp.both) & set(cmp.derived_only))
    assert not (set(cmp.both) & set(cmp.measured_only))
    assert not (set(cmp.derived_only) & set(cmp.measured_only))


@pytest.mark.parametrize(
    "nodeid,expected",
    [
        ("a.py::test_x[case-3]", "a.py::test_x"),
        ("a.py::test_x", "a.py::test_x"),
        ("a.py::Klass::test_x[0]", "a.py::Klass::test_x"),
    ],
)
def test_debracket(nodeid, expected):
    assert lr._debracket(nodeid) == expected


def test_empty_log_is_reported_as_empty_not_as_clean():
    """A log with no durations block yields nothing — never a silent success."""
    assert lr.parse_durations("no durations here\n") == {}
    assert lr.measured_rollout_tests("no durations here\n") == ()
