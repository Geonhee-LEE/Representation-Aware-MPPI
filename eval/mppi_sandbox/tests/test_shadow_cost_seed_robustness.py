# SPDX-License-Identifier: BSD-3-Clause
"""Q-017 re-measurement: the "shadow cost is redundant" finding is a seed-0 artifact.

`test_risk_mppi.py` shipped the Q-017 negative result as a *single-seed*
assertion — at `seed=0`, `w_epist=0` and `w_epist=200` produce a
bit-identical executed clearance, which was read as "the additive shadow
term has nothing to redistribute for a single convex obstacle".

That reading does not survive a seed sweep. Measured on this scenario
(one circle obstacle at (0, -1.5), straight corridor, 15 s):

| seeds | bit-identical | differ | median |Δclearance| | max |Δ| |
|---|---|---|---|---|
| 0–23 (n=24) | **2** (seeds 0, 22) | **22** | 1.6 cm | 7.8 cm |
| 0–7  (n=8)  | 1 (seed 0)         | 7      | 0.9 cm | 2.9 cm |

So the term is **active**, not redundant — it moves the executed clearance
by a centimetre-scale amount on ~92 % of seeds. Seed 0 landed in one of the
two basins where the two arms happen to converge to the same homotopy, and
the original assertion pinned exactly that coincidence.

**But active is not beneficial.** The direction is a coin flip: over seeds
0–23 the shadow arm ends up *farther* from the obstacle on 10 seeds and
*closer* on 12. There is no systematic clearance gain to claim — the term
perturbs the solution without steering it. That distinction (inert vs.
active-but-non-directional) is the one Q-017 actually needs, and it is why
this file asserts the magnitude claim only and leaves the directional claim
to the docstring: asserting a null direction at n=8 would be flaky, and the
honest posture on Q-017 is no premature GREEN in either direction.

This also explains #67's red CI, which was logged in STATE as "a numpy
pin". It is not an import or API break: CI's newer numpy shifts seed 0 out
of the coincidence basin (CI measured 0.0140 vs 0.0520), so the assertion
fails there and passes under local numpy 1.26.4. Pinning numpy would have
made CI green by freezing the one environment in which a false claim holds.
The assertions below hold in *both* environments, because they no longer
depend on which basin a single seed lands in.
"""

import numpy as np

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.run import ROBOT_RADIUS, simulate
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

import pytest

SEEDS = tuple(range(8))
W_EPIST_ON = 200.0
IDENTICAL_TOL = 1e-6

# w_risk / k_margin_per_sigma zeroed so `w_epist` is the *only* live term —
# otherwise "the shadow cost moved the trajectory" is unattributable.
_ISOLATE_SHADOW = dict(w_risk=0.0, k_margin_per_sigma=0.0)

_CACHE: dict = {}


def _sweeps() -> tuple[list, list]:
    """(shadow-on, shadow-off) seed sweeps, memoized.

    Each seed costs two closed-loop sims (~1.5 s) and the assertions below
    read the same pair, so recomputing would multiply this file's CI cost for
    no extra information.
    """
    if "sweeps" not in _CACHE:
        scenario = _straight_scenario(obstacles=[CircleObstacle(0.0, -1.5)],
                                      expected_duration=15.0)
        _CACHE["sweeps"] = tuple(
            ab.seed_sweep(scenario, "risk_mppi", SEEDS, w_epist=w,
                          **_ISOLATE_SHADOW)
            for w in (W_EPIST_ON, 0.0))
    return _CACHE["sweeps"]


def _deltas() -> np.ndarray:
    """Δclearance = shadow-on minus shadow-off, one entry per seed."""
    on, off = _sweeps()
    return ab.paired_delta(on, off)


@pytest.mark.slow
class TestShadowCostRedundancyIsSeedDependent:
    """The Q-017 'redundant' claim must not be re-derivable from one seed."""

    def test_shadow_cost_changes_clearance_on_most_seeds(self):
        """Headline: `w_epist` is *active*. Measured 7/8 here and 22/24 at
        n=24; asserted at >= 5/8 so the test states the effect rather than
        a particular RNG stream. Guards against re-pinning the seed-0
        coincidence that made the original assertion look true."""
        deltas = _deltas()
        differing = int((np.abs(deltas) > IDENTICAL_TOL).sum())
        assert differing >= 5, (
            f"only {differing}/{len(SEEDS)} seeds moved — if this drops, the "
            f"'redundant' reading may be back on the table: {deltas}")

    def test_effect_magnitude_is_material_not_numerical_noise(self):
        """The movement is centimetre-scale, i.e. a real trajectory change,
        not float jitter — so 'nothing to redistribute' is the wrong model
        of what the additive term does."""
        deltas = _deltas()
        assert np.abs(deltas).max() > 1e-2, (
            f"largest |Δclearance| {np.abs(deltas).max():.2e} m is below the "
            f"1 cm materiality floor: {deltas}")
        assert np.isfinite(deltas).all()

    def test_single_seed_would_have_concluded_redundant(self):
        """Pins the actual defect so it cannot silently return: seed 0 alone
        is (near-)identical across the two arms under this numpy, which is
        precisely why the single-seed assertion passed locally while CI —
        on a different numpy — measured 0.0140 vs 0.0520 and failed."""
        deltas = _deltas()
        identical = int((np.abs(deltas) <= IDENTICAL_TOL).sum())
        assert identical <= 3, (
            f"{identical}/{len(SEEDS)} seeds identical — the arms are "
            f"converging more than measured; re-open Q-017's premise")


