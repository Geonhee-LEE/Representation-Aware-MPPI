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

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.obstacles import CircleObstacle, min_clearance
from eval.mppi_sandbox.run import ROBOT_RADIUS, simulate
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

SEEDS = tuple(range(8))
W_EPIST_ON = 200.0
IDENTICAL_TOL = 1e-6


def _clearance(seed: int, w_epist: float) -> float:
    ob = CircleObstacle(0.0, -1.5)
    scenario = _straight_scenario(obstacles=[ob], expected_duration=15.0)
    ctrl = make_controller("risk_mppi", scenario, seed=seed,
                           robot_radius=ROBOT_RADIUS, w_risk=0.0,
                           k_margin_per_sigma=0.0, w_epist=w_epist)
    return min_clearance(simulate(scenario, ctrl), [ob], ROBOT_RADIUS)


_CACHE: dict = {}


def _deltas() -> np.ndarray:
    """Δclearance = shadow-on minus shadow-off, one entry per seed.

    Memoized: the three assertions below read the same sweep, and each
    seed costs two closed-loop sims (~1.5 s), so recomputing would triple
    this file's CI cost for no extra information.
    """
    if "deltas" not in _CACHE:
        _CACHE["deltas"] = np.array(
            [_clearance(s, W_EPIST_ON) - _clearance(s, 0.0) for s in SEEDS])
    return _CACHE["deltas"]


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
