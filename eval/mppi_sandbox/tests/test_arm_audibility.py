# SPDX-License-Identifier: BSD-3-Clause
"""Q-148 / D-263 — is the frozen arms' epistemic channel audible at `ARM_SCALE`?

Most of these run no sim: the verdict algebra and the inversion are properties
of `ChannelAudibility`, and pinning them at the dataclass costs nothing. The two
sim-backed tests are the ones that would silently rot if `_cost` changed — the
attract channel's `FAINT` and the repel channel's `SILENT`.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import arm_audibility as aa
from eval.mppi_sandbox.arm_freeze import (ARM_SCALE, ATTRACT_ONLY, BOTH_ON,
                                          REPEL_ONLY, arm, freeze)
from eval.mppi_sandbox.run import load_scenario


def _chan(ratio: float, weight: float = 1.0, threshold: float = aa.AUDIBLE_RATIO):
    return aa.ChannelAudibility(
        channel="w_voo", weight=weight, ratio=ratio,
        spread_per_unit_weight=ratio * 10.0, threshold=threshold,
        verdict=aa._verdict(ratio, threshold),
    )


# ---------------------------------------------------------------- verdicts

@pytest.mark.parametrize("ratio,expected", [
    (0.0, aa.SILENT),
    (1e-9, aa.FAINT),
    (0.0184, aa.FAINT),          # the measured attract reading
    (0.0999, aa.FAINT),
    (0.1, aa.AUDIBLE),           # the bar is inclusive
    (2.0, aa.AUDIBLE),
])
def test_verdict_partitions_the_ratio(ratio, expected):
    assert _chan(ratio).verdict == expected


def test_silent_gets_no_required_weight():
    """A zero exchange rate is not a large weight — it is no weight (D-241)."""
    c = _chan(0.0)
    assert c.verdict == aa.SILENT
    assert c.required_weight is None
    assert c.is_rescalable is False
    assert aa.required_arm_scale(c, arm(REPEL_ONLY)) is None


def test_faint_is_rescalable_and_the_inversion_is_exact():
    """`required_weight` is the linear inversion, not an estimate."""
    c = _chan(0.02, weight=1.0)
    assert c.is_rescalable
    # ratio is linear in the weight, so ratio(w) = w * (ratio/weight);
    # clearing `threshold` needs w * threshold / ratio.
    assert c.required_weight == pytest.approx(1.0 * 0.1 / 0.02)
    assert c.required_weight == pytest.approx(5.0)
    # and re-grading at that scale clears the bar exactly
    rescaled = _chan(0.02 * c.required_weight, weight=c.required_weight)
    assert rescaled.verdict == aa.AUDIBLE


def test_already_audible_needs_no_scale_up():
    c = _chan(0.5)
    assert c.required_weight < c.weight


def test_required_weight_is_not_an_arm_scale_on_the_mixed_cell():
    """D-047: the two coincide on a single-channel arm and diverge on BOTH_ON."""
    c = _chan(0.02, weight=0.7082)
    single, mixed = arm(ATTRACT_ONLY), arm(BOTH_ON)
    # ATTRACT_ONLY spends all its authority on w_voo, so weight == scale.
    assert aa.required_arm_scale(c, single) == pytest.approx(c.required_weight)
    # BOTH_ON holds only a share of it, so the scale is strictly larger.
    assert aa.required_arm_scale(c, mixed) > c.required_weight


def test_threshold_is_reported_not_hidden():
    """The bar is a declared convention, so it travels with the verdict (D-024)."""
    strict = _chan(0.05, threshold=0.5)
    lax = _chan(0.05, threshold=0.01)
    assert strict.verdict == aa.FAINT and strict.threshold == 0.5
    assert lax.verdict == aa.AUDIBLE and lax.threshold == 0.01


# ------------------------------------------------------------ arm roll-ups

def test_arm_is_audible_is_any_not_all():
    graded = {"w_epist": _chan(0.0), "w_voo": _chan(0.5)}
    assert aa.arm_is_audible(graded) is True


def test_arm_with_only_faint_channels_is_not_audible():
    assert aa.arm_is_audible({"w_voo": _chan(0.01)}) is False


def test_ab_vacuous_iff_no_active_arm_is_heard():
    quiet = {"REPEL_ONLY": {"w_epist": _chan(0.0)},
             "BOTH_ON": {"w_voo": _chan(0.001)}}
    assert aa.ab_is_vacuous(quiet) is True
    loud = dict(quiet, ATTRACT_ONLY={"w_voo": _chan(0.4)})
    assert aa.ab_is_vacuous(loud) is False


def test_ab_vacuous_is_false_on_an_empty_grading():
    """No arms graded is not evidence of vacuity — it is no evidence (D-241)."""
    assert aa.ab_is_vacuous({}) is False
    assert aa.ab_is_vacuous({"REPEL_ONLY": {}}) is False


# ------------------------------------------------------------ scene caveat

def test_scene_caveat_declares_the_ab_scene_absent():
    cav = aa.scene_caveat()
    assert cav["ab_scene"] == aa.AB_SCENE
    assert cav["ab_scene_available_here"] is False
    assert cav["recheck_on_merge"] is True


def test_ab_scene_is_quoted_never_imported():
    """The feasibility boundary: PR #68's yaml is cited, not depended on."""
    import ast
    import pathlib
    src = pathlib.Path(aa.__file__).read_text()
    tree = ast.parse(src)
    imported = [
        n.module for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.module
    ] + [
        a.name for n in ast.walk(tree)
        if isinstance(n, ast.Import) for a in n.names
    ]
    assert not any("blind_corner" in m or "occlusion" in m for m in imported)
    assert aa.AB_SCENE in src          # quoted, and the quote is the point


# ------------------------------------------------------------- sim-backed

@pytest.fixture(scope="module")
def crossing():
    return load_scenario("eval/scenarios/cafe_obstacle_crossing_v0.yaml")


def test_attract_channel_is_faint_at_arm_scale_one(crossing):
    """`w_voo` is live but ~2% of the rest of the cost — rescalable, not silent."""
    graded = aa.grade(crossing, arm(BOTH_ON))
    voo = graded["w_voo"]
    assert voo.verdict == aa.FAINT
    assert 0.001 < voo.ratio < aa.AUDIBLE_RATIO
    assert voo.is_rescalable
    assert voo.required_weight > voo.weight    # must be turned *up*
    assert aa.required_arm_scale(voo, arm(BOTH_ON)) > ARM_SCALE


def test_repel_channel_is_silent_without_an_occluder(crossing):
    """The shadow critic prices a shadow; this scene casts none (D-021)."""
    graded = aa.grade(crossing, arm(REPEL_ONLY))
    epist = graded["w_epist"]
    assert epist.verdict == aa.SILENT
    assert epist.ratio == 0.0
    assert epist.required_weight is None


def test_control_arm_grades_no_channels(crossing):
    """Both weights are 0, so there is nothing to measure — not a zero verdict."""
    control = freeze()[0]
    assert not control.is_active
    assert aa.grade(crossing, control) == {}
