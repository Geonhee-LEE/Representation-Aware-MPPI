# SPDX-License-Identifier: BSD-3-Clause
"""Near-miss scoring: the threshold is the scene's, and the headline is monotone."""

from __future__ import annotations

import math

import pytest

from eval.mppi_sandbox import near_miss as nm
from eval.mppi_sandbox.baseline_matrix import Cell, Matrix, OK, NO_OBSTACLES
from eval.mppi_sandbox.feasibility import declared_margin
from eval.mppi_sandbox.scenario import load_scenario


# --------------------------------------------------------------------------
# The motivating datum, and the boundary.
# --------------------------------------------------------------------------

def test_the_1p6mm_pass_is_a_near_miss_not_a_success():
    """D-119's headline number. `cafe_head_on_v0` declares 0.40 m and
    `stock_mppi` passed at 0.0016 m; the collision counter called that clean."""
    assert nm.classify(0.0016, 0.40) == nm.NEAR_MISS


def test_boundary_is_closed_on_the_safe_side():
    """The scene asked for *at least* `margin`, so exactly `margin` clears."""
    assert nm.classify(0.40, 0.40) == nm.SAFE
    assert nm.classify(0.40 - 1e-9, 0.40) == nm.NEAR_MISS


def test_collision_is_threshold_free():
    """Interpenetration is a collision whatever the scene declared — which is
    why a cell with no margin can still be scored for collisions."""
    assert nm.classify(-0.01, 0.40) == nm.COLLISION
    assert nm.classify(-0.01, 0.01) == nm.COLLISION


# --------------------------------------------------------------------------
# Monotonicity: the property that decides which number is the headline.
# --------------------------------------------------------------------------

def test_near_miss_rate_is_NOT_monotone_in_safety():
    """A graze degrading into a collision *leaves* the `[0, margin)` band, so
    `near_miss_rate` falls. Pinned as a defect of the quantity, not fixed —
    this is the whole reason it is not the comparable scalar."""
    grazing = nm.score([0.01, 0.01, 0.5, 0.5], margin=0.3)
    worse = nm.score([-0.01, -0.01, 0.5, 0.5], margin=0.3)   # both now collide
    assert worse.near_miss_rate < grazing.near_miss_rate
    assert grazing.near_miss_rate == 0.5 and worse.near_miss_rate == 0.0


def test_unsafe_rate_IS_monotone_under_the_same_degradation():
    """Same two ensembles: the monotone scalar refuses to improve."""
    grazing = nm.score([0.01, 0.01, 0.5, 0.5], margin=0.3)
    worse = nm.score([-0.01, -0.01, 0.5, 0.5], margin=0.3)
    assert worse.unsafe_rate >= grazing.unsafe_rate
    assert grazing.unsafe_rate == worse.unsafe_rate == 0.5


def test_unsafe_rate_rises_when_a_safe_run_starts_grazing():
    """And it is not merely constant — it tracks real degradation."""
    before = nm.score([0.5, 0.5, 0.5, 0.5], margin=0.3)
    after = nm.score([0.5, 0.5, 0.5, 0.01], margin=0.3)
    assert before.unsafe_rate == 0.0 and after.unsafe_rate == 0.25


def test_decomposition_sums_to_the_ensemble():
    s = nm.score([-0.1, 0.01, 0.5, 0.5, 0.2], margin=0.3)
    assert s.safe + s.near_misses + s.collisions == s.n == 5
    assert (s.collisions, s.near_misses, s.safe) == (1, 2, 2)


# --------------------------------------------------------------------------
# Undeclared margin is a refusal, not a zero.
# --------------------------------------------------------------------------

def test_undeclared_and_nonpositive_margins_are_both_unscorable():
    assert not nm.is_scorable_margin(None)
    assert not nm.is_scorable_margin(0.0)
    assert not nm.is_scorable_margin(-0.1)
    assert nm.is_scorable_margin(0.3)


def test_scoring_an_unscorable_margin_raises_rather_than_returning_clean():
    """The failure mode being blocked: an empty band silently reporting
    `near_miss_rate = 0.0` for a cell nobody set a threshold on."""
    for bad in (None, 0.0, -0.1):
        with pytest.raises(ValueError, match="empty near-miss band"):
            nm.classify(0.001, bad)


