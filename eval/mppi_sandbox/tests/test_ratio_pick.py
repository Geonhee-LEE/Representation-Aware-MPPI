# SPDX-License-Identifier: BSD-3-Clause
"""Q-148's both-on ratio pick (D-261).

The load-bearing test is `test_the_published_cell_is_indeterminate_at_the_scene`:
D-260's `ATTRACT` headline was surveyed over radii that do not include the one
the A/B runs at except as its single dissenting row, and at that radius the
published cell resolves to no sign at all.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import both_on_cell as boc
from eval.mppi_sandbox import ratio_pick as rp
from eval.mppi_sandbox.epistemic_sign import ATTRACT


@pytest.fixture(scope="module")
def band():
    return rp.scene_band()


@pytest.fixture(scope="module")
def chosen():
    return rp.pick()


def test_the_scene_band_is_the_widest_in_the_surveyed_set(band):
    """Pins the band this whole module reasons about, and its outlier width.

    The width matters on its own: `r=0.3` is `INDETERMINATE` for the published
    ratio *because* its band is wide enough to contain it, so a drift that
    narrowed this band would silently convert measurement 1 into agreement with
    D-260 without anyone noticing the mechanism changed.
    """
    assert band.lo == pytest.approx(0.1704, abs=5e-4)
    assert band.hi == pytest.approx(0.5770, abs=5e-4)
    assert band.mean == pytest.approx(0.4121, abs=5e-4)

    others = [b for b in (boc.rollout_band(r) for r in (0.4, 0.5, 0.6, 0.8, 1.0))
              if b is not None]
    assert band.width > max(b.width for b in others)


def test_the_published_cell_is_indeterminate_at_the_scene(band):
    """Measurement 1 — the headline does not hold at the A/B's own geometry.

    D-260 is not wrong about the radii it surveyed; it is silent about this one.
    Both halves are asserted, so the test states the disagreement rather than
    just the local reading.
    """
    here = rp.published_cell_at_scene_radius()
    assert here.sign == boc.INDETERMINATE
    assert band.lo < boc.PUBLISHED_RATIO < band.hi

    elsewhere = boc.place_at_ratio(boc.PUBLISHED_RATIO, boc.rollout_band(0.5))
    assert elsewhere.sign == ATTRACT


def test_no_contended_ratio_is_a_constant_across_radii():
    """Measurement 2a — the bands share no common point, so the cell is per-scene.

    Asserted via the disjoint pair that causes it, not only via the `None`, so a
    failure names which geometries stopped overlapping.
    """
    assert rp.common_indeterminate_interval() is None

    b3, b5 = boc.rollout_band(0.3), boc.rollout_band(0.5)
    assert b3.hi < b5.lo          # outright disjoint, not merely non-nested


def test_sign_robust_constants_do_exist_across_radii():
    """Measurement 2b — the asymmetry that makes the rejected option tempting.

    Sign-robustness *is* transferable. This is asserted because the argument for
    the pick depends on rejecting the sign-robust cell for a different reason
    (duplication) — if it were also non-transferable the decision would be
    over-determined and D-261's reasoning would not be load-bearing.
    """
    lo, hi = rp.common_sign_robust_halflines()
    assert lo == pytest.approx(0.1704, abs=5e-4)
    assert hi == pytest.approx(0.8347, abs=5e-4)
    assert lo < hi

    for r in (0.3, 0.4, 0.5, 0.6, 0.8, 1.0):
        b = boc.rollout_band(r)
        assert boc.place_at_ratio(lo * 0.9, b).sign == ATTRACT


def test_the_pick_is_contended_and_therefore_not_a_duplicate_arm(chosen):
    """The decision: a cell where the arms contend, sign deliberately unresolved.

    `is_duplicate_of_a_single_arm` is the property the fourth arm exists to
    lack, and it is exactly the negation of the sign resolving — which is why
    the sign-robust alternative could not have served.
    """
    assert chosen.kind == rp.CONTENDED
    assert chosen.ratio == pytest.approx(0.4121, abs=5e-4)
    assert chosen.sign == boc.INDETERMINATE
    assert not chosen.is_duplicate_of_a_single_arm


def test_a_sign_robust_pick_would_have_been_a_duplicate(band):
    """The rejected branch, measured rather than argued.

    Placed just outside each end of the scene band: both resolve to a sign, and
    a resolved sign *is* one arm dominating the sum.
    """
    for ratio in (band.lo * 0.9, band.hi * 1.1):
        cell = boc.place_at_ratio(ratio, band)
        assert cell.sign != boc.INDETERMINATE
        assert rp.Pick(rp.SCENE_RADIUS, ratio, rp.SIGN_ROBUST,
                       cell).is_duplicate_of_a_single_arm


def test_the_pick_does_not_transfer_to_another_radius(chosen):
    """The stated cost, made a check instead of a remembered caveat.

    At `r=0.5` the chosen ratio is robustly `ATTRACT` — the duplication the pick
    avoids at the scene. A scene change obliges a re-pick.
    """
    assert not rp.transfers_to(chosen, 0.5)
    assert boc.place_at_ratio(chosen.ratio, boc.rollout_band(0.5)).sign == ATTRACT
    assert rp.transfers_to(chosen, rp.SCENE_RADIUS)


def test_scene_radius_provenance_is_declared_not_imported():
    """`SCENE_RADIUS` is quoted from an unmerged branch; the quote is auditable.

    Guards the feasibility-filter boundary: this module must not grow an import
    from PR #68, and the value must be re-checked when that branch lands.
    """
    prov = rp.scene_radius_provenance()
    assert prov["value"] == rp.SCENE_RADIUS == 0.3
    assert prov["pr"] == 68
    assert prov["recheck_on_merge"] is True

    # The boundary is about *code*, not prose: naming the scene in a docstring is
    # the provenance record. Checked by AST so a comment mentioning the yaml
    # cannot fail it and a real import cannot pass it.
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(rp.__file__).read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(a.name for a in node.names)
    assert not {"occlusion", "yaml", "load_scenario"} & imported
    assert not any("scenario" in name for name in imported)


def test_unposed_geometry_yields_no_pick():
    """`r=1.25` poses no question, so there is no cell — and no fallback.

    Substituting another radius's ratio is exactly what measurement 2 forbids.
    """
    assert rp.pick(1.25) is None
    assert rp.published_cell_at_scene_radius(1.25) is None
    assert rp.scene_band(1.25) is None
