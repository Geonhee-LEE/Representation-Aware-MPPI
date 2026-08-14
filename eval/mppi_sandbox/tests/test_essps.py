# SPDX-License-Identifier: BSD-3-Clause
"""ESSPS solve + the recorded finding it produced (see `essps` docstring)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.optimize import minimize_scalar

from eval.mppi_sandbox import essps
from eval.mppi_sandbox.ab import ess_band
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams


def _costs(seed: int = 0, k: int = 256, scale: float = 30.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.gamma(2.0, scale, size=k)


# --- the solve itself -------------------------------------------------------

def test_ess_is_monotone_in_lam():
    """The structural fact that makes existence uninteresting."""
    c = _costs()
    vals = [essps.ess_of(c, lam) for lam in (0.01, 0.1, 1.0, 10.0, 100.0, 1e4)]
    assert all(a < b for a, b in zip(vals, vals[1:]))


def test_ess_limits_are_one_and_k():
    c = _costs()
    assert essps.ess_of(c, 1e-3) == pytest.approx(1.0, abs=1e-6)
    assert essps.ess_of(c, 1e8) == pytest.approx(c.size, rel=1e-6)


def test_solve_hits_the_target():
    c = _costs()
    target = essps.TARGET_FRACTION * c.size
    lam = essps.solve_lam_for_ess(c, target)
    assert lam is not None
    assert essps.ess_of(c, lam) == pytest.approx(target, rel=1e-8)


def test_solve_defaults_to_the_paper_fraction():
    c = _costs()
    assert essps.solve_lam_for_ess(c) == pytest.approx(
        essps.solve_lam_for_ess(c, essps.TARGET_FRACTION * c.size), rel=1e-9)


def test_root_find_matches_paper_objective():
    """Brent-minimizing `|ESS - N*|` and root-finding reach the same `lam`."""
    c = _costs(seed=3)
    target = essps.TARGET_FRACTION * c.size
    ours = essps.solve_lam_for_ess(c, target)
    paper = minimize_scalar(
        lambda log_lam: abs(essps.ess_of(c, float(np.exp(log_lam))) - target),
        bracket=(np.log(0.1), np.log(10.0)), method="brent")
    assert float(np.exp(paper.x)) == pytest.approx(ours, rel=1e-4)


def test_unreachable_target_returns_none_not_a_clip():
    c = _costs()
    assert essps.solve_lam_for_ess(c, c.size + 1.0) is None
    assert essps.solve_lam_for_ess(c, 0.5) is None


def test_target_fraction_lands_inside_the_band():
    """A target outside Q-026's band would make the whole question vacuous."""
    lo, hi = ess_band(256)
    assert lo < essps.TARGET_FRACTION * 256 < hi


def test_ess_of_agrees_with_the_controller_weighting(monkeypatch):
    """Pin `ess_of` to `StockMPPI`'s own softmax so the pair cannot drift."""
    c = _costs(seed=7)
    lam = MPPIParams().lam
    w = np.exp(-(c - c.min()) / lam)
    w /= w.sum()
    assert essps.ess_of(c, lam) == pytest.approx(1.0 / np.square(w).sum(), rel=1e-12)


def test_scale_invariance_is_in_the_ratio_not_the_lam():
    """ESS depends on normalized weights, so scaling costs scales `lam` with them."""
    c = _costs(seed=11)
    target = essps.TARGET_FRACTION * c.size
    lam = essps.solve_lam_for_ess(c, target)
    lam_scaled = essps.solve_lam_for_ess(10.0 * c, target)
    assert lam_scaled == pytest.approx(10.0 * lam, rel=1e-6)


# --- the recorded finding ---------------------------------------------------

def test_a_target_lam_existed_at_every_step():
    n_steps, solved, *_ = essps.SOLVED_LAM
    assert solved == n_steps


def test_solved_lam_spread_is_the_finding():
    _, _, lo, med, hi = essps.SOLVED_LAM
    assert lo < med < hi
    assert hi / lo > 40.0


def test_scalar_essps_is_dominated_by_the_best_constant():
    mm_lam, mm_band, n, _ = essps.MEDIAN_MATCHED
    co_lam, co_band, n2, _ = essps.COMPLIANCE_OPTIMAL
    assert n == n2
    assert mm_band < co_band, "median-matching should lose to the best constant"
    assert mm_lam > co_lam


def test_compliance_optimal_is_the_shipped_rung():
    co_lam = essps.COMPLIANCE_OPTIMAL[0]
    assert abs(co_lam - essps.OPERATING_LAM) / essps.OPERATING_LAM < 0.02


def test_no_constant_holds_the_band_through_the_episode():
    below, above = essps.OPTIMAL_OUT_OF_BAND
    n = essps.COMPLIANCE_OPTIMAL[2]
    assert below > 0 and above > 0
    assert essps.COMPLIANCE_OPTIMAL[1] + below + above == n


def test_harvest_reproduces_the_recorded_operating_point_ess():
    """Provenance: this cost stream is the one D-270 measured (31.2344)."""
    assert essps.HARVEST_MEDIAN_ESS == pytest.approx(31.2344, abs=1e-4)


# --- verdict ----------------------------------------------------------------

def test_verdict_is_dominated_not_a_refusal():
    v = essps.verdict()
    assert v["verdict"] == "SCALAR_ESSPS_DOMINATED"
    assert v["solved_at"] == "115/115 steps"
    assert v["optimal_matches_shipped_rung"] is True


def test_verdict_separates_existence_from_usefulness():
    v = essps.verdict()
    # The structural yes must not be reported as a win.
    assert v["retires_per_scene_essps_constant"] is True
    assert v["retires_per_iteration_essps"] is False
    assert v["removes_lam_window_table"] is False


def test_verdict_keeps_d266_scope():
    assert "not transferred" in essps.verdict()["scope"]


def test_verdict_names_would_flip_on_different_numbers():
    """The grade is derived, not typed — a real win would be reported as one."""
    v = essps.ScalarVerdict(solved_steps=115, n_steps=115, lam_spread=47.6,
                            median_matched_in_band=90, optimal_in_band=69,
                            optimal_lam=0.787)
    assert v.exists and v.beats_constant and not v.any_constant_holds
