# SPDX-License-Identifier: BSD-3-Clause
"""The sign of each shipped epistemic critic, read off its own cost.

The 08:00 research feed (PA-MPPI `2509.14978`) asserts this branch "has never
stated which of the two it is" — attract (reward observing the unknown) or
repel (penalise exposure to it). These tests are the refutation: the branch
ships **both**, and the signs are opposed on one geometry at one weight.
"""

import numpy as np
import pytest

from eval.mppi_sandbox.critics import ObservationValueCritic, ShadowCostCritic
from eval.mppi_sandbox.epistemic_sign import (ATTRACT, BOTH, CANCELLED, REPEL,
                                              SILENT, SPREAD_EPS, arm_costs,
                                              blind_corner, cancelling_ratio,
                                              classify, probe_all,
                                              signs_are_opposed)


def _summed(w_epist, w_voo, **geometry):
    """Classify the both-arms-on sum at an arbitrary weight pair."""
    costs, sigma = arm_costs(w_epist, w_voo, **geometry)
    return classify(costs["ShadowCostCritic"] + costs["ObservationValueCritic"],
                    sigma)


class TestTheTwoShippedSignsAreOpposed:
    """The headline: the sign question is answered by the code, not open."""

    def test_shadow_cost_is_repel_and_observation_value_is_attract(self):
        readings = probe_all()
        assert readings["ShadowCostCritic"].sign == REPEL
        assert readings["ObservationValueCritic"].sign == ATTRACT
        assert signs_are_opposed(readings)

    def test_both_arms_read_at_the_same_weight(self):
        """The sign is a property of the form, not of the weight — so the
        reading must not be explainable as a tuning difference. Sweeping the
        shared weight moves the magnitudes and leaves both signs put."""
        for w in (1.0, 10.0, 200.0):
            readings = probe_all(w=w)
            assert readings["ShadowCostCritic"].sign == REPEL
            assert readings["ObservationValueCritic"].sign == ATTRACT

    def test_entering_the_shadow_is_cheaper_under_the_attract_arm(self):
        """The behavioural statement the sign stands for: at a blind corner
        the attract arm prefers the shadow-revealing location that the repel
        arm charges for."""
        r = probe_all()
        assert r["ShadowCostCritic"].split > 0.0
        assert r["ObservationValueCritic"].split < 0.0


class TestBothArmsOnIsQ148sCheapPrecursor:
    """Q-148's stated cheap precursor: both critics read the same EPISTEMIC
    channel and add into the same `_extra_cost`, so both-on is a configuration
    the planner already permits. Their supports differ — repel charges points
    **inside** the shadow, attract discounts points that **see into** it — so
    the sum need not cancel merely because the signs oppose."""

    def test_the_sum_does_not_cancel(self):
        """The lean Q-148 was built on, confirmed: opposed signs, surviving
        sum. If this went CANCELLED the whole both-on configuration would be
        a no-op and the A/B would only ever have two arms to compare."""
        r = probe_all()[BOTH]
        assert r.sign != CANCELLED
        assert r.spread > 0.0

    def test_the_sum_is_exactly_the_two_arms_added(self):
        """Guards the third entry against becoming its own re-derivation: the
        summed means must be the arms' means added, or `BOTH` is measuring
        something other than both-arms-on."""
        r = probe_all()
        assert r[BOTH].mean_exposed == pytest.approx(
            r["ShadowCostCritic"].mean_exposed
            + r["ObservationValueCritic"].mean_exposed)
        assert r[BOTH].mean_observed == pytest.approx(
            r["ShadowCostCritic"].mean_observed
            + r["ObservationValueCritic"].mean_observed)

    def test_at_equal_weight_the_repel_arm_takes_the_sum(self):
        """The headline reading — and it collapses toward the arm D-021
        measured *inaudible*, which is the uncomfortable half."""
        assert probe_all()[BOTH].sign == REPEL

    def test_the_equal_weight_verdict_is_stable_in_the_shared_weight(self):
        """Scaling both arms together cannot move the sum's sign — the sum is
        linear and 1:1 is preserved. Pins that the headline is a statement
        about the *ratio*, not about the magnitude."""
        for w in (1.0, 10.0, 200.0):
            assert probe_all(w=w)[BOTH].sign == REPEL

    def test_zero_weight_leaves_the_sum_silent(self):
        assert probe_all(w=0.0)[BOTH].sign == SILENT

    def test_the_sum_does_not_vote_on_whether_the_arms_are_opposed(self):
        """`signs_are_opposed` is a claim about shipped critics; a derived
        entry must not be able to satisfy it."""
        readings = probe_all()
        assert signs_are_opposed(readings)
        assert signs_are_opposed({k: v for k, v in readings.items()
                                  if k != BOTH})


