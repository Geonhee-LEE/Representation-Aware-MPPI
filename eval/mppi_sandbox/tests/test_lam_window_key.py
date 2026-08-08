# SPDX-License-Identifier: BSD-3-Clause
"""`lam_windows.yaml` is keyed by (scene, controller) and read at any weight."""

from __future__ import annotations

import textwrap

import pytest

from eval.mppi_sandbox import lam_window_key as lwk

TABLE = "eval/scenarios/lam_windows.yaml"


def _table(tmp_path, body: str) -> str:
    p = tmp_path / "lam_windows.yaml"
    p.write_text(body)
    return str(p)


CELLS = textwrap.dedent("""
    cells:
      - scenario: cafe_obstacle_crossing_v0.yaml
        controller: risk_mppi
        admissible: [1.6, 3.2]
      - scenario: cafe_cut_in_v0.yaml
        controller: stock_mppi
        admissible: []
    """)


# --- the shipped table is unkeyed, which is the finding ----------------------

def test_shipped_table_records_no_calibration_weight():
    """The real file, not a fixture: every lookup against it refuses, because
    the weight it was measured at is nowhere in it."""
    look = lwk.lookup(TABLE, "cafe_obstacle_crossing_v0.yaml", "risk_mppi",
                      lwk.CALIBRATION_WEIGHT)
    assert look.verdict == lwk.UNKEYED
    assert look.usable is None
    assert look.measured_at is None
    # The recorded numbers are still readable — the refusal is about
    # provenance, not about hiding the data.
    assert look.admissible == (1.6, 3.2)


def test_unkeyed_refuses_even_at_the_calibration_weight():
    """`UNKEYED` is not softened by the caller happening to be right. The
    constant is not substituted for the missing field."""
    look = lwk.lookup(TABLE, "cafe_head_on_v0.yaml", "stock_mppi", 10.0)
    assert look.verdict == lwk.UNKEYED


# --- the four verdicts on a keyed table -------------------------------------

def test_on_key_returns_the_window(tmp_path):
    path = _table(tmp_path, "calibration_weight: 10.0\n" + CELLS)
    look = lwk.lookup(path, "cafe_obstacle_crossing_v0.yaml", "risk_mppi", 10.0)
    assert look.verdict == lwk.ON_KEY
    assert look.usable == (1.6, 3.2)


def test_off_key_refuses_at_the_weight_d133_walked(tmp_path):
    """D-133 walked this cell at `w = 150` using the `w = 10` window."""
    path = _table(tmp_path, "calibration_weight: 10.0\n" + CELLS)
    look = lwk.lookup(path, "cafe_obstacle_crossing_v0.yaml", "risk_mppi", 150.0)
    assert look.verdict == lwk.OFF_KEY
    assert look.usable is None
    assert "150" in str(look) and "10" in str(look)


def test_empty_window_is_not_no_cell(tmp_path):
    """A cell measured and found inadmissible everywhere is a different fact
    from a cell nobody measured; both refuse, under different names."""
    path = _table(tmp_path, "calibration_weight: 10.0\n" + CELLS)
    empty = lwk.lookup(path, "cafe_cut_in_v0.yaml", "stock_mppi", 10.0)
    absent = lwk.lookup(path, "city_figure8_v0.yaml", "stock_mppi", 10.0)
    assert empty.verdict == lwk.EMPTY_WINDOW and empty.found
    assert absent.verdict == lwk.NO_CELL and not absent.found
    assert empty.usable is None and absent.usable is None


def test_every_refusal_yields_none_and_on_key_does_not(tmp_path):
    """Guard non-vacuity from the other side: `ON_KEY` is reachable, so this
    is not a predicate that refuses everything."""
    path = _table(tmp_path, "calibration_weight: 10.0\n" + CELLS)
    ok = lwk.lookup(path, "cafe_obstacle_crossing_v0.yaml", "risk_mppi", 10.0)
    assert ok.usable is not None
    for w in (9.9, 150.0):
        assert lwk.lookup(path, "cafe_obstacle_crossing_v0.yaml",
                          "risk_mppi", w).usable is None


def test_scenario_accepts_a_path_or_a_basename(tmp_path):
    path = _table(tmp_path, "calibration_weight: 10.0\n" + CELLS)
    a = lwk.lookup(path, "eval/scenarios/cafe_obstacle_crossing_v0.yaml",
                   "risk_mppi", 10.0)
    b = lwk.lookup(path, "cafe_obstacle_crossing_v0.yaml", "risk_mppi", 10.0)
    assert a.verdict == b.verdict == lwk.ON_KEY


