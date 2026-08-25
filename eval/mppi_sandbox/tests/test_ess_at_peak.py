# SPDX-License-Identifier: BSD-3-Clause
"""`ess_at_peak` — the sampler reading at the weight where `w_voo` goes audible.

No test walks the ladder: each rung is a closed-loop run (~13 s). What is
tested is the vocabulary, the pairing, and that the verdict cannot be reached
by an unmeasured rung — the failure modes that would let a green suite ship a
collapse nobody observed.
"""

from __future__ import annotations

import math

import pytest

from eval.mppi_sandbox import ess_at_peak
from eval.mppi_sandbox.arm_audibility import AUDIBLE_RATIO, SCENE_CURVES
from eval.mppi_sandbox.ess_at_peak import PEAK_SCENE, Rung, verdict


def _rung(weight, ess, *, k=256, ratio=None, reached=True):
    return Rung(weight=weight, median_ess=ess, n_samples=k,
                reached_goal=reached, ratio=ratio)


def test_peak_scene_is_the_one_d266_measured_as_monotone():
    """The scene choice is the argument — pin it to D-266's recorded curve."""
    curve = SCENE_CURVES[PEAK_SCENE]
    ratios = [r for _w, r, _rest in curve]
    assert ratios == sorted(ratios), (
        "PEAK_SCENE was chosen because its ratio ladder is monotone rising; "
        "if that stopped being true the separation argument is gone")
    assert ratios[-1] > 10 * AUDIBLE_RATIO, (
        "the top rung must be loudly audible for the ESS question to be sharp")


def test_the_bar_is_imported_not_restated():
    """One quantity, one statement (D-047)."""
    assert ess_at_peak.AUDIBLE_RATIO is AUDIBLE_RATIO


def test_ratios_are_read_from_d266_not_retyped():
    recorded = {float(w): float(r) for w, r, _ in SCENE_CURVES[PEAK_SCENE]}
    assert ess_at_peak._ratios() == recorded


def test_audible_reads_the_bar():
    assert _rung(200.0, 100.0, ratio=3.2644).audible is True
    assert _rung(1.0, 100.0, ratio=0.0581).audible is False
    assert _rung(7.0, 100.0, ratio=None).audible is None


def test_in_band_is_tri_state_and_unmeasured_is_not_compliant():
    """A controller that logged no ESS is unknown, not in band."""
    assert _rung(1.0, float("nan"), k=0).ess_in_band is None
    assert _rung(1.0, float("nan"), k=256).ess_in_band is None
    lo, hi = _rung(1.0, 0.0).band
    assert _rung(1.0, (lo + hi) / 2).ess_in_band is True
    assert _rung(1.0, lo - 1e-9).ess_in_band is False
    assert _rung(1.0, hi + 1e-9).ess_in_band is False


def test_held_verdict_requires_every_audible_rung_in_band():
    lo, hi = ess_at_peak.ess_band(256)
    mid = (lo + hi) / 2
    rungs = [_rung(1.0, mid, ratio=0.0581), _rung(200.0, mid, ratio=3.2644)]
    out = verdict(rungs)
    assert out["verdict"] == "ESS_HELD"
    assert out["held"] is True
    assert out["audible_rungs"] == (200.0,)


def test_collapse_is_reported_only_when_an_audible_rung_leaves_the_band():
    """An inaudible rung falling out of band is not D-027's ceiling."""
    lo, hi = ess_at_peak.ess_band(256)
    mid = (lo + hi) / 2
    # quiet rung out of band, loud rung in band -> not a collapse of the
    # audible region
    ok = verdict([_rung(1.0, lo - 1, ratio=0.0581),
                  _rung(200.0, mid, ratio=3.2644)])
    assert ok["verdict"] == "ESS_HELD"
    assert ok["out_of_band_rungs"] == (1.0,)

    bad = verdict([_rung(1.0, mid, ratio=0.0581),
                   _rung(200.0, hi + 1, ratio=3.2644)])
    assert bad["verdict"] == "ESS_COLLAPSED"
    assert bad["held"] is False


