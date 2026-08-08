# SPDX-License-Identifier: BSD-3-Clause
"""Q-119: price the generator against an answer we already know.

D-138 shipped the write half of `calibration_weight:` and proved the round trip
synthetically — `to_yaml` writes a weight, `lookup` reads it back, on hand-built
cells that never touch the simulator. What that could not show is whether the
*measuring* half still produces the same windows once a weight is threaded
through it. `ab.lam_ladder` gained a `w_obs_soft` parameter to carry the weight
down to `MPPIParams`; a table generated through that new path is only
trustworthy if walking it at the weight the shipped table was already generated
at reproduces the shipped rows.

So this file checks a **regeneration**, not a fresh measurement. The shipped
`lam_windows.yaml` was generated at the controller default (`w_obs_soft = 10`)
and records `cafe_head_on_v0` as `[0.2, 0.4, 0.8]` on both arms. Re-walking that
one scene with an explicit `--w-obs-soft 10` must land on the same two rows. If
it does, the weight-threading is behaviour-preserving at the default and the new
`--w-obs-soft` path can be believed at weights where no prior answer exists. If
it does not, the shipped table and every window read off it are the finding, and
this test is where that shows up.

head_on is the scene to price against because it is the one D-135 re-measured
independently (at `w = 100`, `WINDOW_HELD` on both arms with set equality), so
its behaviour under re-measurement is characterised rather than assumed.

This costs no sim time in CI: the 128-run walk is committed as
`eval/scenarios/variants/lam_windows_w10.yaml` and the tests read the artifact,
the same cost split `test_lam_calibration_table` uses.
"""

from __future__ import annotations

import os

import pytest

from eval.mppi_sandbox import lam_window_key as lwk

SHIPPED = "eval/scenarios/lam_windows.yaml"
REGENERATED = "eval/scenarios/variants/lam_windows_w10.yaml"

SCENE = "cafe_head_on_v0.yaml"
ARMS = ("stock_mppi", "risk_mppi")

#: The weight the shipped table was generated at — `MPPIParams.w_obs_soft`'s
#: own default, which is what makes this a regeneration and not a new cell.
SHIPPED_WEIGHT = 10.0


def _admissible(path: str, controller: str) -> tuple[float, ...]:
    """The window a table records for `SCENE`/`controller`, read without going
    through `lookup` — the point here is to compare *stored rows*, and `lookup`
    deliberately refuses to return one off key."""
    cells, _weight = lwk._rows(path)
    for cell in cells:
        if (os.path.basename(cell["scenario"]) == SCENE
                and cell["controller"] == controller):
            return tuple(float(x) for x in cell["admissible"])
    raise AssertionError(f"{path} has no {SCENE}/{controller} row")


# --------------------------------------------------------------------------
# The regeneration reproduces the shipped answer.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("controller", ARMS)
def test_regenerated_window_matches_the_shipped_row(controller):
    """The load-bearing assertion. Same scene, same weight, same ladder, walked
    through the new `--w-obs-soft` path — the window must be unchanged.

    Set equality and not containment, for D-135's reason: a window that agreed
    only by widening would say nothing about whether the boundary moved."""
    assert _admissible(REGENERATED, controller) == _admissible(SHIPPED, controller)


@pytest.mark.parametrize("controller", ARMS)
def test_regenerated_window_is_the_recorded_three_rungs(controller):
    """Pin the actual value too, so a *joint* drift — both tables regenerated
    wrongly in the same direction — cannot pass the comparison above."""
    assert _admissible(REGENERATED, controller) == (0.2, 0.4, 0.8)


# --------------------------------------------------------------------------
# It is keyed, which is the whole point of regenerating it.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("controller", ARMS)
def test_regenerated_table_grades_on_key_at_the_shipped_weight(controller):
    """The first table in the repo that `lookup` can actually return a window
    from. Before this artifact every call graded `UNKEYED` (D-138)."""
    look = lwk.lookup(REGENERATED, SCENE, controller, SHIPPED_WEIGHT)

    assert look.verdict == lwk.ON_KEY, str(look)
    assert look.usable == (0.2, 0.4, 0.8)
    assert look.measured_at == SHIPPED_WEIGHT


@pytest.mark.parametrize("weight", [30.0, 100.0, 150.0])
def test_regenerated_table_still_refuses_every_other_weight(weight):
    """Being keyed buys one weight, not the ladder of weights the repo has read
    this table at. D-134's crossing/risk cell moved between `w = 10` and
    `w = 150`, so the refusal is load-bearing, not bookkeeping."""
    look = lwk.lookup(REGENERATED, SCENE, "risk_mppi", weight)

    assert look.verdict == lwk.OFF_KEY, str(look)
    assert look.usable is None
    assert look.measured_at == SHIPPED_WEIGHT


def test_shipped_table_is_not_retro_keyed_by_this_cycle():
    """The regeneration covers one scene. Stamping the other seven from it is
    exactly the unearned provenance D-107 refuses, so the shipped table must
    still grade `UNKEYED` — a keyed *variant* is not a keyed matrix."""
    look = lwk.lookup(SHIPPED, SCENE, "stock_mppi", SHIPPED_WEIGHT)

    assert look.verdict == lwk.UNKEYED, str(look)
    assert look.usable is None


def test_regenerated_table_covers_only_the_scene_it_walked():
    """Scope honesty: the file is one scene × two arms, and a reader must not
    mistake it for the matrix. `NO_CELL` is the right refusal for the rest."""
    cells, weight = lwk._rows(REGENERATED)

    assert weight == SHIPPED_WEIGHT
    assert {(os.path.basename(c["scenario"]), c["controller"]) for c in cells} == {
        (SCENE, arm) for arm in ARMS
    }

    absent = lwk.lookup(REGENERATED, "cafe_obstacle_crossing_v0.yaml",
                        "risk_mppi", SHIPPED_WEIGHT)
    assert absent.verdict == lwk.NO_CELL, str(absent)
    assert absent.usable is None