# --- window_shift: the witness that makes OFF_KEY cost something ------------

@pytest.mark.parametrize("recorded,remeasured,expect", [
    ((1.6, 3.2), (1.6, 3.2, 6.4), lwk.WINDOW_HELD),
    ((1.6, 3.2), (1.6, 3.2), lwk.WINDOW_HELD),
    ((1.6, 3.2), (0.8, 1.6), lwk.WINDOW_SHIFTED),
    ((1.6, 3.2), (0.4, 0.8), lwk.WINDOW_DISJOINT),
    ((0.4, 0.8), (), lwk.WINDOW_CLOSED),
    ((), (), lwk.WINDOW_CLOSED),
])
def test_window_shift_grades(recorded, remeasured, expect):
    assert lwk.window_shift(recorded, remeasured) == expect


def test_closed_outranks_disjoint_when_the_new_window_is_empty():
    """An arm admissible nowhere at the new weight has not *moved* — there is
    no new window to have moved to, and the caller's next move (abandon the
    cell at this weight) differs from chasing a relocated one."""
    assert lwk.window_shift((1.6, 3.2), ()) == lwk.WINDOW_CLOSED


# --- the measured witness ----------------------------------------------------

def test_crossing_w150_is_disjoint_from_the_recorded_window():
    """The reason this module exists. `risk_mppi` on
    `cafe_obstacle_crossing_v0` records `[1.6, 3.2]` at `w = 10`; re-measured
    at `w = 150` (16 seeds) its window is `{0.8}` and neither recorded rung is
    admissible. D-133 walked that cell at λ = 3.2 on the recorded window."""
    recorded = lwk.lookup(TABLE, "cafe_obstacle_crossing_v0.yaml",
                          "risk_mppi", 150.0).admissible
    assert recorded == (1.6, 3.2)
    assert lwk.CROSSING_W150["risk_mppi"] == (0.8,)
    assert lwk.window_shift(
        recorded, lwk.CROSSING_W150["risk_mppi"]) == lwk.WINDOW_DISJOINT


def test_crossing_w150_stock_window_closed():
    """The baseline arm is the one D-133 found sole-refusing at `w = 150`, and
    at 16 seeds it is admissible at no rung of the walked ladder — so the rung
    stays unscorable for a reason the table could not have disclosed."""
    recorded = lwk.lookup(TABLE, "cafe_obstacle_crossing_v0.yaml",
                          "stock_mppi", 150.0).admissible
    assert recorded == (0.4, 0.8)
    assert lwk.CROSSING_W150["stock_mppi"] == ()
    assert lwk.window_shift(
        recorded, lwk.CROSSING_W150["stock_mppi"]) == lwk.WINDOW_CLOSED


def test_no_rung_admits_both_arms_at_w150():
    """The measurement's own headline, and why the λ ladder did **not** rescue
    D-133's `w = 150` rung: the two arms' `w = 150` windows are disjoint from
    each other as well as from the table, so there is still no shared
    admissible operating point. The refusal stands and now has a mechanism."""
    stock = set(lwk.CROSSING_W150["stock_mppi"])
    risk = set(lwk.CROSSING_W150["risk_mppi"])
    assert not (stock & risk)


def test_admissible_is_derived_from_the_counts_not_restated():
    """`CROSSING_W150` must stay a function of `CROSSING_W150_ESS` — the
    all-seeds conjunction applied to stored fractions, not a second tuple."""
    for arm, counts in lwk.CROSSING_W150_ESS.items():
        assert lwk.CROSSING_W150[arm] == lwk.admissible_at(counts)
        assert all(n == 16 for _, n in counts.values())


def test_stored_fractions_rescore_under_a_looser_criterion():
    """Q-042's point, made concrete: the counts survive a criterion change and
    a stored boolean would not. At a 3/4 in-band bar the arms *do* share a
    rung — which is a different claim from admissibility, not a repair of it."""
    def at_least(counts, q):
        return tuple(sorted(lam for lam, (k, n) in counts.items()
                            if n and k / n >= q))
    stock = at_least(lwk.CROSSING_W150_ESS["stock_mppi"], 0.75)
    risk = at_least(lwk.CROSSING_W150_ESS["risk_mppi"], 0.75)
    assert stock == (0.4,) and risk == (0.4, 0.8)
    assert set(stock) & set(risk) == {0.4}
    # ...and under the shipped all-seeds criterion they share nothing.
    assert not (set(lwk.CROSSING_W150["stock_mppi"])
                & set(lwk.CROSSING_W150["risk_mppi"]))
