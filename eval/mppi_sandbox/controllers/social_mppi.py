# SPDX-License-Identifier: BSD-3-Clause
"""`RiskMPPI` at the **paired** operating point — the 2x2's winning cell, named.

The branch's largest measured clearance step is not an arm. `three_arm.ARMS`
denominates every arm against an empty baseline (`w_risk = 0.0`) on purpose —
that isolation is what let D-218 separate a main effect from an interaction —
and the effect it found is precisely that `w_ped` **is** an interaction:

    w_risk = 40   0.0068 -> 0.3823   step **+0.3755**
    w_risk =  0   0.0202 -> 0.0010   step  -0.0192

(`cafe_obstacle_crossing_v0`, 6 paired seeds, `lam = 0.8`, worst-case clearance
in m; `three_arm.risk_interaction`.) D-219 then walked all three eligible
scenes and D-234 narrowed `SIGN_FLIP` to the crossing scene, but the sign of
the *top* row never moved: on all three scenes the pair beats both members, and
D-235 strengthened exactly that half (6+/0- p=0.031 -> 11+/1- p=0.006 at n=12
on convoy and head-on) while retracting the bottom row's apparent direction.

So the configuration with the best evidence on this branch — the only one whose
seed majority survived doubling — could until now only be reached by passing
two overrides to `risk_mppi`. Every harness that sweeps *names*
(`ab.seed_sweep`, `baseline_matrix`, `near_miss.score_runs`, the P5 matrix)
therefore could not see it. This module is that name, and nothing else.

It is deliberately the same shape as `gap_gated_mppi`: **the arm, not the
mechanism.** Both cost terms already exist and are already tested
(`RiskMPPI`'s DYNAMIC-channel risk cost, `PredictedGeometryCritic`'s
anisotropic pedestrian field); no new cost, no new constant, no new
measurement is introduced here. `test_social_mppi_arm.py` pins that as an
equivalence — this controller must produce commands **byte-identical** to
`risk_mppi(w_risk=40, w_ped=50)` — so naming the cell cannot silently become
re-tuning it, and so the readings D-218/D-219/D-234/D-235 recorded transfer to
this name without being re-taken.

Why it is **not** added to `three_arm.ARMS`
-------------------------------------------
Adding it there would put a `w_risk = 40` row into a dict whose every entry
carries `w_risk = 0.0`, silently mixing the two denominations the module exists
to keep apart — the exact error D-218 caught D-217 making. `ARMS` answers "what
does each knob buy alone"; this arm answers "what does the pair buy". Both are
wanted; reporting one as the other is what is forbidden.
`test_social_mppi_arm.py` pins the isolation invariant on `ARMS` so a future
cycle cannot quietly break it, in either direction.
"""

from __future__ import annotations

from .risk_mppi import RiskMPPI


class SocialMPPI(RiskMPPI):
    """`RiskMPPI` defaulted to the 2x2's `(w_risk, w_ped) = (40, 50)` cell.

    Overridable like any other controller — the defaults are the claim, not a
    restriction. `w_risk`'s value is `RiskMPPI`'s own shipped default and is
    inherited rather than respelled; only `w_ped` moves.
    """

    def __init__(self, scenario, seed: int = 0, w_ped: float = 50.0, **kwargs):
        super().__init__(scenario, seed=seed, w_ped=w_ped, **kwargs)
