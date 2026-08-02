# SPDX-License-Identifier: BSD-3-Clause
"""Characterization of a defect in the baseline MPPI update (Q-032).

`StockMPPI.command` rolls out the **clipped** control samples but weights the
**raw, unclipped** `noise` in its update:

    controls = clip(U + noise)          # <- what the rollout evaluated
    ...
    U = U + Σ w_k · noise_k             # <- what the update credits

The two agree only where the clip does not bind. Williams et al. (2017), and
every implementation that clamps (nav2's `mppi_controller` computes the new
sequence as the weighted mean of the *clamped* noised controls, which is
algebraically `U + Σ w_k · (clip(U + ε_k) − U)`), weight the perturbation that
actually generated the evaluated trajectory. Weighting `noise` credits the plan
with control authority the rollout never had.

These tests do **not** assert the correct behaviour — they pin how hard the
clip binds, so that the defect is measured rather than asserted-away, and so a
future cycle that fixes it is forced to re-baseline deliberately. The fix is
one line (`eps = controls - self.U[None]`, weight `eps`), and it is *not*
applied here on purpose: it moves every closed-loop number in the sandbox,
including the reference arm of every unmerged P3 A/B (#67/#68/#69). That
re-baseline is its own thrust and belongs on its own branch.

Measured 2026-08-02 10:00 (n=4 seeds/scene, full closed-loop runs):

    scene                     v@v_min   v@v_max   omega    weight mass on
                                                           clipped samples
    cafe_straight_v0 (0.4)     22-29%     4-9%    8-15%       99.1-100%
    cafe_obstacle_crossing     23-27%     8-10%    9-12%       99.4-100%
    city_curved_v0   (0.6)      9-11%    21-25%   14-18%          100%

Closed-loop cost of the defect, corrected-vs-shipped over 12 seeds:

    cafe_straight_v0            0.233 -> 0.312 m/s realized (58% -> 78% of the
                                0.4 target); duration 12.82 s -> 9.50 s
    cafe_obstacle_crossing      0.311 -> 0.404 m/s; 16.09 s -> 12.22 s

The correction is not a uniform win, which is why it is not applied blind: on a
path-blocking obstacle scene (n=16) it went 16/16 -> 15/16 on completion and
median clearance +0.0299 -> +0.0117 m. See Q-032.
"""

import numpy as np
import pytest

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams, StockMPPI
from eval.mppi_sandbox.dynamics import step
from eval.mppi_sandbox.run import ROBOT_RADIUS, simulate
from eval.mppi_sandbox.scenario import load_scenario

STRAIGHT_YAML = "eval/scenarios/cafe_straight_v0.yaml"


class _Instrumented(StockMPPI):
    """Byte-for-byte the shipped update, plus per-tick clip bookkeeping.

    Kept in lockstep with `StockMPPI.command` deliberately: if the two drift,
    `test_instrumented_copy_matches_the_shipped_controller` fails and the
    numbers below stop meaning anything.
    """

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.ticks: list[dict] = []

    def command(self, state, t):
        p, lim = self.p, self.limits
        noise = self.rng.normal(
            0.0, [p.sigma_v, p.sigma_w], size=(p.samples, p.horizon, 2))
        raw = self.U[None] + noise
        controls = raw.copy()
        controls[..., 0] = np.clip(controls[..., 0], lim.v_min, lim.v_max)
        controls[..., 1] = np.clip(controls[..., 1], -lim.omega_max, lim.omega_max)
        realized = controls - self.U[None]

        states = np.broadcast_to(state, (p.samples, 5)).copy()
        traj = np.empty((p.samples, p.horizon, 5))
        for h in range(p.horizon):
            states = step(states, controls[:, h], p.dt, lim)
            traj[:, h] = states

        cost = self._cost(traj, t)
        w = np.exp(-(cost - cost.min()) / p.lam)
        w /= w.sum()

        lo = raw[..., 0] < lim.v_min
        hi = raw[..., 0] > lim.v_max
        om = np.abs(raw[..., 1]) > lim.omega_max
        self.ticks.append(dict(
            frac_v_lo=float(lo.mean()),
            frac_v_hi=float(hi.mean()),
            frac_omega=float(om.mean()),
            weight_mass_on_clipped=float(w[(lo | hi | om).any(axis=1)].sum()),
            update_gap=float(np.abs(np.einsum("k,khu->hu", w, noise)
                                    - np.einsum("k,khu->hu", w, realized)).max()),
        ))

        self.U = self.U + np.einsum("k,khu->hu", w, noise)   # shipped form
        self.U[:, 0] = np.clip(self.U[:, 0], lim.v_min, lim.v_max)
        self.U[:, 1] = np.clip(self.U[:, 1], -lim.omega_max, lim.omega_max)
        u0 = self.U[0].copy()
        self.U[:-1] = self.U[1:]
        return u0


def _drive(scenario, seed=0):
    ctrl = _Instrumented(scenario, seed=seed, robot_radius=ROBOT_RADIUS)
    simulate(scenario, ctrl)
    return ctrl.ticks


class TestInstrumentationIsFaithful:
    def test_instrumented_copy_matches_the_shipped_controller(self):
        """The measurements below are only about `StockMPPI` while this holds."""
        scen = load_scenario(STRAIGHT_YAML)
        shipped = simulate(scen, make_controller("stock_mppi", scen, seed=0,
                                                 robot_radius=ROBOT_RADIUS))
        probed = simulate(scen, _Instrumented(scen, seed=0,
                                              robot_radius=ROBOT_RADIUS))
        assert shipped.shape == probed.shape
        np.testing.assert_allclose(shipped, probed, rtol=0, atol=0)


