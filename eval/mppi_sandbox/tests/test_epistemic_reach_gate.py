# SPDX-License-Identifier: BSD-3-Clause
"""STATE #1 — ablate `w_epist` on the crossing scene. Two answers, both negative.

STATE framed this as the last surviving test of the *mechanism* rather than of a
correlate, on the premise that "the epistemic channel is the only term
`risk_mppi` has that `stock_mppi` does not". Both halves of that premise are
wrong, and neither refutation needed a simulation to find.

**1. The ablation had already been run — it is the shipped default.**
`RiskMPPI.__init__` defaults `w_epist=0.0`, and `calibrate_lam.main` passes no
arm kwargs through to `lam_ladder`. So *every* window in
`eval/scenarios/lam_windows.yaml` — including the `cafe_obstacle_crossing_v0`
separation (`stock_mppi [0.4, 0.8]` vs `risk_mppi [1.6, 3.2]`) that D-017 →
D-020 spent four cycles on — was measured with the epistemic channel **off**.
No separation result in this repo is evidence about the epistemic channel. The
term that actually differs between those two arms is `w_risk = 40.0`, the
DYNAMIC channel, which is the one term the premise did not name.

**2. Switched on, the term is not inert-with-signal. It is signal-free.**
`test_shadow_cost_seed_robustness.py` (11:00) established a failure mode where
the shadow cost prices samples very differently and changes nothing — spread
mean 197 at `offset = 0.3`, trajectory bit-identical. The crossing scene is a
*different* mode, one rung more degenerate:

| scene / horizon              | grid unseen | rollout sigma | spread      | live steps |
|------------------------------|-------------|---------------|-------------|------------|
| crossing, shipped `H = 30`   | 5.7–23.6 %  | **0.0 exactly** | **0.00**  | **0 / 92** |
| crossing, `H = 60`           | same        | varies        | 1512.50     | 121 / 240  |
| `offset=0.3`, `H = 30`       | —           | varies        | 196.49      | 19 / 114   |
| `offset=0.3`, `H = 20`       | —           | varies        | 11.36       | 4 / 88     |
| `offset=0.3`, `H = 10`       | —           | **0.0**       | **0.00**    | **0 / 51** |

Ignorance *is* rendered on the crossing scene — 12 % of the grid carries σ = 1
on average. The rollout cloud simply never touches any of it, so `w_epist`
adds the *same* constant to all K sample costs, which cancels exactly in the
softmax. Not "small", not "dominated": `w_epist = 200` executes a byte-identical
trajectory to `w_epist = 0` on 4/4 seeds, with `w_risk` at its shipped 40.0 or
zeroed.

**The controlled intervention (D-018).** Predictions registered before the run:
(A) raise the horizon on the dead scene → the term becomes live; (B) cut the
horizon on the known-live scene → it goes dead. Both confirmed, and (B) is
monotone across three rungs. So the gate is **rollout reach**, and it is causal
in both directions rather than a property of either scene.

**What failed its own test.** The obvious scalar summary of that gate —
"live iff max rollout reach ≥ distance to the nearest unseen cell" — is
*false*, and this file pins the counterexample: on the crossing scene at
`H = 30` that inequality holds on **28 of 92** steps where the spread is still
exactly zero. Rollouts reach far *along* the path; the shadows sit *lateral to*
and *behind* the actors. Reach gates the term, but a distance scalar does not
predict it — the direction the rollouts explore has to enter the statement.

Consequence for the epistemic channel: on this scene the fix is not a larger
`w_epist`. Any weight is exactly zero. The knobs that matter are the ones that
put rollout points where σ > 0 — planning horizon, sampled speed, sensing
range — and `cafe_obstacle_crossing_v0` sets `target_speed_mps: 0.3`
("slower than cafe_straight — gives MPPI room to dodge"), which makes the
scene named after its obstacles the one with the *shortest* epistemic reach in
the matrix. See D-021 / Q-043.
"""

from __future__ import annotations

import inspect

import numpy as np

