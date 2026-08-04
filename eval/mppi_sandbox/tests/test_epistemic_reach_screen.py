# SPDX-License-Identifier: BSD-3-Clause
"""STATE #1 — the directional reach screen, and the timing model it falsifies.

D-021 pinned rollout reach as the gate on the epistemic channel and refuted the
*scalar* form of that gate using its own data ("live iff max reach >= nearest
unseen cell" holds on 28 of 92 crossing-scene steps where the measured spread
is still exactly zero). `reach.py` is the directional replacement: it builds the
actual MPPI fan and computes the per-sample cost **spread** — the quantity the
softmax can see, since a constant cancels exactly.

Two results, and the second is the one worth carrying.

**1. The geometry model is exact.** Driven from the measured closed-loop states
and times, `reach_on_trajectory` reproduces D-021's verdicts to the step:
`0/92` live at the shipped `H = 30`, and the wake at `H = 60`. Same code, same
fan, same field.

**2. The *nominal-traversal timing model* is falsified, and it is shared.**
Driven from `nominal_traversal` the identical computation reads `5/35` live on
that same scene. The error is entirely in the pose sequence, and it is not
subtle: the closed loop finishes `cafe_obstacle_crossing_v0` in **9.2 s against
a 16.7 s nominal**, so the nominal robot is in the wrong place at every instant
a scheduled actor casts a shadow. Across the eight-scene matrix the
closed-loop / nominal duration ratio spans **0.56x to 15x, in both
directions**.

That last point reaches past this module. `exposure.py` is built on the same
`nominal_traversal`, and its contested-fraction statistic — the one D-018 used
to compare `cafe_obstacle_crossing_v0` (74%) against `cafe_convoy_v0` (43%) —
is computed for those two scenes under timing that is wrong by **0.56x and
1.63x respectively**, i.e. a ~2.9x relative skew between exactly the pair the
statistic exists to separate. D-018 already refuted exposure as a *predictor*
on a controlled intervention, so no live conclusion inverts here; what changes
is the recorded reading that it survives as a cheap screen. Its own docstring
states the standard it fails: "the hazard is a rendezvous, not a place."

A third, smaller correction: D-021's closing clause attributes the crossing
scene's short epistemic reach to `target_speed_mps: 0.3`. The controller does
not track that setting — the measured plan speed is 0.36 m/s and the realized
traversal 0.54 m/s — so the *attribution* is unsupported even though the
measured reach it explains is not in question.
"""

from __future__ import annotations

import glob

import numpy as np
import pytest

from eval.mppi_sandbox import reach
from eval.mppi_sandbox.calibrate_lam import is_scenario_yaml
from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.exposure import nominal_traversal
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.reach import (epistemic_reach, nominal_poses,
                                     reach_on_trajectory, rollout_fan,
                                     screen_scenarios)
from eval.mppi_sandbox.representations import GTBevProducer, RiskChannel
from eval.mppi_sandbox.run import ROBOT_RADIUS, simulate
from eval.mppi_sandbox.scenario import load_scenario
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
SHIPPED_HORIZON = MPPIParams().horizon          # 30 — read, not hard-coded

_CACHE: dict = {}


def _scenario_paths() -> list[str]:
    return [p for p in sorted(glob.glob("eval/scenarios/*.yaml"))
            if is_scenario_yaml(p)]


def _crossing():
    if "crossing" not in _CACHE:
        _CACHE["crossing"] = load_scenario(CROSSING)
    return _CACHE["crossing"]


def _closed_loop(horizon: int) -> np.ndarray:
    """Measured trajectory of the same arm D-021 traced. Memoized — this is
    the only simulation in the file and it is paid twice."""
    key = ("traj", horizon)
    if key not in _CACHE:
        ctrl = make_controller("risk_mppi", _crossing(), seed=0,
                               robot_radius=ROBOT_RADIUS,
                               params=MPPIParams(horizon=horizon),
                               w_epist=200.0, w_risk=0.0,
                               k_margin_per_sigma=0.0)
        _CACHE[key] = simulate(_crossing(), ctrl)
    return _CACHE[key]


def _measured(horizon: int):
    key = ("profile", horizon)
    if key not in _CACHE:
        _CACHE[key] = reach_on_trajectory(_crossing(), _closed_loop(horizon),
                                          horizon=horizon)
    return _CACHE[key]


