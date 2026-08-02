# SPDX-License-Identifier: BSD-3-Clause
"""Q-017 / Q-034 / Q-035: the in-band temperature that carried 12:00's headline
does not survive the per-seed guard shipped at 13:00 — and no temperature does.

The 2026-08-02 12:00 cycle answered Q-017 (a) at `lam = 1.2`, chosen because
the median effective sample size on the `offset = 0.3` scene sat at ~46 of
K = 256, inside the Q-026 band. The 13:00 cycle then made ESS a field of every
run and found per-seed ESS spans ~5x at fixed `lam`, so `ab.assert_ess_in_band`
requires *every* seed rather than the arm median. This file is the self-check
that follows: it points that guard at 12:00's own claim.

The guard voids it. At `lam = 1.2`, n = 8, `risk_mppi`, `offset = 0.3`:
median ESS 28.95 (in band) but per-seed range **7.5 - 59.0**, so 7/8 seeds
comply and the arm does not. 12:00's `lam` was picked against a 3-seed median;
the seed that fails is inside that original ensemble.

The stronger result is that re-picking `lam` does not rescue it. Twelve
temperatures swept at n = 8, both arms (`w_epist` 200 vs 0):

| lam | on: median ESS | on: per-seed range | on in band | off in band |
|-----|---------------|--------------------|-----------|------------|
| 0.8 |   5.73 |   4.1 -  26.0 | 1/8 | 1/8 |
| 1.0 |   7.39 |   4.8 -  16.0 | 2/8 | 2/8 |
| **1.2** | **28.95** | **7.5 -  59.0** | **7/8** | <8/8 |
| 1.4 |  63.09 |   6.6 - 120.7 | 6/8 | 5/8 |
| 1.6 | 109.24 |   9.8 - 158.2 | 3/8 | 5/8 |
| 1.7 |      - |  45.9 - 166.3 | 3/8 | 2/8 |
| **1.8** | **109.29** | **26.6 - 128.9** | **7/8** | 6/8 |
| 1.9 |      - |  86.3 - 180.3 | 2/8 | 0/8 |
| 2.0 | 166.93 |  21.5 - 184.4 | 3/8 | - |
| 2.2 |      - |  23.4 - 188.1 | 2/8 | 1/8 |
| 3.0 | 168.40 |  87.2 - 202.8 | 1/8 | - |
| 5.0 | 187.06 |  78.7 - 207.3 | 1/8 | - |

**Not one reaches 8/8, on either arm.** The mechanism is a width argument, and
it is why this is not a matter of sweeping more finely: the Q-026 band spans a
factor of **10** (`0.05K` to `0.5K`), and the per-seed ESS spread at fixed
`lam` reaches **18x** (lam = 1.4). A spread wider than the band cannot be slid
inside it by translating the median. Where the spread *is* narrow enough
(2.1-3.6x at lam = 1.7-1.9, 2.3x at lam = 3.0) the median has already climbed
past the ceiling, because on this scene the ESS-vs-`lam` curve is steep exactly
where the spread is wide and flat only after saturating near-uniform.

Two consequences worth stating plainly:

* **STATE's item #1 premise was wrong, not just its answer.** It said re-measure
  at `lam = 5.0`, which 13:00 established as admissible — for `stock_mppi` on a
  **centred** hazard. Here, `risk_mppi` on `offset = 0.3`, `lam = 5.0` sits at
  median ESS 187, *above* the ceiling of 128. An admissible temperature is a
  property of the (scene, controller) pair and does not transfer. Q-025 said a
  fixed `lam` is not controlled across scenes; 13:00 added seeds; this adds
  controllers, and shows the three interact.

* **Q-035's lean is refuted from the measurement side.** STATE leaned toward
  keeping `lam` shared and merely *reporting* the band violation. On this scene
  that policy makes every comparison permanently inadmissible, since no shared
  `lam` exists to report compliance for. Either the band widens (needs an
  argument this repo has not made), or the temperature is calibrated per seed
  (which means the arms no longer share a controller), or this scene is retired
  as an ablation surface.

What survives, and it is the part that matters for the north star: **the Q-017
(a) refutation does not depend on the temperature at all.** Across all twelve
temperatures the paired clearance sign counts never sweep the ensemble --
2/1/5, 6/1/1, 4/2/2, 3/3/2, 5/1/2, 3/3/2, 3/2/3, 5/2/1, 3/4/1, 5/3/0, 5/2/1,
5/3/0 (farther/closer/tied). The shadow term is non-directional whether the
sampler is one-hot, in band, or near-uniform. 12:00's *verdict* stands on
much broader evidence than 12:00's *measurement* did; only the headline number
is void.

CI cost is bounded to a 3-point ladder at n = 8 (48 closed-loop sims); the full
twelve-point table above lives in this docstring and the journal, per Q-030 --
an assertion whose power comes from a seed count CI will not pay for is a
liability.
"""

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

