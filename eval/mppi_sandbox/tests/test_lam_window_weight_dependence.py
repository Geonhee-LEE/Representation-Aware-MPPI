# SPDX-License-Identifier: BSD-3-Clause
"""Q-119 lean (b), first rung: does the λ window depend on the **weight**, at
matrix scale rather than at one hand-walked cell?

D-141 regenerated the whole matrix at `w = 10` and every cell reproduced, which
priced the generator but could not answer this — a table re-walked at the weight
it was already written at is a *control*, and its agreement says the code path
is behaviour-preserving, not that windows are weight-invariant. This file reads
the first table written at a weight the matrix had never been calibrated at:
`eval/scenarios/variants/lam_windows_w75.yaml`, 8 scenes x 2 controllers x 8
rungs x 8 seeds at `--w-obs-soft 75`.

`w = 75` is not an arbitrary next weight. It is the bottom rung of D-132's band
`{75, 100, 150}` — the only band the project has a significant mechanism claim
on — and that claim was walked at λ = 0.8, an admissibility read off the `w = 10`
table. So this table can retract a shipped number, and the first thing asserted
below is whether it does.

What the comparison can and cannot say
--------------------------------------

Every cell here is its **own** weight contrast with the scene held fixed by
construction, which is the design the three-cell `REMEASURED` registry could
never buy: `contrasts()` had to search for pairs that isolated an axis, and with
three hand-walked cells it found one. Two generated tables give sixteen.

The limit is the seed count. This table is 8 seeds (matching `w = 10`, so the
contrast is apples-to-apples) where the registry's cells are 16, and
`admissible` is an all-seeds conjunction — a boundary rung that survives 8 seeds
may not survive 16. So a `WINDOW_HELD` here is the weaker claim and a move is
the stronger one, and the counts below should be read as a lower bound on the
movement rather than as a measurement of it.
"""

from __future__ import annotations

import os

import pytest

from eval.mppi_sandbox import lam_window_key as lwk

REFERENCE = "eval/scenarios/variants/lam_windows_w10.yaml"
REMEASURED_TABLE = "eval/scenarios/variants/lam_windows_w75.yaml"

REFERENCE_WEIGHT = 10.0
REMEASURED_WEIGHT = 75.0

#: The columns both tables were walked at. `w = 10` gained a third
#: (`gap_gated_mppi`, D-146) that `w = 75` does not have, so the weight
#: contrast is stated over the two columns that exist at both weights and the
#: third is named below rather than silently intersected away.
COMPARED_ARMS = ("stock_mppi", "risk_mppi")

CENSUS = lwk.table_shift_census(REFERENCE, REMEASURED_TABLE, COMPARED_ARMS)


def _cells(path: str) -> dict[tuple[str, str], dict]:
    rows, _weight = lwk._rows(path)
    return {
        (os.path.basename(c["scenario"]), c["controller"]): {
            **c, "admissible": tuple(float(x) for x in c["admissible"])}
        for c in rows
    }


W75_CELLS = _cells(REMEASURED_TABLE)
W10_CELLS = _cells(REFERENCE)


# --------------------------------------------------------------------------
# The headline: the weight axis moves windows, and by how much.
# --------------------------------------------------------------------------

def test_the_window_is_not_weight_invariant_at_matrix_scale():
    """The claim this cycle bought, pinned as a census and not as a rate.

    D-136 answered the scene-vs-weight question with `FACTOR_INERT` on the
    weight axis, on the evidence available then: `cafe_head_on_v0` re-measured
    to its recorded window at both `w = 100` and `w = 150`. That reading was
    correct about head_on and is now bounded — across the matrix, six of the
    fourteen arm-cells that *had* a window at `w = 10` do not have the same one
    at `w = 75`.

    Pinned as named members rather than "6 of 14" for `shift_census`'s reason: a
    rate whose numerator cannot be enumerated is the shape `published_ratios`
    refuses."""
    moved = set(CENSUS.get(lwk.WINDOW_SHIFTED, ())) \
        | set(CENSUS.get(lwk.WINDOW_DISJOINT, ())) \
        | set(CENSUS.get(lwk.WINDOW_CLOSED, ()))

    assert moved == {
        "cafe_convoy_v0.yaml:risk_mppi",
        "cafe_convoy_v0.yaml:stock_mppi",
        "cafe_freezing_v0.yaml:risk_mppi",
        "cafe_head_on_v0.yaml:risk_mppi",
        "cafe_obstacle_crossing_v0.yaml:risk_mppi",
        "cafe_obstacle_crossing_v0.yaml:stock_mppi",
    }


