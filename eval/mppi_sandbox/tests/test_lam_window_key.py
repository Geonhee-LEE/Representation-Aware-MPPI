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


# --- the second re-measured cell: the one that held (Q-117) ------------------

def test_headon_w100_window_held_on_both_arms():
    """Q-117's question, answered on its reassuring branch. Both arms of
    `cafe_head_on_v0` re-measure at `w = 100` to exactly their recorded
    `[0.2, 0.4, 0.8]`, so a caller reading the `w = 10` table for this cell
    would have run in band."""
    cell = lwk.HEADON_W100_CELL
    for arm in ("stock_mppi", "risk_mppi"):
        assert cell.recorded(arm) == (0.2, 0.4, 0.8)
        assert cell.window(arm) == (0.2, 0.4, 0.8)
        assert cell.shift(arm) == lwk.WINDOW_HELD


def test_d132_operating_point_is_admissible_for_both_arms():
    """The claim this cycle was spent on. D-131/D-132's band (`{75, 100, 150}`
    at p = 2.5e-4) was walked at λ = 0.8 taken from the unkeyed table; λ = 0.8
    is in the re-measured window of **both** arms at `w = 100`, so the band's
    temperature was admissible and D-134 does not reach it."""
    cell = lwk.HEADON_W100_CELL
    assert 0.8 in cell.shared()
    for arm in cell.arms:
        assert cell.counts[arm][0.8] == (16, 16)


def test_headon_window_held_exactly_with_nothing_to_spare():
    """`WINDOW_HELD` here is equality, not containment: 1.6 is 0/16 on both
    arms. Worth asserting because a window that held *by widening* would be a
    weaker reassurance than one that held on its recorded support."""
    cell = lwk.HEADON_W100_CELL
    for arm in cell.arms:
        assert set(cell.window(arm)) == set(cell.recorded(arm))
        assert cell.counts[arm][1.6] == (0, 16)


def test_shared_is_empty_on_crossing_and_nonempty_on_headon():
    """`shared()` is the "can this cell be A/B'd at one λ at all" question, and
    the two registry cells answer it oppositely — which is the whole reason
    D-133's rung is unscorable and D-132's band is not."""
    assert lwk.CROSSING_W150_CELL.shared() == ()
    assert lwk.HEADON_W100_CELL.shared() == (0.2, 0.4, 0.8)


# --- the census: one cell is an anecdote, two are a rate ---------------------

def test_shift_census_enumerates_every_arm_cell():
    """A rate whose numerator cannot be named is the shape `published_ratios`
    refuses, so the census returns members and not counts. Every arm of every
    registered cell appears exactly once."""
    census = lwk.shift_census()
    listed = [label for labels in census.values() for label in labels]
    expected = sum(len(c.arms) for c in lwk.REMEASURED)
    assert len(listed) == expected == 4
    assert len(set(listed)) == len(listed)


def test_census_splits_two_held_two_moved():
    """The honest headline. Both failures are the same scene, and both holds
    are the other — so the guard is neither vacuous nor universal."""
    census = lwk.shift_census()
    assert census[lwk.WINDOW_HELD] == (
        "cafe_head_on_v0.yaml:risk_mppi@w=100",
        "cafe_head_on_v0.yaml:stock_mppi@w=100",
    )
    assert census[lwk.WINDOW_DISJOINT] == (
        "cafe_obstacle_crossing_v0.yaml:risk_mppi@w=150",)
    assert census[lwk.WINDOW_CLOSED] == (
        "cafe_obstacle_crossing_v0.yaml:stock_mppi@w=150",)
    assert lwk.WINDOW_SHIFTED not in census


def test_census_is_not_vacuous_in_either_direction():
    """Guard non-vacuity from both sides at once (D-044 / `guard_vacuity`): a
    census that graded everything `HELD` would make `OFF_KEY` unmotivated, and
    one that graded everything a refusal would make the guard unfalsifiable."""
    census = lwk.shift_census()
    refusing = {lwk.WINDOW_DISJOINT, lwk.WINDOW_CLOSED, lwk.WINDOW_SHIFTED}
    assert census.get(lwk.WINDOW_HELD)
    assert refusing & set(census)


# --- registry plumbing -------------------------------------------------------

def test_every_registry_cell_derives_its_window_from_its_counts():
    """Extends the D-047 check to the whole registry: no cell may restate its
    own window, and every count must be over the seed budget it declares."""
    for cell in lwk.REMEASURED:
        for arm, counts in cell.counts.items():
            assert cell.window(arm) == lwk.admissible_at(counts)
            assert set(counts) == set(cell.ladder)
            assert all(n == cell.seeds for _, n in counts.values())
            assert all(0 <= k <= n for k, n in counts.values())


def test_remeasurement_lookup_is_keyed_by_scene_and_weight():
    """The registry is keyed by the pair, because the same scene at another
    weight is a different measurement — that is D-134's entire finding."""
    assert lwk.remeasurement("cafe_head_on_v0.yaml", 100.0) is lwk.HEADON_W100_CELL
    assert lwk.remeasurement("eval/scenarios/cafe_head_on_v0.yaml",
                             100.0) is lwk.HEADON_W100_CELL
    # right scene, weight nobody walked
    assert lwk.remeasurement("cafe_head_on_v0.yaml", 150.0) is None
    # right weight, scene nobody walked
    assert lwk.remeasurement("cafe_straight_v0.yaml", 100.0) is None


def test_crossing_views_still_agree_with_the_registry_cell():
    """`CROSSING_W150_ESS` / `CROSSING_W150` survive as views of the cell, not
    as a second copy of its data."""
    assert lwk.CROSSING_W150_ESS is lwk.CROSSING_W150_CELL.counts
    for arm in lwk.CROSSING_W150_CELL.arms:
        assert lwk.CROSSING_W150[arm] == lwk.CROSSING_W150_CELL.window(arm)