@pytest.mark.slow
class TestTheGeometryModelReproducesTheMeasurement:
    """Driven from the measured trajectory, the screen *is* D-021's trace."""

    def test_dead_at_the_shipped_horizon(self):
        """The headline D-021 measured closed-loop, recomputed by an
        independent path: a fan built from `dynamics.step` and a σ field from
        `GTBevProducer`, with no controller in the loop."""
        r = _measured(SHIPPED_HORIZON)
        assert r.n_steps > 50, "run ended early — profile is not representative"
        assert r.live_steps == 0, (
            f"reach_on_trajectory now finds {r.live_steps}/{r.n_steps} live "
            f"steps at H={SHIPPED_HORIZON} where D-021 measured 0/92 — either "
            f"the crossing scene left the signal-free class or the fan model "
            f"has drifted from StockMPPI.command")
        assert r.max_spread == 0.0

    def test_raising_the_horizon_wakes_it(self):
        """Direction A of D-018's intervention, on the screen rather than on
        the controller. Without this arm the file would only show that the
        screen agrees with one number."""
        woken = _measured(2 * SHIPPED_HORIZON)
        assert woken.live_steps > 0, (
            f"H={2 * SHIPPED_HORIZON} no longer wakes the term "
            f"(measured 121/240 closed-loop) — reach is not the gate")
        assert woken.max_spread > 0.0

    def test_the_field_is_rendered_not_absent(self):
        """Rules out the vacuous reading, same as D-021's own check: the
        ignorance exists and is out of the fan's reach.

        Asserted on `scene_unseen`, not `grid_unseen`. The old bar
        (`grid_unseen > 0.05`) was stated against an unsubtracted floor of
        `0.027`, so what it actually demanded of the *scene* was `0.023` — and
        the accompanying `> 0.0` form of this same check in
        `test_epistemic_reach_gate.py` could not fail at all, since an empty
        world clears it.
        """
        r = _measured(SHIPPED_HORIZON)
        assert r.renders_ignorance, (
            "the crossing scene stopped casting shadows — the signal-free "
            "finding would be vacuous rather than true")
        assert r.scene_unseen > 0.05, (
            f"scene-attributable ignorance fell to {r.scene_unseen:.3f} "
            f"(grid {r.grid_unseen:.3f} - floor {r.unseen_floor:.3f})")