class TestTheCancellingRatioIsWhatMakesTheSumInterpretable:
    """"REPEL at 1:1" says nothing about how close it was. The ratio says how
    much weight the attract arm needs to take the sum back, and it is the
    scale-free content of the reading."""

    def test_the_predicted_ratio_actually_cancels(self):
        """The ratio is derived algebraically from unit-weight splits; this
        walks the two critics at that ratio and checks the sum really does go
        CANCELLED. Prediction, then measurement — not algebra restated."""
        rho = cancelling_ratio()
        assert _summed(rho, 1.0).sign == CANCELLED

    def test_either_side_of_the_ratio_takes_the_opposite_sign(self):
        """CANCELLED is a knife-edge, not a band: ±1% flips it both ways, so
        `SPLIT_EPS` is detecting the root rather than defining a region."""
        rho = cancelling_ratio()
        assert _summed(rho * 1.01, 1.0).sign == REPEL
        assert _summed(rho * 0.99, 1.0).sign == ATTRACT

    def test_attract_needs_several_times_the_repel_weight(self):
        """The measured asymmetry, and Q-148's practical consequence: equal
        weights are not a neutral default — they hand the sum to repel, and
        the attract arm needs ~2.8x to be heard."""
        rho = cancelling_ratio()
        assert 0.0 < rho < 1.0
        assert 1.0 / rho == pytest.approx(2.79, abs=0.05)

    def test_the_repel_arm_is_what_makes_the_root_well_posed(self):
        """`cancelling_ratio` divides by the repel arm's unit split, so it is
        only defined against an opposed pair. With the two *shipped* critics
        that precondition cannot be violated through geometry — wherever the
        geometry poses the question at all, `ShadowCostCritic = w·σ` has a
        strictly positive split — so the guard in the code is defensive and
        deliberately untested. What is testable is the precondition itself."""
        costs, sigma = arm_costs(1.0, 1.0)
        assert classify(costs["ShadowCostCritic"], sigma).split > 0.0


class TestCancelledIsNotAWeakSignEither:
    """SILENT is "no spread"; CANCELLED is "spread that averages out". Both are
    refusals to name a sign, and they are refusals for different reasons."""

    def test_cancelled_is_disjoint_from_every_other_verdict(self):
        assert CANCELLED not in (REPEL, ATTRACT, SILENT)

    def test_a_cancelled_reading_still_has_spread(self):
        """What separates it from SILENT: the term is loud pointwise, it just
        has no mean preference. Reporting it as SILENT would claim the term
        cancels in the softmax, which it does not."""
        r = _summed(cancelling_ratio(), 1.0)
        assert r.spread > SPREAD_EPS
        assert r.split == pytest.approx(0.0, abs=1e-9)

    def test_an_exactly_balanced_synthetic_cost_is_cancelled(self):
        """The rule on a hand-built vector, with no BEV in the way."""
        sigma = np.array([1.0, 1.0, 0.0, 0.0])
        assert classify(np.array([3.0, 7.0, 4.0, 6.0]), sigma).sign == CANCELLED

    def test_the_old_tie_break_would_have_called_it_attract(self):
        """Regression pin on the reason this verdict was added: `mean_e >
        mean_o else ATTRACT` silently routed an exact tie to ATTRACT, which on
        a summed pair is a reachable configuration rather than a float
        accident."""
        sigma = np.array([1.0, 1.0, 0.0, 0.0])
        r = classify(np.array([3.0, 7.0, 4.0, 6.0]), sigma)
        assert r.mean_exposed == r.mean_observed
        assert r.sign != ATTRACT