def test_the_denominator_excludes_the_cells_that_never_had_a_window():
    """`cafe_cut_in_v0` is empty at both weights, and counting it as a closure
    would be counting a cell that has no operating point at any temperature
    (Q-035) as evidence that the weight closed one.

    This is why `table_shift_census` grades `NEVER_OPEN` apart: `window_shift`
    returns `WINDOW_CLOSED` for any empty new window and cannot distinguish the
    two, so the distinction has to be made by the caller that knows the
    reference."""
    assert set(CENSUS[lwk.NEVER_OPEN]) == {
        "cafe_cut_in_v0.yaml:risk_mppi", "cafe_cut_in_v0.yaml:stock_mppi"}

    graded = sum(len(v) for k, v in CENSUS.items() if k != lwk.NEVER_OPEN)
    assert graded == 14
    assert len(CENSUS[lwk.WINDOW_HELD]) == 8


def test_one_cell_lost_its_window_entirely():
    """The strongest single movement, and the one that is not a boundary-rung
    artifact: `cafe_obstacle_crossing_v0`'s risk arm records `[1.6, 3.2]` at
    `w = 10` and is admissible at **no** rung of the same ladder at `w = 75`.

    D-134 already showed this arm moving to `{0.8}` at `w = 150` from a
    16-seed hand walk. That it also closes at `w = 75` says the `w = 10` row is
    not a window that drifts with weight but one that describes `w = 10`."""
    assert CENSUS[lwk.WINDOW_CLOSED] == (
        "cafe_obstacle_crossing_v0.yaml:risk_mppi",)
    assert W10_CELLS[("cafe_obstacle_crossing_v0.yaml", "risk_mppi")][
        "admissible"] == (1.6, 3.2)
    assert W75_CELLS[("cafe_obstacle_crossing_v0.yaml", "risk_mppi")][
        "admissible"] == ()


# --------------------------------------------------------------------------
# What it means for the one claim the project has staked.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("controller", ("stock_mppi", "risk_mppi"))
def test_d132s_operating_point_survives_at_the_bottom_of_its_band(controller):
    """The retraction test, and it comes back clean.

    D-131/D-132's band is `{75, 100, 150}` and both arms were walked there at
    λ = 0.8 — a temperature whose admissibility came from the `w = 10` table.
    `w = 75` is the rung of that band this cycle re-keyed, and **0.8 is
    admissible on both arms of `cafe_head_on_v0` at it**, so the claim keeps its
    operating point at the bottom of its own band.

    The risk arm grades `WINDOW_SHIFTED` rather than `HELD` — it loses λ = 0.2 —
    which is the honest state of it: the window moved, and it did not move
    through the rung the claim stands on. `w = 100` and `w = 150` remain to be
    re-keyed the same way."""
    window = W75_CELLS[("cafe_head_on_v0.yaml", controller)]["admissible"]

    assert 0.8 in window, f"D-132 walked λ=0.8 at w=75; window here is {window}"


def test_head_on_risk_is_the_arm_that_moved_and_stock_is_not():
    """Which of head_on's arms moved, stated so that a future re-key of `w = 100`
    or `w = 150` has something specific to agree or disagree with.

    D-135 re-measured **both** head_on arms at `w = 100` at 16 seeds and got
    `WINDOW_HELD` on both. Here the stock arm holds and the risk arm drops its
    lowest rung, so either the movement is specific to `w = 75` or the lost rung
    is a boundary case the two seed counts read differently — this file cannot
    separate those, and says so rather than picking one."""
    assert "cafe_head_on_v0.yaml:stock_mppi" in CENSUS[lwk.WINDOW_HELD]
    assert "cafe_head_on_v0.yaml:risk_mppi" in CENSUS[lwk.WINDOW_SHIFTED]

    assert W75_CELLS[("cafe_head_on_v0.yaml", "risk_mppi")][
        "admissible"] == (0.4, 0.8)
    assert W10_CELLS[("cafe_head_on_v0.yaml", "risk_mppi")][
        "admissible"] == (0.2, 0.4, 0.8)