from eval.mppi_sandbox import ab, calibrate_lam
from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.controllers.risk_mppi import RiskMPPI
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.representations import RiskChannel
from eval.mppi_sandbox.run import ROBOT_RADIUS, simulate
from eval.mppi_sandbox.scenario import load_scenario
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
SHIPPED_HORIZON = MPPIParams().horizon      # 30 — read, not hard-coded
W_EPIST_ON = 200.0
SEEDS = tuple(range(4))

#: `w_risk` / `k_margin_per_sigma` zeroed so `w_epist` is the only live term.
#: Every claim below is *also* checked at the shipped `w_risk = 40.0` where the
#: distinction matters (see `test_no_op_survives_the_shipped_w_risk`).
_ISOLATE_SHADOW = dict(w_risk=0.0, k_margin_per_sigma=0.0)

_CACHE: dict = {}


def _shadow_trace(scenario, horizon: int) -> dict:
    """Per-control-step trace of the shadow term on one run. Memoized.

    Records, at each step: the per-sample cost spread (`ptp`) the softmax
    actually sees, the farthest rollout point from the robot, and the distance
    to the nearest σ = 1 cell in the rendered BEV. The last two exist to let
    the reach *hypothesis* be stated and its scalar form be refuted in the same
    pass.
    """
    key = (id(scenario), horizon)
    if key in _CACHE:
        return _CACHE[key]

    ctrl = make_controller("risk_mppi", scenario, seed=0,
                           robot_radius=ROBOT_RADIUS,
                           params=MPPIParams(horizon=horizon),
                           w_epist=W_EPIST_ON, **_ISOLATE_SHADOW)
    spreads: list[float] = []
    reach: list[float] = []
    nearest_unseen: list[float] = []
    grid_unseen: list[float] = []
    inner = ctrl._extra_cost

    def _record(traj, t0):
        cost = inner(traj, t0)
        spreads.append(float(np.ptp(cost)))

        robot = traj[0, 0, :2].copy()
        xy = traj[..., :2].reshape(-1, 2)
        reach.append(float(np.linalg.norm(xy - robot, axis=1).max()))

        grid = ctrl._bev.stack[RiskChannel.EPISTEMIC]
        unseen = grid > 0.5
        grid_unseen.append(float(unseen.mean()))
        n = grid.shape[0]
        res = ctrl.producer.res
        half = n * res / 2.0
        ax = robot[0] - half + (np.arange(n) + 0.5) * res
        ay = robot[1] - half + (np.arange(n) + 0.5) * res
        cx, cy = np.meshgrid(ax, ay)
        d = np.hypot(cx - robot[0], cy - robot[1])
        nearest_unseen.append(float(d[unseen].min()) if unseen.any()
                              else float("inf"))
        return cost

    ctrl._extra_cost = _record
    simulate(scenario, ctrl)

    trace = dict(spread=np.array(spreads), reach=np.array(reach),
                 nearest_unseen=np.array(nearest_unseen),
                 grid_unseen=np.array(grid_unseen))
    _CACHE[key] = trace
    return trace


def _crossing():
    if "crossing" not in _CACHE:
        _CACHE["crossing"] = load_scenario(CROSSING)
    return _CACHE["crossing"]


def _off_centre():
    """The geometry `test_shadow_cost_seed_robustness.py` measured live."""
    if "off_centre" not in _CACHE:
        _CACHE["off_centre"] = _straight_scenario(
            obstacles=[CircleObstacle(0.3, -1.5)], expected_duration=15.0)
    return _CACHE["off_centre"]


