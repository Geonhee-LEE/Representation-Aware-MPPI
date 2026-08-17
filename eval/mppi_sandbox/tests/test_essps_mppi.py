# SPDX-License-Identifier: BSD-3-Clause
"""Contract for the per-iteration ESSPS arm (Q-156 (c) / D-325).

No closed-loop runs here — `essps.PER_ITERATION_ARMS` is a recorded
measurement, following `ess_at_peak.MEASURED_ESS`'s precedent. What the suite
holds is the *wiring* (one weighting path, registry membership, the solve
actually reaching its target) and the *shape of the claim* (compliance and
time-to-goal never collapse into one flag).
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import essps
from eval.mppi_sandbox.ab import ess_band
from eval.mppi_sandbox.controllers import REGISTRY, make_controller
from eval.mppi_sandbox.controllers.essps_mppi import ESSPSMPPI
from eval.mppi_sandbox.controllers.risk_mppi import RiskMPPI
from eval.mppi_sandbox.ess_at_peak import PEAK_SCENE
from eval.mppi_sandbox.run import load_scenario


@pytest.fixture(scope="module")
def peak_scene():
    return load_scenario(f"eval/scenarios/{PEAK_SCENE}.yaml")


def test_registered_and_constructible(peak_scene):
    assert REGISTRY["essps_mppi"] is ESSPSMPPI
    ctrl = make_controller("essps_mppi", peak_scene, seed=0)
    assert isinstance(ctrl, RiskMPPI), "the fork must inherit the risk arm"


def test_only_the_temperature_differs():
    """The fork overrides `_softmax_lam` and nothing else.

    If a future edit overrides `command` or `_extra_cost` here, the two arms
    stop being a controlled comparison and every number in
    `PER_ITERATION_ARMS` silently becomes a two-variable difference.
    """
    overridden = {n for n, v in vars(ESSPSMPPI).items()
                  if callable(v) and not n.startswith("__")}
    assert overridden == {"_softmax_lam"}


def test_stock_hook_is_the_constant():
    """`StockMPPI._softmax_lam` must stay a pass-through of `p.lam`.

    The hook exists so there is exactly one `exp(-(cost-min)/lam)` in the tree
    (D-047). A default that computed anything would make the base arm's
    recorded numbers describe a controller nobody measured.
    """
    from eval.mppi_sandbox.controllers.stock_mppi import StockMPPI

    class _Fake:
        p = type("P", (), {"lam": 0.8})()

    assert StockMPPI._softmax_lam(_Fake(), np.zeros(4)) == pytest.approx(0.8)


def test_solved_lam_hits_the_target_ess():
    """The override's contract: the softmax it returns has ESS == target."""
    rng = np.random.default_rng(0)
    cost = rng.normal(10.0, 3.0, size=256)
    target = essps.TARGET_FRACTION * cost.size
    lam = essps.solve_lam_for_ess(cost, target)
    assert lam is not None
    assert essps.ess_of(cost, lam) == pytest.approx(target, rel=1e-6)


def test_target_sits_inside_the_band():
    """A solve that lands outside the band would make compliance unreachable.

    This is *why* `holds_band` is structural rather than lucky, and it is
    pinned so a change to `TARGET_FRACTION` or `ESS_BAND_FRACTIONS` cannot
    quietly invalidate D-325's reading.
    """
    K = 256
    lo, hi = ess_band(K)
    assert lo < essps.TARGET_FRACTION * K < hi


def test_recorded_arms_are_internally_consistent():
    for name, row in essps.PER_ITERATION_ARMS.items():
        steps, in_band, below, above, _, completion, _, _ = row
        assert in_band + below + above == steps, name
        assert completion >= 0.99, f"{name} reading is a timeout artifact"