# --------------------------------------------------------------------------
# The table is keyed, and the key is load-bearing.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("key", sorted(W75_CELLS), ids=lambda k: f"{k[0]}-{k[1]}")
def test_every_cell_answers_on_key_at_75(key):
    """The point of writing the file at all: 14 cells now answer at a *second*
    weight, so a consumer running at `w = 75` has somewhere keyed to read from
    instead of reading the `w = 10` table off key."""
    scene, controller = key
    look = lwk.lookup(REMEASURED_TABLE, scene, controller, REMEASURED_WEIGHT)

    if W75_CELLS[key]["calibratable"]:
        assert look.verdict == lwk.ON_KEY, str(look)
        assert look.usable == W75_CELLS[key]["admissible"]
    else:
        assert look.verdict == lwk.EMPTY_WINDOW, str(look)
        assert look.usable is None
    assert look.measured_at == REMEASURED_WEIGHT


@pytest.mark.parametrize("weight", [10.0, 100.0, 150.0])
def test_the_w75_table_refuses_the_other_rungs_of_the_band(weight):
    """Being keyed at 75 buys 75. The other two rungs of D-132's band are
    exactly the weights a reader is most likely to reach for this file at, and
    the census above is the witness that the refusal costs something."""
    look = lwk.lookup(REMEASURED_TABLE, "cafe_head_on_v0.yaml", "risk_mppi",
                      weight)

    assert look.verdict == lwk.OFF_KEY, str(look)
    assert look.usable is None
    assert look.measured_at == REMEASURED_WEIGHT


def test_the_two_tables_are_keyed_apart():
    """A census between two tables at the same weight would grade `WINDOW_HELD`
    everywhere and witness nothing, so `table_shift_census` refuses it. Pinned
    because this file's entire result is a difference between the two keys."""
    _rows_ref, ref_w = lwk._rows(REFERENCE)
    _rows_new, new_w = lwk._rows(REMEASURED_TABLE)

    assert (ref_w, new_w) == (REFERENCE_WEIGHT, REMEASURED_WEIGHT)

    with pytest.raises(ValueError, match="keyed at"):
        lwk.table_shift_census(REFERENCE, REFERENCE)


def test_no_temperature_serves_the_whole_matrix_at_75_either():
    """Q-036's answer survives the new weight: the shared window is empty at
    `w = 75` as it is at `w = 10`, so 'calibrate once, run everywhere' is not
    rescued by picking a different barrier weight."""
    windows = [set(c["admissible"]) for c in W75_CELLS.values()]

    assert set.intersection(*windows) == set()


def test_the_column_this_census_does_not_cover_is_named_not_dropped():
    """`gap_gated_mppi` was calibrated at `w = 10` only (D-146), so it has no
    weight contrast and cannot appear in the census above. Asserting that
    asymmetry here keeps `COMPARED_ARMS` honest: if a later cycle walks the
    column at `w = 75`, this test fails and forces the census to widen rather
    than letting the scope silently stay at two columns."""
    ref, new = _cells(REFERENCE), _cells(REMEASURED_TABLE)
    ref_arms = {arm for _s, arm in ref}
    new_arms = {arm for _s, arm in new}
    assert ref_arms - new_arms == {"gap_gated_mppi"}
    assert set(COMPARED_ARMS) == new_arms
    assert all(arm in ref_arms for arm in COMPARED_ARMS)


def test_the_census_scope_cannot_invent_a_column():
    """`arms` selects columns, it does not create them — a typo that shrank the
    denominator silently would be the contaminated-population shape D-142 had
    to split `NEVER_OPEN` out of."""
    with pytest.raises(ValueError, match="no column for"):
        lwk.table_shift_census(REFERENCE, REMEASURED_TABLE,
                               ("stock_mppi", "typo_mppi"))
