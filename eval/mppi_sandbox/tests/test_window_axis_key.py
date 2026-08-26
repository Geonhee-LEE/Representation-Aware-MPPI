# SPDX-License-Identifier: BSD-3-Clause
"""Q-154: the window's ceiling is off-axis, and keying the table does not fix it.

The standing TODO behind Q-154 was "emit `calibration_weight:` so the lookup
grades `ON_KEY` instead of `UNKEYED`". These tests pin the reason that would
have been the wrong move for the cell the bottleneck reads: the clearance it
buys is on `w_obs_soft`, and this branch's ladder moves `w_voo`.

The two load-bearing ones are `test_keying_the_table_would_clear_the_wrong_axis`
(the false clearance, demonstrated rather than asserted) and
`test_on_axis_is_reachable` (without which this guard would be `guard_vacuity`'s
complaint — a check that refuses everything witnesses nothing).
"""

from __future__ import annotations

import textwrap

import pytest

from eval.mppi_sandbox import lam_window_key as lwk
from eval.mppi_sandbox import window_axis_key as wak
from eval.mppi_sandbox.calibrated_ladder import WINDOW_KEY

SHIPPED = lwk.TABLE
KEYED = wak.KEYED_TABLE


def test_the_calibration_walk_varies_exactly_one_cost_axis():
    """The axis set is read off `ab.lam_ladder`, so this is a pin on the walk
    and not on a constant. If someone threads a second cost weight down to
    `MPPIParams` the way D-138 threaded `w_obs_soft`, this goes red — which is
    the intended way for `OFF_AXIS` cells to stop being off-axis."""
    assert wak.calibrated_axes() == ("w_obs_soft",)


def test_w_voo_is_not_a_calibrated_axis():
    """The specific gap, named. `calibrate_lam` has zero `w_voo` references, so
    every window in every shipped table was measured with the attract channel
    off."""
    assert "w_voo" not in wak.calibrated_axes()


def test_the_ladder_runs_off_axis():
    look = wak.lookup(KEYED, WINDOW_KEY[0], WINDOW_KEY[1], wak.LADDER_FIELD)

    assert look.verdict == wak.OFF_AXIS, str(look)
    assert look.off_axis == ("w_voo",)
    assert look.usable is None


def test_keying_the_table_would_clear_the_wrong_axis():
    """The whole finding, as a contrast rather than a claim.

    Against the keyed regeneration the `lam_window_key` half grades `ON_KEY`
    and hands back a usable window — the exact improvement Q-154's prerequisite
    TODO was going to buy. The axis half still refuses. So the prerequisite
    would have converted an honest `UNKEYED` refusal into a false clearance,
    and the composed lookup is what keeps it a refusal."""
    scalar = lwk.lookup(KEYED, WINDOW_KEY[0], WINDOW_KEY[1],
                        wak.LADDER_FIELD["w_obs_soft"])

    assert scalar.verdict == lwk.ON_KEY, str(scalar)
    assert scalar.usable is not None          # the false clearance, witnessed

    composed = wak.q154(KEYED)
    assert composed.key.verdict == lwk.ON_KEY  # same half, same answer
    assert composed.verdict == wak.OFF_AXIS
    assert composed.usable is None


def test_the_unkeyed_table_refuses_for_a_second_reason(tmp_path):
    """Both halves refuse, under different names. The two are not redundant:
    `UNKEYED` is clearable by a re-run and `OFF_AXIS` is not, so collapsing them
    would lose which repair is owed.

    **The witness moved into a fixture (D-477)**, the fourth time this install
    forced that move and for the same reason each time. This read against
    `SHIPPED`, which was the repo's only live unkeyed table; D-477 keyed it, so
    the composed lookup now grades `ON_KEY / OFF_AXIS` and the two-reason case
    lost its input. Keying the real file did not weaken the second reason — it
    removed every witness that the *pair* is still producible, which is the
    state D-317 warns reads identically to a refusal someone deleted.

    So the table is built here instead, unkeyed by construction, and the
    property is restated unchanged. `test_the_ladder_runs_off_axis` above still
    carries the `OFF_AXIS` half against the real shipped tree, so this fixture
    is not the only thing standing between the axis guard and vacuity.
    """
    path = tmp_path / "lam_windows.yaml"
    path.write_text(textwrap.dedent(f"""
        cells:
          - scenario: {WINDOW_KEY[0]}
            controller: {WINDOW_KEY[1]}
            admissible: [0.2, 0.4, 0.8]
        """))  # note: no `calibration_weight:` line — that is the point

    look = wak.lookup(str(path), WINDOW_KEY[0], WINDOW_KEY[1], wak.LADDER_FIELD)

    assert look.key.verdict == lwk.UNKEYED, str(look)
    assert look.verdict == wak.OFF_AXIS
    assert look.usable is None


