# SPDX-License-Identifier: BSD-3-Clause
"""Q-044 / D-023 — what a simulation-free scene screen may assume about timing.

D-022 falsified `nominal_traversal`: the closed loop does not walk the
reference at `target_speed_mps`, and since a hazard is a rendezvous in time,
`exposure.py`'s `contested_fraction` inherits the whole error. Q-044 listed
three ways out — (a) drive the screen from a realized trajectory (correct, one
simulation per scene, no longer a screen), (b) keep the declared nominal and
carry the error bar in the artifact, (c) retire simulation-free scene screens.

This file is (b), taken seriously enough to find out what it costs. The band is
a **one-parameter** perturbation — same polyline, same actor schedules on their
own absolute clock, only the traversal duration scaled — which is exactly what
D-022 measured and no more.

Three things are pinned, in increasing order of how much they hurt:

**1. The band constant is measurement, not judgement.** `TIMING_RATIO_BAND` is
re-derived here from live simulations of the obstacle-carrying scenes, so it
cannot drift away from the controller that produced it.

**2. Static scenes are exempt, exactly.** With nothing moving, `contested_s`
and `traversal_s` scale together, so the band has width 0 and the point
estimate keeps full authority. The screen degrades in proportion to actor
motion — not uniformly, and not to zero.

**3. On the moving-obstacle scenes the screen loses almost all ordering
authority.** Nine of the ten pairs overlap, and the single survivor involves
`cafe_cut_in_v0`, which is unreportable anyway. In particular D-018's cited
**74 % vs 43 %** becomes `[22 %, 83 %]` vs `[15 %, 65 %]` — not citable. This is
the honest cost of (b), and the reason this file states it as a test rather
than a docstring: a future cycle that tightens the band will see these flip.

None of D-018's *refutation* inverts — that rested on a controlled intervention
whose windows did not follow the exposure, and a screen that cannot even order
the pair is worse news for exposure-as-predictor, not better.
"""

from __future__ import annotations

import glob

import numpy as np
import pytest

from eval.mppi_sandbox import exposure as exp
from eval.mppi_sandbox.ab import ROBOT_RADIUS
from eval.mppi_sandbox.calibrate_lam import is_scenario_yaml
from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.run import simulate
from eval.mppi_sandbox.scenario import load_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
CONVOY = "eval/scenarios/cafe_convoy_v0.yaml"

#: The scene whose 15x ratio is a non-completion, not a timing error (Q-037).
DEFECT_SCENE = "eval/scenarios/cafe_cut_in_v0.yaml"

_CACHE: dict = {}


def _scenario_paths() -> list[str]:
    return [p for p in sorted(glob.glob("eval/scenarios/*.yaml"))
            if is_scenario_yaml(p)]


def _obstacle_scenes() -> list[str]:
    """Scenes where exposure is even defined. An obstacle-free scene has no
    rendezvous to mis-time, so it must not vote on the band."""
    return [p for p in _scenario_paths() if load_scenario(p).obstacles]


def _duration_ratio(path: str) -> float:
    """Measured closed-loop / nominal duration. Cached — five sims total."""
    if path not in _CACHE:
        scen = load_scenario(path)
        ctrl = make_controller("risk_mppi", scen, seed=0,
                               robot_radius=ROBOT_RADIUS)
        _CACHE[path] = (float(simulate(scen, ctrl)[-1, 0])
                        / float(exp.nominal_traversal(scen)[-1, 0]))
    return _CACHE[path]


@pytest.mark.slow
class TestTheBandConstantIsMeasured:
    """`TIMING_RATIO_BAND` must keep matching the plant it was read off."""

    def test_reportable_scenes_land_inside_the_declared_band(self):
        ratios = {p: _duration_ratio(p) for p in _obstacle_scenes()
                  if p != DEFECT_SCENE}
        lo, hi = exp.TIMING_RATIO_BAND
        assert min(ratios.values()) == pytest.approx(lo, abs=0.05), ratios
        assert max(ratios.values()) == pytest.approx(hi, abs=0.05), ratios

    def test_the_band_straddles_one_in_both_directions(self):
        """Not a correctable bias. If a future change made every scene err the
        same way, a scalar correction would be the right fix instead of a
        band — this is the test that would notice."""
        ratios = [_duration_ratio(p) for p in _obstacle_scenes()
                  if p != DEFECT_SCENE]
        assert min(ratios) < 0.8 < 1.25 < max(ratios), ratios

    def test_the_15x_outlier_is_the_non_completing_scene(self):
        """Why the band excludes it. Folding a scene defect into a timing
        error bar would widen the band ~27x on a scene no result may cite."""
        assert _duration_ratio(DEFECT_SCENE) > 10.0
        assert exp.TIMING_RATIO_BAND_WITH_DEFECT[1] >= _duration_ratio(DEFECT_SCENE)
        assert exp.TIMING_RATIO_BAND[1] < 3.0

    def test_obstacle_free_scenes_do_not_vote(self):
        """Three of the eight scenes have no obstacles, so their traversal
        timing says nothing about a rendezvous."""
        assert len(_obstacle_scenes()) == 5
        assert len(_scenario_paths()) == 8


