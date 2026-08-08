# SPDX-License-Identifier: BSD-3-Clause
"""Q-119: price the generator against answers we already know — now the matrix.

D-138 shipped the write half of `calibration_weight:` and proved the round trip
synthetically — `to_yaml` writes a weight, `lookup` reads it back, on hand-built
cells that never touch the simulator. What that could not show is whether the
*measuring* half still produces the same windows once a weight is threaded
through it. `ab.lam_ladder` gained a `w_obs_soft` parameter to carry the weight
down to `MPPIParams`; a table generated through that new path is only
trustworthy if walking it at the weight the shipped table was already generated
at reproduces the shipped rows.

So this file checks a **regeneration**, not a fresh measurement. The shipped
`lam_windows.yaml` was generated at the controller default (`w_obs_soft = 10`),
and `eval/scenarios/variants/lam_windows_w10.yaml` re-walks it at an explicit
`--w-obs-soft 10`. If the two agree, the weight-threading is behaviour-preserving
at the default and the new path can be believed at weights where no prior answer
exists. If they disagree, the shipped table and every window read off it are the
finding, and this file is where that shows up.

D-139 walked one scene (`cafe_head_on_v0`, both arms) as the gating step, on the
reasoning that a generator should be priced on a cell whose answer predates the
change before it is trusted to write cells nobody can check. It reproduced
exactly, so this cycle walked **the remaining seven scenes** — the whole 8 x 2
matrix, 1024 closed-loop runs — and the agreement holds across every cell and
every recorded field (D-141).

Why the whole matrix rather than the window alone: `admissible` is the field a
consumer reads, but `min_spread`, `ladder`, `completes_anywhere` and
`calibratable` are the fields that say *why* a window is what it is. A
regeneration that reproduced the windows while moving the spreads would be a
different measurement wearing the same answer, so all five are compared.

This costs no sim time in CI: the walk is committed as the artifact above and
the tests read it, the same cost split `test_lam_calibration_table` uses.
"""

from __future__ import annotations

import os

import pytest

from eval.mppi_sandbox import lam_window_key as lwk

SHIPPED = "eval/scenarios/lam_windows.yaml"
REGENERATED = "eval/scenarios/variants/lam_windows_w10.yaml"

#: The weight the shipped table was generated at — `MPPIParams.w_obs_soft`'s
#: own default, which is what makes this a regeneration and not a new cell.
SHIPPED_WEIGHT = 10.0

#: Every field the table records per cell. `admissible` is what consumers read;
#: the other four are the evidence behind it, and a regeneration that moved them
#: would not be the same measurement even if the window matched.
CELL_FIELDS = ("admissible", "ladder", "min_spread", "completes_anywhere",
               "calibratable")


def _cells(path: str) -> dict[tuple[str, str], dict]:
    """`{(scene, controller): row}` read without going through `lookup` — the
    point here is to compare *stored rows*, and `lookup` deliberately refuses to
    return one off key (and returns nothing at all for an empty window).

    Rung sequences are normalised to tuples because that is what `lookup.usable`
    returns, and a comparison that fails on `[0.2, 0.4] != (0.2, 0.4)` is a test
    reporting the parser's container choice rather than the measurement.
    """
    rows, _weight = lwk._rows(path)
    return {
        (os.path.basename(c["scenario"]), c["controller"]): {
            **c,
            "admissible": tuple(float(x) for x in c["admissible"]),
            "ladder": tuple(float(x) for x in c["ladder"]),
        }
        for c in rows
    }


SHIPPED_CELLS = _cells(SHIPPED)
REGENERATED_CELLS = _cells(REGENERATED)

#: Parametrised rather than looped in a test body, so each cell is its own
#: reported failure and `loop_reach` has no population-claim loop to grade.
CELL_KEYS = sorted(SHIPPED_CELLS)


# --------------------------------------------------------------------------
# The regeneration reproduces the shipped answers.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("key", CELL_KEYS, ids=lambda k: f"{k[0]}-{k[1]}")
@pytest.mark.parametrize("field", CELL_FIELDS)
def test_regenerated_cell_matches_the_shipped_row(key, field):
    """The load-bearing assertion, one case per (cell, field).

    Set equality and not containment, for D-135's reason: a window that agreed
    only by widening would say nothing about whether the boundary moved."""
    assert key in REGENERATED_CELLS, f"{REGENERATED} has no {key} row"

    assert REGENERATED_CELLS[key][field] == SHIPPED_CELLS[key][field]


def test_the_regeneration_covers_the_whole_shipped_matrix():
    """Scope, stated as a set equality in both directions.

    D-139's artifact held one scene and this test named that limit; the limit is
    what this cycle removed. It is asserted rather than described because "the
    matrix" is the claim the `ON_KEY` tests below inherit — if a scene silently
    dropped out of the walk, those tests would still pass on the cells that
    remained."""
    assert set(REGENERATED_CELLS) == set(SHIPPED_CELLS)
    assert len({scene for scene, _arm in REGENERATED_CELLS}) == 8