def test_the_shipped_table_is_keyed_now_and_still_refuses_on_the_axis():
    """The other side of the fixture move, kept against the real file.

    D-477's install cleared the `UNKEYED` half for the shipped tree and cleared
    *only* that half: the ladder still moves `w_voo`, which no calibration walk
    varied, so the composed lookup hands back no window. This is the assertion
    that would notice if a future install were mistaken for a fix to Q-154.
    """
    look = wak.lookup(SHIPPED, WINDOW_KEY[0], WINDOW_KEY[1], wak.LADDER_FIELD)

    assert look.key.verdict == lwk.ON_KEY, str(look)
    assert look.verdict == wak.OFF_AXIS
    assert look.usable is None


def test_on_axis_is_reachable():
    """Non-vacuity. A caller running the cost field the walk measured — attract
    channel off, barrier weight at the key — gets the window, so `OFF_AXIS` is
    a discriminating verdict and not a guard that refuses everything."""
    look = wak.lookup(KEYED, WINDOW_KEY[0], WINDOW_KEY[1],
                      {"w_obs_soft": 10.0, "w_voo": 0.0})

    assert look.verdict == wak.ON_AXIS, str(look)
    assert look.usable == look.key.usable
    assert look.usable  # the freezing cell has a non-empty window


def test_an_off_axis_channel_at_its_default_is_not_off_axis():
    """`w_voo = 0` is the value the calibration ran at, so naming it changes
    nothing. The guard keys on the *value*, not on the mention — otherwise a
    caller could trip it by being explicit about a term it left off."""
    named = wak.lookup(KEYED, WINDOW_KEY[0], WINDOW_KEY[1],
                       {"w_obs_soft": 10.0, "w_voo": 0.0})
    silent = wak.lookup(KEYED, WINDOW_KEY[0], WINDOW_KEY[1],
                        {"w_obs_soft": 10.0})

    assert named.verdict == silent.verdict == wak.ON_AXIS
    assert named.off_axis == silent.off_axis == ()


@pytest.mark.parametrize("w_voo", [5.0, 20.0, 50.0, 200.0])
def test_every_walked_rung_of_the_ladder_is_off_axis(w_voo):
    """Not just the operating point. D-266/D-268's ladder walked these four
    rungs above zero, so no rung of it was inside the calibration's cost
    field — the refusal is about the ladder, not about one cell of it."""
    look = wak.lookup(KEYED, WINDOW_KEY[0], WINDOW_KEY[1],
                      {"w_obs_soft": 10.0, "w_voo": w_voo})

    assert look.verdict == wak.OFF_AXIS, str(look)


def test_off_axis_survives_a_barrier_weight_that_is_also_wrong():
    """`OFF_AXIS` outranks `OFF_KEY`. Both refuse, but only one of them is
    repairable by the re-run Q-154's prerequisite proposed, and the verdict a
    caller reads should name the repair that is actually owed."""
    look = wak.lookup(KEYED, WINDOW_KEY[0], WINDOW_KEY[1],
                      {"w_obs_soft": 150.0, "w_voo": 5.0})

    assert look.key.verdict == lwk.OFF_KEY, str(look)
    assert look.verdict == wak.OFF_AXIS
    assert look.usable is None


def test_axis_default_reads_the_controller_not_a_constant():
    """`w_obs_soft`'s default is derived from `MPPIParams`, matching
    `calibrate_lam.default_weight` — one statement of the default (D-047)."""
    from eval.mppi_sandbox.calibrate_lam import default_weight

    assert wak.axis_default("w_obs_soft") == default_weight()
    assert wak.axis_default("w_voo") == 0.0


def test_q154_defaults_to_the_table_that_helps_most():
    """The answer is taken against the keyed regeneration, not the unkeyed
    shipped file — an off-axis refusal read off the weaker table would be
    indistinguishable from a missing-key one."""
    assert wak.q154().key.verdict == lwk.ON_KEY
    assert wak.q154().verdict == wak.OFF_AXIS