def test_control_row_reproduces_the_branch_provenance():
    """`risk_mppi`'s median ESS must still be D-270's `31.2344`."""
    assert (essps.PER_ITERATION_ARMS["risk_mppi"][4]
            == pytest.approx(essps.HARVEST_MEDIAN_ESS, abs=1e-4))


def test_control_row_agrees_with_d274_compliance_count():
    assert (essps.PER_ITERATION_ARMS["risk_mppi"][1]
            == essps.COMPLIANCE_OPTIMAL[1] == 69)


def test_verdict_reports_compliance_and_cost_separately():
    v = essps.arm_verdict()
    assert v.holds_band and v.beats_control_on_band
    assert v.both_complete
    # The finding that must not get lost: the win is paid for.
    assert v.time_to_goal_ratio > 1.0
    assert v.time_to_goal_ratio == pytest.approx(157 / 115, rel=1e-9)


def test_band_comparison_uses_rates_not_counts():
    """157 > 69 is true for the wrong reason — the arms run different lengths.

    A count comparison would also call a *worse* arm better whenever it simply
    ran longer, so the property is pinned against a synthetic case where the
    counts and the rates disagree.
    """
    worse_but_longer = essps.ArmComparison(
        steps=200, in_band=100, control_steps=115, control_in_band=69,
        completion=0.999, control_completion=0.999,
        clearance=0.3, control_clearance=0.3)
    assert worse_but_longer.in_band > worse_but_longer.control_in_band
    assert not worse_but_longer.beats_control_on_band


# --------------------------------------------------------------------------
# Q-157: what does the 1.37× buy?
# --------------------------------------------------------------------------


def test_the_slowdown_buys_no_clearance():
    """Q-157's answer, and the reason the per-iteration form does not ship.

    The arm holds the band on every step *and* is 37% slower *and* ends up
    marginally closer to the obstacle. Band compliance is therefore bought with
    time and paid for in nothing — the same shape D-274 found for the scalar
    form, one layer up.
    """
    v = essps.arm_verdict()
    assert v.time_to_goal_ratio > 1.0
    assert not v.buys_clearance
    assert v.clearance_gain < 0.0


def test_clearance_gain_is_a_difference_not_a_ratio():
    """Clearance is signed, so a ratio is not monotone in safety.

    An arm that interpenetrates by 0.2 m against a control that interpenetrates
    by 0.4 m has *improved*, and the ratio (0.5) reads the same as a genuine
    halving of a positive clearance. The difference orders both cases right.
    """
    recovering = essps.ArmComparison(
        steps=115, in_band=69, control_steps=115, control_in_band=69,
        completion=0.999, control_completion=0.999,
        clearance=-0.2, control_clearance=-0.4)
    assert recovering.clearance_gain == pytest.approx(0.2)
    assert recovering.buys_clearance


def test_near_miss_is_not_scorable_on_the_peak_scene():
    """The missing second column of Q-157, pinned to its cause.

    `cafe_freezing_v0` carries obstacles and declares no margin, so a near-miss
    count on it would need a threshold nobody declared. This asserts the reason
    (an undeclared margin) rather than the absence, so a scene file that later
    *does* declare one flips this test instead of silently leaving a column
    everyone stopped expecting.
    """
    from eval.mppi_sandbox.ess_at_peak import PEAK_SCENE
    from eval.mppi_sandbox.feasibility import declared_margin
    from eval.mppi_sandbox.scenario import load_scenario

    scene = load_scenario(f"eval/scenarios/{PEAK_SCENE}.yaml")
    assert scene.obstacles, "a scene with no obstacles would be a different reason"
    assert declared_margin(scene) is None
    assert not essps.near_miss_scorable(scene)


def test_near_miss_scorable_is_true_where_a_margin_is_declared():
    """The predicate must not be vacuously False everywhere (D-107)."""
    from eval.mppi_sandbox.scenario import load_scenario

    scene = load_scenario("eval/scenarios/cafe_head_on_v0.yaml")
    assert essps.near_miss_scorable(scene)
