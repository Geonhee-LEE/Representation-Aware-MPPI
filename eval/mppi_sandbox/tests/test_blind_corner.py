# SPDX-License-Identifier: BSD-3-Clause
"""Blind-corner occlusion scenario + metric contract (Q-017 measurement).

Q-017 found the epistemic shadow cost closed-loop *redundant* for a single
convex obstacle (shadow ⊆ obstacle-cost). The missing piece it named was a
scenario "where the shadow hides a low-obstacle-cost shortcut" — a genuine
blind corner. This suite ships that scenario (`cafe_blind_corner_v0.yaml`)
plus the occlusion metric pair (`eval.mppi_sandbox.occlusion`) that scores
it, and pins down three properties:

1. the scenario has a *real* blind spot (the declared pocket is occluded on
   approach), so it is a valid epistemic test-bed — not another geometry
   where σ is trivially inert;
2. the oracle baseline rounds the corner and meets acceptance (the scenario
   is solvable, so any epistemic behaviour change is a *choice*, not forced);
3. the sightline-reveal metric is delayed (pocket revealed only after the
   corner) — the non-zero, path-dependent scalar the EPISTEMIC channel can
   be scored on, the way clearance scores the DYNAMIC channel.

The forward-looking shadow-cost assertion (does `w_epist` reveal the pocket
earlier / not raise exposure?) self-activates once `w_epist` lands on main
via PR #67 — until then it skips, so this file is green on main today.
"""

import inspect
from pathlib import Path

import numpy as np
import yaml

from eval.mppi_sandbox.controllers import RiskMPPI, make_controller
from eval.mppi_sandbox.obstacles import min_clearance
from eval.mppi_sandbox.occlusion import (occlusion_exposure, point_sigma,
                                         sightline_reveal)
from eval.mppi_sandbox.run import ROBOT_RADIUS, run_scenario, simulate
from eval.mppi_sandbox.scenario import load_scenario

SCENARIO = "eval/scenarios/cafe_blind_corner_v0.yaml"


def _pocket():
    raw = yaml.safe_load(Path(SCENARIO).read_text())
    p = raw["blind_pocket"]
    return np.array([p["x"], p["y"]], dtype=float)


class TestScenarioValidity:
    def test_pocket_is_occluded_on_approach(self):
        """The declared blind pocket must be genuinely unseen (σ=1) from the
        start and from the mid-approach — otherwise the scenario is not a
        blind corner and σ would be trivially inert (the Q-017 trap)."""
        scen = load_scenario(SCENARIO)
        pocket = _pocket()
        assert point_sigma(scen.obstacles, scen.start[:2], 0.0, pocket) == 1.0
        assert point_sigma(scen.obstacles, [2.0, 0.4], 0.0, pocket) == 1.0

    def test_pocket_becomes_visible_after_rounding(self):
        """Sanity on the other side: once the robot is past the wall top the
        pocket is in sight — the scenario reveals, it does not permanently
        hide (which would make the reveal metric degenerate)."""
        scen = load_scenario(SCENARIO)
        assert point_sigma(scen.obstacles, [3.2, -0.2], 0.0, _pocket()) < 0.5


class TestBaselineSolvable:
    def test_stock_rounds_corner_within_acceptance(self):
        res = run_scenario(SCENARIO, controller="stock_mppi", seed=0)
        assert res["pass"] is True, res["acceptance"]
        assert res["collision"] is False
        assert res["min_obstacle_clearance"] > 0.0
        assert res["metrics"]["goal_reached"] == 1


class TestSightlineMetric:
    def test_reveal_is_delayed_not_from_start(self):
        """The headline EPISTEMIC scalar: the pocket is hidden at the start
        and only revealed partway along the path — a real, path-dependent
        'how blind was the approach' number (clearance's occlusion-aware
        analogue)."""
        scen = load_scenario(SCENARIO)
        traj = simulate(scen, make_controller("stock_mppi", scen, seed=0,
                                              robot_radius=ROBOT_RADIUS))
        rev = sightline_reveal(traj, scen.obstacles, _pocket())
        assert rev["visible_from_start"] is False
        assert rev["reveal_index"] is not None, "pocket never revealed"
        assert 0.0 < rev["reveal_fraction"] < 1.0
        assert rev["reveal_distance"] > 0.0

    def test_exposure_metric_is_non_negative_and_finite(self):
        scen = load_scenario(SCENARIO)
        traj = simulate(scen, make_controller("stock_mppi", scen, seed=0,
                                              robot_radius=ROBOT_RADIUS))
        exp = occlusion_exposure(traj, scen.obstacles)
        assert exp >= 0.0 and np.isfinite(exp)


def _risk_mppi_has_wepist() -> bool:
    return "w_epist" in inspect.signature(RiskMPPI.__init__).parameters


class TestShadowCostForwardContract:
    """Self-activating once PR #67 (ShadowCostCritic / w_epist) lands on main.

    Conservative on purpose: the shadow cost is add-only (σ≥0, w_epist≥0), so
    the strongest thing provable without over-claiming a future gain is that
    turning it on must NOT break the solve nor drive the robot *blinder*
    (later reveal / higher exposure). A later cycle can tighten this to a
    strict reveal-earlier assertion once the gain is actually measured — the
    honest Q-017 posture (no premature GREEN)."""

    def test_shadow_cost_does_not_regress_blindness(self):
        import pytest
        if not _risk_mppi_has_wepist():
            pytest.skip("w_epist not on main yet (PR #67) — forward contract")
        scen = load_scenario(SCENARIO)
        pocket = _pocket()
        base = simulate(scen, make_controller("risk_mppi", scen, seed=0,
                        robot_radius=ROBOT_RADIUS, w_risk=0.0,
                        k_margin_per_sigma=0.0, w_epist=0.0))
        shad = simulate(scen, make_controller("risk_mppi", scen, seed=0,
                        robot_radius=ROBOT_RADIUS, w_risk=0.0,
                        k_margin_per_sigma=0.0, w_epist=150.0))
        # still solves
        assert min_clearance(shad, scen.obstacles, ROBOT_RADIUS) > 0.0
        # not blinder: reveal no later, exposure no higher (add-only floor)
        rb = sightline_reveal(base, scen.obstacles, pocket)
        rs = sightline_reveal(shad, scen.obstacles, pocket)
        if rb["reveal_fraction"] is not None and rs["reveal_fraction"] is not None:
            assert rs["reveal_fraction"] <= rb["reveal_fraction"] + 1e-6
        assert (occlusion_exposure(shad, scen.obstacles)
                <= occlusion_exposure(base, scen.obstacles) + 1e-6)