class TestStaticScenesAreExemptExactly:
    """The one place the screen keeps full authority — and it is exact."""

    @staticmethod
    def _scen_with(obstacles):
        scen = load_scenario(CROSSING)
        scen.obstacles = obstacles
        return scen

    def test_static_obstacles_give_a_scale_invariant_fraction(self):
        """Analytic claim, checked numerically: with nothing moving, both
        `contested_s` and `traversal_s` scale with the duration ratio."""
        static = [CircleObstacle(x=float(x), y=float(y), radius=0.3)
                  for x, y in np.asarray(
                      load_scenario(CROSSING).waypoints, float)[1:4, :2]]
        scen = self._scen_with(static)
        fracs = []
        for r in np.geomspace(*exp.TIMING_RATIO_BAND, 9):
            traj = exp.nominal_traversal(scen, duration_ratio=float(r))
            clear = exp.clearance_matrix(traj, scen.obstacles)
            contested = (clear < exp.CONTEST_RADIUS).any(axis=1)
            fracs.append(contested.sum() / len(contested))
        assert max(fracs) - min(fracs) < 0.01, fracs
        assert max(fracs) > 0.0, "degenerate — the static obstacles never contest"

    def test_a_moving_scene_is_not_scale_invariant(self):
        """The contrast that makes the previous test mean something."""
        assert exp.exposure_band(CROSSING).width > 0.3

    def test_obstacle_free_scene_reports_zero_width(self):
        band = exp.exposure_band("eval/scenarios/cafe_straight_v0.yaml")
        assert band.n_obstacles == 0
        assert not band.is_timing_sensitive


@pytest.mark.slow
class TestTheBandCostsTheOrdering:
    """What (b) actually buys and what it destroys."""

    def test_d018_headline_pair_no_longer_separates(self):
        """The specific claim this cycle retires. 74 % vs 43 % read off the
        nominal; the intervals overlap, so the screen may not order them."""
        crossing, convoy = exp.exposure_band(CROSSING), exp.exposure_band(CONVOY)
        assert crossing.point == pytest.approx(0.74, abs=0.02)
        assert convoy.point == pytest.approx(0.43, abs=0.02)
        assert not crossing.separates(convoy), (
            f"the D-018 pair separates again ({crossing}, {convoy}) — if the "
            f"band was legitimately tightened, D-018's contested-fraction "
            f"reading may be citable once more")

    def test_the_nominal_point_lies_inside_its_own_band(self):
        """Sanity: ratio 1.0 is in the band, so this holds for every scene or
        the grid is not covering what it claims to."""
        for p in _scenario_paths():
            b = exp.exposure_band(p)
            assert b.lo - 1e-9 <= b.point <= b.hi + 1e-9, b

    def test_almost_every_moving_pair_is_refused(self):
        """The blunt cost. 10 pairs over the 5 obstacle scenes, 1 survives."""
        bands, incomparable = exp.rank_with_band(_obstacle_scenes())
        assert len(bands) == 5
        assert len(incomparable) == 9, [f"{a}~{b}" for a, b in incomparable]

    def test_the_one_surviving_pair_involves_the_unreportable_scene(self):
        """So the usable ordering authority is effectively zero — stated as a
        test because it is the finding, not a caveat."""
        bands, incomparable = exp.rank_with_band(_obstacle_scenes())
        refused = {frozenset(p) for p in incomparable}
        survivors = [frozenset((a.scenario, b.scenario))
                     for i, a in enumerate(bands) for b in bands[i + 1:]
                     if frozenset((a.scenario, b.scenario)) not in refused]
        assert len(survivors) == 1, survivors
        assert "cafe_cut_in_v0.yaml" in set(survivors[0])

    def test_endpoints_alone_would_understate_the_band(self):
        """Why `BAND_GRID` is 41 and not 2: `contested_fraction` is not
        monotone in the duration ratio, so the interior carries the max."""
        lo_r, hi_r = exp.TIMING_RATIO_BAND
        ends = [exp.hazard_exposure(CROSSING, duration_ratio=r).contested_fraction
                for r in (lo_r, hi_r)]
        assert exp.exposure_band(CROSSING).hi > max(ends) + 0.05


class TestNothingElseMoved:
    """The screen's shipped behaviour is unchanged; only its reporting grew."""

    def test_default_traversal_is_untouched(self):
        scen = load_scenario(CROSSING)
        assert np.array_equal(exp.nominal_traversal(scen),
                              exp.nominal_traversal(scen, duration_ratio=1.0))

    def test_point_screen_still_returns_a_total_order(self):
        """`screen_scenarios` is left alone deliberately — D-018's numbers
        stay reproducible, they just stop being citable on their own."""
        ranked = exp.screen_scenarios(_obstacle_scenes())
        fracs = [e.contested_fraction for e in ranked]
        assert fracs == sorted(fracs, reverse=True)
        assert ranked[0].scenario == "cafe_cut_in_v0.yaml"