class TestTheClipBindsHard:
    """If these ever go slack the defect stops mattering — and so does Q-032."""

    def test_saturation_is_pervasive_not_a_tail_event(self):
        ticks = _drive(load_scenario(STRAIGHT_YAML))
        v_lo = np.mean([t["frac_v_lo"] for t in ticks])
        assert v_lo > 0.15, (
            f"only {v_lo:.1%} of sampled v hit v_min — the raw-vs-realized gap "
            f"is no longer pervasive; re-measure Q-032 before relying on it")

    def test_essentially_all_softmax_weight_sits_on_clipped_samples(self):
        """The severity multiplier: a rare clip on a zero-weight sample would
        be harmless. These are the samples the update is *made of*."""
        ticks = _drive(load_scenario(STRAIGHT_YAML))
        mass = np.mean([t["weight_mass_on_clipped"] for t in ticks])
        assert mass > 0.9, f"weight mass on clipped samples fell to {mass:.1%}"

    def test_update_gap_is_large_relative_to_the_sampling_sigma(self):
        """Scale check: the mis-credited increment is not a rounding artifact."""
        ticks = _drive(load_scenario(STRAIGHT_YAML))
        gap = np.max([t["update_gap"] for t in ticks])
        sigma_v = MPPIParams().sigma_v
        assert gap > sigma_v, (
            f"max per-element update gap {gap:.4f} is below one sigma_v "
            f"({sigma_v}) — the mis-credited increment is now within sampling "
            f"noise and Q-032's severity claim needs re-measuring")


class TestClosedLoopConsequence:
    def test_baseline_under_realizes_its_own_target_speed(self):
        """The symptom this defect explains — logged 2026-08-02 02:00 as
        'speed is decoupled from target_speed' and attributed elsewhere."""
        scen = load_scenario(STRAIGHT_YAML)
        traj = simulate(scen, make_controller("stock_mppi", scen, seed=0,
                                              robot_radius=ROBOT_RADIUS))
        realized = float(np.abs(traj[:, 4]).mean())
        assert realized < 0.75 * scen.target_speed, (
            f"realized {realized:.3f} m/s vs target {scen.target_speed} — the "
            f"under-drive Q-032 explains has gone away; re-check the update")


class _Corrected(StockMPPI):
    """Reference implementation of the Williams/nav2 form — weights `eps`.

    Exists only so the invariant below can be stated as a behavioural
    comparison against the shipped controller, rather than by re-deriving one
    tick by hand. A hand-derived tick-0 check does **not** detect the defect:
    at `t=0` the plan sits at `target_speed` with `omega=0`, the clip binds on
    ~0.4 % of elements, and the `lam=0.1` softmax concentrates on unclipped
    samples — so the first-tick update gap is numerically zero. The defect is a
    closed-loop accumulation, and has to be measured as one.
    """

    def command(self, state, t):
        p, lim = self.p, self.limits
        noise = self.rng.normal(
            0.0, [p.sigma_v, p.sigma_w], size=(p.samples, p.horizon, 2))
        controls = self.U[None] + noise
        controls[..., 0] = np.clip(controls[..., 0], lim.v_min, lim.v_max)
        controls[..., 1] = np.clip(controls[..., 1], -lim.omega_max, lim.omega_max)
        eps = controls - self.U[None]                     # the only difference
        states = np.broadcast_to(state, (p.samples, 5)).copy()
        traj = np.empty((p.samples, p.horizon, 5))
        for h in range(p.horizon):
            states = step(states, controls[:, h], p.dt, lim)
            traj[:, h] = states
        cost = self._cost(traj, t)
        w = np.exp(-(cost - cost.min()) / p.lam)
        w /= w.sum()
        self.U = self.U + np.einsum("k,khu->hu", w, eps)
        self.U[:, 0] = np.clip(self.U[:, 0], lim.v_min, lim.v_max)
        self.U[:, 1] = np.clip(self.U[:, 1], -lim.omega_max, lim.omega_max)
        u0 = self.U[0].copy()
        self.U[:-1] = self.U[1:]
        return u0


@pytest.mark.xfail(strict=True, reason="Q-032: the shipped update weights raw "
                                       "noise, not the realized perturbation. "
                                       "Fixing it re-baselines every sandbox "
                                       "A/B — do that deliberately, then "
                                       "delete this xfail.")
def test_shipped_update_matches_the_realized_perturbation_form():
    """The Williams invariant, as a closed-loop behavioural equivalence.

    `strict=True` on purpose: the day a cycle applies the one-line fix, the two
    arms coincide, this XPASSes, and pytest reports XPASS(strict) as a failure.
    That is the intended forcing function — it makes the re-baseline of #67 /
    #68 / #69 an explicit act rather than a silent drift in their reference arm.
    """
    scen = load_scenario(STRAIGHT_YAML)
    shipped = simulate(scen, make_controller("stock_mppi", scen, seed=0,
                                             robot_radius=ROBOT_RADIUS))
    corrected = simulate(scen, _Corrected(scen, seed=0,
                                          robot_radius=ROBOT_RADIUS))
    assert shipped.shape == corrected.shape, (
        f"arms diverged in length: {shipped.shape} vs {corrected.shape}")
    np.testing.assert_allclose(shipped, corrected, rtol=1e-9, atol=1e-9)
