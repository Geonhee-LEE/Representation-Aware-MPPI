# SPDX-License-Identifier: BSD-3-Clause
"""D-270 — the `w_voo` ladder re-taken inside `cafe_freezing_v0`'s calibrated window."""

from __future__ import annotations

import inspect

import pytest

from eval.mppi_sandbox import arm_audibility, calibrated_ladder as cl, ess_at_peak
from eval.mppi_sandbox.ab import ess_band


def test_shipped_temperature_is_below_the_calibrated_window():
    """The premise D-268 named but never checked: `lam = 0.1` is out of window."""
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    window = cl.calibrated_window()
    assert window, "empty window would make this scene unreportable (Q-035)"
    assert MPPIParams().lam < min(window), (
        f"shipped lam {MPPIParams().lam} is inside {window} — then D-268's "
        f"degeneracy needs an explanation other than temperature")


def test_lam_is_unreachable_as_a_controller_kwarg():
    """Why no ladder called `calibrate_lam`: `run_arm(lam=...)` cannot work.

    Pinned because the fix in `sweep`/`sweep_ess` is to pass `params`, and if a
    later change makes `lam` a real kwarg that indirection becomes dead weight
    that should be removed rather than left to rot.
    """
    from eval.mppi_sandbox.controllers.risk_mppi import RiskMPPI
    from eval.mppi_sandbox.controllers.stock_mppi import StockMPPI

    for cls in (StockMPPI, RiskMPPI):
        assert "lam" not in inspect.signature(cls.__init__).parameters, (
            f"{cls.__name__} now takes `lam` directly — drop the `params=` "
            f"indirection in calibrated_ladder.sweep")


def test_both_sweeps_forward_params():
    """The plumbing gap this cycle closed, pinned on both halves of it."""
    for fn in (ess_at_peak.sweep_ess, arm_audibility.sweep_ratio):
        assert "params" in inspect.signature(fn).parameters, (
            f"{fn.__qualname__} dropped `params` — the temperature becomes "
            f"unreachable again and ladders silently revert to lam=0.1")


def test_sweep_ess_refuses_to_pair_recorded_ratios_off_temperature():
    """A ratio measured at `lam = 0.1` does not describe a run at another (D-241).

    Checked on the source rather than by paying for a run: the rung's `ratio`
    must come out `None` whenever `params` is passed.
    """
    src = inspect.getsource(ess_at_peak.sweep_ess)
    assert "params is not None" in src and "ratio=None" in src, (
        "sweep_ess no longer drops the recorded ratio off-temperature")


@pytest.mark.parametrize("lam,weight,ess,ratio", [
    (0.8, 5.0, 31.2344, 0.228470),
    (0.8, 1.0, 116.0037, 0.073362),
    (0.4, 5.0, 1.9995, 0.116878),
])
def test_recorded_cells_match_their_verdict_components(lam, weight, ess, ratio):
    """The three cells the finding turns on, each graded by the imported bars."""
    lo, hi = ess_band(256)
    got = [p for p in cl.points() if p.lam == lam and p.weight == weight]
    assert len(got) == 1
    p = got[0]
    assert p.median_ess == pytest.approx(ess)
    assert p.ratio == pytest.approx(ratio)
    assert p.ess_in_band == (lo <= ess <= hi)
    assert p.audible == (ratio >= arm_audibility.AUDIBLE_RATIO)


def test_the_operating_point_is_the_top_of_the_window_and_is_unique():
    """`(lam 0.8, w_voo 5)` — in band, audible, completed; and nothing else is."""
    usable = cl.usable_points()
    assert [(p.lam, p.weight) for p in usable] == [(0.8, 5.0)], (
        "the co-satisfying set moved — D-270's whole claim is that it is a "
        "single cell at the top of the calibrated window")
    assert usable[0].lam == max(cl.calibrated_window())


def test_usable_requires_all_three_conditions():
    """In band alone, or audible alone, is satisfiable by a degenerate run."""
    base = dict(lam=0.8, weight=5.0, n_samples=256, reached_goal=True)
    assert cl.Point(median_ess=31.0, ratio=0.23, **base).usable
    assert not cl.Point(median_ess=1.0, ratio=0.23, **base).usable      # not weighting
    assert not cl.Point(median_ess=31.0, ratio=0.01, **base).usable     # inaudible
    assert not cl.Point(median_ess=31.0, ratio=0.23,
                        **{**base, "reached_goal": False}).usable       # froze


