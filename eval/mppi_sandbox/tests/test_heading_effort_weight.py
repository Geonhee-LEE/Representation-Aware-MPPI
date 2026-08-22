# SPDX-License-Identifier: BSD-3-Clause
"""D-433: `w_omega` does not fix the heading residual — it reshuffles seeds.

STATE named `heading_err_rms_max` under the `knee+shape` pair the sole dominant
residual on `cafe_obstacle_crossing_v0`: D-430 measured clearance green 16/16
and every remaining failure a tracking check, heading on 10 seeds. The obvious
lever is the rotation-effort weight `w_omega` (0.5 by default, "no free
pirouettes"), so this module prices it.

A 4-point sweep at n=16 (w_omega in {0.5, 1.0, 2.0, 4.0}) reads net pass
6 / 5 / 9 / 7. Read as a headline that is "2.0 lifts 6/16 -> 9/16"; read as a
*response curve* it is non-monotone, which is the signature of seed noise
rather than a knob that works. Two things settle it, and both say the same:

1. **The arms share seeds, so the test is paired.** D-430 quoted Fisher, which
   assumes independent samples and throws away the pairing. McNemar on the same
   16 seeds gives 5 seeds 0->1 against 2 seeds 1->0, exact two-sided
   **p ~ 0.45**. At n=16 the effect is not established.
2. **The per-seed heading deltas are two-sided.** Moving 0.5 -> 2.0 improves
   `heading_err_rms` on 9 seeds and worsens it on 7, spanning -0.55 to +0.28.
   The population barely moves; which seeds sit on which side of 0.30 does.

That is the same shape D-430 found for the barrier-shape knob — *mode is not a
property of the seed, and the knob reshuffles rather than converts*. Finding it
a second time, on a different knob, is the reason this is recorded as a
decision instead of a tuning note: on this scene the arm knobs move seeds
across the threshold in both directions without shifting the distribution, so
**the heading residual is not reachable by effort weighting** and the next
lever has to be structural.

The suspected structure, stated here as the open question and *not* as a
measured claim: clearance is bought by deviating from the reference path, and
`heading_err_rms` is measured against that same path, so the knee that pins
clearance to 0.300-0.328 on 16/16 seeds (D-426: the robot parks exactly on
whatever knee it is priced against) may be *paying* for it in heading. If so no
effort weight can fix it and the trade is definitional. See Q-181.

Cost: 32 integrations (2 arms x 16 seeds, ~25 s), computed once in a module
fixture.
"""

from __future__ import annotations

from math import comb

import pytest

from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.run import run_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
#: Clearance threshold both knobs are set to. Matches `test_knee_shape_ensemble.GATE`.
GATE = 0.30
#: The acceptance threshold this module is about.
HEADING_GATE = 0.30
#: Same 16 seeds as D-430, so the `w0.5` arm here reproduces that arm exactly
#: and the comparison below is genuinely paired.
SEEDS = tuple(range(16))
#: Shipped default (`MPPIParams.w_omega`) and the sweep's argmax. The other two
#: points measured (1.0 -> 5/16, 4.0 -> 7/16) are what establish non-monotonicity;
#: they are quoted in the docstring rather than re-run, because the claim this
#: module pins is the *paired* one and that needs only these two arms.
W_DEFAULT = 0.5
W_BEST = 2.0

ARMS = {
    "w0.5": dict(collision_margin=GATE, obs_barrier_band=GATE, w_omega=W_DEFAULT),
    "w2.0": dict(collision_margin=GATE, obs_barrier_band=GATE, w_omega=W_BEST),
}


@pytest.fixture(scope="module")
def paired():
    """{arm: [per-seed run summary]} — 2 arms x 16 seeds, computed once."""
    return {
        arm: [run_scenario(CROSSING, controller="stock_mppi", seed=s,
                           params=MPPIParams(**kw))
              for s in SEEDS]
        for arm, kw in ARMS.items()
    }


def _passes(runs) -> list[bool]:
    return [bool(r["pass"]) for r in runs]


def _heading(runs) -> list[float]:
    return [r["metrics"]["heading_err_rms"] for r in runs]


def _mcnemar_exact_two_sided(b01: int, b10: int) -> float:
    """Exact binomial test on the discordant pairs. b01/b10 = fail->pass / pass->fail."""
    n = b01 + b10
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(min(b01, b10) + 1)) / 2 ** n
    return min(2.0 * tail, 1.0)


def test_the_headline_is_a_lift_and_that_is_why_it_needs_a_paired_test(paired):
    """w_omega=2.0 does read as more passes — the point is that it is not enough."""
    lo, hi = sum(_passes(paired["w0.5"])), sum(_passes(paired["w2.0"]))
    assert lo == 6, f"D-430's knee+shape arm should reproduce at 6/16, got {lo}"
    assert hi > lo, "the sweep's argmax should out-count the default, else this module is moot"


def test_the_w_omega_lift_is_not_significant_when_paired(paired):
    """The load-bearing negative: p ~ 0.45, so the lift is not established at n=16."""
    a, b = _passes(paired["w0.5"]), _passes(paired["w2.0"])
    b01 = sum(1 for x, y in zip(a, b) if not x and y)
    b10 = sum(1 for x, y in zip(a, b) if x and not y)
    assert (b01, b10) == (5, 2), f"discordant pairs moved: {(b01, b10)}"
    p = _mcnemar_exact_two_sided(b01, b10)
    assert p > 0.05, f"McNemar p={p:.3f} — if this ever goes significant, D-433 is wrong"
    assert p == pytest.approx(0.4531, abs=5e-4)


def test_heading_error_moves_in_both_directions(paired):
    """Not a shift of the distribution — a reshuffle across the threshold (D-430's shape)."""
    lo, hi = _heading(paired["w0.5"]), _heading(paired["w2.0"])
    deltas = [y - x for x, y in zip(lo, hi)]
    improved = sum(1 for d in deltas if d < 0)
    worsened = sum(1 for d in deltas if d > 0)
    assert improved > 0 and worsened > 0, (
        "a one-sided response would mean w_omega is a real lever; it is not"
    )
    assert (improved, worsened) == (9, 7), f"per-seed sign pattern moved: {(improved, worsened)}"


def test_clearance_stays_green_under_both_effort_weights(paired):
    """The knee owns clearance; w_omega does not spend it. 16/16 on both arms."""
    for arm, runs in paired.items():
        clear = [r["min_obstacle_clearance"] for r in runs]
        assert all(c >= GATE for c in clear), f"{arm} lost clearance: min {min(clear):.4f}"


def test_heading_is_still_the_dominant_residual_at_the_sweep_argmax(paired):
    """Even at the best w_omega the scene fails, and it fails on heading alone."""
    failing: dict[str, int] = {}
    for r in paired["w2.0"]:
        for key, val in r["acceptance"].items():
            if val is False:
                failing[key] = failing.get(key, 0) + 1
    assert set(failing) == {"heading_err_rms_max"}, (
        f"at w_omega={W_BEST} the residual should be heading-only, got {failing}"
    )
    assert failing["heading_err_rms_max"] == 7
    # The cte failures D-430 saw on this scene (cte_rms_max 3, cte_max 3) are
    # absent here. That is *not* claimed as a fix — it is the same reshuffle
    # seen from the other side, and it is why the residual set is heading-only.
    assert sum(_passes(paired["w2.0"])) + failing["heading_err_rms_max"] == len(SEEDS)