def test_zero_margin_would_have_scored_the_1p6mm_pass_clean():
    """Why the `0.0` default is the specific danger, stated as a measurement:
    under it the motivating run is SAFE."""
    with pytest.raises(ValueError):
        nm.classify(0.0016, 0.0)
    # ... and had the guard not been there, the band `[0, 0)` admits nothing:
    assert not (0.0 <= 0.0016 < 0.0)


# --------------------------------------------------------------------------
# The threshold comes from the shipped scenes, pinned on the real files.
# --------------------------------------------------------------------------

def test_shipped_scenes_declare_different_margins():
    """A global constant would overrule head_on's 0.40 and flatter convoy."""
    head_on = declared_margin(load_scenario("eval/scenarios/cafe_head_on_v0.yaml"))
    convoy = declared_margin(load_scenario("eval/scenarios/cafe_convoy_v0.yaml"))
    assert head_on == 0.40
    assert convoy == 0.30
    assert head_on != convoy


def test_cafe_freezing_has_obstacles_but_declares_no_margin():
    """The shipped instance of the excluded class. If this scene ever gains a
    margin this test fails loudly, which is the intended notification."""
    scen = load_scenario("eval/scenarios/cafe_freezing_v0.yaml")
    assert scen.obstacles, "freezing scene is supposed to contain obstacles"
    assert declared_margin(scen) is None


def test_feasibility_screen_keeps_its_optimistic_default():
    """The two consumers default oppositely on purpose; this pins that the
    screen was not changed into a refusal by the reader's introduction."""
    from eval.mppi_sandbox.feasibility import goal_ball_clearance
    scen = load_scenario("eval/scenarios/cafe_freezing_v0.yaml")
    assert goal_ball_clearance(scen).required_clearance == 0.0


# --------------------------------------------------------------------------
# Matrix wiring: a third denominator, not a re-slice of the avoidance one.
# --------------------------------------------------------------------------

def _cell(name, status=OK, margin=0.3, safety=None, n=8):
    return Cell(controller="stock_mppi", scenario=name, status=status,
                n_seeds=n, successes=n, margin=margin, safety=safety)


def test_no_margin_cell_is_avoidance_reportable_but_not_near_miss_reportable():
    c = _cell("cafe_freezing_v0", margin=None)
    assert c.avoidance_reportable is True
    assert c.near_miss_reportable is False


def test_near_miss_population_is_a_strict_subset_and_is_named():
    scored = _cell("cafe_head_on_v0", margin=0.4,
                   safety=nm.score([0.5] * 8, margin=0.4))
    unscored = _cell("cafe_freezing_v0", margin=None)
    h = Matrix(cells=(scored, unscored)).headline()
    assert h.avoidance_cells == 2
    assert h.near_miss_cells == 1
    assert h.unscored_margin == ("stock_mppi/cafe_freezing_v0",)


def test_empty_near_miss_population_yields_nan_not_a_clean_zero():
    """D-107's failure, blocked at the headline as well as at the cell."""
    h = Matrix(cells=(_cell("cafe_freezing_v0", margin=None),)).headline()
    assert h.near_miss_cells == 0
    assert math.isnan(h.near_miss_rate)
    assert math.isnan(h.unsafe_rate)


def test_headline_aggregates_over_seeds_not_cells():
    a = _cell("cafe_head_on_v0", margin=0.4,
              safety=nm.score([0.01] + [0.5] * 7, margin=0.4))   # 1 graze / 8
    b = _cell("cafe_convoy_v0", margin=0.3,
              safety=nm.score([0.5] * 8, margin=0.3))            # 0 / 8
    h = Matrix(cells=(a, b)).headline()
    assert h.near_miss_cells == 2
    assert h.near_miss_rate == pytest.approx(1 / 16)
    assert h.unsafe_rate == pytest.approx(1 / 16)


def test_non_ok_cells_never_enter_the_near_miss_population():
    """A scene with no obstacles has a margin key on some files; it must still
    be excluded, because the ladder already refused it."""
    c = _cell("cafe_straight_v0", status=NO_OBSTACLES, margin=0.3,
              safety=nm.score([0.5] * 8, margin=0.3))
    h = Matrix(cells=(c,)).headline()
    assert h.near_miss_cells == 0