@pytest.mark.slow
class TestTheNominalTimingModelIsFalsified:
    """The screen's cheap driver disagrees, and the cause is measurable."""

    def test_nominal_driver_disagrees_with_the_measurement(self):
        """Pinned as a *known defect*, not as a contract. If a future cycle
        fixes the timing model this test is what tells it the fix landed."""
        nominal = epistemic_reach(CROSSING, horizon=SHIPPED_HORIZON)
        assert nominal.live_steps > 0, (
            "the nominal driver now agrees with the measurement on the "
            "crossing scene — if that is a deliberate fix to the timing "
            "model, retire this test and the module docstring's caveat")
        assert _measured(SHIPPED_HORIZON).live_steps == 0

    def test_closed_loop_duration_departs_from_nominal_on_every_scene(self):
        """The root cause, measured across the matrix rather than argued from
        one scene. The ratio is not a small bias to correct — it spans both
        sides of 1 and more than an order of magnitude."""
        ratios = {}
        for path in _scenario_paths():
            scen = load_scenario(path)
            key = ("dur", path)
            if key not in _CACHE:
                ctrl = make_controller("risk_mppi", scen, seed=0,
                                       robot_radius=ROBOT_RADIUS)
                _CACHE[key] = float(simulate(scen, ctrl)[-1, 0])
            ratios[scen.name] = _CACHE[key] / float(nominal_traversal(scen)[-1, 0])

        assert min(ratios.values()) < 0.8, (
            f"no scene now finishes materially faster than nominal: {ratios}")
        assert max(ratios.values()) > 1.5, (
            f"no scene now finishes materially slower than nominal: {ratios}")

    def test_the_two_scenes_d018_compared_are_skewed_in_opposite_directions(self):
        """The specific consequence for `exposure.py`. D-018 read a 74% vs 43%
        contested fraction off `nominal_traversal` for these two scenes; their
        timing errors point opposite ways, so the *gap* is inflated by the
        model before any geometry enters."""
        def _ratio(name: str) -> float:
            scen = load_scenario(f"eval/scenarios/{name}.yaml")
            key = ("dur", f"eval/scenarios/{name}.yaml")
            if key not in _CACHE:
                ctrl = make_controller("risk_mppi", scen, seed=0,
                                       robot_radius=ROBOT_RADIUS)
                _CACHE[key] = float(simulate(scen, ctrl)[-1, 0])
            return _CACHE[key] / float(nominal_traversal(scen)[-1, 0])

        crossing, convoy = _ratio("cafe_obstacle_crossing_v0"), _ratio("cafe_convoy_v0")
        assert crossing < 1.0 < convoy, (
            f"the two scenes' timing errors no longer straddle 1 "
            f"(crossing {crossing:.2f}, convoy {convoy:.2f}) — exposure.py's "
            f"contested-fraction comparison may be recoverable; re-check "
            f"D-018's reading before citing it")
        assert max(convoy / crossing, crossing / convoy) > 2.0

    def test_the_controller_does_not_track_target_speed(self):
        """D-021's closing attribution, checked. `target_speed_mps: 0.3` was
        set to "give MPPI room to dodge"; the realized traversal is ~1.8x
        that, so the setting does not explain the scene's short reach even
        though the short reach itself is measured."""
        scen, traj = _crossing(), _closed_loop(SHIPPED_HORIZON)
        travelled = float(np.linalg.norm(np.diff(traj[:, 1:3], axis=0),
                                         axis=1).sum())
        realized = travelled / float(traj[-1, 0])
        assert realized > 1.3 * scen.target_speed, (
            f"realized speed {realized:.3f} m/s is now close to the "
            f"{scen.target_speed} m/s setting — D-021's speed attribution "
            f"may be recoverable")


class TestTheScreenIsDirectionalNotAScalar:
    """D-021 clause 4: distance cannot express the gate; direction can."""

    def test_a_shadow_behind_the_robot_fools_the_scalar_not_the_fan(self):
        """The constructed counterexample. An obstacle *behind* the start pose
        casts its shadow behind, well inside the fan's maximum reach — so the
        scalar's inequality holds — while no forward rollout point ever enters
        it, so the spread the softmax sees is exactly zero."""
        behind = _straight_scenario(obstacles=[CircleObstacle(0.0, 0.9, radius=0.35)])
        pose = nominal_poses(behind)[0]                 # at origin, heading -Y
        prod = GTBevProducer(behind.obstacles)
        bev = prod.render(pose[1:3], 0.0)
        fan = rollout_fan(pose, behind.target_speed, samples=reach.FAN_SAMPLES)

        unseen = bev.stack[RiskChannel.EPISTEMIC] > reach.UNSEEN_SIGMA
        assert unseen.any(), "the obstacle stopped casting a shadow"
        nearest = float(reach._grid_distances(prod, pose[1:3])[unseen].min())
        max_reach = float(np.linalg.norm(fan.reshape(-1, 2) - pose[1:3],
                                         axis=1).max())
        assert max_reach >= nearest, (
            f"fan reach {max_reach:.2f} m no longer covers the nearest unseen "
            f"cell at {nearest:.2f} m — the scalar is not fooled here any more "
            f"and this counterexample needs re-siting")

        sigma = bev.sample(RiskChannel.EPISTEMIC, fan.reshape(-1, 2),
                           unobserved_value=1.0)
        spread = float(np.ptp(sigma.reshape(reach.FAN_SAMPLES, -1).sum(axis=1)))
        assert spread == 0.0, (
            f"the directional screen reads spread {spread:.3f} on a shadow "
            f"that lies entirely behind the fan — it has stopped being "
            f"directional")

    def test_the_screen_undercounts_the_scalar_across_the_matrix(self):
        """Aggregate form of the same claim: on every scene the scalar calls
        at least as many steps live as the fan does, and strictly more on the
        scene D-021 pinned."""
        for r in _matrix():
            assert r.scalar_live_steps >= r.live_steps, (
                f"{r.scenario}: the scalar now *under*-counts "
                f"({r.scalar_live_steps} vs {r.live_steps}) — the two "
                f"criteria no longer nest and `scalar_false_positives` is "
                f"no longer meaningful")
        crossing = next(r for r in _matrix() if "crossing" in r.scenario)
        assert crossing.scalar_false_positives > 0