class TestTheAblationWasAlreadyTheDefault:
    """Zero-simulation half: the repo's windows are epistemic-OFF measurements."""

    def test_risk_mppi_ships_with_the_epistemic_channel_off(self):
        """The ablation invariant, read as provenance rather than as a contract.

        `w_epist = 0` is documented as "byte-identical to stock_mppi". The
        consequence nobody drew: any measurement that does not *override* it is
        an ablated measurement.
        """
        default = inspect.signature(RiskMPPI.__init__).parameters["w_epist"].default
        assert default == 0.0, (
            "RiskMPPI's `w_epist` default changed — every window in "
            "lam_windows.yaml was generated under the old one, so the table "
            "must be regenerated before any of its numbers are cited")

    def test_the_calibrator_cannot_turn_the_channel_on(self):
        """`calibrate_lam.main` exposes no arm-kwarg flag, so the generated
        table is unconditionally an epistemic-off measurement.

        If a future cycle adds such a flag, this test fails and the table's
        provenance stops being inferable from the CLI alone — at which point
        `lam_windows.yaml` needs to record the arm kwargs it was built with.
        """
        src = inspect.getsource(calibrate_lam.main)
        for knob in ("w_epist", "w_risk", "k_margin_per_sigma"):
            assert knob not in src, (
                f"`{knob}` is now settable from the calibrator CLI — "
                f"lam_windows.yaml must start recording its arm kwargs, "
                f"otherwise its windows are no longer self-describing")

    def test_the_separating_term_is_the_dynamic_channel_not_the_epistemic_one(self):
        """Names the term STATE's premise missed. With `w_epist = 0` by
        default, the only non-zero difference between `risk_mppi` and
        `stock_mppi` in the calibrated table is `w_risk` on the DYNAMIC
        channel — so the crossing scene's window separation is a dynamic-risk
        result, not an epistemic one."""
        params = inspect.signature(RiskMPPI.__init__).parameters
        assert params["w_risk"].default != 0.0
        assert params["w_epist"].default == 0.0
        assert params["k_margin_per_sigma"].default == 0.0


class TestTheTermIsSignalFreeOnTheCrossingScene:
    """Not inert-with-signal (the `offset=0.3` mode). No signal at all."""

    def test_per_sample_spread_is_exactly_zero_at_every_step(self):
        """The headline. A constant added to all K sample costs cancels in the
        softmax exactly, so at the shipped horizon `w_epist` is a no-op for
        *any* weight — there is no value that would make it bite."""
        spread = _shadow_trace(_crossing(), SHIPPED_HORIZON)["spread"]
        assert len(spread) > 50, "run ended early — trace is not representative"
        assert spread.max() == 0.0, (
            f"shadow-cost spread is no longer identically zero "
            f"(max {spread.max():.3e} over {len(spread)} steps) — the crossing "
            f"scene has moved out of the signal-free class and D-021's "
            f"reach argument needs re-measuring on it")

    def test_the_grid_does_carry_ignorance(self):
        """Rules out the trivial explanation. σ = 1 cells exist in every render
        — roughly an eighth of the grid — so 'nothing rendered' is not why the
        term is dead. The field is there and out of reach."""
        unseen = _shadow_trace(_crossing(), SHIPPED_HORIZON)["grid_unseen"]
        assert unseen.min() > 0.0, (
            "no unseen cells at all — the scene stopped casting shadows, which "
            "would make the signal-free finding vacuous rather than true")
        assert unseen.mean() > 0.05, (
            f"grid ignorance collapsed to {unseen.mean():.3f} mean; the "
            f"'rendered but unreachable' reading needs re-checking")

    def test_shadow_weight_is_a_byte_level_no_op(self):
        """The closed-loop consequence of zero spread, measured rather than
        argued: 200 vs 0 executes the same trajectory to the last bit."""
        on, off = self._arms(**_ISOLATE_SHADOW)
        for a, b in zip(on, off):
            assert a.traj.shape == b.traj.shape, (
                f"seed {a.seed}: arms diverged in length — the term is live "
                f"on the crossing scene now; re-open D-021")
            np.testing.assert_allclose(
                a.traj, b.traj, rtol=0, atol=0,
                err_msg=f"seed {a.seed}: crossing-scene arms are no longer "
                        f"bit-identical")

    def test_no_op_survives_the_shipped_w_risk(self):
        """The isolation kwargs are not what makes it a no-op. With
        `w_risk = 40.0` — the configuration the calibrated window was actually
        measured under — the two arms are still bit-identical, so the finding
        applies to the shipped controller and not only to a stripped one."""
        on, off = self._arms()
        for a, b in zip(on, off):
            assert np.array_equal(a.traj, b.traj), (
                f"seed {a.seed}: `w_epist` moves the shipped controller on the "
                f"crossing scene — the window separation may now be partly "
                f"epistemic and D-021's first claim needs re-measuring")

    @staticmethod
    def _arms(**kwargs):
        key = ("arms", tuple(sorted(kwargs.items())))
        if key not in _CACHE:
            _CACHE[key] = tuple(
                ab.seed_sweep(_crossing(), "risk_mppi", SEEDS,
                              w_epist=w, **kwargs)
                for w in (W_EPIST_ON, 0.0))
        return _CACHE[key]