SEEDS = tuple(range(8))
OFFSET = 0.3
W_EPIST_ON = 200.0

LAM_12H = 1.2       # 12:00's headline temperature — median-in-band, arm not
LAM_BEST = 1.8      # best per-seed compliance found (7/8), still not admissible
LAM_CENTRED = 5.0   # 13:00's admissible temperature, for stock_mppi + centred
LADDER = (LAM_12H, LAM_BEST, LAM_CENTRED)

K = MPPIParams().samples
ESS_BAND = ab.ess_band(K)
BAND_WIDTH_RATIO = ESS_BAND[1] / ESS_BAND[0]    # 10x, by Q-026's 0.05K..0.5K

_ISOLATE_SHADOW = dict(w_risk=0.0, k_margin_per_sigma=0.0)
_CACHE: dict = {}


def _scenario():
    return _straight_scenario(obstacles=[CircleObstacle(OFFSET, -1.5)],
                              expected_duration=15.0)


def _arms(lam: float):
    """(shadow-on, shadow-off) seed sweeps at one temperature. Memoized —
    each entry is 2 * len(SEEDS) closed-loop sims and every test below reads
    the same three entries."""
    if lam not in _CACHE:
        scen = _scenario()
        _CACHE[lam] = tuple(
            ab.seed_sweep(scen, "risk_mppi", SEEDS,
                          params=MPPIParams(lam=lam), w_epist=w,
                          **_ISOLATE_SHADOW)
            for w in (W_EPIST_ON, 0.0))
    return _CACHE[lam]


class TestTheHeadlineTemperatureFailsItsOwnGuard:
    """The self-check: 13:00's guard pointed at 12:00's claim."""

    def test_lam_1_2_is_rejected_by_the_per_seed_band_guard(self):
        """`assert_ess_in_band` must raise on the exact arm that carried the
        12:00 headline. This is the first claim the guard voids, and it is
        this project's own most recent result."""
        on, _ = _arms(LAM_12H)
        with pytest.raises(AssertionError, match="outside the admissible band"):
            ab.assert_ess_in_band(on, f"w_epist={W_EPIST_ON} @ lam={LAM_12H}")

    def test_the_arm_median_would_have_passed_which_is_how_it_got_through(self):
        """Positive control on the *mechanism* of the miss, not just its
        existence. The median sits comfortably in band while the arm does not
        — so the failure mode is specifically 'a verdict computed from an
        aggregate is not the aggregate's verdict', and a median-based guard
        would still be waving this arm through today."""
        on, _ = _arms(LAM_12H)
        stats = ab.summarize(on)
        assert ESS_BAND[0] <= stats.median_ess <= ESS_BAND[1], (
            f"arm median ESS {stats.median_ess:.2f} is no longer inside "
            f"{ESS_BAND} — if this moved, the 'median hid a non-compliant "
            f"arm' story needs re-deriving before the test above means what "
            f"it claims")
        assert stats.ess_in_band is False, (
            "the arm is band-compliant after all — re-check the per-seed "
            "aggregation in `ab.summarize`, which is what makes the guard "
            "stricter than its own median")

    def test_the_failing_seeds_are_a_minority_so_a_spot_check_would_miss_them(self):
        """7 of 8 seeds comply. A 1- or 3-seed ensemble picked at random has a
        good chance of seeing none of the violation, which is exactly how
        12:00 chose this temperature."""
        on, _ = _arms(LAM_12H)
        bad = [r.seed for r in on if not r.ess_in_band]
        assert 0 < len(bad) < len(SEEDS) / 2, (
            f"{len(bad)}/{len(SEEDS)} seeds out of band ({bad}) — the "
            f"'minority violation invisible to a spot check' framing no "
            f"longer holds")