class TestScreenMechanics:
    def test_fan_is_warm_started_like_the_controller(self):
        """The fan must not re-derive the cloud in closed form — its geometry
        has to come from the same plant and the same noise, or it silently
        drifts when `MPPIParams` changes. Checked by moving `sigma_w` and
        watching the lateral spread follow."""
        pose = nominal_poses(_straight_scenario())[0]
        narrow = rollout_fan(pose, 0.4, params=MPPIParams(sigma_w=0.05),
                             limits=None, samples=64)
        wide = rollout_fan(pose, 0.4, params=MPPIParams(sigma_w=1.0),
                           limits=None, samples=64)
        assert np.ptp(wide[:, -1, 0]) > 3 * np.ptp(narrow[:, -1, 0])

    def test_fan_reaches_forward_not_backward(self):
        """The property the scalar threw away, as a direct assertion: driving
        along -Y, essentially the whole cloud is at negative Y."""
        pose = nominal_poses(_straight_scenario())[0]
        fan = rollout_fan(pose, 0.4, params=MPPIParams(), limits=None,
                          samples=256)
        assert (fan[..., 1] <= 1e-9).mean() > 0.99

    @pytest.mark.parametrize("samples", [128, 256])
    def test_screen_verdict_is_stable_in_fan_size(self, samples):
        """64 is a budget choice; the audible/deaf partition must not be one."""
        base = {r.scenario: r.audible for r in _matrix()}
        for r in screen_scenarios(_scenario_paths(), samples=samples):
            assert r.audible == base[r.scenario], (
                f"{r.scenario} flips audibility between 64 and {samples} "
                f"fan samples — the verdict is sampling noise, not geometry")

    def test_matrix_partitions_into_audible_and_deaf(self):
        """The deliverable STATE #1 asked for: which scenes can hear the
        channel at all. Obstacle-free scenes cannot — their only σ > 0 cells
        are the beyond-sensing-range grid corners, ~5 m out and unreachable."""
        rows = _matrix()
        assert len(rows) == 8, f"scene count changed: {len(rows)}"
        deaf = {r.scenario for r in rows if not r.audible}
        assert deaf == {"cafe_straight_v0.yaml", "city_curved_v0.yaml",
                        "city_figure8_v0.yaml"}, (
            f"the deaf set moved to {deaf} — if obstacles were added to the "
            f"city scenes (STATE #5) this is the expected failure; re-pin it")
        for r in rows:
            if not r.audible:
                assert r.max_spread == 0.0


def _matrix() -> list[reach.ReachProfile]:
    if "matrix" not in _CACHE:
        _CACHE["matrix"] = screen_scenarios(_scenario_paths())
    return _CACHE["matrix"]


