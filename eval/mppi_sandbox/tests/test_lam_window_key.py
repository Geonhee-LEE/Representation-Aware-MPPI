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


# --- the shipped table is keyed now, and UNKEYED lost its live exemplar ------

def test_shipped_table_now_records_the_weight_it_was_walked_at():
    """Was `test_shipped_table_records_no_calibration_weight`, inverted by
    D-477. The real file, not a fixture: it used to refuse every lookup because
    the weight it was measured at was nowhere in it. D-470 measured it (33.1
    min over 8 controllers) and D-477 installed the result, so the same call
    now resolves.

    Kept pointed at the real path rather than deleted, because the assertion
    that changed is the one that says *which* file the project's windows come
    from.
    """
    look = lwk.lookup(TABLE, "cafe_obstacle_crossing_v0.yaml", "risk_mppi",
                      lwk.CALIBRATION_WEIGHT)
    assert look.verdict == lwk.ON_KEY
    assert look.measured_at == 10.0
    assert look.usable == look.admissible


def test_unkeyed_is_still_reachable_now_that_no_shipped_table_exercises_it(
        tmp_path):
    """Was `test_unkeyed_refuses_even_at_the_calibration_weight`, and the
    rewrite is the load-bearing half of D-477.

    Both of this section's tests used the shipped table as the repo's **only
    live example of an unkeyed table**. Keying it did not weaken `UNKEYED` — it
    removed every witness that the verdict is still produced at all, which is
    precisely the state D-317 warns reads clean from outside: a refusal nobody
    can reach and a refusal that was deleted look identical in a green run.

    So the exemplar moves into a fixture and the property it asserted is
    restated unchanged: `UNKEYED` is not softened by the caller happening to
    name the right weight. `lwk.CALIBRATION_WEIGHT` is *not* substituted for a
    missing `calibration_weight:` field.
    """
    path = _table(tmp_path, CELLS)  # note: no `calibration_weight:` line
    look = lwk.lookup(path, "cafe_obstacle_crossing_v0.yaml", "risk_mppi",
                      lwk.CALIBRATION_WEIGHT)
    assert look.verdict == lwk.UNKEYED
    assert look.usable is None
    assert look.measured_at is None
    # The recorded numbers stay readable — the refusal is about provenance,
    # not about hiding the data.
    assert look.admissible == (1.6, 3.2)


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
    assert len(listed) == expected == 6
    assert len(set(listed)) == len(listed)