class TestRolloutReachIsTheGate:
    """Both directions of the controlled intervention (D-018).

    Neither arm is the cheap/obvious one alone: (A) alone would show a knob
    that wakes the term up without showing it is *the* knob, and (B) alone
    would show a scene-independent decay without showing it explains the dead
    scene. The pair is what licenses the causal claim.
    """

    def test_raising_the_horizon_wakes_the_dead_scene(self):
        """Direction A, registered before the run. Same scene, same weights,
        same seed — only the rollout horizon doubles, and the term goes from
        0/92 live steps to a spread in the thousands."""
        dead = _shadow_trace(_crossing(), SHIPPED_HORIZON)["spread"]
        woken = _shadow_trace(_crossing(), 2 * SHIPPED_HORIZON)["spread"]
        assert dead.max() == 0.0
        live_steps = int((woken > 1e-9).sum())
        assert live_steps > 0.25 * len(woken), (
            f"only {live_steps}/{len(woken)} steps live at H="
            f"{2 * SHIPPED_HORIZON} (measured 121/240) — if the horizon no "
            f"longer wakes the term, reach is not the gate")
        assert woken.max() > 100.0

    def test_cutting_the_horizon_kills_the_live_scene(self):
        """Direction B — the control, on the geometry
        `test_shadow_cost_seed_robustness.py` measured live at the shipped
        horizon. Monotone decay across three rungs, to *exactly* zero.

        This is what rules out 'the crossing scene is just a scene where the
        term happens not to apply': the same knob turns the term off on a scene
        where it demonstrably applies.
        """
        rungs = [_shadow_trace(_off_centre(), h)["spread"]
                 for h in (SHIPPED_HORIZON, 20, 10)]
        means = [float(s.mean()) for s in rungs]
        assert means[0] > means[1] > means[2], (
            f"spread is no longer monotone in horizon: {means} "
            f"(measured 196.49 / 11.36 / 0.00)")
        assert rungs[0].max() > 0.0, (
            "the off-centre scene is no longer live at the shipped horizon — "
            "this control has lost its positive arm, see "
            "test_shadow_cost_seed_robustness.py")
        assert rungs[-1].max() == 0.0, (
            f"spread at H=10 is {rungs[-1].max():.3e}, not zero — the kill "
            f"direction is weaker than measured")

    def test_reach_distance_alone_does_not_predict_liveness(self):
        """The scalar form of the reach claim, refuted by its own data.

        'Live iff the farthest rollout point is at least as far as the nearest
        unseen cell' is the obvious summary and it is wrong: on the crossing
        scene at the shipped horizon that inequality holds on ~28 of 92 steps
        where the spread is still exactly zero. Rollouts reach far *along* the
        path; the shadows sit lateral to and behind the actors. Any future
        scene-screening statistic built on this gate has to carry direction,
        not just distance — the D-018 lesson, one level down.
        """
        tr = _shadow_trace(_crossing(), SHIPPED_HORIZON)
        false_positives = int(((tr["reach"] >= tr["nearest_unseen"])
                               & (tr["spread"] == 0.0)).sum())
        assert false_positives > 10, (
            f"only {false_positives} steps satisfy the distance test while the "
            f"term is dead (measured ~28) — if this reaches zero the scalar "
            f"predictor is salvageable and the docstring above is too "
            f"pessimistic; re-measure before building a screen on it")