@pytest.mark.parametrize("controller", ("stock_mppi", "risk_mppi"))
def test_head_on_is_still_the_recorded_three_rungs(controller):
    """One literal pin, kept from D-139, so a *joint* drift — both tables
    regenerated wrongly in the same direction — cannot pass the comparison
    above. head_on carries it because it is the cell D-135 re-measured
    independently at `w = 100`, so its behaviour under re-measurement is
    characterised rather than assumed."""
    assert REGENERATED_CELLS[("cafe_head_on_v0.yaml", controller)][
        "admissible"] == (0.2, 0.4, 0.8)


def test_no_temperature_serves_the_whole_matrix_either():
    """The aggregate the shipped table reports (`shared_window: []`) survives
    regeneration. This is Q-036's answer, and it is the one claim here that a
    per-cell comparison could not make: every cell could match while the
    intersection changed, if the matching were only approximate."""
    windows = [set(c["admissible"]) for c in REGENERATED_CELLS.values()]
    shared = set.intersection(*windows)

    assert shared == set()


# --------------------------------------------------------------------------
# It is keyed, which is the whole point of regenerating it.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("key", CELL_KEYS, ids=lambda k: f"{k[0]}-{k[1]}")
def test_every_calibratable_cell_now_returns_a_window(key):
    """Before D-139 every `lookup` in the repo graded `UNKEYED` (D-138); after
    it, one scene answered. Now the matrix does — this is the test that says the
    ~24 cell consumers have somewhere keyed to read from.

    The two `cafe_cut_in_v0` cells are the honest exception and are asserted as
    such: being keyed buys a *recorded* answer, not a usable one, and an arm
    that reaches the goal at no temperature has an empty window at every weight
    (Q-035). `EMPTY_WINDOW` with `usable is None` is the right refusal, and
    reading it as a lookup failure would be the Q-034 error."""
    scene, controller = key
    look = lwk.lookup(REGENERATED, scene, controller, SHIPPED_WEIGHT)

    if SHIPPED_CELLS[key]["calibratable"]:
        assert look.verdict == lwk.ON_KEY, str(look)
        assert look.usable == SHIPPED_CELLS[key]["admissible"]
    else:
        assert look.verdict == lwk.EMPTY_WINDOW, str(look)
        assert look.usable is None
    assert look.measured_at == SHIPPED_WEIGHT


@pytest.mark.parametrize("weight", [30.0, 100.0, 150.0])
def test_regenerated_table_still_refuses_every_other_weight(weight):
    """Being keyed buys one weight, not the ladder of weights the repo has read
    this table at. D-134's crossing/risk cell moved between `w = 10` and
    `w = 150`, so the refusal is load-bearing, not bookkeeping."""
    look = lwk.lookup(REGENERATED, "cafe_head_on_v0.yaml", "risk_mppi", weight)

    assert look.verdict == lwk.OFF_KEY, str(look)
    assert look.usable is None
    assert look.measured_at == SHIPPED_WEIGHT


def test_shipped_table_is_not_retro_keyed_by_this_cycle():
    """The regeneration now agrees with the shipped table on all 16 cells, and
    that still does not stamp a weight onto the shipped file.

    The temptation is stronger here than it was at one scene — the two tables
    are now field-for-field identical, so writing `calibration_weight: 10` into
    the shipped one looks like bookkeeping. It is not: that file's rows were
    produced by a code path that never recorded a weight, and a header edit
    would give ~24 cells a provenance nobody re-derived (D-107). The keyed
    matrix is the *variant*, and it earned the key by being re-run."""
    look = lwk.lookup(SHIPPED, "cafe_head_on_v0.yaml", "stock_mppi",
                      SHIPPED_WEIGHT)

    assert look.verdict == lwk.UNKEYED, str(look)
    assert look.usable is None


def test_scenes_outside_the_calibrated_glob_are_still_refused():
    """The walk covered `eval/scenarios/*.yaml`, not the variant scenes beside
    it. `cafe_obstacle_crossing_sync_v0.yaml` is a real scenario this repo can
    run and it has never been calibrated at any weight, so `NO_CELL` is the
    honest answer — and it keeps the refusal non-vacuous now that the eight
    calibrated scenes all answer."""
    absent = lwk.lookup(REGENERATED, "cafe_obstacle_crossing_sync_v0.yaml",
                        "risk_mppi", SHIPPED_WEIGHT)

    assert absent.verdict == lwk.NO_CELL, str(absent)
    assert absent.usable is None