def test_unmeasured_ratio_is_unknown_not_inaudible():
    """The `lam = 0.2` rows carry no ratio and must not be graded as quiet."""
    quiet = [p for p in cl.points() if p.lam == 0.2]
    assert quiet and all(p.ratio is None for p in quiet)
    assert all(p.audible is None for p in quiet)
    assert not any(p.usable for p in quiet)


def test_verdict_reports_an_operating_point_and_can_now_address_d027():
    v = cl.verdict()
    assert v["verdict"] == "OPERATING_POINT_FOUND"
    assert v["usable_points"] == ((0.8, 5.0),)
    # D-268 could not address D-027 (no in-band rung to fall from). At 0.8 the
    # ladder holds band at w=5 and loses it by w=20, which is that reading.
    assert v["can_address_d027_ceiling"] is True
    assert 0.8 in v["addressable_at_lam"]
    # The scope D-266 fixed is untouched by a temperature change on this scene.
    assert v["transfers_to_ab_scene"] is False


def test_d268_verdict_is_unchanged_at_the_shipped_temperature():
    """This module adds a reading; it does not rewrite the one below it.

    D-268 is a true measurement *at `lam = 0.1`*, which is the temperature the
    rest of the branch ran at. Overwriting it would erase that.
    """
    ratios = {w: r for w, r, _ in arm_audibility.SCENE_CURVES[cl.PEAK_SCENE]}
    rungs = [ess_at_peak.Rung(weight=w, median_ess=e, n_samples=k,
                              reached_goal=g, ratio=ratios.get(w))
             for w, e, k, g in ess_at_peak.MEASURED_ESS]
    got = ess_at_peak.verdict(rungs)
    assert got["verdict"] == "ESS_DEGENERATE_THROUGHOUT"
    assert got["can_address_d027_ceiling"] is False


def test_the_window_this_leans_on_is_not_keyed_to_the_ladders_cost_field():
    """Stated, not hidden: the window was taken with the epistemic channels off."""
    keyed = cl.window_is_keyed()
    assert keyed["grade"] in {"UNKEYED", "OFF_KEY"}
    assert keyed["window_channel_weight"] == 0.0
    assert keyed["ladder_channel"] == "w_voo"


def test_the_rungs_that_decide_anything_move_under_recalibration():
    """Why `SCENE_CURVES[freezing]` is not quotable — stated at rung resolution.

    Not "every rung moves": the middle of the ladder (`w = 20, 50`) is stable
    to within 8%, and asserting otherwise was this test's first version and was
    false. What moves are the two rungs any conclusion rests on — the operating
    point at `w = 5` and the headline top rung at `w = 200`.
    """
    old = {w: r for w, r, _ in arm_audibility.SCENE_CURVES[cl.PEAK_SCENE]}
    new = {p.weight: p.ratio for p in cl.points()
           if p.lam == 0.8 and p.ratio is not None}
    assert new, "no re-measured ratios recorded at the top of the window"
    moved = {w: (r - old[w]) / old[w] for w, r in new.items()}

    assert moved[5.0] > 0.20, (
        f"the operating-point rung moved only {moved[5.0]:.1%} — if it is "
        f"temperature-stable, quoting D-266's row for it is defensible")
    assert moved[200.0] < -0.20, (
        f"the top rung moved {moved[200.0]:.1%}; D-266's headline `3.2644` is "
        f"only unquotable if recalibration pulls it down materially")
    # And the direction is not uniform, which is the reason a blanket rescale
    # of the old row cannot repair it: the ends move opposite ways.
    assert moved[5.0] > 0 > moved[200.0]


def test_middle_of_the_ladder_is_temperature_stable():
    """The honest other half: `w ∈ {20, 50}` survive recalibration within 10%.

    Pinned so the finding cannot later be restated as "the whole curve is
    unreliable", which the measurement does not support.
    """
    old = {w: r for w, r, _ in arm_audibility.SCENE_CURVES[cl.PEAK_SCENE]}
    new = {p.weight: p.ratio for p in cl.points()
           if p.lam == 0.8 and p.ratio is not None}
    for w in (20.0, 50.0):
        assert abs(new[w] - old[w]) / old[w] < 0.10
