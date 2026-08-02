# SPDX-License-Identifier: BSD-3-Clause
"""Q-039 — is a single-`lam` two-arm A/B admissible at all?

18:00 measured `cafe_obstacle_crossing_v0` with disjoint per-controller
windows (`stock_mppi` [0.4, 0.8], `risk_mppi` [1.6, 3.2]) while every A/B on
this branch reports both arms at one temperature. These tests pin the answer
in two halves:

  * **structural** — the pair-level verdict read off the calibration table,
    and the guard that refuses a single-`lam` report when no rung serves both
    arms. Free: no simulation, table only.
  * **empirical** — what the protocol choice actually costs. The measured
    answer is the useful one: the *direction* of the risk-vs-stock clearance
    delta survives every protocol, but its *magnitude* does not, because the
    out-of-band arm is not running its intended update. So a single-`lam` A/B
    on a disjoint-window scene is admissible for a sign claim and inadmissible
    for an effect-size claim — which is what #67/#68/#69's headlines are.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.scenario import load_scenario

ARMS = ("stock_mppi", "risk_mppi")
CROSSING = "cafe_obstacle_crossing_v0.yaml"

#: The whole calibratable matrix, partitioned by pair-level verdict. Strict
#: set equalities, per the 17:00 precedent: a coverage claim that only checks
#: its own examples cannot notice a scene drifting into the bad class.
EXPECTED_VERDICTS = {
    "shared": {
        "cafe_convoy_v0.yaml", "cafe_freezing_v0.yaml", "cafe_head_on_v0.yaml",
        "cafe_straight_v0.yaml", "city_curved_v0.yaml", "city_figure8_v0.yaml",
    },
    "per_arm": {CROSSING},
    "unreportable": {"cafe_cut_in_v0.yaml"},
}


@pytest.fixture(scope="module")
def windows():
    from eval.mppi_sandbox.calibrate_lam import load_windows
    return load_windows()


# --- structural: the verdict and the guard -----------------------------------

def test_matrix_partitions_into_three_protocol_classes(windows):
    """Every calibrated scene resolves to exactly one verdict, and the
    partition is what the table says — not what the examples below assume."""
    scenes = sorted({s for s, _ in windows})
    got: dict[str, set[str]] = {v: set() for v in ("shared", "per_arm",
                                                   "unreportable")}
    for scene in scenes:
        got[ab.ab_temperature(scene, ARMS, windows).verdict].add(scene)
    assert got == EXPECTED_VERDICTS
    assert set(scenes) == set().union(*EXPECTED_VERDICTS.values())


def test_crossing_scene_has_two_calibrated_arms_and_no_shared_rung(windows):
    """The Q-039 shape, distinguished from the Q-035 one: *both* arms
    calibrate — the pair is what fails, not either cell."""
    t = ab.ab_temperature(CROSSING, ARMS, windows)
    assert t.per_arm == {"stock_mppi": (0.4, 0.8), "risk_mppi": (1.6, 3.2)}
    assert all(w for w in t.per_arm.values()), "both cells are calibratable"
    assert t.shared == ()
    assert t.verdict == "per_arm"
    assert not t.single_lam_admissible


def test_lam_for_minimises_the_temperature_gap(windows):
    """A per-arm protocol trades the band for a temperature confound bounded
    by the gap, so the rung choice must minimise it: 0.8/1.6 (2x), never the
    equally admissible 0.4/3.2 (8x)."""
    t = ab.ab_temperature(CROSSING, ARMS, windows)
    assert (t.lam_for("stock_mppi"), t.lam_for("risk_mppi")) == (0.8, 1.6)
    assert t.lam_gap == pytest.approx(2.0)


def test_shared_scene_reports_gap_of_one(windows):
    t = ab.ab_temperature("cafe_head_on_v0.yaml", ARMS, windows)
    assert t.verdict == "shared" and t.shared == (0.2, 0.4, 0.8)
    assert t.single_lam_admissible
    assert t.lam_gap == pytest.approx(1.0)
    assert t.lam_for("stock_mppi") == t.lam_for("risk_mppi")


def test_assert_single_lam_ab_accepts_a_shared_rung(windows):
    ab.assert_single_lam_ab("cafe_head_on_v0.yaml", ARMS, 0.4, windows)


def test_assert_single_lam_ab_rejects_disjoint_windows(windows):
    """The guard Q-039 asks for, and the case every A/B on this branch ran."""
    with pytest.raises(AssertionError, match="no shared admissible"):
        ab.assert_single_lam_ab(CROSSING, ARMS, 0.4, windows)
    # …including the rung admissible for the *other* arm — neither is shared.
    with pytest.raises(AssertionError, match="no shared admissible"):
        ab.assert_single_lam_ab(CROSSING, ARMS, 1.6, windows)


def test_assert_single_lam_ab_names_the_per_arm_alternative(windows):
    """A guard that only refuses is a guard people delete."""
    with pytest.raises(AssertionError) as e:
        ab.assert_single_lam_ab(CROSSING, ARMS, 0.4, windows)
    msg = str(e.value)
    assert "stock_mppi=0.8" in msg and "risk_mppi=1.6" in msg
    assert "gap 2.0x" in msg


def test_off_window_rung_is_rejected_even_when_a_shared_one_exists(windows):
    with pytest.raises(AssertionError, match="outside the shared admissible"):
        ab.assert_single_lam_ab("cafe_head_on_v0.yaml", ARMS, 6.4, windows)


def test_uncalibratable_scene_is_unreportable_not_per_arm(windows):
    """`cafe_cut_in_v0` fails one level up (Q-035): no protocol exists, so
    there is no rung to recommend and `lam_for` must refuse rather than
    invent one."""
    t = ab.ab_temperature("cafe_cut_in_v0.yaml", ARMS, windows)
    assert t.verdict == "unreportable"
    with pytest.raises(ValueError, match="empty admissible window"):
        t.lam_for("stock_mppi")
    with pytest.raises(AssertionError, match="empty admissible window"):
        ab.assert_single_lam_ab("cafe_cut_in_v0.yaml", ARMS, 0.4, windows)


def test_uncalibrated_cell_raises_rather_than_defaulting(windows):
    with pytest.raises(KeyError, match="no calibration cell"):
        ab.ab_temperature(CROSSING, ("stock_mppi", "vg_mppi"), windows)


# --- empirical: what the protocol choice actually costs ----------------------

#: CI seed count. 4, not the 8 the finding was measured at: the protocols
#: differ by ~1.8x here and the assertion floor is 1.25x, so the reproduction
#: has margin without paying twice for it.
CI_SEEDS = range(4)

_SWEEPS: dict[tuple[str, float], list] = {}


def _sweep(arm: str, lam: float):
    """Memoized per-(arm, lam) sweep — the three protocols under test share
    four of their six arms, and re-simulating them is the whole cost of this
    file."""
    key = (arm, lam)
    if key not in _SWEEPS:
        scene = load_scenario(f"eval/scenarios/{CROSSING}")
        _SWEEPS[key] = ab.seed_sweep(scene, arm, CI_SEEDS,
                                     params=MPPIParams(lam=lam))
    return _SWEEPS[key]


def _paired(lam_stock: float, lam_risk: float):
    a, b = _sweep("stock_mppi", lam_stock), _sweep("risk_mppi", lam_risk)
    return a, b, ab.paired_delta(b, a)


def test_protocol_moves_the_effect_size_but_not_its_sign():
    """The measured answer to Q-039.

    Same scene, same seeds, same arms — only the temperature protocol differs.
    The single-`lam` run puts `risk_mppi` well below the ESS floor, where its
    update is near-argmin over K draws, and that **inflates** the clearance
    gap it is credited with. Measured at 8 seeds: +0.096 m single-`lam` vs
    +0.049 m per-arm, a 1.9x overstatement; the 4-seed CI reproduction below
    holds the same shape. The sign is 7-8 of 8 favouring `risk_mppi` under
    every protocol.

    So: a disjoint-window scene may carry a *direction* claim at one
    temperature and may not carry a *magnitude* one, which is the distinction
    the re-baseline has to apply to #67/#68/#69.
    """
    a_lo, b_lo, d_single = _paired(0.4, 0.4)   # stock's rung, risk out of band
    a_pa, b_pa, d_perarm = _paired(0.8, 1.6)   # the Q-039 protocol

    # Only the per-arm protocol has both arms executing their intended update.
    assert not ab.summarize(b_lo).ess_in_band, "risk is out of band at 0.4"
    assert ab.summarize(a_pa).ess_in_band and ab.summarize(b_pa).ess_in_band
    for runs in (a_lo, b_lo, a_pa, b_pa):
        assert ab.summarize(runs).all_reached

    # Sign survives the protocol …
    for d in (d_single, d_perarm):
        favours_risk, favours_stock, _ = ab.sign_counts(d)
        assert favours_risk > favours_stock
        assert float(d.mean()) > 0

    # … magnitude does not, and the out-of-band arm is the flattered one.
    assert float(d_single.mean()) > 1.25 * float(d_perarm.mean())


def test_in_band_protocols_agree_more_closely_than_the_out_of_band_one():
    """Corroboration that the spread is the *band exit*, not seed noise: the
    two protocols in which `risk_mppi` runs in band (per-arm 0.8/1.6 and the
    single rung 1.6) agree far better with each other than either does with
    the protocol that runs it below the floor."""
    m_single_lo = float(_paired(0.4, 0.4)[2].mean())
    m_single_hi = float(_paired(1.6, 1.6)[2].mean())
    m_perarm = float(_paired(0.8, 1.6)[2].mean())

    in_band_spread = abs(m_single_hi - m_perarm)
    out_of_band_gap = abs(m_single_lo - m_perarm)
    assert in_band_spread < out_of_band_gap
    assert np.sign(m_single_lo) == np.sign(m_perarm) == np.sign(m_single_hi)
