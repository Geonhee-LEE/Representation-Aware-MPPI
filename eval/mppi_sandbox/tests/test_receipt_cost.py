"""Tests for :mod:`eval.mppi_sandbox.receipt_cost` (STATE #1).

The load-bearing tests are the ones that make the module *refuse*.  A pricer
whose tests only check that it adds up correctly is a pricer that cannot fail,
and its whole reason to exist is that the obvious way to price a subset —
sum what ``--durations`` printed — is wrong in the direction that makes a bad
subset look good.  So:

* both directions of the truncation verdict (a complete report grades
  ``COMPLETE``, a truncated one ``TRUNCATED`` and yields bounds not a price);
* an empty report grades ``NO_DURATIONS`` and never prices anything at zero;
* the budget arithmetic reproduces the 2026-08-10 12:00 strand.
"""

from __future__ import annotations

from eval.mppi_sandbox import receipt_cost as rc


# A report where the rows account for the run: 3 + 5 + 90 = 98 of 100s.
COMPLETE_REPORT = """
============================= slowest durations ==============================
90.00s call     eval/mppi_sandbox/tests/test_sim_heavy.py::test_walk
5.00s setup    eval/mppi_sandbox/tests/test_sim_heavy.py::test_walk
3.00s call     eval/mppi_sandbox/tests/test_fast.py::test_parses
=============== 2 passed in 100.00s (0:01:40) ================================
"""

# Same rows, but the run took 1000s — 902s of tail was never printed.
TRUNCATED_REPORT = COMPLETE_REPORT.replace(
    "2 passed in 100.00s (0:01:40)", "900 passed in 1000.00s (0:16:40)"
)


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------


def test_parses_all_phases_not_just_call():
    """Setup cost is billed to the test that pays it.

    A per-test cost that counted only ``call`` would read a sim-bound test
    whose fixture does the simulating as free — the exact reading that would
    most mislead a subset proposal.
    """
    durations = rc.parse_durations(COMPLETE_REPORT)
    assert len(durations) == 3
    assert {d.phase for d in durations} == {"call", "setup"}
    assert rc.by_module(durations)["eval/mppi_sandbox/tests/test_sim_heavy.py"] == 95.0


def test_prose_lines_are_not_duration_rows():
    """The input is a whole run's stdout, most of which is not timings."""
    assert rc.parse_durations("no rows here\n=== 5 passed in 1.0s ===") == ()


def test_total_comes_from_the_summary_line():
    assert rc.parse_total(COMPLETE_REPORT) == 100.0
    assert rc.parse_total("no summary") is None


# --------------------------------------------------------------------------
# the finding: a truncated report prices a subset too cheaply
# --------------------------------------------------------------------------


def test_complete_report_prices_the_subset():
    p = rc.price(COMPLETE_REPORT, keep=("eval/mppi_sandbox/tests/test_fast.py",))
    assert p.verdict == rc.COMPLETE
    assert p.is_priced
    assert p.kept_seconds == 3.0
    assert p.dropped_seconds == 95.0
    # COMPLETE does not mean "no tail" — it means the tail is within tolerance,
    # so the bound sits just above the price rather than collapsing onto it.
    # Asserting equality here would be asserting a stronger property than the
    # module offers, and it would fail the moment the tolerance is exercised at
    # all, which is the case this fixture is built to sit exactly on.
    assert p.unreported_seconds == 2.0 == 0.02 * p.total_seconds
    assert p.kept_upper_bound == 5.0


def test_truncated_report_yields_bounds_not_a_price():
    """The same rows, a longer run: the subset is bracketed, not priced.

    This is the whole module.  Summing the printed rows gives 3.0s either way;
    only the reconciliation against the independently-measured total reveals
    that 902s of unattributed tail could be sitting inside the subset.
    """
    p = rc.price(TRUNCATED_REPORT, keep=("eval/mppi_sandbox/tests/test_fast.py",))
    assert p.verdict == rc.TRUNCATED
    assert not p.is_priced
    assert p.kept_seconds == 3.0, "the naive sum is unchanged — that is the trap"
    assert p.unreported_seconds == 902.0
    assert p.kept_upper_bound == 905.0
    assert "bounded by" in p.describe()


def test_missing_summary_line_cannot_grade_complete():
    """No independent total ⇒ no reconciliation ⇒ no claim of completeness."""
    no_total = COMPLETE_REPORT.replace("=============== 2 passed in 100.00s (0:01:40) ================================", "")
    p = rc.price(no_total, keep=())
    assert p.verdict == rc.TRUNCATED
    assert p.total_seconds is None


def test_empty_report_is_not_a_free_subset():
    """``NO_DURATIONS`` is the absence of a measurement, not a cheap one."""
    p = rc.price("=== 0 passed in 0.10s ===", keep=("anything.py",))
    assert p.verdict == rc.NO_DURATIONS
    assert not p.is_priced
    assert p.kept_seconds == 0.0
    assert "cannot be priced" in p.describe()


def test_rows_exceeding_the_total_do_not_make_a_negative_tail():
    """Shared setup is billed per-test, so rows can outrun the wall clock."""
    over = COMPLETE_REPORT.replace("2 passed in 100.00s", "2 passed in 10.00s")
    p = rc.price(over, keep=())
    assert p.unreported_seconds == 0.0
    assert p.kept_upper_bound == 0.0


def test_unknown_module_in_keep_is_not_an_error_but_buys_nothing():
    """A subset naming a module that did not run costs what it costs: nothing."""
    p = rc.price(COMPLETE_REPORT, keep=("eval/mppi_sandbox/tests/test_absent.py",))
    assert p.kept_seconds == 0.0
    assert p.dropped_seconds == 98.0
    assert p.kept_modules == ()


# --------------------------------------------------------------------------
# budget arithmetic — the number the 12:00 strand needed
# --------------------------------------------------------------------------


def test_the_suite_admits_exactly_one_run_per_cycle():
    """17m43 against 35 min with ~6 min of overhead: one run, not two.

    D-044's "budget for paying it twice" is arithmetically unavailable at this
    suite cost, independently of whether the inert-surface filter makes the
    second run unnecessary.
    """
    b = rc.Budget(suite_seconds=1063.0, budget_seconds=2100.0, overhead_seconds=360.0)
    assert b.runs_affordable == 1


def test_the_1200_strand_is_reproduced():
    """A suite started with less than its own cost left strands the cycle.

    12:00 ended in 12m44 having reached EXECUTE too late to take a receipt.
    ``latest_start_seconds`` is the number that would have told it so.
    """
    b = rc.Budget(suite_seconds=1063.0, budget_seconds=2100.0, overhead_seconds=360.0)
    assert b.latest_start_seconds == 1037.0
    assert b.strands(started_at_seconds=1200.0)
    assert not b.strands(started_at_seconds=900.0)


def test_a_suite_larger_than_the_budget_reports_negative_slack():
    """Clamping to zero would hide that starting earlier cannot fix it."""
    b = rc.Budget(suite_seconds=2400.0, budget_seconds=2100.0, overhead_seconds=360.0)
    assert b.runs_affordable == 0
    assert b.latest_start_seconds == -300.0
    assert b.strands(started_at_seconds=0.0)