class TestTheVacuityCheckHasAFloor:
    """`grid_unseen > 0` could not fail for the reason it was asked.

    The one job of the vacuity check is to rule out "the term is dead because
    nothing was rendered". `grid_unseen` cannot do that job: the grid is a
    square of half-extent `n·res/2 = 4.00 m` and sensing is a disc of radius
    `5.00 m`, so the corners (out to `5.66 m`) are unobservable in every
    render, of every scene, forever. Ground truth is therefore available
    without inventing a fixture — an obstacle-free world is a scene whose
    answer is known — which is what these pin (D-056's `misscored_probes`
    shape: restrict to a population where the answer is already settled,
    rather than exempt a population from being asked).
    """

    def test_an_empty_world_reads_nonzero_grid_unseen(self):
        """The bar the old check used, evaluated on the vacuous case itself."""
        producer = GTBevProducer([])
        grid = producer.render(np.zeros(2), 0.0).stack[RiskChannel.EPISTEMIC]
        frac = float((grid > reach.UNSEEN_SIGMA).mean())
        assert frac > 0.0, (
            "an empty world now reads zero unseen cells — the floor this "
            "module subtracts has gone away and the subtraction is a no-op")
        assert frac == pytest.approx(reach.empty_world_unseen(producer))

    def test_the_floor_is_geometry_not_scene(self):
        """Pose- and time-invariant, because the grid is robot-centred and an
        empty world casts no shadows. If either dependence appears, a single
        scalar floor is the wrong model and this is what says so."""
        producer = GTBevProducer([])
        floor = reach.empty_world_unseen(producer)
        for xy, t in [((0.0, 0.0), 0.0), ((7.5, -3.25), 4.0),
                      ((-11.0, 20.0), 13.5)]:
            grid = producer.render(np.array(xy), t).stack[RiskChannel.EPISTEMIC]
            assert float((grid > reach.UNSEEN_SIGMA).mean()) == pytest.approx(floor)

    def test_the_floor_is_derived_from_the_producer_not_typed(self):
        """A grid that fits inside its own sensing disc has no floor at all.

        `32 x 0.125` gives a `2.00 m` half-extent and a `2.83 m` corner, well
        inside the `5.00 m` disc. A hand-typed `0.027` would be wrong here;
        the measured one tracks the geometry (D-047's shape).
        """
        assert reach.empty_world_unseen(
            GTBevProducer([], grid_size=32, resolution=0.125)) == 0.0
        assert reach.empty_world_unseen(GTBevProducer([])) > 0.0

    def test_obstacle_free_scenes_are_vacuous_not_out_of_reach(self):
        """The finding. All three deaf scenes are deaf because they render no
        shadow, not because the fan cannot reach one — so `grid_unseen`'s
        documented separation was never made on the nominal driver, and the
        deaf class was never one class."""
        rows = [r for r in _matrix() if not r.audible]
        assert len(rows) == 3
        for r in rows:
            assert r.grid_unseen > 0.0, "the old bar clears — that is the bug"
            assert not r.renders_ignorance, (
                f"{r.scenario} now renders scene ignorance "
                f"({r.scene_unseen:.4f}); it is deaf for the *interesting* "
                f"reason now and D-021's reading applies to it")
            assert r.scene_unseen == 0.0
            assert r.grid_unseen == pytest.approx(r.unseen_floor)

    def test_audible_scenes_clear_the_floor_by_a_margin(self):
        """The subtraction does not eat the signal: every audible scene keeps
        most of its reading. Guards against over-correcting into a floor that
        swallows real shadow."""
        for r in [r for r in _matrix() if r.audible]:
            assert r.renders_ignorance
            assert r.scene_unseen > 0.05, f"{r.scenario}: {r.scene_unseen:.4f}"


class TestTheScalarDifferenceIsASetDifference:
    """`scalar_false_positives` was a difference of aggregates.

    `max(0, scalar_live_steps - live_steps)` equals the per-step set difference
    only if the live set nests inside the scalar's — which the field's own
    docstring conceded "need not" happen, while the `max(0, ...)` silently
    floored the case where it didn't. The sets do nest across the matrix, so
    the published numbers stand; that is now a **measurement** rather than a
    coincidence holding the quantity's place (D-046).
    """

    def test_the_two_verdict_sets_nest_across_the_matrix(self):
        rows = _matrix()
        offenders = {r.scenario: r.spread_only_steps
                     for r in rows if r.spread_only_steps}
        assert offenders == {}, (
            f"spread > 0 where the scalar says dead on {offenders} — the sets "
            f"no longer nest, so the old aggregate subtraction would now "
            f"under-report and `scalar_only_steps` is the only valid form")

    def test_set_difference_agrees_with_the_old_aggregate_where_it_nests(self):
        """Both forms, side by side, on the population where the old one was
        valid — so a future divergence names itself instead of appearing as a
        changed headline number."""
        for r in _matrix():
            assert r.scalar_false_positives == r.scalar_only_steps
            assert r.scalar_only_steps == max(
                0, r.scalar_live_steps - r.live_steps)

    def test_crossing_scene_retains_its_scalar_over_count(self):
        """D-021's qualitative claim on the nominal driver: the scalar is a
        strict over-count wherever it disagrees at all."""
        rows = {r.scenario: r for r in _matrix()}
        crossing = rows["cafe_obstacle_crossing_v0.yaml"]
        assert crossing.scalar_only_steps > 0
        assert crossing.scalar_live_steps > crossing.live_steps