def test_census_splits_four_held_two_moved():
    """The honest headline. Both failures are the same scene, and all four
    holds are the other — so the guard is neither vacuous nor universal."""
    census = lwk.shift_census()
    assert census[lwk.WINDOW_HELD] == (
        "cafe_head_on_v0.yaml:risk_mppi@w=100",
        "cafe_head_on_v0.yaml:risk_mppi@w=150",
        "cafe_head_on_v0.yaml:stock_mppi@w=100",
        "cafe_head_on_v0.yaml:stock_mppi@w=150",
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
    # same scene at another weight is a different cell, not the same one
    assert lwk.remeasurement("cafe_head_on_v0.yaml", 150.0) is lwk.HEADON_W150_CELL
    # right scene, weight nobody walked
    assert lwk.remeasurement("cafe_head_on_v0.yaml", 300.0) is None
    # right weight, scene nobody walked
    assert lwk.remeasurement("cafe_straight_v0.yaml", 100.0) is None


def test_crossing_views_still_agree_with_the_registry_cell():
    """`CROSSING_W150_ESS` / `CROSSING_W150` survive as views of the cell, not
    as a second copy of its data."""
    assert lwk.CROSSING_W150_ESS is lwk.CROSSING_W150_CELL.counts
    for arm in lwk.CROSSING_W150_CELL.arms:
        assert lwk.CROSSING_W150[arm] == lwk.CROSSING_W150_CELL.window(arm)


# --- attribution: which axis a shift belongs to ------------------------------

def _cell(scenario: str, weight: float, windows: dict[str, tuple[float, ...]]):
    """A synthetic `Remeasurement` whose per-arm admissible set is `windows`.

    Counts are synthesised as all-or-nothing over a 4-seed budget, since
    `admissible_at` reads only `k == n`. Synthetic rather than registry cells
    because the logic under test is the *design* — which pairs isolate which
    axis — and pinning that to whichever cells the registry currently holds
    would make every future measurement a test edit.
    """
    ladder = (0.2, 0.4, 0.8, 1.6)
    return lwk.Remeasurement(
        scenario=scenario, weight=weight, seeds=4, ladder=ladder,
        margin=0.40, measured_on="synthetic",
        counts={arm: {lam: ((4, 4) if lam in win else (0, 4)) for lam in ladder}
                for arm, win in windows.items()},
    )


def test_two_cells_differing_in_both_axes_isolate_neither():
    """The registry's opening state, and the reason Q-118 was worth a cycle:
    one pair that differs in scene *and* weight supports no attribution at
    all."""
    cells = (_cell("a.yaml", 150.0, {"stock_mppi": (0.2,)}),
             _cell("b.yaml", 100.0, {"stock_mppi": (0.4,)}))
    for factor in (lwk.SCENE, lwk.WEIGHT):
        assert lwk.contrasts(factor, cells) == ()
        assert lwk.attribution(factor, cells=cells) == lwk.NO_CONTRAST


def test_holding_the_scene_fixed_isolates_the_weight_axis():
    """Two weights on one scene isolate weight and say nothing about scene."""
    cells = (_cell("a.yaml", 100.0, {"stock_mppi": (0.2,)}),
             _cell("a.yaml", 150.0, {"stock_mppi": (0.4,)}))
    assert len(lwk.contrasts(lwk.WEIGHT, cells)) == 1
    assert lwk.contrasts(lwk.SCENE, cells) == ()
    assert lwk.attribution(lwk.SCENE, cells=cells) == lwk.NO_CONTRAST


def test_an_isolated_axis_grades_moves_or_inert_by_the_arms_grades():
    """`FACTOR_MOVES` is a difference in *grade*, not in window: two cells can
    hold different windows and still both grade `WINDOW_CLOSED`."""
    recorded = (0.2, 0.4)
    moves = (_cell("a.yaml", 100.0, {"stock_mppi": recorded}),      # HELD
             _cell("a.yaml", 150.0, {"stock_mppi": ()}))            # CLOSED
    inert = (_cell("a.yaml", 100.0, {"stock_mppi": ()}),            # CLOSED
             _cell("a.yaml", 150.0, {"stock_mppi": ()}))            # CLOSED
    table = "eval/scenarios/lam_windows.yaml"
    assert lwk.attribution(lwk.WEIGHT, table, moves) == lwk.FACTOR_MOVES
    assert lwk.attribution(lwk.WEIGHT, table, inert) == lwk.FACTOR_INERT


def test_an_isolated_pair_sharing_no_arm_is_not_called_inert():
    """Nothing was compared, so the answer is `NO_CONTRAST` and not agreement.
    Collapsing "cannot tell" into `FACTOR_INERT` is the empty-denominator
    failure D-107/D-120/D-127 each booked."""
    cells = (_cell("a.yaml", 100.0, {"stock_mppi": (0.2,)}),
             _cell("a.yaml", 150.0, {"risk_mppi": (0.4,)}))
    assert len(lwk.contrasts(lwk.WEIGHT, cells)) == 1
    assert lwk.attribution(lwk.WEIGHT, cells=cells) == lwk.NO_CONTRAST


def test_unknown_factor_is_refused_by_name():
    with pytest.raises(ValueError):
        lwk.contrasts("temperature")


def test_the_registry_separates_scene_from_weight():
    """Q-118's answer, and the reason the third cell was worth ~300 s: the
    census can now say *which* axis its two movers belong to. Windows move on
    the pathological scene; the 100 → 150 weight excursion moves nothing."""
    assert lwk.attribution(lwk.SCENE) == lwk.FACTOR_MOVES
    assert lwk.attribution(lwk.WEIGHT) == lwk.FACTOR_INERT


def test_each_axis_is_isolated_by_exactly_one_pair():
    """The contrasts are the ones the walk was chosen to create: crossing vs
    head_on at the shared `w = 150`, and head_on's two weights at the shared
    scene. Asserted so a future cell that silently breaks the design — a fresh
    (scene, weight) pair adding no contrast — is visible here."""
    (a, b), = lwk.contrasts(lwk.SCENE)
    assert a.weight == b.weight == 150.0
    assert {a.scenario, b.scenario} == {"cafe_obstacle_crossing_v0.yaml",
                                        "cafe_head_on_v0.yaml"}
    (c, d), = lwk.contrasts(lwk.WEIGHT)
    assert c.scenario == d.scenario == "cafe_head_on_v0.yaml"
    assert {c.weight, d.weight} == {100.0, 150.0}


def test_headon_holds_at_both_measured_weights():
    """The weight-inertness above is set *equality* at both weights, not a
    window that widened at one of them — 1.6 is 0/16 on every arm-cell of this
    scene. A window that held by widening would grade `WINDOW_HELD` too and
    would be a weaker claim."""
    for cell in (lwk.HEADON_W100_CELL, lwk.HEADON_W150_CELL):
        for arm in cell.arms:
            assert cell.shift(arm) == lwk.WINDOW_HELD
            assert set(cell.window(arm)) == set(cell.recorded(arm))
            assert cell.counts[arm][1.6] == (0, 16)


def test_d132_w150_rung_was_walked_at_an_admissible_temperature():
    """This walk could have retracted a rung D-132 shipped and did not.
    `w = 150` is inside the band `{75, 100, 150}`, walked at λ = 0.8 off the
    unkeyed table; λ = 0.8 is admissible for **both** arms at that weight."""
    cell = lwk.HEADON_W150_CELL
    assert 0.8 in cell.shared()
    for arm in cell.arms:
        assert cell.counts[arm][0.8] == (16, 16)


def test_the_census_counts_six_arm_cells_and_names_its_movers():
    """4 of 6 held. The two that did not are both crossing, which is what
    makes the scene attribution above legible rather than a bare grade."""
    census = lwk.shift_census()
    assert sum(len(v) for v in census.values()) == 6
    assert len(census[lwk.WINDOW_HELD]) == 4
    movers = census[lwk.WINDOW_CLOSED] + census[lwk.WINDOW_DISJOINT]
    assert all("cafe_obstacle_crossing_v0" in label for label in movers)