class TestWhyTheMeanSplitAndNotTheCorrelation:
    """`SIGN_STATISTIC = "mean_split"` is a choice, and this pins the reason:
    the correlation is decisive for a pointwise-in-σ cost and nearly signless
    for the aggregate-map cost, even though the latter's split is large."""

    def test_pointwise_cost_correlates_perfectly_with_sigma(self):
        r = probe_all()["ShadowCostCritic"]
        assert r.corr == pytest.approx(1.0)

    def test_aggregate_map_cost_is_decisive_by_split_and_weak_by_corr(self):
        r = probe_all()["ObservationValueCritic"]
        # V(q) is an aggregate over rays from q, not a function of sigma at q,
        # so the correlation understates a sign the split states plainly.
        assert abs(r.corr) < 0.5
        assert r.mean_exposed < 0.5 * r.mean_observed


class TestSilenceIsAThirdVerdictNotAWeakSign:
    """D-021 measured `ShadowCostCritic` signal-free on the crossing scene. A
    term with no spread has no sign; reporting it as weakly-repel would be the
    D-241 silent-vacuity shape."""

    def test_zero_weight_is_silent_under_both_arms(self):
        readings = probe_all(w=0.0)
        assert readings["ShadowCostCritic"].sign == SILENT
        assert readings["ObservationValueCritic"].sign == SILENT
        assert not signs_are_opposed(readings)

    def test_silence_is_decided_before_the_mean_split_is_consulted(self):
        """A constant *non-zero* cost has a mean split of exactly 0 either
        way, but the guard must fire on spread, not on the split — otherwise
        a float wobble in the means picks a sign out of pure silence."""
        sigma = np.array([1.0, 1.0, 0.0, 0.0])
        reading = classify(np.full(4, 7.5), sigma)
        assert reading.sign == SILENT
        assert reading.spread <= SPREAD_EPS
        assert reading.corr == 0.0

    def test_silent_is_disjoint_from_the_two_signs(self):
        assert SILENT not in (REPEL, ATTRACT)


class TestTheGeometryHasToPoseTheQuestion:
    def test_candidate_set_with_no_shadow_is_refused_not_graded(self):
        """A geometry where nothing is exposed cannot answer "does entering
        the shadow cost more" — it is refused rather than silently graded, the
        `headline_rescope` NOT_COMPARABLE pattern."""
        with pytest.raises(ValueError, match="does not pose the question"):
            classify(np.array([1.0, 2.0, 3.0]), np.zeros(3))

    def test_candidate_set_with_no_observed_point_is_refused(self):
        with pytest.raises(ValueError, match="does not pose the question"):
            classify(np.array([1.0, 2.0, 3.0]), np.ones(3))

    def test_mismatched_shapes_are_refused(self):
        with pytest.raises(ValueError, match="differ"):
            classify(np.zeros(3), np.zeros(4))

    def test_the_blind_corner_actually_casts_a_shadow(self):
        """Guards the whole module against a geometry regression: if the disc
        stopped casting a shadow every reading above would go SILENT and the
        suite would still be green without this."""
        _, _, _, points, sigma = blind_corner()
        assert (sigma > 0.5).sum() > 0
        assert (sigma <= 0.5).sum() > 0
        assert len(points) == len(sigma)


class TestTheReadingMatchesTheCriticsDirectly:
    """The instrument must not drift from the cost functions it reads — these
    recompute the two costs by hand and check the classification agrees."""

    def test_shadow_cost_reading_reproduces_the_critic(self):
        producer, bev, robot_xy, points, sigma = blind_corner()
        cost = ShadowCostCritic(w_epist=10.0).cost(bev, points, len(points))
        np.testing.assert_allclose(cost, 10.0 * sigma)
        assert classify(cost, sigma).sign == REPEL

    def test_observation_value_reading_reproduces_the_critic(self):
        producer, bev, robot_xy, points, sigma = blind_corner()
        cost = ObservationValueCritic(w_voo=10.0).cost(
            producer, bev, robot_xy, 0.0, points, len(points))
        assert (cost >= 0.0).all()          # add-only contract
        assert classify(cost, sigma).sign == ATTRACT
