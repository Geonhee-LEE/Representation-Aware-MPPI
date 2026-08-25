# SPDX-License-Identifier: BSD-3-Clause
"""`arm_freeze` — Q-148's four arms as a frozen `(w_epist, w_voo)` table.

The tests that matter here are the ones that keep the table honest rather than
merely arithmetic: the ratio is *pinned to `ratio_pick`* instead of retyped, the
stated cost of the L1 control is asserted to be present, and the unposed
geometry is asserted to propagate as a refusal rather than a fallback.
"""

from __future__ import annotations

import dataclasses

import pytest

from eval.mppi_sandbox import ratio_pick
from eval.mppi_sandbox.arm_freeze import (
    ARM_NAMES,
    ARM_SCALE,
    ATTRACT_ONLY,
    BOTH_ON,
    CONTROL,
    REPEL_ONLY,
    Arm,
    adjudication,
    allocation_is_controlled,
    arm,
    both_on_ratio,
    freeze,
    is_pure_addition_to,
    sign_reading,
    unmeasured_parameters,
)
from eval.mppi_sandbox.both_on_cell import INDETERMINATE
from eval.mppi_sandbox.critics.observation_value import ObservationValueCritic
from eval.mppi_sandbox.critics.shadow_cost import ShadowCostCritic

#: A radius `both_on_cell` cannot place a cell at (D-260: `UNPLACEABLE`).
UNPOSED_RADIUS = 1.25


@pytest.fixture
def arms():
    a = freeze()
    assert a is not None, "the scene radius must be posed"
    return a


def test_table_has_the_four_named_arms_in_reporting_order(arms):
    assert tuple(a.name for a in arms) == ARM_NAMES
    assert len(ARM_NAMES) == 4


def test_control_arm_sets_both_weights_to_zero(arms):
    control = next(a for a in arms if a.name == CONTROL)
    assert (control.w_epist, control.w_voo) == (0.0, 0.0)
    assert not control.is_active
    assert control.channels_on == 0


def test_single_arms_each_light_exactly_one_channel(arms):
    repel = next(a for a in arms if a.name == REPEL_ONLY)
    attract = next(a for a in arms if a.name == ATTRACT_ONLY)
    assert (repel.w_epist, repel.w_voo) == (ARM_SCALE, 0.0)
    assert (attract.w_epist, attract.w_voo) == (0.0, ARM_SCALE)
    assert repel.channels_on == attract.channels_on == 1


def test_both_on_lights_two_channels(arms):
    assert next(a for a in arms if a.name == BOTH_ON).channels_on == 2


def test_both_on_ratio_is_ratio_picks_number_not_a_retyped_constant(arms):
    """D-047: two names for one number are pinned, never independently typed."""
    chosen = ratio_pick.pick()
    assert chosen is not None
    assert both_on_ratio(arms) == pytest.approx(chosen.ratio, rel=1e-12)


def test_every_active_arm_spends_the_same_authority(arms):
    assert allocation_is_controlled(arms)
    spends = {a.authority for a in arms if a.is_active}
    assert len(spends) == 1 and spends.pop() == pytest.approx(ARM_SCALE)


def test_the_control_is_the_stated_cost_no_contrast_is_pure_addition(arms):
    """Under L1 control `BOTH_ON` is a reallocation of both single arms, never
    a superset of either. The docstring says so; this is the assertion."""
    mixed = next(a for a in arms if a.name == BOTH_ON)
    for single in (a for a in arms if a.name in (REPEL_ONLY, ATTRACT_ONLY)):
        assert not is_pure_addition_to(mixed, single)
    # ...and the predicate is not vacuously False: it fires on a genuine superset.
    assert is_pure_addition_to(Arm("x", 2.0, 2.0), Arm(REPEL_ONLY, 1.0, 0.0))


def test_both_on_is_strictly_weaker_than_each_single_arm_in_that_arms_channel(arms):
    mixed = next(a for a in arms if a.name == BOTH_ON)
    assert mixed.w_epist < ARM_SCALE
    assert mixed.w_voo < ARM_SCALE


def test_scale_is_linear_and_leaves_the_ratio_alone(arms):
    scaled = freeze(scale=17.0)
    assert scaled is not None
    assert allocation_is_controlled(scaled)
    assert both_on_ratio(scaled) == pytest.approx(both_on_ratio(arms), rel=1e-12)
    for base, big in zip(arms, scaled):
        assert big.w_epist == pytest.approx(17.0 * base.w_epist)
        assert big.w_voo == pytest.approx(17.0 * base.w_voo)


def test_unposed_geometry_refuses_rather_than_falling_back(arms):
    """D-261 measurement 2: the bands share no point, so another radius's ratio
    is not a substitute. The table must go `None`, not quietly reuse `arms`."""
    assert ratio_pick.pick(UNPOSED_RADIUS) is None
    assert freeze(radius=UNPOSED_RADIUS) is None
    assert arm(BOTH_ON, radius=UNPOSED_RADIUS) is None


def test_arm_lookup_agrees_with_the_table(arms):
    for a in arms:
        assert arm(a.name) == a


def test_as_config_keys_are_the_critics_real_weight_fields(arms):
    """Guards the table against a critic rename: the frozen keys must be knobs
    that exist, or the config sets nothing and every arm silently becomes CONTROL."""
    shadow = {f.name for f in dataclasses.fields(ShadowCostCritic)}
    voo = {f.name for f in dataclasses.fields(ObservationValueCritic)}
    for a in arms:
        assert set(a.as_config()) == {"w_epist", "w_voo"}
        assert "w_epist" in shadow and "w_voo" in voo
    # The defaults are off, so an arm is the only thing that turns a channel on.
    assert ShadowCostCritic().w_epist == 0.0
    assert ObservationValueCritic().w_voo == 0.0


def test_sign_is_carried_as_indeterminate_and_not_as_a_balance_claim():
    reading = sign_reading()
    assert reading["sign"] == INDETERMINATE
    assert reading["is_pointwise_contest"] is False
    assert reading["invalidates_ab"] is False
    assert reading["repel_live_set_equals_exposed_partition"] is True
    assert reading["ref"] == "D-262"


def test_adjudication_names_the_closed_loop_metrics_and_bans_d_reached():
    adj = adjudication()
    assert adj["verdict_metrics"] == ("near_miss", "clearance")
    assert "d_reached" in adj["forbidden_metrics"]
    assert set(adj["verdict_metrics"]) & set(adj["forbidden_metrics"]) == set()
    # The verdict must not need the cost-field sign the table is INDETERMINATE on.
    assert adj["cost_field_sign_required"] is False


def test_the_unmeasured_knobs_are_declared_and_the_ratio_is_not_among_them():
    knobs = unmeasured_parameters()
    assert set(knobs) == {"arm_scale", "normalisation"}
    assert all(k["measured"] is False for k in knobs.values())
    assert knobs["arm_scale"]["value"] == ARM_SCALE
    # The ratio is the one measured number here — claiming it unmeasured would
    # undo D-261.
    assert "ratio" not in knobs
