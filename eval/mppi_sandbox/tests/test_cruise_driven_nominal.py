# SPDX-License-Identifier: BSD-3-Clause
"""D-025 — drive the simulation-free screen off an input the loop reads.

The chain this closes: D-022 falsified `nominal_traversal`; D-023 had to wrap
`exposure.py` in a timing band because of it; D-024 found the reason — the
band's driver, `target_speed_mps`, is a yaml field the closed loop **never
reads**, so the whole error bar was drawn around a declaration. What the loop
does read is `v_max` and `w_terminal / w_speed`, and both are available without
simulating anything.

What these tests pin, in order of how much they constrain future cycles:

**1. The replacement is measured, not asserted.** `CRUISE_SPEED_MPS` and
`TIMING_RATIO_BAND_CRUISE` are re-derived here from live runs, so neither can
drift away from the plant it was read off.

**2. The improvement is real and bounded.** Swapping the driver narrows the
band 3.866x -> 2.320x at identical (zero) simulation cost. It does **not**
close it.

**3. The floor is exact, and it is the load-bearing result.** Band width under
a scene-independent driver is scale-invariant in the driving speed — the
constant cancels out of `max / min` algebraically. So 2.320x is a property of
the scene set, not a score for this particular constant, and a future cycle
that tunes `CRUISE_SPEED_MPS` hoping to narrow the band is guaranteed to fail.
`test_band_width_is_scale_invariant_in_the_driver` exists to make that
guarantee cost one test run instead of one cycle.

**4. Beating the floor costs a simulation.** Per-scene measured cruise reaches
~1.66x, which is exactly Q-044 option (a) — the one D-023 rejected because it
stops being a screen. Recorded so the trade-off stays visible rather than being
rediscovered as a surprise.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox import exposure as exp
from eval.mppi_sandbox import speed_audit as sa
from eval.mppi_sandbox.scenario import load_scenario

#: The scenes `TIMING_RATIO_BAND` was taken over — obstacle-carrying and
#: reportable. `cafe_cut_in_v0` is excluded for the D-023 reason (it never
#: completes; Q-037 ruled that a scene defect), not for convenience.
REPORTABLE = ("cafe_obstacle_crossing_v0", "cafe_convoy_v0",
              "cafe_freezing_v0", "cafe_head_on_v0")

SEEDS = range(4)
_CACHE: dict[str, tuple[float, float, float]] = {}


def _scene(name):
    return load_scenario(f"eval/scenarios/{name}.yaml")


def _measured(name: str) -> tuple[float, float, float]:
    """`(closed_loop_s, path_length_m, measured_cruise_mps)`, memoised."""
    if name not in _CACHE:
        scen = _scene(name)
        runs = ab.seed_sweep(scen, "risk_mppi", SEEDS)
        _CACHE[name] = (
            float(np.median([r.traj[-1, 0] for r in runs])),
            exp.path_length(scen),
            float(np.nanmedian([sa.cruise_speed(r.traj, scen) for r in runs])),
        )
    return _CACHE[name]


def _width(ratios) -> float:
    return float(max(ratios) / min(ratios))


class TestDriverIsSwappable:
    def test_default_is_bit_identical(self):
        """`speed_mps=None` must leave every pre-D-025 caller untouched."""
        for name in REPORTABLE:
            scen = _scene(name)
            assert np.array_equal(
                exp.nominal_traversal(scen),
                exp.nominal_traversal(scen, speed_mps=None))

    def test_explicit_declared_speed_reproduces_the_default(self):
        scen = _scene("cafe_convoy_v0")
        assert np.array_equal(
            exp.nominal_traversal(scen),
            exp.nominal_traversal(scen, speed_mps=scen.target_speed))

    def test_cruise_traversal_ignores_the_declared_speed(self):
        """The point of D-025: two scenes declaring different speeds get the
        same clock, because the controller gives them the same clock."""
        a, b = _scene("cafe_obstacle_crossing_v0"), _scene("cafe_convoy_v0")
        assert a.target_speed != b.target_speed
        speeds = [exp.path_length(s) / float(exp.cruise_traversal(s)[-1, 0])
                  for s in (a, b)]
        assert speeds[0] == pytest.approx(speeds[1], rel=1e-3)

    def test_duration_ratio_still_composes(self):
        scen = _scene("cafe_head_on_v0")
        base = float(exp.cruise_traversal(scen)[-1, 0])
        for r in (0.5, 1.0, 2.0):
            got = float(exp.cruise_traversal(scen, duration_ratio=r)[-1, 0])
            assert got == pytest.approx(base * r, rel=0.02)


class TestCalibrationMatchesThePlant:
    def test_cruise_speed_constant_is_current(self):
        """`CRUISE_SPEED_MPS` re-derived from a live run at shipped `v_max`."""
        scen = _scene("cafe_obstacle_crossing_v0")
        got = sa.speed_response(scen, "stock_mppi", SEEDS, v_max=0.8)
        assert got.cruise_speed == pytest.approx(exp.CRUISE_SPEED_MPS, rel=0.05)

    def test_vmax_binds_below_the_knee_and_the_weight_ratio_above(self):
        """The structure that makes the constant a *controller* property.

        Below the knee cruise tracks `v_max`; above it, cruise stops moving —
        0.8 and 1.2 agree despite a 1.5x change in the limit. That is what
        licenses calibrating once instead of per scene.
        """
        scen = _scene("cafe_obstacle_crossing_v0")
        got = {vm: sa.speed_response(scen, "stock_mppi", SEEDS,
                                     v_max=vm).cruise_speed
               for vm in (0.6, 0.8, 1.2)}
        assert got[0.6] == pytest.approx(0.6, rel=0.05)          # v_max binds
        assert got[1.2] == pytest.approx(got[0.8], rel=0.05)     # ratio binds
        assert got[0.8] < 0.8                                    # and it is a cap

    def test_calibrated_cruise_interpolates_and_refuses_to_extrapolate(self):
        for vm, want in sa.CRUISE_BY_VMAX.items():
            assert sa.calibrated_cruise(vm) == pytest.approx(want)
        mid = sa.calibrated_cruise(0.7)
        assert sa.CRUISE_BY_VMAX[0.60] < mid < sa.CRUISE_BY_VMAX[0.80]
        for bad in (0.2, 2.0):
            with pytest.raises(ValueError, match="calibrated range"):
                sa.calibrated_cruise(bad)


class TestTheBandActuallyNarrows:
    def test_cruise_driver_beats_declared_driver(self):
        """The headline claim, re-derived live on both drivers."""
        declared, cruise = [], []
        for name in REPORTABLE:
            cl, length, _ = _measured(name)
            declared.append(cl / (length / float(_scene(name).target_speed)))
            cruise.append(cl / (length / exp.CRUISE_SPEED_MPS))
        assert _width(declared) == pytest.approx(3.866, rel=0.10)
        assert _width(cruise) == pytest.approx(
            exp.SCENE_INDEPENDENT_BAND_WIDTH, rel=0.10)
        assert _width(cruise) < _width(declared) / 1.5

    def test_cruise_band_constant_is_current(self):
        lo, hi = exp.TIMING_RATIO_BAND_CRUISE
        ratios = [cl / (length / exp.CRUISE_SPEED_MPS)
                  for cl, length, _ in map(_measured, REPORTABLE)]
        assert min(ratios) == pytest.approx(lo, rel=0.10)
        assert max(ratios) == pytest.approx(hi, rel=0.10)

    def test_cruise_band_error_is_one_directional(self):
        """Every scene reads > 1 — the closed loop is never *faster* than a
        pure-cruise walk, because it pays a transient, a ramp and a detour.

        The declared band straddled 1.0, so its error had no sign; this one
        does, which is what makes it a bias rather than noise.
        """
        ratios = [cl / (length / exp.CRUISE_SPEED_MPS)
                  for cl, length, _ in map(_measured, REPORTABLE)]
        assert min(ratios) > 1.0
        assert min(exp.TIMING_RATIO_BAND) < 1.0 < max(exp.TIMING_RATIO_BAND)


class TestTheFloorIsExact:
    def test_band_width_is_scale_invariant_in_the_driver(self):
        """**No constant speed can narrow this band.**

        `ratio_i = closed_loop_i * c / length_i`, so `c` cancels out of
        `max / min` exactly. Checked over a 2.4x sweep of the driver, which
        also covers the value D-024 quoted (0.709) and the shipped one.
        """
        widths = []
        for c in (0.5, 0.709, 0.8, 1.2):
            widths.append(_width([cl * c / length
                                  for cl, length, _ in map(_measured, REPORTABLE)]))
        assert max(widths) == pytest.approx(min(widths), rel=1e-9)
        assert widths[0] == pytest.approx(exp.SCENE_INDEPENDENT_BAND_WIDTH,
                                          rel=0.10)

    def test_beating_the_floor_requires_a_per_scene_simulation(self):
        """Per-scene measured cruise gets under the floor — and is Q-044 (a).

        Recorded, not adopted: it costs one sim per scene, which is exactly the
        property D-023 rejected the option for. The test's job is to keep the
        price tag attached to the number.
        """
        per_scene = [cl / (length / cruise)
                     for cl, length, cruise in map(_measured, REPORTABLE)]
        assert _width(per_scene) < exp.SCENE_INDEPENDENT_BAND_WIDTH
        assert _width(per_scene) == pytest.approx(1.66, rel=0.15)