class TestNuisanceControlsHold:
    """The two controls this comparison needs beyond the seed ensemble.

    Neither was assertable before `ab` existed, and both could silently
    invalidate the magnitude claim above: an arm that stops short reports a
    clearance it never had to earn, and an arm that drives slower earns one
    for a reason that has nothing to do with the shadow term.
    """

    def test_both_arms_complete_the_path_on_every_seed(self):
        on, off = _sweeps()
        ab.assert_all_reached(on, "w_epist=200")
        ab.assert_all_reached(off, "w_epist=0")

    def test_arms_are_speed_matched_so_delta_is_not_a_speed_effect(self):
        """Unlike the #69 visibility-gate comparison — where the blind arm ran
        1.58x the oracle and needed an explicit `v_max` handicap — these two
        arms are within ~1 % of each other unforced, so no handicap is applied
        and the centimetre-scale Δ above is not purchasable by speed."""
        on, off = (ab.summarize(s) for s in _sweeps())
        ratio = on.mean_speed / off.mean_speed
        assert 0.95 <= ratio <= 1.05, (
            f"arms diverged in realized speed ({on.mean_speed:.4f} vs "
            f"{off.mean_speed:.4f} m/s, {ratio:.3f}x) — the clearance delta is "
            f"now speed-confounded and needs a v_max handicap, as on PR #69")

    def test_direction_is_a_coin_flip_not_a_clearance_gain(self):
        """Active but *non-directional* — the distinction Q-017 actually
        needs. Asserted as 'neither side sweeps', not as a null direction:
        at n=8 (5 farther / 2 closer / 1 tied here, 10/12/2 at n=24) a
        two-sided null is under-powered, so the honest claim is only that no
        systematic clearance gain is demonstrable."""
        farther, closer, _ = ab.sign_counts(_deltas(), IDENTICAL_TOL)
        assert max(farther, closer) < len(SEEDS) - 1, (
            f"{farther} farther / {closer} closer — one direction now nearly "
            f"sweeps; the non-directional reading of Q-017 needs re-checking")


# --- 2026-08-02 11:00 -----------------------------------------------------
# The classes above establish that `w_epist` is *active* on the centred-obstacle
# geometry and *non-directional* there. Both claims turned out to be pinned to
# that one geometry, and the reason is not the one Q-017 originally recorded.
#
# Measured at n=24 across five rescopes (the Q-028 protocol), shadow-on vs
# shadow-off, paired by seed, sign test on completing seeds:
#
#   | rescope                      | shipped update | corrected update (Q-032) |
#   |------------------------------|----------------|--------------------------|
#   | centred obstacle (control)   | 10/12/2 p=0.83 | **15/5/3  p=0.041**      |
#   | geometry `offset=0.3`        |  0/0/24 tied   |  0/0/24 tied             |
#   | geometry `offset=0.6`        |  0/0/24 tied   |  0/0/24 tied             |
#   | geometry along-path `-1.2`   | 10/10/4 p=1.00 | 13/7/4  p=0.26           |
#   | cost `w_path=3`              |  0/0/24 tied   |  0/0/24 tied             |
#
# Two consequences, both negative for Q-017 answer (a):
#
# 1. **The direction does not survive.** A first look at n=8 under the corrected
#    update read 7 farther / 0 closer and was logged as the most promising open
#    thread in the project. At n=24 it decays to 15/5 (p = 0.041) — one seed
#    flipping to `closer` would take it to 14/6, p = 0.115. A result that fragile
#    on a single scene, which then vanishes on three of four rescopes, is not a
#    clearance gain.
#
# 2. **The original explanation of the inertness was wrong.** Q-017 recorded
#    "the additive term has nothing to redistribute" — softmax-weighted E[sigma]
#    ~ 0 at the pre-obstacle pose. That is not what is happening. At `offset=0.3`
#    the per-sample shadow-cost spread is *larger* than on the centred scene
#    (mean 197 / max 2000 vs mean 55 / max 2800 cost units) and the executed
#    trajectory is still **bit-identical** between `w_epist` 200 and 0. The term
#    prices samples very differently and changes nothing.
#
# What actually distinguishes the two geometries is homotopy indifference. With
# the obstacle on the path centreline, passing left and passing right are nearly
# cost-tied, the `lam=0.1` softmax sits on a knife edge, and *any* sufficiently
# large additive term tips it. Move the hazard 0.3 m off-centre — or just cheapen
# path adherence — and one homotopy wins outright; the shadow term then cannot
# bridge the gap no matter how much spread it carries.
#
# So `w_epist`'s measurable effect is **knife-edge amplification, not steering**,
# and the scene where it is measurable is the same degenerate class Q-027 already
# ruled inadmissible for safety claims (its oracle grazes at 1 cm). See Q-033.

