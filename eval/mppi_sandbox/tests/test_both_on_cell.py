# SPDX-License-Identifier: BSD-3-Clause
"""Q-148's both-on cell, re-placed on the planner's support (D-258 consequence).

The load-bearing test here is `test_the_published_cell_is_attract_not_cancelling`:
the cell Q-148 currently carries was placed at the *grid* root and is therefore
described as a cancelling cell, and on the rollout support it is not one.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import both_on_cell as boc
from eval.mppi_sandbox import rollout_cloud as rc
from eval.mppi_sandbox.cancelling_stability import REPEL_SPLIT_UNIT
from eval.mppi_sandbox.epistemic_sign import ATTRACT, REPEL


@pytest.fixture(scope="module")
def band():
    """The r=0.5 rollout band — D-258's headline cell."""
    return boc.rollout_band(0.5)


@pytest.fixture(scope="module")
def surveyed():
    return boc.survey()


def test_the_band_is_d258s_measured_one(band):
    """Pinned to D-258's published interval, so this module reads that quantity.

    Not a re-derivation: if `rollout_cloud` drifts, the placement below is about
    a different band and every verdict in this file changes meaning silently.
    """
    assert band.lo == pytest.approx(0.6386, abs=5e-4)
    assert band.hi == pytest.approx(0.8347, abs=5e-4)
    assert band.mean == pytest.approx(0.7475, abs=5e-4)


def test_the_published_cell_is_attract_not_cancelling(band):
    """The headline: D-256's `0.3587` is robustly attract on the planner support.

    It was placed as the ratio at which the sum *cancels*, which is true of the
    grid and false here — the ratio sits below the whole band, so every root in
    the band puts the summed split on the attract side.
    """
    cell = boc.place_at_ratio(boc.PUBLISHED_RATIO, band)
    assert cell.sign == ATTRACT
    assert all(s < 0.0 for s in cell.splits)
    assert cell.ratio < band.lo          # and by a margin, not marginally
    assert cell.headroom < 1.0           # already past the root, not short of it


def test_the_sign_is_a_conjunction_over_the_band_not_its_mean(band):
    """A ratio inside the band is `INDETERMINATE`, not decided by the midpoint.

    This is the guard against reporting a both-on arm's sign because the band's
    mean happened to fall on one side — the failure the three-outcome vocabulary
    exists to prevent.
    """
    inside = boc.place_at_ratio(band.mean, band)
    assert inside.sign == boc.INDETERMINATE
    assert any(s > 0.0 for s in inside.splits)
    assert any(s < 0.0 for s in inside.splits)


def test_the_bracket_brackets(band):
    """Below `lo` is attract, above `hi` is repel, and both are strict."""
    lo, hi = boc.sign_robust_bracket(band)
    assert lo == band.lo and hi == band.hi
    assert boc.place_at_ratio(lo * 0.99, band).sign == ATTRACT
    assert boc.place_at_ratio(hi * 1.01, band).sign == REPEL
    # the contended placement is inside the bracket by construction
    assert lo <= boc.contended_ratio(band) <= hi


def test_headroom_reproduces_the_published_factors(band):
    """`ratio / root` at 1:1 must give D-258's 1.34x, or it is a new quantity.

    D-256's grid 2.79x is the same formula on the grid root; checked here as
    arithmetic on the published number rather than by re-running the grid, since
    `cancelling_stability` already owns that band.
    """
    unit = boc.place_at_ratio(1.0, band)
    assert unit.headroom == pytest.approx(1.3378, abs=2e-3)
    assert unit.sign == REPEL            # 1:1 is still repel — the *margin* shrank
    assert 1.0 / boc.PUBLISHED_RATIO == pytest.approx(2.7878, abs=1e-3)


def test_the_split_algebra_uses_the_structural_constant(band):
    """The repel term is `REPEL_SPLIT_UNIT`, imported — not a literal 1.0."""
    cell = boc.place_at_ratio(0.5, band, w_voo=2.0)
    assert cell.w_epist == 1.0 and cell.w_voo == 2.0
    assert cell.split_against(0.3) == pytest.approx(
        1.0 * REPEL_SPLIT_UNIT - 2.0 * 0.3)
    # scale-invariance of the sign: only the ratio moves it
    assert cell.sign == boc.place_at_ratio(0.5, band, w_voo=100.0).sign


def test_unposed_radius_is_unplaceable_not_grid_substituted(surveyed):
    """At r=1.25 there is no planner-support root, so there is no cell.

    Falling back to the grid root is D-258 alternative (b), explicitly rejected.
    The survey must therefore carry the hole rather than fill it.
    """
    assert boc.rollout_band(1.25) is None
    assert boc.republished_placement(1.25) is None
    assert surveyed[1.25]["status"] == boc.UNPLACEABLE
    assert "band" not in surveyed[1.25]


def test_the_cell_is_never_repel_but_does_not_resolve_everywhere(surveyed):
    """The finding in its honest form — 5 ATTRACT, 1 INDETERMINATE, 1 UNPLACEABLE.

    `published_cell_sign_is_stable` is False and that is not a softening: the
    disagreement is attract-vs-unresolved, never attract-vs-repel. Both
    predicates are pinned so a future band change cannot quietly convert one
    into the other.
    """
    statuses = [v["status"] for v in surveyed.values()]
    assert statuses.count(ATTRACT) == 5
    assert statuses.count(boc.INDETERMINATE) == 1
    assert statuses.count(boc.UNPLACEABLE) == 1
    assert statuses.count(REPEL) == 0

    assert boc.published_cell_is_never_repel(surveyed)
    assert not boc.published_cell_sign_is_stable(surveyed)
    # and the unresolved one is the widest band, which is why it does not resolve
    assert surveyed[0.3]["status"] == boc.INDETERMINATE
    assert surveyed[0.3]["band"].contains(boc.PUBLISHED_RATIO)


def test_survey_radii_are_the_declared_set(surveyed):
    """The survey walks D-257's own radii — not a friendlier subset."""
    from eval.mppi_sandbox.cancelling_stability import DEFAULT_RADII
    assert tuple(surveyed) == DEFAULT_RADII


def test_sombrl_regime_flag_tracks_the_sign(band):
    """The guaranteed-regime flag is the attract sign, not a separate judgement."""
    assert boc.place_at_ratio(boc.PUBLISHED_RATIO, band).sign_is_guaranteed_regime
    assert not boc.place_at_ratio(band.hi * 1.01, band).sign_is_guaranteed_regime
    assert not boc.place_at_ratio(band.mean, band).sign_is_guaranteed_regime