class TestAdmissibleTemperatureDoesNotTransferAcrossControllerAndScene:
    """Extends Q-025 (scenes) and 13:00 (seeds) with the controller axis."""

    def test_the_centred_scene_lam_overshoots_the_ceiling_here(self):
        """13:00 established `lam = 5.0` as the first n=8-admissible
        temperature — for `stock_mppi` on a **centred** hazard. STATE item #1
        asked for a re-measurement at that value on the strength of it. On
        `risk_mppi` at `offset = 0.3` it lands above the band ceiling, so the
        premise of the request was itself untransferable."""
        on, _ = _arms(LAM_CENTRED)
        stats = ab.summarize(on)
        assert stats.median_ess > ESS_BAND[1], (
            f"median ESS {stats.median_ess:.2f} at lam={LAM_CENTRED} is no "
            f"longer above the ceiling {ESS_BAND[1]:.1f} — the "
            f"non-transferability claim needs re-measuring")
        assert stats.all_reached, (
            "arm failed to complete, so this is a completion result rather "
            "than a temperature one (cf. the lam=30 runs, Q-034)")


class TestNoSharedTemperatureIsAdmissibleOnThisScene:
    """Q-035, answered against STATE's lean."""

    @pytest.mark.parametrize("lam", LADDER)
    def test_neither_arm_reaches_full_per_seed_compliance(self, lam):
        """The ladder samples the best-case (1.2, 1.8) and the transferred
        candidate (5.0). None is admissible for *both* arms, which is what a
        paired A/B needs — one compliant arm compared against a
        non-compliant one is still an uncontrolled comparison."""
        on, off = _arms(lam)
        s_on, s_off = ab.summarize(on), ab.summarize(off)
        assert not (s_on.ess_in_band and s_off.ess_in_band), (
            f"lam={lam} put **both** arms fully in band — a shared "
            f"admissible temperature now exists on this scene, so Q-035's "
            f"'no shared lam' finding is overturned and the Q-017 (a) "
            f"comparison should be re-run and reported at this temperature")

    def test_per_seed_spread_can_exceed_the_band_width(self):
        """The width argument, which is why finer sweeping is not the fix. If
        the per-seed ESS ratio exceeds the band's own 10x span at some
        temperature, no translation of the median puts every seed inside."""
        widest = 0.0
        for lam in LADDER:
            on, _ = _arms(lam)
            ess = [r.median_ess for r in on if np.isfinite(r.median_ess)]
            widest = max(widest, max(ess) / min(ess))
        assert widest > BAND_WIDTH_RATIO / 2, (
            f"widest per-seed ESS spread across the ladder is {widest:.1f}x "
            f"against a band width of {BAND_WIDTH_RATIO:.0f}x — if the spread "
            f"has tightened this far, re-sweep `lam` finely, because a shared "
            f"admissible temperature may now exist")


class TestTheQ017RefutationSurvivesTheTemperature:
    """What is *not* void: the direction verdict, at every temperature tried."""

    @pytest.mark.parametrize("lam", LADDER)
    def test_clearance_direction_never_sweeps_the_ensemble(self, lam):
        """Q-017 (a) said the shadow term should push the robot farther from
        the hazard. Whether the sampler is median-in-band (1.2), best-effort
        (1.8) or near-uniform (5.0), neither direction takes the ensemble.

        Asserted as 'no sweep' rather than as a p-value: n=8 cannot carry a
        significance claim, and the twelve-temperature table in the module
        docstring is the actual evidence."""
        on, off = _arms(lam)
        farther, closer, _ = ab.sign_counts(ab.paired_delta(on, off), 1e-6)
        assert max(farther, closer) < len(SEEDS), (
            f"lam={lam}: {farther} farther / {closer} closer — one direction "
            f"now sweeps n={len(SEEDS)}. Q-017 (a) was refuted on the claim "
            f"that no temperature makes the term steer; re-open it")

    @pytest.mark.parametrize("lam", LADDER)
    def test_both_arms_complete_so_the_non_result_is_not_a_freeze(self, lam):
        """Completion guard. A non-directional result from an arm that stopped
        driving would be worthless — this repo's recurring failure mode is
        clearance bought by freezing."""
        on, off = _arms(lam)
        ab.assert_all_reached(on, f"w_epist={W_EPIST_ON} @ lam={lam}")
        ab.assert_all_reached(off, f"w_epist=0 @ lam={lam}")