def test_degenerate_throughout_is_not_reported_as_d027_collapse():
    """Nothing fell if nothing was ever in band — the measured case.

    This is the distinction the measurement forced: `ESS_COLLAPSED` claims the
    weight pushed the sampler out of its band, which requires an in-band rung
    to have been pushed *from*.
    """
    lo, _hi = ess_at_peak.ess_band(256)
    out = verdict([_rung(1.0, lo - 1, ratio=0.0581),
                   _rung(200.0, lo - 5, ratio=3.2644)])
    assert out["verdict"] == "ESS_DEGENERATE_THROUGHOUT"
    assert out["held"] is False
    assert out["can_address_d027_ceiling"] is False


def test_collapse_verdict_can_address_d027_but_degenerate_cannot():
    lo, hi = ess_at_peak.ess_band(256)
    mid = (lo + hi) / 2
    collapsed = verdict([_rung(1.0, mid, ratio=0.0581),
                         _rung(200.0, hi + 1, ratio=3.2644)])
    assert collapsed["verdict"] == "ESS_COLLAPSED"
    assert collapsed["can_address_d027_ceiling"] is True


def test_measured_ladder_is_degenerate_at_every_rung():
    """Pin the finding: the recorded table reproduces the verdict."""
    ratios = ess_at_peak._ratios()
    rungs = [Rung(weight=w, median_ess=ess, n_samples=k, reached_goal=ok,
                  ratio=ratios.get(w))
             for w, ess, k, ok in ess_at_peak.MEASURED_ESS]
    out = verdict(rungs)
    assert out["verdict"] == "ESS_DEGENERATE_THROUGHOUT"
    assert out["can_address_d027_ceiling"] is False
    # the quietest rung is the *closest* to the band — the arm is not the cause
    assert rungs[0].median_ess > rungs[-1].median_ess
    lo, _hi = ess_at_peak.ess_band(256)
    assert all(r.median_ess < lo for r in rungs)


def test_every_measured_rung_still_reached_the_goal():
    """A degenerate sampler that still arrives — the reading is not a crash."""
    assert all(ok for _w, _e, _k, ok in ess_at_peak.MEASURED_ESS)


def test_unmeasured_ess_outranks_both_answers():
    """The guard is non-vacuous: an unknown rung cannot reach a verdict."""
    lo, hi = ess_at_peak.ess_band(256)
    mid = (lo + hi) / 2
    out = verdict([_rung(1.0, float("nan"), k=0, ratio=0.0581),
                   _rung(200.0, mid, ratio=3.2644)])
    assert out["verdict"] == "ESS_UNMEASURED"
    assert out["held"] is None
    assert out["unmeasured_rungs"] == (1.0,)


def test_never_audible_is_distinct_from_held():
    """A ladder that never clears the bar has not shown the sampler holds."""
    lo, hi = ess_at_peak.ess_band(256)
    mid = (lo + hi) / 2
    out = verdict([_rung(1.0, mid, ratio=0.01), _rung(5.0, mid, ratio=0.02)])
    assert out["verdict"] == "NEVER_AUDIBLE"
    assert out["audible_rungs"] == ()


def test_empty_ladder_is_not_a_pass():
    assert verdict(())["verdict"] == "NO_RUNGS"
    assert verdict(())["held"] is None


def test_scope_is_not_widened_by_this_measurement():
    """D-266's non-transfer stands — a freezing-scene ceiling is freezing's."""
    out = verdict([_rung(200.0, 100.0, ratio=3.2644)])
    assert out["transfers_to_ab_scene"] is False
    assert "68" in out["ab_scene_blocked_by"]


def test_isolation_matches_the_ratio_measurement():
    """The ESS run and D-266's ratio run must be the same configuration."""
    assert ess_at_peak.ISOLATION == {"w_risk": 0.0, "k_margin_per_sigma": 0.0}
