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
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

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
