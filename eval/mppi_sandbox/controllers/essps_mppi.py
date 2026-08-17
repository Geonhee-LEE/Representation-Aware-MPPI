# SPDX-License-Identifier: BSD-3-Clause
"""`RiskMPPI` with the temperature **solved per iteration** instead of fixed.

This is Q-156's option (c): the paper's actual ESSPS form (Watson & Peters,
`2210.03512`) wired in under a *new controller name*, so that every
`lam`-conditioned number this branch has recorded — D-270's `31.2344`, D-271's
`7/8`, D-272's `WINDOW_EXHAUSTED`, D-273's axis verdict — keeps describing the
controller it was measured on. Option (a) (moving the solve into `RiskMPPI`
itself) would have re-dated all of them at once; naming the fork buys the
comparison without paying that.

What D-274 measured, and why it forces this
-------------------------------------------
:mod:`essps` retired ESSPS-as-a-per-scene-**constant**: the per-step solved
`lam` moves **47.6x** over one episode, so no scalar can sit where it needs to.
The compliance-optimal constant `0.787` holds the Q-026 band on **69 of 115**
steps, and it beats ESSPS's own median-matching objective (`57/115`). That
result does not indict the solve — it indicts freezing its output. `69/115` is
therefore the bar this arm is measured against, and the question is narrow:
does solving *every step* hold the band where no constant can?

Structurally it should hold at **every** step. ESS is strictly monotone in
`lam` for a fixed cost vector, so a target inside `(1, K)` is always reachable
and :func:`essps.solve_lam_for_ess` always lands on it. The target here is
`TARGET_FRACTION * K = 10/32 * K`, which sits inside the Q-026 band
`(0.05K, 0.5K)` by construction — so a step that solves is a step in band, and
compliance is bounded below by the solve rate. That makes the interesting
outcome the *cost* of holding it, not the holding: what the trajectory does
when the temperature is free to move 47x under it.

What it does not settle
------------------------
Band compliance is a property of the sampler, not of the robot. An arm that
holds the band every step and drives worse is a real possibility and the reason
`reached_goal` travels with the reading. This arm is not proposed as the
branch's operating point on the strength of a compliance count.

Fallback: when the solve returns `None` (target outside the reachable range on
`LAM_BRACKET`, which for a non-degenerate cost vector cannot happen) the arm
falls back to `p.lam` rather than raising, and records the fallback in
:attr:`lam_log` as the constant. `unsolved_steps` counts those, so a run that
quietly degenerated into the fixed-temperature arm reports itself instead of
being read as an ESSPS result.
"""

from __future__ import annotations

import numpy as np

from .risk_mppi import RiskMPPI

# `essps` imports `ab`, which imports this package — so the solver is pulled in
# at call time rather than at module scope. Deferring it here (not restating it)
# keeps `essps.solve_lam_for_ess` the single implementation of the root-find.


def _solver():
    from ..essps import TARGET_FRACTION, solve_lam_for_ess
    return TARGET_FRACTION, solve_lam_for_ess


class ESSPSMPPI(RiskMPPI):
    """`RiskMPPI` whose softmax temperature is re-solved every step.

    Only :meth:`_softmax_lam` differs from `RiskMPPI`; the rollout, the cost
    summation, the critics and the receding-horizon shift are inherited
    verbatim, so the two arms cannot drift apart anywhere except the
    temperature. That is the whole point of the fork.
    """

    def __init__(self, scenario, seed: int = 0, *,
                 target_fraction: float | None = None, **kwargs):
        super().__init__(scenario, seed=seed, **kwargs)
        default_fraction, _ = _solver()
        self.target_fraction = float(default_fraction if target_fraction is None
                                     else target_fraction)
        #: Temperature actually used at each step — solved, or `p.lam` on
        #: fallback. Logged because it is the quantity that distinguishes this
        #: arm, and `ess_log` (inherited) cannot show it.
        self.lam_log: list[float] = []
        #: Steps where the root-find declined and the constant was used.
        self.unsolved_steps: int = 0

    def _softmax_lam(self, cost: np.ndarray) -> float:
        _, solve_lam_for_ess = _solver()
        target = self.target_fraction * float(np.size(cost))
        lam = solve_lam_for_ess(cost, target)
        if lam is None:
            self.unsolved_steps += 1
            lam = float(self.p.lam)
        self.lam_log.append(float(lam))
        return float(lam)