_OFF_CENTRE = 0.3
_INERT_SEEDS = tuple(range(4))


def _arms_at(offset: float, w_epist: float, seeds=_INERT_SEEDS):
    scenario = _straight_scenario(obstacles=[CircleObstacle(offset, -1.5)],
                                  expected_duration=15.0)
    return ab.seed_sweep(scenario, "risk_mppi", seeds, w_epist=w_epist,
                         **_ISOLATE_SHADOW)


@pytest.mark.slow
class TestActivityIsConfinedToTheBlockingGeometry:
    """`w_epist`'s measurable effect does not survive a geometry rescope.

    Asserted on `risk_mppi` as shipped, so this holds independently of whether
    a future cycle applies the Q-032 update fix — the bit-identity was measured
    under both update forms.
    """

    def test_off_centre_hazard_makes_the_shadow_term_bit_inert(self):
        """The headline. 0.3 m of lateral offset — no controller knob moves —
        and `w_epist=200` executes the same trajectory as `w_epist=0`, to the
        last bit, on every seed."""
        on = _arms_at(_OFF_CENTRE, W_EPIST_ON)
        off = _arms_at(_OFF_CENTRE, 0.0)
        for a, b in zip(on, off):
            assert a.traj.shape == b.traj.shape, (
                f"seed {a.seed}: arms diverged in length "
                f"{a.traj.shape} vs {b.traj.shape} — the shadow term is no "
                f"longer inert off-centre; re-run the Q-028 rescope table")
            np.testing.assert_allclose(
                a.traj, b.traj, rtol=0, atol=0,
                err_msg=f"seed {a.seed}: off-centre arms are no longer "
                        f"bit-identical — Q-017's confinement claim needs "
                        f"re-measuring")

    def test_inertness_is_not_explained_by_a_vanishing_shadow_cost(self):
        """Refutes Q-017's recorded explanation ('nothing to redistribute').

        The term assigns visibly different costs to different rollout samples
        at exactly the geometry where it changes nothing. Whatever makes it
        inert, it is not absence of signal — so the fix is not 'render more
        sigma', and a scenario that merely puts more field in front of the
        robot will not make (a) non-inert.
        """
        scenario = _straight_scenario(
            obstacles=[CircleObstacle(_OFF_CENTRE, -1.5)],
            expected_duration=15.0)
        ctrl = make_controller("risk_mppi", scenario, seed=0,
                               robot_radius=ROBOT_RADIUS,
                               w_epist=W_EPIST_ON, **_ISOLATE_SHADOW)
        spreads: list[float] = []
        inner = ctrl._extra_cost

        def _record(traj, t0):
            cost = inner(traj, t0)
            spreads.append(float(np.ptp(cost)))
            return cost

        ctrl._extra_cost = _record
        simulate(scenario, ctrl)

        assert spreads, "controller never evaluated a rollout batch"
        assert max(spreads) > 1.0, (
            f"per-sample shadow-cost spread collapsed to {max(spreads):.3e} — "
            f"if this is genuinely ~0 then 'nothing to redistribute' is the "
            f"right model after all and the note above is wrong")

    def test_the_active_geometry_is_the_one_with_a_blocked_path(self):
        """Positive control for the two assertions above: the same term on the
        centred obstacle *does* move the trajectory. Without this, a bug that
        silently disabled `w_epist` everywhere would pass the inertness test."""
        on = _arms_at(0.0, W_EPIST_ON)
        off = _arms_at(0.0, 0.0)
        moved = sum(
            a.traj.shape != b.traj.shape
            or not np.array_equal(a.traj, b.traj)
            for a, b in zip(on, off))
        assert moved >= 2, (
            f"only {moved}/{len(_INERT_SEEDS)} centred-obstacle seeds moved — "
            f"the shadow term may now be inert everywhere, which would make "
            f"the confinement claim vacuous rather than true")
